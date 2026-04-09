# Neo4j Memory Migration Guide

本文档说明如何使用迁移工具在 Neo4j 实例之间安全转移图谱状态。

## 🛠️ 安装依赖

```bash
cd /path/to/openclaw-neo4j-memory-repo
pip install neo4j click httpx
```

## 📋 使用场景

### 场景 1: 开发环境 → 生产环境

```bash
# 1. 从开发环境导出
python scripts/neo4j_migrate.py export \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password dev_password \
    --output production-export.jsonl

# 2. 导入到生产环境
python scripts/neo4j_migrate.py import \
    --uri bolt://production-server:7687 \
    --user neo4j \
    --password prod_password \
    production-export.jsonl

# 3. 验证迁移结果
python scripts/neo4j_migrate.py verify \
    --src-uri bolt://localhost:7687 \
    --src-user neo4j \
    --src-password dev_password \
    --dst-uri bolt://production-server:7687 \
    --dst-user neo4j \
    --dst-password prod_password
```

### 场景 2: 备份与恢复

```bash
# 备份
python scripts/neo4j_migrate.py export \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password my_password \
    --output backup-$(date +%Y%m%d).jsonl

# 恢复（到新实例）
python scripts/neo4j_migrate.py import \
    --uri bolt://localhost:7688 \
    --user neo4j \
    --password new_password \
    backup-20260410.jsonl
```

### 场景 3: 环境迁移（Docker → 本地）

```bash
# 从 Docker 容器导出
docker exec neo4j-container python scripts/neo4j_migrate.py export \
    --uri bolt://localhost:7687 \
    --user neo4j \
    --password neo4j \
    --output /tmp/migration.jsonl

# 复制到本地
docker cp neo4j-container:/tmp/migration.jsonl ./migration.jsonl

# 导入到本地 Neo4j
python scripts/neo4j_migrate.py import \
    --uri bolt://localhost:7688 \
    --user neo4j \
    --password local_password \
    migration.jsonl
```

## 🔍 验证迁移结果

### 自动验证

```bash
./scripts/quick-verify.sh \
    bolt://localhost:7687 \
    bolt://localhost:7688 \
    neo4j
```

### 手动验证

```bash
# 1. 检查节点数量
cypher-shell -u neo4j -p password <<EOF
MATCH (n)
RETURN labels(n)[0] as label, count(n) as count
ORDER BY count DESC;
EOF

# 2. 测试搜索功能
curl -X POST http://localhost:18900/search \
  -H "Content-Type: application/json" \
  -d '{"query": "哥斯拉"}'

# 3. 测试记忆注入
curl -X POST http://localhost:18900/ingest \
  -H "Content-Type: application/json" \
  -d '{"text": "测试记忆"}'

# 4. 测试冥思功能
curl -X POST http://localhost:18900/meditation/trigger \
  -H "Content-Type: application/json" \
  -d '{"mode": "auto"}'
```

## 📊 导出文件格式

### 数据文件 (export.jsonl)

每行一个 Cypher 语句：

```cypher
CREATE (:Entity {name: "哥斯拉", entity_type: "person", description: "用户"})
CREATE (:Strategy {name: "冥思优化", fitness_score: 0.85})
MATCH (src:Entity {name: "哥斯拉"}), (tgt:Entity {name: "元认知"}) 
CREATE (src)-[:KNOWS]->(tgt)
```

### 元数据文件 (export.jsonl.meta)

```json
{
  "run_id": "a1b2c3d4e5f6",
  "timestamp": "2026-04-10T07:00:00",
  "source_uri": "bolt://localhost:7687",
  "node_count": 7526,
  "relationship_count": 414036,
  "checksum": "abc123...",
  "labels": ["Entity", "Strategy", "Belief"],
  "properties": ["name", "entity_type", "description"]
}
```

## ⚠️ 注意事项

### 数据安全性

1. **备份原数据**: 导入前先备份目标数据库
2. **验证连接**: 确保源和目标连接正常
3. **检查权限**: 确保有足够的读写权限

### 性能优化

1. **批次大小**: 大数据集使用较小的 batch_size (50-100)
2. **索引创建**: 导入前自动创建必要索引
3. **断点续传**: 支持中断后继续

### 兼容性

- ✅ Neo4j 5.x (推荐)
- ✅ Neo4j 4.4+
- ⚠️ Neo4j 4.0-4.3 (部分功能受限)

## 🐛 故障排除

### 问题 1: 连接失败

```bash
# 检查 Neo4j 是否运行
docker ps | grep neo4j

# 检查端口
netstat -tlnp | grep 7687

# 测试连接
cypher-shell -u neo4j -p password "RETURN 1"
```

### 问题 2: 导入失败

```bash
# 查看详细日志
python scripts/neo4j_migrate.py import \
    --uri bolt://localhost:7688 \
    --user neo4j \
    --password password \
    export.jsonl 2>&1 | tee import.log

# 检查错误行
grep "ERROR" import.log | head -20
```

### 问题 3: 验证不通过

```bash
# 查看具体差异
python scripts/neo4j_migrate.py verify \
    --src-uri bolt://localhost:7687 \
    --src-user neo4j \
    --src-password password \
    --dst-uri bolt://localhost:7688 \
    --dst-user neo4j \
    --dst-password password > verify-report.txt

# 查看报告
cat verify-report.txt
```

## 📚 相关文档

- [EVOLUTION.md](../EVOLUTION.md) - 项目进化历史
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南
- [Issue #56](https://github.com/Garylauchina/openclaw-neo4j-memory/issues/56) - 功能需求

## 🙏 致谢

本工具设计参考了：
- Neo4j 官方迁移工具
- APOC 导出导入功能
- Issue #56 的详细需求说明
