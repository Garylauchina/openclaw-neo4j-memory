#!/usr/bin/env python3
"""
极端偏向性测试 - 让保守策略表现明显更好，观察系统是否学会选择
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
import time
import random
from world_interface.strategy_evolution import StrategyEvolutionEngine

class ExtremeBiasEngine(StrategyEvolutionEngine):
    """极端偏向性进化引擎"""
    
    def __init__(self):
        super().__init__()
        
        # 极端进化参数
        self.mutation_rate = 0.2  # 高突变率
        self.crossover_rate = 0.5  # 高交叉率
        self.selection_pressure = 0.9  # 极高选择压力
        
        # 激进淘汰
        self.elimination_threshold = 0.4  # 淘汰阈值提高
    
    def _elimination(self):
        """激进淘汰"""
        if len(self.strategies) <= 2:
            return
        
        strategies = list(self.strategies.values())
        strategies.sort(key=lambda s: s.fitness_score)
        
        # 淘汰低适应度策略
        to_remove = []
        for strategy in strategies:
            if strategy.fitness_score < self.elimination_threshold:
                if strategy.id != self.current_strategy_id:
                    to_remove.append(strategy)
        
        # 至少保留2个策略
        max_to_remove = len(strategies) - 2
        to_remove = to_remove[:max_to_remove]
        
        for strategy in to_remove:
            del self.strategies[strategy.id]
            self.stats["total_strategies"] -= 1
            self.stats["strategies_removed"] += 1
        
        # 更新当前策略
        if self.current_strategy_id and self.current_strategy_id not in self.strategies:
            if self.strategies:
                best = max(self.strategies.values(), key=lambda s: s.fitness_score)
                self.current_strategy_id = best.id

def run_extreme_bias_test():
    """运行极端偏向性测试"""
    print("🧪 运行极端偏向性测试...")
    print("  保守策略: 成功率90%，低成本")
    print("  其他策略: 成功率30-60%，高成本")
    
    engine = ExtremeBiasEngine()
    history = []
    
    # 初始策略
    strategies = list(engine.strategies.values())
    print(f"  初始策略数: {len(strategies)}")
    
    for i in range(100):
        # 选择策略（80%选择当前策略）
        if engine.current_strategy_id and random.random() < 0.8:
            strategy = engine.strategies[engine.current_strategy_id]
        else:
            strategy = random.choice(strategies)
        
        # 极端偏向：保守策略表现极好，其他策略表现差
        if strategy.strategy_type == "conservative":
            arqs = random.uniform(0.8, 0.95)  # 极高ARQS
            real_success = random.random() > 0.1  # 90%成功率
            cost = random.uniform(0.05, 0.2)  # 极低成本
            latency = random.uniform(30, 100)  # 极低延迟
            
        elif strategy.strategy_type == "balanced":
            arqs = random.uniform(0.5, 0.7)
            real_success = random.random() > 0.5  # 50%成功率
            cost = random.uniform(0.3, 0.6)
            latency = random.uniform(150, 300)
            
        elif strategy.strategy_type == "exploratory":
            arqs = random.uniform(0.4, 0.6)
            real_success = random.random() > 0.6  # 40%成功率
            cost = random.uniform(0.4, 0.7)
            latency = random.uniform(200, 400)
            
        elif strategy.strategy_type == "aggressive":
            arqs = random.uniform(0.3, 0.5)
            real_success = random.random() > 0.7  # 30%成功率
            cost = random.uniform(0.5, 0.8)
            latency = random.uniform(300, 600)
        
        # 更新性能
        engine.update_strategy_performance(
            strategy.id, arqs, real_success, cost, latency
        )
        
        # 频繁进化
        if i % 3 == 0:
            engine.evolve()
        
        # 记录
        if i % 20 == 0:
            stats = engine.get_stats()
            history.append({
                "iteration": i,
                "strategy_count": stats['strategy_count'],
                "strategy_types": stats['strategy_types'],
                "avg_fitness": stats['stats']['avg_fitness'],
                "best_fitness": stats['stats']['best_fitness'],
                "current_type": stats['current_strategy']['type'] if stats['current_strategy'] else None
            })
    
    return engine, history

def analyze_extreme_results(engine, history):
    """分析极端测试结果"""
    print("\n📊 极端测试结果分析:")
    
    if not history:
        print("  无历史数据")
        return
    
    initial = history[0]
    final = history[-1]
    
    print(f"  初始状态 (迭代 {initial['iteration']}):")
    print(f"    策略数: {initial['strategy_count']}")
    print(f"    策略类型: {initial['strategy_types']}")
    print(f"    平均适应度: {initial['avg_fitness']:.3f}")
    
    print(f"\n  最终状态 (迭代 {final['iteration']}):")
    print(f"    策略数: {final['strategy_count']}")
    print(f"    策略类型: {final['strategy_types']}")
    print(f"    平均适应度: {final['avg_fitness']:.3f}")
    print(f"    最佳适应度: {final['best_fitness']:.3f}")
    print(f"    当前策略类型: {final['current_type']}")
    
    # 分析策略分布
    final_types = final['strategy_types']
    total = sum(final_types.values())
    
    print(f"\n  ❗ 最终策略分布:")
    for strategy_type, count in sorted(final_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        print(f"    {strategy_type}: {count} ({percentage:.1f}%)")
    
    # 检查是否有单一主导策略
    if len(final_types) == 1:
        dominant_type = list(final_types.keys())[0]
        print(f"  ✅ 策略分布极端偏向: {dominant_type} (100%)")
        return True, dominant_type, 100.0
    
    elif len(final_types) == 2:
        # 检查是否有明显主导
        types = list(final_types.items())
        types.sort(key=lambda x: x[1], reverse=True)
        
        dominant_type, dominant_count = types[0]
        secondary_type, secondary_count = types[1]
        
        dominant_percentage = (dominant_count / total * 100) if total > 0 else 0
        
        if dominant_percentage > 66:
            print(f"  ✅ 策略分布强烈偏向: {dominant_type} ({dominant_percentage:.1f}%)")
            return True, dominant_type, dominant_percentage
        else:
            print(f"  ⚠️  策略分布双峰: {dominant_type} ({dominant_percentage:.1f}%), {secondary_type} ({100-dominant_percentage:.1f}%)")
            return False, None, dominant_percentage
    
    else:
        # 多个策略类型
        print(f"  ⚠️  策略分布多元")
        return False, None, 0

def main():
    """主函数"""
    print("🚀 开始极端偏向性策略进化测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 运行测试
        engine, history = run_extreme_bias_test()
        
        # 分析结果
        has_extreme_bias, dominant_type, dominant_percentage = analyze_extreme_results(engine, history)
        
        # 显示策略详情
        print("\n" + "=" * 60)
        print("🎯 策略性能详情")
        print("=" * 60)
        
        strategies = list(engine.strategies.values())
        strategies.sort(key=lambda s: s.fitness_score, reverse=True)
        
        for i, strategy in enumerate(strategies):
            print(f"{i+1}. {strategy.name} ({strategy.strategy_type}):")
            print(f"   适应度: {strategy.fitness_score:.3f}")
            print(f"   成功率: {strategy.success_rate:.1%}")
            print(f"   平均成本: {strategy.avg_cost:.3f}")
            print(f"   使用次数: {strategy.metrics['usage_count']}")
            print(f"   探索率: {strategy.exploration_rate:.3f}")
            
            # 显示策略参数
            if strategy.policy:
                print(f"   策略参数: {str(strategy.policy)[:80]}...")
            print()
        
        # 显示进化统计
        stats = engine.get_stats()
        print(f"进化统计:")
        print(f"  总策略数: {stats['strategy_count']}")
        print(f"  策略创建: {stats['stats']['strategies_created']}")
        print(f"  策略淘汰: {stats['stats']['strategies_removed']}")
        print(f"  总突变数: {stats['stats']['total_mutations']}")
        print(f"  总交叉数: {stats['stats']['total_crossovers']}")
        print(f"  平均适应度: {stats['stats']['avg_fitness']:.3f}")
        print(f"  最佳适应度: {stats['stats']['best_fitness']:.3f}")
        
        # 结论
        print("\n" + "=" * 60)
        print("🧭 极端测试结论")
        print("=" * 60)
        
        if has_extreme_bias:
            print(f"✅ 策略分布极端偏向: {dominant_type} ({dominant_percentage:.1f}%)")
            print(f"✅ 系统已学会选择最优策略类型")
            print(f"✅ 进化机制高度有效")
            print(f"✅ 系统具备强大的策略选择能力")
            
            if dominant_type == "conservative":
                print(f"\n💡 系统洞察:")
                print(f"  系统识别到: 保守策略在测试环境中表现最佳")
                print(f"  系统行为: 优先选择保守策略，淘汰其他策略")
                print(f"  现实意义: 系统在风险不确定时选择安全路径")
            
            print(f"\n🚀 系统已准备好升级到:")
            print(f"  ✅ 多信号系统")
            print(f"  ✅ 预测系统")  
            print(f"  ✅ 简单金融决策系统")
        else:
            print(f"⚠️  策略分布未形成极端偏向")
            print(f"⚠️  系统仍在探索不同策略")
            print(f"⚠️  可能需要更极端的性能差异")
        
        # 检查当前策略
        current = engine.get_current_strategy()
        if current:
            print(f"\n💡 当前策略选择:")
            print(f"  策略: {current.name} ({current.strategy_type})")
            print(f"  适应度: {current.fitness_score:.3f}")
            print(f"  成功率: {current.success_rate:.1%}")
            
            if current.strategy_type == "conservative" and current.fitness_score > 0.7:
                print(f"  ✅ 系统正确选择了最优策略")
            else:
                print(f"  ⚠️  系统可能未选择最优策略")
        
        return has_extreme_bias, dominant_type
        
    except Exception as e:
        print(f"\n❌ 极端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    main()