#!/usr/bin/env python3
"""
Belief Layer Integration（信念层整合）
将信念分类接入实体提取和冥思流程。
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class BeliefType(str, Enum):
    """信念类型"""
    FACT = "fact"          # 客观事实（如 "Neo4j 是图数据库"）
    PREFERENCE = "preference"  # 用户偏好（如 "我喜欢Python"）
    INFERENCE = "inference"    # 推断关系（如 "因为A所以B"）
    TEMPORAL = "temporal"      # 时间性结论（易变化，如 "今天下雨"）
    OTHER = "other"            # 默认


# 信念分类规则
_BELIEF_CLASSIFICATION_RULES = {
    BeliefType.PREFERENCE: [
        r"喜欢", r"偏好", r"爱好", r"倾向于", r"偏爱",
        r"讨厌", r"不喜欢", r"厌恶", r"反感",
        r"觉得.*好", r"认为.*不错", r"习惯",
    ],
    BeliefType.INFERENCE: [
        r"因为.*所以", r"导致", r"引起", r"造成",
        r"因此", r"因而", r"由此可见", r"可以推断",
        r"意味着", r"表明", r"说明.*原因",
    ],
    BeliefType.TEMPORAL: [
        r"今天", r"现在", r"当前", r"目前", r"最近",
        r"刚刚", r"刚才", r"马上", r"即将", r"即将在",
        r"\d{4}年", r"\d{4}-\d{2}-\d{2}",
    ],
}

# 事实关键词（如果包含这些且不属于上述任何类型，则为事实）
_FACT_INDICATORS = [
    r"是", r"有", r"包括", r"包含", r"由.*组成",
    r"支持", r"依赖", r"需要", r"使用",
    r"运行在", r"部署在", r"位于",
]


def classify_belief(text: str, entity_name: Optional[str] = None,
                    entity_type: Optional[str] = None) -> Tuple[BeliefType, float]:
    """
    对实体/文本进行信念分类（轻量级，无需 LLM）。

    Args:
        text: 源文本或上下文
        entity_name: 实体名称（可选）
        entity_type: 实体类型（可选）

    Returns:
        (信念类型, 置信度 0~1)
    """
    if not text and not entity_name:
        return BeliefType.OTHER, 0.5

    check_text = text or entity_name or ""

    # 优先级匹配：偏好 > 推断 > 时间性 > 事实 > 其他
    for belief_type, patterns in _BELIEF_CLASSIFICATION_RULES.items():
        for pattern in patterns:
            if re.search(pattern, check_text):
                confidence = min(1.0, 0.6 + 0.1 * len([
                    p for p in patterns if re.search(p, check_text)
                ]))
                return belief_type, confidence

    # 检查是否为事实
    fact_matches = sum(1 for p in _FACT_INDICATORS if re.search(p, check_text))
    if fact_matches > 0:
        return BeliefType.FACT, min(1.0, 0.5 + 0.15 * fact_matches)

    # 根据实体类型推断
    if entity_type:
        type_map = {
            "person": (BeliefType.FACT, 0.7),
            "technology": (BeliefType.FACT, 0.75),
            "organization": (BeliefType.FACT, 0.7),
            "event": (BeliefType.TEMPORAL, 0.6),
            "concept": (BeliefType.INFERENCE, 0.5),
            "preference": (BeliefType.PREFERENCE, 0.8),
        }
        if entity_type.lower() in type_map:
            return type_map[entity_type.lower()]

    return BeliefType.OTHER, 0.5


def compute_belief_strength(
    belief_type: BeliefType,
    mention_count: int = 1,
    conflict_count: int = 0,
    consistency: float = 1.0,
) -> float:
    """
    计算信念强度。

    Args:
        belief_type: 信念类型
        mention_count: 提及次数
        conflict_count: 冲突次数
        consistency: 一致性 (0~1)

    Returns:
        信念强度 (0~1)
    """
    # 基础强度
    base = {
        BeliefType.FACT: 0.8,
        BeliefType.PREFERENCE: 0.6,
        BeliefType.INFERENCE: 0.5,
        BeliefType.TEMPORAL: 0.4,
        BeliefType.OTHER: 0.5,
    }.get(belief_type, 0.5)

    # 提及次数加成
    mention_bonus = 0.05 * min(3, mention_count)  # 最多 +0.15

    # 冲突扣分
    conflict_penalty = 0.1 * min(conflict_count, 3)  # 最多 -0.3

    # 一致性加成
    consistency_bonus = 0.1 * consistency

    strength = max(0.0, min(1.0,
        base + mention_bonus - conflict_penalty + consistency_bonus
    ))
    return round(strength, 3)


# ================================================================
# Neo4j Cypher 辅助函数
# ================================================================

def belief_to_cypher_properties(
    belief_type: BeliefType,
    strength: float,
    context_text: Optional[str] = None,
) -> Dict[str, Any]:
    """将信念信息转换为可存入 Neo4j 的属性字典。"""
    props = {
        "belief_type": belief_type.value,
        "belief_strength": strength,
    }
    if context_text:
        props["belief_context"] = context_text
    return props


def cypher_set_belief_properties(prefix: str = "e") -> str:
    """
    生成 Cypher SET 子句，用于在创建/更新节点时设置信念属性。

    Returns:
        Cypher SET 片段
    """
    return f"""
        {prefix}.belief_type = $belief_type,
        {prefix}.belief_strength = $belief_strength,
        {prefix}.belief_updated_at = timestamp()
    """.strip()