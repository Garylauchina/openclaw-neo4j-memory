from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, refresh_notes_for_repeated_evidence, revise_memory


def test_revise_memory_marks_old_item_superseded(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    old_memory = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="User prefers long answers about Neo4j retrieval.",
        write_reason="preference_signal",
        status="tentative",
    )
    assert old_memory is not None

    result = revise_memory(
        store,
        old_memory_id=old_memory.id,
        new_content="User prefers concise answers about Neo4j retrieval.",
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        write_reason="revised_preference_signal",
        status="stable",
    )

    assert result.new_memory.supersedes_id == old_memory.id
    assert result.superseded_memory is not None
    assert result.superseded_memory.status == "superseded"
    assert result.superseded_memory.metadata["superseded_by"] == result.new_memory.id


def test_refresh_notes_for_repeated_evidence_updates_note_content(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    first = store.write(source="telegram", content="Neo4j helps retrieval design.", force=True)
    second = store.write(source="telegram", content="Neo4j supports relation modeling.", force=True)
    assert first is not None and second is not None

    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    updated_notes = refresh_notes_for_repeated_evidence(notes, second)

    assert any(note.key == "Neo4j" for note in updated_notes)
