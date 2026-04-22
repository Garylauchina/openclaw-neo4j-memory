# Compatibility Composition Review Protocol v1

## Goal

Test whether the compatibility layer can make clearer and more disciplined judgments about when crystal sets can be composed, partially composed, kept separate, or require adapters.

---

## Inputs

### Compatibility layer
- `docs/experiments/compatibility-crystal-v1.json`
- `docs/experiments/compatibility-composition-protocol-v1.md`

### Reference current crystal set schema
- `docs/crystal-set-schema-draft-v1.md`

### Review target
- evaluate compatibility logic against the current project crystal set as a self-contained set,
  and against hypothetical future composition with other crystal systems.

---

## Required Review Questions

### 1. Role Compatibility Review
Does the current compatibility layer clearly preserve role distinctions during composition?

### 2. Phase Compatibility Review
Does it clearly preserve phase and ordering constraints?

### 3. Replaceability Review
Does it prevent silent replacement of foundational crystals?

### 4. Conflict Interpretation Review
Does it turn composition failure into structurally interpretable conflict categories?

### 5. Composition Action Review
For likely future composition cases, does it support clear decisions among:
- compose
- partial_compose
- keep_separate
- require_adapter
- reject

---

## Output Requirement

Return a structured review with sections for:
- compatibility findings
- where the layer already gives useful composition discipline
- where compatibility logic remains too abstract
- whether compatibility is sufficiently defined for this prototype phase

---

## One-Sentence Summary

This protocol tests whether the compatibility layer gives the crystal system a meaningful first composition discipline rather than only a conceptual placeholder.
