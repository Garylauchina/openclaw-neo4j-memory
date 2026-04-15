#!/usr/bin/env python3
"""Audit source-scoped relation retention for probe imports."""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore


def fetch_relations(store: GraphStore, source_tag: str, import_batch: str, limit: int) -> List[Dict[str, Any]]:
    query = """
    MATCH (s:Entity)-[r]->(t:Entity)
    WHERE type(r) <> 'SEEN_IN'
      AND coalesce(r.source_tag, '') = $source_tag
      AND coalesce(r.import_batch, '') = $import_batch
    RETURN s.name AS source,
           type(r) AS relation_type,
           t.name AS target,
           coalesce(r.knowledge_state, '') AS knowledge_state,
           coalesce(r.evidence_count, 0) AS evidence_count,
           coalesce(r.source_count, 0) AS source_count
    ORDER BY evidence_count DESC, relation_type ASC, source ASC
    LIMIT $limit
    """
    with store.driver.session(database=store._config.database) as session:
        result = session.run(query, source_tag=source_tag, import_batch=import_batch, limit=limit)
        return [dict(record) for record in result]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit source-scoped relations")
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--import-batch", required=True)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    store = GraphStore(MemoryConfig().neo4j)
    try:
        rows = fetch_relations(store, args.source_tag, args.import_batch, args.limit)
    finally:
        store.close()

    relation_types = Counter(row["relation_type"] for row in rows)
    states = Counter(row["knowledge_state"] or "unknown" for row in rows)

    print("=== Source Relation Audit ===")
    print(f"source_tag={args.source_tag}")
    print(f"import_batch={args.import_batch}")
    print(f"total={len(rows)}")
    print(f"relation_types={dict(relation_types)}")
    print(f"knowledge_states={dict(states)}")

    print("\n--- Relations ---")
    for row in rows[:50]:
        print(
            f"{row['source']}\t[{row['relation_type']}]\t{row['target']}"
            f"\tstate={row['knowledge_state']}\tevidence={row['evidence_count']}\tsources={row['source_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
