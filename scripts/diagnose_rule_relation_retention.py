#!/usr/bin/env python3
"""Diagnose rules-path relation retention before/after ingest."""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path
from typing import List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meditation_memory.config import MemoryConfig
from meditation_memory.entity_extractor import EntityExtractor
from meditation_memory.graph_store import GraphStore


def chunk_text(text: str, chunk_chars: int) -> List[str]:
    text = text.strip()
    if not text:
        return []
    return [text[i:i + chunk_chars] for i in range(0, len(text), chunk_chars)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose rule-path relation retention")
    parser.add_argument("input_path", help="Input file to inspect")
    parser.add_argument("--chunk-chars", type=int, default=1200)
    parser.add_argument("--limit-chunks", type=int, default=5)
    args = parser.parse_args()

    text = Path(args.input_path).read_text(encoding="utf-8")
    chunks = chunk_text(text, args.chunk_chars)[: args.limit_chunks]

    extractor = EntityExtractor(MemoryConfig().llm)
    store = GraphStore(MemoryConfig().neo4j)
    try:
        print("=== Rule Relation Retention Diagnosis ===")
        print(f"input={args.input_path}")
        print(f"chunks_inspected={len(chunks)}")

        total_entities = 0
        total_relations = 0
        relation_types = Counter()

        for idx, chunk in enumerate(chunks, start=1):
            extraction = extractor.extract(chunk, use_llm=False)
            total_entities += len(extraction.entities)
            total_relations += len(extraction.relations)
            relation_types.update(rel.relation_type for rel in extraction.relations)
            print(f"\n--- chunk {idx} ---")
            print(f"entities={len(extraction.entities)} relations={len(extraction.relations)}")
            for rel in extraction.relations[:20]:
                print(f"  {rel.source} [{rel.relation_type}] {rel.target}")

        print("\n=== Aggregate ===")
        print(f"entities={total_entities}")
        print(f"relations={total_relations}")
        print(f"relation_types={dict(relation_types)}")
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
