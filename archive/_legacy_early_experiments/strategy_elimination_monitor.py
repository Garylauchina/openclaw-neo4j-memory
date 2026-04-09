#!/usr/bin/env python3
"""
策略淘汰监测器 - 开始真正的"进化"阶段
实现渐进淘汰机制，基于性能阈值淘汰低效策略
"""

import os
import sys
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# 添加路径
workspace_dir = os.path.expanduser("~/.openclaw/workspace")
sys.path.insert(0, workspace_dir)

class StrategyEliminationMonitor:
    """策略淘汰监测器"""
    
    def __init__(self, strategy_engine=None):
        print("\n" + "=" * 70)
        print("⚰️ STRATEGY ELIMINATION MONITOR - 策略淘汰监测器")
        print("=" * 70)
        
        # 加载策略引擎
        self.strategy_engine = strategy_engine
        if not self.strategy_engine:
            try:
                from cognitive_adapter.real_world_strategy import RealWorldStrategyEngine
                self.strategy_engine = RealWorldStrategyEngine()
                print("✅ 策略引擎已加载")
            except Exception as e:
                print(f"❌ 策略引擎加载失败: {e}")
                return
        
        # 淘汰配置
        self.elimination_config = {
            # 淘汰阈值
            "usage_threshold": 0.05,      # 使用率<5%
            "fitness_threshold_ratio": 0.8,  # Fitness<平均的80%
            "composite_score_threshold": 0.3,  # 综合评分阈值
            
            # 淘汰规则
            "min_strategies": 3,          # 最少保留策略数
            "elimination_batch_size": 1,  # 每次最多淘汰策略数
            "grace_period_batches": 3,    # 宽限期（批次）
            
            # 评分权重
            "usage_weight": 0.4,
            "fitness_weight": 0.6,
            
            # 淘汰模式
            "elimination_mode": "soft",   # soft:标记淘汰, hard:实际移除
            "allow_recovery": True,       # 允许淘汰策略恢复
            "recovery_threshold": 0.5,    # 恢复阈值
        }
        
        # 淘汰历史
        self.elimination_history: List[Dict[str, Any]] = []
        self.eliminated_strategies: Dict[str, Dict[str, Any]] = {}  # 淘汰策略记录
        self.monitoring_start_time = datetime.now()
        
        # 性能跟踪
        self.performance_tracking = {
            "total_elimination_checks": 0,
            "strategies_marked_for_elimination": 0,
            "strategies_actually_eliminated": 0,
            "strategies_recovered": 0,
            "avg_time_to_elimination": 0.0
        }
        
        print(f"🎯 淘汰配置:")
        print(f"   使用率阈值: <{self.elimination_config['usage_threshold']:.0%}")
        print(f"   Fitness阈值: <平均的{self.elimination_config['fitness_threshold_ratio']:.0%}")
        print(f"   综合评分阈值: <{self.elimination_config['composite_score_threshold']}")
        print(f"   最少保留策略: {self.elimination_config['min_strategies']}个")
        print(f"   淘汰模式: {self.elimination_config['elimination_mode']}")
        print(f"   允许恢复: {self.elimination_config['allow_recovery']}")
    
    def calculate_composite_score(self, strategy) -> float:
        """
        计算策略综合评分
        
        公式: score = usage_weight * normalized_usage + fitness_weight * normalized_fitness
        """
        # 获取策略使用率
        total_usage = sum(s.metrics.get("usage_count", 0) for s in self.strategy_engine.strategies.values())
        usage_rate = 0.0
        if total_usage > 0:
            usage_rate = strategy.metrics.get("usage_count", 0) / total_usage
        
        # 获取策略Fitness
        fitness = strategy.fitness_score
        
        # 归一化（确保在0-1范围）
        normalized_usage = min(1.0, usage_rate * 10)  # 放大使用率影响
        normalized_fitness = max(0.0, min(1.0, fitness))  # Fitness已在0-1范围
        
        # 计算综合评分
        composite_score = (
            self.elimination_config["usage_weight"] * normalized_usage +
            self.elimination_config["fitness_weight"] * normalized_fitness
        )
        
        return composite_score
    
    def check_elimination_candidates(self) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        检查淘汰候选策略
        
        返回: [(strategy_name, composite_score, elimination_reason), ...]
        """
        self.performance_tracking["total_elimination_checks"] += 1
        
        strategies = list(self.strategy_engine.strategies.values())
        if len(strategies) <= self.elimination_config["min_strategies"]:
            print("   ⚠️  策略数量已达最小值，跳过淘汰检查")
            return []
        
        # 计算平均Fitness
        fitness_values = [s.fitness_score for s in strategies]
        avg_fitness = sum(fitness_values) / len(fitness_values) if fitness_values else 0.0
        
        # 计算总使用次数
        total_usage = sum(s.metrics.get("usage_count", 0) for s in strategies)
        
        candidates = []
        
        for strategy in strategies:
            strategy_name = strategy.name
            
            # 跳过已淘汰策略
            if strategy_name in self.eliminated_strategies:
                continue
            
            # 计算使用率
            usage_rate = 0.0
            if total_usage > 0:
                usage_rate = strategy.metrics.get("usage_count", 0) / total_usage
            
            # 计算综合评分
            composite_score = self.calculate_composite_score(strategy)
            
            # 检查淘汰条件
            elimination_reason = {}
            
            # 条件1: 使用率过低
            if usage_rate < self.elimination_config["usage_threshold"]:
                elimination_reason["low_usage"] = {
                    "usage_rate": usage_rate,
                    "threshold": self.elimination_config["usage_threshold"]
                }
            
            # 条件2: Fitness过低
            fitness_threshold = avg_fitness * self.elimination_config["fitness_threshold_ratio"]
            if strategy.fitness_score < fitness_threshold:
                elimination_reason["low_fitness"] = {
                    "fitness": strategy.fitness_score,
                    "avg_fitness": avg_fitness,
                    "threshold": fitness_threshold
                }
            
            # 条件3: 综合评分过低
            if composite_score < self.elimination_config["composite_score_threshold"]:
                elimination_reason["low_composite_score"] = {
                    "score": composite_score,
                    "threshold": self.elimination_config["composite_score_threshold"]
                }
            
            # 如果满足任何淘汰条件，加入候选列表
            if elimination_reason:
                candidates.append((strategy_name, composite_score, elimination_reason))
        
        # 按综合评分排序（评分越低越可能被淘汰）
        candidates.sort(key=lambda x: x[1])
        
        return candidates
    
    def eliminate_strategy(self, strategy_name: str, elimination_reason: Dict[str, Any]) -> bool:
        """
        淘汰策略
        
        Args:
            strategy_name: 策略名称
            elimination_reason: 淘汰原因
            
        Returns:
            是否成功淘汰
        """
        if strategy_name not in self.strategy_engine.strategies:
            print(f"   ❌ 策略 {strategy_name} 不存在")
            return False
        
        strategy = self.strategy_engine.strategies[strategy_name]
        
        # 检查是否已达最小策略数
        remaining_strategies = len(self.strategy_engine.strategies) - len(self.eliminated_strategies)
        if remaining_strategies <= self.elimination_config["min_strategies"]:
            print(f"   ⚠️  已达最小策略数 ({remaining_strategies})，跳过淘汰 {strategy_name}")
            return False
        
        # 记录淘汰信息
        elimination_record = {
            "strategy_name": strategy_name,
            "strategy_type": "api_based" if strategy.uses_real_data else "heuristic",
            "elimination_time": datetime.now().isoformat(),
            "elimination_reason": elimination_reason,
            "final_stats": {
                "fitness": strategy.fitness_score,
                "usage_count": strategy.metrics.get("usage_count", 0),
                "avg_accuracy": self._safe_average(strategy.metrics.get("real_world_accuracy", [])),
                "avg_cost": self._safe_average(strategy.metrics.get("cost", [])),
                "success_rate": self._safe_average(strategy.metrics.get("success_rate", []))
            },
            "elimination_mode": self.elimination_config["elimination_mode"]
        }
        
        # 根据淘汰模式执行
        if self.elimination_config["elimination_mode"] == "hard":
            # 硬淘汰：实际移除策略
            del self.strategy_engine.strategies[strategy_name]
            elimination_record["action"] = "removed"
            print(f"   ⚰️  硬淘汰: 移除策略 {strategy_name}")
        else:
            # 软淘汰：标记为淘汰但不移除
            self.eliminated_strategies[strategy_name] = elimination_record
            elimination_record["action"] = "marked_for_elimination"
            print(f"   ⚠️  软淘汰: 标记策略 {strategy_name} 为淘汰")
        
        # 记录淘汰历史
        self.elimination_history.append(elimination_record)
        
        # 更新性能跟踪
        self.performance_tracking["strategies_marked_for_elimination"] += 1
        if self.elimination_config["elimination_mode"] == "hard":
            self.performance_tracking["strategies_actually_eliminated"] += 1
        
        print(f"      淘汰原因: {list(elimination_reason.keys())}")
        print(f"      最终Fitness: {strategy.fitness_score:.3f}")
        print(f"      使用次数: {strategy.metrics.get('usage_count', 0)}")
        
        return True
    
    def check_recovery_candidates(self) -> List[str]:
        """
        检查恢复候选策略（被淘汰但可能恢复的策略）
        
        返回: [strategy_name, ...]
        """
        if not self.elimination_config["allow_recovery"]:
            return []
        
        recovery_candidates = []
        
        for strategy_name, elimination_record in self.eliminated_strategies.items():
            # 检查淘汰时间（需要一定时间才能考虑恢复）
            elimination_time = datetime.fromisoformat(elimination_record["elimination_time"])
            time_since_elimination = (datetime.now() - elimination_time).total_seconds()
            
            # 至少需要60秒才能考虑恢复
            if time_since_elimination < 60:
                continue
            
            # 检查是否有改进迹象（这里简化处理）
            # 在实际系统中，这里应该检查策略的改进情况
            recovery_score = random.random()  # 模拟恢复评分
            
            if recovery_score > self.elimination_config["recovery_threshold"]:
                recovery_candidates.append(strategy_name)
        
        return recovery_candidates
    
    def recover_strategy(self, strategy_name: str) -> bool:
        """
        恢复被淘汰的策略
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            是否成功恢复
        """
        if strategy_name not in self.eliminated_strategies:
            print(f"   ❌ 策略 {strategy_name} 未被淘汰")
            return False
        
        # 从淘汰记录中恢复
        elimination_record = self.eliminated_strategies[strategy_name]
        
        # 在实际系统中，这里应该重新创建策略实例
        # 这里简化处理，只是从淘汰列表中移除
        del self.eliminated_strategies[strategy_name]
        
        # 记录恢复
        recovery_record = {
            "strategy_name": strategy_name,
            "recovery_time": datetime.now().isoformat(),
            "original_elimination_record": elimination_record
        }
        
        self.elimination_history.append(recovery_record)
        self.performance_tracking["strategies_recovered"] += 1
        
        print(f"   🔄 恢复策略: {strategy_name}")
        print(f"      原淘汰时间: {elimination_record['elimination_time']}")
        print(f"      淘汰原因: {list(elimination_record['elimination_reason'].keys())}")
        
        return True
    
    def run_elimination_cycle(self, num_queries: int = 50) -> Dict[str, Any]:
        """
        运行淘汰周期
        
        包括：
        1. 运行一定数量的查询
        2. 检查淘汰候选
        3. 执行淘汰
        4. 检查恢复候选
        5. 执行恢复
        """
        print(f"\n🔄 运行淘汰周期 ({num_queries}次查询)")
        print("=" * 40)
        
        cycle_results = {
            "cycle_start_time": datetime.now().isoformat(),
            "num_queries": num_queries,
            "elimination_candidates_found": 0,
            "strategies_eliminated": [],
            "recovery_candidates_found": 0,
            "strategies_recovered": [],
            "performance_impact": {}
        }
        
        # 1. 运行查询（模拟）
        print(f"   1️⃣ 运行 {num_queries} 次查询...")
        self._simulate_queries(num_queries)
        
        # 2. 检查淘汰候选
        print(f"   2️⃣ 检查淘汰候选...")
        candidates = self.check_elimination_candidates()
        cycle_results["elimination_candidates_found"] = len(candidates)
        
        if candidates:
            print(f"      找到 {len(candidates)} 个淘汰候选:")
            for i, (strategy_name, score, reason) in enumerate(candidates[:3]):  # 只显示前3个
                print(f"        {i+1}. {strategy_name} (评分: {score:.3f}, 原因: {list(reason.keys())})")
            
            # 3. 执行淘汰（最多淘汰指定数量的策略）
            elimination_limit = self.elimination_config["elimination_batch_size"]
            eliminated_count = 0
            
            for strategy_name, score, reason in candidates:
                if eliminated_count >= elimination_limit:
                    break
                
                if self.eliminate_strategy(strategy_name, reason):
                    cycle_results["strategies_eliminated"].append({
                        "strategy_name": strategy_name,
                        "composite_score": score,
                        "elimination_reason": reason
                    })
                    eliminated_count += 1
        else:
            print(f"      未找到淘汰候选")
        
        # 4. 检查恢复候选
        print(f"   3️⃣ 检查恢复候选...")
        recovery_candidates = self.check_recovery_candidates()
        cycle_results["recovery_candidates_found"] = len(recovery_candidates)
        
        if recovery_candidates:
            print(f"      找到 {len(recovery_candidates)} 个恢复候选:")
            for strategy_name in recovery_candidates:
                print(f"        - {strategy_name}")
            
            # 5. 执行恢复
            for strategy_name in recovery_candidates[:2]:  # 最多恢复2个
                if self.recover_strategy(strategy_name):
                    cycle_results["strategies_recovered"].append(strategy_name)
        else:
            print(f"      未找到恢复候选")
        
        # 6. 分析性能影响
        cycle_results["performance_impact"] = self._analyze_performance_impact()
        
        cycle_results["cycle_end_time"] = datetime.now().isoformat()
        
        return cycle_results
    
    def _simulate_queries(self, num_queries: int):
        """模拟查询运行（简化版）"""
        strategies = list(self.strategy_engine.strategies.values())
        
        for i in range(num_queries):
            # 随机选择策略（基于Fitness的概率选择）
            if strategies:
                # 计算选择概率（基于Fitness）
                fitness_values = [s.fitness_score for s in strategies]
                total_fitness = sum(fitness_values)
                
                if total_fitness > 0:
                    probabilities = [f / total_fitness for f in fitness_values]
                    selected_strategy = random.choices(strategies, weights=probabilities)[0]
                else:
                    selected_strategy = random.choice(strategies)
                
                # 模拟使用
                selected_strategy.metrics["usage_count"] = selected_strategy.metrics.get("usage_count", 0) + 1
                
                # 模拟性能更新
                success = random.random() < 0.85
                accuracy = random.uniform(0.7, 0.95)
                cost = random.uniform(0.1, 0.3)
                
                # 更新Fitness
                reward = accuracy * (1.0 if success else 0.5)
                penalty = cost * 0.3
                selected_strategy.fitness_score = 0.7 * selected_strategy.fitness_score + 0.3 * (reward - penalty)
                selected_strategy.fitness_score = max(0.01, selected_strategy.fitness_score)
            
            # 每10次查询显示进度
            if (i + 1) % 10 == 0:
                print(f"      进度: {i+1}/{num_queries}")
    
    def _analyze_performance_impact(self) -> Dict[str, Any]:
        """分析淘汰对性能的影响"""
        strategies = list(self.strategy_engine.strategies.values())
        
        if not strategies:
            return {"error": "无可用策略"}
        
        # 计算平均Fitness
        fitness_values = [s.fitness_score for s in strategies]
        avg_fitness = sum(fitness_values) / len(fitness_values) if fitness_values else 0.0
        
        # 计算Fitness差异
        fitness_diff = max(fitness_values) - min(fitness_values) if len(fitness_values) > 1 else 0.0
        
        # 计算使用率分布
        total_usage = sum(s.metrics.get("usage_count", 0) for s in strategies)
        usage_distribution = {}
        if total_usage > 0:
            for s in strategies:
                usage_distribution[s.name] = s.metrics.get("usage_count", 0) / total_usage
        
        # 计算使用率标准差（衡量分化程度）
        usage_values = list(usage_distribution.values())
        usage_std = self._calculate_std(usage_values) if len(usage_values) > 1 else 0.0
        
        return {
            "avg_fitness": avg_fitness,
            "fitness_range": {
                "min": min(fitness_values) if fitness_values else 0.0,
                "max": max(fitness_values) if fitness_values else 0.0,
                "diff": fitness_diff
            },
            "usage_std": usage_std,
            "total_strategies": len(strategies),
            "eliminated_strategies_count": len(self.eliminated_strategies)
        }
    
    def _safe_average(self, values: List[float]) -> float:
        """安全计算平均值"""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) <= 1:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def get_monitoring_report(self) -> Dict[str, Any]:
        """获取监测报告"""
        strategies = list(self.strategy_engine.strategies.values())
        
        return {
            "monitoring_start_time": self.monitoring_start_time.isoformat(),
            "elapsed_seconds": (datetime.now() - self.monitoring_start_time).total_seconds(),
            "strategy_status": {
                "active_strategies": len(strategies),
                "eliminated_strategies": len(self.eliminated_strategies),
                "total_strategies": len(strategies) + len(self.eliminated_strategies)
            },
            "elimination_history_summary": {
                "total_eliminations": len(self.elimination_history),
                "elimination_actions": sum(1 for r in self.elimination_history if r.get("action") in ["removed", "marked_for_elimination"]),
                "recovery_actions": sum(1 for r in self.elimination_history if "recovery_time" in r)
            },
            "performance_tracking": self.performance_tracking,
            "current_strategies": [
                {
                    "name": s.name,
                    "type": "api_based" if s.uses_real_data else "heuristic",
                    "fitness": s.fitness_score,
                    "usage_count": s.metrics.get("usage_count", 0),
                    "composite_score": self.calculate_composite_score(s)
                }
                for s in strategies
            ],
            "eliminated_strategies": list(self.eliminated_strategies.keys())
        }
    
    def print_monitoring_report(self):
        """打印监测报告"""
        report = self.get_monitoring_report()
        
        print("\n📊 淘汰监测报告")
        print("=" * 40)
        print(f"监测开始时间: {report['monitoring_start_time']}")
        print(f"运行时间: {report['elapsed_seconds']:.1f}秒")
        
        print(f"\n🎯 策略状态:")
        status = report["strategy_status"]
        print(f"   活跃策略: {status['active_strategies']}个")
        print(f"   淘汰策略: {status['eliminated_strategies']}个")
        print(f"   总策略数: {status['total_strategies']}个")
        
        print(f"\n📈 淘汰历史:")
        history = report["elimination_history_summary"]
        print(f"   总淘汰记录: {history['total_eliminations']}条")
        print(f"   淘汰行动: {history['elimination_actions']}次")
        print(f"   恢复行动: {history['recovery_actions']}次")
        
        print(f"\n📊 性能跟踪:")
        tracking = report["performance_tracking"]
        print(f"   淘汰检查次数: {tracking['total_elimination_checks']}")
        print(f"   标记淘汰策略: {tracking['strategies_marked_for_elimination']}")
        print(f"   实际淘汰策略: {tracking['strategies_actually_eliminated']}")
        print(f"   恢复策略: {tracking['strategies_recovered']}")
        
        print(f"\n🏆 当前策略排名:")
        strategies = sorted(report["current_strategies"], key=lambda x: x["composite_score"], reverse=True)
        
        for i, strategy in enumerate(strategies[:5], 1):  # 只显示前5个
            status_symbol = "✅" if strategy["composite_score"] > 0.5 else "⚠️" if strategy["composite_score"] > 0.3 else "❌"
            print(f"   {i}. {status_symbol} {strategy['name']}")
            print(f"      类型: {strategy['type']}")
            print(f"      适应度: {strategy['fitness']:.3f}")
            print(f"      使用次数: {strategy['usage_count']}")
            print(f"      综合评分: {strategy['composite_score']:.3f}")
        
        if report["eliminated_strategies"]:
            print(f"\n⚰️ 淘汰策略:")
            for strategy_name in report["eliminated_strategies"]:
                print(f"   ❌ {strategy_name}")
        
        # 进化状态判断
        print(f"\n🎯 进化状态判断:")
        
        judgments = []
        
        # 判断1: 是否有淘汰发生
        if tracking["strategies_marked_for_elimination"] > 0:
            judgments.append("✅ 淘汰机制已激活")
        else:
            judgments.append("⚠️  淘汰机制未激活")
        
        # 判断2: 策略数量是否健康
        if status["active_strategies"] >= self.elimination_config["min_strategies"]:
            judgments.append("✅ 策略数量健康")
        else:
            judgments.append("❌ 策略数量不足")
        
        # 判断3: 是否有恢复发生
        if tracking["strategies_recovered"] > 0:
            judgments.append("✅ 恢复机制工作")
        else:
            judgments.append("⚠️  恢复机制未测试")
        
        # 判断4: 进化是否持续
        if len(strategies) > 0:
            top_score = strategies[0]["composite_score"] if strategies else 0.0
            if top_score > 0.7:
                judgments.append("✅ 顶级策略表现优秀")
            elif top_score > 0.5:
                judgments.append("⚠️  顶级策略表现一般")
            else:
                judgments.append("❌ 顶级策略表现差")
        
        for judgment in judgments:
            print(f"   {judgment}")
        
        # 最终状态
        passed_judgments = sum(1 for j in judgments if j.startswith("✅"))
        total_judgments = len(judgments)
        
        print(f"\n🎯 最终进化状态:")
        if passed_judgments >= 3:
            print(f"   🎉 淘汰机制健康运行!")
            print(f"   💡 建议: 可以进入下一进化阶段")
        elif passed_judgments >= 2:
            print(f"   ⚠️  淘汰机制部分工作")
            print(f"   💡 建议: 需要更多测试")
        else:
            print(f"   ❌ 淘汰机制未正常工作")
            print(f"   💡 建议: 检查配置和逻辑")
        
        print(f"   通过率: {passed_judgments}/{total_judgments} ({passed_judgments/total_judgments:.0%})")

def test_elimination_monitor():
    """测试淘汰监测器"""
    print("🧪 测试 Strategy Elimination Monitor...")
    
    # 创建监测器
    monitor = StrategyEliminationMonitor()
    
    # 运行3个淘汰周期
    print("\n" + "=" * 70)
    print("🔄 运行淘汰周期测试")
    print("=" * 70)
    
    for cycle_num in range(3):
        print(f"\n📦 淘汰周期 {cycle_num+1}/3")
        print("-" * 40)
        
        cycle_results = monitor.run_elimination_cycle(num_queries=30)
        
        print(f"   周期结果:")
        print(f"     淘汰候选: {cycle_results['elimination_candidates_found']}个")
        print(f"     淘汰策略: {len(cycle_results['strategies_eliminated'])}个")
        print(f"     恢复候选: {cycle_results['recovery_candidates_found']}个")
        print(f"     恢复策略: {len(cycle_results['strategies_recovered'])}个")
    
    # 显示监测报告
    print("\n" + "=" * 70)
    print("📊 最终监测报告")
    print("=" * 70)
    
    monitor.print_monitoring_report()
    
    # 保存报告
    report_path = "/Users/liugang/.openclaw/workspace/elimination_monitor_report.json"
    try:
        report = monitor.get_monitoring_report()
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 监测报告已保存: {report_path}")
    except Exception as e:
        print(f"❌ 报告保存失败: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 淘汰监测器测试完成!")
    print("=" * 70)
    
    return monitor

if __name__ == "__main__":
    test_elimination_monitor()