"""
冥思调度器 (Meditation Scheduler)

负责根据配置触发冥思引擎：
  1. 定时触发 (Slow-wave Sleep): 每日固定时间执行。
  2. 条件触发 (REM Sleep): 监测图谱变化量（节点/关系新增数）超过阈值时触发。

使用异步循环进行监测。
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

from .graph_store import GraphStore
from .meditation_worker import MeditationEngine
from .meditation_config import MeditationConfig

logger = logging.getLogger("meditation.scheduler")


class MeditationScheduler:
    """
    冥思任务调度器
    """

    def __init__(
        self,
        engine: MeditationEngine,
        store: GraphStore,
        config: Optional[MeditationConfig] = None
    ):
        self.engine = engine
        self.store = store
        self.config = config or MeditationConfig()
        self._last_run_time: float = 0
        self._last_check_timestamp_ms: int = int(time.time() * 1000)
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """启动调度器循环（含启动时补跑检查）"""
        if self._is_running:
            return
        self._is_running = True
        # 启动时检查：如果今天还没运行过定时任务，且当前时间已过调度窗口，立即补跑
        await self._catch_up_on_startup()
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Meditation scheduler started.")

    async def stop(self):
        """停止调度器循环"""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Meditation scheduler stopped.")

    async def _catch_up_on_startup(self):
        """启动时补跑检查：如果今天没跑过且当前时间已过调度窗口，立即补跑一次。"""
        now = datetime.now()
        cron_parts = self.config.trigger.cron_schedule.split()
        if len(cron_parts) >= 2:
            target_hour = int(cron_parts[1])
            # 如果当前时间已过今天的调度小时，且超过 180 分钟内没跑过
            if now.hour >= target_hour and (time.time() - self._last_run_time) > 180:
                logger.info(f"Startup catch-up: scheduled time was {target_hour}:00, now {now.hour}:{now.minute:02d}. Running now.")
                await self._trigger_run("startup_catchup")

    async def _scheduler_loop(self):
        """主调度循环"""
        while self._is_running:
            try:
                await self._check_and_trigger()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

            # 每分钟检查一次
            await asyncio.sleep(60)

    async def _check_and_trigger(self):
        """检查是否满足触发条件"""
        if not self.config.enabled:
            return

        now = time.time()
        # 检查最小间隔
        if now - self._last_run_time < self.config.trigger.min_interval_seconds:
            return

        dt_now = datetime.now()
        # 定时触发：使用 ±1 分钟窗口，避免服务重启错过精确时刻
        cron_parts = self.config.trigger.cron_schedule.split()
        if len(cron_parts) >= 2:
            target_min = int(cron_parts[0])
            target_hour = int(cron_parts[1])
            if (dt_now.hour == target_hour and
                abs(dt_now.minute - target_min) <= 1 and
                (now - self._last_run_time) > 120):
                logger.info(f"Cron schedule triggered meditation ({target_hour}:{target_min:02d}).")
                await self._trigger_run("scheduled")
                return

        # 2. 检查条件触发 (变化量阈值)
        changes = self.store.get_change_counts_since(self._last_check_timestamp_ms)
        new_nodes = changes.get("new_nodes", 0)
        new_edges = changes.get("new_edges", 0)

        if (new_nodes >= self.config.trigger.trigger_node_threshold or
            new_edges >= self.config.trigger.trigger_edge_threshold):
            logger.info(f"Change threshold triggered meditation (nodes: {new_nodes}, edges: {new_edges}).")
            await self._trigger_run("conditional")

    async def _trigger_run(self, trigger_type: str):
        """执行冥思"""
        logger.info(f"Triggering meditation run (type: {trigger_type})...")
        try:
            # 更新状态
            self._last_run_time = time.time()
            self._last_check_timestamp_ms = int(time.time() * 1000)

            # 运行引擎
            result = await self.engine.run_meditation(mode="auto")
            logger.info(f"Meditation run finished. Status: {result.status}")
        except Exception as e:
            logger.error(f"Failed to run triggered meditation: {e}")


async def main():
    """本地运行调度器测试"""
    logging.basicConfig(level=logging.INFO)
    store = GraphStore()
    engine = MeditationEngine(store)
    scheduler = MeditationScheduler(engine, store)

    print("Starting scheduler... (Ctrl+C to stop)")
    await scheduler.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await scheduler.stop()
        store.close()

if __name__ == "__main__":
    asyncio.run(main())
