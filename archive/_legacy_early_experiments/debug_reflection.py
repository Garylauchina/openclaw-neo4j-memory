#!/usr/bin/env python3
"""
调试Reflection系统
目标：找出为什么Reflection没有生成任何Diff
"""

import sys
sys.path.append('.')

print("🔍 调试Reflection系统")
print("="*60)

from global_graph import GlobalGraph, NodeType, EdgeType
from active_subgraph import ActiveSubgraphEngine
from active_set import ActiveSetEngine, ActiveSet
from reflection_upgrade import ReflectionEngine
import time

# 创建测试图
print("1. 创建测试图...")
graph = GlobalGraph()

# 添加一些测试数据
user_id = graph.create_node("测试用户", NodeType.USER)
topic1_id = graph.create_node("日本房产", NodeType.TOPIC)
topic2_id = graph.create_node("AI", NodeType.TOPIC)

graph.update_edge(user_id, topic1_id, EdgeType.INTERESTED_IN, 0.8)
graph.update_edge(user_id, topic2_id, EdgeType.INTERESTED_IN, 0.6)

print(f"   图状态: {len(graph.nodes)}节点, {len(graph.edges)}边")

# 创建Active Set引擎
print("\n2. 创建Active Set引擎...")
active_set_engine = ActiveSetEngine(graph)

# 创建Reflection引擎
print("\n3. 创建Reflection引擎...")
reflection_engine = ReflectionEngine(graph)

# 测试查询
test_query = "我喜欢日本房产"
print(f"\n4. 测试查询: '{test_query}'")

# 构建Active Set
print("\n5. 构建Active Set...")
active_set = active_set_engine.build_active_set(test_query)
print(f"   Active Set子图数: {len(active_set.subgraphs) if active_set else 0}")

# 检查Reflection内部状态
print("\n6. 检查Reflection内部状态...")

# 检查是否有extract_patterns方法
if hasattr(reflection_engine, 'extract_patterns'):
    print("   ✅ 有extract_patterns方法")
    
    try:
        # 调用extract_patterns
        patterns = reflection_engine.extract_patterns(active_set)
        print(f"   提取的模式数: {len(patterns)}")
        
        if patterns:
            for i, pattern in enumerate(patterns[:3]):  # 只显示前3个
                print(f"   模式{i+1}: {pattern}")
        else:
            print("   ❌ 未提取到任何模式")
            
            # 检查可能的原因
            print("\n7. 检查可能的原因...")
            
            # 检查active_set内容
            if active_set and hasattr(active_set, 'subgraphs'):
                print(f"   Active Set子图详情:")
                for i, (subgraph, weight) in enumerate(active_set.subgraphs[:3]):
                    print(f"   子图{i+1}: 权重={weight:.3f}, 节点数={len(subgraph.nodes) if hasattr(subgraph, 'nodes') else '未知'}")
                    
                    # 检查子图节点
                    if hasattr(subgraph, 'nodes'):
                        for node_id in list(subgraph.nodes)[:3]:
                            node = graph.nodes.get(node_id)
                            if node:
                                print(f"     节点: {node.name} ({node.type.value})")
            
            # 检查图状态
            print(f"\n   图当前状态:")
            print(f"   总节点数: {len(graph.nodes)}")
            print(f"   总边数: {len(graph.edges)}")
            
            # 检查是否有足够的数据供模式提取
            if len(graph.edges) < 3:
                print("   ⚠️  图数据太少，可能无法提取模式")
                print("   💡 建议：添加更多测试数据")
                
    except Exception as e:
        print(f"   ❌ extract_patterns调用失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   ❌ 没有extract_patterns方法")

# 直接调用reflect方法
print("\n8. 直接调用reflect方法...")
try:
    diffs = reflection_engine.reflect(active_set)
    print(f"   reflect生成的Diff数: {len(diffs)}")
    
    if diffs:
        for i, diff in enumerate(diffs[:3]):
            print(f"   Diff{i+1}: {diff}")
    else:
        print("   ❌ reflect未生成任何Diff")
        
except Exception as e:
    print(f"   ❌ reflect调用失败: {e}")
    import traceback
    traceback.print_exc()

# 检查ReflectionEngine的配置
print("\n9. 检查ReflectionEngine配置...")
if hasattr(reflection_engine, 'config'):
    print(f"   配置: {reflection_engine.config}")
else:
    print("   ⚠️  没有config属性")

# 添加更多测试数据并重试
print("\n10. 添加更多测试数据并重试...")
# 添加更多边
graph.update_edge(user_id, topic1_id, EdgeType.INVESTED_IN, 0.7)
graph.update_edge(user_id, topic2_id, EdgeType.LEARNING, 0.9)

# 添加另一个用户
user2_id = graph.create_node("另一个用户", NodeType.USER)
graph.update_edge(user2_id, topic1_id, EdgeType.DISLIKES, 0.5)

print(f"   添加数据后: {len(graph.nodes)}节点, {len(graph.edges)}边")

# 再次尝试Reflection
try:
    diffs2 = reflection_engine.reflect(active_set)
    print(f"   添加数据后Diff数: {len(diffs2)}")
except Exception as e:
    print(f"   ❌ 再次调用失败: {e}")

print("\n" + "="*60)
print("🔍 调试总结")

# 问题诊断
if len(graph.edges) >= 3:
    print("✅ 图有足够的数据")
else:
    print("❌ 图数据不足")

if hasattr(reflection_engine, 'extract_patterns'):
    print("✅ ReflectionEngine有extract_patterns方法")
else:
    print("❌ ReflectionEngine缺少关键方法")

print("\n💡 建议:")
print("1. 检查ReflectionEngine.extract_patterns的实现")
print("2. 确保图中有足够的关系数据（至少3条边）")
print("3. 检查模式提取的阈值设置")
print("4. 添加日志以跟踪模式提取过程")

print("\n📊 下一步:")
print("1. 查看reflection_upgrade.py中的extract_patterns实现")
print("2. 添加调试日志")
print("3. 降低模式提取阈值")
print("4. 测试更简单的模式提取逻辑")