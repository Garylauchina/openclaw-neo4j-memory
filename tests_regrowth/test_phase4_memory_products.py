from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, refresh_notes_from_memories


def test_consolidated_notes_include_reusable_product_fields(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)

    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    neo4j_note = next(note for note in notes if note.key == "Neo4j")

    assert neo4j_note.product_title
    assert neo4j_note.product_summary
    assert neo4j_note.reusable_form
    assert "Neo4j" in neo4j_note.product_title


def test_product_fields_refresh_with_new_evidence(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))

    new_memory = store.write(
        source="telegram",
        content="Neo4j supports relation modeling across sessions.",
        status="stable",
        force=True,
    )
    assert new_memory is not None

    updated_notes = refresh_notes_from_memories(notes, [new_memory])
    neo4j_note = next(note for note in updated_notes if note.key == "Neo4j")

    assert "Supported by" in neo4j_note.product_summary or neo4j_note.product_summary
    assert "preferred_sources=" in neo4j_note.reusable_form
