from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, run_lightweight_consolidation


def test_lightweight_consolidation_dedupes_and_marks_frequent_entities(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    first = store.write(source="telegram", content="Neo4j helps memory retrieval design.")
    second = store.write(source="telegram", content="Neo4j helps memory retrieval design.", force=True)
    third = store.write(source="telegram", content="Neo4j graph structure supports relation modeling.")
    fourth = store.write(source="telegram", content="Gardening metaphors help explain system cultivation.")

    result = run_lightweight_consolidation(list(reversed(store.recent(limit=10))))

    assert first is not None and second is not None and third is not None and fourth is not None
    assert len(result["duplicate_groups"]) >= 1
    assert "Neo4j" in result["frequent_entities"]
    assert any(note.key == "Neo4j" for note in result["consolidated_notes"])
