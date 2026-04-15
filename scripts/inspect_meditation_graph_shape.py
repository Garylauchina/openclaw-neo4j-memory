#!/usr/bin/env python3
"""Inspect actual graph shape for meditation/distillation outputs in the current mainline DB."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore


def run_query(store: GraphStore, query: str):
    with store.driver.session(database=store._config.database) as session:
        return [dict(record) for record in session.run(query)]


def main() -> int:
    store = GraphStore(MemoryConfig().neo4j)
    try:
        print("=== Meditation Graph Shape Inspection ===")

        label_rows = run_query(store, "CALL db.labels() YIELD label RETURN label ORDER BY label")
        print("\n--- Labels ---")
        for row in label_rows:
            print(row["label"])

        rel_rows = run_query(store, "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")
        print("\n--- Relationship Types ---")
        for row in rel_rows:
            print(row["relationshipType"])

        print("\n--- Non-Entity label counts ---")
        non_entity_counts = run_query(
            store,
            """
            MATCH (n)
            WHERE NONE(label IN labels(n) WHERE label = 'Entity')
            UNWIND labels(n) AS label
            RETURN label, count(*) AS count
            ORDER BY count DESC, label ASC
            """,
        )
        for row in non_entity_counts:
            print(f"{row['label']}\t{row['count']}")

        print("\n--- Sample non-Entity nodes ---")
        sample_nodes = run_query(
            store,
            """
            MATCH (n)
            WHERE NONE(label IN labels(n) WHERE label = 'Entity')
            RETURN labels(n) AS labels, properties(n) AS props
            LIMIT 20
            """,
        )
        for row in sample_nodes:
            props = row["props"]
            snippet = str(props)[:200]
            print(f"{row['labels']}\t{snippet}")

        print("\n--- Non-Entity -> Entity edges ---")
        edge_rows = run_query(
            store,
            """
            MATCH (n)-[r]->(e:Entity)
            WHERE NONE(label IN labels(n) WHERE label = 'Entity')
            RETURN labels(n) AS labels, type(r) AS rel_type, count(*) AS count
            ORDER BY count DESC, rel_type ASC
            LIMIT 50
            """,
        )
        for row in edge_rows:
            print(f"{row['labels']}\t{row['rel_type']}\t{row['count']}")
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
