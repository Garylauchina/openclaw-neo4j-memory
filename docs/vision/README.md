# Vision Documents - 愿景文档

> 本目录存放项目的长期愿景和战略思考文档。

---

## 📚 内容概览

### VISION.md

**日期：** 2026-04-08  
**作者：** Gary & Manus（小虾米）  
**主题：** Agent Memory as Infrastructure for Intelligence Evolution

**核心洞察：**

1. **记忆即能力（Memory Is the Real Capability）**
   > "对于 LLM-based Agent，记忆=能力。LLM 提供通用推理能力，记忆提供将通用能力转化为领域专业知识的具体上下文。"

2. **三层记忆架构**
   | 层级 | 内容 | 存储 | 特点 |
   |------|------|------|------|
   | Raw Data | 源代码、对话日志、文档 | 文件系统、Git | 无限容量，高噪声 |
   | Knowledge Graph | 实体、关系、因果链 | Neo4j | 受控容量，结构化 |
   | Metacognition | 知识关于知识 | Neo4j (Meta 节点) | 最小容量，最高价值 |

3. **元认知三定律**
   - Law 1: 理解用户意图优先于执行用户指令
   - Law 2: 每次交互后反思自己的表现
   - Law 3: 承认能力边界，不确定时主动说明

4. **Agent 经验分享与能力中心**
   > "一个开放平台，Agent 可以分享经验图。任何积累了有价值领域经验的 Agent 都可以贡献其结构化经验到共享仓库。"

---

## 🎯 实现状态

### ✅ 已实现

1. **三层记忆架构** - Raw Data (文件系统) + Knowledge Graph (Neo4j) + Metacognition (Meta 节点)
2. **元认知三定律** - 已整合到 `meditation_memory/metacognition.py`
3. **冥思流水线** - 从 Knowledge Graph 到 Metacognition 的蒸馏

### 🚧 进行中

1. **Agent 经验分享平台** - MCP Server 规划中（Phase 6）

### 🔮 未来愿景

1. **通用图协议** - 用于 Agent 经验共享的标准协议
2. **跨 Agent 学习** - Agent 可以吸收其他 Agent 的经验子图

---

## 📝 使用建议

### 何时参考

- 理解项目长期愿景
- 规划 Phase 6+ 开发方向
- 了解核心设计原则

### 何时不参考

- 学习当前系统功能（请阅读 `README.md`）
- 部署使用（请遵循部署文档）
- 贡献代码（请阅读 `CONTRIBUTING.md`）

---

**目录创建日期：** 2026-04-09  
**维护者：** OpenClaw Agent Team
