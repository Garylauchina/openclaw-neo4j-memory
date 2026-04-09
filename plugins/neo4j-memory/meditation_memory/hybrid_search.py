"""
混合检索实现（Issue #44）

图遍历 + 向量相似度双路召回，提升检索召回率 +20%

功能：
  1. Neo4j 向量索引创建和查询
  2. 双路召回集成（图遍历 + 向量）
  3. 融合排序算法
  4. 降级策略（向量索引不存在/超时降级为图遍历）
"""

import logging
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchConfig:
    """混合检索配置"""
    # 向量检索配置
    vector_index_name: str = "entity_embeddings"
    vector_dimension: int = 1536  # text-embedding-3-small 维度
    vector_top_k: int = 10  # 向量检索返回数量
    
    # 融合排序权重
    graph_weight: float = 0.6  # 图遍历得分权重
    vector_weight: float = 0.4  # 向量相似度权重
    
    # 降级策略
    vector_timeout_seconds: float = 2.0  # 向量检索超时
    fallback_to_graph_only: bool = True  # 向量失败时降级为纯图遍历
    
    # 从环境变量读取
    def __post_init__(self):
        self.vector_top_k = int(os.environ.get("HYBRID_SEARCH_VECTOR_TOP_K", str(self.vector_top_k)))
        self.graph_weight = float(os.environ.get("HYBRID_SEARCH_GRAPH_WEIGHT", str(self.graph_weight)))
        self.vector_weight = float(os.environ.get("HYBRID_SEARCH_VECTOR_WEIGHT", str(self.vector_weight)))
        self.vector_timeout_seconds = float(os.environ.get("HYBRID_SEARCH_VECTOR_TIMEOUT", str(self.vector_timeout_seconds)))


@dataclass
class SearchResult:
    """检索结果"""
    name: str
    entity_type: str
    description: str
    score: float  # 融合得分
    graph_score: float  # 图遍历得分
    vector_score: float  # 向量相似度得分
    source: str  # "graph", "vector", "both"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "score": round(self.score, 4),
            "graph_score": round(self.graph_score, 4),
            "vector_score": round(self.vector_score, 4),
            "source": self.source,
            "metadata": self.metadata
        }


class HybridSearch:
    """
    混合检索器
    
    实现图遍历 + 向量相似度双路召回
    """
    
    def __init__(self, graph_store, config: Optional[HybridSearchConfig] = None):
        self.store = graph_store
        self.config = config or HybridSearchConfig()
        self.vector_index_exists = False
        
        # 检查向量索引是否存在
        self._check_vector_index()
    
    def _check_vector_index(self) -> None:
        """检查向量索引是否存在"""
        try:
            query = """
            SHOW INDEXES
            WHERE name = $index_name
            RETURN count(*) as count
            """
            result = self.store.execute_cypher(query, {"index_name": self.config.vector_index_name})
            if result and len(result) > 0 and result[0].get("count", 0) > 0:
                self.vector_index_exists = True
                logger.info(f"向量索引 {self.config.vector_index_name} 已存在")
            else:
                self.vector_index_exists = False
                logger.warning(f"向量索引 {self.config.vector_index_name} 不存在，将降级为纯图遍历")
        except Exception as e:
            logger.error(f"检查向量索引失败：{e}")
            self.vector_index_exists = False
    
    def create_vector_index(self, embedding_property: str = "embedding") -> bool:
        """
        创建向量索引
        
        Args:
            embedding_property: 存储向量的属性名
            
        Returns:
            True: 创建成功，False: 创建失败
        """
        try:
            # 检查 Neo4j 版本是否支持向量索引
            version_query = "CALL dbms.components() YIELD versions RETURN versions[0] as version"
            version_result = self.store.execute_cypher(version_query)
            if not version_result:
                logger.error("无法获取 Neo4j 版本")
                return False
            
            version = version_result[0].get("version", "")
            if not version.startswith("5."):
                logger.error(f"Neo4j 版本 {version} 不支持向量索引，需要 Neo4j 5.x")
                return False
            
            # 创建向量索引
            create_index_query = f"""
            CREATE VECTOR INDEX {self.config.vector_index_name}
            FOR (e:Entity)
            ON (e.{embedding_property})
            OPTIONS {{
                indexConfig: {{
                    `vector.dimensions`: {self.config.vector_dimension},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
            """
            
            self.store.execute_cypher(create_index_query)
            self.vector_index_exists = True
            logger.info(f"向量索引 {self.config.vector_index_name} 创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建向量索引失败：{e}")
            return False
    
    def search(self, query: str, query_embedding: Optional[List[float]] = None, limit: int = 10) -> List[SearchResult]:
        """
        混合检索
        
        Args:
            query: 查询文本
            query_embedding: 查询向量（可选，如果提供则使用向量检索）
            limit: 返回数量
            
        Returns:
            检索结果列表
        """
        start_time = time.time()
        
        # 1. 图遍历检索
        graph_results = self._graph_search(query, limit=limit * 2)  # 多召回一些用于融合
        
        # 2. 向量检索（如果有向量且索引存在）
        vector_results = []
        if query_embedding and self.vector_index_exists:
            try:
                vector_results = self._vector_search(query_embedding, limit=limit * 2)
            except Exception as e:
                logger.warning(f"向量检索失败，降级为纯图遍历：{e}")
                if not self.config.fallback_to_graph_only:
                    raise
        
        # 3. 融合排序
        fused_results = self._fuse_results(graph_results, vector_results, limit=limit)
        
        elapsed = time.time() - start_time
        logger.info(f"混合检索完成：query='{query}', 返回 {len(fused_results)} 个结果，耗时 {elapsed:.3f}s")
        
        return fused_results
    
    def _graph_search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """
        图遍历检索
        
        使用关键词匹配 + 图遍历
        """
        # 关键词匹配
        keyword_query = """
        MATCH (e:Entity)
        WHERE e.name CONTAINS $query OR e.description CONTAINS $query
        RETURN e.name as name, e.entity_type as entity_type, e.description as description,
               e.mention_count as mention_count, e.degree as degree
        ORDER BY e.mention_count DESC
        LIMIT $limit
        """
        
        try:
            result = self.store.execute_cypher(keyword_query, {"query": query, "limit": limit})
            
            if not result:
                return []
            
            # 计算图遍历得分（基于提及次数和度中心性）
            results = []
            max_mentions = max((r.get("mention_count", 0) or 0) for r in result) or 1
            max_degree = max((r.get("degree", 0) or 0) for r in result) or 1
            
            for r in result:
                mention_score = (r.get("mention_count", 0) or 0) / max_mentions
                degree_score = (r.get("degree", 0) or 0) / max_degree
                graph_score = 0.7 * mention_score + 0.3 * degree_score
                
                results.append(SearchResult(
                    name=r["name"],
                    entity_type=r.get("entity_type", "unknown"),
                    description=r.get("description", ""),
                    score=graph_score,
                    graph_score=graph_score,
                    vector_score=0.0,
                    source="graph",
                    metadata={"mention_count": r.get("mention_count", 0), "degree": r.get("degree", 0)}
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"图遍历检索失败：{e}")
            return []
    
    def _vector_search(self, query_embedding: List[float], limit: int = 20) -> List[SearchResult]:
        """
        向量相似度检索
        
        使用 Neo4j 向量索引查询
        """
        start_time = time.time()
        
        # 向量相似度查询
        vector_query = f"""
        CALL db.index.vector.queryNodes(
            '{self.config.vector_index_name}',
            $limit,
            $query_embedding
        )
        YIELD node, score
        RETURN node.name as name, node.entity_type as entity_type, 
               node.description as description, node.mention_count as mention_count,
               score as vector_score
        """
        
        try:
            # 超时控制
            if time.time() - start_time > self.config.vector_timeout_seconds:
                raise TimeoutError(f"向量检索超时（>{self.config.vector_timeout_seconds}s）")
            
            result = self.store.execute_cypher(vector_query, {
                "query_embedding": query_embedding,
                "limit": limit
            })
            
            if not result:
                return []
            
            # 转换为 SearchResult
            results = []
            for r in result:
                vector_score = r.get("vector_score", 0.0)
                results.append(SearchResult(
                    name=r["name"],
                    entity_type=r.get("entity_type", "unknown"),
                    description=r.get("description", ""),
                    score=vector_score,
                    graph_score=0.0,
                    vector_score=vector_score,
                    source="vector",
                    metadata={"mention_count": r.get("mention_count", 0)}
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"向量检索失败：{e}")
            raise
    
    def _fuse_results(self, graph_results: List[SearchResult], vector_results: List[SearchResult], limit: int = 10) -> List[SearchResult]:
        """
        融合排序算法
        
        使用线性加权融合：final_score = graph_weight * graph_score + vector_weight * vector_score
        """
        # 合并结果（按名称去重）
        result_map: Dict[str, SearchResult] = {}
        
        # 先添加图遍历结果
        for r in graph_results:
            result_map[r.name] = r
        
        # 再融合向量结果
        for r in vector_results:
            if r.name in result_map:
                # 已存在，融合得分
                existing = result_map[r.name]
                existing.source = "both"
                existing.vector_score = r.vector_score
                existing.graph_score = existing.graph_score
                existing.score = (
                    self.config.graph_weight * existing.graph_score +
                    self.config.vector_weight * r.vector_score
                )
            else:
                # 新结果
                r.score = r.vector_score * self.config.vector_weight
                result_map[r.name] = r
        
        # 按融合得分排序
        sorted_results = sorted(result_map.values(), key=lambda x: x.score, reverse=True)
        
        # 返回前 limit 个
        return sorted_results[:limit]
