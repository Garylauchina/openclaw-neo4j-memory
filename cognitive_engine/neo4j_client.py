"""
Neo4j 记忆系统 HTTP 客户端

封装对本地 memory_api_server.py（端口 18900）的 API 调用，
为 cognitive_engine 中的 memory_provider 和 reality_writer 提供统一的访问接口。

所有方法在服务不可达时返回 None/False，不抛异常，确保认知系统可降级运行。

API 端点对照：
  health_check()           → GET  /health
  search(query, ...)       → POST /search
  ingest(text, ...)        → POST /ingest
  get_stats()              → GET  /stats
  trigger_meditation(mode) → POST /meditation/trigger

Phase 2 新增端点：
  upsert_strategy(data)    → POST /internal/strategy
  create_evolution_link(c,p1,p2) → POST /internal/strategy/evolution
  archive_strategy(name)   → POST /internal/strategy/archive
  get_all_strategies()     → GET  /internal/strategy/list
  upsert_rqs(data)         → POST /internal/rqs
  get_all_rqs_records()    → GET  /internal/rqs/list
  upsert_belief(data)      → POST /internal/belief
  get_all_beliefs()        → GET  /internal/belief/list
"""

import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cognitive_engine.neo4j_client")

# 优先使用 requests，不可用时回退到 urllib
try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    import json as _json
    import urllib.request
    import urllib.error


class Neo4jMemoryClient:
    """
    Neo4j 记忆系统 HTTP 客户端

    通过 HTTP 调用 memory_api_server.py 暴露的 RESTful API，
    封装连接管理、重试、超时和错误处理逻辑。
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:18900",
        timeout: int = 10,
        max_retries: int = 3,
    ):
        """
        初始化客户端。

        Args:
            base_url: memory_api_server 的基础 URL
            timeout: 单次请求超时秒数
            max_retries: 最大重试次数
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # 如果 requests 可用，创建 Session 以复用连接
        if _HAS_REQUESTS:
            self._session = requests.Session()
            self._session.headers.update({"Content-Type": "application/json"})
        else:
            self._session = None

        logger.info(
            "Neo4jMemoryClient initialized: base_url=%s, timeout=%ds, max_retries=%d, "
            "http_lib=%s",
            self.base_url, self.timeout, self.max_retries,
            "requests" if _HAS_REQUESTS else "urllib",
        )

    # ------------------------------------------------------------------
    # 公开 API（Phase 1）
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """
        检查后端服务是否可用。

        Returns:
            True 表示服务正常（status == 'ok'），否则 False
        """
        try:
            data = self._get("/health")
            if data and data.get("status") in ("ok", "degraded"):
                logger.debug("Health check passed: %s", data)
                return True
            return False
        except Exception as exc:
            logger.warning("Health check failed: %s", exc)
            return False

    def search(
        self,
        query: str,
        limit: int = 10,
        use_llm: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        调用 POST /search 搜索记忆。

        Args:
            query: 搜索文本
            limit: 返回结果数量上限
            use_llm: 实体抽取是否使用 LLM

        Returns:
            API 返回的 JSON 字典，失败时返回 None。
            成功时结构示例::

                {
                    "status": "success",
                    "context": {
                        "context_text": "...",
                        "subgraph": {"nodes": [...], "edges": [...]},
                        "matched_entities": [...],
                        "entity_count": 5,
                        "edge_count": 3
                    }
                }
        """
        payload = {"query": query, "limit": limit, "use_llm": use_llm}
        return self._post("/search", payload)

    def ingest(
        self,
        text: str,
        session_id: Optional[str] = None,
        use_llm: bool = True,
        async_mode: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        调用 POST /ingest 写入记忆。

        Args:
            text: 要写入的文本
            session_id: 可选的会话 ID
            use_llm: 实体抽取是否使用 LLM
            async_mode: 是否异步写入（True 时后端立即返回 accepted）

        Returns:
            API 返回的 JSON 字典，失败时返回 None。
            异步模式成功示例::

                {"status": "accepted", "message": "Ingest task queued."}
        """
        payload: Dict[str, Any] = {
            "text": text,
            "use_llm": use_llm,
            "async_mode": async_mode,
        }
        if session_id:
            payload["session_id"] = session_id
        return self._post("/ingest", payload)

    def get_stats(self) -> Optional[Dict[str, Any]]:
        """
        调用 GET /stats 获取图谱统计信息。

        Returns:
            统计字典，失败时返回 None
        """
        return self._get("/stats")

    def trigger_meditation(self, mode: str = "auto") -> Optional[Dict[str, Any]]:
        """
        调用 POST /meditation/trigger 触发冥思。

        Args:
            mode: 运行模式（auto / manual / dry_run）

        Returns:
            API 返回的 JSON 字典，失败时返回 None
        """
        return self._post("/meditation/trigger", {"mode": mode})

    # ------------------------------------------------------------------
    # Phase 2: 策略持久化 API
    # ------------------------------------------------------------------

    def upsert_strategy(self, strategy_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        写入或更新策略节点。

        Args:
            strategy_data: 策略摘要字典，来自 RealWorldStrategy.get_summary()

        Returns:
            API 返回的 JSON 字典，失败时返回 None
        """
        return self._post("/internal/strategy", strategy_data)

    def create_evolution_link(
        self, child: str, parent1: str, parent2: str
    ) -> Optional[Dict[str, Any]]:
        """
        记录策略进化谱系。

        Args:
            child: 子策略名称
            parent1: 父策略 1 名称
            parent2: 父策略 2 名称

        Returns:
            API 返回的 JSON 字典，失败时返回 None
        """
        return self._post(
            "/internal/strategy/evolution",
            {"child": child, "parent1": parent1, "parent2": parent2},
        )

    def archive_strategy(self, name: str) -> Optional[Dict[str, Any]]:
        """
        归档被淘汰的策略。

        Args:
            name: 策略名称

        Returns:
            API 返回的 JSON 字典，失败时返回 None
        """
        return self._post("/internal/strategy/archive", {"name": name})

    def get_all_strategies(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取所有活跃策略节点。

        Returns:
            策略列表，失败时返回 None
        """
        data = self._get("/internal/strategy/list")
        if data and data.get("status") == "success":
            return data.get("strategies", [])
        return None

    def upsert_rqs(self, rqs_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        写入或更新 RQS 记录。

        Args:
            rqs_data: RQS 记录字典，来自 ReasoningStats.to_dict()

        Returns:
            API 返回的 JSON 字典，失败时返回 None
        """
        return self._post("/internal/rqs", rqs_data)

    def get_all_rqs_records(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取所有 RQS 记录。

        Returns:
            RQS 记录列表，失败时返回 None
        """
        data = self._get("/internal/rqs/list")
        if data and data.get("status") == "success":
            return data.get("records", [])
        return None

    def upsert_belief(self, belief_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        写入或更新信念节点。

        Args:
            belief_data: 信念数据字典

        Returns:
            API 返回的 JSON 字典，失败时返回 None
        """
        return self._post("/internal/belief", belief_data)

    def get_all_beliefs(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取所有信念节点。

        Returns:
            信念列表，失败时返回 None
        """
        data = self._get("/internal/belief/list")
        if data and data.get("status") == "success":
            return data.get("beliefs", [])
        return None

    # ------------------------------------------------------------------
    # 内部 HTTP 方法
    # ------------------------------------------------------------------

    def _get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """带重试的 GET 请求，失败返回 None。"""
        url = f"{self.base_url}{endpoint}"
        for attempt in range(1, self.max_retries + 1):
            try:
                if _HAS_REQUESTS:
                    resp = self._session.get(url, timeout=self.timeout)
                    resp.raise_for_status()
                    return resp.json()
                else:
                    req = urllib.request.Request(url, method="GET")
                    with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                        return _json.loads(resp.read().decode())
            except Exception as exc:
                logger.warning(
                    "GET %s failed (attempt %d/%d): %s",
                    url, attempt, self.max_retries, exc,
                )
                if attempt < self.max_retries:
                    time.sleep(0.5 * attempt)
        return None

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """带重试的 POST 请求，失败返回 None。"""
        url = f"{self.base_url}{endpoint}"
        for attempt in range(1, self.max_retries + 1):
            try:
                if _HAS_REQUESTS:
                    resp = self._session.post(url, json=payload, timeout=self.timeout)
                    resp.raise_for_status()
                    return resp.json()
                else:
                    data = _json.dumps(payload).encode()
                    req = urllib.request.Request(
                        url,
                        data=data,
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                        return _json.loads(resp.read().decode())
            except Exception as exc:
                logger.warning(
                    "POST %s failed (attempt %d/%d): %s",
                    url, attempt, self.max_retries, exc,
                )
                if attempt < self.max_retries:
                    time.sleep(0.5 * attempt)
        return None

    def close(self):
        """关闭底层 HTTP 会话。"""
        if _HAS_REQUESTS and self._session:
            self._session.close()
            logger.info("Neo4jMemoryClient session closed.")
