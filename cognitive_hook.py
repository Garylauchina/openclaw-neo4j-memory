"""
OpenClaw Cognitive Hook — 认知接管钩子

从 openclaw_cognitive_hook.py 改造而来，作为 OpenClaw 插件与认知引擎之间的桥梁。

改造要点（Phase 1）：
  - import 路径指向 cognitive_engine.cognitive_core
  - 初始化时自动创建 Neo4jMemoryClient 并注入 CognitiveCore
  - 保留原有的 process_query_hook / _should_use_cognitive_core / _fallback_processing 逻辑
  - 认知内核不可用时降级到默认行为
"""

import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger("cognitive_hook")

# 导入认知引擎
try:
    from cognitive_engine.cognitive_core import CognitiveCore
    from cognitive_engine.neo4j_client import Neo4jMemoryClient
    _COGNITIVE_AVAILABLE = True
except ImportError as exc:
    logger.warning("Failed to import cognitive_engine: %s", exc)
    _COGNITIVE_AVAILABLE = False
    CognitiveCore = None
    Neo4jMemoryClient = None


class OpenClawCognitiveHook:
    """
    OpenClaw 认知接管钩子

    替换 OpenClaw 默认的记忆/推理管道，将查询路由到 CognitiveCore。
    当认知内核不可用时，自动降级到默认处理。
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化认知接管钩子。

        Args:
            config_path: CognitiveCore 配置文件路径
        """
        logger.info("Initializing OpenClawCognitiveHook...")

        self.hook_version = "2.0.0-phase1"
        self.integrated_at = datetime.now().isoformat()

        # 状态跟踪
        self.stats = {
            "hook_calls": 0,
            "cognitive_core_calls": 0,
            "fallback_calls": 0,
            "api_calls": 0,
            "graph_writes": 0,
            "errors": 0,
        }

        # 初始化认知内核
        self.cognitive_core: Optional[Any] = None
        self._init_cognitive_core(config_path)

        # 配置
        self.config = {
            "enabled": True,
            "mode": "cognitive_core",  # cognitive_core | hybrid | fallback
            "cache_enabled": True,
            "validation_required": True,
            "reality_anchoring": True,
        }

        logger.info(
            "OpenClawCognitiveHook initialized (version=%s, cognitive_core=%s)",
            self.hook_version,
            "available" if self.cognitive_core else "unavailable",
        )

    def _init_cognitive_core(self, config_path: Optional[str]):
        """初始化认知内核。"""
        if not _COGNITIVE_AVAILABLE:
            logger.warning("Cognitive engine not available, running in fallback mode")
            return

        try:
            # 创建 Neo4j 客户端
            neo4j_base = os.environ.get("NEO4J_API_BASE", "http://127.0.0.1:18900")
            neo4j_client = Neo4jMemoryClient(base_url=neo4j_base)

            # 创建认知内核
            self.cognitive_core = CognitiveCore(
                config_path=config_path,
                neo4j_client=neo4j_client,
            )
            logger.info("CognitiveCore loaded successfully")
        except Exception as exc:
            logger.warning("Failed to load CognitiveCore: %s", exc)
            self.cognitive_core = None

    def process_query_hook(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        查询处理钩子 — 替换 OpenClaw 默认处理。

        Args:
            query: 用户查询
            context: OpenClaw 上下文

        Returns:
            增强的响应字典
        """
        self.stats["hook_calls"] += 1
        logger.info("Hook processing query: %s", query[:80])

        should_use_cognitive = self._should_use_cognitive_core(query, context)

        if should_use_cognitive and self.cognitive_core:
            try:
                self.stats["cognitive_core_calls"] += 1
                result = self.cognitive_core.process_query(query, context)

                # 提取统计信息
                if "system_state" in result:
                    sys_state = result["system_state"]
                    self.stats["api_calls"] += sys_state.get("api_calls", 0)
                    self.stats["graph_writes"] += sys_state.get("graph_writes", 0)

                logger.info(
                    "Cognitive core processed: confidence=%.3f",
                    result.get("metadata", {}).get("confidence", 0.0),
                )

                return self._format_for_openclaw(result, query, context)

            except Exception as exc:
                self.stats["errors"] += 1
                logger.warning("Cognitive core failed: %s", exc)
                return self._fallback_processing(query, context)
        else:
            self.stats["fallback_calls"] += 1
            logger.info("Using fallback processing")
            return self._fallback_processing(query, context)

    def _should_use_cognitive_core(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> bool:
        """判断是否应该使用认知内核。"""
        if not self.config["enabled"]:
            return False
        if not self.cognitive_core:
            return False

        query_lower = query.lower()

        # 应该使用认知内核的关键词
        cognitive_keywords = [
            "usd", "cny", "汇率", "兑换",
            "天气", "temperature", "weather",
            "股票", "stock", "价格",
            "实时", "最新", "当前",
        ]

        # 不应该使用认知内核的关键词
        non_cognitive_keywords = [
            "帮助", "help", "命令", "command",
            "设置", "config", "配置",
            "状态", "status", "统计",
        ]

        for kw in cognitive_keywords:
            if kw in query_lower:
                return True
        for kw in non_cognitive_keywords:
            if kw in query_lower:
                return False

        return self.config["mode"] in ("cognitive_core", "hybrid")

    def _fallback_processing(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """降级处理（模拟 OpenClaw 默认行为）。"""
        response: Dict[str, Any] = {
            "text": f"这是对查询 '{query}' 的默认响应。",
            "source": "openclaw_fallback",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "processed_by": "fallback_handler",
                "cognitive_hook": False,
                "confidence": 0.5,
            },
        }

        query_lower = query.lower()
        if any(kw in query_lower for kw in ("usd", "cny", "汇率")):
            response["text"] = "这是汇率查询的降级响应。认知系统应该处理实时数据查询。"
            response["metadata"]["suggestion"] = "启用认知内核以获得实时汇率数据"

        return response

    def _format_for_openclaw(
        self,
        cognitive_result: Dict[str, Any],
        query: str,
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """将认知结果格式化为 OpenClaw 格式。"""
        formatted_text = cognitive_result.get("formatted_text", "")
        if not formatted_text and cognitive_result.get("results"):
            results = cognitive_result["results"]
            if results and isinstance(results[0], dict):
                if "rate" in results[0]:
                    formatted_text = f"当前USD/CNY汇率: {results[0]['rate']}"
                elif "temperature" in results[0]:
                    formatted_text = f"北京当前气温: {results[0]['temperature']}°C"

        openclaw_response: Dict[str, Any] = {
            "text": formatted_text or f"认知系统处理结果: {cognitive_result.get('query', query)}",
            "source": "cognitive_core",
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "processed_by": "cognitive_core",
                "cognitive_hook": True,
                "confidence": cognitive_result.get("metadata", {}).get("confidence", 0.7),
                "components_used": cognitive_result.get("metadata", {}).get("components_used", 0),
                "validations_passed": cognitive_result.get("metadata", {}).get("validations_passed", 0),
                "original_result": cognitive_result,
            },
        }

        if "system_state" in cognitive_result:
            openclaw_response["metadata"]["system_state"] = cognitive_result["system_state"]

        return openclaw_response

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------

    def get_hook_status(self) -> Dict[str, Any]:
        """获取钩子状态。"""
        cognitive_stats = (
            self.cognitive_core.get_stats() if self.cognitive_core else {}
        )
        hook_calls = self.stats["hook_calls"] or 1  # 避免除零

        return {
            "hook": {
                "version": self.hook_version,
                "integrated_at": self.integrated_at,
                "config": self.config,
                "stats": self.stats,
                "cognitive_core_available": self.cognitive_core is not None,
            },
            "cognitive_core": cognitive_stats,
            "performance": {
                "hook_call_rate": self.stats["hook_calls"],
                "cognitive_usage_rate": self.stats["cognitive_core_calls"] / hook_calls,
                "fallback_rate": self.stats["fallback_calls"] / hook_calls,
                "error_rate": self.stats["errors"] / hook_calls,
            },
        }
