#!/usr/bin/env python3
"""
Issue #38: 健康检查端点单元测试

测试用例：
1. /health - 基本健康检查
2. /diagnose - 详细诊断
3. /ready - 就绪检查
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from health_endpoints import (
    get_health_check,
    get_detailed_diagnose,
    get_readiness_check,
    update_meditation_result
)
from meditation_memory.graph_store import GraphStore
from meditation_memory.meditation_worker import MeditationEngine
from meditation_memory.meditation_config import MeditationConfig


def test_health_check():
    """测试 1：基本健康检查"""
    print("🔍 测试 1: /health 基本健康检查")
    print("-" * 60)
    
    store = GraphStore()
    meditation_config = MeditationConfig()
    meditation_engine = MeditationEngine(store, meditation_config)
    
    result = get_health_check(store, meditation_engine)
    
    # 验证返回结构
    assert "status" in result, "缺少 status 字段"
    assert "neo4j_connection" in result, "缺少 neo4j_connection 字段"
    assert "uptime_seconds" in result, "缺少 uptime_seconds 字段"
    
    # 验证状态值
    assert result["status"] in ["healthy", "degraded", "unhealthy"], f"无效的状态：{result['status']}"
    assert result["neo4j_connection"] in ["connected", "disconnected", "error", "unknown"], \
        f"无效的连接状态：{result['neo4j_connection']}"
    
    # 验证运行时间
    assert isinstance(result["uptime_seconds"], int), "uptime_seconds 应该是整数"
    assert result["uptime_seconds"] >= 0, "uptime_seconds 应该是非负数"
    
    print(f"  ✅ status: {result['status']}")
    print(f"  ✅ neo4j_connection: {result['neo4j_connection']}")
    print(f"  ✅ uptime_seconds: {result['uptime_seconds']}")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_detailed_diagnose():
    """测试 2：详细诊断"""
    print("🔍 测试 2: /diagnose 详细诊断")
    print("-" * 60)
    
    store = GraphStore()
    meditation_config = MeditationConfig()
    meditation_engine = MeditationEngine(store, meditation_config)
    
    result = get_detailed_diagnose(store, meditation_engine)
    
    # 验证返回结构
    assert "neo4j" in result, "缺少 neo4j 字段"
    assert "llm" in result, "缺少 llm 字段"
    assert "meditation" in result, "缺少 meditation 字段"
    assert "api" in result, "缺少 api 字段"
    
    # 验证 Neo4j 状态
    neo4j_status = result["neo4j"].get("status", "unknown")
    assert neo4j_status in ["connected", "disconnected", "error", "unknown"], \
        f"无效的 Neo4j 状态：{neo4j_status}"
    
    # 验证如果有连接，应该有统计数据
    if neo4j_status == "connected":
        assert "node_count" in result["neo4j"], "缺少 node_count"
        assert "relationship_count" in result["neo4j"], "缺少 relationship_count"
        assert "pending_nodes" in result["neo4j"], "缺少 pending_nodes"
        print(f"  ✅ node_count: {result['neo4j']['node_count']:,}")
        print(f"  ✅ relationship_count: {result['neo4j']['relationship_count']:,}")
        print(f"  ✅ pending_nodes: {result['neo4j']['pending_nodes']:,}")
    
    # 验证 LLM 状态
    llm_status = result["llm"].get("status", "unknown")
    assert llm_status in ["ok", "error", "unknown"], f"无效的 LLM 状态：{llm_status}"
    
    # 验证 API 状态
    assert "uptime_seconds" in result["api"], "缺少 api uptime"
    
    print(f"  ✅ neo4j.status: {neo4j_status}")
    print(f"  ✅ llm.status: {llm_status}")
    print(f"  ✅ api.uptime_seconds: {result['api']['uptime_seconds']}")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_readiness_check():
    """测试 3：就绪检查"""
    print("🔍 测试 3: /ready 就绪检查")
    print("-" * 60)
    
    store = GraphStore()
    
    result = get_readiness_check(store)
    
    # 验证返回结构
    assert "ready" in result, "缺少 ready 字段"
    assert "checks" in result, "缺少 checks 字段"
    
    # 验证 ready 是布尔值
    assert isinstance(result["ready"], bool), "ready 应该是布尔值"
    
    # 验证 checks 包含 neo4j
    assert "neo4j" in result["checks"], "checks 缺少 neo4j"
    
    # 如果 Neo4j 连接正常，应该就绪
    neo4j_check = result["checks"]["neo4j"]
    if neo4j_check == "connected":
        assert result["ready"] == True, "Neo4j 连接正常应该就绪"
        print(f"  ✅ ready: {result['ready']}")
        print(f"  ✅ neo4j: {neo4j_check}")
        print(f"  ✅ 服务就绪")
    else:
        assert result["ready"] == False, "Neo4j 未连接应该不就绪"
        assert "reason" in result, "缺少 reason 字段"
        print(f"  ✅ ready: {result['ready']}")
        print(f"  ✅ neo4j: {neo4j_check}")
        print(f"  ✅ reason: {result['reason']}")
        print(f"  ✅ 服务未就绪（预期行为）")
    
    print(f"  ✅ 测试通过")
    print()
    return True


def test_meditation_result_update():
    """测试 4：冥思结果更新"""
    print("🔍 测试 4: 冥思结果更新")
    print("-" * 60)
    
    # 模拟冥思结果
    mock_result = {
        "started_at": "2026-04-09T04:00:00Z",
        "status": "success",
        "duration_ms": 324000,
        "stats": {
            "nodes_scanned": 600,
            "entities_merged": 0,
            "relations_relabeled": 2,
            "meta_knowledge_created": 50
        },
        "errors": []
    }
    
    # 更新结果
    update_meditation_result(mock_result)
    
    # 验证更新后的健康检查包含冥思信息
    store = GraphStore()
    meditation_config = MeditationConfig()
    meditation_engine = MeditationEngine(store, meditation_config)
    
    result = get_health_check(store, meditation_engine)
    
    assert result["last_meditation"] == mock_result["started_at"], "last_meditation 未更新"
    assert result["meditation_status"] == mock_result["status"], "meditation_status 未更新"
    
    print(f"  ✅ last_meditation: {result['last_meditation']}")
    print(f"  ✅ meditation_status: {result['meditation_status']}")
    print(f"  ✅ 测试通过")
    print()
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("Issue #38: 健康检查端点单元测试")
    print("=" * 70)
    print()
    
    tests = [
        ("基本健康检查", test_health_check),
        ("详细诊断", test_detailed_diagnose),
        ("就绪检查", test_readiness_check),
        ("冥思结果更新", test_meditation_result_update)
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
