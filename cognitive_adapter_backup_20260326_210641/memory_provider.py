#!/usr/bin/env python3
"""
Memory Provider - 核心接管点
替换 OpenClaw 的 memory.retrieve()
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from .query_processor import process_query
from .fx_api import get_usd_cny
from .formatter import to_claw_format

class CognitiveMemoryProvider:
    """认知记忆提供器"""
    
    def __init__(self, graph=None, attention=None, rqs=None):
        """
        初始化认知记忆提供器
        
        Args:
            graph: 记忆图系统
            attention: 注意力系统  
            rqs: 推理质量评分系统
        """
        self.graph = graph
        self.attention = attention
        self.rqs = rqs
        
        # 统计信息
        self.stats = {
            "total_queries": 0,
            "api_calls": 0,
            "graph_retrievals": 0,
            "avg_processing_time": 0.0,
            "reality_enhanced_queries": 0
        }
        
        # 缓存（简单实现）
        self.fx_cache = {
            "rate": None,
            "timestamp": None,
            "ttl": 60  # 60秒缓存
        }
        
        print(f"✅ CognitiveMemoryProvider 初始化完成")
        print(f"   图系统: {'已连接' if graph else '模拟模式'}")
        print(f"   注意力系统: {'已连接' if attention else '模拟模式'}")
        print(f"   RQS系统: {'已连接' if rqs else '模拟模式'}")
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        替换 OpenClaw 的 memory.retrieve()
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            格式化后的记忆片段列表
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        print(f"\n🔍 认知检索开始:")
        print(f"   查询: {query}")
        print(f"   时间: {datetime.now().strftime('%H:%M:%S')}")
        
        # 1️⃣ Query → Goal + Attention
        print(f"   步骤1: Query处理...")
        nodes = process_query(query, self.graph, self.attention)
        self.stats["graph_retrievals"] += 1
        
        print(f"     检索到 {len(nodes)} 个相关节点")
        
        # 2️⃣ Graph 检索（带 RQS 排序）
        print(f"   步骤2: RQS排序...")
        if self.rqs and hasattr(self.rqs, 'score'):
            # 如果有RQS系统，使用RQS评分
            for node in nodes:
                if hasattr(node, 'content'):
                    node.rqs = self.rqs.score(node.content)
                else:
                    node.rqs = 0.5
        else:
            # 模拟RQS评分
            for node in nodes:
                if hasattr(node, 'content'):
                    # 简单评分：查询相关性
                    query_words = set(query.lower().split())
                    content_words = set(str(node.content).lower().split())
                    if query_words and content_words:
                        intersection = len(query_words.intersection(content_words))
                        union = len(query_words.union(content_words))
                        node.rqs = intersection / union if union > 0 else 0.3
                    else:
                        node.rqs = 0.3
                else:
                    node.rqs = 0.3
        
        # 排序（注意力分数 × RQS）
        ranked = sorted(
            nodes,
            key=lambda x: getattr(x, 'attention_score', 0.5) * getattr(x, 'rqs', 0.5),
            reverse=True
        )[:k]
        
        print(f"     排序后保留 {len(ranked)} 个节点")
        
        # 3️⃣ ❗ 现实世界增强（关键）
        print(f"   步骤3: 现实世界增强...")
        enhanced_nodes = list(ranked)  # 复制一份
        
        # 检查是否需要汇率信息
        query_lower = query.lower()
        fx_keywords = ["usd", "美元", "汇率", "兑换", "人民币", "cny", "exchange"]
        
        if any(keyword in query_lower for keyword in fx_keywords):
            print(f"     ⚡ 检测到汇率查询，调用真实API...")
            
            # 获取实时汇率
            fx_rate = self._get_fx_rate()
            self.stats["api_calls"] += 1
            self.stats["reality_enhanced_queries"] += 1
            
            if fx_rate != "API_ERROR":
                # 创建增强节点
                fx_node = {
                    "content": f"当前 USD→CNY 汇率：{fx_rate}",
                    "rqs": 0.9,  # 高可信度（实时数据）
                    "attention_score": 1.0,
                    "source": "real_world_api",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "type": "real_time_data",
                        "api": "exchangerate.host",
                        "cache_hit": self.fx_cache["rate"] is not None
                    }
                }
                
                enhanced_nodes.append(fx_node)
                print(f"     ✅ 添加实时汇率节点: {fx_rate}")
            else:
                print(f"     ⚠️  API调用失败，使用缓存数据")
        
        # 4️⃣ 返回给 OpenClaw
        print(f"   步骤4: 格式化输出...")
        results = to_claw_format(enhanced_nodes)
        
        # 更新统计
        processing_time = time.time() - start_time
        total_time = self.stats["avg_processing_time"] * (self.stats["total_queries"] - 1)
        self.stats["avg_processing_time"] = (total_time + processing_time) / self.stats["total_queries"]
        
        print(f"   处理完成: {processing_time:.3f}s")
        print(f"   返回 {len(results)} 个结果")
        
        return results
    
    def _get_fx_rate(self) -> str:
        """获取汇率（带缓存）"""
        current_time = time.time()
        
        # 检查缓存
        if (self.fx_cache["rate"] is not None and 
            self.fx_cache["timestamp"] is not None and
            current_time - self.fx_cache["timestamp"] < self.fx_cache["ttl"]):
            print(f"      缓存命中: {self.fx_cache['rate']}")
            return self.fx_cache["rate"]
        
        # 调用API
        try:
            from .fx_api import get_usd_cny
            rate = get_usd_cny()
            
            if rate != "API_ERROR":
                # 更新缓存
                self.fx_cache["rate"] = rate
                self.fx_cache["timestamp"] = current_time
                print(f"      API调用成功: {rate}")
            else:
                print(f"      API调用失败")
            
            return rate
            
        except Exception as e:
            print(f"      汇率API异常: {e}")
            return "API_ERROR"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "performance": self.stats,
            "cache": {
                "fx_rate": self.fx_cache["rate"],
                "age_seconds": (
                    time.time() - self.fx_cache["timestamp"]
                    if self.fx_cache["timestamp"] else None
                )
            },
            "status": {
                "graph_connected": self.graph is not None,
                "attention_connected": self.attention is not None,
                "rqs_connected": self.rqs is not None
            }
        }
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        perf = stats["performance"]
        
        print(f"\n📊 CognitiveMemoryProvider 统计:")
        print(f"   性能:")
        print(f"     总查询数: {perf['total_queries']}")
        print(f"     API调用数: {perf['api_calls']}")
        print(f"     图检索数: {perf['graph_retrievals']}")
        print(f"     现实增强查询: {perf['reality_enhanced_queries']}")
        print(f"     平均处理时间: {perf['avg_processing_time']:.3f}s")
        
        if perf['total_queries'] > 0:
            enhancement_rate = (perf['reality_enhanced_queries'] / perf['total_queries']) * 100
            print(f"     现实增强率: {enhancement_rate:.1f}%")
        
        print(f"   缓存:")
        if stats['cache']['fx_rate']:
            age = stats['cache']['age_seconds']
            print(f"     汇率缓存: {stats['cache']['fx_rate']} (年龄: {age:.1f}s)")
        else:
            print(f"     汇率缓存: 无")
        
        print(f"   连接状态:")
        print(f"     图系统: {'✅ 已连接' if stats['status']['graph_connected'] else '❌ 未连接'}")
        print(f"     注意力系统: {'✅ 已连接' if stats['status']['attention_connected'] else '❌ 未连接'}")
        print(f"     RQS系统: {'✅ 已连接' if stats['status']['rqs_connected'] else '❌ 未连接'}")

# 测试函数
def test_memory_provider():
    """测试记忆提供器"""
    print("🧪 测试 CognitiveMemoryProvider...")
    
    # 创建模拟系统
    class MockNode:
        def __init__(self, content, attention_score=0.5):
            self.content = content
            self.attention_score = attention_score
            self.rqs = 0.5
    
    class MockGraph:
        def __init__(self):
            self.nodes = [
                MockNode("USD是美元的国际代码", 0.8),
                MockNode("CNY是人民币的国际代码", 0.7),
                MockNode("汇率是两种货币的兑换比例", 0.6),
                MockNode("外汇市场每天24小时交易", 0.5),
                MockNode("中国央行会干预汇率市场", 0.4),
            ]
    
    class MockAttention:
        def select(self, query, nodes):
            # 简单匹配
            query_lower = query.lower()
            selected = []
            for node in nodes:
                if query_lower in str(node.content).lower():
                    selected.append(node)
            return selected if selected else nodes[:3]
    
    class MockRQS:
        def score(self, content):
            # 简单评分
            return 0.7
    
    # 创建提供器
    provider = CognitiveMemoryProvider(
        graph=MockGraph(),
        attention=MockAttention(),
        rqs=MockRQS()
    )
    
    # 测试查询
    test_queries = [
        "USD兑换人民币是多少？",
        "什么是汇率？",
        "今天天气怎么样？"
    ]
    
    for query in test_queries:
        print(f"\n🔍 测试查询: {query}")
        results = provider.retrieve(query, k=3)
        
        print(f"   返回结果:")
        for i, result in enumerate(results):
            text = result.get('text', '')[:50]
            score = result.get('score', 0)
            print(f"     {i+1}. [{score:.3f}] {text}...")
    
    # 显示统计
    provider.print_stats()
    
    return provider

if __name__ == "__main__":
    print("🚀 测试 CognitiveMemoryProvider")
    provider = test_memory_provider()
    print("\n✅ 测试完成")