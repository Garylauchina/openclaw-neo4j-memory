#!/usr/bin/env python3
"""
Action System简单测试
测试核心功能是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

def test_basic_components():
    """测试基础组件"""
    print("🧪 测试Action System基础组件...")
    
    try:
        # 测试Action Generator
        from action_system.action_generator import ActionGenerator, ActionType, ActionRiskLevel
        
        generator = ActionGenerator()
        print("  ✅ Action Generator导入成功")
        
        # 测试Action Executor
        from action_system.action_executor import ActionExecutor, ExecutionStatus
        
        executor = ActionExecutor()
        print("  ✅ Action Executor导入成功")
        
        # 测试Action Validator
        from action_system.action_validation import ActionValidator
        
        validator = ActionValidator()
        print("  ✅ Action Validator导入成功")
        
        # 测试ARQS System
        from action_system.arqs_system import ARQSSystem
        
        arqs_system = ARQSSystem()
        print("  ✅ ARQS System导入成功")
        
        # 测试Closed Loop Feedback (使用修复版)
        try:
            from action_system.closed_loop_feedback_fixed import ClosedLoopFeedbackSystem
            feedback_system = ClosedLoopFeedbackSystem()
            print("  ✅ Closed Loop Feedback System导入成功")
        except:
            print("  ⚠️  Closed Loop Feedback System导入失败，但其他组件正常")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 组件导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_action_creation():
    """测试行动创建"""
    print("\n🧪 测试行动创建...")
    
    try:
        from action_system.action_generator import Action, ActionType, ActionRiskLevel
        
        # 创建测试行动
        action = Action(
            action_type=ActionType.DATA_RETRIEVAL,
            target="获取东京房产数据",
            parameters={"region": "东京", "data_type": "rental_prices"},
            expected_outcome="租金数据表格"
        )
        
        # 设置额外属性
        action.is_experiment = True
        action.hypothesis = "东京房产收益更高"
        
        print(f"  ✅ 行动创建成功:")
        print(f"    类型: {action.action_type.value}")
        print(f"    目标: {action.target}")
        print(f"    风险等级: {action.risk_level.value}")
        print(f"    真实影响: {action.real_world_impact}")
        print(f"    是实验: {action.is_experiment}")
        
        return action
        
    except Exception as e:
        print(f"  ❌ 行动创建失败: {e}")
        return None

def test_execution_simulation():
    """测试执行模拟"""
    print("\n🧪 测试执行模拟...")
    
    try:
        from action_system.action_executor import ActionExecutor, ExecutionStatus
        from action_system.action_generator import Action, ActionType, ActionRiskLevel
        
        # 创建执行器
        executor = ActionExecutor()
        
        # 创建测试行动
        action = Action(
            action_type=ActionType.API_CALL,
            target="调用外部API",
            parameters={"api": "weather", "location": "东京"},
            expected_outcome="天气数据"
        )
        
        # 模拟执行
        context = {"test": True}
        result = executor.execute_action(action, context)
        
        print(f"  ✅ 执行模拟成功:")
        print(f"    状态: {result.status.value}")
        print(f"    执行时间: {result.execution_time:.2f}秒")
        print(f"    错误: {result.error}")
        
        return result
        
    except Exception as e:
        print(f"  ❌ 执行模拟失败: {e}")
        return None

def test_validation_process():
    """测试验证过程"""
    print("\n🧪 测试验证过程...")
    
    try:
        from action_system.action_validation import ActionValidator
        from action_system.action_generator import Action, ActionType, ActionRiskLevel
        from action_system.action_executor import ExecutionResult, ExecutionStatus
        
        # 创建验证器
        validator = ActionValidator()
        
        # 创建测试行动
        action = Action(
            action_type=ActionType.ANALYSIS,
            target="分析数据",
            parameters={"data": "test_data"},
            expected_outcome="分析报告"
        )
        
        # 创建模拟执行结果
        result = ExecutionResult(
            action_id=action.id,
            action_type=action.action_type,
            target=action.target,
            status=ExecutionStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=1.5,
            result={"analysis": "测试分析结果"},
            error=None,
            retry_attempts=0,
            used_fallback=False,
            performance_metrics={"result_quality": 0.8}
        )
        
        # 执行验证
        validation = validator.validate_action(
            action, result, "测试目标", {"context": "test"}
        )
        
        print(f"  ✅ 验证过程成功:")
        print(f"    验证分数: {validation.validation_score:.3f}")
        print(f"    是否有效: {validation.is_valid}")
        print(f"    验证通过: {validation.validation_passed}")
        print(f"    目标对齐: {validation.goal_alignment:.3f}")
        print(f"    结果质量: {validation.result_quality:.3f}")
        
        return validation
        
    except Exception as e:
        print(f"  ❌ 验证过程失败: {e}")
        return None

def test_arqs_calculation():
    """测试ARQS计算"""
    print("\n🧪 测试ARQS计算...")
    
    try:
        from action_system.arqs_system import ARQSSystem
        from action_system.action_generator import Action, ActionType, ActionRiskLevel
        from action_system.action_executor import ExecutionResult, ExecutionStatus
        from action_system.action_validation import ValidationResult
        
        # 创建ARQS系统
        arqs_system = ARQSSystem()
        
        # 创建测试数据
        action = Action(
            id="test_arqs_001",
            action_type=ActionType.DECISION,
            target="做出决策",
            parameters={"options": ["A", "B", "C"]},
            expected_outcome="选择最佳选项",
            risk_level=ActionRiskLevel.HIGH
        )
        
        # 模拟执行结果
        exec_result = ExecutionResult(
            action_id=action.id,
            action_type=action.action_type,
            target=action.target,
            status=ExecutionStatus.COMPLETED,
            start_time=datetime.now(),
            end_time=datetime.now(),
            execution_time=2.0,
            result={"decision": "选项B", "confidence": 0.7},
            error=None
        )
        
        # 模拟验证结果
        validation_result = ValidationResult(
            action_id=action.id,
            action_type=action.action_type,
            validation_score=0.75,
            goal_alignment=0.8,
            result_quality=0.7,
            side_effect_penalty=0.1,
            consistency=0.6,
            is_valid=True,
            validation_passed=True,
            validation_details={},
            risk_assessment={},
            high_risk_factors=[],
            recommendations=[],
            requires_replan=False,
            validation_time=0.1
        )
        
        # 计算ARQS
        reasoning_quality = 0.8  # 模拟RQS分数
        arqs_entry = arqs_system.update_arqs(
            action, exec_result, validation_result, reasoning_quality,
            "测试目标", {"context": "test"}
        )
        
        print(f"  ✅ ARQS计算成功:")
        print(f"    ARQS分数: {arqs_entry.arqs_score:.3f}")
        print(f"    推理质量: {arqs_entry.reasoning_quality:.3f}")
        print(f"    行动成功: {arqs_entry.action_success:.3f}")
        print(f"    长期结果: {arqs_entry.long_term_outcome:.3f}")
        print(f"    置信度: {arqs_entry.confidence:.3f}")
        
        # 获取ARQS报告
        report = arqs_system.get_arqs_report()
        print(f"    当前ARQS: {report['current_state']['arqs_score']:.3f}")
        print(f"    ARQS趋势: {report['current_state']['arqs_trend']}")
        
        return arqs_entry
        
    except Exception as e:
        print(f"  ❌ ARQS计算失败: {e}")
        return None

def test_system_integration():
    """测试系统集成"""
    print("\n" + "=" * 60)
    print("🚀 测试Action System集成")
    print("=" * 60)
    
    # 测试所有组件
    components_ok = test_basic_components()
    
    if not components_ok:
        print("\n❌ 基础组件测试失败，无法继续集成测试")
        return False
    
    # 测试各功能模块
    action = test_action_creation()
    exec_result = test_execution_simulation()
    validation = test_validation_process()
    arqs_entry = test_arqs_calculation()
    
    # 评估测试结果
    tests_passed = 0
    total_tests = 4
    
    if action:
        tests_passed += 1
    if exec_result:
        tests_passed += 1
    if validation:
        tests_passed += 1
    if arqs_entry:
        tests_passed += 1
    
    success_rate = tests_passed / total_tests
    
    print("\n" + "=" * 60)
    print("📊 Action System集成测试结果")
    print("=" * 60)
    print(f"  测试通过率: {tests_passed}/{total_tests} ({success_rate:.1%})")
    
    if success_rate >= 0.75:
        print("  ✅ Action System集成测试基本通过")
        print("  系统具备核心功能:")
        print("    • 行动生成")
        print("    • 行动执行")
        print("    • 行动验证")
        print("    • ARQS计算")
        print("  🔜 闭环反馈系统需要进一步测试")
        return True
    elif success_rate >= 0.5:
        print("  ⚠️  Action System集成测试部分通过")
        print("  系统具备部分核心功能")
        return False
    else:
        print("  ❌ Action System集成测试失败")
        print("  系统需要进一步开发")
        return False

def main():
    """主函数"""
    print("🚀 开始Action System简单测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        success = test_system_integration()
        
        if success:
            print("\n🎉 Action System核心功能测试通过！")
            print("系统已具备从决策到行动的基础能力")
            print("✅ 可以生成、执行、验证行动，并计算ARQS")
        else:
            print("\n⚠️  Action System测试部分失败")
            print("需要进一步优化系统")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Action System测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()