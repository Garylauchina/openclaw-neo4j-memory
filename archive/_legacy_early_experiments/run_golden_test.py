#!/usr/bin/env python3
"""
黄金测试执行脚本
目标：生成第一份客观体检报告和基准数据
要求：不允许中途重启，不允许手动干预，必须完整跑完200轮
"""

import sys
sys.path.append('.')

print("🧪 开始黄金测试（200轮回放）")
print("="*60)
print("执行要求：")
print("1. ✅ 不允许中途重启")
print("2. ✅ 不允许手动干预")
print("3. ✅ 必须完整跑完200轮")
print("="*60)

from evaluation_framework import ReplayRunner, TestScenarios, Evaluator
import json
import time
from datetime import datetime

# 创建标准脚本（严格执行规范）
print("\n1. 创建标准脚本...")
script = TestScenarios.topic_switch_test(20)  # 10个话题 × 20轮 = 200轮
print(f"   脚本长度: {len(script)}轮")
print(f"   话题数量: 10个")
print(f"   循环次数: 20次")

# 创建回放执行器
print("\n2. 创建回放执行器...")
runner = ReplayRunner()

# 记录开始时间
start_time = time.time()
print(f"   开始时间: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")

# 运行测试（严格执行规范）
print("\n3. 运行200轮黄金测试...")
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

# 生成基准数据（严格按照规范格式）
print("\n6. 生成基准数据 (Baseline Snapshot v1)...")
print("-"*40)

# 提取关键指标
baseline_data = {
    "version": "v0.1-baseline",
    "total_turns": summary.total_turns,
    "duration_seconds": duration,
    "graph": {
        "nodes": summary.graph_final_nodes,
        "edges": summary.graph_final_edges,
        "growth_rate": summary.graph_growth_rate
    },
    "active_set": {
        "avg_subgraphs": 0,  # 需要从详细指标计算
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
        "cycles": 20,
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
baseline_file = "baseline_data/baseline_v1.json"

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
    print(f"     初始边数: {graph_edges[0] if graph_edges else 0}")
    print(f"     最终边数: {graph_edges[-1] if graph_edges else 0}")
    print(f"     增长率: {summary.graph_growth_rate:.3f}")
    
    print("\n   📈 写入率曲线:")
    if write_ratios:
        avg_write_ratio = sum(write_ratios) / len(write_ratios)
        print(f"     平均写入率: {avg_write_ratio:.3f}")
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
print("✅ 黄金测试完成")
print("✅ 基准数据生成完成")
print("✅ 第一份客观体检报告就绪")
print("="*60)

# 返回基准数据路径
print(f"\n📁 基准文件: {baseline_file}")
print(f"📁 详细结果: {result_file}")
