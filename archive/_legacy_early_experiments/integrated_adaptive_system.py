#!/usr/bin/env python3
"""
集成自适应学习系统
将Phase Switch集成到现有学习管道中
"""

import sys
sys.path.append('.')

print("🔧 集成自适应学习系统")
print("="*60)
print("目标：将Phase Switch集成到学习管道中")
print("核心：在Reflection入口处插入阶段控制")
print("="*60)

from adaptive_learning_system import AdaptiveLearningSystem, LearningPhase
from global_graph import GlobalGraph, NodeType, EdgeType
from simple_semantic_parser import SimpleSemanticParser
from active_subgraph import ActiveSubgraphEngine
from active_set import ActiveSetEngine, ActiveSet
from reflection_upgrade import ReflectionEngine
from learning_guard import LearningGuard
import time

class AdaptiveReplayRunner:
    """集成自适应学习系统的Replay Runner"""
    
    def __init__(self):
        # 自适应学习系统
        self.adaptive_system = AdaptiveLearningSystem()
        
        # 核心组件
        self.global_graph = GlobalGraph()
        self.semantic_parser = SimpleSemanticParser()
        self.active_subgraph_engine = ActiveSubgraphEngine(self.global_graph)
        self.active_set_engine = ActiveSetEngine(self.global_graph)
        
        # Reflection和Learning Guard（初始使用冷启动配置）
        self.reflection_engine = None
        self.learning_guard = None
        
        # 初始化组件
        self._init_components()
        
        # 统计
        self.total_rounds = 0
        self.successful_rounds = 0
        
    def _init_components(self):
        """初始化组件（使用自适应配置）"""
        # 获取当前配置
        reflection_config = self.adaptive_system.get_config_for_reflection()
        learning_guard_config = self.adaptive_system.get_config_for_learning_guard()
        
        # 创建Reflection Engine
        self.reflection_engine = ReflectionEngine(self.global_graph, reflection_config)
        
        # 创建Learning Guard
        self.learning_guard = LearningGuard(self.global_graph, learning_guard_config)
        
        print(f"   ✅ 初始化组件完成")
        print(f"      当前阶段: {self.adaptive_system.phase_detector.current_phase.value}")
        print(f"      配置: buffer_size={learning_guard_config['buffer_size']}, "
              f"conf_threshold={reflection_config['confidence_threshold']}")
    
    def _update_components_config(self):
        """更新组件配置（当阶段切换时）"""
        # 获取新配置
        reflection_config = self.adaptive_system.get_config_for_reflection()
        learning_guard_config = self.adaptive_system.get_config_for_learning_guard()
        
        # 更新Reflection Engine配置
        self.reflection_engine.config.update(reflection_config)
        
        # 更新Learning Guard配置
        self.learning_guard.config.update(learning_guard_config)
        
        print(f"   🔄 组件配置已更新")
        print(f"      新配置: buffer_size={learning_guard_config['buffer_size']}, "
              f"conf_threshold={reflection_config['confidence_threshold']}")
    
    def step(self, query: str) -> Dict[str, Any]:
        """单步执行（集成自适应控制）"""
        self.total_rounds += 1
        
        try:
            print(f"\n   第 {self.total_rounds} 轮: {query}")
            
            # 1. 语义解析
            parsed = self.semantic_parser.parse(query)
            if not parsed:
                print(f"     ❌ 语义解析失败")
                return {"success": False, "error": "语义解析失败"}
            
            print(f"     ✅ 语义解析: {parsed['subject']} -> {parsed['relation']} -> {parsed['object']}")
            
            # 2. 添加到Graph
            subject_id = self.global_graph.create_node(parsed["subject"], NodeType.USER)
            object_id = self.global_graph.create_node(parsed["object"], NodeType.TOPIC)
            
            # 映射关系类型
            relation = parsed["relation"]
            edge_type = EdgeType.MENTIONED
            
            if relation == "LIKES":
                edge_type = EdgeType.LIKES
            elif relation == "INVESTED_IN":
                edge_type = EdgeType.INVESTED_IN
            elif relation == "ASKING_ABOUT":
                edge_type = EdgeType.ASKING_ABOUT
            elif relation == "LEARNING":
                edge_type = EdgeType.LEARNING
            elif relation == "INTERESTED_IN":
                edge_type = EdgeType.INTERESTED_IN
            
            confidence = parsed.get("confidence", 0.6)
            self.global_graph.update_edge(subject_id, object_id, edge_type, confidence)
            print(f"     ✅ Graph更新: 添加边 {edge_type.value}")
            
            # 3. 构建系统状态（用于阶段检测）
            state = self.adaptive_system.build_system_state(
                self.global_graph, 
                self.reflection_engine, 
                self.learning_guard
            )
            
            # 4. 更新学习阶段（自适应控制核心）
            old_phase = self.adaptive_system.phase_detector.current_phase
            phase = self.adaptive_system.update_phase(state)
            
            # 检查阶段是否切换
            if phase != old_phase:
                print(f"     🔄 阶段切换: {old_phase.value} → {phase.value}")
                # 更新组件配置
                self._update_components_config()
            
            # 打印阶段状态（每5轮一次）
            if self.total_rounds % 5 == 0:
                self.adaptive_system.print_phase_status(phase, state)
            
            # 5. 构建Active Set
            active_set = self.active_set_engine.build_active_set(query)
            
            # 6. Reflection（使用当前阶段配置）
            diffs = self.reflection_engine.reflect(active_set)
            
            if diffs:
                print(f"     ✅ Reflection生成 {len(diffs)} 个Diff")
                
                # 7. Learning Guard验证（使用当前阶段配置）
                validated_diffs = []
                for diff in diffs:
                    result = self.learning_guard.validate_diff(diff, {"source": "adaptive", "query": query})
                    
                    action = result.suggested_action
                    if hasattr(result, 'reasons'):
                        reason = result.reasons[0] if result.reasons else "无原因"
                    else:
                        reason = "无原因信息"
                    
                    print(f"       Learning Guard: {action} (置信度: {result.confidence:.2f}, 原因: {reason})")
                    
                    if action == "accept":
                        validated_diffs.append(diff)
                
                print(f"     ✅ 验证通过: {len(validated_diffs)} 个Diff")
            else:
                print(f"     ⚠️  无Diff生成")
            
            self.successful_rounds += 1
            
            return {
                "success": True,
                "diffs_generated": len(diffs),
                "diffs_applied": len(validated_diffs),
                "phase": phase.value,
                "state": state
            }
            
        except Exception as e:
            print(f"     ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        report = self.adaptive_system.get_system_report()
        report.update({
            "total_rounds": self.total_rounds,
            "success_rate": self.successful_rounds / self.total_rounds if self.total_rounds > 0 else 0,
            "graph_size": len(self.global_graph.nodes),
            "edge_count": len([e for e in self.global_graph.edges.values() if hasattr(e, 'active') and e.active])
        })
        return report

# 运行集成测试
print("\n1. 创建集成自适应系统...")
runner = AdaptiveReplayRunner()

# 创建测试查询（模拟从冷启动到稳定的过程）
print("\n2. 创建测试查询...")
test_queries = []

# 阶段1: 冷启动（前20轮）
cold_start_queries = [
    "我喜欢日本房产",
    "我想投资AI",
    "机器学习怎么学？",
    "Python编程入门",
    "深度学习原理"
]

# 重复4次，共20轮
for i in range(4):
    for query in cold_start_queries:
        test_queries.append(query)

# 阶段2: 稳定学习（后20轮）
stable_queries = [
    "日本房产投资回报率",
    "AI创业市场分析",
    "机器学习算法比较",
    "Python高级特性",
    "神经网络优化"
]

# 重复4次，共20轮
for i in range(4):
    for query in stable_queries:
        test_queries.append(query)

print(f"   总测试轮数: {len(test_queries)}")
print(f"   预期: 前20轮冷启动，后20轮稳定学习")

# 运行测试
print("\n3. 运行集成测试...")
print("-"*40)

start_time = time.time()
results = []

for i, query in enumerate(test_queries):
    result = runner.step(query)
    results.append(result)
    
    # 每10轮输出一次进度
    if (i + 1) % 10 == 0:
        elapsed = time.time() - start_time
        print(f"\n   📊 进度: {i+1}/{len(test_queries)}轮 "
              f"({(i+1)/len(test_queries)*100:.1f}%) "
              f"耗时: {elapsed:.1f}秒")

# 生成最终报告
print("\n4. 生成最终报告...")
print("-"*40)

report = runner.get_system_report()

print(f"\n   🎯 自适应学习系统报告")
print(f"   =======================")
print(f"   总轮数: {report['total_rounds']}")
print(f"   成功率: {report['success_rate']:.1%}")
print(f"   Graph大小: {report['graph_size']}节点, {report['edge_count']}边")

print(f"\n   📊 阶段信息")
phase_info = report['current_phase']
print(f"   当前阶段: {phase_info['phase']}")
print(f"   阶段持续时间: {phase_info['phase_duration']}轮")
print(f"   阶段切换次数: {phase_info['phase_switch_count']}")
print(f"   稳定轮数: {phase_info['stable_rounds']}")
print(f"   是否锁定: {'✅ 是' if phase_info['is_locked'] else '❌ 否'}")

print(f"\n   📈 系统状态")
state = report['system_state']
print(f"   Graph边数: {state['total_edges']}")
print(f"   应用Diff数: {state['total_applied_diffs']}")
print(f"   模式置信度: {state['avg_pattern_confidence']:.3f}")
print(f"   写入率: {state['write_ratio']:.3f}")
print(f"   每轮边数: {state['edges_per_round']:.2f}")
print(f"   每轮Diff数: {state['diffs_per_round']:.2f}")

print(f"\n   📋 阶段指标")
phase_metrics = report['phase_metrics']
print(f"   冷启动轮数: {phase_metrics['cold_start_rounds']}")
print(f"   稳定轮数: {phase_metrics['stable_rounds']}")
print(f"   总切换次数: {phase_metrics['total_transitions']}")

print(f"\n   📊 阶段平均写入率")
for phase, avg_ratio in phase_metrics['avg_write_ratio_by_phase'].items():
    print(f"   {phase}: {avg_ratio:.3f}")

# 验证阶段切换效果
print("\n5. 验证阶段切换效果...")
print("-"*40)

# 检查是否成功从冷启动切换到稳定
if phase_info['phase'] == 'stable' and phase_info['phase_duration'] > 5:
    print(f"   ✅ 成功从冷启动切换到稳定阶段！")
    print(f"   ✅ 稳定阶段已持续 {phase_info['phase_duration']} 轮")
    
    # 检查写入率变化
    cold_start_ratio = phase_metrics['avg_write_ratio_by_phase'].get('cold_start', 0)
    stable_ratio = phase_metrics['avg_write_ratio_by_phase'].get('stable', 0)
    
    if cold_start_ratio > stable_ratio:
        print(f"   ✅ 写入率变化符合预期:")
        print(f"      冷启动阶段: {cold_start_ratio:.3f} (高)")
        print(f"      稳定阶段: {stable_ratio:.3f} (低)")
    else:
        print(f"   ⚠️  写入率变化不明显")
else:
    print(f"   ⚠️  系统仍在冷启动阶段")
    print(f"      可能需要更多轮次或调整阈值")

print("\n" + "="*60)
print("🎯 集成测试完成")
print("="*60)

print(f"\n🕐 总耗时: {time.time() - start_time:.1f}秒")
print(f"📊 最终阶段: {phase_info['phase']}")
print(f"🔄 切换次数: {phase_info['phase_switch_count']}")

# 最终结论
print("\n📋 最终结论:")
if phase_info['phase'] == 'stable' and phase_info['phase_duration'] > 5:
    print("✅ 自适应学习系统工作正常！")
    print("✅ 成功实现冷启动 → 稳定学习切换")
    print("✅ 系统现在具备自适应学习能力")
    
    print("\n💡 关键成就:")
    print("   1. ✅ 自动阶段检测")
    print("   2. ✅ 动态配置切换")
    print("   3. ✅ 阶段锁定机制")
    print("   4. ✅ 完整指标跟踪")
    
    print("\n🚀 系统已升级为:")
    print("   ❗ Adaptive Continual Learning System")
    
    print("\n📊 系统能力:")
    print("   能力       状态")
    print("   学习       ✅")
    print("   控制       ✅")
    print("   可观测     ✅")
    print("   自适应     ✅")
else:
    print("⚠️  系统仍在验证中")
    print("   可能需要调整阶段检测阈值")

print(f"\n📁 下一步建议:")
print("   1. 运行更长时间测试（200+轮）")
print("   2. 调整阶段检测阈值优化切换时机")
print("   3. 添加更多系统指标")
print("   4. 实现Meta-Learning（自动调参）")