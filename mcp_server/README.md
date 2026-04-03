# OpenClaw Neo4j Memory MCP Server

这是一个轻量级的 Model Context Protocol (MCP) 封装层，将 OpenClaw 的记忆系统（`openclaw-neo4j-memory`）通过标准 MCP 接口暴露出来。

通过本服务，任何支持 MCP 的客户端（如 Claude Desktop、Cursor、Windsurf、Manus 等）都可以直接接入 OpenClaw 的长期记忆与认知引擎，实现跨会话的知识积累与策略自我进化。

## 1. 核心优势

与直接连接 Neo4j 数据库的常规 MCP Server 相比，本方案具有以下独特优势：

1. **认知增强**：不只是简单的 CRUD，所有写入的记忆都会经过系统的实体抽取和关系构建。
2. **策略闭环**：通过 `memory_feedback` 提交反馈，系统会自动调整策略的适应度（fitness_score）和推理质量评分（RQS）。
3. **后台冥思**：自动触发后台“冥思”流水线，对图谱进行知识蒸馏和策略进化。
4. **无缝共存**：可以与原有的 OpenClaw Agent 插件同时运行，共享同一个记忆图谱。

## 2. 前置条件

1. 确保你已经部署并运行了 `openclaw-neo4j-memory` 的核心 HTTP 服务（默认端口 `18900`）。
   - 验证命令：`curl http://127.0.0.1:18900/health`
2. 确保已安装 `uv` 包管理器或 Python 3.10+。

## 3. 暴露的 MCP Tools

本 Server 提供了 7 个核心工具：

| 工具名称 | 描述 |
|---------|------|
| `memory_ingest` | 将对话、事实、决策等写入图谱记忆 |
| `memory_search` | 检索与查询相关的记忆上下文 |
| `memory_search_with_strategy` | 检索记忆并获取认知引擎的策略推荐 |
| `memory_feedback` | 提交执行结果反馈，驱动策略自我进化 |
| `memory_stats` | 获取图谱与冥思系统的统计信息 |
| `meditation_trigger` | 手动触发冥思（记忆重整优化） |
| `meditation_status` | 查看冥思运行状态 |

## 4. 客户端配置指南

### Claude Desktop

在 Claude Desktop 的配置文件中（macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`，Windows: `%APPDATA%\Claude\claude_desktop_config.json`）添加以下内容：

```json
{
  "mcpServers": {
    "openclaw-memory": {
      "command": "uv",
      "args": [
        "run",
        "--with", "mcp",
        "--with", "httpx",
        "/绝对路径/到/openclaw-neo4j-memory/mcp_server/mcp_server.py"
      ],
      "env": {
        "MEMORY_API_URL": "http://127.0.0.1:18900",
        "MCP_REQUEST_TIMEOUT": "30"
      }
    }
  }
}
```

*注意：请将 `/绝对路径/到/...` 替换为你本地仓库的实际路径。*

### Cursor

在 Cursor 中，你可以通过 GUI 界面添加 MCP Server：
1. 打开 Cursor Settings > Features > MCP
2. 点击 "+ Add New MCP Server"
3. 选择 Type 为 `command`
4. Name 输入 `openclaw-memory`
5. Command 输入：
   ```bash
   uv run --with mcp --with httpx /绝对路径/到/openclaw-neo4j-memory/mcp_server/mcp_server.py
   ```

### Windsurf

在 Windsurf 中，编辑 `~/.windsurf/mcp_config.json` 文件，添加与 Claude Desktop 相同的配置块。

## 5. 推荐工作流

当在 MCP 客户端中使用本服务时，建议遵循以下工作流：

1. **获取上下文**：每次对话开始前，调用 `memory_search` 获取背景知识。
2. **寻求策略**：遇到复杂决策时，调用 `memory_search_with_strategy` 获取系统积累的经验策略。
3. **记录记忆**：对话结束后，调用 `memory_ingest` 保存重要事实或结论。
4. **提交反馈**：任务完成后，务必调用 `memory_feedback` 告知系统执行是否成功，以此驱动系统进化。

## 6. 故障排查

- **连接失败**：检查 `MEMORY_API_URL` 环境变量是否正确，以及后端的 `memory_api_server.py` 是否正在运行。
- **请求超时**：冥思过程可能较慢，如果频繁超时，可以适当增大 `MCP_REQUEST_TIMEOUT` 环境变量的值（默认 30 秒）。
- **工具未出现**：确保 `uv` 或 Python 环境正确安装了 `mcp` 和 `httpx` 依赖。
