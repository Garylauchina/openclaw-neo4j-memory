# Composition-Case Pressure Test v1

## Goal

Apply the compatibility layer to a plausible but not clean external crystal-set composition case.

The purpose is to test whether the crystal system can make a stable composition judgment under real ambiguity rather than only under abstract schema rules.

---

## Reference Layers

### Compatibility layer
- `docs/experiments/compatibility-crystal-v1.json`
- `docs/experiments/compatibility-composition-protocol-v1.md`
- `docs/experiments/compatibility-composition-review-protocol-v1.md`

### Current crystal set schema
- `docs/crystal-set-schema-draft-v1.md`

### External toy crystal set
- `docs/experiments/toy-external-crystal-set-v1.json`

---

## Chosen Composition Case

The external toy set is intentionally designed to be:
- not fully compatible
- not obviously rejectable
- role-overlapping with the current project set
- weaker in framing/routing discipline than the current project set

This makes it a useful first pressure case for deciding among:
- `compose`
- `partial_compose`
- `require_adapter`
- `reject`

---

## Required Review Questions

### 1. Role Compatibility
Are the external toy crystals role-compatible with the current set, or do they create role confusion?

### 2. Phase Compatibility
Can the toy set coexist with the current pre-ingestion/runtime split without breaking ordering assumptions?

### 3. Replaceability
Would composing the toy crystals imply unsafe silent replacement of current foundational crystals?

### 4. Conflict Interpretation
If composition is limited or blocked, what is the real reason:
- framing conflict
- ordering conflict
- dependency mismatch
- non-replaceable foundation conflict
- adapter need

### 5. Chosen Composition Action
Given the current evidence, what is the right action:
- `compose`
- `partial_compose`
- `keep_separate`
- `require_adapter`
- `reject`

---

## Output Requirement

Return a structured review with sections for:
- case classification
- chosen composition action
- composition rationale
- conflict / adapter assessment
- whether this counts as a successful first composition-pressure handling case

---

## One-Sentence Summary

This protocol tests whether the compatibility layer can make a stable and interpretable judgment in a partially compatible external crystal-set case.
