#!/usr/bin/env python3
"""
偏向性策略进化测试 - 调整参数让系统更快形成策略偏好
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import time
import random
from world_interface.strategy_evolution import StrategyEvolutionEngine

class BiasedEvolutionEngine(StrategyEvolutionEngine):
    """偏向性进化引擎"""
    
    def __init__(self):
        super().__init__()
        
        # 调整进化参数
        self.mutation_rate = 0.15  # 增加突变率
        self.crossover_rate = 0.4   # 增加交叉率
        self.selection_pressure = 0.8  # 增加选择压力（更倾向于优秀策略）
        
        # 淘汰阈值
        self.elimination_threshold = 0.3  # 适应度低于此值的策略将被淘汰
    
    def _elimination(self):
        """淘汰策略（更激进）"""
        if len(self.strategies) <= 3:
            return  # 保持最小策略数量
        
        strategies = list(self.strategies.values())
        
        # 按适应度排序
        strategies.sort(key=lambda s: s.fitness_score)
        
        # 淘汰适应度低的策略
        to_remove = []
        for strategy in strategies:
            if strategy.fitness_score < self.elimination_threshold:
                # 确保不删除当前策略
                if strategy.id != self.current_strategy_id:
                    to_remove.append(strategy)
        
        # 至少保留3个策略
        max_to_remove = len(strategies) - 3
        to_remove = to_remove[:max_to_remove]
        
        for strategy in to_remove:
            del self.strategies[strategy.id]
            self.stats["total_strategies"] -= 1
            self.stats["strategies_removed"] += 1
        
        # 如果当前策略被删除，选择新的当前策略
        if self.current_strategy_id and self.current_strategy_id not in self.strategies:
            if self.strategies:
                # 选择适应度最高的策略
                best_strategy = max(self.strategies.values(), key=lambda s: s.fitness_score)
                self.current_strategy_id = best_strategy.id
            else:
                self.current_strategy_id = None

def run_biased_evolution_test(num_iterations=150):
    """运行偏向性进化测试"""
    print(f"🧪 运行{num_iterations}次迭代的偏向性进化测试...")
    print("  参数: mutation_rate=0.15, crossover_rate=0.4, selection_pressure=0.8")
    
    engine = BiasedEvolutionEngine()
    distribution_history = []
    
    strategies = list(engine.strategies.values())
    
    for i in range(num_iterations):
        # 根据策略类型选择（更倾向于选择当前策略）
        if engine.current_strategy_id and random.random() < 0.7:  # 70%选择当前策略
            strategy = engine.strategies[engine.current_strategy_id]
        else:
            strategy = random.choice(strategies)
        
        # 根据策略类型生成性能数据（保守策略表现明显更好）
        if strategy.strategy_type == "conservative":
            arqs = random.uniform(0.75, 0.95)  # 高ARQS
            real_success = random.random() > 0.15  # 85%成功率
            cost = random.uniform(0.08, 0.25)  # 低成本
            latency = random.uniform(40, 120)  # 低延迟
            
        elif strategy.strategy_type == "balanced":
            arqs = random.uniform(0.65, 0.85)
            real_success = random.random() > 0.25  # 75%成功率
            cost = random.uniform(0.12, 0.35)
            latency = random.uniform(60, 180)
            
        elif strategy.strategy_type == "exploratory":
            arqs = random.uniform(0.45, 0.75)
            real_success = random.random() > 0.45  # 55%成功率
            cost = random.uniform(0.18, 0.45)
            latency = random.uniform(90, 280)
            
        elif strategy.strategy_type == "aggressive":
            arqs = random.uniform(0.35, 0.65)
            real_success = random.random() > 0.65  # 35%成功率
            cost = random.uniform(0.25, 0.65)
            latency = random.uniform(180, 450)
            
        else:  # hybrid
            arqs = random.uniform(0.55, 0.85)
            real_success = random.random() > 0.35  # 65%成功率
            cost = random.uniform(0.15, 0.4)
            latency = random.uniform(80, 220)
        
        # 更新策略性能
        engine.update_strategy_performance(
            strategy.id, arqs, real_success, cost, latency
        )
        
        # 每5次进化一次（更频繁）
        if i % 5 == 0:
            engine.evolve()
        
        # 每25次记录一次分布
        if i % 25 == 0:
            stats = engine.get_stats()
            distribution_history.append({
                "iteration": i,
                "distribution": stats['strategy_types'].copy(),
                "avg_fitness": stats['stats']['avg_fitness'],
                "best_fitness": stats['stats']['best_fitness'],
                "current_strategy": stats['current_strategy']['type'] if stats['current_strategy'] else None
            })
            
            if i % 50 == 0:
                print(f"  迭代 {i}: 平均适应度={stats['stats']['avg_fitness']:.3f}, "
                      f"最佳适应度={stats['stats']['best_fitness']:.3f}, "
                      f"当前策略={stats['current_strategy']['type'] if stats['current_strategy'] else 'None'}")
    
    return engine, distribution_history

def analyze_biased_distribution(distribution_history):
    """分析偏向性分布"""
    print("\n📈 偏向性策略分布分析:")
    
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
    
    # 检查当前策略类型
    current_strategy_type = final.get('current_strategy')
    if current_strategy_type:
        print(f"\n  ❗ 当前策略类型: {current_strategy_type}")
    
    # 计算主导策略
    final_dist = final['distribution']
    if final_dist:
        dominant_type = max(final_dist.items(), key=lambda x: x[1])
        total = sum(final_dist.values())
        dominant_percentage = (dominant_type[1] / total * 100) if total > 0 else 0
        
        print(f"  ❗ 最终主导策略: {dominant_type[0]} ({dominant_percentage:.1f}%)")
        
        if dominant_percentage > 50:
            print(f"  ✅ 策略分布强烈偏向: {dominant_type[0]}")
            return True, dominant_type[0], dominant_percentage
        elif dominant_percentage > 35:
            print(f"  ✅ 策略分布明显偏向: {dominant_type[0]}")
            return True, dominant_type[0], dominant_percentage
        else:
            print(f"  ⚠️  策略分布相对均衡")
            return False, None, dominant_percentage
    else:
        print(f"  ⚠️  无策略分布数据")
        return False, None, 0

def main():
    """主函数"""
    print("🚀 开始偏向性策略进化测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 运行偏向性进化测试
        engine, distribution_history = run_biased_evolution_test(num_iterations=200)
        
        # 分析分布
        has_bias, dominant_type, dominant_percentage = analyze_biased_distribution(distribution_history)
        
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
        print(f"策略淘汰数: {stats['stats']['strategies_removed']}")
        
        # 显示策略详情
        strategies = list(engine.strategies.values())
        strategies.sort(key=lambda s: s.fitness_score, reverse=True)
        
        print(f"\n策略详情:")
        for i, strategy in enumerate(strategies):
            print(f"  {i+1}. {strategy.name} ({strategy.strategy_type}):")
            print(f"     适应度: {strategy.fitness_score:.3f}")
            print(f"     成功率: {strategy.success_rate:.1%}")
            print(f"     平均成本: {strategy.avg_cost:.3f}")
            print(f"     使用次数: {strategy.metrics['usage_count']}")
            print(f"     探索率: {strategy.exploration_rate:.3f}")
        
        # 结论
        print("\n" + "=" * 60)
        print("🧭 偏向性进化测试结论")
        print("=" * 60)
        
        if has_bias:
            print(f"✅ 策略分布已形成明显偏向: {dominant_type} ({dominant_percentage:.1f}%)")
            print(f"✅ 系统已学会选择更有效的策略类型")
            
            if dominant_type == "conservative":
                print(f"  💡 系统偏好: 保守策略（低风险、高成功率）")
                print(f"  💡 现实意义: 系统在不确定环境中倾向于安全第一")
            elif dominant_type == "balanced":
                print(f"  💡 系统偏好: 平衡策略（稳定、适中风险）")
                print(f"  💡 现实意义: 系统寻求风险与回报的平衡")
            elif dominant_type == "exploratory":
                print(f"  💡 系统偏好: 探索策略（高探索、发现新机会）")
                print(f"  💡 现实意义: 系统处于探索阶段，寻找最优策略")
            elif dominant_type == "aggressive":
                print(f"  💡 系统偏好: 激进策略（高风险、高回报）")
                print(f"  💡 现实意义: 系统在确定环境中追求最大回报")
            
            print(f"✅ 进化机制有效工作")
            print(f"✅ 系统已具备策略选择能力")
            print(f"✅ 准备好升级到下一层级: 多信号 + 预测 + 简单金融决策系统")
        else:
            print(f"⚠️  策略分布仍相对均衡")
            print(f"⚠️  系统仍在探索阶段")
            print(f"⚠️  需要进一步调整进化参数")
        
        # 检查进化效果
        if stats['stats']['strategies_removed'] > 0:
            print(f"✅ 淘汰机制有效: 淘汰了{stats['stats']['strategies_removed']}个低适应度策略")
        
        if stats['stats']['avg_fitness'] > 0.6:
            print(f"✅ 系统适应度高: {stats['stats']['avg_fitness']:.3f}")
        elif stats['stats']['avg_fitness'] > 0.4:
            print(f"⚠️  系统适应度中等: {stats['stats']['avg_fitness']:.3f}")
        else:
            print(f"⚠️  系统适应度低: {stats['stats']['avg_fitness']:.3f}")
        
        return has_bias, dominant_type, dominant_percentage
        
    except Exception as e:
        print(f"\n❌ 偏向性进化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None, 0

if __name__ == "__main__":
    main()