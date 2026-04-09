#!/usr/bin/env python3
"""
Issue #37: 冥思成本保护配置单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meditation_cost_config import MeditationCostConfig, BudgetStatus


def test_cost_config_defaults():
    """测试 1：成本配置默认值"""
    print("🔍 测试 1: 成本配置默认值")
    print("-" * 60)
    
    config = MeditationCostConfig()
    
    # 验证默认值
    assert config.max_meditation_budget_per_run == 0.10, "默认单次预算应为 0.10"
    assert config.max_llm_calls_per_run == 50, "默认 LLM 调用次数应为 50"
    assert config.warning_threshold_ratio == 0.80, "默认警告阈值应为 80%"
    assert config.skip_non_critical_threshold_ratio == 0.90, "默认跳过阈值应为 90%"
    assert config.emergency_stop_threshold_ratio == 1.00, "默认紧急停止阈值应为 100%"
    
    print(f"  ✅ max_meditation_budget_per_run: ${config.max_meditation_budget_per_run}")
    print(f"  ✅ max_llm_calls_per_run: {config.max_llm_calls_per_run}")
    print(f"  ✅ warning_threshold_ratio: {config.warning_threshold_ratio * 100}%")
    print(f"  ✅ skip_non_critical_threshold_ratio: {config.skip_non_critical_threshold_ratio * 100}%")
    print(f"  ✅ emergency_stop_threshold_ratio: {config.emergency_stop_threshold_ratio * 100}%")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_budget_ratios():
    """测试 2：预算分配比例验证"""
    print("🔍 测试 2: 预算分配比例验证")
    print("-" * 60)
    
    config = MeditationCostConfig()
    
    # 验证比例总和为 1.0
    assert config.validate_budget_ratios(), "预算分配比例总和应为 1.0"
    
    total = (
        config.step2_pruning_budget_ratio +
        config.step3_merging_budget_ratio +
        config.step4_relabeling_budget_ratio +
        config.step5_distillation_budget_ratio +
        config.step6_strategy_budget_ratio
    )
    
    print(f"  ✅ Step 2 (噪声过滤): {config.step2_pruning_budget_ratio * 100}%")
    print(f"  ✅ Step 3 (实体合并): {config.step3_merging_budget_ratio * 100}%")
    print(f"  ✅ Step 4 (关系重标注): {config.step4_relabeling_budget_ratio * 100}%")
    print(f"  ✅ Step 5 (元知识蒸馏): {config.step5_distillation_budget_ratio * 100}%")
    print(f"  ✅ Step 6 (策略蒸馏): {config.step6_strategy_budget_ratio * 100}%")
    print(f"  ✅ 总计：{total * 100}%")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_step_budget_allocation():
    """测试 3：步骤预算分配"""
    print("🔍 测试 3: 步骤预算分配")
    print("-" * 60)
    
    config = MeditationCostConfig()
    total_budget = 0.10  # $0.10
    
    # 验证每个步骤的预算分配
    step2_budget = config.get_step_budget(2, total_budget)
    step3_budget = config.get_step_budget(3, total_budget)
    step4_budget = config.get_step_budget(4, total_budget)
    step5_budget = config.get_step_budget(5, total_budget)
    step6_budget = config.get_step_budget(6, total_budget)
    
    assert abs(step2_budget - 0.02) < 0.001, "Step 2 应为 $0.02 (20%)"
    assert abs(step3_budget - 0.02) < 0.001, "Step 3 应为 $0.02 (20%)"
    assert abs(step4_budget - 0.03) < 0.001, "Step 4 应为 $0.03 (30%)"
    assert abs(step5_budget - 0.02) < 0.001, "Step 5 应为 $0.02 (20%)"
    assert abs(step6_budget - 0.01) < 0.001, "Step 6 应为 $0.01 (10%)"
    
    print(f"  ✅ Step 2: ${step2_budget:.4f}")
    print(f"  ✅ Step 3: ${step3_budget:.4f}")
    print(f"  ✅ Step 4: ${step4_budget:.4f}")
    print(f"  ✅ Step 5: ${step5_budget:.4f}")
    print(f"  ✅ Step 6: ${step6_budget:.4f}")
    print(f"  ✅ 总计：${step2_budget + step3_budget + step4_budget + step5_budget + step6_budget:.4f}")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_budget_status():
    """测试 4：预算状态跟踪"""
    print("🔍 测试 4: 预算状态跟踪")
    print("-" * 60)
    
    config = MeditationCostConfig()
    status = BudgetStatus()
    
    # 初始状态
    assert status.budget_status == "within_limit", "初始状态应为 within_limit"
    assert status.total_cost == 0.0, "初始成本应为 0"
    assert status.llm_calls == 0, "初始调用次数应为 0"
    
    # 添加成本
    status.add_cost(0.05, 10)
    assert status.total_cost == 0.05, "成本应为 0.05"
    assert status.llm_calls == 10, "调用次数应为 10"
    
    # 检查预算状态（50% 预算）
    budget_status = status.check_budget(config)
    assert budget_status == "within_limit", "50% 预算应为 within_limit"
    
    # 继续添加成本到 85%
    status.add_cost(0.035, 15)
    budget_status = status.check_budget(config)
    assert budget_status == "warning", "85% 预算应为 warning"
    
    # 继续添加成本到 95%
    status.add_cost(0.01, 5)
    budget_status = status.check_budget(config)
    assert budget_status == "critical", "95% 预算应为 critical"
    
    # 继续添加成本到 100%
    status.add_cost(0.005, 5)
    budget_status = status.check_budget(config)
    assert budget_status == "exceeded", "100% 预算应为 exceeded"
    
    print(f"  ✅ 初始状态：{status.budget_status}")
    print(f"  ✅ 50% 预算：within_limit")
    print(f"  ✅ 85% 预算：warning")
    print(f"  ✅ 95% 预算：critical")
    print(f"  ✅ 100% 预算：exceeded")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_budget_status_to_dict():
    """测试 5：预算状态序列化"""
    print("🔍 测试 5: 预算状态序列化")
    print("-" * 60)
    
    status = BudgetStatus()
    status.add_cost(0.08, 35)
    status.nodes_processed = 600
    status.start_time = "2026-04-09T04:00:00Z"
    status.end_time = "2026-04-09T04:05:24Z"
    
    result = status.to_dict()
    
    assert "total_cost" in result, "应包含 total_cost"
    assert "llm_calls" in result, "应包含 llm_calls"
    assert "nodes_processed" in result, "应包含 nodes_processed"
    assert "cost_per_node" in result, "应包含 cost_per_node"
    assert "budget_status" in result, "应包含 budget_status"
    
    # 验证计算
    assert abs(result["total_cost"] - 0.08) < 0.001, "总成本应为 0.08"
    assert result["llm_calls"] == 35, "LLM 调用次数应为 35"
    assert result["nodes_processed"] == 600, "处理节点数应为 600"
    assert abs(result["cost_per_node"] - 0.000133) < 0.000001, "单位成本应约为 0.000133"
    
    print(f"  ✅ total_cost: ${result['total_cost']:.4f}")
    print(f"  ✅ llm_calls: {result['llm_calls']}")
    print(f"  ✅ nodes_processed: {result['nodes_processed']}")
    print(f"  ✅ cost_per_node: ${result['cost_per_node']:.6f}")
    print(f"  ✅ budget_status: {result['budget_status']}")
    print(f"  ✅ 测试通过")
    print()
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("Issue #37: 冥思成本保护配置单元测试")
    print("=" * 70)
    print()
    
    tests = [
        ("成本配置默认值", test_cost_config_defaults),
        ("预算分配比例验证", test_budget_ratios),
        ("步骤预算分配", test_step_budget_allocation),
        ("预算状态跟踪", test_budget_status),
        ("预算状态序列化", test_budget_status_to_dict)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ❌ 测试失败：{e}")
            print()
    
    # 总结
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for name, result, error in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
        if error:
            print(f"       错误：{error}")
    
    print()
    print(f"总计：{passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
