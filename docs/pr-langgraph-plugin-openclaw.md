# PR Draft — LangGraph as OpenClaw Plugin

## Summary

This PR introduces a first-pass **LangGraph orchestrator plugin** for OpenClaw.

The goal is to integrate LangGraph at the **plugin/runtime lifecycle level** instead of treating it as a one-off tool call. In this shape, OpenClaw keeps control of session routing, approvals, sandboxing, and execution, while LangGraph becomes the orchestration layer for:

- retrieval before the agent starts
- async reflection after a turn completes
- pre-compaction checkpoint / archive coordination
- health-checked runtime communication over HTTP

## What changed

### New plugin scaffold

Added a new plugin package under:

- `plugins/langgraph-orchestrator/`

Key files:

- `index.ts` — plugin entry and hook wiring
- `openclaw.plugin.json` — plugin manifest and config schema
- `package.json` — package metadata
- `contracts.ts` — typed runtime request / response contracts
- `runtime-helpers.js` — reusable helper logic for extraction and graceful downgrade
- `runtime-client.js` — reusable HTTP client for LangGraph runtime calls

### Hook integration

The plugin now wires into these OpenClaw lifecycle hooks:

- `before_agent_start`
- `agent_end`
- `before_compaction`

### Command / service integration

Also added:

- `/langgraph` command for runtime status
- plugin service startup health check

## Runtime contract

Current expected LangGraph runtime endpoints:

- `POST /runtime/before-agent-start`
- `POST /runtime/agent-end`
- `POST /runtime/before-compaction`
- `GET /health`

## Design boundary

### OpenClaw remains responsible for

- inbound / outbound messaging
- session routing and ownership
- approvals and permission checks
- actual tool execution
- sandbox / host boundaries
- final reply delivery

### LangGraph plugin becomes responsible for

- retrieval requests
- planning hint injection
- turn-level reflection scheduling
- checkpoint/archive coordination before compaction

## Graceful degradation behavior

If the LangGraph runtime is unavailable:

- do **not** block the main reply path
- do **not** fail the whole agent turn
- warn through plugin logging
- return control back to OpenClaw
- keep command-level diagnostics available

This downgrade path is intentionally part of the design, not an afterthought.

## Tests

### Helper-level tests

```bash
node --test plugins/langgraph-orchestrator/runtime-helpers.test.mjs
```

Covers:

- latest-user-query extraction
- conversation extraction
- bounded query sanitization
- planning-hint formatting
- runtime envelope construction
- graceful downgrade warning behavior

### Mock runtime smoke tests

```bash
node --test plugins/langgraph-orchestrator/runtime-client.test.mjs
```

Covers:

- successful `before-agent-start` round-trip against a mock LangGraph HTTP server
- successful async `agent-end` fire-and-forget logging path
- non-2xx runtime failures surfacing correctly

### Combined run used for verification

```bash
node --test \
  plugins/langgraph-orchestrator/runtime-helpers.test.mjs \
  plugins/langgraph-orchestrator/runtime-client.test.mjs
```

Result at validation time: **9/9 passing**.

## Risks / limitations

### 1. Plugin scaffold only

This PR intentionally stops at a **runtime integration scaffold**. It does not yet ship a production LangGraph service implementation.

### 2. No direct tool-planning execution

The plugin does not let LangGraph execute OpenClaw tools directly. That boundary remains in OpenClaw.

### 3. Type contracts are local for now

The request / response contracts are defined in this repo, but not yet extracted into a shared package consumed by both plugin and runtime service.

### 4. No full plugin registration smoke test yet

We now have mock HTTP smoke coverage, but not a full plugin-host integration harness.

## Rollout plan

### Phase 1 — merge scaffold behind plugin enablement

- keep plugin disabled unless explicitly configured
- verify `/langgraph` health command against a real runtime
- validate logs and downgrade behavior in a dev environment

### Phase 2 — connect to a real LangGraph runtime

- implement runtime endpoints
- validate context injection semantics
- validate reflection payload shape and storage behavior

### Phase 3 — staged production use

- enable for low-risk sessions first
- monitor startup health warnings / timeout rates
- review prompt injection behavior and reflection latency

### Phase 4 — broader orchestration authority

Future work only after stability is proven:

- richer planning hints
n- optional structured action proposals
- shared package for runtime contracts
- stronger integration tests with plugin host lifecycle

## Commit stack in this branch

- `a8b5639` — scaffold langgraph orchestrator plugin
- `43c9a54` — add langgraph runtime contracts and degradation tests
- `6230a41` — wire plugin to shared contracts and helpers
- `70f6515` — add mock langgraph runtime smoke coverage

## Suggested reviewer focus

- plugin/runtime boundary correctness
- graceful degradation safety
- future compatibility of runtime endpoint contracts
- whether the rollout shape is conservative enough
