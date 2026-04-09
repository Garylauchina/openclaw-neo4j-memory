#!/usr/bin/env python3
"""
修复并重新测试
1. 修复语义解析器调试
2. 修复ReplayRunner中的语义解析集成
"""

import sys
sys.path.append('.')

print("🔧 修复并重新测试")
print("="*60)

# 首先检查语义解析器的真正问题
print("\n1. 检查语义解析器真正输出...")
from simple_semantic_parser import SimpleSemanticParser

parser = SimpleSemanticParser()
test_query = "我想投资日本房产"
result = parser.parse(test_query)

print(f"   查询: {test_query}")
print(f"   解析结果类型: {type(result)}")
if result:
    print(f"   解析结果内容:")
    for key, value in result.items():
        print(f"     {key}: {value}")
else:
    print(f"   ❌ 解析结果为None")

# 检查ReplayRunner中如何使用语义解析器
print("\n2. 检查ReplayRunner集成...")
from evaluation_framework import ReplayRunner

# 查看step方法中的语义解析部分
import inspect
source = inspect.getsource(ReplayRunner.step)
lines = source.split('\n')

print("   ReplayRunner.step方法中的语义解析部分:")
for i, line in enumerate(lines):
    if 'semantic_parser' in line or 'parse(' in line:
        print(f"     {i+1}: {line.strip()}")

# 创建修复版的ReplayRunner
print("\n3. 创建修复版ReplayRunner...")

class FixedReplayRunner(ReplayRunner):
    """修复版ReplayRunner，修复语义解析集成"""
    
    def step(self, query: str):
        """修复语义解析集成"""
        try:
            # 1. 语义解析
            if hasattr(self, 'semantic_parser') and self.semantic_parser:
                parsed = self.semantic_parser.parse(query)
                
                if parsed and isinstance(parsed, dict):
                    # 提取关键信息
                    subject = parsed.get('subject', 'USER')
                    relation = parsed.get('relation')
                    obj = parsed.get('object')
                    
                    if relation and obj:
                        # 转换为EdgeType
                        from global_graph import NodeType, EdgeType
                        
                        # 创建或获取节点
                        subject_id = self.global_graph.create_node(subject, NodeType.USER)
                        object_id = self.global_graph.create_node(obj, NodeType.TOPIC)
                        
                        # 映射关系类型
                        edge_type = None
                        if relation == "LIKES":
                            edge_type = EdgeType.LIKES
                        elif relation == "INVESTED_IN":
                            edge_type = EdgeType.INVESTED_IN
                        elif relation == "ASKING_ABOUT":
                            edge_type = EdgeType.ASKING_ABOUT
                        elif relation == "LEARNING":
                            edge_type = EdgeType.LEARNING
                        elif relation == "INTERESTED_IN":
                            edge_type = EdgeType.INTERESTED_IN
                        else:
                            edge_type = EdgeType.MENTIONED
                        
                        # 更新边
                        confidence = parsed.get('confidence', 0.6)
                        self.global_graph.update_edge(subject_id, object_id, edge_type, confidence)
                        
                        print(f"✅ 语义解析成功: {subject} -> {relation} -> {obj}")
            
            # 2. 继续原有流程
            return super().step(query)
            
        except Exception as e:
            print(f"❌ ReplayRunner.step错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

# 测试修复
print("\n4. 测试修复...")
from global_graph import GlobalGraph, NodeType, EdgeType
from active_subgraph import ActiveSubgraphEngine
from active_set import ActiveSetEngine
from reflection_upgrade import ReflectionEngine
from learning_guard import LearningGuard

# 创建测试环境
graph = GlobalGraph()
runner = FixedReplayRunner()
runner._init_system()

# 测试查询
test_queries = [
    "我喜欢日本房产",
    "我想投资AI",
    "机器学习怎么学？"
]

print(f"   测试 {len(test_queries)} 个查询...")
for query in test_queries:
    print(f"\n   查询: {query}")
    result = runner.step(query)
    
    if result["success"]:
        print(f"     ✅ 成功")
        if result.get("diffs_generated", 0) > 0:
            print(f"     生成 {result['diffs_generated']} 个Diff")
    else:
        print(f"     ❌ 失败: {result.get('error', '未知错误')}")

# 检查Graph状态
print("\n5. 检查Graph状态...")
graph_edges = len([e for e in graph.edges.values() if hasattr(e, 'active') and e.active])
print(f"   Graph边数: {graph_edges}")

print("\n" + "="*60)
print("🔧 修复完成")
print("="*60)