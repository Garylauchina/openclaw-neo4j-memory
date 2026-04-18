# Compatibility Composition Protocol v1

## Goal

Provide a minimum protocol for deciding whether crystal sets can be composed, partially composed, kept separate, or require adapters.

---

## Main Compatibility Checks

### 1. Role Compatibility Check
Check whether the crystal sets expose compatible role structures:
- meta-protocol
- reasoning-path
- protocol
- content

### 2. Phase Compatibility Check
Check whether the crystal sets can coexist in:
- pre-ingestion
- runtime
- regrowth
without incompatible sequencing assumptions.

### 3. Dependency Fit Check
Check whether declared dependencies are compatible or conflicting.

### 4. Replaceability Check
Check whether a crystal can be substituted,
or whether it should remain foundational and non-replaceable.

### 5. Conflict Interpretation Check
If composition fails, interpret whether the cause is:
- incompatible framing
- incompatible ordering
- incompatible dependency assumptions
- missing adapter layer
- non-replaceable foundation conflict

---

## Minimal Output Format

```json
{
  "role_compatibility_check": {},
  "phase_compatibility_check": {},
  "dependency_fit_check": {},
  "replaceability_check": {},
  "conflict_interpretation_check": {},
  "chosen_composition_action": "compose | partial_compose | keep_separate | require_adapter | reject"
}
```

---

## One-Sentence Summary

Compatibility Composition Protocol v1 defines the minimum checks required before crystal systems are combined, substituted, or explicitly kept apart.
