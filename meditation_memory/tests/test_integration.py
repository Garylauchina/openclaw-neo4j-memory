"""
集成测试

测试完整的记忆写入 → 检索 → 提示词构建流程。
使用 mock Neo4j 驱动，验证各模块之间的协作。
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from meditation_memory.config import MemoryConfig, Neo4jConfig, LLMConfig, SubgraphConfig
from meditation_memory.entity_extractor import Entity, EntityExtractor, ExtractionResult, Relation
from meditation_memory.graph_store import GraphStore
from meditation_memory.memory_system import MemorySystem
from meditation_memory.subgraph_context import SubgraphContext


class TestFullPipelineWithRuleExtraction(unittest.TestCase):
    """
    完整流程集成测试（规则抽取 + mock Neo4j）

    验证：文本输入 → 实体抽取 → 写入图数据库 → 检索子图 → 构建提示词
    """

    def setUp(self):
        config = MemoryConfig(
            neo4j=Neo4jConfig(),
            llm=LLMConfig(api_key=None),  # 不使用 LLM
            subgraph=SubgraphConfig(max_nodes=10, max_edges=20),
        )
        self.ms = MemorySystem(config)

        # Mock Neo4j 驱动
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__ = MagicMock(return_value=self.mock_session)
        self.mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)
        self.ms._store._driver = self.mock_driver

    def test_ingest_and_retrieve(self):
        """测试写入后检索"""
        # 模拟写入成功
        mock_upsert_result = MagicMock()
        mock_upsert_result.single.return_value = {"eid": "test-id"}
        mock_rel_result = MagicMock()
        mock_rel_result.single.return_value = {"rel_type": "RELATES_TO"}
        self.mock_session.run.return_value = mock_upsert_result

        # 写入
        result = self.ms.ingest("张三在腾讯公司担任工程师", use_llm=False)
        self.assertGreater(result.entities_written, 0)

        # 模拟检索
        # 精确查找
        self.mock_session.run.side_effect = None
        find_result = MagicMock()
        find_result.single.return_value = {"name": "腾讯公司", "entity_type": "organization",
                                            "properties": "{}", "mention_count": 1,
                                            "created_at": 1000, "updated_at": 1000}
        search_result = MagicMock()
        search_result.__iter__ = MagicMock(return_value=iter([]))

        # 子图查询
        subgraph_result = MagicMock()
        subgraph_result.single.return_value = None

        call_count = [0]
        def dynamic_return(*args, **kwargs):
            call_count[0] += 1
            query = args[0] if args else ""
            if "fulltext" in query:
                raise Exception("No fulltext index")
            if "MERGE" in query:
                return mock_upsert_result
            if "{name: $name}" in query and "entity_type" not in query and "OPTIONAL" not in query:
                return find_result
            if "CONTAINS" in query:
                return search_result
            return subgraph_result

        self.mock_session.run.side_effect = dynamic_return

        # 检索
        ctx = self.ms.retrieve_context("腾讯公司有哪些工程师？", use_llm=False)
        self.assertIsNotNone(ctx)

    def test_build_prompt_integration(self):
        """测试提示词构建集成"""
        # 模拟实体查找成功
        find_result = MagicMock()
        find_result.single.return_value = {"name": "人工智能", "entity_type": "concept",
                                            "properties": "{}", "mention_count": 5,
                                            "created_at": 1000, "updated_at": 1000}
        search_result = MagicMock()
        search_result.__iter__ = MagicMock(return_value=iter([]))

        # 子图查询返回数据
        subgraph_nodes = MagicMock()
        subgraph_nodes.single.return_value = {
            "nodes": [
                self._make_mock_node("人工智能", "concept", 5),
                self._make_mock_node("机器学习", "concept", 3),
            ],
            "rels": [
                self._make_mock_rel("人工智能", "机器学习", "contains"),
            ],
        }

        def dynamic_return(*args, **kwargs):
            query = args[0] if args else ""
            if "fulltext" in query:
                raise Exception("No fulltext index")
            if "{name: $name}" in query and "OPTIONAL" not in query:
                return find_result
            if "CONTAINS" in query:
                return search_result
            return subgraph_nodes

        self.mock_session.run.side_effect = dynamic_return

        prompt = self.ms.build_prompt(
            "什么是人工智能？",
            base_prompt="你是一个知识助手",
            use_llm=False,
        )

        # 提示词应该包含基础提示词
        self.assertIn("你是一个知识助手", prompt)

    def _make_mock_node(self, name, entity_type, mention_count):
        """创建 mock 节点"""
        node = MagicMock()
        node.get.side_effect = lambda k, d=None: {
            "name": name,
            "entity_type": entity_type,
            "mention_count": mention_count,
        }.get(k, d)
        return node

    def _make_mock_rel(self, src, tgt, rel_type):
        """创建 mock 关系"""
        rel = MagicMock()
        src_node = MagicMock()
        src_node.get.side_effect = lambda k, d=None: {"name": src}.get(k, d)
        tgt_node = MagicMock()
        tgt_node.get.side_effect = lambda k, d=None: {"name": tgt}.get(k, d)
        rel.start_node = src_node
        rel.end_node = tgt_node
        rel.get.side_effect = lambda k, d=None: {"relation_type": rel_type}.get(k, d)
        return rel


class TestEntityExtractorIntegration(unittest.TestCase):
    """实体抽取器集成测试"""

    def test_rule_extraction_various_texts(self):
        """测试规则抽取对各种文本的处理"""
        extractor = EntityExtractor(LLMConfig(api_key=None))

        test_cases = [
            "张三在北京大学学习人工智能",
            "Apple公司发布了新产品",
            "上海市浦东新区的科技园区",
            "OpenAI released GPT-4 model",
            "",  # 空文本
            "你好",  # 极短文本
        ]

        for text in test_cases:
            result = extractor.extract(text, use_llm=False)
            self.assertIsInstance(result, ExtractionResult)
            self.assertEqual(result.raw_text, text)

    def test_extraction_consistency(self):
        """测试抽取结果一致性"""
        extractor = EntityExtractor(LLMConfig(api_key=None))
        text = "张三在清华大学研究机器学习"

        result1 = extractor.extract(text, use_llm=False)
        result2 = extractor.extract(text, use_llm=False)

        # 同样的输入应该产生同样的结果
        self.assertEqual(len(result1.entities), len(result2.entities))
        names1 = sorted([e.name for e in result1.entities])
        names2 = sorted([e.name for e in result2.entities])
        self.assertEqual(names1, names2)


class TestConfigIntegration(unittest.TestCase):
    """配置集成测试"""

    def test_config_from_env(self):
        """测试从环境变量读取配置"""
        import os
        original = os.environ.get("NEO4J_URI")
        try:
            os.environ["NEO4J_URI"] = "bolt://test-host:7687"
            config = MemoryConfig()
            self.assertEqual(config.neo4j.uri, "bolt://test-host:7687")
        finally:
            if original:
                os.environ["NEO4J_URI"] = original
            else:
                os.environ.pop("NEO4J_URI", None)

    def test_memory_system_with_config(self):
        """测试带配置的 MemorySystem 创建"""
        config = MemoryConfig(
            neo4j=Neo4jConfig(uri="bolt://localhost:7687"),
            llm=LLMConfig(api_key=None),
            subgraph=SubgraphConfig(max_nodes=20),
        )
        ms = MemorySystem(config)
        self.assertEqual(ms._config.subgraph.max_nodes, 20)


if __name__ == "__main__":
    unittest.main()
