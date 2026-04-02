#!/usr/bin/env python3
"""
World Model Interface - 多API环境接口
核心：构建统一的世界模型接口，支持多种API
"""

import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import random

class EnvironmentAction:
    """环境行动"""
    
    def __init__(self, 
                 action_type: str,
                 params: Dict[str, Any],
                 expected_effect: str = "",
                 timeout_seconds: int = 5):
        self.type = action_type
        self.params = params
        self.expected_effect = expected_effect
        self.timeout_seconds = timeout_seconds
        self.action_id = f"action_{int(time.time())}"
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_id": self.action_id,
            "type": self.type,
            "params": self.params,
            "expected_effect": self.expected_effect,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat()
        }

class EnvironmentResult:
    """环境结果"""
    
    def __init__(self,
                 action_id: str,
                 action_type: str,
                 status: str,
                 data: Any,
                 latency: float,
                 cost: float,
                 confidence: float,
                 source: str):
        self.action_id = action_id
        self.action_type = action_type
        self.status = status  # "success", "partial", "failed"
        self.data = data
        self.latency = latency
        self.cost = cost
        self.confidence = confidence
        self.source = source
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "status": self.status,
            "data": self.data,
            "latency": self.latency,
            "cost": self.cost,
            "confidence": self.confidence,
            "source": self.source,
            "timestamp": self.timestamp.isoformat()
        }

class FXAPI:
    """汇率API"""
    
    def __init__(self, name: str = "fx_api"):
        self.name = name
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        
    def can_handle(self, action: EnvironmentAction) -> bool:
        """检查是否能处理"""
        return action.type == "get_exchange_rate"
    
    def execute(self, action: EnvironmentAction) -> EnvironmentResult:
        """执行汇率查询"""
        start_time = time.time()
        
        try:
            base = action.params.get("base", "USD")
            target = action.params.get("target", "CNY")
            
            url = f"{self.base_url}/{base}"
            response = requests.get(url, timeout=action.timeout_seconds)
            
            latency = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                rate = data["rates"].get(target, 0.0)
                
                return EnvironmentResult(
                    action_id=action.action_id,
                    action_type=action.type,
                    status="success",
                    data={"rate": rate, "base": base, "target": target},
                    latency=latency,
                    cost=0.1 * latency,  # 成本与延迟相关
                    confidence=0.9,
                    source=self.name
                )
            else:
                return EnvironmentResult(
                    action_id=action.action_id,
                    action_type=action.type,
                    status="failed",
                    data={"error": f"HTTP {response.status_code}"},
                    latency=latency,
                    cost=0.2,  # 失败成本更高
                    confidence=0.3,
                    source=self.name
                )
                
        except Exception as e:
            latency = time.time() - start_time
            return EnvironmentResult(
                action_id=action.action_id,
                action_type=action.type,
                status="failed",
                data={"error": str(e)},
                latency=latency,
                cost=0.3,
                confidence=0.1,
                source=self.name
            )

class WeatherAPI:
    """天气API（使用Open-Meteo，免费）"""
    
    def __init__(self, name: str = "weather_api"):
        self.name = name
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        
    def can_handle(self, action: EnvironmentAction) -> bool:
        """检查是否能处理"""
        return action.type == "get_weather"
    
    def execute(self, action: EnvironmentAction) -> EnvironmentResult:
        """执行天气查询"""
        start_time = time.time()
        
        try:
            latitude = action.params.get("latitude", 39.9042)  # 北京默认
            longitude = action.params.get("longitude", 116.4074)
            
            url = f"{self.base_url}?latitude={latitude}&longitude={longitude}&current_weather=true"
            response = requests.get(url, timeout=action.timeout_seconds)
            
            latency = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                current = data.get("current_weather", {})
                
                weather_data = {
                    "temperature": current.get("temperature", 0),
                    "windspeed": current.get("windspeed", 0),
                    "winddirection": current.get("winddirection", 0),
                    "weathercode": current.get("weathercode", 0),
                    "latitude": latitude,
                    "longitude": longitude,
                    "time": current.get("time", "")
                }
                
                return EnvironmentResult(
                    action_id=action.action_id,
                    action_type=action.type,
                    status="success",
                    data=weather_data,
                    latency=latency,
                    cost=0.08 * latency,
                    confidence=0.85,
                    source=self.name
                )
            else:
                return EnvironmentResult(
                    action_id=action.action_id,
                    action_type=action.type,
                    status="failed",
                    data={"error": f"HTTP {response.status_code}"},
                    latency=latency,
                    cost=0.15,
                    confidence=0.3,
                    source=self.name
                )
                
        except Exception as e:
            latency = time.time() - start_time
            return EnvironmentResult(
                action_id=action.action_id,
                action_type=action.type,
                status="failed",
                data={"error": str(e)},
                latency=latency,
                cost=0.2,
                confidence=0.1,
                source=self.name
            )

class StockAPI:
    """股票API（模拟）"""
    
    def __init__(self, name: str = "stock_api"):
        self.name = name
        
    def can_handle(self, action: EnvironmentAction) -> bool:
        """检查是否能处理"""
        return action.type == "get_stock_price"
    
    def execute(self, action: EnvironmentAction) -> EnvironmentResult:
        """执行股票查询（模拟）"""
        start_time = time.time()
        
        try:
            symbol = action.params.get("symbol", "AAPL")
            
            # 模拟股票价格（实际应使用真实API）
            base_prices = {
                "AAPL": 180.0,
                "GOOGL": 140.0,
                "MSFT": 420.0,
                "TSLA": 175.0,
                "NVDA": 950.0
            }
            
            base_price = base_prices.get(symbol, 100.0)
            
            # 添加随机波动
            volatility = 0.02  # 2%波动
            change = random.uniform(-volatility, volatility)
            price = base_price * (1 + change)
            
            latency = time.time() - start_time
            
            stock_data = {
                "symbol": symbol,
                "price": round(price, 2),
                "change": round(change * 100, 2),
                "currency": "USD",
                "timestamp": datetime.now().isoformat(),
                "note": "模拟数据（实际需要API密钥）"
            }
            
            return EnvironmentResult(
                action_id=action.action_id,
                action_type=action.type,
                status="success",
                data=stock_data,
                latency=latency,
                cost=0.12 * latency,
                confidence=0.7,  # 模拟数据置信度较低
                source=self.name
            )
                
        except Exception as e:
            latency = time.time() - start_time
            return EnvironmentResult(
                action_id=action.action_id,
                action_type=action.type,
                status="failed",
                data={"error": str(e)},
                latency=latency,
                cost=0.25,
                confidence=0.1,
                source=self.name
            )

class WorldModelEnvironment:
    """世界模型环境"""
    
    def __init__(self):
        self.connectors = []
        self.action_history: List[Dict[str, Any]] = []
        self.result_history: List[Dict[str, Any]] = []
        
        # 注册连接器
        self._register_connectors()
        
        # 统计
        self.stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "total_latency": 0.0,
            "total_cost": 0.0,
            "avg_confidence": 0.0
        }
    
    def _register_connectors(self):
        """注册连接器"""
        self.connectors.append(FXAPI())
        self.connectors.append(WeatherAPI())
        self.connectors.append(StockAPI())
        
        print(f"✅ 世界模型环境初始化完成")
        print(f"   已注册连接器: {', '.join(c.name for c in self.connectors)}")
    
    def act(self, action: EnvironmentAction) -> EnvironmentResult:
        """
        执行环境行动
        
        Args:
            action: 环境行动
            
        Returns:
            环境结果
        """
        self.stats["total_actions"] += 1
        
        print(f"\n🌍 执行环境行动:")
        print(f"   类型: {action.type}")
        print(f"   参数: {action.params}")
        print(f"   预期效果: {action.expected_effect}")
        
        # 查找合适的连接器
        for connector in self.connectors:
            if connector.can_handle(action):
                print(f"   使用连接器: {connector.name}")
                
                # 执行行动
                result = connector.execute(action)
                
                # 更新统计
                self._update_stats(result)
                
                # 记录历史
                self.action_history.append(action.to_dict())
                self.result_history.append(result.to_dict())
                
                # 限制历史大小
                max_history = 100
                if len(self.action_history) > max_history:
                    self.action_history = self.action_history[-max_history:]
                if len(self.result_history) > max_history:
                    self.result_history = self.result_history[-max_history:]
                
                return result
        
        # 没有找到合适的连接器
        print(f"   ⚠️  没有连接器能处理该行动")
        
        result = EnvironmentResult(
            action_id=action.action_id,
            action_type=action.type,
            status="failed",
            data={"error": f"没有连接器能处理行动类型: {action.type}"},
            latency=0.0,
            cost=0.0,
            confidence=0.0,
            source="environment"
        )
        
        self._update_stats(result)
        return result
    
    def _update_stats(self, result: EnvironmentResult):
        """更新统计信息"""
        if result.status == "success":
            self.stats["successful_actions"] += 1
        else:
            self.stats["failed_actions"] += 1
        
        self.stats["total_latency"] += result.latency
        self.stats["total_cost"] += result.cost
        
        # 更新平均置信度
        total_confidence = sum(r.confidence for r in [result] + [r for r in self.result_history])
        count = len(self.result_history) + 1
        self.stats["avg_confidence"] = total_confidence / count if count > 0 else 0.0
    
    def get_available_actions(self) -> List[Dict[str, Any]]:
        """获取可用行动列表"""
        actions = []
        
        # 从连接器收集支持的行动
        for connector in self.connectors:
            if isinstance(connector, FXAPI):
                actions.append({
                    "type": "get_exchange_rate",
                    "description": "获取汇率",
                    "params_template": {"base": "USD", "target": "CNY"},
                    "connector": connector.name
                })
            elif isinstance(connector, WeatherAPI):
                actions.append({
                    "type": "get_weather",
                    "description": "获取天气",
                    "params_template": {"latitude": 39.9042, "longitude": 116.4074},
                    "connector": connector.name
                })
            elif isinstance(connector, StockAPI):
                actions.append({
                    "type": "get_stock_price",
                    "description": "获取股票价格",
                    "params_template": {"symbol": "AAPL"},
                    "connector": connector.name
                })
        
        return actions
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = (
            self.stats["successful_actions"] / self.stats["total_actions"]
            if self.stats["total_actions"] > 0 else 0.0
        )
        
        avg_latency = (
            self.stats["total_latency"] / self.stats["total_actions"]
            if self.stats["total_actions"] > 0 else 0.0
        )
        
        return {
            "performance": {
                **self.stats,
                "success_rate": success_rate,
                "avg_latency": avg_latency
            },
            "connectors": [c.name for c in self.connectors],
            "history_summary": {
                "action_history_count": len(self.action_history),
                "result_history_count": len(self.result_history)
            }
        }
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        perf = stats["performance"]
        
        print(f"\n📊 世界模型环境状态:")
        print(f"   性能:")
        print(f"     总行动数: {perf['total_actions']}")
        print(f"     成功行动: {perf['successful_actions']}")
        print(f"     失败行动: {perf['failed_actions']}")
        print(f"     成功率: {perf['success_rate']:.1%}")
        print(f"     总延迟: {perf['total_latency']:.3f}s")
        print(f"     平均延迟: {perf['avg_latency']:.3f}s")
        print(f"     总成本: {perf['total_cost']:.3f}")
        print(f"     平均置信度: {perf['avg_confidence']:.3f}")
        
        print(f"   连接器: {', '.join(stats['connectors'])}")
        
        print(f"   可用行动:")
        actions = self.get_available_actions()
        for action in actions:
            print(f"     • {action['type']}: {action['description']} ({action['connector']})")

def test_world_model():
    """测试世界模型"""
    print("🧪 测试 WorldModelEnvironment...")
    
    environment = WorldModelEnvironment()
    
    # 测试各种行动
    test_actions = [
        EnvironmentAction(
            type="get_exchange_rate",
            params={"base": "USD", "target": "CNY"},
            expected_effect="获取USD/CNY汇率",
            timeout_seconds=5
        ),
        EnvironmentAction(
            type="get_weather",
            params={"latitude": 39.9042, "longitude": 116.4074},
            expected_effect="获取北京天气",
            timeout_seconds=5
        ),
        EnvironmentAction(
            type="get_stock_price",
            params={"symbol": "AAPL"},
            expected_effect="获取苹果股票价格",
            timeout_seconds=3
        ),
        EnvironmentAction(
            type="unsupported_action",
            params={},
            expected_effect="测试不支持的行动",
            timeout_seconds=2
        )
    ]
    
    for i, action in enumerate(test_actions, 1):
        print(f"\n🔧 测试行动 {i}: {action.type}")
        
        result = environment.act(action)
        
        print(f"   结果状态: {result.status}")
        print(f"   延迟: {result.latency:.3f}s")
        print(f"   成本: {result.cost:.3f}")
        print(f"   置信度: {result.confidence:.3f}")
        print(f"   数据源: {result.source}")
        
        if result.status == "success":
            print(f"   数据: {result.data}")
        else:
            print(f"   错误: {result.data.get('error', '未知错误')}")
    
    # 显示状态
    print(f"\n📋 最终状态:")
    environment.print_status()
    
    # 测试认知集成
    print(f"\n🧠 测试认知集成:")
    
    # 创建认知行动
    cognitive_action = EnvironmentAction(
        type="get_exchange_rate",
        params={"base": "USD", "target": "CNY"},
        expected_effect="为认知系统提供实时汇率数据",
        timeout_seconds=4
    )
    
    print(f"   认知行动: {cognitive_action.expected_effect}")
    result = environment.act(cognitive_action)
    
    if result.status == "success":
        print(f"   ✅ 成功获取现实数据")
        print(f"      汇率: {result.data.get('rate', 'N/A')}")
        print(f"      延迟: {result.latency:.3f}s")
        print(f"      成本: {result.cost:.3f}")
        print(f"      置信度: {result.confidence:.3f}")
        
        # 这些数据应该进入：
        print(f"   🎯 数据应进入:")
        print(f"      1. Validation（验证认知结果）")
        print(f"      2. Belief Update（更新信念）")
        print(f"      3. RQS Adjustment（调整推理质量）")
        print(f"      4. Strategy Evolution（驱动策略进化）")
    else:
        print(f"   ❌ 获取现实数据失败")
    
    return environment

if __name__ == "__main__":
    test_world_model()