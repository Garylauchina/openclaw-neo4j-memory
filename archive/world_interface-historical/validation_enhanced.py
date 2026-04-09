#!/usr/bin/env python3
"""
Validation Layer - 现实增强版
核心：external_feedback 成为验证核心
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime

from .environment import Action, ExecutionResult

@dataclass
class EnhancedValidationResult:
    """增强版验证结果"""
    action_id: str
    action_type: str
    
    # 验证分数（新公式）
    validation_score: float      # 综合验证分数
    internal_consistency: float  # 内部一致性
    goal_alignment: float        # 目标对齐度
    external_feedback: float     # ❗ 外部反馈（核心）
    
    # 现实指标
    success: bool                # 是否成功
    latency_ms: float            # 延迟
    data_quality: float          # 数据质量
    cost: float                  # 行动成本
    
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
            "action_type": self.action_type,
            "validation_scores": {
                "validation_score": self.validation_score,
                "internal_consistency": self.internal_consistency,
                "goal_alignment": self.goal_alignment,
                "external_feedback": self.external_feedback
            },
            "reality_metrics": {
                "success": self.success,
                "latency_ms": self.latency_ms,
                "data_quality": self.data_quality,
                "cost": self.cost
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
            "action_type": self.action_type,
            "validation_score": self.validation_score,
            "external_feedback": self.external_feedback,
            "success": self.success,
            "cost": self.cost,
            "is_valid": self.is_valid,
            "validation_passed": self.validation_passed,
            "has_high_risk": len(self.high_risk_factors) > 0,
            "requires_replan": self.requires_replan
        }

class EnhancedValidator:
    """增强版验证器"""
    
    def __init__(self):
        # 验证历史
        self.validation_history: List[EnhancedValidationResult] = []
        
        # 统计信息
        self.stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "avg_validation_score": 0.0,
            "avg_external_feedback": 0.0,
            "avg_cost": 0.0,
            "success_rate": 0.0
        }
    
    def validate(self, action: Action,
                execution_result: ExecutionResult,
                goal_description: str,
                context: Optional[Dict[str, Any]] = None) -> EnhancedValidationResult:
        """
        验证行动（现实增强版）
        
        ❗ 新公式：
        validation_score = 
            0.3 * internal_consistency
          + 0.3 * goal_alignment
          + 0.4 * ❗ external_feedback
        """
        import time
        start_time = time.time()
        
        # 1. 计算各组件分数
        internal_consistency = self._compute_internal_consistency(action, execution_result, context)
        goal_alignment = self._compute_goal_alignment(action, execution_result, goal_description, context)
        external_feedback = self._compute_external_feedback(execution_result, context)
        
        # 2. 计算综合验证分数（新公式）
        validation_score = self._compute_validation_score(
            internal_consistency, goal_alignment, external_feedback
        )
        
        # 3. 确定验证结果
        is_valid = self._determine_validity(execution_result, validation_score)
        validation_passed = validation_score >= 0.6  # 验证通过阈值
        
        # 4. 提取现实指标
        success = execution_result.status == "success"
        latency_ms = execution_result.latency_ms
        data_quality = self._extract_data_quality(execution_result)
        cost = self._compute_cost(execution_result)
        
        # 5. 风险评估
        risk_assessment, high_risk_factors = self._assess_risk(
            action, execution_result, validation_score, context
        )
        
        # 6. 生成建议
        recommendations, requires_replan = self._generate_recommendations(
            action, execution_result, validation_score, success, cost, context
        )
        
        # 7. 创建验证结果
        validation_time = time.time() - start_time
        
        result = EnhancedValidationResult(
            action_id=action.action_id,
            action_type=action.type,
            validation_score=validation_score,
            internal_consistency=internal_consistency,
            goal_alignment=goal_alignment,
            external_feedback=external_feedback,
            success=success,
            latency_ms=latency_ms,
            data_quality=data_quality,
            cost=cost,
            is_valid=is_valid,
            validation_passed=validation_passed,
            validation_details={
                "internal_consistency_details": self._get_internal_consistency_details(action, execution_result),
                "goal_alignment_details": self._get_goal_alignment_details(action, goal_description),
                "external_feedback_details": self._get_external_feedback_details(execution_result)
            },
            risk_assessment=risk_assessment,
            high_risk_factors=high_risk_factors,
            recommendations=recommendations,
            requires_replan=requires_replan,
            validation_time=validation_time
        )
        
        # 8. 更新历史记录和统计
        self.validation_history.append(result)
        self._update_stats(result)
        
        return result
    
    def _compute_internal_consistency(self, action: Action,
                                    execution_result: ExecutionResult,
                                    context: Optional[Dict[str, Any]]) -> float:
        """计算内部一致性"""
        consistency = 0.5  # 基础一致性
        
        # 1. 行动类型与结果的一致性
        if execution_result.status == "success":
            consistency += 0.2
        
        # 2. 参数与结果的一致性
        if execution_result.result:
            # 检查结果是否包含预期字段
            expected_signals = action.observable_signal.lower().split()
            result_str = str(execution_result.result).lower()
            
            matches = sum(1 for signal in expected_signals if signal in result_str)
            if expected_signals:
                signal_match = matches / len(expected_signals)
                consistency = consistency * 0.7 + signal_match * 0.3
        
        # 3. 执行时间一致性
        if execution_result.execution_time < action.timeout_seconds:
            time_consistency = 1.0 - (execution_result.execution_time / action.timeout_seconds)
            consistency = consistency * 0.8 + time_consistency * 0.2
        
        return max(0.0, min(1.0, consistency))
    
    def _compute_goal_alignment(self, action: Action,
                              execution_result: ExecutionResult,
                              goal_description: str,
                              context: Optional[Dict[str, Any]]) -> float:
        """计算目标对齐度"""
        alignment = 0.5  # 基础对齐度
        
        # 1. 预期效果匹配
        if action.expected_effect and execution_result.result:
            expected_words = set(action.expected_effect.lower().split())
            result_str = str(execution_result.result).lower()
            
            matches = sum(1 for word in expected_words if word in result_str)
            if expected_words:
                effect_match = matches / len(expected_words)
                alignment = alignment * 0.6 + effect_match * 0.4
        
        # 2. 目标描述匹配
        if goal_description:
            goal_words = set(goal_description.lower().split())
            action_words = set(action.target.lower().split())
            
            if goal_words and action_words:
                intersection = len(goal_words.intersection(action_words))
                union = len(goal_words.union(action_words))
                if union > 0:
                    goal_match = intersection / union
                    alignment = alignment * 0.7 + goal_match * 0.3
        
        return max(0.0, min(1.0, alignment))
    
    def _compute_external_feedback(self, execution_result: ExecutionResult,
                                 context: Optional[Dict[str, Any]]) -> float:
        """计算外部反馈（核心）"""
        
        # external_feedback 示例
        external_data = {
            "success": execution_result.status == "success",
            "latency": execution_result.latency_ms,
            "data_quality": self._extract_data_quality(execution_result)
        }
        
        # 转换公式
        success_score = 1.0 if external_data["success"] else 0.0
        data_quality_score = external_data["data_quality"]
        
        # 延迟惩罚（超过500ms开始惩罚）
        latency_penalty = 0.0
        if external_data["latency"] > 500:
            latency_penalty = min(0.3, (external_data["latency"] - 500) / 2000)
        
        # 计算外部反馈分数
        external_score = (
            0.5 * success_score +
            0.3 * data_quality_score -
            0.2 * latency_penalty
        )
        
        return max(0.0, min(1.0, external_score))
    
    def _compute_validation_score(self, internal_consistency: float,
                                goal_alignment: float,
                                external_feedback: float) -> float:
        """计算综合验证分数（新公式）"""
        # ❗ 新公式
        validation_score = (
            0.3 * internal_consistency +
            0.3 * goal_alignment +
            0.4 * external_feedback  # ❗ 外部反馈权重最高
        )
        
        return max(0.0, min(1.0, validation_score))
    
    def _determine_validity(self, execution_result: ExecutionResult,
                          validation_score: float) -> bool:
        """确定有效性"""
        # 基本有效性检查
        if execution_result.status != "success":
            return False
        
        if validation_score < 0.4:
            return False
        
        return True
    
    def _extract_data_quality(self, execution_result: ExecutionResult) -> float:
        """提取数据质量"""
        if not execution_result.result:
            return 0.0
        
        result = execution_result.result
        quality = 0.5  # 基础质量
        
        # 检查数据完整性
        if isinstance(result, dict):
            # 检查关键字段
            important_fields = ["status", "data", "result", "temperature", "location"]
            present_fields = sum(1 for field in important_fields if field in str(result).lower())
            
            completeness = present_fields / len(important_fields)
            quality = quality * 0.6 + completeness * 0.4
            
            # 检查数据丰富度
            if "data" in result and isinstance(result["data"], dict):
                data_size = len(str(result["data"]))
                if data_size > 50:
                    quality = min(1.0, quality + 0.2)
        
        return max(0.0, min(1.0, quality))
    
    def _compute_cost(self, execution_result: ExecutionResult) -> float:
        """计算行动成本"""
        # 与Environment中的成本计算保持一致
        latency_penalty = min(1.0, execution_result.latency_ms / 1000)
        resource_penalty = execution_result.resource_usage
        risk_penalty = execution_result.risk
        
        cost = (
            0.4 * latency_penalty +
            0.3 * resource_penalty +
            0.3 * risk_penalty
        )
        
        return cost
    
    def _assess_risk(self, action: Action,
                    execution_result: ExecutionResult,
                    validation_score: float,
                    context: Optional[Dict[str, Any]]) -> Tuple[Dict[str, float], List[str]]:
        """风险评估"""
        risk_factors = {}
        high_risk_factors = []
        
        # 1. 验证分数风险
        if validation_score < 0.4:
            risk_factors["low_validation_score"] = 1.0 - validation_score
            high_risk_factors.append("验证分数过低")
        
        # 2. 执行失败风险
        if execution_result.status != "success":
            risk_factors["execution_failure"] = 0.8
            high_risk_factors.append("执行失败")
        
        # 3. 高延迟风险
        if execution_result.latency_ms > 1000:
            risk_factors["high_latency"] = min(1.0, execution_result.latency_ms / 2000)
            high_risk_factors.append("高延迟")
        
        # 4. 高成本风险
        cost = self._compute_cost(execution_result)
        if cost > 0.5:
            risk_factors["high_cost"] = cost
            high_risk_factors.append("高成本")
        
        # 5. 数据质量风险
        data_quality = self._extract_data_quality(execution_result)
        if data_quality < 0.3:
            risk_factors["low_data_quality"] = 1.0 - data_quality
            high_risk_factors.append("数据质量低")
        
        return risk_factors, high_risk_factors
    
    def _generate_recommendations(self, action: Action,
                                execution_result: ExecutionResult,
                                validation_score: float,
                                success: bool,
                                cost: float,
                                context: Optional[Dict[str, Any]]) -> Tuple[List[str], bool]:
        """生成建议"""
        recommendations = []
        requires_replan = False
        
        # 1. 基于验证分数的建议
        if validation_score < 0.4:
            recommendations.append("验证分数过低，建议重新规划")
            requires_replan = True
        
        elif validation_score < 0.6:
            recommendations.append("验证分数中等，建议优化行动")
        
        # 2. 基于执行结果的建议
        if not success:
            recommendations.append("执行失败，建议检查连接器或参数")
            requires_replan = True
        
        # 3. 基于成本的建议
        if cost > 0.5:
            recommendations.append(f"行动成本过高: {cost:.3f}，建议优化效率")
        
        # 4. 基于延迟的建议
        if execution_result.latency_ms > 500:
            recommendations.append(f"延迟过高: {execution_result.latency_ms:.1f}ms，建议优化性能")
        
        # 5. 基于数据质量的建议
        data_quality = self._extract_data_quality(execution_result)
        if data_quality < 0.4:
            recommendations.append("数据质量不足，建议改进数据源或处理")
        
        return recommendations, requires_replan
    
    def _get_internal_consistency_details(self, action: Action,
                                        execution_result: ExecutionResult) -> Dict[str, Any]:
        """获取内部一致性详情"""
        return {
            "action_type": action.type,
            "execution_status": execution_result.status,
            "timeout_seconds": action.timeout_seconds,
            "actual_execution_time": execution_result.execution_time,
            "observable_signal": action.observable_signal,
            "result_contains_signal": action.observable_signal.lower() in str(execution_result.result).lower()
        }
    
    def _get_goal_alignment_details(self, action: Action,
                                  goal_description: str) -> Dict[str, Any]:
        """获取目标对齐详情"""
        return {
            "goal_description": goal_description,
            "expected_effect": action.expected_effect,
            "action_target": action.target,
            "goal_words": set(goal_description.lower().split()),
            "action_words": set(action.target.lower().split())
        }
    
    def _get_external_feedback_details(self, execution_result: ExecutionResult) -> Dict[str, Any]:
        """获取外部反馈详情"""
        return {
            "execution_status": execution_result.status,
            "latency_ms": execution_result.latency_ms,
            "resource_usage": execution_result.resource_usage,
            "risk": execution_result.risk,
            "data_quality": self._extract_data_quality(execution_result),
            "cost": self._compute_cost(execution_result)
        }
    
    def _update_stats(self, result: EnhancedValidationResult):
        """更新统计信息"""
        self.stats["total_validations"] += 1
        
        if result.validation_passed:
            self.stats["passed_validations"] += 1
        else:
            self.stats["failed_validations"] += 1
        
        # 更新平均分数
        total_score = sum(v.validation_score for v in self.validation_history)
        self.stats["avg_validation_score"] = total_score / len(self.validation_history)
        
        total_external = sum(v.external_feedback for v in self.validation_history)
        self.stats["avg_external_feedback"] = total_external / len(self.validation_history)
        
        total_cost = sum(v.cost for v in self.validation_history)
        self.stats["avg_cost"] = total_cost / len(self.validation_history)
        
        # 更新成功率
        successful = sum(1 for v in self.validation_history if v.success)
        self.stats["success_rate"] = successful / len(self.validation_history) if self.validation_history else 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "performance": self.stats,
            "history_size": len(self.validation_history),
            "recent_validations": [
                v.get_summary() for v in self.validation_history[-5:]
            ] if self.validation_history else []
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.validation_history = []
        self.stats = {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "avg_validation_score": 0.0,
            "avg_external_feedback": 0.0,
            "avg_cost": 0.0,
            "success_rate": 0.0
        }
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        perf = stats["performance"]
        
        print(f"   📊 增强版验证器状态:")
        print(f"      性能:")
        print(f"        总验证次数: {perf['total_validations']}")
        print(f"        通过验证: {perf['passed_validations']}")
        print(f"        失败验证: {perf['failed_validations']}")
        
        if perf['total_validations'] > 0:
            pass_rate = perf['passed_validations'] / perf['total_validations']
            print(f"        通过率: {pass_rate:.1%}")
            print(f"        平均验证分数: {perf['avg_validation_score']:.3f}")
            print(f"        平均外部反馈: {perf['avg_external_feedback']:.3f}")
            print(f"        平均成本: {perf['avg_cost']:.3f}")
            print(f"        成功率: {perf['success_rate']:.1%}")
        
        print(f"      历史大小: {stats['history_size']}")
        
        if stats['recent_validations']:
            print(f"      最近验证:")
            for i, val in enumerate(stats['recent_validations'][-3:]):
                print(f"        {i+1}. {val['action_type']}: 分数={val['validation_score']:.3f}, "
                      f"外部反馈={val['external_feedback']:.3f}, 成功={val['success']}")