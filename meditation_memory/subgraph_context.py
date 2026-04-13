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

        return self._build_context_result(subgraph, matched_entities, extraction)

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
            result = self._build_context_result(
                self._session.cached_subgraph,
                list(self._session.cached_entities),
                extraction,
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

            result = self._build_context_result(
                new_subgraph,
                matched_entities,
                extraction,
            )
            self._session.update_with_extraction(extraction, new_subgraph=new_subgraph)
            return result
        else:
            # 主题未变化：使用缓存，但补充新实体
            result = self._build_context_result(
                self._session.cached_subgraph,
                list(self._session.cached_entities),
                extraction,
            )
            self._session.update_with_extraction(extraction, new_subgraph=None)
            return result

    def _build_context_result(
        self,
        subgraph: Dict[str, Any],
        matched_entities: List[str],
        extraction: ExtractionResult,
    ) -> "ContextResult":
        prepared = self._prepare_subgraph_for_prompt(subgraph)
        context_text = self._format_subgraph_as_context(prepared)
        return ContextResult(
            context_text=context_text,
            subgraph=prepared,
            matched_entities=matched_entities,
            extraction=extraction,
        )

    def _prepare_subgraph_for_prompt(self, subgraph: Dict[str, Any]) -> Dict[str, Any]:
        """对检索子图做预算化裁剪，避免一次注入过多实体和关系。"""
        nodes = self._sanitize_nodes(subgraph.get("nodes", []))
        if not nodes:
            return {"nodes": [], "edges": []}

        budget_chars = max(200, self._config.max_context_chars)
        node_budget = max(4, min(self._config.max_nodes, budget_chars // 90))
        kept_nodes = nodes[:node_budget]
        kept_names = {node["name"] for node in kept_nodes}

        edges = self._sanitize_edges(subgraph.get("edges", []), kept_names)
        edge_budget = max(4, min(self._config.max_edges, budget_chars // 70))
        kept_edges = edges[:edge_budget]

        return {"nodes": kept_nodes, "edges": kept_edges}

    def _sanitize_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: Dict[str, Dict[str, Any]] = {}
        for node in nodes:
            name = (node.get("name") or "").strip()
            if not name or name.startswith("[META]"):
                continue
            if node.get("entity_type") == "meta_knowledge":
                continue

            mention_count = node.get("mention_count", 0) or 0
            current = seen.get(name)
            if current is None or mention_count > (current.get("mention_count", 0) or 0):
                seen[name] = {
                    "name": name,
                    "entity_type": node.get("entity_type", "其他") or "其他",
                    "mention_count": mention_count,
                }

        return sorted(
            seen.values(),
            key=lambda item: (-(item.get("mention_count", 0) or 0), len(item["name"]), item["name"]),
        )

    def _sanitize_edges(
        self,
        edges: List[Dict[str, Any]],
        kept_names: Set[str],
    ) -> List[Dict[str, Any]]:
        seen = set()
        edge_records: List[Tuple[int, Dict[str, Any]]] = []
        name_rank = {node_name: idx for idx, node_name in enumerate(sorted(kept_names))}

        for edge in edges:
            src = (edge.get("source") or "").strip()
            tgt = (edge.get("target") or "").strip()
            if not src or not tgt:
                continue
            if src not in kept_names or tgt not in kept_names:
                continue
            if "[META]" in src or "[META]" in tgt:
                continue

            relation_type = edge.get("relation_type", "related_to") or "related_to"
            key = (src, tgt, relation_type)
            if key in seen:
                continue
            seen.add(key)

            rank = name_rank.get(src, 999) + name_rank.get(tgt, 999)
            edge_records.append(
                (
                    rank,
                    {
                        "source": src,
                        "target": tgt,
                        "relation_type": relation_type,
                    },
                )
            )

        edge_records.sort(key=lambda item: (item[0], item[1]["source"], item[1]["target"]))
        return [item[1] for item in edge_records]

    def _format_subgraph_as_context(self, subgraph: Dict[str, Any]) -> str:
        """将子图数据格式化为预算化自然语言上下文。"""
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])

        if not nodes and not edges:
            return ""

        type_labels = {
            "person": "人物",
            "place": "地点",
            "concept": "概念",
            "event": "事件",
            "object": "物品",
            "organization": "组织",
            "intent": "意图",
        }

        budget = max(200, self._config.max_context_chars)
        current_length = 0
        lines: List[str] = []

        def append_line(line: str) -> bool:
            nonlocal current_length
            extra = len(line) + (1 if lines else 0)
            if current_length + extra > budget:
                return False
            lines.append(line)
            current_length += extra
            return True

        grouped: Dict[str, List[str]] = {}
        for node in nodes:
            grouped.setdefault(node.get("entity_type", "其他"), []).append(node.get("name", ""))

        if grouped and append_line("### 已知实体"):
            for entity_type, names in grouped.items():
                unique_names: List[str] = []
                for name in names:
                    if name and name not in unique_names:
                        unique_names.append(name)
                label = type_labels.get(entity_type, entity_type)
                if not append_line(f"- {label}：{'、'.join(unique_names)}"):
                    break

        if edges:
            append_line("")
            if append_line("### 已知关系"):
                for edge in edges:
                    readable = self._relation_to_readable(edge.get("relation_type", "related_to"))
                    if not append_line(f"- {edge.get('source', '?')} {readable} {edge.get('target', '?')}"):
                        break

        if current_length >= budget and lines:
            suffix = "\n..."
            if len(lines[-1]) + len(suffix) <= budget:
                lines[-1] = f"{lines[-1]}{suffix}"

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
            "aims_at": "目标是",
            "achieves": "实现",
            "precedes": "先于",
            "prevents": "阻止",
            "supports": "支持",
            "opposes": "反对",
            "contradicts": "与…矛盾",
            "leads_to": "引向",
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
