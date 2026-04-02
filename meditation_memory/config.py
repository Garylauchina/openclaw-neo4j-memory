"""
记忆系统配置模块

所有配置通过环境变量读取，支持合理的默认值。
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Neo4jConfig:
    """Neo4j 连接配置，从环境变量读取"""

    uri: str = field(default_factory=lambda: os.environ.get("NEO4J_URI", "bolt://localhost:7687"))
    user: str = field(default_factory=lambda: os.environ.get("NEO4J_USER", "neo4j"))
    password: str = field(default_factory=lambda: os.environ.get("NEO4J_PASSWORD", "password"))
    database: str = field(default_factory=lambda: os.environ.get("NEO4J_DATABASE", "neo4j"))


@dataclass
class LLMConfig:
    """LLM 配置，用于实体抽取"""

    api_key: Optional[str] = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY"))
    base_url: Optional[str] = field(default_factory=lambda: os.environ.get("OPENAI_BASE_URL"))
    model: str = field(default_factory=lambda: os.environ.get("LLM_MODEL", "gpt-4.1-mini"))


@dataclass
class SubgraphConfig:
    """动态子图构建配置"""

    # 子图规模硬约束
    max_nodes: int = 30
    max_edges: int = 60
    max_depth: int = 2

    # 检索参数
    top_k_entities: int = 10
    min_relevance_score: float = 0.3

    # 提示词模板中子图上下文的最大 token 数（粗略估计）
    max_context_chars: int = 2000

    # 会话级缓存配置
    session_cache_enabled: bool = True
    # 主题变化检测阈值：当前消息的实体与缓存子图实体的重叠度低于此值时，认为主题变化
    topic_shift_threshold: float = 0.3


@dataclass
class MemoryConfig:
    """记忆系统总配置"""

    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    subgraph: SubgraphConfig = field(default_factory=SubgraphConfig)
