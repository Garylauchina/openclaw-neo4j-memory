from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .retrieval import RetrievedMemory


@dataclass
class MemoryContext:
    text: str
    included_ids: List[str]
    suppressed_ids: List[str]


@dataclass
class OrchestrationDecision:
    should_write: bool
    should_retrieve: bool
    should_inject: bool


def should_inject_memory(results: Iterable[RetrievedMemory], min_score: float = 1.0) -> bool:
    results = list(results)
    if not results:
        return False
    return results[0].score >= min_score


def suppress_irrelevant_memories(
    results: Iterable[RetrievedMemory],
    *,
    min_score: float = 1.0,
    max_items: int = 3,
) -> List[RetrievedMemory]:
    kept: List[RetrievedMemory] = []
    for result in results:
        if result.score < min_score:
            continue
        kept.append(result)
        if len(kept) >= max_items:
            break
    return kept


def build_memory_context(
    results: Iterable[RetrievedMemory],
    *,
    min_score: float = 1.0,
    max_items: int = 3,
    max_chars: int = 800,
) -> MemoryContext:
    results = list(results)
    kept = suppress_irrelevant_memories(results, min_score=min_score, max_items=max_items)
    kept_ids = [item.memory.id for item in kept if item.memory is not None]
    suppressed_ids = [
        item.memory.id
        for item in results
        if item.memory is not None and item.memory.id not in kept_ids
    ]

    lines = ["Relevant memory:"]
    for item in kept:
        if item.memory is not None:
            lines.append(f"- ({item.memory.source}) {item.memory.content}")
        elif item.note is not None:
            lines.append(f"- (product:{item.note.product_role}) {item.note.product_summary or item.note.content}")

    text = "\n".join(lines) if len(lines) > 1 else ""
    if len(text) > max_chars:
        text = text[: max_chars - 3].rstrip() + "..."

    return MemoryContext(text=text, included_ids=kept_ids, suppressed_ids=suppressed_ids)


def make_orchestration_decision(
    *,
    should_write: bool,
    should_retrieve: bool,
    retrieved_results: Iterable[RetrievedMemory],
    inject_threshold: float = 1.0,
) -> OrchestrationDecision:
    should_inject = should_retrieve and should_inject_memory(retrieved_results, min_score=inject_threshold)
    return OrchestrationDecision(
        should_write=should_write,
        should_retrieve=should_retrieve,
        should_inject=should_inject,
    )
