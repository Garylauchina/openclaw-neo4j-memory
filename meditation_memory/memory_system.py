"""
记忆系统主入口

MemorySystem 是对外暴露的统一接口，整合了：
  - 实体抽取（EntityExtractor）
  - 图数据库存储（GraphStore）
  - 动态子图上下文构建（SubgraphContext）

上层调用者（如 OpenClaw 插件）只需通过此类即可完成记忆的写入和检索。

支持两种工作模式：
  1. 传统模式（每轮对话触发）— ingest(), retrieve_context(), build_prompt()
  2. 会话模式（会话级缓存 + 主题变化刷新）— start_session(), process_message(), end_session()
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from .config import MemoryConfig
from .entity_extractor import Entity, EntityExtractor, ExtractionResult
from .graph_store import GraphStore
from .subgraph_context import ContextResult, SubgraphContext


class MemorySystem:
    """
    记忆系统统一接口

    使用方式（传统模式）：
        config = MemoryConfig()
        memory = MemorySystem(config)
        memory.init()

        # 写入记忆
        memory.ingest("张三在北京大学学习人工智能")

        # 检索上下文
        result = memory.retrieve_context("张三最近在做什么？")
        print(result.context_text)

        # 构建增强提示词
        prompt = memory.build_prompt("张三最近在做什么？", base_prompt="你是一个助手")

        memory.close()
    
    使用方式（会话模式）：
        config = MemoryConfig()
        memory = MemorySystem(config)
        memory.init()

        # 开始会话
        initial_ctx = memory.start_session("用户第一条消息")

        # 处理会话中的消息
        ctx1 = memory.process_message("用户第二条消息")
        ctx2 = memory.process_message("用户第三条消息")

        # 结束会话，将对话内容写入记忆
        memory.end_session("完整的对话文本")

        memory.close()
    """

    def __init__(self, config: Optional[MemoryConfig] = None):
        self._config = config or MemoryConfig()
        self._store = GraphStore(self._config.neo4j)
        self._extractor = EntityExtractor(self._config.llm)
        self._context_builder = SubgraphContext(
            graph_store=self._store,
            extractor=self._extractor,
            config=self._config.subgraph,
        )
        self._initialized = False

    # ========== 生命周期 ==========

    def init(self):
        """初始化记忆系统（创建索引等）"""
        self._store.init_schema()
        self._initialized = True

    def close(self):
        """关闭记忆系统，释放资源"""
        self._store.close()
        self._initialized = False

    def is_connected(self) -> bool:
        """检查 Neo4j 连接是否正常"""
        return self._store.verify_connectivity()

    # ========== 传统模式：写入接口 ==========

    def _apply_write_guard(self, extraction: ExtractionResult, text: str) -> ExtractionResult:
        """为实体附加最小可信写入防护元数据。"""
        cfg = self._config.write_guard
        if not cfg.enabled:
            return extraction

        source_context = (text or extraction.raw_text or "").strip()
        source_id = hashlib.sha1(source_context.encode("utf-8")).hexdigest()[:12] if source_context else "direct"

        guarded_entities: List[Entity] = []
        for entity in extraction.entities:
            props = dict(entity.properties or {})
            props.setdefault("source_context", source_context[:500])
            props.setdefault("source_id", source_id)
            evidence_count = int(props.get("evidence_count", 1) or 1)
            source_count = int(props.get("source_count", 1) or 1)
            belief_strength = float(props.get("belief_strength", 0.5) or 0.5)
            knowledge_state = "stable"
            if (
                belief_strength < cfg.stable_belief_strength_threshold
                or evidence_count < cfg.stable_min_evidence_count
                or source_count < cfg.stable_min_source_count
            ):
                knowledge_state = "hypothesis"

            props["evidence_count"] = evidence_count
            props["source_count"] = source_count
            props["knowledge_state"] = knowledge_state

            guarded_entities.append(
                Entity(
                    name=entity.name,
                    entity_type=entity.entity_type,
                    properties=props,
                )
            )

        extraction.entities = guarded_entities
        return extraction

    def ingest(self, text: str, use_llm: bool = True) -> IngestResult:
        """
        从文本中抽取实体和关系，写入图数据库。

        这是记忆写入的核心方法。每次对话结束后，可以将对话内容
        传入此方法，系统会自动抽取实体和关系并持久化。

        Args:
            text: 对话文本或任意文本
            use_llm: 是否使用 LLM 进行实体抽取

        Returns:
            IngestResult 包含写入统计
        """
        # 抽取实体和关系
        extraction = self._extractor.extract(text, use_llm=use_llm)
        extraction = self._apply_write_guard(extraction, text)

        # 写入实体
        entity_count = self._store.upsert_entities(extraction.entities)

        # 写入关系
        relation_count = self._store.upsert_relations(extraction.relations)

        return IngestResult(
            extraction=extraction,
            entities_written=entity_count,
            relations_written=relation_count,
        )

    def ingest_from_extraction(self, extraction: ExtractionResult) -> IngestResult:
        """
        直接从已有的抽取结果写入图数据库。
        适用于上层已经完成抽取的场景。
        """
        extraction = self._apply_write_guard(extraction, extraction.raw_text)
        entity_count = self._store.upsert_entities(extraction.entities)
        relation_count = self._store.upsert_relations(extraction.relations)

        return IngestResult(
            extraction=extraction,
            entities_written=entity_count,
            relations_written=relation_count,
        )

    # ========== 传统模式：检索接口 ==========

    def retrieve_context(self, user_input: str, use_llm: bool = True) -> ContextResult:
        """
        根据用户输入检索相关的记忆上下文。

        Args:
            user_input: 用户当前输入
            use_llm: 实体抽取是否使用 LLM

        Returns:
            ContextResult 包含格式化的上下文文本和子图数据
        """
        return self._context_builder.build_context(user_input, use_llm=use_llm)

    def build_prompt(
        self,
        user_input: str,
        base_prompt: str = "",
        use_llm: bool = True,
    ) -> str:
        """
        构建包含记忆上下文的增强系统提示词。

        Args:
            user_input: 用户当前输入
            base_prompt: 基础系统提示词
            use_llm: 实体抽取是否使用 LLM

        Returns:
            增强后的系统提示词字符串
        """
        return self._context_builder.build_system_prompt(
            user_input, base_prompt, use_llm=use_llm,
        )

    # ========== 会话模式：会话生命周期接口 ==========

    def start_session(self, initial_message: str, use_llm: bool = True) -> ContextResult:
        """
        开始一个新的对话会话。
        
        根据初始消息从图数据库检索相关子图，建立会话级缓存。
        会话过程中的子图会被缓存，只在主题变化时刷新。
        
        Args:
            initial_message: 会话的第一条消息
            use_llm: 实体抽取是否使用 LLM
            
        Returns:
            初始上下文（ContextResult）
        """
        return self._context_builder.start_session(initial_message, use_llm=use_llm)

    def process_message(self, user_input: str, use_llm: bool = True) -> ContextResult:
        """
        处理会话中的一条消息。
        
        返回当前缓存的子图上下文。如果检测到主题变化，则重新检索子图。
        
        Args:
            user_input: 用户当前输入
            use_llm: 实体抽取是否使用 LLM
            
        Returns:
            上下文（可能是缓存的，也可能是新检索的）
        """
        return self._context_builder.get_context(user_input, use_llm=use_llm)

    def end_session(self, conversation_text: str, use_llm: bool = True) -> IngestResult:
        """
        结束会话，将整个对话内容写入记忆。
        
        从会话中收集的所有抽取结果，以及新传入的对话文本，
        都会被写入图数据库。
        
        Args:
            conversation_text: 完整的对话文本（用于额外的抽取）
            use_llm: 是否使用 LLM 进行抽取
            
        Returns:
            IngestResult 包含写入统计
        """
        # 获取会话中收集的所有抽取结果
        session_extractions = self._context_builder.end_session()
        
        # 合并所有实体和关系
        all_entities = []
        all_relations = []
        
        for extraction in session_extractions:
            all_entities.extend(extraction.entities)
            all_relations.extend(extraction.relations)
        
        # 对完整对话文本进行额外抽取
        final_extraction = self._extractor.extract(conversation_text, use_llm=use_llm)
        final_extraction = self._apply_write_guard(final_extraction, conversation_text)
        all_entities.extend(final_extraction.entities)
        all_relations.extend(final_extraction.relations)
        
        # 去重
        unique_entities = list({(e.name, e.entity_type): e for e in all_entities}.values())
        unique_relations = list({
            (r.source, r.target, r.relation_type): r for r in all_relations
        }.values())
        
        # 写入图数据库
        entity_count = self._store.upsert_entities(unique_entities)
        relation_count = self._store.upsert_relations(unique_relations)
        
        return IngestResult(
            extraction=final_extraction,
            entities_written=entity_count,
            relations_written=relation_count,
        )

    # ========== 查询接口 ==========

    def search_entities(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按关键词搜索实体"""
        return self._store.search_entities(keyword, limit)

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计信息"""
        db_stats = self._store.get_stats()
        return {
            "initialized": self._initialized,
            "connected": self.is_connected(),
            **db_stats,
        }

    # ========== 底层访问（高级用法）==========

    @property
    def store(self) -> GraphStore:
        """直接访问图数据库存储层"""
        return self._store

    @property
    def extractor(self) -> EntityExtractor:
        """直接访问实体抽取器"""
        return self._extractor


class IngestResult:
    """记忆写入结果"""

    def __init__(
        self,
        extraction: ExtractionResult,
        entities_written: int,
        relations_written: int,
    ):
        self.extraction = extraction
        self.entities_written = entities_written
        self.relations_written = relations_written

    def to_dict(self) -> Dict[str, Any]:
        """转为字典"""
        return {
            "entities_extracted": len(self.extraction.entities),
            "relations_extracted": len(self.extraction.relations),
            "entities_written": self.entities_written,
            "relations_written": self.relations_written,
        }

    def __repr__(self) -> str:
        return (
            f"IngestResult(entities={self.entities_written}, "
            f"relations={self.relations_written})"
        )
