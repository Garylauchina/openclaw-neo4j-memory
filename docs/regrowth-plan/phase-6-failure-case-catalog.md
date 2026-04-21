# Phase 6 Failure-Case Catalog

This file records the concrete failure cases that could justify the first carefully bounded governance layer.

## Rule of interpretation

A failure case belongs here only if:
- it is concrete rather than speculative,
- it is not already well handled by the current write/product/routing layers,
- and a bounded intervention point seems more appropriate than further product/routing tuning alone.

If a case does not meet those tests, it should not justify governance expansion.

## Failure Case FC-1 - Product/raw-memory imbalance persists across mixed routing

### Pattern
In some retrieval situations, reusable products may remain systematically overrepresented or underrepresented even after the current mixed-routing balancing logic is applied.

### Why current layers may be insufficient
Phase 5 introduced bounded routing balance and explicit coordination rules, but those rules remain compact and mode-level.
If the same imbalance pattern keeps recurring across repeated examples, simple routing tuning may become brittle.

### Why this may justify bounded governance
A very small intervention point could help when repeated imbalance is detected and the current routing layer keeps producing degraded mixed outputs.

### Governance threshold
This case should justify governance only if repeated mixed-routing examples show that:
- the current routing layer cannot recover acceptable balance with small tuning,
- and the failure is stable rather than anecdotal.

## Failure Case FC-2 - Repeated update conflict between strong products and fresh raw evidence

### Pattern
A strong reusable product may continue dominating even when fresh raw evidence repeatedly suggests the product should be revised, weakened, or temporarily deferred.

### Why current layers may be insufficient
Phase 4 and Phase 5 support product refresh, bounded revision, and mixed routing, but they do not yet provide a distinct intervention point for repeated product/raw tension.

### Why this may justify bounded governance
A small intervention rule may be needed when repeated fresh evidence consistently pressures an existing product and product-refresh behavior is not enough to prevent degradation.

### Governance threshold
This case should justify governance only if:
- fresh evidence repeatedly conflicts with an established product,
- current revision/update paths do not resolve the tension adequately,
- and retrieval usefulness visibly degrades as a result.

## Failure Case FC-3 - Stable routing degradation across a specific mode

### Pattern
A specific routing mode such as `preference` or `explanatory` may repeatedly underperform in a consistent way that current mode-aware bonuses and balance rules do not fix.

### Why current layers may be insufficient
Phase 5 added mode-aware behavior, but it remains bounded and relatively heuristic.
If a mode repeatedly fails in consistent, identifiable ways, further local bonus tuning may stop being the right tool.

### Why this may justify bounded governance
A minimal intervention point could be justified if the system needs a small mode-specific safeguard or correction trigger.

### Governance threshold
This case should justify governance only if:
- the failure is repeated and mode-specific,
- the problem remains after bounded routing refinement,
- and a minimal correction rule is clearly smaller than continued ad hoc tuning.

## Failure Case FC-4 - Recurrent ambiguous selection where explanation alone is not enough

### Pattern
The system may repeatedly produce mixed outputs where the choice between product and raw evidence remains ambiguous in a way that explanation surfaces can describe but not improve.

### Why current layers may be insufficient
Phase 5 explanations make routing more inspectable, but inspectability alone does not resolve repeated ambiguous behavior.
If the same ambiguity keeps returning, an intervention point may be needed.

### Why this may justify bounded governance
A bounded intervention rule could help break recurring ambiguous selection patterns when explanation no longer helps improve outcomes by itself.

### Governance threshold
This case should justify governance only if:
- the ambiguity is repeated and recognizable,
- current explanation and routing refinement do not reduce it,
- and intervention is smaller than introducing a broader routing policy system.

## Cases explicitly not sufficient by themselves

These do NOT justify governance by themselves:
- a single poor retrieval result
- isolated note/product awkwardness
- one-off ranking surprises
- speculative future edge cases
- architectural desire for cleaner layers
- frustration that the system still feels heuristic

These should be handled by continued product/routing refinement unless repeated failure pressure clearly proves otherwise.

## Current conclusion

At this stage, Phase 6 governance work is justified only conditionally.

The catalog shows that possible governance-worthy failures exist in principle, but each case still requires actual repeated evidence before implementation should proceed.

This means:
- Phase 6 Merge 1 is valid as failure-case cataloging,
- but later Phase 6 merges should proceed only if concrete examples are gathered for one or more failure cases above.
