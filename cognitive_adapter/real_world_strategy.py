#!/usr/bin/env python3
"""
Real World Strategy - 现实世界驱动的策略进化
核心：fitness必须包含real_world_accuracy，并奖励依赖现实的策略
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import random

class RealWorldStrategy:
    """现实世界策略"""
    
    def __init__(self, 
                 name: str,
                 strategy_type: str,
                 uses_real_data: bool = False):
        self.name = name
        self.strategy_type = strategy_type
        self.uses_real_data = uses_real_data  # ❗ 关键：是否依赖现实数据
        
        # 性能指标
        self.metrics = {
            "real_world_accuracy": [],  # ❗ 现实世界准确率
            "success_rate": [],         # 成功率
            "cost": [],                 # 成本
            "stability": [],            # 稳定性
            "usage_count": 0
        }
        
        # 进化历史
        self.evolution_history: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # 适应度分数
        self.fitness_score = 0.0
        self.real_world_bonus = 0.0  # 现实数据奖励
        
    def add_performance(self,
                       real_world_accuracy: float,
                       success_rate: float,
                       cost: float,
                       stability: float = 0.5):
        """添加性能数据"""
        self.metrics["real_world_accuracy"].append(real_world_accuracy)
        self.metrics["success_rate"].append(success_rate)
        self.metrics["cost"].append(cost)
        self.metrics["stability"].append(stability)
        self.metrics["usage_count"] += 1
        
        # 更新适应度
        self._update_fitness()
        
        # 记录历史
        self.evolution_history.append({
            "timestamp": datetime.now().isoformat(),
            "real_world_accuracy": real_world_accuracy,
            "success_rate": success_rate,
            "cost": cost,
            "stability": stability,
            "fitness": self.fitness_score,
            "real_world_bonus": self.real_world_bonus
        })
        
        self.last_updated = datetime.now()
    
    def _update_fitness(self):
        """更新适应度分数"""
        if self.metrics["usage_count"] == 0:
            self.fitness_score = 0.0
            return
        
        # 计算平均指标
        avg_accuracy = self._safe_average(self.metrics["real_world_accuracy"])
        avg_success = self._safe_average(self.metrics["success_rate"])
        avg_cost = self._safe_average(self.metrics["cost"])
        avg_stability = self._safe_average(self.metrics["stability"])
        
        # ❗ 新适应度公式（用户提供）
        base_fitness = (
            0.5 * avg_accuracy +      # 现实世界准确率权重50%
            0.2 * avg_success +       # 成功率权重20%
            0.2 * (1.0 - min(1.0, avg_cost * 2)) +  # 成本权重20%（成本越高，适应度越低）
            0.1 * avg_stability       # 稳定性权重10%
        )
        
        # ❗ 关键：奖励依赖现实数据的策略
        self.real_world_bonus = 0.1 if self.uses_real_data else 0.0
        
        # 最终适应度
        self.fitness_score = min(1.0, max(0.0, base_fitness + self.real_world_bonus))
    
    def _safe_average(self, values: List[float]) -> float:
        """安全计算平均值"""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "name": self.name,
            "type": self.strategy_type,
            "uses_real_data": self.uses_real_data,
            "fitness": self.fitness_score,
            "real_world_bonus": self.real_world_bonus,
            "performance": {
                "avg_accuracy": self._safe_average(self.metrics["real_world_accuracy"]),
                "avg_success": self._safe_average(self.metrics["success_rate"]),
                "avg_cost": self._safe_average(self.metrics["cost"]),
                "usage_count": self.metrics["usage_count"]
            },
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "last_updated": self.last_updated.isoformat(),
                "evolution_steps": len(self.evolution_history)
            }
        }

class RealWorldStrategyEngine:
    """现实世界策略引擎"""
    
    def __init__(self):
        self.strategies: Dict[str, RealWorldStrategy] = {}
        
        # 策略模板
        self.strategy_templates = {
            "reality_greedy": {
                "uses_real_data": True,
                "description": "贪婪策略（依赖实时数据）"
            },
            "reality_trend": {
                "uses_real_data": True,
                "description": "趋势策略（依赖实时数据+历史）"
            },
            "simulation_greedy": {
                "uses_real_data": False,
                "description": "模拟贪婪策略（不依赖实时数据）"
            },
            "simulation_trend": {
                "uses_real_data": False,
                "description": "模拟趋势策略（不依赖实时数据）"
            },
            "hybrid": {
                "uses_real_data": True,
                "description": "混合策略（实时+模拟）"
            }
        }
        
        # 进化参数
        self.mutation_rate = 0.1
        self.crossover_rate = 0.3
        self.selection_pressure = 0.7
        
        # 统计
        self.stats = {
            "total_strategies": 0,
            "strategies_created": 0,
            "strategies_removed": 0,
            "reality_based_wins": 0,
            "simulation_based_wins": 0,
            "avg_fitness": 0.0,
            "avg_real_world_accuracy": 0.0
        }
        
        # 初始化策略
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """初始化策略"""
        for strategy_type, config in self.strategy_templates.items():
            strategy = RealWorldStrategy(
                name=f"{strategy_type}_strategy",
                strategy_type=strategy_type,
                uses_real_data=config["uses_real_data"]
            )
            
            self.strategies[strategy.name] = strategy
            self.stats["total_strategies"] += 1
            self.stats["strategies_created"] += 1
    
    def update_strategy(self,
                       strategy_name: str,
                       real_world_accuracy: float,
                       success_rate: float,
                       cost: float,
                       stability: float = 0.5) -> bool:
        """更新策略性能"""
        if strategy_name not in self.strategies:
            return False
        
        strategy = self.strategies[strategy_name]
        strategy.add_performance(real_world_accuracy, success_rate, cost, stability)
        
        # 更新统计
        self._update_stats()
        
        # 检查现实数据策略是否领先
        if strategy.uses_real_data and strategy.fitness_score > 0.7:
            self.stats["reality_based_wins"] += 1
        
        return True
    
    def select_best_strategy(self, context: Optional[Dict[str, Any]] = None) -> Optional[RealWorldStrategy]:
        """选择最佳策略"""
        if not self.strategies:
            return None
        
        # 根据上下文选择
        requires_real_data = context.get("requires_real_data", False) if context else False
        
        # 筛选候选策略
        candidates = []
        for strategy in self.strategies.values():
            if requires_real_data and not strategy.uses_real_data:
                continue  # 需要现实数据但策略不提供
            
            candidates.append(strategy)
        
        if not candidates:
            # 如果没有符合条件的，返回所有策略中最好的
            candidates = list(self.strategies.values())
        
        # 按适应度排序
        candidates.sort(key=lambda s: s.fitness_score, reverse=True)
        
        # 20%探索，80%利用
        if random.random() < 0.2:
            # 探索：随机选择（偏向现实数据策略）
            reality_based = [s for s in candidates if s.uses_real_data]
            if reality_based and random.random() < 0.7:
                return random.choice(reality_based)
            else:
                return random.choice(candidates)
        else:
            # 利用：选择最好的
            return candidates[0]
    
    def evolve(self):
        """进化策略"""
        if len(self.strategies) < 2:
            return
        
        # 1. 选择
        selected = self._selection()
        
        # 2. 交叉
        if random.random() < self.crossover_rate and len(selected) >= 2:
            self._crossover(selected)
        
        # 3. 突变
        for strategy in selected:
            if random.random() < self.mutation_rate:
                self._mutate(strategy)
        
        # 4. 淘汰
        self._elimination()
        
        # 更新统计
        self._update_stats()
    
    def _selection(self) -> List[RealWorldStrategy]:
        """选择策略"""
        strategies = list(self.strategies.values())
        strategies.sort(key=lambda s: s.fitness_score, reverse=True)
        
        # ❗ 关键：现实数据策略有选择优势
        reality_based = [s for s in strategies if s.uses_real_data]
        if reality_based:
            # 现实数据策略额外获得20%的选择优势
            adjusted_scores = []
            for s in strategies:
                advantage = 0.2 if s.uses_real_data else 0.0
                adjusted_scores.append(s.fitness_score + advantage)
            
            # 加权随机选择
            total_score = sum(adjusted_scores)
            if total_score > 0:
                probabilities = [score/total_score for score in adjusted_scores]
                selected = random.choices(strategies, weights=probabilities, k=min(3, len(strategies)))
                return selected
        
        # 备用：简单选择前N个
        n = max(2, int(len(strategies) * self.selection_pressure))
        return strategies[:n]
    
    def _crossover(self, parents: List[RealWorldStrategy]):
        """交叉（生成新策略）"""
        if len(parents) < 2:
            return
        
        parent1, parent2 = random.sample(parents, 2)
        
        # 创建新策略
        child_name = f"evolved_{parent1.name}_{parent2.name}"
        
        # ❗ 关键：新策略是否使用现实数据（从父代继承）
        uses_real_data = parent1.uses_real_data or parent2.uses_real_data
        
        child = RealWorldStrategy(
            name=child_name,
            strategy_type="evolved",
            uses_real_data=uses_real_data
        )
        
        # 添加到策略池
        self.strategies[child.name] = child
        self.stats["total_strategies"] += 1
        self.stats["strategies_created"] += 1
    
    def _mutate(self, strategy: RealWorldStrategy):
        """突变策略"""
        # ❗ 关键突变：可能改变现实数据依赖
        if random.random() < 0.3:
            strategy.uses_real_data = not strategy.uses_real_data
            print(f"     🧬 策略突变: {strategy.name} 现实数据依赖 → {strategy.uses_real_data}")
    
    def _elimination(self):
        """淘汰策略"""
        if len(self.strategies) <= 3:
            return  # 保持最小策略数量
        
        strategies = list(self.strategies.values())
        strategies.sort(key=lambda s: s.fitness_score)  # 按适应度升序
        
        # ❗ 关键：保护现实数据策略（即使适应度较低）
        to_remove = []
        for strategy in strategies:
            if strategy.uses_real_data:
                # 现实数据策略有保护，需要更低的适应度才被淘汰
                if strategy.fitness_score < 0.2:  # 阈值更低
                    to_remove.append(strategy)
            else:
                # 模拟策略更容易被淘汰
                if strategy.fitness_score < 0.3:  # 阈值更高
                    to_remove.append(strategy)
        
        # 淘汰策略
        for strategy in to_remove[:2]:  # 最多淘汰2个
            if strategy.name in self.strategies:
                del self.strategies[strategy.name]
                self.stats["total_strategies"] -= 1
                self.stats["strategies_removed"] += 1
                print(f"     🗑️  淘汰策略: {strategy.name} (适应度: {strategy.fitness_score:.3f})")
    
    def _update_stats(self):
        """更新统计信息"""
        if not self.strategies:
            self.stats["avg_fitness"] = 0.0
            self.stats["avg_real_world_accuracy"] = 0.0
            return
        
        # 计算平均适应度
        total_fitness = sum(s.fitness_score for s in self.strategies.values())
        self.stats["avg_fitness"] = total_fitness / len(self.strategies)
        
        # 计算平均现实世界准确率
        all_accuracies = []
        for strategy in self.strategies.values():
            if strategy.metrics["real_world_accuracy"]:
                all_accuracies.extend(strategy.metrics["real_world_accuracy"])
        
        if all_accuracies:
            self.stats["avg_real_world_accuracy"] = sum(all_accuracies) / len(all_accuracies)
        else:
            self.stats["avg_real_world_accuracy"] = 0.0
    
    def get_report(self) -> Dict[str, Any]:
        """获取报告"""
        # 策略排名
        strategies = list(self.strategies.values())
        strategies.sort(key=lambda s: s.fitness_score, reverse=True)
        
        ranked_strategies = []
        for i, strategy in enumerate(strategies[:5]):  # 只显示前5个
            summary = strategy.get_summary()
            summary["rank"] = i + 1
            ranked_strategies.append(summary)
        
        # 现实数据 vs 模拟数据对比
        reality_based = [s for s in strategies if s.uses_real_data]
        simulation_based = [s for s in strategies if not s.uses_real_data]
        
        reality_avg_fitness = sum(s.fitness_score for s in reality_based) / len(reality_based) if reality_based else 0.0
        simulation_avg_fitness = sum(s.fitness_score for s in simulation_based) / len(simulation_based) if simulation_based else 0.0
        
        return {
            "stats": self.stats,
            "strategy_comparison": {
                "reality_based": {
                    "count": len(reality_based),
                    "avg_fitness": reality_avg_fitness,
                    "best_strategy": reality_based[0].name if reality_based else None
                },
                "simulation_based": {
                    "count": len(simulation_based),
                    "avg_fitness": simulation_avg_fitness,
                    "best_strategy": simulation_based[0].name if simulation_based else None
                },
                "fitness_gap": reality_avg_fitness - simulation_avg_fitness
            },
            "top_strategies": ranked_strategies,
            "evolution_status": {
                "total_generations": self.stats["strategies_created"] - 4,  # 减去初始4个
                "current_diversity": len(self.strategies),
                "dominant_type": "reality_based" if reality_avg_fitness > simulation_avg_fitness else "simulation_based"
            }
        }
    
    def print_report(self):
        """打印报告"""
        report = self.get_report()
        
        print(f"\n📊 现实世界策略引擎报告:")
        print(f"   统计:")
        print(f"     总策略数: {report['stats']['total_strategies']}")
        print(f"     策略创建: {report['stats']['strategies_created']}")
        print(f"     策略淘汰: {report['stats']['strategies_removed']}")
        print(f"     现实数据获胜: {report['stats']['reality_based_wins']}")
        print(f"     模拟数据获胜: {report['stats']['simulation_based_wins']}")
        print(f"     平均适应度: {report['stats']['avg_fitness']:.3f}")
        print(f"     平均现实准确率: {report['stats']['avg_real_world_accuracy']:.3f}")
        
        comparison = report["strategy_comparison"]
        print(f"   策略对比:")
        print(f"     现实数据策略: {comparison['reality_based']['count']}个, "
              f"平均适应度: {comparison['reality_based']['avg_fitness']:.3f}")
        print(f"     模拟数据策略: {comparison['simulation_based']['count']}个, "
              f"平均适应度: {comparison['simulation_based']['avg_fitness']:.3f}")
        print(f"     适应度差距: {comparison['fitness_gap']:+.3f} "
              f"({'现实领先' if comparison['fitness_gap'] > 0 else '模拟领先'})")
        
        print(f"   进化状态:")
        print(f"     总代数: {report['evolution_status']['total_generations']}")
        print(f"     当前多样性: {report['evolution_status']['current_diversity']}")
        print(f"     主导类型: {report['evolution_status']['dominant_type']}")
        
        if report["top_strategies"]:
            print(f"   顶级策略:")
            for strategy in report["top_strategies"][:3]:  # 只显示前3个
                reality_flag = "🌍" if strategy["uses_real_data"] else "🧠"
                print(f"     {strategy['rank']}. {reality_flag} {strategy['name']} "
                      f"(适应度: {strategy['fitness']:.3f}, "
                      f"现实奖励: {strategy['real_world_bonus']:.2f}, "
                      f"使用次数: {strategy['performance']['usage_count']})")

def test_real_world_strategy():
    """测试现实世界策略引擎"""
    print("🧪 测试 RealWorldStrategyEngine...")
    
    engine = RealWorldStrategyEngine()
    
    # 模拟多轮性能更新
    print(f"\n🔄 模拟策略性能更新...")
    
    for round_num in range(10):
        print(f"\n轮次 {round_num + 1}:")
        
        # 为每个策略生成性能数据
        for strategy_name, strategy in list(engine.strategies.items())[:3]:  # 只测试前3个
            # 生成性能数据（现实数据策略通常更准确）
            if strategy.uses_real_data:
                real_world_accuracy = random.uniform(0.7, 0.95)  # 高准确率
                success_rate = random.uniform(0.6, 0.9)
            else:
                real_world_accuracy = random.uniform(0.4, 0.7)  # 低准确率
                success_rate = random.uniform(0.4, 0.7)
            
            cost = random.uniform(0.1, 0.3)
            stability = random.uniform(0.5, 0.9)
            
            engine.update_strategy(
                strategy_name,
                real_world_accuracy,
                success_rate,
                cost,
                stability
            )
            
            print(f"   {strategy_name}: 准确率={real_world_accuracy:.3f}, "
                  f"成功率={success_rate:.3f}, 成本={cost:.3f}")
        
        # 进化
        if round_num % 3 == 2:  # 每3轮进化一次
            print(f"   🧬 进化策略...")
            engine.evolve()
    
    # 显示最终报告
    print(f"\n📋 最终报告:")
    engine.print_report()
    
    # 测试策略选择
    print(f"\n🎯 测试策略选择:")
    
    test_contexts = [
        {"requires_real_data": True, "description": "需要现实数据"},
        {"requires_real_data": False, "description": "不需要现实数据"},
        {"description": "无要求"}
    ]
    
    for context in test_contexts:
        best_strategy = engine.select_best_strategy(context)
        if best_strategy:
            reality_flag = "🌍" if best_strategy.uses_real_data else "🧠"
            print(f"   {context['description']}: 选择 {reality_flag} {best_strategy.name} "
                  f"(适应度: {best_strategy.fitness_score:.3f})")
    
    return engine

if __name__ == "__main__":
    test_real_world_strategy()