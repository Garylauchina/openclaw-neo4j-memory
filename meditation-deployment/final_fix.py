#!/usr/bin/env python3
"""
最终修复add_edge调用
"""

import re

with open('start_local_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到并修复add_edge调用
for i, line in enumerate(lines):
    if 'graph.add_edge(edge_data[' in line:
        print(f"找到问题行 {i+1}: {line.strip()}")
        
        # 替换为正确的调用
        new_line = '                    graph.add_edge(edge_data)\n'
        lines[i] = new_line
        print(f"替换为: {new_line.strip()}")
        
        # 也修复前面的节点添加
        for j in range(i-5, i):
            if j >= 0 and 'graph.add_node(node_data)' in lines[j]:
                print(f"找到节点添加行 {j+1}: {lines[j].strip()}")
                # 节点添加是正确的，不需要修改

# 写回文件
with open('start_local_service.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ 最终修复完成")
