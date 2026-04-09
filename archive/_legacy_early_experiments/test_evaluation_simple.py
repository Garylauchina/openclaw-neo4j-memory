#!/usr/bin/env python3
"""
简化版评估框架测试
"""

import sys
sys.path.append('.')

print("🧪 简化版评估框架测试")
print("="*60)

# 导入必要的类
from evaluation_framework import TestScenarios, Evaluator

print("1. 测试脚本生成测试")
print("-"*40)

# 测试话题切换
topic_script = TestScenarios.topic_switch_test(1)  # 10轮
print(f"话题切换测试: {len(topic_script)}轮")
print(f"示例: {topic_script[:3]}...")

# 测试一致性强化
consistency_script = TestScenarios.consistency_reinforcement_test(2)  # 8轮
print(f"一致性强化测试: {len(consistency_script)}轮")
print(f"示例: {consistency_script[:3]}...")

# 测试冲突
conflict_script = TestScenarios.conflict_test()  # 8轮
print(f"冲突测试: {len(conflict_script)}轮")
print(f"示例: {conflict_script[:3]}...")

# 测试压力
stress_script = TestScenarios.stress_test(5)  # 5轮
print(f"压力测试: {len(stress_script)}轮")
print(f"示例: {stress_script[:3]}...")

print("\n2. 评估器功能测试")
print("-"*40)

# 创建模拟测试总结
from evaluation_framework import TestSummary
import time

summary = TestSummary(
    test_name="模拟测试",
    total_turns=100,
    total_queries=100,
    graph_growth_rate=0.25,
    avg_entropy=0.8,
    write_ratio=0.3,
    avg_processing_time_ms=150,
    stability_score=95,
    learning_score=85,
    performance_score=90
)
summary.calculate_scores()

print(f"测试名称: {summary.test_name}")
print(f"总轮数: {summary.total_turns}")
print(f"Graph增长率: {summary.graph_growth_rate:.3f}")
print(f"Active Set熵: {summary.avg_entropy:.3f}")
print(f"写入率: {summary.write_ratio:.3f}")
print(f"综合评分: {summary.overall_score:.1f}/100")

# 评估健康度
evaluator = Evaluator()
health_eval = evaluator.evaluate_system_health(summary)

print(f"\n健康状态: {health_eval['health_status']}")
print(f"综合评分: {health_eval['overall_score']:.1f}/100")

print("\n3. 版本对比测试")
print("-"*40)

# 模拟版本对比
v1_results = {
    "overall_score": 75.0,
    "summary": {
        "graph_growth_rate": 0.8,
        "avg_entropy": 0.4,
        "write_ratio": 0.6,
        "avg_processing_time_ms": 800,
        "stability_score": 80,
        "learning_score": 70
    }
}

v2_results = {
    "overall_score": 85.0,
    "summary": {
        "graph_growth_rate": 0.3,
        "avg_entropy": 0.7,
        "write_ratio": 0.3,
        "avg_processing_time_ms": 400,
        "stability_score": 90,
        "learning_score": 85
    }
}

comparison = Evaluator.compare_versions(v1_results, v2_results)

print(f"版本1评分: {comparison['v1_score']:.1f}")
print(f"版本2评分: {comparison['v2_score']:.1f}")
print(f"改进: {comparison['improvement']:.1f} ({comparison['improvement_percent']:.1f}%)")
print(f"结论: {comparison['verdict']}")

if comparison['improvements']:
    print("\n✅ 改进点:")
    for improvement in comparison['improvements'][:3]:
        print(f"  • {improvement}")

print("\n" + "="*60)
print("✅ 评估框架核心功能验证完成")
print("系统现在具备:")
print("  ✅ 可观测 - 完整指标收集")
print("  ✅ 可复现 - 标准化测试脚本")
print("  ✅ 可对比 - 版本对比系统")
print("="*60)
