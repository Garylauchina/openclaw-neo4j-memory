#!/usr/bin/env python3
"""
Action System集成测试
测试完整的行动系统：生成 → 执行 → 验证 → ARQS → 反馈
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from action_system.action_generator import ActionGenerator, Action, ActionType, ActionRiskLevel
from action_system.action_executor import ActionExecutor, ExecutionStatus
from action_system.action_validation import ActionValidator, ValidationResult
from action_system.arqs_system import ARQSSystem, ARQSEntry
from action_system.closed_loop_feedback import ClosedLoopFeedbackSystem, FeedbackEntry

def test_action_generation():
    """测试行动生成"""
    print("🧪 测试行动生成...")
    
    generator = ActionGenerator()
    
    # 测试从计划步骤生成行动
    plan_step = {
        "step_type": "data_retrieval",
        "description": "获取东京房产租金数据",
        "expected_outcome": "租金数据表格，包含区域、价格、空置率",
        "parameters": {
            "region": "东京",
            "data_type": "rental_prices",
            "timeframe": "2026"
        }
    }
    
    actions = generator.generate_from_plan_step(plan_step, "分析东京房产投资机会")
    
    print(f"  生成行动数: {len(actions)}")
    
    for i, action in enumerate(actions):
        print(f"  行动{i+1}: {action.action_type.value} - {action.target}")
        print(f"    预期结果: {action.expected_outcome}")
        print(f"    风险等级: {action.risk_level.value}")
        print(f"    需要确认: {action.requires_confirmation}")
        print(f"    真实影响: {action.real_world_impact}")
    
    return actions

def test_action_execution(actions):
    """测试行动执行"""
    print("\n🧪 测试行动执行...")
    
    executor = ActionExecutor()
    
    # 执行行动
    context = {"user_id": "test_user", "session_id": "test_session"}
    results = executor.execute_actions(actions, context)
    
    print(f"  执行结果数: {len(results)}")
    
    for i, result in enumerate(results):
        print(f"  结果{i+1}: {result.action_type.value}")
        print(f"    状态: {result.status.value}")
        print(f"    执行时间: {result.execution_time:.2f}秒")
        print(f"    错误: {result.error}")
        print(f"    重试次数: {result.retry_attempts}")
        print(f"    使用降级: {result.used_fallback}")
    
    return results

def test_action_validation(actions, execution_results):
    """测试行动验证"""
    print("\n🧪 测试行动验证...")
    
    validator = ActionValidator()
    
    validation_results = []
    for action, result in zip(actions, execution_results):
        validation = validator.validate_action(
            action, result, "分析东京房产投资机会", {"context": "test"}
        )
        validation_results.append(validation)
    
    print(f"  验证结果数: {len(validation_results)}")
    
    for i, validation in enumerate(validation_results):
        print(f"  验证{i+1}: {validation.action_type.value}")
        print(f"    验证分数: {validation.validation_score:.3f}")
        print(f"    是否有效: {validation.is_valid}")
        print(f"    验证通过: {validation.validation_passed}")
        print(f"    高风险因素: {validation.high_risk_factors}")
        print(f"    需要重规划: {validation.requires_replan}")
    
    return validation_results

def test_arqs_system(actions, execution_results, validation_results):
    """测试ARQS系统"""
    print("\n🧪 测试ARQS系统...")
    
    arqs_system = ARQSSystem()
    
    arqs_entries = []
    for i, (action, exec_result, validation) in enumerate(zip(actions, execution_results, validation_results)):
        # 模拟推理质量（来自RQS）
        reasoning_quality = 0.7 + (i * 0.05)  # 逐渐提高
        
        arqs_entry = arqs_system.update_arqs(
            action, exec_result, validation, reasoning_quality,
            "分析东京房产投资机会", {"context": "test"}
        )
        arqs_entries.append(arqs_entry)
    
    print(f"  ARQS条目数: {len(arqs_entries)}")
    
    for i, entry in enumerate(arqs_entries):
        print(f"  ARQS{i+1}: {entry.action_type.value}")
        print(f"    ARQS分数: {entry.arqs_score:.3f}")
        print(f"    推理质量: {entry.reasoning_quality:.3f}")
        print(f"    行动成功: {entry.action_success:.3f}")
        print(f"    长期结果: {entry.long_term_outcome:.3f}")
        print(f"    置信度: {entry.confidence:.3f}")
    
    # 获取ARQS报告
    arqs_report = arqs_system.get_arqs_report()
    print(f"\n  ARQS报告:")
    print(f"    当前ARQS: {arqs_report['current_state']['arqs_score']:.3f}")
    print(f"    ARQS趋势: {arqs_report['current_state']['arqs_trend']}")
    print(f"    平均ARQS: {arqs_system.stats['avg_arqs_score']:.3f}")
    
    return arqs_entries, arqs_system

def test_closed_loop_feedback(actions, execution_results, validation_results, arqs_entries):
    """测试闭环反馈系统"""
    print("\n🧪 测试闭环反馈系统...")
    
    feedback_system = ClosedLoopFeedbackSystem()
    
    feedback_entries = []
    for i, (action, exec_result, validation, arqs_entry) in enumerate(zip(
        actions, execution_results, validation_results, arqs_entries
    )):
        feedback_entry = feedback_system.process_feedback(
            action, exec_result, validation, arqs_entry,
            "分析东京房产投资机会",
            current_beliefs={"test_belief": 0.5},
            current_meta_learning={"learning_rate": 0.05},
            context={"test_context": True}
        )
        feedback_entries.append(feedback_entry)
    
    print(f"  反馈条目数: {len(feedback_entries)}")
    
    for i, entry in enumerate(feedback_entries):
        print(f"  反馈{i+1}: {entry.action_type.value}")
        print(f"    反馈分数: {entry.feedback_score:.3f}")
        print(f"    验证反馈: {entry.validation_feedback:.3f}")
        print(f"    执行反馈: {entry.execution_feedback:.3f}")
        print(f"    结果反馈: {entry.outcome_feedback:.3f}")
        print(f"    需要重规划: {entry.requires_replan}")
        print(f"    置信度: {entry.confidence:.3f}")
    
    # 获取反馈报告
    feedback_report = feedback_system.get_feedback_report()
    print(f"\n  反馈报告:")
    print(f"    信念强度: {feedback_system.system_state['belief_strength']:.3f}")
    print(f"    学习效率: {feedback_system.system_state['learning_efficiency']:.3f}")
    print(f"    适应速度: {feedback_system.system_state['adaptation_speed']:.3f}")
    print(f"    稳定性指数: {feedback_system.system_state['stability_index']:.3f}")
    print(f"    重规划频率: {feedback_system.system_state['replan_frequency']:.3f}")
    print(f"    反馈质量: {feedback_system.system_state['feedback_quality']:.3f}")
    
    return feedback_entries, feedback_system

def test_full_pipeline():
    """测试完整Pipeline"""
    print("=" * 60)
    print("🚀 测试完整Action System Pipeline")
    print("=" * 60)
    
    # 1. 行动生成
    actions = test_action_generation()
    
    # 2. 行动执行
    execution_results = test_action_execution(actions)
    
    # 3. 行动验证
    validation_results = test_action_validation(actions, execution_results)
    
    # 4. ARQS系统
    arqs_entries, arqs_system = test_arqs_system(actions, execution_results, validation_results)
    
    # 5. 闭环反馈
    feedback_entries, feedback_system = test_closed_loop_feedback(
        actions, execution_results, validation_results, arqs_entries
    )
    
    # 6. 系统状态汇总
    print("\n" + "=" * 60)
    print("📊 Action System完整状态汇总")
    print("=" * 60)
    
    # 计算成功率
    successful_executions = sum(1 for r in execution_results if r.status == ExecutionStatus.COMPLETED)
    execution_success_rate = successful_executions / len(execution_results) if execution_results else 0.0
    
    successful_validations = sum(1 for v in validation_results if v.validation_passed)
    validation_success_rate = successful_validations / len(validation_results) if validation_results else 0.0
    
    high_arqs = sum(1 for a in arqs_entries if a.arqs_score > 0.6)
    arqs_success_rate = high_arqs / len(arqs_entries) if arqs_entries else 0.0
    
    replan_count = sum(1 for f in feedback_entries if f.requires_replan)
    replan_rate = replan_count / len(feedback_entries) if feedback_entries else 0.0
    
    print(f"  执行成功率: {execution_success_rate:.1%} ({successful_executions}/{len(execution_results)})")
    print(f"  验证成功率: {validation_success_rate:.1%} ({successful_validations}/{len(validation_results)})")
    print(f"  ARQS成功率: {arqs_success_rate:.1%} ({high_arqs}/{len(arqs_entries)})")
    print(f"  重规划率: {replan_rate:.1%} ({replan_count}/{len(feedback_entries)})")
    
    # 平均分数
    avg_validation_score = sum(v.validation_score for v in validation_results) / len(validation_results) if validation_results else 0.0
    avg_arqs_score = sum(a.arqs_score for a in arqs_entries) / len(arqs_entries) if arqs_entries else 0.0
    avg_feedback_score = sum(f.feedback_score for f in feedback_entries) / len(feedback_entries) if feedback_entries else 0.0
    
    print(f"  平均验证分数: {avg_validation_score:.3f}")
    print(f"  平均ARQS分数: {avg_arqs_score:.3f}")
    print(f"  平均反馈分数: {avg_feedback_score:.3f}")
    
    # 系统状态
    print(f"\n  系统状态:")
    print(f"    当前ARQS: {arqs_system.current_arqs:.3f}")
    print(f"    ARQS趋势: {arqs_system.arqs_trend}")
    print(f"    信念强度: {feedback_system.system_state['belief_strength']:.3f}")
    print(f"    学习效率: {feedback_system.system_state['learning_efficiency']:.3f}")
    print(f"    适应速度: {feedback_system.system_state['adaptation_speed']:.3f}")
    
    # 建议
    print(f"\n  系统建议:")
    arqs_recommendations = arqs_system.get_arqs_report().get('recommendations', [])
    feedback_recommendations = feedback_system.get_feedback_report().get('recommendations', [])
    
    all_recommendations = arqs_recommendations[:2] + feedback_recommendations[:2]
    for rec in all_recommendations[:3]:
        print(f"    • {rec}")
    
    # 最终评估
    print("\n" + "=" * 60)
    print("🎯 Action System最终评估")
    print("=" * 60)
    
    # 计算系统健康分数
    system_health = (
        execution_success_rate * 0.2 +
        validation_success_rate * 0.3 +
        arqs_success_rate * 0.3 +
        (1 - replan_rate) * 0.2
    )
    
    print(f"  系统健康分数: {system_health:.3f}")
    
    if system_health > 0.7:
        print("  ✅ 系统状态: 优秀 - Action System运行良好")
    elif system_health > 0.5:
        print("  ⚠️  系统状态: 良好 - 有改进空间")
    else:
        print("  ❌ 系统状态: 需要改进 - 系统性能不足")
    
    # 检查关键指标
    critical_issues = []
    
    if execution_success_rate < 0.6:
        critical_issues.append("执行成功率过低")
    
    if validation_success_rate < 0.6:
        critical_issues.append("验证成功率过低")
    
    if arqs_system.current_arqs < 0.5:
        critical_issues.append("ARQS分数过低")
    
    if replan_rate > 0.3:
        critical_issues.append("重规划率过高")
    
    if critical_issues:
        print(f"\n  ⚠️  关键问题:")
        for issue in critical_issues:
            print(f"    • {issue}")
    else:
        print(f"\n  ✅ 无关键问题 - 系统运行稳定")
    
    print("\n" + "=" * 60)
    print("✅ Action System集成测试完成")
    print("=" * 60)
    
    return system_health > 0.6

def test_action_system_components():
    """测试Action System各组件"""
    print("\n" + "=" * 60)
    print("🔧 测试Action System各组件状态")
    print("=" * 60)
    
    # 测试各组件
    components = [
        ("Action Generator", ActionGenerator()),
        ("Action Executor", ActionExecutor()),
        ("Action Validator", ActionValidator()),
        ("ARQS System", ARQSSystem()),
        ("Closed Loop Feedback", ClosedLoopFeedbackSystem())
    ]
    
    for name, component in components:
        print(f"\n  {name}:")
        try:
            component.print_status()
            print(f"    ✅ 状态正常")
        except Exception as e:
            print(f"    ❌ 状态异常: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 组件状态测试完成")
    print("=" * 60)

if __name__ == "__main__":
    print("🚀 开始Action System集成测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 测试各组件状态
        test_action_system_components()
        
        # 测试完整Pipeline
        success = test_full_pipeline()
        
        if success:
            print("\n🎉 Action System集成测试通过！")
            print("系统已成功从'决策系统'升级为'行动系统'")
            print("✅ 具备完整闭环：生成 → 执行 → 验证 → ARQS → 反馈")
        else:
            print("\n⚠️  Action System集成测试部分失败")
            print("系统需要进一步优化")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Action System集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)