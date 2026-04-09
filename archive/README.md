# Archive - 历史档案

> 本目录存放早期探索阶段的代码和文档，作为项目进化历程的历史记录。

**创建时间：** 2026-04-09  
**目的：** 保留早期碎片想法，同时保持主仓库整洁

---

## 📚 档案分类

### 1. 早期实验 (_legacy_early_experiments)

**来源：** `_legacy/` 目录  
**时间：** 2026-03-25 ~ 2026-04-06  
**内容：** 30+ 早期代码文件，包括：
- active_subgraph.py - 激活子图（已整合到 subgraph_context.py）
- adaptive_learning_system.py - 自适应学习系统
- belief_layer.py - 信念层（事实/偏好/推断/时间性）
- cognitive_hook.py - 认知接管钩子（已整合）
- 等等...

**状态：** 大部分概念已整合到当前系统，保留作为历史参考。

### 2. 冥思记忆系统历史版本 (meditation-memory-system-historical)

**来源：** `meditation-memory-system/` 目录  
**时间：** 2026-03-25 ~ 2026-03-26  
**内容：** 独立的冥思记忆系统项目，包含：
- meditation_engine/ - 冥思引擎
- deployment/ - 部署配置（42 个子目录）
- adaptive_learning/ - 自适应学习
- belief_layer/ - 信念层
- rqs_system/ - RQS 系统
- 等等...

**状态：** 核心概念已整合到当前 Neo4j 记忆系统，但原项目过于复杂（42 个部署目录），保留作为历史参考。

### 3. 计划系统历史版本 (planning_system-historical)

**来源：** `planning_system/` 目录  
**时间：** 2026-03-26 ~ 2026-04-07  
**内容：** 计划系统 4 个模块：
- plan_aware_attention.py - 计划感知注意力
- plan_evaluator.py - 计划评估器
- plan_executor.py - 计划执行器
- plan_generator.py - 计划生成器

**状态：** 未整合到当前系统，但是高级认知功能，Phase 6 可能考虑整合。

### 4. 世界接口历史版本 (world_interface-historical)

**来源：** `world_interface/` 目录  
**时间：** 2026-03-26 ~ 2026-04-07  
**内容：** 世界接口和环境抽象层：
- environment.py - Environment 抽象层
- strategy_evolution.py - 策略进化
- closed_loop_system.py - 闭环系统
- exchange_rate_system.py - 汇率系统

**状态：** 部分概念（策略进化）已整合，通用环境抽象层未整合。

### 5. 混合记忆原型 (hybrid_memory_prototype-historical)

**来源：** `hybrid_memory_prototype/` 目录  
**时间：** 2026-03-20  
**内容：** 空的原型目录（src/, tests/, data/）

**状态：** 早期想法原型，后来演化为 Neo4j 图记忆系统。

### 6. 早期测试文件 (tests-early)

**来源：** 根目录的早期测试文件  
**时间：** 2026-04-07 ~ 2026-04-08  
**内容：**
- test_time_window.py
- test_time_window2.py
- test_time_factor.py
- simple_metacognition_test.py
- validate_metacognition_integration.py
- verify_p02_filter.py
- verify_p03_feedback.py
- p03_isolate_test.py

**状态：** 部分测试已过时，保留作为历史参考。

### 7. 愿景文档 (docs/vision/)

**来源：** `VISION.md`  
**时间：** 2026-04-08  
**内容：** Gary & Manus（小虾米）对话记录，包含：
- 记忆即能力（Memory Is the Real Capability）
- 三层记忆架构（Raw Data / Knowledge Graph / Metacognition）
- 元认知三定律
- Agent 经验分享与能力中心愿景

**状态：** 核心愿景仍然有效，部分已实现。

---

## 📝 使用说明

### 何时参考档案

1. **理解设计演进** - 了解当前系统是如何从早期想法演化而来
2. **避免重复探索** - 查看哪些想法被放弃及原因
3. **寻找灵感** - 早期可能有未整合但有价值的概念
4. **历史记录** - 记录项目进化历程

### 何时不参考档案

1. **学习当前系统** - 请阅读 `README.md` 和 `docs/` 目录
2. **贡献代码** - 请基于当前 `plugins/neo4j-memory/` 开发
3. **部署使用** - 请遵循当前部署文档

---

## 🎯 档案维护原则

1. **只增不减** - 档案一旦创建，不再删除
2. **添加说明** - 每个档案目录添加 README 说明背景
3. **标记状态** - 标明哪些概念已整合，哪些被放弃
4. **定期整理** - 每半年检查一次档案结构

---

## 📊 档案统计

| 档案 | 文件数 | 代码行数 | 创建日期 |
|------|--------|---------|----------|
| _legacy_early_experiments | 30+ | ~5000 | 2026-03-25 |
| meditation-memory-system-historical | 100+ | ~10000 | 2026-03-25 |
| planning_system-historical | 4 | ~2500 | 2026-03-26 |
| world_interface-historical | 10+ | ~5000 | 2026-03-26 |
| hybrid_memory_prototype-historical | 0 | 0 | 2026-03-20 |
| tests-early | 8 | ~1500 | 2026-04-07 |

**总计：** ~150 文件，~24000 行代码

---

**最后更新：** 2026-04-09  
**维护者：** OpenClaw Agent Team
