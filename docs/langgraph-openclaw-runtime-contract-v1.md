# LangGraph × OpenClaw Runtime Contract v1

## Purpose

This document defines the first stable runtime contract between:

- the **OpenClaw plugin bridge** and
- the **LangGraph orchestration runtime**

The goal is to keep the contract narrow, lifecycle-driven, and safe to degrade when the LangGraph runtime is unavailable.

## Design principles

1. **OpenClaw remains the host authority**
   - messaging
   - tool execution
   - approvals
   - sandbox boundaries
   - final reply delivery

2. **LangGraph remains advisory/orchestration-oriented**
   - retrieval hints
   - planning hints
   - reflection scheduling
   - checkpoint/archive coordination

3. **Failure must degrade safely**
   - runtime unavailability must not block the main reply path
   - synchronous endpoints should be bounded by short timeouts
   - post-turn work may be async / fire-and-forget

## Versioning

Current contract version: **v1**

This version defines 4 runtime endpoints:

- `GET /health`
- `POST /runtime/before-agent-start`
- `POST /runtime/agent-end`
- `POST /runtime/before-compaction`

## Endpoint overview

| Endpoint | Timing | Blocking | Purpose |
| --- | --- | --- | --- |
| `GET /health` | startup / command checks | short sync | runtime reachability |
| `POST /runtime/before-agent-start` | before OpenClaw agent run | short sync | hints and optional prepend context |
| `POST /runtime/agent-end` | after turn completion | usually async-tolerant | turn event ingestion and reflection scheduling |
| `POST /runtime/before-compaction` | before transcript compaction | short sync | checkpoint/archive coordination |

## Common request conventions

### Required identifiers

Every lifecycle request should carry the same core identity fields where available:

- `graph_id`
- `session_id`
- `channel`
- `user_id`

`session_id`, `channel`, and `user_id` may be `null` when unavailable.

### Metadata

All lifecycle requests may include:

```json
{
  "metadata": {
    "key": "value"
  }
}
```

This bag is intentionally extensible and should only contain non-authoritative auxiliary context.

## 1. Health endpoint

### Request

```http
GET /health
```

### Response

```json
{
  "status": "ok",
  "details": {
    "runtime": "langgraph",
    "version": "v1"
  }
}
```

### Semantics

- used for plugin startup checks
- used by `/langgraph` command/status flow
- should return quickly
- should not require session context

## 2. Before-agent-start

### Purpose

Called immediately before OpenClaw starts the agent turn.

This endpoint lets LangGraph provide:

- planning hints
- retrieval hints already transformed into text
- optional prepend context
- lightweight orchestration state hints

### Request shape

```json
{
  "graph_id": "default",
  "session_id": "session-123",
  "channel": "telegram",
  "user_id": "user-456",
  "query": "continue the langgraph integration design",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "metadata": {
    "source": "openclaw-plugin"
  }
}
```

### Response shape

```json
{
  "prepend_context": "Previously established direction: keep OpenClaw as execution host.",
  "planning_hints": [
    "Treat LangGraph as orchestration, not tool executor.",
    "Prefer graceful degradation if runtime state is incomplete."
  ],
  "retrieval_metadata": {
    "source": "langgraph-runtime",
    "policy": "lightweight"
  }
}
```

### Field semantics

#### `prepend_context`

- optional text prepended into the agent context
- should be concise
- should be treated as context, not as direct tool instructions

#### `planning_hints`

- optional array of short hints
- advisory only
- plugin layer may wrap/sanitize before injection

#### `retrieval_metadata`

- optional structured bag for diagnostics or future policy use
- should not be required for main-path correctness

### Blocking behavior

- synchronous
- bounded timeout
- on timeout or failure: plugin logs warning and continues without hints

## 3. Agent-end

### Purpose

Called after a turn completes.

This endpoint gives LangGraph a chance to:

- ingest turn outcome
- update orchestration state
- schedule reflection
- write summaries/checkpoints in its own runtime domain

### Request shape

```json
{
  "graph_id": "default",
  "session_id": "session-123",
  "channel": "telegram",
  "user_id": "user-456",
  "success": true,
  "conversation": "user: ...\nassistant: ...",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "tool_outcomes": {
    "count": 1
  },
  "metadata": {
    "source": "openclaw-plugin"
  }
}
```

### Response shape

```json
{
  "event_written": true,
  "summary_written": false,
  "reflection_scheduled": true
}
```

### Field semantics

#### `success`

Whether OpenClaw considers the turn successful enough to finalize.

#### `conversation`

A flattened textual conversation summary for lightweight runtime ingestion.

#### `messages`

Optional richer message payload if the runtime wants structured post-turn inspection.

#### `tool_outcomes`

Optional structured outcome bag for future orchestration logic.

### Blocking behavior

- should usually be treated as async-tolerant
- plugin may use fire-and-forget semantics
- runtime failure must not retroactively fail the user-visible turn

## 4. Before-compaction

### Purpose

Called before OpenClaw compacts or trims conversation state.

This endpoint lets LangGraph preserve high-value state before short-term context is lost.

### Request shape

```json
{
  "graph_id": "default",
  "session_id": "session-123",
  "channel": "telegram",
  "user_id": "user-456",
  "conversation": "user: ...\nassistant: ...",
  "message_count": 42,
  "compacting_count": 18,
  "token_count": 12000,
  "metadata": {
    "source": "openclaw-plugin"
  }
}
```

### Response shape

```json
{
  "checkpoint_written": true,
  "archive_written": true
}
```

### Field semantics

#### `conversation`

The compaction-bound transcript slice or summary the runtime may archive/checkpoint against.

#### `message_count`

Total messages currently in scope, if known.

#### `compacting_count`

How many messages are about to be compacted, if known.

#### `token_count`

Approximate token size, if available.

### Blocking behavior

- synchronous but bounded
- if unavailable, compaction must still proceed
- runtime failure should only produce warning-level degradation

## Error handling contract

### Runtime unavailable

Expected plugin behavior:

- log warning
- skip LangGraph enrichment
- continue OpenClaw lifecycle normally

### Non-2xx response

Expected plugin behavior:

- treat as runtime failure for that hook
- log endpoint-specific warning
- do not crash the host path

### Malformed response payload

Expected plugin behavior:

- ignore invalid optional fields
- preserve host execution path
- log enough detail for diagnosis

## Timeout guidance

Suggested defaults:

- `before-agent-start`: short timeout (for example ~8s)
- `agent-end`: longer async-tolerant timeout (for example ~15s)
- `before-compaction`: short timeout
- `health`: very short timeout

The exact values may evolve, but the principle is stable:

- pre-turn and pre-compaction paths stay tight
- post-turn async work gets a slightly larger budget

## Non-goals in v1

This contract intentionally does **not** define:

- direct LangGraph tool execution through OpenClaw
- approval bypasses
- final-reply authorship transfer
- memory-backend-specific payload contracts
- shared package extraction for plugin/runtime types

## Validation expectations

A candidate implementation of this contract should be verified with at least:

1. plugin-host smoke test
2. runtime client mock test
3. helper sanitization/injection-safety tests
4. real runtime `/health` check
5. real runtime `before-agent-start` round-trip
6. degradation behavior when runtime is offline

## Next likely extensions after v1

Possible v2+ additions, only after the basic contract proves stable:

- explicit `contract_version` field in requests/responses
- structured checkpoint payloads
- richer retrieval provenance
- reflection job identifiers
- optional restore/checkpoint-read endpoint
