"""
实体抽取模块的单元测试

测试规则模式下的实体和关系抽取功能。
LLM 模式通过 mock 测试。
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from meditation_memory.entity_extractor import (
    Entity,
    EntityExtractor,
    ExtractionResult,
    Relation,
)
from meditation_memory.config import LLMConfig


class TestEntity(unittest.TestCase):
    """Entity 数据类测试"""

    def test_entity_creation(self):
        """测试实体创建"""
        e = Entity(name="张三", entity_type="person")
        self.assertEqual(e.name, "张三")
        self.assertEqual(e.entity_type, "person")
        self.assertEqual(e.properties, {})

    def test_entity_with_properties(self):
        """测试带属性的实体"""
        e = Entity(name="北京", entity_type="place", properties={"country": "中国"})
        self.assertEqual(e.properties["country"], "中国")

    def test_entity_equality(self):
        """测试实体相等性"""
        e1 = Entity(name="张三", entity_type="person")
        e2 = Entity(name="张三", entity_type="person")
        e3 = Entity(name="张三", entity_type="concept")
        self.assertEqual(e1, e2)
        self.assertNotEqual(e1, e3)

    def test_entity_hash(self):
        """测试实体可哈希"""
        e1 = Entity(name="张三", entity_type="person")
        e2 = Entity(name="张三", entity_type="person")
        s = {e1, e2}
        self.assertEqual(len(s), 1)


class TestRelation(unittest.TestCase):
    """Relation 数据类测试"""

    def test_relation_creation(self):
        """测试关系创建"""
        r = Relation(source="张三", target="北京大学", relation_type="works_at")
        self.assertEqual(r.source, "张三")
        self.assertEqual(r.target, "北京大学")
        self.assertEqual(r.relation_type, "works_at")


class TestEntityExtractorRules(unittest.TestCase):
    """规则模式抽取测试"""

    def setUp(self):
        # 不提供 API key，强制使用规则模式
        self.extractor = EntityExtractor(LLMConfig(api_key=None))

    def test_empty_input(self):
        """测试空输入"""
        result = self.extractor.extract("", use_llm=False)
        self.assertIsInstance(result, ExtractionResult)
        self.assertEqual(len(result.entities), 0)
        self.assertEqual(len(result.relations), 0)

    def test_chinese_entity_extraction(self):
        """测试中文实体抽取"""
        text = "张三在北京大学学习人工智能课程"
        result = self.extractor.extract(text, use_llm=False)
        self.assertGreater(len(result.entities), 0)
        # 应该能抽取出一些实体
        entity_names = [e.name for e in result.entities]
        # 至少应该包含一些关键词
        self.assertTrue(len(entity_names) > 0)

    def test_place_detection(self):
        """测试地点类型识别"""
        text = "我住在上海市浦东新区"
        result = self.extractor.extract(text, use_llm=False)
        place_entities = [e for e in result.entities if e.entity_type == "place"]
        # 应该能识别出地点
        place_names = [e.name for e in place_entities]
        has_place = any("市" in n or "区" in n for n in place_names)
        self.assertTrue(has_place, f"未识别出地点实体，得到: {place_names}")

    def test_organization_detection(self):
        """测试组织类型识别"""
        text = "他在腾讯公司工作，之前在清华大学读书"
        result = self.extractor.extract(text, use_llm=False)
        org_entities = [e for e in result.entities if e.entity_type == "organization"]
        org_names = [e.name for e in org_entities]
        # 应该能识别出组织
        has_org = any("公司" in n or "大学" in n for n in org_names)
        self.assertTrue(has_org, f"未识别出组织实体，得到: {org_names}")

    def test_english_entity_extraction(self):
        """测试英文实体抽取"""
        text = "OpenAI released GPT-4 and Google launched Gemini"
        result = self.extractor.extract(text, use_llm=False)
        entity_names = [e.name for e in result.entities]
        # 应该能抽取出大写开头的英文实体
        self.assertTrue(
            any("OpenAI" in n or "Google" in n or "Gemini" in n for n in entity_names),
            f"未识别出英文实体，得到: {entity_names}",
        )

    def test_relation_extraction_cooccurrence(self):
        """测试基于共现的关系抽取"""
        text = "张三在北京大学学习人工智能。李四在清华大学工作。"
        result = self.extractor.extract(text, use_llm=False)
        # 同一句中的实体应该有 related_to 关系
        if len(result.entities) >= 2:
            self.assertGreater(len(result.relations), 0)

    def test_extraction_result_raw_text(self):
        """测试抽取结果保留原始文本"""
        text = "测试文本"
        result = self.extractor.extract(text, use_llm=False)
        self.assertEqual(result.raw_text, text)


class TestEntityExtractorLLM(unittest.TestCase):
    """LLM 模式抽取测试（使用 mock）"""

    def test_llm_extraction_with_mock(self):
        """测试 LLM 模式（mock OpenAI 响应）"""
        extractor = EntityExtractor(LLMConfig(api_key="test-key"))

        # 模拟 LLM 返回
        mock_response_content = json.dumps({
            "entities": [
                {"name": "张三", "entity_type": "person"},
                {"name": "北京大学", "entity_type": "organization"},
            ],
            "relations": [
                {"source": "张三", "target": "北京大学", "relation_type": "works_at"},
            ],
        })

        mock_choice = MagicMock()
        mock_choice.message.content = mock_response_content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        extractor._client = mock_client

        result = extractor.extract("张三在北京大学工作", use_llm=True)

        self.assertEqual(len(result.entities), 2)
        self.assertEqual(result.entities[0].name, "张三")
        self.assertEqual(result.entities[0].entity_type, "person")
        self.assertEqual(len(result.relations), 1)
        self.assertEqual(result.relations[0].relation_type, "works_at")

    def test_llm_fallback_on_error(self):
        """测试 LLM 失败时回退到规则模式"""
        extractor = EntityExtractor(LLMConfig(api_key="test-key"))

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        extractor._client = mock_client

        # 应该回退到规则模式而不是抛异常
        result = extractor.extract("张三在北京大学工作", use_llm=True)
        self.assertIsInstance(result, ExtractionResult)

    def test_llm_parse_invalid_json(self):
        """测试 LLM 返回无效 JSON 时的处理"""
        extractor = EntityExtractor(LLMConfig(api_key="test-key"))

        mock_choice = MagicMock()
        mock_choice.message.content = "这不是 JSON"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        extractor._client = mock_client

        result = extractor._extract_with_llm("测试")
        self.assertEqual(len(result.entities), 0)


if __name__ == "__main__":
    unittest.main()
