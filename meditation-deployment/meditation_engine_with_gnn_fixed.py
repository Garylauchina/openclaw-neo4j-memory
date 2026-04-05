#!/usr/bin/env python3
"""
修复后的冥思引擎 - 修复时间戳处理问题
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import math
import re

class MemoryNode:
    """记忆节点类 - 修复时间戳处理"""
    def __init__(self, node_data: Dict):
        self.id = node_data.get('id', '')
        self.content = node_data.get('content', '')
        self.type = node_data.get('type', 'unknown')
        self.importance = node_data.get('importance', 0.5)
        
        # 修复时间戳处理
        timestamp_str = node_data.get('timestamp', '2026-01-01T00:00:00Z')
        # 清理时间戳字符串
        timestamp_str = timestamp_str.replace('+00:00+00:00', '+00:00')
        timestamp_str = timestamp_str.replace('++', '+')
        
        try:
            if timestamp_str.endswith('Z'):
                self.timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif '+' in timestamp_str:
                self.timestamp = datetime.fromisoformat(timestamp_str)
            else:
                # 如果没有时区信息，假设为UTC
                self.timestamp = datetime.fromisoformat(timestamp_str + '+00:00')
        except ValueError as e:
            print(f"⚠️  时间戳解析错误：{timestamp_str} - {e}")
            self.timestamp = datetime.fromisoformat('2026-01-01T00:00:00+00:00')
        
        self.vector = np.array(node_data.get('vector', [0.0, 0.0, 0.0, 0.0, 0.0]))
        self.connections = []
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'importance': self.importance,
            'timestamp': self.timestamp.isoformat().replace('+00:00', 'Z'),
            'vector': self.vector.tolist()
        }
    
    def __repr__(self) -> str:
        return f"MemoryNode(id={self.id}, type={self.type}, importance={self.importance})"

# 其他类保持不变，直接复制
class MemoryEdge:
    """记忆连接边类"""
    def __init__(self, edge_data: Dict):
        self.source = edge_data.get('source', '')
        self.target = edge_data.get('target', '')
        self.type = edge_data.get('type', 'related_to')
        self.weight = edge_data.get('weight', 0.5)
        
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'source': self.source,
            'target': self.target,
            'type': self.type,
            'weight': self.weight
        }
    
    def __repr__(self) -> str:
        return f"MemoryEdge({self.source} -> {self.target}, type={self.type}, weight={self.weight})"

class MemoryGraph:
    """记忆图类"""
    def __init__(self):
        self.nodes: Dict[str, MemoryNode] = {}
        self.edges: List[MemoryEdge] = []
        
    def add_node(self, node_data: Dict) -> MemoryNode:
        """添加节点"""
        node = MemoryNode(node_data)
        self.nodes[node.id] = node
        return node
    
    def add_edge(self, edge_data: Dict) -> MemoryEdge:
        """添加边"""
        edge = MemoryEdge(edge_data)
        self.edges.append(edge)
        return edge
    
    def load_from_json(self, filepath: str):
        """从JSON文件加载图"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 加载节点
        for node_data in data.get('nodes', []):
            self.add_node(node_data)
            
        # 加载边
        for edge_data in data.get('edges', []):
            self.add_edge(edge_data)
            
        print(f"✅ 加载完成：{len(self.nodes)} 个节点，{len(self.edges)} 条边")
    
    def save_to_json(self, filepath: str):
        """保存图到JSON文件"""
        data = {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"✅ 保存完成：{filepath}")
    
    def get_node(self, node_id: str) -> Optional[MemoryNode]:
        """获取节点"""
        return self.nodes.get(node_id)
    
    def get_edges_for_node(self, node_id: str) -> List[MemoryEdge]:
        """获取节点的所有边"""
        return [edge for edge in self.edges if edge.source == node_id or edge.target == node_id]
    
    def remove_node(self, node_id: str):
        """移除节点及其相关边"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            # 移除相关边
            self.edges = [edge for edge in self.edges 
                         if edge.source != node_id and edge.target != node_id]
    
    def merge_nodes(self, node1_id: str, node2_id: str, new_id: str) -> MemoryNode:
        """合并两个节点"""
        node1 = self.get_node(node1_id)
        node2 = self.get_node(node2_id)
        
        if not node1 or not node2:
            raise ValueError(f"节点不存在：{node1_id} 或 {node2_id}")
        
        # 创建新节点（合并内容）
        new_content = f"{node1.content}\n---\n{node2.content}"
        new_importance = max(node1.importance, node2.importance)
        new_timestamp = max(node1.timestamp, node2.timestamp)
        
        # 合并向量（加权平均）
        weight1 = node1.importance / (node1.importance + node2.importance)
        weight2 = node2.importance / (node1.importance + node2.importance)
        new_vector = node1.vector * weight1 + node2.vector * weight2
        
        new_node_data = {
            'id': new_id,
            'content': new_content,
            'type': node1.type,  # 使用第一个节点的类型
            'importance': new_importance,
            'timestamp': new_timestamp.isoformat().replace('+00:00', 'Z'),
            'vector': new_vector.tolist()
        }
        
        new_node = self.add_node(new_node_data)
        
        # 处理边：重定向到新节点
        for edge in self.edges[:]:  # 使用副本遍历
            if edge.source == node1_id or edge.source == node2_id:
                edge.source = new_id
            if edge.target == node1_id or edge.target == node2_id:
                edge.target = new_id
        
        # 移除旧节点
        self.remove_node(node1_id)
        self.remove_node(node2_id)
        
        return new_node

class SimilarityCalculator:
    """相似度计算器"""
    
    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    @staticmethod
    def text_overlap(text1: str, text2: str) -> float:
        """计算文本重叠度（简化版）"""
        # 清理文本
        text1 = re.sub(r'[^\w\s]', ' ', text1.lower())
        text2 = re.sub(r'[^\w\s]', ' ', text2.lower())
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union
    
    @staticmethod
    def connection_similarity(graph: 'MemoryGraph', node1_id: str, node2_id: str) -> float:
        """计算连接相似度"""
        edges1 = graph.get_edges_for_node(node1_id)
        edges2 = graph.get_edges_for_node(node2_id)
        
        if not edges1 and not edges2:
            return 0.5  # 都没有连接时返回中性值
            
        # 计算连接类型的相似度
        types1 = set(edge.type for edge in edges1)
        types2 = set(edge.type for edge in edges2)
        
        if not types1 or not types2:
            return 0.0
            
        intersection = len(types1.intersection(types2))
        union = len(types1.union(types2))
        
        return intersection / union
    
    @staticmethod
    def calculate_overall_similarity(graph: 'MemoryGraph', node1_id: str, node2_id: str) -> float:
        """计算总体相似度"""
        node1 = graph.get_node(node1_id)
        node2 = graph.get_node(node2_id)
        
        if not node1 or not node2:
            return 0.0
        
        # 向量相似度（70%）
        vector_sim = SimilarityCalculator.cosine_similarity(node1.vector, node2.vector)
        
        # 文本重叠度（20%）
        text_sim = SimilarityCalculator.text_overlap(node1.content, node2.content)
        
        # 连接相似度（10%）
        conn_sim = SimilarityCalculator.connection_similarity(graph, node1_id, node2_id)
        
        # 加权计算
        overall_sim = (vector_sim * 0.7) + (text_sim * 0.2) + (conn_sim * 0.1)
        
        return overall_sim

class MeditationEngine:
    """冥思引擎主类"""
    
    def __init__(self, graph: MemoryGraph):
        self.graph = graph
        self.similarity_calc = SimilarityCalculator()
        self.merge_threshold = 0.75  # 降低阈值
        self.merge_counter = 0
        
    def find_similar_nodes(self) -> List[Tuple[str, str, float]]:
        """查找相似节点对"""
        similar_pairs = []
        node_ids = list(self.graph.nodes.keys())
        
        print(f"🔍 正在分析 {len(node_ids)} 个节点的相似度...")
        
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                node1_id = node_ids[i]
                node2_id = node_ids[j]
                
                similarity = self.similarity_calc.calculate_overall_similarity(
                    self.graph, node1_id, node2_id
                )
                
                if similarity >= self.merge_threshold:
                    similar_pairs.append((node1_id, node2_id, similarity))
        
        # 按相似度排序
        similar_pairs.sort(key=lambda x: x[2], reverse=True)
        
        return similar_pairs
    
    def apply_rule1_similar_node_merge(self) -> Dict:
        """应用规则1：相似节点合并"""
        print("🔍 开始应用规则1：相似节点合并")
        
        # 查找相似节点
        similar_pairs = self.find_similar_nodes()
        
        if not similar_pairs:
            print("✅ 未找到需要合并的相似节点")
            return {'merged_count': 0, 'details': []}
        
        print(f"📊 找到 {len(similar_pairs)} 对相似节点（阈值：{self.merge_threshold}）")
        
        merged_details = []
        merged_count = 0
        
        # 合并相似节点
        for node1_id, node2_id, similarity in similar_pairs:
            # 检查节点是否还存在（可能已被前面的合并操作移除）
            if node1_id not in self.graph.nodes or node2_id not in self.graph.nodes:
                continue
                
            # 生成新节点ID
            new_id = f"merged_{self.merge_counter:03d}"
            self.merge_counter += 1
            
            # 执行合并
            try:
                new_node = self.graph.merge_nodes(node1_id, node2_id, new_id)
                
                merged_details.append({
                    'node1': node1_id,
                    'node2': node2_id,
                    'new_node': new_id,
                    'similarity': similarity,
                    'new_importance': new_node.importance
                })
                
                merged_count += 1
                print(f"✅ 合并：{node1_id} + {node2_id} → {new_id} (相似度: {similarity:.3f})")
                
            except Exception as e:
                print(f"❌ 合并失败：{node1_id} + {node2_id} - {str(e)}")
        
        print(f"🎯 规则1完成：合并了 {merged_count} 对节点")
        
        return {
            'merged_count': merged_count,
            'details': merged_details,
            'remaining_nodes': len(self.graph.nodes),
            'remaining_edges': len(self.graph.edges)
        }
    
    def run_meditation(self) -> Dict:
        """运行完整冥思过程"""
        print("=" * 50)
        print("🧠 开始冥思优化过程")
        print("=" * 50)
        
        # 记录优化前状态
        initial_state = {
            'nodes': len(self.graph.nodes),
            'edges': len(self.graph.edges)
        }
        
        print(f"📊 优化前：{initial_state['nodes']} 个节点，{initial_state['edges']} 条边")
        
        # 应用规则1
        rule1_result = self.apply_rule1_similar_node_merge()
        
        # 计算优化效果
        final_state = {
            'nodes': len(self.graph.nodes),
            'edges': len(self.graph.edges)
        }
        
        optimization_effect = {
            'nodes_reduced': initial_state['nodes'] - final_state['nodes'],
            'edges_reduced': initial_state['edges'] - final_state['edges'],
            'reduction_rate_nodes': (initial_state['nodes'] - final_state['nodes']) / initial_state['nodes'] if initial_state['nodes'] > 0 else 0,
            'reduction_rate_edges': (initial_state['edges'] - final_state['edges']) / initial_state['edges'] if initial_state['edges'] > 0 else 0
        }
        
        print("=" * 50)
        print("📈 冥思优化结果：")
        print(f"  节点数量：{initial_state['nodes']} → {final_state['nodes']} (减少 {optimization_effect['nodes_reduced']})")
        print(f"  边数量：{initial_state['edges']} → {final_state['edges']} (减少 {optimization_effect['edges_reduced']})")
        print(f"  节点减少率：{optimization_effect['reduction_rate_nodes']:.2%}")
        print(f"  边减少率：{optimization_effect['reduction_rate_edges']:.2%}")
        print("=" * 50)
        
        return {
            'initial_state': initial_state,
            'final_state': final_state,
            'optimization_effect': optimization_effect,
            'rule1_result': rule1_result
        }


    def apply_rule2_low_importance_cleanup(self, importance_threshold=0.1, days_threshold=30) -> Dict:
        """应用规则2：低重要性节点清理"""
        print("🔍 开始应用规则2：低重要性节点清理")
        
        from datetime import datetime, timezone
        current_time = datetime.now(timezone.utc)
        nodes_to_clean = []
        
        # 分析需要清理的节点
        for node_id, node in list(self.graph.nodes.items()):
            # 计算天数差
            days_diff = (current_time - node.timestamp).days
            
            # 检查清理条件
            if (node.importance < importance_threshold and 
                days_diff > days_threshold):
                
                nodes_to_clean.append({
                    'id': node_id,
                    'node': node,
                    'days_since_access': days_diff
                })
                print(f"  ✓ 标记清理：{node_id} (重要性: {node.importance:.2f}, {days_diff}天前)")
        
        if not nodes_to_clean:
            print("✅ 没有需要清理的低重要性节点")
            return {'cleaned_count': 0, 'details': []}
        
        print(f"📊 找到 {len(nodes_to_clean)} 个低重要性节点需要清理")
        
        cleaned_details = []
        
        # 执行清理
        for item in nodes_to_clean:
            node_id = item['id']
            node = item['node']
            
            # 从图中移除节点（边会自动清理）
            self.graph.remove_node(node_id)
            
            cleaned_details.append({
                'node_id': node_id,
                'content': node.content[:50] + '...',
                'type': node.type,
                'importance': node.importance,
                'days_since_access': item['days_since_access'],
                'timestamp': node.timestamp.isoformat()
            })
            
            print(f"✅ 清理：{node_id} (重要性: {node.importance:.2f}, {item['days_since_access']}天前)")
        
        print(f"🎯 规则2完成：清理了 {len(nodes_to_clean)} 个低重要性节点")
        
        return {
            'cleaned_count': len(nodes_to_clean),
            'details': cleaned_details,
            'remaining_nodes': len(self.graph.nodes),
            'remaining_edges': len(self.graph.edges)
        }


    def apply_rule5_time_decay_adjustment(self, decay_rate=0.01, min_weight=0.01) -> Dict:
        """应用规则5：时间衰减权重调整"""
        print("🔧 开始应用规则5：时间衰减权重调整")
        
        from datetime import datetime, timezone
        import math
        
        reference_time = datetime.now(timezone.utc)
        adjustment_log = []
        total_adjusted = 0
        total_decay = 0.0
        
        for node_id, node in self.graph.nodes.items():
            # 计算天数差
            days = (reference_time - node.timestamp).days
            
            # 计算衰减因子：e^(-λ * days)
            decay_factor = math.exp(-decay_rate * days)
            decay_factor = max(decay_factor, min_weight)
            
            # 保存原始权重
            original_weight = node.importance
            
            # 应用衰减
            new_weight = original_weight * decay_factor
            
            # 确保不低于最小权重
            if new_weight < min_weight:
                new_weight = min_weight
            
            # 记录调整
            if new_weight != original_weight:
                weight_change = new_weight - original_weight
                weight_change_percent = (weight_change / original_weight * 100) if original_weight > 0 else 0
                
                adjustment_log.append({
                    'node_id': node_id,
                    'original_weight': original_weight,
                    'new_weight': new_weight,
                    'weight_change': weight_change,
                    'weight_change_percent': weight_change_percent,
                    'days_since_creation': days,
                    'decay_factor': decay_factor
                })
                
                total_adjusted += 1
                total_decay += weight_change
                
                # 更新节点权重
                node.importance = new_weight
        
        print(f"📊 调整了 {total_adjusted} 个节点的权重")
        print(f"   总权重衰减：{total_decay:.4f}")
        
        if total_adjusted > 0:
            avg_decay = total_decay / total_adjusted
            print(f"   平均权重变化：{avg_decay:.4f}")
        
        print(f"🎯 规则5完成：时间衰减权重调整")
        
        return {
            'adjusted_count': total_adjusted,
            'total_decay': total_decay,
            'adjustment_log': adjustment_log,
            'decay_rate': decay_rate,
            'min_weight': min_weight
        }



def main():
    """主函数"""
    print("🧠 修复后的冥思引擎启动")
    
    # 1. 加载测试图
    graph = MemoryGraph()
    test_file = '/Users/liugang/.openclaw/workspace/test_memory_graph_with_similar.json'
    graph.load_from_json(test_file)
    
    # 2. 创建冥思引擎
    engine = MeditationEngine(graph)
    
    # 3. 运行冥思
    result = engine.run_meditation()
    
    # 4. 保存优化后的图
    output_file = '/Users/liugang/.openclaw/workspace/test_memory_graph_optimized_final.json'
    graph.save_to_json(output_file)
    
    # 5. 输出详细结果
    if result['rule1_result']['details']:
        print("\n📋 详细合并记录：")
        for detail in result['rule1_result']['details']:
            print(f"  • {detail['node1']} + {detail['node2']} → {detail['new_node']}")
            print(f"    相似度：{detail['similarity']:.3f}")
            print(f"    新重要性：{detail['new_importance']:.2f}")
    else:
        print("\n⚠️  没有节点被合并")
    
    print(f"\n✅ 冥思完成！优化后的图已保存到：{output_file}")
    
    return result

if __name__ == "__main__":
    main()



    def run_complete_meditation_workflow(self) -> Dict:
        """运行完整的冥思工作流程"""
        print("=" * 60)
        print("🧠 开始完整的冥思优化工作流程")
        print("=" * 60)
        
        # 记录初始状态
        initial_state = {
            'nodes': len(self.graph.nodes),
            'edges': len(self.graph.edges),
            'total_importance': sum(node.importance for node in self.graph.nodes.values())
        }
        
        print(f"📊 初始状态：{initial_state['nodes']} 个节点，{initial_state['edges']} 条边")
        print(f"   总重要性：{initial_state['total_importance']:.2f}")
        
        results = {}
        
        # 阶段1：规则5 - 时间衰减权重调整
        print("\n" + "-" * 40)
        print("阶段1：时间衰减权重调整")
        print("-" * 40)
        results['rule5'] = self.apply_rule5_time_decay_adjustment(
            decay_rate=0.01,
            min_weight=0.05
        )
        
        # 阶段2：规则2 - 低重要性节点清理
        print("\n" + "-" * 40)
        print("阶段2：低重要性节点清理")
        print("-" * 40)
        results['rule2'] = self.apply_rule2_low_importance_cleanup(
            importance_threshold=0.1,
            days_threshold=30
        )
        
        # 阶段3：规则1 - 相似节点合并
        print("\n" + "-" * 40)
        print("阶段3：相似节点合并")
        print("-" * 40)
        results['rule1'] = self.apply_rule1_similar_node_merge()
        
        # 记录最终状态
        final_state = {
            'nodes': len(self.graph.nodes),
            'edges': len(self.graph.edges),
            'total_importance': sum(node.importance for node in self.graph.nodes.values())
        }
        
        # 计算优化效果
        optimization_effect = {
            'nodes_reduced': initial_state['nodes'] - final_state['nodes'],
            'edges_reduced': initial_state['edges'] - final_state['edges'],
            'importance_reduced': initial_state['total_importance'] - final_state['total_importance'],
            'reduction_rate_nodes': (initial_state['nodes'] - final_state['nodes']) / initial_state['nodes'] if initial_state['nodes'] > 0 else 0,
            'reduction_rate_edges': (initial_state['edges'] - final_state['edges']) / initial_state['edges'] if initial_state['edges'] > 0 else 0,
            'reduction_rate_importance': (initial_state['total_importance'] - final_state['total_importance']) / initial_state['total_importance'] if initial_state['total_importance'] > 0 else 0
        }
        
        print("\n" + "=" * 60)
        print("📈 完整的冥思优化结果")
        print("=" * 60)
        print(f"  节点数量：{initial_state['nodes']} → {final_state['nodes']} (减少 {optimization_effect['nodes_reduced']})")
        print(f"  边数量：{initial_state['edges']} → {final_state['edges']} (减少 {optimization_effect['edges_reduced']})")
        print(f"  总重要性：{initial_state['total_importance']:.2f} → {final_state['total_importance']:.2f} (减少 {optimization_effect['importance_reduced']:.2f})")
        print(f"  节点减少率：{optimization_effect['reduction_rate_nodes']:.2%}")
        print(f"  边减少率：{optimization_effect['reduction_rate_edges']:.2%}")
        print(f"  重要性减少率：{optimization_effect['reduction_rate_importance']:.2%}")
        print("=" * 60)
        
        # 汇总各规则效果
        print("\n📋 各规则执行效果：")
        print(f"  规则5（时间衰减）：调整了 {results['rule5']['adjusted_count']} 个节点的权重")
        print(f"  规则2（低重要性清理）：清理了 {results['rule2']['cleaned_count']} 个节点")
        print(f"  规则1（相似节点合并）：合并了 {results['rule1']['merged_count']} 对节点")
        
        return {
            'initial_state': initial_state,
            'final_state': final_state,
            'optimization_effect': optimization_effect,
            'rule_results': results
        }



    def apply_gnn_meditation_rule(self, gnn_model_path: str = None) -> Dict:
        """应用GNN冥思规则（深度学习增强）"""
        print("🧠 开始应用GNN冥思规则（深度学习增强）")
        
        try:
            # 导入GNN模块
            from gnn_meditation_rule import GNNMeditationRule
            
            # 创建或加载GNN模型
            gnn_rule = GNNMeditationRule(
                input_dim=128,
                hidden_dim=64,
                output_dim=32,
                learning_rate=0.001
            )
            
            if gnn_model_path:
                gnn_rule.load_model(gnn_model_path)
                print(f"✅ 已加载预训练GNN模型: {gnn_model_path}")
            else:
                print("⚠️  使用未训练的GNN模型，建议先训练模型")
            
            # 将图数据转换为GNN可处理格式
            graph_data = self.graph.to_dict()
            
            # 应用GNN冥思
            gnn_result = gnn_rule.apply_gnn_meditation(graph_data)
            
            # 执行GNN建议（简化版本）
            executed_suggestions = []
            cleaned_count = 0
            merge_marked_count = 0
            
            for suggestion in gnn_result['suggestions']:
                if suggestion['suggestion'] == 'clean' and suggestion['confidence'] > 0.7:
                    # 清理低重要性节点
                    if suggestion['node_id'] in self.graph.nodes:
                        self.graph.remove_node(suggestion['node_id'])
                        executed_suggestions.append({
                            'node_id': suggestion['node_id'],
                            'action': 'cleaned',
                            'confidence': suggestion['confidence']
                        })
                        cleaned_count += 1
                
                elif suggestion['suggestion'] == 'merge' and suggestion['confidence'] > 0.6:
                    # 标记为需要合并
                    executed_suggestions.append({
                        'node_id': suggestion['node_id'],
                        'action': 'marked_for_merge',
                        'confidence': suggestion['confidence']
                    })
                    merge_marked_count += 1
            
            print(f"📊 GNN冥思执行结果：")
            print(f"   处理了 {len(executed_suggestions)} 个节点")
            print(f"   清理了 {cleaned_count} 个节点")
            print(f"   标记了 {merge_marked_count} 个节点待合并")
            
            return {
                'gnn_suggestions': gnn_result['suggestions'],
                'executed_actions': executed_suggestions,
                'total_nodes_before': len(graph_data['nodes']),
                'total_nodes_after': len(self.graph.nodes),
                'average_confidence': gnn_result['average_confidence'],
                'cleaned_count': cleaned_count,
                'merge_marked_count': merge_marked_count
            }
            
        except ImportError as e:
            print(f"❌ GNN模块导入失败: {e}")
            print("   请确保已安装torch和torch_geometric")
            return {'error': 'GNN模块不可用', 'details': str(e)}
        except Exception as e:
            print(f"❌ GNN冥思执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {'error': 'GNN冥思执行失败', 'details': str(e)}
