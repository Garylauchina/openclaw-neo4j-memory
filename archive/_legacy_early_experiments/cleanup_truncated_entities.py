#!/usr/bin/env python3
"""
Neo4j 实体清理脚本（优化版）

清理图谱中的截断碎片实体（如"储规模和技术"、"并分析构建提"、"模和提示词命"）。
优化：批次大小 200，4 线程并发，使用 deepseek/deepseek-chat 付费模型。

运行方式：
    python3 cleanup_truncated_entities.py --dry-run    # 预览模式，不实际执行
    python3 cleanup_truncated_entities.py --execute    # 执行清理
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional

# --- 路径与导入 ---
workspace_root = os.path.dirname(__file__)
for possible_path in [
    os.path.join(workspace_root, "plugins", "neo4j-memory"),
    os.path.join(workspace_root, "meditation_memory"),
]:
    if os.path.isfile(os.path.join(possible_path, "meditation_memory", "graph_store.py")):
        sys.path.insert(0, possible_path)
        break

from meditation_memory.graph_store import GraphStore
from meditation_memory.config import Neo4jConfig
from openai import OpenAI

# --- 配置 ---
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = os.environ.get("NEO4J_DATABASE", "neo4j")

OPENROUTER_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = (
    os.environ.get("OPENAI_BASE_URL")
    or os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
)
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek/deepseek-chat")

BATCH_SIZE = 200       # 每批 200 个实体
MAX_WORKERS = 4        # 4 线程并发

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("cleanup")


# ================================================================
#  规则判断：快速识别明显无效的实体
# ================================================================

_TRUNACTED_PATTERNS = [
    "模和", "规模和", "模提", "件记", "到长", "析构建",
    "储规模", "并分析", "和提", "构建提", "系统作",
    "记忆系", "提取模", "提示词命", "分析构建", "件记忆",
    "到长期", "到长期记忆", "模和提示", "和提示词",
]

_BAD_CHARS_START = [
    "的", "了", "在", "和", "是", "有", "被", "把", "从", "对",
    "让", "给", "与", "或", "而", "就", "都", "也", "还", "又",
    "很", "最", "更", "太", "不", "没", "要", "会", "能", "可",
    "因", "若", "如", "虽", "但", "故", "则", "当", "为",
    "且", "即", "将", "已", "未", "须",
]

_BAD_CHARS_END = [
    "的", "了", "着", "过", "得", "地", "在", "和", "是",
    "有", "被", "把", "来", "去", "于", "从", "向", "对",
    "与", "或", "而", "就", "都", "也", "还", "又", "则",
    "时", "中", "后", "前", "间", "内", "外", "上", "下",
    "为", "因", "由", "经", "以", "及", "等", "给", "将",
]


def is_rule_truncated(name: str) -> bool:
    if re.match(r"^[\d\s.,]+$", name):
        return True
    if re.match(r"^[a-zA-Z]+$", name) and len(name) <= 2:
        return True
    if len(name) == 1 and "\u4e00" <= name <= "\u9fff":
        return True
    if any(name.startswith(w) for w in _BAD_CHARS_START):
        return True
    if any(name.endswith(w) for w in _BAD_CHARS_END):
        return True
    if any(sub in name for sub in _TRUNACTED_PATTERNS):
        return True
    if name.startswith(("http", "www", "/api", "./")):
        return True
    if name.count("/") > 2 or name.count("\\") > 2:
        return True
    return False


# ================================================================
#  LLM 判断
# ================================================================

class LLMJudge:
    def __init__(self):
        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            timeout=120,
        )

    def judge_batch(self, names: List[str], batch_id: int = 0) -> List[Dict[str, Any]]:
        names_json = json.dumps(names, ensure_ascii=False, indent=2)
        system_prompt = (
            "你是一个实体质量检测助手。给定一组实体名称，判断每个名称是否是一个完整的、"
            "有意义的词或短语。\n"
            "判断标准：\n"
            '1. 是完整词/短语 → "valid": true\n'
            '   例如: "人工智能", "OpenClaw", "张三", "北京市", "自然语言处理"\n'
            '2. 截断碎片 → "valid": false\n'
            '   例如: "储规模和技术", "并分析构建提", "模和提示词命", "件记忆系统", "到长期记忆"\n'
            '3. 口语表达、句子碎片、虚词短语 → "valid": false\n'
            '   例如: "我知道", "他认为", "因为", "所以说", "这样的话"\n\n'
            "注意：\n"
            "- 如果实体像是从一句话中间截断产生的，标记为 invalid\n"
            "- 如果实体可能是复合词但看起来不自然，标记为 invalid\n"
            "- 英文、数字混合的合理技术术语标记为 valid\n\n"
            "请严格以如下 JSON 数组格式输出，不要其他内容：\n"
            '[{"name":"实体名","is_valid":true/false,"reason":"简短理由"}]'
        )
        user_prompt = f"请判断以下实体是否是完整有效的：\n{names_json}"

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                    max_tokens=8192,
                )
                content = response.choices[0].message.content or ""
                json_match = re.search(r"\[[\s\S]*\]", content)
                if not json_match:
                    logger.warning("批次 %d: LLM 返回非 JSON: %s", batch_id, content[:200])
                    if attempt < 2:
                        time.sleep(2)
                        continue
                    return [{"name": n, "is_valid": None, "reason": "LLM parse error"} for n in names]
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.error("批次 %d: JSON 解析失败", batch_id)
                if attempt < 2:
                    time.sleep(2)
                    continue
                return [{"name": n, "is_valid": None, "reason": "JSON parse error"} for n in names]
            except Exception as exc:
                logger.error("批次 %d 第 %d 次尝试失败: %s", batch_id, attempt + 1, exc)
                if attempt < 2:
                    time.sleep(3)
                    continue
                return [{"name": n, "is_valid": None, "reason": f"LLM error: {exc}"} for n in names]

        return [{"name": n, "is_valid": None, "reason": "max retries"} for n in names]


# ================================================================
#  主流程
# ================================================================

def fetch_all_entities(store: GraphStore) -> List[Dict[str, Any]]:
    with store.driver.session() as session:
        records = session.run(
            "MATCH (n) WHERE n.name IS NOT NULL AND n.entity_type IS NOT NULL "
            "RETURN n.name AS name, n.entity_type AS type, elementId(n) AS eid "
            "ORDER BY n.name"
        )
        return [
            {"name": r["name"], "type": r["type"], "eid": r["eid"]}
            for r in records
        ]


def find_merge_candidates(invalid_entities: List[Dict], all_entities: List[Dict]) -> List[Dict]:
    merges: List[Dict] = []
    valid_names = {e["name"] for e in all_entities if e not in invalid_entities}
    for inv in invalid_entities:
        name = inv["name"]
        for other_name in valid_names:
            if other_name == name:
                continue
            if name in other_name or other_name in name:
                merges.append({
                    "source_name": name,
                    "target_name": other_name,
                })
                break
    return merges


def execute_cleanup(store: GraphStore, invalid_entities: List[Dict], merges: List[Dict]) -> Dict:
    deleted = 0
    failed = 0
    for entity in invalid_entities:
        eid = entity["eid"]
        name = entity["name"]
        try:
            with store.driver.session() as session:
                session.run("MATCH (n) WHERE elementId(n) = $eid DETACH DELETE n", eid=eid)
            deleted += 1
        except Exception as exc:
            failed += 1
            logger.error("  删除失败 '%s': %s", name, exc)
    return {"deleted": deleted, "merged": len(merges), "failed": failed}


def main():
    parser = argparse.ArgumentParser(description="清理 Neo4j 图谱中的截断碎片实体")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际执行删除")
    parser.add_argument("--execute", action="store_true", help="执行模式，实际删除无效实体")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        print("请指定 --dry-run 或 --execute", flush=True)
        sys.exit(1)

    print("=" * 70, flush=True)
    print("  Neo4j 实体清理工具（优化版）", flush=True)
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"  模式: {'预览 (dry-run)' if args.dry_run else '执行 (execute)'}", flush=True)
    print(f"  LLM: {LLM_MODEL}  批次: {BATCH_SIZE}  并发: {MAX_WORKERS}", flush=True)
    print("=" * 70, flush=True)

    if not OPENROUTER_API_KEY:
        print("错误: 未设置 OPENAI_API_KEY 或 OPENROUTER_API_KEY 环境变量", flush=True)
        sys.exit(1)

    neo4j_cfg = Neo4jConfig(uri=NEO4J_URI, user=NEO4J_USER,
                            password=NEO4J_PASSWORD, database=NEO4J_DATABASE)
    store = GraphStore(neo4j_cfg)

    if not store.verify_connectivity():
        logger.error("无法连接到 Neo4j (%s)", NEO4J_URI)
        sys.exit(1)
    logger.info("已连接 Neo4j")

    stats = store.get_stats()
    total_nodes = stats.get("nodes", 0) if isinstance(stats, dict) else stats
    logger.info("图谱节点总数: %s", total_nodes)

    logger.info("获取所有实体节点…")
    entities = fetch_all_entities(store)
    logger.info("共找到 %d 个实体节点", len(entities))

    # ---- 第一步：规则过滤 ----
    rule_invalid = []
    rule_valid = []
    for entity in entities:
        if is_rule_truncated(entity["name"]):
            rule_invalid.append(entity)
        else:
            rule_valid.append(entity)

    logger.info("规则过滤: %d 个无效, %d 个需要 LLM 判断", len(rule_invalid), len(rule_valid))

    # ---- 第二步：LLM 并发判断 ----
    llm_needed = rule_valid
    llm_judge = LLMJudge()

    # 构建批次
    batches = []
    for i in range(0, len(llm_needed), BATCH_SIZE):
        batch = llm_needed[i:i + BATCH_SIZE]
        batch_names = [e["name"] for e in batch]
        batches.append((i // BATCH_SIZE + 1, batch_names))

    total_batches = len(batches)
    logger.info("共 %d 个批次，开始并发处理（%d 线程）…", total_batches, MAX_WORKERS)

    all_llm_results: List[Dict[str, Any]] = [None] * total_batches  # 保持顺序
    completed = 0
    t0 = time.time()

    def process_batch(args):
        batch_id, names = args
        return batch_id, llm_judge.judge_batch(names, batch_id=batch_id)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_batch, b): b[0] for b in batches}
        for future in as_completed(futures):
            batch_id = futures[future]
            try:
                bid, results = future.result()
                all_llm_results[bid - 1] = results
            except Exception as exc:
                logger.error("批次 %d 异常: %s", batch_id, exc)
                _, names = batches[batch_id - 1]
                all_llm_results[batch_id - 1] = [
                    {"name": n, "is_valid": None, "reason": f"error: {exc}"} for n in names
                ]
            completed += 1
            elapsed = time.time() - t0
            eta = (elapsed / completed) * (total_batches - completed) if completed > 0 else 0
            print(f"  进度: {completed}/{total_batches} ({100*completed/total_batches:.0f}%) "
                  f"已用 {elapsed:.0f}s  预计剩余 {eta:.0f}s", flush=True)

    # 合并结果
    llm_results = []
    for batch_result in all_llm_results:
        if batch_result:
            llm_results.extend(batch_result)

    # ---- 第三步：分类 ----
    invalid_entities = list(rule_invalid)
    valid_entities: List[Dict] = []
    uncertain_entities: List[Dict] = []

    llm_name_to_result = {r["name"]: r for r in llm_results}
    for entity in llm_needed:
        name = entity["name"]
        result = llm_name_to_result.get(name, {"is_valid": None})
        entity["llm_result"] = result
        if result.get("is_valid") is False:
            invalid_entities.append(entity)
        elif result.get("is_valid") is True:
            valid_entities.append(entity)
        else:
            uncertain_entities.append(entity)

    logger.info("判断结果: 有效 %d | 无效 %d | 不确定 %d",
                len(valid_entities), len(invalid_entities), len(uncertain_entities))

    merges = find_merge_candidates(invalid_entities, entities)
    logger.info("找到 %d 个可能的合并", len(merges))

    # ---- 输出报告 ----
    print("\n" + "=" * 70, flush=True)
    print("  清理报告", flush=True)
    print("=" * 70, flush=True)

    print(f"\n  总实体数: {len(entities)}", flush=True)
    print(f"  规则判定无效: {len(rule_invalid)}", flush=True)
    print(f"  LLM 判定无效: {len(invalid_entities) - len(rule_invalid)}", flush=True)
    print(f"  总计无效: {len(invalid_entities)}", flush=True)
    print(f"  有效: {len(valid_entities)}", flush=True)
    print(f"  不确定: {len(uncertain_entities)}", flush=True)

    if invalid_entities:
        print(f"\n❌ 需要删除的实体 ({len(invalid_entities)} 个):", flush=True)
        print("-" * 60, flush=True)
        for i, e in enumerate(invalid_entities[:80]):
            reason = e.get("llm_result", {}).get("reason", "规则判断")
            print(f"  {i+1:4d}. {e['name'][:50]:50s} ({e['type']}) [{reason}]", flush=True)
        if len(invalid_entities) > 80:
            print(f"  … 还有 {len(invalid_entities) - 80} 个", flush=True)

    if merges:
        print(f"\n🔄 建议合并 ({len(merges)} 对):", flush=True)
        print("-" * 60, flush=True)
        for i, m in enumerate(merges[:30]):
            print(f"  {i+1}. '{m['source_name']}' → '{m['target_name']}'", flush=True)
        if len(merges) > 30:
            print(f"  … 还有 {len(merges) - 30} 对", flush=True)

    if uncertain_entities:
        print(f"\n⚠️  不确定 ({len(uncertain_entities)} 个):", flush=True)
        print("-" * 60, flush=True)
        for i, e in enumerate(uncertain_entities[:20]):
            res = e.get("llm_result", {})
            print(f"  {i+1}. {e['name'][:50]:50s} → {json.dumps(res, ensure_ascii=False)}", flush=True)
        if len(uncertain_entities) > 20:
            print(f"  … 还有 {len(uncertain_entities) - 20} 个", flush=True)

    if args.execute:
        print(f"\n{'=' * 70}", flush=True)
        print("  执行清理", flush=True)
        print(f"{'=' * 70}", flush=True)
        result = execute_cleanup(store, invalid_entities, merges)
        print(f"\n清理完成: 删除 {result['deleted']} 个 | 合并建议 {result['merged']} 个 | 失败 {result['failed']} 个", flush=True)
        new_stats = store.get_stats()
        new_nodes = new_stats.get("nodes", 0) if isinstance(new_stats, dict) else new_stats
        print(f"节点: {total_nodes} → {new_nodes}", flush=True)
    else:
        print(f"\n{'=' * 70}", flush=True)
        print("  预览完成。添加 --execute 执行清理。", flush=True)
        print(f"{'=' * 70}", flush=True)

    store.close()


if __name__ == "__main__":
    main()
