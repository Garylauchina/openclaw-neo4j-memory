#!/usr/bin/env python3
"""Audit source-scoped entities for low-information noise.

This script is designed for probe-style analysis. It does not modify the graph.
It inspects entities attached to a specific ImportBatch / source_tag and reports
likely low-information entities versus more credible ones.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore

LOW_INFO_WORDS = {
    "Here", "Use", "Remember", "Good", "Consider", "Instead", "Keep", "Set", "Create",
    "Need", "Make", "Take", "Try", "Best", "Help", "Learn", "Start", "Find", "Check",
}


def is_low_information(name: str, entity_type: str) -> bool:
    if not name:
        return True
    if entity_type.lower() == "concept" and name in LOW_INFO_WORDS:
        return True
    if entity_type.lower() == "concept" and len(name) <= 3 and name.isalpha():
        return True
    if len(name.split()) == 1 and name[:1].isupper() and name[1:].islower() and entity_type.lower() == "concept":
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit source-scoped entities")
    parser.add_argument("--source-tag", default="", help="Source tag to inspect")
    parser.add_argument("--import-batch", default="", help="Import batch to inspect")
    parser.add_argument("--limit", type=int, default=200, help="Max entities to inspect")
    args = parser.parse_args()

    store = GraphStore(MemoryConfig().neo4j)
    try:
        rows = store.get_entities_by_source(source_tag=args.source_tag, import_batch=args.import_batch, limit=args.limit)
    finally:
        store.close()

    low_info: List[Dict[str, Any]] = []
    plausible: List[Dict[str, Any]] = []
    for row in rows:
        if is_low_information(row.get("name", ""), row.get("entity_type", "")):
            low_info.append(row)
        else:
            plausible.append(row)

    print("=== Source Entity Audit ===")
    print(f"source_tag={args.source_tag}")
    print(f"import_batch={args.import_batch}")
    print(f"total={len(rows)}")
    print(f"low_information={len(low_info)}")
    print(f"plausible={len(plausible)}")

    print("\n--- Likely low-information entities ---")
    for row in low_info[:50]:
        print(f"{row['name']}\t{row['entity_type']}\t{row.get('mention_count', 0)}")

    print("\n--- More plausible entities ---")
    for row in plausible[:50]:
        print(f"{row['name']}\t{row['entity_type']}\t{row.get('mention_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
