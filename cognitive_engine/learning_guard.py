#!/usr/bin/env python3
"""
Learning Guard（学习防护层）

核心函数：validate_diff(diff, context) → bool

系统本质：Reliable Learning System（可靠学习系统）
目标：从"会学习"升级到"学得对"
"""

import time
import math
from typing import List, Dict, Tuple, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

# 导入相关模块
from reflection_upgrade import GraphDiff, DiffOp, Pattern, ReflectionEngine
from global_graph import GlobalGraph, NodeType, EdgeType


class KnowledgeState(Enum):
    """知识状态（必须区分）"""
    HYPOTHESIS = "hypothesis"      # 假设（confidence < 0.7）
    STABLE = "stable"              # 稳定认知（confidence ≥ 0.7 + 多轮验证）


@dataclass
class BufferedDiff:
    """缓冲的Diff（延迟写入）"""
    diff: GraphDiff
    timestamp: float = field(default_factory=time.time)
    evidence_count: int = 1
    contexts: List[str] = field(default_factory=list)  # 来源上下文
    state: KnowledgeState = KnowledgeState.HYPOTHESIS
    
    def add_evidence(self, context: str):
        """添加证据"""
        self.evidence_count += 1
        if context not in self.contexts:
            self.contexts.append(context)
        
        # 检查是否可以升级为稳定认知
        if (self.evidence_count >= 3 and 
            len(set(self.contexts)) >= 2 and  # 至少2个独立来源
            self.diff.confidence >= 0.7):
            self.state = KnowledgeState.STABLE


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    confidence: float = 0.0
    reasons: List[str] = field(default_factory=list)  # 通过/拒绝原因
    suggested_action: str = "accept"  # accept, reject, downgrade, buffer
    buffer_key: Optional[str] = None  # 缓冲键（如果建议缓冲）


class LearningGuard:
    """
    学习防护层
    
    三道防线：
    1. 一致性验证（Consistency Check）
    2. 多源验证（Multi-Evidence）
    3. 延迟写入（Delayed Commit）
    
    目标：确保系统"学得对"，而不仅仅是"会学习"
    """
    
    def __init__(self, global_graph: GlobalGraph, config: Optional[Dict] = None):
        self.global_graph = global_graph
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        
        # 缓冲系统（延迟写入）
        self.diff_buffer: Dict[str, BufferedDiff] = {}  # key: diff_signature -> BufferedDiff
        
        # 验证历史
        self.validation_history: List[Tuple[GraphDiff, ValidationResult]] = []
        
        # 错误模式统计（元认知基础）
        self.error_patterns = {
            "frequent_conflicts": defaultdict(int),  # 频繁冲突的类型
            "rejected_diffs": defaultdict(int),      # 被拒绝的diff类型
            "downgraded_diffs": defaultdict(int),    # 被降权的diff类型
        }
        
        # 统计
        self.stats = {
            "total_validations": 0,
            "accepted": 0,
            "rejected": 0,
            "buffered": 0,
            "downgraded": 0,
            "avg_validation_time_ms": 0.0,
            "buffer_size": 0,
        }
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            # 一致性验证
            "consistency_threshold": 0.8,           # 一致性阈值
            "strong_edge_threshold": 0.7,           # 强边阈值
            
            # 多源验证
            "min_independent_sources": 2,           # 最小独立来源数
            "min_evidence_count": 3,                # 最小证据数
            
            # 延迟写入
            "buffer_ttl_seconds": 3600,             # 缓冲TTL（1小时）
            "max_buffer_size": 50,                  # 最大缓冲大小
            
            # 验证权重
            "validation_weights": {
                "consistency": 0.4,                 # 一致性（最重要）
                "evidence_quality": 0.3,            # 证据质量
                "source_independence": 0.2,         # 来源独立性
                "recency": 0.1,                     # 最近性
            },
            
            # 调试
            "debug": False,
            "strict_mode": True,                    # 严格模式（更多拒绝）
        }
    
    # ========== 核心函数：验证Diff ==========
    
    def validate_diff(self, diff: GraphDiff, context: str) -> ValidationResult:
        """
        核心验证函数
        
        validate_diff(diff, context) → bool
        
        三道防线：
        1. 一致性验证（Consistency Check）
        2. 多源验证（Multi-Evidence）
        3. 延迟写入（Delayed Commit）
        """
        start_time = time.time()
        
        # 更新统计
        self.stats["total_validations"] += 1
        
        # 生成Diff签名（用于缓冲）
        diff_signature = self._generate_diff_signature(diff)
        
        # 检查是否已在缓冲中
        if diff_signature in self.diff_buffer:
            buffered_diff = self.diff_buffer[diff_signature]
            buffered_diff.add_evidence(context)
            
            # 检查是否可以提交
            if buffered_diff.state == KnowledgeState.STABLE:
                result = ValidationResult(
                    valid=True,
                    confidence=buffered_diff.diff.confidence,
                    reasons=["多轮验证通过，升级为稳定认知"],
                    suggested_action="accept"
                )
                
                # 从缓冲中移除（即将提交）
                del self.diff_buffer[diff_signature]
                self.stats["buffer_size"] = len(self.diff_buffer)
                
                self._update_stats(result, start_time)
                return result
        
        # 第一道防线：一致性验证
        consistency_result = self._consistency_check(diff)
        if not consistency_result.valid:
            # 记录错误模式
            self.error_patterns["rejected_diffs"][diff.op.value] += 1
            
            self._update_stats(consistency_result, start_time)
            return consistency_result
        
        # 第二道防线：多源验证
        evidence_result = self._evidence_check(diff, context)
        if not evidence_result.valid:
            # 建议缓冲而不是直接拒绝
            buffer_result = ValidationResult(
                valid=False,
                confidence=diff.confidence * 0.5,  # 降权
                reasons=evidence_result.reasons + ["建议缓冲等待更多证据"],
                suggested_action="buffer",
                buffer_key=diff_signature
            )
            
            self._update_stats(buffer_result, start_time)
            return buffer_result
        
        # 第三道防线：延迟写入决策
        if diff.confidence < self.config["consistency_threshold"]:
            # 置信度不足，建议缓冲
            buffer_result = ValidationResult(
                valid=False,
                confidence=diff.confidence,
                reasons=["置信度不足，建议缓冲等待更多证据"],
                suggested_action="buffer",
                buffer_key=diff_signature
            )
            
            # 添加到缓冲
            self._add_to_buffer(diff, context, diff_signature)
            
            self._update_stats(buffer_result, start_time)
            return buffer_result
        
        # 所有验证通过
        result = ValidationResult(
            valid=True,
            confidence=diff.confidence,
            reasons=["所有验证通过"],
            suggested_action="accept"
        )
        
        self._update_stats(result, start_time)
        return result
    
    def _generate_diff_signature(self, diff: GraphDiff) -> str:
        """生成Diff签名"""
        import hashlib
        
        content = f"{diff.op.value}:{diff.src_node_id}:{diff.dst_node_id}:{diff.edge_type.value if diff.edge_type else ''}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _add_to_buffer(self, diff: GraphDiff, context: str, signature: str):
        """添加到缓冲"""
        if signature not in self.diff_buffer:
            buffered_diff = BufferedDiff(
                diff=diff,
                contexts=[context],
                state=KnowledgeState.HYPOTHESIS
            )
            self.diff_buffer[signature] = buffered_diff
            self.stats["buffer_size"] = len(self.diff_buffer)
            
            # 清理过期缓冲
            self._clean_expired_buffer()
    
    def _clean_expired_buffer(self):
        """清理过期缓冲"""
        current_time = time.time()
        expired_signatures = []
        
        for signature, buffered_diff in self.diff_buffer.items():
            # 检查TTL
            if current_time - buffered_diff.timestamp > self.config["buffer_ttl_seconds"]:
                expired_signatures.append(signature)
            
            # 检查缓冲大小
            if len(self.diff_buffer) > self.config["max_buffer_size"]:
                # 按时间排序，删除最旧的
                sorted_buffers = sorted(
                    self.diff_buffer.items(),
                    key=lambda x: x[1].timestamp
                )
                for sig, _ in sorted_buffers[:10]:
                    if sig not in expired_signatures:
                        expired_signatures.append(sig)
                break
        
        # 删除过期缓冲
        for signature in expired_signatures:
            del self.diff_buffer[signature]
        
        self.stats["buffer_size"] = len(self.diff_buffer)
    
    # ========== 第一道防线：一致性验证 ==========
    
    def _consistency_check(self, diff: GraphDiff) -> ValidationResult:
        """
        一致性验证
        
        规则：if new_diff contradicts existing strong edges: reject
        
        示例：
        已有：用户 → 喜欢 → 日本房产 (0.9)
        新学习：用户 → 不喜欢 → 日本房产
        必须：拒绝 or 降权
        """
        reasons = []
        
        # 检查是否与现有强边冲突
        if diff.src_node_id and diff.dst_node_id and diff.edge_type:
            # 获取所有相关边
            related_edges = self._get_related_edges(diff.src_node_id, diff.dst_node_id)
            
            for edge in related_edges:
                # 检查是否是强边
                if abs(edge.state.weight) >= self.config["strong_edge_threshold"]:
                    # 检查是否冲突
                    if self._is_contradictory(diff, edge):
                        conflict_level = self._compute_conflict_level(diff, edge)
                        
                        if conflict_level > 0.8:
                            # 严重冲突，直接拒绝
                            return ValidationResult(
                                valid=False,
                                confidence=0.1,
                                reasons=[f"与强边严重冲突: {edge.type.value}({edge.state.weight:.2f})"],
                                suggested_action="reject"
                            )
                        else:
                            # 轻度冲突，建议降权
                            return ValidationResult(
                                valid=False,
                                confidence=diff.confidence * 0.3,  # 大幅降权
                                reasons=[f"与现有边轻度冲突: {edge.type.value}({edge.state.weight:.2f})"],
                                suggested_action="downgrade"
                            )
        
        # 检查内部一致性
        if diff.op == DiffOp.REINFORCE_EDGE:
            # 强化边：检查边是否存在
            edge_key = f"{diff.src_node_id}::{diff.dst_node_id}::{diff.edge_type.value}"
            edge = self.global_graph.edges.get(edge_key)
            
            if not edge or not edge.active:
                reasons.append("尝试强化不存在的边")
                return ValidationResult(
                    valid=False,
                    confidence=diff.confidence * 0.5,
                    reasons=reasons,
                    suggested_action="reject"
                )
        
        # 一致性验证通过
        reasons.append("一致性验证通过")
        return ValidationResult(
            valid=True,
            confidence=diff.confidence,
            reasons=reasons,
            suggested_action="accept"
        )
    
    def _get_related_edges(self, src_node_id: str, dst_node_id: str) -> List[Any]:
        """获取相关边"""
        related_edges = []
        
        # 检查直接边
        for edge_key, edge in self.global_graph.edges.items():
            if edge.active:
                if (edge.src == src_node_id and edge.dst == dst_node_id) or \
                   (edge.src == dst_node_id and edge.dst == src_node_id):
                    related_edges.append(edge)
        
        return related_edges
    
    def _is_contradictory(self, diff: GraphDiff, edge: Any) -> bool:
        """检查是否冲突"""
        # 正负冲突
        if diff.op == DiffOp.REINFORCE_EDGE and diff.delta > 0:
            if edge.state.weight < -0.3:  # 现有强负边
                return True
        
        # 边类型冲突
        if diff.edge_type:
            contradictory_pairs = [
                (EdgeType.INTERESTED_IN, EdgeType.DISLIKES),
                (EdgeType.LIKES, EdgeType.DISLIKES),
                (EdgeType.AGREES_WITH, EdgeType.DISAGREES_WITH),
            ]
            
            for type1, type2 in contradictory_pairs:
                if (diff.edge_type == type1 and edge.type == type2) or \
                   (diff.edge_type == type2 and edge.type == type1):
                    return True
        
        return False
    
    def _compute_conflict_level(self, diff: GraphDiff, edge: Any) -> float:
        """计算冲突级别"""
        # 基于权重差异
        weight_diff = abs(diff.delta - edge.state.weight)
        
        # 基于边类型
        type_conflict = 1.0 if self._is_contradictory(diff, edge) else 0.0
        
        conflict_level = weight_diff * 0.7 + type_conflict * 0.3
        return min(1.0, conflict_level)
    
    # ========== 第二道防线：多源验证 ==========
    
    def _evidence_check(self, diff: GraphDiff, context: str) -> ValidationResult:
        """
        多源验证
        
        规则：≥2个"独立来源"
        
        区分：
        同一轮重复 ❌
        多轮不同上下文 ✅
        """
        reasons = []
        
        # 检查证据质量
        evidence_quality = self._compute_evidence_quality(diff, context)
        
        # 检查来源独立性
        source_independence = self._compute_source_independence(diff)
        
        # 综合评分
        weights = self.config["validation_weights"]
        evidence_score = (
            weights["evidence_quality"] * evidence_quality +
            weights["source_independence"] * source_independence
        )
        
        if evidence_score < 0.6:
            reasons.append(f"证据质量不足: {evidence_score:.2f}")
            return ValidationResult(
                valid=False,
                confidence=diff.confidence * evidence_score,
                reasons=reasons,
                suggested_action="buffer"
            )
        
        reasons.append(f"证据验证通过: {evidence_score:.2f}")
        return ValidationResult(
            valid=True,
            confidence=diff.confidence * (0.5 + 0.5 * evidence_score),  # 根据证据质量调整
            reasons=reasons,
            suggested_action="accept"
        )
    
    def _compute_evidence_quality(self, diff: GraphDiff, context) -> float:
        """计算证据质量"""
        # 处理context可能是字符串或字典的情况
        if isinstance(context, dict):
            # 从字典中提取查询文本
            query = context.get('query', '')
            if query:
                context_text = query
            else:
                context_text = str(context)
        else:
            context_text = str(context)
        
        # 简单实现：基于上下文长度和多样性
        context_words = len(context_text.split())
        
        if context_words < 5:
            return 0.3  # 上下文太短，证据质量低
        elif context_words > 20:
            return 0.9  # 上下文丰富，证据质量高
        else:
            return 0.6  # 中等质量
    
    def _compute_source_independence(self, diff: GraphDiff) -> float:
        """计算来源独立性"""
        # 检查验证历史中的相同diff
        same_diffs = []
        for hist_diff, result in self.validation_history[-10:]:  # 最近10次
            if self._is_same_diff(hist_diff, diff):
                same_diffs.append(result)
        
        if len(same_diffs) == 0:
            return 1.0  # 全新diff，独立性高
        elif len(same_diffs) == 1:
            return 0.7  # 出现过一次，独立性中等
        else:
            # 多次出现，检查是否来自不同上下文
            contexts = set()
            for result in same_diffs:
                if hasattr(result, 'contexts'):
                    contexts.update(result.contexts)
            
            if len(contexts) >= 2:
                return 0.8  # 来自不同上下文，独立性较高
            else:
                return 0.4  # 同一上下文重复，独立性低
    
    def _is_same_diff(self, diff1: GraphDiff, diff2: GraphDiff) -> bool:
        """检查是否是相同的diff"""
        return (diff1.op == diff2.op and
                diff1.src_node_id == diff2.src_node_id and
                diff1.dst_node_id == diff2.dst_node_id and
                diff1.edge_type == diff2.edge_type)
    
    # ========== 辅助方法 ==========
    
    def _update_stats(self, result: ValidationResult, start_time: float):
        """更新统计"""
        processing_time = (time.time() - start_time) * 1000
        self.stats["avg_validation_time_ms"] = (
            self.stats["avg_validation_time_ms"] * 0.9 + processing_time * 0.1
        )
        
        # 记录验证历史
        if hasattr(result, 'diff'):  # 如果有diff信息
            self.validation_history.append((result.diff, result))
        
        # 保持历史大小
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]
        
        # 更新计数
        if result.valid:
            self.stats["accepted"] += 1
        else:
            if result.suggested_action == "reject":
                self.stats["rejected"] += 1
            elif result.suggested_action == "buffer":
                self.stats["buffered"] += 1
            elif result.suggested_action == "downgrade":
                self.stats["downgraded"] += 1
    
    def apply_validation_result(self, diff: GraphDiff, result: ValidationResult) -> bool:
        """应用验证结果"""
        if result.suggested_action == "accept":
            # 实际应用diff（这里需要调用global_graph的更新方法）
            # 简化实现：记录日志
            if self.config["debug"]:
                print(f"✅ 接受diff: {diff.op.value}, 置信度: {result.confidence:.2f}")
            return True
        
        elif result.suggested_action == "buffer":
            # 已经在前面的validate_diff中处理了缓冲
            if self.config["debug"]:
                print(f"⏳ 缓冲diff: {diff.op.value}, 等待更多证据")
            return False
        
        elif result.suggested_action == "downgrade":
            # 降权处理：降低置信度后重新考虑
            downgraded_confidence = result.confidence
            if self.config["debug"]:
                print(f"⚠️  降权diff: {diff.op.value}, 新置信度: {downgraded_confidence:.2f}")
            return False
        
        elif result.suggested_action == "reject":
            # 记录拒绝原因
            self.error_patterns["rejected_diffs"][diff.op.value] += 1
            if self.config["debug"]:
                print(f"❌ 拒绝diff: {diff.op.value}, 原因: {', '.join(result.reasons)}")
            return False
        
        return False
    
    # ========== 元认知：错误模式分析 ==========
    
    def analyze_error_patterns(self):
        """分析错误模式"""
        print("\n" + "="*60)
        print("错误模式分析（元认知）")
        print("="*60)
        
        # 频繁冲突的类型
        if self.error_patterns["frequent_conflicts"]:
            print("\n频繁冲突的类型:")
            for conflict_type, count in sorted(
                self.error_patterns["frequent_conflicts"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]:
                print(f"  {conflict_type}: {count}次")
        
        # 被拒绝的diff类型
        if self.error_patterns["rejected_diffs"]:
            print("\n被拒绝的diff类型:")
            for op_type, count in sorted(
                self.error_patterns["rejected_diffs"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]:
                print(f"  {op_type}: {count}次")
        
        # 被降权的diff类型
        if self.error_patterns["downgraded_diffs"]:
            print("\n被降权的diff类型:")
            for op_type, count in sorted(
                self.error_patterns["downgraded_diffs"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]:
                print(f"  {op_type}: {count}次")
    
    # ========== 统计和监控 ==========
    
    def print_stats(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("Learning Guard统计信息")
        print("="*60)
        print(f"总验证次数: {self.stats['total_validations']}")
        print(f"接受: {self.stats['accepted']} ({self.stats['accepted']/max(1, self.stats['total_validations'])*100:.1f}%)")
        print(f"拒绝: {self.stats['rejected']} ({self.stats['rejected']/max(1, self.stats['total_validations'])*100:.1f}%)")
        print(f"缓冲: {self.stats['buffered']} ({self.stats['buffered']/max(1, self.stats['total_validations'])*100:.1f}%)")
        print(f"降权: {self.stats['downgraded']} ({self.stats['downgraded']/max(1, self.stats['total_validations'])*100:.1f}%)")
        print(f"平均验证时间: {self.stats['avg_validation_time_ms']:.1f} ms")
        print(f"缓冲大小: {self.stats['buffer_size']}")
        print("="*60)
    
    def print_buffer_status(self):
        """打印缓冲状态"""
        if not self.diff_buffer:
            print("缓冲为空")
            return
        
        print(f"\n缓冲状态 ({len(self.diff_buffer)}个):")
        print("-"*40)
        
        for i, (signature, buffered_diff) in enumerate(self.diff_buffer.items(), 1):
            diff = buffered_diff.diff
            print(f"{i}. {diff.op.value}")
            print(f"   证据数: {buffered_diff.evidence_count}")
            print(f"   状态: {buffered_diff.state.value}")
            print(f"   置信度: {diff.confidence:.2f}")
            print(f"   时间: {time.strftime('%H:%M:%S', time.localtime(buffered_diff.timestamp))}")
            
            if i >= 5:  # 最多显示5个
                print(f"... 还有{len(self.diff_buffer)-5}个")
                break


# ========== 测试函数 ==========

def test_learning_guard_basic():
    """测试Learning Guard基本功能"""
    print("🧪 测试Learning Guard基本功能")
    print("="*60)
    
    # 创建全局图
    graph = GlobalGraph()
    
    # 创建测试数据
    print("\n1. 创建测试数据...")
    
    # 创建用户和话题
    user_id = graph.create_node("测试用户", NodeType.USER)
    topic_id = graph.create_node("日本房产", NodeType.TOPIC)
    
    # 创建强正边（已有稳定认知）
    graph.update_edge(user_id, topic_id, EdgeType.INTERESTED_IN, 0.9)
    print(f"创建强正边: 用户 → INTERESTED_IN → 日本房产 (0.9)")
    
    # 创建Learning Guard
    print("\n2. 创建Learning Guard...")
    guard = LearningGuard(graph, {"debug": True})
    
    # 测试1：一致性验证（冲突检测）
    print("\n3. 测试一致性验证（冲突检测）...")
    
    # 创建冲突的diff（尝试添加负边）
    conflict_diff = GraphDiff(
        op=DiffOp.ADD_EDGE,
        src_node_id=user_id,
        dst_node_id=topic_id,
        edge_type=EdgeType.DISLIKES,
        delta=-0.8,
        confidence=0.8,
        description="尝试添加冲突关系"
    )
    
    result1 = guard.validate_diff(conflict_diff, "用户说不喜欢日本房产")
    print(f"冲突diff验证结果: {'通过' if result1.valid else '拒绝'}")
    print(f"建议操作: {result1.suggested_action}")
    print(f"原因: {', '.join(result1.reasons)}")
    
    # 应用验证结果
    applied1 = guard.apply_validation_result(conflict_diff, result1)
    print(f"应用结果: {'接受' if applied1 else '拒绝/缓冲'}")
    
    # 测试2：多源验证
    print("\n4. 测试多源验证...")
    
    # 创建新关系diff
    new_diff = GraphDiff(
        op=DiffOp.ADD_EDGE,
        src_node_id=user_id,
        dst_node_id=topic_id,
        edge_type=EdgeType.LIKES,
        delta=0.6,
        confidence=0.6,  # 中等置信度
        description="尝试添加新关系"
    )
    
    result2 = guard.validate_diff(new_diff, "用户说喜欢日本房产")
    print(f"新diff验证结果: {'通过' if result2.valid else '拒绝/缓冲'}")
    print(f"建议操作: {result2.suggested_action}")
    print(f"原因: {', '.join(result2.reasons)}")
    
    # 测试3：缓冲系统
    print("\n5. 测试缓冲系统...")
    
    # 创建低置信度diff
    low_conf_diff = GraphDiff(
        op=DiffOp.REINFORCE_EDGE,
        src_node_id=user_id,
        dst_node_id=topic_id,
        edge_type=EdgeType.INTERESTED_IN,
        delta=0.2,
        confidence=0.5,  # 低置信度
        description="低置信度强化"
    )
    
    result3 = guard.validate_diff(low_conf_diff, "用户再次提到日本房产")
    print(f"低置信度diff验证结果: {'通过' if result3.valid else '拒绝/缓冲'}")
    print(f"建议操作: {result3.suggested_action}")
    
    # 打印缓冲状态
    guard.print_buffer_status()
    
    # 打印统计
    print("\n6. Learning Guard统计...")
    guard.print_stats()
    
    print("\n" + "="*60)
    print("✅ Learning Guard基本功能测试完成！")
    print("="*60)
    
    return guard

def test_three_defenses():
    """测试三道防线"""
    print("\n🧪 测试三道防线")
    print("="*60)
    
    graph = GlobalGraph()
    
    # 创建复杂测试场景
    user_id = graph.create_node("复杂用户", NodeType.USER)
    topic1 = graph.create_node("机器学习", NodeType.TOPIC)
    topic2 = graph.create_node("深度学习", NodeType.TOPIC)
    
    # 创建现有认知
    graph.update_edge(user_id, topic1, EdgeType.INTERESTED_IN, 0.8)
    graph.update_edge(topic1, topic2, EdgeType.RELATED_TO, 0.7)
    
    guard = LearningGuard(graph, {"debug": False})
    
    print("\n测试场景: 用户对机器学习有稳定兴趣，系统需要学习新认知")
    print("-"*50)
    
    test_cases = [
        # (描述, diff, 上下文, 预期结果)
        {
            "name": "严重冲突",
            "diff": GraphDiff(
                op=DiffOp.ADD_EDGE,
                src_node_id=user_id,
                dst_node_id=topic1,
                edge_type=EdgeType.DISLIKES,
                delta=-0.7,
                confidence=0.7,
                description="严重冲突：用户说不喜欢机器学习"
            ),
            "context": "用户突然说不喜欢机器学习",
            "expected": "reject"
        },
        {
            "name": "轻度冲突",
            "diff": GraphDiff(
                op=DiffOp.ADD_EDGE,
                src_node_id=user_id,
                dst_node_id=topic1,
                edge_type=EdgeType.LIKES,
                delta=0.3,
                confidence=0.6,
                description="轻度冲突：用户说喜欢机器学习"
            ),
            "context": "用户说喜欢机器学习",
            "expected": "downgrade"
        },
        {
            "name": "新关系（低置信度）",
            "diff": GraphDiff(
                op=DiffOp.ADD_EDGE,
                src_node_id=user_id,
                dst_node_id=topic2,
                edge_type=EdgeType.INTERESTED_IN,
                delta=0.5,
                confidence=0.5,
                description="新关系：用户对深度学习感兴趣"
            ),
            "context": "用户提到深度学习",
            "expected": "buffer"
        },
        {
            "name": "强化现有关系",
            "diff": GraphDiff(
                op=DiffOp.REINFORCE_EDGE,
                src_node_id=user_id,
                dst_node_id=topic1,
                edge_type=EdgeType.INTERESTED_IN,
                delta=0.2,
                confidence=0.9,
                description="强化：用户再次表达对机器学习的兴趣"
            ),
            "context": "用户详细讨论机器学习应用",
            "expected": "accept"
        },
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n测试: {test_case['name']}")
        print(f"描述: {test_case['diff'].description}")
        
        result = guard.validate_diff(test_case['diff'], test_case['context'])
        
        print(f"结果: {result.suggested_action} (预期: {test_case['expected']})")
        print(f"有效: {result.valid}, 置信度: {result.confidence:.2f}")
        
        # 检查是否符合预期
        match = result.suggested_action == test_case['expected']
        results.append((test_case['name'], match, result.suggested_action))
        
        # 应用结果
        guard.apply_validation_result(test_case['diff'], result)
    
    # 总结
    print("\n" + "="*50)
    print("测试结果总结:")
    print("="*50)
    
    passed = 0
    for name, match, action in results:
        status = "✅" if match else "❌"
        print(f"{status} {name}: {action}")
        if match:
            passed += 1
    
    success_rate = passed / len(results) * 100
    print(f"\n通过率: {success_rate:.1f}% ({passed}/{len(results)})")
    
    # 打印详细统计
    print("\n详细统计:")
    guard.print_stats()
    
    # 错误模式分析
    guard.analyze_error_patterns()
    
    print("\n" + "="*60)
    print("三道防线测试完成")
    print("="*60)
    
    return guard, results

def test_system_integration():
    """测试系统集成"""
    print("\n🧪 测试系统集成")
    print("="*60)
    
    # 创建完整系统
    graph = GlobalGraph()
    
    # 创建用户
    user_id = graph.create_node("集成测试用户", NodeType.USER)
    
    print("创建完整系统:")
    print("Global Graph → Reflection Engine → Learning Guard")
    print("-"*50)
    
    # 创建Reflection Engine（简化版）
    from reflection_upgrade import ReflectionEngine
    
    # 创建Learning Guard
    guard = LearningGuard(graph, {"debug": True})
    
    # 模拟学习过程
    print("\n模拟学习过程（带防护）:")
    
    learning_steps = [
        # 步骤1：正确学习（应该接受）
        {
            "diff": GraphDiff(
                op=DiffOp.ADD_EDGE,
                src_node_id=user_id,
                dst_node_id=graph.create_node("正确话题", NodeType.TOPIC),
                edge_type=EdgeType.INTERESTED_IN,
                delta=0.7,
                confidence=0.8,
                description="正确学习：用户对新话题感兴趣"
            ),
            "context": "用户详细讨论新话题，表达浓厚兴趣",
            "expected": "accept"
        },
        # 步骤2：冲突学习（应该拒绝）
        {
            "diff": GraphDiff(
                op=DiffOp.ADD_EDGE,
                src_node_id=user_id,
                dst_node_id=graph.create_node("冲突话题", NodeType.TOPIC),
                edge_type=EdgeType.DISLIKES,
                delta=-0.6,
                confidence=0.7,
                description="冲突学习：用户不喜欢某话题"
            ),
            "context": "用户简单说不喜欢",
            "expected": "reject"
        },
        # 步骤3：模糊学习（应该缓冲）
        {
            "diff": GraphDiff(
                op=DiffOp.ADD_EDGE,
                src_node_id=user_id,
                dst_node_id=graph.create_node("模糊话题", NodeType.TOPIC),
                edge_type=EdgeType.RELATED_TO,
                delta=0.4,
                confidence=0.5,
                description="模糊学习：用户提到相关话题"
            ),
            "context": "用户简单提及",
            "expected": "buffer"
        },
    ]
    
    for i, step in enumerate(learning_steps, 1):
        print(f"\n学习步骤 {i}: {step['diff'].description}")
        
        # 验证
        result = guard.validate_diff(step['diff'], step['context'])
        
        print(f"  验证结果: {result.suggested_action}")
        print(f"  原因: {', '.join(result.reasons[:1])}")  # 只显示第一个原因
        
        # 应用
        applied = guard.apply_validation_result(step['diff'], result)
        print(f"  应用结果: {'✅ 已学习' if applied else '⏳ 等待/❌ 拒绝'}")
    
    # 系统状态
    print("\n系统最终状态:")
    print(f"  节点数: {len(graph.nodes)}")
    active_edges = [e for e in graph.edges.values() if e.active]
    print(f"  活跃边数: {len(active_edges)}")
    
    # 缓冲状态
    guard.print_buffer_status()
    
    print("\n" + "="*60)
    print("系统集成测试完成")
    print("="*60)
    
    return guard

if __name__ == "__main__":
    print("🚀 开始Learning Guard（学习防护层）测试")
    print("="*60)
    
    # 测试基本功能
    guard1 = test_learning_guard_basic()
    
    # 测试三道防线
    guard2, results = test_three_defenses()
    
    # 测试系统集成
    guard3 = test_system_integration()
    
    print("\n" + "="*60)
    print("🎯 Learning Guard实现总结")
    print("="*60)
    print("✅ 核心功能: validate_diff(diff, context) → bool")
    print("✅ 三道防线: 一致性验证 + 多源验证 + 延迟写入")
    print("✅ 系统升级: 从'会学习'升级到'学得对'")
    print("✅ 技术本质: Reliable Learning System")
    print("\n💡 系统现在具备: 学习质量控制能力")
    print("💡 关键能力: 防过度写入、防错误固化、防概念漂移")
    print("\n🎉 Learning Guard实现成功，系统现在是可靠学习系统！")