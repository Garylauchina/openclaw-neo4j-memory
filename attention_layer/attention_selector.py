#!/usr/bin/env python3
"""
Attention Selector（注意力选择器）
核心模块：Top-K裁剪，性能核心
"""

from dataclasses import dataclass
from typing import List, Tuple, Any, Dict, Optional
import heapq
import time

@dataclass
class SelectionConfig:
    """选择配置"""
    top_k: int = 20
    min_score: float = 0.1  # 最低分数阈值
    diversity_penalty: float = 0.1  # 多样性惩罚（防止选择过于相似的节点）
    enforce_min_score: bool = True  # 是否强制执行最低分数
    exploration_ratio: float = 0.2  # 探索比例 (0~1)
    enable_exploration: bool = True  # 是否启用探索
    
    def validate(self):
        """验证配置"""
        if self.top_k <= 0:
            raise ValueError(f"top_k必须大于0，当前为{self.top_k}")
        
        if not 0.0 <= self.min_score <= 1.0:
            raise ValueError(f"min_score必须在0~1之间，当前为{self.min_score}")
        
        if not 0.0 <= self.diversity_penalty <= 1.0:
            raise ValueError(f"diversity_penalty必须在0~1之间，当前为{self.diversity_penalty}")
        
        if not 0.0 <= self.exploration_ratio <= 0.5:
            raise ValueError(f"exploration_ratio必须在0~0.5之间，当前为{self.exploration_ratio}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "top_k": self.top_k,
            "min_score": self.min_score,
            "diversity_penalty": self.diversity_penalty,
            "enforce_min_score": self.enforce_min_score,
            "exploration_ratio": self.exploration_ratio,
            "enable_exploration": self.enable_exploration
        }

class AttentionSelector:
    """注意力选择器"""
    
    def __init__(self, config: Optional[SelectionConfig] = None):
        self.config = config or SelectionConfig()
        self.config.validate()
        
        # 统计信息
        self.stats = {
            "total_selections": 0,
            "total_nodes_processed": 0,
            "avg_selected_count": 0.0,
            "avg_selection_time": 0.0,
            "min_score_violations": 0,
            "diversity_applications": 0,
            "exploration_applications": 0,
            "exploration_ratio": self.config.exploration_ratio,
            "exploration_count": 0
        }
    
    def select_top_k(self, scored_nodes: List[Tuple[Any, float]], 
                    query: Optional[str] = None) -> List[Any]:
        """
        Top-K选择
        
        Args:
            scored_nodes: [(node, score)] 已评分的节点列表
            query: 当前查询（用于多样性计算）
        
        Returns:
            List[Any]: 选中的节点列表
        """
        start_time = time.time()
        
        if not scored_nodes:
            self._update_stats(0, 0, time.time() - start_time)
            return []
        
        # 1. 过滤低分节点
        if self.config.enforce_min_score:
            filtered_nodes = [(node, score) for node, score in scored_nodes 
                             if score >= self.config.min_score]
            min_score_violations = len(scored_nodes) - len(filtered_nodes)
            self.stats["min_score_violations"] += min_score_violations
        else:
            filtered_nodes = scored_nodes
        
        if not filtered_nodes:
            self._update_stats(0, len(scored_nodes), time.time() - start_time)
            return []
        
        # 2. 应用多样性惩罚（可选）
        if self.config.diversity_penalty > 0 and query:
            filtered_nodes = self._apply_diversity_penalty(filtered_nodes, query)
        
        # 3. Top-K选择
        if len(filtered_nodes) <= self.config.top_k:
            selected_nodes = [node for node, _ in filtered_nodes]
        else:
            # 使用堆排序获取Top-K
            heap = []
            for node, score in filtered_nodes:
                if len(heap) < self.config.top_k:
                    heapq.heappush(heap, (score, node))
                else:
                    # 如果当前分数大于堆中最小的分数，替换
                    if score > heap[0][0]:
                        heapq.heapreplace(heap, (score, node))
            
            # 从堆中提取节点（按分数降序）
            selected_nodes = [node for _, node in sorted(heap, key=lambda x: x[0], reverse=True)]
        
        # 4. 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(len(selected_nodes), len(scored_nodes), elapsed_time)
        
        return selected_nodes
    
    def select_with_exploration(self, scored_nodes: List[Tuple[Any, float]], 
                              k: int = 20, explore_ratio: float = 0.2) -> List[Any]:
        """
        Top-K + Exploration混合选择（Soft Attention）
        
        Args:
            scored_nodes: [(node, score)] 已评分的节点列表
            k: 总选择数量
            explore_ratio: 探索比例 (0~1)
        
        Returns:
            List[Any]: 选中的节点列表
        """
        start_time = time.time()
        
        if not scored_nodes:
            self._update_stats(0, 0, time.time() - start_time)
            return []
        
        # 1. 过滤低分节点
        if self.config.enforce_min_score:
            filtered_nodes = [(node, score) for node, score in scored_nodes 
                             if score >= self.config.min_score]
            min_score_violations = len(scored_nodes) - len(filtered_nodes)
            self.stats["min_score_violations"] += min_score_violations
        else:
            filtered_nodes = scored_nodes
        
        if not filtered_nodes:
            self._update_stats(0, len(scored_nodes), time.time() - start_time)
            return []
        
        if len(filtered_nodes) <= k:
            selected_nodes = [node for node, _ in filtered_nodes]
        else:
            # 2. 排序
            sorted_nodes = sorted(filtered_nodes, key=lambda x: x[1], reverse=True)
            
            # 3. 计算Top-K和探索数量
            top_k_count = int(k * (1 - explore_ratio))
            explore_count = k - top_k_count
            
            # 4. 选择Top-K
            top_k_nodes = [node for node, _ in sorted_nodes[:top_k_count]]
            
            # 5. 探索选择（从剩余节点中随机选择）
            remaining_nodes = sorted_nodes[top_k_count:]
            if remaining_nodes and explore_count > 0:
                import random
                # 基于分数加权随机选择（分数高的更可能被选中）
                explore_nodes = []
                remaining_scores = [score for _, score in remaining_nodes]
                total_score = sum(remaining_scores)
                
                if total_score > 0:
                    # 计算概率
                    probabilities = [score / total_score for score in remaining_scores]
                    
                    # 加权随机选择
                    for _ in range(explore_count):
                        if remaining_nodes:
                            # 加权随机选择
                            chosen_idx = random.choices(range(len(remaining_nodes)), weights=probabilities)[0]
                            chosen_node, _ = remaining_nodes[chosen_idx]
                            explore_nodes.append(chosen_node)
                            
                            # 移除已选择的节点（防止重复）
                            remaining_nodes.pop(chosen_idx)
                            if remaining_nodes:
                                remaining_scores.pop(chosen_idx)
                                total_score = sum(remaining_scores)
                                probabilities = [score / total_score for score in remaining_scores] if total_score > 0 else [1/len(remaining_nodes)] * len(remaining_nodes)
                else:
                    # 如果所有分数都为0，均匀随机选择
                    if remaining_nodes:
                        explore_nodes = random.sample([node for node, _ in remaining_nodes], 
                                                     min(explore_count, len(remaining_nodes)))
                
                selected_nodes = top_k_nodes + explore_nodes
            else:
                selected_nodes = top_k_nodes
        
        # 6. 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(len(selected_nodes), len(scored_nodes), elapsed_time)
        
        # 记录探索统计
        self.stats["exploration_applications"] = self.stats.get("exploration_applications", 0) + 1
        self.stats["exploration_ratio"] = explore_ratio
        self.stats["exploration_count"] = explore_count
        
        return selected_nodes
    
    def _apply_diversity_penalty(self, scored_nodes: List[Tuple[Any, float]], 
                                query: str) -> List[Tuple[Any, float]]:
        """应用多样性惩罚"""
        if len(scored_nodes) <= 1:
            return scored_nodes
        
        # 计算节点之间的相似度
        nodes_with_penalties = []
        query_terms = set(query.lower().split())
        
        for i, (node, score) in enumerate(scored_nodes):
            adjusted_score = score
            
            # 检查与前面节点的相似度
            for j in range(i):
                prev_node, prev_score = scored_nodes[j]
                
                # 计算相似度（简化：基于文本）
                node_text = self._get_node_text(node)
                prev_text = self._get_node_text(prev_node)
                
                similarity = self._compute_text_similarity(node_text, prev_text)
                
                # 应用多样性惩罚
                if similarity > 0.7:  # 高度相似
                    penalty = self.config.diversity_penalty * similarity
                    adjusted_score = adjusted_score * (1.0 - penalty)
                    self.stats["diversity_applications"] += 1
            
            nodes_with_penalties.append((node, adjusted_score))
        
        return nodes_with_penalties
    
    def _get_node_text(self, node: Any) -> str:
        """获取节点文本"""
        text = getattr(node, 'text', '')
        if text:
            return text
        
        name = getattr(node, 'name', '')
        if name:
            return name
        
        node_id = getattr(node, 'id', '')
        return str(node_id)
    
    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化版）"""
        if not text1 or not text2:
            return 0.0
        
        # 转换为词集
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _update_stats(self, selected_count: int, total_nodes: int, elapsed_time: float):
        """更新统计信息"""
        self.stats["total_selections"] += 1
        self.stats["total_nodes_processed"] += total_nodes
        
        # 更新平均选择数量
        self.stats["avg_selected_count"] = (
            (self.stats["avg_selected_count"] * (self.stats["total_selections"] - 1) + selected_count)
            / self.stats["total_selections"]
        )
        
        # 更新平均选择时间
        self.stats["avg_selection_time"] = (
            (self.stats["avg_selection_time"] * (self.stats["total_selections"] - 1) + elapsed_time)
            / self.stats["total_selections"]
        )
    
    def select_with_coverage_control(self, scored_nodes: List[Tuple[Any, float]], 
                                   target_coverage: float = 0.1) -> List[Any]:
        """
        基于覆盖率控制的选择
        
        Args:
            scored_nodes: [(node, score)] 已评分的节点列表
            target_coverage: 目标覆盖率 (0~1)
        
        Returns:
            List[Any]: 选中的节点列表
        """
        if not scored_nodes:
            return []
        
        # 计算需要选择的节点数量
        target_count = max(1, int(len(scored_nodes) * target_coverage))
        
        # 确保不超过top_k
        target_count = min(target_count, self.config.top_k)
        
        # 选择Top-N
        if len(scored_nodes) <= target_count:
            return [node for node, _ in scored_nodes]
        
        # 排序并选择
        sorted_nodes = sorted(scored_nodes, key=lambda x: x[1], reverse=True)
        selected_nodes = [node for node, _ in sorted_nodes[:target_count]]
        
        # 更新统计
        self._update_stats(len(selected_nodes), len(scored_nodes), 0.0)
        
        return selected_nodes
    
    def get_selection_metrics(self, selected_nodes: List[Any], 
                            total_nodes: int) -> Dict[str, float]:
        """获取选择指标"""
        if total_nodes == 0:
            return {
                "coverage": 0.0,
                "compression_ratio": 0.0,
                "efficiency": 0.0
            }
        
        coverage = len(selected_nodes) / total_nodes
        compression_ratio = total_nodes / len(selected_nodes) if selected_nodes else 0.0
        efficiency = 1.0 / compression_ratio if compression_ratio > 0 else 0.0
        
        return {
            "coverage": coverage,
            "compression_ratio": compression_ratio,
            "efficiency": efficiency
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_nodes_per_selection = 0.0
        if self.stats["total_selections"] > 0:
            avg_nodes_per_selection = self.stats["total_nodes_processed"] / self.stats["total_selections"]
        
        return {
            "config": self.config.to_dict(),
            "performance": {
                "total_selections": self.stats["total_selections"],
                "total_nodes_processed": self.stats["total_nodes_processed"],
                "avg_selected_count": self.stats["avg_selected_count"],
                "avg_nodes_per_selection": avg_nodes_per_selection,
                "avg_selection_time_ms": self.stats["avg_selection_time"] * 1000,
                "min_score_violations": self.stats["min_score_violations"],
                "diversity_applications": self.stats["diversity_applications"]
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_selections": 0,
            "total_nodes_processed": 0,
            "avg_selected_count": 0.0,
            "avg_selection_time": 0.0,
            "min_score_violations": 0,
            "diversity_applications": 0,
            "exploration_applications": 0,
            "exploration_ratio": self.config.exploration_ratio,
            "exploration_count": 0
        }
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        perf = stats["performance"]
        
        print(f"   📊 Attention Selector状态:")
        print(f"      配置:")
        print(f"        top_k: {config['top_k']}")
        print(f"        最低分数: {config['min_score']:.2f}")
        print(f"        多样性惩罚: {config['diversity_penalty']:.2f}")
        print(f"        强制执行最低分数: {config['enforce_min_score']}")
        print(f"        探索比例: {config['exploration_ratio']:.2f}")
        print(f"        启用探索: {config['enable_exploration']}")
        
        print(f"      性能:")
        print(f"        总选择次数: {perf['total_selections']}")
        print(f"        总处理节点数: {perf['total_nodes_processed']}")
        print(f"        平均选择数量: {perf['avg_selected_count']:.1f}")
        print(f"        平均节点数/选择: {perf['avg_nodes_per_selection']:.1f}")
        print(f"        平均选择时间: {perf['avg_selection_time_ms']:.2f}ms")
        print(f"        最低分数违规: {perf['min_score_violations']}")
        print(f"        多样性应用: {perf['diversity_applications']}")
        print(f"        探索应用: {perf['exploration_applications']}")
        print(f"        探索数量: {perf['exploration_count']}")