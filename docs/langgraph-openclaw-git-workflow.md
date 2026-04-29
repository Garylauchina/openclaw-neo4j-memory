# LangGraph × OpenClaw Git Workflow

## Goal

This workflow keeps the LangGraph ↔ OpenClaw integration moving while both upstream projects continue to evolve.

It is optimized for:

- small reviewable PRs
- explicit compatibility validation
- low-risk upstream syncing
- clear separation between stable work and exploratory work

## Repository lanes

Use the repository as an integration project with three logical lanes:

1. **OpenClaw adapter lane**
   - plugin entry
   - hook wiring
   - config handling
   - host-specific degradation behavior

2. **LangGraph runtime lane**
   - runtime client
   - runtime contract
   - checkpoint / reflection / orchestration payloads

3. **Compatibility lane**
   - version matrix
   - sync branches
   - smoke tests
   - upgrade notes

## Branch model

### Long-lived branches

- `main`
  - latest validated integration line
  - safe default for consumers

- `next`
  - staging branch for upcoming validated work
  - optional but recommended if upstream sync work becomes frequent

### Short-lived branches

#### Feature branches

- `feat/plugin-<topic>`
- `feat/runtime-<topic>`
- `feat/contract-<topic>`

Examples:

- `feat/plugin-before-agent-start`
- `feat/runtime-health-endpoint`
- `feat/contract-before-compaction`

#### Fix branches

- `fix/openclaw-compat-<topic>`
- `fix/langgraph-compat-<topic>`
- `fix/runtime-<topic>`

Examples:

- `fix/openclaw-compat-pluginconfig`
- `fix/langgraph-compat-checkpoint-payload`

#### Test branches

- `test/<topic>`

Examples:

- `test/plugin-host-smoke`
- `test/compaction-contract`

#### Docs branches

- `docs/<topic>`

Examples:

- `docs/langgraph-compat-policy`
- `docs/release-matrix-template`

#### Upstream sync branches

- `sync/openclaw-<version>`
- `sync/langgraph-<version>`
- `sync/openclaw-<version>-langgraph-<version>`

Examples:

- `sync/openclaw-0.9.4`
- `sync/langgraph-0.2.61`
- `sync/openclaw-0.9.4-langgraph-0.2.61`

## PR types

### Type A — Adapter PRs

Changes one side of the boundary only.

Examples:

- read new OpenClaw config field
- adjust LangGraph runtime payload key
- improve degradation logging

### Type B — Contract PRs

Changes the integration contract itself.

Examples:

- add a field to `/runtime/before-agent-start`
- change `before_compaction` archive payload shape

These PRs must update tests and docs together.

### Type C — Sync PRs

Used when adopting a new upstream version.

Examples:

- support new OpenClaw plugin API behavior
- support new LangGraph checkpoint semantics

These PRs should avoid unrelated cleanup.

### Type D — Docs/Test PRs

No behavior change.

Examples:

- compatibility matrix update
- smoke test extension
- release notes

## Normal delivery flow

### Small feature flow

1. branch from `main`
2. implement one narrow change
3. run local contract tests
4. open PR
5. merge after validation

### Upstream sync flow

1. branch from `main` into `sync/...`
2. update one upstream target
3. run full compatibility suite
4. record outcomes in compatibility docs
5. merge only if validated

### Exploratory flow

If behavior is not yet stable:

1. branch from `main`
2. keep work behind docs or optional config
3. merge into `next` first if needed
4. promote to `main` only after the contract settles

## Required checks before merge

### For adapter / contract changes

Run at least:

```bash
node --test \
  plugins/langgraph-orchestrator/runtime-helpers.test.mjs \
  plugins/langgraph-orchestrator/runtime-client.test.mjs \
  plugins/langgraph-orchestrator/plugin-host-smoke.test.mjs
```

### For upstream sync branches

In addition to the above, verify:

- plugin still loads
- runtime health still works
- `before_agent_start` still accepts and returns the expected shape
- `agent_end` still degrades safely on failure
- `before_compaction` still returns archive/checkpoint output compatibly

## Commit discipline

Each commit should ideally do one thing.

Good examples:

- `feat: add before-compaction runtime contract`
- `fix: support updated openclaw hook payload`
- `test: add langgraph health-check smoke case`
- `docs: record supported version pair`

Avoid commits that mix:

- runtime contract changes
- upstream version sync
- docs rewrites
- unrelated refactors

## Rebase / merge guidance

### Prefer rebase for short-lived branches

Use rebase to keep the branch current when the change is small and linear.

### Prefer squash merge for PRs

Squash merge is a good default for this project because:

- most PRs should answer one focused question
- it keeps the integration history readable
- it reduces noise from temporary fixup commits

## When to cut a release tag

Tag when all of the following are true:

1. a version pair is explicitly validated
2. contract docs match implementation
3. smoke tests pass
4. known limitations are documented

Suggested tag style:

- `langgraph-openclaw-v0.1.0`
- `langgraph-openclaw-v0.1.1`

## Operational habits

### Do

- isolate upstream syncs in dedicated branches
- document supported version pairs
- keep OpenClaw-facing and LangGraph-facing code in narrow boundary layers
- update docs when a contract changes

### Do not

- mix OpenClaw and LangGraph upgrades in an unrelated feature PR
- redefine `main` around untested upstream versions
- let runtime failures block the main reply path
- hide breaking contract changes inside refactors

## Suggested next additions

After adopting this workflow, add:

1. `docs/langgraph-openclaw-compatibility-matrix.md`
2. a small script that runs the compatibility suite
3. a PR template section asking whether the change affects:
   - OpenClaw boundary
   - LangGraph boundary
   - compatibility matrix
   - docs/tests only

