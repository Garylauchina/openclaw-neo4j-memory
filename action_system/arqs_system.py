#!/usr/bin/env python3
"""
ARQS（Action-aware RQS）系统
核心：从RQS升级到ARQS：推理质量 + 行动后的真实反馈
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime, timedelta
import statistics

from .action_generator import Action, ActionType
from .action_executor import ExecutionResult, ExecutionStatus
from .action_validation import ValidationResult

@dataclass
class ARQSConfig:
    """ARQS配置"""
    # ARQS权重
    reasoning_quality_weight: float = 0.5   # 推理质量权重
    action_success_weight: float = 0.3      # 行动成功率权重
    long_term_outcome_weight: float = 0.2   # 长期结果权重
    
    # 时间衰减
    short_term_window_hours: int = 1        # 短期窗口（小时）
    medium_term_window_hours: int = 24      # 中期窗口（小时）
    long_term_window_hours: int = 168       # 长期窗口（小时，7天）
    
    # 衰减因子
    short_term_decay: float = 0.95          # 短期衰减
    medium_term_decay: float = 0.85         # 中期衰减
    long_term_decay: float = 0.70           # 长期衰减
    
    # 学习率
    arqs_learning_rate: float = 0.05        # ARQS学习率
    min_learning_rate: float = 0.01         # 最小学习率
    max_learning_rate: float = 0.10         # 最大学习率
    
    # 稳定性
    enable_stability_check: bool = True     # 启用稳定性检查
    stability_threshold: float = 0.7        # 稳定性阈值
    volatility_penalty: float = 0.2         # 波动性惩罚
    
    def validate(self):
        """验证配置"""
        weights = [
            self.reasoning_quality_weight,
            self.action_success_weight,
            self.long_term_outcome_weight
        ]
        
        total_weight = sum(weights)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"ARQS权重总和应为1.0，当前为{total_weight:.3f}")
        
        if not 0.0 < self.short_term_decay <= 1.0:
            raise ValueError(f"short_term_decay必须在0~1之间，当前为{self.short_term_decay}")
        
        if not 0.0 < self.medium_term_decay <= 1.0:
            raise ValueError(f"medium_term_decay必须在0~1之间，当前为{self.medium_term_decay}")
        
        if not 0.0 < self.long_term_decay <= 1.0:
            raise ValueError(f"long_term_decay必须在0~1之间，当前为{self.long_term_decay}")
        
        if not 0.0 < self.arqs_learning_rate <= 0.2:
            raise ValueError(f"arqs_learning_rate必须在0~0.2之间，当前为{self.arqs_learning_rate}")
        
        if not 0.0 <= self.min_learning_rate <= self.max_learning_rate:
            raise ValueError(f"min_learning_rate必须小于等于max_learning_rate")
        
        if not 0.0 <= self.stability_threshold <= 1.0:
            raise ValueError(f"stability_threshold必须在0~1之间，当前为{self.stability_threshold}")
        
        if not 0.0 <= self.volatility_penalty <= 0.5:
            raise ValueError(f"volatility_penalty必须在0~0.5之间，当前为{self.volatility_penalty}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "weights": {
                "reasoning_quality": self.reasoning_quality_weight,
                "action_success": self.action_success_weight,
                "long_term_outcome": self.long_term_outcome_weight
            },
            "time_windows": {
                "short_term_hours": self.short_term_window_hours,
                "medium_term_hours": self.medium_term_window_hours,
                "long_term_hours": self.long_term_window_hours
            },
            "decay_factors": {
                "short_term": self.short_term_decay,
                "medium_term": self.medium_term_decay,
                "long_term": self.long_term_decay
            },
            "learning": {
                "learning_rate": self.arqs_learning_rate,
                "min_learning_rate": self.min_learning_rate,
                "max_learning_rate": self.max_learning_rate
            },
            "stability": {
                "enable_stability_check": self.enable_stability_check,
                "stability_threshold": self.stability_threshold,
                "volatility_penalty": self.volatility_penalty
            }
        }

@dataclass
class ARQSEntry:
    """ARQS条目"""
    timestamp: datetime
    action_id: str
    action_type: ActionType
    
    # 组件分数
    reasoning_quality: float      # 推理质量（来自RQS）
    action_success: float         # 行动成功率
    long_term_outcome: float      # 长期结果预测
    
    # 计算分数
    arqs_score: float             # ARQS综合分数
    confidence: float             # 置信度
    
    # 上下文
    goal_description: str         # 目标描述
    validation_score: float       # 验证分数
    execution_status: str         # 执行状态
    
    # 元数据
    entry_id: str = field(default_factory=lambda: str(time.time()))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "scores": {
                "reasoning_quality": self.reasoning_quality,
                "action_success": self.action_success,
                "long_term_outcome": self.long_term_outcome,
                "arqs_score": self.arqs_score,
                "confidence": self.confidence
            },
            "context": {
                "goal_description": self.goal_description,
                "validation_score": self.validation_score,
                "execution_status": self.execution_status
            }
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type.value,
            "arqs_score": self.arqs_score,
            "confidence": self.confidence,
            "validation_score": self.validation_score
        }

class ARQSSystem:
    """ARQS系统"""
    
    def __init__(self, config: Optional[ARQSConfig] = None):
        self.config = config or ARQSConfig()
        self.config.validate()
        
        # ARQS历史记录
        self.arqs_history: List[ARQSEntry] = []
        
        # 当前ARQS状态
        self.current_arqs: float = 0.5  # 初始ARQS
        self.arqs_confidence: float = 0.5  # 初始置信度
        self.arqs_trend: str = "stable"  # ARQS趋势
        
        # 统计信息
        self.stats = {
            "total_entries": 0,
            "avg_arqs_score": 0.0,
            "arqs_volatility": 0.0,
            "success_rate": 0.0,
            "trend_distribution": {
                "improving": 0,
                "stable": 0,
                "declining": 0
            },
            "time_window_stats": {
                "short_term": {"count": 0, "avg_score": 0.0},
                "medium_term": {"count": 0, "avg_score": 0.0},
                "long_term": {"count": 0, "avg_score": 0.0}
            }
        }
    
    def update_arqs(self, action: Action,
                   execution_result: ExecutionResult,
                   validation_result: ValidationResult,
                   reasoning_quality: float,
                   goal_description: str,
                   context: Optional[Dict[str, Any]] = None) -> ARQSEntry:
        """
        更新ARQS
        
        Args:
            action: 行动对象
            execution_result: 执行结果
            validation_result: 验证结果
            reasoning_quality: 推理质量（来自RQS）
            goal_description: 目标描述
            context: 上下文信息
        
        Returns:
            ARQSEntry: ARQS条目
        """
        import time
        start_time = time.time()
        
        # 1. 计算组件分数
        action_success = self._compute_action_success(action, execution_result, validation_result)
        long_term_outcome = self._predict_long_term_outcome(action, execution_result, validation_result, context)
        
        # 2. 计算ARQS分数
        arqs_score = self._compute_arqs_score(
            reasoning_quality, action_success, long_term_outcome
        )
        
        # 3. 计算置信度
        confidence = self._compute_confidence(
            action, execution_result, validation_result, arqs_score, context
        )
        
        # 4. 创建ARQS条目
        entry = ARQSEntry(
            timestamp=datetime.now(),
            action_id=action.id,
            action_type=action.action_type,
            reasoning_quality=reasoning_quality,
            action_success=action_success,
            long_term_outcome=long_term_outcome,
            arqs_score=arqs_score,
            confidence=confidence,
            goal_description=goal_description,
            validation_score=validation_result.validation_score,
            execution_status=execution_result.status.value
        )
        
        # 5. 更新ARQS历史
        self.arqs_history.append(entry)
        
        # 6. 更新当前ARQS（带学习率）
        self._update_current_arqs(entry)
        
        # 7. 更新统计
        self._update_stats(entry)
        
        return entry
    
    def _compute_action_success(self, action: Action,
                              execution_result: ExecutionResult,
                              validation_result: ValidationResult) -> float:
        """计算行动成功率"""
        success_score = 0.0
        
        # 1. 执行状态
        if execution_result.status == ExecutionStatus.COMPLETED:
            success_score += 0.4
        elif execution_result.status == ExecutionStatus.FALLBACK:
            success_score += 0.2
        else:
            success_score += 0.1
        
        # 2. 验证结果
        if validation_result.validation_passed:
            success_score += 0.3
        else:
            success_score += 0.1
        
        # 3. 结果质量
        if execution_result.performance_metrics:
            quality = execution_result.performance_metrics.get("result_quality", 0.5)
            success_score += 0.2 * quality
        
        # 4. 重试惩罚
        if execution_result.retry_attempts > 0:
            retry_penalty = min(0.1, execution_result.retry_attempts * 0.05)
            success_score -= retry_penalty
        
        # 5. 降级惩罚
        if execution_result.used_fallback:
            success_score -= 0.1
        
        return max(0.0, min(1.0, success_score))
    
    def _predict_long_term_outcome(self, action: Action,
                                 execution_result: ExecutionResult,
                                 validation_result: ValidationResult,
                                 context: Optional[Dict[str, Any]]) -> float:
        """预测长期结果"""
        # 初始预测
        outcome_score = 0.5
        
        # 1. 基于验证分数
        outcome_score = outcome_score * 0.6 + validation_result.validation_score * 0.4
        
        # 2. 基于行动类型
        action_type_impact = {
            ActionType.API_CALL: 0.1,
            ActionType.DATA_RETRIEVAL: 0.2,
            ActionType.ANALYSIS: 0.3,
            ActionType.DECISION: 0.4,
            ActionType.EXECUTION: 0.5,
            ActionType.EXTERNAL_API: 0.3,
            ActionType.VALIDATION: 0.2,
            ActionType.REPORTING: 0.1
        }
        
        impact = action_type_impact.get(action.action_type, 0.1)
        outcome_score = outcome_score * 0.7 + impact * 0.3
        
        # 3. 基于风险
        if action.risk_level.value in ["high", "critical"]:
            # 高风险可能带来高回报，但也可能失败
            risk_adjustment = 0.3 if validation_result.validation_passed else -0.3
            outcome_score += risk_adjustment
        
        # 4. 基于实验框架
        if action.is_experiment:
            # 实验可能带来学习价值，即使失败
            learning_value = 0.2
            outcome_score = max(outcome_score, learning_value)
        
        # 5. 基于上下文
        if context:
            if "historical_success_rate" in context:
                historical_rate = context["historical_success_rate"]
                outcome_score = outcome_score * 0.6 + historical_rate * 0.4
            
            if "environment_stability" in context:
                stability = context["environment_stability"]
                outcome_score *= stability
        
        return max(0.0, min(1.0, outcome_score))
    
    def _compute_arqs_score(self, reasoning_quality: float,
                          action_success: float,
                          long_term_outcome: float) -> float:
        """计算ARQS分数"""
        # 加权组合
        arqs_score = (
            self.config.reasoning_quality_weight * reasoning_quality +
            self.config.action_success_weight * action_success +
            self.config.long_term_outcome_weight * long_term_outcome
        )
        
        # 应用稳定性检查
        if self.config.enable_stability_check:
            stability_adjustment = self._apply_stability_adjustment(arqs_score)
            arqs_score *= stability_adjustment
        
        return max(0.0, min(1.0, arqs_score))
    
    def _compute_confidence(self, action: Action,
                          execution_result: ExecutionResult,
                          validation_result: ValidationResult,
                          arqs_score: float,
                          context: Optional[Dict[str, Any]]) -> float:
        """计算置信度"""
        confidence = 0.5  # 基础置信度
        
        # 1. 验证分数影响
        confidence = confidence * 0.6 + validation_result.validation_score * 0.4
        
        # 2. 执行稳定性影响
        if execution_result.status == ExecutionStatus.COMPLETED:
            confidence += 0.1
        elif execution_result.status == ExecutionStatus.FAILED:
            confidence -= 0.2
        
        # 3. 历史一致性影响
        historical_consistency = self._check_historical_consistency(action, arqs_score)
        confidence = confidence * 0.7 + historical_consistency * 0.3
        
        # 4. 数据充分性影响
        data_sufficiency = min(1.0, len(self.arqs_history) / 10.0)  # 10个条目后达到充分
        confidence = confidence * 0.8 + data_sufficiency * 0.2
        
        return max(0.1, min(1.0, confidence))
    
    def _apply_stability_adjustment(self, current_score: float) -> float:
        """应用稳定性调整"""
        if len(self.arqs_history) < 3:
            return 1.0  # 数据不足，不调整
        
        # 计算近期ARQS的波动性
        recent_scores = [entry.arqs_score for entry in self.arqs_history[-5:]]
        
        if len(recent_scores) < 2:
            return 1.0
        
        # 计算标准差
        try:
            stdev = statistics.stdev(recent_scores)
        except statistics.StatisticsError:
            stdev = 0.0
        
        # 波动性惩罚
        volatility = min(1.0, stdev * 2.0)  # 标准化到0~1
        if volatility > self.config.volatility_penalty:
            adjustment = 1.0 - (volatility - self.config.volatility_penalty)
            return max(0.5, adjustment)
        
        return 1.0
    
    def _check_historical_consistency(self, action: Action,
                                    current_score: float) -> float:
        """检查历史一致性"""
        if not self.arqs_history:
            return 0.5  # 无历史记录
        
        # 查找相似行动的历史记录
        similar_entries = []
        for entry in self.arqs_history[-20:]:  # 最近20个条目
            if entry.action_type == action.action_type:
                similar_entries.append(entry)
        
        if not similar_entries:
            return 0.5
        
        # 计算平均分数和一致性
        historical_scores = [entry.arqs_score for entry in similar_entries]
        avg_score = sum(historical_scores) / len(historical_scores)
        
        # 一致性 = 1 - 与平均值的相对偏差
        if avg_score > 0:
            deviation = abs(current_score - avg_score) / avg_score
        else:
            deviation = abs(current_score - avg_score)
        
        consistency = 1.0 - min(1.0, deviation)
        
        return max(0.0, min(1.0, consistency))
    
    def _update_current_arqs(self, new_entry: ARQSEntry):
        """更新当前ARQS"""
        # 应用学习率
        learning_rate = self._compute_adaptive_learning_rate(new_entry)
        
        # 更新ARQS
        self.current_arqs = (
            self.current_arqs * (1 - learning_rate) +
            new_entry.arqs_score * learning_rate
        )
        
        # 更新置信度
        self.arqs_confidence = (
            self.arqs_confidence * 0.7 +
            new_entry.confidence * 0.3
        )
        
        # 更新趋势
        self._update_arqs_trend(new_entry)
    
    def _compute_adaptive_learning_rate(self, new_entry: ARQSEntry) -> float:
        """计算自适应学习率"""
        base_rate = self.config.arqs_learning_rate
        
        # 基于置信度调整
        confidence_factor = new_entry.confidence
        adjusted_rate = base_rate * confidence_factor
        
        # 基于历史波动性调整
        if len(self.arqs_history) >= 3:
            recent_scores = [entry.arqs_score for entry in self.arqs_history[-3:]]
            volatility = statistics.stdev(recent_scores) if len(recent_scores) >= 2 else 0.0
            
            # 高波动性时降低学习率
            if volatility > 0.2:
                adjusted_rate *= 0.5
        
        # 限制范围
        adjusted_rate = max(self.config.min_learning_rate, 
                          min(self.config.max_learning_rate, adjusted_rate))
        
        return adjusted_rate
    
    def _update_arqs_trend(self, new_entry: ARQSEntry):
        """更新ARQS趋势"""
        if len(self.arqs_history) < 2:
            self.arqs_trend = "stable"
            return
        
        # 获取最近几个条目
        recent_entries = self.arqs_history[-5:] if len(self.arqs_history) >= 5 else self.arqs_history
        
        if len(recent_entries) < 2:
            self.arqs_trend = "stable"
            return
        
        # 计算趋势
        scores = [entry.arqs_score for entry in recent_entries]
        
        # 简单趋势检测
        if len(scores) >= 3:
            # 计算斜率
            x = list(range(len(scores)))
            try:
                slope = self._compute_slope(x, scores)
                
                if slope > 0.05:
                    self.arqs_trend = "improving"
                elif slope < -0.05:
                    self.arqs_trend = "declining"
                else:
                    self.arqs_trend = "stable"
            except:
                self.arqs_trend = "stable"
        else:
            # 简单比较
            if scores[-1] > scores[0] + 0.1:
                self.arqs_trend = "improving"
            elif scores[-1] < scores[0] - 0.1:
                self.arqs_trend = "declining"
            else:
                self.arqs_trend = "stable"
    
    def _compute_slope(self, x: List[float], y: List[float]) -> float:
        """计算斜率（简单线性回归）"""
        n = len(x)
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x_i * x_i for x_i in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    def _update_stats(self, new_entry: ARQSEntry):
        """更新统计信息"""
        self.stats["total_entries"] += 1
        
        # 更新平均ARQS
        total_score = sum(entry.arqs_score for entry in self.arqs_history)
        self.stats["avg_arqs_score"] = total_score / len(self.arqs_history)
        
        # 更新成功率
        successful_entries = sum(1 for entry in self.arqs_history 
                               if entry.validation_score >= 0.6)
        self.stats["success_rate"] = successful_entries / len(self.arqs_history) if self.arqs_history else 0.0
        
        # 更新趋势分布
        self.stats["trend_distribution"][self.arqs_trend] += 1
        
        # 更新波动性
        if len(self.arqs_history) >= 2:
            scores = [entry.arqs_score for entry in self.arqs_history]
            try:
                self.stats["arqs_volatility"] = statistics.stdev(scores)
            except:
                self.stats["arqs_volatility"] = 0.0
        
        # 更新时间窗口统计
        self._update_time_window_stats()
    
    def _update_time_window_stats(self):
        """更新时间窗口统计"""
        now = datetime.now()
        
        # 重置统计
        self.stats["time_window_stats"] = {
            "short_term": {"count": 0, "avg_score": 0.0},
            "medium_term": {"count": 0, "avg_score": 0.0},
            "long_term": {"count": 0, "avg_score": 0.0}
        }
        
        if not self.arqs_history:
            return
        
        # 计算各时间窗口
        short_term_cutoff = now - timedelta(hours=self.config.short_term_window_hours)
        medium_term_cutoff = now - timedelta(hours=self.config.medium_term_window_hours)
        long_term_cutoff = now - timedelta(hours=self.config.long_term_window_hours)
        
        short_term_entries = []
        medium_term_entries = []
        long_term_entries = []
        
        for entry in self.arqs_history:
            if entry.timestamp >= short_term_cutoff:
                short_term_entries.append(entry)
            if entry.timestamp >= medium_term_cutoff:
                medium_term_entries.append(entry)
            if entry.timestamp >= long_term_cutoff:
                long_term_entries.append(entry)
        
        # 更新统计
        for window_name, entries in [
            ("short_term", short_term_entries),
            ("medium_term", medium_term_entries),
            ("long_term", long_term_entries)
        ]:
            if entries:
                avg_score = sum(entry.arqs_score for entry in entries) / len(entries)
                self.stats["time_window_stats"][window_name] = {
                    "count": len(entries),
                    "avg_score": avg_score
                }
    
    def get_arqs_report(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取ARQS报告"""
        # 计算各组件贡献
        if self.arqs_history:
            recent_entries = self.arqs_history[-10:] if len(self.arqs_history) >= 10 else self.arqs_history
            
            avg_reasoning = sum(e.reasoning_quality for e in recent_entries) / len(recent_entries)
            avg_action = sum(e.action_success for e in recent_entries) / len(recent_entries)
            avg_long_term = sum(e.long_term_outcome for e in recent_entries) / len(recent_entries)
        else:
            avg_reasoning = 0.5
            avg_action = 0.5
            avg_long_term = 0.5
        
        # 计算组件贡献百分比
        total_contribution = (
            self.config.reasoning_quality_weight * avg_reasoning +
            self.config.action_success_weight * avg_action +
            self.config.long_term_outcome_weight * avg_long_term
        )
        
        if total_contribution > 0:
            reasoning_contribution = (self.config.reasoning_quality_weight * avg_reasoning) / total_contribution
            action_contribution = (self.config.action_success_weight * avg_action) / total_contribution
            long_term_contribution = (self.config.long_term_outcome_weight * avg_long_term) / total_contribution
        else:
            reasoning_contribution = 0.33
            action_contribution = 0.33
            long_term_contribution = 0.34
        
        return {
            "config": self.config.to_dict(),
            "current_state": {
                "arqs_score": self.current_arqs,
                "arqs_confidence": self.arqs_confidence,
                "arqs_trend": self.arqs_trend,
                "total_entries": len(self.arqs_history)
            },
            "component_analysis": {
                "reasoning_quality": {
                    "score": avg_reasoning,
                    "weight": self.config.reasoning_quality_weight,
                    "contribution": reasoning_contribution
                },
                "action_success": {
                    "score": avg_action,
                    "weight": self.config.action_success_weight,
                    "contribution": action_contribution
                },
                "long_term_outcome": {
                    "score": avg_long_term,
                    "weight": self.config.long_term_outcome_weight,
                    "contribution": long_term_contribution
                }
            },
            "stats": self.stats,
            "recommendations": self._generate_arqs_recommendations(context)
        }
    
    def _generate_arqs_recommendations(self, context: Optional[Dict[str, Any]]) -> List[str]:
        """生成ARQS建议"""
        recommendations = []
        
        # 基于当前ARQS
        if self.current_arqs < 0.4:
            recommendations.append("ARQS分数过低，建议优化推理质量或行动成功率")
        elif self.current_arqs < 0.6:
            recommendations.append("ARQS分数中等，有改进空间")
        
        # 基于置信度
        if self.arqs_confidence < 0.4:
            recommendations.append("ARQS置信度低，建议收集更多数据")
        
        # 基于趋势
        if self.arqs_trend == "declining":
            recommendations.append("ARQS呈下降趋势，需要关注系统性能")
        elif self.arqs_trend == "improving":
            recommendations.append("ARQS呈上升趋势，系统性能在改善")
        
        # 基于波动性
        if self.stats["arqs_volatility"] > 0.2:
            recommendations.append("ARQS波动性较高，建议提高系统稳定性")
        
        # 基于成功率
        if self.stats["success_rate"] < 0.6:
            recommendations.append("行动成功率较低，建议优化行动执行和验证")
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.get_arqs_report()
    
    def reset_stats(self):
        """重置统计信息"""
        self.arqs_history = []
        self.current_arqs = 0.5
        self.arqs_confidence = 0.5
        self.arqs_trend = "stable"
        
        self.stats = {
            "total_entries": 0,
            "avg_arqs_score": 0.0,
            "arqs_volatility": 0.0,
            "success_rate": 0.0,
            "trend_distribution": {
                "improving": 0,
                "stable": 0,
                "declining": 0
            },
            "time_window_stats": {
                "short_term": {"count": 0, "avg_score": 0.0},
                "medium_term": {"count": 0, "avg_score": 0.0},
                "long_term": {"count": 0, "avg_score": 0.0}
            }
        }
    
    def print_status(self):
        """打印状态"""
        report = self.get_arqs_report()
        config = report["config"]
        current_state = report["current_state"]
        component_analysis = report["component_analysis"]
        stats = report["stats"]
        
        print(f"   📊 ARQS系统状态:")
        print(f"      配置:")
        print(f"        权重:")
        print(f"          推理质量: {config['weights']['reasoning_quality']:.2f}")
        print(f"          行动成功: {config['weights']['action_success']:.2f}")
        print(f"          长期结果: {config['weights']['long_term_outcome']:.2f}")
        
        print(f"        时间窗口:")
        print(f"          短期: {config['time_windows']['short_term_hours']}小时")
        print(f"          中期: {config['time_windows']['medium_term_hours']}小时")
        print(f"          长期: {config['time_windows']['long_term_hours']}小时")
        
        print(f"      当前状态:")
        print(f"        ARQS分数: {current_state['arqs_score']:.3f}")
        print(f"        ARQS置信度: {current_state['arqs_confidence']:.3f}")
        print(f"        ARQS趋势: {current_state['arqs_trend']}")
        print(f"        总条目数: {current_state['total_entries']}")
        
        print(f"      组件分析:")
        for component, analysis in component_analysis.items():
            print(f"        {component}:")
            print(f"          分数: {analysis['score']:.3f}")
            print(f"          权重: {analysis['weight']:.2f}")
            print(f"          贡献: {analysis['contribution']:.1%}")
        
        print(f"      统计:")
        print(f"        平均ARQS: {stats['stats']['avg_arqs_score']:.3f}")
        print(f"        ARQS波动性: {stats['stats']['arqs_volatility']:.3f}")
        print(f"        成功率: {stats['stats']['success_rate']:.1%}")
        
        print(f"      时间窗口统计:")
        for window, window_stats in stats['stats']['time_window_stats'].items():
            print(f"        {window}: {window_stats['count']}条目, 平均分数: {window_stats['avg_score']:.3f}")
        
        print(f"      建议:")
        for rec in report.get('recommendations', [])[:3]:
            print(f"        • {rec}")