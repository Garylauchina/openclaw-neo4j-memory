# Neo4j 图谱记忆系统工具

这是面向 OpenClaw 的 Neo4j Memory MVP skill 说明。

核心约定：
- **tool** = 原子能力接口
- **skill** = 任务级编排 / workflow

当前主线能力来自：
- `meditation_memory/`
- `memory_api_server.py`
- 少量 `scripts/`

MVP 封装参考：
- `openclaw_memory_mvp.py`
- `docs/openclaw-memory-mvp.md`

## MVP Tool Surface

### ingest_memory
将重要信息写入长期记忆。系统会自动抽取实体和关系。

**何时使用：**
- 用户分享了值得长期保留的信息
- 对话中出现了事实、偏好、决定、经验总结
- 用户明确要求“记住这个”
- 一轮任务结束后，需要沉淀 durable memory

**参数：**
- `text`: 需要写入的正文
- `metadata`（可选）: 来源、标签、额外上下文
- `use_llm`（可选）: 是否使用 LLM 抽取

### retrieve_context
从长期记忆中检索相关上下文。

**何时使用：**
- 回答前需要回忆历史背景
- 用户提到之前聊过的话题
- 需要找回偏好、身份、长期项目上下文

**参数：**
- `query`: 查询文本
- `options`（可选）: 如 `use_llm`

### build_prompt_context
构造可直接注入的增强 prompt 上下文。

**何时使用：**
- 需要把结构化记忆直接拼进回答前上下文
- 希望使用当前 prompt injection / strategy injection 主线能力

**参数：**
- `query`: 查询文本
- `options`（可选）: 如 `base_prompt`, `use_llm`

### memory_stats
查看记忆系统状态和统计信息。

**何时使用：**
- 用户询问记忆系统状态
- 需要确认系统是否健康
- 想观察 hypothesis/stable/pending 等数量

## 推荐 Skill Workflow

### 对话记忆辅助
1. 回答前，按需调用 `retrieve_context`
2. 若需要更强注入，再调用 `build_prompt_context`
3. 对话中出现 durable 信息时，调用 `ingest_memory`
4. 不要为了每句话都写库，保持节制

### 后台维护
- meditation 作为低频后台能力单独触发
- 不要默认塞进每轮回答路径
- 当前 MVP 不把 meditation 编进核心 conversation skill

## 使用建议

1. **先检索，再增强**：优先 `retrieve_context`，必要时再 `build_prompt_context`
2. **节制写入**：只写 durable memory，不把所有对话原样入库
3. **技能负责编排，工具负责能力**：不要把 graph 逻辑复制到 skill 层
4. **保持主线一致**：默认围绕 `meditation_memory/` 主线调用，不继续依赖镜像路径
