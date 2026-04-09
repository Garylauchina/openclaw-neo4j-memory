#!/usr/bin/env python3
"""测试时间窗口过滤效果"""

import os
from neo4j import GraphDatabase

# 从环境文件读取配置
env_file = "/Users/liugang/.openclaw/neo4j-memory.env"
env_vars = {}
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.replace('export ', '').strip()
                value = value.strip().strip('"\'')
                env_vars[key] = value

# Neo4j连接
uri = env_vars.get('NEO4J_URI', 'bolt://localhost:7687')
user = env_vars.get('NEO4J_USER', 'neo4j')
password = env_vars.get('NEO4J_PASSWORD', 'password')

driver = GraphDatabase.driver(uri, auth=(user, password))

def test_fulltext_search():
    """测试全文搜索时间窗口过滤"""
    query = """
    CALL db.index.fulltext.queryNodes('entity_fulltext_idx', '冥思')
    YIELD node, score
    WHERE NOT node:Archived AND node.updated_at IS NOT NULL
    WITH node, score,
         (timestamp() - node.updated_at) / (1000.0 * 3600 * 24 * 30) as days_ago_normalized,
         CASE 
           WHEN (timestamp() - node.updated_at) < (1000 * 3600 * 24 * 7) THEN 1.0
           WHEN (timestamp() - node.updated_at) < (1000 * 3600 * 24 * 30) THEN 0.7
           WHEN (timestamp() - node.updated_at) < (1000 * 3600 * 24 * 90) THEN 0.4
           ELSE 0.2
         END as recency_factor
    RETURN node.name AS name, 
           node.updated_at AS updated_at,
           score,
           recency_factor,
           score * recency_factor AS weighted_score
    ORDER BY weighted_score DESC
    LIMIT 10
    """
    
    with driver.session() as session:
        result = session.run(query)
        print("=== 全文搜索时间窗口过滤测试 ===")
        print("查询: '冥思'")
        print("结果按 weighted_score = score × recency_factor 排序")
        print("-" * 80)
        for i, record in enumerate(result, 1):
            name = record['name']
            updated_at = record['updated_at']
            score = record['score']
            recency = record['recency_factor']
            weighted = record['weighted_score']
            days_ago = (time.time() * 1000 - updated_at) / (1000 * 3600 * 24) if updated_at else 'N/A'
            print(f"{i:2}. {name[:50]:50} | 更新: {days_ago:.1f}天前 | 原始分: {score:.3f} | 时间因子: {recency:.2f} | 加权分: {weighted:.3f}")
        print()

def test_contains_search():
    """测试CONTAINS搜索时间窗口过滤"""
    query = """
    MATCH (e:Entity)
    WHERE NOT e:Archived AND e.name CONTAINS '冥思' AND e.updated_at IS NOT NULL
    WITH e,
         CASE 
           WHEN (timestamp() - e.updated_at) < (1000 * 3600 * 24 * 7) THEN 1.0
           WHEN (timestamp() - e.updated_at) < (1000 * 3600 * 24 * 30) THEN 0.7
           WHEN (timestamp() - e.updated_at) < (1000 * 3600 * 24 * 90) THEN 0.4
           ELSE 0.2
         END as recency_factor
    RETURN e.name AS name, 
           e.updated_at AS updated_at,
           e.mention_count AS mention_count,
           recency_factor,
           e.mention_count * recency_factor AS weighted_score
    ORDER BY weighted_score DESC
    LIMIT 10
    """
    
    with driver.session() as session:
        result = session.run(query)
        print("=== CONTAINS搜索时间窗口过滤测试 ===")
        print("查询: CONTAINS '冥思'")
        print("结果按 weighted_score = mention_count × recency_factor 排序")
        print("-" * 80)
        for i, record in enumerate(result, 1):
            name = record['name']
            updated_at = record['updated_at']
            mention = record['mention_count']
            recency = record['recency_factor']
            weighted = record['weighted_score']
            days_ago = (time.time() * 1000 - updated_at) / (1000 * 3600 * 24) if updated_at else 'N/A'
            print(f"{i:2}. {name[:50]:50} | 更新: {days_ago:.1f}天前 | 提及数: {mention} | 时间因子: {recency:.2f} | 加权分: {weighted:.1f}")
        print()

if __name__ == '__main__':
    import time
    try:
        test_fulltext_search()
        test_contains_search()
    except Exception as e:
        print(f"错误: {e}")
    finally:
        driver.close()