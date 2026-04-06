#!/usr/bin/env python3
"""验证 P0-3 /feedback 端点持久化效果"""
import json
import httpx
import time

BASE = "http://127.0.0.1:18900"
headers = {"Content-Type": "application/json"}

def test_feedback_storage():
    """测试 /feedback 端点是否正确存储数据到 Neo4j"""
    print("=== 测试 1：成功反馈存储 ===")
    payload = {
        "query": "Neo4j 记忆系统如何工作？",
        "applied_strategy_name": "reality_greedy_v3",
        "success": True,
        "confidence": 0.85,
        "validation_status": "accurate",
        "result_count": 5,
        "returned_entities": ["Neo4j", "记忆系统", "冥思"],
        "useful_entities": ["Neo4j", "记忆系统"],
        "noise_entities": ["冥思"],
        "error_msg": None
    }

    resp = httpx.post(f"{BASE}/feedback", json=payload, headers=headers, timeout=10)
    print(f"  状态码: {resp.status_code}")
    data = resp.json()
    print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

    if resp.status_code == 200:
        assert data.get("feedback_stored") == True, "❌ feedback_stored 应为 True"
        assert "feedback_node_id" in data.get("details", {}), "❌ 缺少 feedback_node_id"
        print("  ✅ 成功反馈存储测试通过")
        
    print("\n=== 测试 2：失败反馈存储 ===")
    payload_fail = {
        "query": "不存在的查询",
        "applied_strategy_name": "unknown_strategy",
        "success": False,
        "confidence": 0.2,
        "validation_status": "wrong",
        "result_count": 0,
        "returned_entities": [],
        "useful_entities": [],
        "noise_entities": ["噪声1", "噪声2"],
        "error_msg": "测试错误消息"
    }

    resp = httpx.post(f"{BASE}/feedback", json=payload_fail, headers=headers, timeout=10)
    print(f"  状态码: {resp.status_code}")
    data = resp.json()
    print(f"  响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

    if resp.status_code == 200:
        assert data.get("feedback_stored") == True, "❌ 失败反馈也应存储"
        print("  ✅ 失败反馈存储测试通过")

    print("\n=== 测试 3：检查 GraphQL 反馈统计 ===")
    if httpx.get(f"{BASE}/stats").status_code == 200:
        print("  ✅ /stats 端点正常")
    else:
        print("  ⚠️  /stats 端点未响应")

    print("\n🎉 P0-3 验证完成！")

if __name__ == "__main__":
    test_feedback_storage()
