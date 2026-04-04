"""
策略蒸馏器（Strategy Distiller）

从知识图谱中的因果链自动生成可复用的决策策略候选。
在冥思流水线的步骤 6.5 中被调用。

Phase 3 新增模块。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cognitive.strategy_distiller")

_DISTILLATION_PROMPT = """你是一个策略分析专家。根据以下从知识图谱中提取的因果链，
生成可复用的决策策略。

因果链数据：
{causal_chains}

请分析这些因果链中的模式，生成策略建议。每个策略应包含：
1. name: 策略名称（英文，snake_case格式）
2. description: 策略描述
3. uses_real_data: 是否需要实时数据 (true/false)
4. applicable_scenarios: 适用场景列表
5. expected_accuracy: 预期准确率 (0-1)

请以 JSON 数组格式输出，最多{max_strategies}个策略：
[{{"name": "...", "description": "...", "uses_real_data": true,
   "applicable_scenarios": ["..."], "expected_accuracy": 0.7}}]"""


class StrategyDistiller:
    """
    从因果链蒸馏策略。

    接收来自 GraphStore.get_causal_chains() 的因果链数据，
    通过 LLM 分析因果模式并生成策略候选。
    """

    def __init__(self, llm_config):
        """
        Args:
            llm_config: MeditationLLMConfig 实例，包含 API 密钥、模型等配置
        """
        self.llm_config = llm_config
        self._client = None

    def _get_client(self):
        """延迟初始化 OpenAI 客户端"""
        if self._client is None:
            from openai import OpenAI
            kwargs = {}
            if self.llm_config.api_key:
                kwargs["api_key"] = self.llm_config.api_key
            if self.llm_config.base_url:
                kwargs["base_url"] = self.llm_config.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def distill(
        self,
        causal_chains: List[Dict[str, Any]],
        max_strategies: int = 3,
        temperature: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        从因果链蒸馏策略。

        Args:
            causal_chains: 因果链数据列表，每条链包含 chain_nodes 和 chain_relations
            max_strategies: 最多生成策略数
            temperature: LLM 调用温度

        Returns:
            策略候选列表，每个元素包含 name, description, uses_real_data,
            applicable_scenarios, expected_accuracy
        """
        if not causal_chains:
            return []

        # 格式化因果链为文本
        chains_text = self._format_chains(causal_chains)

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.llm_config.model,
                messages=[{
                    "role": "user",
                    "content": _DISTILLATION_PROMPT.format(
                        causal_chains=chains_text,
                        max_strategies=max_strategies,
                    )
                }],
                temperature=temperature,
                max_tokens=1024,
            )
            content = response.choices[0].message.content or "[]"
            return self._parse_strategies(content, max_strategies)
        except Exception as e:
            logger.error("Strategy distillation failed: %s", e)
            return []

    def _format_chains(self, chains: List[Dict[str, Any]]) -> str:
        """将因果链格式化为可读文本"""
        lines = []
        for i, chain in enumerate(chains[:10], 1):
            nodes = chain.get("chain_nodes", [])
            node_names = [n.get("name", "?") for n in nodes]
            lines.append(f"链{i}: {' → '.join(node_names)}")
        return "\n".join(lines)

    def _parse_strategies(
        self,
        content: str,
        max_count: int,
    ) -> List[Dict[str, Any]]:
        """解析 LLM 返回的策略 JSON"""
        # 尝试直接解析
        try:
            result = json.loads(content)
            if isinstance(result, list):
                return result[:max_count]
        except json.JSONDecodeError:
            pass

        # 尝试提取 JSON 数组
        json_match = re.search(r"\[[\s\S]*\]", content)
        if not json_match:
            logger.warning(
                "Failed to parse strategies from LLM response: %s",
                content[:200],
            )
            return []
        try:
            strategies = json.loads(json_match.group())
            if isinstance(strategies, list):
                return strategies[:max_count]
        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse JSON array from LLM response: %s",
                content[:200],
            )
        return []
