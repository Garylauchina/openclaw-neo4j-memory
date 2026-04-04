#!/usr/bin/env python3
"""
Attention Feedback（注意力反馈机制）
核心模块：让系统"学会关注"
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
import time
from datetime import datetime, timedelta

@dataclass
class FeedbackConfig:
    """反馈配置"""
    learning_rate: float = 0.05  # 学习率
    decay_rate: float = 0.01  # 衰减率（防止分数无限增长）
    min_score: float = 0.1  # 最低分数
    max_score: float = 1.0  # 最高分数
    feedback_window: int = 10  # 反馈窗口大小
    success_threshold: float = 0.7  # 成功阈值
    
    def validate(self):
        """验证配置"""
        if not 0.0 < self.learning_rate <= 0.1:
            raise ValueError(f"learning_rate必须在0~0.1之间，当前为{self.learning_rate}")
        
        if not 0.0 <= self.decay_rate <= 0.1:
            raise ValueError(f"decay_rate必须在0~0.1之间，当前为{self.decay_rate}")
        
        if not 0.0 <= self.min_score < self.max_score <= 1.0:
            raise ValueError(f"分数范围无效: min={self.min_score}, max={self.max_score}")
        
        if self.feedback_window <= 0:
            raise ValueError(f"feedback_window必须大于0，当前为{self.feedback_window}")
        
        if not 0.0 <= self.success_threshold <= 1.0:
            raise ValueError(f"success_threshold必须在0~1之间，当前为{self.success_threshold}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "learning_rate": self.learning_rate,
            "decay_rate": self.decay_rate,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "feedback_window": self.feedback_window,
            "success_threshold": self.success_threshold
        }

class AttentionFeedback:
    """注意力反馈机制"""
    
    def __init__(self, config: Optional[FeedbackConfig] = None):
        self.config = config or FeedbackConfig()
        self.config.validate()
        
        # 节点反馈历史
        self.node_feedback: Dict[str, List[Dict[str, Any]]] = {}  # node_id -> 反馈历史
        self.node_scores: Dict[str, float] = {}  # node_id -> 当前分数
        
        # 统计信息
        self.stats = {
            "total_feedbacks": 0,
            "successful_feedbacks": 0,
            "failed_feedbacks": 0,
            "score_updates": 0,
            "decay_applications": 0,
            "avg_score_change": 0.0
        }
    
    def update_attention(self, node_id: str, success: bool, 
                        metadata: Optional[Dict[str, Any]] = None) -> float:
        """
        更新注意力分数
        
        Args:
            node_id: 节点ID
            success: 推理是否成功
            metadata: 额外元数据
        
        Returns:
            float: 更新后的分数
        """
        # 获取当前分数
        current_score = self.node_scores.get(node_id, 0.5)
        
        # 计算更新量
        if success:
            update_amount = self.config.learning_rate
            self.stats["successful_feedbacks"] += 1
        else:
            update_amount = -self.config.learning_rate
            self.stats["failed_feedbacks"] += 1
        
        # 应用更新
        new_score = current_score + update_amount
        
        # 应用范围限制
        new_score = max(self.config.min_score, min(self.config.max_score, new_score))
        
        # 应用衰减（防止分数无限增长）
        if new_score > 0.8:
            decay = self.config.decay_rate * (new_score - 0.8) / 0.2
            new_score = new_score * (1.0 - decay)
            self.stats["decay_applications"] += 1
        
        # 更新分数
        self.node_scores[node_id] = new_score
        
        # 记录反馈历史
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "old_score": current_score,
            "new_score": new_score,
            "change": new_score - current_score,
            "metadata": metadata or {}
        }
        
        if node_id not in self.node_feedback:
            self.node_feedback[node_id] = []
        
        self.node_feedback[node_id].append(feedback_entry)
        
        # 限制历史长度
        if len(self.node_feedback[node_id]) > self.config.feedback_window:
            self.node_feedback[node_id] = self.node_feedback[node_id][-self.config.feedback_window:]
        
        # 更新统计
        self.stats["total_feedbacks"] += 1
        self.stats["score_updates"] += 1
        self.stats["avg_score_change"] = (
            (self.stats["avg_score_change"] * (self.stats["score_updates"] - 1) + abs(new_score - current_score))
            / self.stats["score_updates"]
        )
        
        return new_score
    
    def batch_update(self, node_success_pairs: List[tuple], 
                    metadata: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """
        批量更新注意力分数
        
        Args:
            node_success_pairs: [(node_id, success)] 节点成功对列表
            metadata: 额外元数据
        
        Returns:
            Dict[str, float]: 更新后的分数映射
        """
        updated_scores = {}
        
        for node_id, success in node_success_pairs:
            new_score = self.update_attention(node_id, success, metadata)
            updated_scores[node_id] = new_score
        
        return updated_scores
    
    def get_node_success_rate(self, node_id: str, window: Optional[int] = None) -> float:
        """获取节点成功率"""
        if node_id not in self.node_feedback or not self.node_feedback[node_id]:
            return 0.5  # 默认中等成功率
        
        feedback_history = self.node_feedback[node_id]
        if window is not None and window > 0:
            feedback_history = feedback_history[-window:]
        
        if not feedback_history:
            return 0.5
        
        success_count = sum(1 for entry in feedback_history if entry["success"])
        total_count = len(feedback_history)
        
        return success_count / total_count
    
    def get_node_confidence(self, node_id: str) -> float:
        """获取节点置信度（基于历史稳定性）"""
        if node_id not in self.node_feedback or len(self.node_feedback[node_id]) < 3:
            return 0.3  # 低置信度（数据不足）
        
        feedback_history = self.node_feedback[node_id]
        
        # 计算成功率稳定性
        success_rates = []
        window_size = min(5, len(feedback_history))
        
        for i in range(0, len(feedback_history) - window_size + 1):
            window = feedback_history[i:i + window_size]
            success_rate = sum(1 for entry in window if entry["success"]) / window_size
            success_rates.append(success_rate)
        
        if not success_rates:
            return 0.3
        
        # 稳定性 = 1 - 标准差
        import statistics
        if len(success_rates) >= 2:
            stdev = statistics.stdev(success_rates)
            stability = 1.0 - min(1.0, stdev * 2)  # 标准化到0~1
        else:
            stability = 0.5
        
        # 置信度 = 稳定性 * 数据量因子
        data_factor = min(1.0, len(feedback_history) / 10.0)  # 10次反馈达到最大
        confidence = stability * data_factor
        
        return max(0.1, min(1.0, confidence))
    
    def get_recommended_attention_score(self, node_id: str, 
                                      base_score: float) -> float:
        """获取推荐的注意力分数（结合反馈）"""
        if node_id not in self.node_scores:
            return base_score
        
        feedback_score = self.node_scores[node_id]
        confidence = self.get_node_confidence(node_id)
        
        # 混合基础分数和反馈分数
        # 置信度高时更多依赖反馈，置信度低时更多依赖基础分数
        mixed_score = (confidence * feedback_score + (1 - confidence) * base_score)
        
        return max(self.config.min_score, min(self.config.max_score, mixed_score))
    
    def clear_expired_feedback(self, max_age_hours: int = 24):
        """清理过期反馈"""
        current_time = datetime.now()
        expired_count = 0
        
        for node_id in list(self.node_feedback.keys()):
            # 过滤过期条目
            valid_feedback = []
            for entry in self.node_feedback[node_id]:
                try:
                    timestamp = datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
                    age_hours = (current_time - timestamp).total_seconds() / 3600
                    
                    if age_hours <= max_age_hours:
                        valid_feedback.append(entry)
                    else:
                        expired_count += 1
                except:
                    # 无效时间戳，保留
                    valid_feedback.append(entry)
            
            if valid_feedback:
                self.node_feedback[node_id] = valid_feedback
            else:
                # 没有有效反馈，删除节点记录
                del self.node_feedback[node_id]
                if node_id in self.node_scores:
                    del self.node_scores[node_id]
        
        return expired_count
    
    def get_feedback_summary(self, node_id: str) -> Dict[str, Any]:
        """获取反馈摘要"""
        if node_id not in self.node_feedback:
            return {
                "has_feedback": False,
                "current_score": self.node_scores.get(node_id, 0.5),
                "message": "无反馈历史"
            }
        
        feedback_history = self.node_feedback[node_id]
        current_score = self.node_scores.get(node_id, 0.5)
        
        # 计算统计
        total_feedbacks = len(feedback_history)
        success_count = sum(1 for entry in feedback_history if entry["success"])
        success_rate = success_count / total_feedbacks if total_feedbacks > 0 else 0.0
        
        # 计算趋势
        if len(feedback_history) >= 2:
            recent_success = sum(1 for entry in feedback_history[-5:] if entry["success"])
            recent_total = min(5, len(feedback_history))
            recent_rate = recent_success / recent_total if recent_total > 0 else 0.0
            
            trend = "上升" if recent_rate > success_rate else "下降" if recent_rate < success_rate else "稳定"
        else:
            trend = "未知"
        
        return {
            "has_feedback": True,
            "current_score": current_score,
            "total_feedbacks": total_feedbacks,
            "success_rate": success_rate,
            "success_count": success_count,
            "failure_count": total_feedbacks - success_count,
            "trend": trend,
            "confidence": self.get_node_confidence(node_id),
            "recent_feedback": feedback_history[-3:] if feedback_history else []
        }
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        total_nodes = len(self.node_scores)
        avg_score = sum(self.node_scores.values()) / total_nodes if total_nodes > 0 else 0.0
        
        # 计算分数分布
        score_distribution = {
            "excellent": sum(1 for score in self.node_scores.values() if score > 0.8),
            "good": sum(1 for score in self.node_scores.values() if 0.6 < score <= 0.8),
            "fair": sum(1 for score in self.node_scores.values() if 0.4 < score <= 0.6),
            "poor": sum(1 for score in self.node_scores.values() if 0.2 < score <= 0.4),
            "very_poor": sum(1 for score in self.node_scores.values() if score <= 0.2)
        }
        
        return {
            "config": self.config.to_dict(),
            "state": {
                "total_nodes_with_feedback": total_nodes,
                "avg_feedback_score": avg_score,
                "score_distribution": score_distribution,
                "total_feedback_entries": sum(len(fb) for fb in self.node_feedback.values())
            },
            "stats": self.stats,
            "top_nodes": self._get_top_nodes(5)
        }
    
    def _get_top_nodes(self, k: int) -> List[Dict[str, Any]]:
        """获取Top-K节点"""
        sorted_nodes = sorted(self.node_scores.items(), key=lambda x: x[1], reverse=True)
        top_nodes = []
        
        for node_id, score in sorted_nodes[:k]:
            summary = self.get_feedback_summary(node_id)
            top_nodes.append({
                "node_id": node_id,
                "score": score,
                "success_rate": summary.get("success_rate", 0.0),
                "confidence": summary.get("confidence", 0.0),
                "total_feedbacks": summary.get("total_feedbacks", 0)
            })
        
        return top_nodes
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_feedbacks": 0,
            "successful_feedbacks": 0,
            "failed_feedbacks": 0,
            "score_updates": 0,
            "decay_applications": 0,
            "avg_score_change": 0.0
        }
    
    def print_status(self):
        """打印状态"""
        report = self.get_system_report()
        config = report["config"]
        state = report["state"]
        stats = report["stats"]
        dist = state["score_distribution"]
        
        print(f"   📊 Attention Feedback状态:")
        print(f"      配置:")
        print(f"        学习率: {config['learning_rate']:.3f}")
        print(f"        衰减率: {config['decay_rate']:.3f}")
        print(f"        分数范围: [{config['min_score']:.2f}, {config['max_score']:.2f}]")
        print(f"        反馈窗口: {config['feedback_window']}")
        print(f"        成功阈值: {config['success_threshold']:.2f}")
        
        print(f"      状态:")
        print(f"        有反馈节点数: {state['total_nodes_with_feedback']}")
        print(f"        平均反馈分数: {state['avg_feedback_score']:.3f}")
        print(f"        总反馈条目: {state['total_feedback_entries']}")
        
        print(f"      分数分布:")
        print(f"        优秀 (>0.8): {dist['excellent']}")
        print(f"        良好 (0.6~0.8): {dist['good']}")
        print(f"        一般 (0.4~0.6): {dist['fair']}")
        print(f"        差 (0.2~0.4): {dist['poor']}")
        print(f"        极差 (≤0.2): {dist['very_poor']}")
        
        print(f"      统计:")
        print(f"        总反馈次数: {stats['total_feedbacks']}")
        print(f"        成功反馈: {stats['successful_feedbacks']}")
        print(f"        失败反馈: {stats['failed_feedbacks']}")
        print(f"        成功率: {stats['successful_feedbacks']/stats['total_feedbacks']:.1%}" 
              f" (总反馈>0)" if stats['total_feedbacks'] > 0 else " (无反馈)")
        print(f"        平均分数变化: {stats['avg_score_change']:.3f}")