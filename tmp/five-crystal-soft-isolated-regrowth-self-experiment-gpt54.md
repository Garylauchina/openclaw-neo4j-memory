You are running a five-crystal soft-isolated regrowth self-experiment.

You must not consult source code, implementation files, Docker assets, database state, or historical code context.
Use only the provided crystals and protocol.
Return structured results in markdown with sections for: problem definition summary, architecture evolution summary, protocol summary, system regrowth summary, and gap analysis.

## docs/experiments/problem-definition-crystal-v1.json
{
  "crystal_id": "problem-definition-crystal-v1",
  "purpose": "Reasoning-path crystal for the original problem pressure, target object, excluded routes, and core tensions that forced the project into its current form.",
  "content_core": {
    "title": "Problem Definition Crystal v1",
    "type": "reasoning_path_crystal",
    "nodes": [
      {
        "id": "ordinary_rag_insufficiency",
        "label": "ordinary RAG insufficiency",
        "kind": "problem_pressure",
        "description": "Flat recall and prompt stuffing do not provide durable state, credible update, conflict handling, rollback, or interpretable higher-order cognition."
      },
      {
        "id": "memory_not_just_recall",
        "label": "memory is not just recall",
        "kind": "problem_reframing",
        "description": "A useful memory system must handle source, state, update, conflict, and provenance rather than just returning semantically similar text."
      },
      {
        "id": "llm_not_replaced",
        "label": "LLM is not replaced",
        "kind": "scope_boundary",
        "description": "The goal is not to build another base model or a total world simulator; the LLM remains responsible for generation and generalization."
      },
      {
        "id": "external_memory_governance_layer",
        "label": "external memory and governance layer",
        "kind": "target_architecture_pressure",
        "description": "The project aims to build an external memory/cognitive-governance layer that complements Transformer-based LLMs."
      },
      {
        "id": "retention_vs_abstraction",
        "label": "retention vs abstraction",
        "kind": "core_tension",
        "description": "The system must preserve source material while still allowing higher-order structure and compression."
      },
      {
        "id": "control_vs_emergence",
        "label": "control vs emergence",
        "kind": "core_tension",
        "description": "The system must govern updates and retrieval without destroying discovery and growth."
      },
      {
        "id": "usable_memory_over_foundation_modeling",
        "label": "usable memory over foundation-model replacement",
        "kind": "priority_rule",
        "description": "The project prioritizes usable memory, credible updates, retrieval control, and evaluability over any attempt to become a substitute base model."
      },
      {
        "id": "memory_to_experience_to_crystal_to_transfer",
        "label": "memory to experience to crystal to transfer",
        "kind": "problem_chain",
        "description": "The problem matured from raw memory retention toward experience formation, crystal compression, and cross-agent transfer."
      }
    ],
    "edges": [
      {
        "from": "ordinary_rag_insufficiency",
        "to": "memory_not_just_recall",
        "type": "forces",
        "description": "Failures of flat retrieval force a broader definition of memory."
      },
      {
        "from": "memory_not_just_recall",
        "to": "external_memory_governance_layer",
        "type": "motivates",
        "description": "If memory includes source, state, update, and conflict, then an external governance layer becomes necessary."
      },
      {
        "from": "llm_not_replaced",
        "to": "external_memory_governance_layer",
        "type": "constrains",
        "description": "The external layer must complement LLMs rather than attempt to replace them."
      },
      {
        "from": "retention_vs_abstraction",
        "to": "memory_to_experience_to_crystal_to_transfer",
        "type": "drives",
        "description": "The system evolves because raw retention alone is insufficient but abstraction must remain grounded."
      },
      {
        "from": "control_vs_emergence",
        "to": "external_memory_governance_layer",
        "type": "drives",
        "description": "Governance is required precisely because uncontrolled emergence is risky, but hard control also damages usefulness."
      },
      {
        "from": "usable_memory_over_foundation_modeling",
        "to": "llm_not_replaced",
        "type": "supports",
        "description": "Practical memory work keeps the project out of foundation-model replacement scope."
      }
    ],
    "relation_paths": [
      "ordinary RAG insufficiency -> memory is not just recall -> external memory and governance layer",
      "retention vs abstraction -> memory to experience to crystal to transfer",
      "usable memory over foundation-model replacement -> LLM is not replaced -> external memory and governance layer"
    ],
    "tensions": [
      {
        "id": "t1",
        "label": "memory vs retrieval",
        "description": "The project is about memory as governed state, not just retrieval as access."
      },
      {
        "id": "t2",
        "label": "assistance vs autonomy",
        "description": "The system should support LLM cognition without trying to become an autonomous substitute intelligence."
      },
      {
        "id": "t3",
        "label": "grounded evidence vs higher-order compression",
        "description": "The project must move upward into abstraction without severing evidence links."
      }
    ],
    "unresolved_conflicts": [
      {
        "id": "u1",
        "label": "best governance thickness",
        "description": "How much governance is enough before the system becomes rigid remains unresolved."
      },
      {
        "id": "u2",
        "label": "memory-shell role",
        "description": "Exactly how much structure should live in prompt/runtime vs graph/object layers remains unresolved."
      },
      {
        "id": "u3",
        "label": "best regrowth interface",
        "description": "How much of the system should be expressed as transfer-ready crystal vs ordinary implementation remains unresolved."
      }
    ],
    "source_anchors": [
      "this is not a new foundation-model route",
      "LLM handles generation/generalization, memory system handles state/source/update/conflict/rollback",
      "prioritize usable memory, controllable retrieval, credible updates, and evaluability",
      "memory -> experience -> knowledge crystal -> Agent-to-Agent transfer"
    ],
    "problem_space": "What kind of memory/governance system is needed once flat retrieval is recognized as insufficient, but foundation-model replacement is explicitly out of scope.",
    "core_questions": [
      "Why is ordinary retrieval insufficient for durable memory and cognition?",
      "What exact responsibilities should remain in the LLM and what should move into external memory/governance?",
      "Why did the project evolve from memory retention toward experience, crystal formation, and transfer?"
    ],
    "scope_limits": [
      "This crystal defines the project problem and boundaries, not the final runtime protocol.",
      "This crystal should preserve why the project exists, not how every module is implemented."
    ]
  }
}


## docs/experiments/architecture-evolution-crystal-v1.json
{
  "crystal_id": "architecture-evolution-crystal-v1",
  "purpose": "Reasoning-path crystal for how the project architecture evolved, which branches were opened or narrowed, and what experimental pressures shaped the current mainline.",
  "content_core": {
    "title": "Architecture Evolution Crystal v1",
    "type": "reasoning_path_crystal",
    "nodes": [
      {
        "id": "raw_retention_stage",
        "label": "raw retention stage",
        "kind": "architecture_stage",
        "description": "Initial emphasis on preserving incoming material and basic graph memory."
      },
      {
        "id": "meditation_experience_stage",
        "label": "meditation and experience stage",
        "kind": "architecture_stage",
        "description": "The system expanded from retention into asynchronous meditation, reflection, and experience formation."
      },
      {
        "id": "governance_stage",
        "label": "governance and belief-state stage",
        "kind": "architecture_stage",
        "description": "Stable vs hypothesis distinction, pending beliefs, evidence discipline, and anti-contamination pressures entered the mainline."
      },
      {
        "id": "world_feedback_stage",
        "label": "world feedback stage",
        "kind": "architecture_stage",
        "description": "Minimal world-model closure was added through observation, outcome, and belief-update loops."
      },
      {
        "id": "structured_shell_branch",
        "label": "structured shell branch",
        "kind": "branch",
        "description": "A branch explored structured shell architectures and governance-rich mediation, but showed local-identity retention and binding difficulties."
      },
      {
        "id": "raw_slices_reflection_branch",
        "label": "raw slices plus minimal graph hints branch",
        "kind": "branch",
        "description": "A competing branch used raw slices with minimal graph hints and direct LLM reflection, showing strong evidence value."
      },
      {
        "id": "fold_unfold_branch",
        "label": "fold and unfold branch",
        "kind": "branch",
        "description": "The project reframed compression/regrowth as fold/unfold, later as constrained generative reasoning."
      },
      {
        "id": "crystal_transfer_branch",
        "label": "crystal and transfer branch",
        "kind": "branch",
        "description": "The project evolved toward knowledge crystals, reasoning-path crystals, and Agent-to-Agent transfer."
      },
      {
        "id": "mainline_reframe",
        "label": "mainline reframe",
        "kind": "mainline_identity",
        "description": "The mainline became memory -> experience -> knowledge crystal -> Agent-to-Agent transfer."
      }
    ],
    "edges": [
      {
        "from": "raw_retention_stage",
        "to": "meditation_experience_stage",
        "type": "evolves_into",
        "description": "Retention alone proved insufficient, driving higher-order experience formation."
      },
      {
        "from": "meditation_experience_stage",
        "to": "governance_stage",
        "type": "evolves_into",
        "description": "As experience formation grew, governance pressures became necessary."
      },
      {
        "from": "governance_stage",
        "to": "world_feedback_stage",
        "type": "extends_into",
        "description": "Governed cognition naturally pushed toward minimal outcome-based feedback closure."
      },
      {
        "from": "structured_shell_branch",
        "to": "raw_slices_reflection_branch",
        "type": "contrasted_with",
        "description": "Structured shell branch was evaluated against a raw-slices-first evidence line."
      },
      {
        "from": "raw_slices_reflection_branch",
        "to": "fold_unfold_branch",
        "type": "feeds",
        "description": "Evidence from raw reflection sharpened the fold/unfold and drift problem."
      },
      {
        "from": "fold_unfold_branch",
        "to": "crystal_transfer_branch",
        "type": "evolves_into",
        "description": "Fold/unfold matured into reasoning-path crystals and transfer-oriented regrowth questions."
      },
      {
        "from": "crystal_transfer_branch",
        "to": "mainline_reframe",
        "type": "clarifies",
        "description": "Crystal and transfer work helped clarify the full four-stage mainline."
      }
    ],
    "relation_paths": [
      "raw retention stage -> meditation and experience stage -> governance and belief-state stage -> world feedback stage",
      "structured shell branch -> raw slices plus minimal graph hints branch -> fold and unfold branch -> crystal and transfer branch",
      "crystal and transfer branch -> mainline reframe"
    ],
    "tensions": [
      {
        "id": "t1",
        "label": "structured mediation vs raw evidence proximity",
        "description": "Richer structure can improve governance but may damage local identity and evidence binding."
      },
      {
        "id": "t2",
        "label": "governance depth vs usable growth",
        "description": "Stronger governance reduces contamination risk but can impede adaptive growth."
      },
      {
        "id": "t3",
        "label": "human-readable architecture vs transformer-friendly crystal form",
        "description": "Human-friendly explanatory structure can conflict with machine-native unfold stability."
      }
    ],
    "unresolved_conflicts": [
      {
        "id": "u1",
        "label": "structured shell retention problem",
        "description": "Why structured shell routes lose local identity continuity remains unresolved."
      },
      {
        "id": "u2",
        "label": "multi-crystal sufficiency",
        "description": "How many crystals are needed before regrowth quality saturates remains unresolved."
      },
      {
        "id": "u3",
        "label": "runtime update loop for protocol crystals",
        "description": "How runtime experience should or should not feed back into protocol crystals remains unresolved."
      }
    ],
    "source_anchors": [
      "实时写入负责保留材料，异步冥思负责生产知识",
      "structured memory shell vs raw-chunk reflection",
      "Knowledge Fold and Unfold for Transformers",
      "knowledge crystal as reasoning-path crystal",
      "memory -> experience -> knowledge crystal -> Agent-to-Agent transfer"
    ],
    "problem_space": "How the project architecture was progressively shaped by experimental pressures, branch comparisons, drift problems, and transfer-oriented reframing.",
    "core_questions": [
      "Why did the project move from retention toward experience, governance, fold/unfold, and crystal transfer?",
      "Which architectural branches were narrowed, contrasted, or absorbed into the current mainline?",
      "What tensions and failures shaped the present architecture rather than an alternative one?"
    ],
    "scope_limits": [
      "This crystal preserves architectural evolution logic, not every detailed code change.",
      "This crystal explains why the present mainline emerged, not the final implementation protocol."
    ]
  }
}


## docs/experiments/methodology-crystal-v1.json
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


## docs/experiments/retrieval-routing-crystal-v1.json
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


## docs/experiments/system-memory-crystal-v1.json
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


## docs/experiments/five-crystal-soft-isolated-regrowth-protocol-v1.md
# Five-Crystal Soft-Isolated Regrowth Protocol v1

## Goal

Test whether a new agent can regrow the project architecture neighborhood from a small crystal set alone,
without access to source code, Docker setup, database state, or historical implementation files.

This is a soft-isolated regrowth experiment.

---

## Inputs

### Upstream reasoning-path crystals
- `docs/experiments/problem-definition-crystal-v1.json`
- `docs/experiments/architecture-evolution-crystal-v1.json`

### Protocol crystals
- `docs/experiments/methodology-crystal-v1.json`
- `docs/experiments/retrieval-routing-crystal-v1.json`

### Content crystal
- `docs/experiments/system-memory-crystal-v1.json`

---

## Isolation Rules

The receiving agent must not consult:
- source code
- Docker files
- database state
- prior implementation assets
- old issue or PR history outside what is already crystalized here

The only allowed architectural inputs are the five crystals above.

---

## Suggested Reading Order

### Stage 1. Problem-definition crystal
Recover:
- what problem the project is actually solving
- what routes are explicitly out of scope
- what tensions forced the project into this space

### Stage 2. Architecture-evolution crystal
Recover:
- how the project reached its current mainline
- what branches mattered
- what experiments changed architectural direction

### Stage 3. Methodology crystal
Recover:
- how the receiving agent should calibrate itself
- how to avoid hardcoding and false self-discovery

### Stage 4. Retrieval-routing crystal
Recover:
- how runtime layer routing should work
- how layered retrieval should be packaged
- which boundaries should remain protected

### Stage 5. System-memory crystal
Recover:
- the system architecture content core
- modules, flows, tensions, and architecture body

---

## Required Output Layers

The receiving agent should output at least:

### 1. Problem definition summary
- what the system exists to solve
- what it is not trying to be

### 2. Architecture evolution summary
- how the system got here
- what branch tensions still matter

### 3. Protocol summary
- ingestion / calibration behavior
- runtime routing behavior

### 4. System regrowth summary
- architecture summary
- module set
- runtime flows
- preserved tensions

### 5. Gap analysis
- what could not be regrown well
- what likely requires additional crystals
- what remains too implementation-dependent

---

## Evaluation Focus

Main questions:
- can the new agent recover the actual project problem rather than a generic memory-system story?
- can it recover the evolutionary logic rather than only the final structure?
- can it distinguish protocol crystals from content crystals?
- can it regrow a coherent architecture neighborhood without source code?
- do the failures expose missing crystals or weak existing crystals?

---

## Failure Interpretation Rule

Do not interpret failure only as model weakness.

Also interpret failure as possible evidence of:
- missing crystal types
- insufficient reasoning-path compression
- weak protocol-layer crystallization
- missing ordering/dependency information
- excessive dependence on implicit source-code knowledge

---

## One-Sentence Summary

This protocol tests whether a five-crystal set is sufficient for soft-isolated project regrowth, and uses regrowth failures as evidence of what crystal structure is still missing.
