#!/usr/bin/env python3
"""
Phase 3 冥思升级 — 综合测试

覆盖范围：
  1. MeditationStrategyConfig 默认值和环境变量覆盖
  2. EntityExtractor 增强后的 event/intent 类型识别
  3. GraphStore 新增方法的 Cypher 正确性（Mock driver）
  4. StrategyDistiller 的 LLM 调用和 JSON 解析（Mock OpenAI）
  5. 步骤 6.5 策略蒸馏的完整流程
  6. 步骤 6.6 策略进化的淘汰和交叉逻辑
  7. 新步骤失败时的错误处理（不影响后续步骤）
  8. relation_ontology 新增关系类型验证
"""

import asyncio
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch, PropertyMock

# 确保项目根目录在 sys.path 中
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ======================================================================
# 1. MeditationStrategyConfig 默认值和环境变量覆盖
# ======================================================================

class TestMeditationStrategyConfig(unittest.TestCase):
    """测试 MeditationStrategyConfig 的默认值和环境变量覆盖。"""

    def test_default_values(self):
        """验证 MeditationStrategyConfig 的默认值。"""
        from meditation_memory.meditation_config import MeditationStrategyConfig
        config = MeditationStrategyConfig()
        self.assertEqual(config.min_causal_chain_length, 3)
        self.assertEqual(config.max_strategies_per_run, 3)
        self.assertAlmostEqual(config.fitness_elimination_threshold, 0.2)
        self.assertAlmostEqual(config.reality_protection_threshold, 0.15)
        self.assertEqual(config.min_strategy_pool_size, 3)
        self.assertAlmostEqual(config.crossover_rate, 0.3)
        self.assertAlmostEqual(config.mutation_rate, 0.1)
        self.assertAlmostEqual(config.distillation_temperature, 0.3)

    @patch.dict(os.environ, {
        "MEDITATION_MIN_CHAIN_LENGTH": "5",
        "MEDITATION_MAX_NEW_STRATEGIES": "10",
        "MEDITATION_FITNESS_ELIMINATION": "0.4",
        "MEDITATION_REALITY_PROTECTION": "0.25",
        "MEDITATION_MIN_STRATEGY_POOL": "5",
        "MEDITATION_CROSSOVER_RATE": "0.6",
        "MEDITATION_MUTATION_RATE": "0.2",
        "MEDITATION_STRATEGY_TEMPERATURE": "0.5",
    })
    def test_env_override(self):
        """验证环境变量可以覆盖默认值。"""
        from meditation_memory.meditation_config import MeditationStrategyConfig
        config = MeditationStrategyConfig()
        self.assertEqual(config.min_causal_chain_length, 5)
        self.assertEqual(config.max_strategies_per_run, 10)
        self.assertAlmostEqual(config.fitness_elimination_threshold, 0.4)
        self.assertAlmostEqual(config.reality_protection_threshold, 0.25)
        self.assertEqual(config.min_strategy_pool_size, 5)
        self.assertAlmostEqual(config.crossover_rate, 0.6)
        self.assertAlmostEqual(config.mutation_rate, 0.2)
        self.assertAlmostEqual(config.distillation_temperature, 0.5)

    def test_config_in_meditation_config(self):
        """验证 MeditationConfig 包含 strategy 子配置。"""
        from meditation_memory.meditation_config import MeditationConfig
        config = MeditationConfig()
        self.assertTrue(hasattr(config, "strategy"))
        self.assertEqual(config.strategy.min_causal_chain_length, 3)

    @patch.dict(os.environ, {
        "MEDITATION_MAX_NEW_STRATEGIES": "0",
        "MEDITATION_FITNESS_ELIMINATION": "0.0",
    })
    def test_disable_via_env(self):
        """验证通过环境变量可以禁用新功能。"""
        from meditation_memory.meditation_config import MeditationStrategyConfig
        config = MeditationStrategyConfig()
        self.assertEqual(config.max_strategies_per_run, 0)
        self.assertAlmostEqual(config.fitness_elimination_threshold, 0.0)


# ======================================================================
# 2. EntityExtractor 增强后的 event/intent 类型识别
# ======================================================================

class TestEntityExtractorPhase3(unittest.TestCase):
    """测试 EntityExtractor 增强后的 event/intent 类型识别和因果关系。"""

    def test_intent_type_recognition(self):
        """测试规则模式下 intent 类型的识别。"""
        from meditation_memory.entity_extractor import EntityExtractor
        from meditation_memory.config import LLMConfig

        extractor = EntityExtractor(LLMConfig())

        # 测试 _classify_entity_type 方法
        self.assertEqual(extractor._classify_entity_type("投资目标", "n"), "intent")
        self.assertEqual(extractor._classify_entity_type("发展计划", "n"), "intent")
        self.assertEqual(extractor._classify_entity_type("未来期望", "n"), "intent")
        self.assertEqual(extractor._classify_entity_type("用户需求", "n"), "intent")

    def test_non_intent_types(self):
        """测试非 intent 类型不被错误分类。"""
        from meditation_memory.entity_extractor import EntityExtractor
        from meditation_memory.config import LLMConfig

        extractor = EntityExtractor(LLMConfig())

        # 人名
        self.assertEqual(extractor._classify_entity_type("张教授", "nr"), "person")
        # 地名
        self.assertEqual(extractor._classify_entity_type("北京市", "ns"), "place")
        # 机构
        self.assertEqual(extractor._classify_entity_type("谷歌公司", "nt"), "organization")
        # 普通概念
        self.assertEqual(extractor._classify_entity_type("量子计算", "n"), "concept")

    def test_llm_extraction_with_event_and_intent(self):
        """测试 LLM 模式可以提取 event 和 intent 类型实体及因果关系。"""
        from meditation_memory.entity_extractor import EntityExtractor
        from meditation_memory.config import LLMConfig

        extractor = EntityExtractor(LLMConfig(api_key="test-key"))

        # 模拟 LLM 返回包含 event、intent 和 causes 关系的结果
        mock_response_content = json.dumps({
            "entities": [
                {"name": "美联储加息", "entity_type": "event"},
                {"name": "美元走强", "entity_type": "event"},
                {"name": "资本外流", "entity_type": "event"},
                {"name": "稳定汇率", "entity_type": "intent"},
            ],
            "relations": [
                {"source": "美联储加息", "target": "美元走强", "relation_type": "causes"},
                {"source": "美元走强", "target": "资本外流", "relation_type": "leads_to"},
            ],
        })

        mock_choice = MagicMock()
        mock_choice.message.content = mock_response_content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        extractor._client = mock_client

        result = extractor.extract(
            "由于美联储加息导致美元走强，进而引发新兴市场资本外流",
            use_llm=True,
        )

        # 验证 event 类型实体
        event_entities = [e for e in result.entities if e.entity_type == "event"]
        self.assertGreaterEqual(len(event_entities), 2)

        # 验证 intent 类型实体
        intent_entities = [e for e in result.entities if e.entity_type == "intent"]
        self.assertEqual(len(intent_entities), 1)

        # 验证因果关系
        causal_relations = [
            r for r in result.relations
            if r.relation_type in ("causes", "leads_to")
        ]
        self.assertGreaterEqual(len(causal_relations), 1)

    def test_llm_prompt_includes_event_intent(self):
        """验证 LLM 提示词包含 event 和 intent 类型说明。"""
        from meditation_memory.entity_extractor import _EXTRACTION_SYSTEM_PROMPT
        self.assertIn("event", _EXTRACTION_SYSTEM_PROMPT)
        self.assertIn("intent", _EXTRACTION_SYSTEM_PROMPT)
        self.assertIn("causes", _EXTRACTION_SYSTEM_PROMPT)
        self.assertIn("leads_to", _EXTRACTION_SYSTEM_PROMPT)

    def test_intent_indicators_defined(self):
        """验证 _INTENT_INDICATORS 集合已定义。"""
        from meditation_memory.entity_extractor import _INTENT_INDICATORS
        self.assertIsInstance(_INTENT_INDICATORS, set)
        self.assertIn("想要", _INTENT_INDICATORS)
        self.assertIn("目标", _INTENT_INDICATORS)
        self.assertIn("计划", _INTENT_INDICATORS)


# ======================================================================
# 3. GraphStore 新增方法的 Cypher 正确性（Mock driver）
# ======================================================================

class TestGraphStorePhase3(unittest.TestCase):
    """测试 GraphStore 中 Phase 3 新增的 Cypher 方法。"""

    def setUp(self):
        """创建带 Mock driver 的 GraphStore。"""
        self.mock_driver = MagicMock()
        self.mock_session = MagicMock()
        self.mock_driver.session.return_value.__enter__ = Mock(
            return_value=self.mock_session
        )
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
                return_value=iter(
                    return_value if isinstance(return_value, list) else [return_value]
                )
            )
        else:
            mock_result.single.return_value = None
            mock_result.__iter__ = Mock(return_value=iter([]))
        self.mock_session.run.return_value = mock_result

    # ---------- get_causal_chains ----------

    def test_get_causal_chains_cypher(self):
        """验证 get_causal_chains 的 Cypher 查询包含正确的路径匹配。"""
        mock_records = [
            {
                "chain_nodes": [
                    {"name": "事件A", "entity_type": "event", "properties": "{}"},
                    {"name": "事件B", "entity_type": "event", "properties": "{}"},
                    {"name": "事件C", "entity_type": "event", "properties": "{}"},
                ],
                "chain_relations": [
                    {"type": "causes", "properties": "{}"},
                    {"type": "causes", "properties": "{}"},
                ],
                "chain_length": 2,
            }
        ]
        self._setup_session(mock_records)

        results = self.store.get_causal_chains(min_length=3, limit=20)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]["chain_nodes"]), 3)

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        # 验证 Cypher 包含路径匹配和 CAUSES 过滤
        self.assertIn("RELATES_TO", cypher)
        self.assertIn("causes", cypher)
        self.assertIn("NOT e1:Archived", cypher)
        self.assertIn("NOT e2:Archived", cypher)
        self.assertIn("$limit", cypher)

    def test_get_causal_chains_min_length(self):
        """验证 min_length 参数正确转换为路径长度。"""
        self._setup_session([])

        self.store.get_causal_chains(min_length=5, limit=10)

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        # min_length=5 → min_rels=4
        self.assertIn("4..10", cypher)

    def test_get_causal_chains_empty_result(self):
        """验证无因果链时返回空列表。"""
        self._setup_session([])
        results = self.store.get_causal_chains()
        self.assertEqual(results, [])

    def test_get_causal_chains_error_handling(self):
        """验证查询异常时返回空列表而非抛异常。"""
        self.mock_session.run.side_effect = Exception("DB error")
        results = self.store.get_causal_chains()
        self.assertEqual(results, [])

    # ---------- get_event_clusters ----------

    def test_get_event_clusters_cypher(self):
        """验证 get_event_clusters 的 Cypher 查询。"""
        mock_records = [
            {
                "event_name": "市场崩盘",
                "properties": "{}",
                "degree": 5,
                "connections": [
                    {"target": "恐慌", "relation": "RELATES_TO", "target_type": "concept"}
                ],
            }
        ]
        self._setup_session(mock_records)

        results = self.store.get_event_clusters(min_connections=3)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["event_name"], "市场崩盘")

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("entity_type: 'event'", cypher)
        self.assertIn("NOT e:Archived", cypher)
        self.assertIn("$min_connections", cypher)

    def test_get_event_clusters_error_handling(self):
        """验证查询异常时返回空列表。"""
        self.mock_session.run.side_effect = Exception("DB error")
        results = self.store.get_event_clusters()
        self.assertEqual(results, [])

    # ---------- get_strategies_for_evolution ----------

    def test_get_strategies_for_evolution_cypher(self):
        """验证 get_strategies_for_evolution 的 Cypher 查询。"""
        mock_records = [
            {
                "name": "strategy_1",
                "strategy_type": "greedy",
                "uses_real_data": True,
                "fitness_score": 0.9,
                "usage_count": 20,
                "avg_accuracy": 0.85,
                "parent_names": [],
            },
            {
                "name": "strategy_2",
                "strategy_type": "trend",
                "uses_real_data": False,
                "fitness_score": 0.3,
                "usage_count": 5,
                "avg_accuracy": 0.4,
                "parent_names": ["strategy_1"],
            },
        ]
        self._setup_session(mock_records)

        results = self.store.get_strategies_for_evolution()
        self.assertEqual(len(results), 2)

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("NOT s:Archived", cypher)
        self.assertIn("EVOLVED_FROM", cypher)
        self.assertIn("ORDER BY s.fitness_score DESC", cypher)
        self.assertIn("parent.name", cypher)

    # ---------- create_causal_chain_node ----------

    def test_create_causal_chain_node_cypher(self):
        """验证 create_causal_chain_node 的 Cypher 查询。"""
        self._setup_session({"eid": "4:chain:001"})

        chain_data = {
            "chain_id": "chain_001",
            "description": "加息→美元走强→资本外流",
            "length": 3,
        }

        result = self.store.create_causal_chain_node(chain_data)
        self.assertEqual(result, "4:chain:001")

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("CREATE (c:CausalChain", cypher)
        self.assertIn("chain_id: $chain_id", cypher)
        self.assertIn("description: $description", cypher)
        self.assertIn("length: $length", cypher)
        self.assertIn("timestamp()", cypher)

        kwargs = call_args[1]
        self.assertEqual(kwargs["chain_id"], "chain_001")
        self.assertEqual(kwargs["length"], 3)

    def test_create_causal_chain_node_error_handling(self):
        """验证创建失败时返回空字符串。"""
        self.mock_session.run.side_effect = Exception("DB error")
        result = self.store.create_causal_chain_node(
            {"chain_id": "x", "description": "y", "length": 1}
        )
        self.assertEqual(result, "")

    # ---------- link_strategy_to_causal_chain ----------

    def test_link_strategy_to_causal_chain_cypher(self):
        """验证 link_strategy_to_causal_chain 的 Cypher 查询。"""
        self._setup_session()

        self.store.link_strategy_to_causal_chain("strategy_1", "chain_001")

        call_args = self.mock_session.run.call_args
        cypher = call_args[0][0]
        self.assertIn("GENERATED_BY", cypher)
        self.assertIn("$strategy_name", cypher)
        self.assertIn("$chain_id", cypher)
        self.assertIn("Strategy", cypher)
        self.assertIn("CausalChain", cypher)

        kwargs = call_args[1]
        self.assertEqual(kwargs["strategy_name"], "strategy_1")
        self.assertEqual(kwargs["chain_id"], "chain_001")

    def test_link_strategy_to_causal_chain_error_handling(self):
        """验证链接失败时不抛异常。"""
        self.mock_session.run.side_effect = Exception("DB error")
        # 不应抛出异常
        self.store.link_strategy_to_causal_chain("s", "c")

    # ---------- init_schema 包含因果链索引 ----------

    def test_init_schema_includes_causal_chain_index(self):
        """验证 init_schema 包含因果链索引。"""
        self._setup_session()
        self.store.init_schema()

        # 检查所有 run 调用中是否包含因果链索引
        all_calls = self.mock_session.run.call_args_list
        all_cypher = [call[0][0] for call in all_calls]
        found = any("causal_chain_id_idx" in c for c in all_cypher)
        self.assertTrue(found, "init_schema should include CausalChain index")


# ======================================================================
# 4. StrategyDistiller 的 LLM 调用和 JSON 解析（Mock OpenAI）
# ======================================================================

class TestStrategyDistiller(unittest.TestCase):
    """测试 StrategyDistiller 的 LLM 调用和 JSON 解析。"""

    def _make_distiller(self):
        """创建带 mock LLM config 的 StrategyDistiller。"""
        from cognitive_engine.strategy_distiller import StrategyDistiller

        mock_config = MagicMock()
        mock_config.api_key = "test-key"
        mock_config.base_url = "http://test"
        mock_config.model = "gpt-4.1-mini"
        return StrategyDistiller(mock_config)

    def test_distill_empty_chains(self):
        """空因果链应返回空列表。"""
        distiller = self._make_distiller()
        result = distiller.distill([], max_strategies=3)
        self.assertEqual(result, [])

    def test_distill_with_mock_llm(self):
        """测试正常 LLM 返回时的策略解析。"""
        distiller = self._make_distiller()

        mock_strategies = [
            {
                "name": "trend_following",
                "description": "跟随趋势策略",
                "uses_real_data": True,
                "applicable_scenarios": ["市场趋势"],
                "expected_accuracy": 0.75,
            },
            {
                "name": "risk_aversion",
                "description": "风险规避策略",
                "uses_real_data": False,
                "applicable_scenarios": ["市场波动"],
                "expected_accuracy": 0.6,
            },
        ]

        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(mock_strategies)
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        distiller._client = mock_client

        result = distiller.distill(
            [{"chain_nodes": [{"name": "A"}, {"name": "B"}, {"name": "C"}]}],
            max_strategies=3,
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "trend_following")
        self.assertTrue(result[0]["uses_real_data"])

    def test_distill_max_strategies_limit(self):
        """测试 max_strategies 参数限制返回数量。"""
        distiller = self._make_distiller()

        mock_strategies = [
            {"name": f"s{i}", "description": f"策略{i}"}
            for i in range(5)
        ]

        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps(mock_strategies)
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        distiller._client = mock_client

        result = distiller.distill(
            [{"chain_nodes": [{"name": "A"}]}],
            max_strategies=2,
        )
        self.assertEqual(len(result), 2)

    def test_distill_invalid_json(self):
        """测试 LLM 返回无效 JSON 时的处理。"""
        distiller = self._make_distiller()

        mock_choice = MagicMock()
        mock_choice.message.content = "这不是 JSON 格式的内容"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        distiller._client = mock_client

        result = distiller.distill(
            [{"chain_nodes": [{"name": "A"}]}],
            max_strategies=3,
        )
        self.assertEqual(result, [])

    def test_distill_json_in_markdown(self):
        """测试 LLM 返回 Markdown 包裹的 JSON。"""
        distiller = self._make_distiller()

        strategies = [{"name": "test_strategy", "description": "测试"}]
        content = f"以下是策略建议：\n{json.dumps(strategies)}\n请参考。"

        mock_choice = MagicMock()
        mock_choice.message.content = content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        distiller._client = mock_client

        result = distiller.distill(
            [{"chain_nodes": [{"name": "A"}]}],
            max_strategies=3,
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "test_strategy")

    def test_distill_llm_error(self):
        """测试 LLM 调用失败时返回空列表。"""
        distiller = self._make_distiller()

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        distiller._client = mock_client

        result = distiller.distill(
            [{"chain_nodes": [{"name": "A"}]}],
            max_strategies=3,
        )
        self.assertEqual(result, [])

    def test_format_chains(self):
        """测试因果链格式化。"""
        distiller = self._make_distiller()

        chains = [
            {
                "chain_nodes": [
                    {"name": "加息"},
                    {"name": "美元走强"},
                    {"name": "资本外流"},
                ]
            }
        ]
        text = distiller._format_chains(chains)
        self.assertIn("加息", text)
        self.assertIn("→", text)
        self.assertIn("资本外流", text)


# ======================================================================
# 5. 步骤 6.5 策略蒸馏的完整流程
# ======================================================================

class TestStep65StrategyDistillation(unittest.TestCase):
    """测试冥思步骤 6.5 策略蒸馏的完整流程。"""

    def _run_async(self, coro):
        """运行异步协程。"""
        return asyncio.get_event_loop().run_until_complete(coro)

    def _make_engine(self, chains=None, distill_result=None, dry_run=False,
                     max_strategies=3):
        """创建带 mock 的 MeditationEngine。"""
        # Mock GraphStore
        mock_store = MagicMock()
        mock_store.get_causal_chains.return_value = chains or []
        mock_store.get_nodes_needing_meditation.return_value = []
        mock_store.upsert_strategy_node.return_value = "4:s:1"

        # Mock config
        from meditation_memory.meditation_config import (
            MeditationConfig,
            MeditationStrategyConfig,
        )
        config = MeditationConfig()
        config.strategy.max_strategies_per_run = max_strategies
        config.safety.dry_run = dry_run

        # 创建 engine
        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.meditation_worker import MeditationEngine
            engine = MeditationEngine.__new__(MeditationEngine)

        engine.store = mock_store
        engine.config = config
        engine.llm = MagicMock()
        engine._is_running = False

        # Mock StrategyDistiller
        mock_distiller = MagicMock()
        mock_distiller.distill.return_value = distill_result or []
        engine.strategy_distiller = mock_distiller

        return engine, mock_store, mock_distiller

    def test_distillation_with_chains(self):
        """测试有因果链时的策略蒸馏流程。"""
        chains = [
            {
                "chain_nodes": [
                    {"name": "A", "entity_type": "event"},
                    {"name": "B", "entity_type": "event"},
                    {"name": "C", "entity_type": "event"},
                ],
                "chain_relations": [{"type": "causes"}, {"type": "causes"}],
                "chain_length": 2,
            }
        ]
        distill_result = [
            {
                "name": "trend_following",
                "description": "趋势跟随",
                "uses_real_data": True,
                "expected_accuracy": 0.75,
                "applicable_scenarios": ["趋势市场"],
            }
        ]

        engine, mock_store, mock_distiller = self._make_engine(
            chains=chains, distill_result=distill_result
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_5_strategy_distillation(result))

        # 验证调用链
        mock_store.get_causal_chains.assert_called_once()
        mock_distiller.distill.assert_called_once()
        mock_store.upsert_strategy_node.assert_called_once()

        # 验证策略数据
        call_args = mock_store.upsert_strategy_node.call_args[0][0]
        self.assertEqual(call_args["name"], "distilled_trend_following")
        self.assertEqual(call_args["type"], "distilled")
        self.assertTrue(call_args["uses_real_data"])

        # 验证统计
        self.assertEqual(result.causal_chains_found, 1)
        self.assertEqual(result.strategies_distilled, 1)

    def test_distillation_no_chains(self):
        """测试无因果链时跳过蒸馏。"""
        engine, mock_store, mock_distiller = self._make_engine(chains=[])

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_5_strategy_distillation(result))

        mock_distiller.distill.assert_not_called()
        self.assertEqual(result.strategies_distilled, 0)

    def test_distillation_disabled(self):
        """测试 max_strategies_per_run=0 时跳过蒸馏。"""
        engine, mock_store, mock_distiller = self._make_engine(
            max_strategies=0
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_5_strategy_distillation(result))

        mock_store.get_causal_chains.assert_not_called()
        mock_distiller.distill.assert_not_called()

    def test_distillation_dry_run(self):
        """测试 dry_run 模式下不写入图谱。"""
        chains = [{"chain_nodes": [{"name": "A"}], "chain_length": 1}]
        distill_result = [{"name": "test", "description": "test"}]

        engine, mock_store, mock_distiller = self._make_engine(
            chains=chains, distill_result=distill_result, dry_run=True
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult(dry_run=True)

        self._run_async(engine._step_6_5_strategy_distillation(result))

        mock_store.upsert_strategy_node.assert_not_called()
        self.assertEqual(len(result.suggestions), 1)
        self.assertEqual(result.suggestions[0]["step"], "strategy_distillation")

    def test_distillation_no_distiller(self):
        """测试 StrategyDistiller 不可用时跳过。"""
        engine, mock_store, _ = self._make_engine()
        engine.strategy_distiller = None

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_5_strategy_distillation(result))

        mock_store.get_causal_chains.assert_not_called()


# ======================================================================
# 6. 步骤 6.6 策略进化的淘汰和交叉逻辑
# ======================================================================

class TestStep66StrategyEvolution(unittest.TestCase):
    """测试冥思步骤 6.6 策略进化的淘汰和交叉逻辑。"""

    def _run_async(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def _make_engine(self, strategies=None, dry_run=False,
                     fitness_threshold=0.2, reality_threshold=0.15,
                     min_pool=3, crossover_rate=0.3):
        """创建带 mock 的 MeditationEngine。"""
        mock_store = MagicMock()
        mock_store.get_strategies_for_evolution.return_value = strategies or []
        mock_store.upsert_strategy_node.return_value = "4:s:1"

        from meditation_memory.meditation_config import MeditationConfig
        config = MeditationConfig()
        config.strategy.fitness_elimination_threshold = fitness_threshold
        config.strategy.reality_protection_threshold = reality_threshold
        config.strategy.min_strategy_pool_size = min_pool
        config.strategy.crossover_rate = crossover_rate
        config.safety.dry_run = dry_run

        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.meditation_worker import MeditationEngine
            engine = MeditationEngine.__new__(MeditationEngine)

        engine.store = mock_store
        engine.config = config
        engine.llm = MagicMock()
        engine._is_running = False
        engine.strategy_distiller = MagicMock()

        return engine, mock_store

    def test_evolution_archives_low_fitness(self):
        """测试淘汰低适应度策略。"""
        strategies = [
            {"name": "good_s", "fitness_score": 0.9, "uses_real_data": False,
             "usage_count": 10},
            {"name": "bad_s", "fitness_score": 0.1, "uses_real_data": False,
             "usage_count": 10},
            {"name": "medium_s", "fitness_score": 0.5, "uses_real_data": False,
             "usage_count": 10},
        ]

        engine, mock_store = self._make_engine(
            strategies=strategies, crossover_rate=0.0
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_6_strategy_evolution(result))

        # bad_s 的 fitness 0.1 < 0.2 应被淘汰
        mock_store.archive_strategy.assert_called_once_with("bad_s")
        self.assertEqual(result.strategies_archived, 1)
        self.assertEqual(result.strategies_evaluated, 3)

    def test_evolution_protects_real_data_strategy(self):
        """测试现实数据策略使用更低的保护阈值。"""
        strategies = [
            {"name": "real_s", "fitness_score": 0.16, "uses_real_data": True,
             "usage_count": 10},
            {"name": "normal_s", "fitness_score": 0.16, "uses_real_data": False,
             "usage_count": 10},
            {"name": "good_s", "fitness_score": 0.9, "uses_real_data": False,
             "usage_count": 10},
        ]

        engine, mock_store = self._make_engine(
            strategies=strategies, crossover_rate=0.0
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_6_strategy_evolution(result))

        # real_s: fitness 0.16 > reality_protection_threshold 0.15 → 不淘汰
        # normal_s: fitness 0.16 < fitness_elimination_threshold 0.2 → 淘汰
        mock_store.archive_strategy.assert_called_once_with("normal_s")
        self.assertEqual(result.strategies_archived, 1)

    def test_evolution_skips_low_usage(self):
        """测试使用次数不足的策略不被淘汰。"""
        strategies = [
            {"name": "new_s", "fitness_score": 0.1, "uses_real_data": False,
             "usage_count": 2},  # usage_count <= 5, 不淘汰
            {"name": "good_s", "fitness_score": 0.9, "uses_real_data": False,
             "usage_count": 10},
            {"name": "ok_s", "fitness_score": 0.5, "uses_real_data": False,
             "usage_count": 10},
        ]

        engine, mock_store = self._make_engine(
            strategies=strategies, crossover_rate=0.0
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_6_strategy_evolution(result))

        mock_store.archive_strategy.assert_not_called()

    def test_evolution_pool_too_small(self):
        """测试策略池过小时跳过进化。"""
        strategies = [
            {"name": "s1", "fitness_score": 0.1, "uses_real_data": False,
             "usage_count": 10},
        ]

        engine, mock_store = self._make_engine(
            strategies=strategies, min_pool=3
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_6_strategy_evolution(result))

        mock_store.archive_strategy.assert_not_called()
        mock_store.upsert_strategy_node.assert_not_called()

    @patch("meditation_memory.meditation_worker.random")
    def test_evolution_crossover(self, mock_random):
        """测试交叉进化生成新策略。"""
        mock_random.random.return_value = 0.1  # < crossover_rate 0.3
        mock_random.sample.return_value = [
            {"name": "p1", "fitness_score": 0.8, "uses_real_data": True,
             "usage_count": 10},
            {"name": "p2", "fitness_score": 0.7, "uses_real_data": False,
             "usage_count": 10},
        ]

        strategies = [
            {"name": "p1", "fitness_score": 0.8, "uses_real_data": True,
             "usage_count": 10},
            {"name": "p2", "fitness_score": 0.7, "uses_real_data": False,
             "usage_count": 10},
            {"name": "p3", "fitness_score": 0.6, "uses_real_data": False,
             "usage_count": 10},
        ]

        engine, mock_store = self._make_engine(
            strategies=strategies, crossover_rate=0.3
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_6_strategy_evolution(result))

        # 验证创建了子策略
        mock_store.upsert_strategy_node.assert_called_once()
        child_data = mock_store.upsert_strategy_node.call_args[0][0]
        self.assertEqual(child_data["name"], "evolved_p1_p2")
        self.assertEqual(child_data["type"], "evolved")
        # uses_real_data = p1.True OR p2.False = True
        self.assertTrue(child_data["uses_real_data"])
        # fitness = (0.8 + 0.7) / 2 = 0.75
        self.assertAlmostEqual(child_data["fitness"], 0.75)

        # 验证创建了进化链接
        mock_store.create_evolution_link.assert_called_once_with(
            "evolved_p1_p2", "p1", "p2"
        )
        self.assertEqual(result.strategies_evolved, 1)

    @patch("meditation_memory.meditation_worker.random")
    def test_evolution_crossover_skipped_by_rate(self, mock_random):
        """测试交叉概率不满足时跳过。"""
        mock_random.random.return_value = 0.5  # > crossover_rate 0.3

        strategies = [
            {"name": "p1", "fitness_score": 0.8, "uses_real_data": False,
             "usage_count": 10},
            {"name": "p2", "fitness_score": 0.7, "uses_real_data": False,
             "usage_count": 10},
            {"name": "p3", "fitness_score": 0.6, "uses_real_data": False,
             "usage_count": 10},
        ]

        engine, mock_store = self._make_engine(
            strategies=strategies, crossover_rate=0.3
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_6_strategy_evolution(result))

        mock_store.upsert_strategy_node.assert_not_called()
        self.assertEqual(result.strategies_evolved, 0)

    def test_evolution_disabled(self):
        """测试通过配置禁用策略进化。"""
        engine, mock_store = self._make_engine(
            fitness_threshold=0.0, crossover_rate=0.0
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()

        self._run_async(engine._step_6_6_strategy_evolution(result))

        mock_store.get_strategies_for_evolution.assert_not_called()

    def test_evolution_dry_run(self):
        """测试 dry_run 模式下不实际归档或创建策略。"""
        strategies = [
            {"name": "bad_s", "fitness_score": 0.1, "uses_real_data": False,
             "usage_count": 10},
            {"name": "good_s", "fitness_score": 0.9, "uses_real_data": False,
             "usage_count": 10},
            {"name": "ok_s", "fitness_score": 0.5, "uses_real_data": False,
             "usage_count": 10},
        ]

        engine, mock_store = self._make_engine(
            strategies=strategies, dry_run=True, crossover_rate=0.0
        )

        from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult(dry_run=True)

        self._run_async(engine._step_6_6_strategy_evolution(result))

        mock_store.archive_strategy.assert_not_called()
        # 应有 dry_run 建议
        archive_suggestions = [
            s for s in result.suggestions
            if s.get("action") == "archive_strategy"
        ]
        self.assertEqual(len(archive_suggestions), 1)


# ======================================================================
# 7. 新步骤失败时的错误处理（不影响后续步骤）
# ======================================================================

class TestPhase3ErrorHandling(unittest.TestCase):
    """测试新步骤失败时的错误处理。"""

    def _run_async(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_step_6_5_failure_does_not_block_step_7(self):
        """测试步骤 6.5 失败不影响步骤 7 执行。"""
        mock_store = MagicMock()
        # 步骤 1 返回一些节点
        mock_store.get_nodes_needing_meditation.return_value = [
            {"name": "test", "entity_type": "concept"}
        ]
        mock_store.lock_nodes_for_meditation.return_value = 1
        mock_store.create_meditation_snapshot.return_value = "{}"
        mock_store.unlock_nodes_after_meditation.return_value = 1
        # 其他步骤的 mock
        mock_store.get_orphan_nodes.return_value = []
        mock_store.get_generic_word_nodes.return_value = []
        mock_store.get_similar_entity_pairs.return_value = []
        mock_store.get_short_name_entities.return_value = []
        mock_store.get_entities_missing_metadata.return_value = []
        mock_store.get_related_to_edges.return_value = []
        mock_store.get_all_active_nodes_for_weighting.return_value = []
        mock_store.get_dense_subgraphs_for_distillation.return_value = []
        # 步骤 6.5 会失败
        mock_store.get_causal_chains.side_effect = Exception("DB connection lost")

        from meditation_memory.meditation_config import MeditationConfig
        config = MeditationConfig()

        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.meditation_worker import MeditationEngine
            engine = MeditationEngine.__new__(MeditationEngine)

        engine.store = mock_store
        engine.config = config
        engine.llm = MagicMock()
        engine._is_running = False

        # Mock StrategyDistiller
        mock_distiller = MagicMock()
        mock_distiller.distill.side_effect = Exception("Distillation failed")
        engine.strategy_distiller = mock_distiller

        result = self._run_async(engine.run_meditation(mode="auto"))

        # 步骤 7 应该仍然执行（解锁节点）
        mock_store.unlock_nodes_after_meditation.assert_called_once()
        # 状态应为 completed 而非 failed
        self.assertEqual(result.status, "completed")
        # 错误应被记录
        error_msgs = " ".join(result.errors)
        self.assertIn("step_6_5", error_msgs)

    def test_step_6_6_failure_does_not_block_step_7(self):
        """测试步骤 6.6 失败不影响步骤 7 执行。"""
        mock_store = MagicMock()
        mock_store.get_nodes_needing_meditation.return_value = [
            {"name": "test", "entity_type": "concept"}
        ]
        mock_store.lock_nodes_for_meditation.return_value = 1
        mock_store.create_meditation_snapshot.return_value = "{}"
        mock_store.unlock_nodes_after_meditation.return_value = 1
        mock_store.get_orphan_nodes.return_value = []
        mock_store.get_generic_word_nodes.return_value = []
        mock_store.get_similar_entity_pairs.return_value = []
        mock_store.get_short_name_entities.return_value = []
        mock_store.get_entities_missing_metadata.return_value = []
        mock_store.get_related_to_edges.return_value = []
        mock_store.get_all_active_nodes_for_weighting.return_value = []
        mock_store.get_dense_subgraphs_for_distillation.return_value = []
        mock_store.get_causal_chains.return_value = []
        # 步骤 6.6 会失败
        mock_store.get_strategies_for_evolution.side_effect = Exception(
            "Evolution DB error"
        )

        from meditation_memory.meditation_config import MeditationConfig
        config = MeditationConfig()

        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.meditation_worker import MeditationEngine
            engine = MeditationEngine.__new__(MeditationEngine)

        engine.store = mock_store
        engine.config = config
        engine.llm = MagicMock()
        engine._is_running = False
        engine.strategy_distiller = MagicMock()

        result = self._run_async(engine.run_meditation(mode="auto"))

        mock_store.unlock_nodes_after_meditation.assert_called_once()
        self.assertEqual(result.status, "completed")
        error_msgs = " ".join(result.errors)
        self.assertIn("step_6_6", error_msgs)

    def test_both_new_steps_fail_still_completes(self):
        """测试两个新步骤都失败时仍能完成冥思。"""
        mock_store = MagicMock()
        mock_store.get_nodes_needing_meditation.return_value = [
            {"name": "test", "entity_type": "concept"}
        ]
        mock_store.lock_nodes_for_meditation.return_value = 1
        mock_store.create_meditation_snapshot.return_value = "{}"
        mock_store.unlock_nodes_after_meditation.return_value = 1
        mock_store.get_orphan_nodes.return_value = []
        mock_store.get_generic_word_nodes.return_value = []
        mock_store.get_similar_entity_pairs.return_value = []
        mock_store.get_short_name_entities.return_value = []
        mock_store.get_entities_missing_metadata.return_value = []
        mock_store.get_related_to_edges.return_value = []
        mock_store.get_all_active_nodes_for_weighting.return_value = []
        mock_store.get_dense_subgraphs_for_distillation.return_value = []
        mock_store.get_causal_chains.side_effect = Exception("Error 1")
        mock_store.get_strategies_for_evolution.side_effect = Exception("Error 2")

        from meditation_memory.meditation_config import MeditationConfig
        config = MeditationConfig()

        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.meditation_worker import MeditationEngine
            engine = MeditationEngine.__new__(MeditationEngine)

        engine.store = mock_store
        engine.config = config
        engine.llm = MagicMock()
        engine._is_running = False
        engine.strategy_distiller = MagicMock()
        engine.strategy_distiller.distill.side_effect = Exception("Distill error")

        result = self._run_async(engine.run_meditation(mode="auto"))

        self.assertEqual(result.status, "completed")
        self.assertGreaterEqual(len(result.errors), 2)
        mock_store.unlock_nodes_after_meditation.assert_called_once()


# ======================================================================
# 8. relation_ontology 新增关系类型验证
# ======================================================================

class TestRelationOntologyPhase3(unittest.TestCase):
    """验证 relation_ontology 包含 Phase 3 新增的关系类型。"""

    def test_new_relation_types_in_ontology(self):
        """验证 Phase 3 新增的关系类型在 ontology 中。"""
        from meditation_memory.meditation_config import MeditationRestructuringConfig
        config = MeditationRestructuringConfig()

        new_types = ["leads_to", "precedes", "prevents", "achieves", "aims_at"]
        for rel_type in new_types:
            self.assertIn(
                rel_type, config.relation_ontology,
                f"'{rel_type}' should be in relation_ontology"
            )

    def test_existing_relation_types_preserved(self):
        """验证现有关系类型未被移除。"""
        from meditation_memory.meditation_config import MeditationRestructuringConfig
        config = MeditationRestructuringConfig()

        existing_types = [
            "uses", "owns", "located_in", "works_at", "interested_in",
            "created_by", "part_of", "depends_on", "causes", "knows",
            "contains", "belongs_to", "is_instance_of", "familiar_with",
            "studies", "manages", "collaborates_with", "opposes",
            "supports", "derived_from",
        ]
        for rel_type in existing_types:
            self.assertIn(
                rel_type, config.relation_ontology,
                f"'{rel_type}' should still be in relation_ontology"
            )

    def test_ontology_total_count(self):
        """验证关系类型总数为 25（20 + 5 新增）。"""
        from meditation_memory.meditation_config import MeditationRestructuringConfig
        config = MeditationRestructuringConfig()
        self.assertEqual(len(config.relation_ontology), 25)


# ======================================================================
# 9. MeditationRunResult Phase 3 字段
# ======================================================================

class TestMeditationRunResultPhase3(unittest.TestCase):
    """测试 MeditationRunResult 包含 Phase 3 新增字段。"""

    def test_new_fields_exist(self):
        """验证新增统计字段存在且默认为 0。"""
        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()
        self.assertEqual(result.strategies_distilled, 0)
        self.assertEqual(result.strategies_archived, 0)
        self.assertEqual(result.strategies_evolved, 0)
        self.assertEqual(result.causal_chains_found, 0)
        self.assertEqual(result.strategies_evaluated, 0)

    def test_to_dict_includes_new_fields(self):
        """验证 to_dict 包含新增字段。"""
        with patch("meditation_memory.graph_store.GraphDatabase"):
            from meditation_memory.meditation_worker import MeditationRunResult
        result = MeditationRunResult()
        result.strategies_distilled = 2
        result.strategies_archived = 1
        result.strategies_evolved = 1
        result.causal_chains_found = 5
        result.strategies_evaluated = 10

        d = result.to_dict()
        stats = d["stats"]
        self.assertEqual(stats["strategies_distilled"], 2)
        self.assertEqual(stats["strategies_archived"], 1)
        self.assertEqual(stats["strategies_evolved"], 1)
        self.assertEqual(stats["causal_chains_found"], 5)
        self.assertEqual(stats["strategies_evaluated"], 10)


if __name__ == "__main__":
    unittest.main()
