#!/usr/bin/env python3
"""
200轮黄金测试 - 验证系统长期稳定性
严格按照黄金测试规范执行：
1. 不允许中途重启
2. 不允许手动干预
3. 必须完整跑完200轮
"""

import sys
sys.path.append('.')

print("🚀 200轮黄金测试 - 系统长期稳定性验证")
print("="*60)
print("测试规范：")
print("1. ✅ 不允许中途重启")
print("2. ✅ 不允许手动干预")
print("3. ✅ 必须完整跑完200轮")
print("="*60)

from evaluation_framework import ReplayRunner, TestScenarios
import json
import time
from datetime import datetime
import os

# 创建修复版的ReplayRunner（使用修复后的系统）
print("\n1. 创建修复版ReplayRunner...")

class FixedReplayRunner(ReplayRunner):
    """修复版ReplayRunner，使用完全修复的系统"""
    
    def _init_system(self):
        """初始化系统组件（使用修复后的配置）"""
        from global_graph import GlobalGraph, NodeType, EdgeType
        from simple_semantic_parser import SimpleSemanticParser
        from active_subgraph import ActiveSubgraphEngine
        from active_set import ActiveSetEngine
        from reflection_upgrade import ReflectionEngine
        from learning_guard import LearningGuard
        
        # 创建全局图
        self.global_graph = GlobalGraph()
        
        # 创建语义解析器
        self.semantic_parser = SimpleSemanticParser()
        
        # 创建Active Subgraph引擎
        self.active_subgraph_engine = ActiveSubgraphEngine(self.global_graph)
        
        # 创建Active Set引擎
        self.active_set_engine = ActiveSetEngine(self.global_graph)
        
        # 创建Reflection引擎（使用优化配置）
        reflection_config = {
            "min_pattern_frequency": 2,
            "min_pattern_weight": 0.1,
            "confidence_weights": {
                "frequency": 0.3,
                "consistency": 0.4,
                "recency": 0.3
            },
            "confidence_threshold": 0.3,
            "max_diffs_per_reflection": 3,
            "reinforce_delta": 0.15,
            "decay_delta": -0.05,
            "conflict_threshold": 0.4,
            "debug": False,  # 关闭调试以提高性能
            "dry_run": False
        }
        
        self.reflection_engine = ReflectionEngine(self.global_graph, reflection_config)
        
        # 创建Learning Guard（优化配置）
        learning_guard_config = {
            "consistency_threshold": 0.3,
            "stability_threshold": 0.2,
            "novelty_threshold": 0.1,
            "buffer_size": 20,
            "debug": False
        }
        
        self.learning_guard = LearningGuard(self.global_graph, learning_guard_config)

# 创建测试脚本
print("\n2. 创建测试脚本...")
script = TestScenarios.topic_switch_test(10)  # 10个循环 = 200轮
print(f"   脚本长度: {len(script)}轮")
print(f"   话题数量: 10个不同话题")
print(f"   循环次数: 10次")

# 创建修复版执行器
print("\n3. 创建修复版执行器...")
runner = FixedReplayRunner()

# 记录开始时间
start_time = time.time()
start_datetime = datetime.fromtimestamp(start_time)
print(f"   开始时间: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

# 创建结果目录
os.makedirs("golden_test_results", exist_ok=True)
result_file = f"golden_test_results/golden_200_{start_datetime.strftime('%Y%m%d_%H%M%S')}.json"

# 运行200轮测试
print("\n4. 运行200轮黄金测试...")
print("-"*40)

results = []
checkpoint_times = []

for turn_id, query in enumerate(script):
    # 每20轮输出一次进度
    if turn_id % 20 == 0:
        checkpoint_time = time.time()
        elapsed = checkpoint_time - start_time
        checkpoint_times.append((turn_id, checkpoint_time))
        
        print(f"   进度: {turn_id}/{len(script)}轮 "
              f"({turn_id/len(script)*100:.1f}%) "
              f"耗时: {elapsed:.1f}秒")
    
    # 执行一轮
    result = runner.step(query)
    results.append(result)
    
    # 每50轮保存一次检查点
    if turn_id % 50 == 0 and turn_id > 0:
        checkpoint_data = {
            "turn": turn_id,
            "timestamp": datetime.now().isoformat(),
            "graph": {
                "nodes": len(runner.global_graph.nodes),
                "edges": len([e for e in runner.global_graph.edges.values() if hasattr(e, 'active') and e.active])
            },
            "reflection": {
                "patterns": len(runner.reflection_engine.patterns) if hasattr(runner.reflection_engine, 'patterns') else 0,
                "diffs_generated": runner.reflection_engine.stats.get("diffs_generated", 0) if hasattr(runner.reflection_engine, 'stats') else 0,
                "diffs_applied": runner.reflection_engine.stats.get("diffs_applied", 0) if hasattr(runner.reflection_engine, 'stats') else 0
            }
        }
        
        checkpoint_file = f"golden_test_results/checkpoint_{turn_id}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)

# 记录结束时间
end_time = time.time()
duration = end_time - start_time
print(f"\n   结束时间: {datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')}")
print(f"   总耗时: {duration:.1f}秒")
print(f"   平均每轮: {duration/len(script)*1000:.1f}毫秒")

# 计算统计信息
print("\n5. 计算统计信息...")
print("-"*40)

total_success = sum(1 for r in results if r["success"])
total_diffs_generated = sum(r.get("diffs_generated", 0) for r in results)
total_diffs_applied = sum(r.get("diffs_applied", 0) for r in results)
total_errors = sum(1 for r in results if not r["success"])

print(f"   总轮数: {len(results)}")
print(f"   成功轮数: {total_success}")
print(f"   失败轮数: {total_errors}")
print(f"   Diff生成总数: {total_diffs_generated}")
print(f"   Diff应用总数: {total_diffs_applied}")

if total_diffs_generated > 0:
    write_ratio = total_diffs_applied / total_diffs_generated
    print(f"   写入率: {write_ratio:.3f}")
else:
    write_ratio = 0.0
    print(f"   写入率: 0.000")

# 检查Graph状态
print("\n6. Graph状态检查...")
print("-"*40)

graph_nodes = len(runner.global_graph.nodes)
graph_edges = len([e for e in runner.global_graph.edges.values() if hasattr(e, 'active') and e.active])

print(f"   Graph节点数: {graph_nodes}")
print(f"   Graph边数: {graph_edges}")
print(f"   Graph增长率: {graph_edges/len(script)*100:.2f}%")

# 检查Reflection统计
print("\n7. Reflection统计...")
print("-"*40)

if hasattr(runner.reflection_engine, 'stats'):
    stats = runner.reflection_engine.stats
    print(f"   总反射次数: {stats.get('total_reflections', 0)}")
    print(f"   模式提取次数: {stats.get('patterns_extracted', 0)}")
    print(f"   冲突检测次数: {stats.get('conflicts_detected', 0)}")
    print(f"   Diff生成次数: {stats.get('diffs_generated', 0)}")
    print(f"   Diff应用次数: {stats.get('diffs_applied', 0)}")
    
    if stats.get('diffs_generated', 0) > 0:
        avg_confidence = stats.get('avg_confidence', 0)
        print(f"   平均置信度: {avg_confidence:.3f}")

# 检查Learning Guard统计
print("\n8. Learning Guard统计...")
print("-"*40)

if hasattr(runner.learning_guard, 'stats'):
    stats = runner.learning_guard.stats
    print(f"   总验证次数: {stats.get('total_validations', 0)}")
    print(f"   接受Diff数: {stats.get('accepted_diffs', 0)}")
    print(f"   拒绝Diff数: {stats.get('rejected_diffs', 0)}")
    print(f"   冲突检测: {stats.get('consistency_violations', 0)}")

# 系统健康评分
print("\n9. 系统健康评分...")
print("-"*40)

# 计算健康评分（0-100）
health_score = 0

# 1. 稳定性分数（0-30）
stability_score = min(30, (total_success / len(results)) * 30)
health_score += stability_score

# 2. 学习能力分数（0-30）
if total_diffs_generated > 0:
    learning_score = min(30, (total_diffs_applied / total_diffs_generated) * 30)
else:
    learning_score = 0
health_score += learning_score

# 3. Graph健康分数（0-20）
if graph_edges > 0:
    graph_score = min(20, (graph_edges / 100) * 20)  # 假设100边为健康上限
else:
    graph_score = 0
health_score += graph_score

# 4. 性能分数（0-20）
if duration > 0:
    performance_score = min(20, (100 / (duration / len(results))) * 20)  # 假设100ms/轮为健康
else:
    performance_score = 0
health_score += performance_score

print(f"   稳定性分数: {stability_score:.1f}/30")
print(f"   学习能力分数: {learning_score:.1f}/30")
print(f"   Graph健康分数: {graph_score:.1f}/20")
print(f"   性能分数: {performance_score:.1f}/20")
print(f"   🏥 系统健康总分: {health_score:.1f}/100")

# 保存完整结果
print("\n10. 保存完整结果...")
print("-"*40)

final_result = {
    "test_name": "golden_200_rounds",
    "start_time": start_datetime.isoformat(),
    "end_time": datetime.now().isoformat(),
    "duration_seconds": duration,
    "total_turns": len(results),
    "success_rate": total_success / len(results),
    "graph": {
        "nodes": graph_nodes,
        "edges": graph_edges,
        "growth_rate": graph_edges / len(results)
    },
    "reflection": {
        "generated": total_diffs_generated,
        "applied": total_diffs_applied,
        "write_ratio": write_ratio,
        "patterns_count": len(runner.reflection_engine.patterns) if hasattr(runner.reflection_engine, 'patterns') else 0
    },
    "learning_guard": {
        "accepted": runner.learning_guard.stats.get('accepted_diffs', 0) if hasattr(runner.learning_guard, 'stats') else 0,
        "rejected": runner.learning_guard.stats.get('rejected_diffs', 0) if hasattr(runner.learning_guard, 'stats') else 0,
        "conflicts": runner.learning_guard.stats.get('consistency_violations', 0) if hasattr(runner.learning_guard, 'stats') else 0
    },
    "health_score": health_score,
    "health_breakdown": {
        "stability": stability_score,
        "learning": learning_score,
        "graph": graph_score,
        "performance": performance_score
    },
    "checkpoints": [
        {"turn": turn, "time": time} for turn, time in checkpoint_times
    ],
    "config_note": "使用修复后的extract_patterns方法，优化配置",
    "system_version": "v1.0-fixed"
}

with open(result_file, 'w', encoding='utf-8') as f:
    json.dump(final_result, f, ensure_ascii=False, indent=2)

print(f"   结果已保存到: {result_file}")
print(f"   文件大小: {os.path.getsize(result_file)}字节")

print("\n" + "="*60)
print("🎯 200轮黄金测试完成")
print("="*60)

# 最终结论
print("\n📊 最终结论:")

if health_score >= 80:
    print("✅ 系统长期稳定性验证通过！")
    print("✅ 系统在200轮测试中表现稳定")
    print("✅ 学习管道持续工作")
    print("✅ 系统健康状态优秀")
    
    print("\n📈 关键成就:")
    print(f"   1. 成功率: {total_success/len(results)*100:.1f}%")
    print(f"   2. 写入率: {write_ratio:.3f}")
    print(f"   3. Graph增长: {graph_edges}边")
    print(f"   4. 健康评分: {health_score:.1f}/100")
    
elif health_score >= 60:
    print("⚠️  系统基本稳定，但有改进空间")
    print("⚠️  部分指标需要优化")
    
else:
    print("❌ 系统稳定性存在问题")
    print("❌ 需要进一步调试和优化")

print(f"\n📁 结果文件: {result_file}")
print("📊 健康评分:", f"{health_score:.1f}/100")
print("⏱️  总耗时:", f"{duration:.1f}秒")
print("🔄 平均每轮:", f"{duration/len(results)*1000:.1f}毫秒")