# Phase 3 Merge Task Breakdown

This file turns Phase 3 into small mergeable steps.

Phase 3 target:
- stronger distillation
- better structured notes
- memory quality refinement
- while preserving the lightweight regrowth line

## Merge 1 - Stronger note distillation

### Goal
Make note outputs more representative and reusable than in Phase 2.

### Required implementation
- improve note wording and structure
- improve grouping of related memory items
- make note outputs less naive than simple entity-frequency summaries
- ensure note generation favors accumulated evidence over one-off signals

### Required decisions
- what makes a note "better" in this phase?
- how much wording refinement is useful before it becomes over-crafted?
- what grouping logic is sufficient without becoming heavy?

### Required verification
- compare note outputs against Phase 2 notes on representative examples
- confirm notes better represent accumulated memory
- confirm improvements remain interpretable and bounded

### Merge gate
Merge only if note quality visibly improves without introducing abstract governance machinery.

## Merge 2 - Structured note types

### Goal
Expand notes into a small but useful set of structured memory products.

### Required implementation
- define a bounded note/product type set
- support at least some of:
  - preference note
  - topic note
  - summary note
  - retrieval anchor note
- route note generation into these types consistently

### Required decisions
- which note types are worth keeping in Phase 3?
- what note types would be overkill at this stage?
- how should note type selection remain inspectable?

### Required verification
- confirm multiple note types can be produced consistently
- confirm the note type set remains small and useful
- confirm note types help retrieval/reuse rather than just expanding taxonomy

### Merge gate
Merge only if note types increase practical reuse without taxonomy inflation.

## Merge 3 - Better repeated-evidence distillation

### Goal
Make repeated evidence produce better accumulated memory than simple repeated refreshes.

### Required implementation
- improve repeated-evidence aggregation
- let stable items influence note updates more strongly than tentative items
- refresh notes from grouped evidence rather than single-event collisions

### Required decisions
- how much stable evidence should dominate note updates?
- what repeated-evidence threshold is enough for this phase?
- when should repeated evidence strengthen a note vs replace it?

### Required verification
- compare repeated-evidence outcomes against Phase 2 behavior
- confirm note updates become more representative of accumulated memory
- confirm the mechanism remains lightweight and inspectable

### Merge gate
Merge only if repeated-evidence handling improves distillation quality without opening a heavy evidence calculus.

## Merge 4 - Retrieval-aware note refinement

### Goal
Use retrieval usefulness to refine note quality.

### Required implementation
- add lightweight usefulness signals for notes
- allow notes that repeatedly help retrieval to be promoted
- allow notes that do not help retrieval to be demoted or deprioritized
- feed retrieval outcomes back into note refinement in a bounded way

### Required decisions
- what counts as helpful retrieval in this phase?
- what minimal signals are sufficient?
- how much adaptation is acceptable before the system becomes governance-heavy?

### Required verification
- confirm retrieval outcomes can influence note refinement
- confirm useful notes become easier to reuse
- confirm unhelpful notes do not dominate retrieval output

### Merge gate
Merge only if retrieval-aware refinement improves practical usefulness while staying lightweight.

## Merge 5 - Bounded memory quality signals

### Goal
Add lightweight quality signals that help guide note refinement without building a scoring economy.

### Required implementation
- introduce a small set of note-quality signals, such as:
  - `retrieval_helpful_count`
  - `update_count`
  - `stable_source_count`
  - `note_refresh_count`
- use those signals only to support note refinement and prioritization
- keep them descriptive and bounded

### Required decisions
- which quality signals are truly necessary?
- which signals would be overkill or too governance-like?
- how should quality signals remain visible and understandable?

### Required verification
- confirm signals help guide note refinement
- confirm they do not expand into a heavy scoring economy
- confirm note/product quality improves in visible ways

### Merge gate
Merge only if quality signals improve note refinement while remaining bounded and practical.

## Cross-merge anti-drift rules

Do not allow these to enter Phase 3 merges:
- root axiom systems
- structural debt systems
- self-modification protocols
- crystal/transfer implementation layers
- operating-system style governance layers
- predictive prophylaxis systems
- full conflict arbitration kernels
- autonomous self-evolution controllers
- large governance shells around note quality

If any of these appear, stop and compress before continuing.

## End-of-phase closeout

At the end of Phase 3, produce a closeout note answering:
- how note quality improved relative to Phase 2
- how repeated-evidence distillation improved
- how retrieval-aware refinement changed memory usefulness
- what remains intentionally deferred
- whether Phase 4 should focus on stronger memory products, stronger routing, or the first carefully bounded governance layer
