#!/usr/bin/env python3
"""
测试策略进化 - 观察策略分布变化
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import time
import random
from world_interface.strategy_evolution import StrategyEvolutionEngine, Strategy

def create_test_strategies():
    """创建测试策略"""
    engine = StrategyEvolutionEngine()
    
    print("🧪 初始策略分布:")
    stats = engine.get_stats()
    print(f"  策略总数: {stats['strategy_count']}")
    print(f"  策略类型分布: {stats['strategy_types']}")
    
    return engine

def simulate_performance(engine, num_iterations=20):
    """模拟性能更新"""
    print(f"\n🧪 模拟{num_iterations}次性能更新...")
    
    strategies = list(engine.strategies.values())
    
    for i in range(num_iterations):
        # 随机选择一个策略
        strategy = random.choice(strategies)
        
        # 生成模拟性能数据
        # 保守策略表现更好
        if strategy.strategy_type == "conservative":
            arqs = random.uniform(0.6, 0.9)  # 高ARQS
            real_success = random.random() > 0.3  # 70%成功率
            cost = random.uniform(0.1, 0.3)  # 低成本
            latency = random.uniform(50, 200)  # 低延迟
            
        # 探索性策略表现中等
        elif strategy.strategy_type == "exploratory":
            arqs = random.uniform(0.4, 0.7)
            real_success = random.random() > 0.5  # 50%成功率
            cost = random.uniform(0.2, 0.5)
            latency = random.uniform(100, 300)
            
        # 激进策略表现较差
        elif strategy.strategy_type == "aggressive":
            arqs = random.uniform(0.3, 0.6)
            real_success = random.random() > 0.7  # 30%成功率
            cost = random.uniform(0.3, 0.7)
            latency = random.uniform(200, 500)
            
        # 平衡策略表现稳定
        else:  # balanced, hybrid
            arqs = random.uniform(0.5, 0.8)
            real_success = random.random() > 0.4  # 60%成功率
            cost = random.uniform(0.15, 0.4)
            latency = random.uniform(80, 250)
        
        # 更新策略性能
        engine.update_strategy_performance(
            strategy.id, arqs, real_success, cost, latency
        )
        
        # 每5次进化一次
        if i % 5 == 0:
            engine.evolve()
        
        # 每10次显示一次状态
        if i % 10 == 0:
            print(f"  迭代 {i}: {strategy.name} (类型: {strategy.strategy_type})")
            print(f"    适应度: {strategy.fitness_score:.3f}, 成功率: {strategy.success_rate:.1%}")
    
    return engine

def analyze_strategy_distribution(engine):
    """分析策略分布"""
    print("\n📊 策略分布分析:")
    
    stats = engine.get_stats()
    strategy_types = stats['strategy_types']
    
    # 计算总数
    total = sum(strategy_types.values())
    
    print(f"  策略总数: {total}")
    print(f"  类型分布:")
    
    for strategy_type, count in sorted(strategy_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        print(f"    {strategy_type}: {count} ({percentage:.1f}%)")
    
    # 分析适应度分布
    strategies = list(engine.strategies.values())
    strategies.sort(key=lambda s: s.fitness_score, reverse=True)
    
    print(f"\n  适应度排名:")
    for i, strategy in enumerate(strategies[:5]):
        print(f"    {i+1}. {strategy.name} ({strategy.strategy_type}): "
              f"适应度={strategy.fitness_score:.3f}, "
              f"成功率={strategy.success_rate:.1%}, "
              f"使用次数={strategy.metrics['usage_count']}")
    
    # 检查是否有明显偏向
    dominant_type = max(strategy_types.items(), key=lambda x: x[1])
    dominant_percentage = (dominant_type[1] / total * 100) if total > 0 else 0
    
    print(f"\n  ❗ 主导策略类型: {dominant_type[0]} ({dominant_percentage:.1f}%)")
    
    if dominant_percentage > 40:
        print(f"  ✅ 策略分布明显偏向: {dominant_type[0]}")
        return True, dominant_type[0]
    else:
        print(f"  ⚠️  策略分布相对均衡")
        return False, None

def test_evolution_dynamics():
    """测试进化动态"""
    print("🚀 测试策略进化动态")
    print("=" * 60)
    
    # 1. 创建初始策略
    engine = create_test_strategies()
    
    # 2. 模拟性能更新
    engine = simulate_performance(engine, num_iterations=30)
    
    # 3. 分析策略分布
    has_bias, dominant_type = analyze_strategy_distribution(engine)
    
    # 4. 显示详细状态
    print("\n📈 进化引擎详细状态:")
    engine.print_status()
    
    # 5. 结论
    print("\n" + "=" * 60)
    print("🎯 策略进化分析结论")
    print("=" * 60)
    
    if has_bias:
        print(f"✅ 策略分布已明显偏向: {dominant_type}")
        print(f"  说明: 系统已学会选择更有效的策略类型")
        
        if dominant_type == "conservative":
            print(f"  含义: 系统倾向于保守策略（低风险、高成功率）")
        elif dominant_type == "balanced":
            print(f"  含义: 系统倾向于平衡策略（稳定、适中风险）")
        elif dominant_type == "exploratory":
            print(f"  含义: 系统倾向于探索策略（高探索、发现新机会）")
        elif dominant_type == "aggressive":
            print(f"  含义: 系统倾向于激进策略（高风险、高回报）")
        else:
            print(f"  含义: 系统倾向于混合策略（适应性强）")
    else:
        print("⚠️  策略分布相对均衡")
        print("  说明: 系统仍在探索不同策略类型")
        print("  建议: 增加迭代次数或调整进化参数")
    
    # 检查进化是否有效
    stats = engine.get_stats()
    if stats['stats']['total_mutations'] > 0 or stats['stats']['total_crossovers'] > 0:
        print(f"✅ 进化机制有效: {stats['stats']['total_mutations']}次突变, {stats['stats']['total_crossovers']}次交叉")
    else:
        print("⚠️  进化机制未充分激活")
    
    print(f"✅ 平均适应度: {stats['stats']['avg_fitness']:.3f}")
    print(f"✅ 最佳适应度: {stats['stats']['best_fitness']:.3f}")
    
    return has_bias, dominant_type, engine

def main():
    """主函数"""
    print("🚀 开始策略进化分布测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        has_bias, dominant_type, engine = test_evolution_dynamics()
        
        print("\n" + "=" * 60)
        print("🧭 系统状态总结")
        print("=" * 60)
        
        # 获取当前策略
        current_strategy = engine.get_current_strategy()
        if current_strategy:
            print(f"当前策略: {current_strategy.name} ({current_strategy.strategy_type})")
            print(f"适应度: {current_strategy.fitness_score:.3f}")
            print(f"成功率: {current_strategy.success_rate:.1%}")
            print(f"探索率: {current_strategy.exploration_rate:.3f}")
        
        # 评估系统成熟度
        stats = engine.get_stats()
        avg_fitness = stats['stats']['avg_fitness']
        
        if avg_fitness > 0.6:
            maturity = "高"
        elif avg_fitness > 0.4:
            maturity = "中"
        else:
            maturity = "低"
        
        print(f"系统成熟度: {maturity} (平均适应度: {avg_fitness:.3f})")
        
        if has_bias:
            print(f"✅ 系统已具备策略选择能力")
            print(f"✅ 已形成策略偏好: {dominant_type}")
            print(f"✅ 准备好升级到下一层级")
        else:
            print(f"⚠️  系统仍在探索阶段")
            print(f"⚠️  需要更多迭代形成稳定策略")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ 策略进化测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()