#!/usr/bin/env python3
"""
Goal Generator（目标生成器）
核心：从Query自动生成目标
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime

from .goal import Goal

@dataclass
class GoalGeneratorConfig:
    """目标生成器配置"""
    default_priority: float = 0.5
    default_confidence: float = 0.5
    enable_priority_estimation: bool = True
    enable_type_detection: bool = True
    min_query_length: int = 3
    max_goals_per_query: int = 3
    
    def validate(self):
        """验证配置"""
        if not 0.0 <= self.default_priority <= 1.0:
            raise ValueError(f"default_priority必须在0~1之间，当前为{self.default_priority}")
        
        if not 0.0 <= self.default_confidence <= 1.0:
            raise ValueError(f"default_confidence必须在0~1之间，当前为{self.default_confidence}")
        
        if self.min_query_length < 1:
            raise ValueError(f"min_query_length必须大于0，当前为{self.min_query_length}")
        
        if self.max_goals_per_query < 1:
            raise ValueError(f"max_goals_per_query必须大于0，当前为{self.max_goals_per_query}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "default_priority": self.default_priority,
            "default_confidence": self.default_confidence,
            "enable_priority_estimation": self.enable_priority_estimation,
            "enable_type_detection": self.enable_type_detection,
            "min_query_length": self.min_query_length,
            "max_goals_per_query": self.max_goals_per_query
        }

class GoalGenerator:
    """目标生成器"""
    
    # 目标类型检测规则
    GOAL_TYPE_PATTERNS = {
        "query_understanding": [
            r"什么是", r"解释", r"说明", r"介绍", r"定义",
            r"meaning of", r"explain", r"define", r"what is"
        ],
        "problem_solving": [
            r"如何", r"怎么", r"解决", r"处理", r"应对",
            r"how to", r"solve", r"fix", r"handle", r"deal with"
        ],
        "information_gathering": [
            r"查找", r"搜索", r"寻找", r"获取", r"收集",
            r"find", r"search", r"look for", r"get", r"collect"
        ],
        "comparison": [
            r"比较", r"对比", r"区别", r"差异",
            r"compare", r"difference", r"vs", r"versus"
        ],
        "analysis": [
            r"分析", r"评估", r"评价", r"判断",
            r"analyze", r"evaluate", r"assess", r"judge"
        ],
        "prediction": [
            r"预测", r"预计", r"估计", r"推测",
            r"predict", r"forecast", r"estimate", r"guess"
        ]
    }
    
    # 优先级关键词
    PRIORITY_KEYWORDS = {
        "high": [
            r"紧急", r"重要", r"关键", r"必须", r"尽快",
            r"urgent", r"important", r"critical", r"must", r"asap"
        ],
        "medium": [
            r"一般", r"普通", r"常见", r"通常",
            r"normal", r"common", r"usual", r"general"
        ],
        "low": [
            r"随便", r"随意", r"不重要", r"次要",
            r"casual", r"unimportant", r"secondary", r"minor"
        ]
    }
    
    def __init__(self, config: Optional[GoalGeneratorConfig] = None):
        self.config = config or GoalGeneratorConfig()
        self.config.validate()
        
        # 统计信息
        self.stats = {
            "total_queries_processed": 0,
            "total_goals_generated": 0,
            "goal_type_distribution": {},
            "avg_goals_per_query": 0.0,
            "avg_generation_time": 0.0
        }
    
    def generate_goal(self, query: str, context: Optional[Dict[str, Any]] = None) -> Goal:
        """
        从查询生成目标
        
        Args:
            query: 用户查询
            context: 上下文信息
        
        Returns:
            Goal: 生成的目标
        """
        import time
        start_time = time.time()
        
        # 1. 验证查询
        if len(query.strip()) < self.config.min_query_length:
            raise ValueError(f"查询过短: '{query}' (最小长度: {self.config.min_query_length})")
        
        # 2. 检测目标类型
        goal_type = self._detect_goal_type(query)
        
        # 3. 估计优先级
        priority = self._estimate_priority(query, context)
        
        # 4. 生成目标描述
        description = self._generate_description(query, goal_type)
        
        # 5. 创建目标
        goal = Goal(
            description=description,
            goal_type=goal_type,
            priority=priority,
            confidence=self.config.default_confidence
        )
        
        # 6. 添加上下文信息
        if context:
            self._add_context_to_goal(goal, context)
        
        # 7. 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(1, goal_type, elapsed_time)
        
        return goal
    
    def generate_multiple_goals(self, query: str, 
                              context: Optional[Dict[str, Any]] = None) -> List[Goal]:
        """
        从查询生成多个目标
        
        Args:
            query: 用户查询
            context: 上下文信息
        
        Returns:
            List[Goal]: 生成的目标列表
        """
        import time
        start_time = time.time()
        
        goals = []
        
        # 1. 主目标（基于整个查询）
        main_goal = self.generate_goal(query, context)
        goals.append(main_goal)
        
        # 2. 子目标（如果查询包含多个部分）
        if self._has_multiple_parts(query) and len(goals) < self.config.max_goals_per_query:
            sub_goals = self._extract_sub_goals(query, context)
            goals.extend(sub_goals[:self.config.max_goals_per_query - 1])
        
        # 3. 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(len(goals), "multiple", elapsed_time)
        
        return goals
    
    def _detect_goal_type(self, query: str) -> str:
        """检测目标类型"""
        if not self.config.enable_type_detection:
            return "query_understanding"
        
        query_lower = query.lower()
        
        # 检查每种类型
        for goal_type, patterns in self.GOAL_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return goal_type
        
        # 默认类型
        return "query_understanding"
    
    def _estimate_priority(self, query: str, context: Optional[Dict[str, Any]] = None) -> float:
        """估计优先级"""
        if not self.config.enable_priority_estimation:
            return self.config.default_priority
        
        query_lower = query.lower()
        priority_score = self.config.default_priority
        
        # 检查高优先级关键词
        for pattern in self.PRIORITY_KEYWORDS["high"]:
            if re.search(pattern, query_lower, re.IGNORECASE):
                priority_score = max(priority_score, 0.8)
                break
        
        # 检查低优先级关键词
        for pattern in self.PRIORITY_KEYWORDS["low"]:
            if re.search(pattern, query_lower, re.IGNORECASE):
                priority_score = min(priority_score, 0.3)
                break
        
        # 考虑上下文
        if context:
            # 从上下文获取额外信息
            context_priority = context.get("priority", None)
            if context_priority is not None:
                # 加权平均
                priority_score = 0.7 * priority_score + 0.3 * float(context_priority)
        
        return max(0.1, min(1.0, priority_score))
    
    def _generate_description(self, query: str, goal_type: str) -> str:
        """生成目标描述"""
        # 根据目标类型生成不同的描述
        descriptions = {
            "query_understanding": f"理解查询: {query}",
            "problem_solving": f"解决问题: {query}",
            "information_gathering": f"收集信息: {query}",
            "comparison": f"进行比较: {query}",
            "analysis": f"进行分析: {query}",
            "prediction": f"进行预测: {query}"
        }
        
        return descriptions.get(goal_type, f"处理查询: {query}")
    
    def _add_context_to_goal(self, goal: Goal, context: Dict[str, Any]):
        """添加上下文信息到目标"""
        # 添加相关节点
        related_nodes = context.get("related_nodes", [])
        for node_id in related_nodes[:10]:  # 限制数量
            goal.add_related_node(node_id)
        
        # 添加元数据
        if "query_complexity" in context:
            goal.metadata["complexity"] = context["query_complexity"]
        
        if "user_intent" in context:
            goal.metadata["user_intent"] = context["user_intent"]
        
        if "domain" in context:
            goal.metadata["domain"] = context["domain"]
    
    def _has_multiple_parts(self, query: str) -> bool:
        """检查查询是否包含多个部分"""
        # 检查分隔符
        separators = ["和", "与", "以及", "还有", "并且", 
                     "and", "&", ",", ";", "同时"]
        
        for sep in separators:
            if sep in query:
                return True
        
        # 检查问题数量
        question_marks = query.count("?") + query.count("？")
        return question_marks > 1
    
    def _extract_sub_goals(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Goal]:
        """提取子目标"""
        sub_goals = []
        
        # 简单分割（实际应用中可以使用更复杂的分割逻辑）
        separators = ["和", "与", "以及", "还有", "并且", 
                     "and", "&", ",", ";", "同时"]
        
        current_query = query
        for sep in separators:
            if sep in current_query:
                parts = current_query.split(sep)
                for part in parts:
                    part = part.strip()
                    if len(part) >= self.config.min_query_length:
                        try:
                            sub_goal = self.generate_goal(part, context)
                            sub_goals.append(sub_goal)
                        except ValueError:
                            # 忽略过短的查询
                            pass
                break
        
        return sub_goals
    
    def _update_stats(self, goals_generated: int, goal_type: str, elapsed_time: float):
        """更新统计信息"""
        self.stats["total_queries_processed"] += 1
        self.stats["total_goals_generated"] += goals_generated
        
        # 更新目标类型分布
        if goal_type not in self.stats["goal_type_distribution"]:
            self.stats["goal_type_distribution"][goal_type] = 0
        self.stats["goal_type_distribution"][goal_type] += goals_generated
        
        # 更新平均目标数
        self.stats["avg_goals_per_query"] = (
            (self.stats["avg_goals_per_query"] * (self.stats["total_queries_processed"] - 1) + goals_generated)
            / self.stats["total_queries_processed"]
        )
        
        # 更新平均生成时间
        self.stats["avg_generation_time"] = (
            (self.stats["avg_generation_time"] * (self.stats["total_queries_processed"] - 1) + elapsed_time)
            / self.stats["total_queries_processed"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "config": self.config.to_dict(),
            "performance": {
                "total_queries_processed": self.stats["total_queries_processed"],
                "total_goals_generated": self.stats["total_goals_generated"],
                "avg_goals_per_query": self.stats["avg_goals_per_query"],
                "avg_generation_time_ms": self.stats["avg_generation_time"] * 1000,
                "goal_type_distribution": self.stats["goal_type_distribution"]
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_queries_processed": 0,
            "total_goals_generated": 0,
            "goal_type_distribution": {},
            "avg_goals_per_query": 0.0,
            "avg_generation_time": 0.0
        }
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        perf = stats["performance"]
        
        print(f"   📊 Goal Generator状态:")
        print(f"      配置:")
        print(f"        默认优先级: {config['default_priority']:.2f}")
        print(f"        默认置信度: {config['default_confidence']:.2f}")
        print(f"        启用优先级估计: {config['enable_priority_estimation']}")
        print(f"        启用类型检测: {config['enable_type_detection']}")
        print(f"        最小查询长度: {config['min_query_length']}")
        print(f"        最大目标数/查询: {config['max_goals_per_query']}")
        
        print(f"      性能:")
        print(f"        总处理查询数: {perf['total_queries_processed']}")
        print(f"        总生成目标数: {perf['total_goals_generated']}")
        print(f"        平均目标数/查询: {perf['avg_goals_per_query']:.2f}")
        print(f"        平均生成时间: {perf['avg_generation_time_ms']:.2f}ms")
        
        if perf["goal_type_distribution"]:
            print(f"      目标类型分布:")
            for goal_type, count in perf["goal_type_distribution"].items():
                percentage = count / perf["total_goals_generated"] * 100
                print(f"        {goal_type}: {count} ({percentage:.1f}%)")