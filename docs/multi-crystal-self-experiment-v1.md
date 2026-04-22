# Multi-Crystal Self-Experiment v1

## Purpose

This document records the first multi-crystal self-experiment.

Unlike the earlier single-crystal system-regeneration experiment,
this run tests whether a methodology crystal can shape how an agent enters a system crystal before regrowth.

The key hypothesis is:

## the runtime protocol should not simply be
## receive crystal -> unfold

but increasingly:

## receive methodology crystal -> calibrate -> derive adaptation method -> read system crystal -> regrow

---

## Inputs

### Methodology crystal
- `docs/experiments/methodology-crystal-v1.json`

### System crystal
- `docs/experiments/system-memory-crystal-v1.json`

### Protocol
- `docs/experiments/multi-crystal-regeneration-protocol-v1.md`

### Model
- `openai-codex/gpt-5.4`
- prompt-fed self-experiment

---

## Experimental Question

Can a small crystal set outperform a single overloaded crystal by separating:
- method
- structure
- adaptation

more clearly?

In this first run, the question is specifically:

## does the methodology crystal materially change how the model enters the system crystal?

---

## Observed Result

### 1. The methodology crystal was not treated as redundant text
The model did not simply merge both crystals into one flat summary.
Instead it first extracted from the methodology crystal:
- self-definition through testing
- content core vs adaptation layer
- pre-ingestion calibration
- anti-hardcoding boundary
- architecture regrowth vs implementation regeneration

This changed the staging of the run.

---

### 2. The model explicitly separated four layers of activity
The multi-crystal run showed a clearer distinction between:
- methodology constraints
- system structural content
- calibration results
- adaptation / reconstruction policy

This is stronger than the earlier single-crystal behavior,
where the model could still move too quickly from crystal content to architecture restatement.

---

### 3. Regrowth became more protocol-aware and less direct
The model first defined:
- how it should calibrate itself
- what method it should use for reconstruction
- what tensions it must preserve
- what not to collapse into a fixed script

Only then did it read the system crystal and regrow the memory-system architecture.

This suggests the methodology crystal is doing real work.

---

## Main Working Conclusion

The first multi-crystal self-experiment supports a stronger runtime interpretation:

## methodology crystal first,
## system crystal second,
## regrowth third

The multi-crystal path appears more faithful to the intended runtime behavior than a single large system crystal.

Why:
- method is separated from structure
- calibration is separated from regrowth
- adaptation is derived rather than silently assumed

---

## Why This Matters

If this continues to hold, then the crystal runtime protocol may need to be rethought.

Instead of:
- receive crystal
- unfold crystal

The more faithful protocol may be:
- receive methodology crystal
- run calibration
- derive local adaptation method
- then receive or interpret the system crystal
- then regrow the system

That means a crystal system may require:
- structural crystals
- methodological crystals
- later routing crystals

rather than only one monolithic transfer object.

---

## Current Interpretation

At the current stage, the first crystal set is becoming:

- `system-memory-crystal-v1`
- `methodology-crystal-v1`
- later `retrieval-routing-crystal-v1`

This suggests the next system iteration should be built around:

## a small crystal cluster

not a single total crystal.

---

## Current Risk

This result is promising, but should not yet be over-generalized.

What is currently supported:
- methodology crystals can shape entry into system crystals
- multi-crystal runtime sequencing can be meaningful

What is not yet fully proven:
- that calibration method must always be embedded as crystal content
- that every model benefits equally from the same crystal order
- that multi-crystal always beats single-crystal on all tasks

So the current claim should remain experimentally grounded, not prematurely doctrinal.

---

## One-Sentence Summary

Multi-Crystal Self-Experiment v1 suggests that the correct runtime unit may be a crystal set, where the methodology crystal shapes calibration and adaptation before the system crystal is used for regrowth.
