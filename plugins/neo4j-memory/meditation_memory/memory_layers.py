"""
记忆分层设计模块（Issue #45）

明确记忆类型和生命周期，实现分层存储和检索：
  L1: 临时上下文（会话级）
  L2: 稳定事实（永久）
  L3: 偏好习惯（长期）
  L4: 任务状态（任务周期）
  L5: 推理过程（可压缩）
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class MemoryLayer(Enum):
    """记忆层级枚举"""
    L1_CONTEXT = "L1_context"  # 临时上下文
    L2_FACT = "L2_fact"  # 稳定事实
    L3_PREFERENCE = "L3_preference"  # 偏好习惯
    L4_TASK = "L4_task"  # 任务状态
    L5_REASONING = "L5_reasoning"  # 推理过程


@dataclass
class MemoryLayerConfig:
    """记忆层级配置"""
    # 层级定义
    layer: MemoryLayer
    
    # 生命周期（天）
    # None 表示永久存储
    lifetime_days: Optional[float] = None
    
    # 是否可压缩
    compressible: bool = False
    
    # 检索优先级（1-5，1 最高）
    retrieval_priority: int = 3
    
    # 存储策略
    storage_strategy: str = "neo4j"  # neo4j / memory_cache / hybrid
    
    # 清理条件
    cleanup_condition: str = ""
    
    @classmethod
    def get_default_configs(cls) -> Dict[MemoryLayer, 'MemoryLayerConfig']:
        """获取默认层级配置"""
        return {
            MemoryLayer.L1_CONTEXT: cls(
                layer=MemoryLayer.L1_CONTEXT,
                lifetime_days=0.01,  # 约 15 分钟（会话级）
                compressible=False,
                retrieval_priority=1,
                storage_strategy="memory_cache",
                cleanup_condition="session_end"
            ),
            MemoryLayer.L2_FACT: cls(
                layer=MemoryLayer.L2_FACT,
                lifetime_days=None,  # 永久
                compressible=False,
                retrieval_priority=2,
                storage_strategy="neo4j",
                cleanup_condition="never"
            ),
            MemoryLayer.L3_PREFERENCE: cls(
                layer=MemoryLayer.L3_PREFERENCE,
                lifetime_days=365,  # 1 年
                compressible=False,
                retrieval_priority=2,
                storage_strategy="neo4j",
                cleanup_condition="user_update"
            ),
            MemoryLayer.L4_TASK: cls(
                layer=MemoryLayer.L4_TASK,
                lifetime_days=7,  # 任务完成 +7 天
                compressible=False,
                retrieval_priority=3,
                storage_strategy="neo4j",
                cleanup_condition="task_complete_plus_7days"
            ),
            MemoryLayer.L5_REASONING: cls(
                layer=MemoryLayer.L5_REASONING,
                lifetime_days=30,  # 30 天
                compressible=True,
                retrieval_priority=4,
                storage_strategy="neo4j",
                cleanup_condition="meditation_compress"
            ),
        }
    
    def is_expired(self, created_at: datetime) -> bool:
        """检查记忆是否过期"""
        if self.lifetime_days is None:
            return False
        
        expires_at = created_at + timedelta(days=self.lifetime_days)
        return datetime.now() > expires_at
    
    def get_neo4j_label(self) -> str:
        """获取 Neo4j 节点标签"""
        label_map = {
            MemoryLayer.L1_CONTEXT: "Context",
            MemoryLayer.L2_FACT: "Fact",
            MemoryLayer.L3_PREFERENCE: "Preference",
            MemoryLayer.L4_TASK: "Task",
            MemoryLayer.L5_REASONING: "Reasoning",
        }
        return label_map.get(self.layer, "Entity")


@dataclass
class MemoryNode:
    """记忆节点"""
    name: str
    entity_type: str
    description: str
    layer: MemoryLayer
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 生命周期相关
    session_id: Optional[str] = None  # L1 会话 ID
    task_id: Optional[str] = None  # L4 任务 ID
    task_status: Optional[str] = None  # L4 任务状态
    
    # 压缩相关（L5）
    compression_factor: float = 1.0
    is_compressed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "layer": self.layer.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "task_status": self.task_status,
            "compression_factor": self.compression_factor,
            "is_compressed": self.is_compressed
        }
    
    def to_cypher_properties(self) -> Dict[str, Any]:
        """转换为 Neo4j Cypher 属性"""
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "memory_layer": self.layer.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "session_id": self.session_id,
            "task_id": self.task_id,
            "task_status": self.task_status,
            "compression_factor": self.compression_factor,
            "is_compressed": self.is_compressed,
            **self.metadata
        }
    
    @classmethod
    def from_cypher_record(cls, record: Dict[str, Any]) -> 'MemoryNode':
        """从 Neo4j 记录创建"""
        layer_str = record.get("memory_layer", "L2_fact")
        layer = MemoryLayer(layer_str) if layer_str in [l.value for l in MemoryLayer] else MemoryLayer.L2_FACT
        
        created_at = datetime.fromisoformat(record["created_at"]) if record.get("created_at") else datetime.now()
        updated_at = datetime.fromisoformat(record["updated_at"]) if record.get("updated_at") else datetime.now()
        
        return cls(
            name=record["name"],
            entity_type=record.get("entity_type", "unknown"),
            description=record.get("description", ""),
            layer=layer,
            created_at=created_at,
            updated_at=updated_at,
            metadata={k: v for k, v in record.items() if k not in [
                "name", "entity_type", "description", "memory_layer",
                "created_at", "updated_at", "session_id", "task_id", "task_status",
                "compression_factor", "is_compressed"
            ]},
            session_id=record.get("session_id"),
            task_id=record.get("task_id"),
            task_status=record.get("task_status"),
            compression_factor=record.get("compression_factor", 1.0),
            is_compressed=record.get("is_compressed", False)
        )


class MemoryLayerManager:
    """
    记忆层级管理器
    
    负责：
    - 记忆节点的分层标记
    - 分层检索
    - 生命周期管理（过期清理）
    """
    
    def __init__(self, graph_store):
        self.store = graph_store
        self.layer_configs = MemoryLayerConfig.get_default_configs()
    
    def classify_memory(self, text: str, context: Optional[Dict[str, Any]] = None) -> MemoryLayer:
        """
        自动分类记忆层级
        
        基于关键词和上下文判断记忆类型
        
        Args:
            text: 记忆内容
            context: 上下文信息（如 session_id, task_id 等）
            
        Returns:
            MemoryLayer: 记忆层级
        """
        text_lower = text.lower()
        
        # L1: 临时上下文（包含"当前"、"现在"、"这次"等）
        if any(word in text_lower for word in ["当前", "现在", "这次", "本次", "current", "now"]):
            return MemoryLayer.L1_CONTEXT
        
        # L4: 任务状态（包含"任务"、"待办"、"进度"等）
        if any(word in text_lower for word in ["任务", "待办", "进度", "todo", "task", "progress"]):
            return MemoryLayer.L4_TASK
        
        # L3: 偏好习惯（包含"喜欢"、"习惯"、"偏好"、"风格"等）
        if any(word in text_lower for word in ["喜欢", "习惯", "偏好", "风格", "prefer", "like", "habit"]):
            return MemoryLayer.L3_PREFERENCE
        
        # L5: 推理过程（包含"因为"、"所以"、"推理"、"逻辑"等）
        if any(word in text_lower for word in ["因为", "所以", "推理", "逻辑", "因果", "because", "therefore", "reasoning"]):
            return MemoryLayer.L5_REASONING
        
        # L2: 稳定事实（默认）
        return MemoryLayer.L2_FACT
    
    def create_memory_node(self, name: str, entity_type: str, description: str,
                          context: Optional[Dict[str, Any]] = None) -> MemoryNode:
        """
        创建记忆节点（自动分类层级）
        
        Args:
            name: 实体名
            entity_type: 实体类型
            description: 描述
            context: 上下文信息
            
        Returns:
            MemoryNode: 创建的节点
        """
        # 自动分类层级
        layer = self.classify_memory(description, context)
        
        # 创建节点
        node = MemoryNode(
            name=name,
            entity_type=entity_type,
            description=description,
            layer=layer,
            metadata=context or {}
        )
        
        # 设置层级特定属性
        if layer == MemoryLayer.L1_CONTEXT and context:
            node.session_id = context.get("session_id")
        
        if layer == MemoryLayer.L4_TASK and context:
            node.task_id = context.get("task_id")
            node.task_status = context.get("task_status", "pending")
        
        return node
    
    def get_nodes_by_layer(self, layer: MemoryLayer, limit: int = 100) -> list:
        """
        按层级查询节点
        
        Args:
            layer: 记忆层级
            limit: 返回数量
            
        Returns:
            节点列表
        """
        query = """
        MATCH (e:Entity)
        WHERE e.memory_layer = $layer
        RETURN e
        ORDER BY e.created_at DESC
        LIMIT $limit
        """
        
        result = self.store.execute_cypher(query, {"layer": layer.value, "limit": limit})
        
        if not result:
            return []
        
        return [MemoryNode.from_cypher_record(record.get("e", {})) for record in result]
    
    def get_expired_nodes(self) -> Dict[MemoryLayer, list]:
        """
        获取所有过期的节点
        
        Returns:
            {layer: [nodes]}
        """
        expired = {layer: [] for layer in MemoryLayer}
        
        # 查询所有节点
        query = """
        MATCH (e:Entity)
        WHERE e.memory_layer IS NOT NULL
        RETURN e
        """
        
        result = self.store.execute_cypher(query)
        
        if not result:
            return expired
        
        for record in result:
            node_data = record.get("e", {})
            if not node_data:
                continue
            
            node = MemoryNode.from_cypher_record(node_data)
            layer_config = self.layer_configs.get(node.layer)
            
            if layer_config and layer_config.is_expired(node.created_at):
                expired[node.layer].append(node)
        
        return expired
    
    def cleanup_expired(self, dry_run: bool = True) -> Dict[str, int]:
        """
        清理过期节点
        
        Args:
            dry_run: 如果为 True，只统计不删除
            
        Returns:
            {layer: count}
        """
        expired = self.get_expired_nodes()
        stats = {layer.value: 0 for layer in MemoryLayer}
        
        for layer, nodes in expired.items():
            layer_config = self.layer_configs.get(layer)
            
            # 永久存储的层级不清理
            if layer_config and layer_config.lifetime_days is None:
                continue
            
            if dry_run:
                stats[layer.value] = len(nodes)
            else:
                # 批量删除
                node_names = [node.name for node in nodes]
                if node_names:
                    delete_query = """
                    MATCH (e:Entity)
                    WHERE e.name IN $names
                    DETACH DELETE e
                    """
                    self.store.execute_cypher(delete_query, {"names": node_names})
                    stats[layer.value] = len(node_names)
        
        return stats
