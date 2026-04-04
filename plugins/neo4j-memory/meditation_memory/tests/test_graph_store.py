"""
图数据库存储层的单元测试

使用 mock 模拟 Neo4j 驱动，不依赖真实数据库。
"""

import json
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

from meditation_memory.config import Neo4jConfig
from meditation_memory.entity_extractor import Entity, Relation
from meditation_memory.graph_store import GraphStore


class TestGraphStoreInit(unittest.TestCase):
    """GraphStore 初始化测试"""

    def test_default_config(self):
        """测试默认配置"""
        store = GraphStore()
        self.assertIsNotNone(store._config)
        self.assertEqual(store._config.uri, "bolt://localhost:7687")

    def test_custom_config(self):
        """测试自定义配置"""
        config = Neo4jConfig(uri="bolt://custom:7687", user="admin", password="secret")
        store = GraphStore(config)
        self.assertEqual(store._config.uri, "bolt://custom:7687")
        self.assertEqual(store._config.user, "admin")

    def test_driver_lazy_init(self):
        """测试驱动延迟初始化"""
        store = GraphStore()
        self.assertIsNone(store._driver)


class TestGraphStoreOperations(unittest.TestCase):
    """GraphStore 操作测试（使用 mock）"""

    def setUp(self):
        self.store = GraphStore(Neo4jConfig())
        # 创建 mock driver 和 session
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__ = MagicMock(return_value=self.mock_session)
        self.mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)
        self.store._driver = self.mock_driver

    def test_upsert_entity(self):
        """测试实体写入"""
        entity = Entity(name="张三", entity_type="person")

        # 模拟查询结果
        mock_record = {"eid": "4:xxx:0"}
        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result

        eid = self.store.upsert_entity(entity)
        self.assertEqual(eid, "4:xxx:0")

        # 验证 Cypher 查询被调用
        self.mock_session.run.assert_called_once()
        call_args = self.mock_session.run.call_args
        self.assertIn("MERGE", call_args[0][0])
        self.assertEqual(call_args[1]["name"], "张三")
        self.assertEqual(call_args[1]["entity_type"], "person")

    def test_upsert_entities_batch(self):
        """测试批量实体写入"""
        entities = [
            Entity(name="张三", entity_type="person"),
            Entity(name="北京", entity_type="place"),
            Entity(name="人工智能", entity_type="concept"),
        ]

        mock_record = {"eid": "4:xxx:0"}
        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result

        count = self.store.upsert_entities(entities)
        self.assertEqual(count, 3)

    def test_upsert_relation(self):
        """测试关系写入"""
        relation = Relation(
            source="张三",
            target="北京大学",
            relation_type="works_at",
        )

        mock_record = {"rel_type": "RELATES_TO"}
        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result

        success = self.store.upsert_relation(relation)
        self.assertTrue(success)

        call_args = self.mock_session.run.call_args
        self.assertIn("MERGE", call_args[0][0])
        self.assertEqual(call_args[1]["source"], "张三")
        self.assertEqual(call_args[1]["target"], "北京大学")
        self.assertEqual(call_args[1]["relation_type"], "works_at")

    def test_upsert_relation_no_match(self):
        """测试关系写入时实体不存在"""
        relation = Relation(source="不存在", target="也不存在", relation_type="related_to")

        mock_result = MagicMock()
        mock_result.single.return_value = None
        self.mock_session.run.return_value = mock_result

        success = self.store.upsert_relation(relation)
        self.assertFalse(success)

    def test_find_entity(self):
        """测试实体查找"""
        mock_record = {
            "name": "张三",
            "entity_type": "person",
            "properties": "{}",
            "mention_count": 3,
            "created_at": 1000,
            "updated_at": 2000,
        }
        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result

        entity = self.store.find_entity("张三")
        self.assertIsNotNone(entity)
        self.assertEqual(entity["name"], "张三")

    def test_find_entity_not_found(self):
        """测试查找不存在的实体"""
        mock_result = MagicMock()
        mock_result.single.return_value = None
        self.mock_session.run.return_value = mock_result

        entity = self.store.find_entity("不存在的实体")
        self.assertIsNone(entity)

    def test_search_entities(self):
        """测试实体搜索"""
        mock_records = [
            {"name": "人工智能", "entity_type": "concept", "properties": "{}", "mention_count": 5},
            {"name": "人工智能研究", "entity_type": "concept", "properties": "{}", "mention_count": 2},
        ]
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter(mock_records))
        self.mock_session.run.return_value = mock_result

        # 让全文搜索抛异常，回退到 CONTAINS
        def side_effect(*args, **kwargs):
            query = args[0] if args else ""
            if "fulltext" in query:
                raise Exception("No fulltext index")
            return mock_result

        self.mock_session.run.side_effect = side_effect

        results = self.store.search_entities("人工智能")
        self.assertEqual(len(results), 2)

    def test_get_stats(self):
        """测试统计信息"""
        mock_record = {"node_count": 10, "edge_count": 15}
        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result

        stats = self.store.get_stats()
        self.assertEqual(stats["node_count"], 10)
        self.assertEqual(stats["edge_count"], 15)

    def test_close(self):
        """测试关闭连接"""
        self.store.close()
        self.mock_driver.close.assert_called_once()
        self.assertIsNone(self.store._driver)

    def test_close_when_not_connected(self):
        """测试未连接时关闭不报错"""
        store = GraphStore()
        store.close()  # 不应抛异常

    def test_init_schema(self):
        """测试 schema 初始化"""
        self.mock_session.run.return_value = MagicMock()
        self.store.init_schema()
        # 应该执行了多条索引创建语句
        self.assertGreaterEqual(self.mock_session.run.call_count, 1)


class TestGraphStoreSubgraph(unittest.TestCase):
    """子图检索测试"""

    def setUp(self):
        self.store = GraphStore(Neo4jConfig())
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__ = MagicMock(return_value=self.mock_session)
        self.mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)
        self.store._driver = self.mock_driver

    def test_get_subgraph_empty_names(self):
        """测试空实体名称列表"""
        result = self.store.get_subgraph_by_entities([])
        self.assertEqual(result, {"nodes": [], "edges": []})

    def test_get_subgraph_no_result(self):
        """测试查询无结果"""
        mock_result = MagicMock()
        mock_result.single.return_value = None
        self.mock_session.run.return_value = mock_result

        result = self.store.get_subgraph_by_entities(["不存在"])
        # 应该返回空子图而不是报错
        self.assertIn("nodes", result)
        self.assertIn("edges", result)


if __name__ == "__main__":
    unittest.main()
