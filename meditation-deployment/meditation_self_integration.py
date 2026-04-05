#!/usr/bin/env python3
"""
与self-improving技能深度集成
实现完整的自我改进闭环
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
import shutil
import numpy as np

class SelfImprovementIntegration:
    """Self-improving技能集成"""
    
    def __init__(self, 
                 self_improving_dir: str = '/Users/liugang/.openclaw/memory/self-improving',
                 meditation_results_dir: str = '/Users/liugang/.openclaw/workspace/meditation_results'):
        """
        初始化集成器
        
        Args:
            self_improving_dir: self-improving目录
            meditation_results_dir: 冥思结果目录
        """
        self.self_improving_dir = self_improving_dir
        self.meditation_results_dir = meditation_results_dir
        
        # 确保目录存在
        os.makedirs(self.self_improving_dir, exist_ok=True)
        os.makedirs(self.meditation_results_dir, exist_ok=True)
        
        print(f"🔗 Self-improving集成器初始化")
        print(f"   Self-improving目录：{self.self_improving_dir}")
        print(f"   冥思结果目录：{self.meditation_results_dir}")
    
    def load_self_improving_memories(self) -> Dict[str, List[Dict]]:
        """加载self-improving记忆"""
        memories = {
            'errors': [],
            'corrections': [],
            'best_practices': []
        }
        
        # 加载错误记忆
        errors_file = os.path.join(self.self_improving_dir, 'errors.jsonl')
        if os.path.exists(errors_file):
            with open(errors_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        memories['errors'].append(json.loads(line))
        
        # 加载纠正记忆
        corrections_file = os.path.join(self.self_improving_dir, 'corrections.jsonl')
        if os.path.exists(corrections_file):
            with open(corrections_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        memories['corrections'].append(json.loads(line))
        
        # 加载最佳实践记忆
        best_practices_file = os.path.join(self.self_improving_dir, 'best_practices.jsonl')
        if os.path.exists(best_practices_file):
            with open(best_practices_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        memories['best_practices'].append(json.loads(line))
        
        print(f"📚 加载self-improving记忆：")
        print(f"   错误：{len(memories['errors'])}")
        print(f"   纠正：{len(memories['corrections'])}")
        print(f"   最佳实践：{len(memories['best_practices'])}")
        
        return memories
    
    def convert_to_meditation_nodes(self, memories: Dict[str, List[Dict]]) -> List[Dict]:
        """将self-improving记忆转换为冥思节点"""
        nodes = []
        current_time = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # 转换错误记忆
        for i, error in enumerate(memories['errors'], 1):
            importance = 0.9 - (i * 0.05)  # 最近的错误重要性高
            importance = max(importance, 0.1)
            
            node = {
                'id': f"error_{error.get('id', i)}",
                'content': f"错误：{error.get('description', '未知错误')}",
                'type': 'error',
                'importance': importance,
                'timestamp': error.get('timestamp', current_time),
                'vector': self._generate_error_vector(error),
                'metadata': {
                    'source': 'self-improving',
                    'category': 'error',
                    'original_data': error
                }
            }
            nodes.append(node)
        
        # 转换纠正记忆
        for i, correction in enumerate(memories['corrections'], 1):
            importance = 0.8 - (i * 0.03)
            importance = max(importance, 0.1)
            
            node = {
                'id': f"correction_{correction.get('id', i)}",
                'content': f"纠正：{correction.get('description', '未知纠正')}",
                'type': 'correction',
                'importance': importance,
                'timestamp': correction.get('timestamp', current_time),
                'vector': self._generate_correction_vector(correction),
                'metadata': {
                    'source': 'self-improving',
                    'category': 'correction',
                    'original_data': correction
                }
            }
            nodes.append(node)
        
        # 转换最佳实践记忆
        for i, practice in enumerate(memories['best_practices'], 1):
            importance = 0.7 - (i * 0.02)
            importance = max(importance, 0.1)
            
            node = {
                'id': f"practice_{practice.get('id', i)}",
                'content': f"最佳实践：{practice.get('description', '未知实践')}",
                'type': 'best_practice',
                'importance': importance,
                'timestamp': practice.get('timestamp', current_time),
                'vector': self._generate_practice_vector(practice),
                'metadata': {
                    'source': 'self-improving',
                    'category': 'best_practice',
                    'original_data': practice
                }
            }
            nodes.append(node)
        
        print(f"🔄 转换完成：{len(nodes)} 个冥思节点")
        
        return nodes
    
    def _generate_error_vector(self, error: Dict) -> List[float]:
        """为错误生成向量表示"""
        # 基于错误类型和严重程度生成向量
        severity = error.get('severity', 'medium')
        error_type = error.get('type', 'unknown')
        
        # 简单编码
        severity_mapping = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
        severity_value = severity_mapping.get(severity, 0.5)
        
        type_hash = hash(error_type) % 1000 / 1000.0
        
        vector = [severity_value, type_hash, 0.3, 0.4, 0.5]
        return vector
    
    def _generate_correction_vector(self, correction: Dict) -> List[float]:
        """为纠正生成向量表示"""
        # 基于纠正类型和有效性生成向量
        effectiveness = correction.get('effectiveness', 'medium')
        correction_type = correction.get('type', 'unknown')
        
        effectiveness_mapping = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
        effectiveness_value = effectiveness_mapping.get(effectiveness, 0.5)
        
        type_hash = hash(correction_type) % 1000 / 1000.0
        
        vector = [effectiveness_value, type_hash, 0.4, 0.5, 0.6]
        return vector
    
    def _generate_practice_vector(self, practice: Dict) -> List[float]:
        """为最佳实践生成向量表示"""
        # 基于实践类别和应用频率生成向量
        practice_category = practice.get('category', 'general')
        frequency = practice.get('frequency', 'medium')
        
        frequency_mapping = {'low': 0.2, 'medium': 0.5, 'high': 0.8}
        frequency_value = frequency_mapping.get(frequency, 0.5)
        
        category_hash = hash(practice_category) % 1000 / 1000.0
        
        vector = [frequency_value, category_hash, 0.5, 0.6, 0.7]
        return vector
    
    def sync_memories_to_meditation(self, graph_data: Optional[Dict] = None) -> Dict:
        """同步self-improving记忆到冥思系统"""
        print("🔄 开始同步self-improving记忆到冥思系统")
        
        # 加载self-improving记忆
        memories = self.load_self_improving_memories()
        
        # 转换为冥思节点
        meditation_nodes = self.convert_to_meditation_nodes(memories)
        
        # 如果提供了现有图数据，合并新节点
        if graph_data:
            # 合并节点
            existing_ids = {node['id'] for node in graph_data['nodes']}
            new_nodes = [node for node in meditation_nodes if node['id'] not in existing_ids]
            
            # 创建连接（基于相似性）
            new_edges = self._generate_edges_for_new_nodes(new_nodes, graph_data['nodes'])
            
            # 更新图数据
            updated_graph = {
                'nodes': graph_data['nodes'] + new_nodes,
                'edges': graph_data['edges'] + new_edges
            }
            
            print(f"📊 同步结果：")
            print(f"   新增节点：{len(new_nodes)}")
            print(f"   新增边：{len(new_edges)}")
            print(f"   总节点数：{len(updated_graph['nodes'])}")
            print(f"   总边数：{len(updated_graph['edges'])}")
        else:
            # 创建新的图数据
            edges = self._generate_edges_for_new_nodes(meditation_nodes, [])
            updated_graph = {
                'nodes': meditation_nodes,
                'edges': edges
            }
            
            print(f"📊 创建新图：")
            print(f"   节点数：{len(updated_graph['nodes'])}")
            print(f"   边数：{len(updated_graph['edges'])}")
        
        # 保存同步结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = os.path.join(self.meditation_results_dir, f'sync_result_{timestamp}.json')
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(updated_graph, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 同步结果已保存：{result_file}")
        
        return {
            'sync_result': updated_graph,
            'new_nodes_count': len(meditation_nodes),
            'new_edges_count': len(updated_graph['edges']),
            'result_file': result_file
        }
    
    def _generate_edges_for_new_nodes(self, new_nodes: List[Dict], existing_nodes: List[Dict]) -> List[Dict]:
        """为新节点生成连接"""
        edges = []
        
        # 计算节点之间的相似度
        all_nodes = new_nodes + existing_nodes
        
        for i, node1 in enumerate(new_nodes):
            for j, node2 in enumerate(all_nodes):
                if i == j:
                    continue
                
                # 计算余弦相似度
                vector1 = np.array(node1['vector'])
                vector2 = np.array(node2['vector'])
                
                norm1 = np.linalg.norm(vector1)
                norm2 = np.linalg.norm(vector2)
                
                if norm1 > 0 and norm2 > 0:
                    similarity = np.dot(vector1, vector2) / (norm1 * norm2)
                    
                    # 如果相似度超过阈值，创建边
                    if similarity > 0.6:
                        edge = {
                            'source': node1['id'],
                            'target': node2['id'],
                            'type': 'similar_to',
                            'weight': similarity,
                            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                        }
                        edges.append(edge)
        
        print(f"🔗 生成了 {len(edges)} 条边（相似度阈值: 0.6）")
        
        return edges

def test_self_improvement_integration():
    """测试self-improving集成"""
    print("🧪 测试self-improving集成")
    print("=" * 50)
    
    # 创建集成器
    integrator = SelfImprovementIntegration()
    
    # 测试同步
    print("\n🔄 测试记忆同步...")
    sync_result = integrator.sync_memories_to_meditation()
    
    print(f"\n✅ 集成测试完成")
    print(f"   同步文件：{sync_result['result_file']}")
    print(f"   新节点数：{sync_result['new_nodes_count']}")
    print(f"   新边数：{sync_result['new_edges_count']}")
    
    return integrator, sync_result

if __name__ == "__main__":
    import numpy as np
    integrator, sync_result = test_self_improvement_integration()
