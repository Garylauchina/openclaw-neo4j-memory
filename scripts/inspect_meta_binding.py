#!/usr/bin/env python3
from __future__ import annotations
import argparse, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    args = p.parse_args()
    store = GraphStore(MemoryConfig().neo4j)
    try:
        q = """
        MATCH (n:Entity)
        WHERE coalesce(n.meditation_run_id, '') = $run_id
        RETURN n.name AS name,
               n.entity_type AS entity_type,
               n.description AS description,
               n.cluster_signature AS cluster_signature,
               n.meditation_run_id AS meditation_run_id,
               n.source_tag AS source_tag,
               n.import_batch AS import_batch,
               n.probe_overlap_count AS probe_overlap_count,
               n.probe_entity_names AS probe_entity_names,
               n.mention_count AS mention_count,
               n.updated_at AS updated_at
        LIMIT 20
        """
        with store.driver.session(database=store._config.database) as s:
            rows = [dict(x) for x in s.run(q, run_id=args.run_id)]
        print('=== Meta Binding Inspect ===')
        print(f'run_id={args.run_id}')
        for row in rows:
            print(row)
    finally:
        store.close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
