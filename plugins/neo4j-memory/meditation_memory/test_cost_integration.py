#!/usr/bin/env python3
"""
Issue #41: 冥思流水线成本监控集成单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 使用绝对导入
import importlib
meditation_cost_config = importlib.import_module("meditation_cost_config")
meditation_cost_monitor = importlib.import_module("meditation_cost_monitor")

MeditationCostConfig = meditation_cost_config.MeditationCostConfig
BudgetStatus = meditation_cost_config.BudgetStatus
MeditationCostMonitor = meditation_cost_monitor.MeditationCostMonitor


def test_cost_monitor_initialization():
    """测试 1：成本监控器初始化"""
    print("🔍 测试 1: 成本监控器初始化")
    print("-" * 60)
    
    config = MeditationCostConfig()
    monitor = MeditationCostMonitor(config)
    
    assert monitor.cost_config == config, "成本配置应正确设置"
    assert monitor.budget_status.budget_status == "within_limit", "初始状态应为 within_limit"
    assert monitor.budget_status.total_cost == 0.0, "初始成本应为 0"
    assert monitor.budget_status.llm_calls == 0, "初始调用次数应为 0"
    
    print(f"  ✅ cost_config: {config.max_meditation_budget_per_run}")
    print(f"  ✅ budget_status: {monitor.budget_status.budget_status}")
    print(f"  ✅ step_costs: {monitor.step_costs}")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_cost_monitor_add_cost():
    """测试 2: 成本添加和预算检查"""
    print("🔍 测试 2: 成本添加和预算检查")
    print("-" * 60)
    
    config = MeditationCostConfig()
    monitor = MeditationCostMonitor(config)
    monitor.start_meditation()
    
    # 添加 Step 2 成本（20% 预算）
    monitor.add_cost(2, 0.02, llm_calls=10, nodes_processed=100)
    assert monitor.budget_status.total_cost == 0.02, "总成本应为 0.02"
    assert monitor.budget_status.llm_calls == 10, "LLM 调用次数应为 10"
    assert monitor.step_costs[2] == 0.02, "Step 2 成本应为 0.02"
    
    # 检查预算状态（20% < 80%，应为 within_limit）
    status = monitor.check_budget()
    assert status == "within_limit", f"20% 预算应为 within_limit，实际为 {status}"
    
    # 继续添加成本到 85%
    monitor.add_cost(3, 0.065, llm_calls=20, nodes_processed=200)
    status = monitor.check_budget()
    assert status == "warning", f"85% 预算应为 warning，实际为 {status}"
    
    # 继续添加成本到 95%
    monitor.add_cost(4, 0.01, llm_calls=5, nodes_processed=50)
    status = monitor.check_budget()
    assert status == "critical", f"95% 预算应为 critical，实际为 {status}"
    
    # 继续添加成本到 105%
    monitor.add_cost(5, 0.01, llm_calls=5, nodes_processed=50)
    status = monitor.check_budget()
    assert status == "exceeded", f"105% 预算应为 exceeded，实际为 {status}"
    
    print(f"  ✅ 20% 预算：within_limit")
    print(f"  ✅ 85% 预算：warning")
    print(f"  ✅ 95% 预算：critical")
    print(f"  ✅ 105% 预算：exceeded")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_should_skip_step():
    """测试 3: 跳过步骤逻辑"""
    print("🔍 测试 3: 跳过步骤逻辑")
    print("-" * 60)
    
    config = MeditationCostConfig()
    monitor = MeditationCostMonitor(config)
    monitor.start_meditation()
    
    # within_limit: 不应跳过任何步骤
    assert monitor.should_skip_step(2) == False, "within_limit 不应跳过 Step 2"
    assert monitor.should_skip_step(5) == False, "within_limit 不应跳过 Step 5"
    
    # 添加成本到 critical (95%)
    monitor.add_cost(2, 0.095, llm_calls=30, nodes_processed=300)
    monitor.check_budget()
    
    # critical: 应跳过 Step 5（非关键步骤）
    assert monitor.should_skip_step(2) == False, "critical 不应跳过 Step 2"
    assert monitor.should_skip_step(5) == True, "critical 应跳过 Step 5（非关键）"
    
    # 添加成本到 exceeded (105%)
    monitor.add_cost(3, 0.01, llm_calls=5, nodes_processed=50)
    monitor.check_budget()
    
    # exceeded: 应跳过所有步骤
    assert monitor.should_skip_step(4) == True, "exceeded 应跳过 Step 4"
    assert monitor.should_skip_step(5) == True, "exceeded 应跳过 Step 5"
    assert monitor.should_skip_step(6) == True, "exceeded 应跳过 Step 6"
    
    print(f"  ✅ within_limit: 不跳过任何步骤")
    print(f"  ✅ critical: 跳过 Step 5（非关键）")
    print(f"  ✅ exceeded: 跳过所有步骤")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_should_simplify_step():
    """测试 4: 简化步骤逻辑"""
    print("🔍 测试 4: 简化步骤逻辑")
    print("-" * 60)
    
    config = MeditationCostConfig()
    monitor = MeditationCostMonitor(config)
    monitor.start_meditation()
    
    # within_limit: 不应简化
    assert monitor.should_simplify_step(2) == False, "within_limit 不应简化"
    
    # 添加成本到 warning (85%)
    monitor.add_cost(2, 0.085, llm_calls=30, nodes_processed=300)
    monitor.check_budget()
    
    # warning: 应简化后续步骤
    assert monitor.should_simplify_step(3) == True, "warning 应简化 Step 3"
    assert monitor.should_simplify_step(4) == True, "warning 应简化 Step 4"
    
    print(f"  ✅ within_limit: 不简化")
    print(f"  ✅ warning: 简化后续步骤")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_cost_report():
    """测试 5: 成本报告生成"""
    print("🔍 测试 5: 成本报告生成")
    print("-" * 60)
    
    config = MeditationCostConfig()
    monitor = MeditationCostMonitor(config)
    monitor.start_meditation()
    
    # 模拟完整冥思过程（总成本 0.094，占 94%，应为 critical）
    monitor.add_cost(2, 0.02, llm_calls=10, nodes_processed=100)
    monitor.add_cost(3, 0.02, llm_calls=10, nodes_processed=150)
    monitor.add_cost(4, 0.03, llm_calls=15, nodes_processed=200)
    monitor.add_cost(5, 0.016, llm_calls=8, nodes_processed=100)
    monitor.add_cost(6, 0.008, llm_calls=4, nodes_processed=50)
    
    monitor.end_meditation()
    
    report = monitor.get_cost_report()
    
    # 验证报告结构
    assert "total_cost" in report, "报告应包含 total_cost"
    assert "llm_calls" in report, "报告应包含 llm_calls"
    assert "nodes_processed" in report, "报告应包含 nodes_processed"
    assert "cost_per_node" in report, "报告应包含 cost_per_node"
    assert "budget_status" in report, "报告应包含 budget_status"
    assert "step_costs" in report, "报告应包含 step_costs"
    assert "duration_seconds" in report, "报告应包含 duration_seconds"
    
    # 验证数值
    assert abs(report["total_cost"] - 0.094) < 0.001, f"总成本应为 0.094，实际为 {report['total_cost']}"
    assert report["llm_calls"] == 47, f"LLM 调用次数应为 47，实际为 {report['llm_calls']}"
    assert report["nodes_processed"] == 600, f"处理节点数应为 600，实际为 {report['nodes_processed']}"
    assert report["budget_status"] == "critical", f"预算状态应为 critical（94%），实际为 {report['budget_status']}"
    
    # 验证步骤成本
    assert abs(report["step_costs"][2] - 0.02) < 0.001, "Step 2 成本应为 0.02"
    assert abs(report["step_costs"][3] - 0.02) < 0.001, "Step 3 成本应为 0.02"
    assert abs(report["step_costs"][4] - 0.03) < 0.001, "Step 4 成本应为 0.03"
    assert abs(report["step_costs"][5] - 0.016) < 0.001, "Step 5 成本应为 0.016"
    assert abs(report["step_costs"][6] - 0.008) < 0.001, "Step 6 成本应为 0.008"
    
    print(f"  ✅ total_cost: ${report['total_cost']:.4f}")
    print(f"  ✅ llm_calls: {report['llm_calls']}")
    print(f"  ✅ nodes_processed: {report['nodes_processed']}")
    print(f"  ✅ cost_per_node: ${report['cost_per_node']:.6f}")
    print(f"  ✅ budget_status: {report['budget_status']}")
    print(f"  ✅ step_costs: {report['step_costs']}")
    print(f"  ✅ 测试通过")
    print()
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("Issue #41: 冥思流水线成本监控集成单元测试")
    print("=" * 70)
    print()
    
    tests = [
        ("成本监控器初始化", test_cost_monitor_initialization),
        ("成本添加和预算检查", test_cost_monitor_add_cost),
        ("跳过步骤逻辑", test_should_skip_step),
        ("简化步骤逻辑", test_should_simplify_step),
        ("成本报告生成", test_cost_report)
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
