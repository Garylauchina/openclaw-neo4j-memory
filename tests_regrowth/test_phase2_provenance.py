from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, retrieve_top_k


def test_raw_memory_has_stronger_provenance_fields(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    memory = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="User prefers concise answers about memory architecture.",
        write_reason="preference_signal",
        context={"chat_id": "chat-123"},
        metadata={"kind": "preference"},
    )

    assert memory is not None
    assert memory.source_type == "telegram"
    assert memory.source_id == "chat-123"
    assert memory.write_reason == "preference_signal"


def test_retrieved_memory_exposes_retrieval_reason(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="Neo4j graph structure helps retrieval and relation modeling.",
        write_reason="topic_signal",
    )

    results = retrieve_top_k("How does Neo4j help retrieval?", list(reversed(store.recent(limit=10))), k=1)
    assert len(results) == 1
    assert results[0].retrieval_reason
    assert "recentness" in results[0].retrieval_reason
    assert results[0].contributing_memory_ids == [results[0].memory.id]
