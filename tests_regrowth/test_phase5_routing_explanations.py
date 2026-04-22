from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, RoutingDecision, build_consolidated_notes, build_routing_decision, retrieve_with_routing


def test_routing_decision_summary_is_inspectable():
    decision = build_routing_decision("topic", 4)
    assert isinstance(decision, RoutingDecision)
    summary = decision.summary()
    assert "mode=topic" in summary
    assert "max_note_count=" in summary


def test_retrieval_reasons_include_routing_summary(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j supports relation modeling across sessions.", status="stable", force=True)

    memories = list(reversed(store.recent(limit=10)))
    notes = build_consolidated_notes(memories)
    results = retrieve_with_routing("How does Neo4j help retrieval?", memories=memories, notes=notes, k=4)

    assert results
    assert any("routing_summary=" in result.retrieval_reason for result in results)
    assert any("selected_kind=" in result.retrieval_reason for result in results)
