#!/usr/bin/env python3
"""
工作区记忆导入工具 — Issue #58 Phase 1

将 OpenClaw 工作区 Markdown 文件导入 Neo4j 图谱，
让新部署用户的记忆系统从"空白"到"可用"只需一步操作。

用法:
    # 预览模式
    python scripts/workspace_import.py --workspace ~/.openclaw/workspace --dry-run

    # 正式导入
    python scripts/workspace_import.py --workspace ~/.openclaw/workspace

    # 导入并触发冥思
    python scripts/workspace_import.py --workspace ~/.openclaw/workspace \
        --api-url http://127.0.0.1:18900

环境变量:
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
    OPENAI_API_KEY, OPENAI_BASE_URL, LLM_MODEL
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meditation_memory.config import MemoryConfig, Neo4jConfig, LLMConfig
from meditation_memory.graph_store import GraphStore
from meditation_memory.entity_extractor import EntityExtractor

logger = logging.getLogger("workspace_import")

# ============================================================
# 配置
# ============================================================

PRIORITY_FILES = [
    "USER.md",
    "AGENTS.md",
    "TOOLS.md",
    "IDENTITY.md",
    "SOUL.md",
    "MEMORY.md",
    "HEARTBEAT.md",
    "BOOTSTRAP.md",
]
MEMORY_DIR = "memory"
MAX_FILE_CHARS = 8000
LLM_COOLDOWN = 1.0


# ============================================================
# 数据结构
# ============================================================

@dataclass
class FileInfo:
    filename: str
    filepath: str
    content: str
    char_count: int


@dataclass
class ImportStats:
    files_scanned: int = 0
    total_chars: int = 0
    entities_extracted: int = 0
    relations_extracted: int = 0
    entities_written: int = 0
    relations_written: int = 0
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"📁 扫描文件: {self.files_scanned}",
            f"📝 总字符数: {self.total_chars:,}",
            f"🔍 抽取实体: {self.entities_extracted}",
            f"🔗 抽取关系: {self.relations_extracted}",
            f"✅ 写入实体: {self.entities_written}",
            f"✅ 写入关系: {self.relations_written}",
        ]
        if self.errors:
            lines.append(f"⚠️  错误: {len(self.errors)}")
            for e in self.errors[:5]:
                lines.append(f"   - {e}")
        return "\n".join(lines)


# ============================================================
# 步骤 1：环境检测
# ============================================================

def check_environment(
    neo4j_cfg: Neo4jConfig,
    workspace_path: str,
    api_url: Optional[str] = None,
    llm_cfg: Optional[LLMConfig] = None,
) -> Dict[str, dict]:
    results = {}

    # Neo4j
    try:
        store = GraphStore(neo4j_cfg)
        ok = store.verify_connectivity()
        store.close()
        results["neo4j"] = {"ok": ok, "msg": neo4j_cfg.uri if ok else "连接失败"}
    except Exception as e:
        results["neo4j"] = {"ok": False, "msg": str(e)}

    # Memory API
    if api_url:
        try:
            import httpx
            r = httpx.get(f"{api_url}/health", timeout=5)
            d = r.json()
            results["api"] = {"ok": d.get("status") == "ok", "msg": f"{api_url} v{d.get('version','?')}"}
        except Exception as e:
            results["api"] = {"ok": False, "msg": str(e)}

    # Workspace
    wp = Path(workspace_path).expanduser()
    if wp.is_dir():
        fns = list(wp.glob("*.md"))
        results["workspace"] = {"ok": len(fns) > 0, "msg": f"{wp} ({len(fns)} 个 .md)"}
    else:
        results["workspace"] = {"ok": False, "msg": f"不存在: {wp}"}

    # LLM
    if llm_cfg and llm_cfg.api_key:
        results["llm"] = {"ok": True, "msg": llm_cfg.model}
    else:
        results["llm"] = {"ok": False, "msg": "未配置 API Key，将使用规则模式"}

    return results


# ============================================================
# 步骤 2：读取工作区文件
# ============================================================

def scan_workspace(workspace_path: str) -> List[FileInfo]:
    wp = Path(workspace_path).expanduser().resolve()
    files: List[FileInfo] = []
    seen: set = set()

    def add(fp: Path):
        if not fp.is_file() or fp.name in seen:
            return
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return
        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS] + "\n...（已截断）"
        rel = str(fp.relative_to(wp))
        files.append(FileInfo(filename=rel, filepath=str(fp), content=content, char_count=len(content)))
        seen.add(fp.name)

    for n in PRIORITY_FILES:
        add(wp / n)
    md = wp / MEMORY_DIR
    if md.is_dir():
        for f in sorted(md.glob("*.md")):
            add(f)
    for f in sorted(wp.glob("*.md")):
        add(f)
    return files


# ============================================================
# 步骤 3：实体抽取 & 步骤 4：导入
# ============================================================

def import_workspace(
    workspace_path: str,
    store: GraphStore,
    extractor: EntityExtractor,
    api_url: Optional[str] = None,
    dry_run: bool = False,
    use_llm: bool = True,
    trigger_meditation: bool = True,
) -> ImportStats:
    stats = ImportStats()

    # --- 步骤 1：扫描 ---
    print("\n" + "=" * 50)
    print("步骤 1/4：扫描工作区文件")
    print("=" * 50)
    files = scan_workspace(workspace_path)
    stats.files_scanned = len(files)
    stats.total_chars = sum(f.char_count for f in files)
    print(f"  找到 {stats.files_scanned} 个文件，共 {stats.total_chars:,} 字符")
    for f in files:
        print(f"  📄 {f.filename} ({f.char_count:,} 字符)")
    if not files:
        print("  ⚠️  没有 Markdown 文件")
        return stats

    # --- 步骤 2：实体抽取 ---
    print("\n" + "=" * 50)
    print(f"步骤 2/4：实体抽取 ({'LLM' if use_llm else '规则'}模式)")
    print("=" * 50)

    all_entities = []
    all_relations = []
    seen_e = set()
    seen_r = set()

    for fi in files:
        try:
            result = extractor.extract(fi.content, use_llm=use_llm)
            stats.entities_extracted += len(result.entities)
            stats.relations_extracted += len(result.relations)

            for e in result.entities:
                e.properties["source_file"] = fi.filename
                e.properties["source_path"] = fi.filepath
                k = (e.name, e.entity_type)
                if k not in seen_e:
                    seen_e.add(k)
                    all_entities.append(e)
            for r in result.relations:
                r.properties["source_file"] = fi.filename
                k = (r.source, r.target, r.relation_type)
                if k not in seen_r:
                    seen_r.add(k)
                    all_relations.append(r)

            logger.info(f"  {fi.filename}: {len(result.entities)}E/{len(result.relations)}R ({result.extraction_mode})")
            if use_llm:
                time.sleep(LLM_COOLDOWN)
        except Exception as e:
            stats.errors.append(f"{fi.filename}: {e}")
            logger.error(f"  抽取失败 {fi.filename}: {e}")

    print(f"  共 {len(all_entities)} 个实体, {len(all_relations)} 个关系（去重后）")

    # --- 步骤 3：导入 Neo4j ---
    print("\n" + "=" * 50)
    print(f"步骤 3/4：导入 Neo4j {'[预览]' if dry_run else ''}")
    print("=" * 50)

    if dry_run:
        print("  预览模式，以下实体将被导入：")
        for e in all_entities[:20]:
            print(f"    • {e.name} ({e.entity_type}) [{e.properties.get('source_file','?')}]")
        if len(all_entities) > 20:
            print(f"    ... 还有 {len(all_entities)-20} 个实体")
        return stats

    if all_entities:
        stats.entities_written = store.upsert_entities(all_entities)
        print(f"  ✅ 写入 {stats.entities_written} 个实体")
    if all_relations:
        stats.relations_written = store.upsert_relations(all_relations)
        print(f"  ✅ 写入 {stats.relations_written} 个关系")

    # --- 步骤 4：触发冥思 ---
    if trigger_meditation and api_url:
        print("\n" + "=" * 50)
        print("步骤 4/4：触发冥思")
        print("=" * 50)
        try:
            import httpx
            r = httpx.post(f"{api_url}/meditation/trigger", json={"dry_run": False}, timeout=300)
            if r.status_code == 200:
                print(f"  ✅ 冥思触发成功")
            else:
                print(f"  ⚠️  HTTP {r.status_code}")
        except Exception as e:
            print(f"  ⚠️  {e}")
    elif trigger_meditation:
        print("\n  ⚠️  未指定 --api-url，跳过冥思")
        print("  手动触发: curl -X POST http://127.0.0.1:18900/meditation/trigger")

    return stats


# ============================================================
# 主程序
# ============================================================

def main():
    p = argparse.ArgumentParser(
        description="工作区记忆导入工具 — 将 OpenClaw 工作区文件导入 Neo4j 图谱",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python scripts/workspace_import.py --workspace ~/.openclaw/workspace --dry-run
  python scripts/workspace_import.py --workspace ~/.openclaw/workspace
  python scripts/workspace_import.py --workspace ~/.openclaw/workspace --no-llm
  python scripts/workspace_import.py --workspace ~/.openclaw/workspace --api-url http://127.0.0.1:18900
        """,
    )
    p.add_argument("--workspace", default="~/.openclaw/workspace")
    p.add_argument("--api-url", default=None, help="Memory API 地址（用于触发冥思）")
    p.add_argument("--dry-run", action="store_true", help="预览模式，不写入")
    p.add_argument("--no-llm", action="store_true", help="规则模式（不调用 LLM）")
    p.add_argument("--skip-meditation", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    neo4j_cfg = Neo4jConfig(
        uri=os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        user=os.environ.get("NEO4J_USER", "neo4j"),
        password=os.environ.get("NEO4J_PASSWORD", "password"),
        database=os.environ.get("NEO4J_DATABASE", "neo4j"),
    )
    llm_cfg = LLMConfig()
    api_url = args.api_url or "http://127.0.0.1:18900"

    print("=" * 50)
    print("🧠 OpenClaw 工作区记忆导入工具")
    print("=" * 50)
    print(f"  工作区: {os.path.expanduser(args.workspace)}")
    print(f"  Neo4j:  {neo4j_cfg.uri}")
    print(f"  抽取:   {'LLM' if not args.no_llm else '规则'}")
    print(f"  预览:   {'是' if args.dry_run else '否'}")
    print("=" * 50)

    # 环境检测
    print("\n🔍 环境检测...")
    env = check_environment(
        neo4j_cfg, args.workspace,
        api_url=None if args.dry_run else api_url,
        llm_cfg=None if args.no_llm else llm_cfg,
    )
    for name, info in env.items():
        icon = "✅" if info["ok"] else "⚠️ "
        print(f"  {icon} {name}: {info['msg']}")

    if not env["neo4j"]["ok"]:
        print("\n❌ Neo4j 连接失败"); sys.exit(1)
    if not env["workspace"]["ok"]:
        print("\n❌ 工作区无 .md 文件"); sys.exit(1)

    use_llm = not args.no_llm and env.get("llm", {}).get("ok", False)

    store = GraphStore(neo4j_cfg)
    store.init_schema()
    extractor = EntityExtractor(llm_cfg)

    try:
        stats = import_workspace(
            args.workspace, store, extractor,
            api_url=api_url, dry_run=args.dry_run,
            use_llm=use_llm, trigger_meditation=not args.skip_meditation,
        )

        print("\n" + "=" * 50)
        print("📊 统计")
        print("=" * 50)
        print(stats.summary())

        if not args.dry_run:
            ds = store.get_stats()
            print(f"\n  📈 节点: {ds.get('node_count',0)}  关系: {ds.get('edge_count',0)}")

        print("\n✅ 完成！")
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断"); return 1
    except Exception as e:
        logger.error(f"导入失败: {e}", exc_info=True)
        print(f"\n❌ 导入失败: {e}"); return 1
    finally:
        store.close()


if __name__ == "__main__":
    sys.exit(main())
