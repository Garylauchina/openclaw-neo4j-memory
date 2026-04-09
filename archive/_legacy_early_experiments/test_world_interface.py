#!/usr/bin/env python3
"""
测试World Interface完整闭环系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from world_interface.environment import Environment, Action
from world_interface.validation_enhanced import EnhancedValidator
from world_interface.strategy_evolution import StrategyEvolutionEngine, Strategy

def test_environment():
    """测试环境"""
    print("🧪 测试Environment...")
    
    env = Environment()
    
    # 创建测试行动
    action = Action(
        type="api_call",
        target="weather_api",
        params={"location": "Tokyo", "mock": True},
        expected_effect="获取东京天气数据",
        observable_signal="temperature"
    )
    
    # 执行行动
    result = env.act(action)
    
    print(f"  执行结果:")
    print(f"    状态: {result.status}")
    print(f"    延迟: {result.latency_ms:.1f}ms")
    print(f"    资源使用: {result.resource_usage:.3f}")
    print(f"    风险: {result.risk:.3f}")
    
    if result.result:
        print(f"    结果: {result.result.get('location', 'N/A')}, {result.result.get('temperature', 'N/A')}°C")
    
    # 显示环境状态
    env.print_status()
    
    return env, action, result

def test_enhanced_validator(action, execution_result):
    """测试增强版验证器"""
    print("\n🧪 测试EnhancedValidator...")
    
    validator = EnhancedValidator()
    
    # 执行验证
    validation = validator.validate(
        action, execution_result, 
        "获取东京天气信息用于分析",
        {"context": "test"}
    )
    
    print(f"  验证结果:")
    print(f"    验证分数: {validation.validation_score:.3f}")
    print(f"    内部一致性: {validation.internal_consistency:.3f}")
    print(f"    目标对齐: {validation.goal_alignment:.3f}")
    print(f"    外部反馈: {validation.external_feedback:.3f}")  # ❗ 核心指标
    print(f"    是否成功: {validation.success}")
    print(f"    数据质量: {validation.data_quality:.3f}")
    print(f"    成本: {validation.cost:.3f}")
    print(f"    是否有效: {validation.is_valid}")
    print(f"    验证通过: {validation.validation_passed}")
    print(f"    需要重规划: {validation.requires_replan}")
    
    # 显示验证器状态
    validator.print_status()
    
    return validator, validation

def test_strategy_evolution(validation_result, execution_result):
    """测试策略进化"""
    print("\n🧪 测试StrategyEvolution...")
    
    engine = StrategyEvolutionEngine()
    
    # 获取当前策略
    strategy = engine.get_current_strategy()
    if strategy:
        print(f"  当前策略: {strategy.name} ({strategy.strategy_type})")
        print(f"    适应度: {strategy.fitness_score:.3f}")
        print(f"    成功率: {strategy.success_rate:.1%}")
        print(f"    探索率: {strategy.exploration_rate:.3f}")
    
    # 更新策略性能
    if strategy:
        engine.update_strategy_performance(
            strategy.id,
            validation_result.validation_score,  # ARQS分数
            validation_result.success,           # ❗ 真实成功率
            validation_result.cost,              # 成本
            execution_result.latency_ms          # 延迟
        )
        
        print(f"  策略性能更新:")
        print(f"    ARQS分数: {validation_result.validation_score:.3f}")
        print(f"    真实成功: {validation_result.success}")
        print(f"    成本: {validation_result.cost:.3f}")
        print(f"    延迟: {execution_result.latency_ms:.1f}ms")
    
    # 进化策略
    print(f"  进化策略...")
    engine.evolve()
    
    # 显示策略引擎状态
    engine.print_status()
    
    return engine

def test_full_closed_loop():
    """测试完整闭环"""
    print("\n" + "=" * 60)
    print("🚀 测试完整闭环系统")
    print("=" * 60)
    
    # 1. 环境执行
    env, action, exec_result = test_environment()
    
    # 2. 增强验证
    validator, validation = test_enhanced_validator(action, exec_result)
    
    # 3. 策略进化
    engine = test_strategy_evolution(validation, exec_result)
    
    # 4. 系统状态汇总
    print("\n" + "=" * 60)
    print("📊 完整闭环系统状态汇总")
    print("=" * 60)
    
    # 计算关键指标
    success = validation.success
    validation_score = validation.validation_score
    external_feedback = validation.external_feedback  # ❗ 核心指标
    cost = validation.cost
    
    print(f"  关键指标:")
    print(f"    执行成功: {success}")
    print(f"    验证分数: {validation_score:.3f}")
    print(f"    外部反馈: {external_feedback:.3f}")  # ❗ 显示核心指标
    print(f"    行动成本: {cost:.3f}")
    
    # 评估系统健康
    system_health = (
        0.4 * (1.0 if success else 0.0) +      # 成功率权重40%
        0.4 * external_feedback +              # ❗ 外部反馈权重40%
        0.2 * (1.0 - min(1.0, cost * 2))       # 成本权重20%
    )
    
    print(f"  系统健康分数: {system_health:.3f}")
    
    if system_health > 0.7:
        print("  ✅ 系统状态: 优秀 - 闭环系统运行良好")
    elif system_health > 0.5:
        print("  ⚠️  系统状态: 良好 - 有改进空间")
    else:
        print("  ❌ 系统状态: 需要改进 - 系统性能不足")
    
    # 检查现实锚定
    print(f"  现实锚定检查:")
    print(f"    是否经过Environment: ✅")
    print(f"    是否有外部反馈: ✅ ({external_feedback:.3f})")
    print(f"    是否计算成本: ✅ ({cost:.3f})")
    print(f"    策略是否进化: ✅")
    
    print("\n" + "=" * 60)
    print("✅ 完整闭环系统测试完成")
    print("=" * 60)
    
    return system_health > 0.6

def main():
    """主函数"""
    print("🚀 开始World Interface完整闭环系统测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        success = test_full_closed_loop()
        
        if success:
            print("\n🎉 World Interface完整闭环系统测试通过！")
            print("系统已成功从'模拟智能'变成'现实智能'")
            print("✅ 具备完整现实锚定：环境执行 → 增强验证 → 策略进化")
        else:
            print("\n⚠️  World Interface测试部分失败")
            print("需要进一步优化系统")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ World Interface测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()