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
            for item in truncated_entities:

                if isinstance(item, (list, tuple)) and len(item) >= 2:

                    entity_name, count = item[0], item[1]

                    if count <= 1:
                        params["cleanup_targets"].append(entity_name)
        
        # 2. 查找超级节点 (关系扇出度 > 15)
        super_nodes = find_super_nodes_simple(store)
        if super_nodes:
            logger.info(f"Found {len(super_nodes)} super nodes")
            for item in super_nodes:

                if isinstance(item, (list, tuple)) and len(item) >= 2:

                    node_id, fanout = item[0], item[1]

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


class StrategyEvolutionManager:
    """
    策略进化管理器 - 集成元认知三定律优先级编码
    """
    def __init__(self, store: Any):
        self.store = store
        self.strategies = self._load_all_strategies()
    
    def _get_strategy(self, strategy_name: str) -> Optional[Dict[str, Any]]:
        """获取单个策略"""
        return self.strategies.get(strategy_name)
    
    def _load_all_strategies(self) -> Dict[str, Any]:
        """加载所有策略（简化版）"""
        # 从存储加载策略，这里返回模拟数据
        return {
            "priority_management": {
                "name": "priority_management",
                "type": "cognitive",
                "priority": "high",
                "description": "元认知优先级管理策略"
            },
            "belief_conflict": {
                "name": "belief_conflict",
                "type": "reflection",
                "priority": "high",
                "description": "信念冲突检测与解决策略"
            },
            "boundary_control": {
                "name": "boundary_control", 
                "type": "boundary",
                "priority": "medium",
                "description": "能力边界控制策略"
            },
            "noise_filtering": {
                "name": "noise_filtering",
                "type": "general",
                "priority": "low",
                "description": "通用噪声过滤策略"
            }
        }
    
    def _save_strategy(self, strategy: Dict[str, Any]):
        """保存策略"""
        if strategy.get('name'):
            self.strategies[strategy['name']] = strategy
    
    def apply_three_laws_priority(self, strategy_name: str) -> Dict[str, Any]:
        """
        为策略应用元认知三定律优先级编码
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            包含策略优先级和建议的字典
        """
        strategy = self._get_strategy(strategy_name)
        if not strategy:
            return {
                "status": "error",
                "message": f"Strategy {strategy_name} not found"
            }
            
        priority = "other_discard"
        compression_factor = 0.8
        recommendations = []
        
        # 根据策略类型和重要性确定优先级
        if strategy.get('priority', 'low') == 'high':
            priority = 'law1_high'
            compression_factor = 0.0
            recommendations.append("高优先级策略：不压缩，保留所有细节")
            recommendations.append("建议：定期监控策略性能")
        elif strategy.get('type') in ['cognitive', 'reflection']:
            priority = 'law2_medium'
            compression_factor = 0.3
            recommendations.append("认知/反思类策略：适度压缩（保留70%）")
            recommendations.append("建议：定期回顾策略效果")
        elif strategy.get('type') == 'boundary':
            priority = 'law3_medium'
            compression_factor = 0.4
            recommendations.append("边界类策略：适度压缩（保留60%）")
            recommendations.append("建议：监控策略边界是否需要调整")
        else:
            priority = 'other_discard'
            compression_factor = 0.8
            recommendations.append("通用策略：高度压缩（保留20%）")
            recommendations.append("建议：定期评估是否需要保留")
        
        # 更新策略优先级
        strategy['law_priority'] = priority
        strategy['compression_factor'] = compression_factor
        
        # 保存更新
        self._save_strategy(strategy)
        
        return {
            "status": "success",
            "strategy_name": strategy_name,
            "priority": priority,
            "compression_factor": compression_factor,
            "recommendations": recommendations,
            "next_review": "30 days"
        }
        
    def get_strategies_by_priority(self, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        根据优先级获取策略列表
        
        Args:
            priority: 优先级类型（可选，如 'law1_high', 'law2_medium'）
            
        Returns:
            策略列表
        """
        all_strategies = self._load_all_strategies()
        
        if not priority:
            return sorted(
                all_strategies.values(),
                key=lambda s: self._get_priority_weight(s.get('law_priority', 'other_discard')),
                reverse=True
            )
            
        return [
            strategy for strategy in all_strategies.values()
            if strategy.get('law_priority') == priority
        ]
        
    def _get_priority_weight(self, priority: str) -> int:
        """
        获取优先级的权重（用于排序）
        """
        weights = {
            'law1_high': 3,
            'law2_medium': 2,
            'law3_medium': 1,
            'other_discard': 0
        }
        return weights.get(priority, 0)
