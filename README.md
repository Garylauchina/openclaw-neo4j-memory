# OpenClaw Neo4j Graph Memory 插件自部署指南

本文档专为 OpenClaw Agent 编写。通过读取本指南，你可以实现自我部署，在一台全新的 macOS 机器上完整安装、配置并运行基于 Neo4j 的长期记忆系统插件。

## 1. 系统架构概述

这是一个 OpenClaw 插件，提供基于 Neo4j 知识图谱的长期记忆系统。包含两个主要组件：

1. **OpenClaw 插件前端**（`openclaw-neo4j-memory/`）：TypeScript 编写的 OpenClaw 插件，提供核心工具（`neo4j_memory_store`, `neo4j_memory_search`, `neo4j_memory_stats`）和 hooks（自动 ingest/search）。
2. **Python 后端 API 服务**（`merged-cognitive-system/`）：FastAPI 服务，运行在 `127.0.0.1:18900`，处理实体抽取、图谱存储、搜索以及异步图谱重整（冥思）机制。

---

## 2. 依赖与环境准备

在开始部署之前，你需要确保环境满足以下依赖：

### 2.1 系统与基础环境
- 操作系统：macOS
- Python 版本：Python 3.9+
- 容器引擎：Docker（用于运行 Neo4j）

### 2.2 环境变量要求
部署时需要配置以下环境变量。你可以将它们设置在 `launchd` 的 plist 文件中，或在终端会话中导出：

| 变量名 | 说明 | 默认值/推荐值 |
|--------|------|---------------|
| `NEO4J_URI` | Neo4j 数据库连接地址 | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j 用户名 | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j 密码 | `reflection123` |
| `NEO4J_DATABASE` | Neo4j 数据库名称 | `neo4j` |
| `OPENAI_API_KEY` | OpenAI 兼容的 API Key | （需提供） |
| `OPENAI_BASE_URL` | LLM API 地址 | （可选，如 `https://api.openai.com/v1`） |
| `MEDITATION_LLM_MODEL` | 冥思使用的 LLM 模型 | `deepseek/deepseek-chat` |
| `MEDITATION_BATCH_SIZE` | 冥思批处理大小 | `50` |
| `MEDITATION_RELABEL_BATCH`| 关系重构批处理大小 | `100` |

---

## 3. 详细部署步骤

请严格按照以下步骤在终端中执行命令，以完成完整的部署流程。

### 第一步：安装并启动 Neo4j 容器

我们需要启动一个配置了特定内存限制和插件的 Neo4j Docker 容器。

**执行命令：**
```bash
docker run -d \
  --name reflection-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/reflection123 \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  -e NEO4J_server_memory_heap_initial__size=2g \
  -e NEO4J_server_memory_heap_max__size=4g \
  -e NEO4J_server_memory_pagecache_size=1g \
  -e NEO4J_dbms_memory_transaction_total_max=4g \
  -e NEO4J_db_memory_transaction_max=2g \
  neo4j:5.22-community
```

**验证步骤：**
等待约 30 秒让数据库初始化，然后执行：
```bash
curl -I http://localhost:7474
```
如果返回 `HTTP/1.1 200 OK`，则说明 Neo4j 启动成功。

### 第二步：安装 Python 依赖

安装后端 API 服务所需的所有 Python 库。

**执行命令：**
```bash
pip3 install fastapi uvicorn "neo4j>=5.28" jieba openai pydantic httpx
```

**验证步骤：**
执行以下命令，如果没有报错则说明依赖安装成功：
```bash
python3 -c "import fastapi, uvicorn, neo4j, jieba, openai, pydantic, httpx; print('All dependencies installed successfully.')"
```

### 第三步：部署代码文件到 OpenClaw 插件目录

将仓库中的前后端代码复制到 OpenClaw 的插件工作目录 `~/.openclaw/workspace/plugins/neo4j-memory/`。

假设你当前在克隆的仓库根目录下，**执行命令：**
```bash
# 1. 创建目标目录
mkdir -p ~/.openclaw/workspace/plugins/neo4j-memory/

# 2. 复制 Python 后端代码（包含 API 服务和冥思模块）
cp -R merged-cognitive-system/* ~/.openclaw/workspace/plugins/neo4j-memory/

# 3. 复制 TypeScript 前端插件代码（覆盖或合并必要文件）
cp -R openclaw-neo4j-memory/* ~/.openclaw/workspace/plugins/neo4j-memory/
```

**验证步骤：**
检查目标目录中是否包含核心文件：
```bash
ls -l ~/.openclaw/workspace/plugins/neo4j-memory/memory_api_server.py
ls -l ~/.openclaw/workspace/plugins/neo4j-memory/openclaw.plugin.json
```

### 第四步：配置 launchd 并启动后台服务

使用 macOS 的 `launchd` 来管理 Python API 服务，确保它能自动启动和崩溃重启。

**执行命令：**
```bash
# 1. 创建日志目录
mkdir -p ~/.openclaw/logs/

# 2. 将 plist 文件复制到用户的 LaunchAgents 目录
cp ~/.openclaw/workspace/plugins/neo4j-memory/deploy/com.openclaw.neo4j-memory.plist ~/Library/LaunchAgents/

# 3. （可选）如果你需要修改 API Key 等环境变量，请使用文本编辑器修改 plist 文件：
# nano ~/Library/LaunchAgents/com.openclaw.neo4j-memory.plist

# 4. 加载并启动服务
launchctl load ~/Library/LaunchAgents/com.openclaw.neo4j-memory.plist
```

**验证步骤：**
1. 检查服务是否正在运行：
```bash
launchctl list | grep com.openclaw.neo4j-memory
```
2. 检查 API 服务的健康检查端点：
```bash
curl http://127.0.0.1:18900/health
```
如果返回 `{"status": "ok", ...}`，则说明 API 服务启动成功。

---

## 4. 冥思（Meditation）机制详解

冥思是一个后台运行的图谱优化流水线，类似大脑睡眠时的记忆整理过程。它包含 7 步流水线：
1. **快照**：记录运行前的图谱状态基线
2. **剪枝**：归档低质量、孤立、过期的节点
3. **实体合并**：通过 LLM 判断并合并同义实体
4. **关系重构**：将泛化的 `related_to` 关系重标注为语义化类型（如 causes, uses, part_of）
5. **权重调整**：基于语义评分、提及次数、连接度计算节点激活值
6. **知识蒸馏**：为高连接度实体生成元知识摘要节点
7. **提交**：记录运行结果，清除已处理节点的冥思标记

### 4.1 触发与调度配置

- **默认调度**：每天凌晨 3 点自动运行。
- **配置修改**：你可以通过 API 动态修改调度配置，修改后立即生效。
  ```bash
  curl -X POST http://127.0.0.1:18900/meditation/schedule \
    -H 'Content-Type: application/json' \
    -d '{"cron_schedule": "0 4 * * *", "trigger_node_threshold": 100}'
  ```

### 4.2 冥思 API 端点

你可以通过以下 HTTP API（Base URL: `http://127.0.0.1:18900`）管理冥思机制：

- `GET /meditation/config` - 查看当前冥思配置
- `POST /meditation/trigger` - 手动触发冥思（支持 `auto`, `manual`, `dry_run` 模式）
- `GET /meditation/status` - 查看冥思运行状态（`idle` 或 `running`）
- `GET /meditation/history` - 查看冥思运行历史记录
- `POST /meditation/dry-run` - 预览冥思效果，不实际修改数据

---

## 5. 故障排查指南

如果你在部署或运行中遇到问题，请参考以下指南：

### 5.1 服务未启动或连接拒绝
- **现象**：`curl http://127.0.0.1:18900/health` 报错。
- **排查**：
  1. 查看标准输出日志：`cat ~/.openclaw/logs/neo4j-memory-stdout.log`
  2. 查看错误日志：`cat ~/.openclaw/logs/neo4j-memory-stderr.log`
  3. 确认 Python 路径在 plist 中是否正确配置，且所需的依赖包均已安装。

### 5.2 Neo4j 数据库连接失败
- **现象**：健康检查返回 Neo4j 相关的错误。
- **排查**：
  1. 检查 Docker 容器状态：`docker ps -a | grep reflection-neo4j`
  2. 如果容器已退出，查看日志：`docker logs reflection-neo4j`
  3. 确认 plist 文件中的 `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` 与 Docker 启动参数一致。

### 5.3 冥思机制 LLM 调用失败
- **现象**：冥思状态一直处于 `idle`，或日志中提示超时/认证错误。
- **排查**：
  1. 检查 `~/Library/LaunchAgents/com.openclaw.neo4j-memory.plist` 中的 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL` 是否正确。
  2. 确认配置的模型（`MEDITATION_LLM_MODEL`）在目标 API 平台上可用。
  3. 修改配置后，记得执行 `launchctl unload` 和 `launchctl load` 重启服务。
