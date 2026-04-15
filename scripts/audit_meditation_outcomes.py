#!/usr/bin/env python3
"""Audit meditation outcomes for a source-scoped probe.

This is a read-only probe helper. It compares:
- source-scoped imported entities
- source-scoped relations
- global meta-knowledge nodes mentioning those imported entities

Goal: provide a first bridge between online ingest retention and meditation-side outcomes.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore


def fetch_source_entities(store: GraphStore, source_tag: str, import_batch: str, limit: int) -> List[Dict[str, Any]]:
    return store.get_entities_by_source(source_tag=source_tag, import_batch=import_batch, limit=limit)


def fetch_source_relations(store: GraphStore, source_tag: str, import_batch: str, limit: int) -> List[Dict[str, Any]]:
    query = """
    MATCH (s:Entity)-[r]->(t:Entity)
    WHERE type(r) <> 'SEEN_IN'
      AND coalesce(r.source_tag, '') = $source_tag
      AND coalesce(r.import_batch, '') = $import_batch
    RETURN s.name AS source, type(r) AS relation_type, t.name AS target
    LIMIT $limit
    """
    with store.driver.session(database=store._config.database) as session:
        return [dict(record) for record in session.run(query, source_tag=source_tag, import_batch=import_batch, limit=limit)]


def fetch_related_meta_knowledge(store: GraphStore, entity_names: List[str], limit: int) -> List[Dict[str, Any]]:
    if not entity_names:
        return []
    query = """
    MATCH (m:MetaKnowledge)-[:ABOUT|RELATES_TO|DERIVED_FROM*1..2]-(e:Entity)
    WHERE e.name IN $entity_names AND NOT m:Archived
    RETURN m.id AS id,
           coalesce(m.name, m.title, m.content, m.description, '') AS content,
           count(DISTINCT e) AS matched_entities
    ORDER BY matched_entities DESC, content ASC
    LIMIT $limit
    """
    with store.driver.session(database=store._config.database) as session:
        return [dict(record) for record in session.run(query, entity_names=entity_names, limit=limit)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit meditation outcomes for a source-scoped probe")
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--import-batch", required=True)
    parser.add_argument("--entity-limit", type=int, default=100)
    parser.add_argument("--relation-limit", type=int, default=100)
    parser.add_argument("--meta-limit", type=int, default=50)
    args = parser.parse_args()

    store = GraphStore(MemoryConfig().neo4j)
    try:
        entities = fetch_source_entities(store, args.source_tag, args.import_batch, args.entity_limit)
        relations = fetch_source_relations(store, args.source_tag, args.import_batch, args.relation_limit)
        entity_names = [row["name"] for row in entities]
        meta_nodes = fetch_related_meta_knowledge(store, entity_names, args.meta_limit)
    finally:
        store.close()

    print("=== Meditation Outcome Audit ===")
    print(f"source_tag={args.source_tag}")
    print(f"import_batch={args.import_batch}")
    print(f"source_entities={len(entities)}")
    print(f"source_relations={len(relations)}")
    print(f"matched_meta_knowledge={len(meta_nodes)}")

    print("\n--- Sample source entities ---")
    for row in entities[:20]:
        print(f"{row['name']}\t{row['entity_type']}\tmentions={row.get('mention_count', 0)}")

    print("\n--- Sample source relations ---")
    for row in relations[:20]:
        print(f"{row['source']}\t[{row['relation_type']}]\t{row['target']}")

    print("\n--- Related meta knowledge ---")
    for row in meta_nodes[:20]:
        content = (row.get('content') or '').replace('\n', ' ')[:160]
        print(f"matched={row['matched_entities']}\t{content}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
