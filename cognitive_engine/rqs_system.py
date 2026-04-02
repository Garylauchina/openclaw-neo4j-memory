#!/usr/bin/env python3
"""
RQS（推理质量评分）系统
目标：从"反应式纠错"升级到"统计性认知"，实现长期稳定性
核心：RQS = 长期可靠性评分，解决"局部最优陷阱"

Phase 2 改造：
  - 构造函数新增 neo4j_client 参数
  - 新增 _sync_rqs_to_graph() 将 reasoning_stats 同步到图谱
  - 新增 _load_from_graph() 启动时恢复历史统计
  - 在 calculate_rqs / _update_system_stats 后触发同步
  - Neo4j 不可用时静默降级
"""

import logging
import math
import random
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("cognitive_engine.rqs_system")


class ReasoningSignal(Enum):
    """推理信号枚举"""
    GOOD = "good"           # 好推理，强化
    UNCERTAIN = "uncertain" # 不确定，轻微调整
    BAD = "bad"            # 坏推理，惩罚
    
    def __str__(self):
        return self.value


@dataclass
class ReasoningEdge:
    """推理边"""
    edge_id: str
    source: str
    target: str
    relation: str
    belief_strength: float = 0.5
    weight: float = 0.5
    is_conflict: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "edge_id": self.edge_id,
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "belief_strength": self.belief_strength,
            "weight": self.weight,
            "is_conflict": self.is_conflict
        }


@dataclass
class ReasoningTrace:
    """推理轨迹"""
    trace_id: str
    edges: List[ReasoningEdge] = field(default_factory=list)
    conclusion: str = ""
    confidence: float = 0.0
    consistency_score: float = 0.0
    conflict_detected: bool = False
    supporting_evidence: int = 0
    path_id: str = ""  # 路径ID（用于长期跟踪）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "path_id": self.path_id,
            "edges_count": len(self.edges),
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "consistency_score": self.consistency_score,
            "conflict_detected": self.conflict_detected,
            "supporting_evidence": self.supporting_evidence
        }


@dataclass
class ReasoningStats:
    """
    推理统计（新增核心结构）
    
    目标：记录每条推理路径的长期表现
    解决：短期正确 ≠ 长期正确 的问题
    """
    path_id: str
    success_count: int = 0
    fail_count: int = 0
    total_uses: int = 0
    last_used: datetime = field(default_factory=datetime.now)
    stability_score: float = 0.5  # 路径稳定性（0-1）
    historical_success_rate: float = 0.0  # 历史成功率
    rqs_history: List[float] = field(default_factory=list)  # RQS历史记录
    last_update_time: datetime = field(default_factory=datetime.now)
    
    def update(self, signal: ReasoningSignal, rqs: float = 0.0):
        """更新统计"""
        self.total_uses += 1
        
        if signal == ReasoningSignal.GOOD:
            self.success_count += 1
        elif signal == ReasoningSignal.BAD:
            self.fail_count += 1
        
        # 更新历史成功率
        if self.total_uses > 0:
            self.historical_success_rate = self.success_count / self.total_uses
        
        # 记录RQS
        if rqs > 0:
            self.rqs_history.append(rqs)
            if len(self.rqs_history) > 100:  # 限制历史长度
                self.rqs_history = self.rqs_history[-100:]
        
        # 更新稳定性分数（基于RQS历史方差）
        if len(self.rqs_history) >= 2:
            variance = self._calculate_variance(self.rqs_history)
            self.stability_score = max(0.1, 1.0 - variance)  # 方差越小越稳定
        
        self.last_used = datetime.now()
        self.last_update_time = datetime.now()
    
    def _calculate_variance(self, values: List[float]) -> float:
        """计算方差"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def get_rqs_components(self) -> Dict[str, float]:
        """获取RQS各组件分数"""
        return {
            "historical_success": self.historical_success_rate,
            "stability": self.stability_score,
            "recency": self._calculate_recency_score(),
            "total_uses": self.total_uses
        }
    
    def _calculate_recency_score(self) -> float:
        """计算近期性分数（最近使用加分）"""
        hours_since_last_use = (datetime.now() - self.last_used).total_seconds() / 3600
        
        # 指数衰减：24小时内使用过得高分
        if hours_since_last_use < 1:
            return 1.0
        elif hours_since_last_use < 24:
            return 0.8
        elif hours_since_last_use < 168:  # 一周
            return 0.5
        else:
            return 0.2
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path_id": self.path_id,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "total_uses": self.total_uses,
            "historical_success_rate": self.historical_success_rate,
            "stability_score": self.stability_score,
            "last_used": self.last_used.isoformat(),
            "rqs_history_length": len(self.rqs_history),
            "avg_rqs": sum(self.rqs_history) / len(self.rqs_history) if self.rqs_history else 0.0
        }


@dataclass
class RQSResult:
    """RQS计算结果"""
    rqs: float = 0.0  # 推理质量评分 (0-1)
    components: Dict[str, float] = field(default_factory=dict)  # 各组件分数
    error: float = 0.0  # 误差 = 1 - RQS
    signal: ReasoningSignal = ReasoningSignal.UNCERTAIN
    path_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rqs": self.rqs,
            "components": self.components,
            "error": self.error,
            "signal": self.signal.value,
            "path_id": self.path_id
        }


class RQSSystem:
    """
    RQS（推理质量评分）系统
    
    核心：从"反应式纠错"升级到"统计性认知"
    解决：局部最优陷阱（Local optimum trap）
    
    RQS公式：
    RQS = 0.3 * belief_confidence +
          0.2 * consistency +
          0.2 * path_stability +
          0.2 * historical_success +
          0.1 * counterfactual_score
    """
    
    def __init__(self, neo4j_client=None):
        # Phase 2: Neo4j 客户端
        self._neo4j_client = neo4j_client

        # 推理统计存储
        self.reasoning_stats: Dict[str, ReasoningStats] = {}
        
        # 路径ID映射（推理轨迹 -> 路径ID）
        self.path_mapping: Dict[str, str] = {}  # trace_id -> path_id
        
        # 路径稳定性跟踪
        self.path_stability_history: Dict[str, List[float]] = defaultdict(list)
        
        # 反事实测试历史
        self.counterfactual_history: Dict[str, List[float]] = defaultdict(list)
        
        # 系统统计
        self.system_stats = {
            "total_reasonings": 0,
            "paths_tracked": 0,
            "avg_rqs": 0.0,
            "rqs_history": [],
            "stability_improvement": 0.0
        }

        # Phase 2: 尝试从图谱恢复历史统计
        self._load_from_graph()

        logger.info("RQS system initialized (neo4j=%s)",
                     "connected" if self._neo4j_client else "unavailable")
    
    def _generate_path_id(self, trace: ReasoningTrace) -> str:
        """
        生成路径ID
        
        基于推理轨迹的关键特征生成唯一ID
        相同推理模式 → 相同path_id
        """
        if not trace.edges:
            return "empty_path"
        
        # 基于边的关系和信念强度生成ID
        edge_features = []
        for edge in trace.edges:
            feature = f"{edge.relation}_{edge.belief_strength:.2f}"
            edge_features.append(feature)
        
        # 排序确保相同模式得到相同ID
        edge_features.sort()
        path_hash = hash("|".join(edge_features)) % 1000000
        
        return f"path_{abs(path_hash)}"
    
    def calculate_rqs(self, trace: ReasoningTrace, 
                     belief_confidence: float, 
                     consistency: float,
                     counterfactual_score: float = 0.5) -> RQSResult:
        """
        计算RQS（推理质量评分）
        
        RQS公式：
        RQS = 0.3 * belief_confidence +
              0.2 * consistency +
              0.2 * path_stability +
              0.2 * historical_success +
              0.1 * counterfactual_score
        """
        # 生成/获取路径ID
        path_id = self._generate_path_id(trace)
        trace.path_id = path_id
        
        # 获取或创建推理统计
        if path_id not in self.reasoning_stats:
            self.reasoning_stats[path_id] = ReasoningStats(path_id=path_id)
            self.system_stats["paths_tracked"] += 1
        
        stats = self.reasoning_stats[path_id]
        
        # 计算各组件分数
        # 1. belief_confidence (已有)
        belief_score = max(0.1, min(1.0, belief_confidence))
        
        # 2. consistency (已有)
        consistency_score = max(0.1, min(1.0, consistency))
        
        # 3. path_stability (新增核心)
        stability_score = stats.stability_score
        
        # 4. historical_success (关键)
        historical_success = stats.historical_success_rate
        
        # 5. counterfactual_score (已有)
        counterfactual_score = max(0.1, min(1.0, counterfactual_score))
        
        # 计算RQS
        rqs = (
            0.3 * belief_score +
            0.2 * consistency_score +
            0.2 * stability_score +
            0.2 * historical_success +
            0.1 * counterfactual_score
        )
        
        # 限制范围
        rqs = max(0.1, min(1.0, rqs))
        
        # 计算误差
        error = 1.0 - rqs
        
        # 生成信号
        if error < 0.2:
            signal = ReasoningSignal.GOOD
        elif error < 0.5:
            signal = ReasoningSignal.UNCERTAIN
        else:
            signal = ReasoningSignal.BAD
        
        # 创建结果
        result = RQSResult(
            rqs=rqs,
            components={
                "belief_confidence": belief_score,
                "consistency": consistency_score,
                "path_stability": stability_score,
                "historical_success": historical_success,
                "counterfactual_score": counterfactual_score
            },
            error=error,
            signal=signal,
            path_id=path_id
        )
        
        # 更新系统统计
        self._update_system_stats(rqs, path_id)
        
        return result
   
    
    def _update_system_stats(self, rqs: float, path_id: str):
        """更新系统统计"""
        self.system_stats["total_reasonings"] += 1
        self.system_stats["rqs_history"].append(rqs)
        
        # 限制历史长度
        if len(self.system_stats["rqs_history"]) > 1000:
            self.system_stats["rqs_history"] = self.system_stats["rqs_history"][-1000:]
        
        # 计算平均RQS
        if self.system_stats["rqs_history"]:
            self.system_stats["avg_rqs"] = sum(self.system_stats["rqs_history"]) / len(self.system_stats["rqs_history"])

        # Phase 2: 同步到图谱
        if path_id in self.reasoning_stats:
            self._sync_rqs_to_graph(path_id)
    
    def update_reasoning_stats(self, trace: ReasoningTrace, signal: ReasoningSignal, rqs: float):
        """更新推理统计"""
        if not trace.path_id:
            trace.path_id = self._generate_path_id(trace)
        
        path_id = trace.path_id
        
        # 确保统计存在
        if path_id not in self.reasoning_stats:
            self.reasoning_stats[path_id] = ReasoningStats(path_id=path_id)
            self.system_stats["paths_tracked"] += 1
        
        # 更新统计
        stats = self.reasoning_stats[path_id]
        stats.update(signal, rqs)
        
        # 记录路径映射
        self.path_mapping[trace.trace_id] = path_id

        # Phase 2: 同步到图谱
        self._sync_rqs_to_graph(path_id)
    
    def get_path_stability(self, path_id: str) -> float:
        """获取路径稳定性"""
        if path_id in self.reasoning_stats:
            return self.reasoning_stats[path_id].stability_score
        return 0.5  # 默认中等稳定性
    
    def get_historical_success_rate(self, path_id: str) -> float:
        """获取历史成功率"""
        if path_id in self.reasoning_stats:
            return self.reasoning_stats[path_id].historical_success_rate
        return 0.5  # 默认中等成功率
    
    def record_counterfactual_test(self, path_id: str, score: float):
        """记录反事实测试分数"""
        if path_id not in self.counterfactual_history:
            self.counterfactual_history[path_id] = []
        
        self.counterfactual_history[path_id].append(score)
        
        # 限制历史长度
        if len(self.counterfactual_history[path_id]) > 50:
            self.counterfactual_history[path_id] = self.counterfactual_history[path_id][-50:]
    
    def get_counterfactual_score(self, path_id: str) -> float:
        """获取反事实测试平均分数"""
        if path_id in self.counterfactual_history and self.counterfactual_history[path_id]:
            return sum(self.counterfactual_history[path_id]) / len(self.counterfactual_history[path_id])
        return 0.5  # 默认中等分数
    
    def apply_belief_correction_with_rqs(self, trace: ReasoningTrace, rqs_result: RQSResult) -> List[float]:
        """
        基于RQS的信念修正
        
        关键变化：
        旧系统：error = 1 - (confidence * consistency) → 短期评估
        新系统：error = 1 - RQS → 长期统计
        """
        belief_changes = []
        
        # 基于RQS信号确定修正系数
        signal = rqs_result.signal
        rqs = rqs_result.rqs
        
        if signal == ReasoningSignal.GOOD:
            # 好推理：基于RQS的强化（RQS越高，强化越多）
            correction_factor = 1.0 + (rqs * 0.1)  # 1.0-1.1
        elif signal == ReasoningSignal.UNCERTAIN:
            # 不确定：轻微调整
            correction_factor = 0.95 + (rqs * 0.05)  # 0.95-1.0
        else:
            # 坏推理：基于RQS的惩罚（RQS越低，惩罚越重）
            correction_factor = 0.7 + (rqs * 0.2)  # 0.7-0.9
        
        # 应用修正
        for edge in trace.edges:
            old_strength = edge.belief_strength
            
            # 应用修正系数
            new_strength = old_strength * correction_factor
            
            # 应用安全机制
            new_strength = self._apply_safety_mechanisms(new_strength, signal, rqs)
            
            # 更新信念强度
            edge.belief_strength = new_strength
            
            # 记录变化
            belief_changes.append(new_strength - old_strength)
        
        return belief_changes
    
    def _apply_safety_mechanisms(self, belief_strength: float, signal: ReasoningSignal, rqs: float) -> float:
        """
        应用安全机制（考虑RQS）
        
        关键改进：基于RQS调整安全机制强度
        """
        # 基础安全参数
        min_strength = 0.1
        max_strength = 1.0
        
        # 基于RQS调整恢复速率（RQS越高，恢复越快）
        recovery_rate = 0.01 * (1.0 + rqs)  # 0.01-0.02
        
        # 1. 防止过度惩罚
        belief_strength = max(min_strength, belief_strength)
        
        # 2. 防止过度强化
        belief_strength = min(max_strength, belief_strength)
        
        # 3. 恢复机制（基于RQS调整）
        if signal != ReasoningSignal.GOOD:
            belief_strength += recovery_rate
            belief_strength = min(max_strength, belief_strength)
        
        return belief_strength
    
    def update_learning_rate_with_rqs(self, lr: float, rqs: float, error: float) -> float:
        """
        基于RQS更新learning_rate
        
        关键改进：考虑长期可靠性，而不仅仅是单次错误
        """
        new_lr = lr
        
        # 基于RQS调整（RQS越高，可更激进）
        if rqs > 0.8:
            # 长期可靠 → 可更激进
            new_lr += 0.05
        elif rqs < 0.3:
            # 长期不可靠 → 更谨慎
            new_lr -= 0.1
        
        # 基于当前错误调整（保持反应性）
        if error > 0.5:
            new_lr -= 0.05  # 当前错误多 → 更谨慎
        elif error < 0.2:
            new_lr += 0.02  # 当前错误少 → 可稍激进
        
        # 限制范围
        new_lr = max(0.1, min(0.9, new_lr))
        
        return new_lr

    # ------------------------------------------------------------------
    # Phase 2: 图谱同步方法
    # ------------------------------------------------------------------

    def _sync_rqs_to_graph(self, path_id: str):
        """将单条 RQS 记录同步到图谱，Neo4j 不可用时静默降级。"""
        if not self._neo4j_client:
            return
        if path_id not in self.reasoning_stats:
            return
        try:
            stats = self.reasoning_stats[path_id]
            self._neo4j_client.upsert_rqs(stats.to_dict())
            logger.debug("RQS record synced to graph: %s", path_id)
        except Exception as exc:
            logger.warning("Failed to sync RQS %s to graph: %s", path_id, exc)

    def _sync_all_rqs_to_graph(self):
        """将所有 RQS 记录同步到图谱。"""
        if not self._neo4j_client:
            return
        for path_id in self.reasoning_stats:
            self._sync_rqs_to_graph(path_id)

    def _load_from_graph(self) -> bool:
        """
        启动时从图谱恢复历史 RQS 统计。

        Returns:
            True 表示成功恢复了至少一条记录，False 表示无法恢复。
        """
        if not self._neo4j_client:
            return False
        try:
            records = self._neo4j_client.get_all_rqs_records()
            if not records:
                return False

            for record in records:
                path_id = record.get("path_id")
                if not path_id:
                    continue
                stats = ReasoningStats(
                    path_id=path_id,
                    success_count=int(record.get("success_count", 0)),
                    fail_count=int(record.get("fail_count", 0)),
                    total_uses=int(record.get("total_uses", 0)),
                    historical_success_rate=float(record.get("historical_success_rate", 0.0)),
                    stability_score=float(record.get("stability_score", 0.5)),
                )
                # 恢复 avg_rqs 作为单个代表性样本
                avg_rqs = float(record.get("avg_rqs", 0.0))
                if avg_rqs > 0:
                    stats.rqs_history = [avg_rqs]
                # 恢复 last_used
                last_used_str = record.get("last_used", "")
                if last_used_str:
                    try:
                        stats.last_used = datetime.fromisoformat(last_used_str)
                    except (ValueError, TypeError):
                        pass

                self.reasoning_stats[path_id] = stats
                self.system_stats["paths_tracked"] += 1

            logger.info("Restored %d RQS records from graph", len(records))
            return len(records) > 0
        except Exception as exc:
            logger.warning("Failed to load RQS records from graph: %s", exc)
            return False

    # ------------------------------------------------------------------
    # 报告
    # ------------------------------------------------------------------

    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        # 计算路径统计
        total_paths = len(self.reasoning_stats)
        active_paths = 0
        stable_paths = 0
        unreliable_paths = 0
        
        avg_stability = 0.0
        avg_success_rate = 0.0
        
        for stats in self.reasoning_stats.values():
            if stats.total_uses >= 3:  # 至少使用3次才算活跃
                active_paths += 1
            
            if stats.stability_score > 0.7:
                stable_paths += 1
            
            if stats.historical_success_rate < 0.3:
                unreliable_paths += 1
            
            avg_stability += stats.stability_score
            avg_success_rate += stats.historical_success_rate
        
        if total_paths > 0:
            avg_stability /= total_paths
            avg_success_rate /= total_paths
        
        report = {
            "system_stats": {
                "total_reasonings": self.system_stats["total_reasonings"],
                "paths_tracked": total_paths,
                "active_paths": active_paths,
                "stable_paths": stable_paths,
                "unreliable_paths": unreliable_paths,
                "avg_rqs": self.system_stats["avg_rqs"],
                "avg_stability": avg_stability,
                "avg_success_rate": avg_success_rate
            },
            "rqs_distribution": self._get_rqs_distribution(),
            "top_paths": self._get_top_paths(5),
            "system_status": self._get_system_status()
        }
        
        return report
    
    def _get_rqs_distribution(self) -> Dict[str, int]:
        """获取RQS分布"""
        distribution = {
            "excellent": 0,  # RQS > 0.8
            "good": 0,       # RQS > 0.6
            "fair": 0,       # RQS > 0.4
            "poor": 0,       # RQS > 0.2
            "very_poor": 0   # RQS <= 0.2
        }
        
        for stats in self.reasoning_stats.values():
            if stats.rqs_history:
                avg_rqs = sum(stats.rqs_history) / len(stats.rqs_history)
                
                if avg_rqs > 0.8:
                    distribution["excellent"] += 1
                elif avg_rqs > 0.6:
                    distribution["good"] += 1
                elif avg_rqs > 0.4:
                    distribution["fair"] += 1
                elif avg_rqs > 0.2:
                    distribution["poor"] += 1
                else:
                    distribution["very_poor"] += 1
        
        return distribution
    
    def _get_top_paths(self, n: int = 5) -> List[Dict[str, Any]]:
        """获取top N路径"""
        paths_with_stats = []
        
        for path_id, stats in self.reasoning_stats.items():
            if stats.total_uses >= 3:  # 至少使用3次
                avg_rqs = sum(stats.rqs_history) / len(stats.rqs_history) if stats.rqs_history else 0.0
                
                paths_with_stats.append({
                    "path_id": path_id,
                    "total_uses": stats.total_uses,
                    "success_rate": stats.historical_success_rate,
                    "stability": stats.stability_score,
                    "avg_rqs": avg_rqs,
                    "last_used": stats.last_used.isoformat()
                })
        
        # 按使用次数排序
        paths_with_stats.sort(key=lambda x: x["total_uses"], reverse=True)
        
        return paths_with_stats[:n]
    
    def _get_system_status(self) -> str:
        """获取系统状态"""
        total_paths = len(self.reasoning_stats)
        
        if total_paths == 0:
            return "initializing"
        
        # 计算系统稳定性
        avg_stability = 0.0
        for stats in self.reasoning_stats.values():
            avg_stability += stats.stability_score
        
        avg_stability /= total_paths
        
        if avg_stability > 0.8:
            return "highly_stable"
        elif avg_stability > 0.6:
            return "stable"
        elif avg_stability > 0.4:
            return "moderate"
        else:
            return "unstable"
    
    def print_status(self):
        """打印当前状态"""
        report = self.get_system_report()
        
        if not report:
            return
        
        system_stats = report["system_stats"]
        rqs_dist = report["rqs_distribution"]
        top_paths = report["top_paths"]
        
        print(f"\n   📊 RQS系统状态:")
        print(f"      总推理次数: {system_stats['total_reasonings']}")
        print(f"      跟踪路径数: {system_stats['paths_tracked']} "
              f"(活跃: {system_stats['active_paths']})")
        print(f"      平均RQS: {system_stats['avg_rqs']:.3f}")
        print(f"      平均稳定性: {system_stats['avg_stability']:.3f}")
        print(f"      平均成功率: {system_stats['avg_success_rate']:.3f}")
        
        print(f"\n   📈 RQS分布:")
        print(f"      优秀 (RQS>0.8): {rqs_dist['excellent']}")
        print(f"      良好 (RQS>0.6): {rqs_dist['good']}")
        print(f"      一般 (RQS>0.4): {rqs_dist['fair']}")
        print(f"      较差 (RQS>0.2): {rqs_dist['poor']}")
        print(f"      很差 (RQS<=0.2): {rqs_dist['very_poor']}")
        
        print(f"\n   🏆 Top路径:")
        for i, path in enumerate(top_paths, 1):
            print(f"      {i}. {path['path_id']}: "
                  f"使用{path['total_uses']}次, "
                  f"成功率{path['success_rate']:.1%}, "
                  f"稳定性{path['stability']:.3f}")
        
        print(f"\n   🚀 系统状态: {report['system_status']}")
