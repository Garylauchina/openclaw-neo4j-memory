#!/usr/bin/env python3
"""
Issue #45: 记忆分层设计单元测试
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory_layers import MemoryLayer, MemoryLayerConfig, MemoryNode, MemoryLayerManager


def test_memory_layer_enum():
    """测试 1: 记忆层级枚举"""
    print("🔍 测试 1: 记忆层级枚举")
    print("-" * 60)
    
    # 验证所有层级
    assert MemoryLayer.L1_CONTEXT.value == "L1_context"
    assert MemoryLayer.L2_FACT.value == "L2_fact"
    assert MemoryLayer.L3_PREFERENCE.value == "L3_preference"
    assert MemoryLayer.L4_TASK.value == "L4_task"
    assert MemoryLayer.L5_REASONING.value == "L5_reasoning"
    
    print(f"  ✅ L1_CONTEXT: {MemoryLayer.L1_CONTEXT.value}")
    print(f"  ✅ L2_FACT: {MemoryLayer.L2_FACT.value}")
    print(f"  ✅ L3_PREFERENCE: {MemoryLayer.L3_PREFERENCE.value}")
    print(f"  ✅ L4_TASK: {MemoryLayer.L4_TASK.value}")
    print(f"  ✅ L5_REASONING: {MemoryLayer.L5_REASONING.value}")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_layer_config_defaults():
    """测试 2: 层级配置默认值"""
    print("🔍 测试 2: 层级配置默认值")
    print("-" * 60)
    
    configs = MemoryLayerConfig.get_default_configs()
    
    # L1: 临时上下文
    l1_config = configs[MemoryLayer.L1_CONTEXT]
    assert l1_config.lifetime_days is not None and l1_config.lifetime_days < 1, "L1 应为会话级"
    assert l1_config.storage_strategy == "memory_cache", "L1 应使用内存缓存"
    assert l1_config.cleanup_condition == "session_end", "L1 清理条件应为 session_end"
    
    # L2: 稳定事实
    l2_config = configs[MemoryLayer.L2_FACT]
    assert l2_config.lifetime_days is None, "L2 应为永久"
    assert l2_config.compressible == False, "L2 不应压缩"
    assert l2_config.cleanup_condition == "never", "L2 清理条件应为 never"
    
    # L5: 推理过程
    l5_config = configs[MemoryLayer.L5_REASONING]
    assert l5_config.compressible == True, "L5 应可压缩"
    assert l5_config.cleanup_condition == "meditation_compress", "L5 清理条件应为 meditation_compress"
    
    print(f"  ✅ L1: lifetime={l1_config.lifetime_days}天，storage={l1_config.storage_strategy}")
    print(f"  ✅ L2: lifetime=永久，compressible={l2_config.compressible}")
    print(f"  ✅ L3: lifetime={l3_config.lifetime_days}天" if (l3_config := configs.get(MemoryLayer.L3_PREFERENCE)) else "")
    print(f"  ✅ L4: lifetime={l4_config.lifetime_days}天" if (l4_config := configs.get(MemoryLayer.L4_TASK)) else "")
    print(f"  ✅ L5: compressible={l5_config.compressible}, cleanup={l5_config.cleanup_condition}")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_memory_node_creation():
    """测试 3: 记忆节点创建"""
    print("🔍 测试 3: 记忆节点创建")
    print("-" * 60)
    
    node = MemoryNode(
        name="测试实体",
        entity_type="概念",
        description="这是一个测试",
        layer=MemoryLayer.L2_FACT
    )
    
    # 验证基本属性
    assert node.name == "测试实体"
    assert node.entity_type == "概念"
    assert node.layer == MemoryLayer.L2_FACT
    
    # 验证时间戳
    assert isinstance(node.created_at, datetime)
    assert isinstance(node.updated_at, datetime)
    
    # 验证序列化
    node_dict = node.to_dict()
    assert "name" in node_dict
    assert "layer" in node_dict
    assert node_dict["layer"] == "L2_fact"
    
    # 验证 Cypher 属性
    cypher_props = node.to_cypher_properties()
    assert "memory_layer" in cypher_props
    assert cypher_props["memory_layer"] == "L2_fact"
    
    print(f"  ✅ name: {node.name}")
    print(f"  ✅ entity_type: {node.entity_type}")
    print(f"  ✅ layer: {node.layer.value}")
    print(f"  ✅ to_dict: OK")
    print(f"  ✅ to_cypher_properties: OK")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_classify_memory():
    """测试 4: 记忆自动分类"""
    print("🔍 测试 4: 记忆自动分类")
    print("-" * 60)
    
    # 模拟 graph_store
    class MockStore:
        def execute_cypher(self, query, params=None):
            return []
    
    manager = MemoryLayerManager(MockStore())
    
    # 测试 L1: 临时上下文
    layer = manager.classify_memory("当前的对话内容")
    assert layer == MemoryLayer.L1_CONTEXT, f"应分类为 L1，实际 {layer}"
    
    # 测试 L2: 稳定事实
    layer = manager.classify_memory("用户的姓名是张三")
    assert layer == MemoryLayer.L2_FACT, f"应分类为 L2，实际 {layer}"
    
    # 测试 L3: 偏好习惯
    layer = manager.classify_memory("用户喜欢简洁的回答风格")
    assert layer == MemoryLayer.L3_PREFERENCE, f"应分类为 L3，实际 {layer}"
    
    # 测试 L4: 任务状态
    layer = manager.classify_memory("任务进度：已完成 50%")
    assert layer == MemoryLayer.L4_TASK, f"应分类为 L4，实际 {layer}"
    
    # 测试 L5: 推理过程
    layer = manager.classify_memory("因为天气不好，所以取消行程")
    assert layer == MemoryLayer.L5_REASONING, f"应分类为 L5，实际 {layer}"
    
    print(f"  ✅ L1 (临时上下文): '当前的对话内容' → {layer.value}")
    print(f"  ✅ L2 (稳定事实): '用户的姓名是张三' → L2_fact")
    print(f"  ✅ L3 (偏好习惯): '用户喜欢简洁的回答风格' → L3_preference")
    print(f"  ✅ L4 (任务状态): '任务进度：已完成 50%' → L4_task")
    print(f"  ✅ L5 (推理过程): '因为天气不好，所以取消行程' → L5_reasoning")
    print(f"  ✅ 测试通过")
    print()
    return True


def test_is_expired():
    """测试 5: 过期检查"""
    print("🔍 测试 5: 过期检查")
    print("-" * 60)
    
    configs = MemoryLayerConfig.get_default_configs()
    
    # L1: 15 分钟前创建，应过期
    l1_config = configs[MemoryLayer.L1_CONTEXT]
    l1_created = datetime.now() - timedelta(minutes=15)
    assert l1_config.is_expired(l1_created) == True, "L1 15 分钟前应过期"
    
    # L2: 永久存储，永不过期
    l2_config = configs[MemoryLayer.L2_FACT]
    l2_created = datetime.now() - timedelta(days=365)
    assert l2_config.is_expired(l2_created) == False, "L2 永不过期"
    
    # L5: 30 天前创建，应过期
    l5_config = configs[MemoryLayer.L5_REASONING]
    l5_created = datetime.now() - timedelta(days=31)
    assert l5_config.is_expired(l5_created) == True, "L5 31 天前应过期"
    
    # L5: 29 天前创建，未过期
    l5_created_recent = datetime.now() - timedelta(days=29)
    assert l5_config.is_expired(l5_created_recent) == False, "L5 29 天前未过期"
    
    print(f"  ✅ L1 (15 分钟前): expired={l1_config.is_expired(l1_created)}")
    print(f"  ✅ L2 (1 年前): expired={l2_config.is_expired(l2_created)}")
    print(f"  ✅ L5 (31 天前): expired={l5_config.is_expired(l5_created)}")
    print(f"  ✅ L5 (29 天前): expired={l5_config.is_expired(l5_created_recent)}")
    print(f"  ✅ 测试通过")
    print()
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("Issue #45: 记忆分层设计单元测试")
    print("=" * 70)
    print()
    
    tests = [
        ("记忆层级枚举", test_memory_layer_enum),
        ("层级配置默认值", test_layer_config_defaults),
        ("记忆节点创建", test_memory_node_creation),
        ("记忆自动分类", test_classify_memory),
        ("过期检查", test_is_expired)
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
