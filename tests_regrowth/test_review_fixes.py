from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, build_memory_context, refresh_notes_from_memories
from minimal_memory_kernel.retrieval import RetrievedMemory
from minimal_memory_kernel.structure import extract_entities


def test_build_memory_context_handles_note_only_results(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    note = next(note for note in notes if note.key == "Neo4j")

    result = RetrievedMemory(
        memory=None,
        note=note,
        entities=[],
        relations=[],
        score=2.0,
        retrieval_reason="test",
        contributing_memory_ids=list(note.source_ids),
        status=note.status,
        retrieval_mode="topic",
    )

    context = build_memory_context([result])
    assert "product:" in context.text
    assert context.included_ids == []


def test_refresh_notes_from_memories_creates_note_when_threshold_is_newly_crossed(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    first = store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    assert first is not None
    notes = build_consolidated_notes([first])
    assert notes == []

    second = store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    assert second is not None
    updated = refresh_notes_from_memories(notes, [first, second])
    assert any(note.key == "Neo4j" for note in updated)


def test_extract_entities_filters_capitalized_stopwords():
    entities = extract_entities("User said This and That should not become entities, but Neo4j should.")
    names = [entity.name for entity in entities]
    assert "User" not in names
    assert "This" not in names
    assert "That" not in names
    assert "Neo4j" in names
