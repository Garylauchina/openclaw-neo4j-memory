# LangGraph × OpenClaw Compatibility Policy

## Purpose

This document defines how to evolve a LangGraph ↔ OpenClaw integration layer while both upstream projects continue to change.

The goal is to keep the integration stable without forcing the project to chase every upstream release immediately.

## Core strategy

Treat this project as an **integration layer**, not as a mirror of either upstream.

- **OpenClaw** remains the host runtime and execution boundary.
- **LangGraph** remains the orchestration runtime.
- **This repo** owns the compatibility contract between them.

That means the primary artifact of this project is:

- plugin/runtime lifecycle contracts
- adapter boundaries
- compatibility-tested version combinations
- smoke tests and degradation behavior

## Compatibility model

The `main` branch must track a **known-good version pair**, not `latest` from both sides.

Example:

| Integration layer | OpenClaw | LangGraph | Status |
| --- | --- | --- | --- |
| v0.1.x | pinned tested version | pinned tested version | stable |
| v0.2.x | next candidate | next candidate | testing |

### Rules

1. `main` only carries combinations that were explicitly tested.
2. Upstream updates land in dedicated sync branches first.
3. A new upstream version is not adopted until contract tests pass.
4. Experimental support may live in `next`, but should not redefine the stable matrix until validated.

## Branch policy

### Stable branches

- `main` — latest validated integration line
- `next` — upcoming integration line / staging branch

### Upstream sync branches

- `sync/openclaw-<version>`
- `sync/langgraph-<version>`
- `sync/openclaw-<version>-langgraph-<version>` when both need coordinated validation

### Feature / fix branches

- `feat/plugin-hook-<topic>`
- `feat/runtime-contract-<topic>`
- `fix/openclaw-compat-<topic>`
- `fix/langgraph-compat-<topic>`
- `docs/<topic>`
- `test/<topic>`

## Adapter boundaries

Do not scatter upstream-specific calls across the codebase.

### OpenClaw-facing boundary

Keep OpenClaw-specific logic concentrated in a thin adapter layer, for example:

- plugin entry
- lifecycle hook wiring
- config reading
- context injection adaptation
- graceful degradation handling

### LangGraph-facing boundary

Keep LangGraph-specific logic concentrated in a runtime adapter layer, for example:

- runtime client
- request/response translation
- state checkpoint payload conversion
- reflection scheduling requests

### Why this matters

When OpenClaw or LangGraph changes upstream, most compatibility work should stay inside one boundary layer instead of leaking across the entire project.

## Release policy

### Stable releases

A stable release should document:

- supported OpenClaw version
- supported LangGraph version
- supported runtime endpoints
- known limitations
- required smoke tests

### Candidate releases

If upstream drift is being evaluated, publish it as a candidate line first:

- tag or branch it as testing
- do not silently replace the stable matrix
- record incompatible behavior before promotion

## Upstream sync policy

Do not continuously chase head on both upstreams.

Instead, use a **sync window**.

Recommended cadence:

- evaluate upstream changes weekly or biweekly
- open a dedicated sync branch
- run contract tests
- merge only if the validated pair remains healthy

### OpenClaw changes likely to matter

- plugin API shape
- lifecycle hook names or payloads
- config shape
- session payload shape
- compaction timing / semantics

### LangGraph changes likely to matter

- runtime server pattern
- graph/state interfaces
- checkpoint APIs
- async orchestration behavior
- dependency / packaging changes

## Required validation gates

Every upstream sync branch should run the smallest meaningful compatibility suite.

Minimum gates:

1. plugin load / registration smoke test
2. runtime health check
3. `before_agent_start` contract test
4. `agent_end` contract test
5. `before_compaction` contract test
6. graceful degradation test when runtime is unavailable

If one of these fails, the branch is not ready for promotion to `main`.

## Change classification

### Safe to merge independently

- docs only
- additional tests
- logging improvements
- non-breaking internal refactors

### Requires compatibility verification

- plugin lifecycle hook changes
- config parsing changes
- request/response schema changes
- LangGraph runtime endpoint changes
- timeout / degradation behavior changes

### Requires a sync branch

- OpenClaw upstream upgrade
- LangGraph upstream upgrade
- simultaneous upgrade on both sides

## Commit and PR guidance

### Commit style

Prefer narrow commits:

- `feat: add before-agent-start contract adapter`
- `fix: support openclaw pluginConfig in adapter`
- `test: add compaction compatibility smoke test`
- `docs: define langgraph-openclaw compatibility policy`

### PR style

A PR should answer one main question:

- Does it change the OpenClaw boundary?
- Does it change the LangGraph boundary?
- Does it change the compatibility matrix?
- Does it only improve docs/tests?

Avoid mixing all four in one PR.

## Roadmap sequencing

Recommended order:

### Phase 1 — integration scaffold

- plugin hook wiring
- runtime client
- health check
- graceful degradation

### Phase 2 — contract stabilization

- fixed runtime endpoints
- typed payloads
- smoke tests for each lifecycle hook

### Phase 3 — upstream drift management

- compatibility matrix
- sync branches
- repeatable contract verification

### Phase 4 — advanced orchestration

- richer planning hints
- checkpoint restore
- reflection governance
- optional memory backends

## Non-goals for now

This policy intentionally does **not** require:

- tight coupling to a specific memory backend
- direct tool execution by LangGraph
- OpenClaw core changes beyond plugin/runtime integration needs
- immediate adoption of every upstream release

## Recommended next artifacts

After this policy, the project should add:

1. `docs/langgraph-openclaw-git-workflow.md`
2. `docs/langgraph-openclaw-compatibility-matrix.md`
3. a small CI or local verification script for the contract gates

