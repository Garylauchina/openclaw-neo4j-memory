#!/usr/bin/env python3
"""
Action Executor（行动执行器）
核心：执行器强化，支持重试、超时、降级、安全隔离
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
import time
from datetime import datetime
import threading
import queue
import random

# 导入Action类
try:
    from .action_generator import Action, ActionType, ActionRiskLevel
except ImportError:
    # 直接定义（用于独立测试）
    from enum import Enum
    
    class ActionType(Enum):
        API_CALL = "api_call"
        DATA_RETRIEVAL = "data_retrieval"
        ANALYSIS = "analysis"
        DECISION = "decision"
        EXECUTION = "execution"
        EXTERNAL_API = "external_api"
        VALIDATION = "validation"
        REPORTING = "reporting"
    
    class ActionRiskLevel(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    class Action:
        def __init__(self, **kwargs):
            self.id = kwargs.get('id', '')
            self.action_type = kwargs.get('action_type')
            self.target = kwargs.get('target', '')
            self.parameters = kwargs.get('parameters', {})
            self.expected_outcome = kwargs.get('expected_outcome', '')
            self.risk_level = kwargs.get('risk_level', ActionRiskLevel.MEDIUM)
            self.requires_confirmation = kwargs.get('requires_confirmation', False)
            self.real_world_impact = kwargs.get('real_world_impact', False)
            self.fallback_action = kwargs.get('fallback_action')
            self.is_experiment = kwargs.get('is_experiment', False)
            self.hypothesis = kwargs.get('hypothesis')
        
        def get_summary(self):
            return f"{self.action_type.value}: {self.target}"

class ExecutionStatus(Enum):
    """执行状态枚举"""
    PENDING = "pending"          # 等待执行
    EXECUTING = "executing"      # 执行中
    RETRYING = "retrying"        # 重试中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    TIMEOUT = "timeout"          # 超时
    FALLBACK = "fallback"        # 降级执行
    CANCELLED = "cancelled"      # 取消
    SANDBOXED = "sandboxed"      # 沙箱执行

@dataclass
class ExecutionResult:
    """执行结果"""
    action_id: str
    action_type: ActionType
    target: str
    
    # 执行状态
    status: ExecutionStatus
    start_time: datetime
    end_time: datetime
    execution_time: float
    
    # 结果
    result: Any
    error: Optional[str]
    retry_attempts: int
    used_fallback: bool
    
    # 性能指标
    performance_metrics: Dict[str, float]
    
    # 验证标记
    requires_validation: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "target": self.target,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "execution_time": self.execution_time,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "retry_attempts": self.retry_attempts,
            "used_fallback": self.used_fallback,
            "performance_metrics": self.performance_metrics,
            "requires_validation": self.requires_validation
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "status": self.status.value,
            "execution_time": self.execution_time,
            "has_error": self.error is not None,
            "retry_attempts": self.retry_attempts,
            "used_fallback": self.used_fallback
        }

@dataclass
class ActionExecutorConfig:
    """行动执行器配置"""
    # 执行控制
    max_concurrent_actions: int = 3           # 最大并发行动数
    enable_parallel_execution: bool = True    # 启用并行执行
    execution_timeout_seconds: int = 60       # 执行超时时间
    
    # 重试机制
    enable_retry: bool = True                 # 启用重试
    max_retry_count: int = 3                  # 最大重试次数
    retry_delay_seconds: float = 1.0          # 重试延迟
    exponential_backoff: bool = True          # 指数退避
    
    # 降级机制
    enable_fallback: bool = True              # 启用降级
    fallback_timeout_seconds: int = 30        # 降级超时
    
    # 安全隔离
    enable_sandbox: bool = True               # 启用沙箱
    sandbox_for_high_risk: bool = True        # 高风险行动使用沙箱
    sandbox_timeout_seconds: int = 10         # 沙箱超时
    
    # 监控
    enable_monitoring: bool = True            # 启用监控
    monitoring_interval_seconds: float = 0.5  # 监控间隔
    
    def validate(self):
        """验证配置"""
        if self.max_concurrent_actions < 1:
            raise ValueError(f"max_concurrent_actions必须大于0，当前为{self.max_concurrent_actions}")
        
        if self.execution_timeout_seconds < 1:
            raise ValueError(f"execution_timeout_seconds必须大于1秒，当前为{self.execution_timeout_seconds}")
        
        if self.max_retry_count < 0:
            raise ValueError(f"max_retry_count必须大于等于0，当前为{self.max_retry_count}")
        
        if self.retry_delay_seconds < 0:
            raise ValueError(f"retry_delay_seconds必须大于等于0，当前为{self.retry_delay_seconds}")
        
        if self.fallback_timeout_seconds < 1:
            raise ValueError(f"fallback_timeout_seconds必须大于1秒，当前为{self.fallback_timeout_seconds}")
        
        if self.sandbox_timeout_seconds < 1:
            raise ValueError(f"sandbox_timeout_seconds必须大于1秒，当前为{self.sandbox_timeout_seconds}")
        
        if self.monitoring_interval_seconds < 0.1:
            raise ValueError(f"monitoring_interval_seconds必须大于0.1秒，当前为{self.monitoring_interval_seconds}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "execution_control": {
                "max_concurrent_actions": self.max_concurrent_actions,
                "enable_parallel_execution": self.enable_parallel_execution,
                "execution_timeout_seconds": self.execution_timeout_seconds
            },
            "retry_mechanism": {
                "enable_retry": self.enable_retry,
                "max_retry_count": self.max_retry_count,
                "retry_delay_seconds": self.retry_delay_seconds,
                "exponential_backoff": self.exponential_backoff
            },
            "fallback_mechanism": {
                "enable_fallback": self.enable_fallback,
                "fallback_timeout_seconds": self.fallback_timeout_seconds
            },
            "safety_isolation": {
                "enable_sandbox": self.enable_sandbox,
                "sandbox_for_high_risk": self.sandbox_for_high_risk,
                "sandbox_timeout_seconds": self.sandbox_timeout_seconds
            },
            "monitoring": {
                "enable_monitoring": self.enable_monitoring,
                "monitoring_interval_seconds": self.monitoring_interval_seconds
            }
        }

class ActionExecutor:
    """行动执行器"""
    
    def __init__(self, config: Optional[ActionExecutorConfig] = None):
        self.config = config or ActionExecutorConfig()
        self.config.validate()
        
        # 执行状态
        self.execution_status = ExecutionStatus.PENDING
        self.current_action: Optional[Action] = None
        self.execution_results: List[ExecutionResult] = []
        
        # 控制标志
        self._pause_flag = False
        self._cancel_flag = False
        self._sandbox_flag = False
        
        # 执行队列和线程池
        self._execution_queue = queue.Queue()
        self._worker_threads: List[threading.Thread] = []
        self._thread_pool_size = self.config.max_concurrent_actions
        
        # 统计信息
        self.stats = {
            "total_actions_executed": 0,
            "total_actions_succeeded": 0,
            "total_actions_failed": 0,
            "total_retry_attempts": 0,
            "total_fallback_executions": 0,
            "total_sandbox_executions": 0,
            "total_execution_time": 0.0,
            "avg_execution_time": 0.0,
            "timeout_count": 0
        }
        
        # 回调函数
        self.callbacks = {
            "on_action_start": None,
            "on_action_complete": None,
            "on_action_fail": None,
            "on_retry": None,
            "on_fallback": None,
            "on_sandbox": None,
            "on_timeout": None
        }
        
        # 初始化线程池
        self._initialize_thread_pool()
    
    def _initialize_thread_pool(self):
        """初始化线程池"""
        if self.config.enable_parallel_execution:
            for i in range(self._thread_pool_size):
                thread = threading.Thread(
                    target=self._worker_loop,
                    name=f"action_executor_worker_{i}",
                    daemon=True
                )
                thread.start()
                self._worker_threads.append(thread)
    
    def _worker_loop(self):
        """工作线程循环"""
        while True:
            try:
                # 从队列获取任务
                task = self._execution_queue.get(timeout=1.0)
                if task is None:  # 停止信号
                    break
                
                action, context, callback = task
                self._execute_single_action(action, context, callback)
                
                self._execution_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"工作线程错误: {e}")
                continue
    
    def execute_action(self, action: Action,
                      context: Optional[Dict[str, Any]] = None,
                      callback: Optional[Callable] = None) -> ExecutionResult:
        """
        执行单个行动
        
        Args:
            action: 要执行的行动
            context: 上下文信息
            callback: 完成回调
        
        Returns:
            ExecutionResult: 执行结果
        """
        import time
        start_time = time.time()
        
        # 更新状态
        self.execution_status = ExecutionStatus.EXECUTING
        self.current_action = action
        
        # 触发开始回调
        if self.callbacks["on_action_start"]:
            self.callbacks["on_action_start"](action)
        
        # 检查是否需要沙箱执行
        use_sandbox = False
        if self.config.enable_sandbox:
            if self.config.sandbox_for_high_risk and action.risk_level in [ActionRiskLevel.HIGH, ActionRiskLevel.CRITICAL]:
                use_sandbox = True
            elif self._sandbox_flag:
                use_sandbox = True
        
        # 执行行动
        if use_sandbox:
            result = self._execute_in_sandbox(action, context)
        elif self.config.enable_parallel_execution:
            # 放入队列并行执行
            result = self._execute_parallel(action, context, callback)
        else:
            # 顺序执行
            result = self._execute_sequential(action, context)
        
        # 计算执行时间
        execution_time = time.time() - start_time
        
        # 更新行动状态
        action.execution_status = result.status.value
        action.execution_result = result.result
        action.execution_error = result.error
        action.execution_time = execution_time
        action.retry_attempts = result.retry_attempts
        
        # 更新统计
        self._update_stats(result, execution_time)
        
        # 触发完成回调
        if result.status == ExecutionStatus.COMPLETED:
            if self.callbacks["on_action_complete"]:
                self.callbacks["on_action_complete"](result)
        else:
            if self.callbacks["on_action_fail"]:
                self.callbacks["on_action_fail"](result)
        
        # 用户回调
        if callback:
            callback(result)
        
        return result
    
    def execute_actions(self, actions: List[Action],
                       context: Optional[Dict[str, Any]] = None) -> List[ExecutionResult]:
        """
        执行多个行动
        
        Args:
            actions: 行动列表
            context: 上下文信息
        
        Returns:
            List[ExecutionResult]: 执行结果列表
        """
        results = []
        
        for action in actions:
            result = self.execute_action(action, context)
            results.append(result)
            
            # 检查是否需要停止
            if self._cancel_flag:
                break
        
        return results
    
    def _execute_sequential(self, action: Action,
                          context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """顺序执行行动"""
        start_time = datetime.now()
        retry_attempts = 0
        used_fallback = False
        
        try:
            # 主执行
            result = self._execute_core(action, context, start_time)
            
            # 检查是否需要重试
            if (self.config.enable_retry and 
                result.status != ExecutionStatus.COMPLETED and 
                retry_attempts < self.config.max_retry_count):
                
                result = self._execute_with_retry(action, context, start_time)
                retry_attempts = result.retry_attempts
            
            # 检查是否需要降级
            if (self.config.enable_fallback and 
                result.status != ExecutionStatus.COMPLETED and 
                action.fallback_action):
                
                result = self._execute_fallback(action, context, start_time)
                used_fallback = True
            
            return result
            
        except Exception as e:
            # 执行异常
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return ExecutionResult(
                action_id=action.id,
                action_type=action.action_type,
                target=action.target,
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                result=None,
                error=str(e),
                retry_attempts=retry_attempts,
                used_fallback=used_fallback,
                performance_metrics={}
            )
    
    def _execute_parallel(self, action: Action,
                        context: Optional[Dict[str, Any]],
                        callback: Optional[Callable]) -> ExecutionResult:
        """并行执行行动"""
        # 创建结果占位符
        result_placeholder = ExecutionResult(
            action_id=action.id,
            action_type=action.action_type,
            target=action.target,
            status=ExecutionStatus.PENDING,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=0.0,
            result=None,
            error=None,
            retry_attempts=0,
            used_fallback=False,
            performance_metrics={}
        )
        
        # 放入队列
        self._execution_queue.put((action, context, callback))
        
        return result_placeholder
    
    def _execute_in_sandbox(self, action: Action,
                          context: Optional[Dict[str, Any]]) -> ExecutionResult:
        """在沙箱中执行行动"""
        start_time = datetime.now()
        
        # 触发沙箱回调
        if self.callbacks["on_sandbox"]:
            self.callbacks["on_sandbox"](action)
        
        print(f"🛡️  在沙箱中执行高风险行动: {action.action_type.value} - {action.target}")
        
        try:
            # 沙箱执行（模拟）
            time.sleep(0.5)  # 模拟沙箱初始化
            
            # 执行核心逻辑（在沙箱中）
            result = self._execute_core(action, context, start_time, sandbox=True)
            
            # 更新统计
            self.stats["total_sandbox_executions"] += 1
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return ExecutionResult(
                action_id=action.id,
                action_type=action.action_type,
                target=action.target,
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                result=None,
                error=f"沙箱执行失败: {str(e)}",
                retry_attempts=0,
                used_fallback=False,
                performance_metrics={}
            )
    
    def _execute_core(self, action: Action,
                     context: Optional[Dict[str, Any]],
                     start_time: datetime,
                     sandbox: bool = False) -> ExecutionResult:
        """执行核心逻辑"""
        import time
        import random
        
        # 模拟执行时间
        execution_time = random.uniform(0.1, 2.0)
        
        # 检查超时
        if execution_time > self.config.execution_timeout_seconds:
            end_time = datetime.now()
            actual_time = (end_time - start_time).total_seconds()
            
            # 触发超时回调
            if self.callbacks["on_timeout"]:
                self.callbacks["on_timeout"](action, actual_time)
            
            self.stats["timeout_count"] += 1
            
            return ExecutionResult(
                action_id=action.id,
                action_type=action.action_type,
                target=action.target,
                status=ExecutionStatus.TIMEOUT,
                start_time=start_time,
                end_time=end_time,
                execution_time=actual_time,
                result=None,
                error=f"执行超时: {actual_time:.2f}秒 > {self.config.execution_timeout_seconds}秒",
                retry_attempts=0,
                used_fallback=False,
                performance_metrics={
                    "timeout_duration": actual_time,
                    "timeout_threshold": self.config.execution_timeout_seconds
                }
            )
        
        # 模拟执行
        time.sleep(execution_time)
        
        # 生成模拟结果
        result_data = self._generate_mock_result(action, context, sandbox)
        
        # 检查是否模拟失败
        if random.random() < 0.2:  # 20%失败率
            end_time = datetime.now()
            actual_time = (end_time - start_time).total_seconds()
            
            error_msg = random.choice([
                "网络连接失败",
                "服务不可用",
                "数据格式错误",
                "权限不足",
                "资源限制"
            ])
            
            return ExecutionResult(
                action_id=action.id,
                action_type=action.action_type,
                target=action.target,
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=actual_time,
                result=None,
                error=error_msg,
                retry_attempts=0,
                used_fallback=False,
                performance_metrics={
                    "execution_speed": execution_time,
                    "success": False
                }
            )
        
        # 成功执行
        end_time = datetime.now()
        actual_time = (end_time - start_time).total_seconds()
        
        return ExecutionResult(
            action_id=action.id,
            action_type=action.action_type,
            target=action.target,
            status=ExecutionStatus.COMPLETED,
            start_time=start_time,
            end_time=end_time,
            execution_time=actual_time,
            result=result_data,
            error=None,
            retry_attempts=0,
            used_fallback=False,
            performance_metrics={
                "execution_speed": execution_time,
                "success": True,
                "result_quality": random.uniform(0.7, 0.95)
            }
        )
    
    def _execute_with_retry(self, action: Action,
                          context: Optional[Dict[str, Any]],
                          start_time: datetime) -> ExecutionResult:
        """带重试的执行"""
        retry_attempts = 0
        
        while retry_attempts < self.config.max_retry_count:
            retry_attempts += 1
            self.stats["total_retry_attempts"] += 1
            
            # 触发重试回调
            if self.callbacks["on_retry"]:
                self.callbacks["on_retry"](action, retry_attempts)
            
            print(f"🔄 重试行动: {action.action_type.value} - {action.target} (尝试 {retry_attempts}/{self.config.max_retry_count})")
            
            # 应用重试延迟
            if self.config.exponential_backoff:
                delay = self.config.retry_delay_seconds * (2 ** (retry_attempts - 1))
            else:
                delay = self.config.retry_delay_seconds
            
            time.sleep(delay)
            
            # 重试执行
            result = self._execute_core(action, context, datetime.now())
            
            if result.status == ExecutionStatus.COMPLETED:
                # 重试成功
                result.retry_attempts = retry_attempts
                return result
        
        # 重试失败
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return ExecutionResult(
            action_id=action.id,
            action_type=action.action_type,
            target=action.target,
            status=ExecutionStatus.FAILED,
            start_time=start_time,
            end_time=end_time,
            execution_time=execution_time,
            result=None,
            error=f"重试{retry_attempts}次后仍然失败",
            retry_attempts=retry_attempts,
            used_fallback=False,
            performance_metrics={
                "retry_attempts": retry_attempts,
                "total_retry_time": execution_time
            }
        )
    
    def _execute_fallback(self, action: Action,
                        context: Optional[Dict[str, Any]],
                        start_time: datetime) -> ExecutionResult:
        """执行降级行动"""
        if not action.fallback_action:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return ExecutionResult(
                action_id=action.id,
                action_type=action.action_type,
                target=action.target,
                status=ExecutionStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                result=None,
                error="无降级行动可用",
                retry_attempts=0,
                used_fallback=False,
                performance_metrics={}
            )
        
        # 触发降级回调
        if self.callbacks["on_fallback"]:
            self.callbacks["on_fallback"](action, action.fallback_action)
        
        print(f"🔄 执行降级行动: {action.fallback_action.action_type.value} - {action.fallback_action.target}")
        
        # 执行降级行动
        fallback_result = self._execute_core(action.fallback_action, context, datetime.now())
        
        # 更新统计
        self.stats["total_fallback_executions"] += 1
        
        # 标记为降级执行
        fallback_result.used_fallback = True
        fallback_result.status = ExecutionStatus.FALLBACK
        
        return fallback_result
    
    def _generate_mock_result(self, action: Action,
                            context: Optional[Dict[str, Any]],
                            sandbox: bool = False) -> Dict[str, Any]:
        """生成模拟结果"""
        import random
        
        base_result = {
            "action_id": action.id,
            "action_type": action.action_type.value,
            "target": action.target,
            "timestamp": datetime.now().isoformat(),
            "sandbox_execution": sandbox
        }
        
        # 基于行动类型生成特定结果
        if action.action_type == ActionType.API_CALL:
            result = {
                **base_result,
                "status": "success",
                "data": {
                    "items": random.randint(10, 100),
                    "processing_time_ms": random.randint(50, 500),
                    "source": action.parameters.get("region", "unknown")
                },
                "metadata": {
                    "api_version": "v1.0",
                    "rate_limit_remaining": random.randint(1, 1000)
                }
            }
        elif action.action_type == ActionType.DATA_RETRIEVAL:
            result = {
                **base_result,
                "status": "success",
                "data_count": random.randint(100, 10000),
                "data_quality": random.uniform(0.8, 0.99),
                "retrieval_time_ms": random.randint(100, 1000)
            }
        elif action.action_type == ActionType.ANALYSIS:
            result = {
                **base_result,
                "status": "success",
                "insights": [
                    f"洞察{random.randint(1, 5)}: 趋势分析结果",
                    f"洞察{random.randint(6, 10)}: 模式识别发现"
                ],
                "confidence": random.uniform(0.7, 0.95),
                "recommendations": [
                    "建议1: 优化资源配置",
                    "建议2: 调整执行策略"
                ]
            }
        elif action.action_type == ActionType.DECISION:
            options = ["option_A", "option_B", "option_C", "option_D"]
            result = {
                **base_result,
                "status": "success",
                "selected_option": random.choice(options),
                "decision_criteria": action.parameters.get("criteria", ["cost", "benefit", "risk"]),
                "confidence_score": random.uniform(0.6, 0.9),
                "rationale": "基于多维度分析和风险评估"
            }
        elif action.action_type == ActionType.EXECUTION:
            result = {
                **base_result,
                "status": "success",
                "execution_outcome": "completed",
                "completion_percentage": 100,
                "next_steps": ["监控效果", "收集反馈", "优化迭代"]
            }
        elif action.action_type == ActionType.EXTERNAL_API:
            result = {
                **base_result,
                "status": "success",
                "external_service": action.target,
                "response_time_ms": random.randint(200, 2000),
                "data": {
                    "result": "external_data_retrieved",
                    "validity": random.uniform(0.85, 0.98)
                }
            }
        else:
            result = {
                **base_result,
                "status": "success",
                "result": f"完成{action.action_type.value}行动",
                "details": action.parameters
            }
        
        # 如果是实验行动，添加实验数据
        if action.is_experiment:
            result["experiment_data"] = {
                "hypothesis": action.hypothesis,
                "expected_outcome": action.expected_outcome,
                "actual_outcome": "符合预期" if random.random() > 0.3 else "部分符合预期",
                "hypothesis_test_result": random.choice(["supported", "partially_supported", "inconclusive"])
            }
        
        return result
    
    def _update_stats(self, result: ExecutionResult, execution_time: float):
        """更新统计信息"""
        self.stats["total_actions_executed"] += 1
        
        if result.status == ExecutionStatus.COMPLETED:
            self.stats["total_actions_succeeded"] += 1
        else:
            self.stats["total_actions_failed"] += 1
        
        self.stats["total_execution_time"] += execution_time
        
        # 更新平均执行时间
        self.stats["avg_execution_time"] = (
            (self.stats["avg_execution_time"] * (self.stats["total_actions_executed"] - 1) + execution_time)
            / self.stats["total_actions_executed"]
        )
    
    def pause_execution(self):
        """暂停执行"""
        self._pause_flag = True
        self.execution_status = ExecutionStatus.PENDING
    
    def resume_execution(self):
        """恢复执行"""
        self._pause_flag = False
        self.execution_status = ExecutionStatus.EXECUTING
    
    def cancel_execution(self):
        """取消执行"""
        self._cancel_flag = True
        self._pause_flag = False
        self.execution_status = ExecutionStatus.CANCELLED
    
    def enable_sandbox(self):
        """启用沙箱模式"""
        self._sandbox_flag = True
    
    def disable_sandbox(self):
        """禁用沙箱模式"""
        self._sandbox_flag = False
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调函数"""
        if event in self.callbacks:
            self.callbacks[event] = callback
        else:
            raise ValueError(f"未知事件: {event}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_actions = self.stats["total_actions_executed"]
        
        success_rate = 0.0
        if total_actions > 0:
            success_rate = self.stats["total_actions_succeeded"] / total_actions
        
        return {
            "config": self.config.to_dict(),
            "current_state": {
                "execution_status": self.execution_status.value,
                "current_action": self.current_action.get_summary() if self.current_action else None,
                "total_results": len(self.execution_results)
            },
            "stats": {
                "total_actions_executed": self.stats["total_actions_executed"],
                "total_actions_succeeded": self.stats["total_actions_succeeded"],
                "total_actions_failed": self.stats["total_actions_failed"],
                "success_rate": success_rate,
                "total_retry_attempts": self.stats["total_retry_attempts"],
                "total_fallback_executions": self.stats["total_fallback_executions"],
                "total_sandbox_executions": self.stats["total_sandbox_executions"],
                "total_execution_time": self.stats["total_execution_time"],
                "avg_execution_time": self.stats["avg_execution_time"],
                "timeout_count": self.stats["timeout_count"]
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_actions_executed": 0,
            "total_actions_succeeded": 0,
            "total_actions_failed": 0,
            "total_retry_attempts": 0,
            "total_fallback_executions": 0,
            "total_sandbox_executions": 0,
            "total_execution_time": 0.0,
            "avg_execution_time": 0.0,
            "timeout_count": 0
        }
        self.execution_results = []
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        current_state = stats["current_state"]
        stats_data = stats["stats"]
        
        print(f"   📊 Action Executor状态:")
        print(f"      配置:")
        print(f"        执行控制:")
        print(f"          最大并发行动: {config['execution_control']['max_concurrent_actions']}")
        print(f"          启用并行执行: {config['execution_control']['enable_parallel_execution']}")
        print(f"          执行超时: {config['execution_control']['execution_timeout_seconds']}秒")
        
        print(f"        重试机制:")
        print(f"          启用重试: {config['retry_mechanism']['enable_retry']}")
        print(f"          最大重试次数: {config['retry_mechanism']['max_retry_count']}")
        print(f"          重试延迟: {config['retry_mechanism']['retry_delay_seconds']}秒")
        print(f"          指数退避: {config['retry_mechanism']['exponential_backoff']}")
        
        print(f"        降级机制:")
        print(f"          启用降级: {config['fallback_mechanism']['enable_fallback']}")
        print(f"          降级超时: {config['fallback_mechanism']['fallback_timeout_seconds']}秒")
        
        print(f"        安全隔离:")
        print(f"          启用沙箱: {config['safety_isolation']['enable_sandbox']}")
        print(f"          高风险使用沙箱: {config['safety_isolation']['sandbox_for_high_risk']}")
        print(f"          沙箱超时: {config['safety_isolation']['sandbox_timeout_seconds']}秒")
        
        print(f"      当前状态:")
        print(f"        执行状态: {current_state['execution_status']}")
        print(f"        当前行动: {current_state['current_action']}")
        print(f"        总结果数: {current_state['total_results']}")
        
        print(f"      统计:")
        print(f"        总执行行动数: {stats_data['total_actions_executed']}")
        print(f"        成功行动数: {stats_data['total_actions_succeeded']}")
        print(f"        失败行动数: {stats_data['total_actions_failed']}")
        print(f"        成功率: {stats_data['success_rate']:.1%}")
        print(f"        总重试尝试: {stats_data['total_retry_attempts']}")
        print(f"        总降级执行: {stats_data['total_fallback_executions']}")
        print(f"        总沙箱执行: {stats_data['total_sandbox_executions']}")
        print(f"        总执行时间: {stats_data['total_execution_time']:.2f}秒")
        print(f"        平均执行时间: {stats_data['avg_execution_time']:.2f}秒")
        print(f"        超时次数: {stats_data['timeout_count']}")