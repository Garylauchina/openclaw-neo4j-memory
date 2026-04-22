# Phase 2 Working Boundary

This file defines what Phase 2 should actively improve, what it should treat only as reference, and what it must continue to defer.

## Purpose

Protect Phase 2 from regrowing the old heavy architecture while still allowing meaningful credibility and usefulness improvements beyond Phase 1.

## Keep in active focus

### Planning docs
- `docs/regrowth-plan/phase-1-mvp-spec.md`
- `docs/regrowth-plan/phase-1-closeout-note.md`
- `docs/regrowth-plan/phase-1-freeze-summary.md`
- `docs/regrowth-plan/phase-2-scope-spec.md`
- `docs/regrowth-plan/phase-2-merge-task-breakdown.md`
- `docs/regrowth-plan/phase-2-working-boundary.md`

### Code concerns that belong to Phase 2
- provenance strengthening
- tentative vs stable distinction
- better retrieval routing/ranking
- bounded revision/update handling
- slightly better consolidation quality

### Data/object concerns that belong to Phase 2
- `RawMemory`
- `Entity`
- `Relation`
- `RetrievedMemory`
- `ConsolidatedNote`
- bounded memory status (`tentative` / `stable`)
- lightweight provenance fields
- bounded supersession/update link

## Use only as reference/baseline

### The old heavy baseline line
Treat the following as reference only:
- architecture/crystal/regrowth/ecology docs
- update-governance docs
- verification docs
- compatibility docs
- adapter docs
- crystal-system docs
- recursive crystal discovery artifacts
- tmp experimental outputs

### Why reference only
They may contain useful concepts, but they are not direct implementation scope for Phase 2.
Phase 2 should not re-import them wholesale.

## Explicitly ignore in Phase 2 implementation

Do not actively implement or reintroduce these in Phase 2:
- root axiom layers
- structural debt systems
- self-modification protocols
- crystal generation or transfer systems
- adapter systems
- compatibility governance systems
- operating-system style governance layers
- predictive prophylaxis systems
- full conflict arbitration kernels
- autonomous self-evolution controllers
- governance-kernel terminology as implementation driver

## Defer until Phase 3 or later

### Possible Phase 3 topics
- stronger distillation
- stronger retrieval routing
- deeper memory governance
- richer consolidation and abstraction quality

### Later than Phase 3 unless strongly justified
- root-constraint / axiom systems
- crystal and transfer layers
- self-evolution control systems
- governance-kernel and operating-system style abstractions
- ecology/adaptation/adapters as active implementation layers

## Practical working rule

When making a Phase 2 change, ask:
1. Does this improve credibility or usefulness relative to Phase 1?
2. Does this stay bounded and inspectable?
3. Could this be postponed without harming Phase 2's target?

If the answer to (3) is yes, postpone it.

## Merge hygiene rule

A Phase 2 merge should mostly touch:
- minimal implementation files in the lightweight kernel line
- regrowth-plan docs
- minimal verification artifacts

A Phase 2 merge should not become a conceptual cleanup of the whole repository.

## Compression trigger

Stop and compress before continuing if:
- governance vocabulary grows faster than actual retrieval/revision quality
- new objects appear without improving trust, routing, or update behavior
- implementation starts depending on root constraints, debt, or self-modification abstractions
- Phase 2 begins to resemble the old heavy baseline instead of a bounded extension of Phase 1
