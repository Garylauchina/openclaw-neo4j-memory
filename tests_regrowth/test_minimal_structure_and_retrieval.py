from pathlib import Path

from minimal_memory_kernel import (
    MinimalMemoryStore,
    extract_structure,
    retrieve_top_k,
    should_trigger_retrieval,
)


def test_extract_structure_returns_entities_and_relations():
    entities, relations = extract_structure(
        "User prefers Neo4j for Memory architecture discussions about Retrieval."
    )

    names = {entity.name for entity in entities}
    assert "Neo4j" in names
    assert "Memory" in names or "Retrieval" in names
    assert any(relation.relation_type in {"preference_of", "about", "related_to"} for relation in relations)


def test_should_trigger_retrieval_skips_short_inputs():
    assert should_trigger_retrieval("ok") is False
    assert should_trigger_retrieval("Need prior memory about Neo4j retrieval") is True


def test_retrieve_top_k_prefers_related_memory(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="User prefers Neo4j for memory retrieval design.")
    store.write(source="telegram", content="We discussed gardening metaphors for system cultivation.")
    store.write(source="telegram", content="Neo4j graph structure helps retrieval and relation modeling.")

    results = retrieve_top_k("How should Neo4j help memory retrieval?", list(reversed(store.recent(limit=10))), k=2)

    assert len(results) == 2
    assert "Neo4j" in results[0].memory.content
    assert results[0].score >= results[1].score
