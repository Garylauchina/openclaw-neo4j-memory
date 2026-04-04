#!/usr/bin/env python3
"""
Attention Scorer（注意力打分器）
核心模块：计算注意力分数
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import math
import time
from datetime import datetime, timedelta

@dataclass
class AttentionConfig:
    """注意力配置"""
    top_k: int = 20
    relevance_weight: float = 0.25
    belief_weight: float = 0.20
    recency_weight: float = 0.15
    rqs_weight: float = 0.15
    novelty_weight: float = 0.15
    conflict_weight: float = 0.10
    
    def validate(self):
        """验证配置"""
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
        
        if self.top_k <= 0:
            raise ValueError(f"top_k必须大于0，当前为{self.top_k}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "top_k": self.top_k,
            "relevance_weight": self.relevance_weight,
            "belief_weight": self.belief_weight,
            "recency_weight": self.recency_weight,
            "rqs_weight": self.rqs_weight,
            "novelty_weight": self.novelty_weight,
            "conflict_weight": self.conflict_weight
        }

class AttentionScorer:
    """注意力打分器"""
    
    def __init__(self, config: Optional[AttentionConfig] = None):
        self.config = config or AttentionConfig()
        self.config.validate()
        
        # 缓存机制
        self.score_cache: Dict[str, Tuple[float, float]] = {}  # key -> (score, timestamp)
        self.cache_ttl = 300  # 5分钟缓存
        
        # 统计信息
        self.stats = {
            "total_scores_computed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_computation_time": 0.0
        }
    
    def compute_attention_score(self, node: Any, query: str, 
                               metrics: Dict[str, Any]) -> float:
        """
        计算注意力分数
        
        Args:
            node: graph中的节点/边
            query: 当前用户输入
            metrics: 包含RQS、belief等信息
        
        Returns:
            float: 注意力分数 (0~1)
        """
        start_time = time.time()
        
        # 检查缓存
        cache_key = f"{node.id}_{hash(query)}"
        if cache_key in self.score_cache:
            score, timestamp = self.score_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                self.stats["cache_hits"] += 1
                return score
        
        self.stats["cache_misses"] += 1
        
        # 计算各个组件分数
        relevance = self._compute_relevance(node, query)  # 0~1
        belief = self._compute_belief(node, metrics)  # 0~1
        recency = self._compute_recency(node, metrics)  # 0~1
        rqs = self._compute_rqs(node, metrics)  # 0~1
        novelty = self._compute_novelty(node, metrics)  # 0~1
        conflict = self._compute_conflict(node, metrics)  # 0~1
        
        # 计算总分
        score = (
            self.config.relevance_weight * relevance +
            self.config.belief_weight * belief +
            self.config.recency_weight * recency +
            self.config.rqs_weight * rqs +
            self.config.novelty_weight * novelty +
            self.config.conflict_weight * conflict
        )
        
        # 限制范围
        score = max(0.0, min(1.0, score))
        
        # 更新缓存
        self.score_cache[cache_key] = (score, time.time())
        
        # 清理过期缓存
        self._clean_cache()
        
        # 更新统计
        computation_time = time.time() - start_time
        self.stats["total_scores_computed"] += 1
        self.stats["avg_computation_time"] = (
            (self.stats["avg_computation_time"] * (self.stats["total_scores_computed"] - 1) + computation_time)
            / self.stats["total_scores_computed"]
        )
        
        return score
    
    def _compute_relevance(self, node: Any, query: str) -> float:
        """计算相关性分数"""
        # 简化：基于文本匹配
        query_terms = set(query.lower().split())
        node_text = getattr(node, 'text', '') or getattr(node, 'name', '') or str(node.id)
        node_terms = set(node_text.lower().split())
        
        if not query_terms or not node_terms:
            return 0.1  # 默认低相关性
        
        # 计算Jaccard相似度
        intersection = len(query_terms.intersection(node_terms))
        union = len(query_terms.union(node_terms))
        
        if union == 0:
            return 0.1
        
        similarity = intersection / union
        
        # 增强：考虑部分匹配
        partial_matches = sum(1 for q_term in query_terms 
                             for n_term in node_terms 
                             if q_term in n_term or n_term in q_term)
        
        if partial_matches > 0:
            similarity = max(similarity, 0.3)
        
        return min(1.0, similarity)
    
    def _compute_belief(self, node: Any, metrics: Dict[str, Any]) -> float:
        """计算信念分数"""
        # 从节点获取信念强度
        belief_strength = getattr(node, 'belief_strength', None)
        if belief_strength is not None:
            return float(belief_strength)
        
        # 从metrics获取
        node_belief = metrics.get('belief_scores', {}).get(node.id, {})
        if isinstance(node_belief, dict):
            return node_belief.get('strength', 0.5)
        elif isinstance(node_belief, (int, float)):
            return float(node_belief)
        
        return 0.5  # 默认中等信念
    
    def _compute_recency(self, node: Any, metrics: Dict[str, Any]) -> float:
        """计算新鲜度分数"""
        # 获取节点时间戳
        timestamp = getattr(node, 'timestamp', None)
        if timestamp is None:
            # 尝试从metrics获取
            node_info = metrics.get('node_info', {}).get(node.id, {})
            timestamp = node_info.get('last_used')
        
        if timestamp is None:
            return 0.3  # 默认中等新鲜度
        
        # 转换为datetime
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return 0.3
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp)
        
        # 计算时间衰减
        now = datetime.now()
        if timestamp.tzinfo:
            now = datetime.now(timestamp.tzinfo)
        
        time_diff = now - timestamp
        hours_diff = time_diff.total_seconds() / 3600
        
        # 指数衰减：24小时衰减到0.1
        decay_rate = 0.1
        recency = math.exp(-decay_rate * hours_diff)
        
        return min(1.0, max(0.1, recency))
    
    def _compute_rqs(self, node: Any, metrics: Dict[str, Any]) -> float:
        """计算RQS分数"""
        # 从metrics获取RQS
        rqs_scores = metrics.get('rqs_scores', {})
        node_rqs = rqs_scores.get(node.id)
        
        if node_rqs is not None:
            return float(node_rqs)
        
        # 从节点属性获取
        node_rqs = getattr(node, 'rqs', None)
        if node_rqs is not None:
            return float(node_rqs)
        
        return 0.5  # 默认中等RQS
    
    def _compute_novelty(self, node: Any, metrics: Dict[str, Any]) -> float:
        """计算新颖性分数"""
        # 获取节点使用频率
        usage_count = getattr(node, 'usage_count', 0)
        if usage_count == 0:
            return 1.0  # 从未使用过，高新颖性
        
        # 获取最近使用时间
        last_used = getattr(node, 'last_used', None)
        if last_used is None:
            # 从metrics获取
            node_info = metrics.get('node_info', {}).get(node.id, {})
            last_used = node_info.get('last_used')
        
        if last_used is None:
            # 基于使用频率计算
            novelty = 1.0 / (1.0 + math.log1p(usage_count))
            return min(1.0, max(0.1, novelty))
        
        # 转换为datetime
        if isinstance(last_used, str):
            try:
                last_used = datetime.fromisoformat(last_used.replace('Z', '+00:00'))
            except:
                return 0.5
        elif isinstance(last_used, (int, float)):
            last_used = datetime.fromtimestamp(last_used)
        
        # 计算时间衰减
        now = datetime.now()
        if last_used.tzinfo:
            now = datetime.now(last_used.tzinfo)
        
        time_diff = now - last_used
        days_diff = time_diff.total_seconds() / 86400
        
        # 新颖性 = 时间衰减 + 频率衰减
        time_novelty = min(1.0, days_diff / 30)  # 30天达到最大新颖性
        freq_novelty = 1.0 / (1.0 + math.log1p(usage_count))
        
        novelty = 0.6 * time_novelty + 0.4 * freq_novelty
        
        return min(1.0, max(0.1, novelty))
    
    def _compute_conflict(self, node: Any, metrics: Dict[str, Any]) -> float:
        """计算冲突分数（低冲突 = 高分数）"""
        # 获取冲突信息
        conflict_count = getattr(node, 'conflict_count', 0)
        
        # 从metrics获取
        node_conflicts = metrics.get('conflicts', {}).get(node.id, {})
        if isinstance(node_conflicts, dict):
            conflict_count = node_conflicts.get('count', conflict_count)
        elif isinstance(node_conflicts, (int, float)):
            conflict_count = int(node_conflicts)
        
        # 冲突分数 = 1 - 冲突影响
        conflict_impact = min(1.0, conflict_count / 10.0)  # 最多10次冲突
        conflict_score = 1.0 - conflict_impact
        
        return max(0.1, conflict_score)  # 最低0.1分
    
    def _clean_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, (_, timestamp) in self.score_cache.items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.score_cache[key]
    
    def get_component_scores(self, node: Any, query: str, 
                            metrics: Dict[str, Any]) -> Dict[str, float]:
        """获取各个组件分数（用于调试）"""
        return {
            "relevance": self._compute_relevance(node, query),
            "belief": self._compute_belief(node, metrics),
            "recency": self._compute_recency(node, metrics),
            "rqs": self._compute_rqs(node, metrics),
            "novelty": self._compute_novelty(node, metrics),
            "conflict": self._compute_conflict(node, metrics)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_size = len(self.score_cache)
        cache_hit_rate = 0.0
        if self.stats["total_scores_computed"] > 0:
            cache_hit_rate = self.stats["cache_hits"] / self.stats["total_scores_computed"]
        
        return {
            "config": self.config.to_dict(),
            "performance": {
                "total_scores_computed": self.stats["total_scores_computed"],
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "cache_hit_rate": cache_hit_rate,
                "cache_size": cache_size,
                "avg_computation_time_ms": self.stats["avg_computation_time"] * 1000
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_scores_computed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_computation_time": 0.0
        }
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        perf = stats["performance"]
        
        print(f"   📊 Attention Scorer状态:")
        print(f"      配置:")
        print(f"        top_k: {config['top_k']}")
        print(f"        权重: 相关性{config['relevance_weight']:.2f}, "
              f"信念{config['belief_weight']:.2f}, "
              f"新鲜度{config['recency_weight']:.2f}")
        print(f"        RQS{config['rqs_weight']:.2f}, "
              f"新颖性{config['novelty_weight']:.2f}, "
              f"冲突{config['conflict_weight']:.2f}")
        
        print(f"      性能:")
        print(f"        总计算次数: {perf['total_scores_computed']}")
        print(f"        缓存命中率: {perf['cache_hit_rate']:.1%}")
        print(f"        缓存大小: {perf['cache_size']}")
        print(f"        平均计算时间: {perf['avg_computation_time_ms']:.2f}ms")