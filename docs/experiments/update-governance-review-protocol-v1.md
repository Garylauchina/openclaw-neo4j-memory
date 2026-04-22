# Update Governance Review Protocol v1

## Goal

Test whether the update-governance layer can make clearer and more disciplined decisions about when runtime evidence should stay local, revise an existing crystal, add a new crystal, downgrade, or retire.

---

## Inputs

### Update-governance layer
- `docs/experiments/update-governance-crystal-v1.json`
- `docs/experiments/update-governance-protocol-v1.md`

### Reference crystal-gap history
- `docs/gap-driven-crystal-expansion-v1.md`
- `docs/eight-crystal-soft-isolated-self-regrowth-experiment-v1.md`

---

## Required Review Questions

### 1. Runtime Experience Routing Review
Which recent observations should remain experience/governance only rather than crystal edits?

### 2. Revision Threshold Review
Which known gaps meet a threshold for crystal revision or addition rather than local interpretation only?

### 3. Expansion vs Revision Review
For known recent gaps, should the correct action have been:
- revise an existing crystal
- add a new crystal
- keep as experience only

### 4. Downgrade / Retirement Review
Is there evidence that any current crystal should be downgraded, deprecated, or retired?

### 5. Drift Prevention Review
Does the current update-governance layer actually reduce the risk of convenience-driven crystal drift?

---

## Output Requirement

Return a structured review with sections for:
- governance findings
- correctly classified updates
- still ambiguous update cases
- whether update-governance improves crystal-iteration discipline

---

## One-Sentence Summary

This protocol tests whether the update-governance layer meaningfully improves how the crystal system decides when and how to change itself.
