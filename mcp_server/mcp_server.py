#!/usr/bin/env python3
"""
OpenClaw Neo4j Memory — MCP Server

一个轻量级的 MCP (Model Context Protocol) 封装层，将 OpenClaw 的
记忆系统 HTTP API (memory_api_server.py) 暴露为标准 MCP Tools，
使 Claude Desktop、Cursor、Windsurf、Manus 等 MCP 客户端能够
直接接入 OpenClaw 的长期记忆与认知引擎。

架构：
  MCP Client  ←→  本文件 (MCP Server)  ←→  memory_api_server.py (HTTP API)  ←→  Neo4j

本服务不重复实现任何业务逻辑，仅做协议适配。
"""

import os
import json
import logging
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ========== 配置 ==========

MEMORY_API_URL = os.environ.get("MEMORY_API_URL", "http://127.0.0.1:18900")
REQUEST_TIMEOUT = float(os.environ.get("MCP_REQUEST_TIMEOUT", "30"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("openclaw-mcp-server")

# ========== MCP Server 实例 ==========

mcp = FastMCP(
    "OpenClaw Memory",
    instructions=(
        "OpenClaw 长期记忆与认知引擎的 MCP 接口。\n\n"
        "本服务提供以下能力：\n"
        "1. memory_ingest — 将对话、事实、决策等写入图谱记忆\n"
        "2. memory_search — 检索与查询相关的记忆上下文\n"
        "3. memory_search_with_strategy — 检索记忆并获取认知引擎的策略推荐\n"
        "4. memory_feedback — 提交执行结果反馈，驱动策略自我进化\n"
        "5. memory_stats — 获取图谱与冥思系统的统计信息\n"
        "6. meditation_trigger — 手动触发冥思（记忆重整优化）\n"
        "7. meditation_status — 查看冥思运行状态\n\n"
        "推荐工作流：\n"
        "  1) 每次对话开始前，调用 memory_search 获取背景上下文\n"
        "  2) 如需策略指导，调用 memory_search_with_strategy\n"
        "  3) 对话结束后，调用 memory_ingest 保存重要信息\n"
        "  4) 任务完成后，调用 memory_feedback 提交反馈闭环"
    ),
)


# ========== HTTP 客户端辅助函数 ==========


async def _api_request(
    method: str,
    path: str,
    json_body: Optional[dict] = None,
    params: Optional[dict] = None,
) -> dict:
    """
    向 memory_api_server.py 发送 HTTP 请求并返回 JSON 响应。

    如果后端不可达或返回错误，会抛出包含详细信息的异常，
    MCP 框架会将其转化为工具调用的错误响应返回给客户端。
    """
    url = f"{MEMORY_API_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.request(
                method=method,
                url=url,
                json=json_body,
                params=params,
            )
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        raise RuntimeError(
            f"无法连接到 OpenClaw 记忆服务 ({MEMORY_API_URL})。"
            "请确认 memory_api_server.py 正在运行：\n"
            "  curl http://127.0.0.1:18900/health"
        )
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", "")
        except Exception:
            detail = e.response.text[:500]
        raise RuntimeError(
            f"记忆服务返回错误 (HTTP {e.response.status_code}): {detail}"
        )
    except httpx.TimeoutException:
        raise RuntimeError(
            f"请求超时 ({REQUEST_TIMEOUT}s)。如果冥思正在运行，可适当增大 "
            "MCP_REQUEST_TIMEOUT 环境变量。"
        )
    except Exception as e:
        raise RuntimeError(f"请求记忆服务失败: {type(e).__name__}: {e}")


# ========== MCP Tools ==========


@mcp.tool()
async def memory_ingest(
    text: str,
    session_id: str = "",
    use_llm: bool = True,
) -> str:
    """
    将文本写入 OpenClaw 图谱记忆。

    系统会自动进行实体抽取（支持 LLM 增强）和关系构建，
    将信息以结构化的方式存储到 Neo4j 知识图谱中。

    适用场景：
    - 保存对话中的重要事实、决策、结论
    - 记录用户偏好、项目信息、技术方案
    - 归档会话摘要

    Args:
        text: 要写入的文本内容。可以是一段对话、一个事实陈述或任何值得记忆的信息。
        session_id: 可选的会话 ID，用于将记忆关联到特定会话上下文。
        use_llm: 是否使用 LLM 进行增强实体抽取（默认 True，效果更好但稍慢）。

    Returns:
        写入结果的 JSON 字符串，包含提取的实体和关系信息。
    """
    body = {
        "text": text,
        "use_llm": use_llm,
        "async_mode": False,
    }
    if session_id:
        body["session_id"] = session_id

    result = await _api_request("POST", "/ingest", json_body=body)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def memory_search(
    query: str,
    session_id: str = "",
    limit: int = 10,
) -> str:
    """
    搜索与查询相关的记忆上下文。

    基于图谱的子图检索，返回与查询语义相关的实体、关系和上下文信息。
    适合在回答问题前获取背景知识。

    Args:
        query: 搜索查询文本。系统会进行语义匹配，找到图谱中相关的记忆片段。
        session_id: 可选的会话 ID，用于优先返回同一会话的记忆。
        limit: 返回结果的最大数量（默认 10）。

    Returns:
        搜索结果的 JSON 字符串，包含匹配的记忆上下文。
    """
    body = {
        "query": query,
        "limit": limit,
        "include_strategies": False,
    }
    if session_id:
        body["session_id"] = session_id

    result = await _api_request("POST", "/search", json_body=body)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def memory_search_with_strategy(
    query: str,
    session_id: str = "",
    limit: int = 10,
) -> str:
    """
    搜索记忆并获取认知引擎的策略推荐。

    除了返回相关记忆上下文外，还会从认知引擎中检索适用于当前查询的策略推荐。
    策略按 fitness_score（适应度）排序，优先推荐经过实战验证的高分策略。

    推荐在以下场景使用：
    - 处理复杂决策问题时，获取历史经验指导
    - 需要选择最佳处理方案时
    - 希望利用系统积累的认知经验时

    Args:
        query: 搜索查询文本。
        session_id: 可选的会话 ID。
        limit: 返回记忆结果的最大数量（默认 10）。

    Returns:
        JSON 字符串，包含：
        - context: 匹配的记忆上下文
        - recommended_strategies: 推荐策略列表（含 name, fitness_score, strategy_type 等）
    """
    body = {
        "query": query,
        "limit": limit,
        "include_strategies": True,
    }
    if session_id:
        body["session_id"] = session_id

    result = await _api_request("POST", "/search", json_body=body)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def memory_feedback(
    query: str,
    success: bool,
    confidence: float = 0.5,
    applied_strategy_name: str = "",
    validation_status: str = "acceptable",
    error_msg: str = "",
) -> str:
    """
    提交策略执行结果反馈，驱动认知引擎自我进化。

    反馈会触发以下更新：
    1. 策略适应度（fitness_score）调整 — 成功的策略得分上升，失败的下降
    2. RQS（推理质量评分）更新 — 基于验证状态调整推理路径的可信度
    3. 信念系统更新 — 强化或削弱相关信念的置信度

    这是认知闭环的关键一环，持续反馈能让系统的策略推荐越来越精准。

    Args:
        query: 原始查询文本。
        success: 执行是否成功。
        confidence: 结果置信度，范围 0.0-1.0（默认 0.5）。
        applied_strategy_name: 使用的策略名称（如果使用了策略推荐）。
        validation_status: 验证状态，可选值：
            - "accurate" — 结果准确
            - "acceptable" — 结果可接受（默认）
            - "wrong" — 结果错误
        error_msg: 如果失败，提供错误信息以帮助系统学习。

    Returns:
        反馈处理结果的 JSON 字符串，包含各子系统的更新状态。
    """
    body: dict = {
        "query": query,
        "success": success,
        "confidence": confidence,
        "validation_status": validation_status,
    }
    if applied_strategy_name:
        body["applied_strategy_name"] = applied_strategy_name
    if error_msg:
        body["error_msg"] = error_msg

    result = await _api_request("POST", "/feedback", json_body=body)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def memory_stats() -> str:
    """
    获取记忆系统的统计信息。

    返回图谱和冥思系统的综合统计数据，包括：
    - 图谱统计：节点数、关系数、实体类型分布等
    - 冥思统计：运行次数、上次运行时间、优化效果等

    适用场景：
    - 了解记忆系统的当前规模和健康状态
    - 监控冥思优化的效果
    - 调试和诊断系统问题

    Returns:
        统计信息的 JSON 字符串。
    """
    result = await _api_request("GET", "/stats")
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def meditation_trigger(
    mode: str = "auto",
) -> str:
    """
    手动触发冥思（记忆重整优化）。

    冥思是一个后台运行的 9 步图谱优化流水线，类似大脑睡眠时的记忆整理：
    1. 快照 → 2. 剪枝 → 3. 实体合并 → 4. 关系重构
    → 5. 权重调整 → 6. 知识蒸馏 → 6.5 策略蒸馏
    → 6.6 策略进化 → 7. 提交

    通常冥思会按计划自动运行（默认每天凌晨 3:00），但你也可以手动触发。

    Args:
        mode: 触发模式，可选值：
            - "auto" — 自动模式（默认），系统判断是否需要运行
            - "manual" — 强制运行，忽略条件检查

    Returns:
        触发结果的 JSON 字符串。冥思在后台异步执行，可通过 meditation_status 查看进度。
    """
    body = {"mode": mode}
    result = await _api_request("POST", "/meditation/trigger", json_body=body)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def meditation_status() -> str:
    """
    查看冥思的当前运行状态。

    返回冥思系统的实时状态，包括：
    - 当前是否正在运行
    - 如果正在运行，当前执行到哪一步
    - 上一次运行的结果摘要

    Returns:
        冥思状态的 JSON 字符串。
    """
    result = await _api_request("GET", "/meditation/status")
    return json.dumps(result, ensure_ascii=False, indent=2)


# ========== 入口 ==========

if __name__ == "__main__":
    logger.info(
        f"Starting OpenClaw Memory MCP Server "
        f"(backend: {MEMORY_API_URL})"
    )
    mcp.run()
