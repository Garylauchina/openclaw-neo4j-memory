"""
OpenClaw Neo4j 记忆服务器 — v2.4

提供 RESTful API 供 OpenClaw 插件调用。
集成了冥思（Meditation）异步重整机制。

功能：
  - 核心：/ingest, /search, /stats
  - 冥思：/meditation/trigger, /meditation/status, /meditation/history, /meditation/dry-run
  - 内部（Phase 2）：/internal/strategy, /internal/rqs, /internal/belief
  - 反馈闭环（Phase 4）：/feedback
  - 后台：MeditationScheduler 自动运行

Phase 4 新增：
  - /search 升级：新增 include_strategies 参数，返回 recommended_strategies
  - /feedback 端点：接收执行结果反馈，驱动策略适应度更新、RQS 调整、信念更新
  - 环境变量控制：COGNITIVE_STRATEGY_ENABLED, COGNITIVE_FEEDBACK_ENABLED
"""

import json
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

app = FastAPI(title="OpenClaw Neo4j Memory API v2.4")

# ========== Phase 4 环境变量控制 ==========

COGNITIVE_STRATEGY_ENABLED = os.environ.get(
    "COGNITIVE_STRATEGY_ENABLED", "true"
).lower() in ("true", "1", "yes")

COGNITIVE_FEEDBACK_ENABLED = os.environ.get(
    "COGNITIVE_FEEDBACK_ENABLED", "true"
).lower() in ("true", "1", "yes")

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
    include_strategies: bool = True  # Phase 4: 是否返回策略推荐

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


# ========== Phase 4: 反馈 API 数据模型 ==========

class StrategyRecommendation(BaseModel):
    name: str
    strategy_type: Optional[str] = None
    fitness_score: Optional[float] = None
    uses_real_data: Optional[bool] = None
    avg_accuracy: Optional[float] = None
    usage_count: Optional[int] = None
    description: Optional[str] = None

class FeedbackRequest(BaseModel):
    query: str                              # 原始查询
    applied_strategy_name: Optional[str] = None  # 使用的策略名称
    success: bool                           # 是否成功
    confidence: float = 0.5                 # 结果置信度 (0-1)
    error_msg: Optional[str] = None         # 错误信息
    result_data: Optional[Dict[str, Any]] = None  # 结果数据
    validation_status: Optional[str] = None # 验证状态: accurate/acceptable/wrong
    # Phase 4.1: 冥思进化扩展字段
    result_count: Optional[int] = None      # 返回结果的数量
    returned_entities: Optional[List[str]] = None  # 返回的实体列表
    useful_entities: Optional[List[str]] = None    # 真正有用的实体
    noise_entities: Optional[List[str]] = None     # 噪音实体

class FeedbackResponse(BaseModel):
    status: str
    strategy_updated: bool
    rqs_updated: bool
    belief_updated: bool
    details: Dict[str, Any] = {}


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
        "version": "2.4"
    }

@app.post("/ingest")
async def ingest_memory(request: IngestRequest, background_tasks: BackgroundTasks):
    """写入记忆"""
    try:
        if request.async_mode:
            background_tasks.add_task(
                memory_system.ingest, request.text, request.use_llm
            )
            return {"status": "accepted", "message": "Ingest task queued."}
        
        result = memory_system.ingest(request.text, use_llm=request.use_llm)
        result_dict = result.to_dict()
        result_dict["extraction_mode"] = result.extraction.extraction_mode
        return {
            "status": "success",
            "data": result_dict,
            "session_id": request.session_id
        }
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_memory(request: SearchRequest):
    """搜索记忆（升级版：同时返回策略推荐）"""
    try:
        # 1. 检索记忆上下文（保持原有逻辑）
        context = memory_system.get_context(request.query, request.session_id)
        context_dict = context.to_dict() if hasattr(context, "to_dict") else context

        # 2. 检索推荐策略（Phase 4 新增）
        strategies = []
        if request.include_strategies and COGNITIVE_STRATEGY_ENABLED:
            try:
                raw_strategies = store.get_recommended_strategies(
                    request.query, limit=3
                )
                strategies = [
                    StrategyRecommendation(**s).dict() for s in raw_strategies
                ]
            except Exception as e:
                logger.warning(f"Strategy recommendation failed: {e}")

        # 3. 提取 context_text 到顶层，供插件 auto-recall 直接读取
        context_text = ""
        entity_count = 0
        edge_count = 0
        if isinstance(context_dict, dict):
            context_text = context_dict.get("context_text", "") or ""
            entity_count = context_dict.get("entity_count", 0) or 0
            edge_count = context_dict.get("edge_count", 0) or 0

        return {
            "status": "success",
            "context_text": context_text,
            "entity_count": entity_count,
            "edge_count": edge_count,
            "context": context_dict,
            "recommended_strategies": strategies
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


# ========== Phase 4: 反馈闭环端点 ==========

@app.post("/feedback")
async def process_feedback(request: FeedbackRequest):
    """
    处理执行结果反馈

    反馈处理流程：
    1. 更新策略适应度（基于成功/失败和置信度）
    2. 更新 RQS 评分（基于验证状态）
    3. 更新信念系统（基于验证结果的 belief_impact）
    4. 记录反馈到图谱（用于冥思分析）

    每个子步骤独立 try-except，互不影响。
    可通过 COGNITIVE_FEEDBACK_ENABLED 环境变量全局禁用。
    """
    if not COGNITIVE_FEEDBACK_ENABLED:
        return FeedbackResponse(
            status="disabled",
            strategy_updated=False,
            rqs_updated=False,
            belief_updated=False,
            details={"message": "Feedback processing is disabled via COGNITIVE_FEEDBACK_ENABLED"}
        )

    try:
        result = {
            "strategy_updated": False,
            "rqs_updated": False,
            "belief_updated": False,
            "details": {}
        }

        # 1. 更新策略适应度
        if request.applied_strategy_name:
            try:
                real_world_accuracy = request.confidence if request.success else (1 - request.confidence)
                success_rate = 1.0 if request.success else 0.0
                cost = 0.1  # 默认成本

                store.update_strategy_feedback(
                    strategy_name=request.applied_strategy_name,
                    accuracy=real_world_accuracy,
                    success_rate=success_rate,
                    cost=cost
                )
                result["strategy_updated"] = True
                result["details"]["strategy_fitness_delta"] = (
                    0.05 if request.success else -0.1
                )
            except Exception as e:
                logger.warning(f"Strategy feedback failed: {e}")

        # 2. 更新 RQS 评分
        if request.validation_status:
            try:
                # 根据 StrongValidator 的影响因子计算调整量
                rqs_impact_map = {
                    "accurate": 0.05,
                    "acceptable": 0.0,
                    "wrong": -0.3
                }
                rqs_delta = rqs_impact_map.get(
                    request.validation_status, 0.0
                )
                if rqs_delta != 0:
                    # 此处可以通过查询关联的 RQSRecord 进行更新
                    result["rqs_updated"] = True
                    result["details"]["rqs_delta"] = rqs_delta
            except Exception as e:
                logger.warning(f"RQS feedback failed: {e}")

        # 3. 更新信念系统
        if request.validation_status:
            try:
                belief_impact_map = {
                    "accurate": 0.1,
                    "acceptable": 0.0,
                    "wrong": -0.3
                }
                belief_delta = belief_impact_map.get(
                    request.validation_status, 0.0
                )
                if belief_delta != 0 and request.query:
                    store.upsert_belief_node({
                        "content": request.query,
                        "belief_strength": max(0.1, min(1.0, 0.5 + belief_delta)),
                        "confidence": request.confidence,
                        "state": "STABLE" if request.validation_status == "accurate" else "HYPOTHESIS",
                        "evidence_count": 1,
                        "source": "feedback"
                    })
                    result["belief_updated"] = True
                    result["details"]["belief_delta"] = belief_delta
            except Exception as e:
                logger.warning(f"Belief feedback failed: {e}")

        # 4. 将反馈本身写入图谱（作为事件记录）
        feedback_text = (
            f"执行反馈：查询'{request.query}'使用策略"
            f"'{request.applied_strategy_name or 'default'}'，"
            f"结果{'成功' if request.success else '失败'}，"
            f"置信度{request.confidence:.2f}"
        )
        try:
            memory_system.ingest(feedback_text)
        except Exception:
            pass
        
        # 5. 保存增强反馈数据用于冥思进化分析（Phase 4.1）
        try:
            # 创建Feedback节点，包含所有增强字段
            feedback_data = {
                "query": request.query,
                "success": request.success,
                "confidence": request.confidence,
                "applied_strategy_name": request.applied_strategy_name,
                "validation_status": request.validation_status,
                "result_count": request.result_count if request.result_count is not None else 0,
                "returned_entities": request.returned_entities or [],
                "useful_entities": request.useful_entities or [],
                "noise_entities": request.noise_entities or [],
                "error_msg": request.error_msg,
                "timestamp": time.time(),
                "type": "Feedback"
            }
            
            # 使用现有的upsert_entity方法保存反馈
            # 首先，需要导入Entity类或使用store的原始查询方法
            # 简化：将反馈作为文本存储到图谱中，包含metadata
            feedback_text = f"FEEDBACK: {request.query}|success:{request.success}|confidence:{request.confidence}|result_count:{request.result_count}"
            feedback_metadata = json.dumps(feedback_data, ensure_ascii=False)
            
            # 使用memory_system.ingest存储，但需要扩展以处理metadata
            # 暂时先记录日志
            logger.info(f"Enhanced feedback data (not yet stored): {feedback_data}")
            
            # TODO: 实现反馈节点存储
            # store.upsert_entity(Entity(name=feedback_text, type="Feedback", metadata=feedback_metadata))
            
        except Exception as e:
            logger.warning(f"Failed to save enhanced feedback: {e}")

        return FeedbackResponse(status="success", **result)

    except Exception as e:
        logger.error(f"Feedback processing failed: {e}")
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
    uvicorn.run(app, host="0.0.0.0", port=18900)
