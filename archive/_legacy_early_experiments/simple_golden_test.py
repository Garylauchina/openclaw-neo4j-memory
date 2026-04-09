#!/usr/bin/env python3
"""
简单黄金测试 - 直接测试核心功能
绕过ReplayRunner的复杂逻辑
"""

import sys
sys.path.append('.')

print("🧪 简单黄金测试 - 直接测试核心功能")
print("="*60)

from global_graph import GlobalGraph, NodeType, EdgeType
from simple_semantic_parser import SimpleSemanticParser
from active_subgraph import ActiveSubgraphEngine
from active_set import ActiveSetEngine, ActiveSet
from reflection_upgrade import ReflectionEngine
from learning_guard import LearningGuard
import time

# 创建测试环境
print("1. 创建测试环境...")
graph = GlobalGraph()
parser = SimpleSemanticParser()
active_subgraph_engine = ActiveSubgraphEngine(graph)
active_set_engine = ActiveSetEngine(graph)

# 创建Reflection引擎
print("\n2. 创建Reflection引擎...")
reflection_config = {
    "min_pattern_frequency": 2,
    "min_pattern_weight": 0.1,
    "confidence_threshold": 0.3,
    "debug": True
}
reflection_engine = ReflectionEngine(graph, reflection_config)

# 创建Learning Guard
print("\n3. 创建Learning Guard...")
learning_guard_config = {
    "consistency_threshold": 0.3,
    "stability_threshold": 0.2,
    "novelty_threshold": 0.1,
    "debug": True
}
learning_guard = LearningGuard(graph, learning_guard_config)

# 测试查询
print("\n4. 定义测试查询...")
test_queries = [
    "我喜欢日本房产",
    "我想投资AI",
    "日本房产回报率如何？",
    "机器学习入门",
    "深度学习与机器学习的区别",
    "Python编程学习路线",
    "神经网络基本原理",
    "东京和大阪哪个更适合投资？",
    "日本房产的税务问题",
    "AI创业怎么做？"
]

print(f"   测试查询数: {len(test_queries)}")
print(f"   预期重复话题: 日本房产(3次), AI(3次)")

# 运行测试
print("\n5. 运行测试...")
print("-"*40)

all_diffs = []
success_count = 0

for turn, query in enumerate(test_queries):
    print(f"\n   第 {turn+1} 轮: {query}")
    
    try:
        # 1. 语义解析
        parsed = parser.parse(query)
        if not parsed:
            print(f"     ❌ 语义解析失败")
            continue
        
        print(f"     ✅ 语义解析: {parsed['subject']} -> {parsed['relation']} -> {parsed['object']}")
        
        # 2. 添加到Graph
        subject_id = graph.create_node(parsed["subject"], NodeType.USER)
        object_id = graph.create_node(parsed["object"], NodeType.TOPIC)
        
        # 映射关系类型
        relation = parsed["relation"]
        edge_type = EdgeType.MENTIONED  # 默认
        
        if relation == "LIKES":
            edge_type = EdgeType.LIKES
        elif relation == "INVESTED_IN":
            edge_type = EdgeType.INVESTED_IN
        elif relation == "ASKING_ABOUT":
            edge_type = EdgeType.ASKING_ABOUT
        elif relation == "LEARNING":
            edge_type = EdgeType.LEARNING
        elif relation == "INTERESTED_IN":
            edge_type = EdgeType.INTERESTED_IN
        
        confidence = parsed.get("confidence", 0.6)
        graph.update_edge(subject_id, object_id, edge_type, confidence)
        print(f"     ✅ Graph更新: 添加边 {edge_type.value}")
        
        # 3. 构建Active Set
        active_set = active_set_engine.build_active_set(query)
        print(f"     ✅ Active Set: {len(active_set.subgraphs)} 个子图")
        
        # 4. Reflection
        diffs = reflection_engine.reflect(active_set)
        print(f"     ✅ Reflection: 生成 {len(diffs)} 个Diff")
        
        if diffs:
            # 5. Learning Guard验证
            validated_diffs = []
            for diff in diffs:
                result = learning_guard.validate_diff(diff, {"source": "test", "query": query})
                print(f"       Learning Guard: {result.suggested_action} (置信度: {result.confidence:.2f})")
                
                if result.suggested_action == "accept":
                    validated_diffs.append(diff)
            
            all_diffs.extend(validated_diffs)
            print(f"     ✅ 验证通过: {len(validated_diffs)} 个Diff")
        
        success_count += 1
        
    except Exception as e:
        print(f"     ❌ 错误: {e}")
        import traceback
        traceback.print_exc()

# 统计结果
print("\n6. 统计结果...")
print("-"*40)

graph_edges = len([e for e in graph.edges.values() if hasattr(e, 'active') and e.active])
patterns_count = len(reflection_engine.patterns) if hasattr(reflection_engine, 'patterns') else 0

print(f"   总轮数: {len(test_queries)}")
print(f"   成功轮数: {success_count}")
print(f"   Graph边数: {graph_edges}")
print(f"   累计模式数: {patterns_count}")
print(f"   总Diff生成数: {len(all_diffs)}")

# 检查模式
print("\n7. 检查模式...")
print("-"*40)

if hasattr(reflection_engine, 'patterns') and reflection_engine.patterns:
    print(f"   发现的模式:")
    for pattern_key, pattern in list(reflection_engine.patterns.items())[:5]:  # 只显示前5个
        src_node = graph.nodes.get(pattern.src_node_id)
        dst_node = graph.nodes.get(pattern.dst_node_id)
        src_name = src_node.name if src_node else pattern.src_node_id
        dst_name = dst_node.name if dst_node else pattern.dst_node_id
        
        print(f"     {src_name} -> {dst_name} ({pattern.edge_type.value}):")
        print(f"       频率: {pattern.frequency}")
        print(f"       平均权重: {pattern.avg_weight:.3f}")
        print(f"       是否合格: 频率≥{reflection_config['min_pattern_frequency']}? {pattern.frequency >= reflection_config['min_pattern_frequency']}")

# 系统状态判断
print("\n8. 系统状态判断...")
print("-"*40)

system_working = False
if graph_edges > 0 and patterns_count > 0 and len(all_diffs) > 0:
    system_working = True

print(f"   🎯 系统状态: {'✅ 工作正常！' if system_working else '❌ 存在问题'}")

if system_working:
    print("\n📈 关键成就:")
    print(f"   1. Graph增长: {graph_edges} 条边")
    print(f"   2. 模式发现: {patterns_count} 个模式")
    print(f"   3. 学习动作: {len(all_diffs)} 个Diff")
    print(f"   4. 成功率: {success_count}/{len(test_queries)} ({success_count/len(test_queries)*100:.1f}%)")
    
    print("\n🚀 系统验证通过!")
    print("   学习管道完全激活并正常工作")
else:
    print("\n🔧 需要进一步调试:")
    print("   1. 检查语义解析器输出")
    print("   2. 检查Graph更新逻辑")
    print("   3. 检查Reflection配置")

print(f"\n🕐 测试完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")