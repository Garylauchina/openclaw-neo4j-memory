# _legacy_early_experiments - 早期实验代码

**时间：** 2026-03-25 ~ 2026-04-06  
**文件数：** 30+  
**代码行数：** ~5000 行

---

## 📚 内容概览

本目录包含项目早期（2026-03-25 至 2026-04-06）的实验代码，记录了从概念探索到系统整合的历程。

### 核心文件

| 文件 | 核心想法 | 现状 |
|------|---------|------|
| `active_subgraph.py` | 激活子图（从 Global Graph 选择 + 压缩） | ✅ 已整合到 `subgraph_context.py` |
| `adaptive_learning_system.py` | 自适应学习（冷启动→稳定切换） | ⚠️ 部分整合 |
| `belief_layer.py` | 信念层（FACT/PREFERENCE/INFERENCE/TEMPORAL） | ⚠️ 部分整合 |
| `cognitive_hook.py` | 认知接管钩子（OpenClaw 插件桥接） | ✅ 已整合 |
| `activate_strategy_system.py` | 策略系统激活（强制使用策略） | ⚠️ 待评估 |
| `rqs_system/` | RQS（检索质量评分）系统 | ✅ 已整合到 cognitive_engine |
| `meta_learning/` | 元学习模块 | ✅ 已整合到 meditation_evolution |

### 其他文件

- `evaluation_framework.py` - 评估框架
- `consolidate_evolution.py` - 进化整合
- `consolidate_elimination_cycles.py` - 消除周期整合
- `final_verification.py` - 最终验证
- 等等...

---

## 🎯 整合状态

### ✅ 已整合概念

1. **激活子图** - 现在的 `subgraph_context.py`
2. **认知接管钩子** - 现在的 `cognitive_engine/cognitive_hook.py`
3. **RQS 系统** - 现在的 `cognitive_engine/retrieval_quality_scorer.py`
4. **元学习** - 现在的 `meditation_memory/meditation_evolution.py`

### ⚠️ 部分整合概念

1. **信念层** - 部分概念整合到元认知模块，但完整的 FACT/PREFERENCE/INFERENCE/TEMPORAL 分类未整合
2. **自适应学习** - 冷启动/稳定切换概念部分整合

### 🔴 未整合概念

1. **策略系统激活器** - 强制使用策略的机制未整合
2. **部分评估框架** - 过于复杂，当前系统使用更简洁的测试

---

## 💡 历史价值

1. **设计演进记录** - 展示了系统如何从碎片想法演化为统一架构
2. **避免重复探索** - 记录了哪些想法被尝试过及放弃原因
3. **灵感来源** - 部分未整合概念可能在未来阶段有价值

---

## 📝 使用建议

### 何时参考

- 理解当前系统的设计演进
- 寻找未整合但有价值的概念
- 了解哪些想法被放弃及原因

### 何时不参考

- 学习当前系统（请阅读 `README.md` 和 `docs/`）
- 贡献代码（请基于 `plugins/neo4j-memory/`）
- 部署使用（请遵循当前部署文档）

---

**归档日期：** 2026-04-09  
**维护者：** OpenClaw Agent Team
