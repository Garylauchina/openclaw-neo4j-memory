#!/usr/bin/env python3
"""
Reality Writer - Graph写入 + Temporal Decay
核心：把现实数据写回Graph，并随时间衰减
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import math

class TemporalNode:
    """带时间衰减的节点"""
    
    def __init__(self, 
                 content: str,
                 value: Any,
                 node_type: str = "fact",
                 source: str = "real_world",
                 timestamp: Optional[datetime] = None,
                 decay_rate: float = 0.1,  # 衰减率（每小时）
                 belief_strength: float = 0.9,
                 rqs: float = 0.95):
        
        self.content = content
        self.value = value
        self.type = node_type
        self.source = source
        self.timestamp = timestamp or datetime.now()
        self.decay_rate = self._get_decay_rate(node_type, decay_rate)
        self.belief_strength = belief_strength
        self.rqs = rqs
        
        # 元数据
        self.metadata = {
            "created_at": self.timestamp.isoformat(),
            "last_updated": self.timestamp.isoformat(),
            "update_count": 1,
            "confidence_history": [belief_strength],
            "is_temporal": node_type in ["temporal", "fact", "rate", "price"]
        }
    
    def _get_decay_rate(self, node_type: str, base_rate: float) -> float:
        """根据节点类型获取衰减率"""
        decay_rates = {
            "temporal": 0.3,    # 高时变数据（汇率、股价）
            "rate": 0.3,
            "price": 0.3,
            "fact": 0.05,       # 事实（缓慢变化）
            "knowledge": 0.01,  # 知识（几乎不变）
            "belief": 0.02,     # 信念（缓慢变化）
            "static": 0.001     # 静态数据
        }
        
        return decay_rates.get(node_type, base_rate)
    
    def get_current_belief(self) -> float:
        """获取当前信念强度（考虑时间衰减）"""
        if not self.metadata["is_temporal"]:
            return self.belief_strength
        
        # 计算时间差（小时）
        time_delta = (datetime.now() - self.timestamp).total_seconds() / 3600
        
        # 指数衰减：belief = initial * exp(-λ * t)
        decayed_belief = self.belief_strength * math.exp(-self.decay_rate * time_delta)
        
        return max(0.1, decayed_belief)  # 保持最小信念
    
    def update(self, new_value: Any, new_belief: float = 0.9, source: str = "real_world"):
        """更新节点值"""
        self.value = new_value
        self.source = source
        self.timestamp = datetime.now()
        
        # 更新信念强度（加权平均）
        self.belief_strength = 0.7 * new_belief + 0.3 * self.belief_strength
        
        # 更新元数据
        self.metadata["last_updated"] = self.timestamp.isoformat()
        self.metadata["update_count"] += 1
        self.metadata["confidence_history"].append(self.belief_strength)
        
        # 限制历史长度
        if len(self.metadata["confidence_history"]) > 10:
            self.metadata["confidence_history"] = self.metadata["confidence_history"][-10:]
    
    def should_refresh(self, threshold: float = 0.7) -> bool:
        """检查是否需要刷新（信念强度低于阈值）"""
        current_belief = self.get_current_belief()
        return current_belief < threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        current_belief = self.get_current_belief()
        
        return {
            "content": self.content,
            "value": self.value,
            "type": self.type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "current_belief": current_belief,
            "original_belief": self.belief_strength,
            "rqs": self.rqs,
            "decay_rate": self.decay_rate,
            "metadata": self.metadata,
            "needs_refresh": self.should_refresh(),
            "age_hours": (datetime.now() - self.timestamp).total_seconds() / 3600
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        current_belief = self.get_current_belief()
        age_hours = (datetime.now() - self.timestamp).total_seconds() / 3600
        
        return (f"TemporalNode('{self.content[:30]}...', "
                f"value={self.value}, belief={current_belief:.2f}, "
                f"age={age_hours:.1f}h, type={self.type})")

class RealityGraphWriter:
    """现实图写入器"""
    
    def __init__(self, graph=None):
        self.graph = graph
        self.temporal_nodes: Dict[str, TemporalNode] = {}
        
        # 统计
        self.stats = {
            "total_writes": 0,
            "updates": 0,
            "expired_nodes": 0,
            "avg_belief": 0.0,
            "high_confidence_writes": 0
        }
    
    def write_reality_data(self, 
                          content: str,
                          value: Any,
                          node_type: str = "fact",
                          source: str = "real_world",
                          rqs: float = 0.95) -> TemporalNode:
        """
        写入现实数据
        
        Args:
            content: 内容描述
            value: 数据值
            node_type: 节点类型
            source: 数据源
            rqs: 推理质量评分
            
        Returns:
            创建的TemporalNode
        """
        # 检查是否已存在
        node_key = f"{content}_{node_type}"
        
        if node_key in self.temporal_nodes:
            # 更新现有节点
            node = self.temporal_nodes[node_key]
            
            # 计算新信念（基于RQS和源可信度）
            source_confidence = self._get_source_confidence(source)
            new_belief = 0.7 * rqs + 0.3 * source_confidence
            
            node.update(value, new_belief, source)
            
            self.stats["updates"] += 1
            print(f"   🔄 更新节点: {content} = {value} (信念: {new_belief:.2f})")
        else:
            # 创建新节点
            source_confidence = self._get_source_confidence(source)
            initial_belief = 0.8 * rqs + 0.2 * source_confidence
            
            node = TemporalNode(
                content=content,
                value=value,
                node_type=node_type,
                source=source,
                decay_rate=0.1,
                belief_strength=initial_belief,
                rqs=rqs
            )
            
            self.temporal_nodes[node_key] = node
            
            self.stats["total_writes"] += 1
            if initial_belief > 0.8:
                self.stats["high_confidence_writes"] += 1
            
            print(f"   📝 写入现实数据: {content} = {value} (信念: {initial_belief:.2f}, 类型: {node_type})")
        
        # 如果提供了图系统，也写入图
        if self.graph and hasattr(self.graph, 'add_node'):
            self._write_to_graph(node)
        
        # 更新统计
        self._update_stats()
        
        return node
    
    def _get_source_confidence(self, source: str) -> float:
        """获取数据源可信度"""
        source_confidences = {
            "real_world_api": 0.9,
            "validated_api": 0.95,
            "manual_input": 0.8,
            "inferred": 0.6,
            "simulated": 0.4,
            "unknown": 0.3
        }
        
        return source_confidences.get(source, 0.5)
    
    def _write_to_graph(self, node: TemporalNode):
        """写入到图系统"""
        try:
            # 创建图节点
            graph_node = {
                "id": f"reality_{int(time.time())}",
                "content": node.content,
                "value": node.value,
                "type": node.type,
                "source": node.source,
                "timestamp": node.timestamp.isoformat(),
                "belief": node.get_current_belief(),
                "rqs": node.rqs,
                "metadata": {
                    "is_temporal": node.metadata["is_temporal"],
                    "decay_rate": node.decay_rate,
                    "from_reality_writer": True
                }
            }
            
            # 添加到图
            self.graph.add_node(graph_node)
            
            # 创建连接（如果可能）
            if hasattr(self.graph, 'add_edge'):
                # 连接到相关节点
                related_keywords = node.content.lower().split()[:3]
                for keyword in related_keywords:
                    if len(keyword) > 2:  # 只连接有意义的词
                        self.graph.add_edge(
                            graph_node["id"],
                            f"concept_{keyword}",
                            relation="related_to",
                            strength=0.5
                        )
            
            print(f"   🧠 已写入图系统: {node.content[:30]}...")
            
        except Exception as e:
            print(f"   ⚠️  写入图系统失败: {e}")
    
    def cleanup_expired(self, belief_threshold: float = 0.3):
        """清理过期节点（信念强度低于阈值）"""
        to_remove = []
        
        for key, node in self.temporal_nodes.items():
            if node.get_current_belief() < belief_threshold:
                to_remove.append(key)
        
        for key in to_remove:
            del self.temporal_nodes[key]
            self.stats["expired_nodes"] += 1
        
        if to_remove:
            print(f"   🗑️  清理 {len(to_remove)} 个过期节点")
    
    def get_refresh_candidates(self, threshold: float = 0.7) -> List[TemporalNode]:
        """获取需要刷新的节点"""
        candidates = []
        
        for node in self.temporal_nodes.values():
            if node.should_refresh(threshold):
                candidates.append(node)
        
        # 按信念强度排序（最低的优先）
        candidates.sort(key=lambda n: n.get_current_belief())
        
        return candidates
    
    def _update_stats(self):
        """更新统计信息"""
        if not self.temporal_nodes:
            self.stats["avg_belief"] = 0.0
            return
        
        total_belief = sum(node.get_current_belief() for node in self.temporal_nodes.values())
        self.stats["avg_belief"] = total_belief / len(self.temporal_nodes)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        refresh_candidates = self.get_refresh_candidates()
        
        return {
            "performance": self.stats,
            "node_summary": {
                "total_nodes": len(self.temporal_nodes),
                "temporal_nodes": sum(1 for n in self.temporal_nodes.values() if n.metadata["is_temporal"]),
                "static_nodes": sum(1 for n in self.temporal_nodes.values() if not n.metadata["is_temporal"]),
                "needs_refresh": len(refresh_candidates),
                "avg_belief": self.stats["avg_belief"]
            },
            "source_distribution": self._get_source_distribution()
        }
    
    def _get_source_distribution(self) -> Dict[str, int]:
        """获取数据源分布"""
        distribution = {}
        
        for node in self.temporal_nodes.values():
            source = node.source
            distribution[source] = distribution.get(source, 0) + 1
        
        return distribution
    
    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        
        print(f"\n📊 RealityGraphWriter 状态:")
        print(f"   节点统计:")
        print(f"     总节点数: {stats['node_summary']['total_nodes']}")
        print(f"     时变节点: {stats['node_summary']['temporal_nodes']}")
        print(f"     静态节点: {stats['node_summary']['static_nodes']}")
        print(f"     需要刷新: {stats['node_summary']['needs_refresh']}")
        print(f"     平均信念: {stats['node_summary']['avg_belief']:.3f}")
        
        print(f"   性能:")
        print(f"     总写入: {stats['performance']['total_writes']}")
        print(f"     更新次数: {stats['performance']['updates']}")
        print(f"     过期清理: {stats['performance']['expired_nodes']}")
        print(f"     高置信写入: {stats['performance']['high_confidence_writes']}")
        
        if stats['source_distribution']:
            print(f"   数据源分布:")
            for source, count in stats['source_distribution'].items():
                print(f"     {source}: {count}")
        
        # 显示需要刷新的节点
        refresh_candidates = self.get_refresh_candidates()
        if refresh_candidates:
            print(f"   需要刷新的节点:")
            for i, node in enumerate(refresh_candidates[:3]):  # 只显示前3个
                current_belief = node.get_current_belief()
                print(f"     {i+1}. {node.content[:30]}... (信念: {current_belief:.2f}, 年龄: {node.to_dict()['age_hours']:.1f}h)")

def test_reality_writer():
    """测试现实写入器"""
    print("🧪 测试 RealityGraphWriter...")
    
    writer = RealityGraphWriter()
    
    # 测试写入不同类型的数据
    test_data = [
        {
            "content": "USD→CNY汇率",
            "value": 6.9123,
            "type": "temporal",
            "source": "real_world_api",
            "rqs": 0.95
        },
        {
            "content": "北京气温",
            "value": 22.5,
            "type": "temporal", 
            "source": "weather_api",
            "rqs": 0.9
        },
        {
            "content": "地球是圆的",
            "value": True,
            "type": "fact",
            "source": "knowledge",
            "rqs": 0.99
        },
        {
            "content": "比特币价格",
            "value": 45000,
            "type": "temporal",
            "source": "crypto_api",
            "rqs": 0.85
        }
    ]
    
    # 写入数据
    nodes = []
    for data in test_data:
        node = writer.write_reality_data(**data)
        nodes.append(node)
    
    print(f"\n✅ 写入完成")
    
    # 显示节点状态
    print(f"\n📋 节点状态:")
    for i, node in enumerate(nodes):
        node_dict = node.to_dict()
        print(f"  {i+1}. {node.content}")
        print(f"     值: {node_dict['value']}")
        print(f"     当前信念: {node_dict['current_belief']:.3f}")
        print(f"     类型: {node_dict['type']}")
        print(f"     需要刷新: {node_dict['needs_refresh']}")
        print(f"     年龄: {node_dict['age_hours']:.2f}h")
    
    # 模拟时间流逝（测试衰减）
    print(f"\n⏳ 模拟时间流逝（24小时后）...")
    
    # 创建旧节点
    old_time = datetime.now() - timedelta(hours=24)
    old_node = TemporalNode(
        content="旧汇率数据",
        value=7.0,
        node_type="temporal",
        source="real_world_api",
        timestamp=old_time,
        belief_strength=0.9,
        rqs=0.95
    )
    
    print(f"  旧节点: {old_node.content}")
    print(f"    初始信念: {old_node.belief_strength:.3f}")
    print(f"    当前信念: {old_node.get_current_belief():.3f}")
    print(f"    需要刷新: {old_node.should_refresh()}")
    
    # 测试更新
    print(f"\n🔄 测试更新节点...")
    old_node.update(6.9123, 0.95, "real_world_api")
    print(f"  更新后信念: {old_node.get_current_belief():.3f}")
    print(f"  更新后需要刷新: {old_node.should_refresh()}")
    
    # 显示统计
    writer.print_status()
    
    # 测试清理
    print(f"\n🧹 测试清理过期节点...")
    writer.cleanup_expired(belief_threshold=0.5)
    
    # 最终状态
    print(f"\n🎯 最终状态:")
    writer.print_status()
    
    return writer

if __name__ == "__main__":
    test_reality_writer()