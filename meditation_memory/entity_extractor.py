"""
实体与关系抽取模块

从对话文本中抽取实体（人物、地点、概念、事件等）和它们之间的关系。
支持两种模式：
  1. LLM 模式 —— 调用大语言模型进行精准抽取
  2. 规则模式 —— 基于 jieba 分词和词性标注的轻量回退方案
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional

from .config import LLMConfig


# ========== 数据结构 ==========

@dataclass
class Entity:
    """抽取到的实体"""

    name: str  # 实体名称
    entity_type: str  # 类型：person / place / concept / event / object / organization
    properties: dict = field(default_factory=dict)  # 附加属性

    def __hash__(self):
        return hash((self.name, self.entity_type))

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.name == other.name and self.entity_type == other.entity_type


@dataclass
class Relation:
    """抽取到的关系"""

    source: str  # 源实体名称
    target: str  # 目标实体名称
    relation_type: str  # 关系类型，如 located_in / works_at / related_to
    properties: dict = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """一次抽取的完整结果"""

    entities: List[Entity] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)
    raw_text: str = ""


# ========== LLM 抽取提示词 ==========

_EXTRACTION_SYSTEM_PROMPT = """你是一个信息抽取助手。请从用户提供的对话文本中抽取实体和关系。

要求：
1. 实体类型包括：person（人物）、place（地点）、concept（概念）、event（事件）、object（物品）、organization（组织）
2. 关系描述实体之间的联系，尽量使用具体的关系类型（如 uses, part_of, causes, located_in, works_at, created_by, is_instance_of, contradicts, supports, precedes 等），减少使用模糊的 related_to
3. 质量约束：
   - 只提取有意义的命名实体和核心概念
   - 不要提取句子碎片、口语表达、主观判断或动词短语
   - 实体名称必须是完整的词或短语（如"量子计算机"、"比特币"、"爱因斯坦"），不能是截断的句子片段（如"量子计算机使用量子比"）
   - 不要提取代词（我、你、他）、连词（和、或者）、副词（非常、可能）等虚词
4. 限制：每次最多提取 15 个最重要的实体
5. 只抽取文本中明确提到或可直接推断的信息，不要编造

请严格以如下 JSON 格式输出，不要输出其他内容：
{
  "entities": [
    {"name": "实体名", "entity_type": "类型", "properties": {}}
  ],
  "relations": [
    {"source": "源实体名", "target": "目标实体名", "relation_type": "关系类型", "properties": {}}
  ]
}"""

_EXTRACTION_USER_TEMPLATE = "请从以下文本中抽取实体和关系：\n\n{text}"


# ========== 停用词和过滤规则 ==========

# jieba 词性标注中表示实体的词性前缀
# n: 名词, nr: 人名, ns: 地名, nt: 机构, nz: 其他专名, vn: 名动词, an: 名形词, eng: 英文
_ENTITY_POS_PREFIXES = ("n", "nr", "ns", "nt", "nz", "vn", "an", "eng", "x")

# 需要排除的词性
_EXCLUDE_POS = {"r", "p", "c", "u", "d", "v", "a", "m", "q", "f", "s", "t", "w", "y", "e", "o", "k", "h"}

# 停用词表（即使词性标注为名词也要过滤的词）
_STOP_WORDS = {
    # 代词
    "我", "你", "他", "她", "它", "我们", "你们", "他们", "她们", "它们", "大家", "自己",
    "别人", "人家", "某人", "这", "那", "这里", "那里", "这儿", "那儿", "这个", "那个",
    "这些", "那些", "什么", "怎么", "哪里", "谁", "某", "哪个", "哪些",
    # 常见虚义名词
    "东西", "事情", "事", "问题", "方面", "情况", "时候", "地方", "方式", "方法",
    "结果", "原因", "目的", "意思", "意义", "作用", "影响", "关系", "条件", "过程",
    "内容", "部分", "方向", "程度", "范围", "角度", "层面", "水平", "能力", "可能性",
    # 口语碎片
    "一下", "一些", "一点", "一种", "一个", "一样", "一起", "一直", "一定", "一般",
    "其中", "之间", "之中", "之后", "之前", "以上", "以下", "以内", "以外",
    "这样", "那样", "怎样", "如何", "为何", "为什么",
    # 常见动词（有时被标注为名词）
    "分析", "研究", "讨论", "考虑", "处理", "解决", "实现", "发展", "提高", "改进",
    "使用", "利用", "采用", "进行", "完成", "开始", "结束", "继续", "保持", "变化",
    "存在", "包含", "属于", "成为", "认为", "觉得", "知道", "了解", "发现", "感觉",
    "看到", "听到", "说", "讲", "告诉", "建议", "希望", "需要", "想", "要",
}

# 实体类型关键词映射
_PERSON_INDICATORS = {"先生", "女士", "老师", "教授", "博士", "同学", "朋友", "总裁",
                      "经理", "院长", "主任", "总统", "主席", "部长", "将军", "医生"}
_PLACE_INDICATORS = {"市", "省", "区", "县", "镇", "村", "路", "街", "国", "州",
                     "海", "山", "河", "湖", "洋", "岛", "洲", "半岛", "盆地", "高原"}
_ORG_INDICATORS = {"公司", "集团", "大学", "学院", "机构", "组织", "部门", "局", "部",
                   "委", "中心", "协会", "联盟", "基金会", "研究所", "实验室", "银行"}


# ========== 抽取器实现 ==========

class EntityExtractor:
    """实体与关系抽取器"""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self._llm_config = llm_config or LLMConfig()
        self._client = None  # 延迟初始化
        self._jieba_initialized = False

    def _init_jieba(self):
        """延迟初始化 jieba（首次调用时加载词典）"""
        if not self._jieba_initialized:
            try:
                import jieba
                import jieba.posseg
                jieba.setLogLevel(jieba.logging.WARNING)
                self._jieba_initialized = True
            except ImportError:
                pass

    # ---------- 公开接口 ----------

    def extract(self, text: str, use_llm: bool = True) -> ExtractionResult:
        """
        从文本中抽取实体和关系。

        Args:
            text: 待抽取的对话文本
            use_llm: 是否使用 LLM 模式，False 则使用规则模式

        Returns:
            ExtractionResult 包含实体和关系列表
        """
        if not text or not text.strip():
            return ExtractionResult(raw_text=text)

        if use_llm and self._llm_config.api_key:
            try:
                return self._extract_with_llm(text)
            except Exception:
                # LLM 失败时回退到规则模式
                return self._extract_with_rules(text)
        else:
            return self._extract_with_rules(text)

    # ---------- LLM 模式 ----------

    def _get_client(self):
        """延迟初始化 OpenAI 客户端"""
        if self._client is None:
            from openai import OpenAI

            kwargs = {}
            if self._llm_config.api_key:
                kwargs["api_key"] = self._llm_config.api_key
            if self._llm_config.base_url:
                kwargs["base_url"] = self._llm_config.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def _extract_with_llm(self, text: str) -> ExtractionResult:
        """使用 LLM 进行实体关系抽取"""
        client = self._get_client()

        response = client.chat.completions.create(
            model=self._llm_config.model,
            messages=[
                {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": _EXTRACTION_USER_TEMPLATE.format(text=text)},
            ],
            temperature=0.0,
            max_tokens=1024,
        )

        content = response.choices[0].message.content or ""
        return self._parse_llm_response(content, text)

    def _parse_llm_response(self, content: str, raw_text: str) -> ExtractionResult:
        """解析 LLM 返回的 JSON"""
        # 尝试提取 JSON 块
        json_match = re.search(r"\{[\s\S]*\}", content)
        if not json_match:
            return ExtractionResult(raw_text=raw_text)

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return ExtractionResult(raw_text=raw_text)

        entities = []
        for e in data.get("entities", [])[:15]:  # 限制最多15个实体
            if isinstance(e, dict) and "name" in e:
                name = e["name"].strip()
                # 质量验证：过滤掉过短、过长或明显是碎片的实体
                if len(name) < 2 or len(name) > 30:
                    continue
                if name in _STOP_WORDS:
                    continue
                entities.append(Entity(
                    name=name,
                    entity_type=e.get("entity_type", "concept"),
                    properties=e.get("properties", {}),
                ))

        relations = []
        for r in data.get("relations", []):
            if isinstance(r, dict) and "source" in r and "target" in r:
                relations.append(Relation(
                    source=r["source"],
                    target=r["target"],
                    relation_type=r.get("relation_type", "related_to"),
                    properties=r.get("properties", {}),
                ))

        return ExtractionResult(entities=entities, relations=relations, raw_text=raw_text)

    # ---------- 规则模式（基于 jieba 分词） ----------

    def _extract_with_rules(self, text: str) -> ExtractionResult:
        """基于 jieba 分词和词性标注的实体抽取"""
        self._init_jieba()

        entities: List[Entity] = []
        relations: List[Relation] = []
        seen = set()

        try:
            import jieba.posseg as pseg

            # 按句子分割
            sentences = re.split(r"[。！？\n.!?;；]", text)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                sentence_entities = []

                # jieba 词性标注分词
                words = list(pseg.cut(sentence))

                # 合并相邻名词为短语（如"量子" + "计算机" → "量子计算机"）
                merged_words = self._merge_noun_phrases(words)

                for word, pos in merged_words:
                    word = word.strip()

                    # 基本过滤
                    if len(word) < 2:
                        continue
                    if word in _STOP_WORDS:
                        continue
                    if word in seen:
                        continue

                    # 词性过滤：只保留名词性词语
                    pos_prefix = pos[0] if pos else ""
                    if pos_prefix in _EXCLUDE_POS:
                        continue

                    # 额外的质量检查
                    if not self._is_valid_entity(word):
                        continue

                    seen.add(word)

                    # 判断实体类型
                    entity_type = self._classify_entity_type(word, pos)

                    entity = Entity(name=word, entity_type=entity_type)
                    entities.append(entity)
                    sentence_entities.append(entity)

                    # 限制最大实体数量
                    if len(entities) >= 20:
                        break

                # 建立相邻实体之间的关系（每句最多4条）
                for i in range(min(len(sentence_entities) - 1, 4)):
                    relations.append(Relation(
                        source=sentence_entities[i].name,
                        target=sentence_entities[i + 1].name,
                        relation_type="related_to",
                    ))

                if len(entities) >= 20:
                    break

        except ImportError:
            # jieba 不可用时使用极简回退
            entities, relations = self._fallback_extract(text)

        # 提取英文实体（专有名词）
        english_entities = re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b", text)
        for ent in english_entities:
            if len(entities) >= 20:
                break
            ent = ent.strip()
            if ent not in seen and len(ent) > 1 and ent not in {"The", "This", "That", "What", "How", "Why", "When", "Where", "Who", "Which", "And", "But", "For", "Not", "You", "Are", "Was", "Were", "Has", "Have", "Had", "Can", "Could", "Will", "Would", "Should", "May", "Might"}:
                seen.add(ent)
                entities.append(Entity(name=ent, entity_type="concept"))

        return ExtractionResult(entities=entities, relations=relations, raw_text=text)

    def _merge_noun_phrases(self, words) -> list:
        """合并相邻的名词性词语为短语"""
        merged = []
        i = 0
        while i < len(words):
            word, pos = words[i].word, words[i].flag
            pos_prefix = pos[0] if pos else ""

            # 如果是名词性词语，尝试与后续名词合并
            if pos_prefix == "n" or pos in ("nr", "ns", "nt", "nz", "vn", "an", "eng"):
                phrase = word
                j = i + 1
                while j < len(words) and len(phrase) < 15:
                    next_word, next_pos = words[j].word, words[j].flag
                    next_prefix = next_pos[0] if next_pos else ""
                    # 只合并相邻的名词性词语
                    if next_prefix == "n" or next_pos in ("nr", "ns", "nt", "nz", "vn", "an"):
                        phrase += next_word
                        j += 1
                    else:
                        break
                merged.append((phrase, pos))
                i = j
            else:
                merged.append((word, pos))
                i += 1

        return merged

    def _is_valid_entity(self, word: str) -> bool:
        """验证词语是否是有效的实体"""
        # 排除纯数字
        if re.match(r"^[\d\s]+$", word):
            return False

        # 排除过短的中文词（单字已在上面过滤）
        if re.match(r"^[\u4e00-\u9fff]$", word):
            return False

        # 排除以常见虚词开头或结尾的短语
        bad_starts = ["的", "了", "在", "和", "是", "有", "被", "把", "从", "对",
                      "让", "给", "与", "或", "而", "就", "都", "也", "还", "又",
                      "很", "最", "更", "太", "不", "没", "要", "会", "能", "可"]
        bad_ends = ["的", "了", "着", "过", "得", "地", "呢", "吗", "啊", "吧",
                    "呀", "在", "和", "是", "有", "被", "把", "来", "去"]

        if any(word.startswith(w) for w in bad_starts):
            return False
        if any(word.endswith(w) for w in bad_ends):
            return False

        # 排除包含明显口语碎片的短语
        bad_substrings = ["我认为", "你觉得", "如果必须", "也就是说", "换句话说",
                          "怎么", "什么", "为什么", "不知道", "没关系", "不好意思"]
        if any(bad in word for bad in bad_substrings):
            return False

        return True

    def _classify_entity_type(self, word: str, pos: str) -> str:
        """根据词语内容和词性判断实体类型"""
        # 人名
        if pos in ("nr", "nrt"):
            return "person"
        if any(ind in word for ind in _PERSON_INDICATORS):
            return "person"

        # 地名
        if pos == "ns":
            return "place"
        if any(ind in word for ind in _PLACE_INDICATORS):
            return "place"

        # 机构
        if pos == "nt":
            return "organization"
        if any(ind in word for ind in _ORG_INDICATORS):
            return "organization"

        return "concept"

    def _fallback_extract(self, text: str):
        """jieba 不可用时的极简回退提取"""
        entities = []
        relations = []
        seen = set()

        # 只提取英文专有名词和明确的中文专有名词模式
        # 中文：只提取带有明确类型指示符的短语
        for indicator_set, entity_type in [
            (_PERSON_INDICATORS, "person"),
            (_PLACE_INDICATORS, "place"),
            (_ORG_INDICATORS, "organization"),
        ]:
            for ind in indicator_set:
                # 匹配 "X指示符" 模式，如 "张教授"、"北京市"、"谷歌公司"
                pattern = rf"([\u4e00-\u9fff]{{1,6}}{re.escape(ind)})"
                matches = re.findall(pattern, text)
                for m in matches:
                    if m not in seen and len(entities) < 20:
                        seen.add(m)
                        entities.append(Entity(name=m, entity_type=entity_type))

        return entities, relations
