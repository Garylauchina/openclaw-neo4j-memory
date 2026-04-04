#!/usr/bin/env python3
"""
Action Validation Layer（行动验证层）
核心：不是"有没有结果"，而是"这个结果对不对、值不值"
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime

from .action_generator import Action, ActionType
from .action_executor import ExecutionResult

@dataclass
class ValidationResult:
    """验证结果"""
    action_id: str
    action_type: ActionType
    
    # 验证分数
    validation_score: float  # 0~1
    goal_alignment: float    # 目标对齐度
    result_quality: float    # 结果质量
    side_effect_penalty: float  # 副作用惩罚
    consistency: float       # 一致性
    
    # 验证详情
    is_valid: bool
    validation_passed: bool
    validation_details: Dict[str, Any]
    
    # 风险评估
    risk_assessment: Dict[str, float]
    high_risk_factors: List[str]
    
    # 建议
    recommendations: List[str]
    requires_replan: bool
    
    # 元数据
    validation_time: float
    validated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "validation_score": self.validation_score,
            "component_scores": {
                "goal_alignment": self.goal_alignment,
                "result_quality": self.result_quality,
                "side_effect_penalty": self.side_effect_penalty,
                "consistency": self.consistency
            },
            "validation_outcome": {
                "is_valid": self.is_valid,
                "validation_passed": self.validation_passed
            },
            "validation_details": self.validation_details,
            "risk_assessment": self.risk_assessment,
            "high_risk_factors": self.high_risk_factors,
            "recommendations": self.recommendations,
            "requires_replan": self.requires_replan,
            "metadata": {
                "validation_time_ms": self.validation_time * 1000,
                "validated_at": self.validated_at.isoformat()
            }
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "validation_score": self.validation_score,
            "is_valid": self.is_valid,
            "validation_passed": self.validation_passed,
            "has_high_risk": len(self.high_risk_factors) > 0,
            "requires_replan": self.requires_replan
        }

@dataclass
class ActionValidationConfig:
    """行动验证配置"""
    # 验证权重
    goal_alignment_weight: float = 0.4   # 目标对齐度权重
    result_quality_weight: float = 0.2   # 结果质量权重
    side_effect_penalty_weight: float = 0.2  # 副作用惩罚权重
    consistency_weight: float = 0.2      # 一致性权重
    
    # 验证阈值
    validation_threshold: float = 0.6    # 验证通过阈值
    high_risk_threshold: float = 0.7     # 高风险阈值
    replan_threshold: float = 0.4        # 需要重规划阈值
    
    # 目标对齐评估
    enable_goal_alignment: bool = True   # 启用目标对齐评估
    goal_similarity_threshold: float = 0.5  # 目标相似度阈值
    
    # 结果质量评估
    enable_result_quality: bool = True   # 启用结果质量评估
    min_result_quality: float = 0.3      # 最小结果质量
    
    # 副作用评估
    enable_side_effect_check: bool = True  # 启用副作用检查
    max_side_effect_penalty: float = 0.5   # 最大副作用惩罚
    
    # 一致性评估
    enable_consistency_check: bool = True  # 启用一致性检查
    consistency_decay_factor: float = 0.9   # 一致性衰减因子
    
    def validate(self):
        """验证配置"""
        weights = [
            self.goal_alignment_weight,
            self.result_quality_weight,
            self.side_effect_penalty_weight,
            self.consistency_weight
        ]
        
        total_weight = sum(weights)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"验证权重总和应为1.0，当前为{total_weight:.3f}")
        
        if not 0.0 <= self.validation_threshold <= 1.0:
            raise ValueError(f"validation_threshold必须在0~1之间，当前为{self.validation_threshold}")
        
        if not 0.0 <= self.high_risk_threshold <= 1.0:
            raise ValueError(f"high_risk_threshold必须在0~1之间，当前为{self.high_risk_threshold}")
        
        if not 0.0 <= self.replan_threshold <= 1.0:
            raise ValueError(f"replan_threshold必须在0~1之间，当前为{self.replan_threshold}")
        
        if not 0.0 <= self.goal_similarity_threshold <= 1.0:
            raise ValueError(f"goal_similarity_threshold必须在0~1之间，当前为{self.goal_similarity_threshold}")
        
        if not 0.0 <= self.min_result_quality <= 1.0:
            raise ValueError(f"min_result_quality必须在0~1之间，当前为{self.min_result_quality}")
        
        if not 0.0 <= self.max_side_effect_penalty <= 1.0:
            raise ValueError(f"max_side_effect_penalty必须在0~1之间，当前为{self.max_side_effect_penalty}")
        
        if not 0.0 < self.consistency_decay_factor <= 1.0:
            raise ValueError(f"consistency_decay_factor必须在0~1之间，当前为{self.consistency_decay_factor}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "weights": {
                "goal_alignment": self.goal_alignment_weight,
                "result_quality": self.result_quality_weight,
                "side_effect_penalty": self.side_effect_penalty_weight,
                "consistency": self.consistency_weight
            },
            "thresholds": {
                "validation_threshold": self.validation_threshold,
                "high_risk_threshold": self.high_risk_threshold,
                "replan_threshold": self.replan_threshold
            },
            "goal_alignment": {
                "enabled": self.enable_goal_alignment,
                "similarity_threshold": self.goal_similarity_threshold
            },
            "result_quality": {
                "enabled": self.enable_result_quality,
                "min_result_quality": self.min_result_quality
            },
            "side_effect": {
                "enabled": self.enable_side_effect_check,
                "max_penalty": self.max_side_effect_penalty
            },
            "consistency": {
                "enabled": self.enable_consistency_check,
                "decay_factor": self.consistency_decay_factor
            }
        }

class ActionValidator:
    """行动验证器"""
    
    def __init__(self, config: Optional[ActionValidationConfig] = None):
        self.config = config or ActionValidationConfig()
        self.config.validate()
        
        # 历史验证记录
        self.validation_history: List[ValidationResult] = []
        
        # 统计信息
        self.stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "high_risk_validations": 0,
            "replan_recommendations": 0,
            "avg_validation_time": 0.0,
            "score_distribution": {
                "excellent": 0,  # >0.8
                "good": 0,       # 0.6~0.8
                "fair": 0,       # 0.4~0.6
                "poor": 0,       # 0.2~0.4
                "very_poor": 0   # <=0.2
            }
        }
    
    def validate_action(self, action: Action,
                       execution_result: ExecutionResult,
                       goal_description: str,
                       context: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        验证行动
        
        Args:
            action: 行动对象
            execution_result: 执行结果
            goal_description: 目标描述
            context: 上下文信息
        
        Returns:
            ValidationResult: 验证结果
        """
        import time
        start_time = time.time()
        
        # 1. 计算各组件分数
        goal_alignment = self._compute_goal_alignment(action, execution_result, goal_description, context)
        result_quality = self._compute_result_quality(action, execution_result, context)
        side_effect_penalty = self._compute_side_effect_penalty(action, execution_result, context)
        consistency = self._compute_consistency(action, execution_result, context)
        
        # 2. 计算综合验证分数
        validation_score = self._compute_validation_score(
            goal_alignment, result_quality, side_effect_penalty, consistency
        )
        
        # 3. 确定验证结果
        is_valid = self._determine_validity(validation_score, execution_result)
        validation_passed = validation_score >= self.config.validation_threshold
        
        # 4. 风险评估
        risk_assessment, high_risk_factors = self._assess_risk(
            action, execution_result, validation_score, context
        )
        
        # 5. 生成建议
        recommendations, requires_replan = self._generate_recommendations(
            action, execution_result, validation_score, risk_assessment, context
        )
        
        # 6. 创建验证结果
        validation_time = time.time() - start_time
        
        result = ValidationResult(
            action_id=action.id,
            action_type=action.action_type,
            validation_score=validation_score,
            goal_alignment=goal_alignment,
            result_quality=result_quality,
            side_effect_penalty=side_effect_penalty,
            consistency=consistency,
            is_valid=is_valid,
            validation_passed=validation_passed,
            validation_details={
                "goal_alignment_details": self._get_goal_alignment_details(action, goal_description),
                "result_quality_details": self._get_result_quality_details(execution_result),
                "side_effect_details": self._get_side_effect_details(action, execution_result),
                "consistency_details": self._get_consistency_details(action, context)
            },
            risk_assessment=risk_assessment,
            high_risk_factors=high_risk_factors,
            recommendations=recommendations,
            requires_replan=requires_replan,
            validation_time=validation_time
        )
        
        # 7. 更新历史记录和统计
        self.validation_history.append(result)
        self._update_stats(result, validation_time)
        
        return result
    
    def _compute_goal_alignment(self, action: Action,
                              execution_result: ExecutionResult,
                              goal_description: str,
                              context: Optional[Dict[str, Any]]) -> float:
        """计算目标对齐度"""
        if not self.config.enable_goal_alignment:
            return 0.5  # 默认值
        
        alignment_score = 0.0
        
        # 1. 行动目标与总体目标的相关性
        if goal_description and action.expected_outcome:
            goal_similarity = self._compute_text_similarity(
                action.expected_outcome, goal_description
            )
            alignment_score += 0.4 * goal_similarity
        
        # 2. 执行结果与预期结果的一致性
        if execution_result.result and action.expected_outcome:
            result_match = self._evaluate_result_match(
                execution_result.result, action.expected_outcome
            )
            alignment_score += 0.3 * result_match
        
        # 3. 行动对目标的推进程度
        goal_progress = self._estimate_goal_progress(action, execution_result, goal_description, context)
        alignment_score += 0.3 * goal_progress
        
        return max(0.0, min(1.0, alignment_score))
    
    def _compute_result_quality(self, action: Action,
                              execution_result: ExecutionResult,
                              context: Optional[Dict[str, Any]]) -> float:
        """计算结果质量"""
        if not self.config.enable_result_quality:
            return 0.5  # 默认值
        
        quality_score = 0.0
        
        # 1. 执行状态
        if execution_result.status.value == "completed":
            quality_score += 0.3
        elif execution_result.status.value == "failed":
            quality_score += 0.1
        
        # 2. 结果完整性
        if execution_result.result:
            completeness = self._evaluate_result_completeness(execution_result.result)
            quality_score += 0.3 * completeness
        
        # 3. 结果可信度
        if execution_result.performance_metrics:
            confidence = execution_result.performance_metrics.get("result_quality", 0.5)
            quality_score += 0.2 * confidence
        
        # 4. 执行效率
        if execution_result.execution_time > 0:
            efficiency = min(1.0, 10.0 / execution_result.execution_time)  # 10秒内完成得满分
            quality_score += 0.2 * efficiency
        
        # 确保不低于最小质量
        quality_score = max(self.config.min_result_quality, quality_score)
        
        return max(0.0, min(1.0, quality_score))
    
    def _compute_side_effect_penalty(self, action: Action,
                                   execution_result: ExecutionResult,
                                   context: Optional[Dict[str, Any]]) -> float:
        """计算副作用惩罚"""
        if not self.config.enable_side_effect_check:
            return 0.0  # 无惩罚
        
        penalty = 0.0
        
        # 1. 高风险行动的惩罚
        if action.risk_level.value in ["high", "critical"]:
            penalty += 0.3
        
        # 2. 执行错误的惩罚
        if execution_result.error:
            penalty += 0.2
        
        # 3. 资源消耗惩罚
        if execution_result.execution_time > 30:  # 超过30秒
            time_penalty = min(0.2, (execution_result.execution_time - 30) / 100)
            penalty += time_penalty
        
        # 4. 结果不一致惩罚
        if execution_result.result and action.expected_outcome:
            inconsistency = 1.0 - self._evaluate_result_match(
                execution_result.result, action.expected_outcome
            )
            penalty += 0.2 * inconsistency
        
        # 限制最大惩罚
        penalty = min(penalty, self.config.max_side_effect_penalty)
        
        return penalty
    
    def _compute_consistency(self, action: Action,
                           execution_result: ExecutionResult,
                           context: Optional[Dict[str, Any]]) -> float:
        """计算一致性"""
        if not self.config.enable_consistency_check:
            return 0.5  # 默认值
        
        consistency_score = 0.5  # 基础一致性
        
        # 1. 与历史行动的一致性
        historical_consistency = self._check_historical_consistency(action, context)
        consistency_score = consistency_score * 0.7 + historical_consistency * 0.3
        
        # 2. 与系统认知的一致性
        if context and "beliefs" in context:
            belief_consistency = self._check_belief_consistency(action, execution_result, context["beliefs"])
            consistency_score = consistency_score * 0.6 + belief_consistency * 0.4
        
        # 应用衰减
        consistency_score *= self.config.consistency_decay_factor
        
        return max(0.0, min(1.0, consistency_score))
    
    def _compute_validation_score(self, goal_alignment: float,
                                result_quality: float,
                                side_effect_penalty: float,
                                consistency: float) -> float:
        """计算综合验证分数"""
        # 加权组合
        weighted_score = (
            self.config.goal_alignment_weight * goal_alignment +
            self.config.result_quality_weight * result_quality +
            self.config.consistency_weight * consistency
        )
        
        # 应用副作用惩罚
        final_score = weighted_score - (self.config.side_effect_penalty_weight * side_effect_penalty)
        
        return max(0.0, min(1.0, final_score))
    
    def _determine_validity(self, validation_score: float,
                          execution_result: ExecutionResult) -> bool:
        """确定有效性"""
        # 基本有效性检查
        if execution_result.status.value != "completed":
            return False
        
        if validation_score < self.config.validation_threshold:
            return False
        
        return True
    
    def _assess_risk(self, action: Action,
                    execution_result: ExecutionResult,
                    validation_score: float,
                    context: Optional[Dict[str, Any]]) -> Tuple[Dict[str, float], List[str]]:
        """风险评估"""
        risk_factors = {}
        high_risk_factors = []
        
        # 1. 验证分数风险
        if validation_score < self.config.high_risk_threshold:
            risk_factors["low_validation_score"] = 1.0 - validation_score
            high_risk_factors.append("验证分数过低")
        
        # 2. 行动风险
        if action.risk_level.value == "critical":
            risk_factors["critical_action_risk"] = 0.9
            high_risk_factors.append("关键风险行动")
        elif action.risk_level.value == "high":
            risk_factors["high_action_risk"] = 0.7
            high_risk_factors.append("高风险行动")
        
        # 3. 执行错误风险
        if execution_result.error:
            risk_factors["execution_error"] = 0.8
            high_risk_factors.append("执行错误")
        
        # 4. 副作用风险
        side_effect_risk = self._compute_side_effect_penalty(action, execution_result, context)
        if side_effect_risk > 0.3:
            risk_factors["high_side_effects"] = side_effect_risk
            high_risk_factors.append("高副作用")
        
        # 5. 一致性风险
        consistency = self._compute_consistency(action, execution_result, context)
        if consistency < 0.4:
            risk_factors["low_consistency"] = 1.0 - consistency
            high_risk_factors.append("低一致性")
        
        return risk_factors, high_risk_factors
    
    def _generate_recommendations(self, action: Action,
                                execution_result: ExecutionResult,
                                validation_score: float,
                                risk_assessment: Dict[str, float],
                                context: Optional[Dict[str, Any]]) -> Tuple[List[str], bool]:
        """生成建议"""
        recommendations = []
        requires_replan = False
        
        # 1. 基于验证分数的建议
        if validation_score < self.config.replan_threshold:
            recommendations.append("验证分数过低，建议重新规划")
            requires_replan = True
        
        elif validation_score < self.config.validation_threshold:
            recommendations.append("验证分数未达到阈值，建议优化行动")
        
        # 2. 基于风险的建议
        if risk_assessment:
            if "critical_action_risk" in risk_assessment:
                recommendations.append("关键风险行动，需要人工确认")
            
            if "execution_error" in risk_assessment:
                recommendations.append("执行错误，建议检查执行环境")
            
            if "high_side_effects" in risk_assessment:
                recommendations.append("高副作用，建议调整行动参数")
        
        # 3. 基于执行结果的建议
        if execution_result.retry_attempts > 0:
            recommendations.append(f"经过{execution_result.retry_attempts}次重试，建议优化重试策略")
        
        if execution_result.used_fallback:
            recommendations.append("使用了降级行动，建议优化主行动")
        
        # 4. 基于行动类型的建议
        if action.action_type in [ActionType.EXECUTION, ActionType.EXTERNAL_API]:
            recommendations.append("真实世界行动，建议加强监控")
        
        if action.is_experiment:
            recommendations.append("实验行动，建议记录实验结果用于学习")
        
        return recommendations, requires_replan
    
    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 转换为词集
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        
        # 增强：考虑部分匹配
        partial_matches = sum(1 for w1 in words1 
                             for w2 in words2 
                             if w1 in w2 or w2 in w1)
        
        if partial_matches > 0:
            similarity = max(similarity, 0.3)
        
        return min(1.0, similarity)
    
    def _evaluate_result_match(self, actual_result: Any, expected_outcome: str) -> float:
        """评估结果匹配度"""
        if not actual_result or not expected_outcome:
            return 0.0
        
        # 将结果转换为字符串
        result_str = str(actual_result).lower()
        expected_str = expected_outcome.lower()
        
        # 简单关键词匹配
        expected_words = set(expected_str.split())
        result_words = set(result_str.split())
        
        if not expected_words:
            return 0.0
        
        # 计算匹配度
        matches = sum(1 for word in expected_words if word in result_str)
        match_ratio = matches / len(expected_words)
        
        return min(1.0, match_ratio)
    
    def _evaluate_result_completeness(self, result: Any) -> float:
        """评估结果完整性"""
        if not result:
            return 0.0
        
        # 简单完整性评估
        result_str = str(result)
        
        # 检查关键字段
        required_fields = ["status", "data", "result"]
        present_fields = sum(1 for field in required_fields if field in result_str.lower())
        
        completeness = present_fields / len(required_fields)
        
        # 检查数据长度
        if isinstance(result, dict):
            data_length = len(str(result.get("data", "")))
            if data_length > 10:
                completeness = min(1.0, completeness + 0.2)
        
        return completeness
    
    def _estimate_goal_progress(self, action: Action,
                              execution_result: ExecutionResult,
                              goal_description: str,
                              context: Optional[Dict[str, Any]]) -> float:
        """估计目标推进程度"""
        # 简单估计：基于行动类型和目标相关性
        progress = 0.0
        
        # 行动类型对目标的贡献
        action_contributions = {
            ActionType.API_CALL: 0.2,
            ActionType.DATA_RETRIEVAL: 0.3,
            ActionType.ANALYSIS: 0.4,
            ActionType.DECISION: 0.5,
            ActionType.EXECUTION: 0.6,
            ActionType.EXTERNAL_API: 0.3,
            ActionType.VALIDATION: 0.2,
            ActionType.REPORTING: 0.1
        }
        
        progress += action_contributions.get(action.action_type, 0.1)
        
        # 执行成功增加贡献
        if execution_result.status.value == "completed":
            progress += 0.2
        
        # 结果质量增加贡献
        if execution_result.performance_metrics:
            quality = execution_result.performance_metrics.get("result_quality", 0.5)
            progress += 0.1 * quality
        
        return min(1.0, progress)
    
    def _check_historical_consistency(self, action: Action,
                                    context: Optional[Dict[str, Any]]) -> float:
        """检查历史一致性"""
        if not self.validation_history:
            return 0.5  # 无历史记录，默认一致性
        
        # 查找相似历史行动
        similar_actions = []
        for historical in self.validation_history[-10:]:  # 最近10次验证
            if historical.action_type == action.action_type:
                similar_actions.append(historical)
        
        if not similar_actions:
            return 0.5
        
        # 计算平均验证分数
        avg_score = sum(h.validation_score for h in similar_actions) / len(similar_actions)
        
        # 一致性 = 1 - 与平均值的偏差
        deviation = abs(0.5 - avg_score)  # 假设理想一致性在0.5附近
        consistency = 1.0 - deviation
        
        return max(0.0, min(1.0, consistency))
    
    def _check_belief_consistency(self, action: Action,
                                execution_result: ExecutionResult,
                                beliefs: Dict[str, Any]) -> float:
        """检查信念一致性"""
        # 简化实现：检查行动结果是否与信念冲突
        consistency = 0.7  # 基础一致性
        
        # 如果有信念信息，进行更复杂的检查
        if "contradictions" in beliefs:
            contradictions = beliefs["contradictions"]
            if contradictions:
                # 行动可能增加矛盾
                consistency *= 0.8
        
        if "confidence" in beliefs:
            confidence = beliefs.get("confidence", 0.5)
            # 高置信度信念要求更高一致性
            if confidence > 0.8:
                consistency *= 1.1  # 轻微增强
            elif confidence < 0.3:
                consistency *= 0.9  # 轻微减弱
        
        return max(0.0, min(1.0, consistency))
    
    def _get_goal_alignment_details(self, action: Action, goal_description: str) -> Dict[str, Any]:
        """获取目标对齐详情"""
        similarity = self._compute_text_similarity(action.expected_outcome, goal_description)
        
        return {
            "goal_description": goal_description,
            "expected_outcome": action.expected_outcome,
            "similarity_score": similarity,
            "alignment_level": "high" if similarity > 0.7 else "medium" if similarity > 0.4 else "low"
        }
    
    def _get_result_quality_details(self, execution_result: ExecutionResult) -> Dict[str, Any]:
        """获取结果质量详情"""
        return {
            "execution_status": execution_result.status.value,
            "execution_time": execution_result.execution_time,
            "has_error": execution_result.error is not None,
            "error_message": execution_result.error,
            "performance_metrics": execution_result.performance_metrics
        }
    
    def _get_side_effect_details(self, action: Action, execution_result: ExecutionResult) -> Dict[str, Any]:
        """获取副作用详情"""
        return {
            "risk_level": action.risk_level.value,
            "requires_confirmation": action.requires_confirmation,
            "real_world_impact": action.real_world_impact,
            "retry_attempts": execution_result.retry_attempts,
            "used_fallback": execution_result.used_fallback
        }
    
    def _get_consistency_details(self, action: Action, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """获取一致性详情"""
        return {
            "action_type": action.action_type.value,
            "is_experiment": action.is_experiment,
            "has_historical_data": len(self.validation_history) > 0,
            "historical_count": len(self.validation_history),
            "context_provided": context is not None
        }
    
    def _update_stats(self, result: ValidationResult, validation_time: float):
        """更新统计信息"""
        self.stats["total_validations"] += 1
        
        if result.validation_passed:
            self.stats["passed_validations"] += 1
        else:
            self.stats["failed_validations"] += 1
        
        if result.high_risk_factors:
            self.stats["high_risk_validations"] += 1
        
        if result.requires_replan:
            self.stats["replan_recommendations"] += 1
        
        # 更新分数分布
        score = result.validation_score
        if score > 0.8:
            self.stats["score_distribution"]["excellent"] += 1
        elif score > 0.6:
            self.stats["score_distribution"]["good"] += 1
        elif score > 0.4:
            self.stats["score_distribution"]["fair"] += 1
        elif score > 0.2:
            self.stats["score_distribution"]["poor"] += 1
        else:
            self.stats["score_distribution"]["very_poor"] += 1
        
        # 更新平均验证时间
        self.stats["avg_validation_time"] = (
            (self.stats["avg_validation_time"] * (self.stats["total_validations"] - 1) + validation_time)
            / self.stats["total_validations"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_validations = self.stats["total_validations"]
        
        # 计算分布百分比
        score_distribution_pct = {}
        if total_validations > 0:
            for category, count in self.stats["score_distribution"].items():
                score_distribution_pct[category] = count / total_validations
        
        pass_rate = 0.0
        if total_validations > 0:
            pass_rate = self.stats["passed_validations"] / total_validations
        
        high_risk_rate = 0.0
        if total_validations > 0:
            high_risk_rate = self.stats["high_risk_validations"] / total_validations
        
        replan_rate = 0.0
        if total_validations > 0:
            replan_rate = self.stats["replan_recommendations"] / total_validations
        
        return {
            "config": self.config.to_dict(),
            "performance": {
                "total_validations": total_validations,
                "passed_validations": self.stats["passed_validations"],
                "failed_validations": self.stats["failed_validations"],
                "pass_rate": pass_rate,
                "high_risk_validations": self.stats["high_risk_validations"],
                "high_risk_rate": high_risk_rate,
                "replan_recommendations": self.stats["replan_recommendations"],
                "replan_rate": replan_rate,
                "avg_validation_time_ms": self.stats["avg_validation_time"] * 1000
            },
            "score_distribution": {
                "counts": self.stats["score_distribution"],
                "percentages": score_distribution_pct
            },
            "history_size": len(self.validation_history)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "high_risk_validations": 0,
            "replan_recommendations": 0,
            "avg_validation_time": 0.0,
            "score_distribution": {
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "poor": 0,
                "very_poor": 0
            }
        }
        self.validation_history = []
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        perf = stats["performance"]
        dist = stats["score_distribution"]
        
        print(f"   📊 Action Validator状态:")
        print(f"      配置:")
        print(f"        权重:")
        print(f"          目标对齐: {config['weights']['goal_alignment']:.2f}")
        print(f"          结果质量: {config['weights']['result_quality']:.2f}")
        print(f"          副作用惩罚: {config['weights']['side_effect_penalty']:.2f}")
        print(f"          一致性: {config['weights']['consistency']:.2f}")
        
        print(f"        阈值:")
        print(f"          验证阈值: {config['thresholds']['validation_threshold']:.2f}")
        print(f"          高风险阈值: {config['thresholds']['high_risk_threshold']:.2f}")
        print(f"          重规划阈值: {config['thresholds']['replan_threshold']:.2f}")
        
        print(f"      性能:")
        print(f"        总验证次数: {perf['total_validations']}")
        print(f"        通过验证: {perf['passed_validations']} ({perf['pass_rate']:.1%})")
        print(f"        高风险验证: {perf['high_risk_validations']} ({perf['high_risk_rate']:.1%})")
        print(f"        重规划建议: {perf['replan_recommendations']} ({perf['replan_rate']:.1%})")
        print(f"        平均验证时间: {perf['avg_validation_time_ms']:.2f}ms")
        
        print(f"      分数分布:")
        if perf['total_validations'] > 0:
            for category, count in dist["counts"].items():
                pct = dist["percentages"].get(category, 0)
                print(f"        {category}: {count} ({pct:.1%})")