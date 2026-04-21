# Phase 5 Merge Task Breakdown

This file turns Phase 5 into small mergeable steps.

Phase 5 target:
- stronger routing
- better product/raw-memory coordination
- better mixed retrieval behavior
- better practical usefulness
- while preserving the lightweight regrowth line

## Merge 1 - Stronger mixed retrieval routing

### Goal
Make mixed retrieval more useful and better balanced than in Phase 4.

### Required implementation
- improve mixed selection between raw memory and reusable products
- improve balancing of raw and product results
- improve mixed retrieval behavior under common query cases
- keep mixed outputs more useful and less arbitrary

### Required decisions
- what balance between raw memory and products is useful in this phase?
- when should products be favored, and when should raw memory be preserved more strongly?
- how much balancing logic is enough before routing becomes too rigid?

### Required verification
- compare mixed retrieval outputs against Phase 4 behavior
- confirm mixed results are more useful and better balanced
- confirm diversity remains present in outputs

### Merge gate
Merge only if mixed retrieval visibly improves without collapsing into product-only or raw-only routing.

## Merge 2 - Better product/raw-memory coordination rules

### Goal
Clarify bounded coordination rules for raw memory and products.

### Required implementation
- define clearer coexistence rules in retrieval output
- improve product/raw coordination behavior
- make coordination rules more inspectable and less implicit

### Required decisions
- what coexistence rules are truly useful in Phase 5?
- which coordination rules would be too rigid or too governance-like?
- how should coordination remain understandable?

### Required verification
- confirm coordination rules behave consistently
- confirm raw memory and products can coexist usefully
- confirm coordination helps rather than constrains retrieval too early

### Merge gate
Merge only if coordination improves practical usefulness without becoming a heavy routing policy layer.

## Merge 3 - Better mode-aware retrieval behavior

### Goal
Make preference/topic and similar retrieval modes more practically meaningful.

### Required implementation
- improve mode-specific routing behavior
- improve when products are favored under some modes
- improve when raw evidence is preserved under some modes
- make mode differences more useful in actual retrieval outputs

### Required decisions
- which modes deserve distinct behavior in Phase 5?
- how much mode specialization is useful before routing becomes taxonomy-heavy?
- how should mode behavior remain inspectable?

### Required verification
- compare mode-aware outputs against earlier behavior
- confirm routing differences are meaningful and useful
- confirm modes do not create brittle routing behavior

### Merge gate
Merge only if mode-aware behavior becomes more useful without over-specializing the retrieval layer.

## Merge 4 - Better inspectable routing reasons

### Goal
Make mixed retrieval behavior easier to explain and inspect.

### Required implementation
- improve retrieval/routing reason quality
- make mixed raw/product selection easier to understand
- expose bounded routing summaries or explanations

### Required decisions
- what explanation detail is sufficient for this phase?
- what explanation detail would be decorative or too governance-like?
- how should routing reasons remain lightweight?

### Required verification
- confirm routing reasons become clearer and more usable
- confirm mixed-selection explanations align with observed behavior
- confirm explanation improvements remain bounded and practical

### Merge gate
Merge only if routing reasons become more inspectable without expanding into a heavy explanation shell.

## Merge 5 - Bounded routing metadata/signals

### Goal
Add lightweight routing metadata/signals only where they clearly improve usefulness and inspectability.

### Required implementation
- introduce a bounded set of routing metadata/signals, such as:
  - mixed-routing reason summaries
  - product/raw balance summaries
  - routing-mode summaries
  - bounded coordination counters
- use routing metadata only to support usefulness and explanation
- keep metadata descriptive and practical

### Required decisions
- which routing signals are truly useful in Phase 5?
- which signals would be decorative or governance-like?
- how should routing metadata remain visible and understandable?

### Required verification
- confirm routing metadata improves inspection and usefulness
- confirm it does not expand into a heavy routing-governance shell
- confirm routing clarity improves in visible ways

### Merge gate
Merge only if routing metadata improves clarity while remaining bounded and practical.

## Cross-merge anti-drift rules

Do not allow these to enter Phase 5 merges:
- root axiom systems
- structural debt systems
- self-modification protocols
- crystal/transfer implementation layers
- operating-system style governance layers
- predictive prophylaxis systems
- full conflict arbitration kernels
- autonomous self-evolution controllers
- large governance shells around routing behavior

If any of these appear, stop and compress before continuing.

## End-of-phase closeout

At the end of Phase 5, produce a closeout note answering:
- how routing improved relative to Phase 4
- how product/raw-memory coordination improved
- how retrieval-mode behavior improved
- what remains intentionally deferred
- whether Phase 6 should focus on a first carefully bounded governance layer, a new product family only if justified, or further routing refinement only if clearly needed
