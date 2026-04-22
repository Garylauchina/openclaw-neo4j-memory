# Verification-Aware Regrowth Review Protocol v1

## Goal

Test whether the newly added verification layer improves how crystal-driven regrowth outcomes are judged.

This is not a new regrowth experiment from scratch.
It is a structured verification review over the current crystal-regrowth line.

---

## Inputs

### Verification layer
- `docs/experiments/verification-crystal-v1.json`
- `docs/experiments/verification-protocol-v1.md`

### Reference experiment summaries
- `docs/five-crystal-soft-isolated-self-regrowth-experiment-v1.md`
- `docs/eight-crystal-soft-isolated-self-regrowth-experiment-v1.md`

---

## Required Review Questions

### 1. Problem Identity Verification
Did the regrowth results preserve the actual project problem and its scope boundaries?

### 2. Architecture Regrowth Verification
Did the regrowth results preserve the major system layers, mainline structure, and module responsibilities?

### 3. Protocol Fidelity Verification
Did the regrowth results preserve:
- ordering vs framing distinction
- methodology role
- routing role
- safety boundary role
- recovery/resilience role

### 4. Self-Description Verification
Did the regrowth results preserve:
- schema internality
- crystal role distinctions
- failure interpretation logic

### 5. Success-Claim Verification
Were the success claims bounded correctly?
In particular:
- architecture regrowth vs implementation regeneration
- plausible reconstruction vs protocol fidelity
- partial recovery vs deployment-facing recovery

### 6. Failure Interpretation Verification
Does the verification layer produce a clearer diagnosis of what remains missing?

---

## Output Requirement

Return a structured review with sections for:
- verification findings
- improved judgments relative to pre-verification framing
- still-weak verification areas
- next required experiment or crystal

---

## One-Sentence Summary

This protocol tests whether the verification layer makes crystal-regrowth evaluation more explicit, bounded, and diagnostically useful.
