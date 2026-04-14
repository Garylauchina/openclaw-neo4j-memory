#!/usr/bin/env python3
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore


def build_group_key(related_names):
    names = sorted({name.strip() for name in related_names if name and name.strip()})
    return tuple(names)


def choose_primary(items):
    def sort_key(item):
        return (
            -(item.get("related_count") or 0),
            -(item.get("mention_count") or 0),
            item.get("created_at") or 0,
            item.get("name") or "",
        )
    return sorted(items, key=sort_key)[0]


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def main():
    parser = argparse.ArgumentParser(description="Dry-run audit for duplicate meta_knowledge nodes")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--output", default="-")
    parser.add_argument("--include-meta-on-meta", action="store_true")
    args = parser.parse_args()

    cfg = MemoryConfig()
    store = GraphStore(cfg.neo4j)

    base_query = """
    MATCH (m:Entity {entity_type: $entity_type})
    WHERE NOT m:Archived
    RETURN elementId(m) AS eid,
           m.name AS name,
           m.description AS description,
           m.mention_count AS mention_count,
           m.created_at AS created_at,
           m.updated_at AS updated_at
    ORDER BY coalesce(m.updated_at, m.created_at, 0) DESC
    LIMIT $limit
    """

    links_query = """
    UNWIND $eids AS eid
    MATCH (m:Entity)
    WHERE elementId(m) = eid AND NOT m:Archived
    OPTIONAL MATCH (m)-[:RELATES_TO {relation_type: $rel_type}]->(e:Entity)
    WHERE NOT e:Archived
    RETURN elementId(m) AS eid,
           collect(DISTINCT {name: e.name, entity_type: e.entity_type}) AS related_entities,
           count(DISTINCT e) AS related_count
    """

    with store.driver.session(database=store._config.database) as session:
        rows = [dict(r) for r in session.run(base_query, entity_type="meta_knowledge", limit=args.limit)]

        by_eid = {
            row["eid"]: {
                "name": row.get("name"),
                "description": row.get("description") or "",
                "mention_count": row.get("mention_count") or 0,
                "created_at": row.get("created_at") or 0,
                "updated_at": row.get("updated_at") or 0,
                "related_entities": [],
                "related_count": 0,
            }
            for row in rows
        }

        eids = list(by_eid.keys())
        for batch in chunked(eids, max(1, args.batch_size)):
            for record in session.run(links_query, eids=batch, rel_type="SUMMARIZES"):
                item = by_eid.get(record["eid"])
                if item is None:
                    continue
                item["related_entities"] = record.get("related_entities") or []
                item["related_count"] = record.get("related_count") or 0

    groups = defaultdict(list)
    for row in by_eid.values():
        related_entities = row.get("related_entities") or []
        related_names = [e.get("name") for e in related_entities if e.get("name")]
        if not related_names:
            continue
        has_meta_targets = any((e.get("entity_type") == "meta_knowledge") for e in related_entities)
        if has_meta_targets and not args.include_meta_on_meta:
            continue
        key = build_group_key(related_names)
        groups[key].append({
            "name": row.get("name"),
            "description": row.get("description") or "",
            "mention_count": row.get("mention_count") or 0,
            "created_at": row.get("created_at") or 0,
            "updated_at": row.get("updated_at") or 0,
            "related_count": row.get("related_count") or 0,
            "has_meta_targets": has_meta_targets,
            "related_names": list(key),
        })

    duplicate_groups = []
    for key, items in groups.items():
        if len(items) < 2:
            continue
        primary = choose_primary(items)
        archives = [item for item in items if item["name"] != primary["name"]]
        duplicate_groups.append({
            "group_size": len(items),
            "related_count": len(key),
            "has_meta_targets": any(item["has_meta_targets"] for item in items),
            "group_key_sample": list(key)[:12],
            "primary": {
                "name": primary["name"],
                "mention_count": primary["mention_count"],
                "created_at": primary["created_at"],
                "updated_at": primary["updated_at"],
                "description": primary["description"][:200],
            },
            "archive_candidates": [
                {
                    "name": item["name"],
                    "mention_count": item["mention_count"],
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                    "description": item["description"][:200],
                }
                for item in archives
            ],
        })

    duplicate_groups.sort(key=lambda g: (g["has_meta_targets"], -g["group_size"], -g["related_count"]))

    report = {
        "mode": "dry_run_audit",
        "total_meta_nodes_scanned": len(rows),
        "batch_size": args.batch_size,
        "groups_with_exact_related_set_duplicates": len(duplicate_groups),
        "total_archive_candidates": sum(len(g["archive_candidates"]) for g in duplicate_groups),
        "excluded_meta_on_meta_groups": not args.include_meta_on_meta,
        "duplicate_groups": duplicate_groups,
    }

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(output)
    else:
        Path(args.output).write_text(output)
        print(args.output)


if __name__ == "__main__":
    main()
