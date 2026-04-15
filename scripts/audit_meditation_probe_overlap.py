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
        q = """
        MATCH (n:Entity)
        WHERE coalesce(n.meditation_run_id, '') = $run_id
        RETURN n.name AS name,
               n.entity_type AS entity_type,
               coalesce(n.source_tag, '') AS source_tag,
               coalesce(n.import_batch, '') AS import_batch,
               coalesce(n.probe_overlap_count, 0) AS probe_overlap_count,
               coalesce(n.probe_entity_names, []) AS probe_entity_names
        ORDER BY probe_overlap_count DESC, name ASC
        LIMIT 50
        """
        with store.driver.session(database=store._config.database) as s:
            rows = [dict(x) for x in s.run(q, run_id=args.run_id)]
        print('=== Meditation Probe Overlap Audit ===')
        print(f'run_id={args.run_id}')
        print(f'nodes={len(rows)}')
        for row in rows:
            print(f"{row['name']}\t{row['entity_type']}\tprobe_overlap={row['probe_overlap_count']}\tsource_tag={row['source_tag']}\timport_batch={row['import_batch']}\tprobe_entities={row['probe_entity_names']}")
    finally:
        store.close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
