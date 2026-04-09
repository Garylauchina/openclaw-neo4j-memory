#!/usr/bin/env python3
"""
OpenClaw Cognitive Hook - 认知接管钩子
替换OpenClaw默认的记忆/推理管道
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加路径
workspace_dir = os.path.expanduser("~/.openclaw/workspace")
sys.path.insert(0, workspace_dir)

class OpenClawCognitiveHook:
    """OpenClaw认知接管钩子"""
    
    def __init__(self):
        print("\n" + "=" * 70)
        print("🚀 OpenClaw Cognitive Hook - 认知接管系统")
        print("=" * 70)
        
        self.hook_version = "2.0.0"
        self.integrated_at = datetime.now().isoformat()
        
        # 状态跟踪
        self.stats = {
            "hook_calls": 0,
            "cognitive_core_calls": 0,
            "fallback_calls": 0,
            "api_calls": 0,
            "graph_writes": 0,
            "errors": 0
        }
        
        # 初始化认知内核
        self.cognitive_core = None
        self._init_cognitive_core()
        
        # 配置
        self.config = {
            "enabled": True,
            "mode": "cognitive_core",  # cognitive_core | hybrid | fallback
            "cache_enabled": True,
            "validation_required": True,
            "reality_anchoring": True
        }
        
        print(f"✅ 认知接管钩子初始化完成 (版本: {self.hook_version})")
        print(f"   集成时间: {self.integrated_at}")
        print(f"   运行模式: {self.config['mode']}")
    
    def _init_cognitive_core(self):
        """初始化认知内核"""
        try:
            from cognitive_core import CognitiveCore
            self.cognitive_core = CognitiveCore()
            print("✅ 认知内核加载成功")
        except Exception as e:
            print(f"⚠️  认知内核加载失败: {e}")
            self.cognitive_core = None
    
    def process_query_hook(self, query: str, context: Optional[dict] = None) -> dict:
        """
        查询处理钩子 - 替换OpenClaw默认处理
        
        Args:
            query: 用户查询
            context: OpenClaw上下文
            
        Returns:
            增强的响应
        """
        self.stats["hook_calls"] += 1
        
        print(f"\n🔧 认知钩子处理查询: {query[:80]}...")
        
        # 检查是否应该使用认知内核
        should_use_cognitive = self._should_use_cognitive_core(query, context)
        
        if should_use_cognitive and self.cognitive_core:
            try:
                self.stats["cognitive_core_calls"] += 1
                
                # 使用认知内核处理
                result = self.cognitive_core.process_query(query, context)
                
                # 提取统计信息
                if "system_state" in result:
                    sys_state = result["system_state"]
                    self.stats["api_calls"] += sys_state.get("api_calls", 0)
                    self.stats["graph_writes"] += sys_state.get("graph_writes", 0)
                
                print(f"   ✅ 认知内核处理完成")
                print(f"     置信度: {result.get('metadata', {}).get('confidence', 0.0):.3f}")
                
                # 转换为OpenClaw格式
                openclaw_response = self._format_for_openclaw(result, query, context)
                
                return openclaw_response
                
            except Exception as e:
                self.stats["errors"] += 1
                print(f"   ❌ 认知内核处理失败: {e}")
                # 降级到默认处理
                return self._fallback_processing(query, context)
        else:
            # 使用降级处理
            self.stats["fallback_calls"] += 1
            print(f"   ℹ️  使用降级处理")
            return self._fallback_processing(query, context)
    
    def _should_use_cognitive_core(self, query: str, context: Optional[dict]) -> bool:
        """判断是否应该使用认知内核"""
        if not self.config["enabled"]:
            return False
        
        if not self.cognitive_core:
            return False
        
        # 检查查询类型
        query_lower = query.lower()
        
        # 应该使用认知内核的查询类型
        cognitive_queries = [
            "usd", "cny", "汇率", "兑换",
            "天气", "temperature", "weather",
            "股票", "stock", "价格",
            "实时", "最新", "当前"
        ]
        
        # 不应该使用认知内核的查询类型
        non_cognitive_queries = [
            "帮助", "help", "命令", "command",
            "设置", "config", "配置",
            "状态", "status", "统计"
        ]
        
        # 检查是否包含认知查询关键词
        for keyword in cognitive_queries:
            if keyword in query_lower:
                return True
        
        # 检查是否包含非认知查询关键词
        for keyword in non_cognitive_queries:
            if keyword in query_lower:
                return False
        
        # 默认：对于一般查询，根据配置决定
        return self.config["mode"] in ["cognitive_core", "hybrid"]
    
    def _fallback_processing(self, query: str, context: Optional[dict]) -> dict:
        """降级处理（模拟OpenClaw默认行为）"""
        print(f"   🔄 执行降级处理")
        
        # 模拟OpenClaw的默认响应
        response = {
            "text": f"这是对查询 '{query}' 的默认响应。",
            "source": "openclaw_fallback",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "processed_by": "fallback_handler",
                "cognitive_hook": False,
                "confidence": 0.5
            }
        }
        
        # 如果是汇率查询，添加说明
        if "usd" in query.lower() or "cny" in query.lower() or "汇率" in query:
            response["text"] = "这是汇率查询的降级响应。认知系统应该处理实时数据查询。"
            response["metadata"]["suggestion"] = "启用认知内核以获得实时汇率数据"
        
        return response
    
    def _format_for_openclaw(self, cognitive_result: dict, query: str, context: Optional[dict]) -> dict:
        """将认知结果格式化为OpenClaw格式"""
        # 提取格式化文本
        formatted_text = cognitive_result.get("formatted_text", "")
        if not formatted_text and cognitive_result.get("results"):
            # 从结果生成文本
            results = cognitive_result["results"]
            if results and isinstance(results[0], dict):
                if "rate" in results[0]:
                    formatted_text = f"当前USD/CNY汇率: {results[0]['rate']}"
                elif "temperature" in results[0]:
                    formatted_text = f"北京当前气温: {results[0]['temperature']}°C"
        
        # 构建OpenClaw响应
        openclaw_response = {
            "text": formatted_text or f"认知系统处理结果: {cognitive_result.get('query', query)}",
            "source": "cognitive_core",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "processed_by": "cognitive_core",
                "cognitive_hook": True,
                "confidence": cognitive_result.get("metadata", {}).get("confidence", 0.7),
                "components_used": cognitive_result.get("metadata", {}).get("components_used", 0),
                "validations_passed": cognitive_result.get("metadata", {}).get("validations_passed", 0),
                "original_result": cognitive_result
            }
        }
        
        # 添加系统状态
        if "system_state" in cognitive_result:
            openclaw_response["metadata"]["system_state"] = cognitive_result["system_state"]
        
        return openclaw_response
    
    def get_hook_status(self) -> dict:
        """获取钩子状态"""
        cognitive_stats = self.cognitive_core.get_stats() if self.cognitive_core else {}
        
        return {
            "hook": {
                "version": self.hook_version,
                "integrated_at": self.integrated_at,
                "config": self.config,
                "stats": self.stats,
                "cognitive_core_available": self.cognitive_core is not None
            },
            "cognitive_core": cognitive_stats,
            "performance": {
                "hook_call_rate": self.stats["hook_calls"],
                "cognitive_usage_rate": self.stats["cognitive_core_calls"] / self.stats["hook_calls"] if self.stats["hook_calls"] > 0 else 0.0,
                "fallback_rate": self.stats["fallback_calls"] / self.stats["hook_calls"] if self.stats["hook_calls"] > 0 else 0.0,
                "error_rate": self.stats["errors"] / self.stats["hook_calls"] if self.stats["hook_calls"] > 0 else 0.0
            }
        }
    
    def print_status(self):
        """打印状态"""
        status = self.get_hook_status()
        
        print("\n📊 OpenClaw Cognitive Hook 状态:")
        print(f"   钩子信息:")
        print(f"     版本: {status['hook']['version']}")
        print(f"     集成时间: {status['hook']['integrated_at']}")
        print(f"     运行模式: {status['hook']['config']['mode']}")
        print(f"     认知内核可用: {status['hook']['cognitive_core_available']}")
        
        print(f"   调用统计:")
        print(f"     钩子调用: {status['hook']['stats']['hook_calls']}")
        print(f"     认知内核调用: {status['hook']['stats']['cognitive_core_calls']}")
        print(f"     降级调用: {status['hook']['stats']['fallback_calls']}")
        print(f"     API调用: {status['hook']['stats']['api_calls']}")
        print(f"     Graph写入: {status['hook']['stats']['graph_writes']}")
        print(f"     错误: {status['hook']['stats']['errors']}")
        
        print(f"   性能指标:")
        print(f"     认知使用率: {status['performance']['cognitive_usage_rate']:.1%}")
        print(f"     降级率: {status['performance']['fallback_rate']:.1%}")
        print(f"     错误率: {status['performance']['error_rate']:.1%}")
        
        if self.cognitive_core:
            print(f"\n🧠 认知内核状态:")
            self.cognitive_core.print_status()

def test_hook():
    """测试钩子"""
    print("🧪 测试 OpenClaw Cognitive Hook...")
    
    hook = OpenClawCognitiveHook()
    
    # 测试查询
    test_queries = [
        "USD兑换人民币是多少？",
        "北京天气怎么样？",
        "帮助信息",
        "系统状态"
    ]
    
    for query in test_queries:
        print(f"\n🔍 测试查询: {query}")
        
        result = hook.process_query_hook(query)
        
        print(f"   处理方式: {'认知内核' if result['metadata']['cognitive_hook'] else '降级处理'}")
        print(f"   置信度: {result['metadata']['confidence']:.3f}")
        print(f"   响应: {result['text'][:80]}...")
    
    # 显示状态
    print(f"\n📋 最终状态:")
    hook.print_status()
    
    return hook

if __name__ == "__main__":
    test_hook()