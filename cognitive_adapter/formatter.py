#!/usr/bin/env python3
"""
Formatter - 输出适配 OpenClaw
"""

from typing import List, Dict, Any

def to_claw_format(nodes: List[Any]) -> List[Dict[str, Any]]:
    """
    将节点转换为OpenClaw格式
    
    Args:
        nodes: 节点列表
        
    Returns:
        OpenClaw格式的结果列表
    """
    results = []
    
    for i, node in enumerate(nodes):
        # 提取内容
        if isinstance(node, dict):
            content = node.get("content", "")
            attention_score = node.get("attention_score", 0.5)
            rqs = node.get("rqs", 0.5)
            source = node.get("source", "unknown")
            metadata = node.get("metadata", {})
        else:
            # 假设是对象
            content = getattr(node, "content", str(node))
            attention_score = getattr(node, "attention_score", 0.5)
            rqs = getattr(node, "rqs", 0.5)
            source = getattr(node, "source", "graph")
            metadata = getattr(node, "metadata", {})
        
        # 计算综合分数
        score = attention_score * rqs
        
        # 创建结果项
        result = {
            "text": str(content),
            "score": score,
            "rank": i + 1,
            "metadata": {
                "rqs": rqs,
                "attention_score": attention_score,
                "source": source,
                "composite_score": score,
                **metadata  # 合并额外元数据
            }
        }
        
        # 添加特定字段（如果存在）
        if isinstance(node, dict):
            for key in ["timestamp", "type", "confidence"]:
                if key in node:
                    result["metadata"][key] = node[key]
        else:
            for attr in ["timestamp", "type", "confidence"]:
                if hasattr(node, attr):
                    result["metadata"][attr] = getattr(node, attr)
        
        results.append(result)
    
    # 按分数重新排序（确保顺序正确）
    results.sort(key=lambda x: x["score"], reverse=True)
    
    # 更新排名
    for i, result in enumerate(results):
        result["rank"] = i + 1
    
    return results

def format_for_display(results: List[Dict[str, Any]], max_results: int = 5) -> str:
    """
    格式化结果显示
    
    Args:
        results: 结果列表
        max_results: 最大显示数量
        
    Returns:
        格式化字符串
    """
    if not results:
        return "⚠️  没有找到相关结果"
    
    output = []
    
    for i, result in enumerate(results[:max_results]):
        text = result["text"]
        score = result["score"]
        source = result["metadata"].get("source", "unknown")
        
        # 截断长文本
        if len(text) > 80:
            text = text[:77] + "..."
        
        # 格式化行
        line = f"{i+1}. [{score:.3f}] {text}"
        
        # 添加来源标记
        if source == "real_world_api":
            line += " 🌍"
        elif source == "graph":
            line += " 🧠"
        elif source == "simulated":
            line += " 🔄"
        
        output.append(line)
    
    # 添加统计信息
    total = len(results)
    avg_score = sum(r["score"] for r in results) / total if total > 0 else 0
    
    stats = f"\n📊 统计: {total}个结果 | 平均分数: {avg_score:.3f}"
    
    # 检查是否有实时数据
    real_time_count = sum(1 for r in results if r["metadata"].get("source") == "real_world_api")
    if real_time_count > 0:
        stats += f" | 实时数据: {real_time_count}个"
    
    output.append(stats)
    
    return "\n".join(output)

def validate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    验证结果质量
    
    Args:
        results: 结果列表
        
    Returns:
        验证报告
    """
    if not results:
        return {
            "valid": False,
            "reason": "空结果",
            "suggestions": ["检查查询语法", "扩大搜索范围"]
        }
    
    # 检查分数分布
    scores = [r["score"] for r in results]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)
    min_score = min(scores)
    
    # 检查实时数据
    real_time_sources = [r for r in results if r["metadata"].get("source") == "real_world_api"]
    
    # 检查RQS分布
    rqs_values = [r["metadata"].get("rqs", 0.5) for r in results]
    avg_rqs = sum(rqs_values) / len(rqs_values)
    
    # 生成报告
    report = {
        "valid": True,
        "summary": {
            "total_results": len(results),
            "avg_score": avg_score,
            "score_range": max_score - min_score,
            "real_time_count": len(real_time_sources),
            "avg_rqs": avg_rqs
        },
        "quality": {
            "has_real_time_data": len(real_time_sources) > 0,
            "score_variance_ok": (max_score - min_score) > 0.1,  # 分数有差异
            "rqs_threshold_met": avg_rqs > 0.3,  # RQS平均超过0.3
            "diversity_ok": len(set(r["text"][:20] for r in results)) > 1  # 文本有差异
        },
        "suggestions": []
    }
    
    # 生成建议
    if not report["quality"]["has_real_time_data"]:
        report["suggestions"].append("考虑添加实时数据源")
    
    if not report["quality"]["score_variance_ok"]:
        report["suggestions"].append("优化评分算法以增加区分度")
    
    if not report["quality"]["rqs_threshold_met"]:
        report["suggestions"].append("提高RQS评分质量")
    
    if not report["quality"]["diversity_ok"]:
        report["suggestions"].append("增加结果多样性")
    
    return report

def test_formatter():
    """测试格式化器"""
    print("🧪 测试 Formatter...")
    
    # 创建测试数据
    test_nodes = [
        {
            "content": "当前 USD→CNY 汇率：6.9123",
            "attention_score": 1.0,
            "rqs": 0.9,
            "source": "real_world_api",
            "timestamp": "2026-03-26T19:55:00"
        },
        {
            "content": "USD是美元的国际代码，广泛用于国际贸易",
            "attention_score": 0.8,
            "rqs": 0.7,
            "source": "graph"
        },
        {
            "content": "CNY是人民币的国际代码，由中国央行管理",
            "attention_score": 0.7,
            "rqs": 0.6,
            "source": "graph"
        },
        {
            "content": "汇率受多种因素影响，包括利率、通胀和经济政策",
            "attention_score": 0.6,
            "rqs": 0.5,
            "source": "graph"
        }
    ]
    
    # 测试格式转换
    print("\n🔧 测试格式转换:")
    claw_results = to_claw_format(test_nodes)
    
    for i, result in enumerate(claw_results):
        print(f"  {result['rank']}. 分数: {result['score']:.3f}")
        print(f"     文本: {result['text'][:50]}...")
        print(f"     来源: {result['metadata'].get('source')}")
        print(f"     RQS: {result['metadata'].get('rqs')}")
    
    # 测试显示格式化
    print("\n📋 测试显示格式化:")
    display = format_for_display(claw_results, max_results=3)
    print(display)
    
    # 测试验证
    print("\n✅ 测试验证:")
    validation = validate_results(claw_results)
    
    print(f"  是否有效: {validation['valid']}")
    print(f"  总结:")
    for key, value in validation['summary'].items():
        print(f"    {key}: {value}")
    
    print(f"  质量检查:")
    for key, value in validation['quality'].items():
        print(f"    {key}: {'✅' if value else '❌'}")
    
    if validation['suggestions']:
        print(f"  建议:")
        for suggestion in validation['suggestions']:
            print(f"    • {suggestion}")
    
    print("\n✅ Formatter测试完成")

if __name__ == "__main__":
    test_formatter()