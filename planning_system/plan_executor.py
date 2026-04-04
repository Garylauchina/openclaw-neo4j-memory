#!/usr/bin/env python3
"""
Plan Executor（计划执行器）
核心：计划执行接口，支持状态更新、中断、回滚、重规划
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
import time
from datetime import datetime
import threading
import queue

from .plan_generator import PlanStep, StepStatus, ActionType

class ExecutionStatus(Enum):
    """执行状态枚举"""
    NOT_STARTED = "not_started"      # 未开始
    RUNNING = "running"              # 运行中
    PAUSED = "paused"                # 暂停
    COMPLETED = "completed"          # 完成
    FAILED = "failed"                # 失败
    CANCELLED = "cancelled"          # 取消
    ROLLED_BACK = "rolled_back"      # 已回滚

@dataclass
class ExecutionResult:
    """执行结果"""
    step_id: str
    step_index: int
    action: ActionType
    target: str
    
    # 执行状态
    status: StepStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    execution_time: float
    
    # 结果
    result: Any
    error: Optional[str]
    
    # 验证
    verification_passed: bool
    verification_details: Dict[str, Any]
    
    # 指标
    metrics: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "step_index": self.step_index,
            "action": self.action.value,
            "target": self.target,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_time": self.execution_time,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "verification_passed": self.verification_passed,
            "verification_details": self.verification_details,
            "metrics": self.metrics
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "step_id": self.step_id,
            "step_index": self.step_index,
            "action": self.action.value,
            "status": self.status.value,
            "execution_time": self.execution_time,
            "has_error": self.error is not None,
            "verification_passed": self.verification_passed
        }

@dataclass
class PlanExecutionConfig:
    """计划执行配置"""
    # 执行控制
    max_concurrent_steps: int = 1           # 最大并发步骤数
    enable_parallel_execution: bool = False # 启用并行执行
    execution_timeout_seconds: int = 300    # 总执行超时时间（5分钟）
    
    # 中断和回滚
    enable_interruption: bool = True        # 启用中断
    enable_rollback: bool = True            # 启用回滚
    rollback_strategy: str = "sequential"   # 回滚策略：sequential, parallel
    
    # 重规划
    enable_replanning: bool = True          # 启用重规划
    replan_threshold: float = 0.3           # 重规划阈值（失败率）
    max_replan_attempts: int = 3            # 最大重规划尝试次数
    
    # 监控
    enable_monitoring: bool = True          # 启用监控
    monitoring_interval_seconds: int = 1    # 监控间隔
    
    def validate(self):
        """验证配置"""
        if self.max_concurrent_steps < 1:
            raise ValueError(f"max_concurrent_steps必须大于0，当前为{self.max_concurrent_steps}")
        
        if self.execution_timeout_seconds < 10:
            raise ValueError(f"execution_timeout_seconds必须大于10秒，当前为{self.execution_timeout_seconds}")
        
        if not 0.0 <= self.replan_threshold <= 1.0:
            raise ValueError(f"replan_threshold必须在0~1之间，当前为{self.replan_threshold}")
        
        if self.max_replan_attempts < 0:
            raise ValueError(f"max_replan_attempts必须大于等于0，当前为{self.max_replan_attempts}")
        
        if self.monitoring_interval_seconds < 0.1:
            raise ValueError(f"monitoring_interval_seconds必须大于0.1秒，当前为{self.monitoring_interval_seconds}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "execution_control": {
                "max_concurrent_steps": self.max_concurrent_steps,
                "enable_parallel_execution": self.enable_parallel_execution,
                "execution_timeout_seconds": self.execution_timeout_seconds
            },
            "interruption_and_rollback": {
                "enable_interruption": self.enable_interruption,
                "enable_rollback": self.enable_rollback,
                "rollback_strategy": self.rollback_strategy
            },
            "replanning": {
                "enable_replanning": self.enable_replanning,
                "replan_threshold": self.replan_threshold,
                "max_replan_attempts": self.max_replan_attempts
            },
            "monitoring": {
                "enable_monitoring": self.enable_monitoring,
                "monitoring_interval_seconds": self.monitoring_interval_seconds
            }
        }

class PlanExecutor:
    """计划执行器"""
    
    def __init__(self, config: Optional[PlanExecutionConfig] = None):
        self.config = config or PlanExecutionConfig()
        self.config.validate()
        
        # 执行状态
        self.execution_status = ExecutionStatus.NOT_STARTED
        self.current_step_index = -1
        self.execution_results: List[ExecutionResult] = []
        
        # 控制标志
        self._pause_flag = False
        self._cancel_flag = False
        self._rollback_flag = False
        
        # 执行队列
        self._execution_queue = queue.Queue()
        self._worker_threads: List[threading.Thread] = []
        
        # 统计信息
        self.stats = {
            "total_plans_executed": 0,
            "total_steps_executed": 0,
            "total_steps_succeeded": 0,
            "total_steps_failed": 0,
            "total_execution_time": 0.0,
            "avg_step_execution_time": 0.0,
            "replan_attempts": 0,
            "rollback_operations": 0
        }
        
        # 回调函数
        self.callbacks = {
            "on_step_start": None,
            "on_step_complete": None,
            "on_step_fail": None,
            "on_plan_complete": None,
            "on_plan_fail": None,
            "on_replan": None,
            "on_rollback": None
        }
    
    def execute_plan(self, plan_steps: List[PlanStep],
                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行计划
        
        Args:
            plan_steps: 计划步骤列表
            context: 上下文信息
        
        Returns:
            Dict[str, Any]: 执行结果
        """
        import time
        start_time = time.time()
        
        # 重置状态
        self._reset_execution_state()
        
        # 更新状态
        self.execution_status = ExecutionStatus.RUNNING
        self.stats["total_plans_executed"] += 1
        
        # 执行计划
        execution_summary = self._execute_plan_sequential(plan_steps, context)
        
        # 计算总执行时间
        total_execution_time = time.time() - start_time
        self.stats["total_execution_time"] += total_execution_time
        
        # 更新执行结果
        execution_summary["total_execution_time"] = total_execution_time
        execution_summary["stats"] = self._get_current_stats()
        
        # 触发完成回调
        if self.callbacks["on_plan_complete"]:
            self.callbacks["on_plan_complete"](execution_summary)
        
        return execution_summary
    
    def _execute_plan_sequential(self, plan_steps: List[PlanStep],
                               context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """顺序执行计划"""
        execution_results = []
        failed_steps = []
        
        for i, step in enumerate(plan_steps):
            # 检查中断标志
            if self._cancel_flag:
                self.execution_status = ExecutionStatus.CANCELLED
                return self._create_execution_summary(
                    execution_results, failed_steps, "cancelled"
                )
            
            if self._pause_flag:
                self.execution_status = ExecutionStatus.PAUSED
                # 等待恢复
                while self._pause_flag and not self._cancel_flag:
                    time.sleep(0.1)
                
                if self._cancel_flag:
                    self.execution_status = ExecutionStatus.CANCELLED
                    return self._create_execution_summary(
                        execution_results, failed_steps, "cancelled"
                    )
                
                self.execution_status = ExecutionStatus.RUNNING
            
            # 更新当前步骤索引
            self.current_step_index = i
            
            # 触发步骤开始回调
            if self.callbacks["on_step_start"]:
                self.callbacks["on_step_start"](step, i)
            
            # 执行步骤
            step_start_time = time.time()
            result = self._execute_step(step, i, context)
            step_execution_time = time.time() - step_start_time
            
            # 记录结果
            execution_results.append(result)
            self.execution_results.append(result)
            
            # 更新统计
            self.stats["total_steps_executed"] += 1
            if result.status == StepStatus.COMPLETED:
                self.stats["total_steps_succeeded"] += 1
            else:
                self.stats["total_steps_failed"] += 1
                failed_steps.append((i, step, result.error))
            
            # 触发步骤完成回调
            if result.status == StepStatus.COMPLETED:
                if self.callbacks["on_step_complete"]:
                    self.callbacks["on_step_complete"](result)
            else:
                if self.callbacks["on_step_fail"]:
                    self.callbacks["on_step_fail"](result)
            
            # 检查是否需要重规划
            if (self.config.enable_replanning and 
                len(failed_steps) / len(plan_steps) >= self.config.replan_threshold):
                
                if self.stats["replan_attempts"] < self.config.max_replan_attempts:
                    # 触发重规划回调
                    if self.callbacks["on_replan"]:
                        self.callbacks["on_replan"](execution_results, failed_steps)
                    
                    # 执行重规划
                    replan_result = self._handle_replanning(
                        plan_steps, execution_results, failed_steps, context
                    )
                    
                    if replan_result:
                        return replan_result
                else:
                    # 达到最大重规划次数，失败
                    self.execution_status = ExecutionStatus.FAILED
                    return self._create_execution_summary(
                        execution_results, failed_steps, "failed_max_replan"
                    )
        
        # 所有步骤完成
        if failed_steps:
            self.execution_status = ExecutionStatus.FAILED
            status = "completed_with_failures"
        else:
            self.execution_status = ExecutionStatus.COMPLETED
            status = "completed"
        
        return self._create_execution_summary(execution_results, failed_steps, status)
    
    def _execute_step(self, step: PlanStep, step_index: int,
                     context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """执行单个步骤"""
        step_start_time = datetime.now()
        
        try:
            # 开始执行
            step.start_execution()
            
            # 模拟执行（实际应用中会调用真实执行器）
            result = self._simulate_step_execution(step, context)
            
            # 验证结果
            verification_passed, verification_details = self._verify_step_result(step, result)
            
            # 计算指标
            metrics = self._calculate_step_metrics(step, result, verification_passed)
            
            # 完成执行
            if verification_passed:
                step.complete_execution(result, time.time() - step_start_time.timestamp())
                status = StepStatus.COMPLETED
                error = None
            else:
                step.fail_execution("验证失败", time.time() - step_start_time.timestamp())
                status = StepStatus.FAILED
                error = "验证失败"
            
        except Exception as e:
            # 执行失败
            step.fail_execution(str(e), time.time() - step_start_time.timestamp())
            status = StepStatus.FAILED
            result = None
            verification_passed = False
            verification_details = {"error": str(e)}
            metrics = {}
            error = str(e)
        
        # 创建执行结果
        execution_result = ExecutionResult(
            step_id=step.id,
            step_index=step_index,
            action=step.action,
            target=step.target,
            status=status,
            start_time=step_start_time,
            end_time=datetime.now(),
            execution_time=(datetime.now() - step_start_time).total_seconds(),
            result=result,
            error=error,
            verification_passed=verification_passed,
            verification_details=verification_details,
            metrics=metrics
        )
        
        return execution_result
    
    def _simulate_step_execution(self, step: PlanStep,
                                context: Optional[Dict[str, Any]]) -> Any:
        """模拟步骤执行"""
        import random
        import time
        
        # 模拟执行时间
        execution_time = random.uniform(0.1, 2.0)
        time.sleep(execution_time)
        
        # 基于行动类型生成模拟结果
        if step.action == ActionType.RETRIEVE_INFO:
            result = {
                "data": f"检索到关于{step.target}的信息",
                "sources": ["source1", "source2", "source3"],
                "relevance_score": random.uniform(0.6, 0.9)
            }
        elif step.action == ActionType.ANALYZE:
            result = {
                "analysis": f"完成{step.target}分析",
                "insights": ["insight1", "insight2", "insight3"],
                "confidence": random.uniform(0.7, 0.95)
            }
        elif step.action == ActionType.COMPARE:
            result = {
                "comparison": f"完成{step.target}比较",
                "options": ["optionA", "optionB", "optionC"],
                "recommendation": random.choice(["optionA", "optionB", "optionC"])
            }
        elif step.action == ActionType.DECIDE:
            result = {
                "decision": f"基于{step.parameters.get('criteria', '标准')}做出决策",
                "selected_option": random.choice(["option1", "option2", "option3"]),
                "rationale": "基于分析和比较结果"
            }
        elif step.action == ActionType.EXECUTE:
            result = {
                "execution": f"执行{step.target}完成",
                "outcome": "成功",
                "details": "执行过程顺利"
            }
        else:
            result = {
                "action": step.action.value,
                "target": step.target,
                "result": "模拟执行完成"
            }
        
        # 添加一些随机失败
        if random.random() < 0.1:  # 10%失败率
            raise Exception(f"模拟执行失败: {step.action.value} - {step.target}")
        
        return result
    
    def _verify_step_result(self, step: PlanStep, result: Any) -> Tuple[bool, Dict[str, Any]]:
        """验证步骤结果"""
        verification_details = {}
        
        # 检查是否有验证标准
        if not step.verification_criteria:
            return True, {"no_criteria": "无验证标准"}
        
        # 简单验证逻辑
        passed_criteria = 0
        total_criteria = len(step.verification_criteria)
        
        for criterion in step.verification_criteria:
            # 简化验证：随机决定是否通过
            import random
            if random.random() > 0.2:  # 80%通过率
                passed_criteria += 1
                verification_details[criterion] = "通过"
            else:
                verification_details[criterion] = "未通过"
        
        # 计算通过率
        pass_rate = passed_criteria / total_criteria if total_criteria > 0 else 1.0
        
        # 检查成功指标
        if step.success_metrics:
            for metric_name, threshold in step.success_metrics.items():
                # 简化：随机生成指标值
                metric_value = random.uniform(0.5, 1.0)
                verification_details[f"metric_{metric_name}"] = {
                    "value": metric_value,
                    "threshold": threshold,
                    "passed": metric_value >= threshold
                }
                
                if metric_value >= threshold:
                    pass_rate = min(1.0, pass_rate + 0.1)
        
        verification_passed = pass_rate >= 0.7  # 70%通过率阈值
        
        return verification_passed, verification_details
    
    def _calculate_step_metrics(self, step: PlanStep, result: Any,
                              verification_passed: bool) -> Dict[str, float]:
        """计算步骤指标"""
        import random
        
        metrics = {
            "execution_speed": random.uniform(0.7, 1.0),  # 执行速度
            "result_quality": random.uniform(0.6, 0.9),   # 结果质量
            "resource_efficiency": random.uniform(0.5, 0.8),  # 资源效率
        }
        
        if verification_passed:
            metrics["verification_score"] = random.uniform(0.8, 1.0)
        else:
            metrics["verification_score"] = random.uniform(0.3, 0.6)
        
        return metrics
    
    def _handle_replanning(self, plan_steps: List[PlanStep],
                         execution_results: List[ExecutionResult],
                         failed_steps: List[Tuple[int, PlanStep, str]],
                         context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """处理重规划"""
        self.stats["replan_attempts"] += 1
        
        print(f"⚠️  执行重规划 (尝试 {self.stats['replan_attempts']}/{self.config.max_replan_attempts})")
        
        # 简单重规划策略：跳过失败步骤，继续执行
        remaining_steps = []
        
        for i, step in enumerate(plan_steps):
            # 检查是否已经执行过
            executed = any(r.step_index == i for r in execution_results)
            
            # 检查是否失败
            failed = any(f[0] == i for f in failed_steps)
            
            if not executed and not failed:
                remaining_steps.append(step)
        
        if remaining_steps:
            print(f"  重规划后剩余步骤: {len(remaining_steps)}个")
            
            # 继续执行剩余步骤
            remaining_results = self._execute_plan_sequential(remaining_steps, context)
            
            # 合并结果
            all_results = execution_results + remaining_results.get("step_results", [])
            all_failed_steps = failed_steps + [(r.step_index, plan_steps[r.step_index], r.error) 
                                             for r in remaining_results.get("step_results", [])
                                             if r.status != StepStatus.COMPLETED]
            
            return self._create_execution_summary(
                all_results, all_failed_steps, "completed_after_replan"
            )
        
        return None
    
    def _create_execution_summary(self, execution_results: List[ExecutionResult],
                                failed_steps: List[Tuple[int, PlanStep, str]],
                                status: str) -> Dict[str, Any]:
        """创建执行摘要"""
        # 计算统计
        total_steps = len(execution_results)
        succeeded_steps = sum(1 for r in execution_results if r.status == StepStatus.COMPLETED)
        failed_steps_count = len(failed_steps)
        
        success_rate = succeeded_steps / total_steps if total_steps > 0 else 0.0
        
        # 计算平均执行时间
        avg_execution_time = 0.0
        if execution_results:
            total_time = sum(r.execution_time for r in execution_results)
            avg_execution_time = total_time / len(execution_results)
        
        # 更新平均步骤执行时间统计
        if total_steps > 0:
            self.stats["avg_step_execution_time"] = (
                (self.stats["avg_step_execution_time"] * (self.stats["total_steps_executed"] - total_steps) + 
                 sum(r.execution_time for r in execution_results))
                / self.stats["total_steps_executed"]
            )
        
        return {
            "status": status,
            "execution_status": self.execution_status.value,
            "summary": {
                "total_steps": total_steps,
                "succeeded_steps": succeeded_steps,
                "failed_steps": failed_steps_count,
                "success_rate": success_rate,
                "avg_execution_time_per_step": avg_execution_time
            },
            "step_results": [r.to_dict() for r in execution_results],
            "failed_steps_details": [
                {
                    "step_index": step_index,
                    "step_id": step.id,
                    "action": step.action.value,
                    "target": step.target,
                    "error": error
                }
                for step_index, step, error in failed_steps
            ],
            "current_step_index": self.current_step_index
        }
    
    def pause_execution(self):
        """暂停执行"""
        if self.config.enable_interruption:
            self._pause_flag = True
            self.execution_status = ExecutionStatus.PAUSED
    
    def resume_execution(self):
        """恢复执行"""
        self._pause_flag = False
        if self.execution_status == ExecutionStatus.PAUSED:
            self.execution_status = ExecutionStatus.RUNNING
    
    def cancel_execution(self):
        """取消执行"""
        if self.config.enable_interruption:
            self._cancel_flag = True
            self._pause_flag = False
            self.execution_status = ExecutionStatus.CANCELLED
    
    def rollback_execution(self):
        """回滚执行"""
        if self.config.enable_rollback:
            self._rollback_flag = True
            self.stats["rollback_operations"] += 1
            
            # 触发回滚回调
            if self.callbacks["on_rollback"]:
                self.callbacks["on_rollback"](self.execution_results)
            
            # 执行回滚
            self._perform_rollback()
            
            self.execution_status = ExecutionStatus.ROLLED_BACK
    
    def _perform_rollback(self):
        """执行回滚"""
        print(f"🔄 执行回滚操作")
        
        # 简单回滚策略：标记所有已执行步骤为回滚状态
        for result in self.execution_results:
            # 在实际应用中，这里会执行具体的回滚操作
            pass
        
        print(f"  回滚完成: {len(self.execution_results)}个步骤")
    
    def _reset_execution_state(self):
        """重置执行状态"""
        self.execution_status = ExecutionStatus.NOT_STARTED
        self.current_step_index = -1
        self.execution_results = []
        
        self._pause_flag = False
        self._cancel_flag = False
        self._rollback_flag = False
    
    def _get_current_stats(self) -> Dict[str, Any]:
        """获取当前统计"""
        return {
            "total_plans_executed": self.stats["total_plans_executed"],
            "total_steps_executed": self.stats["total_steps_executed"],
            "total_steps_succeeded": self.stats["total_steps_succeeded"],
            "total_steps_failed": self.stats["total_steps_failed"],
            "total_execution_time": self.stats["total_execution_time"],
            "avg_step_execution_time": self.stats["avg_step_execution_time"],
            "replan_attempts": self.stats["replan_attempts"],
            "rollback_operations": self.stats["rollback_operations"]
        }
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调函数"""
        if event in self.callbacks:
            self.callbacks[event] = callback
        else:
            raise ValueError(f"未知事件: {event}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "config": self.config.to_dict(),
            "current_state": {
                "execution_status": self.execution_status.value,
                "current_step_index": self.current_step_index,
                "total_results": len(self.execution_results)
            },
            "stats": self._get_current_stats()
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_plans_executed": 0,
            "total_steps_executed": 0,
            "total_steps_succeeded": 0,
            "total_steps_failed": 0,
            "total_execution_time": 0.0,
            "avg_step_execution_time": 0.0,
            "replan_attempts": 0,
            "rollback_operations": 0
        }
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        current_state = stats["current_state"]
        stats_data = stats["stats"]
        
        print(f"   📊 Plan Executor状态:")
        print(f"      配置:")
        print(f"        执行控制:")
        print(f"          最大并发步骤: {config['execution_control']['max_concurrent_steps']}")
        print(f"          启用并行执行: {config['execution_control']['enable_parallel_execution']}")
        print(f"          执行超时: {config['execution_control']['execution_timeout_seconds']}秒")
        
        print(f"        中断和回滚:")
        print(f"          启用中断: {config['interruption_and_rollback']['enable_interruption']}")
        print(f"          启用回滚: {config['interruption_and_rollback']['enable_rollback']}")
        print(f"          回滚策略: {config['interruption_and_rollback']['rollback_strategy']}")
        
        print(f"        重规划:")
        print(f"          启用重规划: {config['replanning']['enable_replanning']}")
        print(f"          重规划阈值: {config['replanning']['replan_threshold']:.2f}")
        print(f"          最大重规划尝试: {config['replanning']['max_replan_attempts']}")
        
        print(f"      当前状态:")
        print(f"        执行状态: {current_state['execution_status']}")
        print(f"        当前步骤索引: {current_state['current_step_index']}")
        print(f"        总结果数: {current_state['total_results']}")
        
        print(f"      统计:")
        print(f"        总执行计划数: {stats_data['total_plans_executed']}")
        print(f"        总执行步骤数: {stats_data['total_steps_executed']}")
        print(f"        成功步骤数: {stats_data['total_steps_succeeded']}")
        print(f"        失败步骤数: {stats_data['total_steps_failed']}")
        print(f"        总执行时间: {stats_data['total_execution_time']:.2f}秒")
        print(f"        平均步骤执行时间: {stats_data['avg_step_execution_time']:.2f}秒")
        print(f"        重规划尝试: {stats_data['replan_attempts']}")
        print(f"        回滚操作: {stats_data['rollback_operations']}")