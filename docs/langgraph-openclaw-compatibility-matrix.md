# LangGraph × OpenClaw Compatibility Matrix

This file records tested version pairs for the LangGraph ↔ OpenClaw integration layer.

## Status legend

- `stable` — validated and suitable for `main`
- `testing` — under active sync validation
- `blocked` — known incompatibility exists
- `retired` — previously supported but no longer maintained

## Version pairs

| Integration line | OpenClaw | LangGraph | Plugin contract | Runtime contract | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| v0.1.x | TBD | TBD | v1 | v1 | testing | Fill after first explicit validation pass |

## Validation checklist per row

For a row to be marked `stable`, verify all of the following:

- plugin loads successfully
- `/health` succeeds against the runtime
- `before_agent_start` contract passes
- `agent_end` contract passes
- `before_compaction` contract passes
- graceful degradation behavior is confirmed
- docs match actual config and endpoint shape

## Current contract versions

### Plugin-side lifecycle contract

- `before_agent_start`
- `agent_end`
- `before_compaction`

### Runtime endpoints

- `GET /health`
- `POST /runtime/before-agent-start`
- `POST /runtime/agent-end`
- `POST /runtime/before-compaction`

## Upgrade notes template

When adding a new tested row, include notes like:

- what changed upstream
- whether any payload shape changed
- whether any config compatibility shim was added
- whether any tests were added or updated
- whether rollout should stay staged

## Example entry format

```markdown
### v0.1.x validation notes

- OpenClaw: <version>
- LangGraph: <version>
- Result: testing / stable / blocked
- Notes:
  - <note 1>
  - <note 2>
```

