#!/usr/bin/env python3
"""
Attention State（注意力状态）
核心数据结构：存储注意力分数和历史记录
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

@dataclass
class AttentionState:
    """注意力状态"""
    
    def __init__(self):
        self.node_scores: Dict[str, float] = {}  # node_id -> score
        self.edge_scores: Dict[str, float] = {}  # edge_id -> score
        self.history: List[Dict[str, Any]] = []  # 注意力历史记录
        self.total_queries: int = 0
        self.total_nodes_scored: int = 0
        self.avg_attention_score: float = 0.0
        self.last_update: datetime = datetime.now()
        
        # 统计信息
        self.stats = {
            "total_attention_calls": 0,
            "avg_nodes_per_query": 0.0,
            "avg_attention_score": 0.0,
            "attention_coverage_history": [],  # 注意力覆盖率历史
            "top_node_history": []  # 最高分节点历史
        }
    
    def update_node_score(self, node_id: str, score: float):
        """更新节点分数"""
        self.node_scores[node_id] = score
        self.total_nodes_scored += 1
        self.last_update = datetime.now()
        
        # 更新平均分数
        total_score = sum(self.node_scores.values())
        self.avg_attention_score = total_score / len(self.node_scores) if self.node_scores else 0.0
    
    def update_edge_score(self, edge_id: str, score: float):
        """更新边分数"""
        self.edge_scores[edge_id] = score
        self.last_update = datetime.now()
    
    def record_history(self, query: str, selected_nodes: List[str], 
                      total_nodes: int, avg_score: float):
        """记录注意力历史"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "selected_nodes": selected_nodes,
            "selected_count": len(selected_nodes),
            "total_nodes": total_nodes,
            "attention_coverage": len(selected_nodes) / total_nodes if total_nodes > 0 else 0.0,
            "avg_score": avg_score,
            "top_node": selected_nodes[0] if selected_nodes else None,
            "top_score": self.node_scores.get(selected_nodes[0], 0.0) if selected_nodes else 0.0
        }
        
        self.history.append(history_entry)
        self.total_queries += 1
        
        # 更新统计
        self.stats["total_attention_calls"] += 1
        self.stats["avg_nodes_per_query"] = (
            (self.stats["avg_nodes_per_query"] * (self.total_queries - 1) + len(selected_nodes)) 
            / self.total_queries
        )
        self.stats["avg_attention_score"] = (
            (self.stats["avg_attention_score"] * (self.total_queries - 1) + avg_score)
            / self.total_queries
        )
        self.stats["attention_coverage_history"].append(history_entry["attention_coverage"])
        
        if selected_nodes:
            self.stats["top_node_history"].append({
                "node_id": selected_nodes[0],
                "score": self.node_scores.get(selected_nodes[0], 0.0),
                "timestamp": datetime.now().isoformat()
            })
        
        # 限制历史长度
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
        if len(self.stats["attention_coverage_history"]) > 100:
            self.stats["attention_coverage_history"] = self.stats["attention_coverage_history"][-100:]
        if len(self.stats["top_node_history"]) > 100:
            self.stats["top_node_history"] = self.stats["top_node_history"][-100:]
    
    def get_node_score(self, node_id: str) -> float:
        """获取节点分数"""
        return self.node_scores.get(node_id, 0.0)
    
    def get_edge_score(self, edge_id: str) -> float:
        """获取边分数"""
        return self.edge_scores.get(edge_id, 0.0)
    
    def get_top_nodes(self, k: int = 10) -> List[tuple]:
        """获取Top-K节点"""
        sorted_nodes = sorted(self.node_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:k]
    
    def get_top_edges(self, k: int = 10) -> List[tuple]:
        """获取Top-K边"""
        sorted_edges = sorted(self.edge_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_edges[:k]
    
    def get_attention_coverage(self, total_nodes: int) -> float:
        """获取注意力覆盖率"""
        if total_nodes == 0:
            return 0.0
        
        # 最近10次查询的平均覆盖率
        recent_history = self.history[-10:] if len(self.history) >= 10 else self.history
        if not recent_history:
            return 0.0
        
        total_coverage = sum(entry["attention_coverage"] for entry in recent_history)
        return total_coverage / len(recent_history)
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        return {
            "state": {
                "total_nodes_scored": len(self.node_scores),
                "total_edges_scored": len(self.edge_scores),
                "total_queries": self.total_queries,
                "avg_attention_score": self.avg_attention_score,
                "last_update": self.last_update.isoformat()
            },
            "stats": self.stats,
            "top_nodes": self.get_top_nodes(5),
            "top_edges": self.get_top_edges(5),
            "recent_history": self.history[-5:] if self.history else []
        }
    
    def clear_expired_scores(self, max_age_hours: int = 24):
        """清理过期分数"""
        current_time = time.time()
        expired_count = 0
        
        # 清理节点分数（简化：基于历史记录判断）
        if len(self.history) > 100:
            # 保留最近100次查询的相关节点
            recent_nodes = set()
            for entry in self.history[-100:]:
                recent_nodes.update(entry.get("selected_nodes", []))
            
            # 清理不在最近查询中的节点
            nodes_to_remove = [node_id for node_id in self.node_scores.keys() 
                              if node_id not in recent_nodes]
            for node_id in nodes_to_remove:
                del self.node_scores[node_id]
                expired_count += 1
        
        # 清理边分数（简化：基于节点清理）
        edges_to_remove = [edge_id for edge_id in self.edge_scores.keys() 
                          if not any(node_id in edge_id for node_id in self.node_scores.keys())]
        for edge_id in edges_to_remove:
            del self.edge_scores[edge_id]
            expired_count += 1
        
        return expired_count
    
    def print_status(self):
        """打印状态"""
        report = self.get_system_report()
        state = report["state"]
        stats = report["stats"]
        
        print(f"   📊 Attention State状态:")
        print(f"      总节点数: {state['total_nodes_scored']}")
        print(f"      总边数: {state['total_edges_scored']}")
        print(f"      总查询数: {state['total_queries']}")
        print(f"      平均注意力分数: {state['avg_attention_score']:.3f}")
        print(f"      平均节点数/查询: {stats['avg_nodes_per_query']:.1f}")
        print(f"      平均注意力覆盖率: {self.get_attention_coverage(state['total_nodes_scored']):.1%}")
        
        if report["top_nodes"]:
            print(f"      Top节点:")
            for node_id, score in report["top_nodes"][:3]:
                print(f"        {node_id}: {score:.3f}")