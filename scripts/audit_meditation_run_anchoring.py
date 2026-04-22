#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    args = p.parse_args()
    store = GraphStore(MemoryConfig().neo4j)
    try:
        q1 = """
        MATCH (n:Entity)
        WHERE coalesce(n.meditation_run_id, '') = $run_id
        RETURN n.name AS name, n.entity_type AS entity_type, coalesce(n.source_tag, '') AS source_tag, coalesce(n.import_batch, '') AS import_batch
        LIMIT 50
        """
        q2 = """
        MATCH (a:Entity)-[r:RELATES_TO]->(b:Entity)
        WHERE coalesce(r.meditation_run_id, '') = $run_id
        RETURN a.name AS source, r.relation_type AS relation_type, b.name AS target, coalesce(r.source_tag, '') AS source_tag, coalesce(r.import_batch, '') AS import_batch
        LIMIT 100
        """
        with store.driver.session(database=store._config.database) as s:
            nodes = [dict(x) for x in s.run(q1, run_id=args.run_id)]
            edges = [dict(x) for x in s.run(q2, run_id=args.run_id)]
        print('=== Meditation Run Anchoring Audit ===')
        print(f'run_id={args.run_id}')
        print(f'nodes={len(nodes)}')
        print(f'edges={len(edges)}')
        print('\n--- Nodes ---')
        for row in nodes[:20]:
            print(f"{row['name']}\t{row['entity_type']}\t{row['source_tag']}\t{row['import_batch']}")
        print('\n--- Edges ---')
        for row in edges[:40]:
            print(f"{row['source']}\t[{row['relation_type']}]\t{row['target']}\t{row['source_tag']}\t{row['import_batch']}")
    finally:
        store.close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
