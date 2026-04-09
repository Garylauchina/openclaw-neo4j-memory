#!/usr/bin/env python3
"""更新graph_store.py中的回退查询，添加时间窗口过滤"""

import re

# 读取文件
with open('meditation_memory/graph_store.py', 'r') as f:
    content = f.read()

# 定义旧查询
old_query = '''        # 回退：普通 CONTAINS 查询
        fallback_query = \\"\\"\\"
        MATCH (e:Entity)
        WHERE NOT e:Archived AND e.name CONTAINS $keyword
        RETURN e.name AS name, e.entity_type AS entity_type,
               e.properties AS properties, e.mention_count AS mention_count,
               1.0 AS score
        ORDER BY e.mention_count DESC
        LIMIT $limit
        \\"\\"\\"'''

# 定义新查询
new_query = '''        # 回退：普通 CONTAINS 查询（加入时间窗口过滤）
        fallback_query = \\"\\"\\"
        MATCH (e:Entity)
        WHERE NOT e:Archived AND e.name CONTAINS $keyword AND e.updated_at IS NOT NULL
        // 时间窗口过滤：为近期记忆赋予更高权重
        WITH e,
             CASE 
               WHEN (timestamp() - e.updated_at) < (1000 * 3600 * 24 * 7) THEN 1.0      // 一周内：全权重
               WHEN (timestamp() - e.updated_at) < (1000 * 3600 * 24 * 30) THEN 0.7     // 一月内：70%
               WHEN (timestamp() - e.updated_at) < (1000 * 3600 * 24 * 90) THEN 0.4     // 三月内：40%
               ELSE 0.2                                                                   // 更久：20%
             END as recency_factor
        RETURN e.name AS name, e.entity_type AS entity_type,
               e.properties AS properties, e.mention_count AS mention_count,
               e.updated_at AS updated_at,
               e.mention_count * recency_factor AS weighted_score,
               recency_factor
        ORDER BY weighted_score DESC
        LIMIT $limit
        \\"\\"\\"'''

# 替换
if old_query in content:
    content = content.replace(old_query, new_query)
    print("✅ 成功替换回退查询")
    
    # 写入文件
    with open('meditation_memory/graph_store.py', 'w') as f:
        f.write(content)
    print("✅ 文件已更新")
else:
    print("❌ 未找到旧查询，尝试使用正则表达式")
    # 尝试正则表达式
    pattern = r'(\s*# 回退：普通 CONTAINS 查询\n\s*fallback_query = """.*?""")'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_query, content, flags=re.DOTALL)
        with open('meditation_memory/graph_store.py', 'w') as f:
            f.write(content)
        print("✅ 通过正则表达式更新文件")
    else:
        print("❌ 无法找到匹配的查询")