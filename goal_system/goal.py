#!/usr/bin/env python3
"""
Goal数据结构
核心：目标表示和管理
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import time

@dataclass
class Goal:
    """目标数据结构"""
    
    def __init__(self, description: str, 
                goal_type: str = "query_understanding",
                priority: float = 0.5,
                confidence: float = 0.5):
        """
        初始化目标
        
        Args:
            description: 目标描述
            goal_type: 目标类型 (query_understanding, problem_solving, information_gathering, etc.)
            priority: 重要性 (0~1)
            confidence: 目标可靠性 (0~1)
        """
        self.id = str(uuid.uuid4())
        self.description = description
        self.goal_type = goal_type
        
        # 核心属性
        self.priority = max(0.0, min(1.0, priority))  # 重要性
        self.confidence = max(0.0, min(1.0, confidence))  # 目标可靠性
        self.progress = 0.0  # 完成度 (0~1)
        
        # 时间信息
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        self.last_activated = None
        
        # 状态信息
        self.is_active = False
        self.is_completed = False
        self.completion_reason = None
        
        # 统计信息
        self.activation_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_reasoning_time = 0.0  # 总推理时间（秒）
        
        # 相关上下文
        self.related_nodes: List[str] = []  # 相关节点ID
        self.related_patterns: List[str] = []  # 相关模式ID
        self.key_insights: List[str] = []  # 关键洞察
        
        # 元数据
        self.metadata: Dict[str, Any] = {
            "source": "query_generated",
            "complexity": 0.5,
            "estimated_effort": 1.0,  # 估计努力程度
            "dependencies": [],  # 依赖的其他目标
            "subgoals": []  # 子目标
        }
    
    def update_progress(self, progress_delta: float, reason: str = None):
        """更新进度"""
        old_progress = self.progress
        self.progress = max(0.0, min(1.0, self.progress + progress_delta))
        self.last_updated = datetime.now()
        
        # 检查是否完成
        if self.progress >= 0.95 and not self.is_completed:
            self.is_completed = True
            self.completion_reason = reason or "progress_threshold_reached"
        
        return {
            "old_progress": old_progress,
            "new_progress": self.progress,
            "delta": progress_delta,
            "reason": reason
        }
    
    def update_confidence(self, success: bool, learning_rate: float = 0.05):
        """更新置信度"""
        old_confidence = self.confidence
        
        if success:
            self.confidence = min(1.0, self.confidence + learning_rate)
            self.success_count += 1
        else:
            self.confidence = max(0.1, self.confidence - learning_rate)
            self.failure_count += 1
        
        self.last_updated = datetime.now()
        
        return {
            "old_confidence": old_confidence,
            "new_confidence": self.confidence,
            "success": success,
            "learning_rate": learning_rate
        }
    
    def activate(self):
        """激活目标"""
        self.is_active = True
        self.last_activated = datetime.now()
        self.activation_count += 1
        
        return {
            "activated": True,
            "activation_count": self.activation_count,
            "timestamp": self.last_activated.isoformat()
        }
    
    def deactivate(self):
        """停用目标"""
        self.is_active = False
        
        return {
            "deactivated": True,
            "was_active_for": self._get_active_duration()
        }
    
    def add_related_node(self, node_id: str, relevance: float = 0.5):
        """添加相关节点"""
        if node_id not in self.related_nodes:
            self.related_nodes.append(node_id)
            
            # 更新元数据
            if "node_relevance" not in self.metadata:
                self.metadata["node_relevance"] = {}
            self.metadata["node_relevance"][node_id] = relevance
            
            return True
        return False
    
    def add_key_insight(self, insight: str, importance: float = 0.5):
        """添加关键洞察"""
        insight_entry = {
            "text": insight,
            "importance": importance,
            "timestamp": datetime.now().isoformat()
        }
        
        self.key_insights.append(insight_entry)
        
        # 限制洞察数量
        if len(self.key_insights) > 20:
            self.key_insights = self.key_insights[-20:]
        
        return True
    
    def get_goal_score(self) -> float:
        """获取目标综合评分"""
        # 基础评分 = 重要性 * 置信度
        base_score = self.priority * self.confidence
        
        # 进度奖励（接近完成的目标得分更高）
        progress_bonus = self.progress * 0.3
        
        # 新鲜度惩罚（太久没更新的目标得分降低）
        recency_penalty = self._get_recency_penalty()
        
        # 综合评分
        score = (base_score + progress_bonus) * (1.0 - recency_penalty)
        
        return max(0.0, min(1.0, score))
    
    def _get_recency_penalty(self) -> float:
        """获取新鲜度惩罚"""
        now = datetime.now()
        hours_since_update = (now - self.last_updated).total_seconds() / 3600
        
        # 24小时后开始有惩罚，72小时达到最大惩罚0.3
        if hours_since_update <= 24:
            return 0.0
        elif hours_since_update >= 72:
            return 0.3
        else:
            return 0.3 * ((hours_since_update - 24) / 48)
    
    def _get_active_duration(self) -> float:
        """获取激活持续时间（秒）"""
        if not self.last_activated:
            return 0.0
        
        if self.is_active:
            end_time = datetime.now()
        else:
            # 如果已经停用，需要记录停用时间（这里简化处理）
            end_time = self.last_updated
        
        return (end_time - self.last_activated).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "description": self.description,
            "goal_type": self.goal_type,
            
            # 核心属性
            "priority": self.priority,
            "confidence": self.confidence,
            "progress": self.progress,
            
            # 时间信息
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "last_activated": self.last_activated.isoformat() if self.last_activated else None,
            
            # 状态信息
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "completion_reason": self.completion_reason,
            
            # 统计信息
            "activation_count": self.activation_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_reasoning_time": self.total_reasoning_time,
            "goal_score": self.get_goal_score(),
            
            # 相关上下文
            "related_nodes_count": len(self.related_nodes),
            "related_patterns_count": len(self.related_patterns),
            "key_insights_count": len(self.key_insights),
            
            # 元数据
            "metadata": self.metadata
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要信息"""
        return {
            "id": self.id,
            "description": self.description[:50] + "..." if len(self.description) > 50 else self.description,
            "priority": self.priority,
            "confidence": self.confidence,
            "progress": self.progress,
            "is_active": self.is_active,
            "is_completed": self.is_completed,
            "goal_score": self.get_goal_score(),
            "activation_count": self.activation_count,
            "success_rate": self.success_count / max(1, self.success_count + self.failure_count)
        }
    
    def print_status(self):
        """打印状态"""
        summary = self.get_summary()
        
        print(f"   🎯 目标: {summary['description']}")
        print(f"      ID: {summary['id']}")
        print(f"      重要性: {summary['priority']:.2f}")
        print(f"      置信度: {summary['confidence']:.2f}")
        print(f"      完成度: {summary['progress']:.1%}")
        print(f"      目标评分: {summary['goal_score']:.3f}")
        print(f"      状态: {'活跃' if summary['is_active'] else '非活跃'} | "
              f"{'已完成' if summary['is_completed'] else '进行中'}")
        print(f"      激活次数: {summary['activation_count']}")
        print(f"      成功率: {summary['success_rate']:.1%}")
        
        if self.related_nodes:
            print(f"      相关节点: {len(self.related_nodes)}个")
        
        if self.key_insights:
            print(f"      关键洞察: {len(self.key_insights)}个")