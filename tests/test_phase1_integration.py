"""
Phase 1 集成测试 — 认知系统与记忆系统融合

测试覆盖：
  1. Neo4jMemoryClient 能正确调用各 API
  2. CognitiveMemoryProvider 能从 Neo4j 检索记忆
  3. RealityGraphWriter 能将数据写入 Neo4j
  4. 降级模式正常工作
  5. CognitiveCore 在新目录结构下能正常初始化和运行
  6. OpenClawCognitiveHook 桥梁功能正常

所有测试使用 unittest + MagicMock，不依赖真实的 Neo4j 或 FastAPI 服务。
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import json
import time


# ---------------------------------------------------------------------------
# 1. Neo4jMemoryClient 测试
# ---------------------------------------------------------------------------

class TestNeo4jMemoryClient(unittest.TestCase):
    """测试 Neo4jMemoryClient 的 HTTP 调用逻辑。"""

    def setUp(self):
        """在每个测试前创建客户端实例。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient
        self.client = Neo4jMemoryClient(
            base_url="http://127.0.0.1:18900",
            timeout=5,
            max_retries=2,
        )

    def test_init_defaults(self):
        """测试默认初始化参数。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient
        client = Neo4jMemoryClient()
        self.assertEqual(client.base_url, "http://127.0.0.1:18900")
        self.assertEqual(client.timeout, 10)
        self.assertEqual(client.max_retries, 3)

    def test_health_check_success(self):
        """测试健康检查成功。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(self.client._session, "get", return_value=mock_response):
            result = self.client.health_check()
            self.assertTrue(result)

    def test_health_check_degraded(self):
        """测试健康检查降级状态也返回 True。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "degraded"}
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(self.client._session, "get", return_value=mock_response):
            result = self.client.health_check()
            self.assertTrue(result)

    def test_health_check_failure(self):
        """测试健康检查失败返回 False。"""
        with patch.object(
            self.client._session, "get", side_effect=ConnectionError("refused")
        ):
            result = self.client.health_check()
            self.assertFalse(result)

    def test_search_success(self):
        """测试搜索 API 成功调用。"""
        expected_response = {
            "status": "success",
            "context": {
                "context_text": "### 已知实体\n- 人物：张三",
                "subgraph": {
                    "nodes": [
                        {"name": "张三", "entity_type": "person", "mention_count": 3}
                    ],
                    "edges": [
                        {
                            "source": "张三",
                            "target": "北京",
                            "relation_type": "lives_in",
                        }
                    ],
                },
                "matched_entities": ["张三"],
                "entity_count": 1,
                "edge_count": 1,
            },
        }

        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(self.client._session, "post", return_value=mock_response):
            result = self.client.search("张三住在哪里", limit=5)

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "success")
        self.assertIn("context", result)
        self.assertEqual(len(result["context"]["subgraph"]["nodes"]), 1)

    def test_search_failure_returns_none(self):
        """测试搜索失败返回 None。"""
        with patch.object(
            self.client._session, "post", side_effect=ConnectionError("refused")
        ):
            result = self.client.search("test query")
            self.assertIsNone(result)

    def test_ingest_success(self):
        """测试写入 API 成功调用。"""
        expected_response = {"status": "accepted", "message": "Ingest task queued."}

        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(self.client._session, "post", return_value=mock_response):
            result = self.client.ingest("张三住在北京", use_llm=True)

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "accepted")

    def test_ingest_with_session_id(self):
        """测试带 session_id 的写入。"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "accepted"}
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(self.client._session, "post", return_value=mock_response) as mock_post:
            self.client.ingest("test", session_id="sess-123")
            call_args = mock_post.call_args
            payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1]
            self.assertIn("session_id", json.dumps(payload) if isinstance(payload, str) else str(payload))

    def test_get_stats_success(self):
        """测试统计 API 调用。"""
        expected = {"status": "ok", "stats": {"entities": 100, "relations": 50}}
        mock_response = MagicMock()
        mock_response.json.return_value = expected
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()

        with patch.object(self.client._session, "get", return_value=mock_response):
            result = self.client.get_stats()
            self.assertIsNotNone(result)
            self.assertEqual(result["status"], "ok")

    def test_retry_logic(self):
        """测试重试逻辑。"""
        # 第一次失败，第二次成功
        mock_fail = MagicMock(side_effect=ConnectionError("refused"))
        mock_success = MagicMock()
        mock_success.json.return_value = {"status": "ok"}
        mock_success.raise_for_status = MagicMock()

        with patch.object(
            self.client._session, "get", side_effect=[ConnectionError("fail"), mock_success]
        ):
            result = self.client._get("/health")
            self.assertIsNotNone(result)
            self.assertEqual(result["status"], "ok")

    def test_close(self):
        """测试关闭会话。"""
        with patch.object(self.client._session, "close") as mock_close:
            self.client.close()
            mock_close.assert_called_once()


# ---------------------------------------------------------------------------
# 2. CognitiveMemoryProvider 测试
# ---------------------------------------------------------------------------

class TestCognitiveMemoryProvider(unittest.TestCase):
    """测试 CognitiveMemoryProvider 的记忆检索功能。"""

    def _make_mock_client(self, healthy=True, search_result=None):
        """创建 Mock Neo4jMemoryClient。"""
        client = MagicMock()
        client.health_check.return_value = healthy
        client.search.return_value = search_result
        return client

    def test_init_with_neo4j(self):
        """测试 Neo4j 可用时的初始化。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider
        client = self._make_mock_client(healthy=True)
        provider = CognitiveMemoryProvider(neo4j_client=client)
        self.assertTrue(provider._use_neo4j)

    def test_init_without_neo4j(self):
        """测试 Neo4j 不可用时降级到 Mock 模式。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider
        client = self._make_mock_client(healthy=False)
        provider = CognitiveMemoryProvider(neo4j_client=client)
        self.assertFalse(provider._use_neo4j)

    def test_init_mock_mode(self):
        """测试强制 Mock 模式。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider
        client = self._make_mock_client(healthy=True)
        provider = CognitiveMemoryProvider(neo4j_client=client, mock_mode=True)
        self.assertFalse(provider._use_neo4j)

    def test_retrieve_from_neo4j(self):
        """测试从 Neo4j 检索记忆。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider

        search_result = {
            "status": "success",
            "context": {
                "context_text": "### 已知实体\n- 人物：张三\n- 地点：北京",
                "subgraph": {
                    "nodes": [
                        {"name": "张三", "entity_type": "person", "mention_count": 5},
                        {"name": "北京", "entity_type": "location", "mention_count": 3},
                    ],
                    "edges": [
                        {
                            "source": "张三",
                            "target": "北京",
                            "relation_type": "lives_in",
                            "weight": 0.8,
                        }
                    ],
                },
                "matched_entities": ["张三", "北京"],
                "entity_count": 2,
                "edge_count": 1,
            },
        }

        client = self._make_mock_client(healthy=True, search_result=search_result)
        provider = CognitiveMemoryProvider(neo4j_client=client)
        results = provider.retrieve("张三住在哪里", k=5)

        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        # 检查结果格式（to_claw_format 输出）
        for r in results:
            self.assertIn("text", r)
            self.assertIn("score", r)
            self.assertIn("rank", r)
            self.assertIn("metadata", r)

        # 验证 search 被调用
        client.search.assert_called_once()

    def test_retrieve_neo4j_failure_fallback(self):
        """测试 Neo4j 搜索失败时降级到 Mock。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider

        client = self._make_mock_client(healthy=True, search_result=None)
        provider = CognitiveMemoryProvider(neo4j_client=client)
        results = provider.retrieve("测试查询", k=5)

        # 应该返回空列表（Mock 模式无图数据）
        self.assertIsInstance(results, list)
        self.assertEqual(provider.stats["mock_queries"], 1)

    def test_retrieve_fx_enhancement(self):
        """测试汇率查询增强。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider

        search_result = {
            "status": "success",
            "context": {
                "context_text": "",
                "subgraph": {"nodes": [], "edges": []},
                "matched_entities": [],
                "entity_count": 0,
                "edge_count": 0,
            },
        }

        client = self._make_mock_client(healthy=True, search_result=search_result)
        provider = CognitiveMemoryProvider(neo4j_client=client)

        # Mock FX API
        with patch(
            "cognitive_engine.adapters.memory_provider.get_usd_cny",
            return_value="7.2345",
        ):
            results = provider.retrieve("USD兑换人民币汇率", k=5)

        # 应该包含实时汇率节点
        fx_results = [r for r in results if "real_world_api" in str(r.get("metadata", {}).get("source", ""))]
        self.assertGreater(len(fx_results), 0)
        self.assertEqual(provider.stats["reality_enhanced_queries"], 1)

    def test_parse_context_entities(self):
        """测试 context 解析 — 实体节点。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider

        client = self._make_mock_client(healthy=False)
        provider = CognitiveMemoryProvider(neo4j_client=client)

        context = {
            "context_text": "",
            "subgraph": {
                "nodes": [
                    {"name": "Alice", "entity_type": "person", "mention_count": 10},
                ],
                "edges": [],
            },
        }

        nodes = provider._parse_context(context, k=5)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]["content"], "Alice")
        self.assertEqual(nodes[0]["source"], "neo4j_graph")

    def test_parse_context_edges(self):
        """测试 context 解析 — 关系节点。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider

        client = self._make_mock_client(healthy=False)
        provider = CognitiveMemoryProvider(neo4j_client=client)

        context = {
            "context_text": "",
            "subgraph": {
                "nodes": [],
                "edges": [
                    {
                        "source": "Alice",
                        "target": "Bob",
                        "relation_type": "knows",
                        "weight": 0.9,
                    }
                ],
            },
        }

        nodes = provider._parse_context(context, k=5)
        self.assertEqual(len(nodes), 1)
        self.assertIn("knows", nodes[0]["content"])

    def test_get_stats(self):
        """测试统计信息获取。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider
        client = self._make_mock_client(healthy=False)
        provider = CognitiveMemoryProvider(neo4j_client=client)
        stats = provider.get_stats()
        self.assertIn("performance", stats)
        self.assertIn("cache", stats)
        self.assertIn("status", stats)


# ---------------------------------------------------------------------------
# 3. RealityGraphWriter 测试
# ---------------------------------------------------------------------------

class TestRealityGraphWriter(unittest.TestCase):
    """测试 RealityGraphWriter 的数据写入功能。"""

    def _make_mock_client(self, healthy=True, ingest_result=None):
        """创建 Mock Neo4jMemoryClient。"""
        client = MagicMock()
        client.health_check.return_value = healthy
        client.ingest.return_value = ingest_result or {
            "status": "accepted",
            "message": "Ingest task queued.",
        }
        return client

    def test_init_with_neo4j(self):
        """测试 Neo4j 可用时的初始化。"""
        from cognitive_engine.adapters.reality_writer import RealityGraphWriter
        client = self._make_mock_client(healthy=True)
        writer = RealityGraphWriter(neo4j_client=client)
        self.assertTrue(writer._use_neo4j)

    def test_init_without_neo4j(self):
        """测试 Neo4j 不可用时降级。"""
        from cognitive_engine.adapters.reality_writer import RealityGraphWriter
        client = self._make_mock_client(healthy=False)
        writer = RealityGraphWriter(neo4j_client=client)
        self.assertFalse(writer._use_neo4j)

    def test_write_to_memory_and_neo4j(self):
        """测试同时写入内存和 Neo4j。"""
        from cognitive_engine.adapters.reality_writer import RealityGraphWriter

        client = self._make_mock_client(healthy=True)
        writer = RealityGraphWriter(neo4j_client=client)

        node = writer.write_reality_data(
            content="USD/CNY汇率",
            value=7.23,
            type="temporal",
            source="fx_api",
            rqs=0.95,
        )

        # 验证内存写入
        self.assertIsNotNone(node)
        self.assertEqual(node.content, "USD/CNY汇率")
        self.assertEqual(node.value, 7.23)
        self.assertIn("USD/CNY汇率", writer.temporal_nodes)

        # 验证 Neo4j 写入
        client.ingest.assert_called_once()
        self.assertEqual(writer.stats["neo4j_writes"], 1)
        self.assertEqual(writer.stats["high_confidence_writes"], 1)

    def test_write_memory_only(self):
        """测试纯内存写入（Neo4j 不可用）。"""
        from cognitive_engine.adapters.reality_writer import RealityGraphWriter

        client = self._make_mock_client(healthy=False)
        writer = RealityGraphWriter(neo4j_client=client)

        node = writer.write_reality_data(
            content="测试数据",
            value=42,
            type="fact",
            source="test",
            rqs=0.5,
        )

        self.assertIsNotNone(node)
        self.assertEqual(node.content, "测试数据")
        client.ingest.assert_not_called()
        self.assertEqual(writer.stats["neo4j_writes"], 0)

    def test_write_update_existing(self):
        """测试更新已有节点。"""
        from cognitive_engine.adapters.reality_writer import RealityGraphWriter

        client = self._make_mock_client(healthy=False)
        writer = RealityGraphWriter(neo4j_client=client)

        writer.write_reality_data(content="汇率", value=7.0, type="temporal", source="api")
        writer.write_reality_data(content="汇率", value=7.1, type="temporal", source="api")

        self.assertEqual(writer.stats["updates"], 1)
        self.assertEqual(writer.temporal_nodes["汇率"].value, 7.1)

    def test_neo4j_ingest_failure(self):
        """测试 Neo4j 写入失败不影响本地。"""
        from cognitive_engine.adapters.reality_writer import RealityGraphWriter

        client = self._make_mock_client(healthy=True)
        client.ingest.return_value = None  # 模拟失败

        writer = RealityGraphWriter(neo4j_client=client)
        node = writer.write_reality_data(
            content="失败测试",
            value=1,
            type="temporal",
            source="test",
        )

        # 本地写入成功
        self.assertIsNotNone(node)
        self.assertIn("失败测试", writer.temporal_nodes)
        # Neo4j 失败计数
        self.assertEqual(writer.stats["neo4j_failures"], 1)

    def test_temporal_node_belief_decay(self):
        """测试时间节点信念衰减。"""
        from cognitive_engine.adapters.reality_writer import TemporalNode
        from datetime import datetime, timedelta

        node = TemporalNode(
            content="旧数据",
            value=100,
            node_type="temporal",
            source="test",
            timestamp=datetime.now() - timedelta(hours=48),
            belief_strength=0.9,
        )

        current_belief = node.get_current_belief()
        self.assertLess(current_belief, 0.9)
        self.assertTrue(node.should_refresh())

    def test_cleanup_expired(self):
        """测试清理过期节点。"""
        from cognitive_engine.adapters.reality_writer import RealityGraphWriter, TemporalNode
        from datetime import datetime, timedelta

        writer = RealityGraphWriter(mock_mode=True)

        # 添加一个旧节点
        old_node = TemporalNode(
            content="过期数据",
            value=0,
            node_type="temporal",
            source="test",
            timestamp=datetime.now() - timedelta(hours=200),
            belief_strength=0.1,
        )
        writer.temporal_nodes["过期数据"] = old_node

        # 添加一个新节点
        writer.write_reality_data(content="新数据", value=1, type="fact", source="test")

        removed = writer.cleanup_expired(belief_threshold=0.1)
        self.assertGreaterEqual(removed, 1)
        self.assertNotIn("过期数据", writer.temporal_nodes)

    def test_get_stats(self):
        """测试统计信息。"""
        from cognitive_engine.adapters.reality_writer import RealityGraphWriter
        writer = RealityGraphWriter(mock_mode=True)
        writer.write_reality_data(content="A", value=1, type="temporal", source="test")
        stats = writer.get_stats()
        self.assertIn("node_summary", stats)
        self.assertIn("performance", stats)
        self.assertIn("neo4j_status", stats)
        self.assertEqual(stats["node_summary"]["total_nodes"], 1)


# ---------------------------------------------------------------------------
# 4. 降级模式测试
# ---------------------------------------------------------------------------

class TestDegradedMode(unittest.TestCase):
    """测试各组件在 Neo4j 不可用时的降级行为。"""

    def test_provider_degrades_gracefully(self):
        """测试 Provider 在无 Neo4j 客户端时正常工作。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider
        provider = CognitiveMemoryProvider(neo4j_client=None)
        self.assertFalse(provider._use_neo4j)
        results = provider.retrieve("测试", k=3)
        self.assertIsInstance(results, list)

    def test_writer_degrades_gracefully(self):
        """测试 Writer 在无 Neo4j 客户端时正常工作。"""
        from cognitive_engine.adapters.reality_writer import RealityGraphWriter
        writer = RealityGraphWriter(neo4j_client=None)
        self.assertFalse(writer._use_neo4j)
        node = writer.write_reality_data(content="降级测试", value=1, type="fact", source="test")
        self.assertIsNotNone(node)

    def test_cognitive_core_degrades_gracefully(self):
        """测试 CognitiveCore 在 Neo4j 不可用时正常初始化。"""
        from cognitive_engine.cognitive_core import CognitiveCore
        from cognitive_engine.neo4j_client import Neo4jMemoryClient

        mock_client = MagicMock(spec=Neo4jMemoryClient)
        mock_client.health_check.return_value = False

        core = CognitiveCore(neo4j_client=mock_client)
        self.assertFalse(core.writer._use_neo4j)
        self.assertFalse(core.memory_provider._use_neo4j)

        # 仍然可以获取统计
        stats = core.get_stats()
        self.assertIn("processing", stats)
        self.assertIn("neo4j", stats)
        self.assertFalse(stats["neo4j"]["writer_connected"])


# ---------------------------------------------------------------------------
# 5. CognitiveCore 初始化和运行测试
# ---------------------------------------------------------------------------

class TestCognitiveCore(unittest.TestCase):
    """测试 CognitiveCore 在新目录结构下的初始化和运行。"""

    def _make_mock_client(self):
        """创建 Mock Neo4jMemoryClient。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient
        client = MagicMock(spec=Neo4jMemoryClient)
        client.health_check.return_value = False
        client.search.return_value = None
        client.ingest.return_value = None
        return client

    def test_init_success(self):
        """测试正常初始化。"""
        from cognitive_engine.cognitive_core import CognitiveCore
        core = CognitiveCore(neo4j_client=self._make_mock_client())
        self.assertIsNotNone(core.writer)
        self.assertIsNotNone(core.memory_provider)
        self.assertIsNotNone(core.validator)
        self.assertIsNotNone(core.strategy_engine)
        self.assertIsNotNone(core.goal_generator)
        self.assertIsNotNone(core.plan_generator)
        self.assertIsNotNone(core.action_generator)

    def test_config_defaults(self):
        """测试默认配置。"""
        from cognitive_engine.cognitive_core import CognitiveCore
        core = CognitiveCore(neo4j_client=self._make_mock_client())
        self.assertTrue(core.config["enabled"])
        self.assertIn("neo4j_api_base", core.config)
        self.assertIn("settings", core.config)
        self.assertTrue(core.config["settings"]["cache_enabled"])

    def test_process_query_general(self):
        """测试一般查询处理。"""
        from cognitive_engine.cognitive_core import CognitiveCore
        core = CognitiveCore(neo4j_client=self._make_mock_client())

        result = core.process_query("什么是人工智能？")

        self.assertIsInstance(result, dict)
        self.assertIn("query", result)
        self.assertIn("metadata", result)
        self.assertIn("formatted_text", result)
        self.assertEqual(result["query"], "什么是人工智能？")
        self.assertEqual(core.stats["total_queries"], 1)

    def test_process_query_cache(self):
        """测试缓存命中。"""
        from cognitive_engine.cognitive_core import CognitiveCore
        core = CognitiveCore(neo4j_client=self._make_mock_client())

        # 第一次查询
        result1 = core.process_query("测试缓存")
        # 第二次相同查询
        result2 = core.process_query("测试缓存")

        self.assertEqual(core.cache_hits, 1)
        self.assertEqual(core.cache_misses, 1)

    def test_adjust_score(self):
        """测试 RQS 调整接口。"""
        from cognitive_engine.cognitive_core import CognitiveCore
        core = CognitiveCore(neo4j_client=self._make_mock_client())
        # 不应抛异常
        core.adjust_score(0.1)
        core.adjust_score(-0.3)

    def test_update_belief(self):
        """测试信念更新接口。"""
        from cognitive_engine.cognitive_core import CognitiveCore
        core = CognitiveCore(neo4j_client=self._make_mock_client())
        # 不应抛异常
        core.update_belief(evidence={"test": True}, impact=0.1, confidence=0.8)

    def test_get_stats(self):
        """测试统计信息。"""
        from cognitive_engine.cognitive_core import CognitiveCore
        core = CognitiveCore(neo4j_client=self._make_mock_client())
        stats = core.get_stats()
        self.assertIn("processing", stats)
        self.assertIn("cache", stats)
        self.assertIn("system", stats)
        self.assertIn("neo4j", stats)


# ---------------------------------------------------------------------------
# 6. OpenClawCognitiveHook 测试
# ---------------------------------------------------------------------------

class TestOpenClawCognitiveHook(unittest.TestCase):
    """测试 OpenClawCognitiveHook 桥梁功能。"""

    def test_init_fallback_mode(self):
        """测试在认知引擎不可用时的初始化。"""
        # 通过 patch 使 CognitiveCore 初始化失败
        with patch("cognitive_hook.CognitiveCore", side_effect=Exception("test")):
            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()
            self.assertIsNone(hook.cognitive_core)

    def test_fallback_processing(self):
        """测试降级处理。"""
        from cognitive_hook import OpenClawCognitiveHook

        hook = OpenClawCognitiveHook.__new__(OpenClawCognitiveHook)
        hook.cognitive_core = None
        hook.config = {
            "enabled": True,
            "mode": "cognitive_core",
            "cache_enabled": True,
            "validation_required": True,
            "reality_anchoring": True,
        }
        hook.stats = {
            "hook_calls": 0,
            "cognitive_core_calls": 0,
            "fallback_calls": 0,
            "api_calls": 0,
            "graph_writes": 0,
            "errors": 0,
        }

        result = hook.process_query_hook("测试查询")

        self.assertIn("text", result)
        self.assertIn("metadata", result)
        self.assertFalse(result["metadata"]["cognitive_hook"])
        self.assertEqual(hook.stats["fallback_calls"], 1)

    def test_should_use_cognitive_core_keywords(self):
        """测试关键词路由逻辑。"""
        from cognitive_hook import OpenClawCognitiveHook

        hook = OpenClawCognitiveHook.__new__(OpenClawCognitiveHook)
        hook.cognitive_core = MagicMock()
        hook.config = {"enabled": True, "mode": "cognitive_core"}

        # 应该使用认知内核
        self.assertTrue(hook._should_use_cognitive_core("USD兑换人民币", None))
        self.assertTrue(hook._should_use_cognitive_core("今天天气怎么样", None))
        self.assertTrue(hook._should_use_cognitive_core("当前股票价格", None))

        # 不应该使用认知内核
        self.assertFalse(hook._should_use_cognitive_core("帮助信息", None))
        self.assertFalse(hook._should_use_cognitive_core("系统状态", None))

    def test_format_for_openclaw(self):
        """测试 OpenClaw 格式转换。"""
        from cognitive_hook import OpenClawCognitiveHook

        hook = OpenClawCognitiveHook.__new__(OpenClawCognitiveHook)

        cognitive_result = {
            "query": "USD兑换人民币",
            "results": [{"rate": 7.23}],
            "formatted_text": "当前USD/CNY汇率: 7.23",
            "metadata": {"confidence": 0.9, "components_used": 1, "validations_passed": 1},
            "system_state": {"api_calls": 1, "graph_writes": 1},
        }

        result = hook._format_for_openclaw(cognitive_result, "USD兑换人民币", None)

        self.assertEqual(result["source"], "cognitive_core")
        self.assertTrue(result["metadata"]["cognitive_hook"])
        self.assertEqual(result["metadata"]["confidence"], 0.9)
        self.assertIn("system_state", result["metadata"])


# ---------------------------------------------------------------------------
# 7. 模块导入测试
# ---------------------------------------------------------------------------

class TestModuleImports(unittest.TestCase):
    """测试所有模块在新目录结构下能正确导入。"""

    def test_import_neo4j_client(self):
        """测试导入 Neo4jMemoryClient。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient
        self.assertIsNotNone(Neo4jMemoryClient)

    def test_import_memory_provider(self):
        """测试导入 CognitiveMemoryProvider。"""
        from cognitive_engine.adapters.memory_provider import CognitiveMemoryProvider
        self.assertIsNotNone(CognitiveMemoryProvider)

    def test_import_reality_writer(self):
        """测试导入 RealityGraphWriter。"""
        from cognitive_engine.adapters.reality_writer import RealityGraphWriter
        self.assertIsNotNone(RealityGraphWriter)

    def test_import_cognitive_core(self):
        """测试导入 CognitiveCore。"""
        from cognitive_engine.cognitive_core import CognitiveCore
        self.assertIsNotNone(CognitiveCore)

    def test_import_cognitive_hook(self):
        """测试导入 OpenClawCognitiveHook。"""
        from cognitive_hook import OpenClawCognitiveHook
        self.assertIsNotNone(OpenClawCognitiveHook)

    def test_import_adapters(self):
        """测试导入适配器子模块。"""
        from cognitive_engine.adapters.formatter import to_claw_format
        from cognitive_engine.adapters.query_processor import process_query
        self.assertIsNotNone(to_claw_format)
        self.assertIsNotNone(process_query)


if __name__ == "__main__":
    unittest.main()
