#!/usr/bin/env python3
"""
Self-Evolution Pipeline（自我进化管道）
将冥思结果 → 自适应学习 → 元学习反馈 → 参数自动调优 串成闭环。

这是一个纯函数集合（无全局状态），可被 meditation_worker 或
memory_api_server 安全调用。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cognitive.evolution_pipeline")

# ======================================================================
# 1. 冥思结果 → 自适应学习系统状态
# ======================================================================

def build_system_state_from_meditation(
    meditation_result: Dict[str, Any],
    graph_stats: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    把冥思运行结果转换成自适应学习系统可消费的 SystemState。

    Args:
        meditation_result: MeditationRunResult.to_dict() 输出
        graph_stats: Neo4j stats 接口返回的图谱统计

    Returns:
        系统状态字典，可直接传给 AdaptiveLearningController
    """
    stats = meditation_result.get("stats", {})
    errors = meditation_result.get("errors", [])

    graph = graph_stats or {}
    total_nodes = graph.get("node_count", 0)
    total_edges = graph.get("edge_count", 0)

    # 冲突率 = (信念冲突 + 归档节点) / 总扫描
    scanned = max(1, stats.get("nodes_scanned", 1))
    conflicts = stats.get("belief_conflicts_detected", 0)
    pruned = stats.get("nodes_pruned", 0)
    conflict_rate = (conflicts + pruned) / scanned

    # 写入率 = (合并 + 修复 + 关系重标注) / 总扫描
    applied = (
        stats.get("entities_merged", 0)
        + stats.get("entities_repaired", 0)
        + stats.get("relations_relabeled", 0)
    )
    write_ratio = applied / scanned

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "total_applied_diffs": applied,
        "total_patterns": stats.get("meta_knowledge_created", 0),
        "avg_pattern_confidence": 1.0 - conflict_rate,
        "write_ratio": round(write_ratio, 4),
        "conflict_rate": round(conflict_rate, 4),
        "error_count": len(errors),
        "edges_per_round": total_edges / max(1, scanned),
        "diffs_per_round": applied / max(1, scanned),
    }


# ======================================================================
# 2. 元学系统反馈：从冥思统计计算 feedback_signal
# ======================================================================

def compute_metalearn_feedback(
    meditation_result: Dict[str, Any],
    previous_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    量化本次冥思的「学习成效」，反馈给元学习系统。

    Returns:
        {
            "success": True/False,
            "quality_delta": -1.0 ~ +1.0,
            "velocity": int (处理实体数),
            "learning_velocity": float (边增长/轮),
            "confidence": 0.0 ~ 1.0
        }
    """
    stats = meditation_result.get("stats", {})
    errors = meditation_result.get("errors", [])

    # velocity = 本次实际处理的实体数量
    velocity = (
        stats.get("entities_merged", 0)
        + stats.get("entities_repaired", 0)
        + stats.get("relations_relabeled", 0)
        + stats.get("meta_knowledge_created", 0)
    )

    # quality indicators
    belief_conflicts = stats.get("belief_conflicts_detected", 0)
    high_priority = stats.get("attention_high_priority", 0)
    quality_flagged = stats.get("attention_quality_flagged", 0)

    # quality_delta: +1 表示高质量运行，-1 表示大量问题
    quality_delta = 0.0
    if velocity > 0:
        quality_delta += 0.3  # 有实际处理 → 基础加分
    if high_priority > 0:
        quality_delta += 0.1  # 处理了高优先级实体
    if belief_conflicts > 5:
        quality_delta -= 0.2  # 大量信念冲突 → 减分
    if quality_flagged > 10:
        quality_delta -= 0.1  # 大量质量标记 → 减分
    if errors:
        quality_delta -= 0.1 * len(errors)

    quality_delta = max(-1.0, min(1.0, quality_delta))

    # confidence
    confidence = 1.0 - (len(errors) * 0.1) - (belief_conflicts * 0.02)
    confidence = max(0.0, min(1.0, confidence))

    # delta vs previous
    delta_metrics = {}
    if previous_result:
        prev_stats = previous_result.get("stats", {})
        for key in ["entities_merged", "relations_relabeled", "meta_knowledge_created"]:
            curr = stats.get(key, 0)
            prev = prev_stats.get(key, 0)
            if prev > 0:
                delta_metrics[key] = round((curr - prev) / prev, 4)

    return {
        "success": len(errors) == 0 and quality_delta >= 0,
        "quality_delta": round(quality_delta, 4),
        "velocity": velocity,
        "confidence": round(confidence, 4),
        "delta_metrics": delta_metrics,
    }


# ======================================================================
# 3. 冥思配置自动调优建议
# ======================================================================

def suggest_config_adjustments(
    meditation_result: Dict[str, Any],
    current_config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    根据冥思结果给出配置调整建议。

    建议类型：
        - increase_batch_size: 批处理量太小
        - decrease_batch_size: 批处理量太大导致超时/错误
        - increase_pruning_threshold: 修剪太多/太少
        - enable_adaptive_learning: 系统进入稳定期应开启自适应
        - increase_meta_nodes: 知识蒸馏产出不足
    """
    suggestions: List[Dict[str, Any]] = []
    stats = meditation_result.get("stats", {})
    errors = meditation_result.get("errors", [])

    scanned = stats.get("nodes_scanned", 0)

    # 规则1: 扫描量大但处理量小 → 增加批处理
    if scanned > 200 and stats.get("entities_merged", 0) < 5:
        suggestions.append({
            "action": "increase_merging_batch",
            "reason": f"Scanned {scanned} nodes but only merged {stats.get('entities_merged', 0)}",
            "param": "meditation.merging.similar_entity_batch",
        })

    # 规则2: 有错误 → 减少批处理降低风险
    if errors:
        suggestions.append({
            "action": "reduce_batch_size",
            "reason": f"{len(errors)} errors occurred, reducing batch for safety",
            "param": "meditation.*_batch",
        })

    # 规则3: 高优先级实体被处理 → 系统稳定，可开启自适应学习
    if stats.get("attention_high_priority", 0) > 20 and not errors:
        suggestions.append({
            "action": "enable_adaptive_learning",
            "reason": "High priority nodes processed successfully — system is stable",
            "param": "adaptive_learning.enabled",
        })

    # 规则4: 知识蒸馏产出不足 → 增加元知识节点上限
    if scanned > 100 and stats.get("meta_knowledge_created", 0) < 3:
        suggestions.append({
            "action": "increase_meta_node_limit",
            "reason": "Low meta-knowledge yield despite high scan count",
            "param": "meditation.distillation.max_meta_nodes",
        })

    # 规则5: 信念冲突多 → 增加冲突检测权重
    if stats.get("belief_conflicts_detected", 0) > 10:
        suggestions.append({
            "action": "increase_belief_conflict_threshold",
            "reason": f"{stats['belief_conflicts_detected']} belief conflicts detected",
            "param": "belief_integration.conflict_threshold",
        })

    return suggestions


# ======================================================================
# 4. 一键调用：完整进化管道
# ======================================================================

@dataclass
class EvolutionPipelineResult:
    system_state: Dict[str, Any] = field(default_factory=dict)
    feedback: Dict[str, Any] = field(default_factory=dict)
    config_suggestions: List[Dict[str, Any]] = field(default_factory=list)


def run_evolution_pipeline(
    meditation_result: Dict[str, Any],
    graph_stats: Optional[Dict[str, Any]] = None,
    previous_result: Optional[Dict[str, Any]] = None,
    current_config: Optional[Dict[str, Any]] = None,
) -> EvolutionPipelineResult:
    """
    一键执行完整的自我进化管道：
    1. 构建系统状态
    2. 计算元学习反馈
    3. 生成配置调优建议

    调用处：memory_api_server.py 的 meditation 完成回调，或
           meditation_worker.run_meditation() 返回值处理。
    """
    system_state = build_system_state_from_meditation(meditation_result, graph_stats)
    feedback = compute_metalearn_feedback(meditation_result, previous_result)
    suggestions = suggest_config_adjustments(meditation_result, current_config)

    if feedback.get("success"):
        logger.info(
            "Evolution pipeline: quality_delta=%.3f velocity=%d confidence=%.3f",
            feedback["quality_delta"], feedback["velocity"], feedback["confidence"],
        )
    else:
        logger.warning(
            "Evolution pipeline: run not optimal — quality_delta=%.3f errors=%d",
            feedback["quality_delta"], len(meditation_result.get("errors", [])),
        )

    for s in suggestions:
        logger.info("Config suggestion: %s → %s", s["action"], s["reason"])

    return EvolutionPipelineResult(
        system_state=system_state,
        feedback=feedback,
        config_suggestions=suggestions,
    )
