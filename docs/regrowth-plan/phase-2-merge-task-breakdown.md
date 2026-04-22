# Phase 2 Merge Task Breakdown

This file turns Phase 2 into small mergeable steps.

Phase 2 target:
- credibility and usefulness expansion
- while preserving the lightweight character of Phase 1

## Merge 1 - Provenance strengthening

### Goal
Make memory writes and retrievals easier to inspect and trust.

### Required implementation
- add stronger provenance fields to relevant memory objects
- capture source type and source id more explicitly
- capture write reason for memory creation
- capture retrieval reason for retrieval results
- if cheap, track contributing memory ids for consolidated notes

### Required decisions
- which provenance fields are mandatory vs optional?
- where should retrieval reason live?
- what provenance detail is enough for Phase 2 without overbuilding?

### Required verification
- confirm a written memory item exposes its provenance clearly
- confirm a retrieved memory item exposes why it was retrieved
- confirm provenance does not bloat the minimal kernel excessively

### Merge gate
Merge only if provenance becomes meaningfully clearer without triggering governance inflation.

## Merge 2 - Bounded tentative vs stable distinction

### Goal
Introduce a lightweight credibility distinction without building a full belief system.

### Required implementation
- add a bounded memory status field
- support at least:
  - `tentative`
  - `stable`
- define small status assignment rules
- allow retrieved items to expose status
- allow consolidated notes to prefer stable evidence when appropriate

### Required decisions
- what initial writes start as tentative?
- what evidence is sufficient to mark an item stable in Phase 2?
- what should remain impossible in this phase (for example, no deep confidence calculus)?

### Required verification
- confirm new memories can be marked tentative
- confirm repeated or stronger evidence can produce stable items
- confirm retrieval can surface the distinction clearly

### Merge gate
Merge only if the system gains a useful credibility distinction without becoming a belief-governance framework.

## Merge 3 - Better retrieval routing and ranking

### Goal
Improve retrieval quality and reduce noise.

### Required implementation
- refine retrieval score composition
- optionally add a clear relation-aware bonus if cheap
- route between raw memory and consolidated notes
- distinguish lightweight retrieval modes when useful, for example:
  - preference-like retrieval
  - topic-like retrieval
- improve suppression of noisy retrievals

### Required decisions
- what retrieval modes are worth distinguishing in Phase 2?
- how much routing complexity is acceptable before the system becomes heavy?
- what ranking improvements actually improve usefulness?

### Required verification
- compare retrieval quality against Phase 1 behavior
- confirm noise decreases on representative examples
- confirm the routing layer stays understandable and bounded

### Merge gate
Merge only if retrieval becomes noticeably better while staying simple enough to inspect.

## Merge 4 - Bounded revision and update handling

### Goal
Let the system update memory in simple conflict/supersession cases without opening a heavy arbitration stack.

### Required implementation
- support a bounded supersession/update link
- allow an older memory item to be marked superseded
- allow a note to be refreshed when repeated evidence appears
- support a minimal revise/update path for tentative/stable items

### Required decisions
- what counts as superseding evidence in Phase 2?
- when should memory be revised vs linked vs left alone?
- what revision complexity should still be forbidden in this phase?

### Required verification
- confirm a simple old/new update case can be represented
- confirm note refresh works in repeated-evidence cases
- confirm the system does not introduce a full arbitration or belief stack

### Merge gate
Merge only if revision behavior improves usefulness without reopening full conflict governance.

## Merge 5 - Slightly better consolidation quality

### Goal
Make consolidation outputs more reusable than in Phase 1.

### Required implementation
- refine consolidated note generation
- group retrieval anchors more meaningfully
- support preference-oriented notes
- support topic-oriented notes
- if cheap, support supersession-aware note updates

### Required decisions
- how many note types are enough for Phase 2?
- when is a grouped note better than separate notes?
- how far should consolidation quality improve before it becomes over-engineered?

### Required verification
- confirm consolidated outputs help retrieval more than Phase 1 notes did
- confirm note quality improves without introducing heavy abstraction machinery
- confirm consolidation remains bounded and understandable

### Merge gate
Merge only if consolidation quality improves in a visible but still lightweight way.

## Cross-merge anti-drift rules

Do not allow these to enter Phase 2 merges:
- root axiom layers
- structural debt systems
- self-modification protocols
- crystal generation/transfer machinery
- operating-system style governance layers
- predictive prophylaxis systems
- autonomous self-evolution controllers

If any of these appear, stop and compress before continuing.

## End-of-phase closeout

At the end of Phase 2, produce a closeout note answering:
- how credibility improved relative to Phase 1
- how retrieval improved relative to Phase 1
- how bounded revision/update now works
- what remains intentionally deferred
- whether Phase 3 should prioritize stronger distillation, stronger routing, or stronger memory governance
