#!/usr/bin/env python3
"""Audit recent meditation-induced graph deltas around a given timestamp/run window."""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore

TARGET_LABELS = ["Strategy", "Belief", "Claim", "Feedback", "Outcome", "BeliefUpdate", "Observation", "CausalChain"]


def fetch_recent_non_entity_nodes(store: GraphStore, since_ms: int, limit: int) -> List[Dict[str, Any]]:
    query = """
    MATCH (n)
    WHERE ANY(label IN labels(n) WHERE label IN $target_labels)
      AND coalesce(n.updated_at, n.created_at, 0) >= $since_ms
    RETURN labels(n) AS labels,
           coalesce(n.updated_at, n.created_at, 0) AS ts,
           coalesce(n.content, n.description, n.name, n.claim_kind, '') AS content
    ORDER BY ts DESC
    LIMIT $limit
    """
    with store.driver.session(database=store._config.database) as session:
        return [dict(record) for record in session.run(query, target_labels=TARGET_LABELS, since_ms=since_ms, limit=limit)]


def fetch_recent_entity_edges(store: GraphStore, since_ms: int, limit: int) -> List[Dict[str, Any]]:
    query = """
    MATCH (a)-[r]->(b)
    WHERE type(r) <> 'SEEN_IN'
      AND coalesce(r.updated_at, r.created_at, 0) >= $since_ms
    RETURN labels(a) AS source_labels,
           coalesce(a.name, a.content, a.description, '') AS source,
           type(r) AS rel_type,
           labels(b) AS target_labels,
           coalesce(b.name, b.content, b.description, '') AS target,
           coalesce(r.updated_at, r.created_at, 0) AS ts
    ORDER BY ts DESC
    LIMIT $limit
    """
    with store.driver.session(database=store._config.database) as session:
        return [dict(record) for record in session.run(query, since_ms=since_ms, limit=limit)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit recent meditation deltas")
    parser.add_argument("--since-ms", type=int, required=True)
    parser.add_argument("--node-limit", type=int, default=100)
    parser.add_argument("--edge-limit", type=int, default=100)
    args = parser.parse_args()

    store = GraphStore(MemoryConfig().neo4j)
    try:
        nodes = fetch_recent_non_entity_nodes(store, args.since_ms, args.node_limit)
        edges = fetch_recent_entity_edges(store, args.since_ms, args.edge_limit)
    finally:
        store.close()

    print("=== Meditation Delta Audit ===")
    print(f"since_ms={args.since_ms}")
    print(f"recent_non_entity_nodes={len(nodes)}")
    print(f"recent_edges={len(edges)}")

    print("\n--- Recent non-Entity nodes ---")
    for row in nodes[:40]:
        content = (row.get('content') or '').replace('\n', ' ')[:160]
        print(f"ts={row['ts']}\tlabels={row['labels']}\t{content}")

    print("\n--- Recent edges ---")
    for row in edges[:60]:
        print(f"ts={row['ts']}\t{row['source_labels']}::{row['source']}\t[{row['rel_type']}]\t{row['target_labels']}::{row['target']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
