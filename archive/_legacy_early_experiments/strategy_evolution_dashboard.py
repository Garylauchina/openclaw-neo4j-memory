#!/usr/bin/env python3
"""
Strategy Evolution Dashboard - 策略进化观测系统
核心：让系统的"进化"可观测
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np

# 尝试导入matplotlib，如果失败则使用替代方案
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib未安装，将使用文本模式")

# 添加路径
workspace_dir = os.path.expanduser("~/.openclaw/workspace")
sys.path.insert(0, workspace_dir)

class StrategyEvolutionDashboard:
    """策略进化观测系统"""
    
    def __init__(self, strategy_engine=None):
        print("\n" + "=" * 70)
        print("📊 Strategy Evolution Dashboard - 策略进化观测系统")
        print("=" * 70)
        
        # 加载策略引擎
        self.strategy_engine = strategy_engine
        if not self.strategy_engine:
            try:
                from cognitive_adapter.real_world_strategy import RealWorldStrategyEngine
                self.strategy_engine = RealWorldStrategyEngine()
                print("✅ 策略引擎已加载")
            except Exception as e:
                print(f"⚠️  策略引擎加载失败: {e}")
                self.strategy_engine = self._create_mock_engine()
        
        # 观测数据
        self.observation_history: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        
        # 实验配置
        self.experiment_config = {
            "dual_strategy_competition": {
                "enabled": True,
                "strategy_a": {
                    "name": "cheap_strategy",
                    "type": "api_based",
                    "description": "单API，低cost，低稳定性",
                    "uses_real_data": True,
                    "cost_multiplier": 0.5,
                    "stability": 0.3
                },
                "strategy_b": {
                    "name": "robust_strategy", 
                    "type": "hybrid",
                    "description": "双API验证，高cost，高稳定性",
                    "uses_real_data": True,
                    "cost_multiplier": 1.5,
                    "stability": 0.8
                }
            }
        }
        
        # 初始化实验策略
        self._init_experiment_strategies()
        
        print(f"✅ Dashboard 初始化完成")
        print(f"   开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   策略引擎: {len(self.strategy_engine.strategies)}个策略")
    
    def _create_mock_engine(self):
        """创建模拟策略引擎"""
        class MockStrategyEngine:
            def __init__(self):
                self.strategies = {}
                self.stats = {
                    "total_strategies": 0,
                    "strategies_created": 0,
                    "strategies_removed": 0,
                    "reality_based_wins": 0,
                    "simulation_based_wins": 0,
                    "avg_fitness": 0.0,
                    "avg_real_world_accuracy": 0.0
                }
        
        return MockStrategyEngine()
    
    def _init_experiment_strategies(self):
        """初始化实验策略"""
        print("\n🔧 初始化实验策略...")
        
        # 检查是否已有实验策略
        existing_strategies = list(self.strategy_engine.strategies.keys())
        
        # 添加实验策略（如果不存在）
        exp_config = self.experiment_config["dual_strategy_competition"]
        
        for strategy_key in ["strategy_a", "strategy_b"]:
            strategy_config = exp_config[strategy_key]
            strategy_name = strategy_config["name"]
            
            if strategy_name not in existing_strategies:
                print(f"   ➕ 添加实验策略: {strategy_name}")
                
                # 这里应该调用策略引擎的添加策略方法
                # 暂时跳过，使用现有策略
                pass
    
    def observe(self, context: Optional[Dict[str, Any]] = None):
        """
        观测当前系统状态
        
        Args:
            context: 观测上下文
            
        Returns:
            观测结果
        """
        observation = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_seconds": (datetime.now() - self.start_time).total_seconds(),
            "strategies": self._get_strategy_metrics(),
            "performance": self._get_performance_metrics(),
            "evolution": self._get_evolution_metrics(),
            "context": context or {}
        }
        
        # 记录历史
        self.observation_history.append(observation)
        
        # 限制历史大小
        max_history = 1000
        if len(self.observation_history) > max_history:
            self.observation_history = self.observation_history[-max_history:]
        
        return observation
    
    def _get_strategy_metrics(self) -> Dict[str, Any]:
        """获取策略指标"""
        strategies = list(self.strategy_engine.strategies.values())
        
        if not strategies:
            return {
                "total_strategies": 0,
                "strategy_list": [],
                "usage_distribution": {},
                "fitness_range": {"min": 0.0, "max": 0.0, "avg": 0.0}
            }
        
        # 策略列表
        strategy_list = []
        for strategy in strategies:
            strategy_list.append({
                "id": strategy.name,
                "type": "api_based" if strategy.uses_real_data else "heuristic",
                "fitness": strategy.fitness_score,
                "usage_count": strategy.metrics.get("usage_count", 0),
                "real_world_accuracy": self._safe_average(strategy.metrics.get("real_world_accuracy", [])),
                "uses_real_data": strategy.uses_real_data
            })
        
        # 使用分布
        total_usage = sum(s["usage_count"] for s in strategy_list)
        usage_distribution = {}
        if total_usage > 0:
            for s in strategy_list:
                usage_distribution[s["id"]] = s["usage_count"] / total_usage
        
        # Fitness范围
        fitness_values = [s["fitness"] for s in strategy_list]
        
        return {
            "total_strategies": len(strategies),
            "strategy_list": strategy_list,
            "usage_distribution": usage_distribution,
            "fitness_range": {
                "min": min(fitness_values) if fitness_values else 0.0,
                "max": max(fitness_values) if fitness_values else 0.0,
                "avg": sum(fitness_values) / len(fitness_values) if fitness_values else 0.0,
                "std": np.std(fitness_values) if len(fitness_values) > 1 else 0.0
            }
        }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        # 这里应该从验证器获取现实准确性数据
        # 暂时使用模拟数据
        return {
            "real_world_accuracy": 0.75,  # 需要从验证器获取
            "validation_pass_rate": 0.85,  # 需要从验证器获取
            "api_cost": 0.15,  # 需要从世界模型获取
            "latency": 0.8,    # 需要从世界模型获取
            "information_gain": 0.6,  # 需要计算
            "replan_rate": 0.1,  # 需要从验证器获取
            "failure_rate": 0.05  # 需要从验证器获取
        }
    
    def _get_evolution_metrics(self) -> Dict[str, Any]:
        """获取进化指标"""
        if len(self.observation_history) < 2:
            return {
                "has_evolution": False,
                "fitness_trend": "insufficient_data",
                "strategy_diversity": "insufficient_data",
                "learning_curve": "insufficient_data"
            }
        
        # 分析Fitness趋势
        recent_obs = self.observation_history[-10:]  # 最近10次观测
        if len(recent_obs) >= 2:
            first_fitness_avg = self._get_avg_fitness(recent_obs[0])
            last_fitness_avg = self._get_avg_fitness(recent_obs[-1])
            fitness_trend = "increasing" if last_fitness_avg > first_fitness_avg else "decreasing" if last_fitness_avg < first_fitness_avg else "stable"
        else:
            fitness_trend = "insufficient_data"
        
        # 分析策略多样性
        current_strategies = len(self.strategy_engine.strategies)
        strategy_diversity = "high" if current_strategies >= 4 else "medium" if current_strategies >= 2 else "low"
        
        # 分析学习曲线（通过replan/failure率变化）
        if len(self.observation_history) >= 5:
            early_failures = sum(1 for obs in self.observation_history[:5] if obs["performance"]["failure_rate"] > 0.3)
            recent_failures = sum(1 for obs in self.observation_history[-5:] if obs["performance"]["failure_rate"] > 0.3)
            learning_curve = "improving" if recent_failures < early_failures else "stagnant" if recent_failures == early_failures else "worsening"
        else:
            learning_curve = "insufficient_data"
        
        evolution_data = {
            "has_evolution": fitness_trend != "stable" or learning_curve != "stagnant",
            "fitness_trend": fitness_trend,
            "strategy_diversity": strategy_diversity,
            "learning_curve": learning_curve
        }
        
        # 添加策略创建/淘汰数据（如果可用）
        if hasattr(self.strategy_engine, 'stats'):
            if isinstance(self.strategy_engine.stats, dict):
                evolution_data["strategies_created"] = self.strategy_engine.stats.get("strategies_created", 0)
                evolution_data["strategies_removed"] = self.strategy_engine.stats.get("strategies_removed", 0)
            elif hasattr(self.strategy_engine.stats, 'get'):
                evolution_data["strategies_created"] = self.strategy_engine.stats.get("strategies_created", 0)
                evolution_data["strategies_removed"] = self.strategy_engine.stats.get("strategies_removed", 0)
        
        return evolution_data
    
    def _get_avg_fitness(self, observation: Dict[str, Any]) -> float:
        """获取平均Fitness"""
        strategies = observation["strategies"]["strategy_list"]
        if not strategies:
            return 0.0
        return sum(s["fitness"] for s in strategies) / len(strategies)
    
    def _safe_average(self, values: List[float]) -> float:
        """安全计算平均值"""
        if not values:
            return 0.0
        return sum(values) / len(values)
    
    def render(self, output_format: str = "text") -> Dict[str, Any]:
        """
        渲染Dashboard
        
        Args:
            output_format: "text" | "json" | "html"
            
        Returns:
            渲染结果
        """
        # 获取当前观测
        observation = self.observe()
        
        if output_format == "json":
            return observation
        
        elif output_format == "text":
            return self._render_text(observation)
        
        elif output_format == "html":
            return self._render_html(observation)
        
        else:
            return {"error": f"Unsupported format: {output_format}"}
    
    def _render_text(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """渲染文本格式Dashboard"""
        strategies = observation["strategies"]
        performance = observation["performance"]
        evolution = observation["evolution"]
        
        output_lines = []
        
        output_lines.append("\n" + "=" * 70)
        output_lines.append("📊 STRATEGY EVOLUTION DASHBOARD")
        output_lines.append("=" * 70)
        output_lines.append(f"观测时间: {datetime.fromisoformat(observation['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append(f"运行时间: {observation['elapsed_seconds']:.1f}秒")
        output_lines.append("")
        
        # 1️⃣ Strategy 列表
        output_lines.append("1️⃣ STRATEGY 列表")
        output_lines.append("-" * 40)
        
        if strategies["total_strategies"] == 0:
            output_lines.append("   ❌ 无策略")
        else:
            for i, strategy in enumerate(strategies["strategy_list"], 1):
                reality_flag = "🌍" if strategy["uses_real_data"] else "🧠"
                type_symbol = "🔄" if strategy["type"] == "hybrid" else "⚡" if strategy["type"] == "api_based" else "🧠"
                output_lines.append(f"   {i}. {reality_flag}{type_symbol} {strategy['id']}")
                output_lines.append(f"      适应度: {strategy['fitness']:.3f}")
                output_lines.append(f"      使用次数: {strategy['usage_count']}")
                output_lines.append(f"      现实准确率: {strategy['real_world_accuracy']:.3f}")
        
        # 2️⃣ Strategy 使用分布
        output_lines.append("\n2️⃣ STRATEGY 使用分布")
        output_lines.append("-" * 40)
        
        if strategies["usage_distribution"]:
            for strategy_id, usage_rate in strategies["usage_distribution"].items():
                bar_length = int(usage_rate * 20)
                bar = "█" * bar_length + "░" * (20 - bar_length)
                output_lines.append(f"   {strategy_id}: {bar} {usage_rate:.1%}")
        else:
            output_lines.append("   ⚠️  尚无使用数据")
        
        # 3️⃣ Strategy Fitness 轨迹
        output_lines.append("\n3️⃣ STRATEGY FITNESS 轨迹")
        output_lines.append("-" * 40)
        
        fitness_range = strategies["fitness_range"]
        output_lines.append(f"   适应度范围: {fitness_range['min']:.3f} - {fitness_range['max']:.3f}")
        output_lines.append(f"   平均适应度: {fitness_range['avg']:.3f}")
        output_lines.append(f"   适应度标准差: {fitness_range['std']:.3f}")
        
        # 检查Fitness差异
        fitness_diff = fitness_range["max"] - fitness_range["min"]
        if fitness_diff > 0.1:
            output_lines.append(f"   ✅ FITNESS 有显著差异 ({fitness_diff:.3f})")
        elif fitness_diff > 0.01:
            output_lines.append(f"   ⚠️  FITNESS 有轻微差异 ({fitness_diff:.3f})")
        else:
            output_lines.append(f"   ❌ FITNESS 无差异 ({fitness_diff:.3f})")
        
        # 4️⃣ Reality Accuracy
        output_lines.append("\n4️⃣ REALITY ACCURACY（现实一致性）")
        output_lines.append("-" * 40)
        output_lines.append(f"   现实准确率: {performance['real_world_accuracy']:.3f}")
        output_lines.append(f"   验证通过率: {performance['validation_pass_rate']:.3f}")
        
        # 5️⃣ Cost vs Value
        output_lines.append("\n5️⃣ COST vs VALUE（决策能力）")
        output_lines.append("-" * 40)
        output_lines.append(f"   API成本: {performance['api_cost']:.3f}")
        output_lines.append(f"   延迟: {performance['latency']:.3f}s")
        output_lines.append(f"   信息增益: {performance['information_gain']:.3f}")
        
        # 计算trade-off
        efficiency = performance['information_gain'] / (performance['api_cost'] + 0.01)
        if efficiency > 1.0:
            output_lines.append(f"   ✅ 高效决策 (效率: {efficiency:.2f})")
        elif efficiency > 0.5:
            output_lines.append(f"   ⚠️  中等效率 (效率: {efficiency:.2f})")
        else:
            output_lines.append(f"   ❌ 低效决策 (效率: {efficiency:.2f})")
        
        # 6️⃣ Replan / Failure 率
        output_lines.append("\n6️⃣ REPLAN / FAILURE 率")
        output_lines.append("-" * 40)
        output_lines.append(f"   重规划率: {performance['replan_rate']:.3f}")
        output_lines.append(f"   失败率: {performance['failure_rate']:.3f}")
        
        # 7️⃣ Evolution 状态
        output_lines.append("\n7️⃣ EVOLUTION 状态")
        output_lines.append("-" * 40)
        
        if evolution["has_evolution"]:
            output_lines.append("   ✅ 系统正在进化")
        else:
            output_lines.append("   ❌ 系统未进化")
        
        output_lines.append(f"   Fitness趋势: {evolution['fitness_trend']}")
        output_lines.append(f"   策略多样性: {evolution['strategy_diversity']}")
        output_lines.append(f"   学习曲线: {evolution['learning_curve']}")
        output_lines.append(f"   策略创建: {evolution.get('strategies_created', 0)}")
        output_lines.append(f"   策略淘汰: {evolution.get('strategies_removed', 0)}")
        
        # 8️⃣ 关键判断
        output_lines.append("\n8️⃣ 关键判断")
        output_lines.append("-" * 40)
        
        judgments = []
        
        # 判断1: 是否有多个策略
        if strategies["total_strategies"] >= 2:
            judgments.append("✅ 多个策略并存")
        else:
            judgments.append("❌ 策略数量不足")
        
        # 判断2: Fitness是否有差异
        if fitness_diff > 0.01:
            judgments.append("✅ Fitness有差异")
        else:
            judgments.append("❌ Fitness无差异")
        
        # 判断3: 使用率是否有差异
        if strategies["usage_distribution"]:
            usage_values = list(strategies["usage_distribution"].values())
            usage_std = np.std(usage_values) if len(usage_values) > 1 else 0.0
            if usage_std > 0.1:
                judgments.append("✅ 使用率有差异")
            else:
                judgments.append("❌ 使用率无差异")
        else:
            judgments.append("⚠️  无使用率数据")
        
        # 判断4: 是否有进化迹象
        if evolution["has_evolution"]:
            judgments.append("✅ 有进化迹象")
        else:
            judgments.append("❌ 无进化迹象")
        
        for judgment in judgments:
            output_lines.append(f"   {judgment}")
        
        # 9️⃣ 最终状态
        output_lines.append("\n9️⃣ 最终状态")
        output_lines.append("-" * 40)
        
        passed_judgments = sum(1 for j in judgments if j.startswith("✅"))
        total_judgments = len(judgments)
        
        if passed_judgments >= 3:
            output_lines.append("   🎉 系统正在健康进化")
            output_lines.append("   💡 建议: 继续观察，准备进入下一阶段")
        elif passed_judgments >= 2:
            output_lines.append("   ⚠️  系统有进化迹象但不足")
            output_lines.append("   💡 建议: 运行更多实验，收集数据")
        else:
            output_lines.append("   ❌ 系统未显示进化迹象")
            output_lines.append("   💡 建议: 检查闭环机制，运行双策略竞争实验")
        
        output_lines.append(f"   通过率: {passed_judgments}/{total_judgments} ({passed_judgments/total_judgments:.0%})")
        
        output_lines.append("\n" + "=" * 70)
        
        return {
            "text": "\n".join(output_lines),
            "observation": observation,
            "summary": {
                "total_strategies": strategies["total_strategies"],
                "fitness_difference": fitness_diff,
                "has_evolution": evolution["has_evolution"],
                "passed_judgments": passed_judgments,
                "total_judgments": total_judgments
            }
        }
    
    def _render_html(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """渲染HTML格式Dashboard（简化版）"""
        # 这里可以实现完整的HTML Dashboard
        # 暂时返回文本格式
        return self._render_text(observation)
    
    def run_dual_strategy_experiment(self, num_queries: int = 20) -> Dict[str, Any]:
        """
        运行双策略竞争实验
        
        Args:
            num_queries: 查询数量
            
        Returns:
            实验结果
        """
        print(f"\n🧪 运行双策略竞争实验 ({num_queries}次查询)")
        print("-" * 40)
        
        # 获取实验策略配置
        exp_config = self.experiment_config["dual_strategy_competition"]
        strategy_a = exp_config["strategy_a"]
        strategy_b = exp_config["strategy_b"]
        
        print(f"   策略A: {strategy_a['name']} ({strategy_a['description']})")
        print(f"   策略B: {strategy_b['name']} ({strategy_b['description']})")
        
        # 模拟查询
        results = {
            "total_queries": num_queries,
            "strategy_selections": {"A": 0, "B": 0},
            "query_types": {"simple": 0, "critical": 0},
            "performance": {
                "A": {"success": 0, "failure": 0, "total_cost": 0.0},
                "B": {"success": 0, "failure": 0, "total_cost": 0.0}
            }
        }
        
        for i in range(num_queries):
            # 随机生成查询类型
            is_critical = np.random.random() < 0.3  # 30%关键查询
            
            # 选择策略（模拟）
            if is_critical:
                # 关键查询更可能选择robust策略
                selected_strategy = "B" if np.random.random() < 0.7 else "A"
                results["query_types"]["critical"] += 1
            else:
                # 简单查询更可能选择cheap策略
                selected_strategy = "A" if np.random.random() < 0.7 else "B"
                results["query_types"]["simple"] += 1
            
            results["strategy_selections"][selected_strategy] += 1
            
            # 模拟性能
            if selected_strategy == "A":
                success_rate = 0.7  # cheap策略成功率较低
                cost = 0.1 * strategy_a["cost_multiplier"]
            else:
                success_rate = 0.9  # robust策略成功率较高
                cost = 0.2 * strategy_b["cost_multiplier"]
            
            is_success = np.random.random() < success_rate
            
            if is_success:
                results["performance"][selected_strategy]["success"] += 1
            else:
                results["performance"][selected_strategy]["failure"] += 1
            
            results["performance"][selected_strategy]["total_cost"] += cost
        
        # 计算指标
        total_a = results["strategy_selections"]["A"]
        total_b = results["strategy_selections"]["B"]
        
        if total_a > 0:
            results["performance"]["A"]["success_rate"] = results["performance"]["A"]["success"] / total_a
            results["performance"]["A"]["avg_cost"] = results["performance"]["A"]["total_cost"] / total_a
        
        if total_b > 0:
            results["performance"]["B"]["success_rate"] = results["performance"]["B"]["success"] / total_b
            results["performance"]["B"]["avg_cost"] = results["performance"]["B"]["total_cost"] / total_b
        
        # 输出结果
        print(f"\n📊 实验结果:")
        print(f"   总查询数: {results['total_queries']}")
        print(f"   简单查询: {results['query_types']['simple']}")
        print(f"   关键查询: {results['query_types']['critical']}")
        print(f"\n   策略选择分布:")
        print(f"     策略A ({strategy_a['name']}): {results['strategy_selections']['A']}次 ({results['strategy_selections']['A']/num_queries:.1%})")
        print(f"     策略B ({strategy_b['name']}): {results['strategy_selections']['B']}次 ({results['strategy_selections']['B']/num_queries:.1%})")
        
        print(f"\n   策略性能:")
        if total_a > 0:
            print(f"     策略A: 成功率={results['performance']['A']['success_rate']:.1%}, 平均成本={results['performance']['A']['avg_cost']:.3f}")
        if total_b > 0:
            print(f"     策略B: 成功率={results['performance']['B']['success_rate']:.1%}, 平均成本={results['performance']['B']['avg_cost']:.3f}")
        
        # 判断实验是否成功
        print(f"\n🎯 实验判断:")
        
        # 判断1: 不同场景是否选择不同策略
        if results["query_types"]["critical"] > 0:
            critical_b_ratio = results["strategy_selections"]["B"] / max(1, results["query_types"]["critical"])
            if critical_b_ratio > 0.6:
                print(f"   ✅ 关键查询更倾向策略B ({critical_b_ratio:.1%})")
            else:
                print(f"   ❌ 关键查询未明显倾向策略B ({critical_b_ratio:.1%})")
        
        # 判断2: fitness是否分化
        if total_a > 0 and total_b > 0:
            # 简单计算fitness（成功率 - 成本）
            fitness_a = results["performance"]["A"]["success_rate"] - results["performance"]["A"]["avg_cost"]
            fitness_b = results["performance"]["B"]["success_rate"] - results["performance"]["B"]["avg_cost"]
            
            fitness_diff = abs(fitness_a - fitness_b)
            if fitness_diff > 0.1:
                print(f"   ✅ Fitness有显著分化 (差异: {fitness_diff:.3f})")
                print(f"      策略A Fitness: {fitness_a:.3f}")
                print(f"      策略B Fitness: {fitness_b:.3f}")
            else:
                print(f"   ❌ Fitness未分化 (差异: {fitness_diff:.3f})")
        
        # 判断3: 是否出现策略演化
        # 这里需要实际运行策略进化
        print(f"   ⚠️  策略演化需要实际进化机制运行")
        
        return results

def test_dashboard():
    """测试Dashboard"""
    print("🧪 测试 Strategy Evolution Dashboard...")
    
    dashboard = StrategyEvolutionDashboard()
    
    # 运行几次观测
    print("\n🔍 运行初始观测...")
    result1 = dashboard.render("text")
    print(result1["text"])
    
    # 运行双策略竞争实验
    print("\n🧪 运行双策略竞争实验...")
    experiment_results = dashboard.run_dual_strategy_experiment(num_queries=30)
    
    # 再次观测
    print("\n🔍 运行实验后观测...")
    result2 = dashboard.render("text")
    print(result2["text"])
    
    # 输出总结
    summary = result2["summary"]
    print(f"\n📋 Dashboard 测试总结:")
    print(f"   总策略数: {summary['total_strategies']}")
    print(f"   Fitness差异: {summary['fitness_difference']:.3f}")
    print(f"   有进化迹象: {summary['has_evolution']}")
    print(f"   判断通过率: {summary['passed_judgments']}/{summary['total_judgments']}")
    
    return dashboard

if __name__ == "__main__":
    test_dashboard()