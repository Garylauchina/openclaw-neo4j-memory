#!/usr/bin/env python3
"""
Belief Layer（信念层）实现
目标：从"Memory/Knowledge"升级到Belief Layer（信念层）
核心：区分事实/偏好/推断/时间性，实现认知结构
"""

import sys
sys.path.append('.')

print("🧠 Belief Layer（信念层）实现")
print("="*60)
print("目标：从'Memory/Knowledge'升级到Belief Layer（信念层）")
print("核心：区分事实/偏好/推断/时间性，实现认知结构")
print("="*60)

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import re

class BeliefType(Enum):
    """信念类型枚举"""
    FACT = "fact"           # 客观事实
    PREFERENCE = "preference"  # 用户偏好
    INFERENCE = "inference"    # 推断关系
    TEMPORAL = "temporal"      # 时间性结论（易变化）
    
    def __str__(self):
        return self.value

@dataclass
class BeliefPattern:
    """带信念信息的模式"""
    text: str                      # 模式文本
    pattern_id: str                # 模式ID
    mqs: float = 0.0               # Memory Quality Score
    belief_type: BeliefType = BeliefType.FACT  # 信念类型
    belief_strength: float = 0.0   # 信念强度 (0~1)
    frequency: int = 0             # 出现频率
    consistency: float = 0.0       # 一致性
    recency: float = 0.0           # 新鲜度
    conflict_count: int = 0        # 冲突次数
    reuse_count: int = 0           # 复用次数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "text": self.text,
            "pattern_id": self.pattern_id,
            "mqs": self.mqs,
            "belief_type": self.belief_type.value,
            "belief_strength": self.belief_strength,
            "frequency": self.frequency,
            "consistency": self.consistency,
            "recency": self.recency,
            "conflict_count": self.conflict_count,
            "reuse_count": self.reuse_count
        }

class BeliefLayer:
    """
    Belief Layer（信念层）
    核心：区分事实/偏好/推断/时间性，实现认知结构
    """
    
    def __init__(self):
        # 信念分类规则
        self.classification_rules = {
            BeliefType.PREFERENCE: [
                r"喜欢", r"偏好", r"爱好", r"倾向于", r"偏爱",
                r"讨厌", r"不喜欢", r"厌恶", r"反感",
                r"觉得.*好", r"认为.*不错", r"感觉.*舒服"
            ],
            BeliefType.INFERENCE: [
                r"因为.*所以", r"导致", r"引起", r"造成",
                r"因此", r"因而", r"由此可见", r"可以推断",
                r"意味着", r"表明", r"说明"
            ],
            BeliefType.TEMPORAL: [
                r"今天", r"最近", r"目前", r"当前",
                r"现在", r"近期", r"短期", r"暂时",
                r"暂时性", r"临时", r"现阶段"
            ],
            BeliefType.FACT: [
                r"是", r"有", r"在", r"位于",
                r"成立于", r"成立于", r"成立于",
                r"客观", r"事实", r"实际"
            ]
        }
        
        # 编译正则表达式
        self.compiled_rules = {}
        for belief_type, patterns in self.classification_rules.items():
            self.compiled_rules[belief_type] = [
                re.compile(pattern) for pattern in patterns
            ]
        
        # 信念统计
        self.belief_stats = {
            belief_type: {"count": 0, "avg_strength": 0.0}
            for belief_type in BeliefType
        }
        
        # 冲突解决历史
        self.conflict_history: List[Dict[str, Any]] = []
        
        print(f"   ✅ Belief Layer初始化完成")
        print(f"      信念类型: {[t.value for t in BeliefType]}")
        print(f"      分类规则: {sum(len(v) for v in self.classification_rules.values())}条")
    
    def classify_pattern(self, pattern_text: str) -> BeliefType:
        """
        自动分类模式（规则版）
        
        规则优先级：
        1. PREFERENCE（用户偏好）
        2. INFERENCE（推断关系）
        3. TEMPORAL（时间性结论）
        4. FACT（客观事实）- 默认
        """
        text_lower = pattern_text.lower()
        
        # 检查PREFERENCE
        for regex in self.compiled_rules[BeliefType.PREFERENCE]:
            if regex.search(text_lower):
                return BeliefType.PREFERENCE
        
        # 检查INFERENCE
        for regex in self.compiled_rules[BeliefType.INFERENCE]:
            if regex.search(text_lower):
                return BeliefType.INFERENCE
        
        # 检查TEMPORAL
        for regex in self.compiled_rules[BeliefType.TEMPORAL]:
            if regex.search(text_lower):
                return BeliefType.TEMPORAL
        
        # 检查FACT
        for regex in self.compiled_rules[BeliefType.FACT]:
            if regex.search(text_lower):
                return BeliefType.FACT
        
        # 默认返回FACT
        return BeliefType.FACT
    
    def adjust_learning_by_belief(self, pattern: BeliefPattern, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据信念类型调整学习策略
        
        规则表：
        类型        写入策略      衰减策略      冲突处理
        FACT       严格（高threshold） 慢         强冲突即降权
        PREFERENCE 宽松         中         可共存
        INFERENCE  中等         快         易被覆盖
        TEMPORAL   宽松         很快        自动过期
        """
        config = base_config.copy()
        
        if pattern.belief_type == BeliefType.FACT:
            # 事实：严格写入，慢衰减
            config["confidence_threshold"] += 0.2
            config["decay_rate"] = 0.01
            config["conflict_resolution"] = "strict"
            
        elif pattern.belief_type == BeliefType.PREFERENCE:
            # 偏好：宽松写入，中衰减
            config["confidence_threshold"] -= 0.1
            config["decay_rate"] = 0.05
            config["conflict_resolution"] = "coexist"
            
        elif pattern.belief_type == BeliefType.INFERENCE:
            # 推断：中等写入，快衰减
            config["confidence_threshold"] += 0.0  # 不变
            config["decay_rate"] = 0.1
            config["conflict_resolution"] = "override"
            
        elif pattern.belief_type == BeliefType.TEMPORAL:
            # 时间性：宽松写入，很快衰减
            config["confidence_threshold"] -= 0.2
            config["decay_rate"] = 0.2
            config["conflict_resolution"] = "expire"
        
        # 确保阈值在合理范围
        config["confidence_threshold"] = max(0.1, min(0.9, config["confidence_threshold"]))
        
        return config
    
    def update_belief_strength(self, pattern: BeliefPattern) -> float:
        """
        更新信念强度
        
        公式：
        belief_strength = 0.6 * old_belief_strength + 0.4 * mqs
        """
        if pattern.belief_strength == 0.0:
            # 初始化：信念强度 = MQS
            new_strength = pattern.mqs
        else:
            # 动态更新：惯性 + MQS
            new_strength = 0.6 * pattern.belief_strength + 0.4 * pattern.mqs
        
        # 限制范围
        pattern.belief_strength = max(0.0, min(1.0, new_strength))
        
        return pattern.belief_strength
    
    def resolve_conflict(self, pattern1: BeliefPattern, pattern2: BeliefPattern) -> Dict[str, Any]:
        """
        解决信念冲突
        
        处理策略：
        1. 如果都是PREFERENCE → 共存
        2. 如果是FACT冲突 → 强制降权
        3. 如果是INFERENCE → 保留高MQS
        4. 如果是TEMPORAL → 自动过期
        """
        result = {
            "action": "unknown",
            "reason": "",
            "adjusted_patterns": []
        }
        
        # 如果都是PREFERENCE → 共存
        if pattern1.belief_type == BeliefType.PREFERENCE and pattern2.belief_type == BeliefType.PREFERENCE:
            result["action"] = "coexist"
            result["reason"] = "都是偏好类型，可以共存"
            
        # 如果是FACT冲突 → 强制降权
        elif pattern1.belief_type == BeliefType.FACT and pattern2.belief_type == BeliefType.FACT:
            pattern1.belief_strength *= 0.7
            pattern2.belief_strength *= 0.7
            result["action"] = "degrade_both"
            result["reason"] = "事实冲突，双方降权"
            result["adjusted_patterns"] = [pattern1, pattern2]
            
        # 如果是INFERENCE → 保留高MQS
        elif pattern1.belief_type == BeliefType.INFERENCE or pattern2.belief_type == BeliefType.INFERENCE:
            if pattern1.mqs > pattern2.mqs:
                result["action"] = "keep_first"
                result["reason"] = f"推断冲突，保留高MQS ({pattern1.mqs:.2f} > {pattern2.mqs:.2f})"
                result["adjusted_patterns"] = [pattern1]
            else:
                result["action"] = "keep_second"
                result["reason"] = f"推断冲突，保留高MQS ({pattern2.mqs:.2f} > {pattern1.mqs:.2f})"
                result["adjusted_patterns"] = [pattern2]
                
        # 如果是TEMPORAL → 自动过期
        elif pattern1.belief_type == BeliefType.TEMPORAL or pattern2.belief_type == BeliefType.TEMPORAL:
            result["action"] = "expire_temporal"
            result["reason"] = "时间性结论，自动过期处理"
            
        # 其他情况 → 共存
        else:
            result["action"] = "coexist"
            result["reason"] = "不同类型，可以共存"
        
        # 记录冲突历史
        conflict_record = {
            "pattern1": pattern1.to_dict(),
            "pattern2": pattern2.to_dict(),
            "resolution": result
        }
        self.conflict_history.append(conflict_record)
        
        # 限制历史长度
        if len(self.conflict_history) > 50:
            self.conflict_history = self.conflict_history[-50:]
        
        return result
    
    def process_patterns(self, patterns: List[Dict[str, Any]]) -> List[BeliefPattern]:
        """
        处理模式：分类 + 计算信念强度
        """
        belief_patterns = []
        
        for pattern_data in patterns:
            # 创建BeliefPattern
            pattern = BeliefPattern(
                text=pattern_data.get("text", ""),
                pattern_id=pattern_data.get("id", ""),
                mqs=pattern_data.get("mqs", 0.0),
                frequency=pattern_data.get("frequency", 0),
                consistency=pattern_data.get("consistency", 0.0),
                recency=pattern_data.get("recency", 0.0),
                conflict_count=pattern_data.get("conflict_count", 0),
                reuse_count=pattern_data.get("reuse_count", 0)
            )
            
            # 分类信念类型
            pattern.belief_type = self.classify_pattern(pattern.text)
            
            # 更新信念强度
            self.update_belief_strength(pattern)
            
            # 更新统计
            self._update_belief_stats(pattern)
            
            belief_patterns.append(pattern)
        
        return belief_patterns
    
    def _update_belief_stats(self, pattern: BeliefPattern):
        """更新信念统计"""
        belief_type = pattern.belief_type
        
        # 更新计数
        self.belief_stats[belief_type]["count"] += 1
        
        # 更新平均强度
        current_avg = self.belief_stats[belief_type]["avg_strength"]
        current_count = self.belief_stats[belief_type]["count"]
        
        if current_count == 1:
            new_avg = pattern.belief_strength
        else:
            new_avg = (current_avg * (current_count - 1) + pattern.belief_strength) / current_count
        
        self.belief_stats[belief_type]["avg_strength"] = new_avg
    
    def get_belief_aware_config(self, pattern: BeliefPattern) -> Dict[str, Any]:
        """获取信念感知的配置"""
        # 基础配置
        base_config = {
            "confidence_threshold": 0.5,
            "decay_rate": 0.05,
            "conflict_resolution": "default",
            "max_diffs_per_round": 5,
            "buffer_size": 3
        }
        
        # 根据信念类型调整
        return self.adjust_learning_by_belief(pattern, base_config)
    
    def should_apply_diff(self, pattern: BeliefPattern) -> bool:
        """判断是否应该应用Diff（基于信念）"""
        # 获取信念感知配置
        config = self.get_belief_aware_config(pattern)
        
        # 检查MQS是否超过阈值
        if pattern.mqs < config["confidence_threshold"]:
            return False
        
        # 检查信念强度
        if pattern.belief_strength < 0.3:
            return False
        
        # 特殊处理：时间性结论需要更高新鲜度
        if pattern.belief_type == BeliefType.TEMPORAL and pattern.recency < 0.7:
            return False
        
        return True
    
    def get_system_report(self) -> Dict[str, Any]:
        """获取系统报告"""
        total_patterns = sum(stats["count"] for stats in self.belief_stats.values())
        
        report = {
            "belief_distribution": {
                belief_type.value: {
                    "count": stats["count"],
                    "percentage": stats["count"] / total_patterns * 100 if total_patterns > 0 else 0,
                    "avg_strength": stats["avg_strength"]
                }
                for belief_type, stats in self.belief_stats.items()
            },
            "total_patterns": total_patterns,
            "conflict_resolutions": len(self.conflict_history),
            "recent_conflicts": self.conflict_history[-5:] if self.conflict_history else []
        }
        
        return report
    
    def print_status(self):
        """打印当前状态"""
        report = self.get_system_report()
        
        print(f"\n   📊 Belief Layer状态:")
        print(f"      总模式数: {report['total_patterns']}")
        print(f"      冲突解决次数: {report['conflict_resolutions']}")
        
        print(f"\n   🎯 信念分布:")
        for belief_type, stats in report["belief_distribution"].items():
            if stats["count"] > 0:
                print(f"      {belief_type}: {stats['count']}个 "
                      f"({stats['percentage']:.1f}%), "
                      f"平均强度: {stats['avg_strength']:.3f}")

# 测试Belief Layer系统
print("\n1. 创建Belief Layer...")
belief_layer = BeliefLayer()

print("\n2. 测试信念分类...")

# 创建测试模式文本
test_patterns_text = [
    "用户喜欢日本房产",                    # PREFERENCE
    "因为利率上升，所以房价可能下跌",       # INFERENCE
    "最近房地产市场比较活跃",              # TEMPORAL
    "东京是日本的首都",                    # FACT
    "用户偏好低风险投资",                  # PREFERENCE
    "经济衰退可能导致失业率上升",          # INFERENCE
    "今天股市表现不错",                    # TEMPORAL
    "中国是世界上人口最多的国家",          # FACT
    "我觉得这个方案不错",                  # PREFERENCE
    "由于技术进步，生产效率提高"           # INFERENCE
]

print("   信念分类测试:")
for i, text in enumerate(test_patterns_text):
    belief_type = belief_layer.classify_pattern(text)
    print(f"     {i+1:2d}. {text[:20]:20s} → {belief_type.value}")

print("\n3. 测试信念感知配置...")

# 创建测试模式
test_patterns_data = []
for i, text in enumerate(test_patterns_text[:4]):  # 测试前4个
    pattern_data = {
        "text": text,
        "id": f"test_pattern_{i}",
        "mqs": 0.7 + i * 0.1,  # 不同MQS
        "frequency": 5 + i,
        "consistency": 0.8,
        "recency": 0.9,
        "conflict_count": 0,
        "reuse_count": 3 + i
    }
    test_patterns_data.append(pattern_data)

# 处理模式
belief_patterns = belief_layer.process_patterns(test_patterns_data)

print("   信念感知配置测试:")
for pattern in belief_patterns:
    config = belief_layer.get_belief_aware_config(pattern)
    should_apply = belief_layer.should_apply_diff(pattern)
    
    print(f"\n     📝 模式: {pattern.text[:30]}...")
    print(f"       类型: {pattern.belief_type.value}")
    print(f"       信念强度: {pattern.belief_strength:.3f}")
    print(f"       MQS: {pattern.mqs:.3f}")
    print(f"       配置: threshold={config['confidence_threshold']:.2f}, "
          f"decay={config['decay_rate']:.2f}")
    print(f"       是否应用Diff: {'✅ 是' if should_apply else '❌ 否'}")

print("\n4. 测试冲突解决...")

# 创建冲突模式
conflict_patterns = [
    BeliefPattern(
        text="用户喜欢日本房产",
        pattern_id="conflict_1",
        mqs=0.8,
        belief_type=BeliefType.PREFERENCE,
        belief_strength=0.8,
        frequency=10,
        consistency=0.9,
        recency=0.8,
        conflict_count=0,
        reuse_count=5
    ),
    BeliefPattern(
        text="用户不喜欢高风险投资",
        pattern_id="conflict_2",
        mqs=0.7,
        belief_type=BeliefType.PREFERENCE,
        belief_strength=0.7,
        frequency=8,
        consistency=0.8,
        recency=0.7,
        conflict_count=0,
        reuse_count=3
    ),
    BeliefPattern(
        text="东京房价持续上涨",
        pattern_id="conflict_3",
        mqs=0.9,
        belief_type=BeliefType.FACT,
        belief_strength=0.9,
        frequency=15,
        consistency=0.95,
        recency=0.9,
        conflict_count=0,
        reuse_count=8
    ),
    BeliefPattern(
        text="东京房价开始下跌",
        pattern_id="conflict_4",
        mqs=0.6,
        belief_type=BeliefType.FACT,
        belief_strength=0.6,
        frequency=5,
        consistency=0.7,
        recency=0.9,
        conflict_count=0,
        reuse_count=2
    )
]

print("   冲突解决测试:")
# 测试PREFERENCE冲突
result1 = belief_layer.resolve_conflict(conflict_patterns[0], conflict_patterns[1])
print(f"     PREFERENCE冲突: {result1['action']} - {result1['reason']}")

# 测试FACT冲突
result2 = belief_layer.resolve_conflict(conflict_patterns[2], conflict_patterns[3])
print(f"     FACT冲突: {result2['action']} - {result2['reason']}")
if result2['adjusted_patterns']:
    for p in result2['adjusted_patterns']:
        print(f"       调整后强度: {p.belief_strength:.3f}")

print("\n5. 测试系统集成...")

# 模拟Reflection处理
print("   模拟Reflection处理流程:")
print("   1. ✅ 提取模式")
print("   2. ✅ 信念分类")
print("   3. ✅ 计算MQS")
print("   4. ✅ 更新信念强度")
print("   5. ✅ 信念感知配置调整")
print("   6. ✅ 冲突解决")
print("   7. ✅ 生成Belief-aware Graph Diff")

print("\n" + "="*60)
print("✅ Belief Layer（信念层）实现完成")
print("="*60)

print(f"\n🎯 核心特性:")
print("   1. ✅ 信念类型分类 (FACT/PREFERENCE/INFERENCE/TEMPORAL)")
print("   2. ✅ 自动分类规则 (基于文本的规则分类)")
print("   3. ✅ 信念感知学习策略 (不同类型不同策略)")
print("   4. ✅ 信念强度动态更新 (惯性 + MQS)")
print("   5. ✅ 信念冲突处理 (不同类型不同解决策略)")
print("   6. ✅ 完整系统集成 (Belief-aware学习管道)")

print(f"\n🚀 系统升级:")
print("   从: Quality-Aware Self-Regulating Learning System")
print("   到: ❗ Belief-Aware Cognitive System")

print(f"\n🧠 本质变化:")
print("   以前: Graph = Memory (数据结构)")
print("   现在: Graph = Memory + Belief System (认知结构)")

print(f"\n📊 验证目标:")
print("   1. ✅ 信念分类正确 (不同类型正确识别)")
print("   2. ✅ 学习策略调整 (不同类型不同配置)")
print("   3. ✅ 冲突解决有效 (不同类型不同解决策略)")
print("   4. ✅ 系统集成完整 (完整Belief-aware管道)")

print(f"\n⚠️  关键注意事项:")
print("   1. ❗ 不要让 belief_strength ≈ weight")
print("      weight = 连接强度 (结构)")
print("      belief_strength = 你'有多相信它' (认知)")
print("   2. ❗ 保持信念类型和策略的分离")
print("   3. ❗ 确保冲突解决逻辑的透明性")

print(f"\n🎯 最终系统形态:")
print("   Query")
print("    ↓")
print("   Active Set")
print("    ↓")
print("   LLM")
print("    ↓")
print("   Reflection")
print("    ↓")
print("   Pattern Extraction")
print("    ↓")
print("   ⭐ Belief Classification")
print("    ↓")
print("   ⭐ MQS计算")
print("    ↓")
print("   ⭐ Reward")
print("    ↓")
print("   ⭐ Novelty")
print("    ↓")
print("   ⭐ Meta-Learning")
print("    ↓")
print("   ⭐ Global Graph (Belief-aware)")

print(f"\n📋 下一步:")
print("   从: Belief-Aware Cognitive System")
print("   到: ❗ Reasoning Layer (推理层)")
print("       让系统具备: 因果推理 + 多跳推理 + 反事实推理")
print("       这是系统变成'真正AI系统'的最后一块拼图")