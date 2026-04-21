# Phase 2 Scope Spec - Credibility and Usefulness Expansion

## Phase identity

Phase 2 should extend the lightweight Phase 1 kernel without reopening the full heavy architecture.

Phase 2 is about making the memory loop:
- more credible,
- more useful,
- and more selective,
while preserving the simplicity of Phase 1.

## Phase objective

Build the second-stage memory layer that improves:
- provenance strength,
- bounded distinction between tentative and more stable memory,
- better retrieval routing/ranking,
- more careful revision/update handling,
- and slightly better consolidation quality.

Phase 2 should still remain clearly below:
- root axiom systems,
- structural debt systems,
- self-modification governance,
- crystal/transfer systems,
- operating-system style architecture expansion.

## Why Phase 2 exists

Phase 1 proved a lightweight memory kernel can run.
Its main weaknesses were intentionally accepted:
- shallow extraction
- coarse relation typing
- basic retrieval scoring
- minimal provenance
- no hypothesis/stable distinction
- consolidation without revision awareness

Phase 2 exists to improve these weaknesses without abandoning the lightweight regrowth approach.

## In-scope capabilities

### 1. Provenance strengthening
Add clearer provenance to stored and retrieved memory.

Examples of Phase 2 provenance fields:
- source type
- source id
- write reason
- retrieval reason
- contributing memory ids

Goal:
- make memory use easier to inspect and trust.

### 2. Bounded hypothesis vs stable distinction
Introduce a small, bounded distinction between:
- tentative memory items
- more stable memory items

This should remain lightweight.
Do not build a full belief governance framework.

Possible first-phase-2 statuses:
- `tentative`
- `stable`

Goal:
- avoid treating all extracted memory as equally reliable.

### 3. Better retrieval routing and ranking
Improve retrieval quality beyond the Phase 1 simple mixture of lexical/entity/recentness.

Allowed improvements:
- slightly richer score composition
- relation-aware bonus if cheap and clear
- routing between raw memory and consolidated notes
- separate handling for preference-like vs topic-like retrievals

Goal:
- retrieve the right memory more often with less noise.

### 4. Careful revision/update handling
Add a bounded way to revise memory items when new information conflicts with or supersedes old information.

Allowed Phase 2 behavior:
- mark older memory as superseded
- link related tentative/stable items
- update note summaries when repeated evidence appears

Goal:
- introduce minimal memory revision without opening a full conflict-arbitration stack.

### 5. Slightly better consolidation quality
Improve consolidation so it is not just dedupe + frequent entities.

Allowed improvements:
- small summary refinement
- grouped retrieval anchors
- preference-oriented notes
- topic-oriented notes
- simple supersession-aware note updates

Goal:
- make consolidated memory more reusable and less naive.

## Explicit non-goals

Do not build these in Phase 2:
- root axiom layers
- structural debt systems
- self-modification protocols
- crystal generation or transfer systems
- adapter systems
- compatibility governance systems
- update-governance frameworks at full scale
- operating-system style governance layers
- predictive prophylaxis systems
- full arbitration kernels
- autonomous self-evolution controllers

## Core objects for Phase 2

Phase 2 may extend the object set carefully with:
- `RawMemory`
- `Entity`
- `Relation`
- `RetrievedMemory`
- `ConsolidatedNote`
- lightweight memory status field (`tentative` / `stable`)
- provenance fields or small provenance helper object
- optional supersession/update link

Do not expand the object set unless it directly improves credibility or usefulness.

## Runtime paths required

### Write path
Input -> write decision -> raw persistence -> extraction -> status assignment -> provenance capture

### Retrieval path
New input -> retrieval trigger -> route selection -> ranking -> top-k selection -> provenance explanation

### Injection path
Retrieved memory -> selective filtering -> bounded context injection

### Revision path
New evidence -> compare with existing item -> bounded revise/supersede/update action

### Background path
Memory set -> better consolidation -> note updates -> stable retrieval anchors

## Success criteria

Phase 2 is successful if the system can:
1. explain where retrieved memory came from more clearly than Phase 1
2. distinguish tentative memory from more stable memory in a bounded way
3. retrieve more relevant memory with less noise than Phase 1
4. handle simple revision/update cases without a heavy governance stack
5. produce more useful consolidated notes than Phase 1
6. remain recognizably lightweight rather than regrowing the old heavy line

## Anti-drift rules

Stop and compress if:
- new governance vocabulary grows faster than retrieval quality improves
- new objects appear without improving provenance, ranking, or revision behavior
- the branch starts introducing root constraints, debt systems, or self-modification language
- Phase 2 begins to resemble the old architecture/crystal line instead of a bounded extension of Phase 1

## Desired output at phase close

At Phase 2 close, produce:
- a summary of credibility improvements
- a summary of retrieval-quality improvements
- a summary of bounded revision/update behavior
- a list of what remains intentionally deferred
- a recommendation for whether Phase 3 should focus on stronger distillation, stronger routing, or stronger memory governance
