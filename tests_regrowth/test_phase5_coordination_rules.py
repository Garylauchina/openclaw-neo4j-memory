from pathlib import Path

from minimal_memory_kernel import (
    MinimalMemoryStore,
    RoutingDecision,
    apply_note_feedback,
    build_consolidated_notes,
    build_routing_decision,
    retrieve_with_routing,
)


def test_build_routing_decision_exposes_coordination_rules():
    decision = build_routing_decision("preference", 4)
    assert isinstance(decision, RoutingDecision)
    assert decision.max_note_count >= 1
    assert decision.max_memory_count >= 1
    assert decision.coordination_reason


def test_retrieve_with_routing_exposes_coordination_reason(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j supports relation modeling across sessions.", status="stable", force=True)

    memories = list(reversed(store.recent(limit=10)))
    notes = apply_note_feedback(build_consolidated_notes(memories), helpful_keys=["Neo4j"])
    results = retrieve_with_routing("How does Neo4j help retrieval?", memories=memories, notes=notes, k=4)

    assert results
    assert any("coordination=" in result.retrieval_reason for result in results)
