#!/usr/bin/env python3
"""
简单语义解析器（解决冷启动问题）

目标：将自然语言转换为结构化三元组，为Reflection提供输入信号
"""

import re
from typing import Optional, Tuple, List, Dict, Any


class SimpleSemanticParser:
    """简单规则级语义解析器"""
    
    def __init__(self):
        # 定义关键词到关系类型的映射
        self.relation_keywords = {
            "喜欢": "LIKES",
            "不喜欢": "DISLIKES",
            "爱": "LOVES",
            "讨厌": "HATES",
            "想要": "WANTS",
            "需要": "NEEDS",
            "投资": "INVESTED_IN",
            "学习": "LEARNING",
            "研究": "RESEARCHING",
            "关注": "FOLLOWING",
            "支持": "SUPPORTING",
            "反对": "OPPOSING"
        }
        
        # 实体类型识别
        self.entity_patterns = {
            "房产": "PROPERTY",
            "房产投资": "PROPERTY_INVESTMENT",
            "日本房产": "JAPAN_PROPERTY",
            "AI": "TECHNOLOGY",
            "人工智能": "TECHNOLOGY",
            "机器学习": "TECHNOLOGY",
            "深度学习": "TECHNOLOGY",
            "编程": "SKILL",
            "Python": "SKILL",
            "投资": "ACTIVITY",
            "学习": "ACTIVITY",
            "旅游": "ACTIVITY",
            "美食": "INTEREST",
            "音乐": "INTEREST",
            "电影": "INTEREST",
            "书籍": "INTEREST"
        }
        
        # 否定词
        self.negation_words = {"不", "没", "无", "非", "否"}
    
    def extract_entity(self, text: str) -> Tuple[str, str]:
        """从文本中提取实体和类型"""
        # 优先匹配已知实体模式
        for pattern, entity_type in self.entity_patterns.items():
            if pattern in text:
                return pattern, entity_type
        
        # 如果没有匹配，提取关键词作为实体
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
        if words:
            # 取第一个非关系关键词作为实体
            for word in words:
                if word not in self.relation_keywords and word not in self.negation_words:
                    return word, "GENERIC"
        
        return "未知", "UNKNOWN"
    
    def parse(self, text: str) -> Optional[Dict[str, Any]]:
        """
        解析文本为结构化三元组
        
        返回格式：
        {
            "subject": "USER",
            "relation": "INTERESTED_IN",
            "object": "日本房产",
            "object_type": "JAPAN_PROPERTY",
            "confidence": 0.8,
            "negation": False
        }
        """
        if not text or len(text.strip()) < 2:
            return None
        
        text_lower = text.lower()
        
        # 检测否定
        negation = any(neg in text for neg in self.negation_words)
        
        # 查找关系关键词
        relation = None
        relation_type = None
        
        for keyword, rel_type in self.relation_keywords.items():
            if keyword in text:
                relation = keyword
                relation_type = rel_type
                break
        
        if not relation:
            # 如果没有明确关系词，尝试推断
            if "?" in text or "？" in text or "如何" in text or "怎么" in text:
                relation_type = "ASKING_ABOUT"
            elif "是" in text or "为" in text:
                relation_type = "IS_A"
            else:
                # 默认关系
                relation_type = "MENTIONED"
        
        # 提取实体
        entity, entity_type = self.extract_entity(text)
        
        # 计算置信度
        confidence = 0.6  # 基础置信度
        
        if relation in self.relation_keywords:
            confidence += 0.2
        
        if entity_type != "UNKNOWN":
            confidence += 0.1
        
        if negation:
            confidence -= 0.1
        
        # 确保置信度在合理范围
        confidence = max(0.3, min(0.9, confidence))
        
        return {
            "subject": "USER",
            "relation": relation_type,
            "object": entity,
            "object_type": entity_type,
            "confidence": confidence,
            "negation": negation,
            "raw_text": text,
            "timestamp": None  # 将在调用时设置
        }
    
    def batch_parse(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量解析文本"""
        results = []
        for text in texts:
            parsed = self.parse(text)
            if parsed:
                results.append(parsed)
        return results
    
    def to_graph_triple(self, parsed: Dict[str, Any]) -> Tuple[str, str, str, float]:
        """转换为图三元组格式"""
        return (
            parsed["subject"],
            parsed["relation"],
            parsed["object"],
            parsed["confidence"]
        )


# 测试函数
def test_parser():
    """测试解析器"""
    parser = SimpleSemanticParser()
    
    test_cases = [
        "我喜欢日本房产",
        "我不喜欢高风险投资",
        "AI创业怎么做？",
        "日本房产回报率如何？",
        "机器学习入门",
        "我想投资日本房产",
        "我对高风险投资不感兴趣",
        "长期投资更适合我"
    ]
    
    print("🧪 测试简单语义解析器")
    print("="*60)
    
    for text in test_cases:
        result = parser.parse(text)
        if result:
            print(f"📝 输入: {text}")
            print(f"  主体: {result['subject']}")
            print(f"  关系: {result['relation']}")
            print(f"  客体: {result['object']} ({result['object_type']})")
            print(f"  置信度: {result['confidence']:.2f}")
            print(f"  否定: {result['negation']}")
            print()
        else:
            print(f"❌ 无法解析: {text}")
    
    print("="*60)
    print("✅ 解析器测试完成")


if __name__ == "__main__":
    test_parser()