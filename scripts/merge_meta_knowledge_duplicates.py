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


def load_duplicate_plan(store, limit, batch_size, include_meta_on_meta_only=True):
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
        rows = [dict(r) for r in session.run(base_query, entity_type="meta_knowledge", limit=limit)]

        by_eid = {
            row["eid"]: {
                "eid": row["eid"],
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
        for batch in chunked(eids, max(1, batch_size)):
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
        if include_meta_on_meta_only and not has_meta_targets:
            continue
        key = build_group_key(related_names)
        groups[key].append({
            "eid": row["eid"],
            "name": row.get("name"),
            "description": row.get("description") or "",
            "mention_count": row.get("mention_count") or 0,
            "created_at": row.get("created_at") or 0,
            "updated_at": row.get("updated_at") or 0,
            "related_count": row.get("related_count") or 0,
            "has_meta_targets": has_meta_targets,
            "related_names": list(key),
        })

    plans = []
    for key, items in groups.items():
        if len(items) < 2:
            continue
        primary = choose_primary(items)
        archives = [item for item in items if item["eid"] != primary["eid"]]
        if not archives:
            continue
        plans.append({
            "group_size": len(items),
            "related_count": len(key),
            "has_meta_targets": True,
            "group_key_sample": list(key)[:12],
            "primary": primary,
            "archive_candidates": archives,
        })

    plans.sort(key=lambda g: (-g["group_size"], -g["related_count"]))
    return rows, plans


def apply_plan(store, plans):
    rewire_outgoing = """
    MATCH (dup:Entity)-[r:RELATES_TO]->(target:Entity)
    WHERE elementId(dup) = $dup_eid AND NOT target:Archived
    MATCH (keep:Entity)
    WHERE elementId(keep) = $keep_eid
    MERGE (keep)-[nr:RELATES_TO {relation_type: r.relation_type}]->(target)
    ON CREATE SET nr.created_at = coalesce(r.created_at, timestamp()),
                  nr.updated_at = timestamp(),
                  nr.mention_count = coalesce(r.mention_count, 1),
                  nr.properties = coalesce(r.properties, "{}")
    ON MATCH SET nr.updated_at = timestamp(),
                 nr.mention_count = coalesce(nr.mention_count, 0) + coalesce(r.mention_count, 1)
    """

    rewire_incoming = """
    MATCH (source:Entity)-[r:RELATES_TO]->(dup:Entity)
    WHERE elementId(dup) = $dup_eid AND NOT source:Archived
    MATCH (keep:Entity)
    WHERE elementId(keep) = $keep_eid
    MERGE (source)-[nr:RELATES_TO {relation_type: r.relation_type}]->(keep)
    ON CREATE SET nr.created_at = coalesce(r.created_at, timestamp()),
                  nr.updated_at = timestamp(),
                  nr.mention_count = coalesce(r.mention_count, 1),
                  nr.properties = coalesce(r.properties, "{}")
    ON MATCH SET nr.updated_at = timestamp(),
                 nr.mention_count = coalesce(nr.mention_count, 0) + coalesce(r.mention_count, 1)
    """

    archive_query = """
    MATCH (dup:Entity)
    WHERE elementId(dup) = $dup_eid AND NOT dup:Archived
    SET dup:Archived,
        dup.archived_at = timestamp(),
        dup.archive_reason = $reason
    RETURN dup.name AS name
    """

    applied = []
    with store.driver.session(database=store._config.database) as session:
        for plan in plans:
            keep_eid = plan["primary"]["eid"]
            keep_name = plan["primary"]["name"]
            archived_names = []
            for dup in plan["archive_candidates"]:
                dup_eid = dup["eid"]
                session.run(rewire_outgoing, dup_eid=dup_eid, keep_eid=keep_eid)
                session.run(rewire_incoming, dup_eid=dup_eid, keep_eid=keep_eid)
                session.run(
                    archive_query,
                    dup_eid=dup_eid,
                    reason=f"meta_duplicate_merged_into:{keep_name}",
                )
                archived_names.append(dup["name"])
            applied.append({
                "primary": keep_name,
                "archived": archived_names,
                "group_size": plan["group_size"],
            })
    return applied


def main():
    parser = argparse.ArgumentParser(description="Dry-run or apply merge plan for duplicate meta_knowledge nodes")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    cfg = MemoryConfig()
    store = GraphStore(cfg.neo4j)

    rows, plans = load_duplicate_plan(store, args.limit, args.batch_size, include_meta_on_meta_only=True)

    report = {
        "mode": "apply" if args.apply else "dry_run",
        "scope": "meta_on_meta_exact_related_set_duplicates_only",
        "total_meta_nodes_scanned": len(rows),
        "batch_size": args.batch_size,
        "merge_groups": len(plans),
        "total_archive_candidates": sum(len(p["archive_candidates"]) for p in plans),
        "plans": [
            {
                "group_size": p["group_size"],
                "related_count": p["related_count"],
                "primary": {
                    "eid": p["primary"]["eid"],
                    "name": p["primary"]["name"],
                    "mention_count": p["primary"]["mention_count"],
                    "description": p["primary"]["description"][:200],
                },
                "archive_candidates": [
                    {
                        "eid": a["eid"],
                        "name": a["name"],
                        "mention_count": a["mention_count"],
                        "description": a["description"][:200],
                    }
                    for a in p["archive_candidates"]
                ],
                "group_key_sample": p["group_key_sample"],
            }
            for p in plans
        ],
    }

    if args.apply:
        report["applied"] = apply_plan(store, plans)

    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output == "-":
        print(output)
    else:
        Path(args.output).write_text(output)
        print(args.output)


if __name__ == "__main__":
    main()
