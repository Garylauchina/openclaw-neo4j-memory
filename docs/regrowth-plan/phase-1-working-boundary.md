# Phase 1 Working Boundary

This file defines what the new branch should keep in focus, what it should ignore for now, and what should be deferred until after the minimal kernel is runnable.

## Purpose

Protect the new regrowth line from being pulled back into the full architecture/crystal/governance expansion too early.

## Keep in active focus

These are the files and concerns Phase 1 should actively work with.

### Planning docs
- `docs/regrowth-plan/phase-1-mvp-spec.md`
- `docs/regrowth-plan/phase-1-merge-task-breakdown.md`
- `docs/regrowth-plan/phase-1-start-checklist.md`
- `docs/regrowth-plan/baseline-archival-and-new-branch-workflow.md`
- `docs/regrowth-plan/new-branch-implementation-plan.md`
- `docs/regrowth-plan/phase-1-working-boundary.md`

### Code concerns that belong to Phase 1
- raw memory write/read path
- minimal entity extraction
- minimal relation extraction
- retrieval scoring and top-k selection
- prompt-level write/retrieve/inject rules
- lightweight async consolidation

### Data/object concerns that belong to Phase 1
- `RawMemory`
- `Entity`
- `Relation`
- `RetrievedMemory` / `MemorySnippet`
- optional `ConsolidatedNote`

## Use only as reference/baseline

These should be treated as idea sources or comparison material, not as immediate implementation targets.

### Architecture / crystal / regrowth docs
- `docs/architecture-mainline-draft.md`
- `docs/architecture-regrowth-fidelity-draft.md`
- `docs/crystal-system-prototype-phase-closure.md`
- `docs/adapter-layer-emergence-v1.md`
- `docs/adapter-definition-pass-v1.md`
- `docs/multi-crystal-*.md`
- `docs/*regeneration*.md`
- `docs/*crystal*.md`
- `docs/*compatibility*.md`
- `docs/*update-governance*.md`
- `docs/*verification*.md`

### Experiment assets and tmp outputs
- everything under `tmp/` related to crystal drift, recursive crystal discovery, regrowth, review, and pressure tests
- experiment JSON/MD assets that document the prior line

These are valuable as baseline memory, but should not define Phase 1 scope.

## Explicitly ignore in Phase 1 implementation

Do not actively implement, extend, or reintroduce these in Phase 1.

- belief governance layers
- world model layers
- root axiom layers
- structural debt objects
- pruning economy systems
- self-modification protocols
- crystal transfer systems
- adapter systems
- compatibility composition systems
- verification governance layers
- update-governance layers
- operating-system style governance metaphors as implementation drivers
- predictive prophylaxis systems
- full conflict arbitration stacks

## Defer until Phase 2 or later

These may become important later, but are intentionally deferred.

### Defer to Phase 2
- provenance strengthening
- hypothesis vs stable distinction
- bounded validation layer
- stronger retrieval routing
- more careful revision/update handling

### Defer beyond Phase 2 unless strongly justified
- crystal generation
- transfer/regrowth package design
- adapter emergence work
- ecology/stress orchestration
- root-constraint / axiom revision systems
- self-evolution governance kernels

## Practical working rule

When making a Phase 1 change, ask:
1. Does this help the minimal memory loop run?
2. Does this help prompt-level memory orchestration stay useful and bounded?
3. Could this be postponed without breaking the MVP?

If the answer to (3) is yes, postpone it.

## Merge hygiene rule

A Phase 1 merge should mostly touch:
- the small set of implementation files needed for the current merge goal
- the regrowth-plan docs
- minimal verification artifacts

A Phase 1 merge should not become a cleanup sweep of the whole repository.

## Compression trigger

Stop and compress before continuing if:
- a merge starts introducing governance vocabulary faster than runnable behavior
- new objects appear without improving write/retrieve/inject behavior
- the implementation starts depending on crystal, axiom, or operating-system abstractions
- the branch begins to resemble the baseline architecture line more than a minimal kernel
