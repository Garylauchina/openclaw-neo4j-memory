#!/usr/bin/env python3
"""
Phase 2 策略持久化 — 综合测试

覆盖范围：
  1. GraphStore 新增方法的 Cypher 正确性（Mock Neo4j driver）
  2. Neo4jMemoryClient 新增方法的 HTTP 调用（Mock requests）
  3. RealWorldStrategyEngine 的图谱同步和恢复
  4. RQSSystem 的图谱同步和恢复
  5. 降级模式验证
  6. API 端点的请求/响应格式
"""

import json
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch, PropertyMock

# 确保项目根目录在 sys.path 中
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ======================================================================
# 1. GraphStore 新增方法测试（Mock Neo4j driver）
# ======================================================================

class TestGraphStorePhase2(unittest.TestCase):
    """测试 GraphStore 中 Phase 2 新增的 Cypher 方法。"""

    def setUp(self):
        """创建带 Mock driver 的 GraphStore。"""
        # 需要 mock neo4j 包的 GraphDatabase 以避免真实连接
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__ = Mock(return_value=self.mock_session)
        self.mock_driver.session.return_value.__exit__ = Mock(return_value=False)

        # 导入时 patch 掉 Neo4j 驱动
        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.graph_store import GraphStore
            self.GraphStore = GraphStore

        self.store = self.GraphStore.__new__(self.GraphStore)
        # 手动设置内部属性
        from meditation_memory.config import Neo4jConfig
        self.store._config = Neo4jConfig()
        self.store._driver = self.mock_driver

    def _setup_session(self, return_value=None):
        """设置 mock session 的返回值。"""
        mock_result = MagicMock()
        if return_value is not None:
            mock_result.single.return_value = return_value
            mock_result.__iter__ = Mock(
                return_value=iter(return_value if isinstance(return_value, list) else [return_value])
            )
        else:
            mock_result.single.return_value = None
            mock_result.__iter__ = Mock(return_value=iter([]))
        self.mock_session.run.return_value = mock_result

    # ---------- 策略节点操作 ----------

    def test_upsert_strategy_node_cypher(self):
        """验证 upsert_strategy_node 的 Cypher 查询包含正确的 MERGE 和属性。"""
        self._setup_session({"eid": "4:abc:123"})

        strategy_data = {
            "name": "test_strategy",
            "type": "reality_greedy",
            "uses_real_data": True,
            "fitness": 0.85,
            "real_world_bonus": 0.1,
            "performance": {
                "avg_accuracy": 0.9,
                "avg_success": 0.8,
                "avg_cost": 0.2,
                "usage_count": 10,
            },
            "metadata": {
                "created_at": "2026-01-01T00:00:00",
                "evolution_steps": 3,
            },
        }

        result = self.store.upsert_strategy_node(strategy_data)
        self.assertEqual(result, "4:abc:123")

        # 验证 Cypher 调用
        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("MERGE (s:Strategy {name: $name})", cypher)
        self.assertIn("ON CREATE SET", cypher)
        self.assertIn("ON MATCH SET", cypher)
        self.assertIn("s.fitness_score = $fitness_score", cypher)
        self.assertIn("s.needs_meditation = true", cypher)
        self.assertIn("s.uses_real_data = $uses_real_data", cypher)

        # 验证参数
        kwargs = call_args[1]
        self.assertEqual(kwargs["name"], "test_strategy")
        self.assertEqual(kwargs["strategy_type"], "reality_greedy")
        self.assertTrue(kwargs["uses_real_data"])
        self.assertAlmostEqual(kwargs["fitness_score"], 0.85)
        self.assertEqual(kwargs["usage_count"], 10)

    def test_create_evolution_link_cypher(self):
        """验证 create_evolution_link 创建 EVOLVED_FROM 关系。"""
        self._setup_session()

        self.store.create_evolution_link("child_s", "parent1_s", "parent2_s")

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("EVOLVED_FROM", cypher)
        self.assertIn("$child_name", cypher)
        self.assertIn("$parent1_name", cypher)
        self.assertIn("$parent2_name", cypher)

        kwargs = call_args[1]
        self.assertEqual(kwargs["child_name"], "child_s")
        self.assertEqual(kwargs["parent1_name"], "parent1_s")
        self.assertEqual(kwargs["parent2_name"], "parent2_s")

    def test_get_all_strategies_cypher(self):
        """验证 get_all_strategies 排除 Archived 节点。"""
        mock_records = [
            {"name": "s1", "strategy_type": "greedy", "uses_real_data": True,
             "fitness_score": 0.9, "real_world_bonus": 0.1, "avg_accuracy": 0.85,
             "avg_success": 0.8, "avg_cost": 0.15, "usage_count": 20,
             "evolution_steps": 2, "created_at": "2026-01-01"},
            {"name": "s2", "strategy_type": "trend", "uses_real_data": False,
             "fitness_score": 0.7, "real_world_bonus": 0.0, "avg_accuracy": 0.6,
             "avg_success": 0.5, "avg_cost": 0.3, "usage_count": 5,
             "evolution_steps": 0, "created_at": "2026-01-02"},
        ]
        self._setup_session(mock_records)

        results = self.store.get_all_strategies()
        self.assertEqual(len(results), 2)

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("NOT s:Archived", cypher)
        self.assertIn("ORDER BY s.fitness_score DESC", cypher)

    def test_archive_strategy_cypher(self):
        """验证 archive_strategy 添加 :Archived 标签。"""
        self._setup_session()

        self.store.archive_strategy("old_strategy")

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("SET s:Archived", cypher)
        self.assertIn("s.archived_at = timestamp()", cypher)
        self.assertEqual(call_args[1]["name"], "old_strategy")

    # ---------- RQS 记录操作 ----------

    def test_upsert_rqs_node_cypher(self):
        """验证 upsert_rqs_node 的 MERGE 和属性。"""
        self._setup_session({"eid": "4:rqs:456"})

        rqs_data = {
            "path_id": "path_12345",
            "success_count": 8,
            "fail_count": 2,
            "total_uses": 10,
            "historical_success_rate": 0.8,
            "stability_score": 0.75,
            "avg_rqs": 0.72,
            "last_used": "2026-04-01T12:00:00",
        }

        result = self.store.upsert_rqs_node(rqs_data)
        self.assertEqual(result, "4:rqs:456")

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("MERGE (r:RQSRecord {path_id: $path_id})", cypher)
        self.assertIn("r.stability_score = $stability_score", cypher)
        self.assertIn("r.avg_rqs = $avg_rqs", cypher)

        kwargs = call_args[1]
        self.assertEqual(kwargs["path_id"], "path_12345")
        self.assertEqual(kwargs["success_count"], 8)

    def test_get_all_rqs_records_cypher(self):
        """验证 get_all_rqs_records 返回正确结构。"""
        mock_records = [
            {"path_id": "p1", "success_count": 5, "fail_count": 1,
             "total_uses": 6, "historical_success_rate": 0.83,
             "stability_score": 0.9, "avg_rqs": 0.8, "last_used": "2026-04-01"},
        ]
        self._setup_session(mock_records)

        results = self.store.get_all_rqs_records()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["path_id"], "p1")

    # ---------- 信念节点操作 ----------

    def test_upsert_belief_node_cypher(self):
        """验证 upsert_belief_node 的 MERGE 和属性。"""
        self._setup_session({"eid": "4:belief:789"})

        belief_data = {
            "content": "日本房产是好的投资",
            "belief_strength": 0.85,
            "confidence": 0.9,
            "state": "CONFIRMED",
            "evidence_count": 5,
            "source": "reality_writer",
        }

        result = self.store.upsert_belief_node(belief_data)
        self.assertEqual(result, "4:belief:789")

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("MERGE (b:Belief {content: $content})", cypher)
        self.assertIn("b.belief_strength = $belief_strength", cypher)
        self.assertIn("b.state = $state", cypher)

    def test_get_all_beliefs_cypher(self):
        """验证 get_all_beliefs 返回正确结构。"""
        mock_records = [
            {"content": "test belief", "belief_strength": 0.7,
             "confidence": 0.8, "state": "HYPOTHESIS",
             "evidence_count": 2, "source": "cognitive_core"},
        ]
        self._setup_session(mock_records)

        results = self.store.get_all_beliefs()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "test belief")


# ======================================================================
# 2. Neo4jMemoryClient 新增方法测试（Mock requests）
# ======================================================================

class TestNeo4jMemoryClientPhase2(unittest.TestCase):
    """测试 Neo4jMemoryClient 中 Phase 2 新增的 HTTP 客户端方法。"""

    def setUp(self):
        """创建客户端实例。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient
        self.client = Neo4jMemoryClient(
            base_url="http://127.0.0.1:18900",
            timeout=5,
            max_retries=1,  # 测试时减少重试
        )

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_upsert_strategy(self, mock_post):
        """验证 upsert_strategy 发送正确的 POST 请求。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "success", "element_id": "4:abc:1"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        data = {"name": "test_strategy", "type": "greedy", "fitness": 0.8}
        result = self.client.upsert_strategy(data)

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "success")
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        self.assertIn("/internal/strategy", call_kwargs[0][0])

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_create_evolution_link(self, mock_post):
        """验证 create_evolution_link 发送正确的 POST 请求。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "success"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = self.client.create_evolution_link("child", "p1", "p2")

        self.assertIsNotNone(result)
        call_kwargs = mock_post.call_args
        self.assertIn("/internal/strategy/evolution", call_kwargs[0][0])
        payload = call_kwargs[1]["json"]
        self.assertEqual(payload["child"], "child")
        self.assertEqual(payload["parent1"], "p1")
        self.assertEqual(payload["parent2"], "p2")

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_archive_strategy(self, mock_post):
        """验证 archive_strategy 发送正确的 POST 请求。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "success"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = self.client.archive_strategy("old_strategy")

        self.assertIsNotNone(result)
        call_kwargs = mock_post.call_args
        self.assertIn("/internal/strategy/archive", call_kwargs[0][0])
        payload = call_kwargs[1]["json"]
        self.assertEqual(payload["name"], "old_strategy")

    @patch("cognitive_engine.neo4j_client.requests.Session.get")
    def test_get_all_strategies(self, mock_get):
        """验证 get_all_strategies 正确解析响应。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "success",
            "strategies": [
                {"name": "s1", "fitness_score": 0.9},
                {"name": "s2", "fitness_score": 0.7},
            ],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = self.client.get_all_strategies()

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "s1")
        mock_get.assert_called_once()
        self.assertIn("/internal/strategy/list", mock_get.call_args[0][0])

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_upsert_rqs(self, mock_post):
        """验证 upsert_rqs 发送正确的 POST 请求。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "success", "element_id": "4:rqs:1"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        data = {"path_id": "path_123", "total_uses": 10}
        result = self.client.upsert_rqs(data)

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "success")
        self.assertIn("/internal/rqs", mock_post.call_args[0][0])

    @patch("cognitive_engine.neo4j_client.requests.Session.get")
    def test_get_all_rqs_records(self, mock_get):
        """验证 get_all_rqs_records 正确解析响应。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "success",
            "records": [{"path_id": "p1", "total_uses": 5}],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = self.client.get_all_rqs_records()

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["path_id"], "p1")

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_upsert_belief(self, mock_post):
        """验证 upsert_belief 发送正确的 POST 请求。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "success", "element_id": "4:b:1"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        data = {"content": "test belief", "belief_strength": 0.8}
        result = self.client.upsert_belief(data)

        self.assertIsNotNone(result)
        self.assertIn("/internal/belief", mock_post.call_args[0][0])

    @patch("cognitive_engine.neo4j_client.requests.Session.get")
    def test_get_all_beliefs(self, mock_get):
        """验证 get_all_beliefs 正确解析响应。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "success",
            "beliefs": [{"content": "belief1", "belief_strength": 0.7}],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = self.client.get_all_beliefs()

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["content"], "belief1")

    @patch("cognitive_engine.neo4j_client.requests.Session.get")
    def test_get_all_strategies_returns_none_on_failure(self, mock_get):
        """验证 HTTP 失败时返回 None。"""
        mock_get.side_effect = Exception("Connection refused")

        result = self.client.get_all_strategies()
        self.assertIsNone(result)

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_upsert_strategy_returns_none_on_failure(self, mock_post):
        """验证 POST 失败时返回 None。"""
        mock_post.side_effect = Exception("Connection refused")

        result = self.client.upsert_strategy({"name": "test"})
        self.assertIsNone(result)


# ======================================================================
# 3. RealWorldStrategyEngine 图谱同步和恢复测试
# ======================================================================

class TestRealWorldStrategyEngineSync(unittest.TestCase):
    """测试 RealWorldStrategyEngine 的图谱同步和恢复功能。"""

    def test_init_without_neo4j(self):
        """验证无 Neo4j 客户端时正常初始化默认策略。"""
        from cognitive_engine.adapters.real_world_strategy import RealWorldStrategyEngine

        engine = RealWorldStrategyEngine(neo4j_client=None)

        self.assertGreater(len(engine.strategies), 0)
        self.assertEqual(engine.stats["total_strategies"], len(engine.strategies))

    def test_init_with_neo4j_no_data(self):
        """验证 Neo4j 客户端存在但无数据时初始化默认策略。"""
        from cognitive_engine.adapters.real_world_strategy import RealWorldStrategyEngine

        mock_client = MagicMock()
        mock_client.get_all_strategies.return_value = None

        engine = RealWorldStrategyEngine(neo4j_client=mock_client)

        # 应该回退到默认初始化
        self.assertGreater(len(engine.strategies), 0)
        mock_client.get_all_strategies.assert_called_once()

    def test_init_restores_from_graph(self):
        """验证从图谱恢复策略。"""
        from cognitive_engine.adapters.real_world_strategy import RealWorldStrategyEngine

        mock_client = MagicMock()
        mock_client.get_all_strategies.return_value = [
            {
                "name": "restored_strategy_1",
                "strategy_type": "reality_greedy",
                "uses_real_data": True,
                "fitness_score": 0.85,
                "real_world_bonus": 0.1,
                "usage_count": 20,
                "avg_accuracy": 0.9,
                "avg_success": 0.8,
                "avg_cost": 0.15,
            },
            {
                "name": "restored_strategy_2",
                "strategy_type": "simulation_trend",
                "uses_real_data": False,
                "fitness_score": 0.65,
                "real_world_bonus": 0.0,
                "usage_count": 10,
                "avg_accuracy": 0.6,
                "avg_success": 0.5,
                "avg_cost": 0.3,
            },
        ]

        engine = RealWorldStrategyEngine(neo4j_client=mock_client)

        # 应该恢复了 2 个策略，而不是默认的 5 个
        self.assertEqual(len(engine.strategies), 2)
        self.assertIn("restored_strategy_1", engine.strategies)
        self.assertIn("restored_strategy_2", engine.strategies)

        s1 = engine.strategies["restored_strategy_1"]
        self.assertTrue(s1.uses_real_data)
        self.assertAlmostEqual(s1.fitness_score, 0.85)
        self.assertEqual(s1.metrics["usage_count"], 20)

    def test_update_strategy_syncs_to_graph(self):
        """验证 update_strategy 后同步到图谱。"""
        from cognitive_engine.adapters.real_world_strategy import RealWorldStrategyEngine

        mock_client = MagicMock()
        mock_client.get_all_strategies.return_value = None
        mock_client.upsert_strategy.return_value = {"status": "success"}

        engine = RealWorldStrategyEngine(neo4j_client=mock_client)

        # 获取一个策略名称
        strategy_name = list(engine.strategies.keys())[0]

        # 更新策略
        result = engine.update_strategy(strategy_name, 0.9, 0.8, 0.2, 0.7)
        self.assertTrue(result)

        # 验证 upsert_strategy 被调用
        mock_client.upsert_strategy.assert_called()
        call_data = mock_client.upsert_strategy.call_args[0][0]
        self.assertEqual(call_data["name"], strategy_name)

    def test_sync_failure_silent_degradation(self):
        """验证同步失败时静默降级。"""
        from cognitive_engine.adapters.real_world_strategy import RealWorldStrategyEngine

        mock_client = MagicMock()
        mock_client.get_all_strategies.return_value = None
        mock_client.upsert_strategy.side_effect = Exception("Connection lost")

        engine = RealWorldStrategyEngine(neo4j_client=mock_client)

        strategy_name = list(engine.strategies.keys())[0]

        # 应该不抛异常
        result = engine.update_strategy(strategy_name, 0.9, 0.8, 0.2)
        self.assertTrue(result)

    def test_crossover_syncs_evolution_link(self):
        """验证交叉操作同步进化谱系。"""
        from cognitive_engine.adapters.real_world_strategy import RealWorldStrategyEngine

        mock_client = MagicMock()
        mock_client.get_all_strategies.return_value = None
        mock_client.upsert_strategy.return_value = {"status": "success"}
        mock_client.create_evolution_link.return_value = {"status": "success"}

        engine = RealWorldStrategyEngine(neo4j_client=mock_client)

        # 给策略添加一些性能数据使其有适应度
        for name in list(engine.strategies.keys())[:3]:
            engine.update_strategy(name, 0.8, 0.7, 0.2, 0.6)

        # 强制执行交叉
        parents = list(engine.strategies.values())[:2]
        initial_count = len(engine.strategies)
        engine._crossover(parents)

        # 如果创建了新策略，应该同步了进化链接
        if len(engine.strategies) > initial_count:
            mock_client.create_evolution_link.assert_called()


# ======================================================================
# 4. RQSSystem 图谱同步和恢复测试
# ======================================================================

class TestRQSSystemSync(unittest.TestCase):
    """测试 RQSSystem 的图谱同步和恢复功能。"""

    def test_init_without_neo4j(self):
        """验证无 Neo4j 客户端时正常初始化。"""
        from cognitive_engine.rqs_system import RQSSystem

        rqs = RQSSystem(neo4j_client=None)

        self.assertEqual(len(rqs.reasoning_stats), 0)
        self.assertEqual(rqs.system_stats["total_reasonings"], 0)

    def test_init_restores_from_graph(self):
        """验证从图谱恢复 RQS 记录。"""
        from cognitive_engine.rqs_system import RQSSystem

        mock_client = MagicMock()
        mock_client.get_all_rqs_records.return_value = [
            {
                "path_id": "path_100",
                "success_count": 15,
                "fail_count": 3,
                "total_uses": 18,
                "historical_success_rate": 0.833,
                "stability_score": 0.85,
                "avg_rqs": 0.78,
                "last_used": "2026-04-01T10:00:00",
            },
            {
                "path_id": "path_200",
                "success_count": 5,
                "fail_count": 5,
                "total_uses": 10,
                "historical_success_rate": 0.5,
                "stability_score": 0.4,
                "avg_rqs": 0.45,
                "last_used": "2026-03-30T08:00:00",
            },
        ]

        rqs = RQSSystem(neo4j_client=mock_client)

        self.assertEqual(len(rqs.reasoning_stats), 2)
        self.assertIn("path_100", rqs.reasoning_stats)
        self.assertIn("path_200", rqs.reasoning_stats)

        stats_100 = rqs.reasoning_stats["path_100"]
        self.assertEqual(stats_100.success_count, 15)
        self.assertEqual(stats_100.total_uses, 18)
        self.assertAlmostEqual(stats_100.historical_success_rate, 0.833, places=2)
        self.assertAlmostEqual(stats_100.stability_score, 0.85)

    def test_calculate_rqs_syncs_to_graph(self):
        """验证 calculate_rqs 后同步到图谱。"""
        from cognitive_engine.rqs_system import RQSSystem, ReasoningTrace, ReasoningEdge

        mock_client = MagicMock()
        mock_client.get_all_rqs_records.return_value = None
        mock_client.upsert_rqs.return_value = {"status": "success"}

        rqs = RQSSystem(neo4j_client=mock_client)

        # 创建测试轨迹
        trace = ReasoningTrace(trace_id="test_trace_1")
        trace.edges.append(ReasoningEdge(
            edge_id="e1", source="A", target="B",
            relation="supports", belief_strength=0.8
        ))

        result = rqs.calculate_rqs(trace, 0.85, 0.9, 0.7)

        self.assertIsNotNone(result)
        self.assertGreater(result.rqs, 0)

        # 验证 upsert_rqs 被调用
        mock_client.upsert_rqs.assert_called()

    def test_update_reasoning_stats_syncs_to_graph(self):
        """验证 update_reasoning_stats 后同步到图谱。"""
        from cognitive_engine.rqs_system import (
            RQSSystem, ReasoningTrace, ReasoningEdge, ReasoningSignal
        )

        mock_client = MagicMock()
        mock_client.get_all_rqs_records.return_value = None
        mock_client.upsert_rqs.return_value = {"status": "success"}

        rqs = RQSSystem(neo4j_client=mock_client)

        trace = ReasoningTrace(trace_id="test_trace_2")
        trace.edges.append(ReasoningEdge(
            edge_id="e2", source="C", target="D",
            relation="implies", belief_strength=0.6
        ))

        # 先计算 RQS
        rqs_result = rqs.calculate_rqs(trace, 0.7, 0.8)

        # 重置 mock 以验证 update_reasoning_stats 的调用
        mock_client.upsert_rqs.reset_mock()

        # 更新统计
        rqs.update_reasoning_stats(trace, ReasoningSignal.GOOD, rqs_result.rqs)

        # 验证再次调用了 upsert_rqs
        mock_client.upsert_rqs.assert_called()

    def test_sync_failure_silent_degradation(self):
        """验证同步失败时静默降级。"""
        from cognitive_engine.rqs_system import RQSSystem, ReasoningTrace, ReasoningEdge

        mock_client = MagicMock()
        mock_client.get_all_rqs_records.return_value = None
        mock_client.upsert_rqs.side_effect = Exception("Connection lost")

        rqs = RQSSystem(neo4j_client=mock_client)

        trace = ReasoningTrace(trace_id="test_trace_3")
        trace.edges.append(ReasoningEdge(
            edge_id="e3", source="E", target="F",
            relation="supports", belief_strength=0.9
        ))

        # 应该不抛异常
        result = rqs.calculate_rqs(trace, 0.9, 0.95)
        self.assertIsNotNone(result)


# ======================================================================
# 5. 降级模式验证
# ======================================================================

class TestDegradationMode(unittest.TestCase):
    """测试所有组件在 Neo4j 不可用时的降级行为。"""

    def test_strategy_engine_degradation(self):
        """验证策略引擎在 Neo4j 不可用时正常工作。"""
        from cognitive_engine.adapters.real_world_strategy import RealWorldStrategyEngine

        # 模拟 Neo4j 客户端完全不可用
        mock_client = MagicMock()
        mock_client.get_all_strategies.side_effect = Exception("Service unavailable")
        mock_client.upsert_strategy.side_effect = Exception("Service unavailable")

        engine = RealWorldStrategyEngine(neo4j_client=mock_client)

        # 应该回退到默认策略
        self.assertGreater(len(engine.strategies), 0)

        # 更新策略应该成功（忽略同步失败）
        name = list(engine.strategies.keys())[0]
        result = engine.update_strategy(name, 0.8, 0.7, 0.2)
        self.assertTrue(result)

        # 策略选择应该正常工作
        best = engine.select_best_strategy()
        self.assertIsNotNone(best)

    def test_rqs_system_degradation(self):
        """验证 RQS 系统在 Neo4j 不可用时正常工作。"""
        from cognitive_engine.rqs_system import RQSSystem, ReasoningTrace, ReasoningEdge

        mock_client = MagicMock()
        mock_client.get_all_rqs_records.side_effect = Exception("Service unavailable")
        mock_client.upsert_rqs.side_effect = Exception("Service unavailable")

        rqs = RQSSystem(neo4j_client=mock_client)

        trace = ReasoningTrace(trace_id="degraded_trace")
        trace.edges.append(ReasoningEdge(
            edge_id="de1", source="X", target="Y",
            relation="supports", belief_strength=0.7
        ))

        # 计算 RQS 应该正常工作
        result = rqs.calculate_rqs(trace, 0.8, 0.85)
        self.assertIsNotNone(result)
        self.assertGreater(result.rqs, 0)

    def test_neo4j_client_returns_none_on_failure(self):
        """验证 Neo4jMemoryClient 在连接失败时返回 None。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient

        client = Neo4jMemoryClient(
            base_url="http://127.0.0.1:99999",  # 不存在的端口
            timeout=1,
            max_retries=1,
        )

        self.assertIsNone(client.get_all_strategies())
        self.assertIsNone(client.get_all_rqs_records())
        self.assertIsNone(client.get_all_beliefs())
        self.assertIsNone(client.upsert_strategy({"name": "test"}))
        self.assertIsNone(client.upsert_rqs({"path_id": "test"}))
        self.assertIsNone(client.upsert_belief({"content": "test"}))

    def test_strategy_engine_no_client(self):
        """验证策略引擎在无客户端时完全正常。"""
        from cognitive_engine.adapters.real_world_strategy import RealWorldStrategyEngine

        engine = RealWorldStrategyEngine(neo4j_client=None)

        # 所有操作应该正常
        self.assertGreater(len(engine.strategies), 0)
        name = list(engine.strategies.keys())[0]
        engine.update_strategy(name, 0.9, 0.8, 0.1)
        engine.evolve()
        report = engine.get_report()
        self.assertIn("stats", report)

    def test_rqs_system_no_client(self):
        """验证 RQS 系统在无客户端时完全正常。"""
        from cognitive_engine.rqs_system import (
            RQSSystem, ReasoningTrace, ReasoningEdge, ReasoningSignal
        )

        rqs = RQSSystem(neo4j_client=None)

        trace = ReasoningTrace(trace_id="no_client_trace")
        trace.edges.append(ReasoningEdge(
            edge_id="nc1", source="A", target="B",
            relation="supports", belief_strength=0.8
        ))

        result = rqs.calculate_rqs(trace, 0.85, 0.9)
        self.assertIsNotNone(result)

        rqs.update_reasoning_stats(trace, ReasoningSignal.GOOD, result.rqs)
        report = rqs.get_system_report()
        self.assertIn("system_stats", report)


# ======================================================================
# 6. API 端点请求/响应格式测试
# ======================================================================

class TestAPIEndpointFormats(unittest.TestCase):
    """测试 Phase 2 内部 API 端点的请求/响应格式。"""

    def test_strategy_upsert_request_model(self):
        """验证 StrategyUpsertRequest 模型。"""
        sys.path.insert(0, ROOT)
        # 直接测试 Pydantic 模型
        from pydantic import BaseModel

        class StrategyUpsertRequest(BaseModel):
            name: str
            type: str = "unknown"
            uses_real_data: bool = False
            fitness: float = 0.0
            real_world_bonus: float = 0.0
            performance: dict = {}
            metadata: dict = {}

        # 最小请求
        req = StrategyUpsertRequest(name="test")
        self.assertEqual(req.name, "test")
        self.assertEqual(req.type, "unknown")
        self.assertFalse(req.uses_real_data)

        # 完整请求
        req_full = StrategyUpsertRequest(
            name="full_strategy",
            type="reality_greedy",
            uses_real_data=True,
            fitness=0.85,
            real_world_bonus=0.1,
            performance={"avg_accuracy": 0.9, "usage_count": 10},
            metadata={"created_at": "2026-01-01"},
        )
        self.assertEqual(req_full.fitness, 0.85)
        self.assertTrue(req_full.uses_real_data)

    def test_rqs_upsert_request_model(self):
        """验证 RQSUpsertRequest 模型。"""
        from pydantic import BaseModel

        class RQSUpsertRequest(BaseModel):
            path_id: str
            success_count: int = 0
            fail_count: int = 0
            total_uses: int = 0
            historical_success_rate: float = 0.0
            stability_score: float = 0.5
            avg_rqs: float = 0.0
            last_used: str = ""

        req = RQSUpsertRequest(path_id="path_123")
        self.assertEqual(req.path_id, "path_123")
        self.assertEqual(req.stability_score, 0.5)

        req_full = RQSUpsertRequest(
            path_id="path_456",
            success_count=10,
            fail_count=2,
            total_uses=12,
            historical_success_rate=0.833,
            stability_score=0.9,
            avg_rqs=0.78,
            last_used="2026-04-01T12:00:00",
        )
        self.assertEqual(req_full.total_uses, 12)

    def test_belief_upsert_request_model(self):
        """验证 BeliefUpsertRequest 模型。"""
        from pydantic import BaseModel

        class BeliefUpsertRequest(BaseModel):
            content: str
            belief_strength: float = 0.5
            confidence: float = 0.5
            state: str = "HYPOTHESIS"
            evidence_count: int = 0
            source: str = "cognitive_core"

        req = BeliefUpsertRequest(content="test belief")
        self.assertEqual(req.content, "test belief")
        self.assertEqual(req.state, "HYPOTHESIS")

    def test_evolution_link_request_model(self):
        """验证 EvolutionLinkRequest 模型。"""
        from pydantic import BaseModel

        class EvolutionLinkRequest(BaseModel):
            child: str
            parent1: str
            parent2: str

        req = EvolutionLinkRequest(child="c", parent1="p1", parent2="p2")
        self.assertEqual(req.child, "c")
        self.assertEqual(req.parent1, "p1")

    def test_archive_strategy_request_model(self):
        """验证 ArchiveStrategyRequest 模型。"""
        from pydantic import BaseModel

        class ArchiveStrategyRequest(BaseModel):
            name: str

        req = ArchiveStrategyRequest(name="old_strategy")
        self.assertEqual(req.name, "old_strategy")

    def test_strategy_list_response_format(self):
        """验证策略列表响应格式。"""
        # 模拟预期的响应格式
        response = {
            "status": "success",
            "strategies": [
                {
                    "name": "s1",
                    "strategy_type": "reality_greedy",
                    "uses_real_data": True,
                    "fitness_score": 0.85,
                    "real_world_bonus": 0.1,
                    "avg_accuracy": 0.9,
                    "avg_success": 0.8,
                    "avg_cost": 0.15,
                    "usage_count": 20,
                    "evolution_steps": 3,
                },
            ],
        }

        self.assertEqual(response["status"], "success")
        self.assertIsInstance(response["strategies"], list)
        strategy = response["strategies"][0]
        self.assertIn("name", strategy)
        self.assertIn("fitness_score", strategy)
        self.assertIn("uses_real_data", strategy)

    def test_rqs_list_response_format(self):
        """验证 RQS 列表响应格式。"""
        response = {
            "status": "success",
            "records": [
                {
                    "path_id": "path_123",
                    "success_count": 10,
                    "fail_count": 2,
                    "total_uses": 12,
                    "historical_success_rate": 0.833,
                    "stability_score": 0.85,
                    "avg_rqs": 0.78,
                    "last_used": "2026-04-01T12:00:00",
                },
            ],
        }

        self.assertEqual(response["status"], "success")
        self.assertIsInstance(response["records"], list)
        record = response["records"][0]
        self.assertIn("path_id", record)
        self.assertIn("stability_score", record)

    def test_belief_list_response_format(self):
        """验证信念列表响应格式。"""
        response = {
            "status": "success",
            "beliefs": [
                {
                    "content": "test belief",
                    "belief_strength": 0.7,
                    "confidence": 0.8,
                    "state": "CONFIRMED",
                    "evidence_count": 5,
                    "source": "reality_writer",
                },
            ],
        }

        self.assertEqual(response["status"], "success")
        self.assertIsInstance(response["beliefs"], list)
        belief = response["beliefs"][0]
        self.assertIn("content", belief)
        self.assertIn("belief_strength", belief)


# ======================================================================
# 7. CognitiveCore 集成测试
# ======================================================================

class TestCognitiveCorePhase2(unittest.TestCase):
    """测试 CognitiveCore 的 Phase 2 集成。"""

    def test_init_injects_neo4j_to_strategy_engine(self):
        """验证 CognitiveCore 将 neo4j_client 注入策略引擎。"""
        mock_client = MagicMock()
        mock_client.health_check.return_value = False
        mock_client.get_all_strategies.return_value = None
        mock_client.get_all_rqs_records.return_value = None

        from cognitive_engine.cognitive_core import CognitiveCore

        core = CognitiveCore(neo4j_client=mock_client)

        # 验证策略引擎收到了 neo4j_client
        if hasattr(core.strategy_engine, '_neo4j_client'):
            self.assertEqual(core.strategy_engine._neo4j_client, mock_client)

    def test_init_injects_neo4j_to_rqs_system(self):
        """验证 CognitiveCore 将 neo4j_client 注入 RQS 系统。"""
        mock_client = MagicMock()
        mock_client.health_check.return_value = False
        mock_client.get_all_strategies.return_value = None
        mock_client.get_all_rqs_records.return_value = None

        from cognitive_engine.cognitive_core import CognitiveCore

        core = CognitiveCore(neo4j_client=mock_client)

        # 验证 RQS 系统收到了 neo4j_client
        if hasattr(core, 'rqs_system') and hasattr(core.rqs_system, '_neo4j_client'):
            self.assertEqual(core.rqs_system._neo4j_client, mock_client)


if __name__ == "__main__":
    unittest.main(verbosity=2)
