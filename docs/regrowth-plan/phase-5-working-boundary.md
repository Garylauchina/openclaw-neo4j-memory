# Phase 5 Working Boundary

This file defines what Phase 5 should actively improve, what it should use only as reference, and what it must continue to defer.

## Purpose

Protect Phase 5 from turning routing-strengthening into a heavy governance or abstraction layer.

## Keep in active focus

### Planning docs
- `docs/regrowth-plan/phase-4-closeout-note.md`
- `docs/regrowth-plan/phase-4-freeze-summary.md`
- `docs/regrowth-plan/phase-5-scope-spec.md`
- `docs/regrowth-plan/phase-5-merge-task-breakdown.md`
- `docs/regrowth-plan/phase-5-working-boundary.md`

### Code concerns that belong to Phase 5
- stronger mixed retrieval routing
- better product/raw-memory coordination rules
- better mode-aware retrieval behavior
- better inspectable routing reasons
- bounded routing metadata/signals

### Data/object concerns that belong to Phase 5
- `RetrievedMemory`
- `RawMemory`
- `ConsolidatedNote`
- bounded routing metadata/signals
- product/raw coordination behavior
- mixed retrieval reasoning behavior

## Use only as reference/baseline

### The older heavy line
Treat the architecture/crystal/governance line as reference only.
Use it for contrast, not as immediate scope.

### Why reference only
Phase 5 is still a bounded routing-strengthening phase.
It should not absorb crystal, axiom, debt, or operating-system architecture ideas as direct implementation targets.

## Explicitly ignore in Phase 5 implementation

Do not actively implement or reintroduce these in Phase 5:
- root axiom systems
- structural debt systems
- self-modification protocols
- crystal generation/transfer implementation
- adapter systems
- operating-system style governance layers
- predictive prophylaxis systems
- full conflict arbitration kernels
- autonomous self-evolution controllers
- large scoring or policy economies around routing behavior

## Defer until Phase 6 or later

### Possible Phase 6 topics
- the first carefully bounded governance layer
- a new product family only if clearly justified
- further routing refinement only if strongly needed

### Later than Phase 6 unless strongly justified
- root-constraint / axiom systems
- debt/pruning economies
- self-evolution control loops
- crystal-transfer implementation layers
- operating-system style architectural metaphors as implementation drivers

## Practical working rule

When making a Phase 5 change, ask:
1. Does this improve routing usefulness?
2. Does this improve product/raw-memory coordination or routing clarity?
3. Could this be postponed without harming the Phase 5 target?

If the answer to (3) is yes, postpone it.

## Merge hygiene rule

A Phase 5 merge should mostly touch:
- minimal implementation files in the lightweight kernel line
- regrowth-plan docs
- minimal verification artifacts

A Phase 5 merge should not become a broad abstraction or vocabulary expansion sweep.

## Compression trigger

Stop and compress before continuing if:
- governance or ontology vocabulary grows faster than routing usefulness improves
- new object families appear without improving routing quality
- implementation starts depending on root-constraint, debt, or self-modification abstractions
- Phase 5 begins to resemble the older heavy line instead of a bounded routing-strengthening stage
