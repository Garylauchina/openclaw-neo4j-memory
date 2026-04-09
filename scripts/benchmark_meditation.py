#!/usr/bin/env python3
"""
冥思性能基准测试（Issue #47）

测试不同图谱规模下的冥思性能：
  - 冥思时长（秒）
  - LLM 调用次数
  - 总成本（美元）
  - 熵减效果（%）
  - 节点处理速度（节点/分钟）
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'plugins', 'neo4j-memory'))

from meditation_memory.graph_store import GraphStore
from meditation_memory.meditation_worker import MeditationWorker
from meditation_memory.meditation_config import MeditationConfig
from meditation_memory.information_theory import GraphEntropyMetrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("benchmark_meditation")


def run_meditation_benchmark(
    scale: str = "small",
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    运行冥思性能基准测试
    
    Args:
        scale: 测试规模（small/medium/large/xlarge）
        dry_run: 如果为 True，不实际执行冥思
        
    Returns:
        性能指标字典
    """
    logger.info(f"开始冥思基准测试 - 规模：{scale}")
    
    # 初始化
    store = GraphStore()
    config = MeditationConfig()
    config.safety.dry_run = dry_run
    
    # 限制处理节点数（根据规模）
    scale_limits = {
        "small": 100,
        "medium": 500,
        "large": 1000,
        "xlarge": 5000
    }
    node_limit = scale_limits.get(scale, 100)
    
    # 获取图谱统计
    stats = store.get_stats()
    meditation_stats = store.get_meditation_stats()
    
    logger.info(f"当前图谱规模：{stats['node_count']} 节点，{stats['edge_count']} 关系")
    
    # 计算初始熵
    entropy_calculator = GraphEntropyMetrics()
    initial_entropy = entropy_calculator.calculate_global_entropy(store)
    logger.info(f"初始全局熵：{initial_entropy:.4f}")
    
    # 执行冥思
    worker = MeditationWorker(store, config)
    
    start_time = time.time()
    
    if not dry_run:
        result = worker.run_meditation(mode="auto")
    else:
        # 模拟冥思（只获取待处理节点）
        nodes = store.get_nodes_needing_meditation(limit=node_limit)
        result = {
            "nodes_scanned": len(nodes),
            "status": "dry_run"
        }
    
    elapsed_time = time.time() - start_time
    
    # 计算最终熵
    final_entropy = entropy_calculator.calculate_global_entropy(store)
    logger.info(f"最终全局熵：{final_entropy:.4f}")
    
    # 计算熵减
    entropy_reduction = ((initial_entropy - final_entropy) / max(0.001, initial_entropy)) * 100
    
    # 计算处理速度
    nodes_scanned = result.get("nodes_scanned", 0)
    nodes_per_minute = (nodes_scanned / max(1, elapsed_time)) * 60
    
    # 估算 LLM 调用次数（根据步骤）
    estimated_llm_calls = nodes_scanned // 50  # 假设每 50 个节点调用 1 次 LLM
    
    # 估算成本（假设每次 LLM 调用 $0.002）
    estimated_cost = estimated_llm_calls * 0.002
    
    # 构建结果
    benchmark_result = {
        "timestamp": datetime.now().isoformat(),
        "scale": scale,
        "graph_stats": {
            "node_count": stats["node_count"],
            "edge_count": stats["edge_count"],
            "pending_nodes": meditation_stats.get("pending_meditation", 0)
        },
        "meditation_stats": {
            "elapsed_time_seconds": round(elapsed_time, 2),
            "nodes_scanned": nodes_scanned,
            "nodes_per_minute": round(nodes_per_minute, 2),
            "llm_calls_estimated": estimated_llm_calls,
            "cost_estimated_usd": round(estimated_cost, 4),
            "dry_run": dry_run
        },
        "entropy": {
            "initial": round(initial_entropy, 4),
            "final": round(final_entropy, 4),
            "reduction_percent": round(entropy_reduction, 2)
        }
    }
    
    logger.info(f"冥思基准测试完成 - 耗时 {elapsed_time:.2f}s, 处理 {nodes_scanned} 节点")
    
    return benchmark_result


def save_benchmark_result(result: Dict[str, Any], output_dir: str = "/tmp/benchmarks") -> str:
    """保存基准测试结果"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"meditation_benchmark_{timestamp}.json"
    filepath = output_path / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    logger.info(f"基准测试结果已保存：{filepath}")
    return str(filepath)


def print_benchmark_report(result: Dict[str, Any]) -> None:
    """打印基准测试报告"""
    print("=" * 70)
    print("冥思性能基准测试报告")
    print("=" * 70)
    print(f"测试时间：{result['timestamp']}")
    print(f"测试规模：{result['scale']}")
    print(f"干运行：{result['meditation_stats']['dry_run']}")
    print()
    
    print("图谱统计:")
    print(f"  节点数：{result['graph_stats']['node_count']:,}")
    print(f"  关系数：{result['graph_stats']['edge_count']:,}")
    print(f"  待处理节点：{result['graph_stats']['pending_nodes']:,}")
    print()
    
    print("冥思性能:")
    print(f"  耗时：{result['meditation_stats']['elapsed_time_seconds']:.2f} 秒")
    print(f"  处理节点：{result['meditation_stats']['nodes_scanned']:,}")
    print(f"  处理速度：{result['meditation_stats']['nodes_per_minute']:.2f} 节点/分钟")
    print(f"  LLM 调用（估算）：{result['meditation_stats']['llm_calls_estimated']:,} 次")
    print(f"  成本（估算）：${result['meditation_stats']['cost_estimated_usd']:.4f}")
    print()
    
    print("熵减效果:")
    print(f"  初始熵：{result['entropy']['initial']:.4f}")
    print(f"  最终熵：{result['entropy']['final']:.4f}")
    print(f"  熵减：{result['entropy']['reduction_percent']:.2f}%")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="冥思性能基准测试")
    parser.add_argument(
        "--scale",
        type=str,
        default="small",
        choices=["small", "medium", "large", "xlarge"],
        help="测试规模（默认：small）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="干运行（不实际执行冥思）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/tmp/benchmarks",
        help="输出目录（默认：/tmp/benchmarks）"
    )
    
    args = parser.parse_args()
    
    # 运行基准测试
    result = run_meditation_benchmark(
        scale=args.scale,
        dry_run=args.dry_run
    )
    
    # 保存结果
    filepath = save_benchmark_result(result, args.output_dir)
    
    # 打印报告
    print_benchmark_report(result)
    
    print(f"\n结果已保存：{filepath}")


if __name__ == "__main__":
    main()
