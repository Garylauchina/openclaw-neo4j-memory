#!/usr/bin/env python3
"""
实际黄金测试（小规模）
目标：生成第一份客观体检报告和基准数据
使用20轮测试来验证系统
"""

import sys
sys.path.append('.')

print("🧪 实际黄金测试（小规模 - 20轮）")
print("="*60)
print("执行要求：")
print("1. ✅ 不允许中途重启")
print("2. ✅ 不允许手动干预")
print("3. ✅ 必须完整跑完20轮")
print("="*60)

from evaluation_framework import ReplayRunner, TestScenarios, Evaluator
import json
import time
from datetime import datetime

# 创建标准脚本（小规模）
print("\n1. 创建标准脚本...")
script = TestScenarios.topic_switch_test(2)  # 10个话题 × 2轮 = 20轮
print(f"   脚本长度: {len(script)}轮")
print(f"   话题数量: 10个")
print(f"   循环次数: 2次")
print(f"   示例查询: {script[:3]}...")

# 创建回放执行器
print("\n2. 创建回放执行器...")
runner = ReplayRunner()

# 记录开始时间
start_time = time.time()
print(f"   开始时间: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")

# 运行测试
print("\n3. 运行20轮黄金测试...")
print("-"*40)

summary = runner.run(script)

# 记录结束时间
end_time = time.time()
duration = end_time - start_time
print(f"   结束时间: {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   总耗时: {duration:.1f}秒")
print(f"   平均每轮: {duration/len(script)*1000:.1f}毫秒")

# 打印总结
print("\n4. 测试总结:")
print("-"*40)
summary.print_summary()

# 评估健康度
print("\n5. 系统健康度评估:")
print("-"*40)
evaluator = Evaluator()
health_eval = evaluator.evaluate_system_health(summary)

print(f"   健康状态: {health_eval['health_status']}")
print(f"   综合评分: {health_eval['overall_score']:.1f}/100")

if health_eval['warnings']:
    print("\n⚠️  警告:")
    for warning in health_eval['warnings']:
        print(f"   • {warning}")

if health_eval['suggestions']:
    print("\n💡 建议:")
    for suggestion in health_eval['suggestions']:
        print(f"   • {suggestion}")

# 生成基准数据
print("\n6. 生成基准数据 (Baseline Snapshot v1)...")
print("-"*40)

# 提取关键指标
baseline_data = {
    "version": "v0.1-baseline-small",
    "total_turns": summary.total_turns,
    "duration_seconds": duration,
    "graph": {
        "nodes": summary.graph_final_nodes,
        "edges": summary.graph_final_edges,
        "growth_rate": summary.graph_growth_rate
    },
    "active_set": {
        "avg_subgraphs": 0,
        "avg_entropy": summary.avg_entropy,
        "entropy_std": summary.entropy_std,
        "entropy_trend": summary.entropy_trend
    },
    "reflection": {
        "generated": sum(m.reflection_diffs_generated for m in runner.metrics_collector.turn_metrics),
        "applied": sum(m.reflection_diffs_applied for m in runner.metrics_collector.turn_metrics),
        "rejected": sum(m.reflection_diffs_rejected for m in runner.metrics_collector.turn_metrics),
        "write_ratio": summary.write_ratio
    },
    "learning_guard": {
        "pass_rate": summary.avg_pass_rate,
        "conflicts": sum(m.learning_guard_conflicts for m in runner.metrics_collector.turn_metrics)
    },
    "health_score": summary.overall_score,
    "timestamp": datetime.now().isoformat(),
    "test_conditions": {
        "script_type": "topic_switch",
        "total_queries": len(script),
        "topics_count": 10,
        "cycles": 2,
        "strict_mode": True
    }
}

# 计算平均子图数
if runner.metrics_collector.turn_metrics:
    avg_subgraphs = sum(m.active_set_size for m in runner.metrics_collector.turn_metrics) / len(runner.metrics_collector.turn_metrics)
    baseline_data["active_set"]["avg_subgraphs"] = round(avg_subgraphs, 1)

# 保存基准数据
import os
os.makedirs("baseline_data", exist_ok=True)
baseline_file = "baseline_data/baseline_v1_small.json"

with open(baseline_file, 'w', encoding='utf-8') as f:
    json.dump(baseline_data, f, ensure_ascii=False, indent=2)

print(f"   基准数据已保存到: {baseline_file}")
print(f"   文件大小: {os.path.getsize(baseline_file)}字节")

# 打印基准数据摘要
print("\n📊 基准数据摘要:")
print(json.dumps(baseline_data, ensure_ascii=False, indent=2))

# 保存详细结果
print("\n7. 保存详细结果...")
print("-"*40)
result_file = runner.save_results("evaluation_results")
print(f"   详细结果已保存到: {result_file}")

# 生成曲线分析
print("\n8. 关键曲线分析:")
print("-"*40)

# 提取关键曲线数据
if runner.metrics_collector.turn_metrics:
    turns = list(range(len(runner.metrics_collector.turn_metrics)))
    
    # Graph增长曲线
    graph_edges = [m.graph_edges for m in runner.metrics_collector.turn_metrics]
    
    # 写入率曲线
    write_ratios = []
    for m in runner.metrics_collector.turn_metrics:
        if m.reflection_diffs_generated > 0:
            write_ratios.append(m.reflection_diffs_applied / m.reflection_diffs_generated)
        else:
            write_ratios.append(0)
    
    # Entropy曲线
    entropies = [m.active_set_entropy for m in runner.metrics_collector.turn_metrics]
    
    # 冲突检测曲线
    conflicts = [m.learning_guard_conflicts for m in runner.metrics_collector.turn_metrics]
    
    print("   📈 Graph增长曲线:")
    if graph_edges:
        print(f"     初始边数: {graph_edges[0]}")
        print(f"     最终边数: {graph_edges[-1]}")
        print(f"     增长率: {summary.graph_growth_rate:.3f}")
        print(f"     趋势: {'增长' if graph_edges[-1] > graph_edges[0] else '稳定/下降'}")
    
    print("\n   📈 写入率曲线:")
    if write_ratios:
        avg_write_ratio = sum(write_ratios) / len(write_ratios)
        print(f"     平均写入率: {avg_write_ratio:.3f}")
        if len(write_ratios) > 1:
            print(f"     写入率趋势: {'下降' if write_ratios[-1] < write_ratios[0] else '稳定/上升'}")
    
    print("\n   📈 Entropy曲线:")
    if entropies:
        print(f"     平均entropy: {summary.avg_entropy:.3f}")
        print(f"     entropy趋势: {summary.entropy_trend}")
        print(f"     范围: {min(entropies):.3f} ~ {max(entropies):.3f}")
    
    print("\n   📈 冲突检测曲线:")
    if conflicts:
        total_conflicts = sum(conflicts)
        print(f"     总冲突数: {total_conflicts}")
        print(f"     平均每轮: {total_conflicts/len(conflicts):.2f}")

print("\n" + "="*60)
print("✅ 黄金测试（小规模）完成")
print("✅ 基准数据生成完成")
print("✅ 第一份客观体检报告就绪")
print("="*60)

# 回答系统体检问题
print("\n9. 系统体检问题回答:")
print("-"*40)

print("1️⃣ 图是否'收敛'？")
if summary.graph_growth_rate < 0.5:
    print("   ✅ YES → 图增长趋缓（好现象）")
else:
    print("   ❌ NO → 必须调Reflection")

print("\n2️⃣ 是否出现'认知锁死'？")
if summary.avg_entropy < 0.3:
    print(f"   ❌ YES → entropy → {summary.avg_entropy:.3f} (危险)")
else:
    print(f"   ✅ NO → entropy = {summary.avg_entropy:.3f} (正常)")

print("\n3️⃣ 是否'学习过快'？")
if summary.write_ratio > 0.3:
    print(f"   ❌ YES → write_ratio = {summary.write_ratio:.3f} > 0.3")
else:
    print(f"   ✅ NO → write_ratio = {summary.write_ratio:.3f} (正常)")

print("\n4️⃣ 是否'学习过慢'？")
if summary.write_ratio < 0.05:
    print(f"   ❌ YES → write_ratio = {summary.write_ratio:.3f} < 0.05")
else:
    print(f"   ✅ NO → write_ratio = {summary.write_ratio:.3f} (正常)")

print("\n5️⃣ 是否'错误被放大'？")
conflicts_count = sum(m.learning_guard_conflicts for m in runner.metrics_collector.turn_metrics)
if conflicts_count > 0:
    print(f"   ⚠️  检测到冲突: {conflicts_count}次 (需要进一步分析)")
else:
    print("   ✅ 未检测到冲突")

print("\n6️⃣ 是否'话题漂移'？")
print("   ⏳ 需要更详细的话题分析（后续实现）")

print("\n" + "="*60)
print("📁 基准文件: baseline_data/baseline_v1_small.json")
print("📁 详细结果: evaluation_results/replay_results_*.json")
print("="*60)
