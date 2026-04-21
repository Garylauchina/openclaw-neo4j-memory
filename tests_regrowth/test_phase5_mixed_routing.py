from pathlib import Path

from minimal_memory_kernel import MinimalMemoryStore, apply_note_feedback, build_consolidated_notes, retrieve_with_routing


def test_mixed_routing_balances_products_and_raw_memory(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="Neo4j helps retrieval design.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j improves graph-based recall.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j supports relation modeling across sessions.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j keeps provenance visible for later recall.", status="stable", force=True)

    memories = list(reversed(store.recent(limit=10)))
    notes = apply_note_feedback(build_consolidated_notes(memories), helpful_keys=["Neo4j"])
    results = retrieve_with_routing("How does Neo4j help retrieval?", memories=memories, notes=notes, k=4)

    note_results = [result for result in results if result.note is not None]
    memory_results = [result for result in results if result.memory is not None]

    assert note_results
    assert memory_results
    assert len(note_results) <= 2


def test_preference_mode_can_favor_products_without_losing_all_memory_results(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="User prefers concise answers about Neo4j retrieval.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j graph structure helps retrieval and relation modeling.", status="stable", force=True)
    store.write(source="telegram", content="Neo4j supports cross-conversation entity linking.", status="stable", force=True)

    memories = list(reversed(store.recent(limit=10)))
    notes = build_consolidated_notes(memories)
    results = retrieve_with_routing(
        "What preference did the user mention about Neo4j?",
        memories=memories,
        notes=notes,
        k=4,
    )

    assert any(result.note is not None for result in results)
    assert any(result.memory is not None for result in results)
