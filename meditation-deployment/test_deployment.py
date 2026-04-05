#!/usr/bin/env python3
"""
部署验证脚本
"""

import sys
import os
from datetime import datetime

try:
    from meditation_engine_with_gnn_fixed import MemoryGraph, MeditationEngine
    from meditation_self_integration import SelfImprovementIntegration
    
    print("✅ 所有模块导入成功")
    
    # 创建测试图
    graph = MemoryGraph()
    print(f"✅ 记忆图创建: {len(graph.nodes)} 个节点")
    
    # 创建引擎
    engine = MeditationEngine(graph)
    print(f"✅ 冥思引擎创建成功")
    
    # 创建集成器
    integration = SelfImprovementIntegration()
    print(f"✅ Self-improving集成器创建成功")
    
    # 测试同步
    sync_result = integration.sync_memories_to_meditation()
    print(f"✅ 记忆同步测试: {sync_result['new_nodes_count']} 个节点")
    
    # 测试GNN冥思（如果有模型）
    model_path = 'models/gnn_meditation_model.pth'
    if os.path.exists(model_path):
        print("测试GNN冥思...")
        gnn_result = engine.apply_gnn_meditation_rule(model_path)
        print(f"✅ GNN冥思测试: {gnn_result.get('average_confidence', 0):.2f} 置信度")
    else:
        print("⚠️  GNN模型不存在，跳过GNN测试")
    
    print("\n✅ 部署验证通过")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
