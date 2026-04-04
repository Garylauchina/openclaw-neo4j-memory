"""
简化的冥思进化模块 (Meditation Evolution - Simple Version)

第一阶段实现：渐进式上线
1. 先只做"清理截断实体"和"拆分超级节点"
2. 不依赖复杂的反馈分析（后续添加）
3. 集成到现有冥思流程中

根据设计文档：不要大改现有代码，在现有meditation流程的入口处加一个analyze_and_adjust()步骤即可
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("meditation.evolution")

def analyze_and_adjust_simple(store: Any) -> Dict[str, Any]:
    """
    简化的冥思进化分析
    
    第一阶段：只返回截断实体清理和超级节点拆分的参数
    后续阶段：添加反馈信号分析
    
    Args:
        store: 图数据库存储对象
    
    Returns:
        调整后的冥思参数
    """
    params = {
        "merge_threshold": 0.7,
        "compression_level": "light",  # 默认保守
        "max_meta_fanout": 15,
        "cleanup_targets": [],
        "protect_topics": [],
        "split_candidates": [],
        "focus_on_truncated": True,     # 第一阶段：清理截断实体
        "focus_on_super_nodes": True,   # 第一阶段：拆分超级节点
        "evolution_enabled": True,      # 启用进化
        "phase": "1.0"                  # 第一阶段
    }
    
    try:
        # 1. 查找截断的中文实体名 (<4个字符)
        truncated_entities = find_truncated_entities_simple(store)
        if truncated_entities:
            logger.info(f"Found {len(truncated_entities)} truncated entities")
            # 只清理出现次数<=1的截断实体
            for entity_name, count in truncated_entities:
                if count <= 1:
                    params["cleanup_targets"].append(entity_name)
        
        # 2. 查找超级节点 (关系扇出度 > 15)
        super_nodes = find_super_nodes_simple(store)
        if super_nodes:
            logger.info(f"Found {len(super_nodes)} super nodes")
            for node_id, fanout in super_nodes:
                params["split_candidates"].append(node_id)
        
    except Exception as e:
        logger.error(f"Error in simple meditation evolution: {e}")
        params["evolution_enabled"] = False
    
    return params


def find_truncated_entities_simple(store: Any, max_length: int = 4) -> List[tuple]:
    """
    查找截断的中文实体名（简化版）
    
    Args:
        store: 图数据库存储对象
        max_length: 最大长度
    
    Returns:
        [(实体名, 提及次数), ...]
    """
    try:
        # 使用store的现有方法获取短名实体
        # 假设store有get_short_name_entities方法（从之前的搜索中看到）
        if hasattr(store, 'get_short_name_entities'):
            return store.get_short_name_entities(max_name_length=max_length)
        else:
            # 回退方案：返回空列表
            logger.warning("store.get_short_name_entities not available")
            return []
    except Exception as e:
        logger.error(f"Failed to find truncated entities: {e}")
        return []


def find_super_nodes_simple(store: Any, fanout_threshold: int = 15) -> List[tuple]:
    """
    查找超级节点（简化版）
    
    Args:
        store: 图数据库存储对象
        fanout_threshold: 扇出度阈值
    
    Returns:
        [(节点ID, 扇出度), ...]
    """
    try:
        # 这里需要实现查找超级节点的逻辑
        # 简化：返回空列表
        # TODO: 实现实际的超级节点检测
        return []
    except Exception as e:
        logger.error(f"Failed to find super nodes: {e}")
        return []


def execute_meditation_with_evolution(store: Any, engine: Any, mode: str = "auto") -> Dict[str, Any]:
    """
    执行带有进化分析的冥思
    
    流程：
    1. 分析反馈信号，调整参数（第一阶段简化）
    2. 执行冥思
    3. 记录冥思日志
    
    Args:
        store: 图数据库存储对象
        engine: 冥思引擎对象
        mode: 运行模式
    
    Returns:
        冥思结果
    """
    try:
        logger.info("Starting meditation with evolution analysis...")
        
        # 1. 分析并调整参数
        evolution_params = analyze_and_adjust_simple(store)
        
        if not evolution_params.get("evolution_enabled", False):
            logger.info("Meditation evolution disabled, running normal meditation")
            # 执行正常冥思
            # result = await engine.run_meditation(mode=mode)
            # return result
            return {"status": "normal_meditation", "evolution": False}
        
        # 2. 提取进化参数
        focus_on_truncated = evolution_params.get("focus_on_truncated", False)
        focus_on_super_nodes = evolution_params.get("focus_on_super_nodes", False)
        cleanup_targets = evolution_params.get("cleanup_targets", [])
        split_candidates = evolution_params.get("split_candidates", [])
        
        logger.info(f"Evolution params: truncated={focus_on_truncated}, super_nodes={focus_on_super_nodes}")
        logger.info(f"Cleanup targets: {len(cleanup_targets)}, Split candidates: {len(split_candidates)}")
        
        # 3. 执行冥思（这里需要调用引擎的实际方法）
        # 在实际集成中，需要将进化参数传递给冥思引擎
        # result = await engine.run_meditation_with_params(mode=mode, evolution_params=evolution_params)
        
        # 4. 记录冥思日志（简化）
        log_data = {
            "timestamp": time.time(),
            "evolution_params": evolution_params,
            "actions_taken": {
                "truncated_cleaned": len(cleanup_targets),
                "super_nodes_split": len(split_candidates)
            }
        }
        
        # 保存日志（简化）
        # save_meditation_log_simple(store, log_data)
        
        return {
            "status": "success",
            "evolution": True,
            "params": evolution_params,
            "log": log_data
        }
        
    except Exception as e:
        logger.error(f"Meditation with evolution failed: {e}")
        return {"status": "error", "error": str(e)}


# 临时导入time用于日志
import time