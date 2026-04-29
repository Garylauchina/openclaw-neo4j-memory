# LangGraph as OpenClaw Plugin

## Scope

This branch adds a first-pass plugin scaffold for integrating LangGraph into OpenClaw through plugin lifecycle hooks rather than a one-off tool call.

## What is included now

- `plugins/langgraph-orchestrator/index.ts`
  - config schema
  - LangGraph runtime HTTP client
  - `before_agent_start` hook
  - `agent_end` hook
  - `before_compaction` hook
  - `/langgraph` status command
  - plugin service startup health check
- `plugins/langgraph-orchestrator/openclaw.plugin.json`
- `plugins/langgraph-orchestrator/package.json`

## Intended runtime contract

### `POST /runtime/before-agent-start`
Returns retrieval context and optional planning hints.

### `POST /runtime/agent-end`
Persists the completed turn and optionally schedules reflection.

### `POST /runtime/before-compaction`
Archives or checkpoints session state before compaction.

### `GET /health`
Used for startup and manual diagnostics.

## Design boundary

OpenClaw still owns:

- channels and sessions
- approvals and tool execution
- sandbox / host boundaries
- final reply delivery

LangGraph plugin owns:

- retrieval requests
- planning hint injection
- reflection scheduling
- pre-compaction checkpoint coordination

## Next implementation steps

1. add typed request / response contracts shared with the LangGraph service
2. add graceful-degradation tests
3. optionally add tool-planning proposal payloads from LangGraph to OpenClaw
4. decide whether reflection runs in-plugin or via OpenClaw task/sub-agent scheduling
