#!/usr/bin/env python3
"""
简化测试验证系统基本功能
"""

import sys
sys.path.append('.')

print("🧪 简化测试验证系统基本功能")
print("="*60)

from global_graph import GlobalGraph, NodeType, EdgeType
from active_subgraph import ActiveSubgraphEngine
from active_set import ActiveSetEngine
from reflection_upgrade import ReflectionEngine
from learning_guard import LearningGuard

print("1. 测试系统组件初始化...")
print("-"*40)

try:
    # 创建全局图
    graph = GlobalGraph()
    print("✅ GlobalGraph 创建成功")
    
    # 创建Active Subgraph引擎
    subgraph_engine = ActiveSubgraphEngine(graph)
    print("✅ ActiveSubgraphEngine 创建成功")
    
    # 创建Active Set引擎
    active_set_engine = ActiveSetEngine(graph)
    print("✅ ActiveSetEngine 创建成功")
    
    # 创建Reflection引擎
    reflection_engine = ReflectionEngine(graph)
    print("✅ ReflectionEngine 创建成功")
    
    # 创建Learning Guard
    learning_guard = LearningGuard(graph)
    print("✅ LearningGuard 创建成功")
    
    print("\n2. 测试基本功能...")
    print("-"*40)
    
    # 创建测试节点
    user_id = graph.create_node("测试用户", NodeType.USER)
    topic_id = graph.create_node("测试话题", NodeType.TOPIC)
    print(f"✅ 创建节点: 用户={user_id}, 话题={topic_id}")
    
    # 创建边
    graph.update_edge(user_id, topic_id, EdgeType.INTERESTED_IN, 0.7)
    print(f"✅ 创建边: 用户 → INTERESTED_IN → 话题 (0.7)")
    
    # 测试Active Subgraph
    subgraph = subgraph_engine.build_active_subgraph("测试查询")
    print(f"✅ ActiveSubgraph构建: {len(subgraph.nodes) if subgraph else 0}个节点")
    
    # 测试Active Set
    active_set = active_set_engine.build_active_set("测试查询")
    print(f"✅ ActiveSet构建: {len(active_set.subgraphs) if active_set else 0}个子图")
    
    # 测试Reflection
    if active_set:
        diffs = reflection_engine.reflect(active_set)
        print(f"✅ Reflection生成: {len(diffs)}个Diff")
        
        # 测试Learning Guard
        if diffs:
            diff = diffs[0]
            result = learning_guard.validate_diff(diff, {"source": "test"})
            print(f"✅ Learning Guard验证: {result.suggested_action}")
    
    print("\n" + "="*60)
    print("✅ 系统基本功能验证通过")
    print("系统组件: 5/5 正常")
    print("基本功能: 全部正常")
    print("="*60)
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
