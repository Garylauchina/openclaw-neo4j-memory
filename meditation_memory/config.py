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
    """LLM 配置，用于实体抽取
    
    优先级：
    1. OPENAI_API_KEY / OPENAI_BASE_URL (如果指向 OpenRouter)
    2. LLM_MODEL (可选，默认 qwen/qwen3.6-plus:free 用于 OpenRouter)
    """

    api_key: Optional[str] = field(default_factory=lambda: (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("LITELLM_API_KEY")
    ))
    base_url: Optional[str] = field(default_factory=lambda: (
        os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    ))
    model: str = field(default_factory=lambda: (
        os.environ.get("LLM_MODEL")
        or os.environ.get("MEDITATION_LLM_MODEL", "qwen/qwen3.6-plus:free")
    ))


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
class SemanticSearchConfig:
    """语义搜索配置"""

    # 是否启用语义搜索兜底
    enabled: bool = True
    
    # 外部 embedding API 配置
    # 与 LLMConfig 复用同一个 API_KEY，用于 embedding API 调用
    embedding_api_key: Optional[str] = field(default_factory=lambda: (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("LITELLM_API_KEY")
    ))
    embedding_base_url: Optional[str] = field(default_factory=lambda: (
        os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    ))
    # 外部 embedding 模型
    embedding_model: str = field(default_factory=lambda: (
        os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    ))
    
    # 是否启用本地 TF-IDF 保底（仅当外部 API 不可用时）
    local_tfidf_enabled: bool = True
    
    # 语义搜索参数
    fallback_top_k: int = 5  # 语义兜底返回的候选实体数量
    min_semantic_similarity: float = 0.25  # 语义相似度最低阈值
    
    # 候选池限制（避免全量搜索造成性能问题）
    candidate_pool_limit: int = 300  # 最多从数据库取多少候选实体
    
    # 缓存配置
    enable_cache: bool = True
    cache_size: int = 500


@dataclass
class MemoryConfig:
    """记忆系统总配置"""

    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    subgraph: SubgraphConfig = field(default_factory=SubgraphConfig)
    semantic: SemanticSearchConfig = field(default_factory=SemanticSearchConfig)
