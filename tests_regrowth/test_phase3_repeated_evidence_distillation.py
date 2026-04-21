from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, refresh_notes_from_memories


def test_refresh_notes_from_grouped_memories_prioritizes_stable_evidence(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))

    stable_memory = store.write(
        source="telegram",
        content="Neo4j supports stable relation modeling across sessions.",
        status="stable",
        force=True,
    )
    tentative_memory = store.write(
        source="telegram",
        content="Neo4j may also help speculative cross-session linking.",
        status="tentative",
        force=True,
    )
    assert stable_memory is not None and tentative_memory is not None

    updated = refresh_notes_from_memories(notes, [tentative_memory, stable_memory])
    neo4j_note = next(note for note in updated if note.key == "Neo4j")

    assert neo4j_note.preferred_source_ids[0] == stable_memory.id or stable_memory.id in neo4j_note.preferred_source_ids
    assert any("stable relation modeling" in point for point in neo4j_note.summary_points)
    assert neo4j_note.evidence_count >= 3


def test_refresh_notes_from_grouped_memories_handles_multiple_related_updates(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))

    first = store.write(source="telegram", content="Neo4j supports relation modeling.", status="stable", force=True)
    second = store.write(source="telegram", content="Neo4j supports entity linking across turns.", status="stable", force=True)
    assert first is not None and second is not None

    updated = refresh_notes_from_memories(notes, [first, second])
    neo4j_note = next(note for note in updated if note.key == "Neo4j")

    assert len(neo4j_note.summary_points) >= 2
    assert first.id in neo4j_note.preferred_source_ids
    assert second.id in neo4j_note.preferred_source_ids
