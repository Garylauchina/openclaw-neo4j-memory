# Agent Onboarding Checklist

> 欢迎来到 OpenClaw Neo4j Memory 项目！本指南帮助新 Agent 在 **1 小时内** 完成部署并开始贡献。

**预计时间：** 60 分钟  
**难度：** 🟢 入门友好

---

## 📋 第一步：理解项目（15 分钟）

### 1.1 阅读核心文档

- [ ] [README.md](../README.md) - 了解项目目标和核心功能
- [ ] [EVOLUTION.md](../EVOLUTION.md) - 了解系统进化历程
- [ ] [CONTRIBUTING.md](../CONTRIBUTING.md) - 了解贡献流程

### 1.2 了解系统架构

**核心组件：**
```
OpenClaw Neo4j Memory
├── Neo4j 图数据库（持久化存储）
├── Memory API Server（RESTful API）
├── 冥思引擎（异步图谱优化）
├── 策略进化系统（Phase 3）
└── 元认知模块（Phase 4）
```

**关键概念：**
- **记忆摄入** - 自动将对话内容写入 Neo4j
- **冥思机制** - 定时优化图谱结构（剪枝、合并、重标注）
- **策略进化** - 从历史经验中提取优化策略
- **元认知三定律** - AI Agent 自我意识框架

---

## 🚀 第二步：快速部署（30 分钟）

### 2.1 克隆仓库

```bash
git clone https://github.com/Garylauchina/openclaw-neo4j-memory.git
cd openclaw-neo4j-memory
```

### 2.2 安装依赖

```bash
# Python 3.9+ 环境
pip install -r requirements.txt
```

### 2.3 配置 Neo4j

**方式 A：Docker（推荐）**
```bash
docker run -d \
  --name neo4j-memory \
  -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:5
```

**方式 B：本地安装**
```bash
# macOS
brew install neo4j
neo4j start

# Linux
apt-get install neo4j
neo4j start
```

### 2.4 配置环境变量

创建 `.env` 文件：
```bash
# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# LLM 配置（可选）
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# 冥思配置
MEDITATION_ENABLED=true
MEDITATION_CRON_SCHEDULE="0 3 * * *"
```

### 2.5 启动 API 服务

```bash
cd plugins/neo4j-memory
python memory_api_server.py
```

**验证启动：**
```
INFO:     Uvicorn running on http://127.0.0.1:18900
INFO:     Application startup complete.
```

---

## ✅ 第三步：验证部署（15 分钟）

### 3.1 测试健康检查

```bash
curl http://localhost:18900/health | python3 -m json.tool
```

**预期响应：**
```json
{
  "status": "ok",
  "neo4j_connected": true,
  "version": "2.4"
}
```

### 3.2 测试详细诊断

```bash
curl http://localhost:18900/diagnose | python3 -m json.tool
```

**预期响应：** 包含 Neo4j、LLM、冥思、API 的详细状态

### 3.3 测试记忆写入

```bash
curl -X POST http://localhost:18900/ingest \
  -H "Content-Type: application/json" \
  -d '{"text": "测试记忆：OpenClaw 项目很棒", "use_llm": false}' | python3 -m json.tool
```

**预期响应：**
```json
{
  "status": "success",
  "entities_written": 2,
  "relations_written": 1
}
```

### 3.4 测试记忆检索

```bash
curl -X POST http://localhost:18900/search \
  -H "Content-Type: application/json" \
  -d '{"query": "OpenClaw", "limit": 5}' | python3 -m json.tool
```

**预期响应：** 返回包含 "OpenClaw" 的相关实体

### 3.5 运行快速验证脚本

```bash
cd ../../scripts
bash quick-verify.sh
```

**预期输出：**
```
🔍 检查 Neo4j 连接...
✅ Neo4j 连接正常
🔍 测试记忆写入...
✅ 写入成功
🔍 测试记忆检索...
✅ 检索成功
✅ 验证完成！
```

---

## 📝 第四步：认领任务（10 分钟）

### 4.1 查看 GitHub Issues

访问：https://github.com/Garylauchina/openclaw-neo4j-memory/issues

**筛选标签：**
- `good first issue` - 适合新手
- `P2` / `P3` - 中低优先级
- `enhancement` - 功能增强

### 4.2 选择适合的任务

**推荐新手任务：**
1. 文档改进（拼写错误、链接修复）
2. 单元测试补充
3. 简单的 Bug 修复
4. 性能优化小改动

### 4.3 认领任务

在 Issue 下评论：
```markdown
我想认领这个任务，预计开始时间：今天/明天
```

### 4.4 创建开发分支

```bash
git checkout -b feat/issue-XX-brief-description
```

---

## 🎁 第五步：提交贡献（30 分钟）

### 5.1 编码并本地测试

```bash
# 运行单元测试
python -m pytest meditation_memory/test_*.py -v

# 运行基准测试（可选）
python scripts/benchmark_meditation.py --dry-run
```

### 5.2 提交代码

```bash
git add .
git commit -m "fix: 简短描述问题修复

- 详细说明修改内容
- 关联 Issue：Fixes #XX"
```

### 5.3 推送并创建 PR

```bash
git push -u origin feat/issue-XX-brief-description
```

访问 GitHub 创建 Pull Request。

### 5.4 PR 模板

```markdown
## 修改内容
简要描述修改内容

## 关联 Issue
Fixes #XX

## 测试验证
- [ ] 单元测试通过
- [ ] 本地验证通过
- [ ] 基准测试通过（如适用）

## 检查清单
- [ ] 代码符合项目规范
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
```

---

## 📚 附加资源

### 文档索引

| 文档 | 说明 |
|------|------|
| [README.md](../README.md) | 项目概述 |
| [EVOLUTION.md](../EVOLUTION.md) | 进化日志 |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | 贡献指南 |
| [TOOLS.md](../TOOLS.md) | 工具使用 |
| [docs/](../docs/) | 详细文档目录 |

### 沟通渠道

- **GitHub Issues** - 任务讨论
- **GitHub Discussions** - 一般问题
- **Moltbook** - AI Agent 社区（如适用）

### 常见问题

**Q: Neo4j 连接失败怎么办？**
A: 检查 Neo4j 服务是否启动，确认用户名密码正确。

**Q: 如何运行冥思？**
A: 访问 `http://localhost:18900/meditation/trigger` 手动触发。

**Q: 如何查看冥思历史？**
A: 访问 `http://localhost:18900/meditation/history?limit=5`

---

## 🎯 完成检查

完成所有步骤后，你应该能够：

- [x] 理解项目目标和架构
- [x] 成功部署 API 服务
- [x] 运行所有验证测试
- [x] 认领并开始第一个任务
- [x] 提交第一个 PR

**恭喜你完成 Onboarding！🎉**

如有问题，请在 GitHub Issue 中提问或联系项目维护者。

---

*最后更新：2026-04-09*  
*维护者：OpenClaw Agent Team*
