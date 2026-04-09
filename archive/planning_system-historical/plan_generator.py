#!/usr/bin/env python3
"""
Plan Generator（计划生成器）
核心：生成可验证路径（verifiable trajectory），不是简单步骤列表
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import uuid
import time
from datetime import datetime

class ActionType(Enum):
    """行动类型枚举"""
    RETRIEVE_INFO = "retrieve_info"      # 检索信息
    ANALYZE = "analyze"                  # 分析
    COMPARE = "compare"                  # 比较
    DECIDE = "decide"                    # 决策
    EXECUTE = "execute"                  # 执行
    EVALUATE = "evaluate"                # 评估
    ADAPT = "adapt"                      # 调整
    REPORT = "report"                    # 报告

class StepStatus(Enum):
    """步骤状态枚举"""
    PENDING = "pending"          # 等待执行
    EXECUTING = "executing"      # 执行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 取消
    SKIPPED = "skipped"          # 跳过

@dataclass
class PlanStep:
    """计划步骤"""
    
    def __init__(self, 
                 action: ActionType,
                 target: str = "",
                 method: str = "",
                 parameters: Dict[str, Any] = None,
                 expected_output: str = "",
                 timeout_seconds: int = 30):
        """
        初始化计划步骤
        
        Args:
            action: 行动类型
            target: 目标（如"market_data"）
            method: 方法（如"causal"）
            parameters: 参数
            expected_output: 预期输出
            timeout_seconds: 超时时间（秒）
        """
        self.id = str(uuid.uuid4())
        self.action = action
        self.target = target
        self.method = method
        self.parameters = parameters or {}
        self.expected_output = expected_output
        self.timeout_seconds = timeout_seconds
        
        # 执行状态
        self.status = StepStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.execution_time = 0.0
        self.result = None
        self.error = None
        
        # 可执行性
        self.executable = True  # 必须可执行
        self.prerequisites: List[str] = []  # 前置步骤ID
        self.dependencies: List[str] = []   # 依赖资源
        
        # 验证信息
        self.verification_criteria: List[str] = []  # 验证标准
        self.success_metrics: Dict[str, float] = {}  # 成功指标
        
        # 元数据
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def start_execution(self):
        """开始执行"""
        self.status = StepStatus.EXECUTING
        self.start_time = datetime.now()
        self.last_updated = datetime.now()
    
    def complete_execution(self, result: Any, execution_time: float = None):
        """完成执行"""
        self.status = StepStatus.COMPLETED
        self.end_time = datetime.now()
        self.result = result
        
        if execution_time is not None:
            self.execution_time = execution_time
        elif self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()
        
        self.last_updated = datetime.now()
    
    def fail_execution(self, error: str, execution_time: float = None):
        """执行失败"""
        self.status = StepStatus.FAILED
        self.end_time = datetime.now()
        self.error = error
        
        if execution_time is not None:
            self.execution_time = execution_time
        elif self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()
        
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "action": self.action.value,
            "target": self.target,
            "method": self.method,
            "parameters": self.parameters,
            "expected_output": self.expected_output,
            "timeout_seconds": self.timeout_seconds,
            
            # 执行状态
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            
            # 可执行性
            "executable": self.executable,
            "prerequisites": self.prerequisites,
            "dependencies": self.dependencies,
            
            # 验证信息
            "verification_criteria": self.verification_criteria,
            "success_metrics": self.success_metrics,
            
            # 元数据
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "id": self.id,
            "action": self.action.value,
            "target": self.target,
            "status": self.status.value,
            "execution_time": self.execution_time,
            "executable": self.executable,
            "has_error": self.error is not None
        }

@dataclass
class PlanGeneratorConfig:
    """计划生成器配置"""
    max_plan_depth: int = 5           # 最大计划深度
    beam_width: int = 3               # 束搜索宽度
    max_steps_per_plan: int = 10      # 每计划最大步骤数
    min_confidence_threshold: float = 0.3  # 最小置信度阈值
    enable_verification: bool = True  # 启用验证
    enable_prerequisites: bool = True # 启用前置条件
    
    def validate(self):
        """验证配置"""
        if self.max_plan_depth < 1:
            raise ValueError(f"max_plan_depth必须大于0，当前为{self.max_plan_depth}")
        
        if self.beam_width < 1:
            raise ValueError(f"beam_width必须大于0，当前为{self.beam_width}")
        
        if self.max_steps_per_plan < 1:
            raise ValueError(f"max_steps_per_plan必须大于0，当前为{self.max_steps_per_plan}")
        
        if not 0.0 <= self.min_confidence_threshold <= 1.0:
            raise ValueError(f"min_confidence_threshold必须在0~1之间，当前为{self.min_confidence_threshold}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "max_plan_depth": self.max_plan_depth,
            "beam_width": self.beam_width,
            "max_steps_per_plan": self.max_steps_per_plan,
            "min_confidence_threshold": self.min_confidence_threshold,
            "enable_verification": self.enable_verification,
            "enable_prerequisites": self.enable_prerequisites
        }

class PlanGenerator:
    """计划生成器"""
    
    # 行动模板库
    ACTION_TEMPLATES = {
        "information_gathering": [
            (ActionType.RETRIEVE_INFO, "market_data", "search", {"source": "reliable"}),
            (ActionType.RETRIEVE_INFO, "competitor_analysis", "collect", {"depth": "comprehensive"}),
            (ActionType.RETRIEVE_INFO, "user_feedback", "aggregate", {"timeframe": "recent"}),
        ],
        "analysis": [
            (ActionType.ANALYZE, "trends", "causal", {"method": "regression"}),
            (ActionType.ANALYZE, "patterns", "statistical", {"confidence": 0.95}),
            (ActionType.ANALYZE, "risks", "scenario", {"scenarios": ["best", "worst", "likely"]}),
        ],
        "comparison": [
            (ActionType.COMPARE, "options", "feature_matrix", {"dimensions": ["cost", "benefit", "risk"]}),
            (ActionType.COMPARE, "strategies", "swot", {"perspectives": ["strengths", "weaknesses", "opportunities", "threats"]}),
            (ActionType.COMPARE, "solutions", "tradeoff", {"criteria": ["feasibility", "impact", "cost"]}),
        ],
        "decision": [
            (ActionType.DECIDE, "best_option", "multi_criteria", {"criteria": ["ROI", "risk", "alignment"]}),
            (ActionType.DECIDE, "implementation_path", "cost_benefit", {"time_horizon": "medium_term"}),
            (ActionType.DECIDE, "resource_allocation", "priority_matrix", {"dimensions": ["urgency", "importance"]}),
        ],
        "execution": [
            (ActionType.EXECUTE, "implementation", "phased", {"phases": ["planning", "execution", "review"]}),
            (ActionType.EXECUTE, "deployment", "iterative", {"iterations": 3}),
            (ActionType.EXECUTE, "optimization", "continuous", {"feedback_loop": True}),
        ]
    }
    
    def __init__(self, config: Optional[PlanGeneratorConfig] = None):
        self.config = config or PlanGeneratorConfig()
        self.config.validate()
        
        # 统计信息
        self.stats = {
            "total_plans_generated": 0,
            "total_steps_generated": 0,
            "avg_steps_per_plan": 0.0,
            "avg_generation_time": 0.0,
            "action_distribution": {},
            "plan_depth_distribution": {}
        }
    
    def generate_plan(self, goal_description: str, 
                     context: Optional[Dict[str, Any]] = None) -> List[PlanStep]:
        """
        生成计划
        
        Args:
            goal_description: 目标描述
            context: 上下文信息
        
        Returns:
            List[PlanStep]: 计划步骤列表
        """
        import time
        start_time = time.time()
        
        # 1. 分析目标类型
        goal_type = self._analyze_goal_type(goal_description, context)
        
        # 2. 选择行动模板
        templates = self._select_templates(goal_type, context)
        
        # 3. 生成计划步骤
        plan_steps = []
        step_count = 0
        
        for template_group in templates:
            if step_count >= self.config.max_steps_per_plan:
                break
            
            for template in template_group:
                if step_count >= self.config.max_steps_per_plan:
                    break
                
                # 创建步骤
                step = self._create_step_from_template(template, goal_description, context)
                if step:
                    plan_steps.append(step)
                    step_count += 1
        
        # 4. 添加前置条件和依赖
        if self.config.enable_prerequisites:
            self._add_prerequisites(plan_steps)
        
        # 5. 添加验证标准
        if self.config.enable_verification:
            self._add_verification_criteria(plan_steps, goal_description)
        
        # 6. 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(len(plan_steps), elapsed_time)
        
        return plan_steps
    
    def generate_multiple_plans(self, goal_description: str,
                              context: Optional[Dict[str, Any]] = None,
                              num_plans: int = 3) -> List[List[PlanStep]]:
        """
        生成多个计划（束搜索）
        
        Args:
            goal_description: 目标描述
            context: 上下文信息
            num_plans: 计划数量
        
        Returns:
            List[List[PlanStep]]: 多个计划列表
        """
        import time
        start_time = time.time()
        
        plans = []
        
        # 生成多个变体计划
        for i in range(min(num_plans, self.config.beam_width)):
            # 添加一些随机性到上下文
            variant_context = context.copy() if context else {}
            variant_context["plan_variant"] = i
            
            # 生成计划
            plan = self.generate_plan(goal_description, variant_context)
            plans.append(plan)
        
        # 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(sum(len(plan) for plan in plans), elapsed_time, multiple=True)
        
        return plans
    
    def _analyze_goal_type(self, goal_description: str, context: Optional[Dict[str, Any]]) -> str:
        """分析目标类型"""
        goal_lower = goal_description.lower()
        
        # 简单关键词匹配（实际应用中可以使用更复杂的NLP）
        if any(word in goal_lower for word in ["理解", "了解", "什么是", "解释", "说明"]):
            return "information_gathering"
        elif any(word in goal_lower for word in ["分析", "评估", "研究", "调查"]):
            return "analysis"
        elif any(word in goal_lower for word in ["比较", "对比", "区别", "差异"]):
            return "comparison"
        elif any(word in goal_lower for word in ["决定", "选择", "决策", "确定"]):
            return "decision"
        elif any(word in goal_lower for word in ["执行", "实施", "实现", "完成"]):
            return "execution"
        else:
            # 默认类型
            return "information_gathering"
    
    def _select_templates(self, goal_type: str, context: Optional[Dict[str, Any]]) -> List[List[tuple]]:
        """选择行动模板"""
        templates = []
        
        # 基于目标类型选择模板序列
        if goal_type == "information_gathering":
            templates = [
                self.ACTION_TEMPLATES["information_gathering"],
                self.ACTION_TEMPLATES["analysis"],
                self.ACTION_TEMPLATES["comparison"]
            ]
        elif goal_type == "analysis":
            templates = [
                self.ACTION_TEMPLATES["information_gathering"],
                self.ACTION_TEMPLATES["analysis"],
                self.ACTION_TEMPLATES["comparison"],
                self.ACTION_TEMPLATES["decision"]
            ]
        elif goal_type == "comparison":
            templates = [
                self.ACTION_TEMPLATES["information_gathering"],
                self.ACTION_TEMPLATES["comparison"],
                self.ACTION_TEMPLATES["decision"]
            ]
        elif goal_type == "decision":
            templates = [
                self.ACTION_TEMPLATES["information_gathering"],
                self.ACTION_TEMPLATES["analysis"],
                self.ACTION_TEMPLATES["comparison"],
                self.ACTION_TEMPLATES["decision"],
                self.ACTION_TEMPLATES["execution"]
            ]
        elif goal_type == "execution":
            templates = [
                self.ACTION_TEMPLATES["information_gathering"],
                self.ACTION_TEMPLATES["analysis"],
                self.ACTION_TEMPLATES["execution"]
            ]
        
        # 限制深度
        return templates[:self.config.max_plan_depth]
    
    def _create_step_from_template(self, template: tuple, 
                                 goal_description: str, 
                                 context: Optional[Dict[str, Any]]) -> Optional[PlanStep]:
        """从模板创建步骤"""
        action_type, target, method, parameters = template
        
        # 根据目标描述调整参数
        adjusted_parameters = parameters.copy()
        
        # 添加目标相关信息
        if "goal" not in adjusted_parameters:
            adjusted_parameters["goal"] = goal_description
        
        # 添加上下文信息
        if context:
            if "domain" in context:
                adjusted_parameters["domain"] = context["domain"]
            if "constraints" in context:
                adjusted_parameters["constraints"] = context["constraints"]
        
        # 创建步骤
        step = PlanStep(
            action=action_type,
            target=target,
            method=method,
            parameters=adjusted_parameters,
            expected_output=self._generate_expected_output(action_type, target, goal_description),
            timeout_seconds=30
        )
        
        return step
    
    def _generate_expected_output(self, action_type: ActionType, target: str, goal_description: str) -> str:
        """生成预期输出"""
        if action_type == ActionType.RETRIEVE_INFO:
            return f"检索到关于{target}的相关信息，支持{goal_description}"
        elif action_type == ActionType.ANALYZE:
            return f"完成{target}分析，提供关键洞察支持{goal_description}"
        elif action_type == ActionType.COMPARE:
            return f"完成{target}比较，明确优劣和选择标准"
        elif action_type == ActionType.DECIDE:
            return f"基于分析做出{target}决策，支持{goal_description}"
        elif action_type == ActionType.EXECUTE:
            return f"执行{target}，推进{goal_description}实现"
        else:
            return f"完成{action_type.value}行动，推进目标：{goal_description}"
    
    def _add_prerequisites(self, plan_steps: List[PlanStep]):
        """添加前置条件"""
        if len(plan_steps) < 2:
            return
        
        # 简单的前置条件：每个步骤依赖前一个步骤
        for i in range(1, len(plan_steps)):
            plan_steps[i].prerequisites.append(plan_steps[i-1].id)
    
    def _add_verification_criteria(self, plan_steps: List[PlanStep], goal_description: str):
        """添加验证标准"""
        for step in plan_steps:
            if step.action == ActionType.RETRIEVE_INFO:
                step.verification_criteria = [
                    "信息相关性 > 0.7",
                    "信息完整性 > 0.6",
                    "信息时效性 < 24小时"
                ]
                step.success_metrics = {
                    "relevance": 0.8,
                    "completeness": 0.7,
                    "timeliness": 0.9
                }
            elif step.action == ActionType.ANALYZE:
                step.verification_criteria = [
                    "分析深度 > 0.7",
                    "逻辑一致性 > 0.8",
                    "洞察价值 > 0.6"
                ]
                step.success_metrics = {
                    "depth": 0.8,
                    "consistency": 0.85,
                    "insight_value": 0.7
                }
            elif step.action == ActionType.COMPARE:
                step.verification_criteria = [
                    "比较维度完整性 > 0.8",
                    "标准一致性 > 0.9",
                    "结论清晰度 > 0.7"
                ]
                step.success_metrics = {
                    "dimension_completeness": 0.85,
                    "standard_consistency": 0.92,
                    "conclusion_clarity": 0.75
                }
            elif step.action == ActionType.DECIDE:
                step.verification_criteria = [
                    "决策依据充分性 > 0.8",
                    "风险评估完整性 > 0.7",
                    "目标对齐度 > 0.9"
                ]
                step.success_metrics = {
                    "basis_sufficiency": 0.85,
                    "risk_assessment": 0.75,
                    "goal_alignment": 0.95
                }
    
    def _update_stats(self, steps_generated: int, elapsed_time: float, multiple: bool = False):
        """更新统计信息"""
        if multiple:
            self.stats["total_plans_generated"] += 1
        else:
            self.stats["total_plans_generated"] += 1
        
        self.stats["total_steps_generated"] += steps_generated
        
        # 更新平均步骤数
        self.stats["avg_steps_per_plan"] = (
            (self.stats["avg_steps_per_plan"] * (self.stats["total_plans_generated"] - 1) + steps_generated)
            / self.stats["total_plans_generated"]
        )
        
        # 更新平均生成时间
        self.stats["avg_generation_time"] = (
            (self.stats["avg_generation_time"] * (self.stats["total_plans_generated"] - 1) + elapsed_time)
            / self.stats["total_plans_generated"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "config": self.config.to_dict(),
            "performance": {
                "total_plans_generated": self.stats["total_plans_generated"],
                "total_steps_generated": self.stats["total_steps_generated"],
                "avg_steps_per_plan": self.stats["avg_steps_per_plan"],
                "avg_generation_time_ms": self.stats["avg_generation_time"] * 1000,
                "action_distribution": self.stats.get("action_distribution", {}),
                "plan_depth_distribution": self.stats.get("plan_depth_distribution", {})
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_plans_generated": 0,
            "total_steps_generated": 0,
            "avg_steps_per_plan": 0.0,
            "avg_generation_time": 0.0,
            "action_distribution": {},
            "plan_depth_distribution": {}
        }
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        perf = stats["performance"]
        
        print(f"   📊 Plan Generator状态:")
        print(f"      配置:")
        print(f"        最大计划深度: {config['max_plan_depth']}")
        print(f"        束搜索宽度: {config['beam_width']}")
        print(f"        每计划最大步骤数: {config['max_steps_per_plan']}")
        print(f"        最小置信度阈值: {config['min_confidence_threshold']:.2f}")
        print(f"        启用验证: {config['enable_verification']}")
        print(f"        启用前置条件: {config['enable_prerequisites']}")
        
        print(f"      性能:")
        print(f"        总生成计划数: {perf['total_plans_generated']}")
        print(f"        总生成步骤数: {perf['total_steps_generated']}")
        print(f"        平均步骤数/计划: {perf['avg_steps_per_plan']:.1f}")
        print(f"        平均生成时间: {perf['avg_generation_time_ms']:.2f}ms")