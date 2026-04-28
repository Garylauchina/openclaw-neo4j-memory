# LangGraph Orchestrator Plugin

This plugin lets a LangGraph runtime enrich OpenClaw through plugin lifecycle hooks.

## Runtime endpoints

- `POST /runtime/before-agent-start`
- `POST /runtime/agent-end`
- `POST /runtime/before-compaction`
- `GET /health`

## Local smoke test

```bash
node --test plugins/langgraph-orchestrator/runtime-helpers.test.mjs
```

## Degradation rule

If the LangGraph runtime is unavailable, the plugin must warn and return control to OpenClaw without blocking the main reply path.
