# Phase 3 Scope Spec - Distillation and Memory Quality Refinement

## Phase identity

Phase 3 should strengthen what memory becomes, not just how memory is stored or routed.

Phase 3 is about:
- stronger distillation,
- better structured notes,
- and higher memory quality,
while still refusing a jump into heavy governance architecture.

## Phase objective

Build the third-stage memory layer that improves:
- note quality,
- structured distillation,
- memory usefulness over time,
- and the quality of reusable memory outputs,
without reopening root-constraint, debt, self-modification, or operating-system style layers.

## Why Phase 3 exists

Phase 1 proved a lightweight memory kernel can run.
Phase 2 proved the kernel can become more credible, selective, and update-capable.

The next natural step is not deep governance.
The next natural step is improving the quality of the memory products themselves.

Phase 3 exists to answer:
- how should repeated memories become better notes?
- how should memory become more reusable over time?
- how can the system distill more structure without becoming abstractly over-engineered?

## In-scope capabilities

### 1. Stronger note distillation
Improve consolidated note quality beyond the lightweight Phase 2 version.

Allowed improvements:
- better note wording
- better grouping of related memory items
- clearer separation between preference-like and topic-like notes
- note updates informed by repeated evidence and stable items

Goal:
- make notes more reusable and more representative of accumulated memory.

### 2. Structured note types
Expand notes carefully into a small set of reusable memory products.

Possible Phase 3 note/product types:
- preference note
- topic note
- summary note
- retrieval anchor note

The set should remain small and practical.

Goal:
- make memory outputs easier to route and reuse.

### 3. Better distillation from repeated evidence
Improve how repeated evidence becomes a stronger memory product.

Allowed improvements:
- stronger repeated-evidence aggregation
- stable-item preference during note updates
- note refresh based on multiple related memories rather than one-off matches

Goal:
- reduce naive note generation and increase accumulated-memory quality.

### 4. Retrieval-aware note refinement
Allow note quality work to be informed by actual retrieval usefulness.

Allowed improvements:
- use retrieval outcomes to refine note quality
- demote notes that do not help retrieval
- promote notes that repeatedly help retrieval

Goal:
- align distillation with real use, not just offline summarization.

### 5. Bounded memory quality signals
Introduce lightweight quality signals for note usefulness and refinement.

Possible bounded signals:
- retrieval_helpful_count
- update_count
- stable_source_count
- note_refresh_count

Goal:
- guide note refinement without opening a full governance economy.

## Explicit non-goals

Do not build these in Phase 3:
- root axiom systems
- structural debt systems
- self-modification protocols
- crystal generation/transfer systems as active implementation targets
- adapter systems
- operating-system style governance layers
- predictive prophylaxis systems
- full conflict arbitration kernels
- autonomous self-evolution controllers
- large-scale governance shells around note quality

## Core objects for Phase 3

Phase 3 may extend the lightweight object set carefully with:
- `RawMemory`
- `Entity`
- `Relation`
- `RetrievedMemory`
- `ConsolidatedNote`
- small note/product type vocabulary
- lightweight note-quality signals
- bounded update/supersession links already introduced in Phase 2

Do not add new object families unless they directly improve distillation quality.

## Runtime paths required

### Distillation path
Repeated/related memory -> grouped evidence -> improved note generation -> refined structured note

### Retrieval feedback path
Retrieved note -> usefulness signal -> note refinement or demotion/promotion

### Update path
New evidence -> note refresh -> updated note quality state

## Success criteria

Phase 3 is successful if the system can:
1. produce noticeably better note outputs than Phase 2
2. represent repeated evidence more faithfully in notes
3. keep note types small, useful, and understandable
4. use retrieval usefulness to influence note refinement
5. improve memory quality without reopening heavy governance layers

## Anti-drift rules

Stop and compress if:
- note-quality work starts introducing root-constraint or debt vocabulary
- a large governance shell begins forming around note scoring
- new object families appear faster than actual note quality improves
- the branch begins to resemble the old heavy architecture line rather than a bounded quality-refinement stage

## Desired output at phase close

At Phase 3 close, produce:
- a summary of note-quality improvements
- a summary of distillation improvements
- a summary of retrieval-aware refinement behavior
- a list of what remains intentionally deferred
- a recommendation for whether Phase 4 should focus on stronger memory products, stronger routing, or the first carefully bounded governance layer
