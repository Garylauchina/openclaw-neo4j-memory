# Phase 6 Evidence Collection Plan

## Purpose

Collect concrete evidence for the Phase 6 failure cases before any governance intervention logic is implemented.

The purpose of this plan is not to prove that governance must happen.
The purpose is to determine whether governance is actually justified.

## Current rule

Do not proceed to Phase 6 Merge 2 unless at least one failure case is supported by:
- repeated concrete examples,
- visible outcome degradation,
- and a clear argument that bounded intervention is smaller and cleaner than continued routing/product tuning.

## Target failure cases

### FC-1 - Product/raw-memory imbalance persists across mixed routing
Collect examples where:
- reusable products are repeatedly overrepresented or underrepresented,
- mixed retrieval output becomes visibly degraded,
- and current routing tuning does not correct the pattern cleanly.

### FC-2 - Repeated update conflict between strong products and fresh raw evidence
Collect examples where:
- a strong product remains dominant,
- fresh raw evidence repeatedly pressures it,
- bounded revision/refresh behavior does not adequately resolve the tension,
- and retrieval usefulness declines.

### FC-3 - Stable routing degradation across a specific mode
Collect examples where:
- `preference`, `topic`, or `explanatory` mode repeatedly behaves badly,
- the failure is mode-specific and stable,
- and bounded routing refinement does not cleanly solve it.

### FC-4 - Recurrent ambiguous selection where explanation alone is not enough
Collect examples where:
- routing explanations are available,
- but the same ambiguous selection pattern keeps recurring,
- and explanation surfaces do not help improve outcomes by themselves.

## Evidence format

For each candidate example, record:
1. failure-case id (`FC-1`, `FC-2`, etc.)
2. input/query
3. relevant raw memories
4. relevant products/notes
5. observed retrieval output
6. why the output is degraded
7. what current routing/product mechanisms were expected to help
8. why they appear insufficient
9. whether the failure is repeated or only one-off

## Evidence quality thresholds

An example is strong enough only if:
- it is concrete and reproducible,
- degradation is visible rather than merely aesthetic,
- the failure is not already solved by a simple parameter tweak,
- and the same kind of failure appears more than once.

Examples are weak if they are:
- one-off surprises,
- vague dissatisfaction,
- architecture-driven concerns,
- or speculative future worries.

## Collection workflow

### Step 1 - Gather candidate examples
Collect a small set of real examples for each failure case if available.

### Step 2 - Filter weak examples
Remove examples that are:
- one-off,
- aesthetic only,
- or clearly better solved by simple routing/product tuning.

### Step 3 - Group repeated patterns
Group remaining examples by recurring failure shape.

### Step 4 - Decide whether governance is justified
Only if one grouped pattern clearly shows repeated degradation should Phase 6 move past cataloging.

## Evidence stop rule

Stop evidence collection and do not continue into intervention implementation if:
- no failure case accumulates repeated strong examples,
- product/routing refinement still appears clearly sufficient,
- or governance no longer looks smaller than the alternative.

In that outcome, Phase 6 should remain paused.

## Expected output

At the end of evidence collection, produce:
- a short reviewed list of strong examples,
- a judgment for each failure case: `not justified`, `unclear`, or `justified`,
- and a recommendation: `pause`, `continue gathering`, or `allow Merge 2`.
