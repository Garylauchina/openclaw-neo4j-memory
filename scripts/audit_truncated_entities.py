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


def classify_candidate(name: str, entity_type: str, mention_count: int, neighbors: list[str]) -> str:
    name = (name or "").strip()
    entity_type = (entity_type or "").strip()
    neighbors = neighbors or []

    if not name:
        return "empty_name"

    if len(name) <= 1:
        return "likely_truncated"

    generic_terms = {
        "消息总结", "用户发送", "关键指标", "积压节点", "进程管理", "任务调度", "平台运行",
        "技术细节", "技术要点", "知识图谱", "通货膨胀", "版本信息", "功能测试", "默认值",
        "初始化", "核心实体", "主要实体", "结构", "属性", "效果", "明白", "张三",
    }
    if name in generic_terms:
        return "likely_valid_short_name"

    if entity_type in {"person", "place", "organization", "technology"} and len(name) <= 4 and mention_count >= 2:
        return "needs_manual_review"

    if len(name) <= 2 and not neighbors:
        return "likely_truncated"

    if len(name) <= 4 and mention_count <= 1 and not neighbors:
        return "likely_truncated"

    return "needs_manual_review"


def main():
    parser = argparse.ArgumentParser(description="Audit short-name/truncated entity candidates")
    parser.add_argument("--max-name-length", type=int, default=4)
    parser.add_argument("--skip-recent-seconds", type=int, default=300)
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--output", default="-")
    args = parser.parse_args()

    cfg = MemoryConfig()
    store = GraphStore(cfg.neo4j)
    rows = store.get_short_name_entities(
        max_name_length=args.max_name_length,
        skip_recent_seconds=args.skip_recent_seconds,
    )

    normalized = []
    for row in rows:
        item = {
            "name": row.get("name"),
            "entity_type": row.get("entity_type"),
            "mention_count": row.get("mention_count") or 0,
            "neighbor_names": row.get("neighbor_names") or [],
            "element_id": row.get("element_id"),
        }
        item["classification"] = classify_candidate(
            item["name"], item["entity_type"], item["mention_count"], item["neighbor_names"]
        )
        normalized.append(item)

    normalized.sort(key=lambda r: (-(r["mention_count"] or 0), r["name"] or ""))

    report = {
        "max_name_length": args.max_name_length,
        "skip_recent_seconds": args.skip_recent_seconds,
        "candidate_count": len(normalized),
        "entity_type_distribution": dict(Counter((r.get("entity_type") or "unknown") for r in normalized)),
        "classification_distribution": dict(Counter(r["classification"] for r in normalized)),
        "top_candidates": normalized[: args.top],
    }

    if args.output == "-":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(args.output)


if __name__ == "__main__":
    main()
