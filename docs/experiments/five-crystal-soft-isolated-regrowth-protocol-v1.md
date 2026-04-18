# Five-Crystal Soft-Isolated Regrowth Protocol v1

## Goal

Test whether a new agent can regrow the project architecture neighborhood from a small crystal set alone,
without access to source code, Docker setup, database state, or historical implementation files.

This is a soft-isolated regrowth experiment.

---

## Inputs

### Upstream reasoning-path crystals
- `docs/experiments/problem-definition-crystal-v1.json`
- `docs/experiments/architecture-evolution-crystal-v1.json`

### Protocol crystals
- `docs/experiments/methodology-crystal-v1.json`
- `docs/experiments/retrieval-routing-crystal-v1.json`

### Content crystal
- `docs/experiments/system-memory-crystal-v1.json`

---

## Isolation Rules

The receiving agent must not consult:
- source code
- Docker files
- database state
- prior implementation assets
- old issue or PR history outside what is already crystalized here

The only allowed architectural inputs are the five crystals above.

---

## Suggested Reading Order

### Stage 1. Problem-definition crystal
Recover:
- what problem the project is actually solving
- what routes are explicitly out of scope
- what tensions forced the project into this space

### Stage 2. Architecture-evolution crystal
Recover:
- how the project reached its current mainline
- what branches mattered
- what experiments changed architectural direction

### Stage 3. Methodology crystal
Recover:
- how the receiving agent should calibrate itself
- how to avoid hardcoding and false self-discovery

### Stage 4. Retrieval-routing crystal
Recover:
- how runtime layer routing should work
- how layered retrieval should be packaged
- which boundaries should remain protected

### Stage 5. System-memory crystal
Recover:
- the system architecture content core
- modules, flows, tensions, and architecture body

---

## Required Output Layers

The receiving agent should output at least:

### 1. Problem definition summary
- what the system exists to solve
- what it is not trying to be

### 2. Architecture evolution summary
- how the system got here
- what branch tensions still matter

### 3. Protocol summary
- ingestion / calibration behavior
- runtime routing behavior

### 4. System regrowth summary
- architecture summary
- module set
- runtime flows
- preserved tensions

### 5. Gap analysis
- what could not be regrown well
- what likely requires additional crystals
- what remains too implementation-dependent

---

## Evaluation Focus

Main questions:
- can the new agent recover the actual project problem rather than a generic memory-system story?
- can it recover the evolutionary logic rather than only the final structure?
- can it distinguish protocol crystals from content crystals?
- can it regrow a coherent architecture neighborhood without source code?
- do the failures expose missing crystals or weak existing crystals?

---

## Failure Interpretation Rule

Do not interpret failure only as model weakness.

Also interpret failure as possible evidence of:
- missing crystal types
- insufficient reasoning-path compression
- weak protocol-layer crystallization
- missing ordering/dependency information
- excessive dependence on implicit source-code knowledge

---

## One-Sentence Summary

This protocol tests whether a five-crystal set is sufficient for soft-isolated project regrowth, and uses regrowth failures as evidence of what crystal structure is still missing.
