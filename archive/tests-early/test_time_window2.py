#!/usr/bin/env python3
"""测试时间窗口过滤效果 - 修复版"""

import os
import time
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

def test_search(keyword):
    """测试搜索时间窗口过滤"""
    print(f"\n{'='*80}")
    print(f"测试关键词: '{keyword}'")
    print(f"{'='*80}")
    
    # 全文搜索
    query1 = f"""
    CALL db.index.fulltext.queryNodes('entity_fulltext_idx', '{keyword}')
    YIELD node, score
    WHERE NOT node:Archived AND node.updated_at IS NOT NULL
    WITH node, score,
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
    
    print("\n1. 全文搜索 (按加权分数排序):")
    print("-" * 80)
    with driver.session() as session:
        result = session.run(query1)
        for i, record in enumerate(result, 1):
            name = record['name']
            updated_at = record['updated_at']
            score = record['score']
            recency = record['recency_factor']
            weighted = record['weighted_score']
            days_ago = (time.time() * 1000 - updated_at) / (1000 * 3600 * 24) if updated_at else 'N/A'
            recency_str = f"{recency:.2f}"
            if recency == 1.0:
                recency_str = "1.00 (一周内)"
            elif recency == 0.7:
                recency_str = "0.70 (一月内)"
            elif recency == 0.4:
                recency_str = "0.40 (三月内)"
            else:
                recency_str = "0.20 (更久)"
            print(f"{i:2}. {name[:40]:40} | {days_ago:.1f}天前 | 分:{score:.2f}×{recency_str}= {weighted:.2f}")
    
    # CONTAINS搜索
    query2 = f"""
    MATCH (e:Entity)
    WHERE NOT e:Archived AND e.name CONTAINS '{keyword}' AND e.updated_at IS NOT NULL
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
    
    print("\n2. CONTAINS搜索 (按加权提及数排序):")
    print("-" * 80)
    with driver.session() as session:
        result = session.run(query2)
        for i, record in enumerate(result, 1):
            name = record['name']
            updated_at = record['updated_at']
            mention = record['mention_count'] or 0
            recency = record['recency_factor']
            weighted = record['weighted_score']
            days_ago = (time.time() * 1000 - updated_at) / (1000 * 3600 * 24) if updated_at else 'N/A'
            recency_str = f"{recency:.2f}"
            if recency == 1.0:
                recency_str = "1.00 (一周内)"
            elif recency == 0.7:
                recency_str = "0.70 (一月内)"
            elif recency == 0.4:
                recency_str = "0.40 (三月内)"
            else:
                recency_str = "0.20 (更久)"
            print(f"{i:2}. {name[:40]:40} | {days_ago:.1f}天前 | 提及:{mention}×{recency_str}= {weighted:.1f}")

if __name__ == '__main__':
    try:
        # 测试几个关键词
        test_search("冥思")
        test_search("时间")
        test_search("记忆")
        test_search("Moltbook")
        test_search("openclaw")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()