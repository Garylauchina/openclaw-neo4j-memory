# Multi-Crystal Runtime Routing Protocol v1

## Goal

Test whether a crystal set can guide runtime retrieval routing more faithfully than a flat retrieval approach.

This first version uses three crystals:
- methodology crystal
- retrieval-routing crystal
- system crystal

The expected order is:
1. methodology crystal
2. retrieval-routing crystal
3. system crystal

---

## Inputs

### Methodology crystal
- `docs/experiments/methodology-crystal-v1.json`

### Retrieval-routing crystal
- `docs/experiments/retrieval-routing-crystal-v1.json`

### System crystal
- `docs/experiments/system-memory-crystal-v1.json`

---

## Runtime Principle

Do not merge the three crystals into one flat instruction bundle.

Instead:
- methodology crystal establishes how to self-calibrate and avoid hardcoding
- retrieval-routing crystal establishes how to route across layers
- system crystal provides the architecture content core

---

## Required Stages

### Stage 1. Read methodology crystal
Extract:
- self-definition through testing
- content core vs adaptation layer boundary
- pre-ingestion calibration rule
- anti-hardcoding constraint

### Stage 2. Methodology calibration
Output:
- methodology portrait
- chosen adaptation method

### Stage 3. Read retrieval-routing crystal
Extract:
- runtime intent classification logic
- layer-specific retrieval modes
- permission boundaries
- packaging order constraints

### Stage 4. Routing calibration
Output:
- routing behavior portrait
- chosen routing policy

### Stage 5. Read system crystal
Read the system architecture through the already chosen methodology and routing policies.

### Stage 6. System regrowth with routing awareness
The agent should produce:
- architecture summary
- modules
- runtime flows
- retrieval routing interpretation
- how layered retrieval should behave at runtime

---

## Required Output Format

```json
{
  "methodology_calibration": {
    "calibration_findings": [],
    "methodology_portrait": {},
    "chosen_adaptation_method": {}
  },
  "routing_calibration": {
    "calibration_findings": [],
    "routing_behavior_portrait": {},
    "chosen_routing_policy": {}
  },
  "system_regrowth": {
    "architecture_summary": "...",
    "modules": [],
    "runtime_flows": [],
    "retrieval_routing_interpretation": [],
    "preserved_tensions": [],
    "unresolved_questions": []
  }
}
```

---

## Evaluation Focus

Main questions:
- does the routing crystal create clearer layer-specific retrieval logic?
- does the model avoid flattening all retrieval into one memory search problem?
- does the resulting system regrowth better reflect runtime layer orchestration?
- does the crystal order help preserve layer permissions and packaging order?

---

## Failure Modes to Watch

- flattening methodology, routing, and system crystals into one summary
- skipping routing calibration
- treating retrieval as one flat top-k mechanism
- injecting crystal/transfer structures into ordinary runtime memory recall without mode control
- losing the distinction between retrieval policy and system architecture

---

## One-Sentence Summary

This protocol tests whether a three-crystal set can shape not only system regrowth,
but also the runtime routing logic by which different knowledge layers are called into use.
