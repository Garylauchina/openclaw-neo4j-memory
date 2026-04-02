"""
Cognitive Core — 认知内核

统一接口，实现完整的现实学习认知闭环。

改造要点（Phase 1）：
  - 新增 neo4j_api_base 配置项
  - _init_subsystems() 中创建 Neo4jMemoryClient 并传入 memory_provider 和 reality_writer
  - 保留原有12步处理管道不变
  - Neo4j 不可用时自动降级到 Mock 模式
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# 使用包内相对导入
from .neo4j_client import Neo4jMemoryClient
from .adapters.reality_writer import RealityGraphWriter
from .adapters.memory_provider import CognitiveMemoryProvider

# 以下模块在当前目录结构下可选导入（降级安全）
try:
    from .adapters.strong_validator import StrongValidator
except ImportError:
    StrongValidator = None

try:
    from .adapters.real_world_strategy import RealWorldStrategyEngine
except ImportError:
    RealWorldStrategyEngine = None

try:
    from .adapters.world_model_interface import WorldModelEnvironment, EnvironmentAction
except ImportError:
    WorldModelEnvironment = None
    EnvironmentAction = None

logger = logging.getLogger("cognitive_engine.cognitive_core")


class CognitiveCore:
    """
    认知内核 — 统一接口

    提供完整的12步认知处理管道：
      1. 缓存检查
      2. 目标生成
      3. 策略选择
      4. 计划生成
      5. 行动执行（通过 WorldModelEnvironment）
      6. 结果验证（通过 StrongValidator）
      7. 图谱写入（通过 RealityGraphWriter → Neo4j）
      8. 系统状态更新
      9. 响应格式化
      10. 策略进化
      11. 缓存更新
      12. 性能统计
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        neo4j_client: Optional[Neo4jMemoryClient] = None,
    ):
        """
        初始化认知内核。

        Args:
            config_path: 配置文件路径（JSON）
            neo4j_client: 外部传入的 Neo4jMemoryClient（可选，不传则自动创建）
        """
        logger.info("Initializing CognitiveCore...")

        # 加载配置
        self.config = self._load_config(config_path)

        # 创建或使用传入的 Neo4j 客户端
        if neo4j_client:
            self._neo4j_client = neo4j_client
        else:
            neo4j_base = self.config.get("neo4j_api_base", "http://127.0.0.1:18900")
            self._neo4j_client = Neo4jMemoryClient(base_url=neo4j_base)

        # 初始化子系统
        self._init_subsystems()

        # 状态跟踪
        self.stats = {
            "total_queries": 0,
            "api_calls": 0,
            "graph_writes": 0,
            "belief_updates": 0,
            "rqs_updates": 0,
            "strategy_updates": 0,
            "replans_triggered": 0,
            "avg_processing_time": 0.0,
        }

        # 缓存
        self.cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info("CognitiveCore initialized successfully")

    # ------------------------------------------------------------------
    # 配置
    # ------------------------------------------------------------------

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加载配置。"""
        default_config = {
            "enabled": True,
            "version": "2.0.0-phase1",
            "description": "Reality-Learned Cognitive System (Neo4j Integrated)",
            "neo4j_api_base": os.environ.get(
                "NEO4J_API_BASE", "http://127.0.0.1:18900"
            ),
            "components": [
                "RealityGraphWriter",
                "StrongValidator",
                "RealWorldStrategyEngine",
                "WorldModelEnvironment",
                "CognitiveMemoryProvider",
            ],
            "settings": {
                "cache_enabled": True,
                "cache_ttl_seconds": 300,
                "api_fallback_enabled": True,
                "validation_strict_mode": True,
                "replan_threshold": 0.3,
            },
        }

        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as exc:
                logger.warning("Failed to load config from %s: %s", config_path, exc)

        return default_config

    # ------------------------------------------------------------------
    # 子系统初始化
    # ------------------------------------------------------------------

    def _init_subsystems(self):
        """初始化子系统，将 Neo4jMemoryClient 注入适配器。"""
        logger.info("Initializing subsystems...")

        # 1. 现实写入器（对接 Neo4j /ingest）
        self.writer = RealityGraphWriter(neo4j_client=self._neo4j_client)
        logger.info("  RealityGraphWriter initialized (neo4j=%s)",
                     "connected" if self.writer._use_neo4j else "unavailable")

        # 2. 认知记忆提供器（对接 Neo4j /search）
        self.memory_provider = CognitiveMemoryProvider(
            neo4j_client=self._neo4j_client
        )
        logger.info("  CognitiveMemoryProvider initialized (neo4j=%s)",
                     "connected" if self.memory_provider._use_neo4j else "unavailable")

        # 3. 强约束验证器
        if StrongValidator:
            self.validator = StrongValidator(
                graph=self.writer,
                rqs_system=self,
                belief_system=self,
            )
        else:
            self.validator = _MockValidator()
        logger.info("  StrongValidator initialized")

        # 4. 策略引擎
        if RealWorldStrategyEngine:
            self.strategy_engine = RealWorldStrategyEngine()
        else:
            self.strategy_engine = _MockStrategyEngine()
        logger.info("  RealWorldStrategyEngine initialized")

        # 5. 世界模型
        if WorldModelEnvironment:
            self.environment = WorldModelEnvironment()
        else:
            self.environment = _MockEnvironment()
        logger.info("  WorldModelEnvironment initialized")

        # 6-8. 简化版生成器
        self.goal_generator = self._create_goal_generator()
        self.plan_generator = self._create_plan_generator()
        self.action_generator = self._create_action_generator()
        logger.info("  Goal/Plan/Action generators initialized")

    # ------------------------------------------------------------------
    # 12步处理管道
    # ------------------------------------------------------------------

    def process_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理查询 — 完整认知闭环。

        Args:
            query: 用户查询
            context: 上下文信息

        Returns:
            处理结果字典
        """
        start_time = time.time()
        self.stats["total_queries"] += 1
        logger.info("Processing query: %s", query[:80])

        # 1. 检查缓存
        cache_key = f"{query}_{json.dumps(context, sort_keys=True) if context else ''}"
        if self.config["settings"]["cache_enabled"] and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_age = time.time() - cached_data["timestamp"]
            if cache_age < self.config["settings"]["cache_ttl_seconds"]:
                self.cache_hits += 1
                logger.debug("Cache hit (age: %.1fs)", cache_age)
                return cached_data["result"]
        self.cache_misses += 1

        # 2. 生成目标
        goal = self.goal_generator.generate(query)
        logger.info("Goal: %s - %s", goal["type"], goal["target"])

        # 3. 选择策略
        strategy_context = {
            "requires_real_data": goal.get("requires_real_data", False),
            "query_type": goal["type"],
            "priority": goal.get("priority", "low"),
        }
        strategy = self.strategy_engine.select_best_strategy(strategy_context)
        strategy_name = strategy.name if strategy else "default"
        logger.info("Strategy: %s", strategy_name)

        # 4. 生成计划
        plan = self.plan_generator.generate(goal, strategy)
        logger.info("Plan: %d steps", len(plan))

        results: List[Any] = []
        validation_results: List[Any] = []

        # 5. 执行计划
        for i, step in enumerate(plan, 1):
            logger.info("Step %d: %s", i, step.get("description", "unknown"))

            action = self.action_generator.generate(step)
            result = self.environment.act(action)

            if result.status == "success":
                self.stats["api_calls"] += 1
                results.append(result.data)

                # 6. 验证结果
                validation = self.validator.validate(
                    internal_result=result.data,
                    api_result=result.data,
                    context={
                        "action_type": action.type,
                        "source": result.source,
                        "query": query,
                        "inference_path": ["environment", "api_call"],
                    },
                )
                validation_results.append(validation)

                # 7. 写入 Graph
                if goal.get("requires_real_data", False):
                    self._write_to_graph(query, result.data, validation)

                # 8. 更新系统状态
                self._update_systems(validation, result)
            else:
                logger.warning("Step %d failed: %s", i,
                               result.data.get("error", "unknown"))
                if self.config["settings"]["api_fallback_enabled"]:
                    fallback_result = self._handle_failure(step, result)
                    if fallback_result:
                        results.append(fallback_result)

        # 9. 格式化响应
        formatted_response = self._format_response(query, results, validation_results)

        # 10. 触发策略进化
        if validation_results:
            overall_success = any(
                getattr(v, "status", None) == "success" for v in validation_results
            )
            if overall_success and hasattr(self.strategy_engine, "evolve"):
                self.strategy_engine.evolve()

        # 11. 更新缓存
        if self.config["settings"]["cache_enabled"]:
            self.cache[cache_key] = {
                "result": formatted_response,
                "timestamp": time.time(),
                "query": query,
            }

        # 12. 计算处理时间
        processing_time = time.time() - start_time
        total_time = self.stats["avg_processing_time"] * (self.stats["total_queries"] - 1)
        self.stats["avg_processing_time"] = (
            (total_time + processing_time) / self.stats["total_queries"]
        )
        logger.info("Query processed in %.3fs", processing_time)

        return formatted_response

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _write_to_graph(self, query: str, data: Any, validation: Any):
        """写入 Graph（通过 RealityGraphWriter → Neo4j）。"""
        try:
            if isinstance(data, dict):
                if "rate" in data:
                    content = f"USD/CNY汇率: {data['rate']}"
                    value = data["rate"]
                    node_type = "temporal"
                elif "temperature" in data:
                    content = f"北京气温: {data['temperature']}°C"
                    value = data["temperature"]
                    node_type = "temporal"
                else:
                    content = str(data)[:100]
                    value = data
                    node_type = "general"
            else:
                content = str(data)[:100]
                value = data
                node_type = "general"

            rqs = getattr(validation, "confidence", 0.7)

            self.writer.write_reality_data(
                content=content,
                value=value,
                type=node_type,
                source="cognitive_core",
                rqs=rqs,
            )
            self.stats["graph_writes"] += 1
            logger.info("Written to graph: %s (RQS: %.3f)", content[:50], rqs)
        except Exception as exc:
            logger.warning("Graph write failed: %s", exc)

    def _update_systems(self, validation: Any, result: Any):
        """更新系统状态。"""
        if hasattr(validation, "belief_impact"):
            self.stats["belief_updates"] += 1
        if hasattr(validation, "rqs_impact"):
            self.stats["rqs_updates"] += 1

        if result.status == "success":
            real_world_accuracy = getattr(validation, "confidence", 0.8)
            success_rate = 1.0
            cost = getattr(result, "cost", 0.1)

            for strategy_name in list(self.strategy_engine.strategies.keys())[:2]:
                self.strategy_engine.update_strategy(
                    strategy_name, real_world_accuracy, success_rate, cost
                )
            self.stats["strategy_updates"] += 1

        if getattr(validation, "requires_replan", False):
            self.stats["replans_triggered"] += 1
            logger.info("Replan triggered")

    def _handle_failure(
        self, step: Dict[str, Any], result: Any
    ) -> Optional[Dict[str, Any]]:
        """处理失败（降级策略）。"""
        action_type = step.get("action", "")
        if action_type == "get_exchange_rate":
            return {"rate": 6.91, "source": "cache", "note": "API失败，使用缓存数据"}
        elif action_type == "get_weather":
            return {"temperature": 22.0, "source": "fallback", "note": "API失败，使用默认数据"}
        return None

    def _format_response(
        self,
        query: str,
        results: List[Any],
        validations: List[Any],
    ) -> Dict[str, Any]:
        """格式化响应。"""
        overall_confidence = (
            sum(getattr(v, "confidence", 0.7) for v in validations) / len(validations)
            if validations
            else 0.7
        )

        response: Dict[str, Any] = {
            "query": query,
            "results": results,
            "metadata": {
                "processed_by": "cognitive_core",
                "timestamp": datetime.now().isoformat(),
                "confidence": overall_confidence,
                "components_used": len(results),
                "validations_passed": sum(
                    1 for v in validations
                    if getattr(v, "status", None) == "success"
                ) if validations else 0,
            },
            "system_state": {
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate": (
                    self.cache_hits / (self.cache_hits + self.cache_misses)
                    if (self.cache_hits + self.cache_misses) > 0
                    else 0.0
                ),
                "api_calls": self.stats["api_calls"],
                "graph_writes": self.stats["graph_writes"],
            },
        }

        if results:
            first = results[0]
            if isinstance(first, dict) and "rate" in first:
                response["formatted_text"] = f"当前USD/CNY汇率: {first['rate']}"
            elif isinstance(first, dict) and "temperature" in first:
                response["formatted_text"] = f"北京当前气温: {first['temperature']}°C"
            else:
                response["formatted_text"] = f"查询结果: {first}"
        else:
            response["formatted_text"] = "未能获取到相关数据"

        return response

    # ------------------------------------------------------------------
    # 简化版生成器
    # ------------------------------------------------------------------

    def _create_goal_generator(self):
        """创建目标生成器。"""

        class SimpleGoalGenerator:
            def generate(self, query: str) -> Dict[str, Any]:
                if any(kw in query for kw in ("USD", "CNY", "汇率")):
                    return {
                        "type": "exchange_rate_query",
                        "target": "获取实时汇率",
                        "requires_real_data": True,
                        "priority": "high",
                    }
                elif any(kw in query for kw in ("天气", "temperature")):
                    return {
                        "type": "weather_query",
                        "target": "获取天气信息",
                        "requires_real_data": True,
                        "priority": "medium",
                    }
                elif any(kw in query for kw in ("股票", "stock")):
                    return {
                        "type": "stock_query",
                        "target": "获取股票价格",
                        "requires_real_data": True,
                        "priority": "medium",
                    }
                else:
                    return {
                        "type": "general_query",
                        "target": "回答用户问题",
                        "requires_real_data": False,
                        "priority": "low",
                    }

        return SimpleGoalGenerator()

    def _create_plan_generator(self):
        """创建计划生成器。"""

        class SimplePlanGenerator:
            def generate(
                self, goal: Dict[str, Any], strategy: Any
            ) -> List[Dict[str, Any]]:
                plan: List[Dict[str, Any]] = []
                if goal["type"] == "exchange_rate_query":
                    plan.append({
                        "step": 1,
                        "action": "get_exchange_rate",
                        "description": "获取USD/CNY汇率",
                        "params": {"base": "USD", "target": "CNY"},
                    })
                    plan.append({
                        "step": 2,
                        "action": "format_response",
                        "description": "格式化汇率响应",
                    })
                elif goal["type"] == "weather_query":
                    plan.append({
                        "step": 1,
                        "action": "get_weather",
                        "description": "获取天气信息",
                        "params": {"latitude": 39.9042, "longitude": 116.4074},
                    })
                    plan.append({
                        "step": 2,
                        "action": "format_response",
                        "description": "格式化天气响应",
                    })
                else:
                    plan.append({
                        "step": 1,
                        "action": "general_knowledge",
                        "description": "使用通用知识回答",
                    })
                return plan

        return SimplePlanGenerator()

    def _create_action_generator(self):
        """创建行动生成器。"""
        _EnvironmentAction = EnvironmentAction

        class SimpleActionGenerator:
            def generate(self, plan_step: Dict[str, Any]) -> Any:
                action_type = plan_step.get("action", "general_knowledge")
                params = plan_step.get("params", {})
                if _EnvironmentAction:
                    return _EnvironmentAction(
                        action_type=action_type,
                        params=params,
                        expected_effect=plan_step.get("description", ""),
                        timeout_seconds=5,
                    )
                else:
                    return _MockAction(action_type, params)

        return SimpleActionGenerator()

    # ------------------------------------------------------------------
    # RQS / Belief 接口（供 StrongValidator 回调）
    # ------------------------------------------------------------------

    def adjust_score(self, adjustment: float):
        """调整 RQS 分数（供验证器调用）。"""
        logger.debug("RQS adjustment: %+.3f", adjustment)

    def update_belief(
        self, evidence: Dict[str, Any], impact: float, confidence: float
    ):
        """更新信念（供验证器调用）。"""
        logger.debug("Belief update: impact=%+.2f, confidence=%.2f", impact, confidence)

    # ------------------------------------------------------------------
    # 统计
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息。"""
        total = self.cache_hits + self.cache_misses
        return {
            "processing": self.stats,
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.cache_hits / total if total > 0 else 0.0,
                "size": len(self.cache),
            },
            "system": {
                "total_queries": self.stats["total_queries"],
                "avg_processing_time": self.stats["avg_processing_time"],
                "api_call_rate": (
                    self.stats["api_calls"] / self.stats["total_queries"]
                    if self.stats["total_queries"] > 0
                    else 0.0
                ),
                "graph_write_rate": (
                    self.stats["graph_writes"] / self.stats["total_queries"]
                    if self.stats["total_queries"] > 0
                    else 0.0
                ),
            },
            "neo4j": {
                "writer_connected": self.writer._use_neo4j,
                "provider_connected": self.memory_provider._use_neo4j,
            },
        }


# ======================================================================
# Mock 类（降级模式）
# ======================================================================

class _MockValidator:
    """降级用的验证器 Mock。"""

    def validate(self, internal_result, api_result, context=None):
        class _Result:
            status = "acceptable"
            error = 0.0
            confidence = 0.7
            belief_impact = 0.0
            rqs_impact = 0.0
            requires_replan = False
        return _Result()


class _MockStrategyEngine:
    """降级用的策略引擎 Mock。"""

    def __init__(self):
        self.strategies: Dict[str, Any] = {}

    def select_best_strategy(self, context=None):
        class _Strategy:
            name = "mock_strategy"
        return _Strategy()

    def update_strategy(self, *args, **kwargs):
        pass

    def evolve(self):
        pass


class _MockEnvironment:
    """降级用的环境 Mock。"""

    def act(self, action):
        class _Result:
            status = "failed"
            data = {"error": "WorldModelEnvironment not available"}
            latency = 0.0
            cost = 0.0
            confidence = 0.0
            source = "mock"
        return _Result()


class _MockAction:
    """降级用的 Action Mock。"""

    def __init__(self, action_type: str, params: dict):
        self.type = action_type
        self.params = params
