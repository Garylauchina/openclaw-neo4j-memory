from pathlib import Path

from minimal_memory_kernel import (
    MinimalMemoryStore,
    build_memory_context,
    make_orchestration_decision,
    retrieve_top_k,
    should_trigger_retrieval,
    should_write_memory,
)


def test_memory_context_keeps_relevant_items_and_suppresses_low_score(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="User prefers Neo4j for memory retrieval design.")
    store.write(source="telegram", content="We discussed gardening metaphors for system cultivation.")
    store.write(source="telegram", content="Neo4j graph structure helps retrieval and relation modeling.")

    results = retrieve_top_k("How should Neo4j help memory retrieval?", list(reversed(store.recent(limit=10))), k=3)
    context = build_memory_context(results, min_score=1.0, max_items=2, max_chars=400)

    assert context.text.startswith("Relevant memory:")
    assert len(context.included_ids) >= 1
    assert len(context.included_ids) <= 2


def test_orchestration_decision_turns_on_injection_for_relevant_results(tmp_path: Path):
    store = MinimalMemoryStore(tmp_path / "raw_memory.json")
    store.write(source="telegram", content="User prefers concise answers about Neo4j retrieval.")

    query = "Please use prior Neo4j retrieval memory to answer."
    should_retrieve = should_trigger_retrieval(query)
    results = retrieve_top_k(query, list(reversed(store.recent(limit=10))), k=2)
    decision = make_orchestration_decision(
        should_write=should_write_memory(query),
        should_retrieve=should_retrieve,
        retrieved_results=results,
        inject_threshold=1.0,
    )

    assert decision.should_retrieve is True
    assert decision.should_inject is True
