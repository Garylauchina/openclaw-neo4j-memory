FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY memory_api_server.py .
COPY meditation_memory/ ./meditation_memory/
COPY scripts/ ./scripts/
# cognitive_engine 是可选模块，存在时才复制
# cognitive_engine 是可选模块（当前仓库已包含）
# 如果是从 plugins/neo4j-memory/ 子目录构建，可注释此行
COPY cognitive_engine/ ./cognitive_engine/

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:18900/health || exit 1

EXPOSE 18900

CMD ["uvicorn", "memory_api_server:app", "--host", "0.0.0.0", "--port", "18900"]
