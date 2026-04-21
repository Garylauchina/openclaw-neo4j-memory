#!/usr/bin/env python3
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from meditation_memory.config import MemoryConfig
from meditation_memory.graph_store import GraphStore

GENERIC_KEYWORDS = [
    "总结", "指标", "管理", "执行", "效果", "内容", "状态", "数据", "信息", "问题",
    "功能", "策略", "节点", "实体", "报告", "分析", "结果", "参数", "机制", "结构",
]


def is_generic_low_information(name: str, entity_type: str) -> bool:
    name = (name or "").strip()
    entity_type = (entity_type or "").strip()
    if entity_type != "concept":
        return False
    if len(name) > 4:
        return False
    return any(keyword in name for keyword in GENERIC_KEYWORDS)


def main():
    parser = argparse.ArgumentParser(description="Audit graph quality / low-information concept noise")
    parser.add_argument("--output", default="-")
    parser.add_argument("--top", type=int, default=80)
    args = parser.parse_args()

    cfg = MemoryConfig()
    store = GraphStore(cfg.neo4j)

    with store.driver.session(database=store._config.database) as session:
        active_nodes = session.run("MATCH (e:Entity) WHERE NOT e:Archived RETURN count(e) AS c").single()["c"]
        short_nodes = session.run("MATCH (e:Entity) WHERE NOT e:Archived AND size(e.name) <= 4 RETURN count(e) AS c").single()["c"]
        short_concepts = session.run("MATCH (e:Entity) WHERE NOT e:Archived AND e.entity_type = 'concept' AND size(e.name) <= 4 RETURN count(e) AS c").single()["c"]
        relation_types = [r["rel"] for r in session.run("MATCH ()-[r:RELATES_TO]->() RETURN r.relation_type AS rel") if r.get("rel")]

    short_rows = store.get_short_name_entities(max_name_length=4, skip_recent_seconds=0)

    generic_candidates = []
    for row in short_rows:
        if is_generic_low_information(row.get("name"), row.get("entity_type")):
            generic_candidates.append({
                "name": row.get("name"),
                "entity_type": row.get("entity_type"),
                "mention_count": row.get("mention_count") or 0,
                "neighbor_names": row.get("neighbor_names") or [],
                "generic_keyword_hits": [k for k in GENERIC_KEYWORDS if k in (row.get("name") or "")],
            })

    generic_candidates.sort(key=lambda r: (-(r["mention_count"] or 0), r["name"] or ""))
    relation_counter = Counter(relation_types)

    report = {
        "active_nodes": active_nodes,
        "short_nodes": short_nodes,
        "short_concepts": short_concepts,
        "short_node_ratio": round(short_nodes / active_nodes, 4) if active_nodes else 0.0,
        "short_concept_ratio": round(short_concepts / active_nodes, 4) if active_nodes else 0.0,
        "generic_low_information_concepts": len(generic_candidates),
        "generic_low_information_ratio": round(len(generic_candidates) / active_nodes, 4) if active_nodes else 0.0,
        "entity_type_distribution_within_short_nodes": dict(Counter((r.get("entity_type") or "unknown") for r in short_rows)),
        "top_relation_types": relation_counter.most_common(20),
        "top_generic_candidates": generic_candidates[: args.top],
    }

    if args.output == "-":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(args.output)


if __name__ == "__main__":
    main()
