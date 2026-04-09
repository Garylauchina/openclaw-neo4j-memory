#!/usr/bin/env python3
"""
修复并测试完整系统
目标：降低阈值，让系统"活过来"
"""

import sys
sys.path.append('.')

print("🔧 修复并测试完整系统")
print("="*60)

from evaluation_framework import ReplayRunner, TestScenarios
import json
import time
from datetime import datetime

# 创建修复版的ReplayRunner
print("\n1. 创建修复版ReplayRunner...")

class FixedReplayRunner(ReplayRunner):
    """修复版ReplayRunner，使用降低的阈值"""
    
    def _init_system(self):
        """初始化系统组件（使用降低的阈值）"""
        # 创建全局图
        from global_graph import GlobalGraph, NodeType, EdgeType
        self.global_graph = GlobalGraph()
        
        # 创建语义解析器
        from simple_semantic_parser import SimpleSemanticParser
        self.semantic_parser = SimpleSemanticParser()
        
        # 创建Active Subgraph引擎
        from active_subgraph import ActiveSubgraphEngine
        self.active_subgraph_engine = ActiveSubgraphEngine(self.global_graph)
        
        # 创建Active Set引擎
        from active_set import ActiveSetEngine
        self.active_set_engine = ActiveSetEngine(self.global_graph)
        
        # 创建Reflection引擎（使用降低的阈值）
        from reflection_upgrade import ReflectionEngine
        
        # 降低阈值配置
        low_threshold_config = {
            "min_pattern_frequency": 1,      # 频率阈值降低到1
            "min_pattern_weight": 0.1,       # 权重要求降低
            "confidence_weights": {
                "frequency": 0.3,
                "consistency": 0.4,
                "recency": 0.3
            },
            "confidence_threshold": 0.3,     # 置信度阈值大幅降低
            "max_diffs_per_reflection": 3,   # 限制Diff数量
            "reinforce_delta": 0.15,         # 增强幅度
            "decay_delta": -0.05,            # 衰减幅度
            "conflict_threshold": 0.4,       # 冲突阈值降低
            "debug": True,                   # 启用调试
            "dry_run": False
        }
        
        self.reflection_engine = ReflectionEngine(self.global_graph, low_threshold_config)
        
        # 创建Learning Guard（也降低阈值）
        from learning_guard import LearningGuard
        
        learning_guard_config = {
            "consistency_threshold": 0.3,    # 一致性阈值降低
            "stability_threshold": 0.2,      # 稳定性阈值降低
            "novelty_threshold": 0.1,        # 新颖性阈值降低
            "buffer_size": 10,
            "debug": True
        }
        
        self.learning_guard = LearningGuard(self.global_graph, learning_guard_config)

# 创建测试脚本
print("\n2. 创建测试脚本...")
script = TestScenarios.topic_switch_test(2)  # 20轮测试
print(f"   脚本长度: {len(script)}轮")
print(f"   示例查询: {script[:3]}...")

# 创建修复版执行器
print("\n3. 创建修复版执行器...")
runner = FixedReplayRunner()

# 记录开始时间
start_time = time.time()
print(f"   开始时间: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}")

# 运行测试
print("\n4. 运行修复后测试...")
print("-"*40)

results = []
for turn_id, query in enumerate(script):
    if turn_id % 5 == 0:
        print(f"   处理第 {turn_id}/{len(script)} 轮: {query[:20]}...")
    
    result = runner.step(query)
    results.append(result)
    
    # 打印详细信息
    if result["success"]:
        metrics = result.get("metrics")
        if metrics:
            print(f"     ✅ 成功 | 节点:{metrics.graph_nodes} | 边:{metrics.graph_edges} | "
                  f"Diff生成:{result.get('diffs_generated', 0)} | "
                  f"Diff应用:{result.get('diffs_applied', 0)}")
    else:
        print(f"     ❌ 失败: {result.get('error', '未知错误')}")

# 记录结束时间
end_time = time.time()
duration = end_time - start_time
print(f"\n   结束时间: {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   总耗时: {duration:.1f}秒")
print(f"   平均每轮: {duration/len(script)*1000:.1f}毫秒")

# 计算统计信息
print("\n5. 统计信息...")
print("-"*40)

total_success = sum(1 for r in results if r["success"])
total_diffs_generated = sum(r.get("diffs_generated", 0) for r in results)
total_diffs_applied = sum(r.get("diffs_applied", 0) for r in results)

print(f"   总轮数: {len(results)}")
print(f"   成功轮数: {total_success}")
print(f"   Diff生成总数: {total_diffs_generated}")
print(f"   Diff应用总数: {total_diffs_applied}")

if total_diffs_generated > 0:
    write_ratio = total_diffs_applied / total_diffs_generated
    print(f"   写入率: {write_ratio:.3f}")
else:
    write_ratio = 0.0
    print(f"   写入率: 0.000 (无Diff生成)")

# 检查Graph状态
print("\n6. Graph状态检查...")
print("-"*40)

graph_nodes = len(runner.global_graph.nodes)
graph_edges = len([e for e in runner.global_graph.edges.values() if hasattr(e, 'active') and e.active])

print(f"   Graph节点数: {graph_nodes}")
print(f"   Graph边数: {graph_edges}")

# 检查Reflection统计
print("\n7. Reflection统计...")
print("-"*40)

if hasattr(runner.reflection_engine, 'stats'):
    stats = runner.reflection_engine.stats
    print(f"   模式提取次数: {stats.get('patterns_extracted', 0)}")
    print(f"   冲突检测次数: {stats.get('conflicts_detected', 0)}")
    print(f"   Diff生成次数: {stats.get('diffs_generated', 0)}")

# 检查Learning Guard统计
print("\n8. Learning Guard统计...")
print("-"*40)

if hasattr(runner.learning_guard, 'stats'):
    stats = runner.learning_guard.stats
    print(f"   总验证次数: {stats.get('total_validations', 0)}")
    print(f"   接受Diff数: {stats.get('accepted_diffs', 0)}")
    print(f"   拒绝Diff数: {stats.get('rejected_diffs', 0)}")
    print(f"   冲突检测: {stats.get('consistency_violations', 0)}")

# 系统是否"活了"的判断
print("\n9. 系统状态判断...")
print("-"*40)

system_alive = False
alive_criteria = []

# 判断标准1：Graph开始增长
if graph_edges > 0:
    alive_criteria.append(f"✅ Graph开始增长 ({graph_edges}边)")
else:
    alive_criteria.append("❌ Graph未增长")

# 判断标准2：Diff开始出现
if total_diffs_generated > 0:
    alive_criteria.append(f"✅ Diff开始出现 ({total_diffs_generated}个)")
else:
    alive_criteria.append("❌ 无Diff生成")

# 判断标准3：写入率非零
if total_diffs_generated > 0 and total_diffs_applied > 0:
    alive_criteria.append(f"✅ 写入率非零 ({write_ratio:.3f})")
else:
    alive_criteria.append("❌ 写入率为零")

# 判断标准4：冲突检测
if hasattr(runner.learning_guard, 'stats'):
    conflicts = runner.learning_guard.stats.get('consistency_violations', 0)
    if conflicts > 0:
        alive_criteria.append(f"✅ 冲突检测工作 ({conflicts}个)")
    else:
        alive_criteria.append("⚠️  无冲突检测")

# 综合判断
if graph_edges > 0 and total_diffs_generated > 0:
    system_alive = True

print("   判断标准:")
for criterion in alive_criteria:
    print(f"     {criterion}")

print(f"\n   系统状态: {'✅ 活了！' if system_alive else '❌ 未启动'}")

# 保存基准数据
print("\n10. 保存基准数据...")
print("-"*40)

import os
os.makedirs("baseline_data", exist_ok=True)
baseline_file = "baseline_data/baseline_v3_alive.json"

baseline_data = {
    "version": "v0.3-alive-test",
    "total_turns": len(results),
    "duration_seconds": duration,
    "graph": {
        "nodes": graph_nodes,
        "edges": graph_edges,
        "growth_rate": 0.0
    },
    "reflection": {
        "generated": total_diffs_generated,
        "applied": total_diffs_applied,
        "write_ratio": write_ratio
    },
    "learning_guard": {
        "accepted": runner.learning_guard.stats.get('accepted_diffs', 0) if hasattr(runner.learning_guard, 'stats') else 0,
        "rejected": runner.learning_guard.stats.get('rejected_diffs', 0) if hasattr(runner.learning_guard, 'stats') else 0,
        "conflicts": runner.learning_guard.stats.get('consistency_violations', 0) if hasattr(runner.learning_guard, 'stats') else 0
    },
    "system_alive": system_alive,
    "alive_criteria": alive_criteria,
    "timestamp": datetime.now().isoformat(),
    "config_note": "使用降低的阈值配置",
    "test_conditions": {
        "script_type": "topic_switch",
        "total_queries": len(script),
        "topics_count": 10,
        "cycles": 2,
        "with_semantic_parser": True,
        "low_thresholds": True
    }
}

with open(baseline_file, 'w', encoding='utf-8') as f:
    json.dump(baseline_data, f, ensure_ascii=False, indent=2)

print(f"   基准数据已保存到: {baseline_file}")
print(f"   文件大小: {os.path.getsize(baseline_file)}字节")

print("\n" + "="*60)
print("✅ 修复后系统测试完成")
print("="*60)

# 最终结论
print("\n🎯 最终结论:")
if system_alive:
    print("✅ 系统已成功启动！")
    print("   - Graph开始增长")
    print("   - Reflection开始工作")
    print("   - 学习管道已激活")
    print("   - 系统现在可以学习")
    
    print("\n📈 关键指标:")
    print(f"   Graph边数: {graph_edges}")
    print(f"   Diff生成: {total_diffs_generated}")
    print(f"   Diff应用: {total_diffs_applied}")
    print(f"   写入率: {write_ratio:.3f}")
    
    print("\n🚀 下一步:")
    print("1. 运行完整200轮测试")
    print("2. 监控关键曲线")
    print("3. 调整参数优化性能")
else:
    print("❌ 系统仍未启动")
    print("   - 需要进一步调试")
    print("   - 检查Reflection和Learning Guard")
    
    print("\n🔧 调试建议:")
    print("1. 检查ReflectionEngine.extract_patterns")
    print("2. 检查Learning Guard验证逻辑")
    print("3. 添加更多调试日志")

print(f"\n📁 基准文件: {baseline_file}")
print("📊 下一步：运行完整200轮黄金测试")