#!/usr/bin/env python3
"""
完整闭环系统 - 真正完成版
核心：让系统在现实中试错、调整、进化
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime

from .environment import Environment, Action, ExecutionResult
from .validation_enhanced import EnhancedValidator, EnhancedValidationResult
from .strategy_evolution import StrategyEvolutionEngine, Strategy

@dataclass
class ClosedLoopConfig:
    """闭环系统配置"""
    # 执行控制
    max_consecutive_failures: int = 3
    action_budget: float = 1000.0
    exploration_limit: float = 0.3
    
    # 学习参数
    strategy_update_frequency: int = 5  # 每N次行动更新一次策略
    fitness_update_weight: float = 0.1  # 适应度更新权重
    
    # 安全机制
    enable_safety_checks: bool = True
    force_replan_on_failure: bool = True
    stop_on_budget_exceeded: bool = True
    
    def validate(self):
        """验证配置"""
        if self.max_consecutive_failures < 1:
            raise ValueError("max_consecutive_failures必须>=1")
        
        if self.action_budget <= 0:
            raise ValueError("action_budget必须>0")
        
        if not 0.0 <= self.exploration_limit <= 1.0:
            raise ValueError("exploration_limit必须在0~1之间")
        
        if self.strategy_update_frequency < 1:
            raise ValueError("strategy_update_frequency必须>=1")
        
        if not 0.0 <= self.fitness_update_weight <= 1.0:
            raise ValueError("fitness_update_weight必须在0~1之间")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "execution_control": {
                "max_consecutive_failures": self.max_consecutive_failures,
                "action_budget": self.action_budget,
                "exploration_limit": self.exploration_limit
            },
            "learning_parameters": {
                "strategy_update_frequency": self.strategy_update_frequency,
                "fitness_update_weight": self.fitness_update_weight
            },
            "safety_mechanisms": {
                "enable_safety_checks": self.enable_safety_checks,
                "force_replan_on_failure": self.force_replan_on_failure,
                "stop_on_budget_exceeded": self.stop_on_budget_exceeded
            }
        }

class ClosedLoopSystem:
    """完整闭环系统"""
    
    def __init__(self, config: Optional[ClosedLoopConfig] = None):
        self.config = config or ClosedLoopConfig()
        self.config.validate()
        
        # 核心组件
        self.environment = Environment()
        self.validator = EnhancedValidator()
        self.strategy_engine = StrategyEvolutionEngine()
        
        # 执行状态
        self.execution_state = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "total_cost": 0.0,
            "consecutive_failures": 0,
            "current_strategy_id": None,
            "last_strategy_update": 0,
            "budget_remaining": self.config.action_budget
        }
        
        # 历史记录
        self.action_history: List[Dict[str, Any]] = []
        self.validation_history: List[Dict[str, Any]] = []
        self.strategy_history: List[Dict[str, Any]] = []
        
        # 注册默认连接器
        self._register_default_connectors()
    
    def _register_default_connectors(self):
        """注册默认连接器"""
        from .environment import APIConnector, FileConnector, DatabaseConnector
        
        # API连接器
        api_connector = APIConnector(name="weather_api")
        self.environment.register(api_connector)
        
        # 文件连接器
        file_connector = FileConnector(name="file_system")
        self.environment.register(file_connector)
        
        # 数据库连接器
        db_connector = DatabaseConnector(name="database")
        self.environment.register(db_connector)
        
        print("✅ 已注册默认连接器: weather_api, file_system, database")
    
    def execute(self, action: Action,
                goal_description: str,
                context: Optional[Dict[str, Any]] = None) -> Tuple[ExecutionResult, EnhancedValidationResult]:
        """
        执行完整闭环
        
        ❗ 完整执行流：
        Query → Goal → Strategy Selection → Plan → Action → 
        Environment.act() ← ❗现实交互 → Result → Validation（含external） → 
        Cost计算 → ARQS更新 → Strategy Update → Replan（必要）
        """
        # 1. 安全检查
        if not self._safety_check():
            return self._create_safety_failure(action), self._create_safety_validation(action)
        
        # 2. 策略选择
        current_strategy = self._select_strategy(context)
        
        # 3. 应用策略参数
        self._apply_strategy_parameters(current_strategy, context)
        
        # 4. 环境执行（❗现实交互）
        execution_result = self.environment.act(action)
        
        # 5. 更新执行状态
        self._update_execution_state(execution_result)
        
        # 6. 增强验证（含external_feedback）
        validation_result = self.validator.validate(
            action, execution_result, goal_description, context
        )
        
        # 7. 策略性能更新
        self._update_strategy_performance(
            current_strategy, validation_result, execution_result
        )
        
        # 8. 策略进化
        self._evolve_strategies()
        
        # 9. 记录历史
        self._record_history(action, execution_result, validation_result, current_strategy)
        
        return execution_result, validation_result
    
    def _safety_check(self) -> bool:
        """安全检查"""
        if not self.config.enable_safety_checks:
            return True
        
        # 检查预算
        if (self.config.stop_on_budget_exceeded and 
            self.execution_state["total_cost"] >= self.config.action_budget):
            print("⚠️  安全检查失败: 预算已用完")
            return False
        
        # 检查连续失败
        if (self.execution_state["consecutive_failures"] >= 
            self.config.max_consecutive_failures):
            print(f"⚠️  安全检查失败: 连续失败次数过多 ({self.execution_state['consecutive_failures']})")
            return False
        
        return True
    
    def _create_safety_failure(self, action: Action) -> ExecutionResult:
        """创建安全检查失败结果"""
        return ExecutionResult(
            action_id=action.action_id,
            action_type=action.type,
            target=action.target,
            status="failed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=0.0,
            result=None,
            error="安全检查失败",
            latency_ms=0.0,
            resource_usage=0.0,
            risk=0.0
        )
    
    def _create_safety_validation(self, action: Action) -> EnhancedValidationResult:
        """创建安全检查验证结果"""
        return EnhancedValidationResult(
            action_id=action.action_id,
            action_type=action.type,
            validation_score=0.0,
            internal_consistency=0.0,
            goal_alignment=0.0,
            external_feedback=0.0,
            success=False,
            latency_ms=0.0,
            data_quality=0.0,
            cost=0.0,
            is_valid=False,
            validation_passed=False,
            validation_details={"safety_check_failed": True},
            risk_assessment={"safety_violation": 1.0},
            high_risk_factors=["安全检查失败"],
            recommendations=["检查系统安全配置"],
            requires_replan=True,
            validation_time=0.0
        )
    
    def _select_strategy(self, context: Optional[Dict[str, Any]]) -> Strategy:
        """选择策略"""
        # 使用策略引擎选择策略
        strategy = self.strategy_engine.select_strategy(context or {})
        
        if strategy:
            self.execution_state["current_strategy_id"] = strategy.id
            return strategy
        
        # 如果没有策略，创建默认策略
        from .strategy_evolution import Strategy
        default_strategy = Strategy(name="default_strategy", strategy_type="balanced")
        default_strategy.update_policy({
            "attention_top_k": 10,
            "planning_depth": 3,
            "risk_tolerance": 0.3,
            "validation_threshold": 0.6
        })
        
        self.strategy_engine.strategies[default_strategy.id] = default_strategy
        self.execution_state["current_strategy_id"] = default_strategy.id
        
        return default_strategy
    
    def _apply_strategy_parameters(self, strategy: Strategy, context: Optional[Dict[str, Any]]):
        """应用策略参数"""
        # 这里可以修改系统参数，例如：
        # attention.k = strategy.policy.get("attention_top_k", 10)
        # planner.depth = strategy.policy.get("planning_depth", 3)
        # executor.risk = strategy.policy.get("risk_tolerance", 0.3)
        
        # 目前只记录策略参数
        if context:
            context["strategy_parameters"] = strategy.policy
    
    def _update_execution_state(self, execution_result: ExecutionResult):
        """更新执行状态"""
        self.execution_state["total_actions"] += 1
        
        if execution_result.status == "success":
            self.execution_state["successful_actions"] += 1
            self.execution_state["consecutive_failures"] = 0
        else:
            self.execution_state["failed_actions"] += 1
            self.execution_state["consecutive_failures"] += 1
        
        # 更新成本
        cost = self._compute_cost(execution_result)
        self.execution_state["total_cost"] += cost
        self.execution_state["budget_remaining"] = self.config.action_budget - self.execution_state["total_cost"]
    
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
    
    def _update_strategy_performance(self, strategy: Strategy,
                                   validation_result: EnhancedValidationResult,
                                   execution_result: ExecutionResult):
        """更新策略性能"""
        # 模拟ARQS分数（实际应从ARQS系统获取）
        arqs_score = validation_result.validation_score
        
        # 提取现实指标
        real_success = validation_result.success
        cost = validation_result.cost
        latency_ms = validation_result.latency_ms
        
        # 更新策略性能
        self.strategy_engine.update_strategy_performance(
            strategy.id, arqs_score, real_success, cost, latency_ms
        )
        
        # 更新策略更新计数器
        self.execution_state["last_strategy_update"] += 1
        
        # 检查是否需要策略进化
        if self.execution_state["last_strategy_update"] >= self.config.strategy_update_frequency:
            self.strategy_engine.evolve()
            self.execution_state["last_strategy_update"] = 0
    
    def _evolve_strategies(self):
        """进化策略"""
        # 策略进化由update_strategy_performance触发
        pass
    
    def _record_history(self, action: Action,
                       execution_result: ExecutionResult,
                       validation_result: EnhancedValidationResult,
                       strategy: Strategy):
        """记录历史"""
        # 记录行动历史
        self.action_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action.to_dict(),
            "execution_result": execution_result.to_dict(),
            "strategy_id": strategy.id
        })
        
        # 记录验证历史
        self.validation_history.append({
            "timestamp": datetime.now().isoformat(),
            "validation_result": validation_result.to_dict(),
            "strategy_id": strategy.id
        })
        
        # 记录策略历史
        self.strategy_history.append({
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy.get_summary(),
            "action_id": action.action_id
        })
        
        # 限制历史记录大小
        max_history = 1000
        if len(self.action_history) > max_history:
            self.action_history = self.action_history[-max_history:]
        if len(self.validation_history) > max_history:
            self.validation_history = self.validation_history[-max_history:]
        if len(self.strategy_history) > max_history:
            self.strategy_history = self.strategy_history[-max_history:]
    
    def get_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "config": self.config.to_dict(),
            "execution_state": self.execution_state,
            "environment_status": self.environment.get_status(),
            "validator_stats": self.validator.get_stats(),
            "strategy_engine_stats": self.strategy_engine.get_stats(),
            "history_summary": {
                "action_history_count": len(self.action_history),
                "validation_history_count": len(self.validation_history),
                "strategy_history_count": len(self.strategy_history)
            }
        }
    
    def reset(self):
        """重置系统"""
        self.environment.reset()
        self.validator.reset_stats()
        self.strategy_engine.reset()
        
        self.execution_state = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "total_cost": 0.0,
            "consecutive_failures": 0,
            "current_strategy_id": None,
            "last_strategy_update": 0,
            "budget_remaining": self.config.action_budget
        }
        
        self.action_history = []
        self.validation_history = []
        self.strategy_history = []
        
        print("✅ 闭环系统已重置")
    
    def print_status(self):
        """打印状态"""
        status = self.get_status()
        exec_state = status["execution_state"]
        env_status = status["environment_status"]
        
        print(f"   🔁 完整闭环系统状态:")
        print(f"      执行状态:")
        print(f"        总行动数: {exec_state['total_actions']}")
        print(f"        成功行动: {exec_state['successful_actions']}")
        print(f"        失败行动: {exec_state['failed_actions']}")
        
        if exec_state['total_actions'] > 0:
            success_rate = exec_state['successful_actions'] / exec_state['total_actions']
            print(f"        成功率: {success_rate:.1%}")
        
        print(f"        总成本: {exec_state['total_cost']:.3f}")
        print(f"        预算剩余: {exec_state['budget_remaining']:.3f}")
        print(f"        连续失败: {exec_state['consecutive_failures']}")
        
        print(f"      环境状态:")
        print(f"        连接器: {', '.join(env_status['connectors'])}")
        print(f"        环境成功率: {env_status['stats']['successful_actions']/env_status['stats']['total_actions']:.1%}" 
              if env_status['stats']['total_actions'] > 0 else "        环境成功率: 0.0%")
        
        print(f"      历史记录:")
        print(f"        行动历史: {status['history_summary']['action_history_count']}")
        print(f"        验证历史: {status['history_summary']['validation_history_count']}")
        print(f"        策略历史: {status['history_summary']['strategy_history_count']}")
        
        # 显示验证器状态
        self.validator.print_status()
        
        # 显示策略引擎状态
        self.strategy_engine.print_status()

def test_closed_loop_system():
    """测试闭环系统"""
    print("🧪 测试完整闭环系统...")
    
    # 创建闭环系统
    system = ClosedLoopSystem()
    
    # 创建测试行动
    action = Action(
        type="api_call",
        target="weather_api",
        params={"location": "Tokyo", "mock": True},
        expected_effect="获取东京天气数据",
        observable_signal="temperature"
    )
    
    # 执行闭环
    goal = "获取东京天气信息用于分析"
    context = {"task_type": "data_retrieval", "risk_level": "low"}
    
    print(f"  执行行动: {action.type} -> {action.target}")
    print(f"  目标: {goal}")
    print(f"  上下文: {context}")
    
    execution_result, validation_result = system.execute(action, goal, context)
    
    print(f"  执行结果:")
    print(f"    状态: {execution_result.status}")
    print(f"    延迟: {execution_result.latency_ms:.1f}ms")
    print(f"    成本: {system._compute_cost(execution_result):.3f}")
    
    print(f"  验证结果:")
    print(f"    验证分数: {validation_result.validation_score:.3f}")
    print(f"    外部反馈: {validation_result.external_feedback:.3f}")
    print(f"    是否成功: {validation_result.success}")
    print(f"    需要重规划: {validation_result.requires_replan}")
    
    # 显示系统状态
    system.print_status()
    
    return system

if __name__ == "__main__":
    print("🚀 测试完整闭环系统")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        system = test_closed_loop_system()
        print("\n✅ 闭环系统测试完成")
    except Exception as e:
        print(f"\n❌ 闭环系统测试失败: {e}")
        import traceback
        traceback.print_exc()