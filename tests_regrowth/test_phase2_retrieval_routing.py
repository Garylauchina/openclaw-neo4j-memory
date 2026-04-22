from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, detect_retrieval_mode, retrieve_with_routing


def test_detect_retrieval_mode_distinguishes_preference_and_topic():
    assert detect_retrieval_mode("What preference did the user mention?") == "preference"
    assert detect_retrieval_mode("How does Neo4j help retrieval?") == "topic"


def test_retrieve_with_routing_can_surface_notes_and_memories(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="User prefers concise answers about Neo4j retrieval.",
        write_reason="preference_signal",
        status="stable",
    )
    store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="Neo4j graph structure helps retrieval and relation modeling.",
        write_reason="topic_signal",
        status="stable",
    )

    memories = list(reversed(store.recent(limit=10)))
    notes = build_consolidated_notes(memories)
    if notes:
        notes[0].note_type = "preference_note"

    results = retrieve_with_routing(
        "What preference did the user mention about Neo4j?",
        memories=memories,
        notes=notes,
        k=3,
    )

    assert len(results) >= 1
    assert any(result.retrieval_mode == "preference" for result in results)
    assert any((result.note is not None) or (result.memory is not None) for result in results)
