# Crystal Set Schema Draft v1

## Purpose

This draft makes explicit the minimum crystal-set structure that has already been forced out by recent experiments.

It is intentionally narrow.
It does not try to finalize the entire long-term crystal architecture.
It only crystallizes the minimum object-level schema that now appears stable enough to name.

---

## Why This Draft Exists

Recent experiments no longer support viewing crystals as a flat bundle of knowledge files.
They now support at least the following distinctions:

- reasoning-path crystals
- protocol crystals
- content crystals
- ingestion order
- protocol position
- runtime role
- failure-driven crystal expansion

This means the crystal set now behaves more like a protocol architecture than a simple content package.

---

## Minimal Crystal Object Fields

Each crystal should now be describable with at least the following fields.

### `crystal_id`
Unique crystal identifier.

### `crystal_type`
High-level role of the crystal.

Current working values:
- `reasoning_path`
- `protocol`
- `content`

### `protocol_phase`
When the crystal mainly acts.

Current working values:
- `pre-ingestion`
- `runtime`
- `regrowth`
- `cross-phase`

### `requires_prior`
List of crystals that should be read or activated before this one.

### `establishes_frame_for`
List of crystals, layers, or runtime behaviors whose interpretation this crystal shapes.

### `runtime_role`
Operational role during runtime or regrowth.

Examples:
- `problem-framing`
- `evolution-framing`
- `ingestion-calibration`
- `layer-routing`
- `safety-boundary`
- `resilience-recovery`
- `system-content`

### `depends_on`
Broader dependency relations that are not strictly ordering constraints.

### `expansion_reason`
Why this crystal exists.

Current useful values:
- `mainline seed`
- `runtime protocol completion`
- `failure-driven expansion`
- `transfer fidelity support`

---

## Minimal Crystal Set Object

A crystal set should be describable with at least:

### `set_id`
Identifier for the set.

### `purpose`
What this set is meant to support.

### `crystals`
List of crystal objects.

### `reading_order`
The recommended topological read/activation order.

### `phase_groups`
A grouping by protocol phase.

### `failure_interpretation_rule`
How to interpret regrowth or runtime failure.

Example values:
- `model weakness only`
- `possible missing crystal`
- `possible missing dependency`
- `possible weak reasoning-path compression`
- `possible weak protocol-layer crystallization`

---

## Working JSON Shape

```json
{
  "set_id": "project-crystal-set-v1",
  "purpose": "soft-isolated project regrowth and runtime protocol reconstruction",
  "reading_order": [
    "problem-definition-crystal-v1",
    "architecture-evolution-crystal-v1",
    "methodology-crystal-v1",
    "retrieval-routing-crystal-v1",
    "safety-boundary-crystal-v1",
    "recovery-resilience-crystal-v1",
    "system-memory-crystal-v1"
  ],
  "phase_groups": {
    "pre-ingestion": [
      "problem-definition-crystal-v1",
      "architecture-evolution-crystal-v1",
      "methodology-crystal-v1"
    ],
    "runtime": [
      "retrieval-routing-crystal-v1",
      "safety-boundary-crystal-v1",
      "recovery-resilience-crystal-v1"
    ],
    "regrowth": [
      "system-memory-crystal-v1"
    ]
  },
  "failure_interpretation_rule": [
    "possible missing crystal",
    "possible missing dependency",
    "possible weak reasoning-path compression",
    "possible weak protocol-layer crystallization"
  ],
  "crystals": []
}
```

---

## Current Seven-Crystal Working Instance

Below is the current working seven-crystal set,
expressed in the new schema language.

```json
{
  "set_id": "project-crystal-set-v1",
  "purpose": "project-level architecture regrowth plus deployment-facing runtime protocol reconstruction",
  "reading_order": [
    "problem-definition-crystal-v1",
    "architecture-evolution-crystal-v1",
    "methodology-crystal-v1",
    "retrieval-routing-crystal-v1",
    "safety-boundary-crystal-v1",
    "recovery-resilience-crystal-v1",
    "system-memory-crystal-v1"
  ],
  "phase_groups": {
    "pre-ingestion": [
      "problem-definition-crystal-v1",
      "architecture-evolution-crystal-v1",
      "methodology-crystal-v1"
    ],
    "runtime": [
      "retrieval-routing-crystal-v1",
      "safety-boundary-crystal-v1",
      "recovery-resilience-crystal-v1"
    ],
    "regrowth": [
      "system-memory-crystal-v1"
    ]
  },
  "failure_interpretation_rule": [
    "possible missing crystal",
    "possible missing dependency",
    "possible weak reasoning-path compression",
    "possible weak protocol-layer crystallization"
  ],
  "crystals": [
    {
      "crystal_id": "problem-definition-crystal-v1",
      "crystal_type": "reasoning_path",
      "protocol_phase": "pre-ingestion",
      "requires_prior": [],
      "establishes_frame_for": ["architecture-evolution-crystal-v1", "system-memory-crystal-v1"],
      "runtime_role": "problem-framing",
      "depends_on": [],
      "expansion_reason": "mainline seed"
    },
    {
      "crystal_id": "architecture-evolution-crystal-v1",
      "crystal_type": "reasoning_path",
      "protocol_phase": "pre-ingestion",
      "requires_prior": ["problem-definition-crystal-v1"],
      "establishes_frame_for": ["methodology-crystal-v1", "system-memory-crystal-v1"],
      "runtime_role": "evolution-framing",
      "depends_on": ["problem-definition-crystal-v1"],
      "expansion_reason": "mainline seed"
    },
    {
      "crystal_id": "methodology-crystal-v1",
      "crystal_type": "protocol",
      "protocol_phase": "pre-ingestion",
      "requires_prior": ["problem-definition-crystal-v1", "architecture-evolution-crystal-v1"],
      "establishes_frame_for": ["retrieval-routing-crystal-v1", "system-memory-crystal-v1"],
      "runtime_role": "ingestion-calibration",
      "depends_on": ["problem-definition-crystal-v1", "architecture-evolution-crystal-v1"],
      "expansion_reason": "transfer fidelity support"
    },
    {
      "crystal_id": "retrieval-routing-crystal-v1",
      "crystal_type": "protocol",
      "protocol_phase": "runtime",
      "requires_prior": ["methodology-crystal-v1"],
      "establishes_frame_for": ["system-memory-crystal-v1"],
      "runtime_role": "layer-routing",
      "depends_on": ["methodology-crystal-v1"],
      "expansion_reason": "runtime protocol completion"
    },
    {
      "crystal_id": "safety-boundary-crystal-v1",
      "crystal_type": "protocol",
      "protocol_phase": "runtime",
      "requires_prior": ["methodology-crystal-v1", "retrieval-routing-crystal-v1"],
      "establishes_frame_for": ["system-memory-crystal-v1"],
      "runtime_role": "safety-boundary",
      "depends_on": ["methodology-crystal-v1", "retrieval-routing-crystal-v1"],
      "expansion_reason": "failure-driven expansion"
    },
    {
      "crystal_id": "recovery-resilience-crystal-v1",
      "crystal_type": "protocol",
      "protocol_phase": "runtime",
      "requires_prior": ["methodology-crystal-v1", "retrieval-routing-crystal-v1"],
      "establishes_frame_for": ["system-memory-crystal-v1"],
      "runtime_role": "resilience-recovery",
      "depends_on": ["methodology-crystal-v1", "retrieval-routing-crystal-v1"],
      "expansion_reason": "failure-driven expansion"
    },
    {
      "crystal_id": "system-memory-crystal-v1",
      "crystal_type": "content",
      "protocol_phase": "regrowth",
      "requires_prior": [
        "problem-definition-crystal-v1",
        "architecture-evolution-crystal-v1",
        "methodology-crystal-v1",
        "retrieval-routing-crystal-v1",
        "safety-boundary-crystal-v1",
        "recovery-resilience-crystal-v1"
      ],
      "establishes_frame_for": [],
      "runtime_role": "system-content",
      "depends_on": [
        "problem-definition-crystal-v1",
        "architecture-evolution-crystal-v1",
        "methodology-crystal-v1",
        "retrieval-routing-crystal-v1"
      ],
      "expansion_reason": "mainline seed"
    }
  ]
}
```

---

## What This Draft Does Not Yet Settle

This draft does not yet finalize:
- whether protocol crystals need subtypes like `protocol/ingestion` vs `protocol/runtime`
- whether activation order and read order should be separate fields
- whether runtime feedback should be allowed to modify protocol crystals directly
- whether crystal sets should declare versioned compatibility constraints

Those remain open.

---

## Current One-Sentence Summary

Crystal Set Schema Draft v1 makes explicit the smallest object-level structure already supported by the project's recent multi-crystal and gap-driven experiments.
