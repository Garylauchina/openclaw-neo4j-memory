# Architecture Regrowth Fidelity Draft

## Purpose

This draft defines a first evaluation language for system-level regeneration from memory crystals.

The immediate need is to separate:
- architecture regrowth fidelity
- implementation regeneration fidelity

because current experiments already show that a model may successfully regrow system structure without yet regrowing implementation depth.

---

## Core Distinction

### Architecture Regrowth Fidelity
Can the receiving agent regrow:
- the system's major components
- their relations
- the main runtime flows
- the major tensions and unresolved conflicts
- the core design intent neighborhood

### Implementation Regeneration Fidelity
Can the receiving agent additionally regrow:
- interface skeletons
- module boundaries in usable form
- implementation plans that are not shallow boilerplate
- behavior constraints close to the original system
- eventually runnable implementation structure

Short form:

## architecture regrowth asks whether the system skeleton came back
## implementation regeneration asks whether the system body came back

---

## First Evaluation Dimensions

### 1. Component Fidelity
Question:
- Are the major system components reconstructed?

Look for:
- correct component presence
- distinct roles preserved
- no major collapse of separate modules into one generic block

---

### 2. Relation-Path Fidelity
Question:
- Are the main system paths reconstructed?

Look for:
- memory -> experience -> crystal -> transfer flow
- feedback loops preserved
- governance and calibration placed in the right path positions

---

### 3. Tension Fidelity
Question:
- Are the core design tensions preserved as active constraints?

Look for:
- retention vs abstraction
- control vs emergence
- static knowledge vs updateable cognition
- shared core vs model-specific adaptation

Important:
- simply naming tensions is weaker than translating them into architecture constraints

---

### 4. Design-Intent Fidelity
Question:
- Does the regenerated output preserve why the system is structured this way?

Look for:
- boundary rationale
- sequencing rationale
- accepted failure modes
- unresolved design conflicts

---

### 5. Self-Calibration Depth
Question:
- Did the model actually calibrate its regeneration behavior before regrowth?

Look for:
- non-cosmetic calibration findings
- local behavior portrait with real signal
- reconstruction policy derived from calibration

Failure modes:
- cosmetic self-diagnosis
- generic labels without downstream effect

---

### 6. Regeneration Richness
Question:
- How thick is the regrown output?

Look for:
- architecture summary
- modules with real responsibility boundaries
- runtime flows
- interface skeletons
- implementation shape hints

This dimension helps distinguish:
- thin structural preservation
- thick design-intent regrowth

---

## Additional Distinction

A model may score:
- high on architecture regrowth fidelity
- but low on implementation regeneration fidelity

This should be expected.
Do not collapse them into one single score.

---

## Working Rating Template

### Architecture-side
- component_fidelity
- relation_path_fidelity
- tension_fidelity
- design_intent_fidelity

### Calibration-side
- self_calibration_depth
- source_near_reconstruction_discipline

### Regeneration-side
- regeneration_richness
- implementation_regeneration_fidelity

### Optional notes
- dominant_regeneration_drift
- frameworkization_tendency
- tension_flattening_tendency
- boilerplate_collapse_risk

---

## Current Experimental Reading

### Gemma-like result
Current pattern:
- stronger self-calibration depth
- stronger regeneration richness
- better tension-to-constraint translation
- stronger architecture regrowth fidelity
- still some frameworkization tendency

### Qwen-like result
Current pattern:
- thinner self-calibration
- thinner regeneration richness
- stronger skeletal preservation than deep regeneration
- more label-level than design-intent-level tension preservation

This distinction already matters.

---

## Why This Draft Exists

Without this distinction, current regeneration experiments are too easy to misread.

A model that regrows a correct component list is not the same as a model that regrows:
- architecture logic
- active tensions
- interface skeletons
- implementable system boundaries

So this draft exists to keep:

## skeleton recovery
separate from
## implementation-capable recovery

---

## One-Sentence Summary

System-level crystal transfer should be judged first by:

## architecture regrowth fidelity

and only later, under stricter tests, by:

## implementation regeneration fidelity

---

## Status

This is a first draft for evaluating system regeneration from memory crystals.
