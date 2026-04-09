#!/usr/bin/env python3
"""
全局图（Global Graph）实现
基于用户提供的完整规范实现

核心设计原则：
1. 表达长期认知，支持子图构建，支持冥思更新，不参与实时推理
2. 节点类型、关系类型严格枚举
3. 基于数学公式的确定性merge规则
4. 通过结构化diff和确定性merge规则持续演化
"""

import json
import time
import math
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from datetime import datetime

# ========== 枚举定义（严格限制） ==========

class NodeType(Enum):
    """节点类型枚举 - 严格限制"""
    USER = "USER"
    ENTITY = "ENTITY"      # 人/物/概念
    EVENT = "EVENT"        # 事件
    TASK = "TASK"          # 任务
    TOPIC = "TOPIC"        # 话题

class EdgeType(Enum):
    """关系类型枚举 - 第一版不超过20个"""
    INTERESTED_IN = "INTERESTED_IN"
    LIKES = "LIKES"
    DISLIKES = "DISLIKES"
    OWNS = "OWNS"
    INVESTED_IN = "INVESTED_IN"
    RELATED_TO = "RELATED_TO"
    CAUSES = "CAUSES"
    PART_OF = "PART_OF"
    LOCATED_IN = "LOCATED_IN"
    WORKS_ON = "WORKS_ON"
    DECIDES = "DECIDES"
    PREFERS = "PREFERS"
    CONSIDERING = "CONSIDERING"
    REJECTED = "REJECTED"
    LOVES = "LOVES"
    HATES = "HATES"
    WANTS = "WANTS"
    NEEDS = "NEEDS"
    LEARNING = "LEARNING"
    RESEARCHING = "RESEARCHING"
    FOLLOWING = "FOLLOWING"
    SUPPORTING = "SUPPORTING"
    OPPOSING = "OPPOSING"
    ASKING_ABOUT = "ASKING_ABOUT"
    IS_A = "IS_A"
    MENTIONED = "MENTIONED"
    AGREES_WITH = "AGREES_WITH"
    DISAGREES_WITH = "DISAGREES_WITH"

class DiffOp(Enum):
    """Diff操作类型"""
    UPDATE_EDGE = "UPDATE_EDGE"
    MERGE_NODE = "MERGE_NODE"
    CREATE_NODE = "CREATE_NODE"
    DEACTIVATE_EDGE = "DEACTIVATE_EDGE"

# ========== 数据结构定义 ==========

@dataclass
class StateVector:
    """状态向量 - 标准结构（必须统一）"""
    weight: float = 0.0          # 强度 [-1, 1]
    confidence: float = 0.0      # 置信度 [0, 1]
    evidence_count: int = 0      # 证据次数
    last_updated: int = 0        # 时间戳
    decay_factor: float = 1.0    # 衰减因子
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)

@dataclass
class Node:
    """节点 - 最小结构"""
    id: str
    type: NodeType
    name: str
    aliases: List[str] = None
    created_at: int = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.created_at is None:
            self.created_at = int(time.time())
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type.value,
            "name": self.name,
            "aliases": self.aliases,
            "created_at": self.created_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            id=data["id"],
            type=NodeType(data["type"]),
            name=data["name"],
            aliases=data.get("aliases", []),
            created_at=data.get("created_at", int(time.time())),
            metadata=data.get("metadata", {})
        )

@dataclass
class Edge:
    """边 - 最小结构（必须用这个级别）"""
    src: str
    dst: str
    type: EdgeType
    state: StateVector
    active: bool = True
    
    def to_dict(self):
        return {
            "src": self.src,
            "dst": self.dst,
            "type": self.type.value,
            "state": self.state.to_dict(),
            "active": self.active
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            src=data["src"],
            dst=data["dst"],
            type=EdgeType(data["type"]),
            state=StateVector.from_dict(data["state"]),
            active=data.get("active", True)
        )
    
    @property
    def key(self) -> str:
        """边的唯一标识"""
        return f"{self.src}::{self.dst}::{self.type.value}"

@dataclass
class Diff:
    """Diff（更新指令）规范"""
    op: DiffOp
    src: Optional[str] = None
    dst: Optional[str] = None
    type: Optional[EdgeType] = None
    delta: Optional[float] = None          # 权重变化量
    confidence: Optional[float] = None     # 输入置信度
    node_a: Optional[str] = None          # 用于节点合并
    node_b: Optional[str] = None          # 用于节点合并
    name: Optional[str] = None            # 用于创建节点
    node_type: Optional[NodeType] = None  # 用于创建节点
    timestamp: int = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = int(time.time())
    
    def to_dict(self):
        result = {
            "op": self.op.value,
            "timestamp": self.timestamp
        }
        
        if self.src: result["src"] = self.src
        if self.dst: result["dst"] = self.dst
        if self.type: result["type"] = self.type.value
        if self.delta is not None: result["delta"] = self.delta
        if self.confidence is not None: result["confidence"] = self.confidence
        if self.node_a: result["node_a"] = self.node_a
        if self.node_b: result["node_b"] = self.node_b
        if self.name: result["name"] = self.name
        if self.node_type: result["node_type"] = self.node_type.value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(
            op=DiffOp(data["op"]),
            src=data.get("src"),
            dst=data.get("dst"),
            type=EdgeType(data["type"]) if data.get("type") else None,
            delta=data.get("delta"),
            confidence=data.get("confidence"),
            node_a=data.get("node_a"),
            node_b=data.get("node_b"),
            name=data.get("name"),
            node_type=NodeType(data["node_type"]) if data.get("node_type") else None,
            timestamp=data.get("timestamp", int(time.time()))
        )

# ========== 全局图核心实现 ==========

class GlobalGraph:
    """
    全局图实现类
    
    核心定义：
    全局图是一个带状态向量的关系网络，通过结构化diff和确定性merge规则持续演化。
    """
    
    def __init__(self, alpha: float = 0.8, lambda_decay: float = 0.01):
        """
        初始化全局图
        
        Args:
            alpha: merge公式中的α参数（默认0.8）
            lambda_decay: 时间衰减的λ参数（默认0.01）
        """
        self.alpha = alpha
        self.lambda_decay = lambda_decay
        
        # 核心数据结构
        self.nodes: Dict[str, Node] = {}      # 节点ID -> Node对象
        self.edges: Dict[str, Edge] = {}      # 边key -> Edge对象
        self.node_edges: Dict[str, Set[str]] = {}  # 节点ID -> 边key集合
        
        # 统计信息
        self.stats = {
            "total_nodes": 0,
            "total_edges": 0,
            "active_edges": 0,
            "last_updated": int(time.time()),
            "diff_count": 0
        }
        
        # 配置参数
        self.config = {
            "max_edges_per_node": 50,     # 每节点最大边数
            "min_weight_threshold": 0.05, # 最小权重过滤
            "merge_confidence_threshold": 0.7,  # 节点合并置信度阈值
            "decay_enabled": True,        # 是否启用时间衰减
            "conflict_penalty": 0.1       # 冲突惩罚
        }
    
    # ========== MVP 四个核心函数 ==========
    
    def create_node(self, name: str, node_type: NodeType) -> str:
        """
        创建节点
        
        Args:
            name: 节点名称
            node_type: 节点类型
            
        Returns:
            节点ID
        """
        # 生成唯一ID
        node_id = f"node_{uuid.uuid4().hex[:8]}"
        
        # 创建节点
        node = Node(
            id=node_id,
            type=node_type,
            name=name,
            created_at=int(time.time())
        )
        
        # 保存节点
        self.nodes[node_id] = node
        self.node_edges[node_id] = set()
        self.stats["total_nodes"] += 1
        
        return node_id
    
    def update_edge(self, src: str, dst: str, edge_type: EdgeType, delta: float) -> bool:
        """
        更新关系
        
        Args:
            src: 源节点ID
            dst: 目标节点ID
            edge_type: 关系类型
            delta: 权重变化量
            
        Returns:
            是否成功
        """
        # 创建diff
        diff = Diff(
            op=DiffOp.UPDATE_EDGE,
            src=src,
            dst=dst,
            type=edge_type,
            delta=delta,
            confidence=0.9  # 默认置信度
        )
        
        # 应用diff
        return self.apply_diff(diff)
    
    def merge_node(self, node_a: str, node_b: str, confidence: float = 0.8) -> bool:
        """
        合并节点
        
        Args:
            node_a: 节点A ID
            node_b: 节点B ID
            confidence: 合并置信度
            
        Returns:
            是否成功
        """
        # 检查置信度阈值
        if confidence < self.config["merge_confidence_threshold"]:
            print(f"合并置信度 {confidence} 低于阈值 {self.config['merge_confidence_threshold']}")
            return False
        
        # 创建diff
        diff = Diff(
            op=DiffOp.MERGE_NODE,
            node_a=node_a,
            node_b=node_b,
            confidence=confidence
        )
        
        # 应用diff
        return self.apply_diff(diff)
    
    def apply_diff(self, diff: Diff) -> bool:
        """
        应用diff - 统一入口（必须）
        
        Args:
            diff: 更新指令
            
        Returns:
            是否成功
        """
        try:
            if diff.op == DiffOp.CREATE_NODE:
                self._apply_create_node(diff)
            elif diff.op == DiffOp.UPDATE_EDGE:
                self._apply_update_edge(diff)
            elif diff.op == DiffOp.MERGE_NODE:
                self._apply_merge_node(diff)
            elif diff.op == DiffOp.DEACTIVATE_EDGE:
                self._apply_deactivate_edge(diff)
            else:
                print(f"未知的diff操作: {diff.op}")
                return False
            
            # 更新统计信息
            self.stats["diff_count"] += 1
            self.stats["last_updated"] = int(time.time())
            
            return True
            
        except Exception as e:
            print(f"应用diff失败: {e}")
            return False
    
    # ========== Diff应用的具体实现 ==========
    
    def _apply_create_node(self, diff: Diff):
        """应用创建节点diff"""
        node_id = self.create_node(diff.name, diff.node_type)
        print(f"创建节点: {diff.name} ({diff.node_type.value}) -> ID: {node_id}")
    
    def _apply_update_edge(self, diff: Diff):
        """应用更新边diff - 核心merge逻辑"""
        src = diff.src
        dst = diff.dst
        edge_type = diff.type
        delta = diff.delta
        input_conf = diff.confidence or 0.9
        
        # 检查节点是否存在
        if src not in self.nodes:
            print(f"源节点不存在: {src}")
            return
        if dst not in self.nodes:
            print(f"目标节点不存在: {dst}")
            return
        
        # 检查边数量限制
        if len(self.node_edges[src]) >= self.config["max_edges_per_node"]:
            print(f"源节点 {src} 边数已达上限 {self.config['max_edges_per_node']}")
            return
        
        edge_key = f"{src}::{dst}::{edge_type.value}"
        
        # 1. 新边
        if edge_key not in self.edges:
            print(f"创建新边: {src} -> {dst} ({edge_type.value})")
            
            # 创建新边
            state = StateVector(
                weight=delta,
                confidence=input_conf,
                evidence_count=1,
                last_updated=diff.timestamp,
                decay_factor=1.0
            )
            
            edge = Edge(
                src=src,
                dst=dst,
                type=edge_type,
                state=state
            )
            
            # 保存边
            self.edges[edge_key] = edge
            self.node_edges[src].add(edge_key)
            self.stats["total_edges"] += 1
            self.stats["active_edges"] += 1
            
        # 2. 已存在边 - 核心merge公式
        else:
            print(f"更新已存在边: {src} -> {dst} ({edge_type.value})")
            
            edge = self.edges[edge_key]
            old_state = edge.state
            
            # 应用时间衰减
            if self.config["decay_enabled"]:
                time_diff = (diff.timestamp - old_state.last_updated) / 3600.0  # 小时
                decay = math.exp(-self.lambda_decay * time_diff)
                old_weight = old_state.weight * decay
            else:
                old_weight = old_state.weight
            
            # Merge公式: new_weight = α * old_weight + (1 - α) * delta
            new_weight = self.alpha * old_weight + (1 - self.alpha) * delta
            
            # 限制权重范围 [-1, 1]
            new_weight = max(-1.0, min(1.0, new_weight))
            
            # 更新置信度: new_conf = max(old_conf, input_conf)
            new_conf = max(old_state.confidence, input_conf)
            
            # 更新证据计数
            new_evidence = old_state.evidence_count + 1
            
            # 更新状态
            edge.state.weight = new_weight
            edge.state.confidence = new_conf
            edge.state.evidence_count = new_evidence
            edge.state.last_updated = diff.timestamp
            
            # 检查是否低于阈值
            if abs(new_weight) < self.config["min_weight_threshold"]:
                edge.active = False
                self.stats["active_edges"] -= 1
                print(f"边权重 {new_weight:.3f} 低于阈值，标记为inactive")
    
    def _apply_merge_node(self, diff: Diff):
        """应用合并节点diff"""
        node_a_id = diff.node_a
        node_b_id = diff.node_b
        
        # 检查节点是否存在
        if node_a_id not in self.nodes:
            print(f"节点A不存在: {node_a_id}")
            return
        if node_b_id not in self.nodes:
            print(f"节点B不存在: {node_b_id}")
            return
        
        node_a = self.nodes[node_a_id]
        node_b = self.nodes[node_b_id]
        
        print(f"合并节点: {node_a.name} ({node_a_id}) + {node_b.name} ({node_b_id})")
        
        # 合并策略：保留node_a，将node_b的边转移到node_a
        edges_to_update = []
        
        # 收集node_b的所有边
        for edge_key in list(self.node_edges.get(node_b_id, [])):
            edge = self.edges.get(edge_key)
            if edge:
                # 确定新的源/目标节点
                if edge.src == node_b_id:
                    new_src = node_a_id
                    new_dst = edge.dst
                else:
                    new_src = edge.src
                    new_dst = node_a_id
                
                # 创建新的边key
                new_edge_key = f"{new_src}::{new_dst}::{edge.type.value}"
                
                # 检查是否已存在相同类型的边
                if new_edge_key in self.edges:
                    # 合并边的权重
                    existing_edge = self.edges[new_edge_key]
                    existing_edge.state.weight = (existing_edge.state.weight + edge.state.weight) / 2
                    existing_edge.state.confidence = max(existing_edge.state.confidence, edge.state.confidence)
                    existing_edge.state.evidence_count += edge.state.evidence_count
                    
                    # 删除旧边
                    del self.edges[edge_key]
                    self.stats["total_edges"] -= 1
                    if edge.active:
                        self.stats["active_edges"] -= 1
                else:
                    # 更新边
                    edge.src = new_src
                    edge.dst = new_dst
                    
                    # 更新数据结构
                    del self.edges[edge_key]
                    self.edges[new_edge_key] = edge
                    
                    # 更新节点边映射
                    if node_b_id in self.node_edges:
                        self.node_edges[node_b_id].discard(edge_key)
                    self.node_edges[new_src].add(new_edge_key)
        
        # 合并别名
        node_a.aliases = list(set(node_a.aliases + [node_b.name] + node_b.aliases))
        
        # 删除node_b
        del self.nodes[node_b_id]
        if node_b_id in self.node_edges:
            del self.node_edges[node_b_id]
        
        self.stats["total_nodes"] -= 1
        print(f"节点合并完成，保留节点: {node_a.name} ({node_a_id})")
    
    def _apply_deactivate_edge(self, diff: Diff):
        """应用停用边diff"""
        edge_key = f"{diff.src}::{diff.dst}::{diff.type.value}"
        
        if edge_key in self.edges:
            edge = self.edges[edge_key]
            if edge.active:
                edge.active = False
                self.stats["active_edges"] -= 1
                print(f"停用边: {edge_key}")
    
    # ========== 图健康机制 ==========
    
    def compress_graph(self):
        """定期压缩 - 清理低权重边"""
        print("开始图压缩...")
        
        edges_to_deactivate = []
        
        for edge_key, edge in self.edges.items():
            if edge.active and abs(edge.state.weight) < self.config["min_weight_threshold"]:
                edges_to_deactivate.append(edge_key)
        
        for edge_key in edges_to_deactivate:
            edge = self.edges[edge_key]
            edge.active = False
            self.stats["active_edges"] -= 1
        
        print(f"压缩完成，停用 {len(edges_to_deactivate)} 条低权重边")
    
    def detect_redundancy(self) -> List[Tuple[str, str]]:
        """冗余检测 - 返回重复关系对"""
        redundancy_pairs = []
        
        # 按(src, dst)分组
        edge_groups = {}
        for edge_key, edge in self.edges.items():
            if not edge.active:
                continue
            
            group_key = (edge.src, edge.dst)
            if group_key not in edge_groups:
                edge_groups[group_key] = []
            edge_groups[group_key].append(edge)
        
        # 检测冗余
        for group_key, edges in edge_groups.items():
            if len(edges) > 1:
                # 检查是否有相同类型的边
                type_count = {}
                for edge in edges:
                    if edge.type.value not in type_count:
                        type_count[edge.type.value] = []
                    type_count[edge.type.value].append(edge)
                
                # 报告冗余
                for edge_type, edge_list in type_count.items():
                    if len(edge_list) > 1:
                        redundancy_pairs.append((edge_list[0].src, edge_list[0].dst))
                        print(f"冗余检测: {edge_list[0].src} -> {edge_list[0].dst} 有 {len(edge_list)} 条 {edge_type} 边")
        
        return redundancy_pairs
    
    def find_isolated_nodes(self) -> List[str]:
        """孤立节点处理 - 返回孤立节点ID列表"""
        isolated_nodes = []
        
        for node_id in self.nodes:
            active_edges = 0
            for edge_key in self.node_edges.get(node_id, []):
                edge = self.edges.get(edge_key)
                if edge and edge.active:
                    active_edges += 1
            
            if active_edges == 0:
                isolated_nodes.append(node_id)
                print(f"孤立节点: {self.nodes[node_id].name} ({node_id})")
        
        return isolated_nodes
    
    # ========== 查询和工具函数 ==========
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def get_edge(self, src: str, dst: str, edge_type: EdgeType) -> Optional[Edge]:
        """获取边"""
        edge_key = f"{src}::{dst}::{edge_type.value}"
        return self.edges.get(edge_key)
    
    def get_node_edges(self, node_id: str, active_only: bool = True) -> List[Edge]:
        """获取节点的所有边"""
        edges = []
        
        for edge_key in self.node_edges.get(node_id, []):
            edge = self.edges.get(edge_key)
            if edge and (not active_only or edge.active):
                edges.append(edge)
        
        return edges
    
    def find_nodes_by_name(self, name: str) -> List[Node]:
        """按名称查找节点"""
        results = []
        name_lower = name.lower()
        
        for node in self.nodes.values():
            if name_lower in node.name.lower():
                results.append(node)
            elif any(name_lower in alias.lower() for alias in node.aliases):
                results.append(node)
        
        return results
    
    def to_dict(self) -> Dict:
        """转换为字典（用于序列化）"""
        return {
            "config": self.config,
            "stats": self.stats,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": {edge_key: edge.to_dict() for edge_key, edge in self.edges.items()},
            "node_edges": {node_id: list(edges) for node_id, edges in self.node_edges.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """从字典创建（用于反序列化）"""
        graph = cls()
        
        # 恢复配置和统计
        graph.config = data.get("config", graph.config)
        graph.stats = data.get("stats", graph.stats)
        
        # 恢复节点
        for node_id, node_data in data.get("nodes", {}).items():
            graph.nodes[node_id] = Node.from_dict(node_data)
        
        # 恢复边
        for edge_key, edge_data in data.get("edges", {}).items():
            graph.edges[edge_key] = Edge.from_dict(edge_data)
        
        # 恢复节点边映射
        for node_id, edge_keys in data.get("node_edges", {}).items():
            graph.node_edges[node_id] = set(edge_keys)
        
        return graph
    
    def save_to_file(self, filepath: str):
        """保存到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"图已保存到: {filepath}")
    
    @classmethod
    def load_from_file(cls, filepath: str):
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def print_stats(self):
        """打印统计信息"""
        print("\n" + "="*50)
        print("全局图统计信息")
        print("="*50)
        print(f"节点总数: {self.stats['total_nodes']}")
        print(f"边总数: {self.stats['total_edges']}")
        print(f"活跃边数: {self.stats['active_edges']}")
        print(f"Diff应用次数: {self.stats['diff_count']}")
        print(f"最后更新: {datetime.fromtimestamp(self.stats['last_updated']).strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)
    
    def print_node_info(self, node_id: str):
        """打印节点详细信息"""
        node = self.get_node(node_id)
        if not node:
            print(f"节点不存在: {node_id}")
            return
        
        print(f"\n节点信息: {node.name} ({node_id})")
        print(f"类型: {node.type.value}")
        print(f"创建时间: {datetime.fromtimestamp(node.created_at).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"别名: {', '.join(node.aliases) if node.aliases else '无'}")
        
        edges = self.get_node_edges(node_id)
        if edges:
            print(f"\n关联边 ({len(edges)} 条):")
            for edge in edges:
                other_node = self.get_node(edge.dst if edge.src == node_id else edge.src)
                other_name = other_node.name if other_node else "未知节点"
                direction = "->" if edge.src == node_id else "<-"
                print(f"  {direction} {other_name} ({edge.type.value})")
                print(f"    权重: {edge.state.weight:.3f}, 置信度: {edge.state.confidence:.3f}")
                print(f"    证据数: {edge.state.evidence_count}, 活跃: {edge.active}")
        else:
            print("无关联边")


# ========== 测试函数 ==========

def test_global_graph():
    """测试全局图功能"""
    print("🧪 开始测试全局图...")
    
    # 创建全局图实例
    graph = GlobalGraph()
    
    # 1. 创建节点
    print("\n1. 创建节点...")
    user_id = graph.create_node("哥斯拉", NodeType.USER)
    topic_id = graph.create_node("日本房产", NodeType.TOPIC)
    concept_id = graph.create_node("房地产投资", NodeType.ENTITY)
    
    # 2. 更新关系
    print("\n2. 更新关系...")
    graph.update_edge(user_id, topic_id, EdgeType.INTERESTED_IN, 0.6)
    graph.update_edge(user_id, concept_id, EdgeType.INTERESTED_IN, 0.8)
    graph.update_edge(topic_id, concept_id, EdgeType.RELATED_TO, 0.9)
    
    # 再次更新以测试merge公式
    print("\n3. 再次更新关系（测试merge公式）...")
    graph.update_edge(user_id, topic_id, EdgeType.INTERESTED_IN, 0.3)
    graph.update_edge(user_id, concept_id, EdgeType.INTERESTED_IN, -0.2)  # 负delta测试
    
    # 4. 创建冲突关系
    print("\n4. 创建冲突关系...")
    graph.update_edge(user_id, topic_id, EdgeType.DISLIKES, -0.4)
    
    # 5. 测试节点合并
    print("\n5. 测试节点合并...")
    similar_topic_id = graph.create_node("日本房地产", NodeType.TOPIC)
    graph.update_edge(user_id, similar_topic_id, EdgeType.INTERESTED_IN, 0.5)
    
    # 合并节点
    graph.merge_node(topic_id, similar_topic_id, confidence=0.85)
    
    # 6. 图健康检查
    print("\n6. 图健康检查...")
    graph.compress_graph()
    redundancy_pairs = graph.detect_redundancy()
    isolated_nodes = graph.find_isolated_nodes()
    
    # 7. 打印结果
    print("\n7. 最终结果...")
    graph.print_stats()
    graph.print_node_info(user_id)
    
    # 8. 保存和加载测试
    print("\n8. 保存和加载测试...")
    graph.save_to_file("/tmp/test_global_graph.json")
    
    # 加载测试
    loaded_graph = GlobalGraph.load_from_file("/tmp/test_global_graph.json")
    loaded_graph.print_stats()
    
    print("\n✅ 全局图测试完成！")


if __name__ == "__main__":
    test_global_graph()