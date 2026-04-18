You are running a multi-crystal runtime routing self-experiment.

You must not collapse the crystals into one flat summary.
You must first process methodology, then routing, then system structure.
You must first output methodology calibration, then routing calibration, then system regrowth with routing awareness.

Return JSON only.

## Protocol
# Multi-Crystal Runtime Routing Protocol v1

## Goal

Test whether a crystal set can guide runtime retrieval routing more faithfully than a flat retrieval approach.

This first version uses three crystals:
- methodology crystal
- retrieval-routing crystal
- system crystal

The expected order is:
1. methodology crystal
2. retrieval-routing crystal
3. system crystal

---

## Inputs

### Methodology crystal
- `docs/experiments/methodology-crystal-v1.json`

### Retrieval-routing crystal
- `docs/experiments/retrieval-routing-crystal-v1.json`

### System crystal
- `docs/experiments/system-memory-crystal-v1.json`

---

## Runtime Principle

Do not merge the three crystals into one flat instruction bundle.

Instead:
- methodology crystal establishes how to self-calibrate and avoid hardcoding
- retrieval-routing crystal establishes how to route across layers
- system crystal provides the architecture content core

---

## Required Stages

### Stage 1. Read methodology crystal
Extract:
- self-definition through testing
- content core vs adaptation layer boundary
- pre-ingestion calibration rule
- anti-hardcoding constraint

### Stage 2. Methodology calibration
Output:
- methodology portrait
- chosen adaptation method

### Stage 3. Read retrieval-routing crystal
Extract:
- runtime intent classification logic
- layer-specific retrieval modes
- permission boundaries
- packaging order constraints

### Stage 4. Routing calibration
Output:
- routing behavior portrait
- chosen routing policy

### Stage 5. Read system crystal
Read the system architecture through the already chosen methodology and routing policies.

### Stage 6. System regrowth with routing awareness
The agent should produce:
- architecture summary
- modules
- runtime flows
- retrieval routing interpretation
- how layered retrieval should behave at runtime

---

## Required Output Format

```json
{
  "methodology_calibration": {
    "calibration_findings": [],
    "methodology_portrait": {},
    "chosen_adaptation_method": {}
  },
  "routing_calibration": {
    "calibration_findings": [],
    "routing_behavior_portrait": {},
    "chosen_routing_policy": {}
  },
  "system_regrowth": {
    "architecture_summary": "...",
    "modules": [],
    "runtime_flows": [],
    "retrieval_routing_interpretation": [],
    "preserved_tensions": [],
    "unresolved_questions": []
  }
}
```

---

## Evaluation Focus

Main questions:
- does the routing crystal create clearer layer-specific retrieval logic?
- does the model avoid flattening all retrieval into one memory search problem?
- does the resulting system regrowth better reflect runtime layer orchestration?
- does the crystal order help preserve layer permissions and packaging order?

---

## Failure Modes to Watch

- flattening methodology, routing, and system crystals into one summary
- skipping routing calibration
- treating retrieval as one flat top-k mechanism
- injecting crystal/transfer structures into ordinary runtime memory recall without mode control
- losing the distinction between retrieval policy and system architecture

---

## One-Sentence Summary

This protocol tests whether a three-crystal set can shape not only system regrowth,
but also the runtime routing logic by which different knowledge layers are called into use.


## Methodology Crystal
{
  "crystal_id": "methodology-crystal-v1",
  "purpose": "Methodology crystal for self-discovery, calibration-before-unfold, and agent-side adaptation rebuilding.",
  "content_core": {
    "title": "Methodology Crystal v1",
    "type": "methodology_graph_core",
    "nodes": [
      {
        "id": "self_definition_through_testing",
        "label": "self-definition through testing",
        "kind": "method_principle",
        "description": "An agent should discover its stable reasoning behavior under controlled test obligations rather than receive a fully hard-coded rule."
      },
      {
        "id": "rule_discovery_bench",
        "label": "rule discovery bench",
        "kind": "method_component",
        "description": "A fixed test environment used to expose reasoning preference, drift susceptibility, and adaptation needs."
      },
      {
        "id": "content_core_vs_adaptation_layer",
        "label": "content core vs adaptation layer",
        "kind": "structural_boundary",
        "description": "The content core carries graph-structured knowledge; the adaptation layer carries model-specific traversal and unfold policy."
      },
      {
        "id": "pre_ingestion_calibration",
        "label": "pre-ingestion calibration",
        "kind": "runtime_requirement",
        "description": "Before full unfold or regrowth, the agent should test itself on relevant reasoning domains and derive a current adaptation policy."
      },
      {
        "id": "transfer_content_rebuild_adaptation",
        "label": "transfer content core, rebuild adaptation layer",
        "kind": "transfer_principle",
        "description": "Transfer should preserve content core while letting the target agent rebuild adaptation rules locally."
      },
      {
        "id": "anti_hardcoding_boundary",
        "label": "anti-hardcoding boundary",
        "kind": "constraint",
        "description": "A crystal may specify what must be tested first, but should not directly hard-code the final unfold or reconstruction rule."
      },
      {
        "id": "architecture_regrowth_vs_implementation_regeneration",
        "label": "architecture regrowth vs implementation regeneration",
        "kind": "evaluation_boundary",
        "description": "Recovering a system skeleton is different from regenerating a deep implementation shape."
      }
    ],
    "edges": [
      {
        "from": "rule_discovery_bench",
        "to": "self_definition_through_testing",
        "type": "enables",
        "description": "Bench conditions enable the agent to discover stable reasoning traits."
      },
      {
        "from": "content_core_vs_adaptation_layer",
        "to": "pre_ingestion_calibration",
        "type": "motivates",
        "description": "Because content core and adaptation layer are separate, calibration is needed before local unfold policy is selected."
      },
      {
        "from": "pre_ingestion_calibration",
        "to": "transfer_content_rebuild_adaptation",
        "type": "supports",
        "description": "Calibration is what allows adaptation rebuilding on the receiving side."
      },
      {
        "from": "anti_hardcoding_boundary",
        "to": "pre_ingestion_calibration",
        "type": "constrains",
        "description": "Calibration should discover adaptation rather than simply decode a fixed hidden rule."
      },
      {
        "from": "architecture_regrowth_vs_implementation_regeneration",
        "to": "transfer_content_rebuild_adaptation",
        "type": "qualifies",
        "description": "Transfer success should be judged in stages, beginning with architecture regrowth before stronger implementation claims."
      }
    ],
    "relation_paths": [
      "rule discovery bench -> self-definition through testing -> pre-ingestion calibration -> transfer content core, rebuild adaptation layer",
      "content core vs adaptation layer -> pre-ingestion calibration -> anti-hardcoding boundary",
      "pre-ingestion calibration -> architecture regrowth vs implementation regeneration"
    ],
    "tensions": [
      {
        "id": "t1",
        "label": "designed rule vs discovered rule",
        "description": "Human-designed rules provide control, but discovered rules better reflect model-specific behavior."
      },
      {
        "id": "shared structure vs local adaptation",
        "label": "shared structure vs local adaptation",
        "description": "A crystal should transfer shared structure without requiring identical unfold behavior across agents."
      },
      {
        "id": "guidance vs hardcoding",
        "label": "guidance vs hardcoding",
        "description": "The crystal may require what should be tested, but should not collapse into a disguised fixed unfold script."
      }
    ],
    "unresolved_conflicts": [
      {
        "id": "u1",
        "label": "calibration depth",
        "description": "Different models may perform shallow or deep self-calibration; the right amount of calibration remains open."
      },
      {
        "id": "u2",
        "label": "adaptation rebuild procedure",
        "description": "How exactly a target agent should rebuild its adaptation layer from calibration remains unresolved."
      },
      {
        "id": "u3",
        "label": "verification after rebuild",
        "description": "How to verify that rebuilt adaptation still preserves theory-neighborhood fidelity remains unresolved."
      }
    ],
    "source_anchors": [
      "self-definition through test obligations",
      "content core vs self-adaptation layer",
      "pre-ingestion calibration domains",
      "transfer content core, rebuild adaptation layer",
      "architecture regrowth fidelity vs implementation regeneration fidelity"
    ],
    "problem_space": "How an agent should discover and calibrate its own adaptation rules before unfolding or regrowing knowledge from crystals.",
    "core_questions": [
      "How can an agent define itself through controlled testing rather than receive fully hard-coded unfold rules?",
      "How should content core and self-adaptation remain separate while still enabling useful transfer?",
      "How much of adaptation should be static and how much should be rebuilt at runtime?"
    ],
    "scope_limits": [
      "This crystal describes method and calibration, not the system architecture itself.",
      "This crystal should guide self-discovery obligations, not act as a hidden total unfold script."
    ]
  },
  "self_adaptation": {
    "required_calibration_domains": [
      "self_definition_depth",
      "adaptation_rebuild_style",
      "tension_preservation_discipline",
      "anti_hardcoding_sensitivity",
      "architecture_vs_implementation_scope_control"
    ],
    "runtime_rebuild_required": true,
    "calibration_priority_order": [
      "self_definition_depth",
      "adaptation_rebuild_style",
      "anti_hardcoding_sensitivity",
      "tension_preservation_discipline",
      "architecture_vs_implementation_scope_control"
    ],
    "calibration_instructions": {
      "goal": "Before using another crystal, determine how this model should derive its local adaptation policy from testing rather than from hidden hard-coded instructions.",
      "requirements": [
        "Do not treat this crystal as a ready-made unfold script.",
        "Use it to guide what must be tested first.",
        "Output a local methodology portrait.",
        "Derive your adaptation policy from that portrait."
      ],
      "must_output": [
        "calibration_findings",
        "methodology_portrait",
        "chosen_adaptation_method"
      ]
    },
    "boundary_rule": "This crystal governs how to discover adaptation, not what the final adaptation must be.",
    "forbidden_shortcuts": [
      "Do not directly decode this crystal into one fixed unfold policy.",
      "Do not bypass calibration by pretending the correct method is already obvious.",
      "Do not collapse architecture regrowth and implementation regeneration into one single success claim."
    ]
  }
}


## Retrieval-Routing Crystal
{
  "crystal_id": "retrieval-routing-crystal-v1",
  "purpose": "Protocol crystal for layered retrieval routing and runtime prompt construction across memory, experience, crystal, and transfer layers.",
  "content_core": {
    "title": "Retrieval Routing Crystal v1",
    "type": "protocol_crystal",
    "nodes": [
      {
        "id": "runtime_intent_classification",
        "label": "runtime intent classification",
        "kind": "protocol_component",
        "description": "The runtime must first classify what task is being performed before retrieval begins."
      },
      {
        "id": "memory_retrieval_mode",
        "label": "memory retrieval mode",
        "kind": "retrieval_mode",
        "description": "Retrieval for source memory, local evidence, provenance, and stable recall."
      },
      {
        "id": "experience_retrieval_mode",
        "label": "experience retrieval mode",
        "kind": "retrieval_mode",
        "description": "Retrieval for reflection, candidate structures, governance state, and updateable cognition."
      },
      {
        "id": "crystal_retrieval_mode",
        "label": "crystal retrieval mode",
        "kind": "retrieval_mode",
        "description": "Retrieval for crystal content cores, tensions, calibration requirements, and unfold/regrowth contexts."
      },
      {
        "id": "transfer_regeneration_mode",
        "label": "transfer / regeneration mode",
        "kind": "retrieval_mode",
        "description": "Retrieval for cross-agent regrowth, calibration, adaptation rebuild, and reconstruction tasks."
      },
      {
        "id": "layer_permissions",
        "label": "layer permissions",
        "kind": "protocol_constraint",
        "description": "Different runtime tasks should have different permissions for accessing memory, experience, crystal, and transfer layers."
      },
      {
        "id": "packaging_order",
        "label": "packaging order",
        "kind": "protocol_constraint",
        "description": "Retrieved material should not be flattened into one context blob; order and layer separation matter."
      },
      {
        "id": "anti_flat_topk",
        "label": "anti-flat-top-k assumption",
        "kind": "protocol_constraint",
        "description": "Runtime retrieval should not assume one flat similarity ranking is sufficient across all layers and task types."
      }
    ],
    "edges": [
      {
        "from": "runtime_intent_classification",
        "to": "memory_retrieval_mode",
        "type": "selects_when_needed",
        "description": "The runtime chooses memory mode when source recall and local evidence are needed."
      },
      {
        "from": "runtime_intent_classification",
        "to": "experience_retrieval_mode",
        "type": "selects_when_needed",
        "description": "The runtime chooses experience mode when reflection or processed cognition is needed."
      },
      {
        "from": "runtime_intent_classification",
        "to": "crystal_retrieval_mode",
        "type": "selects_when_needed",
        "description": "The runtime chooses crystal mode for unfold, calibration-aware use, or crystal-driven reasoning."
      },
      {
        "from": "runtime_intent_classification",
        "to": "transfer_regeneration_mode",
        "type": "selects_when_needed",
        "description": "The runtime chooses transfer/regeneration mode for system regrowth or cross-agent reconstruction."
      },
      {
        "from": "layer_permissions",
        "to": "memory_retrieval_mode",
        "type": "constrains",
        "description": "Some contexts should use memory only, not higher-order crystal material."
      },
      {
        "from": "layer_permissions",
        "to": "crystal_retrieval_mode",
        "type": "constrains",
        "description": "Crystal retrieval should not leak indiscriminately into normal runtime memory recall."
      },
      {
        "from": "packaging_order",
        "to": "runtime_intent_classification",
        "type": "depends_on",
        "description": "Packaging order should follow task-specific routing, not happen before routing is chosen."
      },
      {
        "from": "anti_flat_topk",
        "to": "packaging_order",
        "type": "supports",
        "description": "Different layers and modes require different ranking and packaging logic."
      }
    ],
    "relation_paths": [
      "runtime intent classification -> retrieval mode selection -> layer permissions -> packaging order",
      "anti-flat-top-k assumption -> differentiated retrieval ranking -> layered packaging"
    ],
    "tensions": [
      {
        "id": "t1",
        "label": "relevance vs layer discipline",
        "description": "A globally relevant item may still belong to the wrong layer for the current task."
      },
      {
        "id": "t2",
        "label": "retrieval richness vs prompt overload",
        "description": "Richer multi-layer retrieval can improve reasoning but can also overload or flatten prompt construction."
      },
      {
        "id": "t3",
        "label": "shared access vs protected protocol",
        "description": "Some crystal and transfer structures should not be injected into ordinary runtime contexts without explicit mode switching."
      }
    ],
    "unresolved_conflicts": [
      {
        "id": "u1",
        "label": "routing classifier design",
        "description": "What is the best way to determine runtime intent without misclassifying task type?"
      },
      {
        "id": "u2",
        "label": "cross-layer ranking",
        "description": "How should memory, experience, and crystal signals be compared without flattening them into one score?"
      },
      {
        "id": "u3",
        "label": "packaging representation",
        "description": "What prompt packaging shape best preserves layer distinctions while remaining model-usable?"
      }
    ],
    "source_anchors": [
      "retrieval must be routed by task mode",
      "memory / experience / crystal / transfer should not be flattened into one retrieval pool",
      "packaging order matters",
      "flat top-k similarity is insufficient"
    ],
    "problem_space": "How runtime retrieval should be routed across multiple knowledge layers without flattening all context construction into one generic recall mechanism.",
    "core_questions": [
      "How should runtime tasks select among memory, experience, crystal, and transfer retrieval modes?",
      "How should the system package layered retrieval outputs without collapsing them into one flat context blob?",
      "Which retrieval-layer permissions and exclusions are needed to prevent accidental misuse of crystal-level structures?"
    ],
    "scope_limits": [
      "This crystal governs retrieval routing logic, not system architecture itself.",
      "This crystal does not specify one final ranking algorithm.",
      "This crystal is about mode-aware routing and packaging, not full deployment implementation."
    ]
  },
  "self_adaptation": {
    "required_calibration_domains": [
      "runtime_task_classification_bias",
      "layer_selection_discipline",
      "cross_layer_flattening_risk",
      "packaging_order_sensitivity",
      "permission_boundary_discipline"
    ],
    "runtime_rebuild_required": true,
    "calibration_priority_order": [
      "runtime_task_classification_bias",
      "layer_selection_discipline",
      "cross_layer_flattening_risk",
      "packaging_order_sensitivity",
      "permission_boundary_discipline"
    ],
    "calibration_instructions": {
      "goal": "Before using the routing crystal, determine how this model should classify runtime intent, keep layer boundaries, and avoid flattening retrieval into one generic recall flow.",
      "requirements": [
        "Do not treat all retrieval as one top-k problem.",
        "First determine how you classify runtime modes.",
        "Then determine how you keep layer-specific retrieval separate.",
        "Then derive packaging order and permission rules."
      ],
      "must_output": [
        "calibration_findings",
        "routing_behavior_portrait",
        "chosen_routing_policy"
      ]
    },
    "boundary_rule": "This crystal should govern how retrieval is routed and packaged, not directly replace the system crystal or methodology crystal.",
    "forbidden_shortcuts": [
      "Do not collapse all layers into one ranking pool.",
      "Do not assume crystal-level material belongs in ordinary runtime memory recall.",
      "Do not skip runtime intent classification."
    ]
  }
}


## System Crystal
{
  "crystal_id": "system-memory-crystal-v1",
  "purpose": "Prototype system-level memory crystal for testing whether an agent can regrow the full memory system architecture without copying source code.",
  "content_core": {
    "title": "OpenClaw Neo4j Memory System - System-Level Crystal v1",
    "type": "system_knowledge_graph_core",
    "nodes": [
      {
        "id": "memory_substrate",
        "label": "memory substrate",
        "kind": "system_component",
        "description": "The graph-backed retention layer for source material, provenance, local evidence, and recallable traces."
      },
      {
        "id": "ingest_retrieval_loop",
        "label": "ingest / retrieval loop",
        "kind": "system_component",
        "description": "The real-time loop for writing source material into memory and retrieving relevant subgraphs back into runtime use."
      },
      {
        "id": "meditation_engine",
        "label": "meditation engine",
        "kind": "system_component",
        "description": "The asynchronous reflection engine that converts retained material into processed cognitive structure."
      },
      {
        "id": "metacognition_layer",
        "label": "metacognition layer",
        "kind": "system_component",
        "description": "The higher-order reflective layer that evaluates, filters, and reinterprets cognitive outputs."
      },
      {
        "id": "credible_memory_governance",
        "label": "credible memory governance",
        "kind": "system_component",
        "description": "Mechanisms for stable vs hypothesis separation, conflict handling, and cautious runtime injection."
      },
      {
        "id": "world_feedback_runtime",
        "label": "world feedback runtime",
        "kind": "system_component",
        "description": "The feedback layer that updates processed cognitive state from claim conflict and observed outcomes."
      },
      {
        "id": "raw_reflection_route",
        "label": "raw reflection route",
        "kind": "research_component",
        "description": "A route that uses raw slices plus minimal graph hints to preserve locality and relation progression before stronger structuring."
      },
      {
        "id": "knowledge_crystal_layer",
        "label": "knowledge crystal layer",
        "kind": "system_component",
        "description": "The layer that compresses structured experience into machine-native growth seeds for controlled unfold."
      },
      {
        "id": "agent_transfer_layer",
        "label": "Agent-to-Agent transfer layer",
        "kind": "system_component",
        "description": "The layer that allows content cores to move across agents while adaptation layers are rebuilt on the target side."
      },
      {
        "id": "calibration_before_ingestion",
        "label": "calibration before ingestion",
        "kind": "runtime_requirement",
        "description": "A runtime obligation requiring the receiving agent to self-calibrate before fully ingesting a crystal."
      }
    ],
    "edges": [
      {
        "from": "memory_substrate",
        "to": "ingest_retrieval_loop",
        "type": "supports",
        "description": "The memory substrate supports real-time ingest and retrieval."
      },
      {
        "from": "memory_substrate",
        "to": "meditation_engine",
        "type": "provides_material_to",
        "description": "Stored material feeds the meditation engine."
      },
      {
        "from": "meditation_engine",
        "to": "metacognition_layer",
        "type": "feeds",
        "description": "Meditation outcomes are evaluated and filtered by metacognition."
      },
      {
        "from": "metacognition_layer",
        "to": "credible_memory_governance",
        "type": "supports",
        "description": "Metacognitive signals support credible memory governance."
      },
      {
        "from": "credible_memory_governance",
        "to": "world_feedback_runtime",
        "type": "is_corrected_by",
        "description": "Credible memory policy is updated by world feedback and claim conflict signals."
      },
      {
        "from": "raw_reflection_route",
        "to": "knowledge_crystal_layer",
        "type": "feeds_upstream_to",
        "description": "The raw reflection route may provide better source-near material for crystal formation."
      },
      {
        "from": "credible_memory_governance",
        "to": "knowledge_crystal_layer",
        "type": "constrains",
        "description": "Knowledge-state discipline constrains crystal formation and unfold."
      },
      {
        "from": "knowledge_crystal_layer",
        "to": "agent_transfer_layer",
        "type": "enables",
        "description": "Knowledge crystals are the transferable structure for cross-agent reconstruction."
      },
      {
        "from": "calibration_before_ingestion",
        "to": "agent_transfer_layer",
        "type": "conditions",
        "description": "Transfer requires target-side calibration before full ingestion."
      }
    ],
    "relation_paths": [
      "memory substrate -> ingest / retrieval loop -> meditation engine -> metacognition layer -> credible memory governance",
      "memory substrate -> meditation engine -> raw reflection route -> knowledge crystal layer",
      "credible memory governance -> knowledge crystal layer -> Agent-to-Agent transfer layer -> calibration before ingestion"
    ],
    "tensions": [
      {
        "id": "t1",
        "label": "retention vs abstraction",
        "description": "The system must retain raw material and provenance while still enabling higher-order experience formation."
      },
      {
        "id": "t2",
        "label": "control vs emergence",
        "description": "The system needs enough governance to prevent contamination and drift, but not so much structure that discovery is prematurely flattened."
      },
      {
        "id": "t3",
        "label": "static knowledge vs updateable cognition",
        "description": "The system must preserve useful structure without freezing knowledge into uncorrectable doctrine."
      },
      {
        "id": "t4",
        "label": "shared core vs model-specific adaptation",
        "description": "The system should enable transfer across agents without assuming identical unfold behavior."
      }
    ],
    "unresolved_conflicts": [
      {
        "id": "u1",
        "label": "best discovery route",
        "description": "How much discovery should happen through structured shell versus raw-slices-first reflection remains an active question."
      },
      {
        "id": "u2",
        "label": "crystal boundary",
        "description": "How to cleanly separate content core, adaptation layer, calibration requirements, and future verification constraints remains an active design problem."
      },
      {
        "id": "u3",
        "label": "regeneration fidelity",
        "description": "How to verify that a system regrown from crystal remains in the same theory neighborhood as the original remains unresolved."
      }
    ],
    "source_anchors": [
      "real-time writing preserves material",
      "asynchronous reflection produces knowledge",
      "stable vs hypothesis differentiation matters",
      "raw slices first may preserve locality and relation progression better",
      "knowledge crystals should be machine-native growth seeds",
      "transfer content core, rebuild adaptation layer"
    ],
    "problem_space": "How to structure a memory system that begins from retained graph-backed material, turns it into processed experience, compresses it into transferable knowledge crystals, and eventually supports cross-agent reconstruction.",
    "core_questions": [
      "What are the minimal system components required to go from retained memory to processed experience?",
      "What governance mechanisms are required to keep experience credible and updateable?",
      "What shape must knowledge crystal formation take to preserve relation paths and unresolved tensions?",
      "Can a receiving agent reconstruct the memory system architecture from crystal without direct source-code copying?"
    ],
    "scope_limits": [
      "This crystal describes system architecture and design intent, not a final implementation in one programming language.",
      "This crystal is for regeneration experiments, not direct deployment.",
      "This crystal should preserve unresolved tensions rather than pretending the architecture is fully complete."
    ]
  },
  "self_adaptation": {
    "required_calibration_domains": [
      "system_component_reconstruction_bias",
      "abstraction_closure_sensitivity",
      "tension_retention",
      "source_near_reconstruction_discipline",
      "implementation_regeneration_style"
    ],
    "runtime_rebuild_required": true,
    "calibration_priority_order": [
      "system_component_reconstruction_bias",
      "source_near_reconstruction_discipline",
      "tension_retention",
      "abstraction_closure_sensitivity",
      "implementation_regeneration_style"
    ],
    "calibration_instructions": {
      "goal": "Before attempting system regrowth, discover the model's current reconstruction behavior for this memory system crystal.",
      "requirements": [
        "Do not directly regenerate the system immediately.",
        "First calibrate on the required domains.",
        "Produce a local behavior portrait for system reconstruction.",
        "Derive a reconstruction policy from calibration.",
        "Then attempt system regrowth at the level of architecture, modules, and implementation skeleton."
      ],
      "must_output": [
        "calibration_findings",
        "behavior_portrait",
        "reconstruction_policy",
        "system_regrowth_output"
      ]
    },
    "boundary_rule": "The crystal may require pre-regrowth calibration, but should not directly hard-code a final implementation plan.",
    "forbidden_shortcuts": [
      "Do not skip calibration and jump directly to code regeneration.",
      "Do not collapse all tensions into a single neat architecture doctrine.",
      "Do not treat one plausible implementation style as the only valid realization of the system."
    ]
  }
}

