# Eight-Crystal Soft-Isolated Regrowth Protocol v1

## Goal

Test whether the expanded eight-crystal set improves soft-isolated regrowth quality over the earlier five-crystal set.

The main comparison focus is whether the added crystals improve:
- self-description
- deployment-facing runtime protocol recovery
- safety boundary recovery
- resilience / restart recovery
- gap diagnosis quality

---

## Inputs

### Meta-protocol crystal
- `docs/experiments/schema-definition-crystal-v1.json`

### Reasoning-path crystals
- `docs/experiments/problem-definition-crystal-v1.json`
- `docs/experiments/architecture-evolution-crystal-v1.json`

### Protocol crystals
- `docs/experiments/methodology-crystal-v1.json`
- `docs/experiments/retrieval-routing-crystal-v1.json`
- `docs/experiments/safety-boundary-crystal-v1.json`
- `docs/experiments/recovery-resilience-crystal-v1.json`

### Content crystal
- `docs/experiments/system-memory-crystal-v1.json`

---

## Isolation Rules

The receiving agent must not consult:
- source code
- Docker assets
- database state
- historical implementation files
- implementation-level repo history outside the provided crystals

The only allowed project knowledge inputs are the eight crystals above.

---

## Suggested Reading Order

1. schema-definition crystal
2. problem-definition crystal
3. architecture-evolution crystal
4. methodology crystal
5. retrieval-routing crystal
6. safety-boundary crystal
7. recovery-resilience crystal
8. system-memory crystal

---

## Required Output Layers

The receiving agent should output at least:

### 1. Self-description summary
- how the crystal set describes itself
- what kinds of crystal roles it contains
- how order and failure interpretation are understood

### 2. Problem definition summary
- what the project is trying to solve
- what it is explicitly not trying to be

### 3. Architecture evolution summary
- how the project reached its mainline
- which branch tensions still matter

### 4. Protocol summary
- ingestion / calibration behavior
- runtime routing behavior
- safety boundary behavior
- resilience / recovery behavior

### 5. System regrowth summary
- architecture summary
- modules
- runtime flows
- preserved tensions

### 6. Comparative gap analysis
- what is improved relative to the five-crystal experiment
- what still fails to regrow well
- what crystal types are still likely missing

---

## Evaluation Focus

Main questions:
- does the schema-definition crystal improve self-description and ordering clarity?
- do safety and recovery crystals improve deployment-facing runtime protocol regrowth?
- does the eight-crystal set improve failure interpretation quality?
- does the expanded set improve practical architecture neighborhood recovery?

---

## One-Sentence Summary

This protocol tests whether the eight-crystal set produces stronger self-describing, deployment-aware architecture regrowth than the earlier five-crystal set.
