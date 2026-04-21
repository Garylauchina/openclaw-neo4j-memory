from pathlib import Path

from minimal_memory_kernel import (
    MinimalMemoryStore,
    apply_note_feedback,
    build_consolidated_notes,
    retrieve_with_routing,
)


def test_apply_note_feedback_promotes_helpful_notes(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    store.write(source="telegram", content="Graphs can support entity recall in assistants.", status="stable", force=True)

    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    updated = apply_note_feedback(notes, helpful_keys=["Neo4j"])
    neo4j_note = next(note for note in updated if note.key == "Neo4j")

    assert neo4j_note.retrieval_helpful_count == 1


def test_retrieve_with_routing_prefers_helpful_notes(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j supports relation modeling across sessions.", status="stable", force=True)

    memories = list(reversed(store.recent(limit=10)))
    notes = build_consolidated_notes(memories)
    notes = apply_note_feedback(notes, helpful_keys=["Neo4j"])

    results = retrieve_with_routing(
        "How does Neo4j help retrieval?",
        memories=memories,
        notes=notes,
        k=5,
    )

    assert len(results) >= 1
    neo4j_note_result = next(result for result in results if result.note is not None and result.note.key == "Neo4j")
    assert neo4j_note_result.note.retrieval_helpful_count == 1
    assert "helpful_bonus" in neo4j_note_result.retrieval_reason
