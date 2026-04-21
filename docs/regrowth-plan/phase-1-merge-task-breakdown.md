# Phase 1 Merge Task Breakdown

This file turns Phase 1 into small mergeable steps.

Phase 1 target:
- lightweight memory structure
- prompt-level memory orchestration
- minimal runnable closed loop

## Merge 1 - Minimal raw write/read path

### Goal
Prove the system can persist and read back raw experience with a basic write decision rule.

### Required implementation
- define a minimal `RawMemory` record shape
- implement raw memory persistence
- implement raw memory readback by id or recent list
- implement a first write decision rule
- connect accepted writes to the persistence layer

### Required decisions
- what counts as an accepted memory write event?
- where does raw memory live in the MVP?
- what minimal metadata is mandatory?

### Required verification
- write one memory item and read it back
- write multiple memory items and list recent items
- confirm the write decision rule can reject obviously low-value items if configured

### Merge gate
Merge only if raw experience can be reliably saved and read back.

## Merge 2 - Minimal structure extraction and retrieval

### Goal
Prove the system can derive lightweight structure and retrieve relevant earlier material.

### Required implementation
- define minimal `Entity` and `Relation` objects
- implement lightweight extraction from raw memory
- define a small relation vocabulary
- implement retrieval query construction
- implement top-k retrieval over:
  - lexical overlap
  - entity overlap
  - recentness
- add optional relation overlap only if cheap and stable
- implement a retrieval trigger rule

### Required decisions
- which extraction errors are tolerated in this phase?
- what retrieval score composition is sufficient for MVP?
- how many memories should top-k return by default?

### Required verification
- ingest related memories with overlapping entities
- issue a new related input
- confirm top-k retrieval includes expected prior memories
- confirm retrieval can be skipped when trigger rule says not to run

### Merge gate
Merge only if related prior material can be found on later relevant input.

## Merge 3 - Minimal memory injection and prompt orchestration

### Goal
Prove the system can inject retrieved memory into current execution and that prompt policy meaningfully changes memory use.

### Required implementation
- define `RetrievedMemory` or `MemorySnippet` formatting
- implement compact memory context construction
- implement injection formatting rule
- implement ignore / suppress rule for irrelevant retrievals
- integrate retrieval result into current task context
- implement prompt-level memory orchestration rules for:
  - write decision
  - retrieval trigger
  - injection formatting
  - ignore / suppress

### Required decisions
- how large can injected memory context be?
- what source attribution format is sufficient?
- what signals cause suppression of noisy memory?

### Required verification
- confirm a relevant prior memory changes the resulting output
- confirm irrelevant retrieved memory is suppressed
- confirm injected context stays bounded
- compare output with and without memory injection on at least one task

### Merge gate
Merge only if memory is not merely stored/retrieved but actually affects execution usefully.

## Merge 4 - Lightweight asynchronous consolidation

### Goal
Prove the system can improve memory reuse over time without turning into a heavy governance system.

### Required implementation
- implement lightweight deduplication
- implement frequent-entity marking
- implement small consolidated notes or retrieval anchors
- ensure background consolidation does not block or destabilize the write path
- if cheap, allow consolidation outcomes to inform prompt guidance updates

### Required decisions
- what consolidation frequency is safe for MVP?
- what counts as a duplicate in this phase?
- are consolidated notes stored separately from raw memory?

### Required verification
- confirm duplicate or near-duplicate raw memories can be reduced or linked
- confirm repeated entities become easier retrieval anchors
- confirm write path still works while consolidation runs
- confirm consolidation remains lightweight and bounded

### Merge gate
Merge only if async consolidation improves reuse without introducing heavy governance complexity.

## Cross-merge anti-drift rules

Do not allow these to enter Phase 1 merges:
- belief governance expansion
- root axiom layers
- structural debt objects
- self-modification protocols
- full conflict arbitration stack
- crystal/transfer systems
- operating-system metaphor expansion

If any of these appear, stop and compress the design before merging.

## End-of-phase closeout

At the end of Merge 4, produce a short Phase 1 closeout note answering:
- what minimal memory loop is now runnable?
- what prompt policy rules were sufficient?
- what still feels missing but was intentionally deferred?
- what inflation risks were successfully avoided?
- what Phase 2 should include and what it should still forbid?
