# 冥思进化机制 — 伪代码设计

## 核心思想

冥思不再用固定规则整理记忆，而是根据"记忆被使用的效果反馈"来动态调整整理策略。每次冥思都比上次更聪明。

---

## 数据流

```
用户对话 → auto_ingest(写入记忆) → 图谱
                                      ↓
用户提问 → auto_search(检索记忆) → 返回结果 → agent使用
                                                  ↓
                                            feedback(好/坏)
                                                  ↓
                                          feedback_log(积累)
                                                  ↓
                                    定时冥思 ← 读取feedback → 调整策略 → 整理图谱
                                                  ↓
                                          冥思日志(记录本次效果)
                                                  ↓
                                        下次冥思读取上次日志 → 继续进化
```

---

## 伪代码

### 1. 冥思主入口（改造现有 meditation 流程）

```python
def run_meditation():
    # ===== 第一步：感知 — 了解当前状态 =====
    graph_stats = get_graph_stats()          # 节点数、关系数、通用关系比例
    recent_feedbacks = get_recent_feedbacks() # 最近N天的feedback记录
    last_meditation_log = get_last_meditation_log()  # 上次冥思的效果记录
    
    # ===== 第二步：反思 — 分析feedback信号 =====
    signals = analyze_feedback_signals(recent_feedbacks)
    # signals 结构:
    # {
    #   "empty_queries": ["MCP Server", "认知闭环", ...],     # 搜了但返回空的查询
    #   "noisy_queries": ["OpenClaw模型配置", ...],           # 搜了但feedback=负面的查询
    #   "useful_entities": ["OpenClaw", "冥思", ...],         # 出现在正面feedback中的实体
    #   "useless_entities": ["弹道导弹目标", "人道主义状况"],  # 出现在负面feedback中的实体
    #   "hot_topics": ["模型配置", "记忆系统"],               # 高频查询的话题
    #   "cold_topics": ["比特币价格"],                        # 长期未被查询的话题
    #   "overall_satisfaction": 0.35,                         # 总体满意度 (0-1)
    # }
    
    # ===== 第三步：决策 — 根据信号调整冥思参数 =====
    params = adjust_meditation_params(signals, last_meditation_log)
    # params 结构:
    # {
    #   "merge_threshold": 0.7,        # 实体合并的相似度阈值 (低=激进合并, 高=保守)
    #   "compression_level": "light",  # 压缩程度: light/medium/aggressive
    #   "max_meta_fanout": 15,         # META节点最大关系扇出度
    #   "cleanup_targets": [...],      # 本次要清理的垃圾实体列表
    #   "protect_topics": [...],       # 本次要保护(不压缩)的话题
    #   "split_candidates": [...],     # 需要拆分的超级节点
    # }
    
    # ===== 第四步：执行 — 用调整后的参数做冥思 =====
    result = execute_meditation(params)
    # result: 本次冥思做了什么、合并了多少、清理了多少、拆分了多少
    
    # ===== 第五步：记录 — 保存本次冥思日志供下次参考 =====
    save_meditation_log({
        "timestamp": now(),
        "input_signals": signals,
        "params_used": params,
        "actions_taken": result,
        "graph_stats_before": graph_stats,
        "graph_stats_after": get_graph_stats(),
    })
```

### 2. 分析反馈信号

```python
def analyze_feedback_signals(feedbacks):
    empty_queries = []
    noisy_queries = []
    useful_entities = Counter()
    useless_entities = Counter()
    topic_frequency = Counter()
    
    for fb in feedbacks:
        topic_frequency[fb.query] += 1
        
        if fb.result_count == 0:
            # 搜了但什么都没找到 → 记忆缺失
            empty_queries.append(fb.query)
            
        elif fb.success == False:
            # 搜到了但用户说没用 → 噪音问题
            noisy_queries.append(fb.query)
            for entity in fb.returned_entities:
                useless_entities[entity] += 1
                
        elif fb.success == True:
            # 搜到了且有用 → 正向信号
            for entity in fb.returned_entities:
                useful_entities[entity] += 1
    
    # 识别热门和冷门话题
    hot_topics = [t for t, count in topic_frequency.most_common(10)]
    all_topics = get_all_topic_entities()
    cold_topics = [t for t in all_topics 
                   if t not in topic_frequency 
                   and t.last_accessed > 30_days_ago]
    
    return {
        "empty_queries": empty_queries,
        "noisy_queries": noisy_queries,
        "useful_entities": dict(useful_entities),
        "useless_entities": dict(useless_entities),
        "hot_topics": hot_topics,
        "cold_topics": cold_topics,
        "overall_satisfaction": len([f for f in feedbacks if f.success]) / max(len(feedbacks), 1),
    }
```

### 3. 动态调整冥思参数

```python
def adjust_meditation_params(signals, last_log):
    params = get_default_params()
    
    # --- 规则1: 满意度低 → 保守整理，少压缩 ---
    if signals["overall_satisfaction"] < 0.5:
        params["compression_level"] = "light"
        params["merge_threshold"] = 0.85  # 只合并非常相似的实体
    
    # --- 规则2: 空查询多 → 说明记忆写入不足或被过度压缩 ---
    if len(signals["empty_queries"]) > 3:
        params["compression_level"] = "light"  # 减少压缩，保留更多细节
        params["protect_topics"] = signals["empty_queries"]  # 保护这些话题的实体
    
    # --- 规则3: 噪音查询多 → 需要清理无用实体和泛化关系 ---
    if len(signals["noisy_queries"]) > 3:
        # 找出经常出现在负面feedback中、但从不出现在正面feedback中的实体
        pure_noise = [e for e in signals["useless_entities"] 
                      if e not in signals["useful_entities"]]
        params["cleanup_targets"] = pure_noise
    
    # --- 规则4: 热门话题 → 保护其实体，不要合并或压缩 ---
    params["protect_topics"].extend(signals["hot_topics"])
    
    # --- 规则5: 冷门话题 → 可以更激进地压缩 ---
    # (不删除，只是压缩成更精炼的META节点)
    
    # --- 规则6: 检查上次冥思的效果 ---
    if last_log:
        before = last_log["graph_stats_before"]["generic_relations_ratio"]
        after = last_log["graph_stats_after"]["generic_relations_ratio"]
        if after >= before:
            # 上次冥思没有降低通用关系比例 → 这次更激进地处理
            params["max_meta_fanout"] = max(params["max_meta_fanout"] - 5, 5)
    
    # --- 规则7: META超级节点检测 ---
    super_nodes = find_nodes_with_fanout_above(params["max_meta_fanout"])
    params["split_candidates"] = super_nodes
    
    return params
```

### 4. 执行冥思（改造现有逻辑）

```python
def execute_meditation(params):
    result = {"merged": 0, "cleaned": 0, "split": 0, "compressed": 0}
    
    # --- 清理垃圾实体 ---
    for entity_name in params["cleanup_targets"]:
        if entity_name not in params["protect_topics"]:
            # 不直接删除，而是降低权重/mention_count
            # 让它在后续搜索中排名更低
            decrease_entity_weight(entity_name)
            result["cleaned"] += 1
    
    # --- 合并相似实体（用调整后的阈值）---
    candidates = find_merge_candidates(threshold=params["merge_threshold"])
    for entity_a, entity_b, similarity in candidates:
        if entity_a not in params["protect_topics"]:
            merge_entities(entity_a, entity_b)
            result["merged"] += 1
    
    # --- 拆分超级节点 ---
    for node in params["split_candidates"]:
        # 按关系类型或话题聚类，拆成多个更具体的META节点
        split_super_node(node, max_fanout=params["max_meta_fanout"])
        result["split"] += 1
    
    # --- 清理截断的实体名（新增）---
    broken_entities = find_truncated_entities()  # 名字<4个字符的中文concept
    for entity in broken_entities:
        if entity.mention_count <= 1 and entity not in params["protect_topics"]:
            # 只出现过一次的截断实体，大概率是垃圾
            remove_entity(entity)
            result["cleaned"] += 1
        else:
            # 多次出现的截断实体，尝试通过上下文还原完整名称
            full_name = infer_full_name_from_context(entity)
            if full_name:
                rename_entity(entity, full_name)
                result["merged"] += 1
    
    # --- 压缩冷门话题（根据compression_level）---
    if params["compression_level"] != "light":
        cold_entities = get_cold_topic_entities()
        for entity in cold_entities:
            if entity not in params["protect_topics"]:
                compress_to_meta(entity)
                result["compressed"] += 1
    
    return result
```

### 5. Feedback 数据结构（需要扩展现有 /feedback 接口）

```python
# 现有的 feedback 已经有:
{
    "query": "OpenClaw记忆系统",
    "applied_strategy_name": "phase2_test_strategy",
    "success": true,
    "confidence": 0.9,
    "validation_status": "accurate"
}

# 需要扩展的字段:
{
    "query": "OpenClaw记忆系统",
    "success": true,
    "confidence": 0.9,
    "result_count": 30,                    # 新增：返回了多少条结果
    "returned_entities": ["OpenClaw", "模型", "IronClaw"],  # 新增：返回了哪些实体
    "useful_entities": ["OpenClaw"],        # 新增：哪些实体真正有用
    "noise_entities": ["比特币生态", "弹道导弹目标"],  # 新增：哪些是噪音
}
```

---

## 进化效果预期

```
第1周: 满意度 0.35 → 冥思保守整理，清理明显垃圾，保护热门话题
第2周: 满意度 0.45 → 噪音减少，开始拆分超级节点
第3周: 满意度 0.55 → 截断实体大幅减少，通用关系比例下降
第4周: 满意度 0.65 → 口语化查询开始有返回（因为实体名更完整了）
第2月: 满意度 0.75 → 冥思策略趋于稳定，记忆质量持续缓慢提升
```

每次冥思都会记录日志，下次冥思读取上次日志，形成闭环。不需要人工干预，系统自己会越来越好。

---

## 实现建议

1. **不要大改现有代码**，在现有 meditation 流程的入口处加一个 `analyze_and_adjust()` 步骤即可
2. **扩展 /feedback 接口**，增加 `returned_entities` 和 `noise_entities` 字段
3. **新增一个 meditation_log 表/节点**，存储每次冥思的参数和效果
4. **渐进式上线**：先只做"清理截断实体"和"拆分超级节点"，观察效果后再加更多规则
