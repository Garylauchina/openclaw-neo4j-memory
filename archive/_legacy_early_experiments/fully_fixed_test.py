#!/usr/bin/env python3
"""
完全修复测试
目标：使用完整的配置让系统工作
"""

import sys
sys.path.append('.')

print("🔧 完全修复测试")
print("="*60)

from global_graph import GlobalGraph, NodeType, EdgeType
from active_subgraph import ActiveSubgraphEngine
from active_set import ActiveSetEngine, ActiveSet
from reflection_upgrade import ReflectionEngine
from learning_guard import LearningGuard
import time

# 创建测试环境
print("1. 创建测试环境...")
graph = GlobalGraph()

# 添加测试数据
print("2. 添加测试数据...")
user_id = graph.create_node("测试用户", NodeType.USER)
topic_ids = []
for i in range(3):
    topic_id = graph.create_node(f"话题{i}", NodeType.TOPIC)
    topic_ids.append(topic_id)
    
    # 添加边
    graph.update_edge(user_id, topic_id, EdgeType.LIKES, 0.7)
    graph.update_edge(user_id, topic_id, EdgeType.INTERESTED_IN, 0.6)

print(f"   图状态: {len(graph.nodes)}节点, {len(graph.edges)}边")

# 创建完整的配置
print("\n3. 创建完整配置...")
full_config = {
    "min_pattern_frequency": 1,
    "min_pattern_weight": 0.01,
    "confidence_weights": {
        "frequency": 0.3,
        "consistency": 0.4,
        "recency": 0.3
    },
    "confidence_threshold": 0.1,  # 极低阈值
    "max_diffs_per_reflection": 5,
    "reinforce_delta": 0.1,
    "decay_delta": -0.05,
    "conflict_threshold": 0.3,
    "debug": True,  # 启用调试
    "dry_run": False
}

print(f"   配置: min_freq={full_config['min_pattern_frequency']}, "
      f"min_weight={full_config['min_pattern_weight']}, "
      f"conf_threshold={full_config['confidence_threshold']}")

# 创建Reflection引擎
print("\n4. 创建Reflection引擎...")
reflection_engine = ReflectionEngine(graph, full_config)

# 创建Active Set
print("\n5. 创建Active Set...")
active_set_engine = ActiveSetEngine(graph)
active_set = active_set_engine.build_active_set("测试查询")
print(f"   Active Set子图数: {len(active_set.subgraphs)}")

# 测试Reflection
print("\n6. 测试Reflection...")
try:
    diffs = reflection_engine.reflect(active_set)
    print(f"   Reflection生成 {len(diffs)} 个Diff")
    
    if diffs:
        print("   ✅ Reflection开始工作！")
        
        # 显示Diff详情
        for i, diff in enumerate(diffs[:3]):
            print(f"     Diff{i+1}:")
            print(f"       操作: {diff.op.value}")
            print(f"       源: {diff.src} -> 目标: {diff.dst}")
            print(f"       类型: {diff.type.value if diff.type else 'N/A'}")
            print(f"       变化量: {diff.delta}")
            print(f"       置信度: {diff.confidence}")
            
            # 测试Learning Guard
            print(f"       测试Learning Guard...")
            learning_guard_config = {
                "consistency_threshold": 0.1,
                "stability_threshold": 0.1,
                "novelty_threshold": 0.1,
                "debug": True
            }
            
            learning_guard = LearningGuard(graph, learning_guard_config)
            result = learning_guard.validate_diff(diff, {"source": "test"})
            
            print(f"       Learning Guard结果:")
            print(f"         建议操作: {result.suggested_action}")
            print(f"         置信度: {result.confidence:.3f}")
            print(f"         原因: {result.reason}")
            
            if result.suggested_action == "accept":
                print("       ✅ Learning Guard接受Diff")
            else:
                print(f"       ❌ Learning Guard拒绝Diff")
    else:
        print("   ❌ Reflection未生成Diff")
        
        # 检查原因
        print("\n7. 检查原因...")
        
        # 直接调用extract_patterns
        patterns = reflection_engine.extract_patterns(active_set)
        print(f"   extract_patterns结果: {len(patterns)} 个模式")
        
        if not patterns:
            print("   ❌ extract_patterns未提取到模式")
            
            # 检查配置
            print(f"   当前配置:")
            print(f"     min_pattern_frequency: {reflection_engine.config.get('min_pattern_frequency')}")
            print(f"     min_pattern_weight: {reflection_engine.config.get('min_pattern_weight')}")
            print(f"     confidence_threshold: {reflection_engine.config.get('confidence_threshold')}")
            
            # 检查图数据
            print(f"   图数据:")
            print(f"     节点数: {len(graph.nodes)}")
            print(f"     边数: {len(graph.edges)}")
            
            # 检查active_set
            if active_set.subgraphs:
                subgraph, weight = active_set.subgraphs[0]
                print(f"     第一个子图:")
                print(f"       权重: {weight}")
                print(f"       节点数: {len(subgraph.nodes)}")
                print(f"       边数: {len(subgraph.edges)}")
                
                # 检查边
                edge_count = 0
                for edge_key in subgraph.edges:
                    edge = graph.edges.get(edge_key)
                    if edge:
                        edge_count += 1
                        if edge_count <= 3:  # 只显示前3个
                            src_node = graph.nodes.get(edge.src)
                            dst_node = graph.nodes.get(edge.dst)
                            print(f"       边{edge_count}: {src_node.name if src_node else edge.src} -> "
                                  f"{dst_node.name if dst_node else edge.dst} "
                                  f"({edge.type.value})")
                
                print(f"       有效边数: {edge_count}")
        
except Exception as e:
    print(f"   ❌ Reflection测试失败: {e}")
    import traceback
    traceback.print_exc()

# 多次测试以积累模式
print("\n8. 多次测试以积累模式...")
test_queries = ["测试查询1", "测试查询2", "测试查询3"]

for i, query in enumerate(test_queries):
    print(f"   测试 {i+1}/{len(test_queries)}: {query}")
    
    # 构建新的active_set
    new_active_set = active_set_engine.build_active_set(query)
    
    # 运行Reflection
    diffs = reflection_engine.reflect(new_active_set)
    print(f"     生成 {len(diffs)} 个Diff")
    
    # 检查模式积累
    if hasattr(reflection_engine, 'patterns'):
        print(f"     累计模式数: {len(reflection_engine.patterns)}")

print("\n" + "="*60)
print("📊 测试总结")

# 检查系统状态
graph_edges = len([e for e in graph.edges.values() if hasattr(e, 'active') and e.active])
patterns_count = len(reflection_engine.patterns) if hasattr(reflection_engine, 'patterns') else 0
diffs_generated = reflection_engine.stats.get("diffs_generated", 0) if hasattr(reflection_engine, 'stats') else 0

print(f"\n📈 系统状态:")
print(f"   Graph边数: {graph_edges}")
print(f"   累计模式数: {patterns_count}")
print(f"   Diff生成数: {diffs_generated}")

# 判断系统是否"活了"
system_alive = False
if graph_edges > 0 and diffs_generated > 0:
    system_alive = True

print(f"\n🎯 系统状态: {'✅ 活了！' if system_alive else '❌ 未启动'}")

if system_alive:
    print("\n💡 关键成就:")
    print("   ✅ Graph开始增长")
    print("   ✅ Reflection开始工作")
    print("   ✅ Diff开始生成")
    print("   ✅ 学习管道激活")
    
    print("\n🚀 下一步:")
    print("1. 运行完整200轮测试")
    print("2. 监控关键曲线")
    print("3. 调整参数优化性能")
else:
    print("\n🔧 需要进一步调试:")
    print("1. 检查extract_patterns的实现")
    print("2. 验证配置是否正确传递")
    print("3. 检查图数据和active_set的匹配")

print(f"\n📁 配置摘要:")
print(f"   min_pattern_frequency: {full_config['min_pattern_frequency']}")
print(f"   min_pattern_weight: {full_config['min_pattern_weight']}")
print(f"   confidence_threshold: {full_config['confidence_threshold']}")
print(f"   debug: {full_config['debug']}")