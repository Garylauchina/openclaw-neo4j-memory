# 冥思（Meditation）记忆图谱异步重整机制架构设计

**作者**: Manus AI
**日期**: 2026年3月31日

## 1. 概述

在当前的 OpenClaw 记忆系统中，`memory_api_server.py` 结合 `meditation_memory` 模块实现了基于 Neo4j 的记忆图谱自动抽取与写入。然而，由于实时写入依赖于规则回退或零样本 LLM 抽取，图谱中积累了大量低质量数据（如通用词实体、截断实体、单一的 `related_to` 关系以及孤立节点）。

借鉴人类睡眠期间大脑对记忆进行整理、修剪和巩固的机制，本设计提出了一种名为“冥思”（Meditation）的异步重整机制。冥思机制在系统空闲时运行，通过引入大语言模型（LLM）的深度语义理解能力，对图谱进行部分优化、实体对齐、关系重构和元知识蒸馏。其核心原则是**部分优化而非完整重构**，在保证记忆持久化基础不动摇的前提下，显著提升上下文检索的质量与准确性。

## 2. 冥思触发机制

为了在保证系统性能和图谱质量之间取得平衡，冥思机制采用**定时触发**与**条件触发**相结合的组合策略。这种设计确保了系统在空闲时段进行深度重整，同时在记忆发生剧烈变化时能够及时介入。

### 2.1 定时触发（Slow-wave Sleep）
定时触发类似于人类的慢波睡眠，主要负责日常的常规清理与巩固。
- **触发时间**：系统负载最低的时段（例如每日凌晨 03:00）。
- **执行策略**：遍历过去 24 小时内新增或更新的节点与边，执行轻量级的实体合并、孤立节点清理和权重衰减计算。
- **配置参数**：`CRON_SCHEDULE="0 3 * * *"`。

### 2.2 条件触发（REM Sleep）
条件触发类似于快速眼动（REM）睡眠，在系统接收大量新信息后启动，主要负责深度联想、关系推理和知识蒸馏。
- **触发条件**：
  - **变化量阈值**：自上次冥思以来，新增实体数或关系数超过设定阈值（如新增 100 个节点或 300 条边）。
  - **主题漂移检测**：在会话模式中，当 `SessionContext` 频繁触发主题切换（`topic_shift_threshold < 0.3` 的次数超过 5 次）时，表明用户引入了大量新领域的知识。
- **执行策略**：将新形成的子图与历史核心图谱进行交叉比对，进行跨会话主题关联和高层级元知识归纳。

## 3. 冥思流程步骤

冥思机制作为一个独立的后台流水线（Pipeline），包含以下有序步骤。每个步骤的输入输出明确，并按需调用 LLM。

**流程图描述**：
1. **数据快照与锁定**：获取当前待处理子图的快照，标记处理状态以避免与实时写入冲突。
2. **孤立节点清理（Pruning）**：扫描无边连接或无意义的通用词节点，进行软删除。
3. **实体整合与修复（Merging）**：识别同义实体和截断实体，合并节点并转移关系。
4. **关系推理与重标注（Restructuring）**：将通用的 `related_to` 关系具体化，并推断隐含关系。
5. **权重强化与衰减（Weighting）**：基于语义重要性和时间衰减模型，调整节点和边的检索权重。
6. **知识蒸馏（Distillation）**：从密集的事实网络中提取高层次的元知识。
7. **事务提交与解锁**：将所有变更作为一个 Neo4j 事务批量提交，记录冥思日志。

### 3.1 关键数据流与 LLM 调用
- **输入**：图数据库中标记为 `needs_meditation=true` 或在指定时间窗口内更新的子图。
- **LLM 调用方式**：为了避免受限于实时对话的延迟，冥思过程采用异步批处理调用（Batch API 或并发请求）。使用较高参数量和推理能力的模型（如 `gpt-4.1` 或 `claude-3.7-sonnet`），并设置较高的 `max_tokens` 以支持长上下文的语义分析。
- **输出**：更新后的图谱数据（合并的节点、新标注的关系、更新的权重属性以及生成的元知识节点）。

## 4. 权重强化和衰减模型

当前的图谱仅依赖简单的 `mention_count` 和 `updated_at` 进行统计，缺乏对记忆质量的评估。冥思机制引入由 LLM 参与语义判断的智能权重调整模型，计算每个节点和关系的**记忆激活值（Activation Level）**。

### 4.1 综合权重计算公式
激活值 $A(e)$ 综合考虑以下三个维度：
1. **频率与近因性（Recency & Frequency）**：基于 Ebbinghaus 遗忘曲线的时间衰减。
2. **语义重要性（Semantic Importance）**：LLM 评估该实体/关系对用户核心身份或长期目标的价值。
3. **网络中心度（Network Centrality）**：该节点在图谱中的 PageRank 或度中心性。

### 4.2 LLM 语义判断机制
在冥思期间，系统会提取高频但低权重的关系，构建 Prompt 询问 LLM 其重要性：
```markdown
**System Prompt:**
你是一个记忆评估专家。请评估以下实体和关系对用户长期记忆的价值。
评分范围为 0.0 到 1.0。0.0 表示无意义的口语词或临时状态，1.0 表示用户的核心偏好、重要事实或长期目标。

**User Input:**
实体: "报告" (mention_count: 45)
关系: "用户" -[related_to]-> "报告"

**Expected JSON Output:**
{
  "semantic_score": 0.1,
  "reason": "通用名词，缺乏具体指代，属于临时操作对象，不具备长期记忆价值。"
}
```

### 4.3 权重应用
- **强化**：对于 `semantic_score > 0.8` 且频繁被检索的核心节点（如“比特币”），其权重衰减率降低，确保在 `SubgraphContext` 检索时始终优先召回。
- **衰减与遗忘**：对于 `semantic_score < 0.3` 且长时间未被访问的节点，逐步降低其激活值。当激活值低于阈值时，将其标记为 `archived=true`，在常规检索中被忽略，从而保持图谱的整洁与高效。

## 5. 实体整合与关系推理规则

当前图谱面临的核心问题之一是实体碎片化和关系语义缺失。冥思机制通过批量图查询和 LLM 推理来解决这些问题。

### 5.1 实体整合规则 (Entity Resolution)
实体整合旨在消除图谱中的冗余，建立单一真实来源（Single Source of Truth）。

1. **同义实体合并**：
   - 提取候选对：利用全文索引或向量嵌入，找出名称相似度高或拥有大量共同邻居节点的实体对（如“比特币”与“BTC”）。
   - LLM 验证：将候选对及其上下文发送给 LLM，判断是否为同一现实世界实体。
   - 合并操作：保留高频或更标准的名称作为主节点，将另一个节点的所有关系转移至主节点，并将被合并名称加入主节点的 `aliases` 属性中。
   
   *Cypher 示例（合并节点并转移关系）*：
   ```cypher
   MATCH (main:Entity {name: "比特币"}), (alias:Entity {name: "BTC"})
   CALL apoc.refactor.mergeNodes([main, alias], {
     properties: "combine",
     mergeRels: true
   }) YIELD node
   RETURN node
   ```

2. **截断实体修复**：
   - 识别异常节点：找出名称长度过短（如单字）或不符合语言习惯的实体（如“术发展”）。
   - 上下文回溯：结合其相连的节点和最近的会话记录，由 LLM 推断完整的实体名称。
   - 修复：更新节点 `name` 属性，例如将“术发展”修复为“技术发展”。

3. **类型与描述补充**：
   - 对于 `type` 和 `description` 为空的节点，LLM 根据其关联边推断其类别（person, organization, concept 等），并生成简短描述写入 `description` 字段。

### 5.2 关系推理规则
当前系统回退模式产生的大量边都是 `related_to`。冥思机制需要对其进行重标注和深化。

1. **关系重标注（Re-labeling）**：
   - 提取特定实体间高频的 `related_to` 边及其来源文本。
   - LLM 根据预定义的语义关系本体库（如 `uses`, `owns`, `located_in`, `works_at`, `interested_in`）进行重新分类。
   - 更新边属性 `relation_type`，保留原 `related_to` 标签以兼容现有查询，但通过属性实现细粒度检索。

2. **隐含关系发现（Link Prediction）**：
   - 基于图结构进行推理。例如，如果 `(User)-[owns]->(Project A)` 且 `(Project A)-[uses]->(Neo4j)`，则推断出 `(User)-[familiar_with]->(Neo4j)`。
   - 跨会话主题关联：如果会话 1 讨论了“OpenClaw 架构”，会话 2 讨论了“去中心化 AI”，冥思机制可以建立 `(OpenClaw)-[is_instance_of]->(Decentralized AI)` 的新边。

## 6. 知识蒸馏 (Knowledge Distillation)

随着对话的积累，图谱中会充斥着大量低层级的事实关系（如“用户今天早上阅读了比特币白皮书”）。知识蒸馏的目的是将这些碎片化信息归纳为高层级的**元知识（Meta-Knowledge）**。

### 6.1 蒸馏过程
- **子图提取**：选取以用户节点（或核心关注对象）为中心、具有高聚集系数的子图。
- **LLM 归纳**：
  ```markdown
  **System Prompt:**
  分析以下实体及其关系，提取出关于用户的高层次洞察或规律（不超过一句话）。
  
  **Input:**
  (Gary)-[related_to]->(比特币价格)
  (Gary)-[related_to]->(闪电网络)
  (Gary)-[related_to]->(去中心化架构)
  
  **Output:**
  "Gary 持续关注比特币技术发展（如闪电网络）及其价格走势，并对去中心化架构感兴趣。"
  ```

### 6.2 元知识的存储与检索优先级
- **存储方式**：将归纳出的结论存储为一种特殊类型的实体节点（`entity_type: "meta_knowledge"`），并建立从该节点到相关底层事实节点的 `[SUMMARIZES]` 关系。
- **检索优先级**：在 `SubgraphContext` 构建系统提示词时，优先检索 `meta_knowledge` 节点。只有当用户提问涉及具体细节时，才沿着 `SUMMARIZES` 边向下钻取底层事实。这大幅减少了注入 Prompt 的 token 消耗，并提高了上下文的信噪比。

## 7. 与现有系统的集成方式

为了不影响当前 `memory_api_server.py` 的实时响应能力，并保持 OpenClaw 架构的解耦特性，冥思机制设计为**独立的异步 Worker 进程**。

### 7.1 架构设计
- **Meditation Worker**：一个独立的 Python 进程（或 Celery/APScheduler 定时任务），与 `memory_api_server.py` 共享底层的 `GraphStore` 模块。
- **通信与协调**：
  - API Server 在处理 `/ingest` 时，对于新写入的节点标记属性 `needs_meditation: true`。
  - Worker 定期（或由 API Server 通过内部信号触发）唤醒，扫描这些标记节点进行处理。
- **与 OpenClaw 插件的协作**：
  - OpenClaw 插件（`index.ts`）无需修改其原有的 fire-and-forget 写入逻辑。
  - 冥思完成后，Worker 会更新图谱。下一次插件调用 `/search` 时，将自动获得经过优化、合并和提炼的高质量子图上下文。

### 7.2 伪代码结构示例
```python
# meditation_worker.py
class MeditationEngine:
    def __init__(self, graph_store, llm_client):
        self.store = graph_store
        self.llm = llm_client

    def run_nightly_consolidation(self):
        # 1. 锁定图谱（或使用事务隔离）
        # 2. 提取需要冥思的子图
        subgraph = self.store.get_nodes_needing_meditation()
        
        # 3. 实体合并与修复
        merged_ops = self._resolve_entities(subgraph)
        
        # 4. 关系重构
        rel_ops = self._infer_relations(subgraph)
        
        # 5. 知识蒸馏
        meta_knowledge = self._distill_knowledge(subgraph)
        
        # 6. 批量提交更新，并清除 needs_meditation 标记
        self.store.apply_meditation_batch(merged_ops, rel_ops, meta_knowledge)
```

## 8. 安全机制

冥思机制涉及对核心记忆的大规模修改，必须具备严格的安全和防错机制，以确保记忆持久化这一“不可动摇的基础”。

### 8.1 数据备份与回滚策略
- **冥思前快照**：在执行合并或删除操作前，利用 Neo4j 的 APOC 插件（如 `apoc.export.graphml.all`）对受影响的子图进行局部导出备份。
- **软删除（Soft Delete）**：冥思过程不执行物理 `DELETE`。对于被清理的孤立节点或合并后的冗余节点，添加标签 `:Archived` 并设置属性 `archived_at`。检索接口（`GraphStore.search_entities`）需更新为默认过滤掉 `:Archived` 节点。
- **版本控制**：为重要实体引入版本历史。每次冥思修改 `description` 或 `properties` 时，将旧值追加到节点的 `history` 数组属性中。

### 8.2 并发控制
- **避免读写冲突**：Meditation Worker 在更新节点时，利用 Neo4j 的事务机制保证原子性。
- **细粒度锁**：对于正在被 `memory_api_server.py` 实时写入的会话上下文节点，Worker 在检测到其 `updated_at` 在过去 5 分钟内发生变化时，跳过该节点的冥思操作，留待下一个周期处理，从而避免锁竞争和数据覆盖。
- **Dry-Run 模式**：提供只读模式，允许开发者在不修改数据库的情况下，预览 LLM 建议的合并和蒸馏结果，用于调试 Prompt 和权重模型。

---
## 附录：配置参数说明

在 `MemoryConfig` 中新增 `MeditationConfig` 模块：

```python
@dataclass
class MeditationConfig:
    enabled: bool = True
    # 触发策略
    cron_schedule: str = "0 3 * * *"  # 每天凌晨3点
    trigger_node_threshold: int = 100 # 节点变化阈值
    # LLM 配置
    llm_model: str = "gpt-4.1"        # 冥思通常需要更强推理能力的模型
    batch_size: int = 50              # 每次处理的实体/关系对数量
    # 权重模型
    decay_factor: float = 0.95        # 每日权重衰减率
    min_activation_threshold: float = 0.1 # 归档阈值
```
