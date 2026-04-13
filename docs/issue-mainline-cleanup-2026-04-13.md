# Issue Draft: Clarify Mainline vs Experimental Surfaces

## Title

主线清理：收敛稳定运行路径，隔离 Issue #38 / #54 实验残留

## Background

最近仓库在根目录实现和 `plugins/neo4j-memory/` 镜像目录之间出现了功能漂移：

- 主线稳定修复已经落在两边：
  - 自动召回查询收缩，避免完整 prompt 递归回灌
  - `/search` 正确传递 `use_llm`
  - 子图上下文预算化裁剪
  - 冥思启动补跑后台化，重任务移到线程，避免阻塞 API
- 但插件镜像目录额外挂上了两类未定实验：
  - Issue #38 的扩展健康检查端点：`/diagnose`、`/ready`
  - Issue #54 的提示词熵接口：`/prompt-entropy/*`

这些能力目前没有进入稳定运行闭环，也没有被确认会长期维护。它们继续挂在主链镜像目录里，会制造两个问题：

1. 让“当前真正受支持的 API 面”变得模糊
2. 让根目录实现和插件镜像目录继续分叉，增加维护成本

## Decision

将主线定义为“OpenClaw 插件稳定运行所需的最小功能集”，优先保证：

- `ingest`
- `search`
- `stats`
- `meditation`
- 基础 `/health`

Issue #38 / #54 相关接口不再视为主线能力，不再保留在插件镜像主路径中。

## Scope

- 对齐 `plugins/neo4j-memory/memory_api_server.py` 到当前稳定主线
- 移除插件镜像中的扩展健康检查端点和提示词熵端点
- 保留已经验证有效的稳定性修复
- 文档中把这些能力明确标记为“实验记录”而不是“当前主线承诺”

## Non-Goals

- 现在不删除历史实验文档
- 现在不删除 `mcp_server.py` 或相关实现
- 现在不重写整体路线图，只先收敛主线边界

## Acceptance Criteria

- 根目录实现和插件镜像目录不再因为 Issue #38 / #54 产生主链分叉
- 运行路径清晰，排障时可以默认插件镜像代码代表稳定部署面
- 后续如果要恢复实验功能，必须以独立 issue / feature flag / 单独模块方式回归
