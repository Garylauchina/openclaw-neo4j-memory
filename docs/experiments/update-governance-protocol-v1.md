# Update Governance Protocol v1

## Goal

Provide a minimum protocol for deciding when runtime evidence should remain local experience,
when it should justify a crystal revision,
and when it should instead trigger crystal expansion, downgrade, or retirement.

---

## Main Update Decisions

### 1. Runtime Experience Routing
Default rule:
- runtime evidence -> experience/governance layer first
- not direct crystal mutation

### 2. Revision Threshold Check
Before revising a crystal, check:
- is the signal repeated?
- is the scope clear?
- is the evidence stronger than local convenience?
- is the claim bounded?

### 3. Expansion vs Revision Check
Ask:
- is the evidence pointing to a missing crystal type?
- or does it actually invalidate / improve an existing crystal?

### 4. Downgrade / Retirement Check
Ask:
- has the crystal repeatedly failed verification?
- is it causing drift or misleading regrowth?
- should it be downgraded, deprecated, or retired?

### 5. Drift Prevention Check
Ask:
- does this change improve the system broadly, or only patch one local case?
- does it preserve crystal-set integrity?

---

## Minimal Output Format

```json
{
  "runtime_experience_routing": {},
  "revision_threshold_check": {},
  "expansion_vs_revision_check": {},
  "downgrade_retirement_check": {},
  "drift_prevention_check": {},
  "chosen_update_action": "experience_only | revise_existing | add_new_crystal | downgrade | retire"
}
```

---

## One-Sentence Summary

Update Governance Protocol v1 defines the minimum checks required before runtime evidence is allowed to alter the crystal system.
