"""
冥思状态持久化模块（Issue #46）

实现冥思进度持久化，支持中断恢复：
  1. 冥思进度持久化（JSON 文件）
  2. 幂等性设计（节点不重复处理）
  3. 中断后恢复机制
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MeditationStatus(Enum):
    """冥思状态枚举"""
    PENDING = "pending"  # 等待开始
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    INTERRUPTED = "interrupted"  # 中断


@dataclass
class StepStats:
    """步骤统计"""
    step_num: int
    processed: int = 0
    pruned: int = 0
    merged: int = 0
    relabeled: int = 0
    enriched: int = 0
    weighted: int = 0
    distilled: int = 0
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "step_num": self.step_num,
            "processed": self.processed,
            "pruned": self.pruned,
            "merged": self.merged,
            "relabeled": self.relabeled,
            "enriched": self.enriched,
            "weighted": self.weighted,
            "distilled": self.distilled
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'StepStats':
        return cls(
            step_num=data.get("step_num", 0),
            processed=data.get("processed", 0),
            pruned=data.get("pruned", 0),
            merged=data.get("merged", 0),
            relabeled=data.get("relabeled", 0),
            enriched=data.get("enriched", 0),
            weighted=data.get("weighted", 0),
            distilled=data.get("distilled", 0)
        )


@dataclass
class MeditationState:
    """冥思状态数据类"""
    # 基本信息
    run_id: str
    started_at: str
    updated_at: str
    status: str  # MeditationStatus 的值
    
    # 当前进度
    current_step: int = 0
    total_steps: int = 6
    
    # 已处理节点 ID 集合（用于幂等性）
    processed_nodes: Dict[int, Set[str]] = field(default_factory=dict)
    
    # 各步骤统计
    step_stats: Dict[int, Dict[str, int]] = field(default_factory=dict)
    
    # 错误信息
    errors: List[str] = field(default_factory=list)
    
    # 元数据
    version: str = "1.0"
    config_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        # 将 Set 转换为 List 以便 JSON 序列化
        processed_nodes_serializable = {
            str(step): list(node_ids) 
            for step, node_ids in self.processed_nodes.items()
        }
        
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "processed_nodes": processed_nodes_serializable,
            "step_stats": self.step_stats,
            "errors": self.errors,
            "version": self.version,
            "config_hash": self.config_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeditationState':
        """从字典创建"""
        # 将 List 转换回 Set
        processed_nodes = {
            int(step): set(node_ids) 
            for step, node_ids in data.get("processed_nodes", {}).items()
        }
        
        return cls(
            run_id=data["run_id"],
            started_at=data["started_at"],
            updated_at=data["updated_at"],
            status=data["status"],
            current_step=data.get("current_step", 0),
            total_steps=data.get("total_steps", 6),
            processed_nodes=processed_nodes,
            step_stats=data.get("step_stats", {}),
            errors=data.get("errors", []),
            version=data.get("version", "1.0"),
            config_hash=data.get("config_hash", "")
        )
    
    @classmethod
    def create_new(cls, run_id: str) -> 'MeditationState':
        """创建新的冥思状态"""
        now = datetime.now().isoformat()
        return cls(
            run_id=run_id,
            started_at=now,
            updated_at=now,
            status=MeditationStatus.PENDING.value,
            processed_nodes={},
            step_stats={}
        )


class MeditationStateManager:
    """
    冥思状态管理器
    
    负责：
    - 状态持久化（JSON 文件）
    - 幂等性检查（节点不重复处理）
    - 中断恢复
    """
    
    def __init__(self, state_dir: str = "/tmp/meditation_states"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.current_state: Optional[MeditationState] = None
    
    def create_state(self, run_id: str) -> MeditationState:
        """创建新的冥思状态"""
        self.current_state = MeditationState.create_new(run_id)
        self.save()
        logger.info(f"创建冥思状态：{run_id}")
        return self.current_state
    
    def load_state(self, run_id: str) -> Optional[MeditationState]:
        """加载指定的冥思状态"""
        state_file = self.state_dir / f"{run_id}.json"
        
        if not state_file.exists():
            logger.warning(f"状态文件不存在：{state_file}")
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_state = MeditationState.from_dict(data)
            logger.info(f"加载冥思状态：{run_id} (step={self.current_state.current_step})")
            return self.current_state
            
        except Exception as e:
            logger.error(f"加载状态文件失败：{e}")
            return None
    
    def save(self) -> bool:
        """保存当前状态（原子写入）"""
        if not self.current_state:
            logger.error("没有当前状态可保存")
            return False
        
        # 更新更新时间
        self.current_state.updated_at = datetime.now().isoformat()
        
        # 原子写入：先写临时文件，再重命名
        state_file = self.state_dir / f"{self.current_state.run_id}.json"
        temp_file = state_file.with_suffix('.tmp')
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_state.to_dict(), f, indent=2, ensure_ascii=False)
            
            # 重命名临时文件为正式文件
            temp_file.rename(state_file)
            logger.debug(f"保存冥思状态：{self.current_state.run_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存状态文件失败：{e}")
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    def update_status(self, status) -> None:
        """更新冥思状态"""
        if self.current_state:
            if isinstance(status, MeditationStatus):
                self.current_state.status = status.value
            else:
                self.current_state.status = str(status)
            self.save()
    
    def update_step(self, step_num: int) -> None:
        """更新当前步骤"""
        if self.current_state:
            self.current_state.current_step = step_num
            
            # 初始化步骤统计
            if step_num not in self.current_state.step_stats:
                self.current_state.step_stats[step_num] = StepStats(step_num=step_num).to_dict()
            
            self.save()
    
    def mark_node_processed(self, step_num: int, node_id: str) -> None:
        """标记节点已处理（幂等性）"""
        if self.current_state:
            if step_num not in self.current_state.processed_nodes:
                self.current_state.processed_nodes[step_num] = set()
            
            self.current_state.processed_nodes[step_num].add(node_id)
            # 定期保存（可以优化为批量保存）
    
    def is_node_processed(self, step_num: int, node_id: str) -> bool:
        """检查节点是否已处理"""
        if not self.current_state:
            return False
        
        processed = self.current_state.processed_nodes.get(step_num, set())
        return node_id in processed
    
    def get_unprocessed_nodes(self, step_num: int, all_nodes: List[str]) -> List[str]:
        """获取未处理的节点列表"""
        if not self.current_state:
            return all_nodes
        
        processed = self.current_state.processed_nodes.get(step_num, set())
        return [n for n in all_nodes if n not in processed]
    
    def update_step_stats(self, step_num: int, stats: Dict[str, int]) -> None:
        """更新步骤统计"""
        if self.current_state:
            self.current_state.step_stats[step_num] = stats
            self.save()
    
    def add_error(self, error: str) -> None:
        """添加错误信息"""
        if self.current_state:
            self.current_state.errors.append(error)
            self.save()
    
    def get_incomplete_states(self) -> List[MeditationState]:
        """获取所有未完成的冥思状态"""
        incomplete = []
        
        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                state = MeditationState.from_dict(data)
                if state.status in [MeditationStatus.IN_PROGRESS.value, MeditationStatus.INTERRUPTED.value]:
                    incomplete.append(state)
                    
            except Exception as e:
                logger.error(f"读取状态文件失败 {state_file}: {e}")
        
        return incomplete
    
    def cleanup_old_states(self, days: int = 7) -> int:
        """清理旧的状态文件"""
        cleaned = 0
        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        
        for state_file in self.state_dir.glob("*.json"):
            try:
                mtime = state_file.stat().st_mtime
                if mtime < cutoff:
                    # 只清理已完成或失败的状态
                    with open(state_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    status = data.get("status", "")
                    if status in [MeditationStatus.COMPLETED.value, MeditationStatus.FAILED.value]:
                        state_file.unlink()
                        cleaned += 1
                        logger.debug(f"清理旧状态文件：{state_file}")
                        
            except Exception as e:
                logger.error(f"清理状态文件失败 {state_file}: {e}")
        
        logger.info(f"清理了 {cleaned} 个旧状态文件")
        return cleaned
    
    def get_state_file_path(self, run_id: str) -> Path:
        """获取状态文件路径"""
        return self.state_dir / f"{run_id}.json"
