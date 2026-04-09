#!/usr/bin/env python3
"""
最终诊断：为什么Reflection不工作
"""

import sys
sys.path.append('.')

print("🔍 最终诊断：Reflection系统")
print("="*60)

from global_graph import GlobalGraph, NodeType, EdgeType
from active_subgraph import ActiveSubgraphEngine
from active_set import ActiveSetEngine, ActiveSet
from reflection_upgrade import ReflectionEngine
import time

# 创建测试环境
print("1. 创建测试环境...")
graph = GlobalGraph()

# 添加丰富的测试数据
print("2. 添加丰富的测试数据...")
user_id = graph.create_node("测试用户", NodeType.USER)
topics = []
for i in range(5):
    topic_id = graph.create_node(f"话题{i}", NodeType.TOPIC)
    topics.append(topic_id)
    
    # 添加多条边（增加频率）
    graph.update_edge(user_id, topic_id, EdgeType.LIKES, 0.7 + i*0.05)
    graph.update_edge(user_id, topic_id, EdgeType.INTERESTED_IN, 0.6 + i*0.05)
    if i % 2 == 0:
        graph.update_edge(user_id, topic_id, EdgeType.INVESTED_IN, 0.8 + i*0.05)

print(f"   图状态: {len(graph.nodes)}节点, {len(graph.edges)}边")

# 创建Reflection引擎（极低阈值）
print("\n3. 创建Reflection引擎（极低阈值）...")
ultra_low_config = {
    "min_pattern_frequency": 1,
    "min_pattern_weight": 0.01,
    "confidence_threshold": 0.1,
    "debug": True
}

reflection_engine = ReflectionEngine(graph, ultra_low_config)

# 创建Active Set
print("\n4. 创建Active Set...")
active_set_engine = ActiveSetEngine(graph)
active_set = active_set_engine.build_active_set("测试查询")
print(f"   Active Set子图数: {len(active_set.subgraphs)}")

# 详细调试extract_patterns
print("\n5. 详细调试extract_patterns...")

# 检查active_set内容
if active_set.subgraphs:
    print(f"   第一个子图信息:")
    subgraph, weight = active_set.subgraphs[0]
    print(f"     权重: {weight}")
    print(f"     节点数: {len(subgraph.nodes)}")
    print(f"     边数: {len(subgraph.edges)}")
    
    # 检查子图中的边
    print(f"     子图中的边:")
    for edge_key in list(subgraph.edges)[:5]:  # 只显示前5个
        edge = graph.edges.get(edge_key)
        if edge:
            src_node = graph.nodes.get(edge.src)
            dst_node = graph.nodes.get(edge.dst)
            print(f"       {src_node.name if src_node else edge.src} -> "
                  f"{dst_node.name if dst_node else edge.dst} "
                  f"({edge.type.value}): {edge.state.weight}")
else:
    print("   ❌ Active Set没有子图")

# 直接调用extract_patterns并添加详细日志
print("\n6. 直接调用extract_patterns（添加详细日志）...")

# 临时修改extract_patterns方法以添加日志
original_extract_patterns = reflection_engine.extract_patterns

def debug_extract_patterns(active_set):
    print("   🔍 开始extract_patterns...")
    print(f"     输入active_set子图数: {len(active_set.subgraphs)}")
    
    patterns = []
    
    # 遍历所有子图
    for subgraph_idx, (subgraph, weight) in enumerate(active_set.subgraphs):
        print(f"     处理子图 {subgraph_idx+1}, 权重: {weight}")
        
        # 提取子图中的边
        for edge_key in subgraph.edges:
            edge = reflection_engine.global_graph.edges.get(edge_key)
            if not edge:
                print(f"       ❌ 边 {edge_key} 不存在于全局图中")
                continue
            
            if not hasattr(edge, 'active') or not edge.active:
                print(f"       ⚠️  边 {edge_key} 不活跃")
                continue
            
            # 创建模式键
            pattern_key = f"{edge.src}::{edge.dst}::{edge.type.value}"
            print(f"       边: {edge.src}->{edge.dst} ({edge.type.value}), "
                  f"权重: {edge.state.weight}, 模式键: {pattern_key}")
            
            # 检查是否已存在
            if pattern_key in reflection_engine.patterns:
                pattern = reflection_engine.patterns[pattern_key]
                print(f"       模式已存在: 频率={pattern.frequency}, 总权重={pattern.total_weight}")
                pattern.update(edge.state.weight * weight, f"subgraph_{subgraph_idx}")
            else:
                from reflection_upgrade import Pattern
                pattern = Pattern(
                    src_node_id=edge.src,
                    dst_node_id=edge.dst,
                    edge_type=edge.type,
                    frequency=1,
                    total_weight=edge.state.weight * weight,
                    subgraph_ids=[f"subgraph_{subgraph_idx}"],
                )
                reflection_engine.patterns[pattern_key] = pattern
                patterns.append(pattern)
                print(f"       创建新模式: 频率=1, 总权重={pattern.total_weight}")
    
    print(f"     提取到 {len(patterns)} 个新模式")
    
    # 过滤和排序
    filtered_patterns = []
    for pattern in patterns:
        # 应用过滤条件
        if (pattern.frequency >= reflection_engine.config["min_pattern_frequency"] and
            pattern.avg_weight >= reflection_engine.config["min_pattern_weight"]):
            
            # 计算置信度
            pattern_confidence = reflection_engine._compute_pattern_confidence(pattern)
            print(f"       模式 {pattern.src_node_id}->{pattern.dst_node_id}: "
                  f"频率={pattern.frequency}, 平均权重={pattern.avg_weight:.3f}, "
                  f"置信度={pattern_confidence:.3f}")
            
            if pattern_confidence > reflection_engine.config["confidence_threshold"]:
                filtered_patterns.append(pattern)
                print(f"       ✅ 模式通过过滤")
            else:
                print(f"       ❌ 模式置信度不足")
        else:
            print(f"       ❌ 模式不满足频率或权重要求")
    
    print(f"     过滤后剩余 {len(filtered_patterns)} 个模式")
    return filtered_patterns

# 临时替换方法
reflection_engine.extract_patterns = debug_extract_patterns

# 调用extract_patterns
try:
    patterns = reflection_engine.extract_patterns(active_set)
    print(f"\n   extract_patterns结果: {len(patterns)} 个模式")
    
    if patterns:
        print("   ✅ extract_patterns开始工作！")
        for i, pattern in enumerate(patterns[:3]):
            print(f"     模式{i+1}: {pattern.src_node_id}->{pattern.dst_node_id} "
                  f"({pattern.edge_type.value}), 频率={pattern.frequency}, "
                  f"平均权重={pattern.avg_weight:.3f}")
    else:
        print("   ❌ extract_patterns仍未提取到模式")
        
except Exception as e:
    print(f"   ❌ extract_patterns失败: {e}")
    import traceback
    traceback.print_exc()

# 恢复原始方法
reflection_engine.extract_patterns = original_extract_patterns

# 测试完整reflect流程
print("\n7. 测试完整reflect流程...")
try:
    diffs = reflection_engine.reflect(active_set)
    print(f"   reflect生成 {len(diffs)} 个Diff")
    
    if diffs:
        print("   ✅ reflect开始工作！")
        for i, diff in enumerate(diffs[:3]):
            print(f"     Diff{i+1}: {diff.op.value} {diff.src}->{diff.dst}")
            
            # 测试Learning Guard
            from learning_guard import LearningGuard
            
            learning_guard = LearningGuard(graph, {"debug": True})
            result = learning_guard.validate_diff(diff, {"source": "diagnosis"})
            
            print(f"       Learning Guard: {result.suggested_action}, "
                  f"置信度: {result.confidence:.3f}, 原因: {result.reason}")
    else:
        print("   ❌ reflect未生成Diff")
        
except Exception as e:
    print(f"   ❌ reflect失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("🔍 诊断总结")

# 关键问题识别
print("\n💡 关键问题识别:")

# 检查图数据
if len(graph.edges) >= 5:
    print("✅ 图有足够的数据")
else:
    print("❌ 图数据不足")

# 检查active_set
if active_set and active_set.subgraphs:
    print("✅ Active Set有子图")
else:
    print("❌ Active Set无子图")

# 检查模式提取
if hasattr(reflection_engine, 'patterns'):
    print(f"✅ ReflectionEngine有模式存储 ({len(reflection_engine.patterns)}个模式)")
else:
    print("❌ ReflectionEngine无模式存储")

print("\n🔧 根本原因分析:")
print("1. 可能问题：extract_patterns的过滤条件仍然太严格")
print("2. 可能问题：子图中的边与全局图中的边不匹配")
print("3. 可能问题：模式置信度计算有问题")

print("\n🚀 立即修复方案:")
print("1. 将min_pattern_frequency设置为1")
print("2. 将min_pattern_weight设置为0.01")
print("3. 将confidence_threshold设置为0.1")
print("4. 确保active_set包含有效的子图")

print("\n📊 验证方法:")
print("1. 运行修复后的测试")
print("2. 检查extract_patterns的详细日志")
print("3. 验证Diff生成和Learning Guard验证")

print("\n🎯 成功标准:")
print("✅ Graph开始增长")
print("✅ Diff开始出现")
print("✅ 写入率 > 0")
print("✅ 系统状态: 活了")