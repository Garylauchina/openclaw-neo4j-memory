# Phase 3 Working Boundary

This file defines what Phase 3 should actively improve, what it should use only as reference, and what it must continue to defer.

## Purpose

Protect Phase 3 from turning note quality refinement into a heavy governance or abstraction layer.

## Keep in active focus

### Planning docs
- `docs/regrowth-plan/phase-2-closeout-note.md`
- `docs/regrowth-plan/phase-2-freeze-summary.md`
- `docs/regrowth-plan/phase-3-scope-spec.md`
- `docs/regrowth-plan/phase-3-merge-task-breakdown.md`
- `docs/regrowth-plan/phase-3-working-boundary.md`

### Code concerns that belong to Phase 3
- stronger note distillation
- structured note types
- better repeated-evidence distillation
- retrieval-aware note refinement
- bounded memory quality signals

### Data/object concerns that belong to Phase 3
- `ConsolidatedNote`
- bounded note/product type set
- lightweight note-quality signals
- repeated-evidence aggregation behavior
- retrieval-aware note refinement behavior

## Use only as reference/baseline

### The older heavy line
Treat the architecture/crystal/governance line as reference only.
Use it for contrast, not as immediate scope.

### Why reference only
Phase 3 is still a bounded quality-refinement phase.
It should not absorb crystal, axiom, debt, or operating-system architecture ideas as direct implementation targets.

## Explicitly ignore in Phase 3 implementation

Do not actively implement or reintroduce these in Phase 3:
- root axiom systems
- structural debt systems
- self-modification protocols
- crystal generation/transfer implementation
- adapter systems
- operating-system style governance layers
- predictive prophylaxis systems
- full conflict arbitration kernels
- autonomous self-evolution controllers
- large scoring economies around memory quality

## Defer until Phase 4 or later

### Possible Phase 4 topics
- stronger memory products
- stronger routing if directly justified
- the first carefully bounded governance layer

### Later than Phase 4 unless strongly justified
- root-constraint / axiom systems
- debt/pruning economies
- self-evolution control loops
- crystal-transfer implementation layers
- operating-system style architectural metaphors as implementation drivers

## Practical working rule

When making a Phase 3 change, ask:
1. Does this improve the quality of memory products?
2. Does this improve repeated-evidence handling or retrieval usefulness?
3. Could this be postponed without harming the Phase 3 target?

If the answer to (3) is yes, postpone it.

## Merge hygiene rule

A Phase 3 merge should mostly touch:
- minimal implementation files in the lightweight kernel line
- regrowth-plan docs
- minimal verification artifacts

A Phase 3 merge should not become a broad abstraction or vocabulary expansion sweep.

## Compression trigger

Stop and compress before continuing if:
- governance or ontology vocabulary grows faster than note quality improves
- new object families appear without improving note usefulness
- implementation starts depending on root-constraint, debt, or self-modification abstractions
- Phase 3 begins to resemble the older heavy line instead of a bounded note-quality stage
