#!/usr/bin/env python3
"""
修复add_edge参数问题
"""

import re

with open('start_local_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找有问题的add_edge调用
pattern = r'graph\.add_edge\(edge_data\[\'source\'\]\, edge_data\[\'target\'\]\,\s*edge_data\.get\(\'type\'\, \'similar_to\'\)\,\s*edge_data\.get\(\'weight\'\, 1\.0\)\)'
if re.search(pattern, content):
    print("找到有问题的add_edge调用")
    
    # 替换为正确的调用
    replacement = "graph.add_edge(edge_data['source'], edge_data['target'])"
    content = re.sub(pattern, replacement, content)
    
    print(f"替换为: {replacement}")
    
    with open('start_local_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ add_edge调用修复完成")
else:
    print("⚠️  未找到预期的add_edge调用模式")
    
    # 直接查看相关代码
    print("\n查看相关代码:")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'add_edge' in line:
            print(f"第{i+1}行: {line}")
