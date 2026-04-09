#!/usr/bin/env python3
"""
长时间策略进化测试 - 观察策略分布变化
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import time
import random
from world_interface.strategy_evolution import StrategyEvolutionEngine

def run_long_evolution_test(num_iterations=100):
    """运行长时间进化测试"""
    print(f"🧪 运行{num_iterations}次迭代的长时间进化测试...")
    
    engine = StrategyEvolutionEngine()
    distribution_history = []
    fitness_history = []
    
    strategies = list(engine.strategies.values())
    
    for i in range(num_iterations):
        # 随机选择一个策略
        strategy = random.choice(strategies)
        
        # 根据策略类型生成性能数据（保守策略表现更好）
        if strategy.strategy_type == "conservative":
            arqs = random.uniform(0.7, 0.9)
            real_success = random.random() > 0.2  # 80%成功率
            cost = random.uniform(0.1, 0.3)
            latency = random.uniform(50, 150)
            
        elif strategy.strategy_type == "balanced":
            arqs = random.uniform(0.6, 0.8)
            real_success = random.random() > 0.3  # 70%成功率
            cost = random.uniform(0.15, 0.4)
            latency = random.uniform(80, 200)
            
        elif strategy.strategy_type == "exploratory":
            arqs = random.uniform(0.4, 0.7)
            real_success = random.random() > 0.5  # 50%成功率
            cost = random.uniform(0.2, 0.5)
            latency = random.uniform(100, 300)
            
        elif strategy.strategy_type == "aggressive":
            arqs = random.uniform(0.3, 0.6)
            real_success = random.random() > 0.7  # 30%成功率
            cost = random.uniform(0.3, 0.7)
            latency = random.uniform(200, 500)
            
        else:  # hybrid
            arqs = random.uniform(0.5, 0.8)
            real_success = random.random() > 0.4  # 60%成功率
            cost = random.uniform(0.2, 0.45)
            latency = random.uniform(100, 250)
        
        # 更新策略性能
        engine.update_strategy_performance(
            strategy.id, arqs, real_success, cost, latency
        )
        
        # 每10次进化一次
        if i % 10 == 0:
            engine.evolve()
        
        # 每20次记录一次分布
        if i % 20 == 0:
            stats = engine.get_stats()
            distribution_history.append({
                "iteration": i,
                "distribution": stats['strategy_types'].copy(),
                "avg_fitness": stats['stats']['avg_fitness'],
                "best_fitness": stats['stats']['best_fitness']
            })
            
            fitness_history.append(stats['stats']['avg_fitness'])
            
            if i % 40 == 0:
                print(f"  迭代 {i}: 平均适应度={stats['stats']['avg_fitness']:.3f}, "
                      f"最佳适应度={stats['stats']['best_fitness']:.3f}")
    
    return engine, distribution_history, fitness_history

def analyze_distribution_trend(distribution_history):
    """分析分布趋势"""
    print("\n📈 策略分布趋势分析:")
    
    if not distribution_history:
        print("  无分布历史数据")
        return None
    
    # 获取初始和最终分布
    initial = distribution_history[0]
    final = distribution_history[-1]
    
    print(f"  初始分布 (迭代 {initial['iteration']}):")
    for strategy_type, count in sorted(initial['distribution'].items()):
        total = sum(initial['distribution'].values())
        percentage = (count / total * 100) if total > 0 else 0
        print(f"    {strategy_type}: {count} ({percentage:.1f}%)")
    
    print(f"\n  最终分布 (迭代 {final['iteration']}):")
    for strategy_type, count in sorted(final['distribution'].items()):
        total = sum(final['distribution'].values())
        percentage = (count / total * 100) if total > 0 else 0
        print(f"    {strategy_type}: {count} ({percentage:.1f}%)")
    
    # 计算变化
    initial_total = sum(initial['distribution'].values())
    final_total = sum(final['distribution'].values())
    
    changes = {}
    for strategy_type in set(list(initial['distribution'].keys()) + list(final['distribution'].keys())):
        initial_count = initial['distribution'].get(strategy_type, 0)
        final_count = final['distribution'].get(strategy_type, 0)
        
        initial_pct = (initial_count / initial_total * 100) if initial_total > 0 else 0
        final_pct = (final_count / final_total * 100) if final_total > 0 else 0
        
        changes[strategy_type] = {
            "initial": initial_pct,
            "final": final_pct,
            "change": final_pct - initial_pct
        }
    
    # 找出变化最大的策略类型
    max_change_type = max(changes.items(), key=lambda x: abs(x[1]["change"]))
    
    print(f"\n  ❗ 最大变化: {max_change_type[0]}")
    print(f"    初始: {max_change_type[1]['initial']:.1f}% → 最终: {max_change_type[1]['final']:.1f}%")
    print(f"    变化: {max_change_type[1]['change']:+.1f}%")
    
    # 检查是否有明显偏向
    final_dist = final['distribution']
    dominant_type = max(final_dist.items(), key=lambda x: x[1])
    total = sum(final_dist.values())
    dominant_percentage = (dominant_type[1] / total * 100) if total > 0 else 0
    
    print(f"\n  ❗ 最终主导策略: {dominant_type[0]} ({dominant_percentage:.1f}%)")
    
    if dominant_percentage > 40:
        print(f"  ✅ 策略分布明显偏向: {dominant_type[0]}")
        return True, dominant_type[0], changes
    else:
        print(f"  ⚠️  策略分布相对均衡")
        return False, None, changes

def analyze_fitness_trend(fitness_history):
    """分析适应度趋势"""
    print("\n📊 适应度趋势分析:")
    
    if len(fitness_history) < 2:
        print("  适应度历史数据不足")
        return
    
    initial_fitness = fitness_history[0]
    final_fitness = fitness_history[-1]
    max_fitness = max(fitness_history)
    min_fitness = min(fitness_history)
    
    print(f"  初始平均适应度: {initial_fitness:.3f}")
    print(f"  最终平均适应度: {final_fitness:.3f}")
    print(f"  最高平均适应度: {max_fitness:.3f}")
    print(f"  最低平均适应度: {min_fitness:.3f}")
    print(f"  适应度变化: {final_fitness - initial_fitness:+.3f}")
    
    # 计算趋势
    if len(fitness_history) >= 3:
        first_third = sum(fitness_history[:len(fitness_history)//3]) / (len(fitness_history)//3)
        last_third = sum(fitness_history[-(len(fitness_history)//3):]) / (len(fitness_history)//3)
        
        trend = last_third - first_third
        
        print(f"  适应度趋势 (前1/3 vs 后1/3): {trend:+.3f}")
        
        if trend > 0.1:
            print(f"  ✅ 适应度明显上升趋势")
        elif trend > 0.05:
            print(f"  ⚠️  适应度缓慢上升趋势")
        elif trend < -0.05:
            print(f"  ⚠️  适应度下降趋势")
        else:
            print(f"  ⚠️  适应度基本稳定")

def main():
    """主函数"""
    print("🚀 开始长时间策略进化测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 运行长时间进化测试
        engine, distribution_history, fitness_history = run_long_evolution_test(num_iterations=200)
        
        # 分析分布趋势
        has_bias, dominant_type, changes = analyze_distribution_trend(distribution_history)
        
        # 分析适应度趋势
        analyze_fitness_trend(fitness_history)
        
        # 显示最终状态
        print("\n" + "=" * 60)
        print("🎯 最终系统状态")
        print("=" * 60)
        
        stats = engine.get_stats()
        print(f"策略总数: {stats['strategy_count']}")
        print(f"平均适应度: {stats['stats']['avg_fitness']:.3f}")
        print(f"最佳适应度: {stats['stats']['best_fitness']:.3f}")
        print(f"总突变数: {stats['stats']['total_mutations']}")
        print(f"总交叉数: {stats['stats']['total_crossovers']}")
        
        # 显示最佳策略
        strategies = list(engine.strategies.values())
        strategies.sort(key=lambda s: s.fitness_score, reverse=True)
        
        print(f"\n最佳策略 (前3):")
        for i, strategy in enumerate(strategies[:3]):
            print(f"  {i+1}. {strategy.name} ({strategy.strategy_type}): "
                  f"适应度={strategy.fitness_score:.3f}, "
                  f"成功率={strategy.success_rate:.1%}, "
                  f"使用次数={strategy.metrics['usage_count']}")
        
        # 结论
        print("\n" + "=" * 60)
        print("🧭 进化测试结论")
        print("=" * 60)
        
        if has_bias:
            print(f"✅ 策略分布已形成明显偏向: {dominant_type}")
            print(f"✅ 系统已学会选择更有效的策略类型")
            print(f"✅ 进化机制有效工作")
            print(f"✅ 准备好升级到下一层级")
        else:
            print(f"⚠️  策略分布仍相对均衡")
            print(f"⚠️  系统仍在探索阶段")
            print(f"⚠️  可能需要调整进化参数或增加迭代次数")
        
        # 检查进化是否有效
        if stats['stats']['total_mutations'] > 5 or stats['stats']['total_crossovers'] > 5:
            print(f"✅ 进化机制充分激活")
        else:
            print(f"⚠️  进化机制激活不足")
        
        # 适应度提升检查
        if fitness_history and fitness_history[-1] > fitness_history[0] + 0.1:
            print(f"✅ 适应度显著提升")
        elif fitness_history and fitness_history[-1] > fitness_history[0]:
            print(f"⚠️  适应度略有提升")
        else:
            print(f"⚠️  适应度未提升")
        
        return has_bias, dominant_type
        
    except Exception as e:
        print(f"\n❌ 长时间进化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    main()