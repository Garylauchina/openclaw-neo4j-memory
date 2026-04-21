from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, product_metadata, refresh_notes_from_memories


def test_product_metadata_exposes_bounded_product_layer(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)

    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    note = next(note for note in notes if note.key == "Neo4j")
    metadata = product_metadata(note)

    assert set(metadata.keys()) == {
        "product_role",
        "evidence_summary",
        "stable_source_summary",
        "retrieval_usefulness_summary",
        "refresh_update_summary",
    }


def test_product_metadata_refreshes_after_new_evidence(tmp_path: Path):
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
    note = next(note for note in updated_notes if note.key == "Neo4j")
    metadata = note.product_metadata

    assert metadata["product_role"]
    assert metadata["evidence_summary"]
    assert metadata["stable_source_summary"] >= 1
