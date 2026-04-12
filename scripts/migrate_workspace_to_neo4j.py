#!/usr/bin/env python3
"""
OpenClaw 工作区 → Neo4j 全量迁移工具 (Issue #70 Phase 2)

将 OpenClaw 工作区中的 Markdown 文件迁移到 Neo4j 图数据库，
构建完整的 Agent 知识图谱。

用法:
    # 预览模式
    python scripts/migrate_workspace_to_neo4j.py \
        --workspace ~/.openclaw/workspace --dry-run

    # 正式迁移
    python scripts/migrate_workspace_to_neo4j.py \
        --workspace ~/.openclaw/workspace

    # 跳过特定文件
    python scripts/migrate_workspace_to_neo4j.py \
        --workspace ~/.openclaw/workspace --skip-files BOOTSTRAP.md

环境变量:
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from neo4j import GraphDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("migrate_workspace")

# ========== 文件 → 节点类型映射 ==========

FILE_TYPE_MAP = {
    "SOUL.md": ("Identity", "has_trait"),
    "IDENTITY.md": ("Identity", "has_property"),
    "USER.md": ("User", "has_context"),
    "AGENTS.md": ("AgentProfile", "has_rule"),
    "TOOLS.md": ("ToolConfig", "has_config"),
    "HEARTBEAT.md": ("Schedule", "has_task"),
    "BOOTSTRAP.md": ("Bootstrap", "has_step"),
    "MEMORY.md": ("Belief", "has_detail"),
}

# 工作区根目录默认文件列表
ROOT_MD_FILES = list(FILE_TYPE_MAP.keys())


@dataclass
class MigrateStats:
    total_files: int = 0
    total_nodes: int = 0
    total_relations: int = 0
    skipped: int = 0
    errors: int = 0


def parse_markdown_sections(content: str) -> list[dict]:
    """解析 Markdown 内容为结构化段落

    返回:
        [{"title": str, "body": str, "level": int}, ...]
    """
    sections = []
    # 匹配 ## 或 ### 标题
    pattern = re.compile(r'^(#{2,4})\s+(.+)$', re.MULTILINE)
    matches = list(pattern.finditer(content))

    for i, m in enumerate(matches):
        title = m.group(2).strip()
        level = len(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[start:end].strip()
        sections.append({"title": title, "body": body, "level": level})

    return sections


def extract_list_items(text: str) -> list[str]:
    """从文本中提取列表项"""
    items = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith(("- ", "* ", "+ ", "• ")) or re.match(r"^\d+[\.\)]\s+", line):
            item = re.sub(r"^[-*+•]|\d+[\.\)]\s*", "", line).strip()
            if item and len(item) > 2:
                items.append(item)
    return items


def extract_code_blocks(text: str) -> list[dict]:
    """提取代码块"""
    blocks = []
    pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    for m in pattern.finditer(text):
        lang = m.group(1) or "text"
        code = m.group(2).strip()
        blocks.append({"lang": lang, "code": code})
    return blocks


def content_hash(text: str) -> str:
    """内容哈希（用于去重）"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build_workspace_index(workspace: str) -> list[Path]:
    """扫描工作区，返回待迁移的 .md 文件列表"""
    ws = Path(workspace).resolve()
    files = []

    # 1. 根目录下的已知文件
    for fname in ROOT_MD_FILES:
        fpath = ws / fname
        if fpath.exists():
            files.append(fpath)

    # 2. 其他根目录 .md 文件（不在 FILE_TYPE_MAP 中的）
    for fpath in sorted(ws.glob("*.md")):
        if fpath not in files and fpath.name != "EVOLUTION.md":
            files.append(fpath)

    # 3. memory/ 目录下的 .md 文件
    memory_dir = ws / "memory"
    if memory_dir.exists():
        for fpath in sorted(memory_dir.glob("*.md")):
            files.append(fpath)

    return files


def parse_file_for_migration(fpath: Path, workspace: str) -> dict:
    """将单个 Markdown 文件解析为节点/关系数据"""
    content = fpath.read_text(encoding="utf-8")
    rel_path = str(fpath.relative_to(workspace))
    fname = fpath.name

    # 确定节点类型
    if fname in FILE_TYPE_MAP:
        node_type, default_rel = FILE_TYPE_MAP[fname]
    elif rel_path.startswith("memory/"):
        node_type = "DailyMemory"
        default_rel = "contains"
    else:
        node_type = "Document"
        default_rel = "has_section"

    sections = parse_markdown_sections(content)
    main_hash = content_hash(content)

    result = {
        "file": rel_path,
        "node_type": node_type,
        "default_rel": default_rel,
        "main_node": {
            "name": fpath.stem,
            "source_path": rel_path,
            "content_hash": main_hash,
            "char_count": len(content),
            "node_type": node_type,
        },
        "sections": [],
        "list_items": [],
        "code_blocks": [],
        "node_count": 1,  # main node
        "rel_count": 0,
    }

    for sec in sections:
        sec_hash = content_hash(sec["body"])
        result["sections"].append({
            "title": sec["title"],
            "body_preview": sec["body"][:200],
            "content_hash": sec_hash,
            "level": sec["level"],
        })
        result["node_count"] += 1
        result["rel_count"] += 1

        # 列表项 → 详情节点
        items = extract_list_items(sec["body"])
        for item in items[:10]:  # 每个 section 最多 10 个
            result["list_items"].append({
                "section": sec["title"],
                "text": item,
            })
            result["node_count"] += 1
            result["rel_count"] += 1

        # 代码块
        blocks = extract_code_blocks(sec["body"])
        for blk in blocks:
            result["code_blocks"].append(blk)
            result["node_count"] += 1
            result["rel_count"] += 1

    return result


def ingest_to_neo4j(driver, parsed: list[dict], dry_run: bool) -> MigrateStats:
    """将解析结果批量写入 Neo4j"""
    stats = MigrateStats()
    stats.total_files = len(parsed)

    # 收集已存在的 content_hash（去重）
    existing_hashes: set[str] = set()
    with driver.session() as session:
        r = session.run("MATCH (n) RETURN n.content_hash AS h")
        for rec in r:
            if rec["h"]:
                existing_hashes.add(rec["h"])

    if dry_run:
        log.info("[预览] 已有 %d 个 content_hash 在图谱中", len(existing_hashes))

    for p in parsed:
        main = p["main_node"]
        if main["content_hash"] in existing_hashes:
            log.info("  ⏭ %s (已存在，跳过)", p["file"])
            stats.skipped += 1
            continue

        if dry_run:
            log.info(
                "  📄 %s → %s 节点, %d sections, %d list items, %d code blocks",
                p["file"], p["node_type"],
                len(p["sections"]), len(p["list_items"]), len(p["code_blocks"])
            )
            stats.total_nodes += p["node_count"]
            stats.total_relations += p["rel_count"]
            continue

        # 写入主节点
        with driver.session() as session:
            # 主节点
            props = dict(main)
            label = p["node_type"]
            set_parts = ", ".join(f"n.`{k}` = $v_{k}" for k in props)
            cypher = f"CREATE (n:{label}) SET {set_parts}"
            params = {f"v_{k}": v for k, v in props.items()}
            session.run(cypher, **params)

            # Section 子节点
            for sec in p["sections"]:
                sec_props = {
                    "title": sec["title"],
                    "body_preview": sec["body_preview"],
                    "content_hash": sec["content_hash"],
                    "level": sec["level"],
                    "source_path": p["file"],
                }
                sec_set = ", ".join(f"s.`{k}` = $s_{k}" for k in sec_props)
                sec_cypher = (
                    f"MATCH (n:{label} {{content_hash: $main_hash}}) "
                    f"WITH n LIMIT 1 "
                    f"CREATE (n)-[r:{p['default_rel']}]->(s:Section) "
                    f"SET {sec_set}"
                )
                session.run(sec_cypher, main_hash=main["content_hash"],
                            **{f"s_{k}": v for k, v in sec_props.items()})
                stats.total_relations += 1

            # List item 子节点
            for item in p["list_items"]:
                item_props = {
                    "text": item["text"],
                    "section": item["section"],
                    "source_path": p["file"],
                }
                item_set = ", ".join(f"d.`{k}` = $d_{k}" for k in item_props)
                item_cypher = (
                    f"MATCH (n:{label} {{content_hash: $main_hash}}) "
                    f"WITH n LIMIT 1 "
                    f"CREATE (n)-[r:has_detail]->(d:Detail) "
                    f"SET {item_set}"
                )
                session.run(item_cypher, main_hash=main["content_hash"],
                            **{f"d_{k}": v for k, v in item_props.items()})
                stats.total_relations += 1

            # Code block 子节点
            for blk in p["code_blocks"]:
                blk_props = {
                    "lang": blk["lang"],
                    "code": blk["code"],
                    "source_path": p["file"],
                }
                blk_set = ", ".join(f"c.`{k}` = $c_{k}" for k in blk_props)
                blk_cypher = (
                    f"MATCH (n:{label} {{content_hash: $main_hash}}) "
                    f"WITH n LIMIT 1 "
                    f"CREATE (n)-[r:has_code]->(c:CodeBlock) "
                    f"SET {blk_set}"
                )
                session.run(blk_cypher, main_hash=main["content_hash"],
                            **{f"c_{k}": v for k, v in blk_props.items()})
                stats.total_relations += 1

        stats.total_nodes += p["node_count"]

    return stats


def main():
    parser = argparse.ArgumentParser(description="OpenClaw 工作区 → Neo4j 迁移工具")
    parser.add_argument("--workspace", default=os.path.expanduser("~/.openclaw/workspace"),
                        help="OpenClaw 工作区路径")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入")
    parser.add_argument("--skip-files", nargs="*", default=[],
                        help="跳过的文件名（如 BOOTSTRAP.md）")
    args = parser.parse_args()

    workspace = os.path.abspath(args.workspace)
    skip_files = set(args.skip_files)

    log.info("=" * 60)
    log.info("🧠 OpenClaw 工作区 → Neo4j 迁移工具")
    log.info("=" * 60)
    log.info("  工作区: %s", workspace)
    log.info("  Neo4j:  %s", os.environ.get("NEO4J_URI", "bolt://localhost:7687"))
    log.info("  预览:   %s", "是" if args.dry_run else "否")
    log.info("")

    # 扫描文件
    files = build_workspace_index(workspace)
    files = [f for f in files if f.name not in skip_files]
    log.info("📁 找到 %d 个文件待迁移", len(files))

    # 解析
    log.info("")
    log.info("=" * 60)
    log.info("步骤 1/2：解析工作区文件")
    log.info("=" * 60)

    parsed = []
    for fpath in files:
        p = parse_file_for_migration(fpath, workspace)
        parsed.append(p)
        log.info(
            "  📄 %s → %s 节点, %d sections, %d list items",
            fpath.name, p["node_type"],
            len(p["sections"]), len(p["list_items"])
        )

    # 连接 Neo4j
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")

    log.info("")
    log.info("=" * 60)
    log.info("步骤 2/2：%s Neo4j", "预览导入" if args.dry_run else "导入")
    log.info("=" * 60)

    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        log.info("✅ Neo4j 连接成功")

        # 创建 content_hash 唯一约束（防止主节点重复）
        with driver.session() as session:
            session.run(
                "CREATE CONSTRAINT unique_content_hash IF NOT EXISTS "
                "FOR (n) REQUIRE n.content_hash IS UNIQUE"
            )
            log.info("✅ 唯一约束 unique_content_hash 已确保")

        stats = ingest_to_neo4j(driver, parsed, dry_run=args.dry_run)

        log.info("")
        log.info("=" * 60)
        log.info("📊 统计")
        log.info("=" * 60)
        log.info("📁 扫描文件: %d", stats.total_files)
        log.info("🔍 解析节点: %d", stats.total_nodes)
        log.info("🔗 解析关系: %d", stats.total_relations)
        log.info("⏭ 跳过重复: %d", stats.skipped)

        if not args.dry_run:
            with driver.session() as session:
                r = session.run("MATCH (n) RETURN count(n) AS c")
                total = r.single()["c"]
                log.info("📈 图谱总节点: %d", total)

        log.info("")
        log.info("✅ 完成！")

    except Exception as e:
        log.error("❌ 迁移失败: %s", e)
        sys.exit(1)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
