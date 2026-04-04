#!/usr/bin/env python3
"""
Action System 集成测试
测试完整的行动系统：生成 → 执行 → 验证 → ARQS → 闭环反馈
"""

import sys
import time
from datetime import datetime

# 导入Action System模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 现在导入模块
try:
    from action_generator import ActionGenerator, Action, ActionType, ActionRiskLevel
    from action_executor import ActionExecutor, ExecutionStatus
    from action_validation import ActionValidator, ValidationResult
    from arqs_system import ARQSSystem, ARQSEntry
    from closed_loop_feedback import ClosedLoopFeedbackSystem, FeedbackEntry
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("正在尝试直接导入...")
    
    # 直接导入
    exec(open("action_generator.py").read())
    exec(open("action_executor.py").read())
    exec(open("action_validation.py").read())
    exec(open("arqs_system.py").read())
    exec(open("closed_loop_feedback.py").read())

def test_basic_action_flow():
    """测试基本行动流程"""
    print("🧪 测试基本行动流程...")
    
    # 1. 创建行动生成器
    generator = ActionGenerator()
    
    # 2. 从计划步骤生成行动
    plan_step = {
        "description": "获取天气数据用于旅行规划",
        "goal": "规划周末旅行",
        "constraints": ["需要实时数据", "需要未来3天预报"],
        "resources": ["天气API", "位置数据"]
    }
    
    actions = generator.generate_actions_from_plan(plan_step, max_actions=2)
    print(f"   ✅ 生成 {len(actions)} 个行动")
    
    for i, action in enumerate(actions):
        print(f"     行动 {i+1}: {action.action_type.value} - {action.target}")
    
    return actions

def test_action_execution(actions):
    """测试行动执行"""
    print("\n🧪 测试行动执行...")
    
    # 1. 创建执行器
    executor = ActionExecutor()
    
    # 2. 执行行动
    context = {"location": "北京", "timeframe": "3天"}
    results = executor.execute_actions(actions, context)
    
    print(f"   ✅ 执行 {len(results)} 个行动结果")
    
    for i, result in enumerate(results):
        status_emoji = "✅" if result.status == ExecutionStatus.COMPLETED else "❌"
        print(f"     结果 {i+1}: {status_emoji} {result.status.value} - {result.execution_time:.2f}秒")
        if result.error:
            print(f"         错误: {result.error}")
    
    return results

def test_action_validation(actions, execution_results):
    """测试行动验证"""
    print("\n🧪 测试行动验证...")
    
    # 1. 创建验证器
    validator = ActionValidator()
    
    # 2. 验证每个行动
    goal_description = "规划周末旅行，需要准确的天气数据"
    validation_results = []
    
    for action, exec_result in zip(actions, execution_results):
        validation_result = validator.validate_action(
            action, exec_result, goal_description
        )
        validation_results.append(validation_result)
        
        status_emoji = "✅" if validation_result.validation_passed else "❌"
        print(f"     验证 {action.action_type.value}: {status_emoji} 分数={validation_result.validation_score:.3f}")
        if validation_result.high_risk_factors:
            print(f"         高风险因素: {validation_result.high_risk_factors}")
    
    return validation_results

def test_arqs_system(actions, execution_results, validation_results):
    """测试ARQS系统"""
    print("\n🧪 测试ARQS系统...")
    
    # 1. 创建ARQS系统
    arqs_system = ARQSSystem()
    
    # 2. 更新ARQS
    goal_description = "规划周末旅行"
    arqs_entries = []
    
    for i, (action, exec_result, validation_result) in enumerate(zip(actions, execution_results, validation_results)):
        # 模拟推理质量（来自RQS）
        reasoning_quality = 0.7 + (i * 0.05)  # 递增
        
        arqs_entry = arqs_system.update_arqs(
            action, exec_result, validation_result,
            reasoning_quality, goal_description
        )
        arqs_entries.append(arqs_entry)
        
        print(f"     ARQS {action.action_type.value}: 分数={arqs_entry.arqs_score:.3f}, 置信度={arqs_entry.confidence:.3f}")
    
    # 3. 获取ARQS报告
    arqs_report = arqs_system.get_arqs_report()
    print(f"   📊 当前ARQS: {arqs_report['current_state']['arqs_score']:.3f}")
    print(f"   📈 ARQS趋势: {arqs_report['current_state']['arqs_trend']}")
    
    return arqs_system, arqs_entries

def test_closed_loop_feedback(actions, execution_results, validation_results, arqs_entries):
    """测试闭环反馈"""
    print("\n🧪 测试闭环反馈...")
    
    # 1. 创建闭环反馈系统
    feedback_system = ClosedLoopFeedbackSystem()
    
    # 2. 处理反馈
    feedback_entries = []
    
    for i, (action, exec_result, validation_result, arqs_entry) in enumerate(zip(actions, execution_results, validation_results, arqs_entries)):
        feedback_entry = feedback_system.process_feedback(
            action, exec_result, validation_result, arqs_entry,
            feedback_type="immediate"
        )
        feedback_entries.append(feedback_entry)
        
        status_emoji = "🔄" if feedback_entry.requires_replan else "✅"
        print(f"     反馈 {action.action_type.value}: {status_emoji} 分数={feedback_entry.overall_feedback:.3f}")
        if feedback_entry.requires_replan:
            print(f"         需要重规划: {feedback_entry.replan_reason}")
    
    # 3. 获取反馈报告
    feedback_report = feedback_system.get_feedback_report()
    print(f"   📊 当前反馈分数: {feedback_report['current_state']['feedback_score']:.3f}")
    print(f"   🛡️  系统稳定性: {feedback_report['current_state']['system_stability']:.3f}")
    
    return feedback_system, feedback_entries

def test_complete_workflow():
    """测试完整工作流"""
    print("=" * 60)
    print("🚀 测试完整Action System工作流")
    print("=" * 60)
    
    try:
        # 1. 生成行动
        actions = test_basic_action_flow()
        
        # 2. 执行行动
        execution_results = test_action_execution(actions)
        
        # 3. 验证行动
        validation_results = test_action_validation(actions, execution_results)
        
        # 4. ARQS系统
        arqs_system, arqs_entries = test_arqs_system(actions, execution_results, validation_results)
        
        # 5. 闭环反馈
        feedback_system, feedback_entries = test_closed_loop_feedback(
            actions, execution_results, validation_results, arqs_entries
        )
        
        # 6. 打印最终状态
        print("\n" + "=" * 60)
        print("📊 最终系统状态")
        print("=" * 60)
        
        # Action Generator状态
        print("\n🎯 Action Generator:")
        generator_stats = ActionGenerator().get_stats()
        print(f"   总生成行动数: {generator_stats['stats']['total_actions_generated']}")
        print(f"   实验行动比例: {generator_stats['stats']['experiment_ratio']:.1%}")
        
        # Action Executor状态
        print("\n⚡ Action Executor:")
        executor = ActionExecutor()
        executor_stats = executor.get_stats()
        print(f"   总执行行动数: {executor_stats['stats']['total_actions_executed']}")
        print(f"   成功率: {executor_stats['stats']['success_rate']:.1%}")
        print(f"   平均执行时间: {executor_stats['stats']['avg_execution_time']:.2f}秒")
        
        # Action Validator状态
        print("\n🔍 Action Validator:")
        validator = ActionValidator()
        validator_stats = validator.get_stats()
        print(f"   总验证次数: {validator_stats['performance']['total_validations']}")
        print(f"   通过率: {validator_stats['performance']['pass_rate']:.1%}")
        print(f"   高风险验证: {validator_stats['performance']['high_risk_rate']:.1%}")
        
        # ARQS系统状态
        print("\n📈 ARQS系统:")
        arqs_report = arqs_system.get_arqs_report()
        print(f"   当前ARQS: {arqs_report['current_state']['arqs_score']:.3f}")
        print(f"   ARQS置信度: {arqs_report['current_state']['arqs_confidence']:.3f}")
        print(f"   ARQS趋势: {arqs_report['current_state']['arqs_trend']}")
        
        # 闭环反馈系统状态
        print("\n🔄 闭环反馈系统:")
        feedback_report = feedback_system.get_feedback_report()
        print(f"   当前反馈分数: {feedback_report['current_state']['feedback_score']:.3f}")
        print(f"   系统稳定性: {feedback_report['current_state']['system_stability']:.3f}")
        print(f"   重规划次数: {feedback_report['current_state']['replan_count']}")
        
        # 系统整体评估
        print("\n🎯 系统整体评估:")
        
        # 计算整体分数
        overall_score = (
            arqs_report['current_state']['arqs_score'] * 0.4 +
            feedback_report['current_state']['feedback_score'] * 0.3 +
            validator_stats['performance']['pass_rate'] * 0.2 +
            executor_stats['stats']['success_rate'] * 0.1
        )
        
        if overall_score > 0.8:
            assessment = "✅ 优秀 - 系统运行良好"
        elif overall_score > 0.6:
            assessment = "🟡 良好 - 系统运行正常"
        elif overall_score > 0.4:
            assessment = "🟠 中等 - 需要优化"
        else:
            assessment = "🔴 较差 - 需要重大改进"
        
        print(f"   整体分数: {overall_score:.3f} - {assessment}")
        
        # 关键指标
        print(f"   关键指标:")
        print(f"     • 行动成功率: {executor_stats['stats']['success_rate']:.1%}")
        print(f"     • 验证通过率: {validator_stats['performance']['pass_rate']:.1%}")
        print(f"     • ARQS分数: {arqs_report['current_state']['arqs_score']:.3f}")
        print(f"     • 系统稳定性: {feedback_report['current_state']['system_stability']:.3f}")
        
        # 建议
        print(f"\n💡 建议:")
        feedback_recommendations = feedback_report.get('recommendations', [])
        if feedback_recommendations:
            for rec in feedback_recommendations[:2]:
                print(f"     • {rec}")
        else:
            print(f"     • 系统运行正常，继续保持")
        
        print("\n" + "=" * 60)
        print("✅ Action System测试完成!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_experiment_actions():
    """测试实验行动"""
    print("\n" + "=" * 60)
    print("🔬 测试实验行动")
    print("=" * 60)
    
    try:
        # 创建实验行动
        generator = ActionGenerator()
        
        experiment_action = generator.create_experiment_action(
            hypothesis="使用新的数据源可以提高天气预测准确率",
            action_type=ActionType.API_CALL,
            target="weather-api-v2",
            parameters={"api_version": "v2", "forecast_days": 3},
            expected_outcome="预测准确率提高10%",
            risk_level=ActionRiskLevel.MEDIUM
        )
        
        print(f"   🔬 实验行动:")
        print(f"     假设: {experiment_action.hypothesis}")
        print(f"     预期结果: {experiment_action.expected_outcome}")
        print(f"     风险等级: {experiment_action.risk_level.value}")
        print(f"     需要确认: {experiment_action.requires_confirmation}")
        
        # 执行实验行动
        executor = ActionExecutor()
        exec_result = executor.execute_action(experiment_action, {})
        
        print(f"\n   ⚡ 执行结果:")
        print(f"     状态: {exec_result.status.value}")
        print(f"     执行时间: {exec_result.execution_time:.2f}秒")
        
        if exec_result.result and "experiment_data" in exec_result.result:
            exp_data = exec_result.result["experiment_data"]
            print(f"     实验数据:")
            print(f"       假设检验结果: {exp_data.get('hypothesis_test_result', 'N/A')}")
            print(f"       实际结果: {exp_data.get('actual_outcome', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 实验行动测试失败: {e}")
        return False

def test_high_risk_actions():
    """测试高风险行动"""
    print("\n" + "=" * 60)
    print("⚠️ 测试高风险行动")
    print("=" * 60)
    
    try:
        generator = ActionGenerator()
        
        # 创建高风险行动
        high_risk_action = Action(
            id="high_risk_001",
            action_type=ActionType.EXECUTION,
            target="system-reboot",
            parameters={"force": True, "delay_seconds": 10},
            expected_outcome="系统重启成功",
            risk_level=ActionRiskLevel.CRITICAL,
            requires_confirmation=True,
            real_world_impact=True,
            fallback_action=None,
            is_experiment=False,
            hypothesis=None
        )
        
        print(f"   ⚠️ 高风险行动:")
        print(f"     类型: {high_risk_action.action_type.value}")
        print(f"     目标: {high_risk_action.target}")
        print(f"     风险等级: {high_risk_action.risk_level.value}")
        print(f"     需要确认: {high_risk_action.requires_confirmation}")
        print(f"     真实世界影响: {high_risk_action.real_world_impact}")
        
        # 验证高风险行动
        validator = ActionValidator()
        
        # 模拟执行结果
        mock_exec_result = type('obj', (object,), {
            'status': ExecutionStatus.COMPLETED,
            'execution_time': 15.5,
            'result': {"reboot_status": "success", "downtime_seconds": 12},
            'error': None,
            'retry_attempts': 0,
            'used_fallback': False,
            'performance_metrics': {"success": True}
        })()
        
        validation_result = validator.validate_action(
            high_risk_action, mock_exec_result, "系统维护"
        )
        
        print(f"\n   🔍 验证结果:")
        print(f"     验证分数: {validation_result.validation_score:.3f}")
        print(f"     高风险因素: {validation_result.high_risk_factors}")
        print(f"     建议: {validation_result.recommendations}")
        
        return True
        
    except Exception as e:
        print(f"❌ 高风险行动测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始Action System集成测试")
    print("=" * 60)
    
    # 记录开始时间
    start_time = time.time()
    
    # 运行测试
    tests_passed = 0
    tests_total = 0
    
    # 测试1: 完整工作流
    tests_total += 1
    if test_complete_workflow():
        tests_passed += 1
    
    # 测试2: 实验行动
    tests_total += 1
    if test_experiment_actions():
        tests_passed += 1
    
    # 测试3: 高风险行动
    tests_total += 1
    if test_high_risk_actions():
        tests_passed += 1
    
    # 计算测试时间
    elapsed_time = time.time() - start_time
    
    # 打印测试总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"   总测试数: {tests_total}")
    print(f"   通过测试: {tests_passed}")
    print(f"   失败测试: {tests_total - tests_passed}")
    print(f"   通过率: {tests_passed/tests_total:.1%}")
    print(f"   总耗时: {elapsed_time:.2f}秒")
    
    if tests_passed == tests_total:
        print("\n✅ 所有测试通过! Action System运行正常。")
        return 0
    else:
        print(f"\n⚠️  {tests_total - tests_passed} 个测试失败，需要检查。")
        return 1

if __name__ == "__main__":
    sys.exit(main())