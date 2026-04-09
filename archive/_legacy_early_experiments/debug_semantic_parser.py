#!/usr/bin/env python3
"""
调试语义解析器问题
"""

import sys
sys.path.append('.')

print("🔍 调试语义解析器问题")
print("="*60)

from simple_semantic_parser import SimpleSemanticParser

# 创建解析器
parser = SimpleSemanticParser()

# 测试查询
test_queries = [
    "我想投资日本房产",
    "AI创业怎么做？",
    "日本房产回报率如何？",
    "机器学习入门",
    "深度学习与机器学习的区别",
    "Python编程学习路线",
    "神经网络基本原理"
]

print("\n1. 测试语义解析...")
for query in test_queries:
    triples = parser.parse(query)
    print(f"\n   查询: {query}")
    print(f"   解析结果: {len(triples)} 个三元组")
    for triple in triples:
        print(f"     {triple}")

# 检查解析器配置
print("\n2. 检查解析器配置...")
print(f"   关系关键词映射: {parser.relation_keywords}")
print(f"   实体关键词映射: {parser.entity_keywords}")

# 测试具体案例
print("\n3. 测试具体案例...")
specific_queries = [
    ("我喜欢日本房产", "应该解析为 (USER, LIKES, 日本房产)"),
    ("我想投资日本房产", "应该解析为 (USER, INVESTED_IN, 日本房产)"),
    ("AI创业怎么做？", "应该解析为 (USER, ASKING_ABOUT, AI)"),
    ("机器学习入门", "应该解析为 (USER, LEARNING, 机器学习)")
]

for query, expected in specific_queries:
    triples = parser.parse(query)
    print(f"\n   查询: {query}")
    print(f"   预期: {expected}")
    print(f"   实际: {triples}")

# 检查问题
print("\n4. 问题分析...")
print("   从测试看，解析器可能没有正确识别所有查询")
print("   需要检查关键词匹配逻辑")

# 查看解析器内部逻辑
print("\n5. 查看解析器parse方法...")
import inspect
source = inspect.getsource(parser.parse)
print("   方法签名:", source.split('\n')[0])
print("   关键逻辑:")
for line in source.split('\n')[1:10]:
    if "for keyword" in line or "if keyword" in line or "triples.append" in line:
        print(f"     {line.strip()}")