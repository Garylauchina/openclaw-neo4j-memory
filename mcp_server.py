"""
Neo4j 记忆系统 — MCP Server

将记忆 REST API 封装为 MCP Tools，供 OpenClaw / Claude Desktop / Cursor 等客户端调用。

Tools:
  - search_memory     检索相关记忆
  - ingest_memory     写入新记忆
  - get_stats         获取图统计信息
  - start_meditation  触发冥思
  - get_meditation_status  查询冥思状态

用法:
  # 本地开发（stdio 传输）
  python mcp_server.py

  # 指定 API 地址
  MEMORY_API_URL=http://localhost:18900 python mcp_server.py
"""

import json
import logging
import os
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_server")

# API 地址，优先使用环境变量，默认指向本地 API 服务
MEMORY_API_URL = os.environ.get("MEMORY_API_URL", "http://localhost:18900")

mcp = FastMCP(
    name="neo4j-memory",
    instructions="Neo4j 图记忆系统 — 通过 MCP 协议读写 Agent 长期记忆"
)


def _client() -> httpx.Client:
    """创建同步 HTTP 客户端（MCP tools 运行在同步上下文中）"""
    return httpx.Client(base_url=MEMORY_API_URL, timeout=30.0)


@mcp.tool()
def search_memory(
    query: str,
    limit: int = 10,
    depth: int = 2,
    use_llm: bool = True
) -> str:
    """从 Neo4j 图数据库中检索相关记忆。

    Args:
        query: 搜索关键词或自然语言查询
        limit: 返回结果数量上限（默认 10）
        depth: 子图展开深度，1=仅直接关联，2=二度关联（默认 2）
        use_llm: 是否使用 LLM 增强搜索结果（默认 True）

    Returns:
        JSON 字符串，包含匹配的实体、关系和上下文
    """
    try:
        with _client() as client:
            resp = client.post("/search", json={
                "query": query,
                "limit": limit,
                "depth": depth,
                "use_llm": use_llm,
            })
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def ingest_memory(
    text: str,
    session_id: str = "",
    use_llm: bool = True
) -> str:
    """将新记忆写入 Neo4j 图数据库。

    Args:
        text: 要记忆的文本内容
        session_id: 可选，会话标识，用于关联同一对话中的记忆
        use_llm: 是否使用 LLM 进行实体抽取（默认 True）

    Returns:
        JSON 字符串，包含抽取的实体数量和关系数量
    """
    try:
        payload: dict = {"text": text, "use_llm": use_llm}
        if session_id:
            payload["session_id"] = session_id
        with _client() as client:
            resp = client.post("/ingest", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def get_stats() -> str:
    """获取记忆图谱的统计信息，包括节点数、关系数、冥思状态等。

    Returns:
        JSON 字符串，包含图谱规模、冥思 pending 数量等统计
    """
    try:
        with _client() as client:
            resp = client.get("/stats")
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def start_meditation(
    mode: str = "auto"
) -> str:
    """触发记忆冥思（后台异步执行）。

    冥思会扫描图谱中的冗余节点、合并相似实体、推断新关系、
    评估策略适应度并归档过期记忆。

    Args:
        mode: 冥思模式，auto（自动）或 manual（手动）

    Returns:
        JSON 字符串，包含任务接受状态
    """
    try:
        with _client() as client:
            resp = client.post("/meditation/trigger", json={"mode": mode})
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def get_meditation_status() -> str:
    """查询最近一次冥思的运行状态和统计结果。

    Returns:
        JSON 字符串，包含上次冥思的运行状态、处理节点数、
        合并/剪枝/推断数量等
    """
    try:
        with _client() as client:
            resp = client.get("/meditation/status")
            resp.raise_for_status()
            data = resp.json()
            return json.dumps(data, ensure_ascii=False, indent=2)
    except httpx.HTTPError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8000"))

    logger.info(
        "Starting Neo4j Memory MCP Server (API: %s, transport: %s)",
        MEMORY_API_URL,
        transport
    )
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport in ("streamable-http", "http"):
        mcp.run(transport="streamable-http")
    else:
        logger.error("Unknown MCP_TRANSPORT=%s, falling back to stdio", transport)
        mcp.run(transport="stdio")
