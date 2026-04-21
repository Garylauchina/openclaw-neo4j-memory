from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class RawMemory:
    id: str
    timestamp: str
    source: str
    source_type: str
    source_id: str
    content: str
    write_reason: str
    status: str
    supersedes_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        source: str,
        content: str,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        write_reason: str = "accepted_by_write_rule",
        status: str = "tentative",
        supersedes_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "RawMemory":
        resolved_context = context or {}
        resolved_source_type = source_type or source
        resolved_source_id = source_id or str(resolved_context.get("source_id") or resolved_context.get("chat_id") or "unknown")
        return cls(
            id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            source_type=resolved_source_type,
            source_id=resolved_source_id,
            content=content,
            write_reason=write_reason,
            status=status,
            supersedes_id=supersedes_id,
            context=resolved_context,
            metadata=metadata or {},
        )


DEFAULT_LOW_VALUE_PREFIXES = (
    "ok",
    "okay",
    "thanks",
    "thank you",
    "got it",
    "sure",
    "nice",
    "cool",
)


def should_write_memory(
    content: str,
    *,
    force: bool = False,
    min_length: int = 12,
) -> bool:
    if force:
        return True

    normalized = " ".join(content.strip().lower().split())
    if not normalized:
        return False

    if len(normalized) < min_length and normalized in DEFAULT_LOW_VALUE_PREFIXES:
        return False

    if normalized in DEFAULT_LOW_VALUE_PREFIXES:
        return False

    return True


class MinimalMemoryStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _load(self) -> List[Dict[str, Any]]:
        raw = self.path.read_text(encoding="utf-8").strip()
        if not raw:
            return []
        return json.loads(raw)

    def _save(self, records: List[Dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    def write(
        self,
        *,
        source: str,
        content: str,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        write_reason: str = "accepted_by_write_rule",
        status: str = "tentative",
        supersedes_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        force: bool = False,
    ) -> Optional[RawMemory]:
        if not should_write_memory(content, force=force):
            return None

        memory = RawMemory.create(
            source=source,
            content=content,
            source_type=source_type,
            source_id=source_id,
            write_reason=write_reason,
            status=status,
            supersedes_id=supersedes_id,
            context=context,
            metadata=metadata,
        )
        records = self._load()
        records.append(asdict(memory))
        self._save(records)
        return memory

    def get(self, memory_id: str) -> Optional[RawMemory]:
        for item in self._load():
            if item["id"] == memory_id:
                return RawMemory(**item)
        return None

    def recent(self, limit: int = 10) -> List[RawMemory]:
        records = self._load()
        sliced = records[-limit:]
        return [RawMemory(**item) for item in reversed(sliced)]

    def update_status(self, memory_id: str, status: str) -> Optional[RawMemory]:
        records = self._load()
        updated = None
        for item in records:
            if item["id"] == memory_id:
                item["status"] = status
                updated = RawMemory(**item)
                break
        if updated is not None:
            self._save(records)
        return updated

    def mark_superseded(self, old_memory_id: str, new_memory_id: str) -> Optional[RawMemory]:
        records = self._load()
        updated = None
        for item in records:
            if item["id"] == old_memory_id:
                item["status"] = "superseded"
                item["metadata"] = dict(item.get("metadata") or {})
                item["metadata"]["superseded_by"] = new_memory_id
                updated = RawMemory(**item)
                break
        if updated is not None:
            self._save(records)
        return updated
