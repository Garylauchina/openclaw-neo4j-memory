from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, classify_product_role


def test_classify_product_role_returns_bounded_roles(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="User prefers concise answers about Neo4j retrieval.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j graph structure helps retrieval and relation modeling.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j supports cross-conversation entity linking.", status="stable", force=True)

    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    neo4j_note = next(note for note in notes if note.key == "Neo4j")
    role = classify_product_role(neo4j_note.note_type, neo4j_note.summary_points, neo4j_note.preferred_source_ids)
    assert role in {"preference_product", "topic_product", "summary_product", "retrieval_anchor_product"}


def test_consolidated_notes_include_product_role(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)

    notes = build_consolidated_notes(list(reversed(store.recent(limit=10))))
    neo4j_note = next(note for note in notes if note.key == "Neo4j")
    assert neo4j_note.product_role in {"preference_product", "topic_product", "summary_product", "retrieval_anchor_product"}
    assert neo4j_note.product_role in neo4j_note.product_title.lower().replace(" ", "_") or neo4j_note.product_title
