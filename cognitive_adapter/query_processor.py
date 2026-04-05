#!/usr/bin/env python3
"""
Query Processor - Goal + Attention最简版
"""

from typing import List, Dict, Any, Optional
import re

def process_query(query: str, graph=None, attention=None) -> List[Any]:
    """
    处理查询：Query → Goal + Attention
    
    Args:
        query: 查询文本
        graph: 记忆图系统
        attention: 注意力系统
        
    Returns:
        相关节点列表
    """
    # 1️⃣ 简化版 Goal（先别复杂化）
    goal = extract_goal(query)
    
    print(f"     目标提取: {goal['type']} - {goal['query']}")
    
    # 2️⃣ Attention 选 Top-K
    if attention and hasattr(attention, 'select') and graph and hasattr(graph, 'nodes'):
        # 使用真实的注意力系统
        print(f"     使用真实注意力系统...")
        nodes = attention.select(query, graph.nodes)
    else:
        # 模拟注意力系统
        print(f"     使用模拟注意力系统...")
        nodes = simulate_attention(query, graph)
    
    return nodes

def extract_goal(query: str) -> Dict[str, Any]:
    """
    提取查询目标
    
    Args:
        query: 查询文本
        
    Returns:
        目标字典
    """
    query_lower = query.lower()
    
    # 目标类型识别
    goal_type = "info_lookup"  # 默认信息查询
    
    # 检查特定类型
    if any(word in query_lower for word in ["多少", "汇率", "价格", "rate", "price"]):
        goal_type = "numeric_query"
    elif any(word in query_lower for word in ["如何", "怎么", "怎样", "how to"]):
        goal_type = "how_to"
    elif any(word in query_lower for word in ["为什么", "为何", "why"]):
        goal_type = "explanation"
    elif any(word in query_lower for word in ["比较", "对比", "vs", "versus"]):
        goal_type = "comparison"
    elif any(word in query_lower for word in ["最新", "实时", "当前", "now", "current"]):
        goal_type = "real_time"
    
    # 提取关键词
    keywords = extract_keywords(query)
    
    return {
        "type": goal_type,
        "query": query,
        "keywords": keywords,
        "requires_real_time": goal_type == "real_time" or "实时" in query_lower,
        "requires_numeric": goal_type == "numeric_query",
        "timestamp": "2026-03-26T19:50:00"  # 模拟时间戳
    }

def extract_keywords(query: str) -> List[str]:
    """
    提取查询关键词
    
    Args:
        query: 查询文本
        
    Returns:
        关键词列表
    """
    # 移除常见停用词
    stop_words = {"的", "了", "和", "是", "在", "有", "我", "你", "他", "她", "它",
                  "这", "那", "就", "都", "也", "还", "与", "或", "而", "但",
                  "a", "an", "the", "and", "or", "but", "in", "on", "at", "to"}
    
    # 分词（简单实现）
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+\.?\d*', query)
    
    # 过滤停用词和短词
    keywords = []
    for word in words:
        word_lower = word.lower()
        if (word_lower not in stop_words and 
            len(word) >= 2 and
            not word.isdigit()):
            keywords.append(word_lower)
    
    # 去重
    unique_keywords = []
    seen = set()
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique_keywords.append(word)
    
    return unique_keywords

def simulate_attention(query: str, graph=None) -> List[Any]:
    """
    模拟注意力系统
    
    Args:
        query: 查询文本
        graph: 记忆图系统
        
    Returns:
        相关节点列表
    """
    if graph is None or not hasattr(graph, 'nodes'):
        # 如果没有图，返回空列表
        return []
    
    query_lower = query.lower()
    query_keywords = extract_keywords(query)
    
    scored_nodes = []
    
    for node in graph.nodes:
        # 计算相关性分数
        score = 0.0
        
        # 检查节点内容
        if hasattr(node, 'content'):
            content = str(node.content).lower()
            
            # 关键词匹配
            for keyword in query_keywords:
                if keyword in content:
                    score += 0.3
            
            # 完全匹配
            if query_lower in content:
                score += 0.5
            
            # 部分匹配
            query_words = set(query_lower.split())
            content_words = set(content.split())
            if query_words and content_words:
                intersection = len(query_words.intersection(content_words))
                score += intersection * 0.1
        
        # 使用节点的attention_score（如果有）
        if hasattr(node, 'attention_score'):
            score *= node.attention_score
        
        # 添加节点和分数
        if score > 0:
            node.attention_score = score
            scored_nodes.append((score, node))
    
    # 按分数排序
    scored_nodes.sort(key=lambda x: x[0], reverse=True)
    
    # 返回节点（不带分数）
    return [node for _, node in scored_nodes[:10]]  # 返回前10个

def test_query_processor():
    """测试查询处理器"""
    print("🧪 测试 QueryProcessor...")
    
    # 创建模拟图
    class MockNode:
        def __init__(self, content, attention_score=0.5):
            self.content = content
            self.attention_score = attention_score
    
    class MockGraph:
        def __init__(self):
            self.nodes = [
                MockNode("USD是美元的国际代码", 0.8),
                MockNode("CNY是人民币的国际代码", 0.7),
                MockNode("汇率是两种货币的兑换比例", 0.6),
                MockNode("外汇市场每天24小时交易", 0.5),
                MockNode("中国央行会干预汇率市场", 0.4),
                MockNode("比特币是一种加密货币", 0.3),
                MockNode("人工智能正在改变世界", 0.2),
            ]
    
    # 测试查询
    test_queries = [
        "USD兑换人民币是多少？",
        "什么是汇率？",
        "比特币是什么？",
        "人工智能的应用",
    ]
    
    graph = MockGraph()
    
    for query in test_queries:
        print(f"\n🔍 测试查询: {query}")
        
        # 提取目标
        goal = extract_goal(query)
        print(f"   目标类型: {goal['type']}")
        print(f"   关键词: {', '.join(goal['keywords'])}")
        print(f"   需要实时数据: {goal['requires_real_time']}")
        
        # 处理查询
        nodes = process_query(query, graph=graph, attention=None)
        
        print(f"   检索到 {len(nodes)} 个相关节点:")
        for i, node in enumerate(nodes[:3]):  # 只显示前3个
            content = str(node.content)[:40]
            score = getattr(node, 'attention_score', 0)
            print(f"     {i+1}. [{score:.3f}] {content}...")
    
    print("\n✅ QueryProcessor测试完成")

if __name__ == "__main__":
    test_query_processor()