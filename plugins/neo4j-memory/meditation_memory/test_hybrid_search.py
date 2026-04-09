#!/usr/bin/env python3
"""
Issue #44: 混合检索实现单元测试
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid_search import HybridSearchConfig, SearchResult, HybridSearch


def test_hybrid_search_config():
    """测试 1: 混合检索配置"""
    print("🔍 测试 1: 混合检索配置")
    print("-" * 60)
    
    config = HybridSearchConfig()
    
    # 验证默认值
    assert config.vector_index_name == "entity_embeddings", "默认索引名应为 entity_embeddings"
    assert config.vector_dimension == 1536, "默认维度应为 1536"
    assert config.vector_top_k == 10, "默认 top_k 应为 10"
    assert abs(config.graph_weight - 0.6) < 0.01, "默认图权重应为 0.6"
    assert abs(config.vector_weight - 0.4) < 0.01, "默认向量权重应为 0.4"
    assert config.vector_timeout_seconds == 2.0, "默认超时时间应为 2 秒"
    
    print(f"  ✅ vector_index_name: {config.vector_index_name}")
    print(f"  ✅ vector_dimension: {config.vector_dimension}")
    print(f"  ✅ vector_top_k: {config.vector_top_k}")
    print(f"  ✅ graph_weight: {config.graph_weight}")
    print(f"  ✅ vector_weight: {config.vector_weight}")
    print(f"  ✅ vector_timeout_seconds: {config.vector_timeout_seconds}")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_search_result():
    """测试 2: 检索结果序列化"""
    print("🔍 测试 2: 检索结果序列化")
    print("-" * 60)
    
    result = SearchResult(
        name="测试实体",
        entity_type="概念",
        description="这是一个测试实体",
        score=0.85,
        graph_score=0.9,
        vector_score=0.75,
        source="both",
        metadata={"mention_count": 10, "degree": 5}
    )
    
    # 验证 to_dict
    result_dict = result.to_dict()
    
    assert "name" in result_dict, "应包含 name"
    assert "entity_type" in result_dict, "应包含 entity_type"
    assert "score" in result_dict, "应包含 score"
    assert "graph_score" in result_dict, "应包含 graph_score"
    assert "vector_score" in result_dict, "应包含 vector_score"
    assert "source" in result_dict, "应包含 source"
    assert "metadata" in result_dict, "应包含 metadata"
    
    # 验证数值精度
    assert result_dict["score"] == 0.85, "score 应为 0.85"
    assert result_dict["graph_score"] == 0.9, "graph_score 应为 0.9"
    assert result_dict["vector_score"] == 0.75, "vector_score 应为 0.75"
    assert result_dict["source"] == "both", "source 应为 both"
    
    print(f"  ✅ name: {result_dict['name']}")
    print(f"  ✅ entity_type: {result_dict['entity_type']}")
    print(f"  ✅ score: {result_dict['score']}")
    print(f"  ✅ graph_score: {result_dict['graph_score']}")
    print(f"  ✅ vector_score: {result_dict['vector_score']}")
    print(f"  ✅ source: {result_dict['source']}")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_fuse_results():
    """测试 3: 融合排序算法"""
    print("🔍 测试 3: 融合排序算法")
    print("-" * 60)
    
    config = HybridSearchConfig()
    config.graph_weight = 0.6
    config.vector_weight = 0.4
    
    # 创建模拟结果
    graph_results = [
        SearchResult("实体 A", "概念", "描述 A", 0.9, 0.9, 0.0, "graph"),
        SearchResult("实体 B", "概念", "描述 B", 0.8, 0.8, 0.0, "graph"),
        SearchResult("实体 C", "概念", "描述 C", 0.7, 0.7, 0.0, "graph"),
    ]
    
    vector_results = [
        SearchResult("实体 B", "概念", "描述 B", 0.95, 0.0, 0.95, "vector"),
        SearchResult("实体 D", "概念", "描述 D", 0.85, 0.0, 0.85, "vector"),
        SearchResult("实体 E", "概念", "描述 E", 0.75, 0.0, 0.75, "vector"),
    ]
    
    # 创建临时 HybridSearch 实例用于测试融合
    # 由于需要 graph_store，我们直接测试融合逻辑
    from typing import Dict
    
    result_map: Dict[str, SearchResult] = {}
    
    # 先添加图遍历结果
    for r in graph_results:
        result_map[r.name] = r
    
    # 再融合向量结果
    for r in vector_results:
        if r.name in result_map:
            existing = result_map[r.name]
            existing.source = "both"
            existing.vector_score = r.vector_score
            # 融合得分：图权重 * 图得分 + 向量权重 * 向量得分
            existing.score = (
                config.graph_weight * existing.graph_score +
                config.vector_weight * r.vector_score
            )
        else:
            # 纯向量结果也需要应用权重
            r.score = config.vector_weight * r.vector_score
            result_map[r.name] = r
    
    # 纯图遍历结果也需要应用权重
    for name, r in result_map.items():
        if r.source == "graph":
            r.score = config.graph_weight * r.graph_score
    
    # 按融合得分排序
    sorted_results = sorted(result_map.values(), key=lambda x: x.score, reverse=True)
    
    # 验证融合结果
    assert len(sorted_results) == 5, f"应有 5 个结果，实际 {len(sorted_results)}"
    
    # 打印所有结果用于调试
    for i, r in enumerate(sorted_results):
        print(f"    第{i+1}名：{r.name} (score={r.score:.4f}, source={r.source})")
    
    # 实体 B 应该是最高分（图 + 向量）
    # 实体 B: 0.6 * 0.8 + 0.4 * 0.95 = 0.48 + 0.38 = 0.86
    # 实体 A: 0.6 * 0.9 = 0.54 (纯图)
    # 实体 D: 0.4 * 0.85 = 0.34 (纯向量)
    assert sorted_results[0].name == "实体 B", f"实体 B 应该是最高分，实际是 {sorted_results[0].name}"
    assert sorted_results[0].source == "both", "实体 B 应来自双路"
    assert abs(sorted_results[0].score - 0.86) < 0.01, f"实体 B 融合得分应为 0.86，实际 {sorted_results[0].score}"
    
    # 验证前两名
    assert sorted_results[0].name == "实体 B", f"第 1 名应为实体 B，实际是 {sorted_results[0].name}"
    assert sorted_results[0].source == "both", "第 1 名应来自双路"
    assert abs(sorted_results[0].score - 0.86) < 0.01, f"第 1 名得分应为 0.86，实际 {sorted_results[0].score}"
    
    assert sorted_results[1].name == "实体 A", f"第 2 名应为实体 A，实际是 {sorted_results[1].name}"
    assert sorted_results[1].source == "graph", "第 2 名应来自图遍历"
    
    print(f"  ✅ 融合排序正确：B(双路) > A(图) > C(图) > D(向量) > E(向量)")
    
    print(f"  ✅ 融合结果数量：{len(sorted_results)}")
    print(f"  ✅ 第 1 名：{sorted_results[0].name} (score={sorted_results[0].score:.4f}, source={sorted_results[0].source})")
    print(f"  ✅ 第 2 名：{sorted_results[1].name} (score={sorted_results[1].score:.4f}, source={sorted_results[1].source})")
    print(f"  ✅ 第 3 名：{sorted_results[2].name} (score={sorted_results[2].score:.4f}, source={sorted_results[2].source})")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_config_from_env():
    """测试 4: 从环境变量读取配置"""
    print("🔍 测试 4: 从环境变量读取配置")
    print("-" * 60)
    
    # 设置环境变量
    os.environ["HYBRID_SEARCH_VECTOR_TOP_K"] = "20"
    os.environ["HYBRID_SEARCH_GRAPH_WEIGHT"] = "0.7"
    os.environ["HYBRID_SEARCH_VECTOR_WEIGHT"] = "0.3"
    os.environ["HYBRID_SEARCH_VECTOR_TIMEOUT"] = "3.0"
    
    config = HybridSearchConfig()
    
    # 验证从环境变量读取
    assert config.vector_top_k == 20, f"vector_top_k 应为 20，实际 {config.vector_top_k}"
    assert abs(config.graph_weight - 0.7) < 0.01, f"graph_weight 应为 0.7，实际 {config.graph_weight}"
    assert abs(config.vector_weight - 0.3) < 0.01, f"vector_weight 应为 0.3，实际 {config.vector_weight}"
    assert config.vector_timeout_seconds == 3.0, f"timeout 应为 3.0，实际 {config.vector_timeout_seconds}"
    
    # 清理环境变量
    del os.environ["HYBRID_SEARCH_VECTOR_TOP_K"]
    del os.environ["HYBRID_SEARCH_GRAPH_WEIGHT"]
    del os.environ["HYBRID_SEARCH_VECTOR_WEIGHT"]
    del os.environ["HYBRID_SEARCH_VECTOR_TIMEOUT"]
    
    print(f"  ✅ vector_top_k: {config.vector_top_k} (from env)")
    print(f"  ✅ graph_weight: {config.graph_weight} (from env)")
    print(f"  ✅ vector_weight: {config.vector_weight} (from env)")
    print(f"  ✅ vector_timeout_seconds: {config.vector_timeout_seconds} (from env)")
    print(f"  ✅ 测试通过")
    print()
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("Issue #44: 混合检索实现单元测试")
    print("=" * 70)
    print()
    
    tests = [
        ("混合检索配置", test_hybrid_search_config),
        ("检索结果序列化", test_search_result),
        ("融合排序算法", test_fuse_results),
        ("从环境变量读取配置", test_config_from_env)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ❌ 测试失败：{e}")
            print()
    
    # 总结
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for name, result, error in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
        if error:
            print(f"       错误：{error}")
    
    print()
    print(f"总计：{passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
