from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Literal, Tuple

from .memory_store import RawMemory
from .structure import extract_structure


NoteType = Literal["preference_note", "topic_note", "summary_note", "retrieval_anchor_note"]
ProductRole = Literal["preference_product", "topic_product", "summary_product", "retrieval_anchor_product"]


@dataclass
class ConsolidatedNote:
    note_type: NoteType
    key: str
    content: str
    source_ids: List[str]
    status: str = "stable"
    superseded_source_ids: List[str] | None = None
    summary_points: List[str] = field(default_factory=list)
    preferred_source_ids: List[str] = field(default_factory=list)
    evidence_count: int = 0
    retrieval_helpful_count: int = 0
    retrieval_unhelpful_count: int = 0
    update_count: int = 0
    note_refresh_count: int = 0
    product_role: ProductRole = "topic_product"
    product_title: str = ""
    product_summary: str = ""
    reusable_form: str = ""
    supporting_evidence: List[str] = field(default_factory=list)
    evidence_surface: str = ""
    product_metadata: Dict[str, str | int] = field(default_factory=dict)

    @property
    def stable_source_count(self) -> int:
        return len(self.preferred_source_ids)


def dedupe_memories(memories: Iterable[RawMemory]) -> Tuple[List[RawMemory], List[List[str]]]:
    unique: List[RawMemory] = []
    duplicate_groups: List[List[str]] = []
    seen: Dict[str, RawMemory] = {}

    for memory in memories:
        normalized = " ".join(memory.content.strip().lower().split())
        if normalized in seen:
            duplicate_groups.append([seen[normalized].id, memory.id])
            continue
        seen[normalized] = memory
        unique.append(memory)

    return unique, duplicate_groups


def mark_frequent_entities(memories: Iterable[RawMemory], min_count: int = 2) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for memory in memories:
        entities, _ = extract_structure(memory.content)
        names = {entity.name for entity in entities}
        for name in names:
            counts[name] = counts.get(name, 0) + 1
    return {name: count for name, count in counts.items() if count >= min_count}


def classify_note_type(entity_name: str, related_memories: List[RawMemory]) -> NoteType:
    relation_types = []
    for memory in related_memories:
        _, relations = extract_structure(memory.content)
        relation_types.extend(relation.relation_type for relation in relations)

    if "preference_of" in relation_types:
        return "preference_note"
    if len(related_memories) >= 3:
        return "summary_note"
    if any(entity_name.lower() in memory.content.lower() and memory.status == "stable" for memory in related_memories):
        return "retrieval_anchor_note"
    return "topic_note"


def _build_summary_points(related_memories: List[RawMemory], limit: int = 3) -> List[str]:
    ordered = sorted(
        related_memories,
        key=lambda memory: (
            memory.status == "stable",
            memory.status != "superseded",
            memory.timestamp,
        ),
        reverse=True,
    )
    points: List[str] = []
    seen: set[str] = set()
    for memory in ordered:
        normalized = " ".join(memory.content.strip().split())
        if normalized.lower() in seen:
            continue
        seen.add(normalized.lower())
        points.append(normalized)
        if len(points) >= limit:
            break
    return points


def product_metadata(note: ConsolidatedNote) -> Dict[str, str | int]:
    return {
        "product_role": note.product_role,
        "evidence_summary": note.evidence_surface,
        "stable_source_summary": note.stable_source_count,
        "retrieval_usefulness_summary": note.retrieval_helpful_count - note.retrieval_unhelpful_count,
        "refresh_update_summary": note.note_refresh_count + note.update_count,
    }


def note_quality_signals(note: ConsolidatedNote) -> Dict[str, int]:
    return {
        "retrieval_helpful_count": note.retrieval_helpful_count,
        "retrieval_unhelpful_count": note.retrieval_unhelpful_count,
        "update_count": note.update_count,
        "note_refresh_count": note.note_refresh_count,
        "stable_source_count": note.stable_source_count,
        "evidence_count": note.evidence_count,
    }


def note_priority(note: ConsolidatedNote) -> float:
    signals = note_quality_signals(note)
    base = float(signals["evidence_count"])
    helpful_bonus = signals["retrieval_helpful_count"] * 0.5
    unhelpful_penalty = signals["retrieval_unhelpful_count"] * 0.25
    preferred_bonus = min(signals["stable_source_count"], 3) * 0.2
    refresh_bonus = min(signals["note_refresh_count"], 3) * 0.1
    update_bonus = min(signals["update_count"], 3) * 0.1
    return base + helpful_bonus + preferred_bonus + refresh_bonus + update_bonus - unhelpful_penalty


def classify_product_role(note_type: NoteType, summary_points: List[str], preferred_source_ids: List[str]) -> ProductRole:
    if note_type == "preference_note":
        return "preference_product"
    if note_type == "summary_note":
        return "summary_product"
    if note_type == "retrieval_anchor_note" or preferred_source_ids:
        return "retrieval_anchor_product"
    return "topic_product"


def _build_product_title(product_role: ProductRole, entity_name: str) -> str:
    label = product_role.replace("_", " ").title().strip()
    return f"{label}: {entity_name}"


def _build_product_summary(product_role: ProductRole, entity_name: str, summary_points: List[str]) -> str:
    if not summary_points:
        return f"Reusable {product_role.replace('_', ' ')} for {entity_name}."
    lead = summary_points[0]
    if len(summary_points) == 1:
        return lead
    return f"{lead} Supported by {len(summary_points) - 1} additional memory points."


def _build_reusable_form(product_role: ProductRole, entity_name: str, preferred_count: int, evidence_count: int) -> str:
    return (
        f"{product_role.replace('_', ' ')} | key={entity_name} | "
        f"preferred_sources={preferred_count} | evidence_count={evidence_count}"
    )


def _build_supporting_evidence(summary_points: List[str]) -> List[str]:
    if len(summary_points) <= 1:
        return []
    return summary_points[1:]


def _build_evidence_surface(preferred_count: int, evidence_count: int, supporting_evidence_count: int) -> str:
    return (
        f"preferred_sources={preferred_count}; "
        f"evidence_count={evidence_count}; "
        f"supporting_evidence={supporting_evidence_count}"
    )


def _compose_note_content(note_type: str, entity_name: str, active_count: int, summary_points: List[str]) -> str:
    label = note_type.replace("_", " ").title()
    if not summary_points:
        return f"{label} for '{entity_name}' based on {active_count} active memories."
    lead = summary_points[0]
    if len(summary_points) == 1:
        return f"{label} for '{entity_name}': {lead}"
    return f"{label} for '{entity_name}': {lead} (+{len(summary_points) - 1} supporting points)"


def build_consolidated_notes(memories: Iterable[RawMemory], min_count: int = 2) -> List[ConsolidatedNote]:
    memory_list = list(memories)
    frequent = mark_frequent_entities(memory_list, min_count=min_count)
    notes: List[ConsolidatedNote] = []

    for entity_name, count in frequent.items():
        related_memories = [memory for memory in memory_list if entity_name.lower() in memory.content.lower()]
        active_memories = [memory for memory in related_memories if memory.status != "superseded"]
        source_ids = [memory.id for memory in related_memories]

        note_type = classify_note_type(entity_name, related_memories)

        superseded_source_ids = [memory.id for memory in related_memories if memory.status == "superseded"]
        preferred_source_ids = [memory.id for memory in active_memories if memory.status == "stable"]
        summary_points = _build_summary_points(active_memories or related_memories)
        active_count = len(active_memories)
        content = _compose_note_content(note_type, entity_name, active_count, summary_points)

        product_role = classify_product_role(note_type, summary_points, preferred_source_ids)
        notes.append(
            ConsolidatedNote(
                note_type=note_type,
                key=entity_name,
                content=content,
                source_ids=source_ids,
                superseded_source_ids=superseded_source_ids,
                summary_points=summary_points,
                preferred_source_ids=preferred_source_ids,
                evidence_count=count,
                product_role=product_role,
                product_title=_build_product_title(product_role, entity_name),
                product_summary=_build_product_summary(product_role, entity_name, summary_points),
                reusable_form=_build_reusable_form(product_role, entity_name, len(preferred_source_ids), count),
                supporting_evidence=_build_supporting_evidence(summary_points),
                evidence_surface=_build_evidence_surface(len(preferred_source_ids), count, max(len(summary_points) - 1, 0)),
                product_metadata={},
            )
        )

    for note in notes:
        note.product_metadata = product_metadata(note)
    return notes


def run_lightweight_consolidation(memories: Iterable[RawMemory]) -> Dict[str, object]:
    memory_list = list(memories)
    unique, duplicate_groups = dedupe_memories(memory_list)
    frequent_entities = mark_frequent_entities(unique)
    notes = build_consolidated_notes(unique)
    return {
        "unique_memories": unique,
        "duplicate_groups": duplicate_groups,
        "frequent_entities": frequent_entities,
        "consolidated_notes": notes,
    }
