#!/usr/bin/env python3
"""
Goal Manager（目标管理器）
核心：目标生命周期管理和Goal-Aware Attention耦合
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time
from datetime import datetime, timedelta

from .goal import Goal
from .goal_generator import GoalGenerator, GoalGeneratorConfig
from .goal_scorer import GoalScorer, GoalScorerConfig

@dataclass
class GoalManagerConfig:
    """目标管理器配置"""
    # 目标生成配置
    generator_config: GoalGeneratorConfig = field(default_factory=GoalGeneratorConfig)
    
    # 目标评分配置
    scorer_config: GoalScorerConfig = field(default_factory=GoalScorerConfig)
    
    # 目标管理配置
    max_active_goals: int = 3
    max_total_goals: int = 100
    goal_ttl_hours: int = 24  # 目标存活时间（小时）
    enable_goal_persistence: bool = True
    goal_update_learning_rate: float = 0.05
    
    def validate(self):
        """验证配置"""
        if self.max_active_goals < 1:
            raise ValueError(f"max_active_goals必须大于0，当前为{self.max_active_goals}")
        
        if self.max_total_goals < self.max_active_goals:
            raise ValueError(f"max_total_goals必须大于等于max_active_goals")
        
        if self.goal_ttl_hours < 1:
            raise ValueError(f"goal_ttl_hours必须大于0，当前为{self.goal_ttl_hours}")
        
        if not 0.0 < self.goal_update_learning_rate <= 0.1:
            raise ValueError(f"goal_update_learning_rate必须在0~0.1之间，当前为{self.goal_update_learning_rate}")
        
        # 验证子配置
        self.generator_config.validate()
        self.scorer_config.validate()
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "generator_config": self.generator_config.to_dict(),
            "scorer_config": self.scorer_config.to_dict(),
            "max_active_goals": self.max_active_goals,
            "max_total_goals": self.max_total_goals,
            "goal_ttl_hours": self.goal_ttl_hours,
            "enable_goal_persistence": self.enable_goal_persistence,
            "goal_update_learning_rate": self.goal_update_learning_rate
        }

class GoalManager:
    """目标管理器"""
    
    def __init__(self, config: Optional[GoalManagerConfig] = None):
        self.config = config or GoalManagerConfig()
        self.config.validate()
        
        # 初始化组件
        self.generator = GoalGenerator(self.config.generator_config)
        self.scorer = GoalScorer(self.config.scorer_config)
        
        # 目标存储
        self.goals: Dict[str, Goal] = {}  # goal_id -> Goal
        self.active_goal_ids: List[str] = []  # 活跃目标ID列表（按激活时间排序）
        
        # 统计信息
        self.stats = {
            "total_goals_created": 0,
            "total_goals_completed": 0,
            "total_goals_expired": 0,
            "total_goal_activations": 0,
            "avg_goals_per_query": 0.0,
            "avg_goal_lifetime_hours": 0.0,
            "goal_completion_rate": 0.0
        }
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Goal]:
        """
        处理查询，生成和管理目标
        
        Args:
            query: 用户查询
            context: 上下文信息
        
        Returns:
            List[Goal]: 生成的目标列表
        """
        # 1. 生成目标
        new_goals = self.generator.generate_multiple_goals(query, context)
        
        # 2. 添加目标到管理器
        for goal in new_goals:
            self.add_goal(goal)
        
        # 3. 选择活跃目标
        self._update_active_goals(context)
        
        # 4. 清理过期目标
        self._cleanup_expired_goals()
        
        return new_goals
    
    def add_goal(self, goal: Goal) -> bool:
        """添加目标到管理器"""
        # 检查是否已存在
        if goal.id in self.goals:
            return False
        
        # 检查总数限制
        if len(self.goals) >= self.config.max_total_goals:
            # 移除最旧的非活跃目标
            self._remove_oldest_inactive_goal()
        
        # 添加目标
        self.goals[goal.id] = goal
        self.stats["total_goals_created"] += 1
        
        return True
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """获取目标"""
        return self.goals.get(goal_id)
    
    def get_active_goals(self) -> List[Goal]:
        """获取活跃目标"""
        active_goals = []
        for goal_id in self.active_goal_ids:
            goal = self.goals.get(goal_id)
            if goal and goal.is_active:
                active_goals.append(goal)
        
        return active_goals
    
    def get_recommended_goals(self, context: Optional[Dict[str, Any]] = None, 
                            limit: int = 5) -> List[Tuple[Goal, float]]:
        """获取推荐目标"""
        all_goals = list(self.goals.values())
        
        # 使用评分器选择Top-K
        scored_goals = self.scorer.select_top_goals(all_goals, context, top_k=limit)
        
        return scored_goals
    
    def update_goal(self, goal_id: str, success: bool, 
                   progress_delta: float = 0.0, 
                   context: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新目标状态
        
        Args:
            goal_id: 目标ID
            success: 是否成功
            progress_delta: 进度变化
            context: 上下文信息
        
        Returns:
            bool: 是否成功更新
        """
        goal = self.get_goal(goal_id)
        if not goal:
            return False
        
        # 1. 更新置信度
        goal.update_confidence(success, self.config.goal_update_learning_rate)
        
        # 2. 更新进度
        if progress_delta != 0:
            reason = "success" if success else "failure"
            goal.update_progress(progress_delta, reason)
        
        # 3. 如果是成功且目标完成，更新统计
        if success and goal.is_completed:
            self.stats["total_goals_completed"] += 1
            
            # 计算目标生命周期
            lifetime_hours = (datetime.now() - goal.created_at).total_seconds() / 3600
            self.stats["avg_goal_lifetime_hours"] = (
                (self.stats["avg_goal_lifetime_hours"] * (self.stats["total_goals_completed"] - 1) + lifetime_hours)
                / self.stats["total_goals_completed"]
            )
        
        # 4. 更新完成率
        if self.stats["total_goals_created"] > 0:
            self.stats["goal_completion_rate"] = (
                self.stats["total_goals_completed"] / self.stats["total_goals_created"]
            )
        
        # 5. 如果目标不再活跃，从活跃列表中移除
        if not goal.is_active and goal_id in self.active_goal_ids:
            self.active_goal_ids.remove(goal_id)
        
        return True
    
    def activate_goal(self, goal_id: str) -> bool:
        """激活目标"""
        goal = self.get_goal(goal_id)
        if not goal:
            return False
        
        # 激活目标
        goal.activate()
        
        # 添加到活跃列表（如果不在列表中）
        if goal_id not in self.active_goal_ids:
            self.active_goal_ids.append(goal_id)
        
        # 更新统计
        self.stats["total_goal_activations"] += 1
        
        # 确保活跃目标数量不超过限制
        self._enforce_active_goals_limit()
        
        return True
    
    def deactivate_goal(self, goal_id: str) -> bool:
        """停用目标"""
        goal = self.get_goal(goal_id)
        if not goal:
            return False
        
        # 停用目标
        goal.deactivate()
        
        # 从活跃列表中移除
        if goal_id in self.active_goal_ids:
            self.active_goal_ids.remove(goal_id)
        
        return True
    
    def _update_active_goals(self, context: Optional[Dict[str, Any]] = None):
        """更新活跃目标"""
        # 获取推荐目标
        recommended_goals = self.get_recommended_goals(context, self.config.max_active_goals)
        
        # 停用当前所有活跃目标
        for goal_id in list(self.active_goal_ids):
            self.deactivate_goal(goal_id)
        
        # 激活推荐目标
        for goal, score in recommended_goals:
            self.activate_goal(goal.id)
    
    def _enforce_active_goals_limit(self):
        """强制执行活跃目标数量限制"""
        while len(self.active_goal_ids) > self.config.max_active_goals:
            # 移除最不活跃的目标（列表中的第一个）
            oldest_goal_id = self.active_goal_ids[0]
            self.deactivate_goal(oldest_goal_id)
    
    def _remove_oldest_inactive_goal(self):
        """移除最旧的非活跃目标"""
        inactive_goals = []
        
        for goal_id, goal in self.goals.items():
            if not goal.is_active and goal_id not in self.active_goal_ids:
                inactive_goals.append((goal_id, goal.created_at))
        
        if inactive_goals:
            # 按创建时间排序，移除最旧的
            inactive_goals.sort(key=lambda x: x[1])
            oldest_goal_id = inactive_goals[0][0]
            del self.goals[oldest_goal_id]
    
    def _cleanup_expired_goals(self):
        """清理过期目标"""
        current_time = datetime.now()
        expired_goal_ids = []
        
        for goal_id, goal in self.goals.items():
            # 检查目标是否过期
            hours_since_creation = (current_time - goal.created_at).total_seconds() / 3600
            
            if hours_since_creation > self.config.goal_ttl_hours:
                expired_goal_ids.append(goal_id)
        
        # 移除过期目标
        for goal_id in expired_goal_ids:
            # 如果目标是活跃的，先停用
            if goal_id in self.active_goal_ids:
                self.deactivate_goal(goal_id)
            
            # 移除目标
            del self.goals[goal_id]
            self.stats["total_goals_expired"] += 1
    
    def get_goal_aware_attention_score(self, node: Any, base_attention_score: float,
                                     goal: Goal, context: Optional[Dict[str, Any]] = None) -> float:
        """
        获取Goal-Aware Attention分数
        
        Args:
            node: 节点对象
            base_attention_score: 基础注意力分数
            goal: 目标对象
            context: 上下文信息
        
        Returns:
            float: Goal-Aware Attention分数
        """
        # 1. 计算目标相关性
        goal_relevance = self._compute_goal_relevance(node, goal, context)
        
        # 2. 计算Goal-Aware分数
        # 公式: goal_aware_score = base_score * goal_relevance
        goal_aware_score = base_attention_score * goal_relevance
        
        # 3. 应用目标优先级加权
        # 高优先级目标对注意力影响更大
        priority_weight = 0.5 + (goal.priority * 0.5)  # 0.5~1.0
        final_score = goal_aware_score * priority_weight
        
        return max(0.0, min(1.0, final_score))
    
    def _compute_goal_relevance(self, node: Any, goal: Goal, 
                              context: Optional[Dict[str, Any]] = None) -> float:
        """计算目标相关性"""
        relevance = 0.0
        
        # 1. 基于节点文本和目标描述的相似度
        node_text = getattr(node, 'text', '') or getattr(node, 'name', '') or str(getattr(node, 'id', ''))
        if node_text and goal.description:
            text_similarity = self._compute_text_similarity(node_text, goal.description)
            relevance += 0.4 * text_similarity
        
        # 2. 基于节点ID是否在目标相关节点中
        node_id = getattr(node, 'id', '')
        if node_id and node_id in goal.related_nodes:
            relevance += 0.3
        
        # 3. 基于上下文匹配
        if context:
            current_query = context.get("current_query", "")
            if current_query:
                # 检查节点是否与当前查询相关
                query_similarity = self._compute_text_similarity(node_text, current_query)
                relevance += 0.3 * query_similarity
        
        return max(0.1, min(1.0, relevance))
    
    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化版）"""
        if not text1 or not text2:
            return 0.1
        
        # 转换为词集
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.1
        
        # Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.1
        
        similarity = intersection / union
        
        # 增强：考虑部分匹配
        partial_matches = sum(1 for w1 in words1 
                             for w2 in words2 
                             if w1 in w2 or w2 in w1)
        
        if partial_matches > 0:
            similarity = max(similarity, 0.3)
        
        return min(1.0, similarity)
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        # 获取组件报告
        generator_report = self.generator.get_stats()
        scorer_report = self.scorer.get_stats()
        
        # 计算目标统计
        active_goals = self.get_active_goals()
        completed_goals = sum(1 for goal in self.goals.values() if goal.is_completed)
        expired_goals = self.stats["total_goals_expired"]
        
        # 计算平均目标数/查询
        total_queries = generator_report["performance"]["total_queries_processed"]
        if total_queries > 0:
            avg_goals_per_query = self.stats["total_goals_created"] / total_queries
        else:
            avg_goals_per_query = 0.0
        
        return {
            "config": self.config.to_dict(),
            "state": {
                "total_goals": len(self.goals),
                "active_goals": len(active_goals),
                "completed_goals": completed_goals,
                "expired_goals": expired_goals,
                "goal_completion_rate": self.stats["goal_completion_rate"],
                "avg_goal_lifetime_hours": self.stats["avg_goal_lifetime_hours"]
            },
            "stats": self.stats,
            "components": {
                "generator": generator_report,
                "scorer": scorer_report
            },
            "active_goals_summary": [goal.get_summary() for goal in active_goals]
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_goals_created": 0,
            "total_goals_completed": 0,
            "total_goals_expired": 0,
            "total_goal_activations": 0,
            "avg_goals_per_query": 0.0,
            "avg_goal_lifetime_hours": 0.0,
            "goal_completion_rate": 0.0
        }
        
        # 重置组件统计
        self.generator.reset_stats()
        self.scorer.reset_stats()
    
    def print_status(self):
        """打印状态"""
        report = self.get_system_report()
        config = report["config"]
        state = report["state"]
        stats = report["stats"]
        
        print(f"🧠 Goal Manager状态报告")
        print(f"="*60)
        
        print(f"📋 配置:")
        print(f"  目标管理:")
        print(f"    最大活跃目标: {config['max_active_goals']}")
        print(f"    最大总目标: {config['max_total_goals']}")
        print(f"    目标存活时间: {config['goal_ttl_hours']}小时")
        print(f"    启用目标持久化: {config['enable_goal_persistence']}")
        print(f"    目标更新学习率: {config['goal_update_learning_rate']:.3f}")
        
        print(f"\n📊 状态:")
        print(f"  总目标数: {state['total_goals']}")
        print(f"  活跃目标: {state['active_goals']}")
        print(f"  完成目标: {state['completed_goals']}")
        print(f"  过期目标: {state['expired_goals']}")
        print(f"  目标完成率: {state['goal_completion_rate']:.1%}")
        print(f"  平均目标生命周期: {state['avg_goal_lifetime_hours']:.1f}小时")
        
        print(f"\n📈 统计:")
        print(f"  总创建目标: {stats['total_goals_created']}")
        print(f"  总目标激活: {stats['total_goal_activations']}")
        print(f"  平均目标数/查询: {stats['avg_goals_per_query']:.2f}")
        
        print(f"\n🔧 组件状态:")
        self.generator.print_status()
        print()
        self.scorer.print_status()
        
        print(f"\n🎯 活跃目标:")
        active_goals = self.get_active_goals()
        if active_goals:
            for i, goal in enumerate(active_goals):
                print(f"  {i+1}. {goal.description[:50]}...")
                print(f"     重要性: {goal.priority:.2f}, 置信度: {goal.confidence:.2f}, "
                      f"完成度: {goal.progress:.1%}")
        else:
            print(f"  暂无活跃目标")
        
        print(f"\n🚀 系统升级:")
        print(f"  从: Attention-Controlled Cognitive System")
        print(f"  到: ❗ Goal-Driven Cognitive System")
        print(f"  核心能力: 让系统从'被动响应'变成'主动认知'")
        
        print(f"\n" + "="*60)