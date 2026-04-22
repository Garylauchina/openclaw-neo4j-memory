# Revision-Case Pressure Test v1

## Goal

Apply the update-governance and verification layers to a case where the correct action is genuinely ambiguous:
- revise an existing crystal
- add a new crystal
- keep the issue as experience only

The purpose is to test whether the crystal system can handle revision pressure rather than only expansion pressure.

---

## Reference Layers

### Update governance
- `docs/experiments/update-governance-crystal-v1.json`
- `docs/experiments/update-governance-protocol-v1.md`

### Verification
- `docs/experiments/verification-crystal-v1.json`
- `docs/experiments/verification-protocol-v1.md`

---

## Chosen Ambiguous Case

### Case
The current crystal set now has:
- `schema-definition-crystal-v1`
- `methodology-crystal-v1`
- `crystal-set-schema-draft-v1.md`

A recurring ambiguity remains around:

## whether `schema-definition-crystal-v1` is fully a new meta-protocol crystal,
## or whether part of what it currently carries should instead be represented as a revision of existing schema/methodology structure.

This is a useful pressure case because it is not a clean missing-layer case like safety or recovery.
It sits between:
- schema internalization as a new layer
- refinement of existing methodological or schema relations

---

## Required Review Questions

### 1. Is the observed pressure best classified as:
- missing crystal layer
- weak existing crystal
- weak schema draft only
- experience-only ambiguity

### 2. If a change is needed, should the correct action be:
- `revise_existing`
- `add_new_crystal`
- `experience_only`

### 3. If revision is recommended, what exactly should be revised and why?

### 4. If expansion is recommended, why is revision insufficient?

### 5. Does the current update-governance layer reduce drift risk in this ambiguous case?

### 6. Does the verification layer help bound the claim rather than overreact?

---

## Output Requirement

Return a structured review with sections for:
- case classification
- chosen update action
- revision vs expansion rationale
- drift-risk assessment
- whether this counts as a successful first revision-pressure handling case

---

## One-Sentence Summary

This protocol tests whether the crystal system can handle a real ambiguous revision-vs-expansion case without defaulting to uncontrolled crystal proliferation.
