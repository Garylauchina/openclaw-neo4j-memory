// 清空数据库（仅测试用）
MATCH (n) DETACH DELETE n;

// 创建记忆节点
CREATE (n:error {id: 'error_1', content: '错误：未知错误', type: 'error', importance: 0.85, timestamp: '2026-03-20T13:21:10.497837', metadata: '{"source": "self-improving", "category": "error", "original_data": {"type": "error", "timestamp": "2026-03-20T13:21:10.497837", "command": "测试命令", "error": "测试错误", "fix": "测试修复方法", "priority": "medium", "status": "pending"}}'});
CREATE (n:correction {id: 'correction_1', content: '纠正：未知纠正', type: 'correction', importance: 0.77, timestamp: '2026-03-23T11:43:36.061263', metadata: '{"source": "self-improving", "category": "correction", "original_data": {"type": "correction", "timestamp": "2026-03-23T11:43:36.061263", "topic": "信息准确性原则", "wrong": "编造未验证的内容", "correct": "基于实际检查报告，注明信息来源，请求用户确认", "context": "INTEGRITY_RULES.md 诚实执行规则", "count": 1}}'});
CREATE (n:best_practice {id: 'practice_1', content: '最佳实践：未知实践', type: 'best_practice', importance: 0.6799999999999999, timestamp: '2026-03-23T11:43:36.085447', metadata: '{"source": "self-improving", "category": "best_practice", "original_data": {"type": "best_practice", "timestamp": "2026-03-23T11:43:36.085447", "category": "工作流程优化", "practice": "制定《诚实执行规则》，建立验证和确认流程", "reason": "防止编造内容，确保信息准确性", "usage_count": 0}}'});

// 创建记忆连接边
MATCH (a {id: 'error_1'}), (b {id: 'correction_1'}) CREATE (a)-[r:similar_to {weight: 0.9817616158326881, timestamp: '2026-03-24T01:37:09.924277Z'}]->(b);
MATCH (a {id: 'error_1'}), (b {id: 'practice_1'}) CREATE (a)-[r:similar_to {weight: 0.9398815235306466, timestamp: '2026-03-24T01:37:09.924285Z'}]->(b);
MATCH (a {id: 'correction_1'}), (b {id: 'error_1'}) CREATE (a)-[r:similar_to {weight: 0.9817616158326881, timestamp: '2026-03-24T01:37:09.924290Z'}]->(b);
MATCH (a {id: 'correction_1'}), (b {id: 'practice_1'}) CREATE (a)-[r:similar_to {weight: 0.9876626401633689, timestamp: '2026-03-24T01:37:09.924294Z'}]->(b);
MATCH (a {id: 'practice_1'}), (b {id: 'error_1'}) CREATE (a)-[r:similar_to {weight: 0.9398815235306466, timestamp: '2026-03-24T01:37:09.924298Z'}]->(b);
// ... 还有 1 条边

// 创建索引（提高查询性能）
CREATE INDEX node_id_index IF NOT EXISTS FOR (n:Node) ON (n.id);
CREATE INDEX node_type_index IF NOT EXISTS FOR (n:Node) ON (n.type);
CREATE INDEX node_timestamp_index IF NOT EXISTS FOR (n:Node) ON (n.timestamp);

// 示例查询：查找所有错误节点
MATCH (n:error) RETURN n.id, n.content, n.importance LIMIT 10;

// 示例查询：查找相似度高的连接
MATCH (a)-[r:similar_to]->(b) WHERE r.weight > 0.9 RETURN a.id, b.id, r.weight LIMIT 10;

// 示例查询：查找节点之间的路径
MATCH path = shortestPath((a:error)-[*..3]-(b:correction)) RETURN path LIMIT 5;