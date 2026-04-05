#!/usr/bin/env python3
"""
修复图传递问题
"""

import re

with open('start_local_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找run_meditation函数中的问题
pattern = r'def run_meditation\(\):.*?graph = MemoryGraph\(\)'
if re.search(pattern, content, re.DOTALL):
    print("找到问题：在run_meditation中创建了新的空图")
    
    # 替换为从同步结果加载图的版本
    new_code = '''def run_meditation():
    """运行冥思优化"""
    logger.info("开始执行冥思优化...")
    
    try:
        from meditation_engine_with_gnn_fixed import MemoryGraph, MeditationEngine
        from meditation_self_integration import SelfImprovementIntegration
        
        # 初始化系统
        graph = MemoryGraph()
        engine = MeditationEngine(graph)
        integration = SelfImprovementIntegration()
        
        # 同步记忆
        logger.info("同步self-improving记忆...")
        sync_result = integration.sync_memories_to_meditation()
        
        # 将同步的节点添加到图中
        if 'sync_result' in sync_result and 'nodes' in sync_result['sync_result']:
            for node_data in sync_result['sync_result']['nodes']:
                graph.add_node(node_data)
            
            # 添加边
            if 'edges' in sync_result['sync_result']:
                for edge_data in sync_result['sync_result']['edges']:
                    graph.add_edge(edge_data['source'], edge_data['target'], 
                                  edge_data.get('type', 'similar_to'), 
                                  edge_data.get('weight', 1.0))
            
            logger.info(f"已加载 {len(sync_result['sync_result']['nodes'])} 个节点和 {len(sync_result['sync_result']['edges'])} 条边到图中")
        
        # 运行冥思
        logger.info("运行冥思优化...")
        meditation_result = engine.run_meditation()
        
        logger.info(f"冥思优化完成")
        logger.info(f"  同步: {sync_result.get('new_nodes_count', 0)} 个节点")
        logger.info(f"  优化: {meditation_result.get('total_nodes_processed', 0)} 个节点")
        
        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f'results/meditation_result_{timestamp}.json'
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump({
                'sync_result': sync_result,
                'meditation_result': meditation_result,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"结果已保存: {result_file}")
        return True
        
    except Exception as e:
        logger.error(f"冥思优化失败: {e}")
        import traceback
        traceback.print_exc()
        return False'''
    
    # 替换整个函数
    content = re.sub(r'def run_meditation\(\):.*?return (True|False)', new_code, content, flags=re.DOTALL)
    
    with open('start_local_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 修复完成：现在同步的节点会正确加载到图中")
else:
    print("⚠️  未找到预期的问题模式")
    
    # 直接查看函数内容
    print("\n当前run_meditation函数内容:")
    match = re.search(r'def run_meditation\(\):.*?(?=def|\Z)', content, re.DOTALL)
    if match:
        print(match.group(0)[:500])
