#!/usr/bin/env python3
"""
Neo4j 截断碎片实体清理 — 纯规则过滤版（秒级完成，无需 LLM）

运行方式：
    python3 cleanup_truncated_entities_quick.py --dry-run   # 预览
    python3 cleanup_truncated_entities_quick.py --execute   # 执行
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List

workspace_root = os.path.dirname(__file__)
for p in [os.path.join(workspace_root, "plugins", "neo4j-memory")]:
    if os.path.isfile(os.path.join(p, "meditation_memory", "graph_store.py")):
        sys.path.insert(0, p)
        break

from meditation_memory.graph_store import GraphStore
from meditation_memory.config import Neo4jConfig

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cleanup")

_BAD_START = (
    "的", "了", "在", "和", "是", "有", "被", "把", "从", "对",
    "让", "给", "与", "或", "而", "就", "都", "也", "还", "又",
    "很", "最", "更", "太", "不", "没", "要", "会", "能", "可",
)
_BAD_END = (
    "的", "了", "着", "过", "得", "地", "在", "和", "是",
    "有", "被", "把", "来", "去", "于", "从", "向", "对",
    "与", "或", "而", "就", "都", "也", "还", "又", "则",
    "时", "中", "后", "前", "间", "内", "外",
)
_TRUNC = [
    "模和", "规模和", "模提", "件记", "到长", "析构建",
    "储规模", "并分析", "和提", "构建提", "系统作",
    "记忆系", "提取模", "提示词命", "分析构建", "件记忆",
    "到长期", "模和提示", "和提示词",
]


def is_truncated(name: str) -> bool:
    if re.match(r"^[\d\s.,]+$", name):
        return True
    if re.match(r"^[a-zA-Z]+$", name) and len(name) <= 2:
        return True
    if len(name) == 1 and "\u4e00" <= name <= "\u9fff":
        return True
    if any(name.startswith(w) for w in _BAD_START):
        return True
    if any(name.endswith(w) for w in _BAD_END):
        return True
    if any(sub in name for sub in _TRUNC):
        return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.dry_run and not args.execute:
        print("指定 --dry-run 或 --execute"); sys.exit(1)

    cfg = Neo4jConfig(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD, database=NEO4J_DATABASE)
    store = GraphStore(cfg)
    if not store.verify_connectivity():
        logger.error("无法连接 Neo4j"); sys.exit(1)

    stats = store.get_stats()
    total = stats.get("nodes", 0) if isinstance(stats, dict) else stats

    invalid: List[Dict[str, Any]] = []
    valid_count = 0
    type_count: Dict[str, int] = {}

    with store.driver.session() as session:
        records = session.run(
            "MATCH (n) WHERE n.name IS NOT NULL AND n.entity_type IS NOT NULL "
            "RETURN n.name AS name, n.entity_type AS type, elementId(n) AS eid "
            "ORDER BY n.name"
        )
        for r in records:
            name, etype = r["name"], r["type"]
            type_count[etype] = type_count.get(etype, 0) + 1
            if is_truncated(name):
                invalid.append({"name": name, "type": etype, "eid": r["eid"]})
            else:
                valid_count += 1

    print("=" * 70)
    print(f"  截断碎片实体清理 — 规则过滤")
    print(f"  实体总数: {valid_count + len(invalid)}")
    print(f"  ✅ 有效: {valid_count}")
    print(f"  ❌ 截断碎片: {len(invalid)}")
    print(f"  类型分布: {json.dumps(type_count, ensure_ascii=False)}")
    print("=" * 70)

    if invalid:
        print(f"\n需要删除的实体 (前 50/{len(invalid)}):")
        for i, e in enumerate(invalid[:50]):
            print(f"  {i+1:3d}. {e['name']:55s} ({e['type']})")
        if len(invalid) > 50:
            print(f"  ... 还有 {len(invalid) - 50} 个")

        with open("/tmp/truncated_entities_full.json", "w") as f:
            json.dump(invalid, f, ensure_ascii=False, indent=2)
        print(f"\n完整列表: /tmp/truncated_entities_full.json")

    if args.execute:
        print(f"\n开始删除 {len(invalid)} 个实体...")
        deleted = failed = 0
        for e in invalid:
            try:
                with store.driver.session() as session:
                    session.run("MATCH (n) WHERE elementId(n) = $eid DETACH DELETE n", eid=e["eid"])
                deleted += 1
            except Exception as ex:
                failed += 1
                logger.error("删除失败 '%s': %s", e["name"], ex)
            if (deleted + failed) % 100 == 0:
                print(f"  进度: {deleted + failed}/{len(invalid)}")
        new_stats = store.get_stats()
        new_total = new_stats.get("nodes", 0) if isinstance(new_stats, dict) else new_stats
        print(f"\n✅ 删除 {deleted} | 失败 {failed}")
        print(f"   节点: {total} → {new_total}")
    else:
        print(f"\n预览完成。加 --execute 执行删除。")

    store.close()


if __name__ == "__main__":
    main()
