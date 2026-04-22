# Phase 6 Evidence Log

This file records candidate examples for the Phase 6 failure cases.

Use the structure below for each example.
Do not treat an example as governance-justifying until it is concrete, repeated, and visibly degrading outcomes.

---

## Example Template

### Example ID
- `EXAMPLE-ID:`

### Failure Case
- `FAILURE-CASE:` (`FC-1` / `FC-2` / `FC-3` / `FC-4`)

### Input / Query
- `INPUT:`

### Relevant Raw Memories
- `RAW-MEMORIES:`

### Relevant Products / Notes
- `PRODUCTS-NOTES:`

### Observed Retrieval Output
- `OBSERVED-OUTPUT:`

### Why Output Is Degraded
- `DEGRADATION:`

### What Current Mechanisms Were Expected To Help
- `EXPECTED-MECHANISMS:`

### Why They Appear Insufficient
- `INSUFFICIENCY:`

### Repeat Status
- `REPEAT-STATUS:` (`one-off` / `repeated` / `unclear`)

### Initial Judgment
- `INITIAL-JUDGMENT:` (`weak` / `unclear` / `strong`)

### Notes
- `NOTES:`

---

## Current Recorded Examples

### Example ID
- `EXAMPLE-ID:` `fc1-mixed-balance-edge-001`

### Failure Case
- `FAILURE-CASE:` `FC-1`

### Input / Query
- `INPUT:` `How does Neo4j help retrieval?`

### Relevant Raw Memories
- `RAW-MEMORIES:` Multiple stable raw memories about Neo4j retrieval, graph recall, relation modeling, and provenance.

### Relevant Products / Notes
- `PRODUCTS-NOTES:` A Neo4j reusable product with helpful feedback and product-role bonuses.

### Observed Retrieval Output
- `OBSERVED-OUTPUT:` Product appears in mixed retrieval output, but raw memories can still dominate the top ranks even when the product is clearly useful.

### Why Output Is Degraded
- `DEGRADATION:` The mixed output is not obviously broken, but it suggests a possible edge where product usefulness remains underexpressed relative to accumulated product shaping.

### What Current Mechanisms Were Expected To Help
- `EXPECTED-MECHANISMS:` Mixed routing balance, product-role bonus, helpful feedback bonus, routing coordination rules.

### Why They Appear Insufficient
- `INSUFFICIENCY:` Current mechanisms can surface the product, but may still leave product/raw representation somewhat unstable across similar cases.

### Repeat Status
- `REPEAT-STATUS:` `unclear`

### Initial Judgment
- `INITIAL-JUDGMENT:` `weak`

### Notes
- `NOTES:` This example is useful as an observation target, but not yet strong enough to justify governance.

---

### Example ID
- `EXAMPLE-ID:` `fc3-explanatory-mode-001`

### Failure Case
- `FAILURE-CASE:` `FC-3`

### Input / Query
- `INPUT:` `Why does Neo4j help retrieval?`

### Relevant Raw Memories
- `RAW-MEMORIES:` Stable raw memories containing relation-rich explanations of Neo4j retrieval and graph structure.

### Relevant Products / Notes
- `PRODUCTS-NOTES:` Summary-like or retrieval-anchor products derived from repeated Neo4j evidence.

### Observed Retrieval Output
- `OBSERVED-OUTPUT:` Explanatory mode can now surface both products and raw evidence, but the balance still depends on bounded heuristic bonuses.

### Why Output Is Degraded
- `DEGRADATION:` No severe failure is shown yet, but the mode still appears heuristic and could degrade if explanatory patterns become more varied.

### What Current Mechanisms Were Expected To Help
- `EXPECTED-MECHANISMS:` Explanatory mode detection, explanatory bonus, routing decision for explanatory mode, mixed routing balance.

### Why They Appear Insufficient
- `INSUFFICIENCY:` Current mechanisms seem adequate for the tested case, but there is not yet enough evidence to show robustness across repeated explanatory failures.

### Repeat Status
- `REPEAT-STATUS:` `one-off`

### Initial Judgment
- `INITIAL-JUDGMENT:` `weak`

### Notes
- `NOTES:` This is currently more a monitored edge than a governance-justifying failure.

---

---

### Example ID
- `EXAMPLE-ID:` `fc2-product-fresh-evidence-tension-001`

### Failure Case
- `FAILURE-CASE:` `FC-2`

### Input / Query
- `INPUT:` Fresh evidence revises an established product preference, e.g. old preference says long answers, new evidence says concise answers.

### Relevant Raw Memories
- `RAW-MEMORIES:` Earlier preference memory plus newer stable raw memory carrying revised preference evidence.

### Relevant Products / Notes
- `PRODUCTS-NOTES:` Preference-oriented product built from earlier evidence and later refreshed through bounded revision/update behavior.

### Observed Retrieval Output
- `OBSERVED-OUTPUT:` Current lightweight revision paths can update the product, but pressure remains if a strong product has already accumulated helpfulness and stable-source weight.

### Why Output Is Degraded
- `DEGRADATION:` No strong degradation has been observed yet, but there is a plausible tension where refreshed product state may lag behind fresh raw evidence pressure in repeated cases.

### What Current Mechanisms Were Expected To Help
- `EXPECTED-MECHANISMS:` Supersession links, bounded revision/update handling, note refresh, product refresh, quality signals.

### Why They Appear Insufficient
- `INSUFFICIENCY:` Current mechanisms appear sufficient for single revision flows, but repeated product/raw tension has not yet been tested enough to know whether they remain adequate.

### Repeat Status
- `REPEAT-STATUS:` `unclear`

### Initial Judgment
- `INITIAL-JUDGMENT:` `weak`

### Notes
- `NOTES:` This is currently a plausible pressure pattern, not a demonstrated governance-worthy failure.

---

### Example ID
- `EXAMPLE-ID:` `fc4-ambiguous-selection-001`

### Failure Case
- `FAILURE-CASE:` `FC-4`

### Input / Query
- `INPUT:` A query where both reusable products and raw evidence appear relevant, but neither clearly dominates, e.g. mixed explanatory/preference intent.

### Relevant Raw Memories
- `RAW-MEMORIES:` Raw memories containing specific evidence fragments relevant to both preference and explanation dimensions.

### Relevant Products / Notes
- `PRODUCTS-NOTES:` Reusable products that summarize part of the same evidence space but do not fully dominate the case.

### Observed Retrieval Output
- `OBSERVED-OUTPUT:` Current routing explanations can describe selected kind, routing mode, and balance summary, but ambiguous mixed selections can still remain underdetermined.

### Why Output Is Degraded
- `DEGRADATION:` The system can explain the ambiguity, but explanation alone may not improve the underlying choice quality in repeated cases.

### What Current Mechanisms Were Expected To Help
- `EXPECTED-MECHANISMS:` Mixed routing balance, mode-aware behavior, routing summaries, coordination reasons, bounded metadata.

### Why They Appear Insufficient
- `INSUFFICIENCY:` Current mechanisms make ambiguity inspectable, but there is not yet enough evidence that they reduce recurrent ambiguity when it matters.

### Repeat Status
- `REPEAT-STATUS:` `unclear`

### Initial Judgment
- `INITIAL-JUDGMENT:` `weak`

### Notes
- `NOTES:` This remains a monitoring case rather than a governance trigger.

## Review Summary

### FC-1
- Status: `not yet evidenced`
- Notes: No repeated concrete examples recorded yet.

### FC-2
- Status: `not yet evidenced`
- Notes: No repeated concrete examples recorded yet.

### FC-3
- Status: `not yet evidenced`
- Notes: No repeated concrete examples recorded yet.

### FC-4
- Status: `not yet evidenced`
- Notes: No repeated concrete examples recorded yet.

---

## Current Recommendation

`pause`

Reason:
- failure cases are cataloged,
- but concrete repeated evidence has not yet been logged,
- so Phase 6 is still not admitted into intervention implementation.
