"""
自我进化的冥思系统 (Meditation Evolution System)

根据设计文档 https://github.com/Garylauchina/openclaw-neo4j-memory/blob/main/docs/meditation_evolution_design.md 实现。
在现有冥思流程的入口处添加 analyze_and_adjust() 步骤，使冥思系统能够根据反馈信号自我进化。

核心架构：
    用户对话 → auto_ingest(写入记忆) → 图谱
     ↓
    用户提问 → auto_search(检索记忆) → 返回结果 → agent使用
     ↓
    feedback(好/坏)
     ↓
    feedback_log(积累)
     ↓
    定时冥思 ← 读取feedback → 调整策略 → 整理图谱
     ↓
    冥思日志(记录本次效果)
     ↓
    下次冥思读取上次日志 → 继续进化

实现步骤：
    1. 扩展 /feedback 接口，增加 returned_entities 和 noise_entities 字段
    2. 新增 meditation_log 存储机制
    3. 在冥思入口添加 analyze_and_adjust() 步骤
    4. 渐进式上线：先只做"清理截断实体"和"拆分超级节点"
"""

import logging
import time
import json
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import os

logger = logging.getLogger("meditation.evolution")

# ============================================================================
# 第一步：扩展的反馈数据结构
# ============================================================================

class EnhancedFeedback:
    """扩展的反馈数据结构，支持冥思进化分析"""
    
    def __init__(
        self,
        query: str,
        success: bool,
        confidence: float = 0.5,
        result_count: int = 0,
        returned_entities: Optional[List[str]] = None,
        useful_entities: Optional[List[str]] = None,
        noise_entities: Optional[List[str]] = None,
        applied_strategy_name: Optional[str] = None,
        validation_status: Optional[str] = None,
        timestamp: Optional[float] = None
    ):
        self.query = query
        self.success = success
        self.confidence = confidence
        self.result_count = result_count
        self.returned_entities = returned_entities or []
        self.useful_entities = useful_entities or []
        self.noise_entities = noise_entities or []
        self.applied_strategy_name = applied_strategy_name
        self.validation_status = validation_status
        self.timestamp = timestamp or time.time()
    
    @classmethod
    def from_api_request(cls, data: Dict[str, Any]) -> "EnhancedFeedback":
        """从API请求数据创建增强反馈对象"""
        return cls(
            query=data.get("query", ""),
            success=data.get("success", False),
            confidence=data.get("confidence", 0.5),
            result_count=data.get("result_count", 0),
            returned_entities=data.get("returned_entities", []),
            useful_entities=data.get("useful_entities", []),
            noise_entities=data.get("noise_entities", []),
            applied_strategy_name=data.get("applied_strategy_name"),
            validation_status=data.get("validation_status"),
            timestamp=data.get("timestamp", time.time())
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "query": self.query,
            "success": self.success,
            "confidence": self.confidence,
            "result_count": self.result_count,
            "returned_entities": self.returned_entities,
            "useful_entities": self.useful_entities,
            "noise_entities": self.noise_entities,
            "applied_strategy_name": self.applied_strategy_name,
            "validation_status": self.validation_status,
            "timestamp": self.timestamp
        }


# ============================================================================
# 第二步：反馈信号分析
# ============================================================================

def analyze_feedback_signals(feedbacks: List[EnhancedFeedback], 
                           graph_store: Any) -> Dict[str, Any]:
    """
    分析反馈信号，识别记忆系统的状态
    
    Args:
        feedbacks: 增强的反馈列表
        graph_store: 图数据库存储对象，用于获取话题实体
    
    Returns:
        信号分析结果字典：
        {
            "empty_queries": ["MCP Server", "认知闭环", ...],  # 搜了但返回空的查询
            "noisy_queries": ["OpenClaw模型配置", ...],        # 搜了但feedback=负面的查询
            "useful_entities": {"OpenClaw": 5, "冥思": 3, ...}, # 出现在正面feedback中的实体及出现次数
            "useless_entities": {"弹道导弹目标": 2, ...},       # 出现在负面feedback中的实体及出现次数
            "hot_topics": ["模型配置", "记忆系统"],             # 高频查询的话题
            "cold_topics": ["比特币价格"],                     # 长期未被查询的话题
            "overall_satisfaction": 0.35,                      # 总体满意度 (0-1)
        }
    """
    empty_queries = []
    noisy_queries = []
    useful_entities = Counter()
    useless_entities = Counter()
    topic_frequency = Counter()
    
    for fb in feedbacks:
        # 统计话题频率
        topic_frequency[fb.query] += 1
        
        # 空查询：结果数量为0
        if fb.result_count == 0:
            empty_queries.append(fb.query)
        
        # 噪音查询：结果不为空但反馈为负面
        elif fb.success == False and fb.result_count > 0:
            noisy_queries.append(fb.query)
            for entity in fb.returned_entities:
                useless_entities[entity] += 1
        
        # 成功查询：结果不为空且反馈为正面
        elif fb.success == True and fb.result_count > 0:
            for entity in fb.returned_entities:
                # 如果实体在useful_entities列表中，计数加1
                if entity in fb.useful_entities:
                    useful_entities[entity] += 1
                # 如果实体在noise_entities列表中，计数加1到无用实体
                elif entity in fb.noise_entities:
                    useless_entities[entity] += 1
    
    # 识别热门话题 (前10个)
    hot_topics = [topic for topic, count in topic_frequency.most_common(10)]
    
    # 识别冷门话题 (需要graph_store获取所有话题实体)
    # 这里简化实现：获取最近30天未被查询的话题
    thirty_days_ago = time.time() - (30 * 24 * 60 * 60)
    cold_topics = []
    # 注意：这个实现需要graph_store的get_all_topic_entities方法
    # 暂时返回空列表，后续集成时补充
    
    # 计算总体满意度
    successful_feedbacks = [f for f in feedbacks if f.success]
    overall_satisfaction = len(successful_feedbacks) / max(len(feedbacks), 1)
    
    return {
        "empty_queries": empty_queries,
        "noisy_queries": noisy_queries,
        "useful_entities": dict(useful_entities),
        "useless_entities": dict(useless_entities),
        "hot_topics": hot_topics,
        "cold_topics": cold_topics,
        "overall_satisfaction": overall_satisfaction
    }


# ============================================================================
# 第三步：冥思参数动态调整
# ============================================================================

def adjust_meditation_params(signals: Dict[str, Any], 
                           last_log: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    根据反馈信号动态调整冥思参数
    
    7条核心规则：
    1. 满意度低 → 保守整理，少压缩
    2. 空查询多 → 说明记忆写入不足或被过度压缩
    3. 噪音查询多 → 需要清理无用实体和泛化关系
    4. 热门话题 → 保护其实体，不要合并或压缩
    5. 冷门话题 → 可以更激进地压缩
    6. 检查上次冥思的效果 → 如果没有降低通用关系比例，这次更激进
    7. META超级节点检测 → 拆分扇出度过高的节点
    
    Args:
        signals: 分析得到的反馈信号
        last_log: 上次冥思的日志记录
    
    Returns:
        调整后的冥思参数：
        {
            "merge_threshold": 0.7,               # 实体合并的相似度阈值
            "compression_level": "light",         # 压缩程度: light/medium/aggressive
            "max_meta_fanout": 15,                # META节点最大关系扇出度
            "cleanup_targets": [...],             # 本次要清理的垃圾实体列表
            "protect_topics": [...],              # 本次要保护(不压缩)的话题
            "split_candidates": [...],            # 需要拆分的超级节点
            "focus_on_truncated": True,           # 是否聚焦清理截断实体（渐进式上线）
            "focus_on_super_nodes": True,         # 是否聚焦拆分超级节点（渐进式上线）
        }
    """
    # 默认参数
    params = {
        "merge_threshold": 0.7,
        "compression_level": "medium",
        "max_meta_fanout": 15,
        "cleanup_targets": [],
        "protect_topics": [],
        "split_candidates": [],
        "focus_on_truncated": True,      # 渐进式上线：先只做这个
        "focus_on_super_nodes": True,    # 渐进式上线：先只做这个
    }
    
    # --- 规则1: 满意度低 → 保守整理，少压缩 ---
    if signals.get("overall_satisfaction", 0.5) < 0.5:
        params["compression_level"] = "light"
        params["merge_threshold"] = 0.85  # 只合并非常相似的实体
    
    # --- 规则2: 空查询多 → 说明记忆写入不足或被过度压缩 ---
    empty_queries = signals.get("empty_queries", [])
    if len(empty_queries) > 3:
        params["compression_level"] = "light"  # 减少压缩，保留更多细节
        params["protect_topics"].extend(empty_queries)  # 保护这些话题的实体
    
    # --- 规则3: 噪音查询多 → 需要清理无用实体和泛化关系 ---
    noisy_queries = signals.get("noisy_queries", [])
    if len(noisy_queries) > 3:
        useful_entities = set(signals.get("useful_entities", {}).keys())
        useless_entities = signals.get("useless_entities", {})
        
        # 找出经常出现在负面feedback中、但从不出现在正面feedback中的实体
        pure_noise = []
        for entity, count in useless_entities.items():
            if entity not in useful_entities and count >= 2:  # 至少出现2次
                pure_noise.append(entity)
        
        params["cleanup_targets"] = pure_noise
    
    # --- 规则4: 热门话题 → 保护其实体，不要合并或压缩 ---
    hot_topics = signals.get("hot_topics", [])
    params["protect_topics"].extend(hot_topics)
    
    # --- 规则5: 冷门话题 → 可以更激进地压缩 ---
    # (实现留空，后续在execute_meditation中处理)
    
    # --- 规则6: 检查上次冥思的效果 ---
    if last_log:
        before = last_log.get("graph_stats_before", {}).get("generic_relations_ratio", 0)
        after = last_log.get("graph_stats_after", {}).get("generic_relations_ratio", 0)
        if after >= before:  # 上次冥思没有降低通用关系比例
            params["max_meta_fanout"] = max(params["max_meta_fanout"] - 5, 5)
    
    # --- 规则7: META超级节点检测 ---
    # 这个需要在execute_meditation中实现，通过graph_store查找
    
    return params


# ============================================================================
# 第四步：冥思日志系统
# ============================================================================

class MeditationLogManager:
    """冥思日志管理器，存储和读取冥思进化历史"""
    
    def __init__(self, store: Any):
        self.store = store
    
    def save_log(self, log_data: Dict[str, Any]) -> bool:
        """
        保存冥思日志到数据库
        
        Args:
            log_data: 冥思日志数据，包含：
                "timestamp": 时间戳,
                "input_signals": 输入信号,
                "params_used": 使用的参数,
                "actions_taken": 执行的操作,
                "graph_stats_before": 冥思前的图谱统计,
                "graph_stats_after": 冥思后的图谱统计
        
        Returns:
            是否成功保存
        """
        try:
            # 创建冥思日志节点
            log_id = f"meditation_log_{int(time.time())}"
            properties = {
                "id": log_id,
                "type": "MeditationLog",
                "timestamp": log_data.get("timestamp", time.time()),
                "input_signals": json.dumps(log_data.get("input_signals", {}), ensure_ascii=False),
                "params_used": json.dumps(log_data.get("params_used", {}), ensure_ascii=False),
                "actions_taken": json.dumps(log_data.get("actions_taken", {}), ensure_ascii=False),
                "graph_stats_before": json.dumps(log_data.get("graph_stats_before", {}), ensure_ascii=False),
                "graph_stats_after": json.dumps(log_data.get("graph_stats_after", {}), ensure_ascii=False),
                "created_at": time.time()
            }
            
            # 保存到图数据库
            self.store.create_node("MeditationLog", properties)
            logger.info(f"Meditation log saved: {log_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save meditation log: {e}")
            return False
    
    def get_last_log(self) -> Optional[Dict[str, Any]]:
        """
        获取最后一次冥思的日志
        
        Returns:
            最后一次冥思日志，如果没有则返回None
        """
        try:
            # 查询最近的冥思日志
            cypher = """
            MATCH (n:MeditationLog)
            RETURN n
            ORDER BY n.timestamp DESC
            LIMIT 1
            """
            result = self.store.execute_query(cypher)
            
            if result and len(result) > 0:
                node_data = result[0].get("n", {})
                properties = node_data.get("properties", {})
                
                # 解析JSON字段
                return {
                    "timestamp": properties.get("timestamp"),
                    "input_signals": json.loads(properties.get("input_signals", "{}")),
                    "params_used": json.loads(properties.get("params_used", "{}")),
                    "actions_taken": json.loads(properties.get("actions_taken", "{}")),
                    "graph_stats_before": json.loads(properties.get("graph_stats_before", "{}")),
                    "graph_stats_after": json.loads(properties.get("graph_stats_after", "{}"))
                }
            
        except Exception as e:
            logger.error(f"Failed to get last meditation log: {e}")
        
        return None
    
    def get_recent_feedbacks(self, days: int = 7) -> List[EnhancedFeedback]:
        """
        获取最近N天的反馈记录
        
        Args:
            days: 天数，默认7天
        
        Returns:
            增强反馈列表
        """
        try:
            # 查询最近的反馈节点
            time_threshold = time.time() - (days * 24 * 60 * 60)
            cypher = """
            MATCH (n:Feedback)
            WHERE n.timestamp >= $time_threshold
            RETURN n
            ORDER BY n.timestamp DESC
            """
            
            result = self.store.execute_query(cypher, {"time_threshold": time_threshold})
            feedbacks = []
            
            for record in result:
                node_data = record.get("n", {})
                properties = node_data.get("properties", {})
                
                # 创建增强反馈对象
                feedback = EnhancedFeedback(
                    query=properties.get("query", ""),
                    success=properties.get("success", False),
                    confidence=properties.get("confidence", 0.5),
                    result_count=properties.get("result_count", 0),
                    returned_entities=properties.get("returned_entities", []),
                    useful_entities=properties.get("useful_entities", []),
                    noise_entities=properties.get("noise_entities", []),
                    applied_strategy_name=properties.get("applied_strategy_name"),
                    validation_status=properties.get("validation_status"),
                    timestamp=properties.get("timestamp")
                )
                feedbacks.append(feedback)
            
            return feedbacks
            
        except Exception as e:
            logger.error(f"Failed to get recent feedbacks: {e}")
            return []


# ============================================================================
# 第五步：进化冥思入口点
# ============================================================================

def analyze_and_adjust(store: Any) -> Dict[str, Any]:
    """
    冥思进化系统的入口点
    
    执行流程：
    1. 感知 — 了解当前状态
    2. 反思 — 分析feedback信号
    3. 决策 — 根据信号调整冥思参数
    4. 返回调整后的参数供冥思引擎使用
    
    Args:
        store: 图数据库存储对象
    
    Returns:
        调整后的冥思参数，如果失败则返回默认参数
    """
    try:
        logger.info("Starting meditation evolution analysis...")
        
        # 1. 感知 — 了解当前状态
        graph_stats = {}  # 需要通过store.get_graph_stats()获取
        log_manager = MeditationLogManager(store)
        
        # 获取最近7天的反馈
        recent_feedbacks = log_manager.get_recent_feedbacks(days=7)
        logger.info(f"Found {len(recent_feedbacks)} recent feedbacks")
        
        # 如果没有足够的反馈，返回默认参数
        if len(recent_feedbacks) < 5:
            logger.info("Not enough feedbacks, using default parameters")
            return {
                "merge_threshold": 0.7,
                "compression_level": "light",  # 默认保守
                "max_meta_fanout": 15,
                "cleanup_targets": [],
                "protect_topics": [],
                "split_candidates": [],
                "focus_on_truncated": True,
                "focus_on_super_nodes": True,
                "evolution_enabled": False
            }
        
        # 2. 反思 — 分析feedback信号
        signals = analyze_feedback_signals(recent_feedbacks, store)
        logger.info(f"Feedback signals analyzed: {signals.get('overall_satisfaction', 0):.2f} satisfaction")
        
        # 获取上次冥思日志
        last_log = log_manager.get_last_log()
        
        # 3. 决策 — 根据信号调整冥思参数
        params = adjust_meditation_params(signals, last_log)
        params["evolution_enabled"] = True
        params["feedbacks_analyzed"] = len(recent_feedbacks)
        
        logger.info(f"Adjusted meditation parameters: {params}")
        return params
        
    except Exception as e:
        logger.error(f"Error in meditation evolution analysis: {e}")
        # 返回安全默认值
        return {
            "merge_threshold": 0.7,
            "compression_level": "light",
            "max_meta_fanout": 15,
            "cleanup_targets": [],
            "protect_topics": [],
            "split_candidates": [],
            "focus_on_truncated": True,
            "focus_on_super_nodes": True,
            "evolution_enabled": False,
            "error": str(e)
        }


# ============================================================================
# 工具函数
# ============================================================================

def find_truncated_entities(store: Any, max_length: int = 4) -> List[str]:
    """
    查找截断的中文实体名
    
    Args:
        store: 图数据库存储对象
        max_length: 最大长度，默认4个字符
    
    Returns:
        截断实体名列表
    """
    try:
        # 查找名字长度小于max_length的中文实体
        cypher = """
        MATCH (n:Entity)
        WHERE size(n.name) < $max_length
        AND n.name =~ '[\\u4e00-\\u9fa5]+'  // 只匹配中文字符
        RETURN n.name as name, n.mention_count as count
        """
        
        result = store.execute_query(cypher, {"max_length": max_length})
        return [(record.get("name"), record.get("count", 0)) for record in result]
        
    except Exception as e:
        logger.error(f"Failed to find truncated entities: {e}")
        return []


def find_super_nodes(store: Any, fanout_threshold: int = 15) -> List[str]:
    """
    查找关系扇出度过高的超级节点
    
    Args:
        store: 图数据库存储对象
        fanout_threshold: 扇出度阈值，默认15
    
    Returns:
        超级节点ID列表
    """
    try:
        # 查找关系数超过阈值的节点
        cypher = """
        MATCH (n)-[r]->()
        WITH n, count(r) as fanout
        WHERE fanout > $threshold
        RETURN n.id as node_id, fanout
        ORDER BY fanout DESC
        """
        
        result = store.execute_query(cypher, {"threshold": fanout_threshold})
        return [(record.get("node_id"), record.get("fanout", 0)) for record in result]
        
    except Exception as e:
        logger.error(f"Failed to find super nodes: {e}")
        return []