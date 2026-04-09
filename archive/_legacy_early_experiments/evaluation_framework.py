#!/usr/bin/env python3
"""
评估框架（Evaluation Framework）

目标：让系统"可观测 + 可复现 + 可对比"
核心：证明系统在长期运行中不会失控
"""

import time
import json
import math
import statistics
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import numpy as np

# 导入系统模块
from global_graph import GlobalGraph, NodeType, EdgeType
from active_subgraph import ActiveSubgraphEngine
from active_set import ActiveSetEngine
from reflection_upgrade import ReflectionEngine
from learning_guard import LearningGuard

# 导入语义解析器
from simple_semantic_parser import SimpleSemanticParser


@dataclass
class TurnMetrics:
    """单轮对话指标"""
    turn_id: int
    query: str
    timestamp: float = field(default_factory=time.time)
    
    # Graph层指标
    graph_nodes: int = 0
    graph_edges: int = 0
    graph_avg_degree: float = 0.0
    
    # Active Set层指标
    active_set_size: int = 0
    active_set_weights: List[float] = field(default_factory=list)
    active_set_entropy: float = 0.0
    
    # Reflection层指标
    reflection_diffs_generated: int = 0
    reflection_diffs_applied: int = 0
    reflection_diffs_rejected: int = 0
    
    # Learning Guard指标
    learning_guard_pass_rate: float = 0.0
    learning_guard_conflicts: int = 0
    learning_guard_buffer_size: int = 0
    
    # 性能指标
    processing_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class TestSummary:
    """测试总结"""
    test_name: str
    start_time: float = field(default_factory=time.time)
    end_time: float = 0.0
    total_turns: int = 0
    total_queries: int = 0
    
    # 稳定性指标
    crashes: int = 0
    errors: int = 0
    
    # Graph健康度
    graph_growth_rate: float = 0.0  # 边数增长率
    graph_final_nodes: int = 0
    graph_final_edges: int = 0
    
    # Active Set健康度
    avg_entropy: float = 0.0
    entropy_std: float = 0.0
    entropy_trend: str = "stable"  # increasing, decreasing, stable
    
    # Reflection健康度
    write_ratio: float = 0.0  # diff_applied / diff_generated
    rejection_rate: float = 0.0
    
    # Learning Guard健康度
    avg_pass_rate: float = 0.0
    conflict_rate: float = 0.0
    
    # 性能指标
    avg_processing_time_ms: float = 0.0
    total_processing_time_ms: float = 0.0
    queries_per_second: float = 0.0
    
    # 评分
    stability_score: float = 0.0  # 0-100
    learning_score: float = 0.0   # 0-100
    performance_score: float = 0.0  # 0-100
    overall_score: float = 0.0    # 0-100
    
    def calculate_scores(self):
        """计算各项评分"""
        # 稳定性评分（无崩溃 + 低错误率）
        stability_base = 100
        if self.crashes > 0:
            stability_base -= 50
        if self.errors > 0:
            stability_base -= self.errors * 5
        self.stability_score = max(0, min(100, stability_base))
        
        # 学习健康度评分
        learning_score = 100
        
        # Graph增长控制（越低越好）
        if self.graph_growth_rate > 0.5:
            learning_score -= 30
        elif self.graph_growth_rate > 0.2:
            learning_score -= 15
        
        # 写入率控制（0.2-0.4为理想）
        if self.write_ratio > 0.5:
            learning_score -= 20  # 过度写入
        elif self.write_ratio < 0.1:
            learning_score -= 10  # 学习不足
        
        # entropy趋势（稳定或轻微下降为佳）
        if self.entropy_trend == "decreasing" and self.avg_entropy < 0.3:
            learning_score -= 15  # 过度集中
        
        self.learning_score = max(0, min(100, learning_score))
        
        # 性能评分
        performance_score = 100
        if self.avg_processing_time_ms > 1000:
            performance_score -= 40
        elif self.avg_processing_time_ms > 500:
            performance_score -= 20
        elif self.avg_processing_time_ms > 200:
            performance_score -= 10
        
        self.performance_score = max(0, min(100, performance_score))
        
        # 综合评分（加权平均）
        weights = {
            "stability": 0.4,
            "learning": 0.4,
            "performance": 0.2
        }
        
        self.overall_score = (
            self.stability_score * weights["stability"] +
            self.learning_score * weights["learning"] +
            self.performance_score * weights["performance"]
        )
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        result = asdict(self)
        result["duration_seconds"] = self.end_time - self.start_time
        result["start_time_str"] = datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S")
        result["end_time_str"] = datetime.fromtimestamp(self.end_time).strftime("%Y-%m-%d %H:%M:%S")
        return result
    
    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    def print_summary(self):
        """打印总结"""
        print("\n" + "="*60)
        print(f"测试总结: {self.test_name}")
        print("="*60)
        print(f"总轮数: {self.total_turns}")
        print(f"总查询: {self.total_queries}")
        print(f"持续时间: {self.end_time - self.start_time:.1f}秒")
        print(f"QPS: {self.queries_per_second:.1f} 查询/秒")
        print()
        
        print("📊 健康度指标:")
        print(f"  Graph增长率: {self.graph_growth_rate:.3f}")
        print(f"  最终图大小: {self.graph_final_nodes}节点, {self.graph_final_edges}边")
        print(f"  Active Set熵: {self.avg_entropy:.3f} (±{self.entropy_std:.3f})")
        print(f"  熵趋势: {self.entropy_trend}")
        print(f"  写入率: {self.write_ratio:.3f}")
        print(f"  拒绝率: {self.rejection_rate:.3f}")
        print(f"  Learning Guard通过率: {self.avg_pass_rate:.3f}")
        print()
        
        print("🎯 评分:")
        print(f"  稳定性: {self.stability_score:.1f}/100")
        print(f"  学习健康度: {self.learning_score:.1f}/100")
        print(f"  性能: {self.performance_score:.1f}/100")
        print(f"  综合评分: {self.overall_score:.1f}/100")
        print("="*60)


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.turn_metrics: List[TurnMetrics] = []
        self.error_log: List[Dict] = []
        
    def record(self, metrics: TurnMetrics):
        """记录单轮指标"""
        self.turn_metrics.append(metrics)
    
    def record_error(self, turn_id: int, error_type: str, error_msg: str):
        """记录错误"""
        self.error_log.append({
            "turn_id": turn_id,
            "error_type": error_type,
            "error_msg": error_msg,
            "timestamp": time.time()
        })
    
    def calculate_summary(self, test_name: str) -> TestSummary:
        """计算测试总结"""
        if not self.turn_metrics:
            return TestSummary(test_name=test_name)
        
        # 基础统计
        summary = TestSummary(test_name=test_name)
        summary.total_turns = len(self.turn_metrics)
        summary.total_queries = len(self.turn_metrics)
        
        # 时间统计
        if self.turn_metrics:
            summary.start_time = self.turn_metrics[0].timestamp
            summary.end_time = self.turn_metrics[-1].timestamp
        
        # Graph统计
        if len(self.turn_metrics) >= 2:
            initial_edges = self.turn_metrics[0].graph_edges
            final_edges = self.turn_metrics[-1].graph_edges
            if initial_edges > 0:
                summary.graph_growth_rate = (final_edges - initial_edges) / initial_edges
        
        summary.graph_final_nodes = self.turn_metrics[-1].graph_nodes if self.turn_metrics else 0
        summary.graph_final_edges = self.turn_metrics[-1].graph_edges if self.turn_metrics else 0
        
        # Active Set熵统计
        entropies = [m.active_set_entropy for m in self.turn_metrics if m.active_set_entropy > 0]
        if entropies:
            summary.avg_entropy = statistics.mean(entropies)
            if len(entropies) > 1:
                summary.entropy_std = statistics.stdev(entropies)
                
                # 熵趋势分析
                first_half = entropies[:len(entropies)//2]
                second_half = entropies[len(entropies)//2:]
                if first_half and second_half:
                    avg_first = statistics.mean(first_half)
                    avg_second = statistics.mean(second_half)
                    if avg_second > avg_first + 0.1:
                        summary.entropy_trend = "increasing"
                    elif avg_second < avg_first - 0.1:
                        summary.entropy_trend = "decreasing"
                    else:
                        summary.entropy_trend = "stable"
        
        # Reflection统计
        total_generated = sum(m.reflection_diffs_generated for m in self.turn_metrics)
        total_applied = sum(m.reflection_diffs_applied for m in self.turn_metrics)
        total_rejected = sum(m.reflection_diffs_rejected for m in self.turn_metrics)
        
        if total_generated > 0:
            summary.write_ratio = total_applied / total_generated
            summary.rejection_rate = total_rejected / total_generated
        
        # Learning Guard统计
        pass_rates = [m.learning_guard_pass_rate for m in self.turn_metrics if m.learning_guard_pass_rate > 0]
        if pass_rates:
            summary.avg_pass_rate = statistics.mean(pass_rates)
        
        conflicts = [m.learning_guard_conflicts for m in self.turn_metrics]
        if conflicts and summary.total_turns > 0:
            summary.conflict_rate = sum(conflicts) / summary.total_turns
        
        # 性能统计
        processing_times = [m.processing_time_ms for m in self.turn_metrics]
        if processing_times:
            summary.avg_processing_time_ms = statistics.mean(processing_times)
            summary.total_processing_time_ms = sum(processing_times)
        
        if summary.end_time > summary.start_time:
            summary.queries_per_second = summary.total_queries / (summary.end_time - summary.start_time)
        
        # 错误统计
        summary.errors = len(self.error_log)
        summary.crashes = len([e for e in self.error_log if e["error_type"] == "crash"])
        
        # 计算评分
        summary.calculate_scores()
        
        return summary
    
    def save_to_file(self, filepath: str):
        """保存指标到文件"""
        data = {
            "turn_metrics": [m.to_dict() for m in self.turn_metrics],
            "error_log": self.error_log,
            "summary": self.calculate_summary("saved_test").to_dict() if self.turn_metrics else {}
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath: str):
        """从文件加载指标"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.turn_metrics = [TurnMetrics(**m) for m in data.get("turn_metrics", [])]
        self.error_log = data.get("error_log", [])


class ReplayRunner:
    """
    对话回放执行器（核心）
    
    核心函数：run_conversation(script) → metrics
    """
    
    def __init__(self, system_config: Optional[Dict] = None):
        self.system_config = system_config or {}
        self.metrics_collector = MetricsCollector()
        
        # 初始化系统组件
        self._init_system()
    
    def _init_system(self):
        """初始化系统组件"""
        # 创建全局图
        self.global_graph = GlobalGraph()
        
        # 创建语义解析器（解决冷启动问题）
        self.semantic_parser = SimpleSemanticParser()
        
        # 创建Active Subgraph引擎
        self.active_subgraph_engine = ActiveSubgraphEngine(self.global_graph)
        
        # 创建Active Set引擎
        self.active_set_engine = ActiveSetEngine(self.global_graph)
        
        # 创建Reflection引擎
        self.reflection_engine = ReflectionEngine(self.global_graph)
        
        # 创建Learning Guard
        self.learning_guard = LearningGuard(self.global_graph)
    
    def step(self, query: str) -> Dict:
        """
        单步执行
        
        模拟系统处理一个查询
        """
        start_time = time.time()
        
        try:
            # 0. 语义解析（解决冷启动问题）
            parsed = self.semantic_parser.parse(query)
            if parsed:
                # 转换为图三元组并添加到图中
                subject = parsed["subject"]
                relation = parsed["relation"]
                obj = parsed["object"]
                confidence = parsed["confidence"]
                
                # 创建节点
                subject_id = self.global_graph.create_node(subject, NodeType.USER)
                object_id = self.global_graph.create_node(obj, NodeType.TOPIC)
                
                # 创建边（使用EdgeType枚举）
                edge_type = EdgeType.INTERESTED_IN  # 默认
                if relation == "DISLIKES":
                    edge_type = EdgeType.DISLIKES
                elif relation == "ASKING_ABOUT":
                    edge_type = EdgeType.ASKING_ABOUT
                elif relation == "LEARNING":
                    edge_type = EdgeType.LEARNING
                elif relation == "INVESTED_IN":
                    edge_type = EdgeType.INVESTED_IN
                
                self.global_graph.update_edge(subject_id, object_id, edge_type, confidence)
            
            # 1. 构建Active Set
            active_set = self.active_set_engine.build_active_set(query)
            
            # 2. 执行Reflection（学习）
            diffs = self.reflection_engine.reflect(active_set)
            
            # 3. 使用Learning Guard验证
            validated_diffs = []
            for diff in diffs:
                result = self.learning_guard.validate_diff(diff, {"source": "replay", "query": query})
                if result.suggested_action == "accept":
                    validated_diffs.append(diff)
            
            # 4. 应用验证通过的Diff
            applied_diffs = []
            for diff in validated_diffs:
                # 这里应该调用global_graph的更新方法
                # 简化实现：记录日志
                applied_diffs.append(diff)
            
            # 收集指标
            metrics = self._collect_metrics(
                query=query,
                active_set=active_set,
                diffs_generated=len(diffs),
                diffs_applied=len(applied_diffs),
                diffs_rejected=len(diffs) - len(validated_diffs),
                processing_time=(time.time() - start_time) * 1000
            )
            
            return {
                "success": True,
                "active_set_size": len(active_set.subgraphs) if active_set else 0,
                "diffs_generated": len(diffs),
                "diffs_applied": len(applied_diffs),
                "parsed_triple": parsed is not None,
                "metrics": metrics
            }
            
        except Exception as e:
            # 记录错误
            self.metrics_collector.record_error(
                turn_id=len(self.metrics_collector.turn_metrics),
                error_type="step_error",
                error_msg=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "metrics": None
            }
    
    def _collect_metrics(self, **kwargs) -> TurnMetrics:
        """收集单轮指标"""
        query = kwargs.get("query", "")
        
        # 创建指标对象
        metrics = TurnMetrics(
            turn_id=len(self.metrics_collector.turn_metrics),
            query=query,
            processing_time_ms=kwargs.get("processing_time", 0.0)
        )
        
        # Graph指标
        metrics.graph_nodes = len(self.global_graph.nodes)
        metrics.graph_edges = len([e for e in self.global_graph.edges.values() if hasattr(e, 'active') and e.active])
        
        # 计算平均度
        if metrics.graph_nodes > 0:
            total_degree = 0
            for node in self.global_graph.nodes.values():
                # 计算节点的边数
                node_edges = 0
                for edge in self.global_graph.edges.values():
                    if hasattr(edge, 'active') and edge.active and (edge.src == node.id or edge.dst == node.id):
                        node_edges += 1
                total_degree += node_edges
            
            metrics.graph_avg_degree = total_degree / metrics.graph_nodes
        
        # Active Set指标
        active_set = kwargs.get("active_set")
        if active_set and hasattr(active_set, 'subgraphs'):
            metrics.active_set_size = len(active_set.subgraphs)
            
            # 计算权重和熵
            weights = []
            for subgraph in active_set.subgraphs:
                if hasattr(subgraph, 'weight'):
                    weights.append(subgraph.weight)
                else:
                    weights.append(1.0 / len(active_set.subgraphs))
            
            metrics.active_set_weights = weights
            
            # 计算熵
            if weights:
                # 归一化
                total = sum(weights)
                if total > 0:
                    normalized = [w / total for w in weights]
                    entropy = -sum(w * math.log(w + 1e-9) for w in normalized)
                    metrics.active_set_entropy = entropy
        
        # Reflection指标
        metrics.reflection_diffs_generated = kwargs.get("diffs_generated", 0)
        metrics.reflection_diffs_applied = kwargs.get("diffs_applied", 0)
        metrics.reflection_diffs_rejected = kwargs.get("diffs_rejected", 0)
        
        # Learning Guard指标
        if hasattr(self.learning_guard, 'stats'):
            stats = self.learning_guard.stats
            total_validations = stats.get("total_validations", 0)
            accepted = stats.get("accepted_diffs", 0)
            
            if total_validations > 0:
                metrics.learning_guard_pass_rate = accepted / total_validations
            
            metrics.learning_guard_conflicts = stats.get("consistency_violations", 0)
            metrics.learning_guard_buffer_size = stats.get("buffer_size", 0)
        
        # 内存使用（简化估算）
        import sys
        metrics.memory_usage_mb = sys.getsizeof(self.global_graph) / (1024 * 1024)
        
        return metrics
    
    def run(self, script: List[str]) -> TestSummary:
        """
        运行对话回放
        
        Args:
            script: 对话脚本列表
            
        Returns:
            测试总结
        """
        print(f"🚀 开始回放测试: {len(script)}轮对话")
        print("-"*40)
        
        for turn_id, query in enumerate(script):
            if turn_id % 10 == 0:
                print(f"  处理第 {turn_id}/{len(script)} 轮...")
            
            # 执行单步
            result = self.step(query)
            
            # 记录指标
            if result["success"] and result["metrics"]:
                self.metrics_collector.record(result["metrics"])
            else:
                print(f"  ❌ 第 {turn_id} 轮失败: {result.get('error', '未知错误')}")
        
        print("-"*40)
        print("✅ 回放测试完成")
        
        # 计算总结
        summary = self.metrics_collector.calculate_summary("对话回放测试")
        return summary
    
    def save_results(self, output_dir: str = "evaluation_results"):
        """保存结果"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"replay_results_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        self.metrics_collector.save_to_file(filepath)
        print(f"📁 结果已保存到: {filepath}")
        
        return filepath


class TestScenarios:
    """测试脚本库（标准化）"""
    
    @staticmethod
    def topic_switch_test(num_cycles: int = 8) -> List[str]:
        """
        话题切换测试
        
        模拟用户在多个话题间切换
        """
        topics = [
            "我想投资日本房产",
            "AI创业怎么做？",
            "日本房产回报率如何？",
            "机器学习入门",
            "日本房产风险？",
            "深度学习与机器学习的区别",
            "东京和大阪哪个更适合投资？",
            "Python编程学习路线",
            "日本房产的税务问题",
            "神经网络基本原理"
        ]
        
        # 重复循环
        script = []
        for i in range(num_cycles):
            script.extend(topics)
        
        return script
    
    @staticmethod
    def consistency_reinforcement_test(repetitions: int = 10) -> List[str]:
        """
        一致性强化测试
        
        重复相同陈述，测试系统是否过度学习
        """
        statements = [
            "我喜欢低风险投资",
            "我偏好稳定收益",
            "我对高风险投资不感兴趣",
            "长期投资更适合我"
        ]
        
        script = []
        for statement in statements:
            script.extend([statement] * repetitions)
        
        return script
    
    @staticmethod
    def conflict_test() -> List[str]:
        """
        冲突测试
        
        测试系统如何处理矛盾信息
        """
        return [
            "我喜欢日本房产",
            "我不喜欢高风险投资",
            "日本房产风险很高",
            "但日本房产收益稳定",
            "我还是更喜欢美国股市",
            "不过日本房产流动性更好",
            "我决定不投资日本了",
            "但朋友推荐日本房产"
        ]
    
    @staticmethod
    def stress_test(num_queries: int = 50) -> List[str]:
        """
        压力测试
        
        大量随机查询，测试系统稳定性
        """
        import random
        
        topics = [
            "投资", "房产", "AI", "机器学习", "编程",
            "旅游", "美食", "科技", "金融", "教育",
            "健康", "运动", "音乐", "电影", "书籍"
        ]
        
        adjectives = [
            "如何", "怎么", "为什么", "什么是", "哪个",
            "最好的", "最差的", "优缺点", "风险", "收益"
        ]
        
        script = []
        for i in range(num_queries):
            topic = random.choice(topics)
            adj = random.choice(adjectives)
            script.append(f"{topic}{adj}")
        
        return script
    
    @staticmethod
    def mixed_test() -> List[str]:
        """
        混合测试
        
        综合各种测试场景
        """
        script = []
        
        # 话题切换
        script.extend(TestScenarios.topic_switch_test(2))
        
        # 一致性强化
        script.extend(TestScenarios.consistency_reinforcement_test(3))
        
        # 冲突测试
        script.extend(TestScenarios.conflict_test())
        
        # 压力测试（少量）
        script.extend(TestScenarios.stress_test(20))
        
        return script


class Evaluator:
    """结果评估器"""
    
    @staticmethod
    def evaluate_system_health(summary: TestSummary) -> Dict:
        """
        评估系统健康度
        
        返回健康度判断和建议
        """
        health_status = "healthy"
        warnings = []
        suggestions = []
        
        # 1. Graph健康度检查
        if summary.graph_growth_rate > 0.5:
            health_status = "warning"
            warnings.append(f"Graph增长过快: {summary.graph_growth_rate:.3f}")
            suggestions.append("降低学习率或增加Learning Guard严格度")
        
        elif summary.graph_growth_rate < 0.01:
            warnings.append(f"Graph增长过慢: {summary.graph_growth_rate:.3f}")
            suggestions.append("检查是否学习不足")
        
        # 2. Active Set熵检查
        if summary.avg_entropy < 0.3:
            health_status = "warning"
            warnings.append(f"Active Set过度集中: 熵={summary.avg_entropy:.3f}")
            suggestions.append("增加话题多样性或调整Active Set权重计算")
        
        elif summary.avg_entropy > 1.5:
            warnings.append(f"Active Set过度分散: 熵={summary.avg_entropy:.3f}")
            suggestions.append("可能话题切换过于频繁")
        
        # 3. 写入率检查
        if summary.write_ratio > 0.5:
            health_status = "warning"
            warnings.append(f"写入率过高: {summary.write_ratio:.3f}")
            suggestions.append("增加Learning Guard验证严格度")
        
        elif summary.write_ratio < 0.1:
            warnings.append(f"写入率过低: {summary.write_ratio:.3f}")
            suggestions.append("可能Learning Guard过于严格")
        
        # 4. 错误检查
        if summary.crashes > 0:
            health_status = "critical"
            warnings.append(f"系统崩溃: {summary.crashes}次")
            suggestions.append("检查系统稳定性")
        
        if summary.errors > 5:
            health_status = "warning"
            warnings.append(f"错误较多: {summary.errors}次")
            suggestions.append("增加错误处理和日志")
        
        # 5. 性能检查
        if summary.avg_processing_time_ms > 1000:
            health_status = "warning"
            warnings.append(f"处理时间过长: {summary.avg_processing_time_ms:.1f}ms")
            suggestions.append("优化算法性能")
        
        return {
            "health_status": health_status,
            "overall_score": summary.overall_score,
            "warnings": warnings,
            "suggestions": suggestions,
            "summary": summary.to_dict()
        }
    
    @staticmethod
    def compare_versions(version1_results: Dict, version2_results: Dict) -> Dict:
        """
        版本对比
        
        比较两个版本的测试结果
        """
        v1_score = version1_results.get("overall_score", 0)
        v2_score = version2_results.get("overall_score", 0)
        
        improvement = v2_score - v1_score
        improvement_percent = (improvement / max(v1_score, 1)) * 100
        
        # 分析改进点
        improvements = []
        regressions = []
        
        metrics_to_compare = [
            ("graph_growth_rate", "Graph增长率", "lower"),
            ("avg_entropy", "Active Set熵", "optimal"),
            ("write_ratio", "写入率", "lower"),
            ("avg_processing_time_ms", "平均处理时间", "lower"),
            ("stability_score", "稳定性", "higher"),
            ("learning_score", "学习健康度", "higher")
        ]
        
        for metric_key, metric_name, optimal in metrics_to_compare:
            v1_val = version1_results["summary"].get(metric_key, 0)
            v2_val = version2_results["summary"].get(metric_key, 0)
            
            if optimal == "higher":
                if v2_val > v1_val:
                    improvements.append(f"{metric_name}: {v1_val:.3f} → {v2_val:.3f} (+{v2_val-v1_val:.3f})")
                elif v2_val < v1_val:
                    regressions.append(f"{metric_name}: {v1_val:.3f} → {v2_val:.3f} ({v2_val-v1_val:.3f})")
            
            elif optimal == "lower":
                if v2_val < v1_val:
                    improvements.append(f"{metric_name}: {v1_val:.3f} → {v2_val:.3f} (-{v1_val-v2_val:.3f})")
                elif v2_val > v1_val:
                    regressions.append(f"{metric_name}: {v1_val:.3f} → {v2_val:.3f} (+{v2_val-v1_val:.3f})")
        
        return {
            "v1_score": v1_score,
            "v2_score": v2_score,
            "improvement": improvement,
            "improvement_percent": improvement_percent,
            "improvements": improvements,
            "regressions": regressions,
            "verdict": "改进" if improvement > 0 else "退步"
        }


class DashboardLogger:
    """仪表板日志输出"""
    
    def __init__(self, output_dir: str = "evaluation_dashboard"):
        import os
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def log_turn(self, turn_metrics: TurnMetrics):
        """记录单轮日志"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"turn_{turn_metrics.turn_id:04d}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(turn_metrics.to_dict(), f, ensure_ascii=False, indent=2)
    
    def generate_report(self, summary: TestSummary, health_evaluation: Dict):
        """生成报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_name": summary.test_name,
            "summary": summary.to_dict(),
            "health_evaluation": health_evaluation,
            "system_info": self._get_system_info()
        }
        
        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📋 报告已生成: {filepath}")
        return filepath
    
    def _get_system_info(self) -> Dict:
        """获取系统信息"""
        import sys
        import platform
        
        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "memory": psutil.virtual_memory().total / (1024**3) if 'psutil' in sys.modules else "unknown"
        }


# ========== 测试函数 ==========

def run_golden_test():
    """运行黄金测试（200轮回放）"""
    print("🧪 开始黄金测试（200轮回放）")
    print("="*60)
    
    # 创建测试脚本
    script = TestScenarios.topic_switch_test(20)  # 10个话题 × 20轮 = 200轮
    
    # 创建回放执行器
    runner = ReplayRunner()
    
    # 运行测试
    summary = runner.run(script)
    
    # 打印总结
    summary.print_summary()
    
    # 评估健康度
    evaluator = Evaluator()
    health_eval = evaluator.evaluate_system_health(summary)
    
    print("\n🏥 系统健康度评估:")
    print(f"  状态: {health_eval['health_status']}")
    print(f"  综合评分: {health_eval['overall_score']:.1f}/100")
    
    if health_eval['warnings']:
        print("\n⚠️  警告:")
        for warning in health_eval['warnings']:
            print(f"  • {warning}")
    
    if health_eval['suggestions']:
        print("\n💡 建议:")
        for suggestion in health_eval['suggestions']:
            print(f"  • {suggestion}")
    
    # 保存结果
    runner.save_results()
    
    print("\n" + "="*60)
    print("✅ 黄金测试完成")
    print("="*60)
    
    return summary, health_eval


def run_all_scenarios():
    """运行所有测试场景"""
    print("🧪 运行所有测试场景")
    print("="*60)
    
    scenarios = {
        "话题切换测试": TestScenarios.topic_switch_test(5),  # 50轮
        "一致性强化测试": TestScenarios.consistency_reinforcement_test(5),  # 20轮
        "冲突测试": TestScenarios.conflict_test(),  # 8轮
        "压力测试": TestScenarios.stress_test(30),  # 30轮
        "混合测试": TestScenarios.mixed_test()  # 约100轮
    }
    
    results = {}
    
    for name, script in scenarios.items():
        print(f"\n📋 运行: {name} ({len(script)}轮)")
        print("-"*40)
        
        runner = ReplayRunner()
        summary = runner.run(script)
        
        # 评估健康度
        evaluator = Evaluator()
        health_eval = evaluator.evaluate_system_health(summary)
        
        results[name] = {
            "summary": summary,
            "health_eval": health_eval
        }
        
        print(f"  评分: {summary.overall_score:.1f}/100")
        print(f"  状态: {health_eval['health_status']}")
    
    # 生成综合报告
    print("\n" + "="*60)
    print("📊 综合测试结果")
    print("="*60)
    
    for name, result in results.items():
        summary = result["summary"]
        health_eval = result["health_eval"]
        
        print(f"\n{name}:")
        print(f"  轮数: {summary.total_turns}")
        print(f"  评分: {summary.overall_score:.1f}/100")
        print(f"  状态: {health_eval['health_status']}")
        print(f"  Graph增长率: {summary.graph_growth_rate:.3f}")
        print(f"  Active Set熵: {summary.avg_entropy:.3f}")
        print(f"  写入率: {summary.write_ratio:.3f}")
    
    print("\n" + "="*60)
    print("✅ 所有测试场景完成")
    print("="*60)
    
    return results


def test_version_comparison():
    """测试版本对比"""
    print("🧪 测试版本对比")
    print("="*60)
    
    # 模拟两个版本的测试结果
    v1_results = {
        "overall_score": 75.0,
        "summary": {
            "graph_growth_rate": 0.8,
            "avg_entropy": 0.4,
            "write_ratio": 0.6,
            "avg_processing_time_ms": 800,
            "stability_score": 80,
            "learning_score": 70
        }
    }
    
    v2_results = {
        "overall_score": 85.0,
        "summary": {
            "graph_growth_rate": 0.3,
            "avg_entropy": 0.7,
            "write_ratio": 0.3,
            "avg_processing_time_ms": 400,
            "stability_score": 90,
            "learning_score": 85
        }
    }
    
    # 对比版本
    comparison = Evaluator.compare_versions(v1_results, v2_results)
    
    print(f"版本1评分: {comparison['v1_score']:.1f}")
    print(f"版本2评分: {comparison['v2_score']:.1f}")
    print(f"改进: {comparison['improvement']:.1f} ({comparison['improvement_percent']:.1f}%)")
    print(f"结论: {comparison['verdict']}")
    
    if comparison['improvements']:
        print("\n✅ 改进点:")
        for improvement in comparison['improvements']:
            print(f"  • {improvement}")
    
    if comparison['regressions']:
        print("\n⚠️  退步点:")
        for regression in comparison['regressions']:
            print(f"  • {regression}")
    
    print("\n" + "="*60)
    print("✅ 版本对比测试完成")
    print("="*60)
    
    return comparison


def main():
    """主函数"""
    print("🚀 评估框架主程序")
    print("="*60)
    
    print("选择测试模式:")
    print("1. 黄金测试 (200轮)")
    print("2. 所有场景测试")
    print("3. 版本对比测试")
    print("4. 退出")
    
    choice = input("请输入选择 (1-4): ").strip()
    
    if choice == "1":
        run_golden_test()
    elif choice == "2":
        run_all_scenarios()
    elif choice == "3":
        test_version_comparison()
    elif choice == "4":
        print("退出程序")
    else:
        print("无效选择")
    
    print("\n" + "="*60)
    print("评估框架运行完成")
    print("="*60)


if __name__ == "__main__":
    main()