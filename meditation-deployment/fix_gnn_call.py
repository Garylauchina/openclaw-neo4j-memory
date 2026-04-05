#!/usr/bin/env python3
"""
修复GNN方法调用问题
"""

import sys
import os

# 检查文件
service_file = 'start_local_service.py'
engine_file = 'meditation_engine_with_gnn_fixed.py'

print("检查文件...")
print(f"1. {service_file}: {os.path.exists(service_file)}")
print(f"2. {engine_file}: {os.path.exists(engine_file)}")

# 检查engine文件中的方法
with open(engine_file, 'r', encoding='utf-8') as f:
    content = f.read()
    if 'def apply_gnn_meditation_rule' in content:
        print("✅ engine文件中找到apply_gnn_meditation_rule方法定义")
        
        # 查找方法签名
        import re
        pattern = r'def apply_gnn_meditation_rule\(self[^)]*\)[^:]*:'
        matches = re.findall(pattern, content)
        if matches:
            print(f"  方法签名: {matches[0]}")
            
            # 检查是否有参数
            if 'model_path' in matches[0]:
                print("  方法需要model_path参数")
            else:
                print("  方法不需要参数")
    else:
        print("❌ engine文件中未找到apply_gnn_meditation_rule方法定义")

# 检查service文件中的调用
with open(service_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'apply_gnn_meditation_rule' in line:
            print(f"\n在service文件第{i+1}行找到调用:")
            print(f"  {line.strip()}")
            
            # 检查调用方式
            if '()' in line and 'model_path' not in line:
                print("⚠️  调用方式: apply_gnn_meditation_rule() - 可能缺少参数")
            elif 'model_path' in line:
                print("✅ 调用包含model_path参数")

print("\n建议修复方案:")
print("1. 如果方法需要model_path参数，修改service文件中的调用")
print("2. 如果方法不存在，检查engine文件的导入和定义")
print("3. 添加错误处理，GNN失败时回退到传统规则")
