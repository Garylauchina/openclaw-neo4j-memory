"""
实体与关系抽取模块

从对话文本中抽取实体（人物、地点、概念、事件、意图等）和它们之间的关系。

抽取策略（优先级从高到低）：
  1. LLM 模式 —— 调用大语言模型进行精准抽取（默认且推荐）
  2. LLM 重试 —— 使用更小的模型重试一次
  3. 规则模式 —— 仅在 LLM 完全不可用时回退，结果标记 extraction_mode: "rules"

Phase 4：
  - 新增 intent（意图/目标）实体类型
  - 新增因果关系类型：causes, leads_to, precedes, prevents, achieves, aims_at
  - 强调提取因果关系
  - 修复截断碎片实体问题：LLM 优先 + 规则模式标注
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional

from .config import LLMConfig

logger = logging.getLogger("entity_extractor")

# ========== 数据结构 ==========

@dataclass
class Entity:
    """抽取到的实体"""

    name: str
    entity_type: str
    properties: dict = field(default_factory=dict)

    def __hash__(self):
        return hash((self.name, self.entity_type))

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.name == other.name and self.entity_type == other.entity_type


@dataclass
class Relation:
    """抽取到的关系"""

    source: str
    target: str
    relation_type: str
    properties: dict = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """一次抽取的完整结果"""

    entities: List[Entity] = field(default_factory=list)
    relations: List[Relation] = field(default_factory=list)
    raw_text: str = ""
    extraction_mode: str = "llm"  # "llm" | "llm_retry" | "rules"


# ========== LLM 抽取提示词 ==========

_EXTRACTION_SYSTEM_PROMPT = """你是一个信息抽取助手。请从用户提供的对话文本中抽取实体和关系。

实体类型：person（人物）、place（地点）、concept（概念）、event（事件）、
   intent（意图/目标）、object（物品）、organization（组织）

关系类型：
   - 因果关系：causes（导致）、leads_to（引向）、precedes（先于）、prevents（阻止）
   - 目标关系：achieves（实现）、aims_at（目标是）
   - 结构关系：uses, part_of, located_in, works_at, created_by, is_instance_of
   - 对立关系：contradicts, supports, opposes
   减少使用 related_to

特别注意：
   - 只提取有意义的命名实体和核心概念
   - 不要提取句子碎片、口语表达、主观判断或动词短语
   - 实体名称必须是完整的词或短语
   - 不要提取代词、连词、副词等虚词
   - 每次最多提取 15 个最重要的实体
   - 只抽取文本中明确提到或可直接推断的信息，不要编造

请严格以如下 JSON 格式输出，不要输出其他内容：
{
  "entities": [
    {"name": "实体名", "entity_type": "类型", "properties": {}}
  ],
  "relations": [
    {"source": "源实体名", "target": "目标实体名",
     "relation_type": "关系类型", "properties": {}}
  ]
}"""

_EXTRACTION_USER_TEMPLATE = "请从以下文本中抽取实体和关系：\n\n{text}"

# ========== 备用模型（当主模型失败时使用） ==========
_RETRY_MODELS = [
    "anthropic/claude-haiku",
    "openai/gpt-4o-mini",
    "qwen/qwen-turbo",
]


# ========== 停用词和过滤规则 ==========

_ENTITY_POS_PREFIXES = ("n", "nr", "ns", "nt", "nz", "vn", "an", "eng", "x")
_EXCLUDE_POS = {"r", "p", "c", "u", "d", "v", "a", "m", "q", "f", "s", "t", "w", "y", "e", "o", "k", "h"}

_STOP_WORDS = {
    "我", "你", "他", "她", "它", "我们", "你们", "他们", "她们", "它们", "大家", "自己",
    "别人", "人家", "某人", "这", "那", "这里", "那里", "这儿", "那儿", "这个", "那个",
    "这些", "那些", "什么", "怎么", "哪里", "谁", "某", "哪个", "哪些",
    "东西", "事情", "事", "问题", "方面", "情况", "时候", "地方", "方式", "方法",
    "结果", "原因", "目的", "意思", "意义", "作用", "影响", "关系", "条件", "过程",
    "内容", "部分", "方向", "程度", "范围", "角度", "层面", "水平", "能力", "可能性",
    "一下", "一些", "一点", "一种", "一个", "一样", "一起", "一直", "一定", "一般",
    "其中", "之间", "之中", "之后", "之前", "以上", "以下", "以内", "以外",
    "这样", "那样", "怎样", "如何", "为何", "为什么",
    "分析", "研究", "讨论", "考虑", "处理", "解决", "实现", "发展", "提高", "改进",
    "使用", "利用", "采用", "进行", "完成", "开始", "结束", "继续", "保持", "变化",
    "存在", "包含", "属于", "成为", "认为", "觉得", "知道", "了解", "发现", "感觉",
    "看到", "听到", "说", "讲", "告诉", "建议", "希望", "需要", "想", "要",
}

# 英文停用词（规则模式/回退模式）
_EN_STOP_WORDS = {
    "The", "This", "That", "What", "How", "Why", "When", "Where", "Who",
    "Which", "And", "But", "For", "Not", "You", "Are", "Was", "Were",
    "Has", "Have", "Had", "Can", "Could", "Will", "Would", "Should",
    "May", "Might", "Just", "Also", "Very", "Only", "Some", "Any", "All",
    "One", "Two", "Three", "First", "Second", "Third", "Many", "More",
    "Such", "Own", "Same", "Other", "Another", "Each", "Every",
    "Here", "Use", "Remember", "Good", "Consider", "Instead", "Keep", "Set", "Create",
    "Need", "Make", "Take", "Try", "Best", "Help", "Learn", "Start", "Find", "Check",
    "Focus", "Identify", "Practice", "Avoid", "Once", "Reward", "Provide", "Replace",
    "Schedule", "Share", "Trying", "Additionally", "However", "Offers", "Often", "Thanks",
    "There", "Tools", "Communicate", "Experiment", "Implement",
}

# 元数据标签前缀（如冥想生成的摘要节点）
_META_PREFIXES = ["[META]", "[TAG]", "<META>", "<TAG>"]

# 动词短语/句子碎片特征后缀（表示这不是一个完整实体）
_VERB_PHRASE_ENDINGS = [
    "导致", "导致价格", "导致数据", "导致系统",
    "暴跌", "上涨", "下降", "上升", "增加", "减少",
    "怎么做", "是什么", "为什么", "怎么办",
    "依赖于", "取决于", "取决于系统",
    "影响了", "改善了", "优化了", "提高了",
    "进行了", "完成了", "开始了", "结束了",
]

# ========== 通用实体名称验证函数 ==========

def _is_valid_name(name: str) -> bool:
    """
    统一的实体名称验证。
    拦截以下噪声类型：
    1. 纯符号/纯数字
    2. [META]/[TAG] 元数据前缀
    3. 动词短语/句子碎片
    4. 停用词
    5. 超出长度范围（< 2 或 > 30）
    6. 英文单词型低信息概念
    """
    if not name:
        return False
    # 长度约束
    if len(name) < 2 or len(name) > 30:
        return False
    # 纯符号/纯数字/纯空白
    if re.match(r"^[^a-zA-Z\u4e00-\u9fff]+$", name):
        return False
    # 元数据标签
    if any(name.startswith(p) for p in _META_PREFIXES):
        return False
    # 中文停用词
    if name in _STOP_WORDS:
        return False
    # 英文停用词
    if name in _EN_STOP_WORDS:
        return False
    # 常见英文单词型低信息概念
    if re.match(r"^[A-Z][a-z]+$", name) and name not in {"Python", "Tableau", "Microsoft", "Coursera", "Seaborn", "Matplotlib"}:
        return False
    # 动词短语后缀
    if any(name.endswith(s) for s in _VERB_PHRASE_ENDINGS):
        return False
    return True


_PERSON_INDICATORS = {"先生", "女士", "老师", "教授", "博士", "同学", "朋友", "总裁",
                      "经理", "院长", "主任", "总统", "主席", "部长", "将军", "医生"}
_PLACE_INDICATORS = {"市", "省", "区", "县", "镇", "村", "路", "街", "国", "州",
                     "海", "山", "河", "湖", "洋", "岛", "洲", "半岛", "盆地", "高原"}
_ORG_INDICATORS = {"公司", "集团", "大学", "学院", "机构", "组织", "部门", "局", "部",
                   "委", "中心", "协会", "联盟", "基金会", "研究所", "实验室", "银行"}
_INTENT_INDICATORS = {"想要", "目标", "计划", "期望", "希望", "打算",
                      "需求", "意图", "目的", "追求"}


# ========== 抽取器实现 ==========

class EntityExtractor:
    """实体与关系抽取器"""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self._llm_config = llm_config or LLMConfig()
        self._client = None
        self._jieba_initialized = False

    def _init_jieba(self):
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

        策略：
          1. 如果 use_llm=True：优先 LLM，失败后重试一次备选模型，
             只有 LLM 完全不可用时才回退到规则模式
          2. 如果 use_llm=False：直接使用规则模式
        """
        if not text or not text.strip():
            return ExtractionResult(raw_text=text)

        if not use_llm:
            return self._extract_with_rules(text)

        # 兼容本地 OpenAI-compatible 服务（如 Ollama/LiteLLM）
        # 这类服务通常只需要 base_url，不一定需要真实 api_key。
        if not self._llm_config.api_key and not self._llm_config.base_url:
            return self._extract_with_rules(text)

        # LLM 模式：先尝试主模型
        result = self._try_llm_with_retry(text)
        if result is not None:
            return result

        # LLM 完全失败：回退到规则模式（但标记为 rules）
        logger.warning("LLM fully unavailable, falling back to rules-based extraction (marked as 'rules')")
        return self._extract_with_rules(text)

    def _try_llm_with_retry(self, text: str) -> Optional[ExtractionResult]:
        """尝试 LLM 抽取，失败后自动重试备选模型。

        Returns:
            ExtractionResult 如果成功，None 如果所有尝试都失败
        """
        # 尝试主模型
        try:
            return self._extract_with_llm(text, model=None)
        except Exception as e:
            logger.warning(f"Primary LLM extraction failed: {e}, trying retry models...")

        # 重试：依次尝试备用模型
        original_model = self._llm_config.model
        for retry_model in _RETRY_MODELS:
            try:
                logger.info(f"Retrying extraction with model: {retry_model}")
                result = self._extract_with_llm(text, model=retry_model)
                if result and result.entities:
                    result.extraction_mode = "llm_retry"
                    return result
            except Exception as e:
                logger.warning(f"Retry model {retry_model} failed: {e}")
                continue

        logger.error("All LLM models failed for entity extraction")
        return None

    # ---------- LLM 模式 ----------

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            kwargs = {}
            if self._llm_config.api_key:
                kwargs["api_key"] = self._llm_config.api_key
            if self._llm_config.base_url:
                kwargs["base_url"] = self._llm_config.base_url
            kwargs["timeout"] = 30  # 添加超时，防止永远挂起
            self._client = OpenAI(**kwargs)
        return self._client

    def _extract_with_llm(self, text: str, model: Optional[str] = None) -> Optional[ExtractionResult]:
        """使用 LLM 进行实体关系抽取。

        Args:
            text: 输入文本
            model: 可选的模型名称，None 则使用配置中的默认模型
        """
        client = self._get_client()
        model_name = model or self._llm_config.model

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": _EXTRACTION_USER_TEMPLATE.format(text=text)},
            ],
            temperature=0.0,
            max_tokens=1024,
            timeout=30,
        )

        content = response.choices[0].message.content or ""
        return self._parse_llm_response(content, text)

    def _parse_llm_response(self, content: str, raw_text: str) -> Optional[ExtractionResult]:
        """解析 LLM 返回的 JSON"""
        json_match = re.search(r"\{[\s\S]*\}", content)
        if not json_match:
            return ExtractionResult(raw_text=raw_text, extraction_mode="llm")

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            return ExtractionResult(raw_text=raw_text, extraction_mode="llm")

        entities = []
        for e in data.get("entities", [])[:15]:
            if not isinstance(e, dict):
                continue
            name = (e.get("name") or e.get("entity") or "").strip()
            if not name or not _is_valid_name(name):
                continue
            entity_type = (e.get("entity_type") or e.get("type") or "concept").strip().lower()
            entities.append(Entity(
                name=name,
                entity_type=entity_type,
                properties=e.get("properties", {}),
            ))

        relations = []
        for r in data.get("relations", []):
            if not isinstance(r, dict):
                continue
            source = (r.get("source") or "").strip()
            target = (r.get("target") or "").strip()
            relation_type = (r.get("relation_type") or r.get("relation") or "related_to").strip()
            if source and target:
                relations.append(Relation(
                    source=source,
                    target=target,
                    relation_type=relation_type,
                    properties=r.get("properties", {}),
                ))

        return ExtractionResult(
            entities=entities,
            relations=relations,
            raw_text=raw_text,
            extraction_mode="llm",
        )

    # ---------- 规则模式（仅在 LLM 完全不可用时使用） ----------

    def _extract_with_rules(self, text: str) -> ExtractionResult:
        """基于 jieba 分词和词性标注的实体抽取（降级方案）"""
        self._init_jieba()

        entities: List[Entity] = []
        relations: List[Relation] = []
        seen = set()

        try:
            import jieba.posseg as pseg

            sentences = re.split(r"[。！？\n.!?;；]", text)

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                sentence_entities = []
                words = list(pseg.cut(sentence))
                merged_words = self._merge_noun_phrases(words)

                for word, pos in merged_words:
                    word = word.strip()

                    if not _is_valid_name(word):
                        continue
                    if word in seen:
                        continue

                    pos_prefix = pos[0] if pos else ""
                    if pos_prefix in _EXCLUDE_POS:
                        continue

                    if not self._is_valid_entity(word):
                        continue

                    seen.add(word)
                    entity_type = self._classify_entity_type(word, pos)

                    # 规则模式实体打上标记
                    entity = Entity(
                        name=word,
                        entity_type=entity_type,
                        properties={"extraction_mode": "rules"},  # 标记为规则模式抽取
                    )
                    entities.append(entity)
                    sentence_entities.append(entity)

                    if len(entities) >= 20:
                        break

                for i in range(min(len(sentence_entities) - 1, 4)):
                    relations.append(Relation(
                        source=sentence_entities[i].name,
                        target=sentence_entities[i + 1].name,
                        relation_type="related_to",
                    ))

                if len(entities) >= 20:
                    break

        except ImportError:
            entities, relations = self._fallback_extract(text)

        # 提取英文实体
        english_entities = re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b", text)
        for ent in english_entities:
            if len(entities) >= 20:
                break
            ent = ent.strip()
            if ent in seen:
                continue
            if not _is_valid_name(ent):  # 统一验证
                continue
            seen.add(ent)
            entities.append(Entity(
                name=ent,
                entity_type="concept",
                properties={"extraction_mode": "rules"},
            ))

        return ExtractionResult(
            entities=entities,
            relations=relations,
            raw_text=text,
            extraction_mode="rules",  # 标记为规则模式
        )

    def _merge_noun_phrases(self, words) -> list:
        """合并相邻的名词性词语为短语。

        修复：不再使用 len(phrase) < 15 进行字符截断，
        改为遇到非名词性词语就停止合并，避免产生截断碎片。
        """
        merged = []
        i = 0
        while i < len(words):
            word, pos = words[i].word, words[i].flag
            pos_prefix = pos[0] if pos else ""

            if pos_prefix == "n" or pos in ("nr", "ns", "nt", "nz", "vn", "an", "eng"):
                phrase = word
                j = i + 1
                # 修复：移除 len(phrase) < 15 截断逻辑
                # 改为：只合并名词性词语，遇到非名词就停止
                while j < len(words):
                    next_word, next_pos = words[j].word, words[j].flag
                    next_prefix = next_pos[0] if next_pos else ""
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
        if re.match(r"^[\d\s]+$", word):
            return False
        if re.match(r"^[\u4e00-\u9fff]$", word):
            return False

        bad_starts = ["的", "了", "在", "和", "是", "有", "被", "把", "从", "对",
                      "让", "给", "与", "或", "而", "就", "都", "也", "还", "又",
                      "很", "最", "更", "太", "不", "没", "要", "会", "能", "可"]
        bad_ends = ["的", "了", "着", "过", "得", "地", "呢", "吗", "啊", "吧",
                    "呀", "在", "和", "是", "有", "被", "把", "来", "去"]

        if any(word.startswith(w) for w in bad_starts):
            return False
        if any(word.endswith(w) for w in bad_ends):
            return False

        bad_substrings = ["我认为", "你觉得", "如果必须", "也就是说", "换句话说",
                          "怎么", "什么", "为什么", "不知道", "没关系", "不好意思"]
        if any(bad in word for bad in bad_substrings):
            return False

        return True

    def _classify_entity_type(self, word: str, pos: str) -> str:
        """根据词语内容和词性判断实体类型"""
        if pos in ("nr", "nrt"):
            return "person"
        if any(ind in word for ind in _PERSON_INDICATORS):
            return "person"
        if pos == "ns":
            return "place"
        if any(ind in word for ind in _PLACE_INDICATORS):
            return "place"
        if pos == "nt":
            return "organization"
        if any(ind in word for ind in _ORG_INDICATORS):
            return "organization"
        if any(ind in word for ind in _INTENT_INDICATORS):
            return "intent"
        return "concept"

    def _fallback_extract(self, text: str):
        """jieba 不可用时的极简回退提取"""
        entities = []
        relations = []
        seen = set()

        for indicator_set, entity_type in [
            (_PERSON_INDICATORS, "person"),
            (_PLACE_INDICATORS, "place"),
            (_ORG_INDICATORS, "organization"),
        ]:
            for ind in indicator_set:
                pattern = rf"([\u4e00-\u9fff]{{1,6}}{re.escape(ind)})"
                matches = re.findall(pattern, text)
                for m in matches:
                    if m not in seen and len(entities) < 20:
                        seen.add(m)
                        entities.append(Entity(
                            name=m,
                            entity_type=entity_type,
                            properties={"extraction_mode": "rules_fallback"},
                        ))

        return entities, relations
