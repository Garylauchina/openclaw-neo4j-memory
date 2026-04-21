# Phase 1 MVP Spec - Lightweight Memory Structure + Prompt Optimization

## Phase objective

Build a minimal long-term memory MVP that combines:
- a lightweight memory structure,
- and a prompt-level memory orchestration layer.

The system should be able to:
- capture raw experience,
- extract minimal structure,
- retrieve relevant past memory for a new input,
- inject retrieved memory into the current task context,
- use prompt-level policies to decide when to write, retrieve, and inject memory,
- and run lightweight asynchronous consolidation.

This phase is about a runnable minimal closed loop, not a full memory architecture.

## Phase principle

Phase 1 should produce the smallest memory form that can survive and be useful.
The goal is not a complete cognitive system.
The goal is a minimal viable memory organism:
- it can retain experience,
- form a little structure,
- recover useful prior material,
- and let prompt policy meaningfully influence memory use.

## In-scope capabilities

### 1. Raw memory write
Persist a minimal raw memory record for each accepted interaction/event.

Minimum fields:
- `id`
- `timestamp`
- `source`
- `content`
- `context`
- `metadata` (small, optional)

Goal:
- ensure the system can retain experience material without immediate loss.

### 2. Minimal structured extraction
Extract only a small amount of reusable structure from raw memory.

Allowed first-phase structural objects:
- `Entity`
- `Relation`

Preferred relation types should stay small and generic, for example:
- `about`
- `mentions`
- `related_to`
- `preference_of`
- `associated_with`

Goal:
- create retrieval hooks, not a full ontology.

### 3. Minimal retrieval
Given a new input, retrieve relevant prior memory.

Minimum retrieval signals:
- lexical overlap
- entity overlap
- recentness

Optional if cheap:
- relation overlap

Minimum outputs:
- top-k raw memories
- top-k structured memory items

Goal:
- prove past experience can be reused in current tasks.

### 4. Minimal memory injection
Inject retrieved memory into the current task context in a compact and stable form.

Requirements:
- bounded size
- clear source attribution
- stable formatting
- observable effect on current response/task behavior

Goal:
- memory must affect execution, not just sit in storage.

### 5. Prompt-level memory orchestration
Add a lightweight prompt policy layer that governs how memory is used.

This layer should answer at least these questions:
- when is a new input worth writing into memory?
- when should the system attempt retrieval before answering?
- how should retrieved memory be injected into the current task context?
- when should memory be ignored to avoid context pollution?

The first-phase orchestration layer should remain light.
It should be implemented as prompt/policy guidance, not as a heavy governance kernel.

Goal:
- make memory usage selective and useful, not automatic and noisy.

### 6. Minimal asynchronous consolidation
Run a lightweight background consolidation path.

Allowed first-phase behaviors:
- obvious deduplication
- frequent-entity marking
- small summary / distilled note generation
- stable retrieval anchor creation

Goal:
- keep real-time writes simple while making memory more reusable over time.

## Explicit non-goals

Do not build these in Phase 1:
- full belief system
- full world model
- root axiom layer
- governance kernel
- structural debt system
- pruning economy
- self-modification protocol
- crystal system
- transfer system
- adapter layer
- advanced predictive conflict / prophylaxis layer
- full conflict arbitration stack
- self-evolving operating-system style governance

## Core data objects

Keep the first-phase object set minimal:
- `RawMemory`
- `Entity`
- `Relation`
- `RetrievedMemory` or `MemorySnippet`
- `ConsolidatedNote` (recommended, optional at first implementation)

## Core prompt/policy objects

Keep the first-phase policy layer minimal:
- write decision rule
- retrieval trigger rule
- injection formatting rule
- ignore / suppress rule for irrelevant memory

These may remain prompt-level rules rather than persistent governance objects.

## Runtime paths required

### Write path
Input -> write decision -> raw memory persistence -> minimal structure extraction

### Retrieval path
New input -> retrieval trigger -> query construction -> memory ranking -> top-k selection

### Injection path
Retrieved memory -> compact memory context -> current task context

### Background path
Raw memory / structure -> lightweight async consolidation

## Success criteria

Phase 1 is successful if the system can complete this loop:
1. accept a new input/event
2. decide whether it should be written to memory
3. save raw memory when appropriate
4. extract minimal structure
5. decide whether retrieval should run on a later related input
6. retrieve relevant prior memory
7. inject that memory into the current task context
8. produce output measurably influenced by retrieved memory
9. avoid injecting obviously irrelevant memory
10. run lightweight asynchronous consolidation without breaking the write path

## Merge milestones

### Merge 1
Minimal raw write/read path
- raw persistence
- basic readback
- initial write decision rule
- smoke verification

### Merge 2
Minimal structure extraction + retrieval
- entity extraction
- small relation set
- retrieval trigger rule
- top-k retrieval

### Merge 3
Minimal memory injection + prompt orchestration
- compact context construction
- bounded injection format
- injection policy
- ignore / suppress rule for irrelevant memory
- observable reuse in output

### Merge 4
Lightweight async consolidation
- dedupe
- frequent-entity marking
- small distilled notes or retrieval anchors
- basic prompt guidance updates informed by consolidation outcomes if cheap

## Evaluation questions

At phase close, answer:
- Can the system retain raw experience reliably?
- Can it retrieve the right old material for a new input?
- Does retrieved memory actually affect current execution?
- Does the prompt policy improve when memory is written, retrieved, or ignored?
- Is the async consolidation path lightweight enough to coexist with real-time writes?
- Did the phase stay minimal, or did governance / abstraction start creeping in?

## Exit condition

Do not leave Phase 1 because the architecture sounds complete.
Leave Phase 1 only when the lightweight memory structure plus prompt orchestration loop is actually runnable and useful.
