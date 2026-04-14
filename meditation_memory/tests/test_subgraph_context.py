"""
动态子图上下文构建模块的单元测试
"""

import unittest
from unittest.mock import MagicMock

from meditation_memory.config import SubgraphConfig
from meditation_memory.entity_extractor import (
    Entity,
    EntityExtractor,
    ExtractionResult,
    Relation,
)
from meditation_memory.graph_store import GraphStore
from meditation_memory.subgraph_context import ContextResult, SessionContext, SubgraphContext


class TestSubgraphContext(unittest.TestCase):
    """SubgraphContext 传统模式测试"""

    def setUp(self):
        # Mock GraphStore
        self.mock_store = MagicMock(spec=GraphStore)
        # Mock EntityExtractor
        self.mock_extractor = MagicMock(spec=EntityExtractor)
        self.config = SubgraphConfig()
        self.ctx_builder = SubgraphContext(
            graph_store=self.mock_store,
            extractor=self.mock_extractor,
            config=self.config,
        )

    def test_build_context_empty_input(self):
        """测试空输入"""
        self.mock_extractor.extract.return_value = ExtractionResult(raw_text="")
        result = self.ctx_builder.build_context("")
        self.assertIsInstance(result, ContextResult)
        self.assertEqual(result.context_text, "")

    def test_build_context_no_entities(self):
        """测试无实体抽取结果"""
        self.mock_extractor.extract.return_value = ExtractionResult(
            entities=[], relations=[], raw_text="一些普通文本"
        )
        result = self.ctx_builder.build_context("一些普通文本")
        self.assertEqual(result.context_text, "")
        self.assertEqual(result.matched_entities, [])

    def test_build_context_with_entities(self):
        """测试有实体时的上下文构建"""
        # 模拟抽取结果
        self.mock_extractor.extract.return_value = ExtractionResult(
            entities=[
                Entity(name="张三", entity_type="person"),
                Entity(name="北京大学", entity_type="organization"),
            ],
            relations=[],
            raw_text="张三在北京大学工作",
        )

        # 模拟实体查找
        self.mock_store.find_entity.side_effect = [
            {"name": "张三", "entity_type": "person"},
            {"name": "北京大学", "entity_type": "organization"},
        ]

        # 模拟子图检索
        self.mock_store.get_subgraph_by_entities.return_value = {
            "nodes": [
                {"name": "张三", "entity_type": "person", "mention_count": 5},
                {"name": "北京大学", "entity_type": "organization", "mention_count": 3},
            ],
            "edges": [
                {"source": "张三", "target": "北京大学", "relation_type": "works_at"},
            ],
        }

        result = self.ctx_builder.build_context("张三在北京大学做什么？")

        self.assertIn("张三", result.context_text)
        self.assertIn("北京大学", result.context_text)
        self.assertGreater(len(result.matched_entities), 0)
        self.assertGreater(len(result.subgraph["nodes"]), 0)

    def test_build_context_entity_not_in_db(self):
        """测试实体不在数据库中"""
        self.mock_extractor.extract.return_value = ExtractionResult(
            entities=[Entity(name="不存在的人", entity_type="person")],
            relations=[],
            raw_text="不存在的人",
        )

        # 精确查找返回 None
        self.mock_store.find_entity.return_value = None
        # 模糊搜索也返回空
        self.mock_store.search_entities.return_value = []

        result = self.ctx_builder.build_context("不存在的人")
        self.assertEqual(result.context_text, "")

    def test_build_context_truncation(self):
        """测试上下文截断"""
        self.config.max_context_chars = 50

        self.mock_extractor.extract.return_value = ExtractionResult(
            entities=[Entity(name="测试", entity_type="concept")],
            relations=[],
            raw_text="测试",
        )
        self.mock_store.find_entity.return_value = {"name": "测试"}

        # 返回大量数据
        nodes = [{"name": f"实体{i}", "entity_type": "concept", "mention_count": 1} for i in range(50)]
        edges = [{"source": f"实体{i}", "target": f"实体{i+1}", "relation_type": "related_to"} for i in range(49)]
        self.mock_store.get_subgraph_by_entities.return_value = {
            "nodes": nodes, "edges": edges,
        }

        result = self.ctx_builder.build_context("测试")
        # 上下文文本应该被截断
        if result.context_text:
            self.assertLessEqual(len(result.context_text), 50 + 10)  # 允许 "..." 后缀

    def test_context_result_to_dict(self):
        """测试 ContextResult 序列化"""
        result = ContextResult(
            context_text="测试上下文",
            subgraph={"nodes": [{"name": "A"}], "edges": []},
            matched_entities=["A"],
        )
        d = result.to_dict()
        self.assertEqual(d["context_text"], "测试上下文")
        self.assertEqual(d["entity_count"], 1)
        self.assertEqual(d["edge_count"], 0)


class TestSubgraphContextPrompt(unittest.TestCase):
    """系统提示词构建测试"""

    def setUp(self):
        self.mock_store = MagicMock(spec=GraphStore)
        self.mock_extractor = MagicMock(spec=EntityExtractor)
        self.ctx_builder = SubgraphContext(
            graph_store=self.mock_store,
            extractor=self.mock_extractor,
        )

    def test_build_system_prompt_no_context(self):
        """测试无上下文时返回原始提示词"""
        self.mock_extractor.extract.return_value = ExtractionResult()
        prompt = self.ctx_builder.build_system_prompt("你好", base_system_prompt="你是助手")
        self.assertEqual(prompt, "你是助手")

    def test_build_system_prompt_with_context(self):
        """测试有上下文时增强提示词"""
        self.mock_extractor.extract.return_value = ExtractionResult(
            entities=[Entity(name="AI", entity_type="concept")],
        )
        self.mock_store.find_entity.return_value = {"name": "AI"}
        self.mock_store.get_subgraph_by_entities.return_value = {
            "nodes": [
                {"name": "AI", "entity_type": "concept", "mention_count": 1},
                {"name": "[META] AI相关知识帮助解释当前问题", "entity_type": "meta_knowledge", "mention_count": 3},
            ],
            "edges": [],
        }

        prompt = self.ctx_builder.build_system_prompt(
            "什么是AI？", base_system_prompt="你是助手"
        )
        self.assertIn("你是助手", prompt)
        self.assertIn("当前上下文", prompt)
        self.assertIn("用户当前问题：什么是AI？", prompt)
        self.assertIn("相关记忆与知识", prompt)
        self.assertIn("### 已知实体", prompt)
        self.assertIn("### 相关元知识", prompt)
        self.assertIn("AI", prompt)


    def test_low_information_short_concepts_are_ranked_lower(self):
        self.mock_extractor.extract.return_value = ExtractionResult(
            entities=[Entity(name="AI", entity_type="concept")],
        )
        self.mock_store.find_entity.return_value = {"name": "AI"}
        self.mock_store.get_subgraph_by_entities.return_value = {
            "nodes": [
                {"name": "消息总结", "entity_type": "concept", "mention_count": 100},
                {"name": "AI", "entity_type": "concept", "mention_count": 5},
                {"name": "机器学习", "entity_type": "concept", "mention_count": 4},
            ],
            "edges": [],
        }

        result = self.ctx_builder.build_context("什么是AI？")
        node_names = [n["name"] for n in result.subgraph["nodes"]]

        self.assertIn("AI", node_names)
        self.assertIn("机器学习", node_names)
        self.assertIn("消息总结", node_names)
        self.assertLess(node_names.index("AI"), node_names.index("消息总结"))
        self.assertLess(node_names.index("机器学习"), node_names.index("消息总结"))

    def test_related_to_edges_are_ranked_lower_than_specific_relations(self):
        edges = self.ctx_builder._sanitize_edges(
            [
                {"source": "AI", "target": "机器学习", "relation_type": "related_to"},
                {"source": "AI", "target": "OpenAI", "relation_type": "created_by"},
            ],
            {"AI", "机器学习", "OpenAI"},
        )
        relation_types = [e["relation_type"] for e in edges]
        self.assertEqual(relation_types[0], "created_by")
        self.assertEqual(relation_types[1], "related_to")

    def test_generic_meta_nodes_are_ranked_lower(self):
        meta_nodes = self.ctx_builder._sanitize_meta_nodes([
            {"name": "[META] 系统稳定性作为核心机制驱动整体演化", "entity_type": "meta_knowledge", "mention_count": 10},
            {"name": "[META] AI相关知识帮助解释当前问题", "entity_type": "meta_knowledge", "mention_count": 3},
        ])
        self.assertEqual(meta_nodes[0]["name"], "[META] AI相关知识帮助解释当前问题")

    def test_prepare_subgraph_uses_split_budgets(self):
        self.ctx_builder._config.max_context_chars = 300
        prepared = self.ctx_builder._prepare_subgraph_for_prompt({
            "nodes": [
                {"name": "AI", "entity_type": "concept", "mention_count": 5},
                {"name": "机器学习", "entity_type": "concept", "mention_count": 4},
                {"name": "OpenAI", "entity_type": "organization", "mention_count": 3},
                {"name": "神经网络", "entity_type": "concept", "mention_count": 2},
            ],
            "edges": [
                {"source": "AI", "target": "OpenAI", "relation_type": "created_by"},
                {"source": "AI", "target": "机器学习", "relation_type": "related_to"},
                {"source": "机器学习", "target": "神经网络", "relation_type": "part_of"},
            ],
        })
        self.assertLessEqual(len(prepared["nodes"]), 3)
        self.assertLessEqual(len(prepared["edges"]), 2)
        self.assertIn("meta_nodes", prepared)



class TestRelationReadable(unittest.TestCase):
    """关系可读化测试"""

    def test_known_relation_types(self):
        """测试已知关系类型的可读化"""
        self.assertEqual(SubgraphContext._relation_to_readable("works_at"), "工作于")
        self.assertEqual(SubgraphContext._relation_to_readable("located_in"), "位于")
        self.assertEqual(SubgraphContext._relation_to_readable("part_of"), "属于")

    def test_unknown_relation_type(self):
        """测试未知关系类型"""
        result = SubgraphContext._relation_to_readable("custom_type")
        self.assertEqual(result, "[custom_type]")


class TestSessionContext(unittest.TestCase):
    """会话级上下文缓存测试"""

    def setUp(self):
        self.config = SubgraphConfig()
        self.initial_context = ContextResult(
            context_text="初始上下文",
            subgraph={
                "nodes": [
                    {"name": "张三", "entity_type": "person"},
                    {"name": "北京大学", "entity_type": "organization"},
                ],
                "edges": [
                    {"source": "张三", "target": "北京大学", "relation_type": "works_at"},
                ],
            },
            matched_entities=["张三", "北京大学"],
            extraction=ExtractionResult(
                entities=[
                    Entity(name="张三", entity_type="person"),
                    Entity(name="北京大学", entity_type="organization"),
                ],
            ),
        )

    def test_session_context_initialization(self):
        """测试会话上下文初始化"""
        session = SessionContext(self.initial_context, self.config)
        self.assertEqual(session.cached_entities, {"张三", "北京大学"})
        self.assertEqual(len(session.session_extractions), 1)

    def test_calculate_entity_overlap_high(self):
        """测试高重叠度（主题未变化）"""
        session = SessionContext(self.initial_context, self.config)
        # 新消息包含缓存中的实体
        overlap = session.calculate_entity_overlap(["张三", "北京大学", "学习"])
        self.assertGreaterEqual(overlap, self.config.topic_shift_threshold)

    def test_calculate_entity_overlap_low(self):
        """测试低重叠度（主题变化）"""
        session = SessionContext(self.initial_context, self.config)
        # 新消息完全不同的实体
        overlap = session.calculate_entity_overlap(["李四", "清华大学"])
        self.assertLess(overlap, self.config.topic_shift_threshold)

    def test_update_with_extraction_no_refresh(self):
        """测试更新而不刷新子图"""
        session = SessionContext(self.initial_context, self.config)
        new_extraction = ExtractionResult(
            entities=[
                Entity(name="张三", entity_type="person"),
                Entity(name="AI研究", entity_type="concept"),
            ],
        )
        session.update_with_extraction(new_extraction, new_subgraph=None)
        
        # 缓存实体应该增加新实体
        self.assertIn("AI研究", session.cached_entities)
        self.assertEqual(len(session.session_extractions), 2)

    def test_update_with_extraction_with_refresh(self):
        """测试更新并刷新子图"""
        session = SessionContext(self.initial_context, self.config)
        new_extraction = ExtractionResult(
            entities=[
                Entity(name="李四", entity_type="person"),
                Entity(name="清华大学", entity_type="organization"),
            ],
        )
        new_subgraph = {
            "nodes": [
                {"name": "李四", "entity_type": "person"},
                {"name": "清华大学", "entity_type": "organization"},
            ],
            "edges": [],
        }
        session.update_with_extraction(new_extraction, new_subgraph=new_subgraph)
        
        # 缓存应该被替换
        self.assertEqual(session.cached_entities, {"李四", "清华大学"})
        self.assertEqual(len(session.session_extractions), 2)


class TestSubgraphContextSession(unittest.TestCase):
    """会话模式测试"""

    def setUp(self):
        self.mock_store = MagicMock(spec=GraphStore)
        self.mock_extractor = MagicMock(spec=EntityExtractor)
        self.config = SubgraphConfig(session_cache_enabled=True, topic_shift_threshold=0.3)
        self.ctx_builder = SubgraphContext(
            graph_store=self.mock_store,
            extractor=self.mock_extractor,
            config=self.config,
        )

    def test_start_session(self):
        """测试会话开始"""
        self.mock_extractor.extract.return_value = ExtractionResult(
            entities=[Entity(name="张三", entity_type="person")],
        )
        self.mock_store.find_entity.return_value = {"name": "张三"}
        self.mock_store.get_subgraph_by_entities.return_value = {
            "nodes": [{"name": "张三", "entity_type": "person"}],
            "edges": [],
        }

        result = self.ctx_builder.start_session("张三是谁？")
        self.assertIsNotNone(self.ctx_builder._session)
        self.assertIn("张三", result.context_text)

    def test_get_context_no_topic_shift(self):
        """测试主题未变化时使用缓存"""
        # 初始化会话
        self.mock_extractor.extract.side_effect = [
            ExtractionResult(
                entities=[Entity(name="张三", entity_type="person")],
            ),
            ExtractionResult(
                entities=[Entity(name="张三", entity_type="person")],
            ),
        ]
        self.mock_store.find_entity.return_value = {"name": "张三"}
        self.mock_store.get_subgraph_by_entities.return_value = {
            "nodes": [{"name": "张三", "entity_type": "person"}],
            "edges": [],
        }

        self.ctx_builder.start_session("张三是谁？")
        
        # 第二条消息，主题相同
        result = self.ctx_builder.get_context("张三在哪里工作？")
        
        # 应该只调用一次 get_subgraph_by_entities（在 start_session 时）
        self.assertEqual(self.mock_store.get_subgraph_by_entities.call_count, 1)

    def test_get_context_with_topic_shift(self):
        """测试主题变化时刷新子图"""
        # 初始化会话
        self.mock_extractor.extract.side_effect = [
            ExtractionResult(
                entities=[Entity(name="张三", entity_type="person")],
            ),
            ExtractionResult(
                entities=[Entity(name="李四", entity_type="person")],
            ),
        ]
        self.mock_store.find_entity.side_effect = [
            {"name": "张三"},
            {"name": "李四"},
        ]
        self.mock_store.get_subgraph_by_entities.side_effect = [
            {
                "nodes": [{"name": "张三", "entity_type": "person"}],
                "edges": [],
            },
            {
                "nodes": [{"name": "李四", "entity_type": "person"}],
                "edges": [],
            },
        ]

        self.ctx_builder.start_session("张三是谁？")
        
        # 第二条消息，主题完全不同
        result = self.ctx_builder.get_context("李四在哪里？")
        
        # 应该调用两次 get_subgraph_by_entities（主题变化时重新检索）
        self.assertEqual(self.mock_store.get_subgraph_by_entities.call_count, 2)
        self.assertIn("李四", result.context_text)

    def test_end_session(self):
        """测试会话结束"""
        self.mock_extractor.extract.side_effect = [
            ExtractionResult(
                entities=[Entity(name="张三", entity_type="person")],
            ),
            ExtractionResult(
                entities=[Entity(name="北京大学", entity_type="organization")],
            ),
        ]
        self.mock_store.find_entity.return_value = {"name": "张三"}
        self.mock_store.get_subgraph_by_entities.return_value = {
            "nodes": [{"name": "张三", "entity_type": "person"}],
            "edges": [],
        }

        self.ctx_builder.start_session("张三是谁？")
        self.ctx_builder.get_context("他在北京大学工作")
        
        extractions = self.ctx_builder.end_session()
        
        # 应该返回两个抽取结果
        self.assertEqual(len(extractions), 2)
        self.assertIsNone(self.ctx_builder._session)

    def test_session_cache_disabled(self):
        """测试禁用会话缓存时的行为"""
        config = SubgraphConfig(session_cache_enabled=False)
        ctx_builder = SubgraphContext(
            graph_store=self.mock_store,
            extractor=self.mock_extractor,
            config=config,
        )

        self.mock_extractor.extract.return_value = ExtractionResult(
            entities=[Entity(name="张三", entity_type="person")],
        )
        self.mock_store.find_entity.return_value = {"name": "张三"}
        self.mock_store.get_subgraph_by_entities.return_value = {
            "nodes": [{"name": "张三", "entity_type": "person"}],
            "edges": [],
        }

        # 即使调用 start_session，也不应该创建会话缓存
        result = ctx_builder.start_session("张三是谁？")
        self.assertIsNone(ctx_builder._session)


if __name__ == "__main__":
    unittest.main()
