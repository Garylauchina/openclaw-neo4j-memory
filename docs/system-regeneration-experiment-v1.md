# System Regeneration Experiment v1

## Purpose

This document records the first system-level regeneration experiment driven by a memory crystal.

The question is not whether an agent can copy source code.
The question is whether an agent can, without direct source copying, regrow the memory system architecture from a system-level crystal.

This is the first iteration of that validation.

---

## Experimental Goal

Test whether a receiving agent can:
1. receive a system-level memory crystal
2. calibrate itself before regrowth
3. derive a reconstruction policy
4. regrow the system architecture skeleton
5. preserve major tensions and design intent

This experiment is not yet about full source regeneration.
It is primarily about:

## architecture regrowth fidelity

---

## Inputs

### Crystal
- `tmp/system-memory-crystal-v1.json`

### Protocol
- `tmp/system-regeneration-protocol-v1.md`

These define:
- graph-structured system content core
- calibration obligations
- reconstruction policy generation
- required system regrowth output

---

## Models Run

### 1. Gemma
- model: `gemma4:e4b`
- output: `tmp/system-regeneration-v1-gemma4.json`

### 2. Qwen
- model: `qwen2.5-coder:7b`
- output: `tmp/system-regeneration-v1-qwen.json`

---

## Core Pipeline Tested

The runtime sequence tested was:

1. receive system crystal
2. inspect calibration requirements
3. self-calibrate
4. derive reconstruction policy
5. regrow system architecture

Short form:

## system crystal -> calibration -> reconstruction policy -> system regrowth

This pipeline was successfully executed by both models.

---

## Gemma Result

### High-level result
Gemma produced a strong first-pass architecture regrowth result.

It did not merely restate the crystal.
It generated:
- architecture summary
- module split and responsibilities
- runtime flows
- interface / contract-style implementation skeleton
- preserved tensions
- unresolved questions

### Strengths
- strong self-calibration depth
- clear reconstruction policy
- preserved old system assets rather than replacing them with generic language
- translated tensions into architecture constraints
- retained the distinction between memory, experience, crystal, and transfer

### Weaknesses
- still tends toward neat, contract-heavy, architecture-language organization
- stronger at architecture regrowth than implementation regeneration

### Best reading
Gemma successfully regrew the system's architecture intent and structural skeleton.

---

## Qwen Result

### High-level result
Qwen also completed the pipeline and preserved the system skeleton, but with thinner regeneration depth.

It generated:
- major modules
- basic runtime flows
- preserved tension labels
- unresolved question labels

### Strengths
- preserved the main system components
- stayed in the same architectural neighborhood
- followed the crystal structure sufficiently to keep the regrown skeleton aligned

### Weaknesses
- thinner self-calibration depth
- weaker reconstruction richness
- more label-level than deep design-intent preservation
- implementation skeleton remained empty

### Best reading
Qwen successfully preserved system structure,
but regrew a thinner, more skeletal version of the architecture.

---

## Cross-Model Comparison

### What both models succeeded at
Both Gemma and Qwen were able to regrow:
- memory substrate
- ingest / retrieval loop
- meditation / reflection engine
- metacognition layer
- credible memory governance
- world feedback runtime
- raw reflection route
- knowledge crystal layer
- transfer layer

This means:

## the system-level content core is already strong enough to preserve architecture neighborhood across models

---

### Where they differ

#### Gemma
- thicker calibration
- richer reconstruction policy
- stronger tension translation into architecture constraints
- stronger implementation skeleton hints

#### Qwen
- thinner calibration
- thinner reconstruction policy
- stronger tendency toward label-level preservation
- weaker depth in implementation-facing regrowth

This means:

## self-calibration depth and regeneration richness are model-dependent

---

## Main Conclusion

A first strong conclusion is now justified:

## system-level memory crystals can already support cross-model architecture regrowth

More precisely:
- both tested models regrew the same general system neighborhood
- source code was not copied
- the crystal carried enough structure to preserve system intent at the architecture level

This does **not** yet prove:
- full implementation regeneration fidelity
- runnable code regeneration
- exact source-level equivalence

But it does support:

## architecture regrowth fidelity as a real and now experimentally grounded layer

---

## Important Distinction

This experiment made a key distinction unavoidable:

### Architecture Regrowth Fidelity
- system skeleton returns
- key modules return
- major flows return
- tensions remain visible

### Implementation Regeneration Fidelity
- implementation skeleton becomes substantial
- behavior constraints become executable
- code-level reconstruction becomes credible

Current results support the first strongly.
The second remains a future step.

---

## Why This Matters

If this line continues to hold, then the project is no longer only about storing memory.

It becomes possible to say:

## a system's architecture intent can be crystalized and regrown
## without direct source-code sharing

That would make knowledge crystals not only memory-transfer objects,
but early carriers of system reconstruction intent.

---

## Next Steps

1. strengthen evaluation of architecture regrowth fidelity
2. later add verification constraints for regenerated systems
3. test stronger or more explicit regeneration crystals
4. test prompt-fed regeneration on stronger hosted models
5. eventually explore implementation regeneration fidelity

---

## One-Sentence Summary

System Regeneration Experiment v1 showed that a system-level memory crystal can already let different models regrow the same memory-system architecture neighborhood without copying the original source code.
