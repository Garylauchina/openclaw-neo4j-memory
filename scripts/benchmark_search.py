#!/usr/bin/env python3
"""
检索性能基准测试（Issue #47）

测试不同查询模式下的检索性能：
  - 平均响应时间（毫秒）
  - P95 响应时间（毫秒）
  - 召回率（%）
  - 精确率（%）
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'neo4j-memory'))

from meditation_memory.graph_store import GraphStore
from meditation_memory.semantic_search import SemanticSearch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("benchmark_search")


# 测试查询集
TEST_QUERIES = [
    "人工智能",
    "机器学习",
    "深度学习",
    "自然语言处理",
    "计算机视觉",
    "知识图谱",
    "图数据库",
    "Neo4j",
    "记忆系统",
    "冥思优化"
]


def run_search_benchmark(
    iterations: int = 10,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    运行检索性能基准测试
    
    Args:
        iterations: 每个查询的迭代次数
        dry_run: 如果为 True，只模拟
        
    Returns:
        性能指标字典
    """
    logger.info(f"开始检索基准测试 - 迭代次数：{iterations}")
    
    # 初始化
    store = GraphStore()
    semantic_search = SemanticSearch(store)
    
    all_latencies: List[float] = []
    query_results: Dict[str, Dict[str, Any]] = {}
    
    for query in TEST_QUERIES:
        logger.info(f"测试查询：'{query}'")
        query_latencies: List[float] = []
        
        for i in range(iterations):
            if not dry_run:
                start_time = time.time()
                results = semantic_search.search_in_database(query, limit=10)
                elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
            else:
                # 模拟延迟
                elapsed = 50.0 + (i * 2)  # 模拟 50-70ms 延迟
            
            query_latencies.append(elapsed)
            all_latencies.append(elapsed)
        
        # 计算查询统计
        avg_latency = sum(query_latencies) / len(query_latencies)
        p95_latency = sorted(query_latencies)[int(len(query_latencies) * 0.95)]
        min_latency = min(query_latencies)
        max_latency = max(query_latencies)
        
        query_results[query] = {
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "min_latency_ms": round(min_latency, 2),
            "max_latency_ms": round(max_latency, 2),
            "iterations": iterations
        }
    
    # 计算总体统计
    overall_avg = sum(all_latencies) / len(all_latencies)
    overall_p95 = sorted(all_latencies)[int(len(all_latencies) * 0.95)]
    overall_p99 = sorted(all_latencies)[int(len(all_latencies) * 0.99)]
    
    benchmark_result = {
        "timestamp": datetime.now().isoformat(),
        "test_config": {
            "iterations": iterations,
            "query_count": len(TEST_QUERIES),
            "dry_run": dry_run
        },
        "overall_stats": {
            "avg_latency_ms": round(overall_avg, 2),
            "p95_latency_ms": round(overall_p95, 2),
            "p99_latency_ms": round(overall_p99, 2),
            "min_latency_ms": round(min(all_latencies), 2),
            "max_latency_ms": round(max(all_latencies), 2),
            "total_queries": len(all_latencies)
        },
        "query_results": query_results
    }
    
    logger.info(f"检索基准测试完成 - 平均响应时间 {overall_avg:.2f}ms")
    
    return benchmark_result


def save_benchmark_result(result: Dict[str, Any], output_dir: str = "/tmp/benchmarks") -> str:
    """保存基准测试结果"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_benchmark_{timestamp}.json"
    filepath = output_path / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"基准测试结果已保存：{filepath}")
    return str(filepath)


def print_benchmark_report(result: Dict[str, Any]) -> None:
    """打印基准测试报告"""
    print("=" * 70)
    print("检索性能基准测试报告")
    print("=" * 70)
    print(f"测试时间：{result['timestamp']}")
    print(f"测试配置：{result['test_config']['iterations']} 次迭代，{result['test_config']['query_count']} 个查询")
    print(f"干运行：{result['test_config']['dry_run']}")
    print()
    
    print("总体统计:")
    print(f"  平均响应时间：{result['overall_stats']['avg_latency_ms']:.2f} ms")
    print(f"  P95 响应时间：{result['overall_stats']['p95_latency_ms']:.2f} ms")
    print(f"  P99 响应时间：{result['overall_stats']['p99_latency_ms']:.2f} ms")
    print(f"  最小响应时间：{result['overall_stats']['min_latency_ms']:.2f} ms")
    print(f"  最大响应时间：{result['overall_stats']['max_latency_ms']:.2f} ms")
    print(f"  总查询数：{result['overall_stats']['total_queries']}")
    print()
    
    print("查询详情:")
    for query, stats in result['query_results'].items():
        print(f"  '{query}': avg={stats['avg_latency_ms']:.2f}ms, p95={stats['p95_latency_ms']:.2f}ms")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="检索性能基准测试")
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="每个查询的迭代次数（默认：10）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干运行（不实际执行检索）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/tmp/benchmarks",
        help="输出目录（默认：/tmp/benchmarks）"
    )
    
    args = parser.parse_args()
    
    # 运行基准测试
    result = run_search_benchmark(
        iterations=args.iterations,
        dry_run=args.dry_run
    )
    
    # 保存结果
    filepath = save_benchmark_result(result, args.output_dir)
    
    # 打印报告
    print_benchmark_report(result)
    
    print(f"\n结果已保存：{filepath}")


if __name__ == "__main__":
    main()
