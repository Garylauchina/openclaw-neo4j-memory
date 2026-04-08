"""
冥思引擎核心（Meditation Worker）

实现设计文档中的 9 步流水线：
  1. 数据快照与锁定
  2. 孤立节点清理（Pruning）
  3. 实体整合与修复（Merging）
  4. 关系推理与重标注（Restructuring）
  5. 权重强化与衰减（Weighting）
  6. 知识蒸馏（Distillation）
  6.5 策略蒸馏（Strategy Distillation）— Phase 3 新增
  6.6 策略进化（Strategy Evolution）— Phase 3 新增
  7. 事务提交与解锁

作为独立的异步 Worker 进程运行，与 memory_api_server 共享 GraphStore。
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

# Import new information theory and rule engine modules
from .information_theory import GraphEntropyMetrics, EntropyReductionAnalyzer, MeditationOptimizer
from .rule_engine import RuleEngine


# Phase 4.1: 冥思进化系统
from .meditation_evolution import analyze_and_adjust, MeditationLogManager

from .graph_store import GraphStore
from .meditation_config import MeditationConfig

# Phase 3: 策略蒸馏器
try:
    import sys as _sys
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _project_root not in _sys.path:
        _sys.path.insert(0, _project_root)
    from cognitive_engine.strategy_distiller import StrategyDistiller
except ImportError:
    StrategyDistiller = None  # type: ignore

logger = logging.getLogger("meditation.worker")


# ================================================================
# 数据结构
# ================================================================

@dataclass
class MeditationRunResult:
    """一次冥思运行的结果"""

    run_id: str = ""
    started_at: str = ""
    finished_at: str = ""
    status: str = "pending"  # pending / running / completed / failed / dry_run
    dry_run: bool = False

    # 各步骤统计
    nodes_scanned: int = 0
    nodes_pruned: int = 0
    entities_merged: int = 0
    entities_repaired: int = 0
    metadata_enriched: int = 0
    relations_relabeled: int = 0
    relations_inferred: int = 0
    weights_updated: int = 0
    nodes_archived_by_weight: int = 0
    meta_knowledge_created: int = 0

    # Phase 3: 策略蒸馏与进化统计
    strategies_distilled: int = 0
    strategies_archived: int = 0
    strategies_evolved: int = 0
    causal_chains_found: int = 0
    strategies_evaluated: int = 0

    # Phase 5 Cognitive Integration
    belief_conflicts_detected: int = 0
    attention_high_priority: int = 0
    attention_quality_flagged: int = 0

    # Phase 7: Metacognition Self-Reflection (Issue #18, #19)
    metacognition_self_reflection_run: bool = False
    metacognition_nodes_created: int = 0
    metacognition_confidence_adjusted: int = 0
    metacognition_law1_insights: int = 0  # Understanding user intent
    metacognition_law2_insights: int = 0  # Self-reflection
    metacognition_law3_insights: int = 0  # Capability boundaries

    # Self-evolution pipeline (非序列化字段)
    evolution_feedback: Dict[str, Any] = field(default_factory=dict)
    evolution_suggestions: List[Dict[str, Any]] = field(default_factory=list)

    # 错误信息
    errors: List[str] = field(default_factory=list)

    # Dry-run 模式下的建议操作
    suggestions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "dry_run": self.dry_run,
            "stats": {
                "nodes_scanned": self.nodes_scanned,
                "nodes_pruned": self.nodes_pruned,
                "entities_merged": self.entities_merged,
                "entities_repaired": self.entities_repaired,
                "metadata_enriched": self.metadata_enriched,
                "relations_relabeled": self.relations_relabeled,
                "relations_inferred": self.relations_inferred,
                "weights_updated": self.weights_updated,
                "nodes_archived_by_weight": self.nodes_archived_by_weight,
                "meta_knowledge_created": self.meta_knowledge_created,
                "strategies_distilled": self.strategies_distilled,
                "strategies_archived": self.strategies_archived,
                "strategies_evolved": self.strategies_evolved,
                "causal_chains_found": self.causal_chains_found,
                "strategies_evaluated": self.strategies_evaluated,
                # Phase 5
                "belief_conflicts_detected": self.belief_conflicts_detected,
                "attention_high_priority": self.attention_high_priority,
                "attention_quality_flagged": self.attention_quality_flagged,
                # Phase 7: Metacognition
                "metacognition_self_reflection_run": self.metacognition_self_reflection_run,
                "metacognition_nodes_created": self.metacognition_nodes_created,
                "metacognition_confidence_adjusted": self.metacognition_confidence_adjusted,
                "metacognition_law1_insights": self.metacognition_law1_insights,
                "metacognition_law2_insights": self.metacognition_law2_insights,
                "metacognition_law3_insights": self.metacognition_law3_insights,
            },
            "errors": self.errors,
            "suggestions": self.suggestions if self.dry_run else [],
        }


# ================================================================
# LLM 客户端封装
# ================================================================

class MeditationLLMClient:
    """
    冥思专用 LLM 客户端

    封装 OpenAI 兼容 API 的调用逻辑，支持同义实体判断、截断修复、
    关系重标注、语义评分和知识蒸馏等功能。
    """

    def __init__(self, config: MeditationConfig):
        self._config = config.llm
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI
            kwargs = {}
            if self._config.api_key:
                kwargs["api_key"] = self._config.api_key
            if self._config.base_url:
                kwargs["base_url"] = self._config.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self._config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self._config.temperature,
                timeout=self._config.request_timeout,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("LLM call failed: %s", e)
            raise

    def _parse_json_response(self, text: str) -> Any:
        """从 LLM 响应中解析 JSON"""
        import re
        # 直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 提取 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        # 找到 { } 或 [ ] 之间的内容
        for sc, ec in [('{', '}'), ('[', ']')]:
            start = text.find(sc)
            end = text.rfind(ec)
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass
        logger.warning("Failed to parse JSON from LLM response: %s", text[:200])
        return None

    def judge_synonym_entities(self, pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """判断实体对是否为同义实体。"""
        if not pairs:
            return []
        system_prompt = (
            "你是一个实体对齐专家。请判断以下实体对是否指代同一个现实世界实体。\n"
            "对于每一对，返回 JSON 数组，每个元素包含：\n"
            '  - "pair_index": 对的索引（从 0 开始）\n'
            '  - "is_same": 是否为同一实体（true/false）\n'
            '  - "main_name": 如果是同一实体，推荐保留的标准名称\n'
            '  - "reason": 判断理由\n'
            "只返回 JSON，不要其他文字。"
        )
        pair_descs = []
        for i, p in enumerate(pairs):
            pair_descs.append(
                f"对 {i}: \"{p['name_a']}\"（类型: {p.get('type_a', '未知')}, "
                f"提及: {p.get('mentions_a', 0)}）vs "
                f"\"{p['name_b']}\"（类型: {p.get('type_b', '未知')}, "
                f"提及: {p.get('mentions_b', 0)}, "
                f"共同邻居: {p.get('shared_neighbors', 0)}）"
            )
        user_prompt = "请判断以下实体对：\n" + "\n".join(pair_descs)
        try:
            resp = self._call_llm(system_prompt, user_prompt)
            results = self._parse_json_response(resp)
            if isinstance(results, list):
                return results
        except Exception as e:
            logger.error("Failed to judge synonym entities: %s", e)
        return []

    def repair_truncated_entity(
        self, entity_name: str, entity_type: str, neighbor_names: List[str],
    ) -> Optional[str]:
        """修复截断实体的名称。"""
        system_prompt = (
            "你是一个实体名称修复专家。给定一个可能被截断的实体名称及其上下文，"
            "请推断出完整的实体名称。\n"
            "只返回 JSON 格式：\n"
            '{"repaired_name": "完整名称", "confidence": 0.0-1.0, "reason": "理由"}\n'
            "如果无法确定，confidence 设为 0。"
        )
        user_prompt = (
            f"截断名称: \"{entity_name}\"\n"
            f"实体类型: {entity_type}\n"
            f"相关实体: {', '.join(neighbor_names[:10])}"
        )
        try:
            resp = self._call_llm(system_prompt, user_prompt)
            result = self._parse_json_response(resp)
            if result and isinstance(result, dict):
                if result.get("confidence", 0) >= 0.6:
                    repaired = result.get("repaired_name", "")
                    if repaired and repaired != entity_name:
                        return repaired
        except Exception as e:
            logger.error("Failed to repair truncated entity '%s': %s", entity_name, e)
        return None

    def infer_entity_metadata(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为缺少元数据的实体推断类型和描述。"""
        if not entities:
            return []
        system_prompt = (
            "你是一个知识图谱专家。请为以下实体推断合适的类型和简短描述。\n"
            "可用的实体类型: person, organization, concept, event, object, place, technology\n"
            "返回 JSON 数组，每个元素包含：\n"
            '  - "name": 实体名称\n'
            '  - "suggested_type": 推荐的实体类型\n'
            '  - "description": 简短描述（一句话）\n'
            "只返回 JSON，不要其他文字。"
        )
        entity_descs = []
        for e in entities:
            neighbors = e.get("neighbors", [])
            nb_str = ", ".join(
                f"{n.get('name', '?')}({n.get('rel', 'related_to')})"
                for n in neighbors[:5] if n.get("name")
            )
            entity_descs.append(
                f"- \"{e['name']}\"（当前类型: {e.get('entity_type', '未知')}, "
                f"关联: {nb_str or '无'}）"
            )
        user_prompt = "请为以下实体推断元数据：\n" + "\n".join(entity_descs)
        try:
            resp = self._call_llm(system_prompt, user_prompt)
            results = self._parse_json_response(resp)
            if isinstance(results, list):
                return results
        except Exception as e:
            logger.error("Failed to infer entity metadata: %s", e)
        return []

    def relabel_relations(
        self, edges: List[Dict[str, Any]], ontology: List[str],
    ) -> List[Dict[str, Any]]:
        """将 related_to 关系重标注为具体的语义关系类型。"""
        if not edges:
            return []
        system_prompt = (
            "你是一个关系分类专家。请将以下通用的 'related_to' 关系重新分类为更具体的语义关系类型。\n"
            f"可用的关系类型: {', '.join(ontology)}\n"
            "如果无法确定更具体的类型，保持 'related_to' 不变。\n"
            "返回 JSON 数组，每个元素包含：\n"
            '  - "index": 关系的索引（从 0 开始）\n'
            '  - "new_relation_type": 新的关系类型\n'
            '  - "confidence": 置信度 0.0-1.0\n'
            '  - "reason": 判断理由\n'
            "只返回 JSON，不要其他文字。"
        )
        edge_descs = []
        for i, e in enumerate(edges):
            edge_descs.append(
                f"{i}: ({e['source_name']}[{e.get('source_type', '?')}]) "
                f"-[related_to]-> "
                f"({e['target_name']}[{e.get('target_type', '?')}]) "
                f"(提及: {e.get('mention_count', 0)})"
            )
        user_prompt = "请重新分类以下关系：\n" + "\n".join(edge_descs)
        try:
            resp = self._call_llm(system_prompt, user_prompt)
            results = self._parse_json_response(resp)
            if isinstance(results, list):
                return results
        except Exception as e:
            logger.error("Failed to relabel relations: %s", e)
        return []

    def infer_implicit_relations(
        self, subgraph_edges: List[Dict[str, Any]], entity_names: List[str],
    ) -> List[Dict[str, Any]]:
        """基于现有图结构推断隐含关系。"""
        if not subgraph_edges or len(entity_names) < 2:
            return []
        system_prompt = (
            "你是一个知识图谱推理专家。基于以下已知的实体关系，"
            "请推断可能存在但尚未记录的隐含关系。\n"
            "只推断有高置信度的关系，不要过度推断。\n"
            "返回 JSON 数组，每个元素包含：\n"
            '  - "source": 源实体名称\n'
            '  - "target": 目标实体名称\n'
            '  - "relation_type": 关系类型\n'
            '  - "confidence": 置信度 0.0-1.0\n'
            '  - "reason": 推理依据\n'
            "如果没有可以推断的关系，返回空数组 []。\n"
            "只返回 JSON，不要其他文字。"
        )
        edge_descs = [
            f"({e.get('source', '?')}) -[{e.get('relation_type', 'related_to')}]-> ({e.get('target', '?')})"
            for e in subgraph_edges
        ]
        user_prompt = (
            f"已知实体: {', '.join(entity_names[:20])}\n"
            f"已知关系:\n" + "\n".join(edge_descs[:30])
        )
        try:
            resp = self._call_llm(system_prompt, user_prompt)
            results = self._parse_json_response(resp)
            if isinstance(results, list):
                return [
                    r for r in results
                    if r.get("confidence", 0) >= 0.7
                    and r.get("source") in entity_names
                    and r.get("target") in entity_names
                ]
        except Exception as e:
            logger.error("Failed to infer implicit relations: %s", e)
        return []

    def evaluate_semantic_importance(
        self, entities: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """评估实体的语义重要性。"""
        if not entities:
            return []
        system_prompt = (
            "你是一个记忆评估专家。请评估以下实体对用户长期记忆的价值。\n"
            "评分范围为 0.0 到 1.0：\n"
            "  - 0.0-0.2: 无意义的口语词或临时状态\n"
            "  - 0.3-0.5: 一般性概念，有一定参考价值\n"
            "  - 0.6-0.8: 重要概念、工具或常用对象\n"
            "  - 0.8-1.0: 核心偏好、重要事实或长期目标\n"
            "返回 JSON 数组，每个元素包含：\n"
            '  - "name": 实体名称\n'
            '  - "semantic_score": 语义评分 0.0-1.0\n'
            '  - "reason": 评分理由\n'
            "只返回 JSON，不要其他文字。"
        )
        entity_descs = []
        for e in entities:
            entity_descs.append(
                f"- \"{e['name']}\"（类型: {e.get('entity_type', '?')}, "
                f"提及: {e.get('mention_count', 0)}, "
                f"度数: {e.get('degree', 0)}）"
            )
        user_prompt = "请评估以下实体的语义重要性：\n" + "\n".join(entity_descs)
        try:
            resp = self._call_llm(system_prompt, user_prompt)
            results = self._parse_json_response(resp)
            if isinstance(results, list):
                return results
        except Exception as e:
            logger.error("Failed to evaluate semantic importance: %s", e)
        return []

    def distill_knowledge(
        self,
        center_name: str,
        neighbor_list: List[Dict[str, str]],
        edges: List[Dict[str, Any]],
    ) -> Optional[str]:
        """从密集子图中蒸馏元知识。"""
        system_prompt = (
            "分析以下实体及其关系，提取出关于核心实体的高层次洞察或规律。\n"
            "用一到两句话概括，要求信息密度高、有归纳价值。\n"
            "只返回 JSON 格式：\n"
            '{"summary": "归纳的元知识", "confidence": 0.0-1.0}\n'
            "只返回 JSON，不要其他文字。"
        )
        edge_descs = [
            f"({e.get('source', '?')}) -[{e.get('relation_type', '?')}]-> ({e.get('target', '?')})"
            for e in edges
        ]
        nb_descs = [f"{n.get('name', '?')}({n.get('type', '?')})" for n in neighbor_list]
        user_prompt = (
            f"核心实体: {center_name}\n"
            f"相关实体: {', '.join(nb_descs[:15])}\n"
            f"关系:\n" + "\n".join(edge_descs[:20])
        )
        try:
            resp = self._call_llm(system_prompt, user_prompt)
            result = self._parse_json_response(resp)
            if result and isinstance(result, dict):
                if result.get("confidence", 0) >= 0.5:
                    return result.get("summary")
        except Exception as e:
            logger.error("Failed to distill knowledge for %s: %s", center_name, e)
        return None


# ================================================================
# 冥思引擎核心类
# ================================================================

class MeditationEngine:
    """
    冥思引擎（Meditation Engine）

    负责编排和执行 9 步冥思流水线（Phase 3 升级版）。
    """

    def __init__(self, graph_store: GraphStore, config: Optional[MeditationConfig] = None):
        self.store = graph_store
        self.config = config or MeditationConfig()
        self.llm = MeditationLLMClient(self.config)
        # Initialize information-theoretic components
        self.entropy_calculator = GraphEntropyMetrics()
        self.entropy_analyzer = EntropyReductionAnalyzer()
        self.meditation_optimizer = MeditationOptimizer()
        self.rule_engine = RuleEngine()
        self._is_running = False
        self._last_result: Optional[Dict[str, Any]] = None  # 上一次冥思结果，供元学习对比
        # Phase 3: 策略蒸馏器
        if StrategyDistiller is not None:
            self.strategy_distiller = StrategyDistiller(self.config.llm)
        else:
            self.strategy_distiller = None

    async def run_meditation(
        self,
        mode: str = "auto",  # auto / manual / dry_run
        target_nodes: Optional[List[str]] = None,
    ) -> MeditationRunResult:
        """
        执行一次完整的冥思流程。

        Args:
            mode: 运行模式
            target_nodes: 指定要处理的节点列表（可选）

        Returns:
            冥思运行结果统计
        """
        if self._is_running:
            raise RuntimeError("Meditation is already running.")

        self._is_running = True
        run_id = str(uuid.uuid4())
        dry_run = (mode == "dry_run" or self.config.safety.dry_run)

        result = MeditationRunResult(
            run_id=run_id,
            started_at=datetime.now().isoformat(),
            status="running",
            dry_run=dry_run,
        )

        logger.info(f"Starting meditation run {run_id} (dry_run={dry_run})")

        try:
            # 0. 冥思进化分析（Phase 4.1）
            evolution_params = {}
            try:
                # 导入简化的进化模块
                from .meditation_evolution_simple import analyze_and_adjust_simple
                evolution_params = analyze_and_adjust_simple(self.store)
                logger.info(f"Evolution analysis complete: enabled={evolution_params.get('evolution_enabled', False)}")
                
                # 将进化参数添加到结果中
                if evolution_params:
                    result.evolution_params = evolution_params
                    
                # 如果启用了进化，调整冥思目标节点
                if evolution_params.get("evolution_enabled", False):
                    # 第一阶段：只关注截断实体和超级节点
                    # 可以在这里调整target_nodes或传递给后续步骤
                    logger.info(f"Evolution targets: {len(evolution_params.get('cleanup_targets', []))} truncated entities, "
                               f"{len(evolution_params.get('split_candidates', []))} super nodes")
                    
            except Exception as e:
                logger.warning(f"Evolution analysis failed, continuing with normal meditation: {e}")
            
            # 1. 数据快照与锁定
            nodes = await self._step_1_snapshot_and_lock(result, target_nodes)
            if not nodes:
                result.status = "completed"
                result.finished_at = datetime.now().isoformat()
                logger.info("No nodes need meditation. Finishing early.")
                return result

            # 2. 孤立节点清理 (Pruning)
            await self._step_2_pruning(result, nodes)

            # 3. 实体整合与修复 (Merging)
            try:
                await self._step_3_merging(result, nodes)
            except Exception as e:
                logger.error(f"Step 3 (Merging) failed, continuing: {e}")
                result.errors.append(f"step_3_merging: {e}")

            # 4. 关系推理与重标注 (Restructuring)
            try:
                await self._step_4_restructuring(result, nodes)
            except Exception as e:
                logger.error(f"Step 4 (Restructuring) failed, continuing: {e}")
                result.errors.append(f"step_4_restructuring: {e}")

            # 5. 权重强化与衰减 (Weighting)
            try:
                await self._step_5_weighting(result, nodes)
            except Exception as e:
                logger.error(f"Step 5 (Weighting) failed, continuing: {e}")
                result.errors.append(f"step_5_weighting: {e}")

            # 6. 知识蒸馏 (Distillation)
            try:
                await self._step_6_distillation(result, nodes)
            except Exception as e:
                logger.error(f"Step 6 (Distillation) failed, continuing: {e}")
                result.errors.append(f"step_6_distillation: {e}")

            # 6.5 策略蒸馏 (Strategy Distillation) — Phase 3
            try:
                await self._step_6_5_strategy_distillation(result)
            except Exception as e:
                logger.error(f"Step 6.5 (Strategy Distillation) failed, continuing: {e}")
                result.errors.append(f"step_6_5_strategy_distillation: {e}")

            # 6.6 策略进化 (Strategy Evolution) — Phase 3
            try:
                await self._step_6_6_strategy_evolution(result)
            except Exception as e:
                logger.error(f"Step 6.6 (Strategy Evolution) failed, continuing: {e}")
                result.errors.append(f"step_6_6_strategy_evolution: {e}")

            # 7. 事务提交与解锁
            await self._step_7_finalize(result)

            # 8. 元认知自反步骤 (Self-Reflection) — Issue #18, #19
            try:
                await self._step_8_self_reflection(result)
            except Exception as e:
                logger.error(f"Step 8 (Self-Reflection) failed, continuing: {e}")
                result.errors.append(f"step_8_self_reflection: {e}")

            result.status = "completed" if not dry_run else "dry_run"
            logger.info(f"Meditation run {run_id} completed successfully.")

        except Exception as e:
            logger.error(f"Meditation run {run_id} failed: {e}", exc_info=True)
            result.status = "failed"
            result.errors.append(str(e))
            # 尝试解锁
            try:
                self.store.unlock_nodes_after_meditation(run_id)
            except:
                pass
        finally:
            result.finished_at = datetime.now().isoformat()
            self._is_running = False

        return result

    # ---------- 辅助方法：信念冲突检测 ----------

    def _detect_belief_conflicts(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Phase 5 Cognitive Integration: 检测图谱中的信念冲突。
        同名实体信念类型不一致 = 矛盾信息。
        """
        conflicts: List[Dict[str, Any]] = []

        # 检查同名实体的信念冲突
        by_name: Dict[str, List[Dict[str, Any]]] = {}
        for n in nodes:
            name = n.get("name")
            if name:
                by_name.setdefault(name, []).append(n)

        for name, instances in by_name.items():
            if len(instances) < 2:
                continue
            belief_types = set(i.get("belief_type") for i in instances if i.get("belief_type"))
            if len(belief_types) > 1:
                avg_strength = sum(
                    i.get("belief_strength", 0.5) for i in instances
                ) / len(instances)
                conflicts.append({
                    "name": name,
                    "belief_types": list(belief_types),
                    "instance_count": len(instances),
                    "avg_belief_strength": round(avg_strength, 3),
                    "action": "review_and_merge",
                })

        return conflicts[:50]

    # ---------- 步骤 1: 快照与锁定 ----------

    async def _step_1_snapshot_and_lock(
        self, result: MeditationRunResult, target_nodes: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """获取待处理节点并加锁，可选创建快照备份。"""
        if target_nodes:
            # 手动模式：直接获取指定节点
            nodes = []
            for name in target_nodes:
                node = self.store.find_entity(name)
                if node:
                    nodes.append(node)
        else:
            # 自动模式：按注意力分数降序获取高优先级节点
            # Phase 5 Cognitive Integration: 使用注意力分数排序
            if hasattr(self.store, 'get_top_entities_by_attention'):
                top = self.store.get_top_entities_by_attention(
                    limit=500,
                    min_score=0.1
                )
                nodes = [{"name": t["name"], "entity_type": t["entity_type"],
                          "attention_score": t["attention_score"],
                          "mention_count": t["mention_count"]} for t in top]
                # 补充：也获取一些低注意力但高提及的实体（质量问题检测）
                if hasattr(self.store, 'get_low_attention_entities_batch'):
                    low = self.store.get_low_attention_entities_batch(
                        limit=100, min_mention_count=3
                    )
                    seen_names = {n["name"] for n in nodes}
                    for item in low:
                        if item["name"] not in seen_names:
                            nodes.append({
                                "name": item["name"],
                                "entity_type": item["entity_type"],
                                "attention_score": item.get("attention_score", 0),
                                "mention_count": item.get("mention_count", 0),
                                "quality_flag": True
                            })
                    seen_names = {n["name"] for n in nodes}
                # 记录优先级统计（None 安全）
                high_count = sum(1 for n in nodes if (n.get("attention_score") or 0) >= 0.5)
                flagged = sum(1 for n in nodes if n.get("quality_flag"))
                logger.info(f"Priority-ordered nodes: {len(nodes)} total, "
                           f"{high_count} high-attention, {flagged} quality-flagged")
            else:
                # Fallback: 旧版本行为
                nodes = self.store.get_nodes_needing_meditation(
                    limit=500,
                    skip_recent_seconds=self.config.safety.skip_recently_updated_seconds
                )
                # 按注意力分数排序（如 Neo4j 已有该属性）
                if nodes and "attention_score" in (nodes[0] or {}):
                    nodes = sorted(nodes, key=lambda n: (n.get("attention_score") or 0), reverse=True)

        if not nodes:
            return []

        result.nodes_scanned = len(nodes)

        # Phase 5: 记录注意力优先级统计
        high = sum(1 for n in nodes if (n.get("attention_score") or 0) >= 0.5)
        flagged = sum(1 for n in nodes if n.get("quality_flag"))
        result.attention_high_priority = high
        result.attention_quality_flagged = flagged

        # Phase 5: 检测信念冲突
        conflicts = self._detect_belief_conflicts(nodes)
        result.belief_conflicts_detected = len(conflicts)
        if conflicts:
            logger.info(f"Step 0: Detected {len(conflicts)} belief conflicts in scanned nodes")

        node_names = [n["name"] for n in nodes]

        # 锁定节点
        if not result.dry_run:
            locked_count = self.store.lock_nodes_for_meditation(node_names, result.run_id)
            logger.info(f"Locked {locked_count}/{len(node_names)} nodes for meditation.")

        # 创建快照
        if self.config.safety.enable_snapshot:
            snapshot_data = self.store.create_meditation_snapshot(node_names)
            if snapshot_data:
                os.makedirs(self.config.safety.snapshot_dir, exist_ok=True)
                filename = f"snapshot_{result.run_id}_{int(time.time())}.json"
                filepath = os.path.join(self.config.safety.snapshot_dir, filename)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(snapshot_data)
                logger.info(f"Created snapshot backup: {filepath}")

        return nodes

    # ---------- 步骤 2: 孤立节点清理 (Pruning) ----------

    async def _step_2_pruning(self, result: MeditationRunResult, nodes: List[Dict[str, Any]]):
        """清理无边连接的孤立节点、通用词节点、以及信念冲突节点。"""
        # 2.0 信念冲突检测（Phase 5 Cognitive Integration）
        belief_conflicts = self._detect_belief_conflicts(nodes)
        if belief_conflicts:
            if result.dry_run:
                result.suggestions.append({
                    "step": "belief_conflict_detection",
                    "action": "flag_conflicts",
                    "conflicts": belief_conflicts[:10],  # 限制报告数量
                    "reason": "contradictory beliefs detected"
                })
            else:
                result.belief_conflicts_detected = len(belief_conflicts)
            logger.info(f"Step 2.0: Detected {len(belief_conflicts)} belief conflicts.")

        # 2.1 处理孤立节点
        orphans = self.store.get_orphan_nodes(
            min_mentions=self.config.pruning.orphan_min_mentions,
            skip_recent_seconds=self.config.safety.skip_recently_updated_seconds
        )
        orphan_names = [o["name"] for o in orphans]

        # 2.2 处理通用词节点
        generics = self.store.get_generic_word_nodes(
            generic_words=self.config.pruning.generic_words,
            skip_recent_seconds=self.config.safety.skip_recently_updated_seconds
        )
        generic_names = [g["name"] for g in generics]

        # 2.3 基于频次的噪声过滤（接入 rule_engine 的 FrequencyAnalyzer）
        entity_counts = self.store.get_entity_mention_counts()
        total_documents = self.store.get_total_documents()
        
        frequency_result = self.rule_engine.frequency_analyzer.filter_by_frequency(
            entity_counts, total_documents
        )
        
        filtered_out_names = list(frequency_result.get('filtered_out_entities', {}).keys())
        logger.info(f"Step 2.3: Frequency filtering identified {len(filtered_out_names)} low-frequency entities to prune")

        # 合并所有待归档节点
        to_archive = list(set(orphan_names + generic_names + filtered_out_names))
        if not to_archive:
            return

        if result.dry_run:
            result.suggestions.append({
                "step": "pruning",
                "action": "archive",
                "nodes": to_archive,
                "reason": "orphan, generic word, or low-frequency entity"
            })
        else:
            archived_count = self.store.archive_nodes(to_archive, reason="meditation_pruning")
            result.nodes_pruned = archived_count
            logger.info(f"Pruned {archived_count} nodes (orphans: {len(orphan_names)}, generics: {len(generic_names)}, low-frequency: {len(filtered_out_names)})")
        
        # 记录频次过滤的统计信息
        result.pruning_stats = {
            "total_entities": len(entity_counts),
            "kept_entities": frequency_result.get('kept_count', 0),
            "filtered_entities": frequency_result.get('filtered_count', 0),
            "average_frequency": frequency_result.get('average_frequency', 0.0)
        }

    # ---------- 步骤 3: 实体整合与修复 (Merging) ----------

    async def _step_3_merging(self, result: MeditationRunResult, nodes: List[Dict[str, Any]]):
        """同义词合并、截断修复、元数据补充。"""
        # 3.0 同名实体合并（Bug 修复：get_similar_entity_pairs 不查同名副本）
        dupes = self.store.get_duplicate_entities(max_copies_per_name=50)
        if dupes:
            logger.info(f"Step 3.0: Found {len(dupes)} duplicate entity groups.")
            for dup_name, eid_list, mention_counts in dupes:
                if len(eid_list) < 2:
                    continue
                # 保留 mention_count 最高的作为主节点
                main_idx = max(range(len(mention_counts)), key=lambda i: mention_counts[i] or 0)
                main_eid = eid_list[main_idx]
                for i, alias_eid in enumerate(eid_list):
                    if i != main_idx and alias_eid != main_eid:
                        if self.store.merge_entity_nodes(main_eid, alias_eid):
                            result.entities_merged += 1
            logger.info(f"Step 3.0 done: merged {result.entities_merged} duplicate entities.")

        # 3.1 同义词合并
        pairs = self.store.get_similar_entity_pairs(limit=100)
        logger.info(f"Step 3.1: Found {len(pairs)} candidate synonym pairs.")
        if pairs:
            # Use rule engine for synonym decisions (LLM only as fallback)
            for idx, pair in enumerate(pairs):
                # Gather simple context for rule engine
                context = {
                    "mention_counts": {
                        pair["name_a"]: pair.get("mentions_a", 0),
                        pair["name_b"]: pair.get("mentions_b", 0)
                    },
                    "shared_neighbors": pair.get("shared_neighbors", 0)
                }
                decision = self.rule_engine.decide_entity_merge(pair["name_a"], pair["name_b"], context)
                if decision.get("should_merge"):
                    # Determine main and alias based on confidence
                    if decision.get("metrics", {}).get("similarity_breakdown", {}).get("composite_score", 0) >= 0.5:
                        # Prefer higher mention count as main
                        if context["mention_counts"][pair["name_a"]] >= context["mention_counts"][pair["name_b"]]:
                            main_eid, alias_eid = pair["eid_a"], pair["eid_b"]
                        else:
                            main_eid, alias_eid = pair["eid_b"], pair["eid_a"]
                    else:
                        # If low similarity, still merge based on rule engine suggestion
                        main_eid, alias_eid = pair["eid_a"], pair["eid_b"]

                    if result.dry_run:
                        result.suggestions.append({
                            "step": "merging",
                            "action": "merge",
                            "main": pair["name_a"] if main_eid == pair["eid_a"] else pair["name_b"],
                            "alias": pair["name_b"] if alias_eid == pair["eid_b"] else pair["name_a"],
                            "reason": "rule_engine"
                        })
                    else:
                        if self.store.merge_entity_nodes(main_eid, alias_eid):
                            result.entities_merged += 1

        logger.info(f"Step 3.1 done: merged {result.entities_merged} entities.")

        # 3.2 截断修复
        short_nodes = self.store.get_short_name_entities(
            max_name_length=self.config.merging.truncation_name_length
        )
        for sn in short_nodes:
            repaired_name = self.llm.repair_truncated_entity(
                sn["name"], sn["entity_type"], sn.get("neighbor_names", [])
            )
            if repaired_name:
                if result.dry_run:
                    result.suggestions.append({
                        "step": "merging",
                        "action": "repair_name",
                        "old": sn["name"],
                        "new": repaired_name
                    })
                else:
                    if self.store.update_entity_name(sn["name"], repaired_name, sn["entity_type"]):
                        result.entities_repaired += 1

        logger.info(f"Step 3.2 done: repaired {result.entities_repaired} truncated entities.")

        # 3.3 元数据补充
        missing_meta = self.store.get_entities_missing_metadata(limit=100)
        if missing_meta:
            enriched = self.llm.infer_entity_metadata(missing_meta)
            for item in enriched:
                name = item.get("name")
                if not name: continue
                if result.dry_run:
                    result.suggestions.append({
                        "step": "merging",
                        "action": "enrich_metadata",
                        "name": name,
                        "type": item.get("suggested_type"),
                        "desc": item.get("description")
                    })
                else:
                    # 查找原始类型用于匹配
                    orig = next((m for m in missing_meta if m["name"] == name), None)
                    orig_type = orig["entity_type"] if orig else None
                    if self.store.update_entity_metadata(
                        name, orig_type, item.get("description"), item.get("suggested_type")
                    ):
                        result.metadata_enriched += 1

        logger.info(f"Step 3.3 done: enriched metadata for {result.metadata_enriched} entities.")

    # ---------- 步骤 4: 关系推理与重标注 (Restructuring) ----------

    async def _step_4_restructuring(self, result: MeditationRunResult, nodes: List[Dict[str, Any]]):
        """重标注 related_to 关系，推断隐含关系。"""
        # 4.1 重标注
        generic_rels = self.store.get_related_to_edges(limit=self.config.restructuring.relabel_batch_size)
        logger.info(f"Step 4.1: Found {len(generic_rels)} generic relations to relabel.")
        if generic_rels:
            # 批量获取节点上下文信息
            all_node_names = set()
            for rel in generic_rels:
                all_node_names.add(rel["source_name"])
                all_node_names.add(rel["target_name"])
            
            # 获取节点元数据
            node_metadata = {}
            for node_name in all_node_names:
                node = self.store.get_node_by_name(node_name)
                if node:
                    node_metadata[node_name] = {
                        "entity_type": node.get("entity_type", "unknown"),
                        "mention_count": node.get("mention_count", 0),
                        "degree": node.get("degree", 0)
                    }
            
            # 批量获取共享邻居
            shared_neighbors = {}
            for rel in generic_rels:
                src = rel["source_name"]
                tgt = rel["target_name"]
                shared = self.store.get_shared_neighbors(src, tgt, limit=5)
                shared_neighbors[(src, tgt)] = len(shared)
            
            # 使用规则引擎进行关系重标注决策
            relations_to_update = []
            for idx, rel in enumerate(generic_rels):
                src = rel["source_name"]
                tgt = rel["target_name"]
                
                # 准备关系信息
                relation_info = {
                    "source": src,
                    "target": tgt,
                    "source_type": node_metadata.get(src, {}).get("entity_type", "unknown"),
                    "target_type": node_metadata.get(tgt, {}).get("entity_type", "unknown"),
                    "source_mentions": node_metadata.get(src, {}).get("mention_count", 0),
                    "target_mentions": node_metadata.get(tgt, {}).get("mention_count", 0),
                    "shared_neighbors": shared_neighbors.get((src, tgt), 0)
                }
                
                # 准备图上下文
                graph_context = {
                    "total_nodes": len(all_node_names),
                    "relation_ontology": self.config.restructuring.relation_ontology,
                    "max_shared_neighbors": max(shared_neighbors.values()) if shared_neighbors else 0
                }
                
                # 调用规则引擎决策
                decision = self.rule_engine.decide_relation_relabeling(relation_info, graph_context)
                new_type = decision.get("new_relation_type")
                
                # 只接受confidence >= 0.7的决策，否则保留related_to
                if new_type and new_type != "related_to" and decision.get("confidence", 0) >= 0.7:
                    relations_to_update.append({
                        "index": idx,
                        "relation": rel,
                        "new_type": new_type
                    })
            
            # 处理更新
            updated_count = 0
            for update in relations_to_update:
                rel = update["relation"]
                new_type = update["new_type"]
                
                if result.dry_run:
                    result.suggestions.append({
                        "step": "restructuring",
                        "action": "relabel",
                        "src": rel["source_name"],
                        "tgt": rel["target_name"],
                        "old": "related_to",
                        "new": new_type
                    })
                else:
                    if self.store.update_relation_type(
                        rel["source_name"], rel["target_name"], "related_to", new_type
                    ):
                        result.relations_relabeled += 1
                        updated_count += 1
            
            logger.info(f"Step 4.1 done: rule engine relabeled {updated_count} relations out of {len(generic_rels)} candidates")

        # 4.2 隐含关系推断（针对本次扫描的节点子图）
        node_names = [n["name"] for n in nodes[:20]] # 限制规模
        subgraph = self.store.get_subgraph_by_entities(node_names, max_depth=1)
        edges = [{"source": e["source"], "target": e["target"], "relation_type": e["relation_type"]}
                 for e in subgraph.get("edges", [])]

        inferred = self.llm.infer_implicit_relations(edges, node_names)
        for inf in inferred:
            if result.dry_run:
                result.suggestions.append({
                    "step": "restructuring",
                    "action": "infer",
                    "src": inf["source"],
                    "tgt": inf["target"],
                    "type": inf["relation_type"],
                    "conf": inf.get("confidence")
                })
            else:
                if self.store.create_inferred_relation(
                    inf["source"], inf["target"], inf["relation_type"], inf.get("confidence", 0.5)
                ):
                    result.relations_inferred += 1

        logger.info(f"Step 4.2 done: inferred {result.relations_inferred} new relations.")

    # ---------- 步骤 5: 权重强化与衰减 (Weighting) ----------

    async def _step_5_weighting(self, result: MeditationRunResult, nodes: List[Dict[str, Any]]):
        """计算记忆激活值：时间衰减 + 使用频次统计 + 网络中心度。"""
        # 获取所有活跃节点进行权重重算
        active_nodes = self.store.get_all_active_nodes_for_weighting(limit=1000)
        if not active_nodes:
            return

        # 基于规则的语义评分，替代LLM评估
        semantic_scores = {}
        for n in active_nodes:
            name = n["name"]
            # 基于提及频次和网络中心度计算语义评分
            mention_count = n.get("mention_count", 0)
            degree = n.get("degree", 0)
            
            # 计算基础语义评分
            freq_score = min(1.0, math.log1p(mention_count) / 5.0)  # 提及频次得分
            centrality_score = min(1.0, math.log1p(degree) / 10.0)  # 网络中心度得分
            
            # 综合语义评分（考虑节点类型权重）
            node_type = n.get("entity_type", "")
            type_weight = 1.0
            if node_type == "Meta_User":
                type_weight = 1.5  # 用户相关节点权重更高
            elif node_type == "Meta_Self":
                type_weight = 1.2  # 自我认知节点权重较高
            
            semantic_score = (freq_score * 0.6 + centrality_score * 0.4) * type_weight
            semantic_score = min(1.0, max(0.1, semantic_score))  # 限制范围
            
            semantic_scores[name] = semantic_score

        updates = []
        to_archive = []
        now_ms = int(time.time() * 1000)

        for n in active_nodes:
            name = n["name"]
            # 1. 语义分 (基于规则计算)
            s_score = semantic_scores.get(name, n.get("semantic_score", 0.5))

            # 2. 时间衰减（改进的 Ebbinghaus 模型，考虑使用频次的影响）
            # 距离上次更新的天数
            last_update = n.get("updated_at") or now_ms
            days_passed = (now_ms - last_update) / (24 * 3600 * 1000)
            
            # 基础衰减率
            decay_rate = self.config.weight.decay_factor
            
            # 根据提及频次调整衰减率：高频节点衰减慢
            mention_count = n.get("mention_count", 0)
            if mention_count > self.config.weight.high_mention_threshold:
                decay_rate = 1.0 - (1.0 - decay_rate) * 0.7  # 高频节点衰减减少70%
            elif mention_count > self.config.weight.medium_mention_threshold:
                decay_rate = 1.0 - (1.0 - decay_rate) * 0.4  # 中频节点衰减减少40%
            
            # 根据语义评分调整衰减率：核心知识衰减慢
            if s_score >= self.config.weight.high_semantic_threshold:
                decay_rate = 1.0 - (1.0 - decay_rate) * self.config.weight.core_decay_reduction

            # 计算基础激活值
            recency_factor = math.pow(decay_rate, days_passed)
            
            # 3. 使用频次因子
            freq_factor = min(1.0, math.log1p(mention_count) / 10.0)
            
            # 4. 网络中心度因子
            centrality_factor = min(1.0, math.log1p(n.get("degree", 0)) / 15.0)

            # 综合计算激活值
            activation = (
                recency_factor * self.config.weight.recency_weight +
                s_score * self.config.weight.semantic_weight +
                freq_factor * self.config.weight.frequency_weight +
                centrality_factor * self.config.weight.centrality_weight
            )
            activation = max(0.0, min(1.0, activation))

            updates.append({
                "name": name,
                "activation_level": activation,
                "semantic_score": s_score
            })

            # 检查是否需要归档
            if activation < self.config.weight.min_activation_threshold:
                to_archive.append(name)

        if result.dry_run:
            result.suggestions.append({
                "step": "weighting",
                "action": "update_weights",
                "count": len(updates),
                "to_archive": to_archive
            })
        else:
            updated_count = self.store.batch_update_weights(updates)
            result.weights_updated = updated_count
            if to_archive:
                archived_count = self.store.archive_nodes(to_archive, reason="low_activation")
                result.nodes_archived_by_weight = archived_count
            logger.info(f"Updated weights for {updated_count} nodes, archived {len(to_archive)} nodes.")

    # ---------- 步骤 6: 知识蒸馏 (Distillation) ----------

    async def _step_6_distillation(self, result: MeditationRunResult, nodes: List[Dict[str, Any]]):
        """从密集子图中提取元知识。"""
        clusters = self.store.get_dense_subgraphs_for_distillation(
            min_cluster_size=self.config.distillation.min_cluster_size,
            limit=self.config.distillation.max_meta_nodes_per_run
        )

        for cluster in clusters:
            center_name = cluster["center_name"]
            # 限制邻居节点数量，避免过度总结
            max_neighbors = 20
            neighbor_names_full = [n["name"] for n in cluster["neighbor_list"]]
            neighbor_names = neighbor_names_full[:max_neighbors]
            
            edges = self.store.get_cluster_edges(center_name, neighbor_names_full[:max_neighbors*2])
            
            # 使用精准的蒸馏prompt生成
            prompt = self._generate_llm_distillation_prompt(center_name, cluster["neighbor_list"][:max_neighbors], edges)
            summary = self.llm.call_llm(prompt, temperature=0.3, max_tokens=300)
            
            if summary:
                if result.dry_run:
                    result.suggestions.append({
                        "step": "distillation",
                        "action": "create_meta",
                        "summary": summary,
                        "targets": [center_name] + neighbor_names[:5]
                    })
                else:
                    if self.store.create_meta_knowledge_node(
                        summary,
                        [center_name] + neighbor_names,
                        self.config.distillation.meta_knowledge_entity_type,
                        self.config.distillation.summarizes_relation_type
                    ):
                        result.meta_knowledge_created += 1
    
    def _generate_llm_distillation_prompt(self, center_name: str, neighbors: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
        """生成精准的知识蒸馏prompt"""
        # 格式化邻居节点
        neighbor_strs = []
        for n in neighbors[:10]:  # 限制数量
            entity_type = n.get("entity_type", "unknown")
            mention_count = n.get("mention_count", 0)
            neighbor_strs.append(f"- {n['name']} (类型: {entity_type}, 提及次数: {mention_count})")
        
        # 格式化关系
        edge_strs = []
        for e in edges[:15]:  # 限制数量
            rel_type = e.get("relation_type", "related_to")
            edge_strs.append(f"- {e['source']} -> {e['target']} [关系: {rel_type}]")
        
        prompt = f"""你是一个知识蒸馏专家，需要从以下图节点和关系中提取简洁的元知识。

中心节点: {center_name}

相关邻居节点（按重要性排序）:
{chr(10).join(neighbor_strs)}

连接关系:
{chr(10).join(edge_strs)}

请提炼出一个精炼的元知识摘要，要求:
1. 简洁明了，不超过150字
2. 聚焦核心概念和关键关系
3. 避免冗余信息
4. 使用中文，逻辑清晰

元知识摘要:"""
        
        return prompt

    # ---------- 步骤 6.5: 策略蒸馏 (Strategy Distillation) — Phase 3 ----------

    async def _step_6_5_strategy_distillation(self, result: MeditationRunResult):
        """
        策略蒸馏：从图谱中的因果链自动生成策略。

        流程：
        1. 查询图谱中的因果链（CAUSES 关系连接的事件序列）
        2. 过滤长度不足的短链
        3. 交由 LLM 分析因果模式，生成策略候选
        4. 为每个新策略创建 :Strategy 节点
        """
        strategy_config = self.config.strategy

        # 若 max_strategies_per_run == 0，跳过此步骤
        if strategy_config.max_strategies_per_run <= 0:
            logger.info("Strategy distillation disabled (max_strategies_per_run=0)")
            return

        if self.strategy_distiller is None:
            logger.warning("StrategyDistiller not available, skipping step 6.5")
            return

        # 1. 获取因果链
        chains = self.store.get_causal_chains(
            min_length=strategy_config.min_causal_chain_length,
            limit=100,
        )
        result.causal_chains_found = len(chains)

        if not chains:
            logger.info("No causal chains found for distillation")
            return

        # 2. LLM 蒸馏
        new_strategies = self.strategy_distiller.distill(
            chains,
            max_strategies=strategy_config.max_strategies_per_run,
        )

        # 3. 写入图谱
        for s in new_strategies:
            strategy_name = f"distilled_{s.get('name', 'unknown')}"
            strategy_data = {
                "name": strategy_name,
                "type": "distilled",
                "uses_real_data": s.get("uses_real_data", False),
                "fitness": s.get("expected_accuracy", 0.5),
                "content": s.get("content", s.get("reasoning", "")),
                "description": s.get("description", ""),
                "performance": {
                    "avg_accuracy": s.get("expected_accuracy", 0.5),
                    "avg_success": 0.0,
                    "avg_cost": 0.0,
                    "usage_count": 0,
                },
                "metadata": {
                    "description": s.get("description", ""),
                    "applicable_scenarios": s.get("applicable_scenarios", []),
                    "source": "meditation_distillation",
                    "created_at": datetime.now().isoformat(),
                    "evolution_steps": 0,
                },
            }

            if result.dry_run:
                result.suggestions.append({
                    "step": "strategy_distillation",
                    "action": "create_strategy",
                    "strategy": strategy_data,
                })
            else:
                self.store.upsert_strategy_node(strategy_data)
                result.strategies_distilled += 1

        logger.info(
            "Step 6.5 completed: chains_found=%d, strategies_created=%d",
            len(chains), result.strategies_distilled,
        )

    # ---------- 步骤 6.6: 策略进化 (Strategy Evolution) — Phase 3 ----------

    async def _step_6_6_strategy_evolution(self, result: MeditationRunResult):
        """
        策略进化：评估适应度，淘汰低效策略，强化高效策略。

        流程：
        1. 获取所有活跃策略及其 fitness_score
        2. 淘汰低于阈值的策略（保护现实数据策略）
        3. 对高分策略执行交叉，生成新策略
        """
        strategy_config = self.config.strategy

        # 若淘汰阈值为 0.0，跳过此步骤
        if (strategy_config.fitness_elimination_threshold <= 0.0
                and strategy_config.crossover_rate <= 0.0):
            logger.info("Strategy evolution disabled")
            return

        # 1. 获取所有策略
        strategies = self.store.get_strategies_for_evolution()
        result.strategies_evaluated = len(strategies)

        if len(strategies) < strategy_config.min_strategy_pool_size:
            logger.info(
                "Strategy pool too small (%d < %d), skipping evolution",
                len(strategies), strategy_config.min_strategy_pool_size,
            )
            return

        # 2. 淘汰低效策略
        for s in strategies:
            fitness = s.get("fitness_score", 0.0) or 0.0
            uses_real = s.get("uses_real_data", False)
            threshold = (
                strategy_config.reality_protection_threshold
                if uses_real
                else strategy_config.fitness_elimination_threshold
            )

            if fitness < threshold and (s.get("usage_count") or 0) > 5:
                if result.dry_run:
                    result.suggestions.append({
                        "step": "strategy_evolution",
                        "action": "archive_strategy",
                        "strategy_name": s["name"],
                        "fitness": fitness,
                        "threshold": threshold,
                    })
                else:
                    self.store.archive_strategy(s["name"])
                    result.strategies_archived += 1
                    logger.info(
                        "Archived strategy %s (fitness=%.3f < %.3f)",
                        s["name"], fitness, threshold,
                    )

        # 3. 交叉进化（从排名前列的策略中选择）
        top_strategies = [
            s for s in strategies
            if (s.get("fitness_score") or 0) > 0.5
        ]
        if (
            len(top_strategies) >= 2
            and random.random() < strategy_config.crossover_rate
        ):
            p1, p2 = random.sample(top_strategies[:5], 2)
            child_name = f"evolved_{p1['name']}_{p2['name']}"
            child_data = {
                "name": child_name,
                "type": "evolved",
                "uses_real_data": (
                    p1.get("uses_real_data", False)
                    or p2.get("uses_real_data", False)
                ),
                "fitness": (
                    (p1.get("fitness_score", 0) or 0)
                    + (p2.get("fitness_score", 0) or 0)
                ) / 2,
                "performance": {"usage_count": 0},
                "metadata": {"source": "meditation_evolution"},
            }

            if result.dry_run:
                result.suggestions.append({
                    "step": "strategy_evolution",
                    "action": "crossover",
                    "child": child_data,
                    "parents": [p1["name"], p2["name"]],
                })
            else:
                self.store.upsert_strategy_node(child_data)
                self.store.create_evolution_link(
                    child_name, p1["name"], p2["name"]
                )
                result.strategies_evolved += 1

        logger.info(
            "Step 6.6 completed: evaluated=%d, archived=%d, evolved=%d",
            result.strategies_evaluated,
            result.strategies_archived,
            result.strategies_evolved,
        )

    # ---------- 步骤 7: 事务提交与解锁 ----------

    async def _step_7_finalize(self, result: MeditationRunResult):
        """解锁节点、记录日志、运行自我进化管道。"""
        if not result.dry_run:
            unlocked = self.store.unlock_nodes_after_meditation(result.run_id)
            logger.info(f"Unlocked {unlocked} nodes after meditation.")

            # Phase 5.5: 自我进化管道（冥思结果 → 自适应 → 元学习反馈）
            try:
                from cognitive_engine.self_evolution_pipeline import run_evolution_pipeline
                meditation_dict = result.to_dict()
                try:
                    graph_stats = self.store.get_stats()
                except Exception:
                    graph_stats = None

                pipeline_result = run_evolution_pipeline(
                    meditation_dict,
                    graph_stats=graph_stats,
                    previous_result=self._last_result,
                )
                result.evolution_feedback = pipeline_result.feedback
                result.evolution_suggestions = pipeline_result.config_suggestions

                if pipeline_result.feedback.get("success"):
                    logger.info(
                        "Self-evolution: quality_delta=%.3f velocity=%d",
                        pipeline_result.feedback["quality_delta"],
                        pipeline_result.feedback["velocity"],
                    )
                else:
                    logger.warning(
                        "Self-evolution: run not optimal — %d suggestions",
                        len(pipeline_result.config_suggestions),
                    )
            except ImportError:
                logger.debug("self_evolution_pipeline not available, skipping")
            except Exception as e:
                logger.warning(f"Self-evolution pipeline error (non-fatal): {e}")
        else:
            logger.info("Dry-run finished, no nodes were locked/unlocked.")

        # 保存本轮结果供下一轮参考
        self._last_result = result.to_dict()

    async def _step_8_self_reflection(self, result: MeditationRunResult):
        """
        Step 8: Metacognition Self-Reflection (Issue #18, #19)
        
        Reviews recent interactions through the Three Laws lens:
        1. Law 1: Understanding user intent over execution
        2. Law 2: Reflection on own performance  
        3. Law 3: Acknowledging capability boundaries
        
        Creates 3-5 new metacognition nodes based on significant patterns.
        """
        logger.info("Starting metacognition self-reflection step")
        result.metacognition_self_reflection_run = True
        
        try:
            # Import metacognition module
            try:
                from .metacognition import MetacognitionGraph, MetacognitionLaw
                metacognition = MetacognitionGraph(self.store)
                logger.info("Metacognition module imported successfully")
            except ImportError as e:
                logger.warning(f"Metacognition module not available: {e}")
                result.errors.append(f"metacognition_module_import_error: {e}")
                return
            
            # Get recent interactions for analysis
            # In practice, this would query conversation logs from memory system
            # For now, we'll create a minimal implementation
            recent_interactions = []
            
            # Try to get recent conversation history
            # This is a placeholder - actual implementation would depend on
            # how conversation logs are stored in the memory system
            try:
                # Attempt to retrieve recent interactions
                # This could be from a log file, database, or memory store
                pass
            except Exception as e:
                logger.warning(f"Could not retrieve recent interactions: {e}")
            
            # Run self-reflection
            new_cognitions = metacognition.run_self_reflection_step(recent_interactions)
            
            # Create nodes in Neo4j (if not dry_run)
            if not result.dry_run:
                created_count = 0
                law_counts = {1: 0, 2: 0, 3: 0}
                
                for cognition in new_cognitions:
                    if metacognition.create_node(cognition):
                        created_count += 1
                        # Track which law this came from
                        if cognition.law == MetacognitionLaw.LAW_1:
                            law_counts[1] += 1
                        elif cognition.law == MetacognitionLaw.LAW_2:
                            law_counts[2] += 1
                        elif cognition.law == MetacognitionLaw.LAW_3:
                            law_counts[3] += 1
                
                result.metacognition_nodes_created = created_count
                result.metacognition_law1_insights = law_counts[1]
                result.metacognition_law2_insights = law_counts[2]
                result.metacognition_law3_insights = law_counts[3]
                
                logger.info(f"Created {created_count} metacognition nodes "
                          f"(Law1: {law_counts[1]}, Law2: {law_counts[2]}, Law3: {law_counts[3]})")
            else:
                logger.info(f"Dry-run: Would create {len(new_cognitions)} metacognition nodes")
                
        except Exception as e:
            logger.error(f"Metacognition self-reflection failed: {e}", exc_info=True)
            result.errors.append(f"metacognition_error: {e}")
        
        logger.info("Metacognition self-reflection step completed")


# ================================================================
# CLI 运行入口
# ================================================================

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Meditation Worker for Memory System")
    parser.add_argument("--mode", choices=["auto", "manual", "dry_run"], default="auto")
    parser.add_argument("--nodes", nargs="+", help="Target nodes for manual mode")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    store = GraphStore()
    if not store.verify_connectivity():
        print("Error: Could not connect to Neo4j.")
        return

    engine = MeditationEngine(store)
    print(f"Starting meditation in {args.mode} mode...")

    result = await engine.run_meditation(mode=args.mode, target_nodes=args.nodes)

    print("\nMeditation Result:")
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))

    store.close()

if __name__ == "__main__":
    asyncio.run(main())
