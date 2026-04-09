#!/usr/bin/env python3
"""
巩固淘汰周期 - 运行多个淘汰周期，验证机制稳定性
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# 添加路径
workspace_dir = os.path.expanduser("~/.openclaw/workspace")
sys.path.insert(0, workspace_dir)

class EliminationCycleConsolidator:
    """淘汰周期巩固器"""
    
    def __init__(self):
        print("\n" + "=" * 70)
        print("🔄 ELIMINATION CYCLE CONSOLIDATOR - 淘汰周期巩固器")
        print("=" * 70)
        
        # 加载实际数据
        print("📂 加载实际策略数据...")
        try:
            from cognitive_adapter.real_world_strategy import RealWorldStrategyEngine
            self.strategy_engine = RealWorldStrategyEngine()
            
            # 从实际报告加载数据
            report_path = "/Users/liugang/.openclaw/workspace/real_elimination_report.json"
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            # 更新策略数据
            for strategy_data in report["initial_state"]["strategies"]:
                strategy_name = strategy_data["name"]
                if strategy_name in self.strategy_engine.strategies:
                    strategy = self.strategy_engine.strategies[strategy_name]
                    strategy.fitness_score = strategy_data["fitness"]
                    strategy.metrics["usage_count"] = strategy_data["usage_count"]
            
            print("✅ 实际数据加载成功")
            
        except Exception as e:
            print(f"❌ 数据加载失败: {e}")
            return
        
        # 加载淘汰监测器
        try:
            from strategy_elimination_monitor import StrategyEliminationMonitor
            self.monitor = StrategyEliminationMonitor(strategy_engine=self.strategy_engine)
            print("✅ 淘汰监测器已加载")
        except Exception as e:
            print(f"❌ 淘汰监测器加载失败: {e}")
            return
        
        # 巩固配置
        self.consolidation_config = {
            "num_cycles": 3,               # 运行3个淘汰周期
            "queries_per_cycle": 100,      # 每个周期100次查询
            "cycle_interval_seconds": 2,   # 周期间隔2秒
            "show_progress_every": 25,     # 每25次查询显示进度
            "save_reports": True,          # 保存详细报告
            "adjust_thresholds": True      # 根据结果调整阈值
        }
        
        # 数据收集
        self.consolidation_data = {
            "start_time": datetime.now().isoformat(),
            "cycles": [],
            "evolution_trends": {},
            "threshold_adjustments": []
        }
        
        print(f"🎯 巩固配置:")
        print(f"   淘汰周期数: {self.consolidation_config['num_cycles']}")
        print(f"   每周期查询数: {self.consolidation_config['queries_per_cycle']}")
        print(f"   周期间隔: {self.consolidation_config['cycle_interval_seconds']}秒")
        print(f"   保存报告: {self.consolidation_config['save_reports']}")
        print(f"   调整阈值: {self.consolidation_config['adjust_thresholds']}")
    
    def run_consolidation_cycles(self):
        """运行巩固淘汰周期"""
        print(f"\n🔄 运行 {self.consolidation_config['num_cycles']} 个淘汰周期")
        print("=" * 40)
        
        # 记录初始状态
        initial_state = self._capture_system_state()
        self.consolidation_data["initial_state"] = initial_state
        
        print(f"📊 初始系统状态:")
        print(f"   活跃策略: {initial_state['active_strategies']}个")
        print(f"   淘汰策略: {initial_state['eliminated_strategies']}个")
        print(f"   Fitness差异: {initial_state['fitness_range']['diff']:.3f}")
        print(f"   使用率标准差: {initial_state['usage_std']:.3f}")
        
        # 运行淘汰周期
        for cycle_num in range(self.consolidation_config["num_cycles"]):
            print(f"\n📦 淘汰周期 {cycle_num+1}/{self.consolidation_config['num_cycles']}")
            print("-" * 40)
            
            # 运行淘汰周期
            cycle_start_time = datetime.now()
            cycle_results = self.monitor.run_elimination_cycle(
                num_queries=self.consolidation_config["queries_per_cycle"]
            )
            cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
            
            # 记录周期数据
            cycle_record = {
                "cycle_num": cycle_num + 1,
                "start_time": cycle_start_time.isoformat(),
                "duration_seconds": cycle_duration,
                "results": cycle_results,
                "system_state": self._capture_system_state()
            }
            
            self.consolidation_data["cycles"].append(cycle_record)
            
            # 显示周期结果
            self._show_cycle_summary(cycle_record, cycle_num + 1)
            
            # 调整阈值（如果需要）
            if self.consolidation_config["adjust_thresholds"]:
                self._adjust_elimination_thresholds(cycle_record)
            
            # 周期间隔（除了最后一个周期）
            if cycle_num < self.consolidation_config["num_cycles"] - 1:
                print(f"⏳ 等待 {self.consolidation_config['cycle_interval_seconds']}秒...")
                time.sleep(self.consolidation_config["cycle_interval_seconds"])
        
        # 记录最终状态
        final_state = self._capture_system_state()
        self.consolidation_data["final_state"] = final_state
        
        # 分析进化趋势
        self._analyze_evolution_trends()
        
        print(f"\n🎉 淘汰周期巩固完成!")
        print("=" * 40)
        
        return self.consolidation_data
    
    def _capture_system_state(self) -> Dict[str, Any]:
        """捕获系统状态"""
        strategies = list(self.strategy_engine.strategies.values())
        
        # 计算Fitness差异
        fitness_values = [s.fitness_score for s in strategies]
        fitness_diff = max(fitness_values) - min(fitness_values) if len(fitness_values) > 1 else 0.0
        
        # 计算使用率
        total_usage = sum(s.metrics.get("usage_count", 0) for s in strategies)
        usage_distribution = {}
        if total_usage > 0:
            for s in strategies:
                usage_distribution[s.name] = s.metrics.get("usage_count", 0) / total_usage
        
        # 计算使用率标准差
        usage_values = list(usage_distribution.values())
        usage_std = self._calculate_std(usage_values) if len(usage_values) > 1 else 0.0
        
        # 计算综合评分
        composite_scores = []
        for s in strategies:
            score = self.monitor.calculate_composite_score(s)
            composite_scores.append(score)
        
        avg_composite_score = sum(composite_scores) / len(composite_scores) if composite_scores else 0.0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_strategies": len(strategies),
            "eliminated_strategies": len(self.monitor.eliminated_strategies),
            "fitness_range": {
                "min": min(fitness_values) if fitness_values else 0.0,
                "max": max(fitness_values) if fitness_values else 0.0,
                "diff": fitness_diff,
                "avg": sum(fitness_values) / len(fitness_values) if fitness_values else 0.0
            },
            "usage_distribution": usage_distribution,
            "usage_std": usage_std,
            "composite_scores": {
                "min": min(composite_scores) if composite_scores else 0.0,
                "max": max(composite_scores) if composite_scores else 0.0,
                "avg": avg_composite_score,
                "diff": max(composite_scores) - min(composite_scores) if len(composite_scores) > 1 else 0.0
            },
            "strategy_details": [
                {
                    "name": s.name,
                    "type": "api_based" if s.uses_real_data else "heuristic",
                    "fitness": s.fitness_score,
                    "usage_count": s.metrics.get("usage_count", 0),
                    "composite_score": self.monitor.calculate_composite_score(s),
                    "is_eliminated": s.name in self.monitor.eliminated_strategies
                }
                for s in strategies
            ]
        }
    
    def _show_cycle_summary(self, cycle_record: Dict[str, Any], cycle_num: int):
        """显示周期总结"""
        results = cycle_record["results"]
        state = cycle_record["system_state"]
        
        print(f"📊 周期 {cycle_num} 结果:")
        print(f"   持续时间: {cycle_record['duration_seconds']:.1f}秒")
        print(f"   淘汰候选: {results['elimination_candidates_found']}个")
        print(f"   淘汰策略: {len(results['strategies_eliminated'])}个")
        print(f"   恢复候选: {results['recovery_candidates_found']}个")
        print(f"   恢复策略: {len(results['strategies_recovered'])}个")
        
        print(f"\n   📈 系统状态变化:")
        print(f"     活跃策略: {state['active_strategies']}个")
        print(f"     淘汰策略: {state['eliminated_strategies']}个")
        print(f"     Fitness差异: {state['fitness_range']['diff']:.3f}")
        print(f"     使用率标准差: {state['usage_std']:.3f}")
        
        # 显示淘汰详情
        if results["strategies_eliminated"]:
            print(f"\n   ⚰️ 淘汰详情:")
            for elimination in results["strategies_eliminated"]:
                strategy_name = elimination["strategy_name"]
                score = elimination["composite_score"]
                reasons = list(elimination["elimination_reason"].keys())
                print(f"     ❌ {strategy_name} (评分: {score:.3f}, 原因: {reasons})")
        
        # 显示恢复详情
        if results["strategies_recovered"]:
            print(f"\n   🔄 恢复详情:")
            for strategy_name in results["strategies_recovered"]:
                print(f"     ✅ {strategy_name}")
    
    def _adjust_elimination_thresholds(self, cycle_record: Dict[str, Any]):
        """根据周期结果调整淘汰阈值"""
        state = cycle_record["system_state"]
        results = cycle_record["results"]
        
        # 获取当前配置
        config = self.monitor.elimination_config
        
        # 分析是否需要调整
        adjustments = []
        
        # 1. 如果淘汰候选太少，降低阈值
        if results["elimination_candidates_found"] == 0 and state["active_strategies"] > 3:
            # 降低使用率阈值
            new_usage_threshold = config["usage_threshold"] * 0.8  # 降低20%
            adjustments.append({
                "parameter": "usage_threshold",
                "old_value": config["usage_threshold"],
                "new_value": new_usage_threshold,
                "reason": "淘汰候选太少，降低阈值增加淘汰压力"
            })
            config["usage_threshold"] = new_usage_threshold
        
        # 2. 如果淘汰候选太多，提高阈值
        elif results["elimination_candidates_found"] > 3:
            # 提高综合评分阈值
            new_score_threshold = config["composite_score_threshold"] * 1.2  # 提高20%
            adjustments.append({
                "parameter": "composite_score_threshold",
                "old_value": config["composite_score_threshold"],
                "new_value": new_score_threshold,
                "reason": "淘汰候选太多，提高阈值减少误淘汰"
            })
            config["composite_score_threshold"] = new_score_threshold
        
        # 3. 如果Fitness差异太小，增加选择压力
        if state["fitness_range"]["diff"] < 0.1:
            # 增加fitness权重
            new_fitness_weight = min(0.8, config["fitness_weight"] * 1.1)  # 增加10%，最多0.8
            new_usage_weight = 1.0 - new_fitness_weight
            adjustments.append({
                "parameter": "fitness_weight",
                "old_value": config["fitness_weight"],
                "new_value": new_fitness_weight,
                "reason": "Fitness差异太小，增加fitness权重"
            })
            adjustments.append({
                "parameter": "usage_weight",
                "old_value": config["usage_weight"],
                "new_value": new_usage_weight,
                "reason": "相应调整usage权重"
            })
            config["fitness_weight"] = new_fitness_weight
            config["usage_weight"] = new_usage_weight
        
        # 记录调整
        if adjustments:
            print(f"\n   🔧 阈值调整:")
            for adj in adjustments:
                print(f"     {adj['parameter']}: {adj['old_value']:.3f} → {adj['new_value']:.3f}")
                print(f"       原因: {adj['reason']}")
            
            self.consolidation_data["threshold_adjustments"].extend(adjustments)
    
    def _analyze_evolution_trends(self):
        """分析进化趋势"""
        print(f"\n📈 进化趋势分析")
        print("=" * 40)
        
        if len(self.consolidation_data["cycles"]) < 2:
            print("   ⚠️  周期数据不足，无法分析趋势")
            return
        
        initial = self.consolidation_data["initial_state"]
        final = self.consolidation_data["final_state"]
        cycles = self.consolidation_data["cycles"]
        
        # 1. Fitness趋势
        initial_fitness_diff = initial["fitness_range"]["diff"]
        final_fitness_diff = final["fitness_range"]["diff"]
        fitness_change = final_fitness_diff - initial_fitness_diff
        
        print(f"   📊 Fitness趋势:")
        print(f"     初始差异: {initial_fitness_diff:.3f}")
        print(f"     最终差异: {final_fitness_diff:.3f}")
        print(f"     变化: {fitness_change:+.3f}")
        
        if fitness_change > 0.05:
            print(f"     ✅ Fitness差异显著增加 - 进化加速")
        elif fitness_change > 0:
            print(f"     ⚠️  Fitness差异轻微增加 - 缓慢进化")
        elif fitness_change == 0:
            print(f"     ⚠️  Fitness差异稳定 - 进化停滞")
        else:
            print(f"     ❌ Fitness差异减少 - 可能退化")
        
        # 2. 淘汰趋势
        total_eliminations = sum(len(cycle["results"]["strategies_eliminated"]) for cycle in cycles)
        total_recoveries = sum(len(cycle["results"]["strategies_recovered"]) for cycle in cycles)
        
        print(f"\n   ⚰️ 淘汰趋势:")
        print(f"     总淘汰策略: {total_eliminations}个")
        print(f"     总恢复策略: {total_recoveries}个")
        print(f"     净淘汰: {total_eliminations - total_recoveries}个")
        
        if total_eliminations > 0:
            print(f"     ✅ 淘汰机制持续工作")
        else:
            print(f"     ⚠️  淘汰机制未产生淘汰")
        
        # 3. 策略多样性趋势
        initial_diversity = initial["active_strategies"]
        final_diversity = final["active_strategies"]
        diversity_change = final_diversity - initial_diversity
        
        print(f"\n   🌈 策略多样性趋势:")
        print(f"     初始多样性: {initial_diversity}个策略")
        print(f"     最终多样性: {final_diversity}个策略")
        print(f"     变化: {diversity_change:+d}个策略")
        
        if final_diversity >= 3:
            print(f"     ✅ 多样性健康 (≥3个策略)")
        else:
            print(f"     ❌ 多样性不足 (<3个策略)")
        
        # 4. 使用率分化趋势
        initial_usage_std = initial["usage_std"]
        final_usage_std = final["usage_std"]
        usage_std_change = final_usage_std - initial_usage_std
        
        print(f"\n   📊 使用率分化趋势:")
        print(f"     初始分化: {initial_usage_std:.3f}")
        print(f"     最终分化: {final_usage_std:.3f}")
        print(f"     变化: {usage_std_change:+.3f}")
        
        if final_usage_std > 0.15:
            print(f"     ✅ 使用率高度分化")
        elif final_usage_std > 0.05:
            print(f"     ⚠️  使用率中度分化")
        else:
            print(f"     ❌ 使用率未分化")
        
        # 5. 综合评分趋势
        initial_avg_score = initial["composite_scores"]["avg"]
        final_avg_score = final["composite_scores"]["avg"]
        score_change = final_avg_score - initial_avg_score
        
        print(f"\n   🎯 综合评分趋势:")
        print(f"     初始平均评分: {initial_avg_score:.3f}")
        print(f"     最终平均评分: {final_avg_score:.3f}")
        print(f"     变化: {score_change:+.3f}")
        
        if score_change > 0.1:
            print(f"     ✅ 综合评分显著提升")
        elif score_change > 0:
            print(f"     ⚠️  综合评分轻微提升")
        elif score_change == 0:
            print(f"     ⚠️  综合评分稳定")
        else:
            print(f"     ❌ 综合评分下降")
        
        # 6. 进化状态判断
        print(f"\n   🎯 进化状态判断:")
        
        judgments = []
        
        # 判断1: 是否有持续淘汰
        if total_eliminations > 0:
            judgments.append("✅ 淘汰持续发生")
        else:
            judgments.append("❌ 淘汰未发生")
        
        # 判断2: Fitness是否增加
        if fitness_change > 0.02:
            judgments.append("✅ Fitness差异增加")
        elif fitness_change > 0:
            judgments.append("⚠️  Fitness差异轻微增加")
        else:
            judgments.append("❌ Fitness差异未增加")
        
        # 判断3: 多样性是否健康
        if final_diversity >= 3:
            judgments.append("✅ 多样性健康")
        else:
            judgments.append("❌ 多样性不足")
        
        # 判断4: 使用率是否分化
        if final_usage_std > 0.1:
            judgments.append("✅ 使用率分化")
        elif final_usage_std > 0.05:
            judgments.append("⚠️  使用率轻微分化")
        else:
            judgments.append("❌ 使用率未分化")
        
        # 判断5: 综合评分是否提升
        if score_change > 0.05:
            judgments.append("✅ 综合评分提升")
        elif score_change > 0:
            judgments.append("⚠️  综合评分轻微提升")
        else:
            judgments.append("❌ 综合评分未提升")
        
        for judgment in judgments:
            print(f"     {judgment}")
        
        # 最终状态
        passed_judgments = sum(1 for j in judgments if j.startswith("✅"))
        total_judgments = len(judgments)
        
        print(f"\n   🎯 最终进化状态:")
        if passed_judgments >= 4:
            print(f"     🎉 系统健康进化中!")
            print(f"     💡 建议: 可以进入下一阶段")
        elif passed_judgments >= 3:
            print(f"     ⚠️  系统部分进化")
            print(f"     💡 建议: 需要更多优化")
        else:
            print(f"     ❌ 系统进化不足")
            print(f"     💡 建议: 检查淘汰机制")
        
        print(f"     通过率: {passed_judgments}/{total_judgments} ({passed_judgments/total_judgments:.0%})")
        
        # 保存分析结果
        self.consolidation_data["evolution_analysis"] = {
            "fitness_change": fitness_change,
            "total_eliminations": total_eliminations,
            "total_recoveries": total_recoveries,
            "diversity_change": diversity_change,
            "usage_std_change": usage_std_change,
            "score_change": score_change,
            "judgments": judgments,
            "passed_judgments": passed_judgments,
            "total_judgments": total_judgments
        }
    
    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) <= 1:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def save_consolidation_report(self):
        """保存巩固报告"""
        report_path = "/Users/liugang/.openclaw/workspace/elimination_consolidation_report.json"
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.consolidation_data, f, indent=2, ensure_ascii=False)
            print(f"\n📄 巩固报告已保存: {report_path}")
        except Exception as e:
            print(f"❌ 报告保存失败: {e}")
    
    def print_final_summary(self):
        """打印最终总结"""
        print("\n" + "=" * 70)
        print("📊 淘汰周期巩固最终总结")
        print("=" * 70)
        
        if "evolution_analysis" not in self.consolidation_data:
            print("⚠️  无进化分析数据")
            return
        
        analysis = self.consolidation_data["evolution_analysis"]
        initial = self.consolidation_data["initial_state"]
        final = self.consolidation_data["final_state"]
        
        print(f"🎯 巩固成果:")
        print(f"   淘汰周期数: {len(self.consolidation_data['cycles'])}")
        print(f"   总查询数: {sum(c['results']['num_queries'] for c in self.consolidation_data['cycles'])}")
        print(f"   总淘汰策略: {analysis['total_eliminations']}个")
        print(f"   总恢复策略: {analysis['total_recoveries']}个")
        
        print(f"\n📈 关键指标变化:")
        print(f"   Fitness差异: {initial['fitness_range']['diff']:.3f} → {final['fitness_range']['diff']:.3f} (Δ{analysis['fitness_change']:+.3f})")
        print(f"   使用率分化: {initial['usage_std']:.3f} → {final['usage_std']:.3f} (Δ{analysis['usage_std_change']:+.3f})")
        print(f"   综合评分: {initial['composite_scores']['avg']:.3f} → {final['composite_scores']['avg']:.3f} (Δ{analysis['score_change']:+.3f})")
        print(f"   策略多样性: {initial['active_strategies']} → {final['active_strategies']} (Δ{analysis['diversity_change']:+d})")
        
        print(f"\n✅ 阈值调整:")
        adjustments = self.consolidation_data.get("threshold_adjustments", [])
        if adjustments:
            for adj in adjustments[:3]:  # 只显示前3个调整
                print(f"   {adj['parameter']}: {adj['old_value']:.3f} → {adj['new_value']:.3f}")
        else:
            print(f"   无调整")
        
        print(f"\n🎯 进化状态:")
        print(f"   通过率: {analysis['passed_judgments']}/{analysis['total_judgments']} ({analysis['passed_judgments']/analysis['total_judgments']:.0%})")
        
        if analysis['passed_judgments'] >= 4:
            print(f"   🎉 结论: 淘汰机制稳定，进化健康")
            print(f"   💡 建议: 可以开始设计策略强化机制")
        elif analysis['passed_judgments'] >= 3:
            print(f"   ⚠️  结论: 淘汰机制部分工作")
            print(f"   💡 建议: 需要更多优化")
        else:
            print(f"   ❌ 结论: 淘汰机制需要改进")
            print(f"   💡 建议: 重新评估淘汰阈值")

def main():
    """主函数"""
    print("🚀 开始淘汰周期巩固...")
    
    # 创建巩固器
    consolidator = EliminationCycleConsolidator()
    
    # 运行巩固周期
    print("\n" + "=" * 70)
    print("🔄 执行淘汰周期巩固")
    print("=" * 70)
    
    results = consolidator.run_consolidation_cycles()
    
    # 保存报告
    consolidator.save_consolidation_report()
    
    # 显示最终总结
    consolidator.print_final_summary()
    
    # 显示最终监测报告
    print("\n" + "=" * 70)
    print("📊 最终淘汰监测报告")
    print("=" * 70)
    
    consolidator.monitor.print_monitoring_report()
    
    print("\n" + "=" * 70)
    print("🎉 淘汰周期巩固完成!")
    print("=" * 70)
    
    return consolidator

if __name__ == "__main__":
    main()