"""
Neo4j 图数据库存储层

负责将实体和关系持久化到 Neo4j，并提供检索接口。
所有 Cypher 操作封装在此模块中，上层无需关心数据库细节。

v2.1 — 新增冥思（Meditation）相关的图查询与批量操作方法：
v3.0 — Phase 3: 策略蒸馏与进化相关方法：
  - get_causal_chains: 获取因果链（CAUSES 关系连接的事件序列）
  - get_event_clusters: 获取高连接度的事件聚类
  - get_strategies_for_evolution: 获取活跃策略及关联信息
  - create_causal_chain_node: 创建因果链元节点
  - link_strategy_to_causal_chain: 建立策略与因果链的溯源关系
  - get_nodes_needing_meditation: 获取标记需要冥思的节点
  - get_orphan_nodes / get_generic_word_nodes: 孤立节点清理查询
  - get_similar_entity_pairs / get_short_name_entities: 实体整合查询
  - get_entities_missing_metadata: 缺少元数据的实体查询
  - get_related_to_edges: 获取 related_to 边用于关系重标注
  - get_all_active_nodes_for_weighting: 获取活跃节点用于权重计算
  - get_dense_subgraphs_for_distillation: 获取密集子图用于知识蒸馏
  - archive_nodes / merge_entity_nodes / batch_update_weights: 批量操作
  - create_meditation_snapshot / get_change_counts_since: 安全与统计
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from typing import Any, Dict, List, Optional, Tuple

from neo4j import GraphDatabase, Driver

from .config import Neo4jConfig
from .entity_extractor import Entity, Relation

logger = logging.getLogger("meditation.graph_store")


# Lazy import belief integration (avoids circular dependency when
# belief_integration imports graph_store types in the future).
_belief_mod = None
def _get_belief_mod():
    global _belief_mod
    if _belief_mod is None:
        try:
            from cognitive_engine import belief_integration
            _belief_mod = belief_integration
        except ImportError:
            pass  # belief layer not available — no-op
    return _belief_mod


# ================================================================
# 注意力分数计算（轻量级，基于实体属性）
# ================================================================

_ATTENTION_ENTITY_TYPE_WEIGHTS = {
    # 高重要性实体类型
    "person": 1.0,
    "organization": 0.95,
    "technology": 0.90,
    "concept": 0.80,
    "event": 0.85,
    "product": 0.75,
    "location": 0.70,
    "project": 0.85,
    # 默认
    "other": 0.50,
}


def compute_attention_score(
    entity_name: str,
    entity_type: str = "other",
    mention_count: int = 0,
    properties: Optional[Dict[str, Any]] = None,
) -> float:
    """
    计算实体注意力分数（轻量级，无需外部依赖）。

    综合考量：
    - 提及次数（log 归一化）
    - 实体类型重要性
    - 名称质量（长度、独特性）

    Returns:
        0.0 ~ 1.0 之间的注意力分数
    """
    if not entity_name:
        return 0.0

    # 1. 提及次数分数 (0 ~ 0.5)
    mention_score = min(0.5, 0.15 * math.log1p(mention_count))

    # 2. 实体类型权重 (0.3 ~ 1.0 -> 映射到 0 ~ 0.3)
    type_weight = _ATTENTION_ENTITY_TYPE_WEIGHTS.get(entity_type.lower(), 0.50)
    type_score = 0.3 * (type_weight - 0.3) / 0.7

    # 3. 名称质量分数 (0 ~ 0.2)
    name_len = len(entity_name)
    # 中文实体通常 2-6 字最佳，英文 3-20 字符
    if "\u4e00" <= entity_name[0] <= "\u9fff":
        name_score = 0.2 * min(1.0, name_len / 6.0)
    else:
        name_score = 0.2 * min(1.0, name_len / 15.0)

    # 4. 特殊标记加分 (0 ~ 0.1)
    bonus = 0.0
    props = properties or {}
    if props.get("is_key_entity"):
        bonus += 0.1
    if props.get("needs_meditation"):
        bonus += 0.05

    total = min(1.0, mention_score + type_score + name_score + bonus)
    return round(total, 4)


class GraphStore:
    """
    Neo4j 图数据库存储层

    职责：
      - 实体（节点）的增删查
      - 关系（边）的增删查
      - 基于关键词 / 实体名称的子图检索
      - 数据库初始化（创建索引等）
      - 冥思相关的批量查询与更新操作
    """

    def __init__(self, config: Optional[Neo4jConfig] = None):
        self._config = config or Neo4jConfig()
        self._driver: Optional[Driver] = None

    # ========== 连接管理 ==========

    @property
    def driver(self) -> Driver:
        """延迟初始化 Neo4j 驱动"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self._config.uri,
                auth=(self._config.user, self._config.password),
            )
        return self._driver

    def close(self):
        """关闭数据库连接"""
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def verify_connectivity(self) -> bool:
        """验证数据库连接是否正常"""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    # ========== 初始化 ==========

    def init_schema(self):
        """
        初始化数据库 schema：创建索引和约束。
        幂等操作，可重复调用。
        """
        queries = [
            # 实体节点索引
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            "CREATE INDEX entity_type_idx IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)",
            # 全文索引，用于模糊搜索
            """
            CREATE FULLTEXT INDEX entity_fulltext_idx IF NOT EXISTS
            FOR (e:Entity) ON EACH [e.name, e.description]
            """,
            # 冥思相关索引
            "CREATE INDEX entity_updated_idx IF NOT EXISTS FOR (e:Entity) ON (e.updated_at)",
            "CREATE INDEX entity_activation_idx IF NOT EXISTS FOR (e:Entity) ON (e.activation_level)",
            "CREATE INDEX entity_needs_meditation_idx IF NOT EXISTS FOR (e:Entity) ON (e.needs_meditation)",
            # Phase 2: 策略节点索引
            "CREATE INDEX strategy_name_idx IF NOT EXISTS FOR (s:Strategy) ON (s.name)",
            "CREATE INDEX strategy_fitness_idx IF NOT EXISTS FOR (s:Strategy) ON (s.fitness_score)",
            # Phase 2: RQS 记录索引
            "CREATE INDEX rqs_path_idx IF NOT EXISTS FOR (r:RQSRecord) ON (r.path_id)",
            # Phase 2: 信念节点索引
            "CREATE INDEX belief_content_idx IF NOT EXISTS FOR (b:Belief) ON (b.content)",
            # Phase 5: Claim 节点索引
            "CREATE INDEX claim_entity_value_idx IF NOT EXISTS FOR (c:Claim) ON (c.entity_name, c.claim_kind, c.claimed_value)",
            # Phase 3: 因果链索引
            "CREATE INDEX causal_chain_id_idx IF NOT EXISTS FOR (c:CausalChain) ON (c.chain_id)",
            # Phase 4: 反馈节点索引
            "CREATE INDEX feedback_query_ts_idx IF NOT EXISTS FOR (f:Feedback) ON (f.query, f.timestamp)",
            "CREATE INDEX feedback_success_idx IF NOT EXISTS FOR (f:Feedback) ON (f.success)",
            # Phase 5: world model nodes
            "CREATE INDEX observation_id_idx IF NOT EXISTS FOR (o:Observation) ON (o.observation_id)",
            "CREATE INDEX outcome_id_idx IF NOT EXISTS FOR (o:Outcome) ON (o.outcome_id)",
            "CREATE INDEX belief_update_id_idx IF NOT EXISTS FOR (u:BeliefUpdate) ON (u.update_id)",
            "CREATE INDEX import_batch_idx IF NOT EXISTS FOR (b:ImportBatch) ON (b.import_batch)",
            "CREATE INDEX import_batch_source_tag_idx IF NOT EXISTS FOR (b:ImportBatch) ON (b.source_tag)",
        ]
        with self.driver.session(database=self._config.database) as session:
            for query in queries:
                try:
                    session.run(query)
                except Exception:
                    pass

    # ========== 实体操作 ==========

    def upsert_entity(self, entity: Entity) -> str:
        """
        插入或更新实体节点（MERGE 语义）。
        MERGE 键仅使用 {name}，避免同一名称因 entity_type 不同重复创建节点。
        ON MATCH 时更新 entity_type（以最新为准）、累加 mention_count。
        质量过滤：丢弃过短、停用词、纯数字等垃圾实体。

        Returns:
            节点的 elementId（过滤返回 ""）
        """
        # 质量过滤
        if not self._is_valid_entity_name(entity.name):
            return ""

        # 自动计算注意力分数
        attention = compute_attention_score(
            entity.name, entity.entity_type,
            getattr(entity, 'mention_count', 0),
            getattr(entity, 'properties', {})
        )

        # 自动分类信念类型
        belief_mod = _get_belief_mod()
        belief_type = "unknown"
        belief_strength = 0.5
        if belief_mod:
            ctx = entity.properties.get("source_context", entity.name)
            belief_type_val, belief_strength = belief_mod.classify_belief(
                ctx, entity.name, entity.entity_type
            )
            belief_type = getattr(belief_type_val, 'value', str(belief_type_val))

        query = """
        MERGE (e:Entity {name: $name})
        ON CREATE SET
            e.entity_type = $entity_type,
            e.properties = $properties,
            e.created_at = timestamp(),
            e.updated_at = timestamp(),
            e.mention_count = 1,
            e.attention_score = $attention,
            e.belief_type = $belief_type,
            e.belief_strength = $belief_strength,
            e.knowledge_state = $knowledge_state,
            e.evidence_count = $evidence_count,
            e.source_count = $source_count,
            e.source_tag = $source_tag,
            e.import_batch = $import_batch,
            e.source_path = $source_path,
            e.needs_meditation = true
        ON MATCH SET
            e.entity_type = $entity_type,
            e.properties = $properties,
            e.updated_at = timestamp(),
            e.mention_count = coalesce(e.mention_count, 0) + 1,
            e.attention_score = $attention,
            e.belief_type = $belief_type,
            e.belief_strength = $belief_strength,
            e.knowledge_state = $knowledge_state,
            e.evidence_count = $evidence_count,
            e.source_count = $source_count,
            e.source_tag = CASE WHEN $source_tag <> '' THEN $source_tag ELSE e.source_tag END,
            e.import_batch = CASE WHEN $import_batch <> '' THEN $import_batch ELSE e.import_batch END,
            e.source_path = CASE WHEN $source_path <> '' THEN $source_path ELSE e.source_path END,
            e.needs_meditation = true
        RETURN elementId(e) AS eid
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                name=entity.name,
                entity_type=entity.entity_type,
                properties=json.dumps(entity.properties, ensure_ascii=False),
                attention=attention,
                belief_type=belief_type,
                belief_strength=belief_strength,
                knowledge_state=entity.properties.get("knowledge_state", "stable"),
                evidence_count=entity.properties.get("evidence_count", 1),
                source_count=entity.properties.get("source_count", 1),
                source_tag=entity.properties.get("source_tag", ""),
                import_batch=entity.properties.get("import_batch", ""),
                source_path=entity.properties.get("source_path", ""),
            )
            record = result.single()
            return record["eid"] if record else ""

    def upsert_entities(self, entities: List[Entity]) -> int:
        """批量插入或更新实体，返回处理数量（自动质量过滤 + 注意力分数 + 信念分类）"""
        valid = [e for e in entities if self._is_valid_entity_name(e.name)]
        if not valid:
            return 0

        belief_mod = _get_belief_mod()

        query = """
        UNWIND $batch AS item
        MERGE (e:Entity {name: item.name})
        ON CREATE SET
            e.entity_type = item.entity_type,
            e.properties = item.properties,
            e.created_at = timestamp(),
            e.updated_at = timestamp(),
            e.mention_count = item.mention_count,
            e.attention_score = item.attention,
            e.belief_type = item.belief_type,
            e.belief_strength = item.belief_strength,
            e.knowledge_state = item.knowledge_state,
            e.evidence_count = item.evidence_count,
            e.source_count = item.source_count,
            e.source_tag = item.source_tag,
            e.import_batch = item.import_batch,
            e.source_path = item.source_path,
            e.needs_meditation = true
        ON MATCH SET
            e.entity_type = item.entity_type,
            e.properties = item.properties,
            e.updated_at = timestamp(),
            e.mention_count = coalesce(e.mention_count, 0) + item.mention_count,
            e.attention_score = item.attention,
            e.belief_type = item.belief_type,
            e.belief_strength = CASE
                WHEN coalesce(e.belief_strength, 0.0) > item.belief_strength THEN coalesce(e.belief_strength, 0.0)
                ELSE item.belief_strength
            END,
            e.evidence_count = coalesce(e.evidence_count, 0) + item.evidence_count,
            e.source_count = CASE
                WHEN item.source_id IS NOT NULL AND item.source_id <> '' AND coalesce(e.last_source_id, '') <> item.source_id
                    THEN coalesce(e.source_count, 0) + item.source_count
                ELSE coalesce(e.source_count, 0)
            END,
            e.source_tag = CASE WHEN item.source_tag <> '' THEN item.source_tag ELSE e.source_tag END,
            e.import_batch = CASE WHEN item.import_batch <> '' THEN item.import_batch ELSE e.import_batch END,
            e.source_path = CASE WHEN item.source_path <> '' THEN item.source_path ELSE e.source_path END,
            e.last_source_id = item.source_id,
            e.knowledge_state = CASE
                WHEN (
                    CASE
                        WHEN coalesce(e.belief_strength, 0.0) > item.belief_strength THEN coalesce(e.belief_strength, 0.0)
                        ELSE item.belief_strength
                    END
                ) >= $stable_belief_strength_threshold
                AND (coalesce(e.evidence_count, 0) + item.evidence_count) >= $stable_min_evidence_count
                AND (
                    CASE
                        WHEN item.source_id IS NOT NULL AND item.source_id <> '' AND coalesce(e.last_source_id, '') <> item.source_id
                            THEN coalesce(e.source_count, 0) + item.source_count
                        ELSE coalesce(e.source_count, 0)
                    END
                ) >= $stable_min_source_count
                THEN 'stable'
                ELSE 'hypothesis'
            END,
            e.needs_meditation = true
        RETURN count(e) AS updated
        """

        batch = []
        for e in valid:
            attention = compute_attention_score(e.name, e.entity_type, 1, e.properties)
            belief_type = "unknown"
            belief_strength = 0.5
            if belief_mod:
                ctx = e.properties.get("source_context", e.name)
                bt_val, bs = belief_mod.classify_belief(ctx, e.name, e.entity_type)
                belief_type = getattr(bt_val, 'value', str(bt_val))
                belief_strength = bs
            batch.append({
                "name": e.name,
                "entity_type": e.entity_type,
                "properties": json.dumps(e.properties, ensure_ascii=False),
                "mention_count": 1,
                "attention": attention,
                "belief_type": belief_type,
                "belief_strength": belief_strength,
                "knowledge_state": e.properties.get("knowledge_state", "stable"),
                "evidence_count": e.properties.get("evidence_count", 1),
                "source_count": e.properties.get("source_count", 1),
                "source_id": e.properties.get("source_id", ""),
                "source_tag": e.properties.get("source_tag", ""),
                "import_batch": e.properties.get("import_batch", ""),
                "source_path": e.properties.get("source_path", ""),
            })
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                batch=batch,
                stable_belief_strength_threshold=0.7,
                stable_min_evidence_count=3,
                stable_min_source_count=2,
            )
            record = result.single()
            return record["updated"] if record else 0

    def anchor_entities_to_import_batch(self, entities: List[Entity], source_tag: str = "", import_batch: str = "", source_path: str = "") -> int:
        """为本次 probe/import 建立 ImportBatch 锚点和 SEEN_IN 关系。"""
        if not entities or not import_batch:
            return 0
        batch = []
        seen = set()
        for entity in entities:
            key = (entity.name, source_path or entity.properties.get("source_path", ""))
            if key in seen:
                continue
            seen.add(key)
            batch.append({
                "name": entity.name,
                "source_path": source_path or entity.properties.get("source_path", ""),
            })
        query = """
        MERGE (b:ImportBatch {import_batch: $import_batch})
        ON CREATE SET
            b.source_tag = $source_tag,
            b.source_path = $source_path,
            b.created_at = timestamp(),
            b.updated_at = timestamp()
        ON MATCH SET
            b.source_tag = CASE WHEN $source_tag <> '' THEN $source_tag ELSE b.source_tag END,
            b.source_path = CASE WHEN $source_path <> '' THEN $source_path ELSE b.source_path END,
            b.updated_at = timestamp()
        WITH b
        UNWIND $batch AS item
        MATCH (e:Entity {name: item.name})
        MERGE (e)-[:SEEN_IN]->(b)
        RETURN count(e) AS linked
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                import_batch=import_batch,
                source_tag=source_tag,
                source_path=source_path,
                batch=batch,
            )
            record = result.single()
            return int(record["linked"]) if record and record.get("linked") is not None else 0

    def get_entities_by_source(self, source_tag: str = "", import_batch: str = "", limit: int = 50) -> List[Dict[str, Any]]:
        """按 source_tag / import_batch 查询实体，供实验审计使用。"""
        clauses = []
        if source_tag:
            clauses.append("b.source_tag = $source_tag")
        if import_batch:
            clauses.append("b.import_batch = $import_batch")
        where_clause = " AND ".join(clauses) if clauses else "true"
        query = f"""
        MATCH (e:Entity)-[:SEEN_IN]->(b:ImportBatch)
        WHERE {where_clause}
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.mention_count AS mention_count,
               b.source_tag AS source_tag,
               b.import_batch AS import_batch,
               b.source_path AS source_path
        ORDER BY e.mention_count DESC, e.name ASC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, source_tag=source_tag, import_batch=import_batch, limit=limit)
            return [dict(r) for r in result]

    def get_top_entities_by_attention(
        self, limit: int = 30, min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        按注意力分数获取优先级最高的实体。
        冥思系统可用此方法优先处理重要实体。
        """
        query = """
        MATCH (e:Entity)
        WHERE e.attention_score IS NOT NULL
          AND e.attention_score >= $min_score
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.mention_count AS mention_count,
               e.attention_score AS attention_score,
               e.created_at AS created_at,
               e.updated_at AS updated_at
        ORDER BY e.attention_score DESC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, min_score=min_score, limit=limit)
            return [dict(r) for r in result]

    def get_low_attention_entities_batch(
        self, limit: int = 100, min_mention_count: int = 1
    ) -> List[Dict[str, Any]]:
        """
        获取注意力分数较低但已被多次提及的实体。
        这些实体可能有信息丢失或质量问题，需要冥思重点关注。
        """
        query = """
        MATCH (e:Entity)
        WHERE e.mention_count >= $min_mentions
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.mention_count AS mention_count,
               e.attention_score AS attention_score
        ORDER BY e.mention_count DESC, e.attention_score ASC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, min_mentions=min_mention_count, limit=limit)
            return [dict(r) for r in result]

    # ================================================================
    # 实体质量过滤
    # ================================================================

    _ENTITY_STOP_WORDS = frozenset([
        # 代词/指示词/虚词
        "我", "你", "他", "她", "它", "我们", "你们", "他们", "她们", "它们",
        "这", "那", "这个", "那个", "这些", "那些", "这里", "那里", "哪里",
        "自己", "别人", "大家", "某人", "什么", "怎么", "怎样", "为什么",
        "谁", "哪个", "哪些", "某", "如何", "为何", "怎么", "哪儿",
        "的", "了", "着", "过", "得", "地", "和", "与", "或", "而",
        "就", "都", "也", "还", "又", "才", "只", "仅", "最",
        "很", "太", "更", "非常", "十分", "极其", "比较",
        # 无意义名词
        "东西", "事情", "事", "问题", "方面", "情况", "时候", "地方",
        "方式", "方法", "结果", "原因", "目的", "意思", "意义", "作用",
        "影响", "关系", "条件", "过程", "内容", "部分", "方向", "程度",
        "范围", "角度", "层面", "水平", "能力", "可能性", "需要", "注意",
        # 口语碎片
        "一下", "一些", "一点", "一种", "一个", "一样", "一起", "一直",
        "一定", "一般", "其中", "之间", "之中", "之后", "之前",
        "这样", "那样", "如果", "是否", "已经", "正在", "开始",
        # 常见泛动词
        "分析", "研究", "讨论", "考虑", "处理", "解决", "实现", "发展",
        "提高", "改进", "使用", "利用", "采用", "进行", "完成", "结束",
        "继续", "保持", "变化", "存在", "包含", "属于", "成为", "认为",
        "觉得", "知道", "了解", "发现", "感觉", "看到", "听到", "说",
        "讲", "告诉", "建议", "希望", "需要", "想", "要",
    ])

    @classmethod
    def _is_valid_entity_name(cls, name: str) -> bool:
        """检查实体名称是否有质量，拒绝碎片/垃圾。"""
        if not name:
            return False
        # 太短
        if len(name) < 2:
            return False
        # 太长
        if len(name) > 100:
            return False
        # 纯数字/标点
        import re as _re
        if _re.match(r"^[\d\s.,;:!?/_\\-]+$", name):
            return False
        # 纯英文太短
        if _re.match(r"^[a-zA-Z]+$", name) and len(name) <= 2:
            return False
        # 单字中文
        if len(name) == 1 and "\u4e00" <= name <= "\u9fff":
            return False
        # 停用词
        if name in cls._ENTITY_STOP_WORDS:
            return False
        # URL / 文件路径
        if name.startswith(("http", "www.", "/api", "./", "../")):
            return False
        if name.count("/") > 2 or name.count("\\") > 2:
            return False
        # 以虚词开头/结尾（中文）
        bad_starts = ("的", "了", "在", "和", "是", "有", "被", "把", "从", "对",
                      "让", "给", "与", "或", "而", "就", "都", "也", "还", "又",
                      "很", "最", "更", "太", "不", "没", "要", "会", "能", "可")
        bad_ends = ("的", "了", "着", "过", "得", "地", "在", "和", "是",
                    "有", "被", "把", "来", "去", "于", "从", "向", "对",
                    "与", "或", "而", "就", "都", "也", "还", "又", "则",
                    "时", "中", "后", "前", "间", "内", "外")
        if any(name.startswith(w) for w in bad_starts):
            return False
        if any(name.endswith(w) for w in bad_ends):
            return False
        return True

    def find_entity(self, name: str, entity_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """按名称查找实体（默认过滤 :Archived 节点）"""
        if entity_type:
            query = """
            MATCH (e:Entity {name: $name, entity_type: $entity_type})
            WHERE NOT e:Archived
            RETURN e.name AS name, e.entity_type AS entity_type,
                   e.properties AS properties, e.mention_count AS mention_count,
                   e.created_at AS created_at, e.updated_at AS updated_at
            """
            params = {"name": name, "entity_type": entity_type}
        else:
            query = """
            MATCH (e:Entity {name: $name})
            WHERE NOT e:Archived
            RETURN e.name AS name, e.entity_type AS entity_type,
                   e.properties AS properties, e.mention_count AS mention_count,
                   e.created_at AS created_at, e.updated_at AS updated_at
            """
            params = {"name": name}

        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, **params)
            record = result.single()
            if record:
                return dict(record)
            return None

    def search_entities(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        按关键词搜索实体（模糊匹配）。
        优先使用全文索引，回退到 CONTAINS 匹配。
        默认过滤掉 :Archived 节点。
        """
        try:
            return self._fulltext_search(keyword, limit)
        except Exception:
            pass

        query = """
        MATCH (e:Entity)
        WHERE e.name CONTAINS $keyword AND NOT e:Archived
        RETURN e.name AS name, e.entity_type AS entity_type,
               e.properties AS properties, e.mention_count AS mention_count
        ORDER BY e.mention_count DESC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, keyword=keyword, limit=limit)
            return [dict(record) for record in result]

    def _fulltext_search(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """全文索引搜索（过滤 :Archived）"""
        query = """
        CALL db.index.fulltext.queryNodes('entity_fulltext_idx', $keyword)
        YIELD node, score
        WHERE NOT node:Archived
        RETURN node.name AS name, node.entity_type AS entity_type,
               node.properties AS properties, node.mention_count AS mention_count,
               score
        ORDER BY score DESC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, keyword=keyword, limit=limit)
            return [dict(record) for record in result]

    # ========== 关系操作 ==========

    def upsert_relation(self, relation: Relation) -> bool:
        """
        插入或更新关系。
        统一使用 RELATES_TO 关系标签，真实类型存储在 relation_type 属性中。
        过滤 :Archived 节点。
        """
        query = """
        MATCH (src:Entity {name: $source})
        MATCH (tgt:Entity {name: $target})
        WHERE NOT src:Archived AND NOT tgt:Archived
        MERGE (src)-[r:RELATES_TO {relation_type: $relation_type}]->(tgt)
        ON CREATE SET
            r.properties = $properties,
            r.created_at = timestamp(),
            r.updated_at = timestamp(),
            r.mention_count = 1,
            r.knowledge_state = $knowledge_state,
            r.evidence_count = $evidence_count,
            r.source_count = $source_count,
            r.last_source_id = $source_id
        ON MATCH SET
            r.properties = $properties,
            r.updated_at = timestamp(),
            r.mention_count = coalesce(r.mention_count, 0) + 1,
            r.evidence_count = coalesce(r.evidence_count, 0) + $evidence_count,
            r.source_count = CASE
                WHEN $source_id IS NOT NULL AND $source_id <> '' AND coalesce(r.last_source_id, '') <> $source_id
                    THEN coalesce(r.source_count, 0) + $source_count
                ELSE coalesce(r.source_count, 0)
            END,
            r.last_source_id = $source_id,
            r.knowledge_state = CASE
                WHEN (coalesce(r.evidence_count, 0) + $evidence_count) >= $stable_min_evidence_count
                 AND (
                    CASE
                        WHEN $source_id IS NOT NULL AND $source_id <> '' AND coalesce(r.last_source_id, '') <> $source_id
                            THEN coalesce(r.source_count, 0) + $source_count
                        ELSE coalesce(r.source_count, 0)
                    END
                 ) >= $stable_min_source_count
                THEN 'stable'
                ELSE $knowledge_state
            END
        RETURN type(r) AS rel_type
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                source=relation.source,
                target=relation.target,
                relation_type=relation.relation_type,
                properties=json.dumps(relation.properties, ensure_ascii=False),
                knowledge_state=relation.properties.get("knowledge_state", "hypothesis"),
                evidence_count=relation.properties.get("evidence_count", 1),
                source_count=relation.properties.get("source_count", 1),
                source_id=relation.properties.get("source_id", ""),
                stable_min_evidence_count=3,
                stable_min_source_count=2,
            )
            record = result.single()
            return record is not None

    def upsert_relations(self, relations: List[Relation]) -> int:
        """批量插入或更新关系，返回成功数量"""
        count = 0
        for relation in relations:
            if self.upsert_relation(relation):
                count += 1
        return count

    # ========== 子图检索 ==========

    def get_entity_neighborhood(
        self,
        entity_name: str,
        max_depth: int = 2,
        max_nodes: int = 30,
        max_edges: int = 60,
    ) -> Dict[str, Any]:
        """
        获取指定实体的邻域子图。
        """
        query = """
        MATCH (start:Entity {name: $name})
        WHERE NOT start:Archived
        CALL apoc.path.subgraphAll(start, {maxLevel: $max_depth})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        fallback_query = """
        MATCH (start:Entity {name: $name})
        WHERE NOT start:Archived
        OPTIONAL MATCH path = (start)-[*1..%(depth)s]-(neighbor:Entity)
        WHERE NOT neighbor:Archived
        WITH start, collect(DISTINCT neighbor) AS neighbors,
             collect(DISTINCT relationships(path)) AS all_rels
        RETURN start, neighbors, all_rels
        """ % {"depth": max_depth}

        with self.driver.session(database=self._config.database) as session:
            try:
                return self._execute_neighborhood_query(
                    session, query,
                    {"name": entity_name, "max_depth": max_depth},
                    max_nodes, max_edges, use_apoc=True,
                )
            except Exception:
                return self._execute_neighborhood_fallback(
                    session, fallback_query,
                    {"name": entity_name},
                    max_nodes, max_edges,
                )

    def _execute_neighborhood_query(
        self, session, query: str, params: dict,
        max_nodes: int, max_edges: int, use_apoc: bool,
    ) -> Dict[str, Any]:
        """执行 APOC 邻域查询"""
        result = session.run(query, **params)
        record = result.single()
        if not record:
            return {"nodes": [], "edges": []}

        nodes_data = []
        edges_data = []

        for node in record["nodes"][:max_nodes]:
            nodes_data.append({
                "name": node.get("name", ""),
                "entity_type": node.get("entity_type", ""),
                "mention_count": node.get("mention_count", 0),
            })

        for rel in record["relationships"][:max_edges]:
            edges_data.append({
                "source": rel.start_node.get("name", ""),
                "target": rel.end_node.get("name", ""),
                "relation_type": rel.get("relation_type", "related_to"),
            })

        return {"nodes": nodes_data, "edges": edges_data}

    def _execute_neighborhood_fallback(
        self, session, query: str, params: dict,
        max_nodes: int, max_edges: int,
    ) -> Dict[str, Any]:
        """使用原生 Cypher 的邻域查询回退方案"""
        result = session.run(query, **params)
        record = result.single()
        if not record:
            return {"nodes": [], "edges": []}

        nodes_data = []
        edges_set = set()
        edges_data = []

        start = record["start"]
        if start:
            nodes_data.append({
                "name": start.get("name", ""),
                "entity_type": start.get("entity_type", ""),
                "mention_count": start.get("mention_count", 0),
            })

        for neighbor in (record["neighbors"] or [])[:max_nodes - 1]:
            if neighbor:
                nodes_data.append({
                    "name": neighbor.get("name", ""),
                    "entity_type": neighbor.get("entity_type", ""),
                    "mention_count": neighbor.get("mention_count", 0),
                })

        for rel_list in (record["all_rels"] or []):
            if rel_list:
                for rel in rel_list:
                    if rel and len(edges_data) < max_edges:
                        key = (
                            rel.start_node.get("name", ""),
                            rel.end_node.get("name", ""),
                            rel.get("relation_type", ""),
                        )
                        if key not in edges_set:
                            edges_set.add(key)
                            edges_data.append({
                                "source": key[0],
                                "target": key[1],
                                "relation_type": key[2] or "related_to",
                            })

        return {"nodes": nodes_data, "edges": edges_data}

    def get_subgraph_by_entities(
        self,
        entity_names: List[str],
        max_depth: int = 1,
        max_nodes: int = 30,
        max_edges: int = 60,
    ) -> Dict[str, Any]:
        """
        根据多个实体名称检索相关子图（过滤 :Archived）。
        """
        if not entity_names:
            return {"nodes": [], "edges": []}

        query = """
        UNWIND $names AS entity_name
        MATCH (e:Entity {name: entity_name})
        WHERE NOT e:Archived
        OPTIONAL MATCH path = (e)-[r:RELATES_TO*1..%(depth)s]-(neighbor:Entity)
        WHERE NOT neighbor:Archived
        WITH collect(DISTINCT e) + collect(DISTINCT neighbor) AS all_nodes,
             collect(DISTINCT r) AS all_rels_nested
        UNWIND all_nodes AS node
        WITH collect(DISTINCT node) AS nodes, all_rels_nested
        UNWIND all_rels_nested AS rel_list
        UNWIND rel_list AS rel
        WITH nodes, collect(DISTINCT rel) AS rels
        RETURN nodes, rels
        """ % {"depth": max_depth}

        with self.driver.session(database=self._config.database) as session:
            try:
                result = session.run(query, names=entity_names)
                record = result.single()
            except Exception:
                return self._get_subgraph_individually(
                    session, entity_names, max_depth, max_nodes, max_edges
                )

        if not record:
            return {"nodes": [], "edges": []}

        nodes_data = []
        seen_nodes = set()
        for node in (record["nodes"] or [])[:max_nodes]:
            if node:
                name = node.get("name", "")
                if name and name not in seen_nodes:
                    seen_nodes.add(name)
                    nodes_data.append({
                        "name": name,
                        "entity_type": node.get("entity_type", ""),
                        "mention_count": node.get("mention_count", 0),
                    })

        edges_data = []
        seen_edges = set()
        for rel in (record["rels"] or [])[:max_edges]:
            if rel:
                src = rel.start_node.get("name", "")
                tgt = rel.end_node.get("name", "")
                rtype = rel.get("relation_type", "related_to")
                key = (src, tgt, rtype)
                if key not in seen_edges:
                    seen_edges.add(key)
                    edges_data.append({
                        "source": src,
                        "target": tgt,
                        "relation_type": rtype,
                    })

        return {"nodes": nodes_data, "edges": edges_data}

    def _get_subgraph_individually(
        self, session, entity_names: List[str],
        max_depth: int, max_nodes: int, max_edges: int,
    ) -> Dict[str, Any]:
        """逐个实体查询邻域并合并结果"""
        all_nodes = {}
        all_edges = set()
        edges_data = []

        for name in entity_names:
            query = """
            MATCH (e:Entity {name: $name})
            WHERE NOT e:Archived
            OPTIONAL MATCH (e)-[r:RELATES_TO]-(neighbor:Entity)
            WHERE NOT neighbor:Archived
            RETURN e, collect(DISTINCT neighbor) AS neighbors,
                   collect(DISTINCT r) AS rels
            """
            result = session.run(query, name=name)
            record = result.single()
            if not record:
                continue

            node = record["e"]
            if node:
                n = node.get("name", "")
                if n and n not in all_nodes:
                    all_nodes[n] = {
                        "name": n,
                        "entity_type": node.get("entity_type", ""),
                        "mention_count": node.get("mention_count", 0),
                    }

            for neighbor in (record["neighbors"] or []):
                if neighbor and len(all_nodes) < max_nodes:
                    n = neighbor.get("name", "")
                    if n and n not in all_nodes:
                        all_nodes[n] = {
                            "name": n,
                            "entity_type": neighbor.get("entity_type", ""),
                            "mention_count": neighbor.get("mention_count", 0),
                        }

            for rel in (record["rels"] or []):
                if rel and len(edges_data) < max_edges:
                    src = rel.start_node.get("name", "")
                    tgt = rel.end_node.get("name", "")
                    rtype = rel.get("relation_type", "related_to")
                    key = (src, tgt, rtype)
                    if key not in all_edges:
                        all_edges.add(key)
                        edges_data.append({
                            "source": src, "target": tgt,
                            "relation_type": rtype,
                        })

        return {"nodes": list(all_nodes.values()), "edges": edges_data}

    # ========== 统计与清理 ==========

    def get_stats(self) -> Dict[str, int]:
        """获取图数据库统计信息（排除 :Archived 节点）"""
        query = """
        MATCH (e:Entity)
        WHERE NOT e:Archived
        WITH count(e) AS node_count,
             count(CASE WHEN coalesce(e.knowledge_state, 'stable') = 'hypothesis' THEN 1 END) AS hypothesis_entity_count,
             count(CASE WHEN coalesce(e.knowledge_state, 'stable') = 'stable' THEN 1 END) AS stable_entity_count
        OPTIONAL MATCH ()-[r:RELATES_TO]->()
        RETURN node_count, count(r) AS edge_count,
               hypothesis_entity_count, stable_entity_count
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query)
            record = result.single()
            if record:
                return {
                    "node_count": record["node_count"],
                    "edge_count": record["edge_count"],
                    "hypothesis_entity_count": record.get("hypothesis_entity_count", 0),
                    "stable_entity_count": record.get("stable_entity_count", record["node_count"]),
                }
            return {
                "node_count": 0,
                "edge_count": 0,
                "hypothesis_entity_count": 0,
                "stable_entity_count": 0,
            }

    def clear_all(self):
        """清空所有数据（仅用于测试）"""
        with self.driver.session(database=self._config.database) as session:
            session.run("MATCH (n) DETACH DELETE n")

    # ================================================================
    # 冥思（Meditation）专用方法
    # ================================================================

    # ---------- 数据快照与锁定 ----------

    def get_nodes_needing_meditation(
        self,
        limit: int = 500,
        skip_recent_seconds: int = 300,
    ) -> List[Dict[str, Any]]:
        """
        获取标记了 needs_meditation=true 的节点。
        跳过最近 skip_recent_seconds 秒内更新的节点以避免读写冲突。
        """
        query = """
        MATCH (e:Entity)
        WHERE e.needs_meditation = true
          AND NOT e:Archived
          AND e.updated_at < (timestamp() - $skip_ms)
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.properties AS properties,
               e.mention_count AS mention_count,
               e.description AS description,
               e.created_at AS created_at,
               e.updated_at AS updated_at,
               e.activation_level AS activation_level,
               e.aliases AS aliases,
               elementId(e) AS element_id
        ORDER BY e.updated_at ASC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                skip_ms=skip_recent_seconds * 1000,
                limit=limit,
            )
            return [dict(record) for record in result]

    def get_nodes_in_time_window(
        self,
        hours: int = 24,
        skip_recent_seconds: int = 300,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        """获取指定时间窗口内更新的节点（用于定时冥思）。"""
        query = """
        MATCH (e:Entity)
        WHERE NOT e:Archived
          AND e.updated_at > (timestamp() - $window_ms)
          AND e.updated_at < (timestamp() - $skip_ms)
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.properties AS properties,
               e.mention_count AS mention_count,
               e.description AS description,
               e.created_at AS created_at,
               e.updated_at AS updated_at,
               e.activation_level AS activation_level,
               e.aliases AS aliases,
               elementId(e) AS element_id
        ORDER BY e.updated_at ASC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                window_ms=hours * 3600 * 1000,
                skip_ms=skip_recent_seconds * 1000,
                limit=limit,
            )
            return [dict(record) for record in result]

    def lock_nodes_for_meditation(self, node_names: List[str], run_id: str) -> int:
        """
        标记节点为冥思处理中（设置 meditation_lock）。

        Args:
            node_names: 要锁定的节点名称列表
            run_id: 本次冥思运行的唯一标识

        Returns:
            成功锁定的节点数
        """
        query = """
        UNWIND $names AS n
        MATCH (e:Entity {name: n})
        WHERE NOT e:Archived
          AND (e.meditation_lock IS NULL OR e.meditation_lock = "")
        SET e.meditation_lock = $run_id,
            e.meditation_lock_at = timestamp()
        RETURN count(e) AS locked
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, names=node_names, run_id=run_id)
            record = result.single()
            return record["locked"] if record else 0

    def unlock_nodes_after_meditation(self, run_id: str) -> int:
        """
        解除冥思锁定并清除 needs_meditation 标记。

        Args:
            run_id: 本次冥思运行的唯一标识

        Returns:
            解锁的节点数
        """
        query = """
        MATCH (e:Entity)
        WHERE e.meditation_lock = $run_id
        SET e.meditation_lock = null,
            e.meditation_lock_at = null,
            e.needs_meditation = false
        RETURN count(e) AS unlocked
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, run_id=run_id)
            record = result.single()
            return record["unlocked"] if record else 0

    # ---------- 孤立节点清理（Pruning）----------

    def get_orphan_nodes(
        self,
        min_mentions: int = 2,
        skip_recent_seconds: int = 300,
    ) -> List[Dict[str, Any]]:
        """获取孤立节点（无边连接且 mention_count 低于阈值）。"""
        query = """
        MATCH (e:Entity)
        WHERE NOT e:Archived
          AND e.updated_at < (timestamp() - $skip_ms)
          AND coalesce(e.mention_count, 0) < $min_mentions
        OPTIONAL MATCH (e)-[r:RELATES_TO]-()
        WITH e, count(r) AS rel_count
        WHERE rel_count = 0
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.mention_count AS mention_count,
               e.updated_at AS updated_at,
               elementId(e) AS element_id
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                min_mentions=min_mentions,
                skip_ms=skip_recent_seconds * 1000,
            )
            return [dict(record) for record in result]

    def get_generic_word_nodes(
        self,
        generic_words: List[str],
        skip_recent_seconds: int = 300,
    ) -> List[Dict[str, Any]]:
        """获取通用词节点（名称在黑名单中的节点）。"""
        query = """
        MATCH (e:Entity)
        WHERE NOT e:Archived
          AND e.updated_at < (timestamp() - $skip_ms)
          AND e.name IN $words
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.mention_count AS mention_count,
               elementId(e) AS element_id
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                words=generic_words,
                skip_ms=skip_recent_seconds * 1000,
            )
            return [dict(record) for record in result]

    def archive_nodes(self, node_names: List[str], reason: str = "") -> int:
        """
        软删除节点：添加 :Archived 标签，设置 archived_at 和 archive_reason。

        Args:
            node_names: 要归档的节点名称列表
            reason: 归档原因

        Returns:
            归档的节点数
        """
        if not node_names:
            return 0
        query = """
        UNWIND $names AS n
        MATCH (e:Entity {name: n})
        WHERE NOT e:Archived
        SET e:Archived,
            e.archived_at = timestamp(),
            e.archive_reason = $reason
        RETURN count(e) AS archived
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, names=node_names, reason=reason)
            record = result.single()
            return record["archived"] if record else 0

    # ---------- 实体整合与修复（Merging）----------

    def get_similar_entity_pairs(
        self,
        skip_recent_seconds: int = 300,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取共享邻居节点的同类型实体对（候选合并对）。

        排除 meta_knowledge 类型节点（蒸馏产物不应被合并），
        排除名称过长的节点（通常是摘要性质的 [META] 节点）。
        
        优化：为了避免大规模图上的笛卡尔积导致内存溢出，
        改为先获取候选实体及其邻居集合，在 Python 端计算共享邻居数。
        """
        # 第一步：获取所有符合条件的实体类型
        types_query = """
        MATCH (a:Entity)
        WHERE NOT a:Archived
          AND a.updated_at < (timestamp() - $skip_ms)
          AND a.entity_type <> "meta_knowledge"
          AND NOT a.name STARTS WITH "[META]"
          AND size(a.name) <= 30
        RETURN DISTINCT a.entity_type AS entity_type
        """
        
        # 第二步：按类型获取实体及其邻居
        entities_query = """
        MATCH (a:Entity)
        WHERE NOT a:Archived
          AND a.entity_type = $entity_type
          AND a.updated_at < (timestamp() - $skip_ms)
          AND NOT a.name STARTS WITH "[META]"
          AND size(a.name) <= 30
        OPTIONAL MATCH (a)-[:RELATES_TO]-(neighbor:Entity)
        WHERE NOT neighbor:Archived
        WITH a, collect(elementId(neighbor)) AS neighbors
        WHERE size(neighbors) > 0
        RETURN elementId(a) AS eid,
               a.name AS name,
               a.entity_type AS entity_type,
               a.mention_count AS mention_count,
               neighbors
        """
        
        results = []
        skip_ms = skip_recent_seconds * 1000
        
        with self.driver.session(database=self._config.database) as session:
            # 获取所有有效的实体类型
            types_result = session.run(types_query, skip_ms=skip_ms)
            entity_types = [record["entity_type"] for record in types_result if record["entity_type"]]
            
            for entity_type in entity_types:
                # 获取该类型下的所有实体及其邻居
                entities_result = session.run(entities_query, entity_type=entity_type, skip_ms=skip_ms)
                
                # 转换为 Python 列表以进行两两比较
                entities = []
                for record in entities_result:
                    entities.append({
                        "eid": record["eid"],
                        "name": record["name"],
                        "type": record["entity_type"],
                        "mentions": record["mention_count"],
                        "neighbors": set(record["neighbors"])
                    })
                
                # 在 Python 端计算共享邻居
                n = len(entities)
                for i in range(n):
                    for j in range(i + 1, n):
                        a = entities[i]
                        b = entities[j]
                        
                        # 确保 a 的 elementId < b 的 elementId（保持与原逻辑一致，避免重复对）
                        if a["eid"] >= b["eid"]:
                            a, b = b, a
                            
                        shared_neighbors = len(a["neighbors"].intersection(b["neighbors"]))
                        
                        if shared_neighbors >= 2:
                            results.append({
                                "name_a": a["name"],
                                "eid_a": a["eid"],
                                "type_a": a["type"],
                                "mentions_a": a["mentions"],
                                "name_b": b["name"],
                                "eid_b": b["eid"],
                                "type_b": b["type"],
                                "mentions_b": b["mentions"],
                                "shared_neighbors": shared_neighbors
                            })
                            
        # 按共享邻居数降序排序，并截取 limit 个结果
        results.sort(key=lambda x: x["shared_neighbors"], reverse=True)
        return results[:limit]

    def get_duplicate_entities(
        self,
        max_copies_per_name: int = 10,
    ) -> list:
        """
        获取所有同名的重复实体（用于合并）。

        返回 [(name, [eid_a, eid_b, ...], [mention_a, mention_b, ...]), ...]
        """
        query = """
        MATCH (e:Entity)
        WHERE NOT e:Archived
        WITH e.name AS name, collect(elementId(e)) AS eids, collect(e.mention_count) AS mentions, count(e) AS cnt
        WHERE cnt > 1 AND cnt <= $max_copies
          AND size(name) > 0
        RETURN name, eids, mentions
        ORDER BY cnt DESC
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, max_copies=max_copies_per_name)
            return [(row["name"], row["eids"], row["mentions"]) for row in result]

    def get_short_name_entities(
        self,
        max_name_length: int = 2,
        skip_recent_seconds: int = 300,
    ) -> List[Dict[str, Any]]:
        """获取短名实体及其邻居，用于审计或进一步筛选。"""
        query = """
        MATCH (e:Entity)
        WHERE NOT e:Archived
          AND e.updated_at < (timestamp() - $skip_ms)
          AND size(e.name) <= $max_len
        OPTIONAL MATCH (e)-[r:RELATES_TO]-(neighbor:Entity)
        WHERE NOT neighbor:Archived
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.mention_count AS mention_count,
               collect(DISTINCT neighbor.name) AS neighbor_names,
               elementId(e) AS element_id
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                max_len=max_name_length,
                skip_ms=skip_recent_seconds * 1000,
            )
            return [dict(record) for record in result]

    def get_truncated_entity_candidates(
        self,
        max_name_length: int = 2,
        skip_recent_seconds: int = 300,
    ) -> List[Dict[str, Any]]:
        """获取更可能是真实异常截断的实体候选，避免把所有短名都送去修复。"""
        short_entities = self.get_short_name_entities(
            max_name_length=max_name_length,
            skip_recent_seconds=skip_recent_seconds,
        )

        generic_allowlist = {
            "消息总结", "用户发送", "关键指标", "积压节点", "进程管理", "任务调度", "平台运行",
            "技术细节", "技术要点", "知识图谱", "通货膨胀", "版本信息", "功能测试", "默认值",
            "初始化", "核心实体", "主要实体", "结构", "属性", "效果", "明白", "张三",
        }
        review_types = {"person", "place", "organization", "technology"}

        candidates = []
        for entity in short_entities:
            name = (entity.get("name") or "").strip()
            entity_type = (entity.get("entity_type") or "").strip()
            mention_count = entity.get("mention_count") or 0
            neighbor_names = entity.get("neighbor_names") or []

            if not name:
                continue
            if name in generic_allowlist:
                continue
            if entity_type in review_types and mention_count >= 2:
                continue
            if len(name) <= 1:
                candidates.append(entity)
                continue
            if len(name) <= 2 and not neighbor_names:
                candidates.append(entity)
                continue
            if len(name) <= max_name_length and mention_count <= 1 and not neighbor_names:
                candidates.append(entity)

        return candidates

    def get_entities_missing_metadata(
        self,
        skip_recent_seconds: int = 300,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取缺少描述的实体及其邻居关系。"""
        query = """
        MATCH (e:Entity)
        WHERE NOT e:Archived
          AND e.updated_at < (timestamp() - $skip_ms)
          AND (e.description IS NULL OR e.description = "")
        OPTIONAL MATCH (e)-[r:RELATES_TO]-(neighbor:Entity)
        WHERE NOT neighbor:Archived
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.mention_count AS mention_count,
               e.properties AS properties,
               collect(DISTINCT {
                   name: neighbor.name,
                   type: neighbor.entity_type,
                   rel: r.relation_type
               }) AS neighbors,
               elementId(e) AS element_id
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                skip_ms=skip_recent_seconds * 1000,
                limit=limit,
            )
            return [dict(record) for record in result]

    def merge_entity_nodes(
        self,
        main_eid: str,
        alias_eid: str,
        new_aliases: Optional[List[str]] = None,
    ) -> bool:
        """
        合并两个实体节点：将 alias_eid 的所有关系转移到 main_eid，
        然后将 alias_eid 归档。

        Args:
            main_eid: 主节点的 elementId（保留）
            alias_eid: 别名节点的 elementId（将被归档）
            new_aliases: 更新后的别名列表

        Returns:
            是否成功
        """
        logger.info(
            "Attempting to merge entities: %s (alias) -> %s (main)",
            alias_eid, main_eid
        )
        # 步骤 1：将 alias 的出边转移到 main
        transfer_out = """
        MATCH (alias:Entity)-[r:RELATES_TO]->(target:Entity)
        MATCH (main:Entity)
        WHERE elementId(alias) = $alias_eid AND elementId(main) = $main_eid
          AND NOT alias:Archived AND NOT main:Archived
          AND main <> target
        MERGE (main)-[nr:RELATES_TO {relation_type: r.relation_type}]->(target)
        ON CREATE SET
            nr.properties = r.properties,
            nr.created_at = r.created_at,
            nr.updated_at = timestamp(),
            nr.mention_count = r.mention_count
        ON MATCH SET
            nr.updated_at = timestamp(),
            nr.mention_count = CASE WHEN coalesce(nr.mention_count, 0) + coalesce(r.mention_count, 0) > 999999 THEN 999999 ELSE coalesce(nr.mention_count, 0) + coalesce(r.mention_count, 0) END
        DELETE r
        RETURN count(nr) AS transferred
        """
        # 步骤 2：将 alias 的入边转移到 main
        transfer_in = """
        MATCH (source:Entity)-[r:RELATES_TO]->(alias:Entity)
        MATCH (main:Entity)
        WHERE elementId(alias) = $alias_eid AND elementId(main) = $main_eid
          AND NOT alias:Archived AND NOT main:Archived
          AND source <> main
        MERGE (source)-[nr:RELATES_TO {relation_type: r.relation_type}]->(main)
        ON CREATE SET
            nr.properties = r.properties,
            nr.created_at = r.created_at,
            nr.updated_at = timestamp(),
            nr.mention_count = r.mention_count
        ON MATCH SET
            nr.updated_at = timestamp(),
            nr.mention_count = CASE WHEN coalesce(nr.mention_count, 0) + coalesce(r.mention_count, 0) > 999999 THEN 999999 ELSE coalesce(nr.mention_count, 0) + coalesce(r.mention_count, 0) END
        DELETE r
        RETURN count(nr) AS transferred
        """
        # 步骤 3：更新 main 的 aliases 属性，归档 alias
        archive_alias = """
        MATCH (main:Entity)
        WHERE elementId(main) = $main_eid
        SET main.aliases = $aliases,
            main.mention_count = CASE WHEN coalesce(main.mention_count, 0) + $extra_mentions > 999999 THEN 999999 ELSE coalesce(main.mention_count, 0) + $extra_mentions END,
            main.updated_at = timestamp()
        WITH main
        MATCH (alias:Entity)
        WHERE elementId(alias) = $alias_eid AND NOT alias:Archived
        SET alias:Archived,
            alias.archived_at = timestamp(),
            alias.archive_reason = "merged_into:" + main.name
        RETURN main.name AS main_name
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                # 获取 alias 的 mention_count
                alias_info = session.run(
                    "MATCH (e:Entity) WHERE elementId(e) = $eid AND NOT e:Archived "
                    "RETURN coalesce(e.mention_count, 0) AS mc, "
                    "coalesce(e.aliases, []) AS existing_aliases, "
                    "e.name AS name",
                    eid=alias_eid,
                ).single()
                if not alias_info:
                    return False

                extra_mentions = alias_info["mc"]
                actual_alias_name = alias_info["name"]

                # 转移出边
                session.run(transfer_out, alias_eid=alias_eid, main_eid=main_eid)
                # 转移入边
                session.run(transfer_in, alias_eid=alias_eid, main_eid=main_eid)

                # 构建别名列表
                aliases = list(new_aliases) if new_aliases else []
                if actual_alias_name not in aliases:
                    aliases.append(actual_alias_name)

                # 归档
                session.run(
                    archive_alias,
                    main_eid=main_eid,
                    alias_eid=alias_eid,
                    aliases=json.dumps(aliases, ensure_ascii=False),
                    extra_mentions=extra_mentions,
                )
                logger.info(
                    "Successfully merged entity %s (alias) into %s (main), archived alias",
                    alias_eid, main_eid
                )
                return True
        except Exception as e:
            logger.error("Failed to merge entities %s -> %s: %s", alias_eid, main_eid, e)
            return False

    def update_entity_name(self, old_name: str, new_name: str, entity_type: str) -> bool:
        """
        修复截断实体：更新节点名称，保留版本历史。

        Args:
            old_name: 旧名称
            new_name: 修复后的新名称
            entity_type: 实体类型

        Returns:
            是否成功
        """
        query = """
        MATCH (e:Entity {name: $old_name, entity_type: $entity_type})
        WHERE NOT e:Archived
        SET e.name = $new_name,
            e.updated_at = timestamp(),
            e.history = coalesce(e.history, []) + [$history_entry]
        RETURN e.name AS name
        """
        history_entry = json.dumps(
            {"field": "name", "old_value": old_name, "new_value": new_name,
             "changed_at": int(time.time() * 1000), "changed_by": "meditation"},
            ensure_ascii=False,
        )
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(
                    query,
                    old_name=old_name,
                    new_name=new_name,
                    entity_type=entity_type,
                    history_entry=history_entry,
                )
                return result.single() is not None
        except Exception as e:
            logger.error("Failed to update entity name %s -> %s: %s", old_name, new_name, e)
            return False

    def update_entity_metadata(
        self,
        name: str,
        entity_type: Optional[str] = None,
        description: Optional[str] = None,
        new_entity_type: Optional[str] = None,
    ) -> bool:
        """
        补充实体的类型和描述信息，保留版本历史。

        Args:
            name: 实体名称
            entity_type: 当前实体类型（用于匹配）
            description: 新的描述
            new_entity_type: 新的实体类型（如果需要修正）

        Returns:
            是否成功
        """
        set_clauses = ["e.updated_at = timestamp()"]
        params: Dict[str, Any] = {"name": name}
        history_entries = []

        if description:
            set_clauses.append("e.description = $description")
            params["description"] = description
            history_entries.append(json.dumps(
                {"field": "description", "new_value": description,
                 "changed_at": int(time.time() * 1000), "changed_by": "meditation"},
                ensure_ascii=False,
            ))

        if new_entity_type and new_entity_type != entity_type:
            set_clauses.append("e.entity_type = $new_entity_type")
            params["new_entity_type"] = new_entity_type
            history_entries.append(json.dumps(
                {"field": "entity_type", "old_value": entity_type,
                 "new_value": new_entity_type,
                 "changed_at": int(time.time() * 1000), "changed_by": "meditation"},
                ensure_ascii=False,
            ))

        if not set_clauses or (not description and not new_entity_type):
            return False

        # 追加历史记录
        for entry in history_entries:
            set_clauses.append(f"e.history = coalesce(e.history, []) + ['{entry}']")

        match_clause = "MATCH (e:Entity {name: $name})"
        if entity_type:
            match_clause = f"MATCH (e:Entity {{name: $name, entity_type: $entity_type}})"
            params["entity_type"] = entity_type

        query = f"""
        {match_clause}
        WHERE NOT e:Archived
        SET {', '.join(set_clauses)}
        RETURN e.name AS name
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(query, **params)
                return result.single() is not None
        except Exception as e:
            logger.error("Failed to update metadata for %s: %s", name, e)
            return False

    # ---------- 关系推理与重标注（Restructuring）----------

    def get_related_to_edges(
        self,
        skip_recent_seconds: int = 300,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """获取所有 relation_type='related_to' 的边（用于关系重标注）。"""
        query = """
        MATCH (src:Entity)-[r:RELATES_TO]->(tgt:Entity)
        WHERE NOT src:Archived AND NOT tgt:Archived
          AND r.relation_type = "related_to"
          AND r.updated_at < (timestamp() - $skip_ms)
        RETURN src.name AS source_name,
               src.entity_type AS source_type,
               tgt.name AS target_name,
               tgt.entity_type AS target_type,
               r.mention_count AS mention_count,
               r.properties AS properties,
               elementId(r) AS rel_element_id
        ORDER BY r.mention_count DESC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                skip_ms=skip_recent_seconds * 1000,
                limit=limit,
            )
            return [dict(record) for record in result]

    def update_relation_type(
        self,
        source_name: str,
        target_name: str,
        old_relation_type: str,
        new_relation_type: str,
        rel_element_id: Optional[str] = None,
    ) -> bool:
        """
        更新关系的 relation_type 属性。
        保留原始 RELATES_TO 标签以兼容现有查询。

        Args:
            source_name: 源实体名称
            target_name: 目标实体名称
            old_relation_type: 旧关系类型
            new_relation_type: 新关系类型
            rel_element_id: 【新参数】关系的 elementId（优先使用，避免 name 匹配失败）

        Returns:
            是否成功
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                if rel_element_id:
                    # ★ 优先路径：用 elementId 精确匹配边
                    query = """
                    MATCH ()-[r:RELATES_TO]->()
                    WHERE elementId(r) = $element_id
                      AND r.relation_type = $old_type
                    SET r.relation_type = $new_type,
                        r.original_relation_type = $old_type,
                        r.relabeled_by = "meditation",
                        r.relabeled_at = timestamp(),
                        r.updated_at = timestamp()
                    RETURN type(r) AS rel_type
                    """
                    result = session.run(
                        query,
                        element_id=rel_element_id,
                        old_type=old_relation_type,
                        new_type=new_relation_type,
                    )
                else:
                    # 回退路径：用 entity name 匹配（兼容旧调用）
                    query = """
                    MATCH (src:Entity {name: $source})-[r:RELATES_TO {relation_type: $old_type}]->(tgt:Entity {name: $target})
                    WHERE NOT src:Archived AND NOT tgt:Archived
                    SET r.relation_type = $new_type,
                        r.original_relation_type = $old_type,
                        r.relabeled_by = "meditation",
                        r.relabeled_at = timestamp(),
                        r.updated_at = timestamp()
                    RETURN type(r) AS rel_type
                    """
                    # 先检查边是否存在
                    check_query = """
                    MATCH (src:Entity {name: $source})-[r:RELATES_TO]->(tgt:Entity {name: $target})
                    WHERE NOT src:Archived AND NOT tgt:Archived
                    RETURN elementId(r) AS eid, r.relation_type AS current_type
                    """
                    check_result = session.run(check_query, source=source_name, target=target_name)
                    check_record = check_result.single()
                    if check_record:
                        if check_record["current_type"] != old_relation_type:
                            logger.warning(
                                "Relation type mismatch: %s->%s expected %s but has %s",
                                source_name, target_name, old_relation_type, check_record["current_type"]
                            )
                            return False
                    else:
                        logger.warning(
                            "No relation found to relabel: %s->%s",
                            source_name, target_name
                        )
                        return False

                    result = session.run(
                        query,
                        source=source_name,
                        target=target_name,
                        old_type=old_relation_type,
                        new_type=new_relation_type,
                    )

                success = result.single() is not None
                if success:
                    logger.info(
                        "Successfully relabeled: %s->%s [%s→%s]%s",
                        source_name, target_name, old_relation_type, new_relation_type,
                        f" (id={rel_element_id})" if rel_element_id else ""
                    )
                else:
                    logger.warning(
                        "Relabel query matched nothing: %s->%s%s",
                        source_name, target_name,
                        f" (id={rel_element_id})" if rel_element_id else ""
                    )
                return success
        except Exception as e:
            logger.error(
                "Failed to update relation type %s->%s from %s to %s: %s",
                source_name, target_name, old_relation_type, new_relation_type, e,
            )
            return False

    def create_inferred_relation(
        self,
        source_name: str,
        target_name: str,
        relation_type: str,
        confidence: float = 0.5,
    ) -> bool:
        """
        创建推断出的新关系。

        Args:
            source_name: 源实体名称
            target_name: 目标实体名称
            relation_type: 关系类型
            confidence: 推断置信度

        Returns:
            是否成功
        """
        query = """
        MATCH (src:Entity {name: $source})
        MATCH (tgt:Entity {name: $target})
        WHERE NOT src:Archived AND NOT tgt:Archived
        MERGE (src)-[r:RELATES_TO {relation_type: $rel_type}]->(tgt)
        ON CREATE SET
            r.created_at = timestamp(),
            r.updated_at = timestamp(),
            r.mention_count = 0,
            r.inferred_by = "meditation",
            r.inference_confidence = $confidence,
            r.properties = "{}"
        RETURN type(r) AS rel_type
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(
                    query,
                    source=source_name,
                    target=target_name,
                    rel_type=relation_type,
                    confidence=confidence,
                )
                return result.single() is not None
        except Exception as e:
            logger.error(
                "Failed to create inferred relation %s-[%s]->%s: %s",
                source_name, relation_type, target_name, e,
            )
            return False

    # ---------- 权重强化与衰减（Weighting）----------

    def get_all_active_nodes_for_weighting(
        self,
        skip_recent_seconds: int = 300,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """获取所有活跃节点及其度数用于权重计算。"""
        query = """
        MATCH (e:Entity)
        WHERE NOT e:Archived
          AND e.updated_at < (timestamp() - $skip_ms)
        OPTIONAL MATCH (e)-[r:RELATES_TO]-()
        WITH e, count(r) AS degree
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.mention_count AS mention_count,
               e.created_at AS created_at,
               e.updated_at AS updated_at,
               e.activation_level AS activation_level,
               e.semantic_score AS semantic_score,
               degree,
               elementId(e) AS element_id
        ORDER BY degree DESC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                skip_ms=skip_recent_seconds * 1000,
                limit=limit,
            )
            return [dict(record) for record in result]

    def batch_update_weights(
        self,
        updates: List[Dict[str, Any]],
    ) -> int:
        """
        批量更新节点的权重属性。

        Args:
            updates: 更新列表，每个元素包含：
                - name: 实体名称
                - activation_level: 新的激活值
                - semantic_score: 语义评分（可选）

        Returns:
            成功更新的节点数
        """
        if not updates:
            return 0
        query = """
        UNWIND $updates AS u
        MATCH (e:Entity {name: u.name})
        WHERE NOT e:Archived
        SET e.activation_level = u.activation_level,
            e.semantic_score = CASE WHEN u.semantic_score IS NOT NULL
                               THEN u.semantic_score
                               ELSE e.semantic_score END,
            e.weight_updated_at = timestamp()
        RETURN count(e) AS updated
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(query, updates=updates)
                record = result.single()
                return record["updated"] if record else 0
        except Exception as e:
            logger.error("Failed to batch update weights: %s", e)
            return 0

    # ---------- 知识蒸馏（Distillation）----------

    def get_dense_subgraphs_for_distillation(
        self,
        min_cluster_size: int = 5,
        limit: int = 10,
        skip_recent_seconds: int = 0,
        priority_entity_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取高密度子图用于知识蒸馏。
        查找以高度数节点为中心的节点簇。
        """
        query = """
        MATCH (center:Entity)-[r:RELATES_TO]-(neighbor:Entity)
        WHERE NOT center:Archived AND NOT neighbor:Archived
          AND center.entity_type <> "meta_knowledge"
          AND (
            $skip_recent_ms <= 0
            OR center.last_distilled_at IS NULL
            OR center.last_distilled_at < timestamp() - $skip_recent_ms
          )
        WITH center, collect(DISTINCT neighbor) AS neighbors, count(DISTINCT r) AS edge_count
        WHERE size(neighbors) >= $min_size
        WITH center, neighbors, edge_count,
             size([n IN neighbors WHERE n.name IN $priority_names]) + CASE WHEN center.name IN $priority_names THEN 1 ELSE 0 END AS priority_overlap
        RETURN center.name AS center_name,
               center.entity_type AS center_type,
               [n IN neighbors | {name: n.name, type: n.entity_type, source_tag: coalesce(n.source_tag, ''), import_batch: coalesce(n.import_batch, '')}] AS neighbor_list,
               edge_count,
               size(neighbors) AS neighbor_count,
               priority_overlap
        ORDER BY priority_overlap DESC, edge_count DESC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                min_size=min_cluster_size,
                limit=limit,
                skip_recent_ms=max(0, skip_recent_seconds) * 1000,
                priority_names=priority_entity_names or [],
            )
            return [dict(record) for record in result]

    def get_cluster_edges(
        self,
        center_name: str,
        neighbor_names: List[str],
    ) -> List[Dict[str, Any]]:
        """
        获取一个簇内所有节点之间的关系（用于蒸馏 prompt 构建）。

        Args:
            center_name: 中心节点名称
            neighbor_names: 邻居节点名称列表

        Returns:
            簇内的关系列表
        """
        all_names = [center_name] + neighbor_names
        query = """
        UNWIND $names AS n1
        UNWIND $names AS n2
        WITH n1, n2 WHERE n1 <> n2
        MATCH (a:Entity {name: n1})-[r:RELATES_TO]->(b:Entity {name: n2})
        WHERE NOT a:Archived AND NOT b:Archived
        RETURN DISTINCT a.name AS source,
               b.name AS target,
               r.relation_type AS relation_type
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, names=all_names)
            return [dict(record) for record in result]

    def _text_jaccard(self, a: str, b: str) -> float:
        """计算两段文本的 Jaccard 相似度（基于字符 bigram）。"""
        if not a or not b:
            return 0.0
        def ngrams(s, n=2):
            return set(s[i:i+n] for i in range(len(s) - n + 1))
        sa, sb = ngrams(a), ngrams(b)
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    def _build_meta_cluster_signature(self, related_entity_names: List[str]) -> str:
        normalized = sorted({name.strip().lower() for name in related_entity_names if name and name.strip()})
        raw = "|".join(normalized)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def _find_meta_knowledge_by_signature(
        self,
        cluster_signature: str,
        meta_entity_type: str = "meta_knowledge",
    ) -> Optional[str]:
        query = """
        MATCH (m:Entity {entity_type: $entity_type, cluster_signature: $cluster_signature})
        RETURN m.name AS name
        LIMIT 1
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                record = session.run(
                    query,
                    entity_type=meta_entity_type,
                    cluster_signature=cluster_signature,
                ).single()
                return record["name"] if record else None
        except Exception as e:
            logger.warning("Failed to find meta knowledge by signature: %s", e)
            return None

    def _find_similar_meta_knowledge(
        self,
        summary: str,
        similarity_threshold: float = 0.85,
    ) -> Optional[str]:
        """
        查找与给定摘要语义相似的已有元知识节点。

        使用 Jaccard bigram 相似度，超过阈值则认为重复。

        Returns:
            相似节点的名称，或 None
        """
        query = """
        MATCH (m:Entity {entity_type: "meta_knowledge"})
        WHERE m.description IS NOT NULL
        RETURN m.name AS name, m.description AS description
        LIMIT 200
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(query)
                for record in result:
                    desc = record["description"]
                    sim = self._text_jaccard(summary, desc)
                    if sim >= similarity_threshold:
                        return record["name"]
        except Exception as e:
            logger.warning("Failed to find similar meta knowledge: %s", e)
        return None

    def create_meta_knowledge_node(
        self,
        summary: str,
        related_entity_names: List[str],
        meta_entity_type: str = "meta_knowledge",
        summarizes_rel_type: str = "SUMMARIZES",
        center_entity_name: Optional[str] = None,
        meditation_run_id: Optional[str] = None,
        source_tag: Optional[str] = None,
        import_batch: Optional[str] = None,
        probe_entity_names: Optional[List[str]] = None,
        probe_overlap_count: int = 0,
    ) -> bool:
        """
        创建元知识节点并建立到底层事实节点的 SUMMARIZES 关系。

        创建前会检查是否存在语义相似的已有元知识节点（Jaccard 相似度 > 0.85），
        若存在则复用该节点并更新描述和关系，避免产生大量重复的 META 节点。

        Args:
            summary: 元知识摘要文本
            related_entity_names: 相关底层实体名称列表
            meta_entity_type: 元知识节点的实体类型
            summarizes_rel_type: 到底层事实的关系类型

        Returns:
            是否成功
        """
        cluster_signature = self._build_meta_cluster_signature(related_entity_names)

        # 去重优先级 1: 同一簇签名直接复用
        existing_name = self._find_meta_knowledge_by_signature(cluster_signature, meta_entity_type)
        if not existing_name:
            # 去重优先级 2: 文本相似度兜底
            existing_name = self._find_similar_meta_knowledge(summary, similarity_threshold=0.85)
        if existing_name:
            # 复用已有节点：更新描述并建立新关系
            reuse_query = """
            MATCH (m:Entity {name: $name, entity_type: $entity_type})
            SET m.description = $summary,
                m.updated_at = timestamp(),
                m.cluster_signature = $cluster_signature,
                m.mention_count = coalesce(m.mention_count, 0) + 1,
                m.meditation_run_id = coalesce($meditation_run_id, m.meditation_run_id),
                m.source_tag = coalesce($source_tag, m.source_tag),
                m.import_batch = coalesce($import_batch, m.import_batch),
                m.probe_entity_names = coalesce($probe_entity_names, m.probe_entity_names),
                m.probe_overlap_count = CASE WHEN $probe_overlap_count > 0 THEN $probe_overlap_count ELSE coalesce(m.probe_overlap_count, 0) END
            RETURN elementId(m) AS eid
            """
            link_query = """
            MATCH (m:Entity {name: $meta_name, entity_type: $entity_type})
            MATCH (e:Entity {name: $entity_name})
            WHERE NOT e:Archived
            MERGE (m)-[r:RELATES_TO {relation_type: $rel_type}]->(e)
            ON CREATE SET
                r.created_at = timestamp(),
                r.updated_at = timestamp(),
                r.mention_count = 1,
                r.properties = "{}",
                r.meditation_run_id = $meditation_run_id,
                r.source_tag = $source_tag,
                r.import_batch = $import_batch
            ON MATCH SET
                r.updated_at = timestamp(),
                r.meditation_run_id = coalesce($meditation_run_id, r.meditation_run_id),
                r.source_tag = coalesce($source_tag, r.source_tag),
                r.import_batch = coalesce($import_batch, r.import_batch)
            RETURN type(r) AS rel_type
            """
            touch_center_query = """
            MATCH (e:Entity {name: $center_name})
            WHERE NOT e:Archived
            SET e.last_distilled_at = timestamp()
            """
            try:
                with self.driver.session(database=self._config.database) as session:
                    session.run(
                        reuse_query,
                        name=existing_name,
                        entity_type=meta_entity_type,
                        summary=summary,
                        cluster_signature=cluster_signature,
                        meditation_run_id=meditation_run_id,
                        source_tag=source_tag,
                        import_batch=import_batch,
                        probe_entity_names=probe_entity_names,
                        probe_overlap_count=probe_overlap_count,
                    )
                    for entity_name in related_entity_names:
                        session.run(
                            link_query,
                            meta_name=existing_name,
                            entity_type=meta_entity_type,
                            entity_name=entity_name,
                            rel_type=summarizes_rel_type,
                            meditation_run_id=meditation_run_id,
                            source_tag=source_tag,
                            import_batch=import_batch,
                        )
                    if center_entity_name:
                        session.run(touch_center_query, center_name=center_entity_name)
                logger.info("Reused similar meta knowledge node: %s", existing_name)
                return True
            except Exception as e:
                logger.error("Failed to reuse meta knowledge node: %s", e)
                return False

        # 无相似节点，创建新节点
        meta_name = f"[META] {summary[:50]}..." if len(summary) > 50 else f"[META] {summary}"

        create_query = """
        MERGE (m:Entity {name: $name, entity_type: $entity_type})
        ON CREATE SET
            m.description = $summary,
            m.created_at = timestamp(),
            m.updated_at = timestamp(),
            m.cluster_signature = $cluster_signature,
            m.mention_count = 1,
            m.created_by = "meditation",
            m.activation_level = 1.0,
            m.meditation_run_id = $meditation_run_id,
            m.source_tag = $source_tag,
            m.import_batch = $import_batch,
            m.probe_entity_names = $probe_entity_names,
            m.probe_overlap_count = $probe_overlap_count
        ON MATCH SET
            m.description = $summary,
            m.updated_at = timestamp(),
            m.cluster_signature = $cluster_signature,
            m.meditation_run_id = coalesce($meditation_run_id, m.meditation_run_id),
            m.source_tag = coalesce($source_tag, m.source_tag),
            m.import_batch = coalesce($import_batch, m.import_batch),
            m.probe_entity_names = coalesce($probe_entity_names, m.probe_entity_names),
            m.probe_overlap_count = CASE WHEN $probe_overlap_count > 0 THEN $probe_overlap_count ELSE coalesce(m.probe_overlap_count, 0) END
        RETURN elementId(m) AS eid
        """
        link_query = """
        MATCH (m:Entity {name: $meta_name, entity_type: $entity_type})
        MATCH (e:Entity {name: $entity_name})
        WHERE NOT e:Archived
        MERGE (m)-[r:RELATES_TO {relation_type: $rel_type}]->(e)
        ON CREATE SET
            r.created_at = timestamp(),
            r.updated_at = timestamp(),
            r.mention_count = 1,
            r.properties = "{}"
        RETURN type(r) AS rel_type
        """
        touch_center_query = """
        MATCH (e:Entity {name: $center_name})
        WHERE NOT e:Archived
        SET e.last_distilled_at = timestamp()
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(
                    create_query,
                    name=meta_name,
                    entity_type=meta_entity_type,
                    summary=summary,
                    cluster_signature=cluster_signature,
                    meditation_run_id=meditation_run_id,
                    source_tag=source_tag,
                    import_batch=import_batch,
                    probe_entity_names=probe_entity_names,
                    probe_overlap_count=probe_overlap_count,
                )
                if not result.single():
                    return False

                for entity_name in related_entity_names:
                    session.run(
                        link_query,
                        meta_name=meta_name,
                        entity_type=meta_entity_type,
                        entity_name=entity_name,
                        rel_type=summarizes_rel_type,
                        meditation_run_id=meditation_run_id,
                        source_tag=source_tag,
                        import_batch=import_batch,
                    )
                if center_entity_name:
                    session.run(touch_center_query, center_name=center_entity_name)
                return True
        except Exception as e:
            logger.error("Failed to create meta knowledge node: %s", e)
            return False

    # ---------- 安全与统计 ----------

    def create_meditation_snapshot(self, node_names: List[str]) -> Optional[str]:
        """
        为指定节点创建快照数据（JSON 格式）。

        Args:
            node_names: 要快照的节点名称列表

        Returns:
            快照 JSON 字符串，失败返回 None
        """
        query = """
        UNWIND $names AS n
        MATCH (e:Entity {name: n})
        OPTIONAL MATCH (e)-[r:RELATES_TO]-(other:Entity)
        RETURN e.name AS name,
               e.entity_type AS entity_type,
               e.properties AS properties,
               e.mention_count AS mention_count,
               e.description AS description,
               e.activation_level AS activation_level,
               e.aliases AS aliases,
               collect(DISTINCT {
                   other_name: other.name,
                   relation_type: r.relation_type,
                   direction: CASE WHEN startNode(r) = e THEN "out" ELSE "in" END
               }) AS relations
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(query, names=node_names)
                records = [dict(record) for record in result]
                return json.dumps(records, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error("Failed to create meditation snapshot: %s", e)
            return None

    def get_change_counts_since(self, timestamp_ms: int) -> Dict[str, int]:
        """
        获取自指定时间戳以来的变化量统计。

        Args:
            timestamp_ms: 起始时间戳（毫秒）

        Returns:
            {"new_nodes": N, "new_edges": M}
        """
        query = """
        OPTIONAL MATCH (e:Entity)
        WHERE NOT e:Archived AND e.created_at > $ts
        WITH count(e) AS new_nodes
        OPTIONAL MATCH ()-[r:RELATES_TO]->()
        WHERE r.created_at > $ts
        RETURN new_nodes, count(r) AS new_edges
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, ts=timestamp_ms)
            record = result.single()
            if record:
                return {
                    "new_nodes": record["new_nodes"] or 0,
                    "new_edges": record["new_edges"] or 0,
                }
            return {"new_nodes": 0, "new_edges": 0}

    def get_feedback_stats(self) -> Dict[str, Any]:
        """获取反馈节点统计信息（用于冥思进化分析）。"""
        query = """
        OPTIONAL MATCH (f:Feedback)
        WITH count(f) AS total_count
        OPTIONAL MATCH (f:Feedback {success: true})
        WITH total_count, count(f) AS success_count
        OPTIONAL MATCH (f:Feedback {success: false})
        WITH total_count, success_count, count(f) AS failure_count
        RETURN total_count, success_count, failure_count
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query)
            record = result.single()
            if record:
                return {
                    "total_feedback": record["total_count"] or 0,
                    "successful": record["success_count"] or 0,
                    "failed": record["failure_count"] or 0,
                }
            return {"total_feedback": 0, "successful": 0, "failed": 0}

    def get_feedback_trends(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取反馈趋势（按时间排序），用于冥思分析。"""
        query = """
        MATCH (f:Feedback)
        RETURN f.query AS query,
               f.success AS success,
               f.confidence AS confidence,
               f.applied_strategy_name AS strategy,
               f.validation_status AS validation_status,
               f.result_count AS result_count,
               f.noise_entities AS noise_entities,
               f.timestamp AS timestamp,
               f.error_msg AS error_msg
        ORDER BY f.timestamp DESC
        LIMIT $limit
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]

    def get_meditation_stats(self) -> Dict[str, Any]:
        """获取冥思相关的统计信息。"""
        query = """
        OPTIONAL MATCH (needs:Entity {needs_meditation: true})
        WHERE NOT needs:Archived
        WITH count(needs) AS pending_count
        OPTIONAL MATCH (archived:Entity:Archived)
        WITH pending_count, count(archived) AS archived_count
        OPTIONAL MATCH (meta:Entity {entity_type: "meta_knowledge"})
        WHERE NOT meta:Archived
        WITH pending_count, archived_count, count(meta) AS meta_count
        OPTIONAL MATCH ()-[r:RELATES_TO {relation_type: "related_to"}]->()
        RETURN pending_count,
               archived_count,
               meta_count,
               count(r) AS generic_relation_count
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query)
            record = result.single()
            if record:
                return {
                    "pending_meditation": record["pending_count"] or 0,
                    "archived_nodes": record["archived_count"] or 0,
                    "meta_knowledge_nodes": record["meta_count"] or 0,
                    "generic_relations": record["generic_relation_count"] or 0,
                }
            return {
                "pending_meditation": 0,
                "archived_nodes": 0,
                "meta_knowledge_nodes": 0,
                "generic_relations": 0,
            }

    # ================================================================
    # Phase 2: 策略持久化方法
    # ================================================================

    # ========== 策略节点操作 ==========

    def upsert_strategy_node(self, strategy_data: Dict[str, Any]) -> str:
        """
        插入或更新策略节点。

        Args:
            strategy_data: 策略摘要字典，来自 RealWorldStrategy.get_summary()

        Returns:
            节点的 elementId
        """
        query = """
        MERGE (s:Strategy {name: $name})
        ON CREATE SET
            s.strategy_type = $strategy_type,
            s.uses_real_data = $uses_real_data,
            s.fitness_score = $fitness_score,
            s.real_world_bonus = $real_world_bonus,
            s.avg_accuracy = $avg_accuracy,
            s.avg_success = $avg_success,
            s.avg_cost = $avg_cost,
            s.usage_count = $usage_count,
            s.created_at = $created_at,
            s.updated_at = timestamp(),
            s.evolution_steps = $evolution_steps,
            s.needs_meditation = true,
            s.content = $content,
            s.description = $description,
            s.applicable_scenarios = $applicable_scenarios,
            s.source = $source
        ON MATCH SET
            s.fitness_score = $fitness_score,
            s.real_world_bonus = $real_world_bonus,
            s.avg_accuracy = $avg_accuracy,
            s.avg_success = $avg_success,
            s.avg_cost = $avg_cost,
            s.usage_count = $usage_count,
            s.updated_at = timestamp(),
            s.evolution_steps = $evolution_steps,
            s.needs_meditation = true,
            s.content = $content,
            s.description = $description,
            s.applicable_scenarios = $applicable_scenarios,
            s.source = $source
        RETURN elementId(s) AS eid
        """
        perf = strategy_data.get("performance", {})
        meta = strategy_data.get("metadata", {})
        content = strategy_data.get("content") or meta.get("description", "") or ""
        description = strategy_data.get("description") or meta.get("description", "") or content
        applicable_scenarios = (
            strategy_data.get("applicable_scenarios")
            or meta.get("applicable_scenarios", [])
            or []
        )
        source = strategy_data.get("source") or meta.get("source", "unknown")
        created_at = strategy_data.get("created_at") or meta.get("created_at", "")
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                name=strategy_data["name"],
                strategy_type=strategy_data.get("type", strategy_data.get("strategy_type", "unknown")),
                uses_real_data=strategy_data.get("uses_real_data", False),
                fitness_score=strategy_data.get("fitness", strategy_data.get("fitness_score", 0.0)),
                real_world_bonus=strategy_data.get("real_world_bonus", 0.0),
                avg_accuracy=perf.get("avg_accuracy", strategy_data.get("avg_accuracy", 0.0)),
                avg_success=perf.get("avg_success", strategy_data.get("avg_success", 0.0)),
                avg_cost=perf.get("avg_cost", strategy_data.get("avg_cost", 0.0)),
                usage_count=perf.get("usage_count", strategy_data.get("usage_count", 0)),
                created_at=created_at,
                evolution_steps=meta.get("evolution_steps", strategy_data.get("evolution_steps", 0)),
                content=content,
                description=description,
                applicable_scenarios=applicable_scenarios,
                source=source,
            )
            record = result.single()
            return record["eid"] if record else ""

    def create_evolution_link(
        self, child_name: str, parent1_name: str, parent2_name: str
    ) -> None:
        """记录策略进化谱系（交叉产生的子策略指向两个父策略）。"""
        query = """
        MATCH (child:Strategy {name: $child_name})
        MATCH (p1:Strategy {name: $parent1_name})
        MATCH (p2:Strategy {name: $parent2_name})
        MERGE (child)-[:EVOLVED_FROM {generation: child.evolution_steps}]->(p1)
        MERGE (child)-[:EVOLVED_FROM {generation: child.evolution_steps}]->(p2)
        """
        with self.driver.session(database=self._config.database) as session:
            session.run(
                query,
                child_name=child_name,
                parent1_name=parent1_name,
                parent2_name=parent2_name,
            )

    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """获取所有活跃策略节点（用于系统启动时恢复策略池）。"""
        query = """
        MATCH (s:Strategy)
        WHERE NOT s:Archived
        RETURN s.name AS name, s.strategy_type AS strategy_type,
               s.uses_real_data AS uses_real_data,
               s.fitness_score AS fitness_score,
               s.real_world_bonus AS real_world_bonus,
               s.avg_accuracy AS avg_accuracy,
               s.avg_success AS avg_success,
               s.avg_cost AS avg_cost,
               s.usage_count AS usage_count,
               s.evolution_steps AS evolution_steps,
               s.created_at AS created_at
        ORDER BY s.fitness_score DESC
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query)
            return [dict(record) for record in result]

    def archive_strategy(self, strategy_name: str) -> None:
        """归档（软删除）被淘汰的策略。"""
        query = """
        MATCH (s:Strategy {name: $name})
        SET s:Archived, s.archived_at = timestamp()
        """
        with self.driver.session(database=self._config.database) as session:
            session.run(query, name=strategy_name)

    def get_recommended_strategies(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        基于查询内容推荐适应度最高的策略。
        
        实现逻辑：
        1. 按适应度排序返回活跃策略
        2. 未来可扩展：基于查询内容语义匹配相关策略
        
        Args:
            query: 查询文本（当前未用于语义匹配，保留用于未来扩展）
            limit: 返回策略数量上限
            
        Returns:
            策略列表，每个策略包含 name, strategy_type, fitness_score, uses_real_data,
            avg_accuracy, usage_count, description 等字段
        """
        strategies = self.get_all_strategies()
        
        # 当前简单实现：直接返回适应度最高的策略
        # 未来扩展：基于查询内容与策略描述/元数据的语义匹配
        
        if not strategies:
            return []
        
        # 按适应度排序，取前N个
        sorted_strategies = sorted(
            strategies, 
            key=lambda s: s.get("fitness_score", 0.0), 
            reverse=True
        )
        
        # 添加描述字段（基于策略类型和性能指标生成）
        for strategy in sorted_strategies[:limit]:
            strategy["description"] = self._generate_strategy_description(strategy)
        
        return sorted_strategies[:limit]
    
    def _generate_strategy_description(self, strategy: Dict[str, Any]) -> str:
        """为策略生成描述信息。"""
        parts = []
        
        strategy_type = strategy.get("strategy_type", "unknown")
        parts.append(f"类型: {strategy_type}")
        
        if strategy.get("uses_real_data"):
            parts.append("使用真实数据")
        
        fitness = strategy.get("fitness_score", 0.0)
        parts.append(f"适应度: {fitness:.2f}")
        
        accuracy = strategy.get("avg_accuracy", 0.0)
        if accuracy > 0:
            parts.append(f"平均准确率: {accuracy:.2f}")
        
        usage = strategy.get("usage_count", 0)
        if usage > 0:
            parts.append(f"使用次数: {usage}")
        
        return ", ".join(parts)

    # ========== RQS 记录节点操作 ==========

    def upsert_rqs_node(self, rqs_data: Dict[str, Any]) -> str:
        """
        插入或更新推理质量评分记录。

        Args:
            rqs_data: 来自 ReasoningStats.to_dict()

        Returns:
            节点的 elementId
        """
        query = """
        MERGE (r:RQSRecord {path_id: $path_id})
        ON CREATE SET
            r.success_count = $success_count,
            r.fail_count = $fail_count,
            r.total_uses = $total_uses,
            r.historical_success_rate = $historical_success_rate,
            r.stability_score = $stability_score,
            r.avg_rqs = $avg_rqs,
            r.last_used = $last_used,
            r.created_at = timestamp(),
            r.updated_at = timestamp()
        ON MATCH SET
            r.success_count = $success_count,
            r.fail_count = $fail_count,
            r.total_uses = $total_uses,
            r.historical_success_rate = $historical_success_rate,
            r.stability_score = $stability_score,
            r.avg_rqs = $avg_rqs,
            r.last_used = $last_used,
            r.updated_at = timestamp()
        RETURN elementId(r) AS eid
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                path_id=rqs_data["path_id"],
                success_count=rqs_data.get("success_count", 0),
                fail_count=rqs_data.get("fail_count", 0),
                total_uses=rqs_data.get("total_uses", 0),
                historical_success_rate=rqs_data.get("historical_success_rate", 0.0),
                stability_score=rqs_data.get("stability_score", 0.5),
                avg_rqs=rqs_data.get("avg_rqs", 0.0),
                last_used=rqs_data.get("last_used", ""),
            )
            record = result.single()
            return record["eid"] if record else ""

    def get_all_rqs_records(self) -> List[Dict[str, Any]]:
        """获取所有 RQS 记录（用于系统启动时恢复）。"""
        query = """
        MATCH (r:RQSRecord)
        RETURN r.path_id AS path_id,
               r.success_count AS success_count,
               r.fail_count AS fail_count,
               r.total_uses AS total_uses,
               r.historical_success_rate AS historical_success_rate,
               r.stability_score AS stability_score,
               r.avg_rqs AS avg_rqs,
               r.last_used AS last_used
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query)
            return [dict(record) for record in result]

    # ========== 信念节点操作 ==========

    def upsert_belief_node(self, belief_data: Dict[str, Any]) -> str:
        """
        插入或更新信念节点。

        Args:
            belief_data: 信念数据字典

        Returns:
            节点的 elementId
        """
        query = """
        MERGE (b:Belief {content: $content})
        ON CREATE SET
            b.belief_strength = $belief_strength,
            b.confidence = $confidence,
            b.state = $state,
            b.evidence_count = $evidence_count,
            b.source = $source,
            b.created_at = timestamp(),
            b.updated_at = timestamp()
        ON MATCH SET
            b.belief_strength = $belief_strength,
            b.confidence = $confidence,
            b.state = $state,
            b.evidence_count = $evidence_count,
            b.updated_at = timestamp()
        RETURN elementId(b) AS eid
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                content=belief_data["content"],
                belief_strength=belief_data.get("belief_strength", 0.5),
                confidence=belief_data.get("confidence", 0.5),
                state=belief_data.get("state", "HYPOTHESIS"),
                evidence_count=belief_data.get("evidence_count", 0),
                source=belief_data.get("source", "cognitive_core"),
            )
            record = result.single()
            return record["eid"] if record else ""

    def get_all_beliefs(self) -> List[Dict[str, Any]]:
        """获取所有 Belief 节点。"""
        query = """
        MATCH (b:Belief)
        RETURN b.content AS content,
               b.belief_strength AS belief_strength,
               b.confidence AS confidence,
               b.state AS state,
               b.evidence_count AS evidence_count,
               b.source AS source
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query)
            return [dict(record) for record in result]

    def upsert_entity_claim(
        self,
        entity_name: str,
        claimed_type: str,
        source_type: str = "ingest_llm",
        source_ref: str = "",
        initial_state: str = "hypothesis",
        support_delta: int = 1,
        conflict_delta: int = 0,
    ) -> str:
        """创建或更新 entity typing claim。"""
        query = """
        MERGE (c:Claim {entity_name: $entity_name, claim_kind: 'entity_typing', claimed_value: $claimed_value})
        ON CREATE SET
            c.claim_id = $claim_id,
            c.target_type = 'entity',
            c.source_type = $source_type,
            c.source_ref = $source_ref,
            c.state = $initial_state,
            c.support_score = $support_delta,
            c.conflict_score = $conflict_delta,
            c.net_confidence = $support_delta - $conflict_delta,
            c.created_at = timestamp(),
            c.updated_at = timestamp()
        ON MATCH SET
            c.source_type = $source_type,
            c.source_ref = $source_ref,
            c.support_score = coalesce(c.support_score, 0) + $support_delta,
            c.conflict_score = coalesce(c.conflict_score, 0) + $conflict_delta,
            c.net_confidence = (coalesce(c.support_score, 0) + $support_delta) - (coalesce(c.conflict_score, 0) + $conflict_delta),
            c.updated_at = timestamp(),
            c.state = CASE
                WHEN ((coalesce(c.support_score, 0) + $support_delta) - (coalesce(c.conflict_score, 0) + $conflict_delta)) <= -1 THEN 'contradicted'
                WHEN ((coalesce(c.support_score, 0) + $support_delta) - (coalesce(c.conflict_score, 0) + $conflict_delta)) >= 2 THEN 'stable'
                ELSE 'hypothesis'
            END
        WITH c
        MATCH (e:Entity {name: $entity_name})
        MERGE (c)-[:ABOUT]->(e)
        RETURN c.claim_id AS claim_id
        """
        claim_id = hashlib.md5(f"{entity_name}:entity_typing:{claimed_type}".encode("utf-8")).hexdigest()[:16]
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                entity_name=entity_name,
                claimed_value=claimed_type,
                source_type=source_type,
                source_ref=source_ref,
                initial_state=initial_state,
                support_delta=support_delta,
                conflict_delta=conflict_delta,
                claim_id=claim_id,
            )
            record = result.single()
            return record["claim_id"] if record else ""

    def get_entity_claims(self, entity_name: str) -> List[Dict[str, Any]]:
        """获取某个实体的所有 typing claims。"""
        query = """
        MATCH (c:Claim {entity_name: $entity_name, claim_kind: 'entity_typing'})
        RETURN c.claim_id AS claim_id,
               c.entity_name AS entity_name,
               c.claim_kind AS claim_kind,
               c.claimed_value AS claimed_value,
               c.state AS state,
               c.support_score AS support_score,
               c.conflict_score AS conflict_score,
               c.net_confidence AS net_confidence,
               c.source_type AS source_type,
               c.source_ref AS source_ref,
               c.updated_at AS updated_at
        ORDER BY c.net_confidence DESC, c.updated_at DESC
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, entity_name=entity_name)
            return [dict(record) for record in result]

    def get_claim_runtime_signal(self, entity_name: str) -> Dict[str, Any]:
        """获取实体 claim 层对 runtime 的最小信号。"""
        claims = self.get_entity_claims(entity_name)
        if not claims:
            return {
                "has_competing_claims": False,
                "conflict_score": 0,
                "support_score": 0,
                "dominant_claim_state": None,
                "dominant_claimed_value": None,
            }
        dominant = claims[0]
        total_conflict = sum(int(c.get("conflict_score") or 0) for c in claims)
        total_support = sum(int(c.get("support_score") or 0) for c in claims)
        return {
            "has_competing_claims": len(claims) > 1,
            "conflict_score": total_conflict,
            "support_score": total_support,
            "dominant_claim_state": dominant.get("state"),
            "dominant_claimed_value": dominant.get("claimed_value"),
        }

    def apply_claim_feedback(
        self,
        entity_name: str,
        claimed_type: str,
        feedback_type: str,
        delta: int = 1,
    ) -> bool:
        """对 entity typing claim 应用反馈。"""
        support_delta = delta if feedback_type == 'support' else 0
        conflict_delta = delta if feedback_type == 'weaken' else (2 * delta if feedback_type == 'contradict' else 0)
        query = """
        MATCH (c:Claim {entity_name: $entity_name, claim_kind: 'entity_typing', claimed_value: $claimed_value})
        SET c.support_score = coalesce(c.support_score, 0) + $support_delta,
            c.conflict_score = coalesce(c.conflict_score, 0) + $conflict_delta,
            c.net_confidence = (coalesce(c.support_score, 0) + $support_delta) - (coalesce(c.conflict_score, 0) + $conflict_delta),
            c.updated_at = timestamp(),
            c.state = CASE
                WHEN ((coalesce(c.support_score, 0) + $support_delta) - (coalesce(c.conflict_score, 0) + $conflict_delta)) <= -1 THEN 'contradicted'
                WHEN ((coalesce(c.support_score, 0) + $support_delta) - (coalesce(c.conflict_score, 0) + $conflict_delta)) >= 2 THEN 'stable'
                ELSE 'hypothesis'
            END
        RETURN c.claim_id AS claim_id
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                entity_name=entity_name,
                claimed_value=claimed_type,
                support_delta=support_delta,
                conflict_delta=conflict_delta,
            )
            return result.single() is not None

    def sync_entity_type_from_claims(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """根据 claims 同步实体当前类型。"""
        claims = self.get_entity_claims(entity_name)
        if not claims:
            return None
        dominant = claims[0]
        second = claims[1] if len(claims) > 1 else None
        dominant_score = dominant.get("net_confidence") or 0
        second_score = (second.get("net_confidence") or -999) if second else -999
        query = """
        MATCH (e:Entity {name: $entity_name})
        SET e.entity_type = CASE
                WHEN $apply_type THEN $claimed_value
                ELSE e.entity_type
            END,
            e.knowledge_state = $knowledge_state,
            e.conflict_with_existing = $conflict_with_existing,
            e.updated_at = timestamp()
        RETURN e.name AS name, e.entity_type AS entity_type, e.knowledge_state AS knowledge_state
        """
        apply_type = dominant.get("state") == "stable" and dominant_score >= second_score + 1
        knowledge_state = "stable" if apply_type else "hypothesis"
        conflict_with_existing = not apply_type and len(claims) > 1
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                entity_name=entity_name,
                claimed_value=dominant.get("claimed_value"),
                apply_type=apply_type,
                knowledge_state=knowledge_state,
                conflict_with_existing=conflict_with_existing,
            )
            record = result.single()
            return dict(record) if record else None

    def complete_pending_belief(self, content: str) -> bool:
        """将 pending belief 标记为已稳定/已完成。"""
        query = """
        MATCH (b:Belief {content: $content})
        SET b.state = 'STABLE',
            b.completed_at = timestamp(),
            b.updated_at = timestamp()
        RETURN b.content AS content
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, content=content)
            return result.single() is not None

    def record_claim_observation(
        self,
        entity_name: str,
        claimed_type: str,
        observation_type: str,
        content: str,
        source: str,
        polarity: str,
        confidence: float = 1.0,
    ) -> str:
        """记录针对 claim 的最小 Observation。"""
        observation_id = hashlib.md5(f"obs:{entity_name}:{claimed_type}:{content}:{source}".encode("utf-8")).hexdigest()[:16]
        query = """
        MERGE (o:Observation {observation_id: $observation_id})
        ON CREATE SET
            o.observation_type = $observation_type,
            o.content = $content,
            o.source = $source,
            o.polarity = $polarity,
            o.confidence = $confidence,
            o.created_at = timestamp()
        WITH o
        MATCH (c:Claim {entity_name: $entity_name, claim_kind: 'entity_typing', claimed_value: $claimed_value})
        MERGE (o)-[:OBSERVES]->(c)
        RETURN o.observation_id AS observation_id
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                observation_id=observation_id,
                observation_type=observation_type,
                content=content,
                source=source,
                polarity=polarity,
                confidence=confidence,
                entity_name=entity_name,
                claimed_value=claimed_type,
            )
            record = result.single()
            return record["observation_id"] if record else ""

    def record_claim_outcome(
        self,
        entity_name: str,
        claimed_type: str,
        status: str,
        summary: str,
        confidence: float = 1.0,
    ) -> str:
        """记录针对 claim 的最小 Outcome。"""
        outcome_id = hashlib.md5(f"out:{entity_name}:{claimed_type}:{status}:{summary}".encode("utf-8")).hexdigest()[:16]
        query = """
        MERGE (o:Outcome {outcome_id: $outcome_id})
        ON CREATE SET
            o.status = $status,
            o.summary = $summary,
            o.confidence = $confidence,
            o.created_at = timestamp()
        WITH o
        MATCH (c:Claim {entity_name: $entity_name, claim_kind: 'entity_typing', claimed_value: $claimed_value})
        MERGE (o)-[:EVALUATES]->(c)
        RETURN o.outcome_id AS outcome_id
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                outcome_id=outcome_id,
                status=status,
                summary=summary,
                confidence=confidence,
                entity_name=entity_name,
                claimed_value=claimed_type,
            )
            record = result.single()
            return record["outcome_id"] if record else ""

    def record_belief_update(
        self,
        entity_name: str,
        claimed_type: str,
        update_type: str,
        delta: int,
        reason: str,
    ) -> str:
        """记录针对 claim 的最小 BeliefUpdate。"""
        update_id = hashlib.md5(f"upd:{entity_name}:{claimed_type}:{update_type}:{reason}:{delta}".encode("utf-8")).hexdigest()[:16]
        query = """
        MERGE (u:BeliefUpdate {update_id: $update_id})
        ON CREATE SET
            u.update_type = $update_type,
            u.delta = $delta,
            u.reason = $reason,
            u.created_at = timestamp()
        WITH u
        MATCH (c:Claim {entity_name: $entity_name, claim_kind: 'entity_typing', claimed_value: $claimed_value})
        MERGE (u)-[:UPDATES]->(c)
        RETURN u.update_id AS update_id
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(
                query,
                update_id=update_id,
                update_type=update_type,
                delta=delta,
                reason=reason,
                entity_name=entity_name,
                claimed_value=claimed_type,
            )
            record = result.single()
            return record["update_id"] if record else ""

    def get_pending_belief_count(self) -> int:
        """获取当前待验证 belief 数量。"""
        query = """
        MATCH (b:Belief)
        WHERE b.content STARTS WITH 'pending::' AND coalesce(b.state, 'HYPOTHESIS') = 'HYPOTHESIS'
        RETURN count(b) AS count
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query)
            record = result.single()
            return int(record["count"]) if record and record.get("count") is not None else 0

    def expire_pending_beliefs(self, ttl_seconds: int) -> int:
        """将超过 TTL 的 pending belief 标记为 EXPIRED。"""
        query = """
        MATCH (b:Belief)
        WHERE b.content STARTS WITH 'pending::'
          AND coalesce(b.state, 'HYPOTHESIS') = 'HYPOTHESIS'
          AND coalesce(b.updated_at, b.created_at, timestamp()) < timestamp() - $ttl_ms
        SET b.state = 'EXPIRED',
            b.expired_at = timestamp(),
            b.updated_at = timestamp()
        RETURN count(b) AS count
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query, ttl_ms=max(ttl_seconds, 0) * 1000)
            record = result.single()
            return int(record["count"]) if record and record.get("count") is not None else 0

    # ================================================================
    # Phase 3: 策略蒸馏与进化方法
    # ================================================================

    def get_causal_chains(
        self,
        min_length: int = 3,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取图谱中的因果链（由 CAUSES 关系连接的事件序列）。

        Args:
            min_length: 最小链长度（节点数）
            limit: 返回链数量上限

        Returns:
            因果链列表，每条链包含事件序列和关系
        """
        # 动态构建最小路径长度（关系数 = 节点数 - 1）
        min_rels = max(min_length - 1, 1)
        query = f"""
        MATCH path = (e1:Entity)-[:RELATES_TO*{min_rels}..10]->(e2:Entity)
        WHERE e1.entity_type IN ['event', 'concept']
          AND e2.entity_type IN ['event', 'concept']
          AND NOT e1:Archived AND NOT e2:Archived
          AND ALL(r IN relationships(path) WHERE r.relation_type IN ['causes', 'leads_to', 'precedes'])
        WITH path, length(path) AS chain_length
        ORDER BY chain_length DESC
        LIMIT $limit
        RETURN [n IN nodes(path) | {{
            name: n.name,
            entity_type: n.entity_type,
            properties: n.properties
        }}] AS chain_nodes,
        [r IN relationships(path) | {{
            type: r.relation_type,
            properties: r.properties
        }}] AS chain_relations,
        chain_length
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(query, limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error("Failed to get causal chains: %s", e)
            return []

    def get_event_clusters(
        self,
        min_connections: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        获取高连接度的事件聚类（用于策略蒸馏候选）。

        Args:
            min_connections: 最小连接数

        Returns:
            事件聚类列表
        """
        query = """
        MATCH (e:Entity {entity_type: 'event'})
        WHERE NOT e:Archived
        WITH e, size((e)--()) AS degree
        WHERE degree >= $min_connections
        OPTIONAL MATCH (e)-[r]->(target:Entity)
        RETURN e.name AS event_name,
               e.properties AS properties,
               degree,
               collect({
                   target: target.name,
                   relation: type(r),
                   target_type: target.entity_type
               }) AS connections
        ORDER BY degree DESC
        LIMIT 50
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(query, min_connections=min_connections)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error("Failed to get event clusters: %s", e)
            return []

    def get_strategies_for_evolution(self) -> List[Dict[str, Any]]:
        """
        获取所有活跃策略及其关联信息（用于冥思进化步骤）。

        Returns:
            策略列表，包含名称、类型、适应度、父策略等信息
        """
        query = """
        MATCH (s:Strategy)
        WHERE NOT s:Archived
        OPTIONAL MATCH (s)-[:EVOLVED_FROM]->(parent:Strategy)
        RETURN s.name AS name,
               s.strategy_type AS strategy_type,
               s.uses_real_data AS uses_real_data,
               s.fitness_score AS fitness_score,
               s.usage_count AS usage_count,
               s.avg_accuracy AS avg_accuracy,
               collect(parent.name) AS parent_names
        ORDER BY s.fitness_score DESC
        """
        with self.driver.session(database=self._config.database) as session:
            result = session.run(query)
            return [dict(record) for record in result]

    def get_strategies_for_injection(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        获取可供 prompt 注入的活跃策略。

        Returns:
            策略列表，包含名称、描述、适用场景、适应度等字段。
        """
        query = """
        MATCH (s:Strategy)
        WHERE NOT s:Archived
        RETURN s.name AS name,
               s.strategy_type AS strategy_type,
               s.uses_real_data AS uses_real_data,
               s.fitness_score AS fitness_score,
               s.avg_accuracy AS avg_accuracy,
               s.content AS content,
               s.description AS description,
               s.applicable_scenarios AS applicable_scenarios,
               s.source AS source,
               s.created_at AS created_at
        ORDER BY coalesce(s.fitness_score, s.avg_accuracy, 0.0) DESC,
                 coalesce(s.avg_accuracy, 0.0) DESC,
                 s.name ASC
        LIMIT $limit
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(query, limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error("Failed to get strategies for injection: %s", e)
            return []

    def create_causal_chain_node(self, chain_data: Dict[str, Any]) -> str:
        """
        创建因果链元节点。

        Args:
            chain_data: 包含 chain_id, description, length 的字典

        Returns:
            节点的 elementId
        """
        query = """
        CREATE (c:CausalChain {
            chain_id: $chain_id,
            description: $description,
            length: $length,
            created_at: timestamp()
        })
        RETURN elementId(c) AS eid
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                result = session.run(
                    query,
                    chain_id=chain_data["chain_id"],
                    description=chain_data.get("description", ""),
                    length=chain_data.get("length", 0),
                )
                record = result.single()
                return record["eid"] if record else ""
        except Exception as e:
            logger.error("Failed to create causal chain node: %s", e)
            return ""

    def link_strategy_to_causal_chain(
        self,
        strategy_name: str,
        chain_id: str,
    ) -> None:
        """
        建立策略与因果链的 GENERATED_BY 关系。

        Args:
            strategy_name: 策略名称
            chain_id: 因果链 ID
        """
        query = """
        MATCH (s:Strategy {name: $strategy_name})
        MATCH (c:CausalChain {chain_id: $chain_id})
        MERGE (s)-[:GENERATED_BY {created_at: timestamp()}]->(c)
        """
        try:
            with self.driver.session(database=self._config.database) as session:
                session.run(
                    query,
                    strategy_name=strategy_name,
                    chain_id=chain_id,
                )
        except Exception as e:
            logger.error(
                "Failed to link strategy %s to chain %s: %s",
                strategy_name, chain_id, e,
            )
