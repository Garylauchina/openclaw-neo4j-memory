#!/usr/bin/env python3
"""
GNN冥思规则：基于图神经网络的深度学习冥思
使用GNN学习图结构特征，实现智能优化
"""

import json
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv
from torch_geometric.data import Data
import networkx as nx

class GNNMeditationRule:
    """GNN冥思规则：基于图神经网络的深度学习优化"""
    
    def __init__(self, 
                 input_dim: int = 128,
                 hidden_dim: int = 64,
                 output_dim: int = 32,
                 learning_rate: float = 0.001):
        """
        初始化GNN冥思规则
        
        Args:
            input_dim: 输入特征维度
            hidden_dim: 隐藏层维度
            output_dim: 输出特征维度
            learning_rate: 学习率
        """
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.learning_rate = learning_rate
        
        # 初始化GNN模型
        self.model = self._build_gnn_model()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # 训练历史
        self.training_history = []
        
        print(f"🧠 GNN冥思规则初始化完成")
        print(f"   输入维度: {input_dim}, 隐藏维度: {hidden_dim}, 输出维度: {output_dim}")
        print(f"   学习率: {learning_rate}")
    
    def _build_gnn_model(self) -> nn.Module:
        """构建GNN模型"""
        class GNNMeditationModel(nn.Module):
            def __init__(self, input_dim, hidden_dim, output_dim):
                super().__init__()
                # 图卷积层
                self.conv1 = GCNConv(input_dim, hidden_dim)
                self.conv2 = GCNConv(hidden_dim, hidden_dim)
                self.conv3 = GCNConv(hidden_dim, output_dim)
                
                # 注意力层
                self.attention = GATConv(hidden_dim, hidden_dim, heads=2, concat=False)
                
                # 全连接层
                self.fc1 = nn.Linear(output_dim, 32)
                self.fc2 = nn.Linear(32, 16)
                self.fc3 = nn.Linear(16, 3)  # 3个输出：合并、清理、保留概率
                
                # Dropout
                self.dropout = nn.Dropout(0.3)
                
            def forward(self, x, edge_index):
                # 图卷积
                x = self.conv1(x, edge_index)
                x = F.relu(x)
                x = self.dropout(x)
                
                x = self.conv2(x, edge_index)
                x = F.relu(x)
                
                # 注意力机制
                x = self.attention(x, edge_index)
                x = F.relu(x)
                x = self.dropout(x)
                
                x = self.conv3(x, edge_index)
                x = F.relu(x)
                
                # 全局池化
                x = torch.mean(x, dim=0, keepdim=True)
                
                # 全连接层
                x = self.fc1(x)
                x = F.relu(x)
                x = self.dropout(x)
                
                x = self.fc2(x)
                x = F.relu(x)
                
                x = self.fc3(x)
                x = F.softmax(x, dim=1)
                
                return x
        
        return GNNMeditationModel(self.input_dim, self.hidden_dim, self.output_dim)
    
    def prepare_graph_data(self, graph_data: Dict) -> Tuple[torch.Tensor, torch.Tensor, List]:
        """准备图数据供GNN训练"""
        nodes = graph_data['nodes']
        edges = graph_data['edges']
        
        # 提取节点特征
        node_features = []
        node_ids = []
        
        for node in nodes:
            # 基础特征：重要性、时间衰减、连接度
            importance = node['importance']
            
            # 时间衰减特征
            timestamp_str = node['timestamp']
            if timestamp_str.endswith('Z'):
                node_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
            else:
                node_time = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
            
            days_diff = (datetime.now(timezone.utc) - node_time).days
            time_feature = np.exp(-0.01 * days_diff)  # 时间衰减
            
            # 向量特征（取前5维，不足补0）
            vector = node.get('vector', [0.0] * 5)
            vector_features = vector[:5] + [0.0] * (5 - len(vector[:5]))
            
            # 组合特征
            features = [importance, time_feature] + vector_features
            
            # 添加文本特征（简单编码）
            content = node['content']
            text_length = min(len(content) / 100, 1.0)  # 归一化文本长度
            features.append(text_length)
            
            # 类型特征
            type_mapping = {
                'preference': 0.1,
                'knowledge': 0.2,
                'correction': 0.3,
                'error': 0.4,
                'best_practice': 0.5,
                'test': 0.6,
                'demo': 0.7,
                'outdated': 0.8
            }
            node_type = node.get('type', 'unknown')
            type_feature = type_mapping.get(node_type, 0.9)
            features.append(type_feature)
            
            # 填充到固定维度
            while len(features) < self.input_dim:
                features.append(0.0)
            features = features[:self.input_dim]
            
            node_features.append(features)
            node_ids.append(node['id'])
        
        # 创建边索引
        edge_index = []
        node_id_to_idx = {node_id: idx for idx, node_id in enumerate(node_ids)}
        
        for edge in edges:
            source_idx = node_id_to_idx.get(edge['source'])
            target_idx = node_id_to_idx.get(edge['target'])
            
            if source_idx is not None and target_idx is not None:
                edge_index.append([source_idx, target_idx])
        
        # 转换为PyTorch张量
        x = torch.tensor(node_features, dtype=torch.float)
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        
        return x, edge_index, node_ids
    
    def train_on_graph(self, graph_data: Dict, epochs: int = 50) -> Dict:
        """在图上训练GNN模型"""
        print(f"🧠 开始GNN训练，epochs: {epochs}")
        
        # 准备数据
        x, edge_index, node_ids = self.prepare_graph_data(graph_data)
        
        print(f"📊 训练数据：{len(node_ids)} 个节点，{edge_index.shape[1]} 条边")
        
        # 创建训练标签（模拟标签，实际应用中需要真实标签）
        # 这里使用启发式方法生成模拟标签
        num_nodes = len(node_ids)
        labels = torch.zeros(num_nodes, 3)  # 3个类别：合并、清理、保留
        
        for i, node_id in enumerate(node_ids):
            # 基于节点特征生成模拟标签
            importance = x[i, 0].item()
            time_feature = x[i, 1].item()
            
            # 启发式标签生成
            if importance < 0.1 and time_feature < 0.3:
                labels[i, 1] = 1.0  # 清理
            elif importance > 0.7 and time_feature > 0.7:
                labels[i, 2] = 1.0  # 保留
            else:
                labels[i, 0] = 1.0  # 合并
        
        # 训练循环
        self.model.train()
        losses = []
        
        for epoch in range(epochs):
            self.optimizer.zero_grad()
            
            # 前向传播
            outputs = self.model(x, edge_index)
            
            # 计算损失（使用交叉熵损失）
            # 扩展outputs以匹配labels的形状
            outputs_expanded = outputs.repeat(num_nodes, 1)
            loss = F.cross_entropy(outputs_expanded, torch.argmax(labels, dim=1))
            
            # 反向传播
            loss.backward()
            self.optimizer.step()
            
            losses.append(loss.item())
            
            if (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
        
        # 保存训练历史
        self.training_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'epochs': epochs,
            'final_loss': losses[-1],
            'node_count': len(node_ids),
            'edge_count': edge_index.shape[1]
        })
        
        print(f"✅ GNN训练完成，最终损失: {losses[-1]:.4f}")
        
        return {
            'training_losses': losses,
            'node_ids': node_ids,
            'final_loss': losses[-1]
        }
    
    def apply_gnn_meditation(self, graph_data: Dict) -> Dict:
        """应用GNN冥思规则"""
        print("🧠 开始应用GNN冥思规则")
        
        # 准备数据
        x, edge_index, node_ids = self.prepare_graph_data(graph_data)
        
        # 模型预测
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(x, edge_index)
        
        # 解析预测结果
        predictions = outputs.squeeze().tolist()
        
        # 生成优化建议
        optimization_suggestions = []
        
        for i, node_id in enumerate(node_ids):
            pred_probs = predictions  # 对于所有节点相同的预测
            
            # 根据预测概率生成建议
            merge_prob = pred_probs[0]
            clean_prob = pred_probs[1]
            keep_prob = pred_probs[2]
            
            suggestion = {
                'node_id': node_id,
                'merge_probability': merge_prob,
                'clean_probability': clean_prob,
                'keep_probability': keep_prob,
                'suggestion': self._get_suggestion_from_probs(merge_prob, clean_prob, keep_prob),
                'confidence': max(merge_prob, clean_prob, keep_prob)
            }
            
            optimization_suggestions.append(suggestion)
        
        # 按置信度排序
        optimization_suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"📊 GNN冥思完成，生成 {len(optimization_suggestions)} 条优化建议")
        print(f"   最高置信度: {optimization_suggestions[0]['confidence']:.2f}")
        print(f"   建议分布: 合并 {sum(1 for s in optimization_suggestions if s['suggestion'] == 'merge')} 个")
        print(f"             清理 {sum(1 for s in optimization_suggestions if s['suggestion'] == 'clean')} 个")
        print(f"             保留 {sum(1 for s in optimization_suggestions if s['suggestion'] == 'keep')} 个")
        
        return {
            'suggestions': optimization_suggestions,
            'total_nodes': len(node_ids),
            'average_confidence': sum(s['confidence'] for s in optimization_suggestions) / len(optimization_suggestions)
        }
    
    def _get_suggestion_from_probs(self, merge_prob: float, clean_prob: float, keep_prob: float) -> str:
        """根据概率生成具体建议"""
        probs = [('merge', merge_prob), ('clean', clean_prob), ('keep', keep_prob)]
        probs.sort(key=lambda x: x[1], reverse=True)
        
        # 如果最高概率超过阈值，使用该建议
        if probs[0][1] > 0.6:
            return probs[0][0]
        
        # 否则使用启发式规则
        if clean_prob > 0.4:
            return 'clean'
        elif merge_prob > 0.3:
            return 'merge'
        else:
            return 'keep'
    
    def save_model(self, filepath: str):
        """保存GNN模型"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'input_dim': self.input_dim,
            'hidden_dim': self.hidden_dim,
            'output_dim': self.output_dim,
            'learning_rate': self.learning_rate,
            'training_history': self.training_history
        }, filepath)
        
        print(f"✅ GNN模型已保存: {filepath}")
    
    def load_model(self, filepath: str):
        """加载GNN模型"""
        checkpoint = torch.load(filepath)
        
        self.input_dim = checkpoint['input_dim']
        self.hidden_dim = checkpoint['hidden_dim']
        self.output_dim = checkpoint['output_dim']
        self.learning_rate = checkpoint['learning_rate']
        
        self.model = self._build_gnn_model()
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        self.training_history = checkpoint.get('training_history', [])
        
        print(f"✅ GNN模型已加载: {filepath}")

def test_gnn_meditation():
    """测试GNN冥思规则"""
    print("🧪 测试GNN冥思规则")
    print("=" * 50)
    
    # 创建测试图数据
    test_data = {
        'nodes': [
            {
                'id': 'node_001',
                'content': '重要知识节点，应该保留',
                'type': 'knowledge',
                'importance': 0.9,
                'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'vector': [0.1, 0.2, 0.3, 0.4, 0.5]
            },
            {
                'id': 'node_002',
                'content': '低重要性陈旧节点，应该清理',
                'type': 'outdated',
                'importance': 0.05,
                'timestamp': '2026-02-01T00:00:00Z',
                'vector': [0.9, 0.8, 0.7, 0.6, 0.5]
            },
            {
                'id': 'node_003',
                'content': '相似节点A，可能合并',
                'type': 'preference',
                'importance': 0.7,
                'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'vector': [0.2, 0.3, 0.4, 0.5, 0.6]
            },
            {
                'id': 'node_004',
                'content': '相似节点B，可能合并',
                'type': 'preference',
                'importance': 0.6,
                'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'vector': [0.25, 0.35, 0.45, 0.55, 0.65]
            }
        ],
        'edges': [
            {'source': 'node_001', 'target': 'node_002', 'type': 'related_to', 'weight': 0.3},
            {'source': 'node_003', 'target': 'node_004', 'type': 'similar_to', 'weight': 0.8}
        ]
    }
    
    print(f"📊 测试图：{len(test_data['nodes'])} 个节点，{len(test_data['edges'])} 条边")
    
    # 创建GNN冥思规则
    gnn_rule = GNNMeditationRule(
        input_dim=128,
        hidden_dim=64,
        output_dim=32,
        learning_rate=0.001
    )
    
    # 训练GNN模型
    print("\n🔧 训练GNN模型...")
    training_result = gnn_rule.train_on_graph(test_data, epochs=30)
    
    # 应用GNN冥思
    print("\n🔧 应用GNN冥思规则...")
    meditation_result = gnn_rule.apply_gnn_meditation(test_data)
    
    # 显示结果
    print("\n📋 GNN冥思建议（前3个）：")
    for i, suggestion in enumerate(meditation_result['suggestions'][:3]):
        print(f"  {i+1}. {suggestion['node_id']}:")
        print(f"     建议: {suggestion['suggestion']}")
        print(f"     置信度: {suggestion['confidence']:.2f}")
        print(f"     概率分布: 合并{suggestion['merge_probability']:.2f}, "
              f"清理{suggestion['clean_probability']:.2f}, "
              f"保留{suggestion['keep_probability']:.2f}")
    
    # 保存模型
    model_file = '/Users/liugang/.openclaw/workspace/gnn_meditation_model.pth'
    gnn_rule.save_model(model_file)
    
    print(f"\n✅ GNN冥思测试完成")
    print(f"   平均置信度: {meditation_result['average_confidence']:.2f}")
    print(f"   模型已保存: {model_file}")
    
    return gnn_rule, meditation_result

def integrate_gnn_with_meditation_engine():
    """将GNN冥思规则集成到冥思引擎"""
    print("\n🔧 将GNN冥思规则集成到冥思引擎")
    print("=" * 50)
    
    try:
        # 读取完整冥思引擎
        with open('/Users/liugang/.openclaw/workspace/meditation_engine_complete.py', 'r', encoding='utf-8') as f:
            engine_code = f.read()
        
        # 在MeditationEngine类中添加GNN冥思方法
        gnn_method = '''
    def apply_gnn_meditation_rule(self, gnn_model_path: Optional[str] = None) -> Dict:
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
            
            # 执行GNN建议（简化版本，实际需要更复杂的执行逻辑）
            executed_suggestions = []
            
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
                
                elif suggestion['suggestion'] == 'merge' and suggestion['confidence'] > 0.6:
                    # 标记为需要合并（实际合并需要找到相似节点）
                    executed_suggestions.append({
                        'node_id': suggestion['node_id'],
                        'action': 'marked_for_merge',
                        'confidence': suggestion['confidence']
                    })
            
            print(f"📊 GNN冥思执行结果：")
            print(f"   处理了 {len(executed_suggestions)} 个节点")
            print(f"   清理了 {sum(1 for s in executed_suggestions if s['action'] == 'cleaned')} 个节点")
            print(f"   标记了 {sum(1 for s in executed_suggestions if s['action'] == 'marked_for_merge')} 个节点待合并")
            
            return {
                'gnn_suggestions': gnn_result['suggestions'],
                'executed_actions': executed_suggestions,
                'total_nodes_before': len(graph_data['nodes']),
                'total_nodes_after': len(self.graph.nodes),
                'average_confidence': gnn_result['average_confidence']
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
'''
        
        # 找到合适的位置插入（在run_complete_meditation_workflow方法后）
        insert_marker = 'def run_complete_meditation_workflow(self) -> Dict:'
        if insert_marker in engine_code:
            # 找到方法的结束
            method_start = engine_code.find(insert_marker)
            method_end = engine_code.find('\n\n', method_start)
            
            if method_end != -1:
                # 插入GNN方法
                new_engine_code = (engine_code[:method_end] + 
                                 '\n\n' + gnn_method + 
                                 engine_code[method_end:])
                
                # 保存更新后的引擎
                updated_file = '/Users/liugang/.openclaw/workspace/meditation_engine_with_gnn.py'
                with open(updated_file, 'w', encoding='utf-8') as f:
                    f.write(new_engine_code)
                
                print(f"✅ GNN冥思规则已集成到冥思引擎：{updated_file}")
                
                # 测试集成后的引擎
                print("\n🧪 测试集成GNN的冥思引擎...")
                test_gnn_integration(updated_file)
                
                return updated_file
            else:
                print("❌ 无法找到工作流程方法的结束位置")
                return None
        else:
            print("❌ 无法找到工作流程方法")
            return None
            
    except Exception as e:
        print(f"❌ 集成失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_gnn_integration(engine_file: str):
    """测试集成GNN的冥思引擎"""
    import importlib.util
    
    # 动态导入引擎模块
    spec = importlib.util.spec_from_file_location("meditation_engine_gnn", engine_file)
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
        
        print("创建测试图...")
        graph = module.MemoryGraph()
        
        # 创建测试数据
        from datetime import datetime, timezone
        
        test_nodes = [
            {
                'id': 'test_gnn_1',
                'content': '测试GNN冥思节点1',
                'type': 'test',
                'importance': 0.8,
                'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'vector': [0.1, 0.2, 0.3, 0.4, 0.5]
            },
            {
                'id': 'test_gnn_2',
                'content': '测试GNN冥思节点2',
                'type': 'test',
                'importance': 0.1,
                'timestamp': '2026-02-01T00:00:00Z',
                'vector': [0.9, 0.8, 0.7, 0.6, 0.5]
            }
        ]
        
        for node_data in test_nodes:
            graph.add_node(node_data)
        
        print(f"测试图：{len(graph.nodes)} 个节点")
        
        # 创建引擎
        engine = module.MeditationEngine(graph)
        
        # 测试GNN冥思规则（不使用预训练模型）
        print("\n执行GNN冥思规则...")
        result = engine.apply_gnn_meditation_rule()
        
        if 'error' in result:
            print(f"⚠️  GNN冥思执行有错误：{result['error']}")
            print(f"   详情：{result.get('details', '无')}")
        else:
            print(f"✅ GNN冥思执行成功")
            print(f"   平均置信度：{result['average_confidence']:.2f}")
            print(f"   执行了 {len(result['executed_actions'])} 个动作")
        
        return 'error' not in result
        
    except Exception as e:
        print(f"❌ 测试失败：{str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🧠 GNN冥思规则开发")
    print("=" * 50)
    
    # 1. 测试GNN冥思规则基本功能
    print("\n" + "=" * 50)
    print("阶段1：测试GNN冥思规则基本功能")
    print("=" * 50)
    gnn_rule, meditation_result = test_gnn_meditation()
    
    # 2. 集成到冥思引擎
    print("\n" + "=" * 50)
    print("阶段2：集成到冥思引擎")
    print("=" * 50)
    engine_file = integrate_gnn_with_meditation_engine()
    
    print("\n" + "=" * 50)
    if engine_file:
        print("✅ GNN冥思规则开发完成！")
        print(f"   核心文件：gnn_meditation_rule.py")
        print(f"   集成引擎：{engine_file}")
        print(f"   模型文件：/Users/liugang/.openclaw/workspace/gnn_meditation_model.pth")
    else:
        print("⚠️  GNN冥思规则开发完成，但集成有问题")
    
    print("=" * 50)
    
    return engine_file is not None

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)
