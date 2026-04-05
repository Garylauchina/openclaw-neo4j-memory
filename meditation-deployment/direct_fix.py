#!/usr/bin/env python3
"""
直接修复冥思优化调用
"""

import re

with open('start_local_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到问题行
for i, line in enumerate(lines):
    if 'apply_gnn_meditation_rule()' in line:
        print(f"找到问题行 {i+1}: {line.strip()}")
        
        # 替换为正确的调用
        new_line = '            meditation_result = engine.run_meditation()  # 使用传统冥思规则\n'
        lines[i] = new_line
        print(f"替换为: {new_line.strip()}")
        
        # 在上一行添加注释
        if i > 0:
            lines[i-1] = '            # GNN功能暂时禁用，使用传统冥思规则\n' + lines[i-1]

# 写回文件
with open('start_local_service.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ 修复完成：暂时禁用GNN，使用传统冥思规则")
