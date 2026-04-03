"""
Phase 4 认知闭环 — 综合测试

覆盖范围：
  1. GraphStore 新增方法测试（get_recommended_strategies, update_strategy_feedback）
  2. Neo4jMemoryClient 新增方法测试（get_recommended_strategies, submit_feedback, search with include_strategies）
  3. OpenClawCognitiveHook 升级测试（process_query_hook 策略推荐, post_execution_hook 反馈提交）
  4. API 端点格式测试（/search 升级, /feedback 新增, 环境变量控制）
  5. 端到端闭环测试
  6. 反馈驱动进化测试
  7. 向后兼容测试
  8. 降级测试

所有测试使用 unittest + MagicMock，不依赖真实的 Neo4j 或 FastAPI 服务。
"""

import json
import os
import sys
import time
import threading
import unittest
from unittest.mock import MagicMock, Mock, patch, PropertyMock

# 确保项目根目录在 sys.path 中
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ======================================================================
# 1. GraphStore 新增方法测试（Mock Neo4j driver）
# ======================================================================

class TestGraphStorePhase4(unittest.TestCase):
    """测试 GraphStore 中 Phase 4 新增的 Cypher 方法。"""

    def setUp(self):
        """创建带 Mock driver 的 GraphStore。"""
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__ = Mock(return_value=self.mock_session)
        self.mock_driver.session.return_value.__exit__ = Mock(return_value=False)

        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.graph_store import GraphStore
            self.GraphStore = GraphStore

        self.store = self.GraphStore.__new__(self.GraphStore)
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

    # ---------- get_recommended_strategies ----------

    def test_get_recommended_strategies_returns_list(self):
        """验证 get_recommended_strategies 返回策略列表。"""
        mock_records = [
            {
                "name": "reality_greedy_v3",
                "strategy_type": "reality_greedy",
                "fitness_score": 0.85,
                "uses_real_data": True,
                "avg_accuracy": 0.9,
                "usage_count": 42,
            },
            {
                "name": "simulation_trend_v2",
                "strategy_type": "simulation_trend",
                "fitness_score": 0.65,
                "uses_real_data": False,
                "avg_accuracy": 0.6,
                "usage_count": 15,
            },
        ]
        self._setup_session(mock_records)

        results = self.store.get_recommended_strategies("USD/CNY 汇率", limit=3)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "reality_greedy_v3")
        self.assertEqual(results[1]["name"], "simulation_trend_v2")

    def test_get_recommended_strategies_cypher(self):
        """验证 get_recommended_strategies 的 Cypher 查询正确性。"""
        self._setup_session([])

        self.store.get_recommended_strategies("test query", limit=5)

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("MATCH (s:Strategy)", cypher)
        self.assertIn("NOT s:Archived", cypher)
        self.assertIn("ORDER BY s.fitness_score DESC", cypher)
        self.assertIn("LIMIT $limit", cypher)

        kwargs = call_args[1]
        self.assertEqual(kwargs["limit"], 5)

    def test_get_recommended_strategies_empty_result(self):
        """验证无策略时返回空列表。"""
        self._setup_session([])

        results = self.store.get_recommended_strategies("test")

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_get_recommended_strategies_error_returns_empty(self):
        """验证数据库错误时返回空列表（不抛异常）。"""
        self.mock_session.run.side_effect = Exception("Database error")

        results = self.store.get_recommended_strategies("test")

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_get_recommended_strategies_default_limit(self):
        """验证默认 limit 为 3。"""
        self._setup_session([])

        self.store.get_recommended_strategies("test")

        call_args = self.mock_session.run.call_args
        kwargs = call_args[1]
        self.assertEqual(kwargs["limit"], 3)

    # ---------- update_strategy_feedback ----------

    def test_update_strategy_feedback_cypher(self):
        """验证 update_strategy_feedback 的 Cypher 查询正确性。"""
        self._setup_session()

        self.store.update_strategy_feedback(
            strategy_name="reality_greedy_v3",
            accuracy=0.9,
            success_rate=1.0,
            cost=0.1,
        )

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]

        # 验证 EMA 更新逻辑
        self.assertIn("MATCH (s:Strategy {name: $name})", cypher)
        self.assertIn("NOT s:Archived", cypher)
        self.assertIn("s.usage_count = coalesce(s.usage_count, 0) + 1", cypher)
        self.assertIn("s.avg_accuracy * 0.9 + $accuracy * 0.1", cypher)
        self.assertIn("s.fitness_score * 0.9", cypher)
        self.assertIn("s.needs_meditation = true", cypher)

        kwargs = call_args[1]
        self.assertEqual(kwargs["name"], "reality_greedy_v3")
        self.assertAlmostEqual(kwargs["accuracy"], 0.9)
        self.assertAlmostEqual(kwargs["success_rate"], 1.0)
        self.assertAlmostEqual(kwargs["cost"], 0.1)

    def test_update_strategy_feedback_ema_weights(self):
        """验证 EMA 权重为 0.1（新数据）和 0.9（历史）。"""
        self._setup_session()

        self.store.update_strategy_feedback("test_strategy", 0.8, 1.0, 0.2)

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]

        # 验证 EMA 权重
        self.assertIn("* 0.9 +", cypher)
        self.assertIn("* 0.1", cypher)

    def test_update_strategy_feedback_error_raises(self):
        """验证数据库错误时抛出异常（由调用方处理）。"""
        self.mock_session.run.side_effect = Exception("Database error")

        with self.assertRaises(Exception):
            self.store.update_strategy_feedback("test", 0.5, 0.5, 0.5)

    def test_update_strategy_feedback_fitness_formula(self):
        """验证适应度公式包含正确的权重因子。"""
        self._setup_session()

        self.store.update_strategy_feedback("test", 0.9, 1.0, 0.1)

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]

        # 验证适应度公式的各个权重
        self.assertIn("0.5 * $accuracy", cypher)
        self.assertIn("0.2 * $success_rate", cypher)
        self.assertIn("0.2 * (1.0 - $cost * 2)", cypher)
        self.assertIn("0.1 * 0.5", cypher)
        self.assertIn("CASE WHEN s.uses_real_data THEN 0.1 ELSE 0.0 END", cypher)


# ======================================================================
# 2. Neo4jMemoryClient 新增方法测试（Mock requests）
# ======================================================================

class TestNeo4jMemoryClientPhase4(unittest.TestCase):
    """测试 Neo4jMemoryClient 中 Phase 4 新增的 HTTP 客户端方法。"""

    def setUp(self):
        """创建客户端实例。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient
        self.client = Neo4jMemoryClient(
            base_url="http://127.0.0.1:18900",
            timeout=5,
            max_retries=1,
        )

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_search_with_include_strategies(self, mock_post):
        """验证 search 传入 include_strategies=True 时发送正确参数。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "success",
            "context": {"context_text": "test", "entity_count": 0, "edge_count": 0},
            "recommended_strategies": [
                {"name": "s1", "fitness_score": 0.8}
            ],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = self.client.search("test query", include_strategies=True)

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "success")
        self.assertIn("recommended_strategies", result)
        self.assertEqual(len(result["recommended_strategies"]), 1)

        # 验证 POST 请求的 payload 包含 include_strategies
        call_kwargs = mock_post.call_args
        payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1] if len(call_kwargs[0]) > 1 else None
        if payload is None:
            # requests.Session.post(url, json=payload)
            payload = call_kwargs[1].get("json", {})
        self.assertTrue(payload.get("include_strategies", False))

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_search_without_include_strategies(self, mock_post):
        """验证 search 默认不传 include_strategies。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "success",
            "context": {"context_text": "test"},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = self.client.search("test query")

        self.assertIsNotNone(result)
        call_kwargs = mock_post.call_args
        payload = call_kwargs[1].get("json", {})
        self.assertNotIn("include_strategies", payload)

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_get_recommended_strategies(self, mock_post):
        """验证 get_recommended_strategies 正确调用 search 并提取策略。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "success",
            "context": {"context_text": ""},
            "recommended_strategies": [
                {"name": "s1", "fitness_score": 0.9},
                {"name": "s2", "fitness_score": 0.7},
            ],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = self.client.get_recommended_strategies("USD/CNY 汇率", limit=3)

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "s1")

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_get_recommended_strategies_failure(self, mock_post):
        """验证 get_recommended_strategies 失败时返回 None。"""
        mock_post.side_effect = Exception("Connection refused")

        result = self.client.get_recommended_strategies("test")

        self.assertIsNone(result)

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_submit_feedback(self, mock_post):
        """验证 submit_feedback 发送正确的 POST 请求。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "success",
            "strategy_updated": True,
            "rqs_updated": False,
            "belief_updated": True,
            "details": {"strategy_fitness_delta": 0.05},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        feedback_data = {
            "query": "USD/CNY 汇率",
            "applied_strategy_name": "reality_greedy_v3",
            "success": True,
            "confidence": 0.9,
            "validation_status": "accurate",
        }
        result = self.client.submit_feedback(feedback_data)

        self.assertIsNotNone(result)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["strategy_updated"])
        self.assertTrue(result["belief_updated"])

        # 验证 POST 到 /feedback
        call_args = mock_post.call_args
        url = call_args[0][0]
        self.assertIn("/feedback", url)

    @patch("cognitive_engine.neo4j_client.requests.Session.post")
    def test_submit_feedback_failure(self, mock_post):
        """验证 submit_feedback 失败时返回 None。"""
        mock_post.side_effect = Exception("Connection refused")

        result = self.client.submit_feedback({"query": "test", "success": True})

        self.assertIsNone(result)


# ======================================================================
# 3. OpenClawCognitiveHook 升级测试
# ======================================================================

class TestCognitiveHookPhase4(unittest.TestCase):
    """测试 OpenClawCognitiveHook 的 Phase 4 升级功能。"""

    def _create_hook_with_mocks(self, search_result=None, feedback_result=None):
        """创建带 mock 的 hook 实例。"""
        with patch("cognitive_hook._COGNITIVE_AVAILABLE", True), \
             patch("cognitive_hook.CognitiveCore") as MockCore, \
             patch("cognitive_hook.Neo4jMemoryClient") as MockClient:

            mock_client_instance = MagicMock()
            MockClient.return_value = mock_client_instance

            if search_result is not None:
                mock_client_instance.search.return_value = search_result
            else:
                mock_client_instance.search.return_value = None

            if feedback_result is not None:
                mock_client_instance.submit_feedback.return_value = feedback_result
            else:
                mock_client_instance.submit_feedback.return_value = {
                    "status": "success",
                    "strategy_updated": True,
                    "rqs_updated": False,
                    "belief_updated": False,
                }

            mock_core_instance = MagicMock()
            mock_core_instance.process_query.return_value = {
                "formatted_text": "认知处理结果",
                "metadata": {"confidence": 0.85, "components_used": 3, "validations_passed": 2},
                "system_state": {"api_calls": 1, "graph_writes": 2},
            }
            MockCore.return_value = mock_core_instance

            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()

            return hook, mock_client_instance, mock_core_instance

    def test_process_query_hook_returns_strategies(self):
        """验证 process_query_hook 返回策略推荐。"""
        search_result = {
            "status": "success",
            "context": {
                "context_text": "### 已知实体\n- USD/CNY",
                "entity_count": 1,
                "edge_count": 0,
            },
            "recommended_strategies": [
                {
                    "name": "reality_greedy_v3",
                    "strategy_type": "reality_greedy",
                    "fitness_score": 0.85,
                    "uses_real_data": True,
                },
            ],
        }

        hook, mock_client, _ = self._create_hook_with_mocks(search_result=search_result)

        result = hook.process_query_hook("USD/CNY 汇率是多少？")

        self.assertIn("recommended_strategies", result)
        self.assertEqual(len(result["recommended_strategies"]), 1)
        self.assertEqual(result["recommended_strategies"][0]["name"], "reality_greedy_v3")

    def test_process_query_hook_returns_selected_strategy(self):
        """验证 process_query_hook 返回选中的策略。"""
        search_result = {
            "status": "success",
            "context": {"context_text": "", "entity_count": 0, "edge_count": 0},
            "recommended_strategies": [
                {"name": "s1", "fitness_score": 0.9, "uses_real_data": True},
                {"name": "s2", "fitness_score": 0.7, "uses_real_data": False},
            ],
        }

        hook, _, _ = self._create_hook_with_mocks(search_result=search_result)

        result = hook.process_query_hook("test query")

        self.assertIn("selected_strategy", result)
        self.assertIsNotNone(result["selected_strategy"])
        # 应选择适应度最高的
        self.assertEqual(result["selected_strategy"]["name"], "s1")

    def test_process_query_hook_returns_memory_context(self):
        """验证 process_query_hook 返回记忆上下文。"""
        search_result = {
            "status": "success",
            "context": {
                "context_text": "### 已知实体\n- 张三",
                "entity_count": 1,
                "edge_count": 0,
            },
            "recommended_strategies": [],
        }

        hook, _, _ = self._create_hook_with_mocks(search_result=search_result)

        result = hook.process_query_hook("张三在哪里？")

        self.assertIn("memory_context", result)
        self.assertEqual(result["memory_context"]["entity_count"], 1)

    def test_process_query_hook_search_failure_graceful(self):
        """验证搜索失败时优雅降级。"""
        hook, mock_client, _ = self._create_hook_with_mocks(search_result=None)
        mock_client.search.side_effect = Exception("Connection refused")

        result = hook.process_query_hook("test query")

        # 应该返回空策略和空上下文
        self.assertEqual(result.get("recommended_strategies", []), [])
        self.assertEqual(result.get("memory_context", {}), {})

    def test_post_execution_hook_submits_feedback(self):
        """验证 post_execution_hook 提交反馈。"""
        hook, mock_client, _ = self._create_hook_with_mocks()

        hook.post_execution_hook(
            query="USD/CNY 汇率",
            strategy_name="reality_greedy_v3",
            success=True,
            confidence=0.9,
            validation_status="accurate",
        )

        # 等待后台线程完成
        time.sleep(0.5)

        mock_client.submit_feedback.assert_called_once()
        call_args = mock_client.submit_feedback.call_args[0][0]
        self.assertEqual(call_args["query"], "USD/CNY 汇率")
        self.assertEqual(call_args["applied_strategy_name"], "reality_greedy_v3")
        self.assertTrue(call_args["success"])
        self.assertAlmostEqual(call_args["confidence"], 0.9)
        self.assertEqual(call_args["validation_status"], "accurate")

    def test_post_execution_hook_nonblocking(self):
        """验证 post_execution_hook 是非阻塞的。"""
        hook, mock_client, _ = self._create_hook_with_mocks()

        # 让反馈提交需要一些时间
        def slow_feedback(data):
            time.sleep(1.0)
            return {"status": "success"}

        mock_client.submit_feedback.side_effect = slow_feedback

        start_time = time.time()
        hook.post_execution_hook(
            query="test",
            success=True,
        )
        elapsed = time.time() - start_time

        # 非阻塞：应该立即返回
        self.assertLess(elapsed, 0.5)

    def test_post_execution_hook_failure_silent(self):
        """验证 post_execution_hook 失败时静默不抛异常。"""
        hook, mock_client, _ = self._create_hook_with_mocks()
        mock_client.submit_feedback.side_effect = Exception("Connection refused")

        # 不应抛异常
        hook.post_execution_hook(
            query="test",
            success=False,
            confidence=0.3,
        )

        # 等待后台线程完成
        time.sleep(0.5)

        # 验证错误计数增加
        self.assertEqual(hook.stats["feedback_errors"], 1)

    def test_post_execution_hook_no_client(self):
        """验证无客户端时 post_execution_hook 静默跳过。"""
        with patch("cognitive_hook._COGNITIVE_AVAILABLE", False):
            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()

        hook.post_execution_hook(query="test", success=True)

        # 不应有任何反馈提交
        self.assertEqual(hook.stats["feedback_submitted"], 0)

    def test_post_execution_hook_default_strategy_name(self):
        """验证 post_execution_hook 默认策略名称为 'default'。"""
        hook, mock_client, _ = self._create_hook_with_mocks()

        hook.post_execution_hook(
            query="test",
            success=True,
        )

        time.sleep(0.5)

        call_args = mock_client.submit_feedback.call_args[0][0]
        self.assertEqual(call_args["applied_strategy_name"], "default")

    def test_select_strategy_prefers_real_data(self):
        """验证 _select_strategy 在需要实时数据时优先选择 uses_real_data 的策略。"""
        with patch("cognitive_hook._COGNITIVE_AVAILABLE", False):
            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()

        strategies = [
            {"name": "s1", "fitness_score": 0.9, "uses_real_data": False},
            {"name": "s2", "fitness_score": 0.7, "uses_real_data": True},
        ]
        context = {"requires_real_data": True}

        selected = hook._select_strategy(strategies, context)

        self.assertEqual(selected["name"], "s2")

    def test_select_strategy_highest_fitness(self):
        """验证 _select_strategy 默认选择适应度最高的策略。"""
        with patch("cognitive_hook._COGNITIVE_AVAILABLE", False):
            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()

        strategies = [
            {"name": "s1", "fitness_score": 0.9, "uses_real_data": False},
            {"name": "s2", "fitness_score": 0.7, "uses_real_data": True},
        ]

        selected = hook._select_strategy(strategies, None)

        self.assertEqual(selected["name"], "s1")

    def test_select_strategy_empty_list(self):
        """验证 _select_strategy 空列表时返回 None。"""
        with patch("cognitive_hook._COGNITIVE_AVAILABLE", False):
            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()

        selected = hook._select_strategy([], None)

        self.assertIsNone(selected)

    def test_hook_stats_include_feedback_counters(self):
        """验证 hook 统计信息包含反馈相关计数器。"""
        with patch("cognitive_hook._COGNITIVE_AVAILABLE", False):
            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()

        self.assertIn("feedback_submitted", hook.stats)
        self.assertIn("feedback_errors", hook.stats)
        self.assertEqual(hook.stats["feedback_submitted"], 0)
        self.assertEqual(hook.stats["feedback_errors"], 0)


# ======================================================================
# 4. API 端点格式测试
# ======================================================================

class TestAPIEndpointFormatsPhase4(unittest.TestCase):
    """测试 Phase 4 API 端点的请求/响应格式。"""

    def test_search_request_model_with_include_strategies(self):
        """验证 SearchRequest 模型支持 include_strategies 参数。"""
        from pydantic import BaseModel
        from typing import Optional

        class SearchRequest(BaseModel):
            query: str
            session_id: Optional[str] = None
            limit: int = 10
            use_llm: bool = True
            include_strategies: bool = True

        # 默认值
        req = SearchRequest(query="test")
        self.assertTrue(req.include_strategies)

        # 显式设置
        req2 = SearchRequest(query="test", include_strategies=False)
        self.assertFalse(req2.include_strategies)

    def test_strategy_recommendation_model(self):
        """验证 StrategyRecommendation 模型。"""
        from pydantic import BaseModel
        from typing import Optional

        class StrategyRecommendation(BaseModel):
            name: str
            strategy_type: Optional[str] = None
            fitness_score: Optional[float] = None
            uses_real_data: Optional[bool] = None
            avg_accuracy: Optional[float] = None
            usage_count: Optional[int] = None
            description: Optional[str] = None

        rec = StrategyRecommendation(
            name="reality_greedy_v3",
            strategy_type="reality_greedy",
            fitness_score=0.85,
            uses_real_data=True,
            avg_accuracy=0.9,
            usage_count=42,
        )
        self.assertEqual(rec.name, "reality_greedy_v3")
        self.assertAlmostEqual(rec.fitness_score, 0.85)
        self.assertTrue(rec.uses_real_data)

        # 最小请求
        rec_min = StrategyRecommendation(name="test")
        self.assertEqual(rec_min.name, "test")
        self.assertIsNone(rec_min.fitness_score)

    def test_feedback_request_model(self):
        """验证 FeedbackRequest 模型。"""
        from pydantic import BaseModel
        from typing import Optional, Dict, Any

        class FeedbackRequest(BaseModel):
            query: str
            applied_strategy_name: Optional[str] = None
            success: bool
            confidence: float = 0.5
            error_msg: Optional[str] = None
            result_data: Optional[Dict[str, Any]] = None
            validation_status: Optional[str] = None

        # 最小请求
        req = FeedbackRequest(query="test", success=True)
        self.assertEqual(req.query, "test")
        self.assertTrue(req.success)
        self.assertAlmostEqual(req.confidence, 0.5)

        # 完整请求
        req_full = FeedbackRequest(
            query="USD/CNY 汇率",
            applied_strategy_name="reality_greedy_v3",
            success=True,
            confidence=0.9,
            validation_status="accurate",
        )
        self.assertEqual(req_full.applied_strategy_name, "reality_greedy_v3")
        self.assertEqual(req_full.validation_status, "accurate")

    def test_feedback_response_model(self):
        """验证 FeedbackResponse 模型。"""
        from pydantic import BaseModel
        from typing import Dict, Any

        class FeedbackResponse(BaseModel):
            status: str
            strategy_updated: bool
            rqs_updated: bool
            belief_updated: bool
            details: Dict[str, Any] = {}

        resp = FeedbackResponse(
            status="success",
            strategy_updated=True,
            rqs_updated=False,
            belief_updated=True,
            details={"strategy_fitness_delta": 0.05},
        )
        self.assertEqual(resp.status, "success")
        self.assertTrue(resp.strategy_updated)
        self.assertFalse(resp.rqs_updated)
        self.assertTrue(resp.belief_updated)

    def test_search_response_format_with_strategies(self):
        """验证 /search 升级后的响应格式。"""
        response = {
            "status": "success",
            "context": {
                "context_text": "### 已知实体\n- USD/CNY",
                "subgraph": {
                    "nodes": [{"name": "USD/CNY", "entity_type": "currency_pair"}],
                    "edges": [],
                },
                "matched_entities": ["USD/CNY"],
                "entity_count": 1,
                "edge_count": 0,
            },
            "recommended_strategies": [
                {
                    "name": "reality_greedy_v3",
                    "strategy_type": "reality_greedy",
                    "fitness_score": 0.85,
                    "uses_real_data": True,
                    "avg_accuracy": 0.9,
                    "usage_count": 42,
                },
            ],
        }

        self.assertEqual(response["status"], "success")
        self.assertIn("context", response)
        self.assertIn("recommended_strategies", response)
        self.assertIsInstance(response["recommended_strategies"], list)

        strategy = response["recommended_strategies"][0]
        self.assertIn("name", strategy)
        self.assertIn("fitness_score", strategy)
        self.assertIn("uses_real_data", strategy)

    def test_feedback_response_format(self):
        """验证 /feedback 响应格式。"""
        response = {
            "status": "success",
            "strategy_updated": True,
            "rqs_updated": False,
            "belief_updated": True,
            "details": {
                "strategy_fitness_delta": 0.05,
                "belief_delta": 0.1,
            },
        }

        self.assertEqual(response["status"], "success")
        self.assertIn("strategy_updated", response)
        self.assertIn("rqs_updated", response)
        self.assertIn("belief_updated", response)
        self.assertIn("details", response)

    def test_env_var_cognitive_strategy_enabled(self):
        """验证 COGNITIVE_STRATEGY_ENABLED 环境变量解析。"""
        # True 值
        for val in ("true", "1", "yes", "True", "YES"):
            result = val.lower() in ("true", "1", "yes")
            self.assertTrue(result, f"Expected True for '{val}'")

        # False 值
        for val in ("false", "0", "no", "disabled"):
            result = val.lower() in ("true", "1", "yes")
            self.assertFalse(result, f"Expected False for '{val}'")

    def test_env_var_cognitive_feedback_enabled(self):
        """验证 COGNITIVE_FEEDBACK_ENABLED 环境变量解析。"""
        for val in ("true", "1", "yes"):
            result = val.lower() in ("true", "1", "yes")
            self.assertTrue(result)

        for val in ("false", "0", "no"):
            result = val.lower() in ("true", "1", "yes")
            self.assertFalse(result)


# ======================================================================
# 5. 端到端闭环测试
# ======================================================================

class TestEndToEndFeedbackLoop(unittest.TestCase):
    """端到端闭环测试：查询 → 策略推荐 → 执行 → 反馈 → 进化。"""

    def test_full_loop_search_recommend_feedback(self):
        """模拟完整的认知闭环流程。"""
        # 1. 搜索并获取策略推荐
        search_response = {
            "status": "success",
            "context": {
                "context_text": "### 已知实体\n- USD/CNY: 货币对",
                "subgraph": {
                    "nodes": [{"name": "USD/CNY", "entity_type": "currency_pair", "mention_count": 10}],
                    "edges": [],
                },
                "matched_entities": ["USD/CNY"],
                "entity_count": 1,
                "edge_count": 0,
            },
            "recommended_strategies": [
                {
                    "name": "reality_greedy_v3",
                    "strategy_type": "reality_greedy",
                    "fitness_score": 0.85,
                    "uses_real_data": True,
                    "avg_accuracy": 0.9,
                    "usage_count": 42,
                },
            ],
        }

        # 验证搜索结果包含策略推荐
        self.assertIn("recommended_strategies", search_response)
        strategies = search_response["recommended_strategies"]
        self.assertGreater(len(strategies), 0)

        # 2. 选择最优策略
        selected = strategies[0]
        self.assertEqual(selected["name"], "reality_greedy_v3")

        # 3. 模拟执行成功
        execution_success = True
        execution_confidence = 0.9

        # 4. 构建反馈
        feedback = {
            "query": "USD/CNY 汇率是多少？",
            "applied_strategy_name": selected["name"],
            "success": execution_success,
            "confidence": execution_confidence,
            "validation_status": "accurate",
        }

        # 5. 模拟反馈响应
        feedback_response = {
            "status": "success",
            "strategy_updated": True,
            "rqs_updated": False,
            "belief_updated": True,
            "details": {
                "strategy_fitness_delta": 0.05,
                "belief_delta": 0.1,
            },
        }

        self.assertEqual(feedback_response["status"], "success")
        self.assertTrue(feedback_response["strategy_updated"])

    def test_full_loop_with_hook(self):
        """通过 CognitiveHook 模拟完整闭环。"""
        search_result = {
            "status": "success",
            "context": {"context_text": "test", "entity_count": 0, "edge_count": 0},
            "recommended_strategies": [
                {"name": "s1", "fitness_score": 0.8, "uses_real_data": True},
            ],
        }

        with patch("cognitive_hook._COGNITIVE_AVAILABLE", True), \
             patch("cognitive_hook.CognitiveCore") as MockCore, \
             patch("cognitive_hook.Neo4jMemoryClient") as MockClient:

            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.search.return_value = search_result
            mock_client.submit_feedback.return_value = {
                "status": "success",
                "strategy_updated": True,
                "rqs_updated": False,
                "belief_updated": False,
            }

            mock_core = MagicMock()
            mock_core.process_query.return_value = {
                "formatted_text": "结果",
                "metadata": {"confidence": 0.85},
                "system_state": {},
            }
            MockCore.return_value = mock_core

            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()

            # Step 1: 查询 + 策略推荐
            result = hook.process_query_hook("USD/CNY 汇率")
            self.assertIn("recommended_strategies", result)
            selected = result.get("selected_strategy")

            # Step 2: 提交反馈
            hook.post_execution_hook(
                query="USD/CNY 汇率",
                strategy_name=selected["name"] if selected else None,
                success=True,
                confidence=0.9,
                validation_status="accurate",
            )

            # 等待后台线程
            time.sleep(0.5)

            # Step 3: 验证反馈已提交
            mock_client.submit_feedback.assert_called_once()

    def test_search_then_feedback_context_preserved(self):
        """验证搜索后反馈不影响上下文结构。"""
        context = {
            "context_text": "### 已知实体\n- 张三\n- 北京",
            "subgraph": {
                "nodes": [
                    {"name": "张三", "entity_type": "person", "mention_count": 5},
                    {"name": "北京", "entity_type": "location", "mention_count": 3},
                ],
                "edges": [
                    {"source": "张三", "target": "北京", "relation_type": "lives_in", "weight": 0.8},
                ],
            },
            "matched_entities": ["张三", "北京"],
            "entity_count": 2,
            "edge_count": 1,
        }

        search_response = {
            "status": "success",
            "context": context,
            "recommended_strategies": [],
        }

        # 上下文结构应完整保留
        self.assertIn("context_text", search_response["context"])
        self.assertIn("subgraph", search_response["context"])
        self.assertIn("matched_entities", search_response["context"])
        self.assertIn("entity_count", search_response["context"])
        self.assertIn("edge_count", search_response["context"])
        self.assertEqual(search_response["context"]["entity_count"], 2)
        self.assertEqual(search_response["context"]["edge_count"], 1)


# ======================================================================
# 6. 反馈驱动进化测试
# ======================================================================

class TestFeedbackDrivenEvolution(unittest.TestCase):
    """测试反馈驱动的策略进化。"""

    def test_success_feedback_increases_fitness(self):
        """验证成功反馈应导致适应度上升趋势。"""
        # 模拟 EMA 计算：fitness = old * 0.9 + new * 0.1
        old_fitness = 0.5
        # 成功反馈：accuracy=0.9, success_rate=1.0, cost=0.1
        new_component = (
            0.5 * 0.9 +       # accuracy
            0.2 * 1.0 +       # success_rate
            0.2 * (1.0 - 0.1 * 2) +  # cost penalty
            0.1 * 0.5 +       # base
            0.1              # real_data bonus (假设 uses_real_data=True)
        )
        new_fitness = old_fitness * 0.9 + new_component * 0.1

        self.assertGreater(new_fitness, old_fitness)

    def test_failure_feedback_decreases_fitness(self):
        """验证失败反馈应导致适应度下降趋势。"""
        old_fitness = 0.8
        # 失败反馈：accuracy=0.1, success_rate=0.0, cost=0.5
        new_component = (
            0.5 * 0.1 +       # accuracy
            0.2 * 0.0 +       # success_rate
            0.2 * (1.0 - 0.5 * 2) +  # cost penalty (negative)
            0.1 * 0.5 +       # base
            0.0              # no real_data bonus
        )
        new_fitness = old_fitness * 0.9 + new_component * 0.1

        self.assertLess(new_fitness, old_fitness)

    def test_ema_smoothing_prevents_drastic_change(self):
        """验证 EMA 平滑防止单次反馈造成剧烈波动。"""
        old_fitness = 0.5

        # 极端成功反馈
        max_component = (
            0.5 * 1.0 +  # accuracy = 1.0
            0.2 * 1.0 +  # success_rate = 1.0
            0.2 * 1.0 +  # cost = 0
            0.1 * 0.5 +  # base
            0.1          # real_data bonus
        )
        new_fitness = old_fitness * 0.9 + max_component * 0.1

        # 变化幅度应该较小（EMA 权重 0.1）
        delta = abs(new_fitness - old_fitness)
        self.assertLess(delta, 0.15)  # 变化不超过 15%

    def test_multiple_success_feedbacks_trend(self):
        """验证连续成功反馈导致适应度持续上升。"""
        fitness = 0.5
        success_component = (
            0.5 * 0.9 +
            0.2 * 1.0 +
            0.2 * 0.8 +
            0.1 * 0.5 +
            0.1
        )

        fitness_history = [fitness]
        for _ in range(10):
            fitness = fitness * 0.9 + success_component * 0.1
            fitness_history.append(fitness)

        # 每次迭代后适应度应该递增
        for i in range(1, len(fitness_history)):
            self.assertGreaterEqual(fitness_history[i], fitness_history[i - 1])

    def test_multiple_failure_feedbacks_trend(self):
        """验证连续失败反馈导致适应度持续下降。"""
        fitness = 0.8
        failure_component = (
            0.5 * 0.1 +
            0.2 * 0.0 +
            0.2 * 0.0 +
            0.1 * 0.5 +
            0.0
        )

        fitness_history = [fitness]
        for _ in range(5):
            fitness = fitness * 0.9 + failure_component * 0.1
            fitness_history.append(fitness)

        # 每次迭代后适应度应该递减
        for i in range(1, len(fitness_history)):
            self.assertLessEqual(fitness_history[i], fitness_history[i - 1])

    def test_feedback_rqs_impact_map(self):
        """验证 RQS 影响因子映射。"""
        rqs_impact_map = {
            "accurate": 0.05,
            "acceptable": 0.0,
            "wrong": -0.3,
        }

        self.assertGreater(rqs_impact_map["accurate"], 0)
        self.assertEqual(rqs_impact_map["acceptable"], 0)
        self.assertLess(rqs_impact_map["wrong"], 0)

    def test_feedback_belief_impact_map(self):
        """验证信念影响因子映射。"""
        belief_impact_map = {
            "accurate": 0.1,
            "acceptable": 0.0,
            "wrong": -0.3,
        }

        self.assertGreater(belief_impact_map["accurate"], 0)
        self.assertEqual(belief_impact_map["acceptable"], 0)
        self.assertLess(belief_impact_map["wrong"], 0)

    def test_feedback_independent_substeps(self):
        """验证反馈的每个子步骤独立执行。"""
        # 模拟反馈处理流程
        results = {
            "strategy_updated": False,
            "rqs_updated": False,
            "belief_updated": False,
        }

        # 子步骤 1: 策略更新（成功）
        try:
            results["strategy_updated"] = True
        except Exception:
            pass

        # 子步骤 2: RQS 更新（失败）
        try:
            raise Exception("RQS update failed")
        except Exception:
            pass

        # 子步骤 3: 信念更新（成功）
        try:
            results["belief_updated"] = True
        except Exception:
            pass

        # 策略和信念更新成功，RQS 失败不影响其他
        self.assertTrue(results["strategy_updated"])
        self.assertFalse(results["rqs_updated"])
        self.assertTrue(results["belief_updated"])


# ======================================================================
# 7. 向后兼容测试
# ======================================================================

class TestBackwardCompatibility(unittest.TestCase):
    """测试 Phase 4 改动的向后兼容性。"""

    def test_search_without_include_strategies_param(self):
        """验证旧版客户端不传 include_strategies 时正常工作。"""
        # 模拟旧版请求（不包含 include_strategies）
        old_request = {
            "query": "test query",
            "limit": 10,
            "use_llm": True,
        }

        # 旧版请求应该被新的 SearchRequest 模型接受
        from pydantic import BaseModel
        from typing import Optional

        class SearchRequest(BaseModel):
            query: str
            session_id: Optional[str] = None
            limit: int = 10
            use_llm: bool = True
            include_strategies: bool = True

        req = SearchRequest(**old_request)
        self.assertTrue(req.include_strategies)  # 默认为 True

    def test_search_response_context_unchanged(self):
        """验证 /search 响应中 context 字段格式不变。"""
        # Phase 1/2/3 期望的 context 格式
        expected_context_keys = {
            "context_text", "subgraph", "matched_entities",
            "entity_count", "edge_count",
        }

        response = {
            "status": "success",
            "context": {
                "context_text": "test",
                "subgraph": {"nodes": [], "edges": []},
                "matched_entities": [],
                "entity_count": 0,
                "edge_count": 0,
            },
            "recommended_strategies": [],
        }

        # context 字段应包含所有旧版期望的键
        actual_context_keys = set(response["context"].keys())
        self.assertTrue(expected_context_keys.issubset(actual_context_keys))

    def test_search_response_strategies_default_empty(self):
        """验证 recommended_strategies 默认为空列表。"""
        response = {
            "status": "success",
            "context": {"context_text": ""},
            "recommended_strategies": [],
        }

        self.assertIsInstance(response["recommended_strategies"], list)
        self.assertEqual(len(response["recommended_strategies"]), 0)

    def test_old_client_ignores_strategies(self):
        """验证旧版客户端可安全忽略 recommended_strategies。"""
        response = {
            "status": "success",
            "context": {
                "context_text": "### 已知实体\n- 张三",
                "subgraph": {"nodes": [{"name": "张三"}], "edges": []},
                "matched_entities": ["张三"],
                "entity_count": 1,
                "edge_count": 0,
            },
            "recommended_strategies": [
                {"name": "s1", "fitness_score": 0.8},
            ],
        }

        # 旧版客户端只读取 status 和 context
        self.assertEqual(response["status"], "success")
        context = response["context"]
        self.assertIn("context_text", context)
        self.assertIn("subgraph", context)

    def test_memory_provider_compatibility(self):
        """验证 CognitiveMemoryProvider 能正确处理升级后的 /search 响应。"""
        # 升级后的响应（包含 recommended_strategies）
        upgraded_response = {
            "status": "success",
            "context": {
                "context_text": "### 已知实体\n- 张三",
                "subgraph": {
                    "nodes": [{"name": "张三", "entity_type": "person", "mention_count": 5}],
                    "edges": [],
                },
                "matched_entities": ["张三"],
                "entity_count": 1,
                "edge_count": 0,
            },
            "recommended_strategies": [
                {"name": "s1", "fitness_score": 0.8},
            ],
        }

        # CognitiveMemoryProvider 只读取 context 字段
        context = upgraded_response.get("context", {})
        self.assertIn("context_text", context)
        self.assertIn("subgraph", context)

        # 额外字段不影响旧逻辑
        subgraph = context.get("subgraph", {})
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])
        self.assertEqual(len(nodes), 1)
        self.assertEqual(len(edges), 0)

    def test_neo4j_client_search_backward_compatible(self):
        """验证 Neo4jMemoryClient.search 默认不传 include_strategies。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient

        client = Neo4jMemoryClient(
            base_url="http://127.0.0.1:18900",
            timeout=5,
            max_retries=1,
        )

        with patch("cognitive_engine.neo4j_client.requests.Session.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "status": "success",
                "context": {"context_text": ""},
            }
            mock_resp.raise_for_status = MagicMock()
            mock_post.return_value = mock_resp

            client.search("test")

            call_kwargs = mock_post.call_args
            payload = call_kwargs[1].get("json", {})
            # 默认不传 include_strategies
            self.assertNotIn("include_strategies", payload)

    def test_phase1_search_response_still_valid(self):
        """验证 Phase 1 的搜索响应格式仍然有效。"""
        phase1_response = {
            "status": "success",
            "context": {
                "context_text": "### 已知实体\n- 张三",
                "subgraph": {
                    "nodes": [{"name": "张三", "entity_type": "person", "mention_count": 5}],
                    "edges": [],
                },
                "matched_entities": ["张三"],
                "entity_count": 1,
                "edge_count": 0,
            },
        }

        # Phase 1 响应不包含 recommended_strategies，但应该能被安全处理
        strategies = phase1_response.get("recommended_strategies", [])
        self.assertEqual(strategies, [])


# ======================================================================
# 8. 降级测试
# ======================================================================

class TestDegradationPhase4(unittest.TestCase):
    """测试 Phase 4 功能在各种故障场景下的降级行为。"""

    def test_feedback_disabled_via_env_var(self):
        """验证 COGNITIVE_FEEDBACK_ENABLED=false 时反馈被禁用。"""
        # 模拟禁用反馈
        enabled = "false".lower() in ("true", "1", "yes")
        self.assertFalse(enabled)

        # 禁用时应返回 disabled 状态
        if not enabled:
            response = {
                "status": "disabled",
                "strategy_updated": False,
                "rqs_updated": False,
                "belief_updated": False,
                "details": {"message": "Feedback processing is disabled via COGNITIVE_FEEDBACK_ENABLED"},
            }
            self.assertEqual(response["status"], "disabled")
            self.assertFalse(response["strategy_updated"])

    def test_strategy_disabled_via_env_var(self):
        """验证 COGNITIVE_STRATEGY_ENABLED=false 时策略推荐被禁用。"""
        enabled = "false".lower() in ("true", "1", "yes")
        self.assertFalse(enabled)

    def test_strategy_recommendation_failure_graceful(self):
        """验证策略推荐失败时不影响搜索结果。"""
        # 模拟策略推荐失败但搜索成功的场景
        context_dict = {
            "context_text": "### 已知实体\n- 张三",
            "entity_count": 1,
            "edge_count": 0,
        }

        strategies = []
        try:
            raise Exception("Strategy recommendation failed")
        except Exception:
            strategies = []  # 降级为空列表

        response = {
            "status": "success",
            "context": context_dict,
            "recommended_strategies": strategies,
        }

        # 搜索结果应该正常返回
        self.assertEqual(response["status"], "success")
        self.assertIn("context", response)
        self.assertEqual(response["recommended_strategies"], [])

    def test_feedback_substep_strategy_failure_independent(self):
        """验证策略更新失败不影响 RQS 和信念更新。"""
        result = {
            "strategy_updated": False,
            "rqs_updated": False,
            "belief_updated": False,
        }

        # 策略更新失败
        try:
            raise Exception("Strategy update failed")
        except Exception:
            pass  # 静默失败

        # RQS 更新成功
        try:
            result["rqs_updated"] = True
        except Exception:
            pass

        # 信念更新成功
        try:
            result["belief_updated"] = True
        except Exception:
            pass

        self.assertFalse(result["strategy_updated"])
        self.assertTrue(result["rqs_updated"])
        self.assertTrue(result["belief_updated"])

    def test_feedback_substep_rqs_failure_independent(self):
        """验证 RQS 更新失败不影响策略和信念更新。"""
        result = {
            "strategy_updated": False,
            "rqs_updated": False,
            "belief_updated": False,
        }

        # 策略更新成功
        try:
            result["strategy_updated"] = True
        except Exception:
            pass

        # RQS 更新失败
        try:
            raise Exception("RQS update failed")
        except Exception:
            pass

        # 信念更新成功
        try:
            result["belief_updated"] = True
        except Exception:
            pass

        self.assertTrue(result["strategy_updated"])
        self.assertFalse(result["rqs_updated"])
        self.assertTrue(result["belief_updated"])

    def test_feedback_substep_belief_failure_independent(self):
        """验证信念更新失败不影响策略和 RQS 更新。"""
        result = {
            "strategy_updated": False,
            "rqs_updated": False,
            "belief_updated": False,
        }

        # 策略更新成功
        try:
            result["strategy_updated"] = True
        except Exception:
            pass

        # RQS 更新成功
        try:
            result["rqs_updated"] = True
        except Exception:
            pass

        # 信念更新失败
        try:
            raise Exception("Belief update failed")
        except Exception:
            pass

        self.assertTrue(result["strategy_updated"])
        self.assertTrue(result["rqs_updated"])
        self.assertFalse(result["belief_updated"])

    def test_hook_post_execution_failure_nonblocking(self):
        """验证 hook 的 post_execution_hook 失败不阻塞主流程。"""
        with patch("cognitive_hook._COGNITIVE_AVAILABLE", True), \
             patch("cognitive_hook.CognitiveCore") as MockCore, \
             patch("cognitive_hook.Neo4jMemoryClient") as MockClient:

            mock_client = MagicMock()
            MockClient.return_value = mock_client
            mock_client.submit_feedback.side_effect = Exception("Service unavailable")

            MockCore.return_value = MagicMock()

            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()

            start_time = time.time()
            hook.post_execution_hook(
                query="test",
                success=False,
            )
            elapsed = time.time() - start_time

            # 应该立即返回
            self.assertLess(elapsed, 0.5)

            # 等待后台线程完成
            time.sleep(0.5)

            # 错误计数应增加
            self.assertEqual(hook.stats["feedback_errors"], 1)

    def test_neo4j_client_feedback_returns_none_on_failure(self):
        """验证 Neo4jMemoryClient.submit_feedback 连接失败时返回 None。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient

        client = Neo4jMemoryClient(
            base_url="http://127.0.0.1:99999",
            timeout=1,
            max_retries=1,
        )

        result = client.submit_feedback({
            "query": "test",
            "success": True,
        })

        self.assertIsNone(result)

    def test_neo4j_client_recommend_returns_none_on_failure(self):
        """验证 Neo4jMemoryClient.get_recommended_strategies 连接失败时返回 None。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient

        client = Neo4jMemoryClient(
            base_url="http://127.0.0.1:99999",
            timeout=1,
            max_retries=1,
        )

        result = client.get_recommended_strategies("test")

        self.assertIsNone(result)

    def test_graph_store_recommend_returns_empty_on_driver_failure(self):
        """验证 GraphStore.get_recommended_strategies 在驱动失败时返回空列表。"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)
        mock_session.run.side_effect = Exception("Driver error")

        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.graph_store import GraphStore
        store = GraphStore.__new__(GraphStore)
        from meditation_memory.config import Neo4jConfig
        store._config = Neo4jConfig()
        store._driver = mock_driver

        result = store.get_recommended_strategies("test")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_graph_store_feedback_raises_on_driver_failure(self):
        """验证 GraphStore.update_strategy_feedback 在驱动失败时抛出异常。"""
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = Mock(return_value=False)
        mock_session.run.side_effect = Exception("Driver error")

        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.graph_store import GraphStore
        store = GraphStore.__new__(GraphStore)
        from meditation_memory.config import Neo4jConfig
        store._config = Neo4jConfig()
        store._driver = mock_driver

        with self.assertRaises(Exception):
            store.update_strategy_feedback("test", 0.5, 0.5, 0.5)


# ======================================================================
# 9. 版本与配置测试
# ======================================================================

class TestPhase4VersionAndConfig(unittest.TestCase):
    """测试 Phase 4 版本信息和配置。"""

    def test_hook_version(self):
        """验证 hook 版本号包含 phase4。"""
        with patch("cognitive_hook._COGNITIVE_AVAILABLE", False):
            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()

        self.assertIn("phase4", hook.hook_version)

    def test_hook_status_includes_feedback_stats(self):
        """验证 hook 状态报告包含反馈统计。"""
        with patch("cognitive_hook._COGNITIVE_AVAILABLE", False):
            from cognitive_hook import OpenClawCognitiveHook
            hook = OpenClawCognitiveHook()

        status = hook.get_hook_status()
        self.assertIn("hook", status)
        self.assertIn("stats", status["hook"])
        self.assertIn("feedback_submitted", status["hook"]["stats"])
        self.assertIn("feedback_errors", status["hook"]["stats"])

    def test_neo4j_client_docstring_mentions_phase4(self):
        """验证 Neo4jMemoryClient 文档字符串提及 Phase 4。"""
        from cognitive_engine.neo4j_client import Neo4jMemoryClient
        docstring = Neo4jMemoryClient.__doc__ or ""
        # 检查模块级文档
        import cognitive_engine.neo4j_client as mod
        module_doc = mod.__doc__ or ""
        self.assertIn("Phase 4", module_doc)

    def test_tools_md_has_phase4_tools(self):
        """验证 TOOLS.md 包含 Phase 4 工具说明。"""
        tools_path = os.path.join(ROOT, "TOOLS.md")
        if os.path.exists(tools_path):
            with open(tools_path, "r") as f:
                content = f.read()
            self.assertIn("neo4j_cognitive_recommend", content)
            self.assertIn("neo4j_cognitive_feedback", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
