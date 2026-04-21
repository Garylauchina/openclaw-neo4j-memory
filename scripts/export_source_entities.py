#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--source-tag', required=True)
    p.add_argument('--import-batch', required=True)
    p.add_argument('--limit', type=int, default=30)
    args = p.parse_args()
    store = GraphStore(MemoryConfig().neo4j)
    try:
        rows = store.get_entities_by_source(source_tag=args.source_tag, import_batch=args.import_batch, limit=args.limit)
        print(json.dumps([row['name'] for row in rows], ensure_ascii=False))
    finally:
        store.close()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
