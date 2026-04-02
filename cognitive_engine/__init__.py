"""
认知引擎（Cognitive Engine）

从 cognitive-system 仓库融合而来，对接 openclaw-neo4j-memory 的 Neo4j 存储层。
提供完整的认知处理管道，包括：
  - CognitiveCore: 认知内核，12步处理管道
  - Neo4jMemoryClient: Neo4j API 客户端
  - 策略引擎、RQS系统、自我纠错推理器等子系统

第一阶段（Phase 1）：对接存储层
  - memory_provider 对接 /search API
  - reality_writer 对接 /ingest API
  - Neo4j 不可用时自动降级到 Mock 模式
"""

__version__ = "1.0.0-phase1"
