# Two-Layer Crystal Boundary Draft

## Purpose

This draft defines a working boundary between:

- **content core**
- **self-adaptation layer**

for a two-layer knowledge crystal architecture.

The goal is to make the crystal usable for:
- model-specific unfold control
- Agent-to-Agent transfer
- future recompilation of adaptation rules

---

## Core Principle

A knowledge crystal should not be treated as a single flat object.

It should be split into:

## Layer 1. Content Core
A graph-structured knowledge object.
This is the structural knowledge itself.

## Layer 2. Self-Adaptation Layer
A model-specific traversal / ingestion / unfold policy.
This tells a specific agent how to read and unfold the core.

Short form:

## content core = what is structurally there
## self-adaptation layer = how this model should traverse it

---

## Layer 1: Content Core

### Definition
The content core is a graph data structure representing structured knowledge.

It should contain problem structure, not model preference.

It should answer:
- what entities / concepts are present
- what relations exist
- what tensions remain unresolved
- what evidence anchors support the structure
- what scope boundaries apply

It should **not** answer:
- in what order a specific model should read this
- what rhetorical style a specific model should avoid
- how much stepwise explicitness a specific model needs

---

## Content Core Candidate Fields

### Structural graph fields
- `nodes`
- `edges`
- `relation_paths`
- `subgraphs`

### Knowledge-state / boundary fields
- `tensions`
- `unresolved_conflicts`
- `scope_limits`
- `non_promotable_relations`
- `candidate_mechanisms`
- `candidate_causal_edges`

### Evidence linkage fields
- `source_anchors`
- `source_trace_points`
- `evidence_clusters`
- `local_evidence_regions`

### Problem-space fields
- `problem_space`
- `core_questions`
- `in_scope`
- `out_of_scope`

### Optional graph-local metadata
- node type
- edge type
- evidence density
- contradiction markers
- provenance ids

---

## Content Core Inclusion Rule
A field belongs in content core when it describes:

## the structure of the knowledge object itself,
## independent of which model will later read it.

If a different model can read the same field without rewriting its meaning,
that field is probably content core.

---

## Layer 2: Self-Adaptation Layer

### Definition
The self-adaptation layer contains model-specific rules for traversing and unfolding the content core.

It should encode:
- reading priorities
- bridge order
- resistance needs
- source reanchor requirements
- abstraction ceilings
- anti-drift constraints

It is not the knowledge itself.
It is the policy for using the knowledge.

---

## Self-Adaptation Candidate Fields

### Traversal policy
- `preferred_ingestion_order`
- `preferred_bridge_order`
- `required_stepwise_expansion`
- `priority_subgraphs`

### Source / anchor policy
- `source_reuse_intensity`
- `mandatory_source_reanchor_points`
- `source_fragment_reuse_policy`

### Drift control
- `anti_closure_rules`
- `anti_frameworkization_rules`
- `anti_checklist_rules`
- `abstraction_ceiling`
- `problem_space_lock_policy`

### Resistance policy
- `required_tension_retention`
- `mandatory_unresolved_conflict_preservation`
- `non_upgrade_boundaries`
- `causal_promotion_guard`

### Output / unfold style policy
- `preferred_unfold_shape`
- `forbidden_formulations`
- `style_avoidance_rules`
- `knowledge_state_expression_policy`

---

## Self-Adaptation Inclusion Rule
A field belongs in self-adaptation when it describes:

## how a particular model should read, traverse, unfold, or restrain itself
## while interacting with the content core.

If the field must change when the target model changes,
it belongs in self-adaptation.

---

## Boundary Test

Use this quick test:

### Question A
If I give this field unchanged to Gemma, Qwen, and GPT-5.4,
should its meaning stay the same?

- If yes, it is probably content core.
- If no, it is probably self-adaptation.

### Question B
Does this field describe knowledge structure,
or model handling policy?

- structure -> content core
- handling policy -> self-adaptation

### Question C
If the receiving agent had to rebuild this field from its own bench portrait,
would that make sense?

- If yes, it is likely self-adaptation.

---

## Transfer Rule

For Agent-to-Agent transfer:

## transfer the content core
## rebuild or recompile the self-adaptation layer for the target agent

This means transfer is not necessarily:
- send one flat crystal unchanged

Instead it becomes:
- send graph-structured knowledge core
- let the target agent derive or load its own adaptation layer

Short form:

## transfer content core, recompile adaptation layer

---

## Why This Boundary Matters

Without the split:
- content and policy get mixed
- model-specific prompts leak into the knowledge object
- transfer becomes brittle
- evaluation becomes ambiguous

With the split:
- the graph core can remain stable
- model-specific behavior can vary cleanly
- Rule Discovery Bench can target adaptation-layer discovery directly
- Agent-to-Agent transfer becomes conceptually cleaner

---

## Relation to Rule Discovery Bench

Rule Discovery Bench should mainly discover:
- self-adaptation layer fields

not content core fields.

The bench is for discovering:
- how a model drifts
- how it needs bridges ordered
- what resistance it needs
- what source reanchors it requires
- what formulations destabilize it

The bench is **not** the primary tool for discovering the objective structure of a specific knowledge graph.

---

## Minimal Working Schema Sketch

```json
{
  "content_core": {
    "nodes": [],
    "edges": [],
    "relation_paths": [],
    "tensions": [],
    "unresolved_conflicts": [],
    "source_anchors": [],
    "problem_space": "",
    "core_questions": [],
    "scope_limits": []
  },
  "self_adaptation": {
    "preferred_bridge_order": [],
    "required_stepwise_expansion": false,
    "anti_closure_rules": [],
    "mandatory_source_reanchor_points": [],
    "required_tension_retention": [],
    "forbidden_formulations": []
  }
}
```

---

## Current Working Interpretation

At the current stage:

- graph-like knowledge structure should move into content core
- model-tuned unfold rules should move into self-adaptation

This is the minimum boundary needed before deeper two-layer crystal experiments.

---

## Status

This is a working draft.
It should be revised after the first explicit two-layer crystal experiments.
