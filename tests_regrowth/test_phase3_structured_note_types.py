from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, classify_note_type


def test_classify_note_type_returns_bounded_types(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    preference_memory = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="User prefers concise answers about Neo4j retrieval.",
        write_reason="preference_signal",
        status="stable",
    )
    topic_memory = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="Neo4j graph structure helps retrieval and relation modeling.",
        write_reason="topic_signal",
        status="stable",
    )
    extra_memory = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="Neo4j supports cross-conversation entity linking.",
        write_reason="topic_signal",
        status="stable",
    )

    assert preference_memory is not None and topic_memory is not None and extra_memory is not None
    memories = list(reversed(store.recent(limit=10)))
    neo4j_related = [memory for memory in memories if "neo4j" in memory.content.lower()]
    note_type = classify_note_type("Neo4j", neo4j_related)
    assert note_type in {"preference_note", "topic_note", "summary_note", "retrieval_anchor_note"}


def test_build_consolidated_notes_uses_structured_note_types(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="User prefers concise answers about Neo4j retrieval.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j graph structure helps retrieval and relation modeling.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j supports cross-conversation entity linking.", status="stable", force=True)

    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    neo4j_note = next(note for note in notes if note.key == "Neo4j")
    assert neo4j_note.note_type in {"preference_note", "topic_note", "summary_note", "retrieval_anchor_note"}
