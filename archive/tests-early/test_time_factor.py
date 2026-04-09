#!/usr/bin/env python3
"""测试时间衰减因子计算"""

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

def test_recency_factors():
    """测试时间衰减因子分布"""
    print("=" * 80)
    print("测试时间窗口过滤 - 时间衰减因子分布")
    print("=" * 80)
    
    # 查询不同时间段的实体数量
    query = """
    MATCH (e:Entity)
    WHERE NOT e:Archived AND e.updated_at IS NOT NULL
    WITH e,
         CASE 
           WHEN (timestamp() - e.updated_at) < (1000 * 3600 * 24 * 7) THEN '一周内 (100%)'
           WHEN (timestamp() - e.updated_at) < (1000 * 3600 * 24 * 30) THEN '一月内 (70%)'
           WHEN (timestamp() - e.updated_at) < (1000 * 3600 * 24 * 90) THEN '三月内 (40%)'
           ELSE '更久 (20%)'
         END as recency_group
    RETURN recency_group, COUNT(*) as count
    ORDER BY 
        CASE recency_group
            WHEN '一周内 (100%)' THEN 1
            WHEN '一月内 (70%)' THEN 2
            WHEN '三月内 (40%)' THEN 3
            ELSE 4
        END
    """
    
    with driver.session() as session:
        result = session.run(query)
        print("\n实体更新时间分布:")
        print("-" * 80)
        total = 0
        for record in result:
            group = record['recency_group']
            count = record['count']
            total += count
            print(f"  {group:20} : {count:4} 个实体")
        print(f"  {'总计':20} : {total:4} 个实体")
    
    # 测试搜索查询中的时间衰减
    print("\n搜索查询测试:")
    print("-" * 80)
    
    test_queries = ["冥思", "时间", "记忆", "Moltbook", "openclaw"]
    
    for query_keyword in test_queries:
        print(f"\n关键词: '{query_keyword}'")
        
        search_query = f"""
        CALL db.index.fulltext.queryNodes('entity_fulltext_idx', '{query_keyword}')
        YIELD node, score
        WHERE NOT node:Archived AND node.updated_at IS NOT NULL
        WITH node, score,
             CASE 
               WHEN (timestamp() - node.updated_at) < (1000 * 3600 * 24 * 7) THEN 1.0
               WHEN (timestamp() - node.updated_at) < (1000 * 3600 * 24 * 30) THEN 0.7
               WHEN (timestamp() - node.updated_at) < (1000 * 3600 * 24 * 90) THEN 0.4
               ELSE 0.2
             END as recency_factor
        RETURN COUNT(*) as total, 
               AVG(score) as avg_score,
               AVG(recency_factor) as avg_recency,
               AVG(score * recency_factor) as avg_weighted
        """
        
        with driver.session() as session:
            result = session.run(search_query)
            record = result.single()
            if record and record['total'] > 0:
                total = record['total']
                avg_score = record['avg_score'] or 0
                avg_recency = record['avg_recency'] or 0
                avg_weighted = record['avg_weighted'] or 0
                print(f"  找到 {total} 个结果 | 平均原始分: {avg_score:.2f} | 平均时间因子: {avg_recency:.2f} | 平均加权分: {avg_weighted:.2f}")
                
                # 获取前3个结果查看详情
                detail_query = f"""
                CALL db.index.fulltext.queryNodes('entity_fulltext_idx', '{query_keyword}')
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
                LIMIT 3
                """
                
                detail_result = session.run(detail_query)
                for i, rec in enumerate(detail_result, 1):
                    name = rec['name']
                    updated_at = rec['updated_at']
                    score = rec['score']
                    recency = rec['recency_factor']
                    weighted = rec['weighted_score']
                    days_ago = (time.time() * 1000 - updated_at) / (1000 * 3600 * 24) if updated_at else 0
                    print(f"    {i}. {name[:30]:30} | {days_ago:.1f}天前 | 分:{score:.2f}×{recency:.2f}= {weighted:.2f}")
            else:
                print(f"  无结果")

if __name__ == '__main__':
    try:
        test_recency_factors()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()