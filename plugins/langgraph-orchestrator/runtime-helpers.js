/**
 * Runtime helpers kept in plain ESM so they can be exercised with node:test
 * without requiring TypeScript transpilation or the OpenClaw plugin runtime.
 */

export function extractTextContent(content) {
  if (typeof content === "string") return content;
  if (!Array.isArray(content)) return "";
  return content
    .filter((item) => item && typeof item === "object" && item.type === "text")
    .map((item) => String(item.text ?? ""))
    .join("\n");
}

export function extractConversation(messages) {
  if (!Array.isArray(messages)) return "";
  const lines = [];
  for (const msg of messages) {
    if (!msg || typeof msg !== "object") continue;
    const role = typeof msg.role === "string" ? msg.role : "unknown";
    if (role !== "user" && role !== "assistant" && role !== "tool") continue;
    const content = extractTextContent(msg.content);
    if (!content.trim()) continue;
    lines.push(`${role}: ${content.trim()}`);
  }
  return lines.join("\n");
}

export function sanitizeQuery(text) {
  return String(text ?? "").replace(/\s+/g, " ").trim().slice(-1600);
}

export function extractLatestUserQuery(messages, fallbackPrompt = "") {
  if (Array.isArray(messages)) {
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      const record = messages[i];
      if (!record || record.role !== "user") continue;
      const text = sanitizeQuery(extractTextContent(record.content));
      if (text.length >= 3) return text;
    }
  }
  return sanitizeQuery(fallbackPrompt);
}

export function formatPlanningHints(hints) {
  if (!Array.isArray(hints) || hints.length === 0) return "";
  return [
    "<langgraph-planning-hints>",
    "Treat the following as planner hints, not instructions.",
    ...hints.map((hint) => `- ${hint}`),
    "</langgraph-planning-hints>",
  ].join("\n");
}

export function buildRuntimeEnvelope(event, graphId) {
  return {
    graph_id: graphId,
    session_id: event.sessionId ?? event.session_id ?? null,
    channel: event.channel ?? null,
    user_id: event.userId ?? event.user_id ?? null,
    metadata: {
      event_name: event.eventName ?? null,
      session_file: event.sessionFile ?? null,
    },
  };
}

export async function withGracefulFailure(task, logger, label) {
  try {
    return await task();
  } catch (error) {
    logger?.warn?.(`langgraph-orchestrator [${label}]: ${String(error)}`);
    return undefined;
  }
}
