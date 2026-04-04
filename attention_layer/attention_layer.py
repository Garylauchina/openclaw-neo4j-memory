#!/usr/bin/env python3
"""
Attention Layer（注意力层主流程）
核心入口：集成所有组件，提供完整注意力控制
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime

from .attention_state import AttentionState
from .attention_scorer import AttentionScorer, AttentionConfig
from .attention_selector import AttentionSelector, SelectionConfig
from .attention_feedback import AttentionFeedback, FeedbackConfig

@dataclass
class AttentionLayerConfig:
    """注意力层配置"""
    # Scorer配置
    relevance_weight: float = 0.25
    belief_weight: float = 0.20
    recency_weight: float = 0.15
    rqs_weight: float = 0.15
    novelty_weight: float = 0.15
    conflict_weight: float = 0.10
    
    # Selector配置
    top_k: int = 20
    min_score: float = 0.1
    diversity_penalty: float = 0.1
    enforce_min_score: bool = True
    exploration_ratio: float = 0.2
    enable_exploration: bool = True
    
    # Feedback配置
    feedback_learning_rate: float = 0.05
    feedback_decay_rate: float = 0.01
    feedback_min_score: float = 0.1
    feedback_max_score: float = 1.0
    feedback_window: int = 10
    feedback_success_threshold: float = 0.7
    
    # 性能配置
    enable_caching: bool = True
    cache_ttl: int = 300  # 5分钟
    enable_feedback: bool = True
    enable_diversity: bool = True
    
    def validate(self):
        """验证配置"""
        # 验证权重总和为1
        weights = [
            self.relevance_weight,
            self.belief_weight,
            self.recency_weight,
            self.rqs_weight,
            self.novelty_weight,
            self.conflict_weight
        ]
        
        total_weight = sum(weights)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"权重总和应为1.0，当前为{total_weight:.3f}")
        
        # 验证其他参数
        if self.top_k <= 0:
            raise ValueError(f"top_k必须大于0，当前为{self.top_k}")
        
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError(f"min_score必须在0~1之间，当前为{self.min_score}")
        
        if not 0.0 <= self.diversity_penalty <= 1.0:
            raise ValueError(f"diversity_penalty必须在0~1之间，当前为{self.diversity_penalty}")
        
        if not 0.0 <= self.exploration_ratio <= 0.5:
            raise ValueError(f"exploration_ratio必须在0~0.5之间，当前为{self.exploration_ratio}")
        
        if not 0.0 < self.feedback_learning_rate <= 0.1:
            raise ValueError(f"feedback_learning_rate必须在0~0.1之间，当前为{self.feedback_learning_rate}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "scorer": {
                "relevance_weight": self.relevance_weight,
                "belief_weight": self.belief_weight,
                "recency_weight": self.recency_weight,
                "rqs_weight": self.rqs_weight,
                "novelty_weight": self.novelty_weight,
                "conflict_weight": self.conflict_weight
            },
            "selector": {
                "top_k": self.top_k,
                "min_score": self.min_score,
                "diversity_penalty": self.diversity_penalty,
                "enforce_min_score": self.enforce_min_score,
                "exploration_ratio": self.exploration_ratio,
                "enable_exploration": self.enable_exploration
            },
            "feedback": {
                "learning_rate": self.feedback_learning_rate,
                "decay_rate": self.feedback_decay_rate,
                "min_score": self.feedback_min_score,
                "max_score": self.feedback_max_score,
                "window": self.feedback_window,
                "success_threshold": self.feedback_success_threshold
            },
            "performance": {
                "enable_caching": self.enable_caching,
                "cache_ttl": self.cache_ttl,
                "enable_feedback": self.enable_feedback,
                "enable_diversity": self.enable_diversity
            }
        }

class AttentionLayer:
    """注意力层主类"""
    
    def __init__(self, config: Optional[AttentionLayerConfig] = None):
        self.config = config or AttentionLayerConfig()
        self.config.validate()
        
        # 初始化组件
        scorer_config = AttentionConfig(
            top_k=self.config.top_k,
            relevance_weight=self.config.relevance_weight,
            belief_weight=self.config.belief_weight,
            recency_weight=self.config.recency_weight,
            rqs_weight=self.config.rqs_weight,
            novelty_weight=self.config.novelty_weight,
            conflict_weight=self.config.conflict_weight
        )
        
        selector_config = SelectionConfig(
            top_k=self.config.top_k,
            min_score=self.config.min_score,
            diversity_penalty=self.config.diversity_penalty,
            enforce_min_score=self.config.enforce_min_score,
            exploration_ratio=self.config.exploration_ratio,
            enable_exploration=self.config.enable_exploration
        )
        
        feedback_config = FeedbackConfig(
            learning_rate=self.config.feedback_learning_rate,
            decay_rate=self.config.feedback_decay_rate,
            min_score=self.config.feedback_min_score,
            max_score=self.config.feedback_max_score,
            feedback_window=self.config.feedback_window,
            success_threshold=self.config.feedback_success_threshold
        )
        
        self.state = AttentionState()
        self.scorer = AttentionScorer(scorer_config)
        self.selector = AttentionSelector(selector_config)
        self.feedback = AttentionFeedback(feedback_config)
        
        # 统计信息
        self.stats = {
            "total_runs": 0,
            "total_nodes_processed": 0,
            "avg_selected_count": 0.0,
            "avg_attention_coverage": 0.0,
            "avg_run_time": 0.0,
            "feedback_applications": 0
        }
    
    def run(self, graph: Any, query: str, metrics: Dict[str, Any]) -> List[Any]:
        """
        运行注意力层
        
        Args:
            graph: 图对象（需要实现nodes属性）
            query: 当前用户输入
            metrics: 包含RQS、belief等信息
        
        Returns:
            List[Any]: 选中的节点列表
        """
        start_time = time.time()
        
        # 1. 获取所有节点
        nodes = list(getattr(graph, 'nodes', []))
        if not nodes:
            self._update_stats(0, 0, time.time() - start_time)
            return []
        
        # 2. 计算注意力分数
        scored_nodes = []
        for node in nodes:
            score = self.scorer.compute_attention_score(node, query, metrics)
            scored_nodes.append((node, score))
        
        # 3. Top-K选择（带探索）
        if self.config.enable_diversity:
            if self.config.enable_exploration:
                selected_nodes = self.selector.select_with_exploration(
                    scored_nodes, 
                    k=self.config.top_k,
                    explore_ratio=self.config.exploration_ratio
                )
            else:
                selected_nodes = self.selector.select_top_k(scored_nodes, query)
        else:
            # 简单排序选择
            sorted_nodes = sorted(scored_nodes, key=lambda x: x[1], reverse=True)
            selected_nodes = [node for node, _ in sorted_nodes[:self.config.top_k]]
        
        # 4. 更新状态
        selected_node_ids = [getattr(node, 'id', str(i)) for i, node in enumerate(selected_nodes)]
        avg_score = sum(score for _, score in scored_nodes) / len(scored_nodes) if scored_nodes else 0.0
        
        self.state.record_history(
            query=query,
            selected_nodes=selected_node_ids,
            total_nodes=len(nodes),
            avg_score=avg_score
        )
        
        # 5. 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(len(selected_nodes), len(nodes), elapsed_time)
        
        return selected_nodes
    
    def run_with_feedback(self, graph: Any, query: str, 
                         metrics: Dict[str, Any],
                         previous_success: Optional[Dict[str, bool]] = None) -> List[Any]:
        """
        运行注意力层（带反馈）
        
        Args:
            graph: 图对象
            query: 当前用户输入
            metrics: 包含RQS、belief等信息
            previous_success: 之前推理的成功情况 {node_id: success}
        
        Returns:
            List[Any]: 选中的节点列表
        """
        # 1. 应用之前的反馈
        if previous_success and self.config.enable_feedback:
            self._apply_feedback(previous_success)
        
        # 2. 运行注意力层
        selected_nodes = self.run(graph, query, metrics)
        
        return selected_nodes
    
    def _apply_feedback(self, success_map: Dict[str, bool]):
        """应用反馈"""
        feedback_pairs = []
        for node_id, success in success_map.items():
            feedback_pairs.append((node_id, success))
        
        if feedback_pairs:
            self.feedback.batch_update(feedback_pairs)
            self.stats["feedback_applications"] += 1
    
    def get_attention_coverage(self) -> float:
        """获取注意力覆盖率"""
        return self.state.get_attention_coverage(len(self.state.node_scores))
    
    def get_selection_metrics(self, selected_nodes: List[Any], 
                            total_nodes: int) -> Dict[str, float]:
        """获取选择指标"""
        return self.selector.get_selection_metrics(selected_nodes, total_nodes)
    
    def get_recommended_nodes(self, graph: Any, query: str, 
                             metrics: Dict[str, Any], 
                             count: int = 10) -> List[Tuple[Any, float]]:
        """
        获取推荐节点（带分数）
        
        Args:
            graph: 图对象
            query: 查询
            metrics: 指标
            count: 推荐数量
        
        Returns:
            List[Tuple[Any, float]]: [(node, score)] 节点和分数
        """
        nodes = list(getattr(graph, 'nodes', []))
        if not nodes:
            return []
        
        # 计算分数
        scored_nodes = []
        for node in nodes:
            # 基础分数
            base_score = self.scorer.compute_attention_score(node, query, metrics)
            
            # 结合反馈分数
            node_id = getattr(node, 'id', '')
            if node_id and self.config.enable_feedback:
                recommended_score = self.feedback.get_recommended_attention_score(node_id, base_score)
            else:
                recommended_score = base_score
            
            scored_nodes.append((node, recommended_score))
        
        # 排序
        sorted_nodes = sorted(scored_nodes, key=lambda x: x[1], reverse=True)
        
        return sorted_nodes[:count]
    
    def _update_stats(self, selected_count: int, total_nodes: int, elapsed_time: float):
        """更新统计信息"""
        self.stats["total_runs"] += 1
        self.stats["total_nodes_processed"] += total_nodes
        
        # 更新平均选择数量
        self.stats["avg_selected_count"] = (
            (self.stats["avg_selected_count"] * (self.stats["total_runs"] - 1) + selected_count)
            / self.stats["total_runs"]
        )
        
        # 更新平均覆盖率
        coverage = selected_count / total_nodes if total_nodes > 0 else 0.0
        self.stats["avg_attention_coverage"] = (
            (self.stats["avg_attention_coverage"] * (self.stats["total_runs"] - 1) + coverage)
            / self.stats["total_runs"]
        )
        
        # 更新平均运行时间
        self.stats["avg_run_time"] = (
            (self.stats["avg_run_time"] * (self.stats["total_runs"] - 1) + elapsed_time)
            / self.stats["total_runs"]
        )
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        # 获取各组件报告
        state_report = self.state.get_system_report()
        scorer_report = self.scorer.get_stats()
        selector_report = self.selector.get_stats()
        feedback_report = self.feedback.get_system_report()
        
        # 计算性能指标
        compression_ratio = 0.0
        if self.stats["avg_selected_count"] > 0:
            compression_ratio = self.stats["total_nodes_processed"] / (self.stats["avg_selected_count"] * self.stats["total_runs"])
        
        efficiency = 1.0 / compression_ratio if compression_ratio > 0 else 0.0
        
        return {
            "config": self.config.to_dict(),
            "performance": {
                "total_runs": self.stats["total_runs"],
                "total_nodes_processed": self.stats["total_nodes_processed"],
                "avg_selected_count": self.stats["avg_selected_count"],
                "avg_attention_coverage": self.stats["avg_attention_coverage"],
                "avg_run_time_ms": self.stats["avg_run_time"] * 1000,
                "compression_ratio": compression_ratio,
                "efficiency": efficiency,
                "feedback_applications": self.stats["feedback_applications"]
            },
            "components": {
                "state": state_report,
                "scorer": scorer_report,
                "selector": selector_report,
                "feedback": feedback_report
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_runs": 0,
            "total_nodes_processed": 0,
            "avg_selected_count": 0.0,
            "avg_attention_coverage": 0.0,
            "avg_run_time": 0.0,
            "feedback_applications": 0
        }
        
        # 重置组件统计
        self.scorer.reset_stats()
        self.selector.reset_stats()
        self.feedback.reset_stats()
    
    def print_status(self):
        """打印状态"""
        report = self.get_system_report()
        config = report["config"]
        perf = report["performance"]
        
        print(f"🧠 Attention Layer状态报告")
        print(f"="*60)
        
        print(f"📋 配置:")
        print(f"  Scorer权重: 相关性{config['scorer']['relevance_weight']:.2f}, "
              f"信念{config['scorer']['belief_weight']:.2f}, "
              f"新鲜度{config['scorer']['recency_weight']:.2f}")
        print(f"              RQS{config['scorer']['rqs_weight']:.2f}, "
              f"新颖性{config['scorer']['novelty_weight']:.2f}, "
              f"冲突{config['scorer']['conflict_weight']:.2f}")
        
        print(f"  Selector: top_k={config['selector']['top_k']}, "
              f"最低分数={config['selector']['min_score']:.2f}")
        
        print(f"  Feedback: 学习率={config['feedback']['learning_rate']:.3f}, "
              f"窗口={config['feedback']['window']}")
        
        print(f"  性能: 缓存={config['performance']['enable_caching']}, "
              f"反馈={config['performance']['enable_feedback']}, "
              f"多样性={config['performance']['enable_diversity']}")
        
        print(f"\n📊 性能:")
        print(f"  总运行次数: {perf['total_runs']}")
        print(f"  总处理节点数: {perf['total_nodes_processed']}")
        print(f"  平均选择数量: {perf['avg_selected_count']:.1f}")
        print(f"  平均注意力覆盖率: {perf['avg_attention_coverage']:.1%}")
        print(f"  平均运行时间: {perf['avg_run_time_ms']:.2f}ms")
        print(f"  压缩比: {perf['compression_ratio']:.1f}x")
        print(f"  效率: {perf['efficiency']:.1%}")
        print(f"  反馈应用次数: {perf['feedback_applications']}")
        
        print(f"\n🔧 组件状态:")
        self.state.print_status()
        print()
        self.scorer.print_status()
        print()
        self.selector.print_status()
        print()
        self.feedback.print_status()
        
        print(f"\n🎯 系统变化预测:")
        print(f"  ✅ 1. 推理速度下降（好事）")
        print(f"     原因: 搜索空间从{perf['total_nodes_processed']/max(1, perf['total_runs']):.0f} → {perf['avg_selected_count']:.0f}")
        print(f"     压缩比: {perf['compression_ratio']:.1f}x")
        
        print(f"  ✅ 2. 推理质量上升")
        print(f"     原因: 垃圾路径被过滤，只保留Top-{config['selector']['top_k']}")
        
        print(f"  ✅ 3. RQS更稳定")
        print(f"     原因: 输入更干净 → 输出更稳定")
        
        print(f"  ⚠️ 4. 必须监控指标:")
        print(f"     注意力覆盖率: {perf['avg_attention_coverage']:.1%}")
        print(f"     理想范围: 5%~20%")
        
        print(f"\n🚀 系统已升级为:")
        print(f"   ❗ Attention-Controlled Cognitive System")
        print(f"   核心能力: 让系统学会'把计算资源花在最值得的地方'")
        
        print(f"\n" + "="*60)