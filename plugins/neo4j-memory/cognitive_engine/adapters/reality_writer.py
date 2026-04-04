"""
Reality Writer — 现实数据写入器

将认知系统产生的数据写入 Neo4j 图谱，替代原有的纯内存存储。

改造要点（Phase 1）：
  - 初始化时接受 neo4j_client 参数
  - write_reality_data() 在本地存储的同时，通过 /ingest API 写入 Neo4j
  - 保留原有的 TemporalNode 内存管理（信念衰减、刷新判断等）
  - Neo4j 不可用时降级到纯内存模式
"""

import logging
import math
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cognitive_engine.reality_writer")


class TemporalNode:
    """
    时间感知的知识节点

    支持信念衰减：随时间推移，信念强度按指数衰减，
    当信念低于阈值时标记为需要刷新。
    """

    # 不同节点类型的衰减率（越大衰减越快）
    DECAY_RATES = {
        "temporal": 0.1,    # 时变数据衰减较快
        "fact": 0.001,      # 事实衰减极慢
        "opinion": 0.05,    # 观点中等衰减
        "prediction": 0.08, # 预测较快衰减
    }

    # 刷新阈值
    REFRESH_THRESHOLD = 0.5

    def __init__(
        self,
        content: str,
        value: Any,
        node_type: str = "temporal",
        source: str = "unknown",
        timestamp: Optional[datetime] = None,
        belief_strength: float = 0.9,
        rqs: float = 0.5,
    ):
        self.content = content
        self.value = value
        self.node_type = node_type
        self.source = source
        self.timestamp = timestamp or datetime.now()
        self.belief_strength = belief_strength
        self.rqs = rqs

        self.decay_rate = self.DECAY_RATES.get(node_type, 0.05)
        self.update_count = 0
        self.last_updated = self.timestamp
        self.history: List[Dict[str, Any]] = []

    def get_current_belief(self) -> float:
        """计算当前信念强度（考虑时间衰减）。"""
        age_hours = (datetime.now() - self.last_updated).total_seconds() / 3600.0
        decayed = self.belief_strength * math.exp(-self.decay_rate * age_hours)
        return max(0.01, min(1.0, decayed))

    def should_refresh(self) -> bool:
        """判断是否需要刷新。"""
        return self.get_current_belief() < self.REFRESH_THRESHOLD

    def update(self, new_value: Any, new_rqs: float, source: str):
        """更新节点值。"""
        self.history.append({
            "old_value": self.value,
            "new_value": new_value,
            "old_belief": self.belief_strength,
            "timestamp": datetime.now().isoformat(),
        })
        self.value = new_value
        self.rqs = new_rqs
        self.source = source
        self.belief_strength = min(1.0, self.belief_strength + 0.1)
        self.last_updated = datetime.now()
        self.update_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        current_belief = self.get_current_belief()
        age_hours = (datetime.now() - self.timestamp).total_seconds() / 3600.0
        return {
            "content": self.content,
            "value": self.value,
            "type": self.node_type,
            "source": self.source,
            "belief_strength": self.belief_strength,
            "current_belief": current_belief,
            "rqs": self.rqs,
            "needs_refresh": self.should_refresh(),
            "age_hours": age_hours,
            "update_count": self.update_count,
            "timestamp": self.timestamp.isoformat(),
            "last_updated": self.last_updated.isoformat(),
        }


class RealityGraphWriter:
    """
    现实数据写入器

    在本地维护 TemporalNode 内存缓存的同时，
    通过 Neo4jMemoryClient 将数据持久化到 Neo4j 图谱。
    """

    def __init__(self, neo4j_client=None, mock_mode: bool = False):
        """
        初始化写入器。

        Args:
            neo4j_client: Neo4jMemoryClient 实例（Phase 1 新增）
            mock_mode: 强制使用纯内存模式
        """
        self.neo4j_client = neo4j_client
        self.mock_mode = mock_mode

        # 内存存储
        self.temporal_nodes: Dict[str, TemporalNode] = {}
        self.static_nodes: Dict[str, Dict[str, Any]] = {}

        # 统计
        self.stats = {
            "total_writes": 0,
            "neo4j_writes": 0,
            "neo4j_failures": 0,
            "memory_only_writes": 0,
            "updates": 0,
            "expired_nodes": 0,
            "high_confidence_writes": 0,
        }

        # 确定运行模式
        neo4j_available = False
        if neo4j_client and not mock_mode:
            neo4j_available = neo4j_client.health_check()

        self._use_neo4j = neo4j_available and not mock_mode

        logger.info(
            "RealityGraphWriter initialized: neo4j=%s, mock_mode=%s",
            "connected" if self._use_neo4j else "unavailable",
            mock_mode,
        )

    def write_reality_data(
        self,
        content: str,
        value: Any,
        type: str = "temporal",
        source: str = "unknown",
        rqs: float = 0.5,
        belief_strength: float = 0.9,
    ) -> TemporalNode:
        """
        写入现实数据。

        同时写入本地内存和 Neo4j 图谱（如果可用）。

        Args:
            content: 内容描述
            value: 数据值
            type: 节点类型（temporal / fact / opinion / prediction）
            source: 数据来源
            rqs: 推理质量评分
            belief_strength: 初始信念强度

        Returns:
            创建或更新的 TemporalNode
        """
        self.stats["total_writes"] += 1
        logger.info(
            "Writing reality data: content='%s', type=%s, source=%s",
            content[:50], type, source,
        )

        # 1. 本地内存写入/更新
        if content in self.temporal_nodes:
            node = self.temporal_nodes[content]
            node.update(value, rqs, source)
            self.stats["updates"] += 1
            logger.debug("Updated existing node: %s", content[:50])
        else:
            node = TemporalNode(
                content=content,
                value=value,
                node_type=type,
                source=source,
                belief_strength=belief_strength,
                rqs=rqs,
            )
            if type == "fact":
                self.static_nodes[content] = node.to_dict()
            self.temporal_nodes[content] = node

        # 2. 写入 Neo4j（如果可用）
        if self._use_neo4j:
            self._write_to_neo4j(node)

        if rqs > 0.8:
            self.stats["high_confidence_writes"] += 1

        return node

    def _write_to_neo4j(self, node: TemporalNode):
        """
        通过 /ingest API 将节点数据写入 Neo4j。

        将 TemporalNode 的结构化信息转换为自然语言文本，
        以便 memory_api_server 的 EntityExtractor 能正确提取实体和关系。
        """
        try:
            # 构造适合 EntityExtractor 的文本
            text_parts = [f"{node.content}的值为{node.value}"]
            text_parts.append(f"数据类型为{node.node_type}")
            text_parts.append(f"数据来源为{node.source}")
            text_parts.append(f"置信度为{node.rqs:.2f}")
            text_parts.append(f"记录时间为{node.last_updated.isoformat()}")

            text = "。".join(text_parts) + "。"

            result = self.neo4j_client.ingest(
                text=text,
                use_llm=True,
                async_mode=True,
            )

            if result and result.get("status") in ("accepted", "success"):
                self.stats["neo4j_writes"] += 1
                logger.info("Neo4j ingest success for: %s", node.content[:50])
            else:
                self.stats["neo4j_failures"] += 1
                logger.warning(
                    "Neo4j ingest returned unexpected status: %s",
                    result.get("status") if result else "None",
                )
        except Exception as exc:
            self.stats["neo4j_failures"] += 1
            logger.warning("Neo4j ingest exception: %s", exc)

    # ------------------------------------------------------------------
    # 节点管理
    # ------------------------------------------------------------------

    def get_node(self, content: str) -> Optional[TemporalNode]:
        """获取指定节点。"""
        return self.temporal_nodes.get(content)

    def get_refresh_candidates(self) -> List[TemporalNode]:
        """获取需要刷新的节点列表。"""
        candidates = [
            node for node in self.temporal_nodes.values()
            if node.should_refresh()
        ]
        candidates.sort(key=lambda n: n.get_current_belief())
        return candidates

    def cleanup_expired(self, belief_threshold: float = 0.1) -> int:
        """清理信念过低的节点。"""
        to_remove = [
            key for key, node in self.temporal_nodes.items()
            if node.get_current_belief() < belief_threshold
        ]
        for key in to_remove:
            del self.temporal_nodes[key]
            self.stats["expired_nodes"] += 1

        if to_remove:
            logger.info("Cleaned up %d expired nodes", len(to_remove))
        return len(to_remove)

    # ------------------------------------------------------------------
    # 统计
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息。"""
        temporal_count = len(self.temporal_nodes)
        static_count = len(self.static_nodes)
        needs_refresh = sum(
            1 for n in self.temporal_nodes.values() if n.should_refresh()
        )
        avg_belief = (
            sum(n.get_current_belief() for n in self.temporal_nodes.values())
            / temporal_count
            if temporal_count > 0
            else 0.0
        )

        return {
            "node_summary": {
                "total_nodes": temporal_count + static_count,
                "temporal_nodes": temporal_count,
                "static_nodes": static_count,
                "needs_refresh": needs_refresh,
                "avg_belief": avg_belief,
            },
            "performance": self.stats,
            "neo4j_status": {
                "connected": self._use_neo4j,
                "writes": self.stats["neo4j_writes"],
                "failures": self.stats["neo4j_failures"],
            },
            "source_distribution": self._get_source_distribution(),
        }

    def _get_source_distribution(self) -> Dict[str, int]:
        """获取数据源分布。"""
        distribution: Dict[str, int] = {}
        for node in self.temporal_nodes.values():
            source = node.source
            distribution[source] = distribution.get(source, 0) + 1
        return distribution
