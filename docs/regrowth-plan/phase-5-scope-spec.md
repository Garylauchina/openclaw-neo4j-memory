# Phase 5 Scope Spec - Stronger Routing and Product/Raw-Memory Coordination

## Phase identity

Phase 5 should strengthen routing and coordination between reusable memory products and raw memory before introducing any carefully bounded governance layer.

Phase 5 is about:
- stronger routing,
- better product/raw-memory coordination,
- clearer mixed retrieval behavior,
- and better practical usefulness,
while still refusing a jump into heavy governance architecture.

## Phase objective

Build a fifth-stage retrieval/routing layer that improves:
- coordination between raw memory and reusable products,
- routing quality,
- mixed retrieval usefulness,
- and inspectable retrieval behavior,
without reopening root-constraint, debt, self-modification, or operating-system style layers.

## Why Phase 5 exists

Phase 1 proved a lightweight memory kernel can run.
Phase 2 proved the kernel can become more credible, selective, and update-capable.
Phase 3 proved the system can grow a real note/product layer.
Phase 4 proved the product layer can become clearer and more reusable.

The next natural step is to improve how raw memory and products are coordinated in retrieval.

Phase 5 exists to answer:
- when should retrieval prefer raw memory versus reusable products?
- how should different retrieval modes coordinate mixed outputs?
- how can routing become more useful without turning into a heavy governance shell?

## In-scope capabilities

### 1. Stronger mixed retrieval routing
Improve how the system routes between raw memory and reusable products.

Allowed improvements:
- clearer mixed retrieval selection
- better balancing of raw memory and products
- better routing under different query intents
- more useful mixed-output behavior

Goal:
- make routing more useful without collapsing into a single retrieval mode.

### 2. Better product/raw-memory coordination
Clarify how raw memory and products should coexist during retrieval.

Allowed improvements:
- clearer product/raw-memory coordination rules
- bounded coexistence rules in retrieval outputs
- better handling of product dominance versus raw evidence presence

Goal:
- keep both raw evidence and reusable products available when useful.

### 3. Better mode-aware retrieval behavior
Improve how different query types affect routing behavior.

Allowed improvements:
- better preference-mode routing
- better topic-mode routing
- better routing when reusable products clearly help
- better routing when raw evidence is more important

Goal:
- make retrieval mode distinctions more practically useful.

### 4. Better inspectable routing reasons
Improve routing explainability and inspectability.

Allowed improvements:
- clearer retrieval/routing reasons
- more explicit mixed-routing signals
- better visibility into why products or raw memories were selected

Goal:
- make routing behavior understandable without building a governance layer.

### 5. Bounded routing metadata/signals
Add lightweight routing metadata or signals only where they directly improve usefulness and inspectability.

Possible bounded additions:
- mixed-routing reason summaries
- product/raw balance summaries
- routing-mode summaries
- bounded coordination counters

Goal:
- improve routing clarity without creating a routing-governance shell.

## Explicit non-goals

Do not build these in Phase 5:
- root axiom systems
- structural debt systems
- self-modification protocols
- crystal generation/transfer systems as active implementation targets
- adapter systems
- operating-system style governance layers
- predictive prophylaxis systems
- full conflict arbitration kernels
- autonomous self-evolution controllers
- large governance shells around routing behavior

## Core objects for Phase 5

Phase 5 may extend the lightweight object set carefully with:
- `RawMemory`
- `RetrievedMemory`
- `ConsolidatedNote`
- bounded routing metadata/signals
- bounded product/raw coordination rules
- bounded retrieval-mode distinctions already introduced earlier

Do not add new object families unless they directly improve routing usefulness.

## Runtime paths required

### Mixed retrieval path
Query -> routing mode -> raw/product coordination -> mixed retrieval output

### Routing refinement path
Retrieval behavior -> routing signal -> bounded routing improvement

### Explanation path
Retrieval output -> routing reason -> inspectable mixed-selection explanation

## Success criteria

Phase 5 is successful if the system can:
1. coordinate raw memory and products more usefully than Phase 4
2. preserve retrieval diversity while still using reusable products well
3. make retrieval modes more practically meaningful
4. produce clearer routing reasons and inspectable mixed behavior
5. avoid reopening heavy governance layers

## Anti-drift rules

Stop and compress if:
- routing work starts introducing root-constraint or debt vocabulary
- large governance language begins forming around routing behavior
- new object families appear faster than routing usefulness improves
- Phase 5 begins to resemble the older heavy architecture line rather than a bounded routing-strengthening stage

## Desired output at phase close

At Phase 5 close, produce:
- a summary of routing improvements
- a summary of product/raw-memory coordination improvements
- a summary of retrieval-mode improvements
- a list of what remains intentionally deferred
- a recommendation for whether Phase 6 should focus on a first carefully bounded governance layer, a new product family only if justified, or further routing refinement only if clearly needed
