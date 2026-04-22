from __future__ import annotations

from typing import Iterable, List

from .consolidation import ConsolidatedNote, note_priority


def apply_note_feedback(
    notes: Iterable[ConsolidatedNote],
    *,
    helpful_keys: Iterable[str] = (),
    unhelpful_keys: Iterable[str] = (),
) -> List[ConsolidatedNote]:
    helpful_set = {key.lower() for key in helpful_keys}
    unhelpful_set = {key.lower() for key in unhelpful_keys}

    updated: List[ConsolidatedNote] = []
    for note in notes:
        if note.key.lower() in helpful_set:
            note.retrieval_helpful_count += 1
            note.update_count += 1
        if note.key.lower() in unhelpful_set:
            note.retrieval_unhelpful_count += 1
            note.update_count += 1
        updated.append(note)

    updated.sort(key=note_priority, reverse=True)
    return updated
