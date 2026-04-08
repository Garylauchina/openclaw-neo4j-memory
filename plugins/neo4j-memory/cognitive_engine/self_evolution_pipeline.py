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
        + stats.get("nodes_archived", 0)
        + stats.get("relations_reannotated", 0)
    )
    apply_rate = applied / scanned

    # 信息增益 = 元知识数量 - 归档节点数量
    info_gain = stats.get("meta_knowledge_created", 0) - pruned

    # 系统状态字典
    state = {
        "metrics": {
            "conflict_rate": conflict_rate,
            "apply_rate": apply_rate,
            "info_gain": info_gain,
            "error_rate": len(errors) / len(meditation_result.get("steps", [])),
            "efficiency": stats.get("total_seconds", 0) / max(1, total_nodes),
        },
        "node_stats": {
            "total": total_nodes,
            "pruned": pruned,
            "merged": stats.get("entities_merged", 0),
            "created": stats.get("meta_knowledge_created", 0),
        },
        "edge_stats": {
            "total": total_edges,
            "replaced": stats.get("relations_reannotated", 0),
        },
        "success": not bool(errors),
        "needs_adjustment": conflict_rate > 0.3 or apply_rate < 0.1,
        "current_steps": meditation_result.get("steps", []),
    }

    # 状态映射：从 Metrics 映射到 SystemStatus
    if state["metrics"]["conflict_rate"] > 0.5:
        state["status"] = "CRITICAL"
    elif state["needs_adjustment"]:
        state["status"] = "WARNING"
    elif state["metrics"]["info_gain"] > 0:
        state["status"] = "IMPROVED"
    else:
        state["status"] = "STABLE"

    return state

# ======================================================================
# 元认知三定律优先级编码集成
# ======================================================================

def apply_three_laws_priority_to_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    为系统状态应用元认知三定律优先级编码

    Args:
        state: 系统状态字典

    Returns:
        更新后的系统状态
    """
    priority_weights = {
        'law1_high': 3.0,
        'law2_medium': 2.0,
        'law3_medium': 1.0,
        'other_discard': 0.5
    }

    # 为不同类型的节点设置优先级
    if 'node_stats' in state:
        node_stats = state['node_stats']
        total_nodes = node_stats.get('total', 0)

        # 处理不同类型的节点
        for node_type in ['cognitive', 'reflection', 'boundary', 'general']:
            count = node_stats.get(f'{node_type}_count', 0)
            if count > 0:
                # 根据节点类型确定优先级
                if node_type == 'cognitive':
                    priority = 'law1_high'
                elif node_type == 'reflection':
                    priority = 'law2_medium'
                elif node_type == 'boundary':
                    priority = 'law3_medium'
                else:
                    priority = 'other_discard'

                # 应用优先级权重
                weight = priority_weights[priority]
                state.setdefault('priority_weights', {})[node_type] = weight
                state.setdefault('priority_assignments', {})[node_type] = priority

                logger.info(f"Applied {priority} priority to {node_type} nodes (count: {count}, weight: {weight})")

    # 为策略应用优先级
    if 'strategy_performance' in state:
        for strategy_name, performance in state['strategy_performance'].items():
            # 根据策略性能和类型确定优先级
            if performance.get('success_rate', 0) > 0.9:
                priority = 'law1_high'
            elif performance.get('type') in ['cognitive', 'reflection']:
                priority = 'law2_medium'
            elif performance.get('type') == 'boundary':
                priority = 'law3_medium'
            else:
                priority = 'other_discard'

            # 更新策略
            performance['law_priority'] = priority
            performance['compression_factor'] = calculate_compression_factor(priority)
            logger.info(f"Set strategy {strategy_name} to {priority} priority")

    return state


def calculate_compression_factor(priority: str) -> float:
    """
    根据优先级计算压缩因子

    Args:
        priority: 优先级类型

    Returns:
        压缩因子 (0.0-1.0)
    """
    compression_map = {
        'law1_high': 0.0,    # 不压缩
        'law2_medium': 0.3,  # 保留70%
        'law3_medium': 0.4,  # 保留60%
        'other_discard': 0.8 # 保留20%
    }
    return compression_map.get(priority, 0.8)

# ======================================================================
# 2. 自适应学习 → 元学习反馈
# ======================================================================

def compute_metalearn_feedback(
    current_result: Dict[str, Any], previous_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    计算元学习反馈信号：质量增益、速度、稳定性等。

    Args:
        current_result: 本次冥思结果
        previous_result: 上次冥思结果（可选，用于计算增量）

    Returns:
        包含反馈信号的字典
    """
    stats = current_result.get("stats", {})
    total_seconds = stats.get("total_seconds", 0)

    feedback = {
        "quality_delta": 0.0,
        "velocity": stats.get("nodes_scanned", 0),
        "stability": 1.0 - len(current_result.get("errors", [])) / 10.0,
        "success": True,
        "timestamp": stats.get("start_time"),
    }

    # 如果有历史数据，计算增量
    if previous_result:
        prev_stats = previous_result.get("stats", {})
        
        # 质量增益 = (本次信息增益 - 上次信息增益) / max(1, 上次信息增益)
        current_gain = stats.get("meta_knowledge_created", 0) - stats.get("nodes_pruned", 0)
        prev_gain = prev_stats.get("meta_knowledge_created", 0) - prev_stats.get("nodes_pruned", 0)
        if prev_gain != 0:
            feedback["quality_delta"] = (current_gain - prev_gain) / abs(prev_gain)
        else:
            feedback["quality_delta"] = current_gain

        # 速度比 = 本次扫描速度 / 上次扫描速度
        prev_seconds = prev_stats.get("total_seconds", float("inf"))
        if prev_seconds > 0 and total_seconds > 0:
            current_speed = stats.get("nodes_scanned", 0) / total_seconds
            prev_speed = prev_stats.get("nodes_scanned", 0) / prev_seconds
            feedback["speed_ratio"] = current_speed / prev_speed

        # 稳定性变化
        feedback["stability_delta"] = feedback["stability"] - (1.0 - len(previous_result.get("errors", [])) / 10.0)

    return feedback

# ======================================================================
# 3. 元学习反馈 → 配置自动调优
# ======================================================================

def suggest_config_adjustments(
    current_result: Dict[str, Any], current_config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    根据反馈信号生成冥思配置调优建议。

    Args:
        current_result: 本次冥思结果
        current_config: 当前配置（可选，用于基线比较）

    Returns:
        调优建议列表
    """
    suggestions = []
    stats = current_result.get("stats", {})
    errors = current_result.get("errors", [])

    # 冲突率过高 → 调整合并阈值
    conflict_rate = (
        (stats.get("belief_conflicts_detected", 0) + stats.get("nodes_pruned", 0))
        / max(1, stats.get("nodes_scanned", 1))
    )
    if conflict_rate > 0.4:
        suggestions.append({
            "action": "increase_merge_threshold",
            "reason": f"High conflict rate {conflict_rate:.2f}",
            "current": current_config.get("merge_threshold", 0.7),
            "suggested": 0.8,
        })

    # 没有合并任何实体 → 降低相似度阈值
    if stats.get("entities_merged", 0) == 0:
        suggestions.append({
            "action": "decrease_similarity_threshold",
            "reason": "No entities merged",
            "current": current_config.get("similarity_threshold", 0.8),
            "suggested": 0.6,
        })

    # 元知识创建过少 → 增加蒸馏阈值
    meta_created = stats.get("meta_knowledge_created", 0)
    if meta_created < 5:
        suggestions.append({
            "action": "lower_distillation_threshold",
            "reason": f"Low meta-knowledge creation ({meta_created})",
            "current": current_config.get("min_cluster_size", 5),
            "suggested": 3,
        })

    # 有错误发生 → 建议分步调试
    if errors:
        suggestions.append({
            "action": "enable_step_debugging",
            "reason": f"{len(errors)} errors detected",
            "suggested": True,
        })

    return suggestions

# ======================================================================
# 数据结构与完整管道
# ======================================================================


@dataclass
class EvolutionPipelineResult:
    """自我进化管道返回结果"""
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
    
    # 应用元认知三定律优先级编码
    system_state_with_priority = apply_three_laws_priority_to_state(system_state)

    feedback = compute_metalearn_feedback(meditation_result, previous_result)
    suggestions = suggest_config_adjustments(meditation_result, current_config)

    if feedback.get("success"):
        logger.info(
            "Evolution pipeline: quality_delta=%.3f velocity=%d confidence=%.3f",
            feedback["quality_delta"], feedback["velocity"], feedback.get("confidence", 0.0),
        )
    else:
        logger.warning(
            "Evolution pipeline: run not optimal — quality_delta=%.3f errors=%d",
            feedback["quality_delta"], len(meditation_result.get("errors", [])),
        )

    for s in suggestions:
        logger.info("Config suggestion: %s → %s", s["action"], s["reason"])

    return EvolutionPipelineResult(
        system_state=system_state_with_priority,
        feedback=feedback,
        config_suggestions=suggestions,
    )