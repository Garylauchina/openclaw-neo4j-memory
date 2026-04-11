# 从手动部署迁移到 Docker Compose

如果你之前是手动部署（本地 Neo4j + 直接运行 Python），迁移步骤如下：

## 1. 备份现有数据

```bash
# 从现有 Neo4j 导出数据
neo4j-admin database dump neo4j --to-path=/tmp/neo4j-backup
```

## 2. 克隆新项目

```bash
cd /path/to/openclaw-neo4j-memory
git pull origin main
```

## 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入：
# - 与之前相同的 NEO4J_PASSWORD
# - 你的 LLM API Key
```

## 4. 停止旧服务

```bash
# 停止旧 API 服务
pkill -f memory_api_server.py

# 停止旧 Neo4j（如果是 Docker）
docker stop <old-neo4j-container>
```

## 5. 启动新服务

```bash
make start
# 或
docker compose up -d
```

## 6. 迁移数据（可选）

如果你需要保留旧数据，使用迁移脚本：

```bash
# 从旧 Neo4j 实例迁移
# 先确认旧实例仍可连接
make migrate
```

## 7. 更新 OpenClaw 配置

API 地址不变（`http://127.0.0.1:18900`），`openclaw.json` 无需修改。

## 常见问题

### 端口冲突
编辑 `.env` 修改端口：
```
NEO4J_BOLT_PORT=17687
API_PORT=18901
```

### 内存不足
编辑 `docker-compose.yml` 中 Neo4j 的内存限制：
```yaml
NEO4J_dbms_memory_heap_max__size=2G
```

### 数据持久化
Docker Volume 数据存储在：
```bash
docker volume ls | grep neo4j
# 备份：make backup
```
