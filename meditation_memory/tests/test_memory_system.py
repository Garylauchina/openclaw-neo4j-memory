"""
记忆系统主入口的单元测试
"""

import unittest
from unittest.mock import MagicMock, patch

from meditation_memory.config import MemoryConfig, Neo4jConfig, LLMConfig, WriteGuardConfig
from meditation_memory.entity_extractor import Entity, ExtractionResult, Relation
from meditation_memory.memory_system import IngestResult, MemorySystem
from meditation_memory.subgraph_context import ContextResult


class TestMemorySystemInit(unittest.TestCase):
    """MemorySystem 初始化测试"""

    def test_default_init(self):
        """测试默认初始化"""
        ms = MemorySystem()
        self.assertIsNotNone(ms._store)
        self.assertIsNotNone(ms._extractor)
        self.assertIsNotNone(ms._context_builder)
        self.assertFalse(ms._initialized)

    def test_custom_config(self):
        """测试自定义配置"""
        config = MemoryConfig(
            neo4j=Neo4jConfig(uri="bolt://custom:7687"),
            llm=LLMConfig(model="gpt-4"),
        )
        ms = MemorySystem(config)
        self.assertEqual(ms._store._config.uri, "bolt://custom:7687")


class TestMemorySystemIngest(unittest.TestCase):
    """记忆写入测试"""

    def setUp(self):
        self.ms = MemorySystem()
        # Mock 底层组件
        self.ms._store = MagicMock()
        self.ms._extractor = MagicMock()

    def test_ingest_text(self):
        """测试文本写入"""
        self.ms._extractor.extract.return_value = ExtractionResult(
            entities=[
                Entity(name="张三", entity_type="person"),
                Entity(name="北京", entity_type="place"),
            ],
            relations=[
                Relation(source="张三", target="北京", relation_type="located_in"),
            ],
            raw_text="张三住在北京",
        )
        self.ms._store.upsert_entities.return_value = 2
        self.ms._store.upsert_relations.return_value = 1

        result = self.ms.ingest("张三住在北京")

        self.assertIsInstance(result, IngestResult)
        self.assertEqual(result.entities_written, 2)
        self.assertEqual(result.relations_written, 1)
        self.ms._extractor.extract.assert_called_once_with("张三住在北京", use_llm=True)

    def test_ingest_empty_text(self):
        """测试空文本写入"""
        self.ms._extractor.extract.return_value = ExtractionResult()
        self.ms._store.upsert_entities.return_value = 0
        self.ms._store.upsert_relations.return_value = 0

        result = self.ms.ingest("")
        self.assertEqual(result.entities_written, 0)
        self.assertEqual(result.relations_written, 0)

    def test_ingest_from_extraction(self):
        """测试从已有抽取结果写入"""
        extraction = ExtractionResult(
            entities=[Entity(name="测试", entity_type="concept")],
            relations=[],
        )
        self.ms._store.upsert_entities.return_value = 1
        self.ms._store.upsert_relations.return_value = 0

        result = self.ms.ingest_from_extraction(extraction)
        self.assertEqual(result.entities_written, 1)

    def test_ingest_without_llm(self):
        """测试不使用 LLM 的写入"""
        self.ms._extractor.extract.return_value = ExtractionResult()
        self.ms._store.upsert_entities.return_value = 0
        self.ms._store.upsert_relations.return_value = 0

        self.ms.ingest("测试", use_llm=False)
        self.ms._extractor.extract.assert_called_once_with("测试", use_llm=False)

    def test_write_guard_marks_low_evidence_entities_as_hypothesis(self):
        self.ms._extractor.extract.return_value = ExtractionResult(
            entities=[Entity(name="张三", entity_type="person", properties={})],
            relations=[],
            raw_text="张三最近在研究一个方向",
        )
        self.ms._store.upsert_entities.return_value = 1
        self.ms._store.upsert_relations.return_value = 0

        self.ms.ingest("张三最近在研究一个方向")

        written_entities = self.ms._store.upsert_entities.call_args[0][0]
        self.assertEqual(written_entities[0].properties["knowledge_state"], "hypothesis")
        self.assertEqual(written_entities[0].properties["evidence_count"], 1)
        self.assertEqual(written_entities[0].properties["source_count"], 1)

    def test_write_guard_can_keep_entity_stable_when_thresholds_met(self):
        config = MemoryConfig(write_guard=WriteGuardConfig(
            enabled=True,
            stable_belief_strength_threshold=0.7,
            stable_min_evidence_count=1,
            stable_min_source_count=1,
        ))
        ms = MemorySystem(config)
        ms._store = MagicMock()
        ms._extractor = MagicMock()
        ms._extractor.extract.return_value = ExtractionResult(
            entities=[Entity(name="Neo4j", entity_type="technology", properties={"belief_strength": 0.8})],
            relations=[],
            raw_text="Neo4j 是图数据库",
        )
        ms._store.upsert_entities.return_value = 1
        ms._store.upsert_relations.return_value = 0

        ms.ingest("Neo4j 是图数据库")

        written_entities = ms._store.upsert_entities.call_args[0][0]
        self.assertEqual(written_entities[0].properties["knowledge_state"], "stable")
        ms._store.upsert_belief_node.assert_not_called()

    def test_hypothesis_entities_are_buffered_as_pending_beliefs(self):
        self.ms._extractor.extract.return_value = ExtractionResult(
            entities=[Entity(name="张三", entity_type="person", properties={})],
            relations=[],
            raw_text="张三最近在研究一个方向",
        )
        self.ms._store.upsert_entities.return_value = 1
        self.ms._store.upsert_relations.return_value = 0

        self.ms.ingest("张三最近在研究一个方向")

        self.ms._store.upsert_belief_node.assert_called_once()
        belief_payload = self.ms._store.upsert_belief_node.call_args[0][0]
        self.assertEqual(belief_payload["content"], "pending::person::张三")
        self.assertEqual(belief_payload["state"], "HYPOTHESIS")
        self.assertEqual(belief_payload["evidence_count"], 1)


class TestMemorySystemRetrieve(unittest.TestCase):
    """记忆检索测试"""

    def setUp(self):
        self.ms = MemorySystem()
        self.ms._context_builder = MagicMock()

    def test_retrieve_context(self):
        """测试上下文检索"""
        mock_result = ContextResult(
            context_text="张三 工作于 北京大学",
            subgraph={"nodes": [], "edges": []},
            matched_entities=["张三"],
        )
        self.ms._context_builder.build_context.return_value = mock_result

        result = self.ms.retrieve_context("张三在哪工作？")
        self.assertEqual(result.context_text, "张三 工作于 北京大学")

    def test_build_prompt(self):
        """测试提示词构建"""
        self.ms._context_builder.build_system_prompt.return_value = "你是助手\n\n## 当前上下文\n用户当前问题：张三在哪？\n\n## 相关记忆与知识\n..."

        prompt = self.ms.build_prompt("张三在哪？", base_prompt="你是助手")
        self.assertIn("你是助手", prompt)


class TestMemorySystemStats(unittest.TestCase):
    """统计信息测试"""

    def setUp(self):
        self.ms = MemorySystem()
        self.ms._store = MagicMock()

    def test_get_stats(self):
        """测试获取统计信息"""
        self.ms._store.get_stats.return_value = {"node_count": 10, "edge_count": 5}
        self.ms._store.verify_connectivity.return_value = True

        stats = self.ms.get_stats()
        self.assertEqual(stats["node_count"], 10)
        self.assertEqual(stats["edge_count"], 5)
        self.assertTrue(stats["connected"])

    def test_search_entities(self):
        """测试实体搜索"""
        self.ms._store.search_entities.return_value = [
            {"name": "AI", "entity_type": "concept"}
        ]
        results = self.ms.search_entities("AI")
        self.assertEqual(len(results), 1)


class TestMemorySystemSession(unittest.TestCase):
    """会话管理接口测试"""

    def setUp(self):
        self.ms = MemorySystem()
        self.ms._context_builder = MagicMock()
        self.ms._extractor = MagicMock()
        self.ms._store = MagicMock()

    def test_start_session(self):
        """测试开始会话"""
        mock_result = ContextResult(
            context_text="张三信息",
            subgraph={"nodes": [{"name": "张三"}], "edges": []},
            matched_entities=["张三"],
        )
        self.ms._context_builder.start_session.return_value = mock_result

        result = self.ms.start_session("张三是谁？")
        self.assertEqual(result.context_text, "张三信息")
        self.ms._context_builder.start_session.assert_called_once_with("张三是谁？", use_llm=True)

    def test_process_message(self):
        """测试处理会话消息"""
        mock_result = ContextResult(
            context_text="张三信息",
            subgraph={"nodes": [{"name": "张三"}], "edges": []},
            matched_entities=["张三"],
        )
        self.ms._context_builder.get_context.return_value = mock_result

        result = self.ms.process_message("张三在哪里工作？")
        self.assertEqual(result.context_text, "张三信息")
        self.ms._context_builder.get_context.assert_called_once_with("张三在哪里工作？", use_llm=True)

    def test_end_session(self):
        """测试结束会话"""
        # 模拟会话中收集的抽取结果
        session_extractions = [
            ExtractionResult(
                entities=[Entity(name="张三", entity_type="person")],
                relations=[],
            ),
            ExtractionResult(
                entities=[Entity(name="北京大学", entity_type="organization")],
                relations=[Relation(source="张三", target="北京大学", relation_type="works_at")],
            ),
        ]
        self.ms._context_builder.end_session.return_value = session_extractions

        # 模拟最终抽取
        self.ms._extractor.extract.return_value = ExtractionResult(
            entities=[
                Entity(name="张三", entity_type="person"),
                Entity(name="北京大学", entity_type="organization"),
            ],
            relations=[Relation(source="张三", target="北京大学", relation_type="works_at")],
        )

        self.ms._store.upsert_entities.return_value = 2
        self.ms._store.upsert_relations.return_value = 1

        result = self.ms.end_session("完整的对话文本")

        self.assertIsInstance(result, IngestResult)
        self.assertEqual(result.entities_written, 2)
        self.assertEqual(result.relations_written, 1)
        self.ms._context_builder.end_session.assert_called_once()
        self.ms._extractor.extract.assert_called_once_with("完整的对话文本", use_llm=True)

    def test_end_session_deduplication(self):
        """测试会话结束时的去重"""
        # 会话中有重复的实体
        session_extractions = [
            ExtractionResult(
                entities=[Entity(name="张三", entity_type="person")],
                relations=[],
            ),
            ExtractionResult(
                entities=[Entity(name="张三", entity_type="person")],  # 重复
                relations=[],
            ),
        ]
        self.ms._context_builder.end_session.return_value = session_extractions
        self.ms._extractor.extract.return_value = ExtractionResult(
            entities=[Entity(name="张三", entity_type="person")],
            relations=[],
        )
        self.ms._store.upsert_entities.return_value = 1  # 去重后只有 1 个
        self.ms._store.upsert_relations.return_value = 0

        result = self.ms.end_session("对话文本")

        # 验证去重后的结果
        self.assertEqual(result.entities_written, 1)


class TestIngestResult(unittest.TestCase):
    """IngestResult 测试"""

    def test_to_dict(self):
        """测试序列化"""
        result = IngestResult(
            extraction=ExtractionResult(
                entities=[Entity(name="A", entity_type="concept")],
                relations=[Relation(source="A", target="B", relation_type="related_to")],
            ),
            entities_written=1,
            relations_written=1,
        )
        d = result.to_dict()
        self.assertEqual(d["entities_extracted"], 1)
        self.assertEqual(d["relations_extracted"], 1)
        self.assertEqual(d["entities_written"], 1)
        self.assertEqual(d["relations_written"], 1)

    def test_repr(self):
        """测试字符串表示"""
        result = IngestResult(
            extraction=ExtractionResult(),
            entities_written=3,
            relations_written=2,
        )
        s = repr(result)
        self.assertIn("3", s)
        self.assertIn("2", s)


if __name__ == "__main__":
    unittest.main()
