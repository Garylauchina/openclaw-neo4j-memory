#!/usr/bin/env python3
"""验证 P0-2 实体名称过滤效果"""
import sys
sys.path.insert(0, "/Users/liugang/.openclaw/workspace")
from meditation_memory.entity_extractor import _is_valid_name

# === 应该通过的 ===
valid = [
    "张三", "Neo4j", "OpenClaw", "深度学习",
    "记忆管理系统", "LLM", "刘刚",
    "GitHub", "Tavily Search",
]

# === 应该拦截的 ===
invalid = [
    "一",                        # 纯中文单字
    "---",                       # 纯符号
    "1234",                      # 纯数字
    "[META] 数据质量",           # 元数据标签
    "[TAG] test",                # 元数据标签
    "导致价格暴跌",              # 动词短语碎片
    "怎么",                      # 停用词
    "什么",                      # 停用词
    "导致",                      # 动词短语后缀
    "暴跌",                      # 动词短语后缀
    "The",                       # 英文停用词
    "This",                      # 英文停用词
    "This is a very long entity name that exceeds the limit",  # 超过30字符
    "a",                         # 太短
]

print("=== 应该通过的实体 ===")
pass_count = 0
for name in valid:
    result = _is_valid_name(name)
    status = "✅ PASS" if result else "❌ FAIL"
    if result: pass_count += 1
    print(f"  {status}: '{name}'")

print(f"\n  通过率: {pass_count}/{len(valid)}")

print("\n=== 应该拦截的噪声 ===")
reject_count = 0
for name in invalid:
    result = _is_valid_name(name)
    status = "✅ BLOCKED" if not result else "❌ FAILED (passed through)"
    if not result: reject_count += 1
    print(f"  {status}: '{name}'")

print(f"\n  拦截率: {reject_count}/{len(invalid)}")

print(f"\n=== 总评 ===")
total = len(valid) + len(invalid)
correct = pass_count + reject_count
print(f"  正确率: {correct}/{total} ({100*correct/total:.0f}%)")
