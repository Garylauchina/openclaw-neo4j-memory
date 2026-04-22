#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore


def plausible_partial_truncation(short_name: str, full_name: str) -> bool:
    short_name = (short_name or "").strip()
    full_name = (full_name or "").strip()
    if not short_name or not full_name or short_name == full_name:
        return False
    if len(full_name) - len(short_name) > 2:
        return False
    if len(short_name) < 2 or len(full_name) < 3:
        return False
    return full_name.endswith(short_name) or full_name.startswith(short_name)


def main():
    parser = argparse.ArgumentParser(description="Audit partial semantic truncation candidates")
    parser.add_argument("--max-name-length", type=int, default=8)
    parser.add_argument("--output", default="-")
    parser.add_argument("--top", type=int, default=80)
    args = parser.parse_args()

    cfg = MemoryConfig()
    store = GraphStore(cfg.neo4j)

    with store.driver.session(database=store._config.database) as session:
        rows = [dict(r) for r in session.run(
            """
            MATCH (e:Entity)
            WHERE NOT e:Archived
              AND size(e.name) <= $max_len
            RETURN e.name AS name,
                   e.entity_type AS entity_type,
                   e.mention_count AS mention_count
            """,
            max_len=args.max_name_length,
        )]

    names = [r.get("name") for r in rows if r.get("name")]
    by_name = {r["name"]: r for r in rows if r.get("name")}

    candidates = []
    for short_name in names:
        overlaps = []
        for other_name in names:
            if plausible_partial_truncation(short_name, other_name):
                overlaps.append(other_name)
        if overlaps:
            candidates.append({
                "name": short_name,
                "entity_type": by_name[short_name].get("entity_type"),
                "mention_count": by_name[short_name].get("mention_count") or 0,
                "possible_full_forms": sorted(set(overlaps))[:10],
            })

    candidates.sort(key=lambda x: (-(x["mention_count"] or 0), x["name"]))
    report = {
        "max_name_length": args.max_name_length,
        "candidate_count": len(candidates),
        "top_candidates": candidates[: args.top],
    }

    if args.output == "-":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(args.output)


if __name__ == "__main__":
    main()
