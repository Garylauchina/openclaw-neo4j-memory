from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, refresh_notes_for_repeated_evidence


def test_consolidated_notes_include_summary_points_and_preferred_sources(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    stable_memory = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="Neo4j graph structure helps retrieval and relation modeling.",
        write_reason="topic_signal",
        status="stable",
    )
    tentative_memory = store.write(
        source="telegram",
        source_type="telegram",
        source_id="chat-123",
        content="Neo4j also helps connect entities across conversations.",
        write_reason="topic_signal",
        status="tentative",
    )

    assert stable_memory is not None and tentative_memory is not None
    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    neo4j_note = next(note for note in notes if note.key == "Neo4j")

    assert neo4j_note.summary_points
    assert stable_memory.id in neo4j_note.preferred_source_ids
    assert neo4j_note.evidence_count >= 2
    assert "Neo4j" in neo4j_note.content


def test_repeated_evidence_refresh_updates_note_summary_points(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j graph structure helps retrieval.", status="stable", force=True)
    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))

    new_memory = store.write(
        source="telegram",
        content="Neo4j supports relation modeling across multiple turns.",
        status="stable",
        force=True,
    )
    assert new_memory is not None

    updated_notes = refresh_notes_for_repeated_evidence(notes, new_memory)
    neo4j_note = next(note for note in updated_notes if note.key == "Neo4j")

    assert any("relation modeling" in point for point in neo4j_note.summary_points)
    assert new_memory.id in neo4j_note.preferred_source_ids
    assert "supporting points" in neo4j_note.content or "Neo4j" in neo4j_note.content
