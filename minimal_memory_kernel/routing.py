from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, List

if TYPE_CHECKING:
    from .retrieval import RetrievedMemory


@dataclass
class RoutingDecision:
    mode: str
    max_note_count: int
    max_memory_count: int
    selected_note_count: int
    selected_memory_count: int
    coordination_reason: str

    def summary(self) -> str:
        return (
            f"mode={self.mode}; max_note_count={self.max_note_count}; "
            f"max_memory_count={self.max_memory_count}; reason={self.coordination_reason}"
        )

    def metadata(self) -> dict[str, str | int]:
        return {
            "routing_mode": self.mode,
            "coordination_reason": self.coordination_reason,
            "product_raw_balance_summary": f"notes={self.selected_note_count}/{self.max_note_count}; memories={self.selected_memory_count}/{self.max_memory_count}",
            "coordination_counter": self.selected_note_count + self.selected_memory_count,
        }


def build_routing_decision(mode: str, k: int) -> RoutingDecision:
    if mode == "preference":
        return RoutingDecision(
            mode=mode,
            max_note_count=max(1, (k + 1) // 2),
            max_memory_count=max(1, k // 2),
            selected_note_count=0,
            selected_memory_count=0,
            coordination_reason="preference mode favors products but preserves raw memory presence",
        )
    if mode == "explanatory":
        return RoutingDecision(
            mode=mode,
            max_note_count=max(1, (k + 1) // 2),
            max_memory_count=max(1, max(1, k // 3)),
            selected_note_count=0,
            selected_memory_count=0,
            coordination_reason="explanatory mode favors summary-like products while preserving some raw evidence",
        )
    return RoutingDecision(
        mode=mode,
        max_note_count=max(1, k // 2),
        max_memory_count=max(1, k // 2),
        selected_note_count=0,
        selected_memory_count=0,
        coordination_reason="topic mode keeps products and raw memory balanced",
    )


def apply_routing_decision(decision: RoutingDecision, combined: Iterable["RetrievedMemory"], k: int) -> List["RetrievedMemory"]:
    selected: List["RetrievedMemory"] = []
    deferred_notes: List["RetrievedMemory"] = []
    deferred_memories: List["RetrievedMemory"] = []

    for item in combined:
        if item.note is not None:
            if decision.selected_note_count >= decision.max_note_count:
                deferred_notes.append(item)
                continue
            decision.selected_note_count += 1
            selected.append(item)
        else:
            if decision.selected_memory_count >= decision.max_memory_count:
                deferred_memories.append(item)
                continue
            decision.selected_memory_count += 1
            selected.append(item)
        if len(selected) >= k:
            break

    if len(selected) < k:
        for item in deferred_notes + deferred_memories:
            selected.append(item)
            if len(selected) >= k:
                break

    return selected
