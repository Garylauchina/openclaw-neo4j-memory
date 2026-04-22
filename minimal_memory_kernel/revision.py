from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .consolidation import ConsolidatedNote, build_consolidated_notes
from .memory_store import MinimalMemoryStore, RawMemory


@dataclass
class RevisionResult:
    new_memory: RawMemory
    superseded_memory: Optional[RawMemory]


def revise_memory(
    store: MinimalMemoryStore,
    *,
    old_memory_id: str,
    new_content: str,
    source: str,
    source_type: str,
    source_id: str,
    write_reason: str,
    status: str = "stable",
) -> RevisionResult:
    new_memory = store.write(
        source=source,
        source_type=source_type,
        source_id=source_id,
        content=new_content,
        write_reason=write_reason,
        status=status,
        supersedes_id=old_memory_id,
        force=True,
    )
    if new_memory is None:
        raise RuntimeError("Failed to create revised memory")
    superseded = store.mark_superseded(old_memory_id, new_memory.id)
    return RevisionResult(new_memory=new_memory, superseded_memory=superseded)


def refresh_notes_for_repeated_evidence(notes: Iterable[ConsolidatedNote], memory: RawMemory) -> list[ConsolidatedNote]:
    return refresh_notes_from_memories(notes, [memory])


def refresh_notes_from_memories(notes: Iterable[ConsolidatedNote], memories: Iterable[RawMemory]) -> list[ConsolidatedNote]:
    updated_notes = list(notes)
    grouped_memories = list(memories)

    existing_keys = {note.key.lower() for note in updated_notes}
    candidate_new_notes = build_consolidated_notes(grouped_memories)
    for candidate in candidate_new_notes:
        if candidate.key.lower() not in existing_keys:
            updated_notes.append(candidate)
            existing_keys.add(candidate.key.lower())

    for note in updated_notes:
        related = [memory for memory in grouped_memories if note.key.lower() in memory.content.lower()]
        if not related:
            continue

        stable_related = [memory for memory in related if memory.status == "stable"]
        tentative_related = [memory for memory in related if memory.status == "tentative"]
        superseded_related = [memory for memory in related if memory.status == "superseded"]

        for memory in related:
            if memory.id not in note.source_ids:
                note.source_ids.append(memory.id)

        note.superseded_source_ids = list(note.superseded_source_ids or [])
        for memory in superseded_related:
            if memory.id not in note.superseded_source_ids:
                note.superseded_source_ids.append(memory.id)

        for memory in stable_related:
            if memory.id not in note.preferred_source_ids:
                note.preferred_source_ids.append(memory.id)

        candidate_points = []
        for memory in stable_related + tentative_related + superseded_related:
            normalized = " ".join(memory.content.strip().split())
            if normalized and normalized not in candidate_points:
                candidate_points.append(normalized)
        if candidate_points:
            note.summary_points = (candidate_points + list(note.summary_points))[:3]

        active_count = len([source_id for source_id in note.source_ids if source_id not in set(note.superseded_source_ids or [])])
        note.evidence_count = max(note.evidence_count, len(note.source_ids), active_count)
        note.update_count += len(related)
        note.note_refresh_count += 1
        lead = note.summary_points[0] if note.summary_points else f"based on {active_count} active memories"
        if len(note.summary_points) > 1:
            note.content = f"{note.note_type.replace('_', ' ').title()} for '{note.key}': {lead} (+{len(note.summary_points) - 1} supporting points)"
        else:
            note.content = f"{note.note_type.replace('_', ' ').title()} for '{note.key}': {lead}"
        if note.note_type == "preference_note":
            note.product_role = "preference_product"
        elif note.note_type == "summary_note":
            note.product_role = "summary_product"
        elif note.note_type == "retrieval_anchor_note" or note.preferred_source_ids:
            note.product_role = "retrieval_anchor_product"
        else:
            note.product_role = "topic_product"
        note.product_title = f"{note.product_role.replace('_', ' ').title().strip()}: {note.key}"
        if note.summary_points:
            if len(note.summary_points) == 1:
                note.product_summary = note.summary_points[0]
            else:
                note.product_summary = f"{note.summary_points[0]} Supported by {len(note.summary_points) - 1} additional memory points."
        note.reusable_form = (
            f"{note.product_role.replace('_', ' ')} | key={note.key} | "
            f"preferred_sources={len(note.preferred_source_ids)} | evidence_count={note.evidence_count}"
        )
        note.supporting_evidence = note.summary_points[1:] if len(note.summary_points) > 1 else []
        note.evidence_surface = (
            f"preferred_sources={len(note.preferred_source_ids)}; "
            f"evidence_count={note.evidence_count}; "
            f"supporting_evidence={len(note.supporting_evidence)}"
        )
        note.product_metadata = {
            "product_role": note.product_role,
            "evidence_summary": note.evidence_surface,
            "stable_source_summary": len(note.preferred_source_ids),
            "retrieval_usefulness_summary": note.retrieval_helpful_count - note.retrieval_unhelpful_count,
            "refresh_update_summary": note.note_refresh_count + note.update_count,
        }

    return updated_notes
