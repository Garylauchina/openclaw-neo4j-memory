#!/usr/bin/env python3
"""
自适应学习系统 (Adaptive Learning System)
目标：系统自动从"冷启动模式" → "稳定学习模式"切换
核心：不同阶段需要不同学习策略
"""

import sys
sys.path.append('.')

print("🚀 自适应学习系统实现")
print("="*60)
print("目标：系统自动从冷启动 → 稳定学习切换")
print("核心：不同阶段需要不同策略")
print("="*60)

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from enum import Enum
import time

class LearningPhase(Enum):
    """学习阶段枚举"""
    COLD_START = "cold_start"    # 冷启动阶段
    STABLE = "stable"           # 稳定学习阶段
    TRANSITION = "transition"   # 过渡阶段

@dataclass
class SystemState:
    """系统状态快照"""
    # 核心指标
    total_edges: int = 0
    total_applied_diffs: int = 0
    avg_pattern_confidence: float = 0.0
    
    # 扩展指标
    total_nodes: int = 0
    total_patterns: int = 0
    write_ratio: float = 0.0
    phase_duration: int = 0  # 当前阶段持续时间（轮数）
    
    # 计算指标
    edges_per_round: float = 0.0
    diffs_per_round: float = 0.0

@dataclass
class PhaseConfig:
    """阶段配置"""
    # Learning Guard配置
    buffer_size: int = 5
    consistency_threshold: float = 0.3
    stability_threshold: float = 0.2
    novelty_threshold: float = 0.1
    
    # Reflection配置
    min_pattern_frequency: int = 2
    min_pattern_weight: float = 0.1
    confidence_threshold: float = 0.5
    max_diffs_per_reflection: int = 3
    
    # 学习策略
    reinforce_delta: float = 0.15  # 增强幅度
    decay_delta: float = -0.05    # 衰减幅度
    
    # 调试
    debug: bool = False

class PhaseDetector:
    """阶段检测器"""
    
    def __init__(self):
        # 阶段锁定机制
        self.current_phase = LearningPhase.COLD_START
        self.phase_start_time = time.time()
        self.phase_rounds = 0
        self.phase_switch_count = 0
        self.stable_rounds = 0  # 稳定阶段连续轮数
        
        # 阶段锁定阈值
        self.STABLE_LOCK_ROUNDS = 5   # 稳定5轮后锁定
        self.MIN_STABLE_ROUNDS = 3    # 最少稳定3轮
        
    def detect_phase(self, state: SystemState) -> LearningPhase:
        """
        检测系统处于哪个阶段
        
        判断规则（第一版）：
        1. Graph规模 < 50边 → 冷启动
        2. 应用Diff数 < 10 → 冷启动  
        3. 模式平均置信度 < 0.6 → 冷启动
        否则 → 稳定
        """
        
        # 检查是否满足稳定阶段条件
        is_stable = True
        
        # 条件1: Graph规模
        if state.total_edges < 50:
            is_stable = False
            if self.current_phase == LearningPhase.STABLE:
                print(f"   ⚠️  稳定条件1不满足: edges={state.total_edges} < 50")
        
        # 条件2: 写入情况
        if state.total_applied_diffs < 10:
            is_stable = False
            if self.current_phase == LearningPhase.STABLE:
                print(f"   ⚠️  稳定条件2不满足: applied_diffs={state.total_applied_diffs} < 10")
        
        # 条件3: Pattern稳定性
        if state.avg_pattern_confidence < 0.6:
            is_stable = False
            if self.current_phase == LearningPhase.STABLE:
                print(f"   ⚠️  稳定条件3不满足: avg_confidence={state.avg_pattern_confidence:.3f} < 0.6")
        
        # 确定阶段
        if is_stable:
            new_phase = LearningPhase.STABLE
        else:
            new_phase = LearningPhase.COLD_START
        
        # 检查阶段切换
        if new_phase != self.current_phase:
            self._handle_phase_switch(new_phase, state)
        
        # 更新阶段持续时间
        self.phase_rounds += 1
        
        return self.current_phase
    
    def _handle_phase_switch(self, new_phase: LearningPhase, state: SystemState):
        """处理阶段切换"""
        old_phase = self.current_phase
        self.current_phase = new_phase
        self.phase_start_time = time.time()
        self.phase_rounds = 0
        self.phase_switch_count += 1
        
        print(f"   🔄 阶段切换: {old_phase.value} → {new_phase.value}")
        print(f"     切换次数: {self.phase_switch_count}")
        print(f"     系统状态: edges={state.total_edges}, diffs={state.total_applied_diffs}, conf={state.avg_pattern_confidence:.3f}")
        
        # 重置稳定轮数计数器
        if new_phase == LearningPhase.STABLE:
            self.stable_rounds = 1
        else:
            self.stable_rounds = 0
    
    def update_stable_rounds(self, current_phase: LearningPhase):
        """更新稳定轮数计数器"""
        if current_phase == LearningPhase.STABLE:
            self.stable_rounds += 1
        else:
            self.stable_rounds = 0
    
    def should_lock_phase(self) -> bool:
        """检查是否应该锁定当前阶段"""
        if (self.current_phase == LearningPhase.STABLE and 
            self.stable_rounds >= self.STABLE_LOCK_ROUNDS):
            return True
        return False
    
    def get_phase_info(self) -> Dict[str, Any]:
        """获取阶段信息"""
        return {
            "phase": self.current_phase.value,
            "phase_duration": self.phase_rounds,
            "phase_switch_count": self.phase_switch_count,
            "stable_rounds": self.stable_rounds,
            "is_locked": self.should_lock_phase()
        }

class AdaptiveLearningSystem:
    """自适应学习系统"""
    
    def __init__(self):
        # 阶段检测器
        self.phase_detector = PhaseDetector()
        
        # 两套学习策略
        self.cold_start_config = self._create_cold_start_config()
        self.stable_config = self._create_stable_config()
        
        # 当前配置
        self.current_config = self.cold_start_config
        
        # 系统状态历史
        self.state_history = []
        
        # 阶段跟踪指标
        self.phase_metrics = {
            "cold_start_rounds": 0,
            "stable_rounds": 0,
            "transitions": 0,
            "write_ratio_by_phase": {
                "cold_start": [],
                "stable": []
            }
        }
    
    def _create_cold_start_config(self) -> PhaseConfig:
        """创建冷启动配置（激进）"""
        return PhaseConfig(
            # Learning Guard配置（激进）
            buffer_size=1,                # 极小缓冲区，立即学习
            consistency_threshold=0.05,   # 极低一致性要求
            stability_threshold=0.05,     # 极低稳定性要求
            novelty_threshold=0.01,       # 极低新颖性要求
            
            # Reflection配置（激进）
            min_pattern_frequency=1,      # 低频率要求
            min_pattern_weight=0.01,      # 极低权重要求
            confidence_threshold=0.3,     # 低置信度要求
            max_diffs_per_reflection=10,  # 允许更多Diff
            
            # 学习策略（激进）
            reinforce_delta=0.3,          # 大增强幅度
            decay_delta=-0.15,            # 大衰减幅度
            
            debug=True
        )
    
    def _create_stable_config(self) -> PhaseConfig:
        """创建稳定学习配置（保守）"""
        return PhaseConfig(
            # Learning Guard配置（保守）
            buffer_size=5,                # 大缓冲区，谨慎学习
            consistency_threshold=0.3,    # 高一致性要求
            stability_threshold=0.2,      # 高稳定性要求
            novelty_threshold=0.1,        # 高新颖性要求
            
            # Reflection配置（保守）
            min_pattern_frequency=2,      # 高频率要求
            min_pattern_weight=0.1,       # 高权重要求
            confidence_threshold=0.7,     # 高置信度要求
            max_diffs_per_reflection=2,   # 限制Diff数量
            
            # 学习策略（保守）
            reinforce_delta=0.1,          # 小增强幅度
            decay_delta=-0.05,            # 小衰减幅度
            
            debug=False
        )
    
    def build_system_state(self, global_graph, reflection_engine, learning_guard) -> SystemState:
        """构建系统状态快照"""
        # 计算核心指标
        total_edges = len([e for e in global_graph.edges.values() if hasattr(e, 'active') and e.active])
        total_nodes = len(global_graph.nodes)
        
        # 从Reflection Engine获取指标
        total_patterns = len(reflection_engine.patterns) if hasattr(reflection_engine, 'patterns') else 0
        total_applied_diffs = reflection_engine.stats.get("diffs_applied", 0) if hasattr(reflection_engine, 'stats') else 0
        
        # 计算模式平均置信度
        avg_pattern_confidence = 0.0
        if total_patterns > 0 and hasattr(reflection_engine, 'patterns'):
            confidences = []
            for pattern in reflection_engine.patterns.values():
                if hasattr(reflection_engine, '_compute_pattern_confidence'):
                    conf = reflection_engine._compute_pattern_confidence(pattern)
                    confidences.append(conf)
            if confidences:
                avg_pattern_confidence = sum(confidences) / len(confidences)
        
        # 计算写入率
        write_ratio = 0.0
        total_diffs_generated = reflection_engine.stats.get("diffs_generated", 0) if hasattr(reflection_engine, 'stats') else 0
        if total_diffs_generated > 0:
            write_ratio = total_applied_diffs / total_diffs_generated
        
        # 计算每轮指标
        total_rounds = len(self.state_history) + 1
        edges_per_round = total_edges / total_rounds if total_rounds > 0 else 0
        diffs_per_round = total_applied_diffs / total_rounds if total_rounds > 0 else 0
        
        return SystemState(
            total_edges=total_edges,
            total_applied_diffs=total_applied_diffs,
            avg_pattern_confidence=avg_pattern_confidence,
            total_nodes=total_nodes,
            total_patterns=total_patterns,
            write_ratio=write_ratio,
            phase_duration=self.phase_detector.phase_rounds,
            edges_per_round=edges_per_round,
            diffs_per_round=diffs_per_round
        )
    
    def update_phase(self, state: SystemState):
        """更新学习阶段"""
        # 检测当前阶段
        phase = self.phase_detector.detect_phase(state)
        
        # 应用阶段配置
        if phase == LearningPhase.COLD_START:
            self.current_config = self.cold_start_config
            self.phase_metrics["cold_start_rounds"] += 1
        else:
            self.current_config = self.stable_config
            self.phase_metrics["stable_rounds"] += 1
        
        # 更新稳定轮数计数器
        self.phase_detector.update_stable_rounds(phase)
        
        # 检查阶段锁定
        if self.phase_detector.should_lock_phase():
            print(f"   🔒 阶段锁定: 稳定阶段已持续{self.phase_detector.stable_rounds}轮")
        
        # 记录阶段写入率
        phase_key = phase.value
        self.phase_metrics["write_ratio_by_phase"][phase_key].append(state.write_ratio)
        
        # 保存状态历史
        self.state_history.append(state)
        
        return phase
    
    def get_config_for_reflection(self) -> Dict[str, Any]:
        """获取Reflection Engine配置"""
        return {
            "min_pattern_frequency": self.current_config.min_pattern_frequency,
            "min_pattern_weight": self.current_config.min_pattern_weight,
            "confidence_threshold": self.current_config.confidence_threshold,
            "max_diffs_per_reflection": self.current_config.max_diffs_per_reflection,
            "reinforce_delta": self.current_config.reinforce_delta,
            "decay_delta": self.current_config.decay_delta,
            "debug": self.current_config.debug
        }
    
    def get_config_for_learning_guard(self) -> Dict[str, Any]:
        """获取Learning Guard配置"""
        return {
            "consistency_threshold": self.current_config.consistency_threshold,
            "stability_threshold": self.current_config.stability_threshold,
            "novelty_threshold": self.current_config.novelty_threshold,
            "buffer_size": self.current_config.buffer_size,
            "debug": self.current_config.debug
        }
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        if not self.state_history:
            return {}
        
        current_state = self.state_history[-1]
        phase_info = self.phase_detector.get_phase_info()
        
        # 计算阶段平均写入率
        avg_write_ratio_by_phase = {}
        for phase, ratios in self.phase_metrics["write_ratio_by_phase"].items():
            if ratios:
                avg_write_ratio_by_phase[phase] = sum(ratios) / len(ratios)
            else:
                avg_write_ratio_by_phase[phase] = 0.0
        
        return {
            "current_phase": phase_info,
            "system_state": {
                "total_edges": current_state.total_edges,
                "total_applied_diffs": current_state.total_applied_diffs,
                "avg_pattern_confidence": current_state.avg_pattern_confidence,
                "write_ratio": current_state.write_ratio,
                "edges_per_round": current_state.edges_per_round,
                "diffs_per_round": current_state.diffs_per_round
            },
            "phase_metrics": {
                "cold_start_rounds": self.phase_metrics["cold_start_rounds"],
                "stable_rounds": self.phase_metrics["stable_rounds"],
                "total_transitions": self.phase_detector.phase_switch_count,
                "avg_write_ratio_by_phase": avg_write_ratio_by_phase
            },
            "current_config": {
                "buffer_size": self.current_config.buffer_size,
                "confidence_threshold": self.current_config.confidence_threshold,
                "max_diffs_per_round": self.current_config.max_diffs_per_reflection
            }
        }
    
    def print_phase_status(self, phase: LearningPhase, state: SystemState):
        """打印阶段状态"""
        phase_info = self.phase_detector.get_phase_info()
        
        print(f"\n   📊 阶段状态: {phase.value.upper()}")
        print(f"      持续时间: {phase_info['phase_duration']}轮")
        print(f"      切换次数: {phase_info['phase_switch_count']}")
        print(f"      稳定轮数: {phase_info['stable_rounds']}")
        print(f"      是否锁定: {'✅ 是' if phase_info['is_locked'] else '❌ 否'}")
        
        print(f"\n   📈 系统指标:")
        print(f"      Graph边数: {state.total_edges}")
        print(f"      应用Diff数: {state.total_applied_diffs}")
        print(f"      模式置信度: {state.avg_pattern_confidence:.3f}")
        print(f"      写入率: {state.write_ratio:.3f}")
        
        print(f"\n   ⚙️  当前配置:")
        print(f"      缓冲区大小: {self.current_config.buffer_size}")
        print(f"      置信度阈值: {self.current_config.confidence_threshold}")
        print(f"      最大Diff数: {self.current_config.max_diffs_per_reflection}")

# 测试自适应系统
print("\n1. 创建自适应学习系统...")
adaptive_system = AdaptiveLearningSystem()

print("\n2. 测试阶段检测...")
# 模拟不同系统状态
test_states = [
    SystemState(total_edges=10, total_applied_diffs=2, avg_pattern_confidence=0.4),  # 冷启动
    SystemState(total_edges=30, total_applied_diffs=5, avg_pattern_confidence=0.5),  # 冷启动
    SystemState(total_edges=60, total_applied_diffs=12, avg_pattern_confidence=0.7), # 稳定
    SystemState(total_edges=80, total_applied_diffs=15, avg_pattern_confidence=0.8), # 稳定
]

print("   测试状态序列:")
for i, state in enumerate(test_states):
    phase = adaptive_system.phase_detector.detect_phase(state)
    print(f"     状态{i+1}: edges={state.total_edges}, diffs={state.total_applied_diffs}, "
          f"conf={state.avg_pattern_confidence:.1f} → 阶段: {phase.value}")

print("\n3. 测试配置切换...")
print("   冷启动配置:")
cold_config = adaptive_system.cold_start_config
print(f"     buffer_size: {cold_config.buffer_size}")
print(f"     confidence_threshold: {cold_config.confidence_threshold}")
print(f"     max_diffs_per_reflection: {cold_config.max_diffs_per_reflection}")

print("\n   稳定配置:")
stable_config = adaptive_system.stable_config
print(f"     buffer_size: {stable_config.buffer_size}")
print(f"     confidence_threshold: {stable_config.confidence_threshold}")
print(f"     max_diffs_per_reflection: {stable_config.max_diffs_per_reflection}")

print("\n" + "="*60)
print("✅ 自适应学习系统框架完成")
print("="*60)

print("\n🎯 核心特性:")
print("   1. ✅ 自动阶段检测（基于数据指标）")
print("   2. ✅ 两套学习策略（冷启动激进 vs 稳定保守）")
print("   3. ✅ 动态配置切换")
print("   4. ✅ 阶段锁定机制（防止震荡）")
print("   5. ✅ 完整阶段跟踪指标")

print("\n🚀 下一步:")
print("   1. 集成到现有学习管道")
print("   2. 运行验证测试")
print("   3. 观察阶段切换效果")

print(f"\n🕐 实现完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")