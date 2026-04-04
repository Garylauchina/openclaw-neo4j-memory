#!/usr/bin/env python3
"""
Action Generator（行动生成器）
核心：从Plan Step → Concrete Action，必须可执行、可观测
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import uuid
import time
from datetime import datetime

class ActionType(Enum):
    """行动类型枚举"""
    API_CALL = "api_call"              # API调用
    DATA_RETRIEVAL = "data_retrieval"  # 数据检索
    ANALYSIS = "analysis"              # 分析
    DECISION = "decision"              # 决策
    EXECUTION = "execution"            # 执行
    VALIDATION = "validation"          # 验证
    ADAPTATION = "adaptation"          # 调整
    REPORTING = "reporting"            # 报告
    
    # 真实世界行动
    EXTERNAL_API = "external_api"      # 外部API
    DATABASE_QUERY = "database_query"  # 数据库查询
    FILE_OPERATION = "file_operation"  # 文件操作
    NETWORK_REQUEST = "network_request" # 网络请求

class ActionRiskLevel(Enum):
    """行动风险等级"""
    LOW = "low"        # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"      # 高风险
    CRITICAL = "critical"  # 关键风险

@dataclass
class Action:
    """行动定义"""
    
    def __init__(self, 
                 action_type: ActionType,
                 target: str,
                 parameters: Dict[str, Any] = None,
                 expected_outcome: str = "",
                 timeout_seconds: int = 30,
                 retry_count: int = 3,
                 fallback_action: Optional['Action'] = None):
        """
        初始化行动
        
        Args:
            action_type: 行动类型
            target: 目标（如"market_data_service"）
            parameters: 参数（如{"region": "Tokyo"}）
            expected_outcome: 预期结果
            timeout_seconds: 超时时间
            retry_count: 重试次数
            fallback_action: 降级行动
        """
        self.id = str(uuid.uuid4())
        self.action_type = action_type
        self.target = target
        self.parameters = parameters or {}
        self.expected_outcome = expected_outcome
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.fallback_action = fallback_action
        
        # 可执行性和可观测性
        self.executable = True  # 必须可执行
        self.observable = True  # 必须可观测
        self.real_world_impact = self._determine_real_world_impact()
        
        # 风险评估
        self.risk_level = self._assess_risk_level()
        self.requires_confirmation = self.risk_level in [ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL]
        
        # 实验框架
        self.is_experiment = False
        self.hypothesis = ""
        self.experiment_parameters: Dict[str, Any] = {}
        
        # 元数据
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # 执行状态（运行时设置）
        self.execution_status: Optional[str] = None
        self.execution_result: Optional[Any] = None
        self.execution_error: Optional[str] = None
        self.execution_time: float = 0.0
        self.retry_attempts: int = 0
    
    def _determine_real_world_impact(self) -> bool:
        """确定是否有真实世界影响"""
        # 基于行动类型判断
        real_world_actions = {
            ActionType.EXTERNAL_API,
            ActionType.DATABASE_QUERY,
            ActionType.FILE_OPERATION,
            ActionType.NETWORK_REQUEST,
            ActionType.EXECUTION
        }
        
        return self.action_type in real_world_actions
    
    def _assess_risk_level(self) -> ActionRiskLevel:
        """评估风险等级"""
        # 基于行动类型和参数评估风险
        risk_mapping = {
            ActionType.API_CALL: ActionRiskLevel.LOW,
            ActionType.DATA_RETRIEVAL: ActionRiskLevel.LOW,
            ActionType.ANALYSIS: ActionRiskLevel.LOW,
            ActionType.DECISION: ActionRiskLevel.MEDIUM,
            ActionType.VALIDATION: ActionRiskLevel.LOW,
            ActionType.REPORTING: ActionRiskLevel.LOW,
            ActionType.ADAPTATION: ActionRiskLevel.MEDIUM,
            
            # 真实世界行动风险较高
            ActionType.EXTERNAL_API: ActionRiskLevel.MEDIUM,
            ActionType.DATABASE_QUERY: ActionRiskLevel.MEDIUM,
            ActionType.FILE_OPERATION: ActionRiskLevel.HIGH,
            ActionType.NETWORK_REQUEST: ActionRiskLevel.MEDIUM,
            ActionType.EXECUTION: ActionRiskLevel.HIGH
        }
        
        base_risk = risk_mapping.get(self.action_type, ActionRiskLevel.MEDIUM)
        
        # 基于参数调整风险
        if "delete" in str(self.parameters).lower() or "remove" in str(self.parameters).lower():
            return ActionRiskLevel.CRITICAL
        
        if "modify" in str(self.parameters).lower() or "update" in str(self.parameters).lower():
            return ActionRiskLevel.HIGH
        
        return base_risk
    
    def to_experiment(self, hypothesis: str, expected_outcome: str = "") -> 'Action':
        """转换为实验行动"""
        self.is_experiment = True
        self.hypothesis = hypothesis
        
        if expected_outcome:
            self.expected_outcome = expected_outcome
        
        self.experiment_parameters = {
            "hypothesis": hypothesis,
            "expected_outcome": self.expected_outcome,
            "created_at": datetime.now().isoformat()
        }
        
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "target": self.target,
            "parameters": self.parameters,
            "expected_outcome": self.expected_outcome,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "fallback_action": self.fallback_action.to_dict() if self.fallback_action else None,
            
            # 可执行性和可观测性
            "executable": self.executable,
            "observable": self.observable,
            "real_world_impact": self.real_world_impact,
            
            # 风险评估
            "risk_level": self.risk_level.value,
            "requires_confirmation": self.requires_confirmation,
            
            # 实验框架
            "is_experiment": self.is_experiment,
            "hypothesis": self.hypothesis,
            "experiment_parameters": self.experiment_parameters,
            
            # 执行状态
            "execution_status": self.execution_status,
            "execution_result": str(self.execution_result) if self.execution_result else None,
            "execution_error": self.execution_error,
            "execution_time": self.execution_time,
            "retry_attempts": self.retry_attempts,
            
            # 元数据
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "target": self.target,
            "executable": self.executable,
            "real_world_impact": self.real_world_impact,
            "risk_level": self.risk_level.value,
            "requires_confirmation": self.requires_confirmation,
            "is_experiment": self.is_experiment
        }

@dataclass
class ActionGeneratorConfig:
    """行动生成器配置"""
    # 行动生成
    enable_real_world_actions: bool = True      # 启用真实世界行动
    max_action_complexity: int = 3              # 最大行动复杂度
    require_observability: bool = True          # 要求可观测性
    
    # 风险评估
    risk_assessment_enabled: bool = True        # 启用风险评估
    confirmation_threshold: str = "high"        # 确认阈值
    
    # 实验框架
    enable_experiment_mode: bool = True         # 启用实验模式
    default_hypothesis_format: str = "如果{action}，那么{outcome}"  # 默认假设格式
    
    def validate(self):
        """验证配置"""
        if self.max_action_complexity < 1:
            raise ValueError(f"max_action_complexity必须大于0，当前为{self.max_action_complexity}")
        
        valid_thresholds = ["low", "medium", "high", "critical"]
        if self.confirmation_threshold not in valid_thresholds:
            raise ValueError(f"confirmation_threshold必须是{valid_thresholds}之一，当前为{self.confirmation_threshold}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_generation": {
                "enable_real_world_actions": self.enable_real_world_actions,
                "max_action_complexity": self.max_action_complexity,
                "require_observability": self.require_observability
            },
            "risk_assessment": {
                "risk_assessment_enabled": self.risk_assessment_enabled,
                "confirmation_threshold": self.confirmation_threshold
            },
            "experiment_framework": {
                "enable_experiment_mode": self.enable_experiment_mode,
                "default_hypothesis_format": self.default_hypothesis_format
            }
        }

class ActionGenerator:
    """行动生成器"""
    
    # 行动模板库
    ACTION_TEMPLATES = {
        "retrieve_info": [
            (ActionType.API_CALL, "market_data_service", {"region": "Tokyo", "timeframe": "1_month"}),
            (ActionType.DATA_RETRIEVAL, "user_behavior_data", {"source": "analytics_db", "limit": 1000}),
            (ActionType.EXTERNAL_API, "financial_data_api", {"symbol": "AAPL", "interval": "daily"}),
        ],
        "analyze": [
            (ActionType.ANALYSIS, "trend_analysis", {"method": "regression", "confidence": 0.95}),
            (ActionType.ANALYSIS, "pattern_detection", {"algorithm": "clustering", "k": 5}),
            (ActionType.DATABASE_QUERY, "analysis_results", {"query": "SELECT * FROM analysis WHERE date > '2026-01-01'"}),
        ],
        "compare": [
            (ActionType.ANALYSIS, "comparative_analysis", {"options": ["A", "B", "C"], "criteria": ["cost", "benefit"]}),
            (ActionType.DECISION, "option_evaluation", {"evaluation_matrix": "weighted_scoring"}),
            (ActionType.FILE_OPERATION, "comparison_report", {"format": "csv", "location": "/reports/"}),
        ],
        "decide": [
            (ActionType.DECISION, "best_option_selection", {"method": "multi_criteria", "weights": {"ROI": 0.4, "risk": 0.3}}),
            (ActionType.EXECUTION, "decision_implementation", {"phase": "initial", "resources": ["budget", "team"]}),
            (ActionType.REPORTING, "decision_documentation", {"audience": "stakeholders", "format": "presentation"}),
        ],
        "execute": [
            (ActionType.EXECUTION, "plan_implementation", {"phase": "execution", "monitoring": True}),
            (ActionType.EXTERNAL_API, "service_deployment", {"environment": "production", "rollback_enabled": True}),
            (ActionType.NETWORK_REQUEST, "system_integration", {"endpoint": "https://api.example.com", "method": "POST"}),
        ]
    }
    
    def __init__(self, config: Optional[ActionGeneratorConfig] = None):
        self.config = config or ActionGeneratorConfig()
        self.config.validate()
        
        # 统计信息
        self.stats = {
            "total_actions_generated": 0,
            "real_world_actions": 0,
            "high_risk_actions": 0,
            "experiment_actions": 0,
            "avg_generation_time": 0.0
        }
    
    def generate_action(self, plan_step_description: str,
                       context: Optional[Dict[str, Any]] = None) -> Action:
        """
        生成行动
        
        Args:
            plan_step_description: 计划步骤描述
            context: 上下文信息
        
        Returns:
            Action: 生成的行动
        """
        import time
        start_time = time.time()
        
        # 1. 解析计划步骤
        step_info = self._parse_plan_step(plan_step_description, context)
        
        # 2. 选择行动模板
        template = self._select_action_template(step_info, context)
        
        # 3. 生成具体行动
        action = self._create_action_from_template(template, step_info, context)
        
        # 4. 应用实验框架（如果启用）
        if self.config.enable_experiment_mode and context and context.get("enable_experiments", False):
            action = self._convert_to_experiment(action, step_info, context)
        
        # 5. 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(action, elapsed_time)
        
        return action
    
    def generate_actions_for_plan(self, plan_steps: List[Dict[str, Any]],
                                context: Optional[Dict[str, Any]] = None) -> List[Action]:
        """
        为计划生成行动序列
        
        Args:
            plan_steps: 计划步骤列表
            context: 上下文信息
        
        Returns:
            List[Action]: 行动序列
        """
        actions = []
        
        for step in plan_steps:
            step_description = f"{step.get('action', 'unknown')} - {step.get('target', 'unknown')}"
            action = self.generate_action(step_description, context)
            actions.append(action)
        
        return actions
    
    def _parse_plan_step(self, step_description: str,
                        context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """解析计划步骤"""
        # 简单解析逻辑
        parts = step_description.split(" - ")
        
        if len(parts) >= 2:
            action_part = parts[0].strip()
            target_part = parts[1].strip()
        else:
            action_part = step_description
            target_part = ""
        
        # 推断行动类型
        action_type = self._infer_action_type(action_part, context)
        
        # 推断目标
        target = self._infer_target(target_part, context)
        
        return {
            "original_description": step_description,
            "action_part": action_part,
            "target_part": target_part,
            "inferred_action_type": action_type,
            "inferred_target": target,
            "context": context or {}
        }
    
    def _infer_action_type(self, action_part: str,
                          context: Optional[Dict[str, Any]]) -> str:
        """推断行动类型"""
        action_lower = action_part.lower()
        
        if any(word in action_lower for word in ["retrieve", "fetch", "get", "search"]):
            return "retrieve_info"
        elif any(word in action_lower for word in ["analyze", "analysis", "study", "research"]):
            return "analyze"
        elif any(word in action_lower for word in ["compare", "comparison", "evaluate", "assessment"]):
            return "compare"
        elif any(word in action_lower for word in ["decide", "decision", "choose", "select"]):
            return "decide"
        elif any(word in action_lower for word in ["execute", "implement", "run", "perform"]):
            return "execute"
        else:
            return "retrieve_info"  # 默认类型
    
    def _infer_target(self, target_part: str,
                     context: Optional[Dict[str, Any]]) -> str:
        """推断目标"""
        if not target_part:
            return "unknown_target"
        
        # 简单目标推断
        target_lower = target_part.lower()
        
        if any(word in target_lower for word in ["market", "sales", "revenue"]):
            return "market_data"
        elif any(word in target_lower for word in ["user", "customer", "client"]):
            return "user_data"
        elif any(word in target_lower for word in ["product", "item", "service"]):
            return "product_data"
        elif any(word in target_lower for word in ["financial", "finance", "money"]):
            return "financial_data"
        else:
            return target_part
    
    def _select_action_template(self, step_info: Dict[str, Any],
                               context: Optional[Dict[str, Any]]) -> tuple:
        """选择行动模板"""
        action_type = step_info["inferred_action_type"]
        
        # 获取模板列表
        templates = self.ACTION_TEMPLATES.get(action_type, [])
        
        if not templates:
            # 默认模板
            templates = self.ACTION_TEMPLATES["retrieve_info"]
        
        # 选择第一个模板
        return templates[0]
    
    def _create_action_from_template(self, template: tuple,
                                   step_info: Dict[str, Any],
                                   context: Optional[Dict[str, Any]]) -> Action:
        """从模板创建行动"""
        action_type, target, parameters = template
        
        # 调整参数
        adjusted_parameters = parameters.copy()
        
        # 添加步骤信息
        adjusted_parameters["step_description"] = step_info["original_description"]
        adjusted_parameters["inferred_action_type"] = step_info["inferred_action_type"]
        
        # 添加上下文信息
        if context:
            if "domain" in context:
                adjusted_parameters["domain"] = context["domain"]
            if "constraints" in context:
                adjusted_parameters["constraints"] = context["constraints"]
        
        # 生成预期结果
        expected_outcome = self._generate_expected_outcome(action_type, target, step_info)
        
        # 创建行动
        action = Action(
            action_type=action_type,
            target=target,
            parameters=adjusted_parameters,
            expected_outcome=expected_outcome,
            timeout_seconds=30,
            retry_count=3
        )
        
        # 应用配置
        if not self.config.enable_real_world_actions:
            # 如果没有启用真实世界行动，确保没有真实世界影响
            action.real_world_impact = False
        
        return action
    
    def _generate_expected_outcome(self, action_type: ActionType,
                                 target: str,
                                 step_info: Dict[str, Any]) -> str:
        """生成预期结果"""
        if action_type == ActionType.API_CALL:
            return f"成功调用{target} API，返回有效数据"
        elif action_type == ActionType.DATA_RETRIEVAL:
            return f"成功检索{target}数据，数据完整可用"
        elif action_type == ActionType.ANALYSIS:
            return f"完成{target}分析，提供可操作的洞察"
        elif action_type == ActionType.DECISION:
            return f"基于分析做出{target}决策，决策依据充分"
        elif action_type == ActionType.EXECUTION:
            return f"成功执行{target}，达到预期效果"
        elif action_type == ActionType.EXTERNAL_API:
            return f"成功调用外部{target}服务，获得有效响应"
        else:
            return f"完成{action_type.value}行动，推进目标实现"
    
    def _convert_to_experiment(self, action: Action,
                             step_info: Dict[str, Any],
                             context: Optional[Dict[str, Any]]) -> Action:
        """转换为实验行动"""
        # 生成假设
        hypothesis = self.config.default_hypothesis_format.format(
            action=action.action_type.value,
            outcome=action.expected_outcome
        )
        
        # 转换为实验
        action.to_experiment(hypothesis)
        
        return action
    
    def _update_stats(self, action: Action, elapsed_time: float):
        """更新统计信息"""
        self.stats["total_actions_generated"] += 1
        
        if action.real_world_impact:
            self.stats["real_world_actions"] += 1
        
        if action.risk_level in [ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL]:
            self.stats["high_risk_actions"] += 1
        
        if action.is_experiment:
            self.stats["experiment_actions"] += 1
        
        # 更新平均生成时间
        self.stats["avg_generation_time"] = (
            (self.stats["avg_generation_time"] * (self.stats["total_actions_generated"] - 1) + elapsed_time)
            / self.stats["total_actions_generated"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_actions = self.stats["total_actions_generated"]
        
        return {
            "config": self.config.to_dict(),
            "performance": {
                "total_actions_generated": total_actions,
                "real_world_actions": self.stats["real_world_actions"],
                "real_world_percentage": (
                    self.stats["real_world_actions"] / total_actions * 100 
                    if total_actions > 0 else 0.0
                ),
                "high_risk_actions": self.stats["high_risk_actions"],
                "experiment_actions": self.stats["experiment_actions"],
                "avg_generation_time_ms": self.stats["avg_generation_time"] * 1000
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_actions_generated": 0,
            "real_world_actions": 0,
            "high_risk_actions": 0,
            "experiment_actions": 0,
            "avg_generation_time": 0.0
        }
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        perf = stats["performance"]
        
        print(f"   📊 Action Generator状态:")
        print(f"      配置:")
        print(f"        行动生成:")
        print(f"          启用真实世界行动: {config['action_generation']['enable_real_world_actions']}")
        print(f"          最大行动复杂度: {config['action_generation']['max_action_complexity']}")
        print(f"          要求可观测性: {config['action_generation']['require_observability']}")
        
        print(f"        风险评估:")
        print(f"          启用风险评估: {config['risk_assessment']['risk_assessment_enabled']}")
        print(f"          确认阈值: {config['risk_assessment']['confirmation_threshold']}")
        
        print(f"        实验框架:")
        print(f"          启用实验模式: {config['experiment_framework']['enable_experiment_mode']}")
        print(f"          默认假设格式: {config['experiment_framework']['default_hypothesis_format']}")
        
        print(f"      性能:")
        print(f"        总生成行动数: {perf['total_actions_generated']}")
        print(f"        真实世界行动: {perf['real_world_actions']} ({perf['real_world_percentage']:.1f}%)")
        print(f"        高风险行动: {perf['high_risk_actions']}")
        print(f"        实验行动: {perf['experiment_actions']}")
        print(f"        平均生成时间: {perf['avg_generation_time_ms']:.2f}ms")