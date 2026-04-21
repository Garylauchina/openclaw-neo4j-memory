from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, refresh_notes_from_memories


def test_consolidated_products_separate_surface_from_supporting_evidence(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j supports relation modeling across sessions.", status="stable", force=True)

    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    neo4j_note = next(note for note in notes if note.key == "Neo4j")

    assert neo4j_note.product_summary
    assert isinstance(neo4j_note.supporting_evidence, list)
    assert neo4j_note.evidence_surface


def test_product_evidence_fields_refresh_with_new_accumulated_evidence(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))

    new_memories = [
        store.write(source="telegram", content="Neo4j supports relation modeling across sessions.", status="stable", force=True),
        store.write(source="telegram", content="Neo4j helps entity linking across turns.", status="stable", force=True),
    ]
    assert all(memory is not None for memory in new_memories)

    updated_notes = refresh_notes_from_memories(notes, [memory for memory in new_memories if memory is not None])
    neo4j_note = next(note for note in updated_notes if note.key == "Neo4j")

    assert neo4j_note.evidence_surface
    assert len(neo4j_note.supporting_evidence) >= 1 or len(neo4j_note.summary_points) >= 1
