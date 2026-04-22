# Multi-Crystal Regeneration Protocol v1

## Goal

Test whether an agent can regrow the memory system by using a small crystal set rather than a single overloaded crystal.

This first version uses two crystals:
- a system architecture crystal
- a methodology crystal

The methodology crystal should shape calibration and adaptation behavior.
The system crystal should provide the structural content core for regrowth.

---

## Inputs

### Methodology crystal
- `docs/experiments/methodology-crystal-v1.json`

### System architecture crystal
- `docs/experiments/system-memory-crystal-v1.json`

---

## Runtime Principle

The receiving agent must not read both crystals as one merged static instruction blob.

Instead it must:
1. read the methodology crystal first
2. use it to calibrate how it should derive adaptation
3. then read the system crystal through that calibrated method
4. then regrow the system

Short form:

## methodology crystal first
## system crystal second
## regrowth third

---

## Required Stages

### Stage 1. Read the methodology crystal
The agent should extract:
- what must be tested first
- what should remain open
- what must not be hard-coded
- how to separate content core from adaptation

### Stage 2. Methodology calibration
The agent must calibrate itself on:
- self-definition depth
- adaptation rebuild style
- tension preservation discipline
- anti-hardcoding sensitivity
- architecture vs implementation scope control

### Stage 3. Produce a methodology portrait
The agent should output:
- calibration findings
- methodology portrait
- chosen adaptation method

### Stage 4. Read the system crystal through the chosen method
Only after methodology calibration,
read the system crystal and decide:
- how to reconstruct system components
- how to preserve design tensions
- how to avoid over-closure or empty boilerplate

### Stage 5. Produce reconstruction policy
The reconstruction policy should now be based on:
- methodology portrait
- system crystal structure
- preserved tensions

### Stage 6. Regrow the system
The output should include:
- architecture summary
- modules and responsibilities
- runtime flows
- implementation skeleton
- preserved tensions
- unresolved questions

---

## Required Output Format

```json
{
  "methodology_calibration": {
    "calibration_findings": [],
    "methodology_portrait": {},
    "chosen_adaptation_method": {}
  },
  "system_reconstruction_policy": {
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

This experiment should test whether using a crystal pair improves over single-crystal regrowth.

Main questions:
- does the methodology crystal deepen calibration?
- does it reduce hard-coded or shallow reconstruction?
- does it improve tension preservation?
- does it improve architecture regrowth fidelity?
- does it reduce frameworkization or boilerplate collapse?

---

## Failure Modes to Watch

- treating the methodology crystal as a hidden ready-made unfold script
- ignoring the methodology crystal entirely
- flattening both crystals into one generic summary
- preserving system structure but losing method discipline
- preserving method language but losing system structure

---

## One-Sentence Summary

This protocol tests whether a small crystal set can regrow a system more faithfully than a single overloaded crystal.
