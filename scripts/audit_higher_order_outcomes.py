#!/usr/bin/env python3
"""Audit higher-order meditation outcomes adjacent to a source-scoped probe."""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore

TARGET_LABELS = ["Strategy", "Belief", "Feedback", "Outcome", "BeliefUpdate", "Observation", "CausalChain"]


def fetch_source_entities(store: GraphStore, source_tag: str, import_batch: str, limit: int) -> List[str]:
    rows = store.get_entities_by_source(source_tag=source_tag, import_batch=import_batch, limit=limit)
    return [row["name"] for row in rows]


def fetch_nodes(store: GraphStore, entity_names: List[str], limit: int) -> List[Dict[str, Any]]:
    if not entity_names:
        return []
    query = """
    MATCH (n)-[r]-(e:Entity)
    WHERE e.name IN $entity_names
      AND ANY(label IN labels(n) WHERE label IN $target_labels)
    RETURN labels(n) AS labels,
           type(r) AS rel_type,
           e.name AS entity_name,
           coalesce(n.content, n.description, n.name, '') AS content
    LIMIT $limit
    """
    with store.driver.session(database=store._config.database) as session:
        return [dict(record) for record in session.run(query, entity_names=entity_names, target_labels=TARGET_LABELS, limit=limit)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit higher-order outcomes for a source-scoped probe")
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--import-batch", required=True)
    parser.add_argument("--entity-limit", type=int, default=100)
    parser.add_argument("--node-limit", type=int, default=200)
    args = parser.parse_args()

    store = GraphStore(MemoryConfig().neo4j)
    try:
        entity_names = fetch_source_entities(store, args.source_tag, args.import_batch, args.entity_limit)
        rows = fetch_nodes(store, entity_names, args.node_limit)
    finally:
        store.close()

    label_counts = Counter(tuple(row["labels"]) for row in rows)
    rel_counts = Counter(row["rel_type"] for row in rows)

    print("=== Higher-Order Outcome Audit ===")
    print(f"source_tag={args.source_tag}")
    print(f"import_batch={args.import_batch}")
    print(f"source_entities={len(entity_names)}")
    print(f"matched_nodes={len(rows)}")
    print(f"labels={dict(label_counts)}")
    print(f"relation_types={dict(rel_counts)}")

    print("\n--- Sample higher-order nodes ---")
    for row in rows[:40]:
        content = (row.get("content") or "").replace("\n", " ")[:160]
        print(f"{row['labels']}\trel={row['rel_type']}\tentity={row['entity_name']}\t{content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
