#!/usr/bin/env python3
"""
Plan Evaluator（计划评估器）
核心：系统真正的"决策能力来源"，引入Projected RQS（未来推理质量预测）
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime

from .plan_generator import PlanStep, ActionType

@dataclass
class PlanEvaluationConfig:
    """计划评估配置"""
    # 评分权重
    expected_success_weight: float = 0.3
    cost_efficiency_weight: float = 0.2
    risk_score_weight: float = 0.2
    rqs_projection_weight: float = 0.2  # ❗ Projected RQS权重
    novelty_weight: float = 0.1
    
    # RQS投影配置
    rqs_projection_horizon: int = 5  # 预测步数
    rqs_decay_factor: float = 0.9    # 衰减因子
    enable_rqs_projection: bool = True
    
    # 风险配置
    max_acceptable_risk: float = 0.7
    risk_penalty_factor: float = 2.0
    
    # 成本配置
    time_cost_weight: float = 0.6
    resource_cost_weight: float = 0.4
    max_time_cost: float = 100.0  # 最大时间成本
    
    # 新颖性配置
    novelty_boost_threshold: float = 0.7
    novelty_penalty_threshold: float = 0.3
    
    def validate(self):
        """验证配置"""
        weights = [
            self.expected_success_weight,
            self.cost_efficiency_weight,
            self.risk_score_weight,
            self.rqs_projection_weight,
            self.novelty_weight
        ]
        
        total_weight = sum(weights)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"评分权重总和应为1.0，当前为{total_weight:.3f}")
        
        if not 1 <= self.rqs_projection_horizon <= 10:
            raise ValueError(f"rqs_projection_horizon必须在1~10之间，当前为{self.rqs_projection_horizon}")
        
        if not 0.0 < self.rqs_decay_factor <= 1.0:
            raise ValueError(f"rqs_decay_factor必须在0~1之间，当前为{self.rqs_decay_factor}")
        
        if not 0.0 <= self.max_acceptable_risk <= 1.0:
            raise ValueError(f"max_acceptable_risk必须在0~1之间，当前为{self.max_acceptable_risk}")
        
        if self.risk_penalty_factor < 1.0:
            raise ValueError(f"risk_penalty_factor必须大于等于1.0，当前为{self.risk_penalty_factor}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "weights": {
                "expected_success": self.expected_success_weight,
                "cost_efficiency": self.cost_efficiency_weight,
                "risk_score": self.risk_score_weight,
                "rqs_projection": self.rqs_projection_weight,
                "novelty": self.novelty_weight
            },
            "rqs_projection": {
                "horizon": self.rqs_projection_horizon,
                "decay_factor": self.rqs_decay_factor,
                "enabled": self.enable_rqs_projection
            },
            "risk": {
                "max_acceptable_risk": self.max_acceptable_risk,
                "penalty_factor": self.risk_penalty_factor
            },
            "cost": {
                "time_cost_weight": self.time_cost_weight,
                "resource_cost_weight": self.resource_cost_weight,
                "max_time_cost": self.max_time_cost
            },
            "novelty": {
                "boost_threshold": self.novelty_boost_threshold,
                "penalty_threshold": self.novelty_penalty_threshold
            }
        }

@dataclass
class PlanEvaluationResult:
    """计划评估结果"""
    plan_id: str
    plan_steps: List[PlanStep]
    
    # 评分组件
    expected_success_rate: float = 0.0
    cost_efficiency: float = 0.0
    risk_score: float = 0.0
    rqs_projection: float = 0.0  # ❗ Projected RQS
    novelty_score: float = 0.0
    
    # 综合评分
    total_score: float = 0.0
    confidence: float = 0.0
    
    # 详细分析
    step_analysis: List[Dict[str, Any]] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # 风险评估
    high_risk_steps: List[str] = field(default_factory=list)
    critical_path: List[str] = field(default_factory=list)
    
    # 元数据
    evaluation_time: float = 0.0
    evaluated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "plan_id": self.plan_id,
            "plan_summary": {
                "step_count": len(self.plan_steps),
                "actions": [step.action.value for step in self.plan_steps],
                "targets": [step.target for step in self.plan_steps]
            },
            "scores": {
                "expected_success_rate": self.expected_success_rate,
                "cost_efficiency": self.cost_efficiency,
                "risk_score": self.risk_score,
                "rqs_projection": self.rqs_projection,
                "novelty_score": self.novelty_score,
                "total_score": self.total_score,
                "confidence": self.confidence
            },
            "analysis": {
                "step_analysis": self.step_analysis,
                "strengths": self.strengths,
                "weaknesses": self.weaknesses,
                "recommendations": self.recommendations
            },
            "risk_assessment": {
                "high_risk_steps": self.high_risk_steps,
                "critical_path": self.critical_path
            },
            "metadata": {
                "evaluation_time_ms": self.evaluation_time * 1000,
                "evaluated_at": self.evaluated_at.isoformat()
            }
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "plan_id": self.plan_id,
            "step_count": len(self.plan_steps),
            "total_score": self.total_score,
            "confidence": self.confidence,
            "risk_score": self.risk_score,
            "rqs_projection": self.rqs_projection,
            "has_high_risk": len(self.high_risk_steps) > 0
        }

class PlanEvaluator:
    """计划评估器"""
    
    def __init__(self, config: Optional[PlanEvaluationConfig] = None):
        self.config = config or PlanEvaluationConfig()
        self.config.validate()
        
        # RQS模拟器（简化版）
        self.rqs_simulator = RQSSimulator()
        
        # 统计信息
        self.stats = {
            "total_plans_evaluated": 0,
            "total_steps_evaluated": 0,
            "avg_evaluation_time": 0.0,
            "score_distribution": {
                "excellent": 0,  # >0.8
                "good": 0,       # 0.6~0.8
                "fair": 0,       # 0.4~0.6
                "poor": 0,       # 0.2~0.4
                "very_poor": 0   # <=0.2
            },
            "risk_distribution": {
                "low": 0,        # <0.3
                "medium": 0,     # 0.3~0.6
                "high": 0,       # 0.6~0.8
                "critical": 0    # >0.8
            }
        }
    
    def evaluate_plan(self, plan_steps: List[PlanStep], 
                     context: Optional[Dict[str, Any]] = None) -> PlanEvaluationResult:
        """
        评估计划
        
        Args:
            plan_steps: 计划步骤列表
            context: 上下文信息
        
        Returns:
            PlanEvaluationResult: 评估结果
        """
        import time
        start_time = time.time()
        
        # 生成计划ID
        plan_id = f"plan_{int(time.time())}_{len(plan_steps)}"
        
        # 1. 分析每个步骤
        step_analysis = []
        for i, step in enumerate(plan_steps):
            step_analysis.append(self._analyze_step(step, i, context))
        
        # 2. 计算各组件分数
        expected_success_rate = self._compute_expected_success_rate(plan_steps, step_analysis, context)
        cost_efficiency = self._compute_cost_efficiency(plan_steps, step_analysis, context)
        risk_score = self._compute_risk_score(plan_steps, step_analysis, context)
        rqs_projection = self._compute_rqs_projection(plan_steps, step_analysis, context)
        novelty_score = self._compute_novelty_score(plan_steps, step_analysis, context)
        
        # 3. 计算综合评分
        total_score = self._compute_total_score(
            expected_success_rate,
            cost_efficiency,
            risk_score,
            rqs_projection,
            novelty_score
        )
        
        # 4. 计算置信度
        confidence = self._compute_confidence(step_analysis, total_score)
        
        # 5. 识别高风险步骤
        high_risk_steps = self._identify_high_risk_steps(plan_steps, step_analysis)
        
        # 6. 识别关键路径
        critical_path = self._identify_critical_path(plan_steps, step_analysis)
        
        # 7. 生成分析
        strengths, weaknesses, recommendations = self._generate_analysis(
            plan_steps, step_analysis, total_score, risk_score, context
        )
        
        # 8. 创建评估结果
        evaluation_time = time.time() - start_time
        
        result = PlanEvaluationResult(
            plan_id=plan_id,
            plan_steps=plan_steps,
            expected_success_rate=expected_success_rate,
            cost_efficiency=cost_efficiency,
            risk_score=risk_score,
            rqs_projection=rqs_projection,
            novelty_score=novelty_score,
            total_score=total_score,
            confidence=confidence,
            step_analysis=step_analysis,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            high_risk_steps=high_risk_steps,
            critical_path=critical_path,
            evaluation_time=evaluation_time
        )
        
        # 9. 更新统计
        self._update_stats(result, evaluation_time)
        
        return result
    
    def evaluate_multiple_plans(self, plans: List[List[PlanStep]],
                              context: Optional[Dict[str, Any]] = None) -> List[PlanEvaluationResult]:
        """
        评估多个计划
        
        Args:
            plans: 多个计划列表
            context: 上下文信息
        
        Returns:
            List[PlanEvaluationResult]: 评估结果列表
        """
        results = []
        
        for plan_steps in plans:
            result = self.evaluate_plan(plan_steps, context)
            results.append(result)
        
        return results
    
    def select_best_plan(self, evaluation_results: List[PlanEvaluationResult],
                        context: Optional[Dict[str, Any]] = None) -> Optional[PlanEvaluationResult]:
        """
        选择最佳计划
        
        Args:
            evaluation_results: 评估结果列表
            context: 上下文信息
        
        Returns:
            Optional[PlanEvaluationResult]: 最佳计划评估结果
        """
        if not evaluation_results:
            return None
        
        # 过滤高风险计划
        acceptable_results = []
        for result in evaluation_results:
            if result.risk_score <= self.config.max_acceptable_risk:
                acceptable_results.append(result)
        
        if not acceptable_results:
            # 如果没有可接受的风险计划，选择风险最低的
            acceptable_results = evaluation_results
        
        # 按总分排序
        sorted_results = sorted(acceptable_results, key=lambda x: x.total_score, reverse=True)
        
        return sorted_results[0] if sorted_results else None
    
    def _analyze_step(self, step: PlanStep, step_index: int, 
                     context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """分析单个步骤"""
        analysis = {
            "step_id": step.id,
            "step_index": step_index,
            "action": step.action.value,
            "target": step.target,
            "executable": step.executable,
            "timeout_seconds": step.timeout_seconds,
            "verification_criteria": step.verification_criteria,
            "success_metrics": step.success_metrics
        }
        
        # 计算步骤分数
        step_scores = {}
        
        # 1. 可执行性分数
        step_scores["executability"] = 1.0 if step.executable else 0.3
        
        # 2. 复杂度分数（基于action类型）
        complexity_scores = {
            ActionType.RETRIEVE_INFO: 0.3,
            ActionType.ANALYZE: 0.6,
            ActionType.COMPARE: 0.5,
            ActionType.DECIDE: 0.7,
            ActionType.EXECUTE: 0.8,
            ActionType.EVALUATE: 0.4,
            ActionType.ADAPT: 0.6,
            ActionType.REPORT: 0.2
        }
        step_scores["complexity"] = complexity_scores.get(step.action, 0.5)
        
        # 3. 风险分数
        risk_factors = {
            "timeout_risk": min(1.0, step.timeout_seconds / 60.0),  # 超时风险
            "dependency_risk": 0.2 if step.prerequisites else 0.0,  # 依赖风险
            "complexity_risk": step_scores["complexity"] * 0.8      # 复杂度风险
        }
        step_scores["risk"] = sum(risk_factors.values()) / len(risk_factors)
        
        # 4. 预期成功率
        step_scores["expected_success"] = 0.8 - (step_scores["risk"] * 0.5)
        
        # 5. 成本效率
        step_scores["cost_efficiency"] = 0.7 - (step_scores["complexity"] * 0.3)
        
        analysis["scores"] = step_scores
        
        return analysis
    
    def _compute_expected_success_rate(self, plan_steps: List[PlanStep],
                                     step_analysis: List[Dict[str, Any]],
                                     context: Optional[Dict[str, Any]]) -> float:
        """计算预期成功率"""
        if not plan_steps:
            return 0.0
        
        # 基于步骤成功率计算整体成功率
        step_success_rates = []
        for analysis in step_analysis:
            step_success_rates.append(analysis["scores"]["expected_success"])
        
        # 考虑步骤间的依赖关系
        # 简单模型：整体成功率 = 步骤成功率的几何平均
        import math
        if step_success_rates:
            product = 1.0
            for rate in step_success_rates:
                product *= rate
            
            geometric_mean = math.pow(product, 1.0 / len(step_success_rates))
            return geometric_mean
        
        return 0.5
    
    def _compute_cost_efficiency(self, plan_steps: List[PlanStep],
                               step_analysis: List[Dict[str, Any]],
                               context: Optional[Dict[str, Any]]) -> float:
        """计算成本效率"""
        if not plan_steps:
            return 0.0
        
        # 计算时间成本
        total_time_cost = 0.0
        for step in plan_steps:
            # 基于超时时间估算时间成本
            time_cost = min(1.0, step.timeout_seconds / self.config.max_time_cost)
            total_time_cost += time_cost
        
        avg_time_cost = total_time_cost / len(plan_steps) if plan_steps else 0.0
        
        # 计算资源成本（简化）
        resource_cost = 0.0
        for analysis in step_analysis:
            complexity = analysis["scores"]["complexity"]
            resource_cost += complexity * 0.1
        
        avg_resource_cost = resource_cost / len(step_analysis) if step_analysis else 0.0
        
        # 综合成本
        total_cost = (
            self.config.time_cost_weight * avg_time_cost +
            self.config.resource_cost_weight * avg_resource_cost
        )
        
        # 成本效率 = 1 - 归一化成本
        cost_efficiency = max(0.0, 1.0 - total_cost)
        
        return cost_efficiency
    
    def _compute_risk_score(self, plan_steps: List[PlanStep],
                          step_analysis: List[Dict[str, Any]],
                          context: Optional[Dict[str, Any]]) -> float:
        """计算风险分数"""
        if not plan_steps:
            return 0.0
        
        # 收集步骤风险
        step_risks = []
        for analysis in step_analysis:
            step_risks.append(analysis["scores"]["risk"])
        
        # 整体风险 = 最大步骤风险 * 步骤数量惩罚
        max_step_risk = max(step_risks) if step_risks else 0.0
        step_count_penalty = min(1.0, len(plan_steps) / 10.0)  # 步骤越多风险越高
        
        overall_risk = max_step_risk * (1.0 + step_count_penalty * 0.5)
        
        # 应用风险惩罚
        if overall_risk > self.config.max_acceptable_risk:
            risk_penalty = (overall_risk - self.config.max_acceptable_risk) * self.config.risk_penalty_factor
            overall_risk = min(1.0, overall_risk + risk_penalty)
        
        return min(1.0, overall_risk)
    
    def _compute_rqs_projection(self, plan_steps: List[PlanStep],
                              step_analysis: List[Dict[str, Any]],
                              context: Optional[Dict[str, Any]]) -> float:
        """计算Projected RQS（未来推理质量预测）"""
        if not self.config.enable_rqs_projection:
            return 0.5  # 默认值
        
        # 使用RQS模拟器预测
        projected_rqs = self.rqs_simulator.project_rqs(plan_steps, context)
        
        return projected_rqs
    
    def _compute_novelty_score(self, plan_steps: List[PlanStep],
                             step_analysis: List[Dict[str, Any]],
                             context: Optional[Dict[str, Any]]) -> float:
        """计算新颖性分数"""
        if not plan_steps:
            return 0.5
        
        # 分析行动类型分布
        action_counts = {}
        for step in plan_steps:
            action_type = step.action.value
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        # 计算多样性
        total_steps = len(plan_steps)
        diversity = 0.0
        if total_steps > 0:
            # 使用香农熵计算多样性
            import math
            entropy = 0.0
            for count in action_counts.values():
                probability = count / total_steps
                if probability > 0:
                    entropy -= probability * math.log2(probability)
            
            # 归一化到0~1
            max_entropy = math.log2(len(ActionType))
            diversity = entropy / max_entropy if max_entropy > 0 else 0.0
        
        # 计算创新性（基于行动组合）
        innovation = 0.0
        if len(action_counts) >= 3:
            innovation = 0.7
        elif len(action_counts) >= 2:
            innovation = 0.4
        else:
            innovation = 0.1
        
        # 综合新颖性
        novelty_score = (diversity * 0.6 + innovation * 0.4)
        
        # 应用新颖性阈值
        if novelty_score > self.config.novelty_boost_threshold:
            novelty_score = min(1.0, novelty_score * 1.2)  # 新颖性奖励
        elif novelty_score < self.config.novelty_penalty_threshold:
            novelty_score = max(0.0, novelty_score * 0.8)  # 新颖性惩罚
        
        return novelty_score
    
    def _compute_total_score(self, expected_success_rate: float,
                           cost_efficiency: float,
                           risk_score: float,
                           rqs_projection: float,
                           novelty_score: float) -> float:
        """计算综合评分"""
        # 应用权重
        weighted_success = expected_success_rate * self.config.expected_success_weight
        weighted_cost = cost_efficiency * self.config.cost_efficiency_weight
        weighted_risk = (1.0 - risk_score) * self.config.risk_score_weight  # 风险是负向的
        weighted_rqs = rqs_projection * self.config.rqs_projection_weight
        weighted_novelty = novelty_score * self.config.novelty_weight
        
        # 综合评分
        total_score = (
            weighted_success +
            weighted_cost +
            weighted_risk +
            weighted_rqs +
            weighted_novelty
        )
        
        return max(0.0, min(1.0, total_score))
    
    def _compute_confidence(self, step_analysis: List[Dict[str, Any]],
                          total_score: float) -> float:
        """计算置信度"""
        if not step_analysis:
            return 0.5
        
        # 基于步骤可执行性
        executability_scores = [analysis["scores"]["executability"] for analysis in step_analysis]
        avg_executability = sum(executability_scores) / len(executability_scores)
        
        # 基于验证标准
        verification_coverage = 0.0
        for analysis in step_analysis:
            if analysis["verification_criteria"]:
                verification_coverage += 0.2
            if analysis["success_metrics"]:
                verification_coverage += 0.1
        
        verification_coverage = min(1.0, verification_coverage / len(step_analysis))
        
        # 综合置信度
        confidence = (
            avg_executability * 0.4 +
            verification_coverage * 0.3 +
            total_score * 0.3
        )
        
        return max(0.0, min(1.0, confidence))
    
    def _identify_high_risk_steps(self, plan_steps: List[PlanStep],
                                step_analysis: List[Dict[str, Any]]) -> List[str]:
        """识别高风险步骤"""
        high_risk_steps = []
        risk_threshold = 0.6  # 高风险阈值
        
        for i, analysis in enumerate(step_analysis):
            risk_score = analysis["scores"]["risk"]
            if risk_score > risk_threshold:
                step = plan_steps[i]
                high_risk_steps.append({
                    "step_id": step.id,
                    "step_index": i,
                    "action": step.action.value,
                    "risk_score": risk_score,
                    "reason": self._get_risk_reason(analysis)
                })
        
        return high_risk_steps
    
    def _get_risk_reason(self, step_analysis: Dict[str, Any]) -> str:
        """获取风险原因"""
        risk_score = step_analysis["scores"]["risk"]
        
        if risk_score > 0.8:
            return "风险极高：步骤复杂且依赖多"
        elif risk_score > 0.6:
            return "高风险：步骤复杂或超时风险高"
        elif risk_score > 0.4:
            return "中等风险：有一定执行难度"
        else:
            return "低风险：步骤相对简单"
    
    def _identify_critical_path(self, plan_steps: List[PlanStep],
                              step_analysis: List[Dict[str, Any]]) -> List[str]:
        """识别关键路径"""
        critical_path = []
        
        # 简单实现：选择复杂度最高的3个步骤
        step_complexities = []
        for i, analysis in enumerate(step_analysis):
            complexity = analysis["scores"]["complexity"]
            step_complexities.append((i, complexity))
        
        # 按复杂度排序
        step_complexities.sort(key=lambda x: x[1], reverse=True)
        
        # 选择前3个作为关键路径
        for i, (step_index, _) in enumerate(step_complexities[:3]):
            step = plan_steps[step_index]
            critical_path.append({
                "step_id": step.id,
                "step_index": step_index,
                "action": step.action.value,
                "position": i + 1
            })
        
        return critical_path
    
    def _generate_analysis(self, plan_steps: List[PlanStep],
                         step_analysis: List[Dict[str, Any]],
                         total_score: float,
                         risk_score: float,
                         context: Optional[Dict[str, Any]]) -> Tuple[List[str], List[str], List[str]]:
        """生成分析"""
        strengths = []
        weaknesses = []
        recommendations = []
        
        # 分析优势
        if total_score > 0.7:
            strengths.append("计划整体评分良好")
        
        executable_steps = sum(1 for analysis in step_analysis if analysis["scores"]["executability"] > 0.8)
        if executable_steps == len(plan_steps):
            strengths.append("所有步骤都可执行")
        elif executable_steps >= len(plan_steps) * 0.8:
            strengths.append("大部分步骤可执行")
        
        # 分析弱点
        if risk_score > 0.6:
            weaknesses.append("整体风险较高")
        
        low_executability_steps = sum(1 for analysis in step_analysis if analysis["scores"]["executability"] < 0.5)
        if low_executability_steps > 0:
            weaknesses.append(f"{low_executability_steps}个步骤可执行性低")
        
        # 生成建议
        if risk_score > 0.6:
            recommendations.append("考虑降低高风险步骤的复杂度或增加验证")
        
        if total_score < 0.5:
            recommendations.append("建议重新设计计划，提高可执行性和成功率")
        
        if len(plan_steps) > 8:
            recommendations.append("计划步骤较多，考虑简化或分阶段执行")
        
        return strengths, weaknesses, recommendations
    
    def _update_stats(self, result: PlanEvaluationResult, evaluation_time: float):
        """更新统计信息"""
        self.stats["total_plans_evaluated"] += 1
        self.stats["total_steps_evaluated"] += len(result.plan_steps)
        
        # 更新分数分布
        total_score = result.total_score
        if total_score > 0.8:
            self.stats["score_distribution"]["excellent"] += 1
        elif total_score > 0.6:
            self.stats["score_distribution"]["good"] += 1
        elif total_score > 0.4:
            self.stats["score_distribution"]["fair"] += 1
        elif total_score > 0.2:
            self.stats["score_distribution"]["poor"] += 1
        else:
            self.stats["score_distribution"]["very_poor"] += 1
        
        # 更新风险分布
        risk_score = result.risk_score
        if risk_score < 0.3:
            self.stats["risk_distribution"]["low"] += 1
        elif risk_score < 0.6:
            self.stats["risk_distribution"]["medium"] += 1
        elif risk_score < 0.8:
            self.stats["risk_distribution"]["high"] += 1
        else:
            self.stats["risk_distribution"]["critical"] += 1
        
        # 更新平均评估时间
        self.stats["avg_evaluation_time"] = (
            (self.stats["avg_evaluation_time"] * (self.stats["total_plans_evaluated"] - 1) + evaluation_time)
            / self.stats["total_plans_evaluated"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_evaluations = self.stats["total_plans_evaluated"]
        
        # 计算分布百分比
        score_distribution_pct = {}
        if total_evaluations > 0:
            for category, count in self.stats["score_distribution"].items():
                score_distribution_pct[category] = count / total_evaluations
        
        risk_distribution_pct = {}
        if total_evaluations > 0:
            for category, count in self.stats["risk_distribution"].items():
                risk_distribution_pct[category] = count / total_evaluations
        
        return {
            "config": self.config.to_dict(),
            "performance": {
                "total_plans_evaluated": self.stats["total_plans_evaluated"],
                "total_steps_evaluated": self.stats["total_steps_evaluated"],
                "avg_evaluation_time_ms": self.stats["avg_evaluation_time"] * 1000,
                "avg_steps_per_plan": (
                    self.stats["total_steps_evaluated"] / total_evaluations 
                    if total_evaluations > 0 else 0.0
                )
            },
            "score_distribution": {
                "counts": self.stats["score_distribution"],
                "percentages": score_distribution_pct
            },
            "risk_distribution": {
                "counts": self.stats["risk_distribution"],
                "percentages": risk_distribution_pct
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_plans_evaluated": 0,
            "total_steps_evaluated": 0,
            "avg_evaluation_time": 0.0,
            "score_distribution": {
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "poor": 0,
                "very_poor": 0
            },
            "risk_distribution": {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            }
        }
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        perf = stats["performance"]
        score_dist = stats["score_distribution"]
        risk_dist = stats["risk_distribution"]
        
        print(f"   📊 Plan Evaluator状态:")
        print(f"      配置:")
        print(f"        评分权重:")
        print(f"          预期成功率: {config['weights']['expected_success']:.2f}")
        print(f"          成本效率: {config['weights']['cost_efficiency']:.2f}")
        print(f"          风险分数: {config['weights']['risk_score']:.2f}")
        print(f"          RQS投影: {config['weights']['rqs_projection']:.2f}")
        print(f"          新颖性: {config['weights']['novelty']:.2f}")
        
        print(f"      RQS投影:")
        print(f"          预测步数: {config['rqs_projection']['horizon']}")
        print(f"          衰减因子: {config['rqs_projection']['decay_factor']:.2f}")
        print(f"          启用: {config['rqs_projection']['enabled']}")
        
        print(f"      性能:")
        print(f"        总评估计划数: {perf['total_plans_evaluated']}")
        print(f"        总评估步骤数: {perf['total_steps_evaluated']}")
        print(f"        平均步骤数/计划: {perf['avg_steps_per_plan']:.1f}")
        print(f"        平均评估时间: {perf['avg_evaluation_time_ms']:.2f}ms")
        
        print(f"      分数分布:")
        if perf['total_plans_evaluated'] > 0:
            for category, count in score_dist["counts"].items():
                pct = score_dist["percentages"].get(category, 0)
                print(f"        {category}: {count} ({pct:.1%})")
        
        print(f"      风险分布:")
        if perf['total_plans_evaluated'] > 0:
            for category, count in risk_dist["counts"].items():
                pct = risk_dist["percentages"].get(category, 0)
                print(f"        {category}: {count} ({pct:.1%})")

class RQSSimulator:
    """RQS模拟器（简化版）"""
    
    def __init__(self):
        # 行动类型的RQS基准
        self.action_rqs_baseline = {
            "retrieve_info": 0.8,
            "analyze": 0.7,
            "compare": 0.6,
            "decide": 0.5,
            "execute": 0.4,
            "evaluate": 0.7,
            "adapt": 0.6,
            "report": 0.9
        }
        
        # 衰减因子
        self.decay_factors = [0.9, 0.8, 0.7, 0.6, 0.5]  # 5步衰减
    
    def project_rqs(self, plan_steps: List[PlanStep], 
                   context: Optional[Dict[str, Any]] = None) -> float:
        """预测RQS"""
        if not plan_steps:
            return 0.5
        
        # 计算每个步骤的RQS
        step_rqs_scores = []
        for i, step in enumerate(plan_steps):
            # 基础RQS
            base_rqs = self.action_rqs_baseline.get(step.action.value, 0.5)
            
            # 应用衰减
            decay_factor = self.decay_factors[min(i, len(self.decay_factors)-1)]
            step_rqs = base_rqs * decay_factor
            
            step_rqs_scores.append(step_rqs)
        
        # 平均RQS
        if step_rqs_scores:
            avg_rqs = sum(step_rqs_scores) / len(step_rqs_scores)
        else:
            avg_rqs = 0.5
        
        # 应用上下文调整
        if context:
            # 如果有历史RQS数据，进行调整
            historical_rqs = context.get("historical_rqs", 0.5)
            avg_rqs = (avg_rqs * 0.7 + historical_rqs * 0.3)
        
        return max(0.0, min(1.0, avg_rqs))
