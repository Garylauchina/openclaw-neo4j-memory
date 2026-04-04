"""
Memory Provider — 认知记忆提供器

替换 OpenClaw 的 memory.retrieve()，从 Neo4j 图谱检索真实记忆。

改造要点（Phase 1）：
  - 初始化时接受 neo4j_client 参数
  - retrieve() 优先调用 neo4j_client.search() 从 Neo4j 检索真实记忆
  - 将 /search 返回的 context（context_text, subgraph, matched_entities）
    转换为认知系统内部的 Node 格式
  - 保留原有的汇率 API 增强逻辑
  - Neo4j 不可用时降级到原有 Mock 模式
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cognitive_engine.memory_provider")

# 尝试导入同包模块（使用相对导入）
try:
    from .query_processor import process_query
    from .fx_api import get_usd_cny
    from .formatter import to_claw_format
except ImportError:
    # 备用：独立运行时的 stub
    def process_query(query: str, graph=None, attention=None) -> list:
        return []

    def get_usd_cny() -> str:
        return "6.9123"

    def to_claw_format(data: list) -> list:
        return [{"text": str(d), "score": 0.5, "rank": i + 1, "metadata": {}}
                for i, d in enumerate(data)]


class CognitiveMemoryProvider:
    """
    认知记忆提供器

    优先通过 Neo4jMemoryClient 调用 /search API 从 Neo4j 图谱检索记忆。
    当 Neo4j 不可用时，自动降级到本地 Mock 模式。
    """

    def __init__(
        self,
        neo4j_client=None,
        graph=None,
        attention=None,
        rqs=None,
        mock_mode: bool = False,
    ):
        """
        初始化认知记忆提供器。

        Args:
            neo4j_client: Neo4jMemoryClient 实例（Phase 1 新增）
            graph: 记忆图系统（旧版兼容）
            attention: 注意力系统（旧版兼容）
            rqs: 推理质量评分系统（旧版兼容）
            mock_mode: 强制使用 Mock 模式
        """
        self.neo4j_client = neo4j_client
        self.graph = graph
        self.attention = attention
        self.rqs = rqs
        self.mock_mode = mock_mode

        # 统计信息
        self.stats = {
            "total_queries": 0,
            "neo4j_queries": 0,
            "mock_queries": 0,
            "api_calls": 0,
            "graph_retrievals": 0,
            "avg_processing_time": 0.0,
            "reality_enhanced_queries": 0,
        }

        # 汇率缓存
        self.fx_cache: Dict[str, Any] = {
            "rate": None,
            "timestamp": None,
            "ttl": 60,
        }

        # 确定运行模式
        neo4j_available = False
        if neo4j_client and not mock_mode:
            neo4j_available = neo4j_client.health_check()

        self._use_neo4j = neo4j_available and not mock_mode

        logger.info(
            "CognitiveMemoryProvider initialized: neo4j=%s, mock_mode=%s, "
            "graph=%s, attention=%s, rqs=%s",
            "connected" if self._use_neo4j else "unavailable",
            mock_mode,
            "yes" if graph else "no",
            "yes" if attention else "no",
            "yes" if rqs else "no",
        )

    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        从 Neo4j 图谱（或 Mock）检索相关记忆。

        Args:
            query: 查询文本
            k: 返回结果数量上限

        Returns:
            格式化后的记忆片段列表，每项包含 text, score, rank, metadata
        """
        start_time = time.time()
        self.stats["total_queries"] += 1

        logger.info("Cognitive retrieve: query='%s', k=%d", query[:80], k)

        # 1. 尝试 Neo4j 检索
        if self._use_neo4j:
            nodes = self._neo4j_retrieve(query, k)
            if nodes is not None:
                self.stats["neo4j_queries"] += 1
            else:
                # Neo4j 调用失败，降级到 Mock
                logger.warning("Neo4j retrieve failed, falling back to mock")
                nodes = self._mock_retrieve(query, k)
                self.stats["mock_queries"] += 1
        else:
            nodes = self._mock_retrieve(query, k)
            self.stats["mock_queries"] += 1

        # 2. 现实世界增强（汇率 API）
        enhanced_nodes = self._reality_enhance(query, nodes)

        # 3. 格式化输出
        results = to_claw_format(enhanced_nodes)

        # 4. 更新统计
        processing_time = time.time() - start_time
        total_time = self.stats["avg_processing_time"] * (self.stats["total_queries"] - 1)
        self.stats["avg_processing_time"] = (
            (total_time + processing_time) / self.stats["total_queries"]
        )

        logger.info(
            "Retrieve completed: %d results in %.3fs",
            len(results), processing_time,
        )
        return results

    # ------------------------------------------------------------------
    # Neo4j 检索
    # ------------------------------------------------------------------

    def _neo4j_retrieve(self, query: str, k: int) -> Optional[List[Dict[str, Any]]]:
        """
        通过 Neo4jMemoryClient 调用 /search API 检索记忆。

        将 /search 返回的 context 结构转换为认知系统内部的节点格式。

        /search 返回的 context 结构（来自 ContextResult.to_dict()）::

            {
                "context_text": "### 已知实体\\n- 人物：...",
                "subgraph": {
                    "nodes": [{"name": "...", "entity_type": "person", ...}, ...],
                    "edges": [{"source": "A", "target": "B", "relation_type": "..."}, ...]
                },
                "matched_entities": ["entity1", "entity2"],
                "entity_count": 5,
                "edge_count": 3
            }

        Returns:
            节点列表（dict 格式），或 None 表示调用失败
        """
        try:
            result = self.neo4j_client.search(query, limit=k, use_llm=True)
            if result is None:
                return None

            if result.get("status") != "success":
                logger.warning("Neo4j search returned non-success: %s", result.get("status"))
                return None

            context = result.get("context", {})
            return self._parse_context(context, k)

        except Exception as exc:
            logger.warning("Neo4j search exception: %s", exc)
            return None

    def _parse_context(self, context: Dict[str, Any], k: int) -> List[Dict[str, Any]]:
        """
        将 /search 返回的 context 转换为认知系统内部的节点格式。

        解析三类信息：
          1. subgraph.nodes → 实体节点
          2. subgraph.edges → 关系节点
          3. context_text → 摘要/元知识节点
        """
        nodes: List[Dict[str, Any]] = []
        subgraph = context.get("subgraph", {})

        # 解析实体信息（从 subgraph.nodes）
        for entity in subgraph.get("nodes", [])[:k]:
            node_name = entity.get("name", "")
            entity_type = entity.get("entity_type", "concept")
            properties = {
                key: val for key, val in entity.items()
                if key not in ("name", "entity_type")
            }
            nodes.append({
                "content": node_name,
                "entity_type": entity_type,
                "properties": properties,
                "mention_count": entity.get("mention_count", 1),
                "attention_score": min(1.0, entity.get("mention_count", 1) * 0.2),
                "rqs": entity.get("activation_level", 0.5),
                "source": "neo4j_graph",
            })

        # 解析关系信息（从 subgraph.edges）
        for rel in subgraph.get("edges", []):
            src = rel.get("source", "?")
            tgt = rel.get("target", "?")
            rtype = rel.get("relation_type", "related_to")
            nodes.append({
                "content": f"{src} --[{rtype}]--> {tgt}",
                "relation_type": rtype,
                "attention_score": 0.4,
                "rqs": rel.get("weight", 0.5),
                "source": "neo4j_graph",
            })

        # 解析 context_text 作为摘要节点（如果有实质内容）
        context_text = context.get("context_text", "").strip()
        if context_text and len(context_text) > 10:
            nodes.append({
                "content": context_text[:500],
                "attention_score": 0.8,
                "rqs": 0.7,
                "source": "neo4j_meta_knowledge",
            })

        return nodes[:k]

    # ------------------------------------------------------------------
    # Mock 检索（降级模式）
    # ------------------------------------------------------------------

    def _mock_retrieve(self, query: str, k: int) -> List[Dict[str, Any]]:
        """
        Mock 模式检索：使用旧版 process_query + attention 逻辑。
        """
        logger.debug("Using mock retrieve for query: %s", query[:50])
        self.stats["graph_retrievals"] += 1

        raw_nodes = process_query(query, self.graph, self.attention)

        # 为每个节点计算 RQS
        for node in raw_nodes:
            if self.rqs and hasattr(self.rqs, "score"):
                content = getattr(node, "content", str(node))
                node.rqs = self.rqs.score(content)
            else:
                content = str(getattr(node, "content", ""))
                query_words = set(query.lower().split())
                content_words = set(content.lower().split())
                if query_words and content_words:
                    intersection = len(query_words & content_words)
                    union = len(query_words | content_words)
                    node.rqs = intersection / union if union > 0 else 0.3
                else:
                    node.rqs = 0.3

        # 排序
        ranked = sorted(
            raw_nodes,
            key=lambda x: getattr(x, "attention_score", 0.5) * getattr(x, "rqs", 0.5),
            reverse=True,
        )[:k]

        # 转换为 dict 格式
        result = []
        for node in ranked:
            result.append({
                "content": getattr(node, "content", str(node)),
                "attention_score": getattr(node, "attention_score", 0.5),
                "rqs": getattr(node, "rqs", 0.5),
                "source": "mock_graph",
            })
        return result

    # ------------------------------------------------------------------
    # 现实世界增强
    # ------------------------------------------------------------------

    def _reality_enhance(
        self, query: str, nodes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        检测汇率查询关键词，调用真实 API 添加实时数据节点。
        """
        enhanced = list(nodes)
        query_lower = query.lower()
        fx_keywords = ["usd", "美元", "汇率", "兑换", "人民币", "cny", "exchange"]

        if any(kw in query_lower for kw in fx_keywords):
            logger.info("Detected FX query, calling real API...")
            fx_rate = self._get_fx_rate()
            self.stats["api_calls"] += 1
            self.stats["reality_enhanced_queries"] += 1

            if fx_rate != "API_ERROR":
                enhanced.append({
                    "content": f"当前 USD→CNY 汇率：{fx_rate}",
                    "rqs": 0.9,
                    "attention_score": 1.0,
                    "source": "real_world_api",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {
                        "type": "real_time_data",
                        "api": "exchangerate",
                        "cache_hit": self.fx_cache["rate"] is not None,
                    },
                })
                logger.info("Added real-time FX node: %s", fx_rate)
            else:
                logger.warning("FX API call failed")

        return enhanced

    def _get_fx_rate(self) -> str:
        """获取汇率（带缓存）。"""
        current_time = time.time()

        if (
            self.fx_cache["rate"] is not None
            and self.fx_cache["timestamp"] is not None
            and current_time - self.fx_cache["timestamp"] < self.fx_cache["ttl"]
        ):
            return self.fx_cache["rate"]

        try:
            rate = get_usd_cny()
            if rate != "API_ERROR":
                self.fx_cache["rate"] = rate
                self.fx_cache["timestamp"] = current_time
            return rate
        except Exception as exc:
            logger.warning("FX API exception: %s", exc)
            return "API_ERROR"

    # ------------------------------------------------------------------
    # 统计与状态
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息。"""
        return {
            "performance": self.stats,
            "cache": {
                "fx_rate": self.fx_cache["rate"],
                "age_seconds": (
                    time.time() - self.fx_cache["timestamp"]
                    if self.fx_cache["timestamp"]
                    else None
                ),
            },
            "status": {
                "neo4j_connected": self._use_neo4j,
                "graph_connected": self.graph is not None,
                "attention_connected": self.attention is not None,
                "rqs_connected": self.rqs is not None,
            },
        }
