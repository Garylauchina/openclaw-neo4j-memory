#!/usr/bin/env python3
"""
集成Meta-Learning自优化系统
将连续自调节能力集成到学习管道中
"""

import sys
sys.path.append('.')

print("🔧 集成Meta-Learning自优化系统")
print("="*60)
print("目标：将连续自调节能力集成到学习管道")
print("核心：learning_rate连续控制 + 反馈闭环")
print("="*60)

from meta_learning_system import MetaLearningController, SystemMetrics
from global_graph import GlobalGraph, NodeType, EdgeType
from simple_semantic_parser import SimpleSemanticParser
from active_subgraph import ActiveSubgraphEngine
from active_set import ActiveSetEngine, ActiveSet
from reflection_upgrade import ReflectionEngine
from learning_guard import LearningGuard
import time

class MetaLearningReplayRunner:
    """集成Meta-Learning的Replay Runner"""
    
    def __init__(self, initial_phase: str = "cold_start"):
        # Meta-Learning控制器
        self.meta_controller = MetaLearningController()
        
        # 基于阶段设置初始learning_rate（兼容现有系统）
        initial_lr = self.meta_controller.get_phase_based_initial_lr(initial_phase)
        self.meta_controller.learning_rate = initial_lr
        
        # 核心组件
        self.global_graph = GlobalGraph()
        self.semantic_parser = SimpleSemanticParser()
        self.active_subgraph_engine = ActiveSubgraphEngine(self.global_graph)
        self.active_set_engine = ActiveSetEngine(self.global_graph)
        
        # Reflection和Learning Guard（使用Meta-Learning配置）
        self.reflection_engine = None
        self.learning_guard = None
        
        # 初始化组件
        self._init_components()
        
        # 统计
        self.total_rounds = 0
        self.successful_rounds = 0
        
        # 学习指标
        self.total_diffs_generated = 0
        self.total_diffs_applied = 0
        self.total_conflicts = 0
        
        print(f"   ✅ 集成Meta-Learning系统完成")
        print(f"      初始阶段: {initial_phase}")
        print(f"      初始learning_rate: {initial_lr:.2f}")
    
    def _init_components(self):
        """初始化组件（使用Meta-Learning配置）"""
        # 获取Meta-Learning配置
        config = self.meta_controller.build_config()
        
        # 创建Reflection Engine
        self.reflection_engine = ReflectionEngine(self.global_graph, config)
        
        # 创建Learning Guard
        self.learning_guard = LearningGuard(self.global_graph, config)
        
        print(f"   ✅ 组件初始化完成")
        print(f"      当前配置: buffer_size={config['buffer_size']}, "
              f"conf_threshold={config['confidence_threshold']:.2f}")
    
    def _update_components_config(self):
        """更新组件配置（当learning_rate变化时）"""
        # 获取新配置
        config = self.meta_controller.build_config()
        
        # 更新Reflection Engine配置
        self.reflection_engine.config.update(config)
        
        # 更新Learning Guard配置
        self.learning_guard.config.update(config)
        
        print(f"   🔄 组件配置已更新")
        print(f"      新配置: buffer_size={config['buffer_size']}, "
              f"conf_threshold={config['confidence_threshold']:.2f}")
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        # 计算写入率
        write_ratio = 0.0
        if self.total_diffs_generated > 0:
            write_ratio = self.total_diffs_applied / self.total_diffs_generated
        
        # 计算冲突率
        conflict_rate = 0.0
        if hasattr(self.reflection_engine, 'stats'):
            total_patterns = self.reflection_engine.stats.get("patterns_created", 0)
            if total_patterns > 0:
                conflict_rate = self.total_conflicts / total_patterns
        
        # 计算学习速度
        learning_velocity = 0.0
        if self.total_rounds > 0:
            active_edges = len([e for e in self.global_graph.edges.values() if hasattr(e, 'active') and e.active])
            learning_velocity = active_edges / self.total_rounds
        
        return SystemMetrics(
            write_ratio=write_ratio,
            conflict_rate=conflict_rate,
            learning_velocity=learning_velocity,
            graph_edges=len([e for e in self.global_graph.edges.values() if hasattr(e, 'active') and e.active]),
            total_patterns=self.reflection_engine.stats.get("patterns_created", 0) if hasattr(self.reflection_engine, 'stats') else 0,
            total_conflicts=self.total_conflicts,
            total_diffs_generated=self.total_diffs_generated,
            total_diffs_applied=self.total_diffs_applied
        )
    
    def step(self, query: str) -> Dict[str, Any]:
        """单步执行（集成Meta-Learning控制）"""
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
            
            # 3. 构建Active Set
            active_set = self.active_set_engine.build_active_set(query)
            
            # 4. Reflection（使用当前Meta-Learning配置）
            diffs = self.reflection_engine.reflect(active_set)
            self.total_diffs_generated += len(diffs)
            
            # 初始化validated_diffs（修复变量作用域问题）
            validated_diffs = []
            
            if diffs:
                print(f"     ✅ Reflection生成 {len(diffs)} 个Diff")
                
                # 5. Learning Guard验证（使用当前Meta-Learning配置）
                for diff in diffs:
                    result = self.learning_guard.validate_diff(diff, {"source": "meta_learning", "query": query})
                    
                    action = result.suggested_action
                    if hasattr(result, 'reasons'):
                        reason = result.reasons[0] if result.reasons else "无原因"
                    else:
                        reason = "无原因信息"
                    
                    print(f"       Learning Guard: {action} (置信度: {result.confidence:.2f}, 原因: {reason})")
                    
                    if action == "accept":
                        validated_diffs.append(diff)
                        self.total_diffs_applied += 1
                    
                    # 记录冲突
                    if "冲突" in reason or "conflict" in reason.lower():
                        self.total_conflicts += 1
                
                print(f"     ✅ 验证通过: {len(validated_diffs)} 个Diff")
            else:
                print(f"     ⚠️  无Diff生成")
            
            # 6. Meta-Learning反馈调整（核心）
            if self.total_rounds % 3 == 0:  # 每3轮调整一次
                metrics = self._collect_system_metrics()
                old_lr = self.meta_controller.learning_rate
                new_lr = self.meta_controller.update_learning_rate(metrics)
                
                # 检查learning_rate是否变化
                if abs(new_lr - old_lr) > 0.01:
                    print(f"     🔄 Meta-Learning调整: learning_rate {old_lr:.3f} → {new_lr:.3f}")
                    # 更新组件配置
                    self._update_components_config()
                
                # 每10轮打印一次状态
                if self.total_rounds % 10 == 0:
                    self.meta_controller.print_status()
            
            self.successful_rounds += 1
            
            return {
                "success": True,
                "diffs_generated": len(diffs),
                "diffs_applied": len(validated_diffs),
                "learning_rate": self.meta_controller.learning_rate,
                "write_ratio": self._collect_system_metrics().write_ratio
            }
            
        except Exception as e:
            print(f"     ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        meta_report = self.meta_controller.get_system_report()
        metrics = self._collect_system_metrics()
        
        report = {
            "meta_learning": meta_report,
            "system_metrics": metrics.to_dict(),
            "performance": {
                "total_rounds": self.total_rounds,
                "success_rate": self.successful_rounds / self.total_rounds if self.total_rounds > 0 else 0,
                "graph_size": len(self.global_graph.nodes),
                "edge_count": metrics.graph_edges
            },
            "learning_trend": {
                "learning_rate_history": self.meta_controller.learning_rate_history,
                "write_ratio_history": [m.write_ratio for m in self.meta_controller.metrics_history] if self.meta_controller.metrics_history else [],
                "conflict_rate_history": [m.conflict_rate for m in self.meta_controller.metrics_history] if self.meta_controller.metrics_history else []
            }
        }
        return report

# 运行集成测试
print("\n1. 创建集成Meta-Learning系统...")
runner = MetaLearningReplayRunner(initial_phase="cold_start")

# 创建测试查询（模拟真实对话）
print("\n2. 创建测试查询...")
test_queries = []

# 多样化查询，模拟真实对话模式
topics = ["日本房产", "AI投资", "机器学习", "Python编程", "深度学习", "神经网络", "加密货币", "股票投资", "创业", "科技趋势"]
verbs = ["喜欢", "投资", "学习", "研究", "关注", "讨论", "分析", "探索", "实践", "应用"]

# 生成50轮测试查询
import random
for i in range(50):
    topic = random.choice(topics)
    verb = random.choice(verbs)
    query = f"我{verb}{topic}"
    test_queries.append(query)

print(f"   总测试轮数: {len(test_queries)}")
print(f"   话题多样性: {len(set(topics))}个不同话题")
print(f"   动词多样性: {len(set(verbs))}个不同动词")

# 运行测试
print("\n3. 运行Meta-Learning集成测试...")
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
print("\n4. 生成Meta-Learning最终报告...")
print("-"*40)

report = runner.get_system_report()

print(f"\n   🎯 Meta-Learning自优化系统报告")
print(f"   ===============================")
print(f"   总轮数: {report['performance']['total_rounds']}")
print(f"   成功率: {report['performance']['success_rate']:.1%}")
print(f"   Graph大小: {report['performance']['graph_size']}节点, {report['performance']['edge_count']}边")

print(f"\n   📊 Meta-Learning状态")
meta_info = report['meta_learning']
if meta_info:
    lr_info = meta_info['learning_rate']
    print(f"   当前learning_rate: {lr_info['current']:.3f}")
    print(f"   历史长度: {lr_info['history_length']}次调整")
    print(f"   趋势: {lr_info['trend']:+.3f}")
    print(f"   稳定性: {lr_info['stability']:.3f}")
    print(f"   范围: [{lr_info['min']:.3f}, {lr_info['max']:.3f}]")

print(f"\n   📈 系统指标")
metrics = report['system_metrics']
print(f"   写入率: {metrics['write_ratio']:.3f}")
print(f"   冲突率: {metrics['conflict_rate']:.3f}")
print(f"   学习速度: {metrics['learning_velocity']:.3f}")
print(f"   生成Diff: {metrics['total_diffs_generated']}")
print(f"   应用Diff: {metrics['total_diffs_applied']}")

print(f"\n   🎯 控制状态")
control_state = meta_info.get('control_state', {}) if meta_info else {}
print(f"   学太慢: {'✅ 否' if not control_state.get('is_too_slow', False) else '⚠️  是'}")
print(f"   学太快: {'✅ 否' if not control_state.get('is_too_fast', False) else '⚠️  是'}")
print(f"   有冲突: {'✅ 否' if not control_state.get('has_conflict', False) else '⚠️  是'}")
print(f"   写入率最优: {'✅ 是' if control_state.get('write_ratio_optimal', False) else '❌ 否'}")

# 验证Meta-Learning效果
print("\n5. 验证Meta-Learning效果...")
print("-"*40)

# 检查learning_rate曲线
lr_history = report['learning_trend']['learning_rate_history']
if len(lr_history) >= 5:
    # 计算曲线平滑度
    changes = [abs(lr_history[i] - lr_history[i-1]) for i in range(1, len(lr_history))]
    avg_change = sum(changes) / len(changes) if changes else 0
    
    if avg_change < 0.1:
        print(f"   ✅ learning_rate曲线平滑: 平均变化 {avg_change:.3f} (非跳变)")
    else:
        print(f"   ⚠️  learning_rate变化较大: 平均变化 {avg_change:.3f}")
    
    # 检查最终learning_rate
    final_lr = lr_history[-1]
    if 0.3 <= final_lr <= 0.7:
        print(f"   ✅ learning_rate在合理范围: {final_lr:.3f}")
    else:
        print(f"   ⚠️  learning_rate可能偏极端: {final_lr:.3f}")
else:
    print(f"   ⚠️  历史数据不足，无法评估曲线")

# 检查write_ratio
write_ratio = metrics['write_ratio']
if 0.1 <= write_ratio <= 0.3:
    print(f"   ✅ write_ratio在最优区间: {write_ratio:.3f} ∈ [0.1, 0.3]")
elif write_ratio < 0.1:
    print(f"   ⚠️  write_ratio偏低: {write_ratio:.3f} < 0.1 (学太慢)")
else:
    print(f"   ⚠️  write_ratio偏高: {write_ratio:.3f} > 0.3 (学太快)")

# 检查conflict_rate
conflict_rate = metrics['conflict_rate']
if 0.05 <= conflict_rate <= 0.15:
    print(f"   ✅ conflict_rate在健康范围: {conflict_rate:.3f} ∈ [0.05, 0.15]")
elif conflict_rate < 0.05:
    print(f"   ⚠️  conflict_rate偏低: {conflict_rate:.3f} < 0.05 (可能探索不足)")
else:
    print(f"   ⚠️  conflict_rate偏高: {conflict_rate:.3f} > 0.15 (冲突太多)")

print("\n" + "="*60)
print("🎯 Meta-Learning集成测试完成")
print("="*60)

print(f"\n🕐 总耗时: {time.time() - start_time:.1f}秒")
print(f"📊 最终learning_rate: {lr_history[-1] if lr_history else 0:.3f}")
print(f"📈 最终write_ratio: {write_ratio:.3f}")
print(f"⚠️  最终conflict_rate: {conflict_rate:.3f}")

# 最终结论
print("\n📋 最终结论:")

# 判断系统是否成功自优化
success_criteria = [
    (0.3 <= (lr_history[-1] if lr_history else 0) <= 0.7, "learning_rate在合理范围"),
    (0.1 <= write_ratio <= 0.3, "write_ratio在最优区间"),
    (0.05 <= conflict_rate <= 0.15, "conflict_rate在健康范围"),
    (avg_change < 0.1 if 'avg_change' in locals() else False, "learning_rate曲线平滑")
]

success_count = sum(1 for criterion, _ in success_criteria if criterion)

if success_count >= 3:
    print("✅ Meta-Learning自优化系统工作正常！")
    print("✅ 成功实现连续自调节能力")
    print("✅ 系统现在具备基于反馈的自优化能力")
    
    print("\n💡 关键成就:")
    print("   1. ✅ 从离散阶段切换 → 连续自调节")
    print("   2. ✅ 基于反馈调整learning_rate")
    print("   3. ✅ 惯性平滑防止抖动")
    print("   4. ✅ 完整指标跟踪和优化")
    
    print("\n🚀 系统已升级为:")
    print("   ❗ Self-Regulating Learning System")
    
    print("\n📊 系统能力:")
    print("   能力         状态")
    print("   学习         ✅")
    print("   自适应       ✅")
    print("   自调参       ✅")
    print("   稳定控制     ✅")
else:
    print("⚠️  Meta-Learning系统仍在调整中")
    print(f"   满足条件: {success_count}/4")
    
    for criterion, desc in success_criteria:
        status = "✅" if criterion else "❌"
        print(f"   {status} {desc}")

print(f"\n📁 下一步建议:")
print("   1. 运行更长时间测试（200+轮）")
print("   2. 调整反馈阈值优化调节效果")
print("   3. 添加更多系统指标（如entropy、pattern质量）")
print("   4. 实现Memory Quality Score（记忆质量评估）")

print(f"\n🎯 长期愿景:")
print("   从: Self-Regulating Learning System")
print("   到: ❗ Self-Evolving Cognitive System")