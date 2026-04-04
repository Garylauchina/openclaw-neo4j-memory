#!/usr/bin/env python3
"""
Plan-Aware Attention（计划感知注意力）
核心：从"Goal-Aware"升级到"Goal + Plan-Aware" Attention
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import time

from .plan_generator import PlanStep, ActionType

@dataclass
class PlanAwareAttentionConfig:
    """计划感知注意力配置"""
    # 注意力权重
    goal_weight: float = 0.4          # 目标权重
    plan_step_weight: float = 0.4     # 当前计划步骤权重
    base_attention_weight: float = 0.2 # 基础注意力权重
    
    # 计划步骤影响
    current_step_boost: float = 1.5   # 当前步骤增强
    next_step_boost: float = 1.2      # 下一步骤增强
    previous_step_decay: float = 0.8   # 前一步骤衰减
    
    # 时间衰减
    step_time_decay_factor: float = 0.95  # 步骤时间衰减因子
    max_time_decay: float = 0.5           # 最大时间衰减
    
    # 聚焦控制
    enable_focus_control: bool = True     # 启用聚焦控制
    focus_threshold: float = 0.7          # 聚焦阈值
    focus_boost: float = 1.3              # 聚焦增强
    
    def validate(self):
        """验证配置"""
        weights = [
            self.goal_weight,
            self.plan_step_weight,
            self.base_attention_weight
        ]
        
        total_weight = sum(weights)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"注意力权重总和应为1.0，当前为{total_weight:.3f}")
        
        if self.current_step_boost < 1.0:
            raise ValueError(f"current_step_boost必须大于等于1.0，当前为{self.current_step_boost}")
        
        if self.next_step_boost < 1.0:
            raise ValueError(f"next_step_boost必须大于等于1.0，当前为{self.next_step_boost}")
        
        if not 0.0 <= self.previous_step_decay <= 1.0:
            raise ValueError(f"previous_step_decay必须在0~1之间，当前为{self.previous_step_decay}")
        
        if not 0.0 < self.step_time_decay_factor <= 1.0:
            raise ValueError(f"step_time_decay_factor必须在0~1之间，当前为{self.step_time_decay_factor}")
        
        if not 0.0 <= self.max_time_decay <= 1.0:
            raise ValueError(f"max_time_decay必须在0~1之间，当前为{self.max_time_decay}")
        
        if not 0.0 <= self.focus_threshold <= 1.0:
            raise ValueError(f"focus_threshold必须在0~1之间，当前为{self.focus_threshold}")
        
        if self.focus_boost < 1.0:
            raise ValueError(f"focus_boost必须大于等于1.0，当前为{self.focus_boost}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "weights": {
                "goal_weight": self.goal_weight,
                "plan_step_weight": self.plan_step_weight,
                "base_attention_weight": self.base_attention_weight
            },
            "step_boosts": {
                "current_step_boost": self.current_step_boost,
                "next_step_boost": self.next_step_boost,
                "previous_step_decay": self.previous_step_decay
            },
            "time_decay": {
                "step_time_decay_factor": self.step_time_decay_factor,
                "max_time_decay": self.max_time_decay
            },
            "focus_control": {
                "enable_focus_control": self.enable_focus_control,
                "focus_threshold": self.focus_threshold,
                "focus_boost": self.focus_boost
            }
        }

class PlanAwareAttention:
    """计划感知注意力"""
    
    def __init__(self, config: Optional[PlanAwareAttentionConfig] = None):
        self.config = config or PlanAwareAttentionConfig()
        self.config.validate()
        
        # 缓存机制
        self.attention_cache: Dict[str, Tuple[float, float]] = {}  # cache_key -> (score, timestamp)
        self.cache_ttl = 30  # 30秒缓存
        
        # 统计信息
        self.stats = {
            "total_attention_computations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_computation_time": 0.0,
            "attention_distribution": {
                "goal_dominant": 0,    # 目标主导 (>0.6 goal_weight)
                "plan_dominant": 0,    # 计划主导 (>0.6 plan_weight)
                "balanced": 0,         # 平衡 (0.4~0.6)
                "base_dominant": 0     # 基础主导 (>0.6 base_weight)
            }
        }
    
    def compute_plan_aware_attention(self, 
                                   node: Any,
                                   base_attention_score: float,
                                   goal_description: str,
                                   current_plan_step: Optional[PlanStep],
                                   plan_context: Optional[Dict[str, Any]] = None,
                                   node_context: Optional[Dict[str, Any]] = None) -> float:
        """
        计算计划感知注意力分数
        
        Args:
            node: 节点对象
            base_attention_score: 基础注意力分数
            goal_description: 目标描述
            current_plan_step: 当前计划步骤
            plan_context: 计划上下文
            node_context: 节点上下文
        
        Returns:
            float: 计划感知注意力分数 (0~1)
        """
        import time
        start_time = time.time()
        
        # 生成缓存键
        cache_key = self._generate_cache_key(
            node, goal_description, current_plan_step, plan_context
        )
        
        # 检查缓存
        if cache_key in self.attention_cache:
            score, timestamp = self.attention_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                self.stats["cache_hits"] += 1
                return score
        
        self.stats["cache_misses"] += 1
        
        # 1. 计算目标相关性
        goal_relevance = self._compute_goal_relevance(node, goal_description, node_context)
        
        # 2. 计算计划步骤相关性
        plan_step_relevance = self._compute_plan_step_relevance(
            node, current_plan_step, plan_context, node_context
        )
        
        # 3. 计算综合注意力分数
        plan_aware_score = self._compute_combined_attention(
            base_attention_score,
            goal_relevance,
            plan_step_relevance
        )
        
        # 4. 应用聚焦控制
        if self.config.enable_focus_control:
            plan_aware_score = self._apply_focus_control(
                plan_aware_score, goal_relevance, plan_step_relevance
            )
        
        # 5. 限制范围
        plan_aware_score = max(0.0, min(1.0, plan_aware_score))
        
        # 6. 更新缓存
        self.attention_cache[cache_key] = (plan_aware_score, time.time())
        
        # 7. 清理过期缓存
        self._clean_cache()
        
        # 8. 更新统计
        elapsed_time = time.time() - start_time
        self._update_stats(plan_aware_score, goal_relevance, plan_step_relevance, elapsed_time)
        
        return plan_aware_score
    
    def _compute_goal_relevance(self, node: Any, goal_description: str,
                              node_context: Optional[Dict[str, Any]]) -> float:
        """计算目标相关性"""
        # 获取节点文本
        node_text = self._get_node_text(node, node_context)
        
        if not node_text or not goal_description:
            return 0.1
        
        # 计算文本相似度
        similarity = self._compute_text_similarity(node_text, goal_description)
        
        # 增强：考虑节点类型和目标类型的匹配
        node_type = self._get_node_type(node, node_context)
        goal_type = self._infer_goal_type(goal_description)
        
        type_match_boost = 1.0
        if node_type and goal_type:
            # 简单类型匹配逻辑
            type_matches = {
                ("concept", "understanding"): 1.3,
                ("data", "analysis"): 1.4,
                ("option", "decision"): 1.5,
                ("action", "execution"): 1.4
            }
            
            type_match_boost = type_matches.get((node_type, goal_type), 1.0)
        
        goal_relevance = similarity * type_match_boost
        
        return max(0.1, min(1.0, goal_relevance))
    
    def _compute_plan_step_relevance(self, node: Any,
                                   current_plan_step: Optional[PlanStep],
                                   plan_context: Optional[Dict[str, Any]],
                                   node_context: Optional[Dict[str, Any]]) -> float:
        """计算计划步骤相关性"""
        if not current_plan_step:
            return 0.1
        
        # 获取节点文本
        node_text = self._get_node_text(node, node_context)
        
        # 1. 基于行动类型的相关性
        action_relevance = self._compute_action_relevance(node, current_plan_step.action, node_context)
        
        # 2. 基于目标的相关性
        target_relevance = self._compute_target_relevance(node_text, current_plan_step.target)
        
        # 3. 基于方法的相关性
        method_relevance = self._compute_method_relevance(node, current_plan_step.method, node_context)
        
        # 4. 基于步骤位置的影响
        position_factor = 1.0
        if plan_context:
            current_step_index = plan_context.get("current_step_index", 0)
            total_steps = plan_context.get("total_steps", 1)
            
            # 当前步骤增强
            if current_step_index == plan_context.get("executing_step_index", -1):
                position_factor = self.config.current_step_boost
            # 下一步骤增强
            elif current_step_index == plan_context.get("executing_step_index", -1) + 1:
                position_factor = self.config.next_step_boost
            # 前一步骤衰减
            elif current_step_index < plan_context.get("executing_step_index", -1):
                position_factor = self.config.previous_step_decay
        
        # 5. 时间衰减
        time_decay = 1.0
        if plan_context and "step_start_times" in plan_context:
            step_start_time = plan_context["step_start_times"].get(current_step_index)
            if step_start_time:
                elapsed_time = time.time() - step_start_time
                # 指数衰减
                time_decay = self.config.step_time_decay_factor ** (elapsed_time / 60.0)  # 每分钟衰减
                time_decay = max(self.config.max_time_decay, time_decay)
        
        # 综合相关性
        step_relevance = (action_relevance * 0.4 + 
                         target_relevance * 0.3 + 
                         method_relevance * 0.3)
        
        step_relevance = step_relevance * position_factor * time_decay
        
        return max(0.1, min(1.0, step_relevance))
    
    def _compute_action_relevance(self, node: Any, action: ActionType,
                                node_context: Optional[Dict[str, Any]]) -> float:
        """计算行动类型相关性"""
        # 行动类型与节点类型的匹配
        node_type = self._get_node_type(node, node_context)
        
        # 行动类型映射
        action_node_type_mapping = {
            ActionType.RETRIEVE_INFO: ["data", "information", "source"],
            ActionType.ANALYZE: ["data", "pattern", "trend"],
            ActionType.COMPARE: ["option", "alternative", "solution"],
            ActionType.DECIDE: ["option", "decision", "recommendation"],
            ActionType.EXECUTE: ["action", "task", "operation"],
            ActionType.EVALUATE: ["result", "outcome", "metric"],
            ActionType.ADAPT: ["adjustment", "modification", "optimization"],
            ActionType.REPORT: ["summary", "conclusion", "finding"]
        }
        
        # 检查节点类型是否与行动类型匹配
        expected_types = action_node_type_mapping.get(action, [])
        if node_type in expected_types:
            return 0.8
        elif node_type:
            # 部分匹配
            for expected_type in expected_types:
                if expected_type in node_type or node_type in expected_type:
                    return 0.6
        
        return 0.3
    
    def _compute_target_relevance(self, node_text: str, target: str) -> float:
        """计算目标相关性"""
        if not node_text or not target:
            return 0.1
        
        # 文本相似度
        similarity = self._compute_text_similarity(node_text, target)
        
        # 增强：检查是否包含目标关键词
        target_words = set(target.lower().split())
        node_words = set(node_text.lower().split())
        
        if target_words and node_words:
            overlap = len(target_words.intersection(node_words))
            if overlap > 0:
                similarity = max(similarity, 0.5)
        
        return similarity
    
    def _compute_method_relevance(self, node: Any, method: str,
                                node_context: Optional[Dict[str, Any]]) -> float:
        """计算方法相关性"""
        if not method:
            return 0.5
        
        # 获取节点方法信息
        node_method = self._get_node_method(node, node_context)
        
        if node_method:
            # 方法匹配
            if method.lower() in node_method.lower() or node_method.lower() in method.lower():
                return 0.8
        
        # 默认相关性
        return 0.3
    
    def _compute_combined_attention(self, base_score: float,
                                  goal_relevance: float,
                                  plan_step_relevance: float) -> float:
        """计算综合注意力分数"""
        # 加权组合
        combined_score = (
            self.config.goal_weight * goal_relevance +
            self.config.plan_step_weight * plan_step_relevance +
            self.config.base_attention_weight * base_score
        )
        
        return combined_score
    
    def _apply_focus_control(self, attention_score: float,
                           goal_relevance: float,
                           plan_step_relevance: float) -> float:
        """应用聚焦控制"""
        # 检查是否需要聚焦
        max_component = max(goal_relevance, plan_step_relevance)
        
        if max_component > self.config.focus_threshold:
            # 应用聚焦增强
            focus_boost = 1.0 + (max_component - self.config.focus_threshold) * (self.config.focus_boost - 1.0)
            attention_score = min(1.0, attention_score * focus_boost)
        
        return attention_score
    
    def _get_node_text(self, node: Any, node_context: Optional[Dict[str, Any]]) -> str:
        """获取节点文本"""
        # 尝试从节点对象获取文本
        if hasattr(node, 'text'):
            return str(node.text)
        elif hasattr(node, 'name'):
            return str(node.name)
        elif hasattr(node, 'description'):
            return str(node.description)
        elif hasattr(node, 'id'):
            return str(node.id)
        
        # 从上下文获取
        if node_context and 'node_text' in node_context:
            return str(node_context['node_text'])
        
        return ""
    
    def _get_node_type(self, node: Any, node_context: Optional[Dict[str, Any]]) -> Optional[str]:
        """获取节点类型"""
        # 尝试从节点对象获取类型
        if hasattr(node, 'type'):
            return str(node.type)
        elif hasattr(node, 'node_type'):
            return str(node.node_type)
        
        # 从上下文获取
        if node_context and 'node_type' in node_context:
            return str(node_context['node_type'])
        
        # 基于文本推断
        node_text = self._get_node_text(node, node_context)
        if not node_text:
            return None
        
        # 简单类型推断
        text_lower = node_text.lower()
        
        if any(word in text_lower for word in ["数据", "信息", "资料", "data", "information"]):
            return "data"
        elif any(word in text_lower for word in ["分析", "研究", "调查", "analysis", "research"]):
            return "analysis"
        elif any(word in text_lower for word in ["选项", "选择", "方案", "option", "choice"]):
            return "option"
        elif any(word in text_lower for word in ["决策", "决定", "判断", "decision", "judgment"]):
            return "decision"
        elif any(word in text_lower for word in ["行动", "执行", "实施", "action", "execution"]):
            return "action"
        elif any(word in text_lower for word in ["概念", "定义", "原理", "concept", "definition"]):
            return "concept"
        
        return None
    
    def _get_node_method(self, node: Any, node_context: Optional[Dict[str, Any]]) -> Optional[str]:
        """获取节点方法"""
        # 尝试从节点对象获取方法
        if hasattr(node, 'method'):
            return str(node.method)
        elif hasattr(node, 'approach'):
            return str(node.approach)
        
        # 从上下文获取
        if node_context and 'node_method' in node_context:
            return str(node_context['node_method'])
        
        return None
    
    def _infer_goal_type(self, goal_description: str) -> Optional[str]:
        """推断目标类型"""
        if not goal_description:
            return None
        
        goal_lower = goal_description.lower()
        
        if any(word in goal_lower for word in ["理解", "了解", "什么是", "解释", "说明"]):
            return "understanding"
        elif any(word in goal_lower for word in ["分析", "评估", "研究", "调查"]):
            return "analysis"
        elif any(word in goal_lower for word in ["比较", "对比", "区别", "差异"]):
            return "comparison"
        elif any(word in goal_lower for word in ["决定", "选择", "决策", "确定"]):
            return "decision"
        elif any(word in goal_lower for word in ["执行", "实施", "实现", "完成"]):
            return "execution"
        
        return None
    
    def _compute_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        if not text1 or not text2:
            return 0.1
        
        # 转换为词集
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.1
        
        # Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        if union == 0:
            return 0.1
        
        similarity = intersection / union
        
        # 增强：考虑部分匹配
        partial_matches = sum(1 for w1 in words1 
                             for w2 in words2 
                             if w1 in w2 or w2 in w1)
        
        if partial_matches > 0:
            similarity = max(similarity, 0.3)
        
        return min(1.0, similarity)
    
    def _generate_cache_key(self, node: Any, goal_description: str,
                          current_plan_step: Optional[PlanStep],
                          plan_context: Optional[Dict[str, Any]]) -> str:
        """生成缓存键"""
        # 获取节点ID
        node_id = ""
        if hasattr(node, 'id'):
            node_id = str(node.id)
        
        # 获取计划步骤ID
        step_id = current_plan_step.id if current_plan_step else "no_step"
        
        # 生成键
        key_parts = [
            node_id,
            hash(goal_description) if goal_description else "no_goal",
            step_id,
            hash(str(plan_context)) if plan_context else "no_context"
        ]
        
        return "_".join(str(part) for part in key_parts)
    
    def _clean_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, (_, timestamp) in self.attention_cache.items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.attention_cache[key]
    
    def _update_stats(self, attention_score: float,
                     goal_relevance: float,
                     plan_step_relevance: float,
                     elapsed_time: float):
        """更新统计信息"""
        self.stats["total_attention_computations"] += 1
        
        # 更新注意力分布
        goal_weight_ratio = goal_relevance / (goal_relevance + plan_step_relevance + 0.001)
        plan_weight_ratio = plan_step_relevance / (goal_relevance + plan_step_relevance + 0.001)
        
        if goal_weight_ratio > 0.6:
            self.stats["attention_distribution"]["goal_dominant"] += 1
        elif plan_weight_ratio > 0.6:
            self.stats["attention_distribution"]["plan_dominant"] += 1
        elif 0.4 <= goal_weight_ratio <= 0.6 and 0.4 <= plan_weight_ratio <= 0.6:
            self.stats["attention_distribution"]["balanced"] += 1
        else:
            self.stats["attention_distribution"]["base_dominant"] += 1
        
        # 更新平均计算时间
        self.stats["avg_computation_time"] = (
            (self.stats["avg_computation_time"] * (self.stats["total_attention_computations"] - 1) + elapsed_time)
            / self.stats["total_attention_computations"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_computations = self.stats["total_attention_computations"]
        
        # 计算分布百分比
        attention_distribution_pct = {}
        if total_computations > 0:
            for category, count in self.stats["attention_distribution"].items():
                attention_distribution_pct[category] = count / total_computations
        
        cache_hit_rate = 0.0
        if self.stats["total_attention_computations"] > 0:
            cache_hit_rate = self.stats["cache_hits"] / self.stats["total_attention_computations"]
        
        return {
            "config": self.config.to_dict(),
            "performance": {
                "total_attention_computations": self.stats["total_attention_computations"],
                "cache_hits": self.stats["cache_hits"],
                "cache_misses": self.stats["cache_misses"],
                "cache_hit_rate": cache_hit_rate,
                "cache_size": len(self.attention_cache),
                "avg_computation_time_ms": self.stats["avg_computation_time"] * 1000
            },
            "attention_distribution": {
                "counts": self.stats["attention_distribution"],
                "percentages": attention_distribution_pct
            }
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_attention_computations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_computation_time": 0.0,
            "attention_distribution": {
                "goal_dominant": 0,
                "plan_dominant": 0,
                "balanced": 0,
                "base_dominant": 0
            }
        }
        self.attention_cache.clear()
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        config = stats["config"]
        perf = stats["performance"]
        dist = stats["attention_distribution"]
        
        print(f"   📊 Plan-Aware Attention状态:")
        print(f"      配置:")
        print(f"        权重:")
        print(f"          目标权重: {config['weights']['goal_weight']:.2f}")
        print(f"          计划步骤权重: {config['weights']['plan_step_weight']:.2f}")
        print(f"          基础注意力权重: {config['weights']['base_attention_weight']:.2f}")
        
        print(f"        步骤增强:")
        print(f"          当前步骤增强: {config['step_boosts']['current_step_boost']:.2f}")
        print(f"          下一步骤增强: {config['step_boosts']['next_step_boost']:.2f}")
        print(f"          前一步骤衰减: {config['step_boosts']['previous_step_decay']:.2f}")
        
        print(f"        聚焦控制:")
        print(f"          启用聚焦控制: {config['focus_control']['enable_focus_control']}")
        print(f"          聚焦阈值: {config['focus_control']['focus_threshold']:.2f}")
        print(f"          聚焦增强: {config['focus_control']['focus_boost']:.2f}")
        
        print(f"      性能:")
        print(f"        总计算次数: {perf['total_attention_computations']}")
        print(f"        缓存命中率: {perf['cache_hit_rate']:.1%}")
        print(f"        缓存大小: {perf['cache_size']}")
        print(f"        平均计算时间: {perf['avg_computation_time_ms']:.2f}ms")
        
        print(f"      注意力分布:")
        if perf['total_attention_computations'] > 0:
            for category, count in dist["counts"].items():
                pct = dist["percentages"].get(category, 0)
                print(f"        {category}: {count} ({pct:.1%})")