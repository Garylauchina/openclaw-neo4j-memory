"""隔离测试 P0-3 反馈存储逻辑"""
import json, time, sys, os
sys.path.insert(0, "/Users/liugang/.openclaw/workspace/plugins/neo4j-memory")

from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'reflection123'))

# 模拟 memory_api_server.py 中的步骤 5
class MockRequest:
    def __init__(self):
        self.query = "测试 P0-3"
        self.success = True
        self.confidence = 0.9
        self.applied_strategy_name = "test_strategy"
        self.validation_status = "accurate"
        self.result_count = 5
        self.returned_entities = ["Neo4j", "记忆系统"]
        self.useful_entities = ["Neo4j"]
        self.noise_entities = ["噪声1"]
        self.error_msg = None

req = MockRequest()

# 模拟配置
class MockConfig:
    database = "neo4j"

store_config = MockConfig()

feedback_data = {
    "query": req.query,
    "success": req.success,
    "confidence": req.confidence,
    "applied_strategy_name": req.applied_strategy_name,
    "validation_status": req.validation_status,
    "result_count": req.result_count if req.result_count is not None else 0,
    "returned_entities": req.returned_entities or [],
    "useful_entities": req.useful_entities or [],
    "noise_entities": req.noise_entities or [],
    "error_msg": req.error_msg,
    "timestamp": time.time(),
}

print("=== 模拟步骤 5 ===")

try:
    feedback_node_query = """
    MERGE (f:Feedback {query: $query, timestamp: $ts})
    ON CREATE SET
        f.success = $success,
        f.confidence = $confidence,
        f.applied_strategy_name = $strategy,
        f.validation_status = $validation_status,
        f.result_count = $result_count,
        f.returned_entities = $returned_entities,
        f.useful_entities = $useful_entities,
        f.noise_entities = $noise_entities,
        f.error_msg = $error_msg,
        f.created_at = timestamp()
    RETURN elementId(f) AS eid
    """
    record = None
    print("执行 MERGE...")
    with driver.session(database=store_config.database) as session:
        neo4j_result = session.run(
            feedback_node_query,
            query=req.query,
            ts=feedback_data["timestamp"],
            success=req.success,
            confidence=req.confidence,
            strategy=req.applied_strategy_name or "",
            validation_status=req.validation_status or "",
            result_count=feedback_data["result_count"],
            returned_entities=json.dumps(feedback_data["returned_entities"], ensure_ascii=False),
            useful_entities=json.dumps(feedback_data["useful_entities"], ensure_ascii=False),
            noise_entities=json.dumps(feedback_data["noise_entities"], ensure_ascii=False),
            error_msg=req.error_msg or "",
        )
        record = neo4j_result.single()
        if record:
            print(f"✅ Feedback 节点创建: {record['eid']}")

    # 关联策略
    if req.applied_strategy_name:
        link_query = """
        MATCH (f:Feedback {query: $query, timestamp: $ts})
        MATCH (s:Strategy {name: $strategy_name})
        MERGE (f)-[:FEEDBACK_FOR]->(s)
        """
        with driver.session(database=store_config.database) as session:
            session.run(
                link_query,
                query=req.query,
                ts=feedback_data["timestamp"],
                strategy_name=req.applied_strategy_name,
            )
            print("✅ FEEDBACK_FOR 关系创建完成")

    # 关联噪音实体
    if req.noise_entities:
        noise_link_query = """
        MATCH (f:Feedback {query: $query, timestamp: $ts})
        MATCH (e:Entity {name: $entity_name})
        WHERE NOT e:Archived
        MERGE (f)-[:NOISE_ENTITY]->(e)
        """
        with driver.session(database=store_config.database) as session:
            for noise_entity in feedback_data["noise_entities"][:10]:
                session.run(
                    noise_link_query,
                    query=req.query,
                    ts=feedback_data["timestamp"],
                    entity_name=noise_entity,
                )
                print(f"✅ NOISE_ENTITY 关系创建: {noise_entity}")

except Exception as e:
    print(f"❌ 错误: {e}")

driver.close()
