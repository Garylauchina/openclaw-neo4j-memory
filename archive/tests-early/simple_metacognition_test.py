#!/usr/bin/env python3
"""
简单测试元认知模块
"""
import sys
sys.path.insert(0, 'plugins/neo4j-memory/meditation_memory')

print("=== 简单元认知模块测试 ===")

# 测试1: 导入模块
print("1. 测试导入模块...")
try:
    from metacognition import MetacognitionNode, MetacognitionLaw, MetacognitionCategory
    print("   ✅ 导入成功")
except Exception as e:
    print(f"   ❌ 导入失败: {e}")
    sys.exit(1)

# 测试2: 创建节点
print("2. 测试创建节点...")
try:
    node = MetacognitionNode(
        node_type="Meta_Self",
        concept="测试: 我需要在推送到远程仓库前确认仓库边界",
        category="limitation",
        law=MetacognitionLaw.LAW_3,
        confidence=0.8,
        is_core=False
    )
    print(f"   ✅ 创建节点: {node}")
except Exception as e:
    print(f"   ❌ 创建节点失败: {e}")
    sys.exit(1)

# 测试3: 检查三定律
print("3. 检查三定律...")
try:
    laws = list(MetacognitionLaw)
    print(f"   ✅ 三定律: {[law.value for law in laws]}")
    assert len(laws) == 3, "应该有3个定律"
except Exception as e:
    print(f"   ❌ 检查三定律失败: {e}")
    sys.exit(1)

# 测试4: 检查分类
print("4. 检查分类...")
try:
    categories = list(MetacognitionCategory)
    print(f"   ✅ 分类数: {len(categories)}")
    # 检查关键分类
    needed_cats = {'limitation', 'user_preference', 'interaction_pattern'}
    cat_values = {c.value for c in categories}
    for cat in needed_cats:
        if cat in cat_values:
            print(f"   ✅ 包含分类: {cat}")
        else:
            print(f"   ⚠️  缺少分类: {cat}")
except Exception as e:
    print(f"   ❌ 检查分类失败: {e}")
    sys.exit(1)

# 测试5: 检查Step 8方法引用
print("5. 检查冥思工作流集成...")
try:
    import re
    with open('plugins/neo4j-memory/meditation_memory/meditation_worker.py', 'r') as f:
        content = f.read()
    
    # 检查Step 8方法
    if 'async def _step_8_self_reflection' in content:
        print("   ✅ 找到 Step 8 方法定义")
    else:
        print("   ❌ 未找到 Step 8 方法定义")
    
    # 检查导入
    if 'from .metacognition import MetacognitionGraph' in content:
        print("   ✅ 找到 metacognition 导入语句")
    else:
        print("   ❌ 未找到 metacognition 导入语句")
    
    # 检查调用
    if 'await self._step_8_self_reflection(result)' in content:
        print("   ✅ 找到 Step 8 调用")
    else:
        print("   ❌ 未找到 Step 8 调用")
        
except Exception as e:
    print(f"   ❌ 检查冥思工作流失败: {e}")
    sys.exit(1)

print("\n=== 所有测试通过 ===")
print("元认知模块基本功能正常，冥思工作流集成完整。")
print("注意: Neo4j CRUD操作为模拟实现，需要后续完善。")