from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, refresh_notes_for_repeated_evidence, revise_memory


def test_build_consolidated_notes_produces_preference_and_topic_oriented_notes(tmp_path: Path):
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

    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    assert any(note.note_type in {"preference_note", "topic_note"} for note in notes)


def test_consolidated_notes_track_superseded_sources(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    original = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="User prefers long answers about Neo4j retrieval.",
        write_reason="preference_signal",
        status="stable",
    )
    assert original is not None

    revise_memory(
        store,
        old_memory_id=original.id,
        new_content="User prefers concise answers about Neo4j retrieval.",
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        write_reason="revised_preference_signal",
        status="stable",
    )

    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    superseded_note = next(note for note in notes if note.key == "Neo4j")
    assert original.id in (superseded_note.superseded_source_ids or [])

    refreshed = refresh_notes_for_repeated_evidence(notes, store.recent(limit=1)[0])
    assert any(note.key == "Neo4j" for note in refreshed)
