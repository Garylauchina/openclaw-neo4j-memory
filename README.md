# openclaw-neo4j-memory

> 本文档面向 OpenClaw Agent 自主阅读和执行。你可以通过读取本指南完成自我部署、自我修复和自我升级。

## 0. 兆底自修复（自部署的第一件事）

> **核心原则：只要你能启动 + 有 LLM 可用，你就能自己修复一切。**

你的所有能力（读代码、执行命令、分析日志、安装依赖、重启服务）都建立在两个前提上：
1. **Gateway 能启动**：OpenClaw 主进程正常运行
2. **有一个 LLM 可用**：能调通至少一个语言模型

如果你发现自己刚启动、或者系统崩溃后恢复，**立即执行以下兆底检查**：

### 0.1 检查 Gateway

```bash
# 检查 OpenClaw 主进程是否在运行
ps aux | grep -E "node.*openclaw|node.*index.js" | grep -v grep

# 检查 Gateway 端口
lsof -i :18789 | grep LISTEN

# 如果 Gateway 没运行，尝试重启：
launchctl stop com.openclaw.gateway 2>/dev/null || true
sleep 2
launchctl start com.openclaw.gateway 2>/dev/null || true
sleep 5
lsof -i :18789 | grep LISTEN

# 如果仍然失败，检查关键文件是否存在：
ls /opt/homebrew/lib/node_modules/openclaw/dist/index.js 2>/dev/null || echo "MISSING"
# 如果 MISSING，重装 OpenClaw：
npm install -g openclaw
```

### 0.2 检查 LLM 可用性

```bash
# 确认环境变量存在
echo $OPENAI_API_KEY | head -c 10
echo $OPENAI_BASE_URL

# 如果环境变量为空，从 ~/.zshrc 加载：
source ~/.zshrc

# 测试 LLM 调用：
python3 -c "
from openai import OpenAI
import os
client = OpenAI(
    api_key=os.environ.get('OPENAI_API_KEY'),
    base_url=os.environ.get('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')
)
r = client.chat.completions.create(
    model=os.environ.get('MEDITATION_LLM_MODEL', 'qwen/qwen3-235b-a22b:free'),
    messages=[{'role':'user','content':'ping'}],
    max_tokens=3
)
print('LLM OK:', r.choices[0].message.content)
"
```

### 0.3 兆底逻辑

```
Gateway 能启动？
  ├─ 是 → LLM 可用？
  │       ├─ 是 → 你已具备完整自修复能力。
  │       │        读取本 README 剩余章节，自行诊断和修复其他组件。
  │       └─ 否 → 检查 ~/.zshrc 中的 OPENAI_API_KEY 和 OPENAI_BASE_URL。
  │                如果 key 失效，通知用户更新 API key。
  │                如果网络问题，等待 5 分钟后重试。
  └─ 否 → 检查 Node.js 和 OpenClaw 安装状态：
           node --version
           npm list -g openclaw
           如果缺失，执行 npm install -g openclaw
           如果 Node.js 本身不存在，通知用户安装 Node.js。
```

### 0.4 兆底红线

以下情况**绝对不要自动处理**，必须通知用户：
- `docker rm reflection-neo4j`（删除 Neo4j 容器会丢失所有图谱数据）
- `docker run --name reflection-neo4j`（重建容器会丢失数据卷）
- 任何涉及 Neo4j 数据目录的删除操作
- LLM API Key 失效（401 错误，需要用户提供新 key）
- 同一故障自动修复连续失败 3 次

### 0.5 修复前必做：创建回滚点

任何修改操作（git pull、pip install、改配置）之前，先记录当前状态：

```bash
# 代码回滚点
cd ~/.openclaw/workspace/plugins/neo4j-memory
ROLLBACK_SHA=$(git rev-parse HEAD)
echo "$(date): rollback_sha=$ROLLBACK_SHA" >> /tmp/openclaw-rollback.log

# 依赖回滚点
pip3 freeze > /tmp/pip-snapshot-$(date +%Y%m%d%H%M%S).txt

# 配置回滚点
cp ~/.zshrc ~/.zshrc.bak.$(date +%Y%m%d%H%M%S)
```

修复失败时回退：

```bash
# 代码回滚
git checkout $ROLLBACK_SHA
pkill -f memory_api_server || true && sleep 2
nohup python3 memory_api_server.py > /tmp/memory_api.log 2>&1 &

# 依赖回滚
LATEST_SNAPSHOT=$(ls -t /tmp/pip-snapshot-*.txt | head -1)
pip3 install -r $LATEST_SNAPSHOT

# 配置回滚
LATEST_BACKUP=$(ls -t ~/.zshrc.bak.* | head -1)
cp $LATEST_BACKUP ~/.zshrc && source ~/.zshrc
```

---

## 1. 你是谁、这是什么

你是 OpenClaw Agent。这个仓库是你的**长期记忆系统 + 认知引擎**，部署在宿主机（macOS）上，通过 HTTP API（端口 18900）与你通信。

系统由两大模块组成：

| 模块 | 目录 | 职责 |
|------|------|------|
| 记忆系统（冥思） | `meditation_memory/` | Neo4j 图谱存储、实体抽取、子图检索、冥思 9 步重整 |
| 认知引擎 | `cognitive_engine/` | 12 步认知管道、策略蒸馏/进化、RQS、信念系统、反馈闭环 |

它们通过 `memory_api_server.py`（FastAPI v2.4）统一对外提供 HTTP API。你通过 `index.ts` 注册的工具和钩子与之交互。

---

## 1. 前置依赖

在部署前，确认以下组件已就绪：

```bash
# 检查 Docker
docker --version

# 检查 Neo4j 容器
docker ps | grep neo4j
# 如果没有运行：
docker run -d --name reflection-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/reflection123 \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  -e NEO4J_server_memory_heap_initial__size=2g \
  -e NEO4J_server_memory_heap_max__size=4g \
  -e NEO4J_server_memory_pagecache_size=1g \
  -e NEO4J_dbms_memory_transaction_total_max=4g \
  -e NEO4J_db_memory_transaction_max=2g \
  neo4j:5.22-community

# 等待 30 秒后验证
curl -I http://localhost:7474
# 期望: HTTP/1.1 200 OK

# 检查 Python 依赖
python3 -c "import neo4j, fastapi, uvicorn, jieba, openai, requests; print('OK')"
# 如果缺少：
pip3 install neo4j fastapi uvicorn jieba openai requests pydantic httpx
```

---

## 2. 环境变量

以下环境变量必须设置。写入 `~/.zshrc` 确保持久化：

```bash
# Neo4j 连接
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="reflection123"
export NEO4J_DATABASE="neo4j"

# LLM API（用于实体抽取、策略蒸馏、冥思关系重构）
export OPENAI_API_KEY="你的API密钥"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"

# 冥思 LLM 模型（可选，默认 gpt-4.1-mini）
export MEDITATION_LLM_MODEL="qwen/qwen3-235b-a22b:free"

# 冥思批处理参数（可选）
export MEDITATION_BATCH_SIZE="50"
export MEDITATION_RELABEL_BATCH="100"

# 认知闭环开关（可选，默认 true）
export COGNITIVE_STRATEGY_ENABLED="true"
export COGNITIVE_FEEDBACK_ENABLED="true"

# Python 路径
export PYTHONPATH="$HOME/.openclaw/workspace/plugins/neo4j-memory"
```

---

## 3. 部署步骤

```bash
# 1. 进入插件目录
cd ~/.openclaw/workspace/plugins/neo4j-memory

# 2. 拉取最新代码
git remote add github https://github.com/Garylauchina/openclaw-neo4j-memory.git 2>/dev/null || true
git fetch github
git checkout main
git pull github main

# 3. 杀掉旧进程并启动 API 服务
pkill -f memory_api_server || true
sleep 2
nohup python3 memory_api_server.py > /tmp/memory_api.log 2>&1 &
sleep 5

# 4. 验证
curl http://127.0.0.1:18900/health
# 期望返回: {"status":"ok","neo4j_connected":true,"version":"2.4"}
```

### 开机自启（launchd）

```bash
cp deploy/com.openclaw.neo4j-memory.plist ~/Library/LaunchAgents/
# 如需修改环境变量，编辑 plist 文件中的 EnvironmentVariables 部分
launchctl load ~/Library/LaunchAgents/com.openclaw.neo4j-memory.plist

# 验证
launchctl list | grep com.openclaw.neo4j-memory
curl http://127.0.0.1:18900/health
```

---

## 4. 目录结构

```
openclaw-neo4j-memory/
├── memory_api_server.py          # FastAPI 服务入口（端口 18900，v2.4）
├── index.ts                      # OpenClaw 插件注册（工具 + 钩子 + 命令）
├── openclaw.plugin.json          # 插件元数据和配置项
├── package.json                  # npm 包配置
├── cognitive_hook.py             # 认知接管钩子（查询→推荐→反馈）
├── TOOLS.md                      # 工具和 API 详细使用说明
│
├── meditation_memory/            # 记忆系统核心
│   ├── config.py                 # Neo4j/LLM/子图配置（读环境变量）
│   ├── entity_extractor.py       # 实体和关系抽取（规则 + LLM，25 种关系类型）
│   ├── graph_store.py            # Neo4j 图操作（CRUD + 冥思 + 策略/RQS/信念）
│   ├── memory_system.py          # 记忆系统门面（ingest/retrieve/session）
│   ├── subgraph_context.py       # 动态子图构建
│   ├── meditation_worker.py      # 冥思 9 步流水线引擎
│   ├── meditation_scheduler.py   # 冥思调度器（cron + 条件触发）
│   └── meditation_config.py      # 冥思配置 + 策略蒸馏配置
│
├── cognitive_engine/             # 认知引擎
│   ├── cognitive_core.py         # 12 步认知管道主控
│   ├── neo4j_client.py           # Neo4j HTTP 客户端（带重试和降级）
│   ├── strategy_distiller.py     # 策略蒸馏器（因果链→策略，需要 LLM）
│   ├── rqs_system.py             # 推理质量评分系统
│   ├── adaptive_learning_system.py  # 自适应学习
│   ├── meta_learning_system.py      # 元学习
│   ├── self_correcting_reasoner.py  # 自校正推理
│   ├── learning_guard.py            # 学习守卫
│   ├── simple_semantic_parser.py    # 语义解析
│   └── adapters/                 # 适配器层
│       ├── memory_provider.py    # 记忆检索适配器（对接 /search）
│       ├── reality_writer.py     # 现实数据写入适配器（对接 /ingest）
│       ├── real_world_strategy.py   # 真实世界策略
│       ├── strong_validator.py      # 强验证器
│       ├── world_model_interface.py # 世界模型接口
│       ├── query_processor.py       # 查询处理器
│       ├── formatter.py            # 格式化器
│       └── fx_api.py               # 外汇 API 连接器
│
├── tests/                        # 认知引擎集成测试（共 211 个）
│   ├── test_phase1_integration.py  # 49 个 — 存储层对接
│   ├── test_phase2_strategy.py     # 44 个 — 策略持久化
│   ├── test_phase3_meditation.py   # 49 个 — 冥思升级
│   └── test_phase4_feedback.py     # 69 个 — 认知闭环
│
├── meditation_memory/tests/      # 记忆系统单元测试
│   ├── test_entity_extractor.py
│   ├── test_graph_store.py
│   ├── test_memory_system.py
│   ├── test_subgraph_context.py
│   └── test_integration.py
│
└── deploy/
    └── com.openclaw.neo4j-memory.plist  # macOS LaunchAgent 配置
```

---

## 5. HTTP API 速查

Base URL: `http://127.0.0.1:18900`

### 核心 API

| 方法 | 路径 | 用途 | 参数 |
|------|------|------|------|
| GET | `/health` | 健康检查 | — |
| POST | `/ingest` | 写入记忆 | `{"text": "...", "use_llm": true, "async_mode": false}` |
| POST | `/search` | 搜索记忆 + 策略推荐 | `{"query": "...", "include_strategies": true}` |
| GET | `/stats` | 图谱统计 | — |
| POST | `/feedback` | 提交执行反馈 | `{"query": "...", "applied_strategy_name": "...", "success": true, "confidence": 0.9, "validation_status": "accurate"}` |

### 冥思 API

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/meditation/config` | 查看冥思调度配置 |
| POST | `/meditation/schedule` | 修改冥思调度配置（立即生效） |
| POST | `/meditation/trigger` | 手动触发冥思。参数：`{"mode": "manual"}` |
| GET | `/meditation/status` | 查看冥思运行状态 |
| GET | `/meditation/history` | 查看冥思历史记录 |
| POST | `/meditation/dry-run` | 预览冥思（不修改数据） |

### 内部结构化写入 API

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/internal/strategy` | 写入/更新策略节点 |
| POST | `/internal/strategy/evolution` | 记录策略进化谱系 |
| POST | `/internal/strategy/archive` | 归档淘汰策略 |
| GET | `/internal/strategy/list` | 获取所有活跃策略 |
| POST | `/internal/rqs` | 写入/更新 RQS 记录 |
| GET | `/internal/rqs/list` | 获取所有 RQS 记录 |
| POST | `/internal/belief` | 写入/更新信念节点 |
| GET | `/internal/belief/list` | 获取所有信念 |

---

## 6. OpenClaw 工具和钩子

### 注册工具（通过 index.ts）

| 工具名 | 何时使用 |
|--------|----------|
| `neo4j_memory_store` | 对话中遇到重要信息时，主动保存到图谱 |
| `neo4j_memory_search` | 回答问题前，检索相关背景记忆 |
| `neo4j_memory_stats` | 用户询问记忆系统状态时 |
| `neo4j_cognitive_recommend` | 搜索记忆的同时获取策略推荐 |
| `neo4j_cognitive_feedback` | 查询处理完成后，提交执行结果反馈 |

### 自动钩子（无需手动调用）

| 钩子 | 触发时机 | 行为 |
|------|----------|------|
| `before_agent` | 每轮对话开始前 | 自动检索记忆上下文，注入系统提示词 |
| `agent_end` | 每轮对话结束后 | 自动将对话内容写入图谱 |
| `before_compaction` | 上下文压缩前 | 将完整会话归档到图谱 |

### /memory 命令

在对话中输入 `/memory` 可查看记忆系统状态。

---

## 7. 认知闭环工作流

这是你处理每个查询时应遵循的完整闭环流程：

```
用户提问
  ↓
[before_agent 钩子] 自动检索记忆上下文
  ↓
[neo4j_cognitive_recommend] 获取策略推荐，选择 fitness_score 最高的策略
  ↓
按策略处理查询，生成回答
  ↓
[neo4j_cognitive_feedback] 提交反馈：
  - success: true/false
  - confidence: 0-1
  - validation_status: accurate / acceptable / wrong
  ↓
系统自动更新（EMA 权重 0.1，防止单次反馈剧烈波动）：
  - 策略适应度 fitness_score
  - RQS 推理质量评分
  - 信念强度 belief_strength
  ↓
[冥思] 定期运行 9 步流水线：
  1. 快照 → 2. 剪枝 → 3. 实体合并 → 4. 关系重构
  → 5. 权重调整 → 6. 知识蒸馏 → 6.5 策略蒸馏（因果链→新策略）
  → 6.6 策略进化（交叉+变异+淘汰） → 7. 提交
  ↓
下次查询时，推荐的策略已经进化过了
```

---

## 8. 冥思机制详解

冥思是后台运行的图谱优化流水线，类似大脑睡眠时的记忆整理。

### 9 步流水线

| 步骤 | 名称 | 作用 |
|------|------|------|
| 1 | 快照 | 记录运行前的图谱状态基线 |
| 2 | 剪枝 | 归档低质量、孤立、过期的节点 |
| 3 | 实体合并 | 通过 LLM 判断并合并同义实体 |
| 4 | 关系重构 | 将 `related_to` 重标注为语义化类型（causes, uses, part_of 等） |
| 5 | 权重调整 | 基于语义评分、提及次数、连接度计算节点激活值 |
| 6 | 知识蒸馏 | 为高连接度实体生成元知识摘要节点 |
| 6.5 | 策略蒸馏 | 从因果链自动生成策略候选（需要 LLM） |
| 6.6 | 策略进化 | 交叉、变异、淘汰，优胜劣汰 |
| 7 | 提交 | 记录运行结果，清除冥思标记 |

### 触发方式

1. **定时触发**：默认每天凌晨 3:00（cron 表达式可配置）
2. **条件触发**：新增节点/关系超过阈值时自动触发
3. **手动触发**：`POST /meditation/trigger`

### 调度配置示例

```bash
# 修改为每天凌晨 4 点执行
curl -X POST http://127.0.0.1:18900/meditation/schedule \
  -H 'Content-Type: application/json' \
  -d '{"cron_schedule": "0 4 * * *"}'

# 降低触发阈值（让冥思更频繁）
curl -X POST http://127.0.0.1:18900/meditation/schedule \
  -H 'Content-Type: application/json' \
  -d '{"trigger_node_threshold": 50, "trigger_edge_threshold": 150}'

# 临时禁用冥思
curl -X POST http://127.0.0.1:18900/meditation/schedule \
  -H 'Content-Type: application/json' \
  -d '{"enabled": false}'
```

---

## 9. 策略蒸馏配置

策略蒸馏器通过 LLM 从因果链自动生成策略。配置参数：

| 参数 | 环境变量 | 默认值 | 说明 |
|------|----------|--------|------|
| min_causal_chain_length | — | 3 | 因果链最小长度（低于此值不蒸馏） |
| max_strategies_per_run | `MEDITATION_MAX_NEW_STRATEGIES` | 3 | 每次冥思最多生成的新策略数 |
| fitness_elimination_threshold | `MEDITATION_FITNESS_ELIMINATION` | 0.2 | 适应度低于此值的策略被淘汰 |
| crossover_rate | `MEDITATION_CROSSOVER_RATE` | 0.3 | 策略交叉概率 |

---

## 10. 故障排查

```bash
# === API 服务不响应 ===
curl http://127.0.0.1:18900/health
# 如果无响应：
ps aux | grep memory_api_server
pkill -f memory_api_server && sleep 2
cd ~/.openclaw/workspace/plugins/neo4j-memory
nohup python3 memory_api_server.py > /tmp/memory_api.log 2>&1 &
sleep 5
curl http://127.0.0.1:18900/health

# === Neo4j 连接失败 ===
docker ps | grep neo4j
# 如果容器没运行：
docker start reflection-neo4j
# 等待 15 秒后重试

# === Neo4j 认证限制（短时间内尝试太多次） ===
docker restart reflection-neo4j
# 等待 15 秒

# === 端口被占用 ===
lsof -i :18900
kill -9 <PID>

# === 查看错误日志 ===
tail -50 /tmp/memory_api.log
tail -50 ~/.openclaw/logs/neo4j-memory-stderr.log

# === 冥思 LLM 调用失败 ===
# 检查环境变量
echo $OPENAI_API_KEY
echo $OPENAI_BASE_URL
# 确认 API 可用：
python3 -c "
from openai import OpenAI
import os
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'], base_url=os.environ['OPENAI_BASE_URL'])
r = client.chat.completions.create(model='qwen/qwen3-235b-a22b:free', messages=[{'role':'user','content':'OK'}], max_tokens=5)
print(r.choices[0].message.content)
"

# === 运行测试验证系统完整性 ===
cd ~/.openclaw/workspace/plugins/neo4j-memory
python3 -m pytest tests/ -v --tb=short
```

---

## 11. 升级流程

当仓库有新版本时：

```bash
cd ~/.openclaw/workspace/plugins/neo4j-memory
git fetch github
git pull github main
pkill -f memory_api_server && sleep 2
nohup python3 memory_api_server.py > /tmp/memory_api.log 2>&1 &
sleep 5
curl http://127.0.0.1:18900/health
```

如果使用 launchd：

```bash
launchctl unload ~/Library/LaunchAgents/com.openclaw.neo4j-memory.plist
cd ~/.openclaw/workspace/plugins/neo4j-memory
git pull github main
cp deploy/com.openclaw.neo4j-memory.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.openclaw.neo4j-memory.plist
```

---

## 12. 关键约束（必读）

- `memory_api_server.py` **必须**在端口 **18900** 运行，`index.ts` 硬编码了这个地址
- Neo4j 密码是 **reflection123**，容器名是 **reflection-neo4j**
- 所有认知引擎功能在 Neo4j 不可用时**自动降级**，不会抛异常，不会影响你的正常对话
- 策略蒸馏需要 LLM API，没有配置 `OPENAI_API_KEY` 时蒸馏步骤会静默跳过
- 冥思的实体合并和关系重构也需要 LLM API
- 反馈更新使用 **EMA（指数移动平均）**，权重 0.1，单次反馈不会造成策略适应度剧烈波动
- `tests/` 目录共 **211 个测试**，可随时运行 `python3 -m pytest tests/ -v` 验证系统完整性
- 插件配置项在 `openclaw.plugin.json` 中定义，包括 `auto_ingest`、`auto_search`、`archive_on_compaction`、`use_llm_ingest`、`use_llm_search`
