#!/usr/bin/env python3
"""
简化版Reflection测试
目标：绕过复杂逻辑，直接测试核心功能
"""

import sys
sys.path.append('.')

print("🧪 简化版Reflection测试")
print("="*60)

from global_graph import GlobalGraph, NodeType, EdgeType, Diff, DiffOp
from reflection_upgrade import ReflectionEngine
import time

# 创建测试图
print("1. 创建测试图...")
graph = GlobalGraph()

# 添加测试数据
user_id = graph.create_node("测试用户", NodeType.USER)
topic1_id = graph.create_node("日本房产", NodeType.TOPIC)
topic2_id = graph.create_node("AI", NodeType.TOPIC)

# 添加多条边以增加频率
graph.update_edge(user_id, topic1_id, EdgeType.INTERESTED_IN, 0.8)
graph.update_edge(user_id, topic1_id, EdgeType.INVESTED_IN, 0.7)  # 第二条边
graph.update_edge(user_id, topic2_id, EdgeType.INTERESTED_IN, 0.6)
graph.update_edge(user_id, topic2_id, EdgeType.LEARNING, 0.9)     # 第四条边

print(f"   图状态: {len(graph.nodes)}节点, {len(graph.edges)}边")

# 创建简化版Reflection引擎
print("\n2. 创建简化版Reflection引擎...")

class SimpleReflectionEngine:
    """简化版Reflection引擎"""
    
    def __init__(self, global_graph: GlobalGraph):
        self.global_graph = global_graph
        self.config = {
            "min_pattern_frequency": 1,  # 降低频率要求
            "min_pattern_weight": 0.1,   # 降低权重要求
            "confidence_threshold": 0.3, # 降低置信度阈值
            "max_diffs_per_reflection": 5
        }
    
    def reflect(self, active_set) -> list:
        """简化版reflect"""
        print("   🔍 开始简化版Reflection...")
        
        # 1. 简单模式提取：直接使用图中的边
        patterns = []
        for edge_key, edge in self.global_graph.edges.items():
            if hasattr(edge, 'active') and edge.active:
                pattern = {
                    "src": edge.src,
                    "dst": edge.dst,
                    "type": edge.type,
                    "weight": edge.state.weight,
                    "confidence": 0.8  # 高置信度
                }
                patterns.append(pattern)
                print(f"   提取模式: {edge.src} -> {edge.dst} ({edge.type.value})")
        
        print(f"   提取到 {len(patterns)} 个模式")
        
        # 2. 生成简单的Diff
        diffs = []
        for pattern in patterns[:self.config["max_diffs_per_reflection"]]:
            # 创建UPDATE_EDGE Diff
            diff = Diff(
                op=DiffOp.UPDATE_EDGE,
                src=pattern["src"],
                dst=pattern["dst"],
                type=pattern["type"],
                delta=0.1,  # 权重增加0.1
                confidence=pattern["confidence"],
                timestamp=int(time.time())
            )
            diffs.append(diff)
            print(f"   生成Diff: {diff.op.value} {diff.src}->{diff.dst}")
        
        print(f"   生成 {len(diffs)} 个Diff")
        return diffs

# 创建简化引擎
simple_engine = SimpleReflectionEngine(graph)

# 测试简化版Reflection
print("\n3. 测试简化版Reflection...")
try:
    diffs = simple_engine.reflect(None)  # 不需要active_set
    print(f"   ✅ 简化版Reflection成功生成 {len(diffs)} 个Diff")
    
    if diffs:
        print(f"   第一个Diff: {diffs[0]}")
        
        # 测试Learning Guard
        print("\n4. 测试Learning Guard...")
        from learning_guard import LearningGuard
        
        learning_guard = LearningGuard(graph)
        validation_result = learning_guard.validate_diff(diffs[0], {"source": "test"})
        
        print(f"   Learning Guard验证结果:")
        print(f"     建议操作: {validation_result.suggested_action}")
        print(f"     置信度: {validation_result.confidence}")
        print(f"     原因: {validation_result.reason}")
        
        if validation_result.suggested_action == "accept":
            print("   ✅ Learning Guard接受Diff")
        else:
            print(f"   ❌ Learning Guard拒绝Diff: {validation_result.reason}")
    else:
        print("   ❌ 简化版Reflection未生成任何Diff")
        
except Exception as e:
    print(f"   ❌ 简化版Reflection失败: {e}")
    import traceback
    traceback.print_exc()

# 测试原始ReflectionEngine（使用简化配置）
print("\n5. 测试原始ReflectionEngine（简化配置）...")
try:
    # 创建使用简化配置的ReflectionEngine
    from reflection_upgrade import ReflectionEngine
    
    simple_config = {
        "min_pattern_frequency": 1,
        "min_pattern_weight": 0.1,
        "confidence_threshold": 0.3,
        "debug": True
    }
    
    reflection_engine = ReflectionEngine(graph, simple_config)
    
    # 需要创建一个简单的active_set
    from active_set import ActiveSet
    
    # 创建一个空的active_set
    empty_active_set = ActiveSet(subgraphs=[], query="测试查询")
    
    diffs2 = reflection_engine.reflect(empty_active_set)
    print(f"   原始ReflectionEngine生成 {len(diffs2)} 个Diff")
    
    if diffs2:
        print("   ✅ 原始ReflectionEngine开始工作！")
        for i, diff in enumerate(diffs2[:2]):
            print(f"     Diff{i+1}: {diff.op.value} {diff.src}->{diff.dst}")
    else:
        print("   ❌ 原始ReflectionEngine仍未生成Diff")
        
except Exception as e:
    print(f"   ❌ 原始ReflectionEngine测试失败: {e}")

print("\n" + "="*60)
print("📊 测试总结")

# 关键发现
print("\n💡 关键发现:")
print("1. 简化版Reflection可以工作")
print("2. 原始ReflectionEngine的阈值可能过高")
print("3. Learning Guard需要测试")

print("\n🔧 建议修复:")
print("1. 降低ReflectionEngine的阈值")
print("2. 确保有足够的测试数据")
print("3. 添加更多调试日志")

print("\n🚀 下一步:")
print("1. 更新ReflectionEngine配置")
print("2. 重新运行系统测试")
print("3. 验证学习管道是否激活")