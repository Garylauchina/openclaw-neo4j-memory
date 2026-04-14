#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path


def log(msg: str):
    print(f"[meditation-worker] {msg}", flush=True)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from meditation_memory.graph_store import GraphStore
from meditation_memory.meditation_config import MeditationConfig
from meditation_memory.meditation_worker import MeditationEngine
from meditation_memory.config import MemoryConfig

STATUS_PATH = Path(os.environ.get("MEDITATION_STATUS_PATH", "/tmp/openclaw-meditation-status.json"))
HISTORY_PATH = Path(os.environ.get("MEDITATION_HISTORY_PATH", "/tmp/openclaw-meditation-history.json"))
LOCK_PATH = Path(os.environ.get("MEDITATION_LOCK_PATH", "/tmp/openclaw-meditation.lock"))


def write_status(payload):
    STATUS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def append_history(payload):
    history = []
    if HISTORY_PATH.exists():
        try:
            history = json.loads(HISTORY_PATH.read_text())
        except Exception:
            history = []
    history.append(payload)
    history = history[-100:]
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="auto")
    parser.add_argument("--target-nodes", default="")
    args = parser.parse_args()

    log(f"starting mode={args.mode}")
    if LOCK_PATH.exists():
        write_status({
            "status": "error",
            "message": "Meditation worker already running.",
            "heartbeat_at": time.time(),
        })
        return 1

    LOCK_PATH.write_text(str(os.getpid()))

    try:
        memory_config = MemoryConfig()
        store = GraphStore(memory_config.neo4j)
        meditation_config = MeditationConfig()
        engine = MeditationEngine(store, meditation_config)

        target_nodes = [n for n in args.target_nodes.split(",") if n] if args.target_nodes else None

        started_at = time.time()
        write_status({
            "status": "running",
            "current_step": "initializing",
            "started_at": started_at,
            "heartbeat_at": started_at,
            "dry_run": args.mode == "dry_run",
        })

        task = asyncio.create_task(
            asyncio.to_thread(
                lambda: asyncio.run(engine.run_meditation(mode=args.mode, target_nodes=target_nodes))
            )
        )

        def _log_task_done(t: asyncio.Task):
            try:
                exc = t.exception()
                if exc is not None:
                    log(f"task done with exception: {exc}")
                else:
                    log("task done successfully")
            except asyncio.CancelledError:
                log("task cancelled")
            except Exception as cb_exc:
                log(f"task done callback failed: {cb_exc}")

        task.add_done_callback(_log_task_done)

        while not task.done():
            await asyncio.sleep(1)
            current = getattr(engine, "_current_result", None)
            if current is not None:
                payload = current.to_dict()
                payload["heartbeat_at"] = time.time()
                write_status(payload)
            else:
                write_status({
                    "status": "running",
                    "current_step": "initializing",
                    "started_at": started_at,
                    "heartbeat_at": time.time(),
                    "dry_run": args.mode == "dry_run",
                })

        result = await task
        payload = result.to_dict()
        payload["heartbeat_at"] = time.time()
        write_status(payload)
        append_history(payload)
        return 0
    except Exception as e:
        log(f"failed: {e}")
        payload = {
            "status": "failed",
            "error": str(e),
            "heartbeat_at": time.time(),
        }
        write_status(payload)
        append_history(payload)
        return 1
    finally:
        try:
            LOCK_PATH.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
