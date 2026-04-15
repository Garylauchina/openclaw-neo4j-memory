#!/usr/bin/env python3
"""Audit source-adjacent claim layer for a probe import."""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore


def fetch_source_entities(store: GraphStore, source_tag: str, import_batch: str, limit: int) -> List[str]:
    rows = store.get_entities_by_source(source_tag=source_tag, import_batch=import_batch, limit=limit)
    return [row["name"] for row in rows]


def fetch_claims(store: GraphStore, entity_names: List[str], limit: int) -> List[Dict[str, Any]]:
    if not entity_names:
        return []
    query = """
    MATCH (c:Claim)-[:ABOUT]->(e:Entity)
    WHERE e.name IN $entity_names
    RETURN e.name AS entity_name,
           c.claim_kind AS claim_kind,
           c.claimed_value AS claimed_value,
           coalesce(c.state, '') AS state,
           coalesce(c.support_score, 0) AS support_score,
           coalesce(c.conflict_score, 0) AS conflict_score,
           coalesce(c.evidence_count, 0) AS evidence_count,
           coalesce(c.source_count, 0) AS source_count
    ORDER BY support_score DESC, conflict_score ASC, entity_name ASC
    LIMIT $limit
    """
    with store.driver.session(database=store._config.database) as session:
        return [dict(record) for record in session.run(query, entity_names=entity_names, limit=limit)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit claim layer for a source-scoped probe")
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--import-batch", required=True)
    parser.add_argument("--entity-limit", type=int, default=100)
    parser.add_argument("--claim-limit", type=int, default=200)
    args = parser.parse_args()

    store = GraphStore(MemoryConfig().neo4j)
    try:
        entity_names = fetch_source_entities(store, args.source_tag, args.import_batch, args.entity_limit)
        claims = fetch_claims(store, entity_names, args.claim_limit)
    finally:
        store.close()

    claim_kind_counts = Counter(row["claim_kind"] or "" for row in claims)
    state_counts = Counter(row["state"] or "" for row in claims)
    claimed_value_counts = Counter(row["claimed_value"] or "" for row in claims)

    print("=== Claim Layer Audit ===")
    print(f"source_tag={args.source_tag}")
    print(f"import_batch={args.import_batch}")
    print(f"source_entities={len(entity_names)}")
    print(f"claims={len(claims)}")
    print(f"claim_kinds={dict(claim_kind_counts)}")
    print(f"states={dict(state_counts)}")
    print(f"top_claimed_values={dict(claimed_value_counts.most_common(10))}")

    print("\n--- Sample claims ---")
    for row in claims[:30]:
        print(
            f"{row['entity_name']}\tkind={row['claim_kind']}\tvalue={row['claimed_value']}"
            f"\tstate={row['state']}\tsupport={row['support_score']}\tconflict={row['conflict_score']}"
            f"\tevidence={row['evidence_count']}\tsources={row['source_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
