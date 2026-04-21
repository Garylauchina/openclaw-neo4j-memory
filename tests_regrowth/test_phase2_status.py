from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, retrieve_top_k


def test_new_memories_start_as_tentative(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    memory = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="User prefers concise answers about Neo4j retrieval.",
        write_reason="preference_signal",
    )

    assert memory is not None
    assert memory.status == "tentative"


def test_memory_status_can_be_promoted_to_stable(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    memory = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="User prefers concise answers about Neo4j retrieval.",
        write_reason="preference_signal",
    )

    assert memory is not None
    updated = store.update_status(memory.id, "stable")
    assert updated is not None
    assert updated.status == "stable"

    loaded = store.get(memory.id)
    assert loaded is not None
    assert loaded.status == "stable"


def test_retrieval_exposes_memory_status(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    memory = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="Neo4j graph structure helps retrieval and relation modeling.",
        write_reason="topic_signal",
    )
    assert memory is not None
    store.update_status(memory.id, "stable")

    results = retrieve_top_k("How does Neo4j help retrieval?", list(reversed(store.recent(limit=10))), k=1)
    assert len(results) == 1
    assert results[0].status == "stable"
