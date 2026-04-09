#!/usr/bin/env python3
"""
修复后系统测试（解决冷启动问题）
目标：验证语义解析器集成后系统是否"活了"
"""

import sys
sys.path.append('.')

print("🧪 修复后系统测试（解决冷启动问题）")
print("="*60)
print("测试目标：验证系统是否开始工作")
print("关键指标：edges > 0, diff_generated > 0, write_ratio > 0")
print("="*60)

from evaluation_framework import ReplayRunner, TestScenarios
import json
import time
from datetime import datetime

# 创建测试脚本（使用标准话题切换测试）
print("\n1. 创建测试脚本...")
script = TestScenarios.topic_switch_test(2)  # 20轮测试
print(f"   脚本长度: {len(script)}轮")
print(f"   示例查询: {script[:3]}...")

# 创建回放执行器（包含语义解析器）
print("\n2. 创建修复后的回放执行器...")
runner = ReplayRunner()

# 记录开始时间
start_time = time.time()
print(f"   开始时间: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")

# 运行测试
print("\n3. 运行修复后测试...")
print("-"*40)

# 手动运行测试以获取详细日志
results = []
for turn_id, query in enumerate(script):
    if turn_id % 5 == 0:
        print(f"   处理第 {turn_id}/{len(script)} 轮: {query[:20]}...")
    
    result = runner.step(query)
    results.append(result)
    
    # 打印关键信息
    if result["success"]:
        print(f"     ✅ 成功 | 解析: {result.get('parsed_triple', False)} | "
              f"Diff生成: {result.get('diffs_generated', 0)} | "
              f"Diff应用: {result.get('diffs_applied', 0)}")
    else:
        print(f"     ❌ 失败: {result.get('error', '未知错误')}")

# 记录结束时间
end_time = time.time()
duration = end_time - start_time
print(f"\n   结束时间: {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   总耗时: {duration:.1f}秒")
print(f"   平均每轮: {duration/len(script)*1000:.1f}毫秒")

# 计算统计信息
print("\n4. 统计信息...")
print("-"*40)

total_success = sum(1 for r in results if r["success"])
total_parsed = sum(1 for r in results if r.get("parsed_triple", False))
total_diffs_generated = sum(r.get("diffs_generated", 0) for r in results)
total_diffs_applied = sum(r.get("diffs_applied", 0) for r in results)

print(f"   总轮数: {len(results)}")
print(f"   成功轮数: {total_success}")
print(f"   解析成功: {total_parsed}")
print(f"   Diff生成总数: {total_diffs_generated}")
print(f"   Diff应用总数: {total_diffs_applied}")

if total_diffs_generated > 0:
    write_ratio = total_diffs_applied / total_diffs_generated
    print(f"   写入率: {write_ratio:.3f}")
else:
    print(f"   写入率: 0.000 (无Diff生成)")

# 检查Graph状态
print("\n5. Graph状态检查...")
print("-"*40)

graph_nodes = len(runner.global_graph.nodes)
graph_edges = len([e for e in runner.global_graph.edges.values() if e.active])

print(f"   Graph节点数: {graph_nodes}")
print(f"   Graph边数: {graph_edges}")

# 检查Reflection状态
print("\n6. Reflection状态检查...")
print("-"*40)

# 尝试手动调用Reflection来检查问题
from reflection_upgrade import ReflectionEngine
from active_set import ActiveSet

# 创建一个测试active_set
test_active_set = ActiveSet(subgraphs=[], query="测试查询")

# 检查Reflection是否工作
reflection_engine = ReflectionEngine(runner.global_graph)
try:
    diffs = reflection_engine.reflect(test_active_set)
    print(f"   Reflection测试: 生成 {len(diffs)} 个Diff")
    
    if diffs:
        print(f"   Diff类型: {type(diffs[0]) if diffs else '无'}")
        print(f"   Diff内容示例: {str(diffs[0])[:100] if diffs else '无'}")
    else:
        print("   ❌ Reflection未生成任何Diff")
        
except Exception as e:
    print(f"   ❌ Reflection调用失败: {e}")

# 检查Pattern Extraction
print("\n7. Pattern Extraction检查...")
print("-"*40)

try:
    # 检查Reflection内部状态
    if hasattr(reflection_engine, 'extract_patterns'):
        patterns = reflection_engine.extract_patterns(test_active_set)
        print(f"   Pattern提取: {len(patterns)} 个模式")
        
        if patterns:
            print(f"   模式置信度: {[p.get('confidence', 0) for p in patterns[:3]]}")
        else:
            print("   ❌ 未提取到任何模式")
    else:
        print("   ⚠️  ReflectionEngine没有extract_patterns方法")
        
except Exception as e:
    print(f"   ❌ Pattern提取失败: {e}")

# 生成测试报告
print("\n8. 测试报告...")
print("-"*40)

# 系统是否"活了"的判断标准
system_alive = False
if graph_edges > 0 and total_diffs_generated > 0:
    system_alive = True

print(f"   Graph开始增长: {'✅' if graph_edges > 0 else '❌'} ({graph_edges}边)")
print(f"   Diff开始出现: {'✅' if total_diffs_generated > 0 else '❌'} ({total_diffs_generated}个)")
print(f"   写入率非零: {'✅' if total_diffs_generated > 0 and total_diffs_applied > 0 else '❌'}")
print(f"   系统状态: {'✅ 活了' if system_alive else '❌ 未启动'}")

# 保存基准数据
print("\n9. 保存基准数据...")
print("-"*40)

import os
os.makedirs("baseline_data", exist_ok=True)
baseline_file = "baseline_data/baseline_v2_fixed.json"

baseline_data = {
    "version": "v0.2-fixed",
    "total_turns": len(results),
    "duration_seconds": duration,
    "graph": {
        "nodes": graph_nodes,
        "edges": graph_edges,
        "growth_rate": 0.0  # 需要更长时间测试
    },
    "reflection": {
        "generated": total_diffs_generated,
        "applied": total_diffs_applied,
        "write_ratio": write_ratio if total_diffs_generated > 0 else 0.0
    },
    "semantic_parsing": {
        "parsed_count": total_parsed,
        "parsing_rate": total_parsed / len(results) if results else 0.0
    },
    "system_alive": system_alive,
    "timestamp": datetime.now().isoformat(),
    "test_conditions": {
        "script_type": "topic_switch",
        "total_queries": len(script),
        "topics_count": 10,
        "cycles": 2,
        "with_semantic_parser": True
    }
}

with open(baseline_file, 'w', encoding='utf-8') as f:
    json.dump(baseline_data, f, ensure_ascii=False, indent=2)

print(f"   基准数据已保存到: {baseline_file}")
print(f"   文件大小: {os.path.getsize(baseline_file)}字节")

print("\n" + "="*60)
print("✅ 修复后系统测试完成")
print("="*60)

# 打印关键结论
print("\n🎯 关键结论:")
if system_alive:
    print("✅ 系统已成功启动！")
    print("   - Graph开始增长")
    print("   - Reflection开始工作")
    print("   - 学习管道已激活")
else:
    print("❌ 系统仍未启动")
    print("   - 需要进一步调试")
    print("   - 可能问题：Pattern Extraction或Diff生成")

print(f"\n📁 基准文件: {baseline_file}")
print("📊 下一步：运行完整200轮测试验证稳定性")