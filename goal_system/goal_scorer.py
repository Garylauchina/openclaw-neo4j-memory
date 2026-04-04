#!/usr/bin/env python3
"""
Goal Scorer（目标评分器）
核心：目标评分和选择
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import time

from .goal import Goal

@dataclass
class GoalScorerConfig:
    """目标评分器配置"""
    priority_weight: float = 0.4
    confidence_weight: float = 0.3
    progress_weight: float = 0.3
    recency_weight: float = 0.2
    activation_weight: float = 0.1
    min_score_threshold: float = 0.1
    enable_context_matching: bool = True
    
    def validate(self):
        """验证配置"""
        weights = [
            self.priority_weight,
            self.confidence_weight,
            self.progress_weight
        ]
        
        total_weight = sum(weights)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"核心权重总和应为1.0，当前为{total_weight:.3f}")
        
        if not 0.0 <= self.recency_weight <= 0.5:
            raise ValueError(f"recency_weight必须在0~0.5之间，当前为{self.recency_weight}")
        
        if not 0.0 <= self.activation_weight <= 0.5:
            raise ValueError(f"activation_weight必须在0~0.5之间，当前为{self.activation_weight}")
        
        if not 0.0 <= self.min_score_threshold <= 0.5:
            raise ValueError(f"min_score_threshold必须在0~0.5之间，当前为{self.min_score_threshold}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "priority_weight": self.priority_weight,
            "confidence_weight": self.confidence_weight,
            "progress_weight": self.progress_weight,
            "recency_weight": self.recency_weight,
            "activation_weight": self.activation_weight,
            "min_score_threshold": self.min_score_threshold,
            "enable_context_matching": self.enable_context_matching
        }

class GoalScorer:
    """目标评分器"""
    
    def __init__(self, config: Optional[GoalScorerConfig] = None):
        self.config = config or GoalScorerConfig()
        self.config.validate()
        
        # 缓存机制
        self.score_cache: Dict[str, Tuple[float, float]] = {}  # goal_id -> (score, timestamp)
        self.cache_ttl = 60  # 1分钟缓存
        
        # 统计信息
        self.stats = {
            "total_scores_computed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_computation_time": 0.0,
            "score_distribution": {
                "excellent": 0,  # >0.8
                "good": 0,       # 0.6~0.8
                "fair": 0,       # 0.4~0.6
                "poor": 0,       # 0.2~0.4
                "very_poor": 0   # <=0.2
            }
        }
    
    def score_goal(self, goal: Goal, context: Optional[Dict[str, Any]] = None) -> float:
        """
        评分目标
        
        Args:
            goal: 目标对象
            context: 上下文信息
        
        Returns:
            float: 目标评分 (0~1)
        """
        start_time = time.time()
        
        # 检查缓存
        cache_key = f"{goal.id}_{hash(str(context)) if context else 'no_context'}"
        if cache_key in self.score_cache:
            score, timestamp = self.score_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                self.stats["cache_hits"] += 1
                return score
        
        self.stats["cache_misses"] += 1
        
        # 1. 基础评分
        base_score = self._compute_base_score(goal)
        
        # 2. 上下文匹配评分（如果启用）
        context_score = 0.0
        if self.config.enable_context_matching and context:
            context_score = self._compute_context_score(goal, context)
        
        # 3. 综合评分
        if self.config.enable_context_matching and context:
            # 加权平均：70%基础评分 + 30%上下文评分
            final_score = 0.7 * base_score + 0.3 * context_score
        else:
            final_score = base_score
        
        # 4. 应用阈值
        if final_score < self.config.min_score_threshold:
            final_score = self.config.min_score_threshold
        
        # 限制范围
        final_score = max(0.0, min(1.0, final_score))
        
        # 5. 更新缓存
        self.score_cache[cache_key] = (final_score, time.time())
        
        # 6. 清理过期缓存
        self._clean_cache()
        
        # 7. 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(final_score, elapsed_time)
        
        return final_score
    
    def _compute_base_score(self, goal: Goal) -> float:
        """计算基础评分"""
        # 1. 核心组件
        priority_component = goal.priority * self.config.priority_weight
        confidence_component = goal.confidence * self.config.confidence_weight
        progress_component = (1 - goal.progress) * self.config.progress_weight  # 进度越低，得分越高（鼓励未完成的目标）
        
        # 2. 时间组件（新鲜度）
        recency_component = self._compute_recency_score(goal) * self.config.recency_weight
        
        # 3. 激活组件（激活次数越多，得分越低，防止过度激活）
        activation_component = self._compute_activation_score(goal) * self.config.activation_weight
        
        # 4. 综合评分
        base_score = (
            priority_component +
            confidence_component +
            progress_component +
            recency_component -
            activation_component  # 激活组件是负向的
        )
        
        return max(0.0, min(1.0, base_score))
    
    def _compute_context_score(self, goal: Goal, context: Dict[str, Any]) -> float:
        """计算上下文匹配评分"""
        context_score = 0.0
        
        # 1. 查询匹配
        current_query = context.get("current_query", "")
        if current_query:
            query_similarity = self._compute_text_similarity(goal.description, current_query)
            context_score += 0.4 * query_similarity
        
        # 2. 领域匹配
        goal_domain = goal.metadata.get("domain", "")
        context_domain = context.get("domain", "")
        if goal_domain and context_domain:
            if goal_domain == context_domain:
                context_score += 0.3
        
        # 3. 节点匹配
        goal_nodes = set(goal.related_nodes)
        context_nodes = set(context.get("active_nodes", []))
        
        if goal_nodes and context_nodes:
            overlap = len(goal_nodes.intersection(context_nodes))
            total = len(goal_nodes.union(context_nodes))
            
            if total > 0:
                node_similarity = overlap / total
                context_score += 0.3 * node_similarity
        
        return max(0.0, min(1.0, context_score))
    
    def _compute_recency_score(self, goal: Goal) -> float:
        """计算新鲜度评分"""
        from datetime import datetime
        
        now = datetime.now()
        hours_since_update = (now - goal.last_updated).total_seconds() / 3600
        
        # 指数衰减：24小时衰减到0.5
        decay_rate = 0.03
        recency_score = 1.0 / (1.0 + decay_rate * hours_since_update)
        
        return max(0.1, min(1.0, recency_score))
    
    def _compute_activation_score(self, goal: Goal) -> float:
        """计算激活评分（负向）"""
        # 激活次数越多，负向评分越高（防止过度激活）
        activation_penalty = min(1.0, goal.activation_count / 10.0)  # 10次激活达到最大惩罚
        
        return activation_penalty
    
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
        
        similarity = intersection / union
        
        # 增强：考虑部分匹配
        partial_matches = sum(1 for w1 in words1 
                             for w2 in words2 
                             if w1 in w2 or w2 in w1)
        
        if partial_matches > 0:
            similarity = max(similarity, 0.3)
        
        return min(1.0, similarity)
    
    def _clean_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, (_, timestamp) in self.score_cache.items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.score_cache[key]
    
    def _update_stats(self, score: float, elapsed_time: float):
        """更新统计信息"""
        self.stats["total_scores_computed"] += 1
        
        # 更新分数分布
        if score > 0.8:
            self.stats["score_distribution"]["excellent"] += 1
        elif score > 0.6:
            self.stats["score_distribution"]["good"] += 1
        elif score > 0.4:
            self.stats["score_distribution"]["fair"] += 1
        elif score > 0.2:
            self.stats["score_distribution"]["poor"] += 1
        else:
            self.stats["score_distribution"]["very_poor"] += 1
        
        # 更新平均计算时间
        self.stats["avg_computation_time"] = (
            (self.stats["avg_computation_time"] * (self.stats["total_scores_computed"] - 1) + elapsed_time)
            / self.stats["total_scores_computed"]
        )
    
    def select_top_goals(self, goals: List[Goal], 
                        context: Optional[Dict[str, Any]] = None,
                        top_k: int = 3) -> List[Tuple[Goal, float]]:
        """
        选择Top-K目标
        
        Args:
            goals: 目标列表
            context: 上下文信息
            top_k: 选择数量
        
        Returns:
            List[Tuple[Goal, float]]: [(goal, score)] 目标和评分
        """
        if not goals:
            return []
        
        # 评分所有目标
        scored_goals = []
        for goal in goals:
            score = self.score_goal(goal, context)
            scored_goals.append((goal, score))
        
        # 排序
        sorted_goals = sorted(scored_goals, key=lambda x: x[1], reverse=True)
        
        # 选择Top-K
        return sorted_goals[:top_k]
    
    def get_goal_recommendations(self, goals: List[Goal],
                               context: Optional[Dict[str, Any]] = None,
                               recommendation_count: int = 5) -> List[Dict[str, Any]]:
        """
        获取目标推荐
        
        Args:
            goals: 目标列表
            context: 上下文信息
            recommendation_count: 推荐数量
        
        Returns:
            List[Dict[str, Any]]: 推荐列表
        """
        if not goals:
            return []
        
        # 评分所有目标
        scored_goals = []
        for goal in goals:
            score = self.score_goal(goal, context)
            scored_goals.append((goal, score))
        
        # 排序
        sorted_goals = sorted(scored_goals, key=lambda x: x[1], reverse=True)
        
        # 生成推荐
        recommendations = []
        for i, (goal, score) in enumerate(sorted_goals[:recommendation_count]):
            recommendation = {
                "rank": i + 1,
                "goal_id": goal.id,
                "description": goal.description,
                "score": score,
                "priority": goal.priority,
                "confidence": goal.confidence,
                "progress": goal.progress,
                "is_active": goal.is_active,
                "is_completed": goal.is_completed,
                "reason": self._generate_recommendation_reason(goal, score, context)
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_recommendation_reason(self, goal: Goal, score: float, 
                                      context: Optional[Dict[str, Any]] = None) -> str:
        """生成推荐理由"""
        reasons = []
        
        # 基于分数
        if score > 0.8:
            reasons.append("评分极高")
        elif score > 0.6:
            reasons.append("评分良好")
        
        # 基于优先级
        if goal.priority > 0.7:
            reasons.append("重要性高")
        
        # 基于进度
        if goal.progress < 0.3:
            reasons.append("刚开始")
        elif goal.progress > 0.7:
            reasons.append("接近完成")
        
        # 基于上下文匹配
        if context and self.config.enable_context_matching:
            current_query = context.get("current_query", "")
            if current_query and self._compute_text_similarity(goal.description, current_query) > 0.5:
                reasons.append("与当前查询高度相关")
        
        # 默认理由
        if not reasons:
            reasons.append("综合评分较高")
        
        return "，".join(reasons)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_size = len(self.score_cache)
        cache_hit_rate = 0.0
        if self.stats["total_scores_computed"] > 0:
            cache_hit_rate = self.stats["cache_hits"] / self.stats["total_scores_computed"]
        
        # 计算分数分布百分比
        total_scores = self.stats["total_scores_computed"]
        score_distribution_pct = {}
        if total_scores > 0:
            for category, count in self.stats["score_distribution"].items():
                score_distribution_pct[category] = count / total_scores
        
        return {
            "config": self.config.to_dict(),
            "performance": {
                "total_scores_computed": self.stats["total_scores_computed"],
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "cache_hit_rate": cache_hit_rate,
                "cache_size": cache_size,
                "avg_computation_time_ms": self.stats["avg_computation_time"] * 1000
            },
            "score_distribution": {
                "counts": self.stats["score_distribution"],
                "percentages": score_distribution_pct
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_scores_computed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_computation_time": 0.0,
            "score_distribution": {
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "poor": 0,
                "very_poor": 0
            }
        }
        self.score_cache.clear()
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        perf = stats["performance"]
        dist_counts = stats["score_distribution"]["counts"]
        dist_pct = stats["score_distribution"]["percentages"]
        
        print(f"   📊 Goal Scorer状态:")
        print(f"      配置:")
        print(f"        权重: 优先级{config['priority_weight']:.2f}, "
              f"置信度{config['confidence_weight']:.2f}, "
              f"进度{config['progress_weight']:.2f}")
        print(f"        额外权重: 新鲜度{config['recency_weight']:.2f}, "
              f"激活{config['activation_weight']:.2f}")
        print(f"        最低分数阈值: {config['min_score_threshold']:.2f}")
        print(f"        启用上下文匹配: {config['enable_context_matching']}")
        
        print(f"      性能:")
        print(f"        总计算次数: {perf['total_scores_computed']}")
        print(f"        缓存命中率: {perf['cache_hit_rate']:.1%}")
        print(f"        缓存大小: {perf['cache_size']}")
        print(f"        平均计算时间: {perf['avg_computation_time_ms']:.2f}ms")
        
        print(f"      分数分布:")
        if perf['total_scores_computed'] > 0:
            print(f"        优秀 (>0.8): {dist_counts['excellent']} ({dist_pct.get('excellent', 0):.1%})")
            print(f"        良好 (0.6~0.8): {dist_counts['good']} ({dist_pct.get('good', 0):.1%})")
            print(f"        一般 (0.4~0.6): {dist_counts['fair']} ({dist_pct.get('fair', 0):.1%})")
            print(f"        差 (0.2~0.4): {dist_counts['poor']} ({dist_pct.get('poor', 0):.1%})")
            print(f"        极差 (≤0.2): {dist_counts['very_poor']} ({dist_pct.get('very_poor', 0):.1%})")