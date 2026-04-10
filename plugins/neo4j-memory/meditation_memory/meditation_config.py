"""
冥思（Meditation）配置模块

定义冥思机制的所有可配置参数，包括：
  - 触发策略（定时 / 条件触发）
  - LLM 调用配置
  - 权重模型参数
  - 安全与并发控制参数
  - 知识蒸馏参数
  - 策略蒸馏与进化参数（Phase 3）

所有配置通过环境变量读取，支持合理的默认值。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

# 成本保护配置（Issue #37）
from .meditation_cost_config import MeditationCostConfig


@dataclass
class MeditationTriggerConfig:
    """
    冥思触发策略配置

    支持两种触发模式：
      1. 定时触发（Slow-wave Sleep）— 每日凌晨执行常规清理
      2. 条件触发（REM Sleep）— 变化量超过阈值时启动深度重整
    """

    # 定时触发 cron 表达式（默认每天凌晨 3 点）
    cron_schedule: str = field(
        default_factory=lambda: os.environ.get(
            "MEDITATION_CRON_SCHEDULE", "0 3 * * *"
        )
    )

    # 条件触发：新增节点数阈值
    trigger_node_threshold: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_NODE_THRESHOLD", "100")
        )
    )

    # 条件触发：新增关系数阈值
    trigger_edge_threshold: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_EDGE_THRESHOLD", "300")
        )
    )

    # 条件触发：主题漂移检测次数阈值
    topic_shift_count_threshold: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_TOPIC_SHIFT_THRESHOLD", "5")
        )
    )

    # 两次冥思之间的最小间隔（秒），防止频繁触发
    min_interval_seconds: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_MIN_INTERVAL", "3600")
        )
    )


@dataclass
class MeditationLLMConfig:
    """
    冥思专用 LLM 配置

    冥思通常需要更强推理能力的模型，与实时对话使用的轻量模型分开配置。
    """

    # OpenAI 兼容 API 密钥（默认共用环境变量）
    api_key: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY")
    )

    # API Base URL（可选，用于兼容第三方 API）
    base_url: Optional[str] = field(
        default_factory=lambda: os.environ.get("OPENAI_BASE_URL")
    )

    # 冥思使用的模型（默认使用更强的推理模型）
    model: str = field(
        default_factory=lambda: os.environ.get(
            "MEDITATION_LLM_MODEL", "deepseek/deepseek-chat"
        )
    )

    # 每批处理的实体/关系对数量
    batch_size: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_BATCH_SIZE", "50")
        )
    )

    # LLM 调用超时（秒）
    request_timeout: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_LLM_TIMEOUT", "120")
        )
    )

    # LLM 调用最大并发数
    max_concurrent_requests: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_LLM_CONCURRENCY", "5")
        )
    )

    # LLM 调用最大重试次数
    max_retries: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_LLM_RETRIES", "3")
        )
    )

    # temperature（冥思场景需要确定性输出，默认较低）
    temperature: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_LLM_TEMPERATURE", "0.1")
        )
    )


@dataclass
class MeditationWeightConfig:
    """
    权重强化与衰减模型参数

    激活值 A(e) 综合考虑三个维度：
      1. 频率与近因性（Recency & Frequency）— 基于 Ebbinghaus 遗忘曲线
      2. 语义重要性（Semantic Importance）— LLM 评估
      3. 网络中心度（Network Centrality）— PageRank / 度中心性
    """

    # 每日权重衰减率（基于 Ebbinghaus 遗忘曲线）
    decay_factor: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_DECAY_FACTOR", "0.95")
        )
    )

    # 归档阈值：激活值低于此值的节点将被标记为 archived
    min_activation_threshold: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_MIN_ACTIVATION", "0.1")
        )
    )

    # 语义评分高阈值：高于此值的节点衰减率降低
    high_semantic_threshold: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_HIGH_SEMANTIC", "0.8")
        )
    )

    # 语义评分低阈值：低于此值且长时间未访问的节点加速衰减
    low_semantic_threshold: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_LOW_SEMANTIC", "0.3")
        )
    )

    # 四个维度的权重系数（总和为 1.0）
    recency_weight: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_RECENCY_WEIGHT", "0.25")
        )
    )
    semantic_weight: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_SEMANTIC_WEIGHT", "0.35")
        )
    )
    centrality_weight: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_CENTRALITY_WEIGHT", "0.25")
        )
    )
    frequency_weight: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_FREQUENCY_WEIGHT", "0.15")
        )
    )
    
    # 提及频次阈值
    high_mention_threshold: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_HIGH_MENTION_THRESHOLD", "10")
        )
    )
    medium_mention_threshold: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_MEDIUM_MENTION_THRESHOLD", "3")
        )
    )

    # 核心节点衰减率降低倍数（对高语义评分节点）
    core_decay_reduction: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_CORE_DECAY_REDUCTION", "0.5")
        )
    )


@dataclass
class MeditationPruningConfig:
    """孤立节点清理（Pruning）配置"""

    # 孤立节点的最小 mention_count 阈值：低于此值的孤立节点将被清理
    orphan_min_mentions: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_ORPHAN_MIN_MENTIONS", "2")
        )
    )

    # 通用词黑名单（这些词即使有连接也可能被清理）
    generic_words: List[str] = field(
        default_factory=lambda: [
            "东西", "事情", "内容", "方面", "情况", "问题", "部分",
            "方法", "方式", "过程", "结果", "目的", "原因", "条件",
            "thing", "stuff", "something", "it", "this", "that",
        ]
    )

    # 实体名称最短长度（低于此长度的实体视为可疑截断）
    min_entity_name_length: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_MIN_NAME_LENGTH", "2")
        )
    )


@dataclass
class MeditationMergingConfig:
    """实体整合与修复（Merging）配置"""

    # 名称相似度阈值（用于同义实体候选对筛选）
    name_similarity_threshold: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_NAME_SIMILARITY", "0.75")
        )
    )

    # 共同邻居数阈值（超过此值的实体对视为候选合并对）
    common_neighbor_threshold: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_COMMON_NEIGHBORS", "3")
        )
    )

    # 截断实体修复：名称长度低于此值视为可能截断
    truncation_name_length: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_TRUNCATION_LENGTH", "2")
        )
    )


@dataclass
class MeditationRestructuringConfig:
    """关系推理与重标注（Restructuring）配置"""

    # 预定义的语义关系本体库
    relation_ontology: List[str] = field(
        default_factory=lambda: [
            "uses",           # 使用
            "owns",           # 拥有
            "located_in",     # 位于
            "works_at",       # 工作于
            "interested_in",  # 感兴趣
            "created_by",     # 由…创建
            "part_of",        # 属于
            "depends_on",     # 依赖于
            "causes",         # 导致
            "knows",          # 认识
            "contains",       # 包含
            "belongs_to",     # 属于
            "is_instance_of", # 是…的实例
            "familiar_with",  # 熟悉
            "studies",        # 研究
            "manages",        # 管理
            "collaborates_with",  # 合作
            "opposes",        # 反对
            "supports",       # 支持
            "derived_from",   # 源自
            # Phase 3: 因果与目标关系类型
            "leads_to",       # 引向
            "precedes",       # 先于
            "prevents",       # 阻止
            "achieves",       # 实现
            "aims_at",        # 目标是
        ]
    )

    # 每批处理的 related_to 关系数量
    relabel_batch_size: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_RELABEL_BATCH", "500")
        )
    )


@dataclass
class MeditationDistillationConfig:
    """知识蒸馏（Distillation）配置"""

    # 子图聚集系数阈值（高于此值的子图才进行蒸馏）
    min_cluster_size: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_MIN_CLUSTER_SIZE", "3")
        )
    )

    # 每次蒸馏生成的元知识节点数上限
    max_meta_nodes_per_run: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_MAX_META_NODES", "50")
        )
    )

    # 元知识节点的实体类型标识
    meta_knowledge_entity_type: str = "meta_knowledge"

    # 元知识到底层事实的关系类型
    summarizes_relation_type: str = "SUMMARIZES"


@dataclass
class MeditationStrategyConfig:
    """策略蒸馏与进化配置（Phase 3）"""

    # 策略蒸馏：最小因果链长度（低于此长度的链不参与蒸馏）
    min_causal_chain_length: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_MIN_CHAIN_LENGTH", "3")
        )
    )

    # 策略蒸馏：每次冥思最多生成的新策略数
    max_strategies_per_run: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_MAX_NEW_STRATEGIES", "20")
        )
    )

    # 策略进化：适应度淘汰阈值（低于此值的策略被归档）
    fitness_elimination_threshold: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_FITNESS_ELIMINATION", "0.2")
        )
    )

    # 策略进化：现实数据策略的保护阈值（更低，给予保护）
    reality_protection_threshold: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_REALITY_PROTECTION", "0.15")
        )
    )

    # 策略进化：最小策略池大小（低于此数量不执行淘汰）
    min_strategy_pool_size: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_MIN_STRATEGY_POOL", "3")
        )
    )

    # 策略进化：交叉概率
    crossover_rate: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_CROSSOVER_RATE", "0.3")
        )
    )

    # 策略进化：突变概率
    mutation_rate: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_MUTATION_RATE", "0.1")
        )
    )

    # 策略蒸馏使用的 LLM 提示词温度（略高于常规冥思，鼓励创造性）
    distillation_temperature: float = field(
        default_factory=lambda: float(
            os.environ.get("MEDITATION_STRATEGY_TEMPERATURE", "0.3")
        )
    )


@dataclass
class MeditationSafetyConfig:
    """安全机制配置"""

    # 并发控制：跳过最近 N 秒内更新的节点
    skip_recently_updated_seconds: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_SKIP_RECENT_SECONDS", "300")
        )
    )

    # 是否启用冥思前快照备份
    enable_snapshot: bool = field(
        default_factory=lambda: os.environ.get(
            "MEDITATION_ENABLE_SNAPSHOT", "true"
        ).lower() == "true"
    )

    # 快照存储目录
    snapshot_dir: str = field(
        default_factory=lambda: os.environ.get(
            "MEDITATION_SNAPSHOT_DIR", "/tmp/meditation_snapshots"
        )
    )

    # 最大保留快照数
    max_snapshots: int = field(
        default_factory=lambda: int(
            os.environ.get("MEDITATION_MAX_SNAPSHOTS", "10")
        )
    )

    # Dry-Run 模式（只预览不提交）
    dry_run: bool = field(
        default_factory=lambda: os.environ.get(
            "MEDITATION_DRY_RUN", "false"
        ).lower() == "true"
    )


@dataclass
class MeditationConfig:
    """
    冥思机制总配置

    整合所有子配置模块，提供统一的配置入口。
    """

    # 是否启用冥思机制
    enabled: bool = field(
        default_factory=lambda: os.environ.get(
            "MEDITATION_ENABLED", "true"
        ).lower() == "true"
    )

    # 子配置模块
    trigger: MeditationTriggerConfig = field(default_factory=MeditationTriggerConfig)
    llm: MeditationLLMConfig = field(default_factory=MeditationLLMConfig)
    weight: MeditationWeightConfig = field(default_factory=MeditationWeightConfig)
    pruning: MeditationPruningConfig = field(default_factory=MeditationPruningConfig)
    merging: MeditationMergingConfig = field(default_factory=MeditationMergingConfig)
    restructuring: MeditationRestructuringConfig = field(
        default_factory=MeditationRestructuringConfig
    )
    distillation: MeditationDistillationConfig = field(
        default_factory=MeditationDistillationConfig
    )
    safety: MeditationSafetyConfig = field(default_factory=MeditationSafetyConfig)
    # Phase 3: 策略蒸馏与进化配置
    strategy: MeditationStrategyConfig = field(
        default_factory=MeditationStrategyConfig
    )
    # Issue #37: 成本保护配置
    cost: MeditationCostConfig = field(default_factory=MeditationCostConfig)

    def to_dict(self) -> dict:
        """将配置序列化为字典（用于日志和 API 响应）"""
        import dataclasses
        result = {}
        for f in dataclasses.fields(self):
            val = getattr(self, f.name)
            if dataclasses.is_dataclass(val):
                sub = {}
                for sf in dataclasses.fields(val):
                    sv = getattr(val, sf.name)
                    sub[sf.name] = sv
                result[f.name] = sub
            else:
                result[f.name] = val
        return result
