from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, build_consolidated_notes, detect_retrieval_mode, retrieve_with_routing


def test_detect_retrieval_mode_supports_explanatory_queries():
    assert detect_retrieval_mode("Why does Neo4j help retrieval?") == "explanatory"
    assert detect_retrieval_mode("How does Neo4j help retrieval?") == "explanatory"


def test_explanatory_mode_surfaces_summary_like_products(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j supports relation modeling across sessions.", status="stable", force=True)

    memories = list(reversed(store.recent(limit=10)))
    notes = build_consolidated_notes(memories)
    results = retrieve_with_routing(
        "Why does Neo4j help retrieval?",
        memories=memories,
        notes=notes,
        k=4,
    )

    assert any(result.note is not None for result in results)
    note_result = next(result for result in results if result.note is not None)
    assert "explanatory_bonus" in note_result.retrieval_reason or "coordination=explanatory mode" in note_result.retrieval_reason
