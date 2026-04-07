"""
动态子图上下文构建模块

根据当前用户输入，从 Neo4j 图数据库中检索最相关的子图（实体 + 关系），
将其格式化为结构化的上下文文本，注入到 LLM 对话的系统提示词中。

支持两种工作模式：
  1. 传统模式（每轮对话触发）— build_context() 和 build_system_prompt()
  2. 会话模式（会话级缓存 + 主题变化刷新）— start_session(), get_context(), end_session()
"""

from __future__ import annotations

import re
import math
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from difflib import SequenceMatcher

from .config import SubgraphConfig
from .entity_extractor import EntityExtractor, ExtractionResult
from .graph_store import GraphStore


class SessionContext:
    """
    会话级上下文缓存管理器
    
    在一个会话中维护：
      - 初始子图（会话开始时检索）
      - 缓存的实体集合
      - 对话历史中提取的所有实体
    
    在以下情况刷新子图：
      - 检测到主题变化（当前消息实体与缓存实体重叠度低于阈值）
      - 出现了缓存中不存在的新实体
    """

    def __init__(
        self,
        initial_context: ContextResult,
        config: SubgraphConfig,
    ):
        """
        初始化会话上下文
        
        Args:
            initial_context: 会话开始时的初始上下文
            config: 子图配置
        """
        self._initial_context = initial_context
        self._config = config
        
        # 缓存的子图和实体集合
        self._cached_subgraph = initial_context.subgraph
        self._cached_entities: Set[str] = set(initial_context.matched_entities)
        
        # 会话中收集的所有实体和关系（用于会话结束时写入）
        self._session_entities: List[str] = list(initial_context.matched_entities)
        self._session_extractions: List[ExtractionResult] = []
        if initial_context.extraction:
            self._session_extractions.append(initial_context.extraction)

    @property
    def cached_subgraph(self) -> Dict[str, Any]:
        """获取当前缓存的子图"""
        return self._cached_subgraph

    @property
    def cached_entities(self) -> Set[str]:
        """获取当前缓存的实体集合"""
        return self._cached_entities.copy()

    @property
    def session_extractions(self) -> List[ExtractionResult]:
        """获取会话中收集的所有抽取结果"""
        return self._session_extractions.copy()

    def update_with_extraction(
        self,
        extraction: ExtractionResult,
        new_subgraph: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        使用新的抽取结果更新会话上下文
        
        Args:
            extraction: 新的抽取结果
            new_subgraph: 如果主题变化，传入新检索的子图；否则为 None
        """
        # 收集本轮提取的实体
        new_entity_names = [e.name for e in extraction.entities]
        self._session_entities.extend(new_entity_names)
        self._session_extractions.append(extraction)
        
        # 如果主题变化，更新缓存
        if new_subgraph is not None:
            self._cached_subgraph = new_subgraph
            self._cached_entities = set(new_entity_names)
        else:
            # 否则，补充新实体到缓存
            self._cached_entities.update(new_entity_names)

    def calculate_entity_overlap(self, new_entities: List[str]) -> float:
        """
        计算新实体与缓存实体的重叠度
        
        重叠度 = 交集大小 / max(缓存实体数, 新实体数)
        
        Args:
            new_entities: 新抽取的实体名称列表
            
        Returns:
            重叠度（0.0 - 1.0）
        """
        if not self._cached_entities or not new_entities:
            return 0.0
        
        new_set = set(new_entities)
        intersection = len(self._cached_entities & new_set)
        denominator = max(len(self._cached_entities), len(new_set))
        
        return intersection / denominator if denominator > 0 else 0.0


class SubgraphContext:
    """
    动态子图上下文构建器

    工作流程（传统模式）：
      1. 从用户输入中抽取关键实体
      2. 在 Neo4j 中检索这些实体的邻域子图
      3. 将子图格式化为自然语言上下文
      4. 返回可直接注入提示词的文本
    
    工作流程（会话模式）：
      1. 会话开始时（start_session）— 根据第一条消息检索初始子图
      2. 会话过程中（get_context）— 返回缓存子图，检测主题变化时刷新
      3. 会话结束时（end_session）— 返回会话中收集的所有实体和关系
    """

    def __init__(
        self,
        graph_store: GraphStore,
        extractor: EntityExtractor,
        config: Optional[SubgraphConfig] = None,
    ):
        self._store = graph_store
        self._extractor = extractor
        self._config = config or SubgraphConfig()
        
        # 会话级缓存
        self._session: Optional[SessionContext] = None

    # ========== 传统模式（每轮对话触发）==========

    def build_context(self, user_input: str, use_llm: bool = True) -> ContextResult:
        """
        根据用户输入构建动态上下文。

        Args:
            user_input: 当前用户的输入文本
            use_llm: 实体抽取是否使用 LLM

        Returns:
            ContextResult 包含格式化的上下文文本和元数据
        """
        # 第一步：从用户输入中抽取实体
        extraction = self._extractor.extract(user_input, use_llm=use_llm)
        entity_names = [e.name for e in extraction.entities]

        if not entity_names:
            return ContextResult(
                context_text="",
                subgraph={"nodes": [], "edges": []},
                matched_entities=[],
                extraction=extraction,
            )

        # 第二步：在图数据库中搜索匹配的实体
        matched_entities = self._search_matching_entities(entity_names)

        if not matched_entities:
            return ContextResult(
                context_text="",
                subgraph={"nodes": [], "edges": []},
                matched_entities=[],
                extraction=extraction,
            )

        # 第三步：检索子图
        subgraph = self._store.get_subgraph_by_entities(
            entity_names=matched_entities,
            max_depth=self._config.max_depth,
            max_nodes=self._config.max_nodes,
            max_edges=self._config.max_edges,
        )

        # 第四步：格式化为上下文文本
        context_text = self._format_subgraph_as_context(subgraph)

        # 截断到最大长度
        if len(context_text) > self._config.max_context_chars:
            context_text = context_text[: self._config.max_context_chars] + "\n..."

        return ContextResult(
            context_text=context_text,
            subgraph=subgraph,
            matched_entities=matched_entities,
            extraction=extraction,
        )

    def build_system_prompt(
        self,
        user_input: str,
        base_system_prompt: str = "",
        use_llm: bool = True,
    ) -> str:
        """
        构建包含动态子图上下文的完整系统提示词。

        Args:
            user_input: 用户输入
            base_system_prompt: 基础系统提示词
            use_llm: 实体抽取是否使用 LLM

        Returns:
            增强后的系统提示词
        """
        ctx = self.build_context(user_input, use_llm=use_llm)

        if not ctx.context_text:
            return base_system_prompt

        enhanced_prompt = base_system_prompt
        if enhanced_prompt:
            enhanced_prompt += "\n\n"

        enhanced_prompt += (
            "## 相关记忆上下文\n"
            "以下是从长期记忆图谱中检索到的与当前对话相关的信息，"
            "请在回答时参考这些背景知识：\n\n"
            f"{ctx.context_text}"
        )

        return enhanced_prompt

    # ========== 会话模式（会话级缓存 + 主题变化刷新）==========

    def start_session(self, initial_message: str, use_llm: bool = True) -> ContextResult:
        """
        开始一个新的对话会话。
        
        根据初始消息从图数据库检索相关子图，建立会话级缓存。
        
        Args:
            initial_message: 会话的第一条消息
            use_llm: 实体抽取是否使用 LLM
            
        Returns:
            初始上下文（ContextResult）
        """
        if not self._config.session_cache_enabled:
            # 如果禁用会话缓存，直接使用传统模式
            return self.build_context(initial_message, use_llm=use_llm)
        
        # 构建初始上下文
        initial_context = self.build_context(initial_message, use_llm=use_llm)
        
        # 创建会话缓存
        self._session = SessionContext(initial_context, self._config)
        
        return initial_context

    def get_context(self, user_input: str, use_llm: bool = True) -> ContextResult:
        """
        在会话过程中获取上下文。
        
        返回当前缓存的子图上下文。如果检测到主题变化，则重新检索子图。
        
        Args:
            user_input: 当前用户输入
            use_llm: 实体抽取是否使用 LLM
            
        Returns:
            上下文（可能是缓存的，也可能是新检索的）
        """
        if not self._config.session_cache_enabled or self._session is None:
            # 如果禁用会话缓存或未开始会话，直接使用传统模式
            return self.build_context(user_input, use_llm=use_llm)
        
        # 抽取当前消息的实体
        extraction = self._extractor.extract(user_input, use_llm=use_llm)
        current_entities = [e.name for e in extraction.entities]
        
        if not current_entities:
            # 无新实体，返回缓存上下文
            context_text = self._format_subgraph_as_context(self._session.cached_subgraph)
            if len(context_text) > self._config.max_context_chars:
                context_text = context_text[: self._config.max_context_chars] + "\n..."
            
            result = ContextResult(
                context_text=context_text,
                subgraph=self._session.cached_subgraph,
                matched_entities=list(self._session.cached_entities),
                extraction=extraction,
            )
            self._session.update_with_extraction(extraction, new_subgraph=None)
            return result
        
        # 计算实体重叠度，判断是否主题变化
        overlap = self._session.calculate_entity_overlap(current_entities)
        
        if overlap < self._config.topic_shift_threshold:
            # 主题变化：重新检索子图
            matched_entities = self._search_matching_entities(current_entities)
            
            if matched_entities:
                new_subgraph = self._store.get_subgraph_by_entities(
                    entity_names=matched_entities,
                    max_depth=self._config.max_depth,
                    max_nodes=self._config.max_nodes,
                    max_edges=self._config.max_edges,
                )
            else:
                new_subgraph = {"nodes": [], "edges": []}
            
            context_text = self._format_subgraph_as_context(new_subgraph)
            if len(context_text) > self._config.max_context_chars:
                context_text = context_text[: self._config.max_context_chars] + "\n..."
            
            result = ContextResult(
                context_text=context_text,
                subgraph=new_subgraph,
                matched_entities=matched_entities,
                extraction=extraction,
            )
            self._session.update_with_extraction(extraction, new_subgraph=new_subgraph)
            return result
        else:
            # 主题未变化：使用缓存，但补充新实体
            context_text = self._format_subgraph_as_context(self._session.cached_subgraph)
            if len(context_text) > self._config.max_context_chars:
                context_text = context_text[: self._config.max_context_chars] + "\n..."
            
            result = ContextResult(
                context_text=context_text,
                subgraph=self._session.cached_subgraph,
                matched_entities=list(self._session.cached_entities),
                extraction=extraction,
            )
            self._session.update_with_extraction(extraction, new_subgraph=None)
            return result

    def end_session(self) -> List[ExtractionResult]:
        """
        结束会话，返回会话中收集的所有抽取结果。
        
        这些结果可以由上层调用者（如 MemorySystem）写入图数据库。
        
        Returns:
            会话中收集的所有 ExtractionResult 列表
        """
        if self._session is None:
            return []
        
        extractions = self._session.session_extractions
        self._session = None
        return extractions

    # ========== 内部方法 ==========

    def _search_matching_entities(self, entity_names: List[str]) -> List[str]:
        """在图数据库中搜索匹配的实体名称，新增语义搜索兜底（P0-4）"""
        matched = []
        
        for name in entity_names:
            # 1. 精确匹配
            entity = self._store.find_entity(name)
            if entity:
                matched.append(name)
                continue

            # 2. 模糊搜索
            results = self._store.search_entities(name, limit=3)
            for r in results:
                if r["name"] not in matched:
                    matched.append(r["name"])

            # 如果通过精确或模糊搜索找到了匹配，继续下一个实体
            if any(m == name for m in matched):
                continue
                
            # 3. 语义搜索兜底（仅当前面的搜索失败时）
            semantic_matches = self._semantic_fallback_search(name, limit=2)
            for match, score in semantic_matches:
                if match not in matched:
                    matched.append(match)
                    logger = logging.getLogger(__name__)
                    logger.info(f"语义兜底匹配: '{name}' → '{match}' (score={score:.3f})")

            if len(matched) >= self._config.top_k_entities:
                break

        return matched[: self._config.top_k_entities]

    def _semantic_fallback_search(self, query: str, limit: int = 3) -> List[Tuple[str, float]]:
        """
        语义搜索兜底：当精确匹配和模糊搜索失败时，
        使用文本相似度从数据库中查找语义相关的实体。
        
        返回: [(实体名, 相似度), ...]，按相似度降序排列
        """
        try:
            # 从数据库中获取候选实体（限制数量以避免性能问题）
            candidate_pool = self._fetch_candidate_entities(limit=300)
            if not candidate_pool:
                return []
            
            # 计算查询与每个候选实体的相似度
            scored_candidates = []
            query_lower = query.lower()
            
            for candidate in candidate_pool:
                cand_lower = candidate.lower()
                
                # 使用多种相似度计算方法
                # 1. Jaccard 相似度（集合重叠）
                query_set = set(query_lower)
                cand_set = set(cand_lower)
                if query_set and cand_set:
                    jaccard = len(query_set & cand_set) / len(query_set | cand_set)
                else:
                    jaccard = 0.0
                
                # 2. 序列相似度（编辑距离归一化）
                seq_similarity = SequenceMatcher(None, query_lower, cand_lower).ratio()
                
                # 3. 字符重叠度（长字符串的通用相似度）
                char_overlap = len(set(query_lower) & set(cand_lower)) / max(len(set(query_lower)), 1)
                
                # 加权综合相似度
                final_score = 0.5 * seq_similarity + 0.3 * jaccard + 0.2 * char_overlap
                
                # 如果候选实体包含查询词（或查询词包含候选实体），提高分数
                if query_lower in cand_lower or cand_lower in query_lower:
                    final_score = max(final_score, 0.7)
                
                if final_score >= 0.3:  # 相似度阈值
                    scored_candidates.append((candidate, final_score))
            
            # 按相似度降序排序
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            
            return scored_candidates[:limit]
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"语义兜底搜索失败: {e}")
            return []

    def _fetch_candidate_entities(self, limit: int = 300) -> List[str]:
        """从数据库获取候选实体名称"""
        query = """
        MATCH (e:Entity)
        WHERE NOT e:Archived
        RETURN e.name
        LIMIT $limit
        """
        try:
            with self._store.driver.session(database=self._store._config.database) as session:
                result = session.run(query, limit=limit)
                return [record["e.name"] for record in result]
        except Exception:
            return []


    def _format_subgraph_as_context(self, subgraph: Dict[str, Any]) -> str:
        """将子图数据格式化为自然语言上下文"""
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])

        if not nodes and not edges:
            return ""

        # 过滤噪声：META 元知识节点和占位符
        nodes = [
            n for n in nodes
            if n.get("entity_type") != "meta_knowledge"
            and not n.get("name", "").startswith("[META]")
            and n.get("name", "")
        ]
        edges = [
            e for e in edges
            if "[META]" not in e.get("source", "")
            and "[META]" not in e.get("target", "")
        ]

        lines: List[str] = []

        # 格式化实体信息
        if nodes:
            lines.append("### 已知实体")
            # 按类型分组
            type_groups: Dict[str, List[str]] = {}
            for node in nodes:
                t = node.get("entity_type", "其他")
                type_groups.setdefault(t, []).append(node.get("name", ""))

            type_labels = {
                "person": "人物",
                "place": "地点",
                "concept": "概念",
                "event": "事件",
                "object": "物品",
                "organization": "组织",
            }
            for etype, names in type_groups.items():
                label = type_labels.get(etype, etype)
                lines.append(f"- {label}：{', '.join(names)}")

        # 格式化关系信息
        if edges:
            lines.append("")
            lines.append("### 已知关系")
            for edge in edges:
                src = edge.get("source", "?")
                tgt = edge.get("target", "?")
                rtype = edge.get("relation_type", "related_to")
                # 将关系类型转为可读描述
                readable = self._relation_to_readable(rtype)
                lines.append(f"- {src} {readable} {tgt}")

        return "\n".join(lines)

    @staticmethod
    def _relation_to_readable(relation_type: str) -> str:
        """将关系类型转为中文可读描述"""
        mapping = {
            "related_to": "与…相关",
            "works_at": "工作于",
            "located_in": "位于",
            "part_of": "属于",
            "causes": "导致",
            "created_by": "由…创建",
            "belongs_to": "属于",
            "knows": "认识",
            "uses": "使用",
            "contains": "包含",
            "depends_on": "依赖于",
        }
        return mapping.get(relation_type, f"[{relation_type}]")


class ContextResult:
    """上下文构建结果"""

    def __init__(
        self,
        context_text: str,
        subgraph: Dict[str, Any],
        matched_entities: List[str],
        extraction: Optional[ExtractionResult] = None,
    ):
        self.context_text = context_text
        self.subgraph = subgraph
        self.matched_entities = matched_entities
        self.extraction = extraction

    def to_dict(self) -> Dict[str, Any]:
        """转为字典"""
        return {
            "context_text": self.context_text,
            "subgraph": self.subgraph,
            "matched_entities": self.matched_entities,
            "entity_count": len(self.subgraph.get("nodes", [])),
            "edge_count": len(self.subgraph.get("edges", [])),
        }
