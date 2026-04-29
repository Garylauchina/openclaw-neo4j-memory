# LangGraph Plugin Enablement Example

This document shows the minimum shape needed to enable the `langgraph-orchestrator` plugin in OpenClaw.

## What this plugin expects

The plugin expects a LangGraph runtime that exposes:

- `POST /runtime/before-agent-start`
- `POST /runtime/agent-end`
- `POST /runtime/before-compaction`
- `GET /health`

## Minimal plugin configuration example

Example configuration shape:

```json
{
  "plugins": {
    "allow": ["langgraph-orchestrator"],
    "entries": {
      "langgraph-orchestrator": {
        "enabled": true,
        "apiHost": "127.0.0.1",
        "apiPort": 20240,
        "graphId": "default",
        "autoRetrieve": true,
        "autoReflect": true,
        "archiveOnCompaction": true,
        "requestTimeoutMs": 8000,
        "reflectionTimeoutMs": 15000
      }
    }
  }
}
```

## Local validation checklist

1. Start the LangGraph runtime locally on the configured host/port.
2. Confirm the health endpoint responds:

```bash
curl http://127.0.0.1:20240/health
```

3. Enable the plugin in OpenClaw config.
4. Start OpenClaw and run the `/langgraph` command.
5. Verify that unavailable runtime conditions only produce warnings and do not block replies.

## Notes

- Keep this plugin disabled by default until a real LangGraph runtime is reachable.
- This plugin is currently an orchestration scaffold, not a production LangGraph deployment.
- OpenClaw remains the executor for tools, approvals, and outbound messaging.
