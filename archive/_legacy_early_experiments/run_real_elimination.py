#!/usr/bin/env python3
"""
运行真正的淘汰监测 - 使用实际实验数据
"""

import os
import sys
import json
from datetime import datetime

# 添加路径
workspace_dir = os.path.expanduser("~/.openclaw/workspace")
sys.path.insert(0, workspace_dir)

def load_actual_strategy_data():
    """加载实际策略数据"""
    print("📂 加载实际策略数据...")
    
    try:
        # 从巩固实验报告加载数据
        report_path = "/Users/liugang/.openclaw/workspace/evolution_consolidation_report.json"
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        final_state = report["final_state"]
        
        print(f"✅ 加载成功:")
        print(f"   策略数量: {len(final_state['strategies'])}")
        print(f"   Fitness范围: {final_state['fitness_range']['min']:.3f} - {final_state['fitness_range']['max']:.3f}")
        print(f"   Fitness差异: {final_state['fitness_range']['diff']:.3f}")
        
        return final_state
        
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return None

def create_strategy_engine_with_actual_data(final_state):
    """创建包含实际数据的策略引擎"""
    print("\n🔧 创建包含实际数据的策略引擎...")
    
    try:
        from cognitive_adapter.real_world_strategy import RealWorldStrategyEngine
        
        # 创建策略引擎
        engine = RealWorldStrategyEngine()
        
        # 更新策略数据
        for strategy_data in final_state["strategies"]:
            strategy_name = strategy_data["name"]
            
            if strategy_name in engine.strategies:
                strategy = engine.strategies[strategy_name]
                
                # 更新Fitness
                strategy.fitness_score = strategy_data["fitness"]
                
                # 更新使用次数
                strategy.metrics["usage_count"] = strategy_data["usage_count"]
                
                # 更新其他指标
                strategy.metrics["real_world_accuracy"] = [strategy_data["avg_accuracy"]] * 10  # 模拟历史数据
                strategy.metrics["cost"] = [strategy_data["avg_cost"]] * 10
                strategy.metrics["success_rate"] = [strategy_data["success_rate"]] * 10
                
                print(f"   ✅ 更新策略 {strategy_name}:")
                print(f"      适应度: {strategy.fitness_score:.3f}")
                print(f"      使用次数: {strategy.metrics['usage_count']}")
                print(f"      平均准确率: {strategy_data['avg_accuracy']:.3f}")
        
        return engine
        
    except Exception as e:
        print(f"❌ 策略引擎创建失败: {e}")
        return None

def run_real_elimination_monitoring():
    """运行真正的淘汰监测"""
    print("\n" + "=" * 70)
    print("⚰️ 运行真正的淘汰监测")
    print("=" * 70)
    
    # 1. 加载实际数据
    final_state = load_actual_strategy_data()
    if not final_state:
        print("❌ 无法加载实际数据，退出")
        return
    
    # 2. 创建包含实际数据的策略引擎
    engine = create_strategy_engine_with_actual_data(final_state)
    if not engine:
        print("❌ 无法创建策略引擎，退出")
        return
    
    # 3. 创建淘汰监测器
    from strategy_elimination_monitor import StrategyEliminationMonitor
    monitor = StrategyEliminationMonitor(strategy_engine=engine)
    
    # 4. 显示初始状态
    print("\n📊 初始策略状态:")
    strategies = list(engine.strategies.values())
    strategies_sorted = sorted(strategies, key=lambda x: x.fitness_score, reverse=True)
    
    for i, strategy in enumerate(strategies_sorted, 1):
        status = "🏆" if i == 1 else "📈" if i <= 3 else "⚠️"
        print(f"   {i}. {status} {strategy.name}")
        print(f"      适应度: {strategy.fitness_score:.3f}")
        print(f"      使用次数: {strategy.metrics.get('usage_count', 0)}")
        print(f"      类型: {'🌍 现实数据' if strategy.uses_real_data else '🧠 模拟数据'}")
    
    # 5. 检查淘汰候选（基于实际数据）
    print("\n🔍 检查淘汰候选（基于实际数据）...")
    candidates = monitor.check_elimination_candidates()
    
    if candidates:
        print(f"✅ 找到 {len(candidates)} 个淘汰候选:")
        
        for i, (strategy_name, composite_score, elimination_reason) in enumerate(candidates, 1):
            strategy = engine.strategies[strategy_name]
            
            # 计算使用率
            total_usage = sum(s.metrics.get("usage_count", 0) for s in strategies)
            usage_rate = 0.0
            if total_usage > 0:
                usage_rate = strategy.metrics.get("usage_count", 0) / total_usage
            
            print(f"\n   {i}. ❌ {strategy_name}")
            print(f"      综合评分: {composite_score:.3f}")
            print(f"      适应度: {strategy.fitness_score:.3f}")
            print(f"      使用率: {usage_rate:.1%}")
            print(f"      淘汰原因: {list(elimination_reason.keys())}")
            
            # 显示具体原因
            for reason_key, reason_data in elimination_reason.items():
                if reason_key == "low_usage":
                    print(f"        - 使用率过低: {reason_data['usage_rate']:.1%} < {reason_data['threshold']:.0%}")
                elif reason_key == "low_fitness":
                    print(f"        - 适应度过低: {reason_data['fitness']:.3f} < {reason_data['threshold']:.3f}")
                elif reason_key == "low_composite_score":
                    print(f"        - 综合评分过低: {reason_data['score']:.3f} < {reason_data['threshold']}")
        
        # 6. 执行淘汰
        print("\n⚰️ 执行淘汰...")
        elimination_limit = monitor.elimination_config["elimination_batch_size"]
        eliminated_count = 0
        
        for strategy_name, composite_score, elimination_reason in candidates:
            if eliminated_count >= elimination_limit:
                break
            
            if monitor.eliminate_strategy(strategy_name, elimination_reason):
                eliminated_count += 1
        
        print(f"✅ 淘汰完成: 淘汰了 {eliminated_count} 个策略")
        
    else:
        print("✅ 未找到淘汰候选 - 所有策略表现良好")
    
    # 7. 运行一个淘汰周期（包含真实查询）
    print("\n🔄 运行淘汰周期（包含真实查询）...")
    cycle_results = monitor.run_elimination_cycle(num_queries=50)
    
    print(f"\n📊 周期结果:")
    print(f"   淘汰候选: {cycle_results['elimination_candidates_found']}个")
    print(f"   淘汰策略: {len(cycle_results['strategies_eliminated'])}个")
    print(f"   恢复候选: {cycle_results['recovery_candidates_found']}个")
    print(f"   恢复策略: {len(cycle_results['strategies_recovered'])}个")
    
    # 8. 显示最终监测报告
    print("\n" + "=" * 70)
    print("📊 最终淘汰监测报告")
    print("=" * 70)
    
    monitor.print_monitoring_report()
    
    # 9. 保存详细报告
    report_path = "/Users/liugang/.openclaw/workspace/real_elimination_report.json"
    try:
        full_report = {
            "timestamp": datetime.now().isoformat(),
            "initial_state": final_state,
            "elimination_results": cycle_results,
            "monitoring_report": monitor.get_monitoring_report(),
            "candidates_analysis": [
                {
                    "strategy_name": name,
                    "composite_score": score,
                    "elimination_reason": reason
                }
                for name, score, reason in (candidates if candidates else [])
            ]
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 详细报告已保存: {report_path}")
        
    except Exception as e:
        print(f"❌ 报告保存失败: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 真正的淘汰监测完成!")
    print("=" * 70)
    
    return monitor

def main():
    """主函数"""
    print("🚀 开始真正的淘汰监测...")
    
    monitor = run_real_elimination_monitoring()
    
    # 显示关键结论
    if monitor:
        print("\n🎯 关键结论:")
        
        report = monitor.get_monitoring_report()
        tracking = report["performance_tracking"]
        
        if tracking["strategies_marked_for_elimination"] > 0:
            print("   ✅ 淘汰机制成功激活")
            print("   ✅ 系统开始真正的'进化'阶段")
            print("   ✅ 低效策略被识别和标记")
        else:
            print("   ⚠️  淘汰机制未激活")
            print("   ⚠️  可能需要调整淘汰阈值")
        
        # 检查是否有策略被淘汰
        eliminated_count = len(monitor.eliminated_strategies)
        if eliminated_count > 0:
            print(f"   ✅ {eliminated_count} 个策略被标记淘汰")
            print("   🎉 系统正在经历真正的'淘汰'过程")
        else:
            print("   ⚠️  尚无策略被淘汰")
            print("   💡 建议: 可能需要更激进的淘汰阈值")
        
        # 进化阶段判断
        active_strategies = report["strategy_status"]["active_strategies"]
        if active_strategies >= 3:
            print(f"   ✅ 系统保持健康多样性 ({active_strategies}个活跃策略)")
        else:
            print(f"   ⚠️  系统多样性可能不足 ({active_strategies}个活跃策略)")

if __name__ == "__main__":
    main()