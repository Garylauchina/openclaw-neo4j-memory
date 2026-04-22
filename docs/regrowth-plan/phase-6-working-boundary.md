# Phase 6 Working Boundary

This file defines what Phase 6 should actively improve, what it should use only as reference, and what it must continue to defer.

## Purpose

Protect Phase 6 from turning failure-driven governance into a heavy governance or abstraction layer.

## Keep in active focus

### Planning docs
- `docs/regrowth-plan/phase-5-closeout-note.md`
- `docs/regrowth-plan/phase-5-freeze-summary.md`
- `docs/regrowth-plan/phase-6-scope-spec.md`
- `docs/regrowth-plan/phase-6-merge-task-breakdown.md`
- `docs/regrowth-plan/phase-6-working-boundary.md`

### Code concerns that belong to Phase 6
- failure-case cataloging
- minimal intervention rules
- bounded conflict/pressure handling
- inspectable governance reasons
- bounded governance metadata/signals

### Data/object concerns that belong to Phase 6
- `RoutingDecision`
- `RetrievedMemory`
- `ConsolidatedNote`
- bounded failure-case annotations
- bounded intervention reasons
- bounded governance metadata/signals

## Use only as reference/baseline

### The older heavy line
Treat the architecture/crystal/governance line as reference only.
Use it for contrast, not as immediate scope.

### Why reference only
Phase 6 is still a bounded failure-driven governance phase.
It should not absorb crystal, axiom, debt, or operating-system architecture ideas as direct implementation targets.

## Explicitly ignore in Phase 6 implementation

Do not actively implement or reintroduce these in Phase 6:
- root axiom systems
- structural debt systems
- self-modification protocols
- crystal generation/transfer implementation
- adapter systems
- operating-system style governance layers
- predictive prophylaxis systems
- full conflict arbitration kernels
- autonomous self-evolution controllers
- large scoring or policy economies around governance behavior
- broad rule engines not tied to concrete failure cases

## Defer until later unless strongly justified

### Possible later topics
- deeper bounded governance only if current interventions prove insufficient
- a new product family only if clearly justified
- further routing refinement only if governance does not solve the observed pressure

### Much later unless strongly justified
- root-constraint / axiom systems
- debt/pruning economies
- self-evolution control loops
- crystal-transfer implementation layers
- operating-system style architectural metaphors as implementation drivers

## Practical working rule

When making a Phase 6 change, ask:
1. Does this solve a concrete failure case?
2. Does this remain smaller than a general-purpose governance layer?
3. Could this be postponed without harming the actual failure-case target?

If the answer to (3) is yes, postpone it.

## Merge hygiene rule

A Phase 6 merge should mostly touch:
- minimal implementation files in the lightweight kernel line
- regrowth-plan docs
- minimal verification artifacts

A Phase 6 merge should not become a broad architecture or vocabulary expansion sweep.

## Compression trigger

Stop and compress before continuing if:
- governance scope grows faster than concrete failure justification
- new object families appear before failure cases are clearly defined
- implementation starts depending on root-constraint, debt, or self-modification abstractions
- Phase 6 begins to resemble the older heavy line instead of a bounded failure-driven governance stage
