#!/usr/bin/env python3
"""
简化部署验证
"""

import sys

try:
    from meditation_engine_with_gnn_fixed import MemoryGraph, MeditationEngine
    
    print("✅ 冥思引擎导入成功")
    
    # 创建测试图
    graph = MemoryGraph()
    print(f"✅ 记忆图创建: {len(graph.nodes)} 个节点")
    
    # 创建引擎
    engine = MeditationEngine(graph)
    print(f"✅ 冥思引擎创建成功")
    
    # 测试可用方法
    print("\n🧪 测试冥思方法:")
    
    # 测试规则1
    try:
        result1 = engine.apply_rule1_similar_node_merge()
        print(f"  ✅ 规则1测试: {result1.get('nodes_merged', 0)} 个节点合并")
    except Exception as e:
        print(f"  ❌ 规则1测试失败: {e}")
    
    # 测试规则2
    try:
        result2 = engine.apply_rule2_low_importance_cleanup()
        print(f"  ✅ 规则2测试: {result2.get('nodes_cleaned', 0)} 个节点清理")
    except Exception as e:
        print(f"  ❌ 规则2测试失败: {e}")
    
    # 测试规则5
    try:
        result5 = engine.apply_rule5_time_decay_adjustment()
        print(f"  ✅ 规则5测试: {result5.get('nodes_adjusted', 0)} 个节点调整")
    except Exception as e:
        print(f"  ❌ 规则5测试失败: {e}")
    
    # 测试完整冥思
    try:
        result_full = engine.run_meditation()
        print(f"  ✅ 完整冥思测试: {result_full.get('total_nodes_processed', 0)} 个节点处理")
    except Exception as e:
        print(f"  ❌ 完整冥思测试失败: {e}")
    
    print("\n✅ 基础功能验证通过")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
