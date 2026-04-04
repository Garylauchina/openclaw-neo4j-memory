#!/usr/bin/env python3
"""
完整闭环反馈系统 - 修复版
核心：让系统的认知对现实负责
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime, timedelta
import statistics

from .action_generator import Action, ActionType
from .action_executor import ExecutionResult, ExecutionStatus
from .action_validation import ValidationResult
from .arqs_system import ARQSEntry, ARQSSystem

@dataclass
class FeedbackConfig:
    """反馈系统配置"""
    # 反馈权重
    validation_weight: float = 0.4          # 验证权重
    execution_weight: float = 0.3           # 执行权重
    outcome_weight: float = 0.3             # 结果权重
    
    # 时间窗口
    feedback_window_hours: int = 24         # 反馈窗口（小时）
    learning_window_hours: int = 168        # 学习窗口（小时，7天）
    
    # 学习参数
    belief_update_rate: float = 0.1         # 信念更新率
    meta_learning_rate: float = 0.05        # 元学习率
    replan_threshold: float = 0.4           # 重规划阈值
    
    # 稳定性
    enable_feedback_stability: bool = True  # 启用反馈稳定性
    min_feedback_samples: int = 5           # 最小反馈样本数
    confidence_decay: float = 0.95          # 置信度衰减
    
    def validate(self):
        """验证配置"""
        weights = [
            self.validation_weight,
            self.execution_weight,
            self.outcome_weight
        ]
        
        total_weight = sum(weights)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"反馈权重总和应为1.0，当前为{total_weight:.3f}")
        
        if not 0.0 < self.belief_update_rate <= 0.3:
            raise ValueError(f"belief_update_rate必须在0~0.3之间，当前为{self.belief_update_rate}")
        
        if not 0.0 < self.meta_learning_rate <= 0.2:
            raise ValueError(f"meta_learning_rate必须在0~0.2之间，当前为{self.meta_learning_rate}")
        
        if not 0.0 <= self.replan_threshold <= 1.0:
            raise ValueError(f"replan_threshold必须在0~1之间，当前为{self.replan_threshold}")
        
        if not self.min_feedback_samples >= 1:
            raise ValueError(f"min_feedback_samples必须>=1，当前为{self.min_feedback_samples}")
        
        if not 0.0 < self.confidence_decay <= 1.0:
            raise ValueError(f"confidence_decay必须在0~1之间，当前为{self.confidence_decay}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "weights": {
                "validation": self.validation_weight,
                "execution": self.execution_weight,
                "outcome": self.outcome_weight
            },
            "time_windows": {
                "feedback_window_hours": self.feedback_window_hours,
                "learning_window_hours": self.learning_window_hours
            },
            "learning_parameters": {
                "belief_update_rate": self.belief_update_rate,
                "meta_learning_rate": self.meta_learning_rate,
                "replan_threshold": self.replan_threshold
            },
            "stability": {
                "enable_feedback_stability": self.enable_feedback_stability,
                "min_feedback_samples": self.min_feedback_samples,
                "confidence_decay": self.confidence_decay
            }
        }

@dataclass
class FeedbackEntry:
    """反馈条目"""
    timestamp: datetime
    action_id: str
    action_type: ActionType
    
    # 反馈分数
    feedback_score: float           # 综合反馈分数
    validation_feedback: float      # 验证反馈
    execution_feedback: float       # 执行反馈
    outcome_feedback: float         # 结果反馈
    
    # 学习更新
    belief_updates: Dict[str, float]  # 信念更新
    meta_learning_updates: Dict[str, float]  # 元学习更新
    
    # 决策
    requires_replan: bool           # 需要重规划
    replan_reason: str              # 重规划原因
    
    # 上下文
    goal_description: str           # 目标描述
    arqs_score: float               # ARQS分数
    validation_score: float         # 验证分数
    
    # 元数据
    entry_id: str = field(default_factory=lambda: str(time.time()))
    confidence: float = 0.5         # 置信度
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "feedback_scores": {
                "feedback_score": self.feedback_score,
                "validation_feedback": self.validation_feedback,
                "execution_feedback": self.execution_feedback,
                "outcome_feedback": self.outcome_feedback
            },
            "learning_updates": {
                "belief_updates": self.belief_updates,
                "meta_learning_updates": self.meta_learning_updates
            },
            "decision": {
                "requires_replan": self.requires_replan,
                "replan_reason": self.replan_reason
            },
            "context": {
                "goal_description": self.goal_description,
                "arqs_score": self.arqs_score,
                "validation_score": self.validation_score
            },
            "metadata": {
                "confidence": self.confidence
            }
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "action_type": self.action_type.value,
            "feedback_score": self.feedback_score,
            "requires_replan": self.requires_replan,
            "confidence": self.confidence
        }

class ClosedLoopFeedbackSystem:
    """闭环反馈系统"""
    
    def __init__(self, config: Optional[FeedbackConfig] = None):
        self.config = config or FeedbackConfig()
        self.config.validate()
        
        # 反馈历史
        self.feedback_history: List[FeedbackEntry] = []
        
        # 系统状态
        self.system_state = {
            "belief_strength": 0.5,          # 信念强度
            "learning_efficiency": 0.5,      # 学习效率
            "adaptation_speed": 0.5,         # 适应速度
            "stability_index": 0.5,          # 稳定性指数
            "replan_frequency": 0.0,         # 重规划频率
            "feedback_quality": 0.5          # 反馈质量
        }
        
        # 统计信息
        self.stats = {
            "total_feedbacks": 0,
            "avg_feedback_score": 0.0,
            "replan_count": 0,
            "replan_rate": 0.0,
            "belief_update_count": 0,
            "meta_learning_count": 0,
            "feedback_trend": "stable",
            "time_window_stats": {
                "recent": {"count": 0, "avg_score": 0.0},
                "learning": {"count": 0, "avg_score": 0.0}
            }
        }
    
    def process_feedback(self, action: Action,
                        execution_result: ExecutionResult,
                        validation_result: ValidationResult,
                        arqs_entry: ARQSEntry,
                        goal_description: str,
                        current_beliefs: Optional[Dict[str, Any]] = None,
                        current_meta_learning: Optional[Dict[str, Any]] = None,
                        context: Optional[Dict[str, Any]] = None) -> FeedbackEntry:
        """
        处理反馈
        
        Args:
            action: 行动对象
            execution_result: 执行结果
            validation_result: 验证结果
            arqs_entry: ARQS条目
            goal_description: 目标描述
            current_beliefs: 当前信念
            current_meta_learning: 当前元学习状态
            context: 上下文信息
        
        Returns:
            FeedbackEntry: 反馈条目
        """
        import time
        start_time = time.time()
        
        # 1. 计算反馈分数
        validation_feedback = self._compute_validation_feedback(validation_result)
        execution_feedback = self._compute_execution_feedback(execution_result)
        outcome_feedback = self._compute_outcome_feedback(action, execution_result, validation_result, context)
        
        # 2. 计算综合反馈分数
        feedback_score = self._compute_feedback_score(
            validation_feedback, execution_feedback, outcome_feedback
        )
        
        # 3. 计算学习更新
        belief_updates = self._compute_belief_updates(
            action, validation_result, arqs_entry, current_beliefs, context
        )
        
        meta_learning_updates = self._compute_meta_learning_updates(
            action, execution_result, validation_result, arqs_entry, current_meta_learning, context
        )
        
        # 4. 决策：是否需要重规划
        requires_replan, replan_reason = self._decide_replan(
            feedback_score, validation_result, execution_result, context
        )
        
        # 5. 计算置信度
        confidence = self._compute_confidence(
            action, execution_result, validation_result, feedback_score, context
        )
        
        # 6. 创建反馈条目
        feedback_entry = FeedbackEntry(
            timestamp=datetime.now(),
            action_id=action.id,
            action_type=action.action_type,
            feedback_score=feedback_score,
            validation_feedback=validation_feedback,
            execution_feedback=execution_feedback,
            outcome_feedback=outcome_feedback,
            belief_updates=belief_updates,
            meta_learning_updates=meta_learning_updates,
            requires_replan=requires_replan,
            replan_reason=replan_reason,
            goal_description=goal_description,
            arqs_score=arqs_entry.arqs_score,
            validation_score=validation_result.validation_score,
            confidence=confidence
        )
        
        # 7. 更新反馈历史
        self.feedback_history.append(feedback_entry)
        
        # 8. 更新系统状态
        self._update_system_state(feedback_entry)
        
        # 9. 更新统计
        self._update_stats(feedback_entry)
        
        return feedback_entry
    
    def _compute_validation_feedback(self, validation_result: ValidationResult) -> float:
        """计算验证反馈"""
        # 验证分数直接影响反馈
        validation_feedback = validation_result.validation_score
        
        # 考虑验证置信度
        if validation_result.high_risk_factors:
            # 高风险因素降低反馈
            risk_penalty = min(0.3, len(validation_result.high_risk_factors) * 0.1)
            validation_feedback -= risk_penalty
        
        # 考虑验证建议
        if validation_result.requires_replan:
            # 需要重规划表明验证发现问题
            validation_feedback *= 0.8
        
        return max(0.0, min(1.0, validation_feedback))
    
    def _compute_execution_feedback(self, execution_result: ExecutionResult) -> float:
        """计算执行反馈"""
        execution_feedback = 0.5  # 基础反馈
        
        # 1. 执行状态
        if execution_result.status == ExecutionStatus.COMPLETED:
            execution_feedback += 0.3
        elif execution_result.status == ExecutionStatus.FALLBACK:
            execution_feedback += 0.1
        else:
            execution_feedback -= 0.2
        
        # 2. 执行效率
        if execution_result.execution_time > 0:
            efficiency = min(1.0, 5.0 / execution_result.execution_time)  # 5秒内完成得满分
            execution_feedback += 0.2 * efficiency
        
        # 3. 重试惩罚
        if execution_result.retry_attempts > 0:
            retry_penalty = min(0.2, execution_result.retry_attempts * 0.05)
            execution_feedback -= retry_penalty
        
        # 4. 降级惩罚
        if execution_result.used_fallback:
            execution_feedback -= 0.1
        
        # 5. 结果质量
        if execution_result.performance_metrics:
            quality = execution_result.performance_metrics.get("result_quality", 0.5)
            execution_feedback += 0.1 * quality
        
        return max(0.0, min(1.0, execution_feedback))
    
    def _compute_outcome_feedback(self, action: Action,
                                execution_result: ExecutionResult,
                                validation_result: ValidationResult,
                                context: Optional[Dict[str, Any]]) -> float:
        """计算结果反馈"""
        outcome_feedback = 0.5  # 基础反馈
        
        # 1. 目标对齐度
        outcome_feedback = outcome_feedback * 0.6 + validation_result.goal_alignment * 0.4
        
        # 2. 长期影响预测
        if action.is_experiment:
            # 实验行动：即使失败也有学习价值
            learning_value = 0.3
            outcome_feedback = max(outcome_feedback, learning_value)
        
        # 3. 风险调整
        if action.risk_level.value in ["high", "critical"]:
            # 高风险行动：成功则高回报，失败则高惩罚
            risk_multiplier = 1.5 if validation_result.validation_passed else 0.5
            outcome_feedback *= risk_multiplier
        
        # 4. 上下文影响
        if context:
            if "environment_stability" in context:
                stability = context["environment_stability"]
                outcome_feedback *= stability
            
            if "historical_success" in context:
                historical = context["historical_success"]
                outcome_feedback = outcome_feedback * 0.7 + historical * 0.3
        
        return max(0.0, min(1.0, outcome_feedback))
    
    def _compute_feedback_score(self, validation_feedback: float,
                              execution_feedback: float,
                              outcome_feedback: float) -> float:
        """计算综合反馈分数"""
        # 加权组合
        feedback_score = (
            self.config.validation_weight * validation_feedback +
            self.config.execution_weight * execution_feedback +
            self.config.outcome_weight * outcome_feedback
        )
        
        # 应用稳定性检查
        if self.config.enable_feedback_stability:
            stability_adjustment = self._apply_feedback_stability(feedback_score)
            feedback_score *= stability_adjustment
        
        return max(0.0, min(1.0, feedback_score))
    
    def _compute_belief_updates(self, action: Action,
                              validation_result: ValidationResult,
                              arqs_entry: ARQSEntry,
                              current_beliefs: Optional[Dict[str, Any]],
                              context: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """计算信念更新"""
        belief_updates = {}
        
        if not current_beliefs:
            return belief_updates
        
        # 1. 基于验证结果的信念更新
        if validation_result.validation_passed:
            # 验证通过：强化相关信念
            belief_updates["validation_confidence"] = self.config.belief_update_rate
        else:
            # 验证失败：减弱相关信念
            belief_updates["validation_confidence"] = -self.config.belief_update_rate
        
        # 2. 基于ARQS的信念更新
        if arqs_entry.arqs_score > 0.7:
            # 高ARQS：强化系统能力信念
            belief_updates["system_capability"] = self.config.belief_update_rate * 0.5
        elif arqs_entry.arqs_score < 0.4:
            # 低ARQS：减弱系统能力信念
            belief_updates["system_capability"] = -self.config.belief_update_rate * 0.5
        
        # 3. 基于行动类型的信念更新
        action_type_key = f"action_type_{action.action_type.value}"
        if validation_result.validation_passed:
            belief_updates[action_type_key] = self.config.belief_update_rate
        else:
            belief_updates[action_type_key] = -self.config.belief_update_rate
        
        # 4. 基于风险的信念更新
        if action.risk_level.value in ["high", "critical"]:
            risk_key = f"risk_tolerance_{action.risk_level.value}"
            if validation_result.validation_passed:
                # 高风险成功：增加风险承受信念
                belief_updates[risk_key] = self.config.belief_update_rate * 0.3
            else:
                # 高风险失败：减少风险承受信念
                belief_updates[risk_key] = -self.config.belief_update_rate * 0.5
        
        return belief_updates
    
    def _compute_meta_learning_updates(self, action: Action,
                                     execution_result: ExecutionResult,
                                     validation_result: ValidationResult,
                                     arqs_entry: ARQSEntry,
                                     current_meta_learning: Optional[Dict[str, Any]],
                                     context: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """计算元学习更新"""
        meta_updates = {}
        
        if not current_meta_learning:
            return meta_updates
        
        # 1. 学习率调整
        if validation_result.validation_passed:
            # 验证通过：可能可以增加学习率
            meta_updates["learning_rate"] = self.config.meta_learning_rate * 0.1
        else:
            # 验证失败：可能需要降低学习率
            meta_updates["learning_rate"] = -self.config.meta_learning_rate * 0.2
        
        # 2. 重试策略调整
        if execution_result.retry_attempts > 0:
            # 有重试：调整重试策略
            if execution_result.status == ExecutionStatus.COMPLETED:
                # 重试成功：保持或轻微增强重试策略
                meta_updates["retry_strategy"] = self.config.meta_learning_rate * 0.05
            else:
                # 重试失败：减弱重试策略
                meta_updates["retry_strategy"] = -self.config.meta_learning_rate * 0.1
        
        # 3. 降级策略调整
        if execution_result.used_fallback:
            # 使用了降级：调整降级策略
            if execution_result.status == ExecutionStatus.FALLBACK:
                # 降级成功：增强降级策略
                meta_updates["fallback_strategy"] = self.config.meta_learning_rate * 0.1
            else:
                # 降级失败：减弱降级策略
                meta_updates["fallback_strategy"] = -self.config.meta_learning_rate * 0.15
        
        # 4. 验证阈值调整
        if validation_result.validation_score < self.config.replan_threshold:
            # 验证分数低于重规划阈值：可能需要调整验证阈值
            meta_updates["validation_threshold"] = -self.config.meta_learning_rate * 0.05
        
        # 5. ARQS权重调整
        # 基于各组件对ARQS的贡献调整权重
        component_contributions = {
            "reasoning_quality": arqs_entry.reasoning_quality,
            "action_success": arqs_entry.action_success,
            "long_term_outcome": arqs_entry.long_term_outcome
        }
        
        # 找出贡献最低的组件
        min_component = min(component_contributions.items(), key=lambda x: x[1])
        if min_component[1] < 0.4:
            # 组件贡献过低：可能需要调整权重
            meta_updates[f"arqs_weight_{min_component[0]}"] = self.config.meta_learning_rate * 0.05
        
        return meta_updates
    
    def _decide_replan(self, feedback_score: float,
                     validation_result: ValidationResult,
                     execution_result: ExecutionResult,
                     context: Optional[Dict[str, Any]]) -> Tuple[bool, str]:
        """决定是否需要重规划"""
        requires_replan = False
        replan_reason = ""
        
        # 1. 基于反馈分数
        if feedback_score < self.config.replan_threshold:
            requires_replan = True
            replan_reason = f"反馈分数过低: {feedback_score:.2f} < {self.config.replan_threshold}"
        
        # 2. 基于验证结果
        elif validation_result.requires_replan:
            requires_replan = True
            replan_reason = "验证层建议重规划"
        
        # 3. 基于执行结果
        elif execution_result.status == ExecutionStatus.FAILED:
            requires_replan = True
            replan_reason = "执行失败"
        
        # 4. 基于历史趋势
        elif self._check_historical_trend():
            requires_replan = True
            replan_reason = "历史趋势显示需要重规划"
        
        # 5. 基于上下文
        if context and context.get("force_replan", False):
            requires_replan = True
            replan_reason = "上下文强制重规划"
        
        return requires_replan, replan_reason
    
    def _compute_confidence(self, action: Action,
                          execution_result: ExecutionResult,
                          validation_result: ValidationResult,
                          feedback_score: float,
                          context: Optional[Dict[str, Any]]) -> float:
        """计算置信度"""
        confidence = 0.5  # 基础置信度
        
        # 1. 数据充分性
        sample_sufficiency = min(1.0, len(self.feedback_history) / self.config.min_feedback_samples)
        confidence = confidence * 0.7 + sample_sufficiency * 0.3
        
        # 2. 执行稳定性
        if execution_result.status == ExecutionStatus.COMPLETED:
            confidence += 0.1
        elif execution_result.status == ExecutionStatus.FAILED:
            confidence -= 0.2
        
        # 3. 验证一致性
        if validation_result.validation_passed:
            confidence += 0.1
        
        # 4. 反馈分数
        confidence = confidence * 0.6 + feedback_score * 0.4
        
        # 5. 历史一致性
        historical_consistency = self._check_feedback_consistency(feedback_score)
        confidence = confidence * 0.8 + historical_consistency * 0.2
        
        # 应用衰减
        confidence *= self.config.confidence_decay
        
        return max(0.1, min(1.0, confidence))
    
    def _apply_feedback_stability(self, current_score: float) -> float:
        """应用反馈稳定性"""
        if len(self.feedback_history) < 3:
            return 1.0  # 数据不足，不调整
        
        # 计算近期反馈的波动性
        recent_scores = [entry.feedback_score for entry in self.feedback_history[-5:]]
        
        if len(recent_scores) < 2:
            return 1.0
        
        # 计算标准差
        try:
            stdev = statistics.stdev(recent_scores)
        except statistics.StatisticsError:
            stdev = 0.0
        
        # 波动性调整
        volatility = min(1.0, stdev * 3.0)  # 标准化到0~1
        if volatility > 0.3:
            # 高波动性：降低当前分数的影响
            adjustment = 1.0 - (volatility - 0.3)
            return max(0.6, adjustment)
        
        return 1.0
    
    def _check_historical_trend(self) -> bool:
        """检查历史趋势"""
        if len(self.feedback_history) < 5:
            return False
        
        # 获取最近反馈分数
        recent_scores = [entry.feedback_score for entry in self.feedback_history[-5:]]
        
        # 检查下降趋势
        if len(recent_scores) >= 3:
            # 计算简单趋势
            if recent_scores[-1] < recent_scores[-2] < recent_scores[-3]:
                # 连续下降
                return True
            
            # 检查低分数比例
            low_scores = sum(1 for score in recent_scores if score < self.config.replan_threshold)
            if low_scores >= 3:  # 5个中有3个低分
                return True
        
        return False
    
    def _check_feedback_consistency(self, current_score: float) -> float:
        """检查反馈一致性"""
        if not self.feedback_history:
            return 0.5  # 无历史记录
        
        # 计算历史平均分数
        historical_scores = [entry.feedback_score for entry in self.feedback_history]
        avg_score = sum(historical_scores) / len(historical_scores)
        
        # 一致性 = 1 - 与平均值的相对偏差
        if avg_score > 0:
            deviation = abs(current_score - avg_score) / avg_score
        else:
            deviation = abs(current_score - avg_score)
        
        consistency = 1.0 - min(1.0, deviation)
        
        return max(0.0, min(1.0, consistency))
    
    def _update_system_state(self, feedback_entry: FeedbackEntry):
        """更新系统状态"""
        # 1. 更新信念强度
        if feedback_entry.belief_updates:
            update_sum = sum(abs(v) for v in feedback_entry.belief_updates.values())
            self.system_state["belief_strength"] = min(1.0, 
                self.system_state["belief_strength"] + update_sum * 0.1)
        
        # 2. 更新学习效率
        if feedback_entry.meta_learning_updates:
            self.system_state["learning_efficiency"] = min(1.0,
                self.system_state["learning_efficiency"] + 0.05)
        
        # 3. 更新适应速度
        adaptation_signal = 1.0 if feedback_entry.feedback_score > 0.6 else -0.5
        self.system_state["adaptation_speed"] = max(0.0, min(1.0,
            self.system_state["adaptation_speed"] + adaptation_signal * 0.1))
        
        # 4. 更新稳定性指数
        recent_scores = [entry.feedback_score for entry in self.feedback_history[-10:]]
        if len(recent_scores) >= 3:
            try:
                volatility = statistics.stdev(recent_scores)
                stability = 1.0 - min(1.0, volatility * 2.0)
                self.system_state["stability_index"] = (
                    self.system_state["stability_index"] * 0.8 + stability * 0.2
                )
            except:
                pass
        
        # 5. 更新重规划频率
        if feedback_entry.requires_replan:
            self.system_state["replan_frequency"] = min(1.0,
                self.system_state["replan_frequency"] + 0.1)
        else:
            self.system_state["replan_frequency"] = max(0.0,
                self.system_state["replan_frequency"] - 0.05)
        
        # 6. 更新反馈质量
        self.system_state["feedback_quality"] = (
            self.system_state["feedback_quality"] * 0.7 + 
            feedback_entry.feedback_score * 0.3
        )
    
    def _update_stats(self, feedback_entry: FeedbackEntry):
        """更新统计信息"""
        self.stats["total_feedbacks"] += 1
        
        # 更新平均反馈分数
        total_score = sum(entry.feedback_score for entry in self.feedback_history)
        self.stats["avg_feedback_score"] = total_score / len(self.feedback_history)
        
        # 更新重规划统计
        if feedback_entry.requires_replan:
            self.stats["replan_count"] += 1
        
        self.stats["replan_rate"] = self.stats["replan_count"] / self.stats["total_feedbacks"]
        
        # 更新学习统计
        if feedback_entry.belief_updates:
            self.stats["belief_update_count"] += 1
        
        if feedback_entry.meta_learning_updates:
            self.stats["meta_learning_count"] += 1
        
        # 更新趋势
        self._update_feedback_trend()
        
        # 更新时间窗口统计
        self._update_time_window_stats()
    
    def _update_feedback_trend(self):
        """更新反馈趋势"""
        if len(self.feedback_history) < 3:
            self.stats["feedback_trend"] = "stable"
            return
        
        recent_scores = [entry.feedback_score for entry in self.feedback_history[-3:]]
        
        # 简单趋势检测
        if recent_scores[-1] > recent_scores[0] + 0.1:
            self.stats["feedback_trend"] = "improving"
        elif recent_scores[-1] < recent_scores[0] - 0.1:
            self.stats["feedback_trend"] = "declining"
        else:
            self.stats["feedback_trend"] = "stable"
    
    def _update_time_window_stats(self):
        """更新时间窗口统计"""
        now = datetime.now()
        
        # 重置统计
        self.stats["time_window_stats"] = {
            "recent": {"count": 0, "avg_score": 0.0},
            "learning": {"count": 0, "avg_score": 0.0}
        }
        
        if not self.feedback_history:
            return
        
        # 计算时间窗口
        recent_cutoff = now - timedelta(hours=self.config.feedback_window_hours)
        learning_cutoff = now - timedelta(hours=self.config.learning_window_hours)
        
        recent_entries = []
        learning_entries = []
        
        for entry in self.feedback_history:
            if entry.timestamp >= recent_cutoff:
                recent_entries.append(entry)
            if entry.timestamp >= learning_cutoff:
                learning_entries.append(entry)
        
        # 更新统计
        for window_name, entries in [
            ("recent", recent_entries),
            ("learning", learning_entries)
        ]:
            if entries:
                avg_score = sum(entry.feedback_score for entry in entries) / len(entries)
                self.stats["time_window_stats"][window_name] = {
                    "count": len(entries),
                    "avg_score": avg_score
                }
    
    def get_feedback_report(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取反馈报告"""
        # 计算各组件平均分数
        if self.feedback_history:
            recent_entries = self.feedback_history[-10:] if len(self.feedback_history) >= 10 else self.feedback_history
            
            avg_validation = sum(e.validation_feedback for e in recent_entries) / len(recent_entries)
            avg_execution = sum(e.execution_feedback for e in recent_entries) / len(recent_entries)
            avg_outcome = sum(e.outcome_feedback for e in recent_entries) / len(recent_entries)
        else:
            avg_validation = 0.5
            avg_execution = 0.5
            avg_outcome = 0.5
        
        # 计算组件贡献百分比
        total_contribution = (
            self.config.validation_weight * avg_validation +
            self.config.execution_weight * avg_execution +
            self.config.outcome_weight * avg_outcome
        )
        
        if total_contribution > 0:
            validation_contribution = (self.config.validation_weight * avg_validation) / total_contribution
            execution_contribution = (self.config.execution_weight * avg_execution) / total_contribution
            outcome_contribution = (self.config.outcome_weight * avg_outcome) / total_contribution
        else:
            validation_contribution = 0.33
            execution_contribution = 0.33
            outcome_contribution = 0.34
        
        return {
            "config": self.config.to_dict(),
            "system_state": self.system_state,
            "component_analysis": {
                "validation_feedback": {
                    "score": avg_validation,
                    "weight": self.config.validation_weight,
                    "contribution": validation_contribution
                },
                "execution_feedback": {
                    "score": avg_execution,
                    "weight": self.config.execution_weight,
                    "contribution": execution_contribution
                },
                "outcome_feedback": {
                    "score": avg_outcome,
                    "weight": self.config.outcome_weight,
                    "contribution": outcome_contribution
                }
            },
            "stats": self.stats,
            "recommendations": self._generate_feedback_recommendations(context)
        }
    
    def _generate_feedback_recommendations(self, context: Optional[Dict[str, Any]]) -> List[str]:
        """生成反馈建议"""
        recommendations = []
        
        # 基于系统状态
        if self.system_state["feedback_quality"] < 0.4:
            recommendations.append("反馈质量过低，建议优化验证和执行过程")
        
        if self.system_state["stability_index"] < 0.4:
            recommendations.append("系统稳定性不足，建议减少波动性")
        
        if self.system_state["replan_frequency"] > 0.3:
            recommendations.append("重规划频率过高，建议优化规划质量")
        
        # 基于统计
        if self.stats["avg_feedback_score"] < 0.5:
            recommendations.append("平均反馈分数偏低，需要系统改进")
        
        if self.stats["replan_rate"] > 0.2:
            recommendations.append("重规划率过高，表明规划与执行脱节")
        
        if self.stats["feedback_trend"] == "declining":
            recommendations.append("反馈趋势下降，需要关注系统性能")
        
        # 基于时间窗口
        recent_stats = self.stats["time_window_stats"]["recent"]
        learning_stats = self.stats["time_window_stats"]["learning"]
        
        if recent_stats["count"] > 0 and learning_stats["count"] > 0:
            if recent_stats["avg_score"] < learning_stats["avg_score"] - 0.1:
                recommendations.append("近期表现下降，需要调整策略")
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.get_feedback_report()
    
    def reset_stats(self):
        """重置统计信息"""
        self.feedback_history = []
        
        self.system_state = {
            "belief_strength": 0.5,
            "learning_efficiency": 0.5,
            "adaptation_speed": 0.5,
            "stability_index": 0.5,
            "replan_frequency": 0.0,
            "feedback_quality": 0.5
        }
        
        self.stats = {
            "total_feedbacks": 0,
            "avg_feedback_score": 0.0,
            "replan_count": 0,
            "replan_rate": 0.0,
            "belief_update