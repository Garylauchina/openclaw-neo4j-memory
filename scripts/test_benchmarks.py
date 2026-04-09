#!/usr/bin/env python3
"""
性能基准测试单元测试（Issue #47）
"""

import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark_meditation import run_meditation_benchmark, save_benchmark_result
from benchmark_search import run_search_benchmark, save_benchmark_result as save_search_result


def test_meditation_benchmark_dry_run():
    """测试 1: 冥思基准测试（干运行）"""
    print("🔍 测试 1: 冥思基准测试（干运行）")
    print("-" * 60)
    
    result = run_meditation_benchmark(scale="small", dry_run=True)
    
    # 验证结果结构
    assert "timestamp" in result, "应包含 timestamp"
    assert "scale" in result, "应包含 scale"
    assert "graph_stats" in result, "应包含 graph_stats"
    assert "meditation_stats" in result, "应包含 meditation_stats"
    assert "entropy" in result, "应包含 entropy"
    
    # 验证规模
    assert result["scale"] == "small", f"规模应为 small，实际 {result['scale']}"
    
    # 验证干运行标志
    assert result["meditation_stats"]["dry_run"] == True, "dry_run 应为 True"
    
    print(f"  ✅ timestamp: {result['timestamp']}")
    print(f"  ✅ scale: {result['scale']}")
    print(f"  ✅ dry_run: {result['meditation_stats']['dry_run']}")
    print(f"  ✅ nodes_scanned: {result['meditation_stats']['nodes_scanned']}")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_meditation_result_save():
    """测试 2: 冥思结果保存"""
    print("🔍 测试 2: 冥思结果保存")
    print("-" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_meditation_benchmark(scale="small", dry_run=True)
        filepath = save_benchmark_result(result, tmpdir)
        
        # 验证文件存在
        assert os.path.exists(filepath), f"结果文件不存在：{filepath}"
        
        # 验证 JSON 格式
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_result = json.load(f)
        
        assert loaded_result["scale"] == "small", "保存的规模应一致"
        
        print(f"  ✅ 文件保存：{filepath}")
        print(f"  ✅ JSON 格式：OK")
        print(f"  ✅ 测试通过")
    print()
    return True


def test_search_benchmark_dry_run():
    """测试 3: 检索基准测试（干运行）"""
    print("🔍 测试 3: 检索基准测试（干运行）")
    print("-" * 60)
    
    result = run_search_benchmark(iterations=3, dry_run=True)
    
    # 验证结果结构
    assert "timestamp" in result, "应包含 timestamp"
    assert "test_config" in result, "应包含 test_config"
    assert "overall_stats" in result, "应包含 overall_stats"
    assert "query_results" in result, "应包含 query_results"
    
    # 验证配置
    assert result["test_config"]["iterations"] == 3, "迭代次数应为 3"
    assert result["test_config"]["dry_run"] == True, "dry_run 应为 True"
    
    # 验证总体统计
    assert "avg_latency_ms" in result["overall_stats"], "应包含平均延迟"
    assert "p95_latency_ms" in result["overall_stats"], "应包含 P95 延迟"
    
    print(f"  ✅ timestamp: {result['timestamp']}")
    print(f"  ✅ iterations: {result['test_config']['iterations']}")
    print(f"  ✅ avg_latency: {result['overall_stats']['avg_latency_ms']:.2f}ms")
    print(f"  ✅ p95_latency: {result['overall_stats']['p95_latency_ms']:.2f}ms")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_search_result_save():
    """测试 4: 检索结果保存"""
    print("🔍 测试 4: 检索结果保存")
    print("-" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_search_benchmark(iterations=3, dry_run=True)
        filepath = save_search_result(result, tmpdir)
        
        # 验证文件存在
        assert os.path.exists(filepath), f"结果文件不存在：{filepath}"
        
        # 验证 JSON 格式
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_result = json.load(f)
        
        assert loaded_result["test_config"]["iterations"] == 3, "迭代次数应一致"
        
        print(f"  ✅ 文件保存：{filepath}")
        print(f"  ✅ JSON 格式：OK")
        print(f"  ✅ 测试通过")
    print()
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("Issue #47: 性能基准测试单元测试")
    print("=" * 70)
    print()
    
    tests = [
        ("冥思基准测试（干运行）", test_meditation_benchmark_dry_run),
        ("冥思结果保存", test_meditation_result_save),
        ("检索基准测试（干运行）", test_search_benchmark_dry_run),
        ("检索结果保存", test_search_result_save)
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
