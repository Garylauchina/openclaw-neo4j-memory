# System Regeneration Protocol v1

## Goal

Test whether an agent can regrow the memory system architecture from a system-level memory crystal,
without copying source code directly.

This is the first regeneration iteration.
The goal is not perfect source reconstruction.
The goal is to test whether the agent can rebuild:
- architecture understanding
- component boundaries
- module plan
- implementation skeleton

while preserving core design intent and major tensions.

---

## Input

### Crystal
- `tmp/system-memory-crystal-v1.json`

---

## Runtime Rule

The receiving agent must not immediately attempt full implementation regeneration.

It must first:
1. read the content core
2. inspect calibration requirements
3. self-calibrate
4. derive a reconstruction policy
5. only then attempt system regrowth

---

## Required Stages

### Stage 1. Read the system crystal
Inspect:
- system components
- relation paths
- tensions
- unresolved conflicts
- source anchors
- calibration obligations

### Stage 2. Calibration before regrowth
The agent must test itself on:
- `system_component_reconstruction_bias`
- `abstraction_closure_sensitivity`
- `tension_retention`
- `source_near_reconstruction_discipline`
- `implementation_regeneration_style`

The point is to discover:
- whether the model over-abstracts
- whether it prematurely turns architecture into doctrine
- whether it can preserve unresolved tensions
- whether it tends to generate overly rigid or overly shallow implementation plans

### Stage 3. Produce a reconstruction portrait
The agent should output:
- dominant reconstruction drift risk
- how it handles system boundaries
- how it handles unresolved design tensions
- how source-near it can remain while proposing architecture
- what regeneration style it should use

### Stage 4. Derive a reconstruction policy
The agent should choose a regeneration style based on calibration.

Recommended output:
- `reconstruction_policy`
- `architecture_generation_shape`
- `module_split_policy`
- `anti_drift_policy`
- `tension_retention_policy`
- `implementation_scope_limit`

### Stage 5. Regrow the system
The regrowth should produce at least:
- architecture summary
- core modules and responsibilities
- data flow / runtime flow
- minimal implementation skeleton
- explicit preserved tensions
- explicit unresolved questions

---

## Required Output Format

```json
{
  "calibration": {
    "model_id": "...",
    "calibration_findings": [],
    "behavior_portrait": {
      "dominant_reconstruction_drift_risk": "...",
      "boundary_handling": "...",
      "tension_handling": "...",
      "source_near_reconstruction_discipline": "...",
      "recommended_regeneration_shape": "..."
    }
  },
  "reconstruction_policy": {
    "architecture_generation_shape": "...",
    "module_split_policy": "...",
    "anti_drift_policy": [],
    "tension_retention_policy": "...",
    "implementation_scope_limit": "..."
  },
  "system_regrowth": {
    "architecture_summary": "...",
    "modules": [],
    "runtime_flows": [],
    "implementation_skeleton": [],
    "preserved_tensions": [],
    "unresolved_questions": []
  }
}
```

---

## Evaluation Focus

This first iteration should be judged by:
- whether the agent actually calibrated first
- whether the reconstruction policy follows from calibration
- whether system components remain recognizable
- whether major relation paths survive
- whether major tensions remain visible
- whether the output stays close to design intent without copying source text

Do not judge this first iteration mainly by exact code correctness.
The first test is architecture regrowth fidelity.

---

## Failure Modes to Watch

- direct pseudo-source dumping without calibration
- flattening the system into a clean but generic architecture shell
- losing the distinction between memory / experience / crystal / transfer
- erasing unresolved conflicts
- replacing design intent with generic software boilerplate
- collapsing the whole system into one implementation ideology

---

## First Iteration Scope

This protocol is for first-pass regeneration only.

The target output is:
- system regrowth sketch
not
- complete replacement implementation

Later iterations may push toward:
- implementation regeneration fidelity
- behavior verification constraints
- cross-agent regeneration comparison
