"""
Issue #38: MCP Server 健康检查端点增强

实现三个健康检查端点：
1. GET /health - 基本健康状态
2. GET /diagnose - 详细诊断信息
3. GET /ready - 就绪检查（用于容器编排）
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# 启动时间（用于计算 uptime）
START_TIME = datetime.now()

# 上次冥思运行记录
_last_meditation_result: Optional[Dict[str, Any]] = None


def get_health_check(store, meditation_engine) -> Dict[str, Any]:
    """
    GET /health - 基本健康检查
    
    返回：
    {
        "status": "healthy",
        "neo4j_connection": "connected",
        "llm_api_status": "ok",
        "uptime_seconds": 86400,
        "last_meditation": "2026-04-09T04:00:00Z",
        "meditation_status": "success"
    }
    """
    result = {
        "status": "healthy",
        "neo4j_connection": "unknown",
        "llm_api_status": "unknown",
        "uptime_seconds": 0,
        "last_meditation": None,
        "meditation_status": "unknown"
    }
    
    # 1. 检查 Neo4j 连接
    try:
        connected = store.verify_connectivity()
        result["neo4j_connection"] = "connected" if connected else "disconnected"
        if not connected:
            result["status"] = "unhealthy"
    except Exception as e:
        result["neo4j_connection"] = "error"
        result["neo4j_error"] = str(e)
        result["status"] = "unhealthy"
    
    # 2. 检查 LLM API（简单 ping 测试）
    try:
        from meditation_memory.llm_client import LLMClient
        llm = LLMClient()
        # 尝试获取模型列表（轻量级测试）
        if hasattr(llm, 'list_models'):
            models = llm.list_models()
            if models and len(models) > 0:
                result["llm_api_status"] = "ok"
            else:
                result["llm_api_status"] = "degraded"
                result["llm_warning"] = "Model list is empty"
        else:
            # 没有 list_models 方法，尝试简单初始化
            result["llm_api_status"] = "ok"
            result["llm_note"] = "LLM client initialized successfully"
    except Exception as e:
        result["llm_api_status"] = "error"
        result["llm_error"] = str(e)
    
    # 3. 计算运行时间
    result["uptime_seconds"] = int((datetime.now() - START_TIME).total_seconds())
    
    # 4. 上次冥思状态
    global _last_meditation_result
    if _last_meditation_result:
        result["last_meditation"] = _last_meditation_result.get("started_at")
        result["meditation_status"] = _last_meditation_result.get("status", "unknown")
    
    return result


def get_detailed_diagnose(store, meditation_engine) -> Dict[str, Any]:
    """
    GET /diagnose - 详细诊断信息
    
    返回：
    {
        "neo4j": {
            "status": "connected",
            "node_count": 4485,
            "relationship_count": 417039,
            "pending_nodes": 375
        },
        "llm": {
            "status": "ok",
            "provider": "openrouter",
            "model": "qwen/qwen3.5-plus",
            "rate_limit_remaining": 100
        },
        "meditation": {
            "last_run": "2026-04-09T04:00:00Z",
            "status": "success",
            "duration_seconds": 324,
            "nodes_processed": 600,
            "errors": 0
        },
        "api": {
            "uptime_seconds": 86400,
            "requests_last_hour": 150,
            "avg_response_time_ms": 45
        }
    }
    """
    result = {
        "neo4j": {},
        "llm": {},
        "meditation": {},
        "api": {}
    }
    
    # 1. Neo4j 详细状态
    try:
        connected = store.verify_connectivity()
        result["neo4j"]["status"] = "connected" if connected else "disconnected"
        
        if connected:
            # 获取图谱统计
            stats = store.get_stats()
            meditation_stats = store.get_meditation_stats()
            
            result["neo4j"]["node_count"] = stats.get("node_count", 0)
            result["neo4j"]["relationship_count"] = stats.get("edge_count", 0)
            result["neo4j"]["pending_nodes"] = meditation_stats.get("pending_meditation", 0)
            result["neo4j"]["archived_nodes"] = meditation_stats.get("archived_nodes", 0)
            result["neo4j"]["meta_knowledge_nodes"] = meditation_stats.get("meta_knowledge_nodes", 0)
            result["neo4j"]["generic_relations"] = meditation_stats.get("generic_relations", 0)
    except Exception as e:
        result["neo4j"]["status"] = "error"
        result["neo4j"]["error"] = str(e)
    
    # 2. LLM 详细状态
    try:
        from meditation_memory.llm_client import LLMClient
        from meditation_memory.config import MemoryConfig
        
        llm = LLMClient()
        config = MemoryConfig()
        
        result["llm"]["status"] = "ok"
        result["llm"]["provider"] = config.llm.provider if hasattr(config, 'llm') else "unknown"
        result["llm"]["model"] = config.llm.model if hasattr(config, 'llm') else "unknown"
        result["llm"]["rate_limit_remaining"] = "unknown"  # 需要 API 支持
    except Exception as e:
        result["llm"]["status"] = "error"
        result["llm"]["error"] = str(e)
    
    # 3. 冥思详细状态
    global _last_meditation_result
    if _last_meditation_result:
        result["meditation"]["last_run"] = _last_meditation_result.get("started_at")
        result["meditation"]["status"] = _last_meditation_result.get("status", "unknown")
        
        stats = _last_meditation_result.get("stats", {})
        result["meditation"]["duration_seconds"] = int(_last_meditation_result.get("duration_ms", 0) / 1000)
        result["meditation"]["nodes_processed"] = stats.get("nodes_scanned", 0)
        result["meditation"]["errors"] = len(_last_meditation_result.get("errors", []))
        result["meditation"]["entities_merged"] = stats.get("entities_merged", 0)
        result["meditation"]["relations_relabeled"] = stats.get("relations_relabeled", 0)
        result["meditation"]["meta_knowledge_created"] = stats.get("meta_knowledge_created", 0)
    else:
        result["meditation"]["last_run"] = None
        result["meditation"]["status"] = "no_runs_yet"
    
    # 4. API 服务状态
    result["api"]["uptime_seconds"] = int((datetime.now() - START_TIME).total_seconds())
    result["api"]["requests_last_hour"] = "unknown"  # 需要添加请求计数器
    result["api"]["avg_response_time_ms"] = "unknown"  # 需要添加性能监控
    
    return result


def get_readiness_check(store) -> Dict[str, Any]:
    """
    GET /ready - 就绪检查（用于 Kubernetes/容器编排）
    
    返回：
    - 200 OK - 服务就绪
    - 503 Service Unavailable - 服务未就绪（如 Neo4j 未连接）
    
    就绪条件：
    1. Neo4j 连接正常
    2. 服务启动完成
    """
    result = {
        "ready": False,
        "checks": {}
    }
    
    # 宽限期配置：可通过环境变量 GRACE_PERIOD_SECONDS 调整，默认 5 秒
    grace_period = int(os.environ.get("GRACE_PERIOD_SECONDS", "5"))
    result["checks"]["grace_period_seconds"] = grace_period
    
    # 1. 检查 Neo4j 连接（必需）
    try:
        connected = store.verify_connectivity()
        result["checks"]["neo4j"] = "connected" if connected else "disconnected"
        if not connected:
            result["ready"] = False
            result["reason"] = "Neo4j connection failed"
            return result
    except Exception as e:
        result["checks"]["neo4j"] = "error"
        result["checks"]["neo4j_error"] = str(e)
        result["ready"] = False
        result["reason"] = f"Neo4j connection error: {e}"
        return result
    
    # 2. 检查服务启动时间（确保初始化完成）
    uptime = (datetime.now() - START_TIME).total_seconds()
    result["checks"]["uptime_seconds"] = int(uptime)
    
    if uptime < grace_period:
        result["ready"] = False
        result["reason"] = f"Service still initializing (uptime: {int(uptime)}s < grace_period: {grace_period}s)"
        return result
    
    # 所有检查通过
    result["ready"] = True
    result["message"] = "Service is ready"
    
    return result


def update_meditation_result(result: Dict[str, Any]):
    """更新上次冥思运行结果（从 meditation_worker 调用）"""
    global _last_meditation_result
    _last_meditation_result = result
