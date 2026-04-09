#!/usr/bin/env python3
"""
激活子图（Active Subgraph）实现
基于用户提供的完整规范实现

核心设计原则：
1. 为当前query构建最优上下文
2. 从Global Graph中"选择+压缩"
3. 控制规模防止context爆炸（max_nodes≤30, max_edges≤60）
4. 不做持久化，不修改全局图
"""

import json
import time
import hashlib
import math
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import heapq
from collections import defaultdict, deque

# 导入全局图
from global_graph import GlobalGraph, Node, Edge, NodeType, EdgeType, StateVector

# ========== 数据结构定义 ==========

@dataclass
class QueryParseResult:
    """Query解析结果"""
    topics: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    intent: str = "general"  # analysis, question, decision, etc.
    keywords: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)

@dataclass
class AnchorNode:
    """锚点节点"""
    node_id: str
    node: Node
    score: float
    source: str  # "graph", "vector", "recent"
    relevance: float  # 语义相关性 [0, 1]
    
    def __lt__(self, other):
        return self.score > other  # 用于最大堆
    
    def to_dict(self):
        return {
            "node_id": self.node_id,
            "node_name": self.node.name,
            "score": self.score,
            "source": self.source,
            "relevance": self.relevance
        }

@dataclass
class ActiveSubgraph:
    """激活子图 - 标准结构"""
    nodes: Set[str] = field(default_factory=set)  # 节点ID集合
    edges: Set[str] = field(default_factory=set)  # 边key集合
    score: float = 0.0  # 子图整体评分
    topic: str = ""  # 主要话题
    anchors: List[AnchorNode] = field(default_factory=list)  # 锚点节点
    query: str = ""  # 原始查询
    query_parse: QueryParseResult = field(default_factory=QueryParseResult)
    created_at: int = field(default_factory=lambda: int(time.time()))
    cache_key: str = ""  # 缓存键
    
    def to_dict(self):
        return {
            "nodes": list(self.nodes),
            "edges": list(self.edges),
            "score": self.score,
            "topic": self.topic,
            "anchors": [anchor.to_dict() for anchor in self.anchors],
            "query": self.query,
            "query_parse": self.query_parse.to_dict(),
            "created_at": self.created_at,
            "cache_key": self.cache_key,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges)
        }
    
    @classmethod
    def from_dict(cls, data: Dict, graph: GlobalGraph):
        """从字典创建（需要全局图实例来获取节点和边）"""
        subgraph = cls(
            nodes=set(data.get("nodes", [])),
            edges=set(data.get("edges", [])),
            score=data.get("score", 0.0),
            topic=data.get("topic", ""),
            query=data.get("query", ""),
            created_at=data.get("created_at", int(time.time())),
            cache_key=data.get("cache_key", "")
        )
        
        # 恢复query_parse
        if "query_parse" in data:
            subgraph.query_parse = QueryParseResult.from_dict(data["query_parse"])
        
        # 锚点节点需要从全局图重建
        subgraph.anchors = []
        for anchor_data in data.get("anchors", []):
            node_id = anchor_data.get("node_id")
            if node_id and node_id in graph.nodes:
                node = graph.nodes[node_id]
                anchor = AnchorNode(
                    node_id=node_id,
                    node=node,
                    score=anchor_data.get("score", 0.0),
                    source=anchor_data.get("source", "graph"),
                    relevance=anchor_data.get("relevance", 0.0)
                )
                subgraph.anchors.append(anchor)
        
        return subgraph

# ========== 激活子图引擎实现 ==========

class ActiveSubgraphEngine:
    """
    激活子图引擎
    
    核心定义：
    Active Subgraph = 从全局图中按query动态提取的、受限规模的高相关结构子集。
    
    本质：Graph-based Context Retrieval Engine
    比RAG高级一层：RAG是top-k chunks，这是top-k structured subgraph
    """
    
    def __init__(self, global_graph: GlobalGraph, config: Optional[Dict] = None):
        """
        初始化激活子图引擎
        
        Args:
            global_graph: 全局图实例
            config: 配置参数
        """
        self.global_graph = global_graph
        
        # 默认配置
        self.config = {
            # 硬约束（必须实现）
            "max_nodes": 30,           # 最大节点数
            "max_edges": 60,           # 最大边数
            "max_depth": 2,            # 扩展深度限制
            
            # Anchor召回
            "anchor_top_k": 8,         # 锚点节点数量
            "min_anchor_score": 0.3,   # 最小锚点分数
            
            # 扩展参数
            "edge_weight_threshold": 0.1,  # 边权重阈值
            "min_node_score": 0.2,     # 最小节点分数
            
            # 评分权重
            "anchor_score_weights": {  # 锚点评分权重
                "semantic_similarity": 0.5,
                "recency": 0.3,
                "node_degree": 0.2
            },
            "expansion_score_weights": {  # 扩展评分权重
                "edge_weight": 0.6,
                "edge_confidence": 0.2,
                "recency": 0.2
            },
            
            # 缓存
            "cache_enabled": True,
            "cache_ttl_seconds": 300,  # 缓存存活时间（5分钟）
            
            # 错误控制
            "fallback_to_vector": True,  # 无锚点时回退到向量检索
            "force_truncate": True,      # 子图过大时强制截断
            "noise_threshold": 0.15,     # 噪声阈值
        }
        
        # 更新自定义配置
        if config:
            self.config.update(config)
        
        # 缓存
        self.cache: Dict[str, Tuple[ActiveSubgraph, int]] = {}
        
        # 最近上下文（模拟）
        self.recent_context: List[Tuple[str, int]] = []  # [(node_id, timestamp), ...]
        
        # 统计信息
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_subgraph_size": 0,
            "avg_processing_time_ms": 0,
            "errors": 0
        }
    
    # ========== MVP三个核心函数 ==========
    
    def get_anchor_nodes(self, query: str, query_parse: QueryParseResult) -> List[AnchorNode]:
        """
        获取锚点节点
        
        Args:
            query: 查询字符串
            query_parse: 查询解析结果
            
        Returns:
            锚点节点列表
        """
        anchors = []
        
        # 1. Graph节点匹配
        graph_anchors = self._get_graph_anchors(query_parse)
        anchors.extend(graph_anchors)
        
        # 2. Vector检索（如果有）- 第一版先用占位符
        if self.config["fallback_to_vector"] and len(anchors) < self.config["anchor_top_k"] // 2:
            vector_anchors = self._get_vector_anchors(query, query_parse)
            anchors.extend(vector_anchors)
        
        # 3. 最近上下文
        recent_anchors = self._get_recent_anchors()
        anchors.extend(recent_anchors)
        
        # 去重和排序
        unique_anchors = self._deduplicate_anchors(anchors)
        sorted_anchors = sorted(unique_anchors, key=lambda x: x.score, reverse=True)
        
        # 取top-k
        top_k = min(self.config["anchor_top_k"], len(sorted_anchors))
        result = sorted_anchors[:top_k]
        
        # 过滤低分锚点
        result = [a for a in result if a.score >= self.config["min_anchor_score"]]
        
        return result
    
    def expand_subgraph(self, anchors: List[AnchorNode]) -> Tuple[Set[str], Set[str]]:
        """
        扩展子图
        
        Args:
            anchors: 锚点节点列表
            
        Returns:
            (节点集合, 边集合)
        """
        if not anchors:
            return set(), set()
        
        # 初始化
        all_nodes = set()
        all_edges = set()
        node_scores = {}  # 节点ID -> 分数
        
        # 为每个锚点进行BFS扩展
        for anchor in anchors:
            nodes, edges, scores = self._bfs_expand(
                anchor.node_id, 
                max_depth=self.config["max_depth"]
            )
            
            # 合并结果
            all_nodes.update(nodes)
            all_edges.update(edges)
            
            # 更新节点分数（取最高分）
            for node_id, score in scores.items():
                if node_id not in node_scores or score > node_scores[node_id]:
                    node_scores[node_id] = score
        
        # 过滤低分节点
        filtered_nodes = set()
        for node_id in all_nodes:
            if node_scores.get(node_id, 0) >= self.config["min_node_score"]:
                filtered_nodes.add(node_id)
        
        # 过滤边（只保留节点之间的边）
        filtered_edges = set()
        for edge_key in all_edges:
            edge = self.global_graph.edges.get(edge_key)
            if edge and edge.active:
                # 检查边是否连接两个在节点集合中的节点
                if edge.src in filtered_nodes and edge.dst in filtered_nodes:
                    # 检查边权重阈值
                    if abs(edge.state.weight) >= self.config["edge_weight_threshold"]:
                        filtered_edges.add(edge_key)
        
        return filtered_nodes, filtered_edges
    
    def prune_subgraph(self, nodes: Set[str], edges: Set[str], anchors: List[AnchorNode]) -> Tuple[Set[str], Set[str]]:
        """
        子图裁剪
        
        Args:
            nodes: 节点集合
            edges: 边集合
            anchors: 锚点节点列表
            
        Returns:
            裁剪后的(节点集合, 边集合)
        """
        if not nodes:
            return set(), set()
        
        # 1. 计算节点重要性分数
        node_scores = self._compute_node_scores(nodes, edges, anchors)
        
        # 2. Top-K节点选择
        sorted_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)
        top_k = min(self.config["max_nodes"], len(sorted_nodes))
        selected_nodes = {node_id for node_id, _ in sorted_nodes[:top_k]}
        
        # 3. 连通性保证：至少包含所有锚点
        anchor_node_ids = {anchor.node_id for anchor in anchors}
        selected_nodes.update(anchor_node_ids)
        
        # 4. 边过滤：只保留selected_nodes之间的边
        selected_edges = set()
        for edge_key in edges:
            edge = self.global_graph.edges.get(edge_key)
            if edge and edge.active:
                if edge.src in selected_nodes and edge.dst in selected_nodes:
                    selected_edges.add(edge_key)
        
        # 5. 边数限制
        if len(selected_edges) > self.config["max_edges"]:
            # 按边权重排序
            edge_weights = []
            for edge_key in selected_edges:
                edge = self.global_graph.edges.get(edge_key)
                if edge:
                    weight = abs(edge.state.weight)
                    edge_weights.append((edge_key, weight))
            
            sorted_edges = sorted(edge_weights, key=lambda x: x[1], reverse=True)
            top_edges = min(self.config["max_edges"], len(sorted_edges))
            selected_edges = {edge_key for edge_key, _ in sorted_edges[:top_edges]}
        
        return selected_nodes, selected_edges
    
    # ========== 总体构建函数 ==========
    
    def build_active_subgraph(self, query: str) -> ActiveSubgraph:
        """
        构建激活子图 - 总体函数（必须实现）
        
        Args:
            query: 查询字符串
            
        Returns:
            激活子图
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(query)
            if self.config["cache_enabled"] and cache_key in self.cache:
                cached_subgraph, cached_time = self.cache[cache_key]
                # 检查缓存是否过期
                if time.time() - cached_time < self.config["cache_ttl_seconds"]:
                    self.stats["cache_hits"] += 1
                    return cached_subgraph
            
            self.stats["cache_misses"] += 1
            
            # Step 1: Query解析（轻量）
            query_parse = self._parse_query(query)
            
            # Step 2: Anchor Nodes召回（关键）
            anchors = self.get_anchor_nodes(query, query_parse)
            
            # 错误控制：空锚点处理
            if not anchors and self.config["fallback_to_vector"]:
                # 回退机制
                anchors = self._fallback_anchors(query, query_parse)
            
            # Step 3: 子图扩展
            nodes, edges = self.expand_subgraph(anchors)
            
            # Step 4: 子图裁剪（非常关键）
            pruned_nodes, pruned_edges = self.prune_subgraph(nodes, edges, anchors)
            
            # 计算子图整体评分
            subgraph_score = self._compute_subgraph_score(pruned_nodes, pruned_edges, anchors)
            
            # 确定主要话题
            topic = self._determine_topic(pruned_nodes, query_parse)
            
            # 构建激活子图
            subgraph = ActiveSubgraph(
                nodes=pruned_nodes,
                edges=pruned_edges,
                score=subgraph_score,
                topic=topic,
                anchors=anchors,
                query=query,
                query_parse=query_parse,
                cache_key=cache_key
            )
            
            # 更新最近上下文
            self._update_recent_context(pruned_nodes)
            
            # 缓存结果
            if self.config["cache_enabled"]:
                self.cache[cache_key] = (subgraph, time.time())
                # 清理过期缓存
                self._clean_expired_cache()
            
            # 更新统计
            processing_time_ms = (time.time() - start_time) * 1000
            self.stats["avg_processing_time_ms"] = (
                self.stats["avg_processing_time_ms"] * (self.stats["total_queries"] - 1) + 
                processing_time_ms
            ) / self.stats["total_queries"]
            
            self.stats["avg_subgraph_size"] = (
                self.stats["avg_subgraph_size"] * (self.stats["total_queries"] - 1) + 
                len(pruned_nodes)
            ) / self.stats["total_queries"]
            
            return subgraph
            
        except Exception as e:
            self.stats["errors"] += 1
            print(f"构建激活子图失败: {e}")
            # 返回空子图
            return ActiveSubgraph(
                query=query,
                query_parse=QueryParseResult(),
                cache_key=self._generate_cache_key(query)
            )
    
    # ========== 核心算法实现 ==========
    
    def _parse_query(self, query: str) -> QueryParseResult:
        """
        Query解析（轻量）
        
        目标：找"锚点"，不是理解世界
        """
        result = QueryParseResult()
        
        # 简单关键词提取（改进版）
        query_lower = query.lower()
        
        # 提取话题（从查询中提取可能的话题词）
        # 查找可能的话题词（名词性词汇）
        import re
        
        # 中文话题模式：去除常见虚词后的连续词汇
        chinese_words = re.findall(r'[\u4e00-\u9fff]+', query)
        
        # 过滤常见虚词
        common_words = {"的", "了", "在", "和", "是", "有", "我", "你", "他", "她", "它", 
                       "关于", "讨论", "话题", "主题", "分析", "研究", "什么", "为什么",
                       "如何", "怎么", "建议", "应该", "可以", "可能", "这个", "那个"}
        
        # 提取关键词（长度>1且不是常见虚词）
        keywords = []
        for word in chinese_words:
            if len(word) > 1 and word not in common_words:
                keywords.append(word)
                
                # 如果是2-4个字的词，可能是一个话题
                if 2 <= len(word) <= 4:
                    result.topics.append(word)
        
        # 如果没有提取到话题，使用前几个关键词作为话题
        if not result.topics and keywords:
            result.topics = keywords[:2]
        
        # 实体就是关键词
        result.entities = keywords[:5]
        
        # 提取意图
        intent_keywords = {
            "analysis": ["分析", "研究", "调查", "评估", "探讨", "了解"],
            "question": ["什么", "为什么", "如何", "怎么", "?", "？", "吗", "呢"],
            "decision": ["决定", "选择", "应该", "建议", "推荐", "最好"],
            "comparison": ["比较", "对比", "vs", "versus", "哪个", "区别"]
        }
        
        for intent, keywords_list in intent_keywords.items():
            if any(keyword in query for keyword in keywords_list):
                result.intent = intent
                break
        else:
            result.intent = "general"
        
        # 提取关键词（所有重要词汇）
        result.keywords = keywords[:10]
        
        # 如果没有关键词，使用整个查询作为关键词（简单处理）
        if not result.keywords:
            # 分割查询为词汇
            words = query_lower.split()
            result.keywords = [w for w in words if len(w) > 1][:5]
        
        return result
    
    def _get_graph_anchors(self, query_parse: QueryParseResult) -> List[AnchorNode]:
        """从全局图中获取锚点节点"""
        anchors = []
        
        # 按名称匹配（支持部分匹配）
        for keyword in query_parse.keywords:
            # 尝试完全匹配
            matching_nodes = self.global_graph.find_nodes_by_name(keyword)
            
            # 如果没有完全匹配，尝试部分匹配
            if not matching_nodes:
                for node_id, node in self.global_graph.nodes.items():
                    # 检查关键词是否在节点名称中（部分匹配）
                    if keyword in node.name.lower():
                        matching_nodes.append(node)
                    
                    # 检查别名
                    for alias in node.aliases:
                        if keyword in alias.lower():
                            matching_nodes.append(node)
                            break
            
            # 去重
            seen_ids = set()
            unique_nodes = []
            for node in matching_nodes:
                if node.id not in seen_ids:
                    seen_ids.add(node.id)
                    unique_nodes.append(node)
            
            # 为每个匹配节点计算评分
            for node in unique_nodes:
                # 计算相关性（基于匹配程度）
                relevance = 0.0
                if keyword == node.name.lower():
                    relevance = 1.0  # 完全匹配
                elif keyword in node.name.lower():
                    # 部分匹配，根据匹配长度比例
                    relevance = len(keyword) / len(node.name)
                
                # 检查别名匹配
                for alias in node.aliases:
                    if keyword == alias.lower():
                        relevance = max(relevance, 0.8)  # 别名完全匹配
                    elif keyword in alias.lower():
                        relevance = max(relevance, len(keyword) / len(alias) * 0.6)
                
                # 计算评分
                score = self._compute_anchor_score(
                    node=node,
                    query_parse=query_parse,
                    source="graph"
                )
                
                # 根据相关性调整分数
                adjusted_score = score * (0.3 + 0.7 * relevance)
                
                if adjusted_score > 0:
                    anchor = AnchorNode(
                        node_id=node.id,
                        node=node,
                        score=adjusted_score,
                        source="graph",
                        relevance=relevance
                    )
                    anchors.append(anchor)
        
        return anchors
    
    def _get_vector_anchors(self, query: str, query_parse: QueryParseResult) -> List[AnchorNode]:
        """向量检索锚点（第一版先用占位符）"""
        # 第一版：使用基于名称的简单向量相似度
        anchors = []
        
        # 计算查询的简单向量（关键词频率）
        query_vector = {}
        for word in query_parse.keywords:
            query_vector[word] = query_vector.get(word, 0) + 1
        
        # 为每个节点计算相似度
        for node_id, node in self.global_graph.nodes.items():
            # 节点向量（名称中的关键词）
            node_vector = {}
            for word in node.name.lower().split():
                if len(word) > 2:
                    node_vector[word] = node_vector.get(word, 0) + 1
            
            # 添加别名
            for alias in node.aliases:
                for word in alias.lower().split():
                    if len(word) > 2:
                        node_vector[word] = node_vector.get(word, 0) + 1
            
            # 计算余弦相似度
            similarity = self._cosine_similarity(query_vector, node_vector)
            
            if similarity > 0.1:  # 阈值
                score = self._compute_anchor_score(
                    node=node,
                    query_parse=query_parse,
                    source="vector"
                )
                
                # 调整分数基于相似度
                adjusted_score = score * (0.5 + 0.5 * similarity)
                
                anchor = AnchorNode(
                    node_id=node_id,
                    node=node,
                    score=adjusted_score,
                    source="vector",
                    relevance=similarity
                )
                anchors.append(anchor)
        
        return anchors
    
    def _get_recent_anchors(self) -> List[AnchorNode]:
        """从最近上下文中获取锚点"""
        anchors = []
        current_time = time.time()
        
        for node_id, timestamp in self.recent_context:
            # 检查时间衰减（最近5分钟内）
            if current_time - timestamp < 300:  # 5分钟
                if node_id in self.global_graph.nodes:
                    node = self.global_graph.nodes[node_id]
                    
                    # 计算最近性分数（随时间衰减）
                    recency = max(0, 1 - (current_time - timestamp) / 300)
                    
                    anchor = AnchorNode(
                        node_id=node_id,
                        node=node,
                        score=recency * 0.5,  # 最近性占50%权重
                        source="recent",
                        relevance=recency
                    )
                    anchors.append(anchor)
        
        return anchors
    
    def _compute_anchor_score(self, node: Node, query_parse: QueryParseResult, source: str) -> float:
        """
        锚点评分函数（必须有）
        
        score = 0.5 * semantic_similarity + 0.3 * recency + 0.2 * node_degree
        """
        weights = self.config["anchor_score_weights"]
        
        # 1. 语义相关性（简化版）
        semantic_similarity = 0.0
        for keyword in query_parse.keywords:
            if keyword in node.name.lower():
                semantic_similarity += 0.3
            for alias in node.aliases:
                if keyword in alias.lower():
                    semantic_similarity += 0.2
        
        semantic_similarity = min(1.0, semantic_similarity)
        
        # 2. 最近性（基于节点最后更新时间）
        current_time = time.time()
        node_age = current_time - node.created_at
        recency = max(0, 1 - node_age / (365 * 24 * 3600))  # 一年衰减
        
        # 3. 节点度数
        node_degree = len(self.global_graph.node_edges.get(node.id, set()))
        normalized_degree = min(1.0, node_degree / 20)  # 假设最大20度
        
        # 计算总分
        score = (
            weights["semantic_similarity"] * semantic_similarity +
            weights["recency"] * recency +
            weights["node_degree"] * normalized_degree
        )
        
        return score
    
    def _bfs_expand(self, start_node_id: str, max_depth: int = 2) -> Tuple[Set[str], Set[str], Dict[str, float]]:
        """
        BFS扩展算法
        
        Args:
            start_node_id: 起始节点ID
            max_depth: 最大深度
            
        Returns:
            (节点集合, 边集合, 节点分数字典)
        """
        visited = set()
        nodes = set()
        edges = set()
        node_scores = {}
        
        queue = deque([(start_node_id, 0, 1.0)])  # (node_id, depth, path_score)
        
        while queue:
            node_id, depth, path_score = queue.popleft()
            
            if node_id in visited or depth > max_depth:
                continue
            
            visited.add(node_id)
            nodes.add(node_id)
            
            # 获取节点的边
            for edge_key in self.global_graph.node_edges.get(node_id, set()):
                edge = self.global_graph.edges.get(edge_key)
                if not edge or not edge.active:
                    continue
                
                # 检查边权重阈值
                if abs(edge.state.weight) < self.config["edge_weight_threshold"]:
                    continue
                
                edges.add(edge_key)
                
                # 确定邻居节点
                neighbor_id = edge.dst if edge.src == node_id else edge.src
                
                # 计算邻居节点分数
                neighbor_score = self._compute_expansion_score(edge, path_score)
                
                # 更新节点分数
                if neighbor_id not in node_scores or neighbor_score > node_scores[neighbor_id]:
                    node_scores[neighbor_id] = neighbor_score
                
                # 添加到队列（如果未访问且深度未超限）
                if neighbor_id not in visited and depth < max_depth:
                    queue.append((neighbor_id, depth + 1, neighbor_score))
        
        # 起始节点分数设为1.0
        node_scores[start_node_id] = 1.0
        
        return nodes, edges, node_scores
    
    def _compute_expansion_score(self, edge: Edge, path_score: float) -> float:
        """
        扩展评分（关键）
        
        node_score = edge.weight * 0.6 + edge.confidence * 0.2 + recency * 0.2
        """
        weights = self.config["expansion_score_weights"]
        
        # 边权重（归一化到[0, 1]）
        edge_weight = (edge.state.weight + 1) / 2  # 从[-1,1]映射到[0,1]
        
        # 边置信度
        edge_confidence = edge.state.confidence
        
        # 最近性（基于边最后更新时间）
        current_time = time.time()
        edge_age = current_time - edge.state.last_updated
        recency = max(0, 1 - edge_age / (30 * 24 * 3600))  # 一个月衰减
        
        # 计算分数
        score = (
            weights["edge_weight"] * edge_weight +
            weights["edge_confidence"] * edge_confidence +
            weights["recency"] * recency
        )
        
        # 乘以路径分数（衰减）
        return score * path_score * 0.8  # 每跳衰减20%
    
    def _compute_node_scores(self, nodes: Set[str], edges: Set[str], anchors: List[AnchorNode]) -> Dict[str, float]:
        """计算节点重要性分数"""
        node_scores = {}
        
        # 锚点节点高分
        anchor_ids = {anchor.node_id for anchor in anchors}
        for node_id in nodes:
            score = 0.0
            
            # 基础分数
            if node_id in anchor_ids:
                score += 2.0  # 锚点节点加分
            
            # 节点度数（在子图中）
            degree = 0
            for edge_key in edges:
                edge = self.global_graph.edges.get(edge_key)
                if edge and (edge.src == node_id or edge.dst == node_id):
                    degree += 1
            
            score += degree * 0.1
            
            # 节点类型权重
            node = self.global_graph.nodes.get(node_id)
            if node:
                if node.type == NodeType.USER:
                    score += 0.5
                elif node.type == NodeType.ENTITY:
                    score += 0.3
            
            node_scores[node_id] = score
        
        return node_scores
    
    def _compute_subgraph_score(self, nodes: Set[str], edges: Set[str], anchors: List[AnchorNode]) -> float:
        """
        子图整体评分
        
        subgraph_score = Σ node_score + Σ edge.weight
        """
        score = 0.0
        
        # 节点分数
        node_scores = self._compute_node_scores(nodes, edges, anchors)
        score += sum(node_scores.values())
        
        # 边权重
        edge_weight_sum = 0.0
        for edge_key in edges:
            edge = self.global_graph.edges.get(edge_key)
            if edge:
                edge_weight_sum += abs(edge.state.weight)
        
        score += edge_weight_sum
        
        # 归一化
        normalized_score = score / (len(nodes) + len(edges) + 1)
        
        return min(10.0, normalized_score * 10)  # 映射到[0, 10]范围
    
    # ========== 工具函数 ==========
    
    def _deduplicate_anchors(self, anchors: List[AnchorNode]) -> List[AnchorNode]:
        """去重锚点节点（按节点ID）"""
        seen = set()
        unique_anchors = []
        
        for anchor in anchors:
            if anchor.node_id not in seen:
                seen.add(anchor.node_id)
                unique_anchors.append(anchor)
        
        return unique_anchors
    
    def _determine_topic(self, nodes: Set[str], query_parse: QueryParseResult) -> str:
        """确定主要话题"""
        if query_parse.topics:
            return query_parse.topics[0]
        
        # 从节点中找最常见的词
        word_count = defaultdict(int)
        for node_id in nodes:
            node = self.global_graph.nodes.get(node_id)
            if node:
                for word in node.name.split():
                    if len(word) > 2:
                        word_count[word] += 1
        
        if word_count:
            most_common = max(word_count.items(), key=lambda x: x[1])
            return most_common[0]
        
        return query_parse.keywords[0] if query_parse.keywords else "general"
    
    def _generate_cache_key(self, query: str) -> str:
        """生成缓存键：hash(topic + intent)"""
        query_parse = self._parse_query(query)
        cache_string = f"{','.join(query_parse.topics)}:{query_parse.intent}"
        return hashlib.md5(cache_string.encode()).hexdigest()[:8]
    
    def _update_recent_context(self, nodes: Set[str]):
        """更新最近上下文"""
        current_time = time.time()
        
        for node_id in nodes:
            # 添加到最近上下文
            self.recent_context.append((node_id, current_time))
        
        # 保持最近上下文大小（最多50个）
        if len(self.recent_context) > 50:
            self.recent_context = self.recent_context[-50:]
    
    def _clean_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, (_, cached_time) in self.cache.items():
            if current_time - cached_time > self.config["cache_ttl_seconds"]:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.cache[key]
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """计算余弦相似度"""
        # 获取所有单词
        all_words = set(vec1.keys()) | set(vec2.keys())
        
        # 计算点积和模长
        dot_product = 0.0
        norm1 = 0.0
        norm2 = 0.0
        
        for word in all_words:
            v1 = vec1.get(word, 0.0)
            v2 = vec2.get(word, 0.0)
            
            dot_product += v1 * v2
            norm1 += v1 * v1
            norm2 += v2 * v2
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (math.sqrt(norm1) * math.sqrt(norm2))
    
    def _fallback_anchors(self, query: str, query_parse: QueryParseResult) -> List[AnchorNode]:
        """回退机制：无锚点时使用"""
        anchors = []
        
        # 使用全局图中度数最高的节点作为回退
        all_nodes = list(self.global_graph.nodes.values())
        sorted_nodes = sorted(
            all_nodes, 
            key=lambda n: len(self.global_graph.node_edges.get(n.id, set())),
            reverse=True
        )
        
        for i, node in enumerate(sorted_nodes[:3]):  # 取前3个
            score = 0.5 - i * 0.1  # 递减分数
            
            anchor = AnchorNode(
                node_id=node.id,
                node=node,
                score=score,
                source="fallback",
                relevance=0.1
            )
            anchors.append(anchor)
        
        return anchors
    
    # ========== 上下文构建 ==========
    
    def build_context_text(self, subgraph: ActiveSubgraph) -> str:
        """
        构建结构化上下文
        
        输出给LLM的不是"图"，而是结构化上下文：
        [事实] 用户 → 喜欢 → 日本房产 (0.8)
        [关系] 日本房产 → 位于 → 大阪
        [历史] 用户之前提到投资回报问题
        
        必须做：Graph → Text Projection
        """
        if not subgraph.nodes:
            return "无相关上下文信息。"
        
        context_parts = []
        
        # 1. 事实部分（用户相关）
        user_facts = []
        for edge_key in subgraph.edges:
            edge = self.global_graph.edges.get(edge_key)
            if edge and edge.src in subgraph.nodes and edge.dst in subgraph.nodes:
                src_node = self.global_graph.nodes.get(edge.src)
                dst_node = self.global_graph.nodes.get(edge.dst)
                
                if src_node and dst_node:
                    # 检查是否是用户相关事实
                    if src_node.type == NodeType.USER or dst_node.type == NodeType.USER:
                        fact = f"{src_node.name} → {edge.type.value} → {dst_node.name} ({edge.state.weight:.2f})"
                        user_facts.append(fact)
        
        if user_facts:
            context_parts.append("[事实]")
            context_parts.extend(user_facts[:5])  # 最多5个事实
        
        # 2. 关系部分（非用户相关）
        relations = []
        for edge_key in subgraph.edges:
            edge = self.global_graph.edges.get(edge_key)
            if edge and edge.src in subgraph.nodes and edge.dst in subgraph.nodes:
                src_node = self.global_graph.nodes.get(edge.src)
                dst_node = self.global_graph.nodes.get(edge.dst)
                
                if src_node and dst_node:
                    # 排除用户相关事实（已经在第一部分）
                    if src_node.type != NodeType.USER and dst_node.type != NodeType.USER:
                        relation = f"{src_node.name} → {edge.type.value} → {dst_node.name}"
                        relations.append(relation)
        
        if relations:
            context_parts.append("[关系]")
            context_parts.extend(relations[:5])  # 最多5个关系
        
        # 3. 历史部分（最近上下文）
        if self.recent_context:
            recent_nodes = []
            for node_id, timestamp in self.recent_context[-3:]:  # 最近3个
                if node_id in self.global_graph.nodes:
                    node = self.global_graph.nodes[node_id]
                    recent_nodes.append(node.name)
            
            if recent_nodes:
                context_parts.append(f"[历史] 最近提到的: {', '.join(recent_nodes)}")
        
        # 4. 话题总结
        context_parts.append(f"[话题] 当前讨论: {subgraph.topic}")
        
        # 5. 锚点信息
        if subgraph.anchors:
            anchor_names = [anchor.node.name for anchor in subgraph.anchors[:3]]
            context_parts.append(f"[锚点] 相关概念: {', '.join(anchor_names)}")
        
        # 如果没有内容，返回默认信息
        if not context_parts:
            return f"当前讨论话题: {subgraph.topic}"
        
        return "\n".join(context_parts)
