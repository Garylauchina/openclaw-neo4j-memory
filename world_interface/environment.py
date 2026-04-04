#!/usr/bin/env python3
"""
World Interface - Environment 抽象层
核心：所有 Action 必须经过 Environment，不允许"直接返回结果"
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import time
from datetime import datetime
import json

@dataclass
class Action:
    """新 Action 结构（强制）"""
    type: str                    # "api_call", "db_query", "file_operation"
    target: str                  # "weather_api", "database", "file_system"
    params: Dict[str, Any]       # 参数
    
    # 现实约束
    expected_effect: str         # 预期效果描述
    observable_signal: str       # 可观测信号
    timeout_seconds: int = 30    # 超时时间
    retry_count: int = 3         # 重试次数
    
    # 元数据
    action_id: str = field(default_factory=lambda: str(time.time()))
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_id": self.action_id,
            "type": self.type,
            "target": self.target,
            "params": self.params,
            "expected_effect": self.expected_effect,
            "observable_signal": self.observable_signal,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat()
        }

@dataclass
class ExecutionResult:
    """执行结果"""
    action_id: str
    action_type: str
    target: str
    
    # 执行状态
    status: str                  # "success", "failed", "timeout"
    start_time: datetime
    end_time: datetime
    execution_time: float        # 秒
    
    # 结果数据
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # 现实指标
    latency_ms: float = 0.0      # 延迟
    resource_usage: float = 0.0  # 资源使用率
    risk: float = 0.0            # 风险评估
    
    # 元数据
    retry_attempts: int = 0
    used_fallback: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "target": self.target,
            "status": self.status,
            "execution_time": self.execution_time,
            "latency_ms": self.latency_ms,
            "resource_usage": self.resource_usage,
            "risk": self.risk,
            "result": self.result,
            "error": self.error,
            "retry_attempts": self.retry_attempts,
            "used_fallback": self.used_fallback,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat()
        }

class Connector:
    """现实接口插件基类"""
    
    def __init__(self, name: str, connector_type: str):
        self.name = name
        self.connector_type = connector_type
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency_ms": 0.0,
            "avg_latency_ms": 0.0
        }
    
    def can_handle(self, action: Action) -> bool:
        """检查是否能处理该行动"""
        raise NotImplementedError
    
    def execute(self, action: Action) -> ExecutionResult:
        """执行行动"""
        raise NotImplementedError
    
    def observe(self) -> Dict[str, Any]:
        """观察环境状态"""
        return {
            "connector_name": self.name,
            "connector_type": self.connector_type,
            "stats": self.stats,
            "health": "ok" if self.stats["failed_requests"] < 10 else "degraded"
        }
    
    def _update_stats(self, success: bool, latency_ms: float):
        """更新统计信息"""
        self.stats["total_requests"] += 1
        
        if success:
            self.stats["successful_requests"] += 1
        else:
            self.stats["failed_requests"] += 1
        
        self.stats["total_latency_ms"] += latency_ms
        self.stats["avg_latency_ms"] = (
            self.stats["total_latency_ms"] / self.stats["total_requests"]
        )

class APIConnector(Connector):
    """API连接器"""
    
    def __init__(self, name: str = "default_api"):
        super().__init__(name, "api")
        self.base_url = "https://api.weatherapi.com/v1"  # 示例API
    
    def can_handle(self, action: Action) -> bool:
        """检查是否能处理API调用"""
        return action.type == "api_call" and action.target == "weather_api"
    
    def execute(self, action: Action) -> ExecutionResult:
        """执行API调用"""
        import requests
        start_time = datetime.now()
        
        try:
            # 模拟真实API调用（实际使用时替换为真实调用）
            if action.params.get("mock", False):
                # 模拟模式
                time.sleep(0.1)  # 模拟延迟
                result = {
                    "location": action.params.get("location", "Tokyo"),
                    "temperature": 22.5,
                    "condition": "Sunny",
                    "humidity": 65,
                    "wind_speed": 12.3,
                    "timestamp": datetime.now().isoformat()
                }
                status = "success"
                error = None
                latency = 100  # 模拟100ms延迟
            else:
                # 真实API调用（需要API密钥）
                # 实际使用时取消注释
                # response = requests.get(
                #     f"{self.base_url}/current.json",
                #     params={
                #         "key": "YOUR_API_KEY",
                #         "q": action.params.get("location", "Tokyo")
                #     },
                #     timeout=action.timeout_seconds
                # )
                # response.raise_for_status()
                # result = response.json()
                # status = "success"
                # error = None
                # latency = response.elapsed.total_seconds() * 1000
                
                # 暂时使用模拟
                time.sleep(0.15)
                result = {
                    "location": action.params.get("location", "Tokyo"),
                    "temperature": 22.5,
                    "condition": "Sunny",
                    "humidity": 65,
                    "wind_speed": 12.3,
                    "timestamp": datetime.now().isoformat(),
                    "note": "模拟数据（实际需要API密钥）"
                }
                status = "success"
                error = None
                latency = 150
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 更新统计
            self._update_stats(True, latency)
            
            return ExecutionResult(
                action_id=action.action_id,
                action_type=action.type,
                target=action.target,
                status=status,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                result=result,
                error=error,
                latency_ms=latency,
                resource_usage=0.1,  # API调用资源使用
                risk=0.05  # 低风险
            )
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 更新统计
            self._update_stats(False, execution_time * 1000)
            
            return ExecutionResult(
                action_id=action.action_id,
                action_type=action.type,
                target=action.target,
                status="failed",
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                result=None,
                error=str(e),
                latency_ms=execution_time * 1000,
                resource_usage=0.2,  # 失败时资源使用更高
                risk=0.3  # 失败增加风险
            )

class FileConnector(Connector):
    """文件系统连接器"""
    
    def __init__(self, name: str = "file_system"):
        super().__init__(name, "file")
        self.base_path = "/tmp/world_interface"
    
    def can_handle(self, action: Action) -> bool:
        """检查是否能处理文件操作"""
        return action.type == "file_operation"
    
    def execute(self, action: Action) -> ExecutionResult:
        """执行文件操作"""
        import os
        import json as json_module
        start_time = datetime.now()
        
        try:
            operation = action.params.get("operation", "read")
            file_path = action.params.get("file_path", "default.json")
            full_path = os.path.join(self.base_path, file_path)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            if operation == "write":
                data = action.params.get("data", {})
                with open(full_path, 'w') as f:
                    json_module.dump(data, f, indent=2)
                result = {"status": "written", "file_path": full_path}
                
            elif operation == "read":
                if os.path.exists(full_path):
                    with open(full_path, 'r') as f:
                        data = json_module.load(f)
                    result = {"status": "read", "data": data}
                else:
                    result = {"status": "not_found", "file_path": full_path}
                    
            elif operation == "append":
                data = action.params.get("data", {})
                existing_data = []
                if os.path.exists(full_path):
                    with open(full_path, 'r') as f:
                        existing_data = json_module.load(f)
                        if not isinstance(existing_data, list):
                            existing_data = [existing_data]
                
                existing_data.append(data)
                with open(full_path, 'w') as f:
                    json_module.dump(existing_data, f, indent=2)
                result = {"status": "appended", "count": len(existing_data)}
                
            else:
                raise ValueError(f"未知操作: {operation}")
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 更新统计
            self._update_stats(True, execution_time * 1000)
            
            return ExecutionResult(
                action_id=action.action_id,
                action_type=action.type,
                target=action.target,
                status="success",
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                result=result,
                error=None,
                latency_ms=execution_time * 1000,
                resource_usage=0.05,  # 文件操作资源使用低
                risk=0.02  # 低风险
            )
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 更新统计
            self._update_stats(False, execution_time * 1000)
            
            return ExecutionResult(
                action_id=action.action_id,
                action_type=action.type,
                target=action.target,
                status="failed",
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                result=None,
                error=str(e),
                latency_ms=execution_time * 1000,
                resource_usage=0.1,
                risk=0.1
            )

class DatabaseConnector(Connector):
    """数据库连接器（模拟）"""
    
    def __init__(self, name: str = "database"):
        super().__init__(name, "database")
        self.data_store = {}  # 模拟数据库
    
    def can_handle(self, action: Action) -> bool:
        """检查是否能处理数据库查询"""
        return action.type == "db_query"
    
    def execute(self, action: Action) -> ExecutionResult:
        """执行数据库查询"""
        start_time = datetime.now()
        
        try:
            query_type = action.params.get("query_type", "select")
            table = action.params.get("table", "default")
            data = action.params.get("data", {})
            
            # 初始化表
            if table not in self.data_store:
                self.data_store[table] = []
            
            if query_type == "insert":
                record_id = str(len(self.data_store[table]) + 1)
                record = {"id": record_id, **data, "created_at": datetime.now().isoformat()}
                self.data_store[table].append(record)
                result = {"status": "inserted", "id": record_id, "table": table}
                
            elif query_type == "select":
                filters = action.params.get("filters", {})
                records = self.data_store[table]
                
                # 简单过滤
                if filters:
                    filtered = []
                    for record in records:
                        match = True
                        for key, value in filters.items():
                            if key in record and record[key] != value:
                                match = False
                                break
                        if match:
                            filtered.append(record)
                    result = {"status": "selected", "count": len(filtered), "records": filtered}
                else:
                    result = {"status": "selected", "count": len(records), "records": records}
                    
            elif query_type == "update":
                record_id = action.params.get("id")
                updates = action.params.get("updates", {})
                
                for i, record in enumerate(self.data_store[table]):
                    if record.get("id") == record_id:
                        self.data_store[table][i].update(updates)
                        self.data_store[table][i]["updated_at"] = datetime.now().isoformat()
                        result = {"status": "updated", "id": record_id, "table": table}
                        break
                else:
                    result = {"status": "not_found", "id": record_id}
                    
            else:
                raise ValueError(f"未知查询类型: {query_type}")
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 更新统计
            self._update_stats(True, execution_time * 1000)
            
            return ExecutionResult(
                action_id=action.action_id,
                action_type=action.type,
                target=action.target,
                status="success",
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                result=result,
                error=None,
                latency_ms=execution_time * 1000,
                resource_usage=0.08,
                risk=0.03
            )
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 更新统计
            self._update_stats(False, execution_time * 1000)
            
            return ExecutionResult(
                action_id=action.action_id,
                action_type=action.type,
                target=action.target,
                status="failed",
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                result=None,
                error=str(e),
                latency_ms=execution_time * 1000,
                resource_usage=0.15,
                risk=0.08
            )

class Environment:
    """环境抽象层"""
    
    def __init__(self):
        self.connectors: List[Connector] = []
        self.action_history: List[Dict[str, Any]] = []
        self.result_history: List[Dict[str, Any]] = []
        
        # 安全机制
        self.action_budget = 1000  # 行动预算
        self.total_cost = 0.0
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        
        # 统计
        self.stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0
        }
    
    def register(self, connector: Connector):
        """注册连接器"""
        self.connectors.append(connector)
        print(f"✅ 注册连接器: {connector.name} ({connector.connector_type})")
    
    def act(self, action: Action) -> ExecutionResult:
        """
        执行行动
        
        ❗ 所有 Action 必须经过 Environment
        ❗ 不允许"直接返回结果"
        """
        # 检查预算
        if self.total_cost >= self.action_budget:
            return ExecutionResult(
                action_id=action.action_id,
                action_type=action.type,
                target=action.target,
                status="failed",
                start_time=datetime.now(),
                end_time=datetime.now(),
                execution_time=0.0,
                result=None,
                error="行动预算已用完",
                latency_ms=0.0,
                resource_usage=0.0,
                risk=0.0
            )
        
        # 检查连续失败
        if self.consecutive_failures >= self.max_consecutive_failures:
            return ExecutionResult(
                action_id=action.action_id,
                action_type=action.type,
                target=action.target,
                status="failed",
                start_time=datetime.now(),
                end_time=datetime.now(),
                execution_time=0.0,
                result=None,
                error=f"连续失败次数过多: {self.consecutive_failures}",
                latency_ms=0.0,
                resource_usage=0.0,
                risk=0.0
            )
        
        # 查找合适的连接器
        for connector in self.connectors:
            if connector.can_handle(action):
                print(f"🔗 使用连接器: {connector.name} 处理行动: {action.type} -> {action.target}")
                
                # 执行行动
                result = connector.execute(action)
                
                # 更新统计
                self._update_stats(result)
                
                # 记录历史
                self.action_history.append(action.to_dict())
                self.result_history.append(result.to_dict())
                
                # 更新连续失败计数
                if result.status == "success":
                    self.consecutive_failures = 0
                else:
                    self.consecutive_failures += 1
                
                return result
        
        # 没有找到合适的连接器
        print(f"⚠️  没有连接器能处理行动: {action.type} -> {action.target}")
        
        result = ExecutionResult(
            action_id=action.action_id,
            action_type=action.type,
            target=action.target,
            status="failed",
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=0.0,
            result=None,
            error=f"没有连接器能处理该行动: {action.type} -> {action.target}",
            latency_ms=0.0,
            resource_usage=0.0,
            risk=0.0
        )
        
        self._update_stats(result)
        return result
    
    def observe(self) -> List[Dict[str, Any]]:
        """观察环境状态"""
        observations = []
        
        for connector in self.connectors:
            observations.append(connector.observe())
        
        # 添加环境状态
        observations.append({
            "type": "environment_status",
            "total_actions": self.stats["total_actions"],
            "success_rate": (
                self.stats["successful_actions"] / self.stats["total_actions"]
                if self.stats["total_actions"] > 0 else 0.0
            ),
            "total_cost": self.total_cost,
            "budget_remaining": self.action_budget - self.total_cost,
            "consecutive_failures": self.consecutive_failures,
            "avg_latency_ms": self.stats["avg_latency_ms"]
        })
        
        return observations
    
    def _update_stats(self, result: ExecutionResult):
        """更新统计信息"""
        self.stats["total_actions"] += 1
        
        if result.status == "success":
            self.stats["successful_actions"] += 1
        else:
            self.stats["failed_actions"] += 1
        
        # 计算成本
        cost = self._compute_cost(result)
        self.total_cost += cost
        self.stats["total_cost"] = self.total_cost
        
        # 更新平均延迟
        total_latency = self.stats["avg_latency_ms"] * (self.stats["total_actions"] - 1)
        self.stats["avg_latency_ms"] = (total_latency + result.latency_ms) / self.stats["total_actions"]
    
    def _compute_cost(self, result: ExecutionResult) -> float:
        """计算行动成本"""
        # cost定义
        latency_penalty = min(1.0, result.latency_ms / 1000)  # 1秒内完成得满分
        resource_penalty = result.resource_usage
        risk_penalty = result.risk
        
        cost = (
            0.4 * latency_penalty +
            0.3 * resource_penalty +
            0.3 * risk_penalty
        )
        
        return cost
    
    def reset(self):
        """重置环境"""
        self.action_history = []
        self.result_history = []
        self.total_cost = 0.0
        self.consecutive_failures = 0
        
        self.stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0
        }
        
        for connector in self.connectors:
            connector.stats = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_latency_ms": 0.0,
                "avg_latency_ms": 0.0
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取环境状态"""
        return {
            "connectors": [c.name for c in self.connectors],
            "stats": self.stats,
            "budget": {
                "total": self.action_budget,
                "used": self.total_cost,
                "remaining": self.action_budget - self.total_cost,
                "usage_percentage": (self.total_cost / self.action_budget * 100) if self.action_budget > 0 else 0
            },
            "safety": {
                "consecutive_failures": self.consecutive_failures,
                "max_consecutive_failures": self.max_consecutive_failures,
                "needs_intervention": self.consecutive_failures >= self.max_consecutive_failures
            },
            "history": {
                "total_actions": len(self.action_history),
                "total_results": len(self.result_history)
            }
        }
    
    def print_status(self):
        """打印状态"""
        status = self.get_status()
        observations = self.observe()
        
        print(f"   🌍 World Interface状态:")
        print(f"      连接器: {', '.join(status['connectors'])}")
        print(f"      统计:")
        print(f"        总行动数: {status['stats']['total_actions']}")
        print(f"        成功行动: {status['stats']['successful_actions']}")
        print(f"        失败行动: {status['stats']['failed_actions']}")
        print(f"        成功率: {status['stats']['successful_actions']/status['stats']['total_actions']:.1%}" 
              if status['stats']['total_actions'] > 0 else "        成功率: 0.0%")
        print(f"        总成本: {status['stats']['total_cost']:.3f}")
        print(f"        平均延迟: {status['stats']['avg_latency_ms']:.1f}ms")
        
        print(f"      预算:")
        print(f"        总预算: {status['budget']['total']}")
        print(f"        已使用: {status['budget']['used']:.3f}")
        print(f"        剩余: {status['budget']['remaining']:.3f}")
        print(f"        使用率: {status['budget']['usage_percentage']:.1f}%")
        
        print(f"      安全:")
        print(f"        连续失败: {status['safety']['consecutive_failures']}")
        print(f"        最大允许失败: {status['safety']['max_consecutive_failures']}")
        print(f"        需要干预: {status['safety']['needs_intervention']}")
        
        print(f"      观察:")
        for obs in observations[:3]:  # 只显示前3个观察
            if "connector_name" in obs:
                print(f"        {obs['connector_name']}: {obs['health']}")