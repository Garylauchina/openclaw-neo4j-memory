#!/usr/bin/env python3
"""
Strategy Evolution - 现实驱动版
核心：real_success 成为核心指标，ARQS 不再主导
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime
import random
import copy

@dataclass
class Strategy:
    """策略结构升级"""
    
    def __init__(self, name: str, strategy_type: str):
        self.name = name
        self.strategy_type = strategy_type
        self.id = f"{strategy_type}_{name}_{int(time.time())}"
        
        # 策略参数
        self.policy: Dict[str, Any] = {}
        
        # 探索率
        self.exploration_rate = 0.1
        self.min_exploration_rate = 0.05
        self.max_exploration_rate = 0.3
        
        # 现实指标
        self.metrics = {
            "arqs": [],          # ARQS分数历史
            "real_success": [],  # ❗ 真实成功率历史
            "cost": [],          # 成本历史
            "latency": [],       # 延迟历史
            "usage_count": 0     # 使用次数
        }
        
        # 进化历史
        self.evolution_history: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # 性能指标
        self.fitness_score = 0.0
        self.success_rate = 0.0
        self.avg_cost = 0.0
        self.avg_latency = 0.0
    
    def update_policy(self, policy_updates: Dict[str, Any]):
        """更新策略参数"""
        self.policy.update(policy_updates)
        self.last_updated = datetime.now()
    
    def add_metric(self, arqs_score: float, real_success: bool, 
                  cost: float, latency_ms: float):
        """添加指标数据"""
        self.metrics["arqs"].append(arqs_score)
        self.metrics["real_success"].append(1.0 if real_success else 0.0)
        self.metrics["cost"].append(cost)
        self.metrics["latency"].append(latency_ms)
        self.metrics["usage_count"] += 1
        
        # 更新性能指标
        self._update_performance_metrics()
        
        # 记录进化历史
        self.evolution_history.append({
            "timestamp": datetime.now().isoformat(),
            "arqs_score": arqs_score,
            "real_success": real_success,
            "cost": cost,
            "latency_ms": latency_ms,
            "fitness_score": self.fitness_score
        })
    
    def _update_performance_metrics(self):
        """更新性能指标"""
        if not self.metrics["usage_count"]:
            return
        
        # 计算成功率
        if self.metrics["real_success"]:
            self.success_rate = sum(self.metrics["real_success"]) / len(self.metrics["real_success"])
        
        # 计算平均成本
        if self.metrics["cost"]:
            self.avg_cost = sum(self.metrics["cost"]) / len(self.metrics["cost"])
        
        # 计算平均延迟
        if self.metrics["latency"]:
            self.avg_latency = sum(self.metrics["latency"]) / len(self.metrics["latency"])
        
        # 计算适应度分数
        self.fitness_score = self._calculate_fitness()
    
    def _calculate_fitness(self) -> float:
        """计算适应度分数（必须改）"""
        
        # ❗ Fitness公式（必须改）
        # 之前：主要依赖ARQS
        # 现在：real_success 成为核心指标
        
        if not self.metrics["usage_count"]:
            return 0.0
        
        # 计算各组件
        avg_arqs = sum(self.metrics["arqs"]) / len(self.metrics["arqs"]) if self.metrics["arqs"] else 0.0
        avg_real_success = self.success_rate
        avg_cost = self.avg_cost
        
        # ❗ 新公式：real_success 权重最高
        fitness = (
            0.4 * avg_real_success +   # ❗ 真实成功率权重40%
            0.4 * avg_arqs +           # ARQS权重40%
            0.2 * (1.0 - min(1.0, avg_cost * 2))  # 成本惩罚（成本越高，适应度越低）
        )
        
        return max(0.0, min(1.0, fitness))
    
    def adjust_exploration_rate(self, success_rate: float):
        """调整探索率"""
        # 成功率低时增加探索
        if success_rate < 0.3:
            self.exploration_rate = min(
                self.max_exploration_rate,
                self.exploration_rate + 0.05
            )
        # 成功率高时减少探索
        elif success_rate > 0.7:
            self.exploration_rate = max(
                self.min_exploration_rate,
                self.exploration_rate - 0.03
            )
        
        # 确保在范围内
        self.exploration_rate = max(
            self.min_exploration_rate,
            min(self.max_exploration_rate, self.exploration_rate)
        )
    
    def should_explore(self) -> bool:
        """是否应该探索"""
        return random.random() < self.exploration_rate
    
    def mutate(self, mutation_rate: float = 0.1):
        """突变策略"""
        old_policy = copy.deepcopy(self.policy)
        
        for key in self.policy:
            if random.random() < mutation_rate:
                value = self.policy[key]
                
                if isinstance(value, (int, float)):
                    # 数值突变
                    mutation = random.uniform(-0.2, 0.2)
                    if isinstance(value, int):
                        self.policy[key] = max(1, int(value * (1 + mutation)))
                    else:
                        self.policy[key] = max(0.0, value * (1 + mutation))
                
                elif isinstance(value, bool):
                    # 布尔值突变
                    self.policy[key] = not value
        
        # 记录突变
        self.evolution_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "mutation",
            "old_policy": old_policy,
            "new_policy": copy.deepcopy(self.policy),
            "mutation_rate": mutation_rate
        })
        
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "strategy_type": self.strategy_type,
            "policy": self.policy,
            "exploration_rate": self.exploration_rate,
            "performance": {
                "fitness_score": self.fitness_score,
                "success_rate": self.success_rate,
                "avg_cost": self.avg_cost,
                "avg_latency": self.avg_latency,
                "usage_count": self.metrics["usage_count"]
            },
            "metrics_summary": {
                "arqs_count": len(self.metrics["arqs"]),
                "real_success_count": len(self.metrics["real_success"]),
                "avg_arqs": sum(self.metrics["arqs"]) / len(self.metrics["arqs"]) if self.metrics["arqs"] else 0.0,
                "avg_real_success": self.success_rate
            },
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "last_updated": self.last_updated.isoformat(),
                "evolution_steps": len(self.evolution_history)
            }
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.strategy_type,
            "fitness": self.fitness_score,
            "success_rate": self.success_rate,
            "usage_count": self.metrics["usage_count"],
            "exploration_rate": self.exploration_rate
        }

class StrategyEvolutionEngine:
    """策略进化引擎"""
    
    def __init__(self):
        # 策略池
        self.strategies: Dict[str, Strategy] = {}
        
        # 策略类型配置
        self.strategy_templates = {
            "conservative": {
                "attention_top_k": 5,
                "planning_depth": 2,
                "risk_tolerance": 0.1,
                "validation_threshold": 0.7
            },
            "balanced": {
                "attention_top_k": 10,
                "planning_depth": 3,
                "risk_tolerance": 0.3,
                "validation_threshold": 0.6
            },
            "exploratory": {
                "attention_top_k": 15,
                "planning_depth": 4,
                "risk_tolerance": 0.5,
                "validation_threshold": 0.5
            },
            "aggressive": {
                "attention_top_k": 20,
                "planning_depth": 5,
                "risk_tolerance": 0.7,
                "validation_threshold": 0.4
            }
        }
        
        # 进化参数
        self.mutation_rate = 0.1
        self.crossover_rate = 0.3
        self.selection_pressure = 0.7  # 选择压力（越高越倾向于优秀策略）
        
        # 当前策略
        self.current_strategy_id: Optional[str] = None
        
        # 统计信息
        self.stats = {
            "total_strategies": 0,
            "strategies_created": 0,
            "strategies_removed": 0,
            "total_mutations": 0,
            "total_crossovers": 0,
            "avg_fitness": 0.0,
            "best_fitness": 0.0
        }
        
        # 初始化策略池
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """初始化策略池"""
        for strategy_type, policy in self.strategy_templates.items():
            strategy = Strategy(
                name=f"{strategy_type}_strategy",
                strategy_type=strategy_type
            )
            strategy.update_policy(policy)
            
            self.strategies[strategy.id] = strategy
            self.stats["total_strategies"] += 1
            self.stats["strategies_created"] += 1
        
        # 设置默认策略
        if self.strategies:
            self.current_strategy_id = list(self.strategies.keys())[0]
    
    def select_strategy(self, context: Dict[str, Any]) -> Optional[Strategy]:
        """选择策略"""
        if not self.strategies:
            return None
        
        # 获取上下文信息
        task_type = context.get("task_type", "general")
        uncertainty = context.get("uncertainty", 0.5)
        risk_level = context.get("risk_level", "medium")
        
        # 策略选择逻辑
        if uncertainty > 0.7:
            # 高不确定性：选择探索性策略
            strategy_type = "exploratory"
        elif risk_level in ["high", "critical"]:
            # 高风险：选择保守策略
            strategy_type = "conservative"
        elif task_type in ["analysis", "research"]:
            # 分析任务：选择平衡策略
            strategy_type = "balanced"
        else:
            # 默认：选择平衡策略
            strategy_type = "balanced"
        
        # 查找匹配的策略
        matching_strategies = []
        for strategy in self.strategies.values():
            if strategy.strategy_type == strategy_type:
                matching_strategies.append(strategy)
        
        if not matching_strategies:
            # 没有匹配的策略，返回当前策略
            return self.get_current_strategy()
        
        # 根据适应度选择（带探索）
        if random.random() < 0.2:  # 20%探索
            # 随机选择
            selected = random.choice(matching_strategies)
        else:
            # 根据适应度选择
            matching_strategies.sort(key=lambda s: s.fitness_score, reverse=True)
            selected = matching_strategies[0]
        
        # 更新当前策略
        self.current_strategy_id = selected.id
        
        return selected
    
    def get_current_strategy(self) -> Optional[Strategy]:
        """获取当前策略"""
        if self.current_strategy_id and self.current_strategy_id in self.strategies:
            return self.strategies[self.current_strategy_id]
        return None
    
    def update_strategy_performance(self, strategy_id: str,
                                  arqs_score: float,
                                  real_success: bool,
                                  cost: float,
                                  latency_ms: float):
        """更新策略性能"""
        if strategy_id not in self.strategies:
            return False
        
        strategy = self.strategies[strategy_id]
        strategy.add_metric(arqs_score, real_success, cost, latency_ms)
        
        # 调整探索率
        strategy.adjust_exploration_rate(strategy.success_rate)
        
        # 更新统计
        self._update_stats()
        
        return True
    
    def evolve(self):
        """进化策略"""
        if len(self.strategies) < 2:
            return  # 需要至少2个策略才能进化
        
        # 1. 选择
        selected_strategies = self._selection()
        
        # 2. 交叉
        if random.random() < self.crossover_rate and len(selected_strategies) >= 2:
            self._crossover(selected_strategies)
            self.stats["total_crossovers"] += 1
        
        # 3. 突变
        for strategy in selected_strategies:
            if random.random() < self.mutation_rate:
                strategy.mutate(self.mutation_rate)
                self.stats["total_mutations"] += 1
        
        # 4. 淘汰
        self._elimination()
        
        # 更新统计
        self._update_stats()
    
    def _selection(self) -> List[Strategy]:
        """选择策略"""
        strategies = list(self.strategies.values())
        
        # 按适应度排序
        strategies.sort(key=lambda s: s.fitness_score, reverse=True)
        
        # 选择前N个策略
        n = max(2, int(len(strategies) * self.selection_pressure))
        selected = strategies[:n]
        
        return selected
    
    def _crossover(self, parents: List[Strategy]):
        """交叉（生成新策略）"""
        if len(parents) < 2:
            return
        
        # 选择两个父代
        parent1, parent2 = random.sample(parents, 2)
        
        # 创建新策略
        child_name = f"hybrid_{parent1.strategy_type}_{parent2.strategy_type}"
        child = Strategy(
            name=child_name,
            strategy_type="hybrid"
        )
        
        # 交叉策略参数
        child_policy = {}
        for key in parent1.policy:
            if key in parent2.policy:
                # 随机选择父代的参数
                if random.random() < 0.5:
                    child_policy[key] = parent1.policy[key]
                else:
                    child_policy[key] = parent2.policy[key]
            else:
                child_policy[key] = parent1.policy[key]
        
        # 添加父代没有的参数
        for key in parent2.policy:
            if key not in child_policy:
                child_policy[key] = parent2.policy[key]
        
        child.update_policy(child_policy)
        
        # 设置探索率（取平均值）
        child.exploration_rate = (parent1.exploration_rate + parent2.exploration_rate) / 2
        
        # 添加到策略池
        self.strategies[child.id] = child
        self.stats["total_strategies"] += 1
        self.stats["strategies_created"] += 1
        
        # 记录交叉历史
        child.evolution_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "crossover",
            "parent1": parent1.id,
            "parent2": parent2.id,
            "child_policy": child_policy
        })
    
    def _elimination(self):
        """淘汰策略"""
        if len(self.strategies) <= 5:
            return  # 保持最小策略数量
        
        strategies = list(self.strategies.values())
        
        # 按适应度排序
        strategies.sort(key=lambda s: s.fitness_score)
        
        # 淘汰适应度最低的策略
        to_remove = strategies[0]
        
        # 确保不删除当前策略
        if to_remove.id == self.current_strategy_id:
            if len(strategies) > 1:
                to_remove = strategies[1]
            else:
                return
        
        # 删除策略
        del self.strategies[to_remove.id]
        self.stats["total_strategies"] -= 1
        self.stats["strategies_removed"] += 1
        
        # 如果当前策略被删除，选择新的当前策略
        if self.current_strategy_id == to_remove.id:
            if self.strategies:
                self.current_strategy_id = list(self.strategies.keys())[0]
            else:
                self.current_strategy_id = None
    
    def _update_stats(self):
        """更新统计信息"""
        if not self.strategies:
            self.stats["avg_fitness"] = 0.0
            self.stats["best_fitness"] = 0.0
            return
        
        # 计算平均适应度
        total_fitness = sum(s.fitness_score for s in self.strategies.values())
        self.stats["avg_fitness"] = total_fitness / len(self.strategies)
        
        # 计算最佳适应度
        best_fitness = max(s.fitness_score for s in self.strategies.values())
        self.stats["best_fitness"] = best_fitness
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "stats": self.stats,
            "current_strategy": (
                self.strategies[self.current_strategy_id].get_summary()
                if self.current_strategy_id and self.current_strategy_id in self.strategies
                else None
            ),
            "strategy_count": len(self.strategies),
            "strategy_types": {
                strategy_type: sum(1 for s in self.strategies.values() if s.strategy_type == strategy_type)
                for strategy_type in set(s.strategy_type for s in self.strategies.values())
            }
        }
    
    def reset(self):
        """重置进化引擎"""
        self.strategies = {}
        self.current_strategy_id = None
        
        self.stats = {
            "total_strategies": 0,
            "strategies_created": 0,
            "strategies_removed": 0,
            "total_mutations": 0,
            "total_crossovers": 0,
            "avg_fitness": 0.0,
            "best_fitness": 0.0
        }
        
        # 重新初始化
        self._initialize_strategies()
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        
        print(f"   🧬 策略进化引擎状态:")
        print(f"      统计:")
        print(f"        总策略数: {stats['strategy_count']}")
        print(f"        策略创建: {stats['stats']['strategies_created']}")
        print(f"        策略淘汰: {stats['stats']['strategies_removed']}")
        print(f"        总突变数: {stats['stats']['total_mutations']}")
        print(f"        总交叉数: {stats['stats']['total_crossovers']}")
        print(f"        平均适应度: {stats['stats']['avg_fitness']:.3f}")
        print(f"        最佳适应度: {stats['stats']['best_fitness']:.3f}")
        
        print(f"      策略类型分布:")
        for strategy_type, count in stats['strategy_types'].items():
            print(f"        {strategy_type}: {count}")
        
        if stats['current_strategy']:
            current = stats['current_strategy']
            print(f"      当前策略:")
            print(f"        名称: {current['name']}")
            print(f"        类型: {current['type']}")
            print(f"        适应度: {current['fitness']:.3f}")
            print(f"        成功率: {current['success_rate']:.1%}")
            print(f"        使用次数: {current['usage_count']}")
            print(f"        探索率: {current['exploration_rate']:.3f}")
        
        # 显示前3个策略
        strategies = list(self.strategies.values())
        strategies.sort(key=lambda s: s.fitness_score, reverse=True)
        
        if strategies:
            print(f"      最佳策略:")
            for i, strategy in enumerate(strategies[:3]):
                print(f"        {i+1}. {strategy.name} (适应度: {strategy.fitness_score:.3f}, "
                      f"成功率: {strategy.success_rate:.1%}, 使用: {strategy.metrics['usage_count']})")