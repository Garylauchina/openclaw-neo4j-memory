# Neo4j 图谱记忆系统 — 工具与 API 完整说明

你拥有一个基于 Neo4j 知识图谱的长期记忆系统，运行在本地 `http://127.0.0.1:18900`。
该系统包含两大模块：**核心记忆**（读写查询）和**冥思机制**（异步图谱重整）。

---

## 一、核心记忆工具（通过 OpenClaw 工具调用）

### neo4j_memory_store

将重要信息写入长期记忆。系统会自动从文本中抽取实体和关系。

**何时使用：**
- 用户分享了重要的个人信息（姓名、职业、偏好等）
- 对话中出现了值得记住的事实或决定
- 用户明确要求你记住某些内容
- 对话结束时，总结并保存关键信息

**参数：**
- `text`：要写入记忆的文本内容

### neo4j_memory_search

从长期记忆中搜索相关信息。

**何时使用：**
- 用户提到之前聊过的话题
- 需要回忆用户的偏好或背景信息
- 用户问"你还记得..."之类的问题
- 对话开始时，主动检索与用户相关的背景

**参数：**
- `query`：搜索查询文本

### neo4j_memory_stats

查看记忆系统状态和统计信息。

**何时使用：**
- 用户询问记忆系统的状态
- 需要确认记忆系统是否正常工作
- 想了解已存储的记忆规模

---

## 二、冥思（Meditation）— 记忆图谱异步重整机制

冥思是一个后台运行的图谱优化流水线，类似大脑睡眠时的记忆整理过程。
它会自动执行：剪枝低质量节点、合并重复实体、语义化关系类型、调整权重、蒸馏元知识。

### 触发方式

冥思支持三种触发方式：

1. **定时触发（Slow-wave Sleep）**：按 cron 表达式定时执行，默认每天凌晨 3:00
2. **条件触发（REM Sleep）**：当新增节点或关系超过阈值时自动触发
3. **手动触发**：通过 API 调用立即触发

### 冥思 HTTP API

以下 API 均可通过 HTTP 直接调用（base URL: `http://127.0.0.1:18900`）。

#### GET /meditation/config

查看当前冥思调度配置。

```bash
curl http://127.0.0.1:18900/meditation/config
```

返回示例：
```json
{
  "enabled": true,
  "trigger": {
    "cron_schedule": "0 3 * * *",
    "min_interval_seconds": 3600,
    "trigger_node_threshold": 100,
    "trigger_edge_threshold": 300,
    "topic_shift_count_threshold": 5
  },
  "scheduler_running": true,
  "last_run_time": 1743400000.0
}
```

#### POST /meditation/schedule

动态修改冥思调度配置。修改后立即生效，无需重启服务。

**参数（均为可选，只传需要修改的字段）：**

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `enabled` | boolean | 启用/禁用冥思调度器 | true |
| `cron_schedule` | string | 定时触发 cron 表达式（分 时 日 月 周） | "0 3 * * *" |
| `min_interval_seconds` | int | 两次冥思之间的最小间隔（秒） | 3600 |
| `trigger_node_threshold` | int | 条件触发：新增节点数阈值 | 100 |
| `trigger_edge_threshold` | int | 条件触发：新增关系数阈值 | 300 |

```bash
# 示例：设置每天凌晨 4 点执行，最小间隔 2 小时
curl -X POST http://127.0.0.1:18900/meditation/schedule \
  -H 'Content-Type: application/json' \
  -d '{"cron_schedule": "0 4 * * *", "min_interval_seconds": 7200}'

# 示例：临时禁用冥思
curl -X POST http://127.0.0.1:18900/meditation/schedule \
  -H 'Content-Type: application/json' \
  -d '{"enabled": false}'

# 示例：降低条件触发阈值，让冥思更频繁运行
curl -X POST http://127.0.0.1:18900/meditation/schedule \
  -H 'Content-Type: application/json' \
  -d '{"trigger_node_threshold": 50, "trigger_edge_threshold": 150}'
```

#### POST /meditation/trigger

手动触发一次冥思运行（后台异步执行）。

**参数：**

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `mode` | string | 运行模式：auto / manual / dry_run | "auto" |
| `target_nodes` | string[] | 指定处理的节点名称列表（可选） | null（处理所有待处理节点） |

```bash
# 手动触发
curl -X POST http://127.0.0.1:18900/meditation/trigger \
  -H 'Content-Type: application/json' \
  -d '{"mode": "manual"}'

# 预览模式（不实际修改数据）
curl -X POST http://127.0.0.1:18900/meditation/trigger \
  -H 'Content-Type: application/json' \
  -d '{"mode": "dry_run"}'
```

#### GET /meditation/status

查看当前冥思运行状态。

```bash
curl http://127.0.0.1:18900/meditation/status
```

返回 `"status": "idle"` 表示空闲，`"status": "running"` 表示正在执行。

#### GET /meditation/history?limit=10

查看冥思运行历史记录。

```bash
curl "http://127.0.0.1:18900/meditation/history?limit=5"
```

#### POST /meditation/dry-run

预览冥思将会做什么，不实际修改数据。

```bash
curl -X POST http://127.0.0.1:18900/meditation/dry-run \
  -H 'Content-Type: application/json' \
  -d '{}'
```

---

## 三、其他 API

#### GET /health

检查服务健康状态和 Neo4j 连接。

#### GET /stats

获取图谱统计信息（节点数、关系数、冥思统计等）。

#### POST /ingest

写入记忆（与 neo4j_memory_store 工具等效）。

参数：`{"text": "...", "use_llm": true, "async_mode": false}`

#### POST /search

搜索记忆（与 neo4j_memory_search 工具等效）。

参数：`{"query": "...", "use_llm": true}`

---

## 四、使用建议

### 记忆读写
1. **主动记忆**：在对话中遇到重要信息时，主动使用 `neo4j_memory_store` 保存
2. **主动回忆**：在回答问题前，先用 `neo4j_memory_search` 检索相关背景
3. **自然融合**：将检索到的记忆自然地融入回答中，不要生硬地列出
4. **避免重复**：不要反复存储相同的信息

### 冥思管理
1. **日常运行**：冥思默认每天凌晨 3 点自动运行，通常无需干预
2. **查看效果**：通过 `/meditation/history` 查看每次运行的统计（剪枝数、合并数、蒸馏数等）
3. **调整频率**：如果图谱增长较快，可通过 `/meditation/schedule` 降低触发阈值或增加定时频率
4. **手动触发**：用户要求整理记忆时，可通过 `/meditation/trigger` 手动触发
5. **安全预览**：不确定效果时，先用 dry_run 模式预览

### 冥思 7 步流水线说明
1. **快照**：记录运行前的图谱状态基线
2. **剪枝**：归档低质量、孤立、过期的节点
3. **实体合并**：通过 LLM 判断并合并同义实体
4. **关系重构**：将泛化的 `related_to` 关系重标注为语义化类型（如 causes, uses, part_of）
5. **权重调整**：基于语义评分、提及次数、连接度计算节点激活值
6. **知识蒸馏**：为高连接度实体生成元知识摘要节点
7. **提交**：记录运行结果，清除已处理节点的冥思标记
