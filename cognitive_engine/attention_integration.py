#!/usr/bin/env python3
"""
Attention Layer Integration（注意力层整合）
将注意力机制接入现有记忆系统。
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class AttentionIntegration:
    """注意力层整合器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.attention_layer = None
        self._initialized = False
        
    def initialize(self):
        """初始化注意力层（懒加载）"""
        if self._initialized:
            return True
            
        try:
            # 尝试导入注意力层
            from attention_layer.attention_layer import AttentionLayer
            from attention_layer.attention_scorer import AttentionScorer
            from attention_layer.attention_state import AttentionState
            
            logger.info("Attention layer modules imported successfully")
            
            # 创建默认配置
            attention_config = {
                'relevance_weight': 0.25,
                'belief_weight': 0.20,
                'recency_weight': 0.15,
                'rqs_weight': 0.15,
                'novelty_weight': 0.15,
                'conflict_weight': 0.10,
                'top_k': 20,
                'min_score': 0.1,
                'enable_feedback': True
            }
            
            # 合并用户配置
            if self.config:
                attention_config.update(self.config)
                
            # 创建注意力层实例
            self.attention_layer = AttentionLayer(attention_config)
            self._initialized = True
            logger.info("Attention layer initialized successfully")
            return True
            
        except ImportError as e:
            logger.warning(f"Cannot import attention layer: {e}. Attention features will be disabled.")
            return False
        except Exception as e:
            logger.error(f"Error initializing attention layer: {e}")
            return False
    
    def score_entity(self, entity_name: str, context: Optional[Dict[str, Any]] = None) -> float:
        """
        为实体计算注意力分数
        
        Args:
            entity_name: 实体名称
            context: 上下文信息（mention_count, recency, relationships等）
            
        Returns:
            注意力分数 (0-1)，如果注意力层不可用则返回默认值0.5
        """
        if not self.initialize() or not self.attention_layer:
            return 0.5  # 默认中等分数
            
        try:
            # 准备注意力状态
            attention_state = {
                'entity_name': entity_name,
                'timestamp': datetime.now().isoformat(),
                'context': context or {}
            }
            
            # 计算分数
            score = self.attention_layer.score_entity(attention_state)
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error scoring entity {entity_name}: {e}")
            return 0.5
    
    def select_top_entities(self, entities: List[str], context_list: List[Dict[str, Any]] = None, 
                           top_k: int = 10) -> List[Tuple[str, float]]:
        """
        从实体列表中选择注意力分数最高的实体
        
        Args:
            entities: 实体名称列表
            context_list: 每个实体的上下文信息列表（可选）
            top_k: 返回的实体数量
            
        Returns:
            排序后的(实体, 分数)列表
        """
        if not self.initialize() or not self.attention_layer:
            # 如果没有注意力层，返回原始列表（带默认分数）
            return [(entity, 0.5) for entity in entities[:top_k]]
            
        try:
            if context_list is None:
                context_list = [{}] * len(entities)
                
            # 计算所有实体的分数
            scored_entities = []
            for entity, context in zip(entities, context_list):
                score = self.score_entity(entity, context)
                scored_entities.append((entity, score))
                
            # 按分数排序
            scored_entities.sort(key=lambda x: x[1], reverse=True)
            return scored_entities[:top_k]
            
        except Exception as e:
            logger.error(f"Error selecting top entities: {e}")
            return [(entity, 0.5) for entity in entities[:top_k]]
    
    def update_feedback(self, entity_name: str, success: bool, 
                       confidence: float = 1.0, context: Optional[Dict[str, Any]] = None):
        """
        更新注意力反馈（当实体被成功使用时）
        
        Args:
            entity_name: 实体名称
            success: 是否成功使用
            confidence: 置信度 (0-1)
            context: 上下文信息
        """
        if not self.initialize() or not self.attention_layer:
            return
            
        try:
            self.attention_layer.update_feedback(
                entity_name=entity_name,
                success=success,
                confidence=confidence,
                context=context or {}
            )
            logger.debug(f"Attention feedback updated for {entity_name}: success={success}")
        except Exception as e:
            logger.error(f"Error updating attention feedback for {entity_name}: {e}")


# 全局实例（懒加载）
_global_attention_integration = None

def get_attention_integration(config: Optional[Dict[str, Any]] = None) -> AttentionIntegration:
    """获取全局注意力整合器实例"""
    global _global_attention_integration
    if _global_attention_integration is None:
        _global_attention_integration = AttentionIntegration(config)
    return _global_attention_integration