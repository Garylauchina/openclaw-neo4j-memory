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

        mock_record = {"updated": 3}
        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result

        count = self.store.upsert_entities(entities)
        self.assertEqual(count, 3)

        call_args = self.mock_session.run.call_args
        batch = call_args[1]["batch"]
        self.assertEqual(len(batch), 3)
        self.assertTrue(all(item["mention_count"] == 1 for item in batch))
        self.assertTrue(all("knowledge_state" in item for item in batch))
        self.assertEqual(call_args[1]["stable_min_evidence_count"], 3)
        self.assertEqual(call_args[1]["stable_min_source_count"], 2)

    def test_get_stats_includes_knowledge_state_counts(self):
        mock_record = {
            "node_count": 10,
            "edge_count": 15,
            "hypothesis_entity_count": 4,
            "stable_entity_count": 6,
        }
        mock_result = MagicMock()
        mock_result.single.return_value = mock_record
        self.mock_session.run.return_value = mock_result

        stats = self.store.get_stats()
        self.assertEqual(stats["hypothesis_entity_count"], 4)
        self.assertEqual(stats["stable_entity_count"], 6)

    def test_upsert_relation(self):
        """测试关系写入"""
        relation = Relation(
            source="张三",
            target="北京大学",
            relation_type="works_at",
            properties={"knowledge_state": "hypothesis", "evidence_count": 1, "source_count": 1, "source_id": "src1"},
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
        self.assertEqual(call_args[1]["knowledge_state"], "hypothesis")
        self.assertEqual(call_args[1]["evidence_count"], 1)
        self.assertEqual(call_args[1]["source_count"], 1)
        self.assertEqual(call_args[1]["source_id"], "src1")

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

    def test_complete_pending_belief(self):
        mock_result = MagicMock()
        mock_result.single.return_value = {"content": "pending::concept::AI"}
        self.mock_session.run.return_value = mock_result

        ok = self.store.complete_pending_belief("pending::concept::AI")
        self.assertTrue(ok)

    def test_get_pending_belief_count(self):
        mock_result = MagicMock()
        mock_result.single.return_value = {"count": 4}
        self.mock_session.run.return_value = mock_result

        count = self.store.get_pending_belief_count()
        self.assertEqual(count, 4)

    def test_expire_pending_beliefs(self):
        mock_result = MagicMock()
        mock_result.single.return_value = {"count": 2}
        self.mock_session.run.return_value = mock_result

        count = self.store.expire_pending_beliefs(3600)
        self.assertEqual(count, 2)
        call_args = self.mock_session.run.call_args
        self.assertEqual(call_args[1]["ttl_ms"], 3600 * 1000)

    def test_upsert_entity_claim(self):
        mock_result = MagicMock()
        mock_result.single.return_value = {"claim_id": "abc123"}
        self.mock_session.run.return_value = mock_result

        claim_id = self.store.upsert_entity_claim("Apple", "organization")
        self.assertEqual(claim_id, "abc123")

    def test_get_entity_claims(self):
        mock_records = [
            {"claim_id": "c1", "entity_name": "Apple", "claim_kind": "entity_typing", "claimed_value": "organization", "state": "stable", "support_score": 2, "conflict_score": 0, "net_confidence": 2},
            {"claim_id": "c2", "entity_name": "Apple", "claim_kind": "entity_typing", "claimed_value": "product", "state": "hypothesis", "support_score": 1, "conflict_score": 1, "net_confidence": 0},
        ]
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter(mock_records))
        self.mock_session.run.return_value = mock_result

        claims = self.store.get_entity_claims("Apple")
        self.assertEqual(len(claims), 2)

    def test_apply_claim_feedback(self):
        mock_result = MagicMock()
        mock_result.single.return_value = {"claim_id": "c1"}
        self.mock_session.run.return_value = mock_result

        ok = self.store.apply_claim_feedback("Apple", "organization", "contradict", delta=1)
        self.assertTrue(ok)

    def test_sync_entity_type_from_claims(self):
        self.store.get_entity_claims = MagicMock(return_value=[
            {"claimed_value": "organization", "state": "stable", "net_confidence": 3},
            {"claimed_value": "product", "state": "hypothesis", "net_confidence": 0},
        ])
        mock_result = MagicMock()
        mock_result.single.return_value = {"name": "Apple", "entity_type": "organization", "knowledge_state": "stable"}
        self.mock_session.run.return_value = mock_result

        result = self.store.sync_entity_type_from_claims("Apple")
        self.assertEqual(result["entity_type"], "organization")

    def test_record_claim_observation(self):
        mock_result = MagicMock()
        mock_result.single.return_value = {"observation_id": "obs1"}
        self.mock_session.run.return_value = mock_result

        obs_id = self.store.record_claim_observation("Apple", "organization", "later_text_evidence", "Observed competing type", "src1", "contradict")
        self.assertEqual(obs_id, "obs1")

    def test_record_claim_outcome(self):
        mock_result = MagicMock()
        mock_result.single.return_value = {"outcome_id": "out1"}
        self.mock_session.run.return_value = mock_result

        out_id = self.store.record_claim_outcome("Apple", "organization", "contradicted", "Competing type observed")
        self.assertEqual(out_id, "out1")

    def test_record_belief_update(self):
        mock_result = MagicMock()
        mock_result.single.return_value = {"update_id": "upd1"}
        self.mock_session.run.return_value = mock_result

        upd_id = self.store.record_belief_update("Apple", "organization", "contradict", 1, "Competing type observed")
        self.assertEqual(upd_id, "upd1")

    def test_build_meta_cluster_signature_is_order_insensitive(self):
        sig1 = self.store._build_meta_cluster_signature(["张三", "项目A", "北京"])
        sig2 = self.store._build_meta_cluster_signature(["北京", "张三", "项目A", "张三"])
        self.assertEqual(sig1, sig2)

    def test_create_meta_knowledge_reuses_existing_signature_match(self):
        self.store._find_meta_knowledge_by_signature = MagicMock(return_value="[META] existing")
        self.store._find_similar_meta_knowledge = MagicMock(return_value=None)

        self.mock_session.run.return_value = MagicMock()

        ok = self.store.create_meta_knowledge_node(
            summary="张三长期参与项目A并与北京相关资源形成稳定协作。",
            related_entity_names=["张三", "项目A", "北京"],
            center_entity_name="张三",
        )

        self.assertTrue(ok)
        self.store._find_meta_knowledge_by_signature.assert_called_once()
        self.store._find_similar_meta_knowledge.assert_not_called()

        reuse_call = self.mock_session.run.call_args_list[0]
        self.assertIn("cluster_signature", reuse_call[1])
        self.assertTrue(any(call.kwargs.get("center_name") == "张三" for call in self.mock_session.run.call_args_list if hasattr(call, "kwargs")))

    def test_get_dense_subgraphs_for_distillation_passes_recent_skip(self):
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([]))
        self.mock_session.run.return_value = mock_result

        self.store.get_dense_subgraphs_for_distillation(min_cluster_size=3, limit=5, skip_recent_seconds=3600)

        call_args = self.mock_session.run.call_args
        self.assertEqual(call_args[1]["skip_recent_ms"], 3600 * 1000)

    def test_get_truncated_entity_candidates_filters_valid_short_names(self):
        self.store.get_short_name_entities = MagicMock(return_value=[
            {"name": "消息总结", "entity_type": "concept", "mention_count": 72, "neighbor_names": ["技术要点"]},
            {"name": "张三", "entity_type": "person", "mention_count": 2, "neighbor_names": ["项目A"]},
            {"name": "代码分支", "entity_type": "concept", "mention_count": 0, "neighbor_names": []},
            {"name": "游", "entity_type": "concept", "mention_count": 0, "neighbor_names": []},
        ])

        results = self.store.get_truncated_entity_candidates(max_name_length=4, skip_recent_seconds=0)
        names = [r["name"] for r in results]

        self.assertEqual(names, ["代码分支", "游"])

    def test_get_truncated_entity_candidates_keeps_short_low_context_candidates(self):
        self.store.get_short_name_entities = MagicMock(return_value=[
            {"name": "AB", "entity_type": "concept", "mention_count": 0, "neighbor_names": []},
            {"name": "接口", "entity_type": "technology", "mention_count": 3, "neighbor_names": ["协议"]},
        ])

        results = self.store.get_truncated_entity_candidates(max_name_length=4, skip_recent_seconds=0)
        names = [r["name"] for r in results]

        self.assertIn("AB", names)
        self.assertNotIn("接口", names)

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
