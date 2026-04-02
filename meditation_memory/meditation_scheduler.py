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
        """启动调度器循环"""
        if self._is_running:
            return
        self._is_running = True
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

        # 1. 检查定时触发 (简单实现：检查小时和分钟)
        # 默认 "0 3 * * *" -> 凌晨 3 点
        cron_parts = self.config.trigger.cron_schedule.split()
        if len(cron_parts) >= 2:
            target_min = int(cron_parts[0])
            target_hour = int(cron_parts[1])
            dt_now = datetime.now()
            if dt_now.hour == target_hour and dt_now.minute == target_min:
                logger.info("Cron schedule triggered meditation.")
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
