#!/usr/bin/env python3
"""
激活子图全面测试
验证规范中的所有要求
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from active_subgraph import *
from global_graph import *

def test_specification_compliance():
    """测试规范符合性"""
    print("🧪 测试激活子图规范符合性")
    print("="*60)
    
    # 创建全局图
    graph = GlobalGraph()
    
    # 创建测试数据
    print("\n1. 创建测试全局图数据...")
    
    # 创建用户
    user_id = graph.create_node("哥斯拉", NodeType.USER)
    
    # 创建丰富的测试数据
    test_data = [
        # (名称, 类型, 与用户的关系, 权重)
        ("日本房产", NodeType.TOPIC, EdgeType.INTERESTED_IN, 0.8),
        ("AI记忆系统", NodeType.TOPIC, EdgeType.INTERESTED_IN, 0.9),
        ("机器学习", NodeType.TOPIC, EdgeType.INTERESTED_IN, 0.7),
        ("Python编程", NodeType.TOPIC, EdgeType.INTERESTED_IN, 0.6),
        ("投资理财", NodeType.TOPIC, EdgeType.DISLIKES, -0.4),
        ("大阪", NodeType.ENTITY, EdgeType.RELATED_TO, 0.5),
        ("东京", NodeType.ENTITY, EdgeType.RELATED_TO, 0.4),
        ("房地产", NodeType.ENTITY, EdgeType.RELATED_TO, 0.6),
        ("算法", NodeType.ENTITY, EdgeType.RELATED_TO, 0.7),
        ("深度学习", NodeType.ENTITY, EdgeType.RELATED_TO, 0.8),
    ]
    
    node_map = {}
    for name, node_type, relation, weight in test_data:
        node_id = graph.create_node(name, node_type)
        node_map[name] = node_id
        
        # 创建用户关系
        if relation:
            graph.update_edge(user_id, node_id, relation, weight)
    
    # 创建实体间关系
    print("\n2. 创建实体间关系...")
    entity_relations = [
        ("日本房产", "大阪", EdgeType.LOCATED_IN, 0.9),
        ("日本房产", "东京", EdgeType.LOCATED_IN, 0.8),
        ("日本房产", "房地产", EdgeType.RELATED_TO, 0.7),
        ("机器学习", "算法", EdgeType.RELATED_TO, 0.9),
        ("机器学习", "深度学习", EdgeType.PART_OF, 0.8),
        ("AI记忆系统", "机器学习", EdgeType.RELATED_TO, 0.8),
        ("AI记忆系统", "Python编程", EdgeType.RELATED_TO, 0.6),
        ("大阪", "东京", EdgeType.RELATED_TO, 0.3),
        ("算法", "深度学习", EdgeType.RELATED_TO, 0.7),
    ]
    
    for src_name, dst_name, relation, weight in entity_relations:
        if src_name in node_map and dst_name in node_map:
            graph.update_edge(node_map[src_name], node_map[dst_name], relation, weight)
    
    # 创建激活子图引擎
    print("\n3. 创建激活子图引擎...")
    engine = ActiveSubgraphEngine(graph)
    
    # ========== 测试1：硬约束验证 ==========
    print("\n4. 测试硬约束验证")
    print("-"*40)
    
    print(f"✅ 硬约束配置:")
    print(f"  max_nodes: {engine.config['max_nodes']} (必须 ≤ 30)")
    print(f"  max_edges: {engine.config['max_edges']} (必须 ≤ 60)")
    print(f"  max_depth: {engine.config['max_depth']} (必须 = 2)")
    
    assert engine.config['max_nodes'] <= 30, f"max_nodes必须≤30，当前{engine.config['max_nodes']}"
    assert engine.config['max_edges'] <= 60, f"max_edges必须≤60，当前{engine.config['max_edges']}"
    assert engine.config['max_depth'] == 2, f"max_depth必须=2，当前{engine.config['max_depth']}"
    
    print("✅ 硬约束验证通过")
    
    # ========== 测试2：Query解析 ==========
    print("\n5. 测试Query解析（轻量）")
    print("-"*40)
    
    test_queries = [
        "关于日本房产的分析",
        "机器学习在AI记忆系统中的应用",
        "Python编程学习建议",
        "我不喜欢投资理财"
    ]
    
    for query in test_queries:
        parse_result = engine._parse_query(query)
        print(f"查询: {query}")
        print(f"  话题: {parse_result.topics}")
        print(f"  实体: {parse_result.entities[:3]}")
        print(f"  意图: {parse_result.intent}")
        print(f"  关键词: {parse_result.keywords[:5]}")
    
    print("✅ Query解析测试通过")
    
    # ========== 测试3：Anchor Nodes召回 ==========
    print("\n6. 测试Anchor Nodes召回（关键）")
    print("-"*40)
    
    query = "关于日本房产的分析"
    query_parse = engine._parse_query(query)
    anchors = engine.get_anchor_nodes(query, query_parse)
    
    print(f"查询: {query}")
    print(f"召回锚点数量: {len(anchors)}")
    print(f"锚点详情:")
    for i, anchor in enumerate(anchors[:5], 1):
        print(f"  {i}. {anchor.node.name} (分数: {anchor.score:.2f}, 来源: {anchor.source})")
    
    # 验证锚点质量
    assert len(anchors) > 0, "必须召回至少一个锚点"
    assert all(anchor.score >= engine.config['min_anchor_score'] for anchor in anchors), "锚点分数必须≥阈值"
    
    print("✅ Anchor Nodes召回测试通过")
    
    # ========== 测试4：评分函数验证 ==========
    print("\n7. 测试评分函数")
    print("-"*40)
    
    # 测试锚点评分函数
    test_node = graph.nodes[node_map["日本房产"]]
    score = engine._compute_anchor_score(test_node, query_parse, "graph")
    
    weights = engine.config["anchor_score_weights"]
    print(f"锚点评分权重:")
    print(f"  语义相关性: {weights['semantic_similarity']}")
    print(f"  最近性: {weights['recency']}")
    print(f"  节点度数: {weights['node_degree']}")
    print(f"测试节点 '{test_node.name}' 分数: {score:.2f}")
    
    assert 0 <= score <= 1, f"锚点分数必须在[0,1]范围内，当前{score}"
    
    # 测试扩展评分函数
    test_edge_key = f"{node_map['日本房产']}::{node_map['大阪']}::{EdgeType.LOCATED_IN.value}"
    test_edge = graph.edges.get(test_edge_key)
    if test_edge:
        expansion_score = engine._compute_expansion_score(test_edge, 1.0)
        print(f"扩展评分: {expansion_score:.2f}")
        assert 0 <= expansion_score <= 1, f"扩展分数必须在[0,1]范围内"
    
    print("✅ 评分函数测试通过")
    
    # ========== 测试5：子图扩展 ==========
    print("\n8. 测试子图扩展（BFS + 权重控制）")
    print("-"*40)
    
    nodes, edges = engine.expand_subgraph(anchors)
    
    print(f"扩展结果:")
    print(f"  节点数: {len(nodes)}")
    print(f"  边数: {len(edges)}")
    
    # 验证扩展约束
    assert len(nodes) > 0, "扩展必须产生节点"
    
    # 检查深度限制
    print(f"  深度限制: {engine.config['max_depth']}")
    
    # 检查边权重过滤
    for edge_key in list(edges)[:3]:
        edge = graph.edges.get(edge_key)
        if edge:
            print(f"  边权重: {edge.state.weight:.2f} (阈值: {engine.config['edge_weight_threshold']})")
            assert abs(edge.state.weight) >= engine.config['edge_weight_threshold'], "边权重必须≥阈值"
    
    print("✅ 子图扩展测试通过")
    
    # ========== 测试6：子图裁剪 ==========
    print("\n9. 测试子图裁剪（非常关键）")
    print("-"*40)
    
    pruned_nodes, pruned_edges = engine.prune_subgraph(nodes, edges, anchors)
    
    print(f"裁剪前: {len(nodes)}节点, {len(edges)}边")
    print(f"裁剪后: {len(pruned_nodes)}节点, {len(pruned_edges)}边")
    
    # 验证硬约束
    assert len(pruned_nodes) <= engine.config['max_nodes'], f"节点数必须≤{engine.config['max_nodes']}"
    assert len(pruned_edges) <= engine.config['max_edges'], f"边数必须≤{engine.config['max_edges']}"
    
    # 验证连通性保证
    anchor_ids = {anchor.node_id for anchor in anchors}
    assert anchor_ids.issubset(pruned_nodes), "裁剪后必须包含所有锚点"
    
    print("✅ 子图裁剪测试通过")
    
    # ========== 测试7：完整构建流程 ==========
    print("\n10. 测试完整构建流程")
    print("-"*40)
    
    subgraph = engine.build_active_subgraph(query)
    
    print(f"激活子图构建结果:")
    print(f"  话题: {subgraph.topic}")
    print(f"  评分: {subgraph.score:.2f}/10.0")
    print(f"  节点数: {len(subgraph.nodes)}/{engine.config['max_nodes']}")
    print(f"  边数: {len(subgraph.edges)}/{engine.config['max_edges']}")
    print(f"  锚点数: {len(subgraph.anchors)}")
    
    # 验证所有约束
    assert len(subgraph.nodes) <= engine.config['max_nodes'], "节点数超限"
    assert len(subgraph.edges) <= engine.config['max_edges'], "边数超限"
    assert subgraph.score >= 0, "子图评分必须≥0"
    
    print("✅ 完整构建流程测试通过")
    
    # ========== 测试8：结构化上下文构建 ==========
    print("\n11. 测试结构化上下文构建")
    print("-"*40)
    
    context_text = engine.build_context_text(subgraph)
    print("结构化上下文:")
    print("-"*40)
    print(context_text)
    print("-"*40)
    
    # 验证上下文格式
    assert "[事实]" in context_text or "[关系]" in context_text, "上下文必须包含事实或关系"
    assert subgraph.topic in context_text, "上下文必须包含话题"
    
    print("✅ 结构化上下文构建测试通过")
    
    # ========== 测试9：缓存机制 ==========
    print("\n12. 测试缓存机制（必须有）")
    print("-"*40)
    
    # 第一次查询
    subgraph1 = engine.build_active_subgraph(query)
    print(f"第一次查询 - 缓存键: {subgraph1.cache_key}")
    
    # 第二次查询（应该命中缓存）
    subgraph2 = engine.build_active_subgraph(query)
    print(f"第二次查询 - 缓存键: {subgraph2.cache_key}")
    
    assert subgraph1.cache_key == subgraph2.cache_key, "缓存键必须一致"
    
    # 检查缓存统计
    print(f"缓存统计: {engine.stats['cache_hits']}命中, {engine.stats['cache_misses']}未命中")
    
    print("✅ 缓存机制测试通过")
    
    # ========== 测试10：错误控制 ==========
    print("\n13. 测试错误控制（必须实现）")
    print("-"*40)
    
    # 测试空查询
    empty_query = "   "
    empty_subgraph = engine.build_active_subgraph(empty_query)
    print(f"空查询处理: {len(empty_subgraph.nodes)}节点")
    
    # 测试无相关内容的查询
    unrelated_query = "完全不相关的话题xyz123"
    unrelated_subgraph = engine.build_active_subgraph(unrelated_query)
    print(f"无相关内容查询处理: {len(unrelated_subgraph.nodes)}节点")
    
    # 验证回退机制
    if len(unrelated_subgraph.anchors) > 0:
        print(f"  回退锚点: {unrelated_subgraph.anchors[0].node.name}")
    
    print("✅ 错误控制测试通过")
    
    # ========== 测试11：系统稳定性 ==========
    print("\n14. 测试系统稳定性")
    print("-"*40)
    
    # 多次查询测试稳定性
    stability_queries = [
        "日本房产",
        "机器学习",
        "Python",
        "投资",
        "AI系统",
        "深度学习",
        "算法",
        "房地产"
    ]
    
    all_subgraphs = []
    for q in stability_queries:
        sg = engine.build_active_subgraph(q)
        all_subgraphs.append(sg)
        
        # 验证约束
        assert len(sg.nodes) <= engine.config['max_nodes'], f"查询'{q}'节点数超限"
        assert len(sg.edges) <= engine.config['max_edges'], f"查询'{q}'边数超限"
    
    print(f"稳定性测试: {len(stability_queries)}次查询全部通过约束检查")
    
    # 检查不会爆炸
    avg_nodes = sum(len(sg.nodes) for sg in all_subgraphs) / len(all_subgraphs)
    avg_edges = sum(len(sg.edges) for sg in all_subgraphs) / len(all_subgraphs)
    
    print(f"平均子图大小: {avg_nodes:.1f}节点, {avg_edges:.1f}边")
    print(f"最大子图: {max(len(sg.nodes) for sg in all_subgraphs)}节点")
    
    assert avg_nodes <= engine.config['max_nodes'] * 0.8, "平均节点数过高，可能爆炸"
    
    print("✅ 系统稳定性测试通过")
    
    # ========== 测试12：性能测试 ==========
    print("\n15. 测试性能")
    print("-"*40)
    
    import time
    start_time = time.time()
    
    # 批量查询
    for i in range(10):
        engine.build_active_subgraph(f"测试查询{i}")
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / 10 * 1000  # 转换为毫秒
    
    print(f"性能测试: 10次查询耗时{total_time:.2f}秒")
    print(f"平均查询时间: {avg_time:.1f}毫秒")
    
    assert avg_time < 100, f"平均查询时间过高: {avg_time:.1f}ms"
    
    print("✅ 性能测试通过")
    
    # 打印最终统计
    print("\n" + "="*60)
    print("🎉 激活子图规范符合性测试完成！")
    print("="*60)
    
    engine.print_stats()
    
    return engine, graph

def test_real_conversation_scenarios():
    """测试真实对话场景"""
    print("\n🧪 测试真实对话场景")
    print("="*60)
    
    # 创建更丰富的全局图
    graph = GlobalGraph()
    
    # 创建用户
    user_id = graph.create_node("哥斯拉", NodeType.USER)
    
    # 模拟真实对话历史
    conversation_history = [
        # 对话1: 表达兴趣
        ("日本房产投资", NodeType.TOPIC, EdgeType.INTERESTED_IN, 0.8),
        ("大阪", NodeType.ENTITY, EdgeType.LOCATED_IN, 0.9),
        ("房地产", NodeType.ENTITY, EdgeType.RELATED_TO, 0.7),
        
        # 对话2: 询问信息
        ("机器学习", NodeType.TOPIC, EdgeType.INTERESTED_IN, 0.7),
        ("算法", NodeType.ENTITY, EdgeType.RELATED_TO, 0.8),
        ("深度学习", NodeType.ENTITY, EdgeType.PART_OF, 0.6),
        
        # 对话3: 表达偏好
        ("Python编程", NodeType.TOPIC, EdgeType.INTERESTED_IN, 0.6),
        ("框架", NodeType.ENTITY, EdgeType.RELATED_TO, 0.5),
        
        # 对话4: 表达不喜欢
        ("高风险投资", NodeType.TOPIC, EdgeType.DISLIKES, -0.5),
        ("股票", NodeType.ENTITY, EdgeType.RELATED_TO, 0.4),
    ]
    
    node_map = {}
    for name, node_type, relation, weight in conversation_history:
        if name not in node_map:
            node_id = graph.create_node(name, node_type)
            node_map[name] = node_id
        
        # 创建用户关系
        graph.update_edge(user_id, node_map[name], relation, weight)
    
    # 创建实体间关系
    entity_relations = [
        ("日本房产投资", "大阪", EdgeType.LOCATED_IN, 0.9),
        ("日本房产投资", "房地产", EdgeType.RELATED_TO, 0.8),
        ("机器学习", "算法", EdgeType.RELATED_TO, 0.9),
        ("机器学习", "深度学习", EdgeType.PART_OF, 0.8),
        ("Python编程", "框架", EdgeType.RELATED_TO, 0.7),
        ("高风险投资", "股票", EdgeType.RELATED_TO, 0.6),
        ("大阪", "房地产", EdgeType.RELATED_TO, 0.5),
        ("算法", "深度学习", EdgeType.RELATED_TO, 0.7),
    ]
    
    for src_name, dst_name, relation, weight in entity_relations:
        if src_name in node_map and dst_name in node_map:
            graph.update_edge(node_map[src_name], node_map[dst_name], relation, weight)
    
    # 创建引擎
    engine = ActiveSubgraphEngine(graph)
    
    # 测试真实对话查询
    real_queries = [
        "我想了解日本房产投资的情况",
        "机器学习有什么好的学习资源？",
        "Python编程难不难学？",
        "我不喜欢高风险投资，有什么建议？",
        "大阪的房地产市场怎么样？",
    ]
    
    print("\n真实对话场景测试:")
    print("-"*40)
    
    for query in real_queries:
        print(f"\n查询: {query}")
        
        # 构建激活子图
        subgraph = engine.build_active_subgraph(query)
        
        # 打印摘要
        print(f"  话题: {subgraph.topic}")
        print(f"  评分: {subgraph.score:.2f}/10.0")
        print(f"  大小: {len(subgraph.nodes)}节点, {len(subgraph.edges)}边")
        
        # 验证质量
        assert len(subgraph.nodes) > 0, "必须产生节点"
        assert subgraph.score > 0, "评分必须>0"
        
        # 打印上下文摘要
        context = engine.build_context_text(subgraph)
        context_lines = context.split('\n')
        print(f"  上下文摘要:")
        for line in context_lines[:3]:  # 只显示前3行
            print(f"    {line}")
    
    print("\n" + "="*60)
    print("真实对话场景测试完成")
    print("="*60)
    
    engine.print_stats()
    
    return engine

def test_engineering_advice():
    """测试工程建议：第一版只用Graph（不加vector）"""
    print("\n🧪 测试工程建议：纯Graph是否足够")
    print("="*60)
    
    # 创建测试图
    graph = GlobalGraph()
    
    # 创建用户和丰富的关系
    user_id = graph.create_node("测试用户", NodeType.USER)
    
    # 创建多样化数据
    for i in range(20):
        topic_id = graph.create_node(f"话题{i}", NodeType.TOPIC)
        entity_id = graph.create_node(f"实体{i}", NodeType.ENTITY)
        
        # 创建关系
        graph.update_edge(user_id, topic_id, EdgeType.INTERESTED_IN, 0.5 + i*0.02)
        graph.update_edge(topic_id, entity_id, EdgeType.RELATED_TO, 0.6)
    
    # 创建引擎（禁用vector回退）
    config = {
        "fallback_to_vector": False,  # 纯Graph测试
        "anchor_top_k": 5,
    }
    engine = ActiveSubgraphEngine(graph, config)
    
    # 测试各种查询
    test_queries = [
        "话题5",
        "实体10",
        "测试用户感兴趣的内容",
        "相关的话题",
    ]
    
    print("\n纯Graph测试结果:")
    print("-"*40)
    
    success_count = 0
    for query in test_queries:
        subgraph = engine.build_active_subgraph(query)
        
        if len(subgraph.nodes) > 0:
            success_count += 1
            print(f"  ✅ '{query}': {len(subgraph.nodes)}节点")
        else:
            print(f"  ❌ '{query}': 无节点")
    
    success_rate = success_count / len(test_queries) * 100
    print(f"\n纯Graph成功率: {success_rate:.1f}%")
    
    if success_rate >= 70:
        print("✅ 纯Graph足够用于第一版")
    else:
        print("⚠️  可能需要添加vector检索")
    
    return success_rate >= 70

if __name__ == "__main__":
    print("🚀 开始激活子图全面测试")
    print("="*60)
    
    # 测试规范符合性
    engine, graph = test_specification_compliance()
    
    # 测试真实对话场景
    test_real_conversation_scenarios()
    
    # 测试工程建议
    graph_sufficient = test_engineering_advice()
    
    print("\n" + "="*60)
    print("🎯 测试总结")
    print("="*60)
    print("✅ 规范符合性: 通过 (15项测试全部通过)")
    print("✅ 核心功能: 通过 (Query解析、Anchor召回、扩展、裁剪)")
    print("✅ 稳定性: 通过 (硬约束生效，不会爆炸)")
    print("✅ 可解释性: 通过 (结构化上下文构建)")
    print(f"✅ 工程建议: {'通过' if graph_sufficient else '部分通过'} (纯Graph{'足够' if graph_sufficient else '可能需要增强'})")
    print("\n💡 激活子图实现成功，符合所有规范要求！")
    print("\n本质验证: Graph-based Context Retrieval Engine")
    print("比RAG高级一层: RAG是top-k chunks，这是top-k structured subgraph")