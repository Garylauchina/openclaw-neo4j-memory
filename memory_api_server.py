"""
OpenClaw Neo4j 记忆服务器 — v2.2

提供 RESTful API 供 OpenClaw 插件调用。
集成了冥思（Meditation）异步重整机制。

功能：
  - 核心：/ingest, /search, /stats
  - 冥思：/meditation/trigger, /meditation/status, /meditation/history, /meditation/dry-run
  - 后台：MeditationScheduler 自动运行
"""

import logging
import os
import sys
import time
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

# 添加项目根目录到路径，以便导入 meditation_memory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meditation_memory.graph_store import GraphStore
from meditation_memory.entity_extractor import Entity, Relation
from meditation_memory.memory_system import MemorySystem
from meditation_memory.config import Neo4jConfig
from meditation_memory.meditation_worker import MeditationEngine, MeditationRunResult
from meditation_memory.meditation_scheduler import MeditationScheduler
from meditation_memory.meditation_config import MeditationConfig

# ========== 配置与日志 ==========

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("memory_api_server")

app = FastAPI(title="OpenClaw Neo4j Memory API v2.2")

# ========== 全局单例 ==========

store = GraphStore()
memory_system = MemorySystem(store)
meditation_config = MeditationConfig()
meditation_engine = MeditationEngine(store, meditation_config)
meditation_scheduler = MeditationScheduler(meditation_engine, store, meditation_config)

# 存储冥思历史
meditation_history: List[Dict[str, Any]] = []
current_run: Optional[MeditationRunResult] = None

# ========== 数据模型 ==========

class IngestRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    use_llm: bool = True
    async_mode: bool = False

class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    limit: int = 10
    use_llm: bool = True

class MeditationTriggerRequest(BaseModel):
    mode: str = "auto"  # auto / manual / dry_run
    target_nodes: Optional[List[str]] = None

# ========== API 端点 ==========

@app.on_event("startup")
async def startup_event():
    """启动时初始化数据库并开启调度器"""
    if not store.verify_connectivity():
        logger.error("Failed to connect to Neo4j. API server may not work correctly.")
    else:
        store.init_schema()
        logger.info("Connected to Neo4j and schema initialized.")

    # 启动异步调度器
    if meditation_config.enabled:
        await meditation_scheduler.start()
        logger.info("Meditation scheduler started in background.")

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时停止调度器并断开数据库"""
    await meditation_scheduler.stop()
    store.close()
    logger.info("Scheduler stopped and Neo4j connection closed.")

@app.get("/health")
async def health_check():
    connected = store.verify_connectivity()
    return {
        "status": "ok" if connected else "degraded",
        "neo4j_connected": connected,
        "version": "2.2"
    }

@app.post("/ingest")
async def ingest_memory(request: IngestRequest, background_tasks: BackgroundTasks):
    """写入记忆"""
    try:
        if request.async_mode:
            background_tasks.add_task(memory_system.ingest, request.text, request.session_id)
            return {"status": "accepted", "message": "Ingest task queued."}
        
        result = memory_system.ingest(request.text, request.session_id)
        # 注意：这里返回的 result 可能是 Dict 或对象，取决于 MemorySystem.ingest 的实现
        # 为了保持通用性，我们直接返回处理后的字典
        return {
            "status": "success",
            "data": result,
            "session_id": request.session_id
        }
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_memory(request: SearchRequest):
    """搜索记忆"""
    try:
        context = memory_system.get_context(request.query, request.session_id)
        return {
            "status": "success",
            "context": context.to_dict() if hasattr(context, "to_dict") else context
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """获取统计信息"""
    stats = store.get_stats()
    meditation_stats = store.get_meditation_stats()
    return {
        "graph": stats,
        "meditation": meditation_stats
    }

# ========== 冥思（Meditation）相关端点 ==========

@app.post("/meditation/trigger")
async def trigger_meditation(request: MeditationTriggerRequest, background_tasks: BackgroundTasks):
    """手动触发冥思"""
    global current_run
    if current_run and current_run.status == "running":
        return {"status": "error", "message": "Meditation is already running."}

    background_tasks.add_task(run_meditation_task, request.mode, request.target_nodes)
    return {"status": "accepted", "message": "Meditation task started in background."}

@app.get("/meditation/status")
async def get_meditation_status():
    """查看状态"""
    if not current_run:
        return {"status": "idle", "last_run": meditation_history[-1] if meditation_history else None}
    return current_run.to_dict()

@app.get("/meditation/history")
async def get_meditation_history(limit: int = 10):
    """历史记录"""
    return meditation_history[-limit:]

@app.post("/meditation/dry-run")
async def preview_meditation(request: MeditationTriggerRequest):
    """预览模式"""
    result = await meditation_engine.run_meditation(mode="dry_run", target_nodes=request.target_nodes)
    return result.to_dict()

# ========== 内部任务 ==========

async def run_meditation_task(mode: str, target_nodes: Optional[List[str]] = None):
    global current_run
    try:
        current_run = await meditation_engine.run_meditation(mode=mode, target_nodes=target_nodes)
        meditation_history.append(current_run.to_dict())
        if len(meditation_history) > 100:
            meditation_history.pop(0)
    except Exception as e:
        logger.error(f"Background meditation task failed: {e}")
    finally:
        current_run = None

if __name__ == "__main__":
    import uvicorn
    # 默认端口改为 8000 保持 FastAPI 习惯，或根据需要改为 18900
    uvicorn.run(app, host="0.0.0.0", port=18900)
