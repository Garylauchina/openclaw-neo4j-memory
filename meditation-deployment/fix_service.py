#!/usr/bin/env python3
"""
修复service文件中的GNN调用
"""

import re

with open('start_local_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找冥思优化部分
pattern = r'meditation_result = engine\.apply_gnn_meditation_rule\(\)'
if pattern in content:
    print("找到需要修复的调用")
    
    # 替换为带参数和错误处理的版本
    replacement = '''# 尝试GNN冥思
    model_path = 'models/gnn_meditation_model.pth'
    if os.path.exists(model_path):
        try:
            meditation_result = engine.apply_gnn_meditation_rule(model_path)
            logger.info(f"GNN冥思完成: {{meditation_result.get('nodes_processed', 0)}} 个节点")
        except Exception as e:
            logger.warning(f"GNN冥思失败，使用传统规则: {{e}}")
            meditation_result = engine.run_meditation()
            logger.info(f"传统冥思完成: {{meditation_result.get('total_nodes_processed', 0)}} 个节点")
    else:
        logger.warning("GNN模型不存在，使用传统规则")
        meditation_result = engine.run_meditation()
        logger.info(f"传统冥思完成: {{meditation_result.get('total_nodes_processed', 0)}} 个节点")'''
    
    content = re.sub(pattern, replacement, content)
    
    # 添加os导入
    if 'import os' not in content:
        content = content.replace('import schedule', 'import schedule\nimport os')
    
    with open('start_local_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 修复完成")
else:
    print("⚠️  未找到需要修复的调用模式")
