.PHONY: start stop restart status logs clean migrate backup restore rebuild help

# ========================================
# Neo4j 记忆系统 — Makefile 快捷命令
# ========================================

start:          ## 启动全部服务
	docker compose up -d

stop:           ## 停止全部服务
	docker compose down

restart:        ## 重启全部服务
	docker compose restart

logs:           ## 查看日志（tail -50，Ctrl+C 退出）
	docker compose logs -f --tail=50

logs-api:       ## 只看 API 日志
	docker compose logs -f --tail=50 memory-api

logs-neo4j:     ## 只看 Neo4j 日志
	docker compose logs -f --tail=50 neo4j

status:         ## 查看服务状态 + 健康检查
	@docker compose ps
	@echo ""
	@echo "=== API Health ==="
	@curl -s http://localhost:$${API_PORT:-18900}/health 2>/dev/null | python3 -m json.tool || echo "API 未就绪"
	@echo ""
	@echo "=== Graph Stats ==="
	@curl -s http://localhost:$${API_PORT:-18900}/stats 2>/dev/null | python3 -m json.tool || echo "API 未就绪"

rebuild:        ## 重新构建镜像并启动
	docker compose up -d --build

clean:          ## 停止并删除全部数据（⚠️ 不可恢复）
	@read -p "确定要删除所有数据吗？(y/N) " ans && [ $${ans:-N} = y ] || exit 1
	docker compose down -v

backup:         ## 备份 Neo4j 数据库（使用 neo4j-admin dump）
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	docker compose exec neo4j neo4j-admin database dump neo4j --to-path=/tmp/backups --to-stdout > backups/neo4j-dump-$${TIMESTAMP}.dump 2>/dev/null; \
	if [ -s "backups/neo4j-dump-$${TIMESTAMP}.dump" ]; then \
		echo "✅ 备份完成: backups/neo4j-dump-$${TIMESTAMP}.dump"; \
	else \
		echo "⚠️  neo4j-admin dump 不可用，尝试文件备份..."; \
		docker compose exec -T neo4j tar czf - -C /var/lib/neo4j/data/databases neo4j > backups/neo4j-backup-$${TIMESTAMP}.tar.gz; \
		echo "✅ 文件备份完成: backups/neo4j-backup-$${TIMESTAMP}.tar.gz"; \
	fi

restore:        ## 从 dump 恢复（make restore FILE=backups/neo4j-dump-xxx.dump）
	@if [ -z "$(FILE)" ]; then echo "用法: make restore FILE=backups/neo4j-dump-xxx.dump"; exit 1; fi
	@echo "⚠️  恢复将覆盖现有数据，确认继续？(Ctrl+C 取消)"
	@sleep 3
	docker compose exec -T neo4j neo4j-admin database load neo4j --from-path=/tmp < $(FILE) || \
	(echo "⚠️  neo4j-admin load 失败，尝试从 tar.gz 恢复..." && \
	 docker compose down && \
	 docker compose up -d neo4j && sleep 5 && \
	 docker compose exec neo4j rm -rf /data/databases/neo4j && \
	 docker compose exec -T neo4j tar xzf - -C /var/lib/neo4j/data/databases < $(FILE) && \
	 docker compose restart neo4j && \
	 echo "✅ 文件恢复完成，请等待 Neo4j 启动后验证")
	@echo "✅ 恢复完成，请重启服务: make restart"

migrate:        ## 从远程 Neo4j 迁移数据（需先配置环境变量）
	@if [ -z "$$MIGRATE_SSH_USER" ]; then \
		echo "请先设置环境变量:"; \
		echo "  export MIGRATE_SSH_USER=user"; \
		echo "  export MIGRATE_SSH_HOST=remote-host"; \
		echo "  export MIGRATE_NEO4J_PASSWORD=xxx"; \
		echo "  export MIGRATE_LOCAL_NEO4J_PASSWORD=yyy"; \
		echo "或使用 .env.migrate 文件: source .env.migrate && make migrate"; \
		exit 1; \
	fi
	python3 scripts/migrate_from_remote.py

help:           ## 显示此帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
