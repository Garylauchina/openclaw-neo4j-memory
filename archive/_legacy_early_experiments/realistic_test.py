#!/usr/bin/env python3
"""
真实场景测试：用户反复提到相同话题
目标：验证在重复对话中系统能否学习
"""

import sys
sys.path.append('.')

print("🧪 真实场景测试：重复对话")
print("="*60)
print("模拟真实场景：用户反复提到'日本房产'和'AI'")
print("目标：验证系统能否提取重复模式并学习")
print("="*60)

from global_graph import GlobalGraph, NodeType, EdgeType
from active_subgraph import ActiveSubgraphEngine
from active_set import ActiveSetEngine, ActiveSet
from reflection_upgrade import ReflectionEngine
from learning_guard import LearningGuard
import time

# 创建测试环境
print("1. 创建测试环境...")
graph = GlobalGraph()

# 创建用户和固定话题
user_id = graph.create_node("用户", NodeType.USER)
topic1_id = graph.create_node("日本房产", NodeType.TOPIC)
topic2_id = graph.create_node("AI", NodeType.TOPIC)

print(f"   创建固定节点: 用户, 日本房产, AI")

# 创建Reflection引擎（低阈值）
print("\n2. 创建Reflection引擎...")
config = {
    "min_pattern_frequency": 2,  # 需要至少2次出现
    "min_pattern_weight": 0.1,
    "confidence_threshold": 0.3,
    "debug": True
}

reflection_engine = ReflectionEngine(graph, config)

# 创建Active Set引擎
active_set_engine = ActiveSetEngine(graph)

# 模拟重复对话
print("\n3. 模拟重复对话...")
conversation = [
    "我喜欢日本房产",      # 第1次提到
    "AI创业怎么做？",     # 第1次提到
    "日本房产回报率如何？", # 第2次提到日本房产
    "机器学习入门",        # 第2次提到AI相关
    "日本房产风险？",      # 第3次提到日本房产
    "深度学习与机器学习的区别", # 第3次提到AI
    "东京和大阪哪个更适合投资？", # 第4次提到日本房产
    "Python编程学习路线",  # 第4次提到AI相关
    "日本房产的税务问题",  # 第5次提到日本房产
    "神经网络基本原理"     # 第5次提到AI
]

print(f"   对话轮数: {len(conversation)}")
print(f"   话题重复: 日本房产(5次), AI相关(5次)")

# 运行对话
print("\n4. 运行对话并观察学习...")
all_diffs = []

for turn, query in enumerate(conversation):
    print(f"\n   第 {turn+1} 轮: {query}")
    
    # 语义解析（模拟）
    if "日本房产" in query:
        # 用户喜欢日本房产
        graph.update_edge(user_id, topic1_id, EdgeType.LIKES, 0.7)
        print(f"     添加边: 用户 -> LIKES -> 日本房产")
    elif "AI" in query or "机器学习" in query or "深度学习" in query or "Python" in query or "神经网络" in query:
        # 用户对AI感兴趣
        graph.update_edge(user_id, topic2_id, EdgeType.INTERESTED_IN, 0.6)
        print(f"     添加边: 用户 -> INTERESTED_IN -> AI")
    
    # 构建Active Set
    active_set = active_set_engine.build_active_set(query)
    
    # 运行Reflection
    diffs = reflection_engine.reflect(active_set)
    
    if diffs:
        print(f"     ✅ 生成 {len(diffs)} 个Diff")
        all_diffs.extend(diffs)
        
        # 显示Diff详情
        for diff in diffs[:2]:  # 只显示前2个
            if hasattr(diff, 'op'):
                print(f"       Diff: {diff.op.value}", end="")
                if hasattr(diff, 'src') and diff.src:
                    src_node = graph.nodes.get(diff.src)
                    dst_node = graph.nodes.get(diff.dst)
                    src_name = src_node.name if src_node else diff.src
                    dst_name = dst_node.name if dst_node else diff.dst
                    print(f" {src_name} -> {dst_name}", end="")
                if hasattr(diff, 'delta'):
                    print(f" (Δ={diff.delta:.2f})", end="")
                print()
    else:
        print(f"     ⚠️  无Diff生成")
    
    # 检查模式积累
    if hasattr(reflection_engine, 'patterns'):
        print(f"     累计模式数: {len(reflection_engine.patterns)}")

# 统计结果
print("\n5. 统计结果...")
print("-"*40)

graph_edges = len([e for e in graph.edges.values() if hasattr(e, 'active') and e.active])
patterns_count = len(reflection_engine.patterns) if hasattr(reflection_engine, 'patterns') else 0
diffs_generated = len(all_diffs)

print(f"   Graph边数: {graph_edges}")
print(f"   累计模式数: {patterns_count}")
print(f"   总Diff生成数: {diffs_generated}")

# 检查具体模式
print("\n6. 检查具体模式...")
print("-"*40)

if hasattr(reflection_engine, 'patterns') and reflection_engine.patterns:
    print(f"   发现的模式:")
    for pattern_key, pattern in list(reflection_engine.patterns.items())[:5]:  # 只显示前5个
        src_node = graph.nodes.get(pattern.src_node_id)
        dst_node = graph.nodes.get(pattern.dst_node_id)
        src_name = src_node.name if src_node else pattern.src_node_id
        dst_name = dst_node.name if dst_node else pattern.dst_node_id
        
        print(f"     {src_name} -> {dst_name} ({pattern.edge_type.value}):")
        print(f"       频率: {pattern.frequency}")
        print(f"       平均权重: {pattern.avg_weight:.3f}")
        print(f"       子图来源: {len(pattern.subgraph_ids)}个")
else:
    print("   ⚠️  未发现模式")

# 检查Reflection统计
print("\n7. Reflection统计...")
print("-"*40)

if hasattr(reflection_engine, 'stats'):
    stats = reflection_engine.stats
    print(f"   总反射次数: {stats.get('total_reflections', 0)}")
    print(f"   模式提取次数: {stats.get('patterns_extracted', 0)}")
    print(f"   Diff生成次数: {stats.get('diffs_generated', 0)}")
    print(f"   Diff应用次数: {stats.get('diffs_applied', 0)}")

# 系统是否学习的判断
print("\n8. 系统学习判断...")
print("-"*40)

learned = False
if patterns_count > 0 and diffs_generated > 0:
    learned = True

print(f"   🎯 系统是否学习: {'✅ 是！' if learned else '❌ 否'}")
print(f"   📊 学习证据:")
print(f"     1. 模式发现: {patterns_count} 个")
print(f"     2. 学习动作: {diffs_generated} 个Diff")
print(f"     3. 图更新: {graph_edges} 条边")

print("\n" + "="*60)
print("📊 测试总结")

if learned:
    print("✅ 系统在重复对话中成功学习！")
    print("✅ 能够提取重复模式")
    print("✅ 能够生成学习Diff")
    print("✅ 学习管道正常工作")
    
    print("\n💡 关键洞察:")
    print("   1. 重复是学习的关键")
    print("   2. 系统需要相同话题多次出现")
    print("   3. 模式提取需要频率≥2")
    
    print("\n🚀 真实场景验证:")
    print("   在真实对话中，用户会反复提到相同话题")
    print("   系统能够从重复中学习用户偏好")
    print("   学习管道已激活并正常工作")
else:
    print("❌ 系统未学习")
    print("   可能原因:")
    print("   1. 话题重复不够频繁")
    print("   2. 模式提取阈值过高")
    print("   3. 测试数据问题")

print(f"\n🕐 测试完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")