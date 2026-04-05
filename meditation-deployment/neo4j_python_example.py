#!/usr/bin/env python3
"""
Neo4j Python驱动示例
使用neo4j-driver连接和操作Neo4j数据库
"""

from neo4j import GraphDatabase
import json
from datetime import datetime

class Neo4jGraphDAO:
    """Neo4j图数据访问对象"""
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def create_node(self, node_data):
        """创建节点"""
        with self.driver.session() as session:
            result = session.execute_write(self._create_node_tx, node_data)
            return result
    
    @staticmethod
    def _create_node_tx(tx, node_data):
        query = """
        CREATE (n:MemoryNode {
            id: $id,
            content: $content,
            type: $type,
            importance: $importance,
            timestamp: $timestamp,
            vector: $vector,
            metadata: $metadata
        })
        RETURN n.id as node_id
        """
        
        result = tx.run(query, 
                       id=node_data['id'],
                       content=node_data['content'],
                       type=node_data['type'],
                       importance=node_data['importance'],
                       timestamp=node_data['timestamp'],
                       vector=json.dumps(node_data['vector']),
                       metadata=json.dumps(node_data.get('metadata', {})))
        
        return result.single()["node_id"]
    
    def create_edge(self, edge_data):
        """创建边"""
        with self.driver.session() as session:
            result = session.execute_write(self._create_edge_tx, edge_data)
            return result
    
    @staticmethod
    def _create_edge_tx(tx, edge_data):
        query = """
        MATCH (a {id: $source}), (b {id: $target})
        CREATE (a)-[r:CONNECTION {
            type: $type,
            weight: $weight,
            timestamp: $timestamp
        }]->(b)
        RETURN type(r) as relationship_type
        """
        
        result = tx.run(query,
                       source=edge_data['source'],
                       target=edge_data['target'],
                       type=edge_data['type'],
                       weight=edge_data['weight'],
                       timestamp=edge_data.get('timestamp', datetime.now().isoformat()))
        
        return result.single()["relationship_type"]
    
    def find_similar_nodes(self, node_id, threshold=0.7):
        """查找相似节点"""
        with self.driver.session() as session:
            result = session.execute_read(self._find_similar_nodes_tx, node_id, threshold)
            return result
    
    @staticmethod
    def _find_similar_nodes_tx(tx, node_id, threshold):
        query = """
        MATCH (n {id: $node_id})-[r:similar_to]-(m)
        WHERE r.weight >= $threshold
        RETURN m.id as similar_node_id, m.content as content, r.weight as similarity
        ORDER BY r.weight DESC
        LIMIT 10
        """
        
        result = tx.run(query, node_id=node_id, threshold=threshold)
        return [{"node_id": record["similar_node_id"], 
                 "content": record["content"],
                 "similarity": record["similarity"]} 
                for record in result]
    
    def run_meditation_rule1(self):
        """执行冥思规则1：相似节点合并"""
        with self.driver.session() as session:
            result = session.execute_write(self._run_meditation_rule1_tx)
            return result
    
    @staticmethod
    def _run_meditation_rule1_tx(tx):
        # 查找高度相似的节点对
        query = """
        MATCH (a)-[r:similar_to]->(b)
        WHERE r.weight >= 0.75
        RETURN a.id as node1, b.id as node2, r.weight as similarity
        ORDER BY r.weight DESC
        LIMIT 10
        """
        
        similar_pairs = []
        result = tx.run(query)
        for record in result:
            similar_pairs.append({
                "node1": record["node1"],
                "node2": record["node2"],
                "similarity": record["similarity"]
            })
        
        # 合并相似节点（简化版本）
        merged_count = 0
        for pair in similar_pairs:
            merge_query = """
            MATCH (a {id: $node1}), (b {id: $node2})
            CREATE (merged:MemoryNode {
                id: 'merged_' + a.id + '_' + b.id,
                content: a.content + ' | ' + b.content,
                type: 'merged',
                importance: (a.importance + b.importance) / 2,
                timestamp: datetime(),
                vector: [0.5, 0.5, 0.5, 0.5, 0.5]
            })
            WITH a, b, merged
            OPTIONAL MATCH (a)-[r1]-(x)
            WHERE x <> b
            CREATE (merged)-[new_r1:CONNECTION {
                type: r1.type,
                weight: r1.weight,
                timestamp: datetime()
            }]-(x)
            WITH a, b, merged
            OPTIONAL MATCH (b)-[r2]-(y)
            WHERE y <> a
            CREATE (merged)-[new_r2:CONNECTION {
                type: r2.type,
                weight: r2.weight,
                timestamp: datetime()
            }]-(y)
            DELETE a, b
            RETURN merged.id as merged_node_id
            """
            
            tx.run(merge_query, node1=pair["node1"], node2=pair["node2"])
            merged_count += 1
        
        return {"merged_pairs": len(similar_pairs), "merged_count": merged_count}

# 使用示例
if __name__ == "__main__":
    # 连接配置
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "testpassword123"
    
    # 创建DAO实例
    dao = Neo4jGraphDAO(URI, USER, PASSWORD)
    
    try:
        # 测试连接
        print("测试Neo4j连接...")
        
        # 示例：创建测试节点
        test_node = {
            'id': 'test_node_1',
            'content': '测试记忆节点',
            'type': 'test',
            'importance': 0.8,
            'timestamp': datetime.now().isoformat(),
            'vector': [0.1, 0.2, 0.3, 0.4, 0.5],
            'metadata': {'source': 'test'}
        }
        
        node_id = dao.create_node(test_node)
        print(f"✅ 创建节点: {node_id}")
        
        # 示例：查找相似节点
        similar_nodes = dao.find_similar_nodes('test_node_1', 0.5)
        print(f"✅ 找到 {len(similar_nodes)} 个相似节点")
        
        # 示例：执行冥思规则
        meditation_result = dao.run_meditation_rule1()
        print(f"✅ 冥思规则执行结果: {meditation_result}")
        
    finally:
        dao.close()
        print("✅ 连接已关闭")
