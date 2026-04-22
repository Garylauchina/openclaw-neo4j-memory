from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, RoutingDecision, build_consolidated_notes, build_routing_decision, retrieve_with_routing


def test_routing_decision_metadata_exposes_bounded_routing_layer():
    decision = build_routing_decision("topic", 4)
    assert isinstance(decision, RoutingDecision)
    metadata = decision.metadata()
    assert set(metadata.keys()) == {
        "routing_mode",
        "coordination_reason",
        "product_raw_balance_summary",
        "coordination_counter",
    }


def test_retrieval_reasons_include_routing_metadata(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j supports relation modeling across sessions.", status="stable", force=True)

    memories = list(reversed(store.recent(limit=10)))
    notes = build_consolidated_notes(memories)
    results = retrieve_with_routing("How does Neo4j help retrieval?", memories=memories, notes=notes, k=4)

    assert results
    assert any("routing_mode=" in result.retrieval_reason for result in results)
    assert any("balance=" in result.retrieval_reason for result in results)
    assert any("coordination_counter=" in result.retrieval_reason for result in results)
