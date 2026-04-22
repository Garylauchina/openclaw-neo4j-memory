from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from .consolidation import ConsolidatedNote, note_priority
from .memory_store import RawMemory
from .routing import apply_routing_decision, build_routing_decision
from .structure import Entity, Relation, entity_overlap, extract_structure


@dataclass
class RetrievedMemory:
    memory: RawMemory | None
    note: ConsolidatedNote | None
    entities: List[Entity]
    relations: List[Relation]
    score: float
    retrieval_reason: str
    contributing_memory_ids: List[str]
    status: str
    retrieval_mode: str


def should_trigger_retrieval(content: str, min_words: int = 4) -> bool:
    text = " ".join(content.strip().split())
    if not text:
        return False
    return len(text.split()) >= min_words


def detect_retrieval_mode(query: str) -> str:
    lowered = query.lower()
    if any(word in lowered for word in ["prefer", "preference", "likes", "wants"]):
        return "preference"
    if any(word in lowered for word in ["why", "how", "explain"]):
        return "explanatory"
    return "topic"


def lexical_overlap_score(query: str, content: str) -> float:
    query_terms = {term.lower() for term in query.split() if term.strip()}
    content_terms = {term.lower() for term in content.split() if term.strip()}
    if not query_terms or not content_terms:
        return 0.0
    return len(query_terms & content_terms) / len(query_terms)


def recentness_score(index: int, total: int) -> float:
    if total <= 1:
        return 1.0
    return (index + 1) / total


def score_memory(query: str, memory: RawMemory, index: int, total: int) -> RetrievedMemory:
    entities, relations = extract_structure(memory.content)
    lexical = lexical_overlap_score(query, memory.content)
    entity_score = float(entity_overlap(query, entities))
    recency = recentness_score(index, total)
    mode = detect_retrieval_mode(query)
    stable_bonus = 0.5 if memory.status == "stable" else 0.0
    preference_bonus = 0.75 if mode == "preference" and "preference_of" in [r.relation_type for r in relations] else 0.0
    explanatory_bonus = 0.4 if mode == "explanatory" and relations else 0.0
    relation_bonus = 0.25 if relations else 0.0
    score = (lexical * 2.0) + entity_score + (recency * 0.5) + stable_bonus + preference_bonus + explanatory_bonus + relation_bonus

    reasons = []
    if lexical > 0:
        reasons.append(f"lexical_overlap={lexical:.2f}")
    if entity_score > 0:
        reasons.append(f"entity_overlap={entity_score:.0f}")
    if stable_bonus > 0:
        reasons.append("stable_bonus=0.50")
    if preference_bonus > 0:
        reasons.append("preference_bonus=0.75")
    if explanatory_bonus > 0:
        reasons.append("explanatory_bonus=0.40")
    if relation_bonus > 0:
        reasons.append("relation_bonus=0.25")
    reasons.append(f"recentness={recency:.2f}")

    return RetrievedMemory(
        memory=memory,
        note=None,
        entities=entities,
        relations=relations,
        score=score,
        retrieval_reason=", ".join(reasons),
        contributing_memory_ids=[memory.id],
        status=memory.status,
        retrieval_mode=mode,
    )


def score_note(query: str, note: ConsolidatedNote, index: int, total: int) -> RetrievedMemory:
    lexical = lexical_overlap_score(query, note.content + " " + note.key + " " + note.product_summary)
    mode = detect_retrieval_mode(query)
    note_type_bonus = 0.5 if mode == "preference" and "preference" in note.note_type else 0.25
    recency = recentness_score(index, total)
    helpful_bonus = note.retrieval_helpful_count * 0.3
    unhelpful_penalty = note.retrieval_unhelpful_count * 0.15
    priority_bonus = note_priority(note) * 0.2
    product_role_bonus = 0.4 if mode == "preference" and note.product_role == "preference_product" else 0.2
    explanatory_bonus = 0.35 if mode == "explanatory" and note.product_role in {"summary_product", "retrieval_anchor_product"} else 0.0
    stable_product_bonus = min(note.stable_source_count, 3) * 0.15
    score = (
        (lexical * 2.0)
        + note_type_bonus
        + (recency * 0.25)
        + helpful_bonus
        + priority_bonus
        + product_role_bonus
        + explanatory_bonus
        + stable_product_bonus
        - unhelpful_penalty
    )

    reasons = []
    if lexical > 0:
        reasons.append(f"lexical_overlap={lexical:.2f}")
    reasons.append(f"note_type_bonus={note_type_bonus:.2f}")
    reasons.append(f"product_role_bonus={product_role_bonus:.2f}")
    if explanatory_bonus > 0:
        reasons.append(f"explanatory_bonus={explanatory_bonus:.2f}")
    if stable_product_bonus > 0:
        reasons.append(f"stable_product_bonus={stable_product_bonus:.2f}")
    if helpful_bonus > 0:
        reasons.append(f"helpful_bonus={helpful_bonus:.2f}")
    if priority_bonus > 0:
        reasons.append(f"priority_bonus={priority_bonus:.2f}")
    if unhelpful_penalty > 0:
        reasons.append(f"unhelpful_penalty={unhelpful_penalty:.2f}")
    reasons.append(f"recentness={recency:.2f}")

    return RetrievedMemory(
        memory=None,
        note=note,
        entities=[],
        relations=[],
        score=score,
        retrieval_reason=", ".join(reasons),
        contributing_memory_ids=list(note.source_ids),
        status=note.status,
        retrieval_mode=mode,
    )


def retrieve_top_k(query: str, memories: Sequence[RawMemory], k: int = 3) -> List[RetrievedMemory]:
    scored = [score_memory(query, memory, index, len(memories)) for index, memory in enumerate(memories)]
    scored.sort(key=lambda item: item.score, reverse=True)
    return scored[:k]


def retrieve_with_routing(
    query: str,
    *,
    memories: Sequence[RawMemory],
    notes: Sequence[ConsolidatedNote],
    k: int = 3,
) -> List[RetrievedMemory]:
    mode = detect_retrieval_mode(query)
    scored_memories = [score_memory(query, memory, index, len(memories)) for index, memory in enumerate(memories)]
    scored_notes = [score_note(query, note, index, len(notes)) for index, note in enumerate(notes)]

    combined = scored_memories + scored_notes
    if mode == "preference":
        combined.sort(key=lambda item: (item.note is not None, item.score), reverse=True)
    elif mode == "explanatory":
        combined.sort(
            key=lambda item: (
                item.note is not None and item.note.product_role in {"summary_product", "retrieval_anchor_product"},
                item.score,
            ),
            reverse=True,
        )
    else:
        combined.sort(
            key=lambda item: (
                item.note is not None and item.note.product_role in {"summary_product", "retrieval_anchor_product"},
                item.score,
            ),
            reverse=True,
        )

    decision = build_routing_decision(mode, k)
    selected = apply_routing_decision(decision, combined, k)
    summary = decision.summary()
    metadata = decision.metadata()
    for item in selected:
        kind = "product" if item.note is not None else "raw_memory"
        item.retrieval_reason = (
            f"{item.retrieval_reason}, selected_kind={kind}, coordination={decision.coordination_reason}, "
            f"routing_summary={summary}, routing_mode={metadata['routing_mode']}, "
            f"balance={metadata['product_raw_balance_summary']}, coordination_counter={metadata['coordination_counter']}"
        )
    return selected
