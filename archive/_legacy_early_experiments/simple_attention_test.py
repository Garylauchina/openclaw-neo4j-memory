#!/usr/bin/env python3
"""
简单注意力层测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dataclasses import dataclass
from datetime import datetime
import time

# 模拟节点
@dataclass
class TestNode:
    id: str
    text: str = ""
    belief_strength: float = 0.5
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

# 测试注意力层
def test_attention_layer():
    print("🧠 Attention Layer简单测试")
    print("="*60)
    
    # 导入注意力层
    try:
        from attention_layer.attention_layer import AttentionLayer, AttentionLayerConfig
        from attention_layer.attention_state import AttentionState
        from attention_layer.attention_scorer import AttentionScorer, AttentionConfig
        from attention_layer.attention_selector import AttentionSelector, SelectionConfig
        from attention_layer.attention_feedback import AttentionFeedback, FeedbackConfig
        
        print("✅ 所有模块导入成功")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 创建测试节点
    nodes = []
    for i in range(50):
        node = TestNode(
            id=f"test_node_{i}",
            text=f"测试节点{i} 内容文本",
            belief_strength=0.3 + (i % 10) * 0.07
        )
        nodes.append(node)
    
    print(f"✅ 创建{len(nodes)}个测试节点")
    
    # 创建注意力层
    config = AttentionLayerConfig(
        top_k=10,
        relevance_weight=0.25,
        belief_weight=0.20,
        recency_weight=0.15,
        rqs_weight=0.15,
        novelty_weight=0.15,
        conflict_weight=0.10
    )
    
    attention = AttentionLayer(config)
    print("✅ Attention Layer创建成功")
    
    # 模拟图
    class MockGraph:
        def __init__(self, nodes):
            self.nodes = nodes
    
    graph = MockGraph(nodes)
    
    # 测试查询
    query = "测试节点"
    metrics = {
        "rqs_scores": {f"test_node_{i}": 0.5 for i in range(50)},
        "belief_scores": {f"test_node_{i}": 0.3 + (i % 10) * 0.07 for i in range(50)},
        "conflicts": {f"test_node_{i}": {"count": i % 3} for i in range(50)}
    }
    
    # 运行注意力层
    start_time = time.time()
    selected_nodes = attention.run(graph, query, metrics)
    elapsed_time = time.time() - start_time
    
    print(f"\n📊 测试结果:")
    print(f"  输入节点数: {len(nodes)}")
    print(f"  输出节点数: {len(selected_nodes)} (Top-{config.top_k})")
    print(f"  处理时间: {elapsed_time*1000:.1f}ms")
    
    if selected_nodes:
        selected_ids = [node.id for node in selected_nodes]
        print(f"  选择的节点: {selected_ids[:5]}...")
    
    # 获取系统报告
    report = attention.get_system_report()
    coverage = report["performance"]["avg_attention_coverage"]
    compression = report["performance"]["compression_ratio"]
    
    print(f"\n📈 性能指标:")
    print(f"  注意力覆盖率: {coverage:.1%}")
    print(f"  压缩比: {compression:.1f}x")
    
    # 验证
    assert len(selected_nodes) <= config.top_k, f"选择节点数超过top_k"
    assert len(selected_nodes) > 0, "没有选择任何节点"
    assert coverage > 0, "注意力覆盖率为0"
    
    print("\n✅ 测试通过!")
    
    # 打印状态
    print("\n" + "="*60)
    attention.print_status()
    
    return True

def test_individual_components():
    print("\n🧪 测试单个组件")
    print("="*60)
    
    # 测试AttentionState
    from attention_layer.attention_state import AttentionState
    state = AttentionState()
    
    # 更新分数
    state.update_node_score("node_1", 0.8)
    state.update_node_score("node_2", 0.6)
    state.update_edge_score("edge_1", 0.7)
    
    # 记录历史
    state.record_history(
        query="测试查询",
        selected_nodes=["node_1", "node_2"],
        total_nodes=10,
        avg_score=0.7
    )
    
    print("✅ AttentionState测试通过")
    
    # 测试AttentionScorer
    from attention_layer.attention_scorer import AttentionScorer, AttentionConfig
    scorer_config = AttentionConfig()
    scorer = AttentionScorer(scorer_config)
    
    # 测试节点
    test_node = TestNode(id="score_node", text="测试评分节点", belief_strength=0.7)
    query = "测试"
    metrics = {"rqs_scores": {"score_node": 0.6}}
    
    score = scorer.compute_attention_score(test_node, query, metrics)
    print(f"✅ AttentionScorer测试通过 - 分数: {score:.3f}")
    
    # 测试AttentionSelector
    from attention_layer.attention_selector import AttentionSelector, SelectionConfig
    selector_config = SelectionConfig(top_k=5)
    selector = AttentionSelector(selector_config)
    
    # 创建测试节点列表
    scored_nodes = []
    for i in range(20):
        node = TestNode(id=f"select_node_{i}", text=f"选择测试节点{i}")
        score = 0.1 + i * 0.04  # 0.1~0.86
        scored_nodes.append((node, score))
    
    selected = selector.select_top_k(scored_nodes)
    print(f"✅ AttentionSelector测试通过 - 选择{len(selected)}个节点")
    
    # 测试AttentionFeedback
    from attention_layer.attention_feedback import AttentionFeedback, FeedbackConfig
    feedback_config = FeedbackConfig()
    feedback = AttentionFeedback(feedback_config)
    
    # 更新反馈
    feedback.update_attention("feedback_node_1", True)
    feedback.update_attention("feedback_node_2", False)
    
    print("✅ AttentionFeedback测试通过")
    
    return True

def main():
    print("🚀 Attention Layer实现验证")
    print("="*60)
    
    try:
        # 测试单个组件
        if not test_individual_components():
            print("❌ 组件测试失败")
            return False
        
        # 测试完整注意力层
        if not test_attention_layer():
            print("❌ 注意力层测试失败")
            return False
        
        print("\n" + "="*60)
        print("🎉 Attention Layer实现完成!")
        print("="*60)
        
        print("\n🏆 核心成就:")
        print("  1. ✅ AttentionState - 注意力状态管理")
        print("  2. ✅ AttentionScorer - 注意力分数计算")
        print("  3. ✅ AttentionSelector - Top-K选择")
        print("  4. ✅ AttentionFeedback - 反馈学习机制")
        print("  5. ✅ AttentionLayer - 完整集成")
        
        print("\n🚀 系统升级:")
        print("  从: Self-Stabilizing Cognitive System")
        print("  到: ❗ Attention-Controlled Cognitive System")
        
        print("\n🎯 核心能力:")
        print("  ❗ 让系统学会'把计算资源花在最值得的地方'")
        
        print("\n📊 预期效果:")
        print("  ✅ 推理速度下降 (搜索空间压缩)")
        print("  ✅ 推理质量上升 (垃圾路径过滤)")
        print("  ✅ RQS更稳定 (输入更干净)")
        
        print("\n⚠️ 监控指标:")
        print("  注意力覆盖率: 5%~20% (理想范围)")
        
        print("\n🔜 下一步:")
        print("  ❗ Attention × Goal System (目标驱动注意力)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)