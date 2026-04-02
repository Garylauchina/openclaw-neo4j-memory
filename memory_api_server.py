"""
OpenClaw Neo4j 记忆服务器 — v2.3

提供 RESTful API 供 OpenClaw 插件调用。
集成了冥思（Meditation）异步重整机制。

功能：
  - 核心：/ingest, /search, /stats
  - 冥思：/meditation/trigger, /meditation/status, /meditation/history, /meditation/dry-run
  - 内部（Phase 2）：/internal/strategy, /internal/rqs, /internal/belief
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

app = FastAPI(title="OpenClaw Neo4j Memory API v2.3")

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


# ========== Phase 2: 内部 API 数据模型 ==========

class StrategyUpsertRequest(BaseModel):
    name: str
    type: str = "unknown"
    uses_real_data: bool = False
    fitness: float = 0.0
    real_world_bonus: float = 0.0
    performance: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class RQSUpsertRequest(BaseModel):
    path_id: str
    success_count: int = 0
    fail_count: int = 0
    total_uses: int = 0
    historical_success_rate: float = 0.0
    stability_score: float = 0.5
    avg_rqs: float = 0.0
    last_used: str = ""

class BeliefUpsertRequest(BaseModel):
    content: str
    belief_strength: float = 0.5
    confidence: float = 0.5
    state: str = "HYPOTHESIS"
    evidence_count: int = 0
    source: str = "cognitive_core"

class EvolutionLinkRequest(BaseModel):
    child: str
    parent1: str
    parent2: str

class ArchiveStrategyRequest(BaseModel):
    name: str


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
        "version": "2.3"
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


# ========== Phase 2: 内部结构化写入端点 ==========

@app.post("/internal/strategy")
async def upsert_strategy(request: StrategyUpsertRequest):
    """写入或更新策略节点"""
    try:
        eid = store.upsert_strategy_node(request.dict())
        return {"status": "success", "element_id": eid}
    except Exception as e:
        logger.error(f"Strategy upsert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/strategy/evolution")
async def create_evolution_link(request: EvolutionLinkRequest):
    """记录策略进化谱系"""
    try:
        store.create_evolution_link(request.child, request.parent1, request.parent2)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Evolution link creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/strategy/archive")
async def archive_strategy(request: ArchiveStrategyRequest):
    """归档被淘汰的策略"""
    try:
        store.archive_strategy(request.name)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Strategy archive failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/internal/strategy/list")
async def list_strategies():
    """获取所有活跃策略"""
    try:
        strategies = store.get_all_strategies()
        return {"status": "success", "strategies": strategies}
    except Exception as e:
        logger.error(f"Strategy list failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/rqs")
async def upsert_rqs(request: RQSUpsertRequest):
    """写入或更新 RQS 记录"""
    try:
        eid = store.upsert_rqs_node(request.dict())
        return {"status": "success", "element_id": eid}
    except Exception as e:
        logger.error(f"RQS upsert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/internal/rqs/list")
async def list_rqs_records():
    """获取所有 RQS 记录"""
    try:
        records = store.get_all_rqs_records()
        return {"status": "success", "records": records}
    except Exception as e:
        logger.error(f"RQS list failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/internal/belief")
async def upsert_belief(request: BeliefUpsertRequest):
    """写入或更新信念节点"""
    try:
        eid = store.upsert_belief_node(request.dict())
        return {"status": "success", "element_id": eid}
    except Exception as e:
        logger.error(f"Belief upsert failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/internal/belief/list")
async def list_beliefs():
    """获取所有信念节点"""
    try:
        beliefs = store.get_all_beliefs()
        return {"status": "success", "beliefs": beliefs}
    except Exception as e:
        logger.error(f"Belief list failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
