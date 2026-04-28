import { Type } from "@sinclair/typebox";
import { definePluginEntry, type OpenClawPluginApi } from "openclaw/plugin-sdk/plugin-entry";
import type {
  AgentEndResponse,
  BeforeAgentStartResponse,
  BeforeCompactionResponse,
  HealthResponse,
} from "./contracts.ts";
import {
  buildRuntimeEnvelope,
  extractConversation,
  extractLatestUserQuery,
  formatPlanningHints,
  withGracefulFailure,
} from "./runtime-helpers.js";

const langGraphConfigSchema = Type.Object({
  enabled: Type.Boolean({ default: true, description: "Enable LangGraph orchestration hooks" }),
  apiHost: Type.String({ default: "127.0.0.1", description: "Host of the LangGraph runtime API" }),
  apiPort: Type.Number({ default: 20240, description: "Port of the LangGraph runtime API" }),
  graphId: Type.String({ default: "default", description: "Graph or tenant identifier" }),
  autoRetrieve: Type.Boolean({ default: true, description: "Fetch retrieval context before agent start" }),
  autoReflect: Type.Boolean({ default: true, description: "Write turn events and schedule reflection after agent end" }),
  archiveOnCompaction: Type.Boolean({ default: true, description: "Checkpoint session state before compaction" }),
  requestTimeoutMs: Type.Number({ default: 8000, description: "Timeout for synchronous runtime requests" }),
  reflectionTimeoutMs: Type.Number({ default: 15000, description: "Timeout for asynchronous reflection requests" }),
});

type LangGraphConfig = {
  enabled: boolean;
  apiHost: string;
  apiPort: number;
  graphId: string;
  autoRetrieve: boolean;
  autoReflect: boolean;
  archiveOnCompaction: boolean;
  requestTimeoutMs: number;
  reflectionTimeoutMs: number;
};

type LoggerLike = {
  info: (...args: unknown[]) => void;
  warn?: (...args: unknown[]) => void;
  error: (...args: unknown[]) => void;
};

class LangGraphRuntimeClient {
  private readonly baseUrl: string;

  constructor(host: string, port: number) {
    this.baseUrl = `http://${host}:${port}`;
  }

  async request<T>(
    path: string,
    method: "GET" | "POST" = "GET",
    body?: unknown,
    timeoutMs = 8000,
  ): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers: { "Content-Type": "application/json" },
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
      });

      if (!response.ok) {
        const text = await response.text().catch(() => "");
        throw new Error(`HTTP ${response.status}: ${text}`);
      }

      return (await response.json()) as T;
    } finally {
      clearTimeout(timer);
    }
  }

  fireAndForget<T>(path: string, body: unknown, timeoutMs: number, log: LoggerLike, label: string): void {
    this.request<T>(path, "POST", body, timeoutMs)
      .then((result) => {
        log.info(`langgraph-orchestrator [${label}]: OK ${JSON.stringify(result)}`);
      })
      .catch((error) => {
        log.warn?.(`langgraph-orchestrator [${label}]: ${String(error)}`);
      });
  }
}

async function readSessionFile(sessionFile?: string): Promise<string> {
  if (!sessionFile) return "";
  try {
    const fs = await import("node:fs/promises");
    return await fs.readFile(sessionFile, "utf8");
  } catch {
    return "";
  }
}

function buildConfig(rawConfig?: unknown): LangGraphConfig {
  const cfg = (rawConfig ?? {}) as Partial<LangGraphConfig>;
  return {
    enabled: cfg.enabled ?? true,
    apiHost: cfg.apiHost ?? "127.0.0.1",
    apiPort: cfg.apiPort ?? 20240,
    graphId: cfg.graphId ?? "default",
    autoRetrieve: cfg.autoRetrieve ?? true,
    autoReflect: cfg.autoReflect ?? true,
    archiveOnCompaction: cfg.archiveOnCompaction ?? true,
    requestTimeoutMs: cfg.requestTimeoutMs ?? 8000,
    reflectionTimeoutMs: cfg.reflectionTimeoutMs ?? 15000,
  };
}

export default definePluginEntry({
  id: "langgraph-orchestrator",
  configSchema: langGraphConfigSchema,
  async register(api: OpenClawPluginApi, rawConfig?: unknown) {
    const config = buildConfig(rawConfig);
    const log = api.logger;

    if (!config.enabled) {
      log.info("langgraph-orchestrator: disabled by config.");
      return;
    }

    const client = new LangGraphRuntimeClient(config.apiHost, config.apiPort);

    if (config.autoRetrieve) {
      api.on("before_agent_start", async (event: Record<string, unknown>) => {
        const messages = Array.isArray(event.messages) ? (event.messages as unknown[]) : undefined;
        const query = extractLatestUserQuery(messages, typeof event.prompt === "string" ? event.prompt : "");
        if (!query) return;

        return withGracefulFailure(async () => {
          const result = await client.request<BeforeAgentStartResponse>(
            "/runtime/before-agent-start",
            "POST",
            {
              ...buildRuntimeEnvelope(event, config.graphId),
              query,
              messages,
            },
            config.requestTimeoutMs,
          );

          const contextParts = [result.prepend_context, formatPlanningHints(result.planning_hints)]
            .filter((value): value is string => Boolean(value && value.trim()));

          if (contextParts.length === 0) return undefined;
          return { prependContext: contextParts.join("\n\n") };
        }, log, "before_agent_start");
      });
    }

    if (config.autoReflect) {
      api.on("agent_end", async (event: Record<string, unknown>) => {
        if (event.success === false) return;
        const messages = Array.isArray(event.messages) ? (event.messages as unknown[]) : undefined;
        const conversation = extractConversation(messages);
        if (!conversation) return;

        client.fireAndForget<AgentEndResponse>(
          "/runtime/agent-end",
          {
            ...buildRuntimeEnvelope(event, config.graphId),
            success: event.success !== false,
            conversation,
            messages,
            tool_outcomes: event.toolOutcomes ?? event.tool_outcomes ?? null,
          },
          config.reflectionTimeoutMs,
          log,
          "agent_end",
        );
      });
    }

    if (config.archiveOnCompaction) {
      api.on("before_compaction", async (event: Record<string, unknown>) => {
        const archivedSession = await readSessionFile(typeof event.sessionFile === "string" ? event.sessionFile : undefined);
        const messages = Array.isArray(event.messages) ? (event.messages as unknown[]) : undefined;
        const conversation = archivedSession || extractConversation(messages);
        if (!conversation) return;

        client.fireAndForget<BeforeCompactionResponse>(
          "/runtime/before-compaction",
          {
            ...buildRuntimeEnvelope(event, config.graphId),
            message_count: event.messageCount ?? null,
            compacting_count: event.compactingCount ?? null,
            token_count: event.tokenCount ?? null,
            conversation,
          },
          config.reflectionTimeoutMs,
          log,
          "before_compaction",
        );
      });
    }

    api.registerCommand({
      name: "langgraph",
      description: "Show LangGraph orchestrator plugin status",
      async handler() {
        const result = await withGracefulFailure(async () => {
          const health = await client.request<HealthResponse>("/health", "GET", undefined, config.requestTimeoutMs);
          const lines = [
            "LangGraph Orchestrator Status",
            `  Enabled:      ${config.enabled ? "ON" : "OFF"}`,
            `  Endpoint:     http://${config.apiHost}:${config.apiPort}`,
            `  Graph:        ${config.graphId}`,
            `  AutoRetrieve: ${config.autoRetrieve ? "ON" : "OFF"}`,
            `  AutoReflect:  ${config.autoReflect ? "ON" : "OFF"}`,
            `  Archive:      ${config.archiveOnCompaction ? "ON" : "OFF"}`,
            `  Health:       ${String(health.status ?? "unknown")}`,
          ];
          return { text: lines.join("\n") };
        }, log, "command");

        return result ?? { text: `LangGraph orchestrator error: runtime unavailable at http://${config.apiHost}:${config.apiPort}` };
      },
    });

    api.registerService({
      id: "langgraph-orchestrator",
      async start() {
        await withGracefulFailure(async () => {
          const health = await client.request<HealthResponse>("/health", "GET", undefined, config.requestTimeoutMs);
          log.info(`langgraph-orchestrator: service started — ${JSON.stringify(health)}`);
        }, log, "service_start");
      },
      stop() {
        log.info("langgraph-orchestrator: service stopped.");
      },
    });

    log.info("langgraph-orchestrator: plugin hooks registered.");
  },
});
