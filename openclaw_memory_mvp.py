"""OpenClaw-first Neo4j Memory MVP wrapper.

This module defines a small, stable, tool-like surface over the current
mainline memory system. It is intentionally thin: skill/workflow orchestration
should live outside this file.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from meditation_memory.config import MemoryConfig
from meditation_memory.memory_system import MemorySystem


class OpenClawMemoryMVP:
    """Minimal OpenClaw-facing wrapper around the mainline memory system."""

    def __init__(self, config: Optional[MemoryConfig] = None):
        self._memory = MemorySystem(config or MemoryConfig())
        self._initialized = False

    def init(self) -> None:
        if not self._initialized:
            self._memory.init()
            self._initialized = True

    def close(self) -> None:
        if self._initialized:
            self._memory.close()
            self._initialized = False

    def ingest_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None, use_llm: bool = True) -> Dict[str, Any]:
        payload = text if not metadata else f"{text}\n\n[metadata]\n{metadata}"
        result = self._memory.ingest(payload, use_llm=use_llm)
        return {
            "status": "success",
            "tool": "ingest_memory",
            "data": result.to_dict(),
        }

    def retrieve_context(self, query: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        options = options or {}
        result = self._memory.retrieve_context(query, use_llm=options.get("use_llm", True))
        return {
            "status": "success",
            "tool": "retrieve_context",
            "data": result.to_dict(),
        }

    def build_prompt_context(self, query: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        options = options or {}
        prompt = self._memory.build_prompt(
            query,
            base_prompt=options.get("base_prompt", ""),
            use_llm=options.get("use_llm", True),
        )
        return {
            "status": "success",
            "tool": "build_prompt_context",
            "data": {
                "prompt": prompt,
            },
        }

    def memory_stats(self) -> Dict[str, Any]:
        return {
            "status": "success",
            "tool": "memory_stats",
            "data": self._memory.get_stats(),
        }
