from pathlib import Path

from minimal_memory_kernel import (
    MinimalMemoryStore,
    apply_note_feedback,
    build_consolidated_notes,
    note_quality_signals,
    refresh_notes_from_memories,
)


def test_note_quality_signals_expose_bounded_quality_layer(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))

    note = notes[0]
    signals = note_quality_signals(note)
    assert set(signals.keys()) == {
        "retrieval_helpful_count",
        "retrieval_unhelpful_count",
        "update_count",
        "note_refresh_count",
        "stable_source_count",
        "evidence_count",
    }


def test_quality_signals_update_after_feedback_and_refresh(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    notes = apply_note_feedback(notes, helpful_keys=["Neo4j"])

    new_memory = store.write(
        source="telegram",
        content="Neo4j supports relation modeling across sessions.",
        status="stable",
        force=True,
    )
    assert new_memory is not None

    notes = refresh_notes_from_memories(notes, [new_memory])
    neo4j_note = next(note for note in notes if note.key == "Neo4j")
    signals = note_quality_signals(neo4j_note)

    assert signals["retrieval_helpful_count"] >= 1
    assert signals["update_count"] >= 2
    assert signals["note_refresh_count"] >= 1
    assert signals["stable_source_count"] >= 1
