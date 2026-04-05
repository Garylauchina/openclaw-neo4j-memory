# AI冥思记忆系统 v2.0 - 生产环境部署指南

## 🚀 快速开始

### 1. 环境要求
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **磁盘空间**: 至少2GB
- **内存**: 至少4GB
- **CPU**: 4核以上（推荐）

### 2. 一键部署
```bash
# 进入部署目录
cd /Users/liugang/.openclaw/workspace/meditation-deployment

# 执行部署脚本
./deploy.sh
```

### 3. 验证部署
```bash
# 检查服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f meditation-service

# 访问Web界面
open http://localhost:8080
```

## 📊 服务架构

### 容器服务
```
1. meditation-service (主服务)
   - 端口: 8080
   - 功能: REST API + Web界面
   - 健康检查: /api/health

2. scheduler (定时任务)
   - 功能: 每日冥思、同步、健康检查
   - 定时: 02:00冥思，03:00同步

3. redis (缓存)
   - 端口: 6379
   - 功能: 缓存中间结果

4. postgres (数据库)
   - 端口: 5432
   - 功能: 持久化存储

5. prometheus (监控)
   - 端口: 9090
   - 功能: 指标收集

6. grafana (可视化)
   - 端口: 3000
   - 功能: 监控面板
```

### 数据目录
```
meditation-deployment/
├── models/          # 模型文件
├── state/           # 状态文件
├── results/         # 结果文件
├── logs/            # 日志文件
└── monitoring/      # 监控配置
```

## 🔧 配置管理

### 环境变量
```bash
# 主服务配置
ENVIRONMENT=production
LOG_LEVEL=INFO
MEDITATION_FREQUENCY=daily
GNN_MODEL_PATH=/data/models/gnn_meditation_model.pth
STATE_FILE=/data/state/meditation_state.json

# 定时任务配置
SCHEDULE_TIME=02:00
```

### API配置
通过Web界面或API管理配置：
```bash
# 获取当前配置
curl http://localhost:8080/api/config

# 更新配置
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "meditation_frequency": "daily",
    "use_gnn": true,
    "similarity_threshold": 0.75
  }'
```

## 📈 监控和告警

### 监控指标
- **系统健康**: 服务状态、响应时间
- **冥思效果**: 节点减少率、优化时间
- **资源使用**: CPU、内存、磁盘
- **任务执行**: 成功率、执行时间

### 访问监控
1. **Grafana面板**: http://localhost:3000
   - 用户名: admin
   - 密码: admin

2. **Prometheus**: http://localhost:9090

### 告警配置
默认告警规则：
- 服务宕机超过5分钟
- 冥思任务失败
- 资源使用超过80%
- 响应时间超过10秒

## 🔄 维护操作

### 日常维护
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [service-name]

# 重启服务
docker-compose restart [service-name]

# 更新服务
./deploy.sh update
```

### 数据备份
```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz models/ state/ results/

# 恢复数据
tar -xzf backup-YYYYMMDD.tar.gz
```

### 故障排除
```bash
# 检查容器状态
docker ps -a

# 查看容器日志
docker logs [container-id]

# 进入容器调试
docker exec -it [container-id] /bin/bash

# 重启所有服务
docker-compose down && docker-compose up -d
```

## 🚨 常见问题

### 1. 端口冲突
如果端口被占用，修改 `docker-compose.yml` 中的端口映射。

### 2. 内存不足
增加Docker内存限制或减少服务数量。

### 3. 模型加载失败
检查 `models/` 目录是否有 `gnn_meditation_model.pth` 文件。

### 4. 服务启动失败
查看日志：`docker-compose logs -f meditation-service`

### 5. 定时任务不执行
检查scheduler服务状态：`docker-compose logs -f scheduler`

## 📋 升级指南

### 从v1.0升级到v2.0
```bash
# 1. 备份数据
tar -czf backup-v1.0.tar.gz models/ state/ results/

# 2. 停止旧服务
docker-compose down

# 3. 更新代码
git pull origin main

# 4. 重新部署
./deploy.sh update
```

### 版本兼容性
- **v2.0**: 支持GNN、性能优化、系统集成
- **v1.0**: 基础冥思规则，无深度学习

## 🔒 安全建议

### 生产环境安全
1. **修改默认密码**
   - Grafana: 修改admin密码
   - PostgreSQL: 修改数据库密码
   - Redis: 设置密码

2. **网络隔离**
   - 使用内部网络
   - 限制外部访问
   - 启用防火墙

3. **数据加密**
   - 敏感数据加密存储
   - 传输使用HTTPS
   - 定期更换密钥

### 访问控制
```bash
# 限制API访问
curl -X POST http://localhost:8080/api/config \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"require_auth": true}'
```

## 📞 支持与帮助

### 文档资源
- **项目文档**: https://github.com/Garylauchina/meditation-memory-system
- **API文档**: http://localhost:8080/api/docs
- **监控文档**: http://localhost:3000

### 问题反馈
1. 查看日志：`docker-compose logs`
2. 检查状态：`docker-compose ps`
3. 提交Issue：GitHub仓库

### 紧急恢复
```bash
# 停止所有服务
docker-compose down

# 从备份恢复
tar -xzf backup-YYYYMMDD.tar.gz

# 重新启动
docker-compose up -d
```

## 🎯 性能优化

### 硬件建议
- **CPU**: 8核以上（GNN训练）
- **内存**: 16GB以上（大规模图）
- **GPU**: 可选（加速GNN）

### 配置调优
```json
{
  "batch_size": 32,
  "learning_rate": 0.001,
  "similarity_threshold": 0.75,
  "cleanup_threshold": 0.1,
  "decay_rate": 0.01
}
```

### 监控指标
- **响应时间**: < 100ms
- **内存使用**: < 70%
- **CPU使用**: < 80%
- **磁盘IO**: < 50MB/s

---

**部署完成时间**: 2026-03-23 18:45
**版本**: v2.0 (生产环境部署版)
**状态**: 就绪，等待启动
```

echo "✅ 部署文档 README_DEPLOYMENT.md 已创建"
echo ""

echo "=== 阶段1完成：Docker容器化配置 ==="
echo "✅ 创建了完整的Docker部署配置"
echo "✅ 包含：Dockerfile、docker-compose.yml、部署脚本、服务文件"
echo "✅ 支持：多服务部署、监控系统、定时任务、数据持久化"
echo ""
echo "📁 部署目录内容："
ls -la
