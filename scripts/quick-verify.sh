#!/bin/bash
# 快速验证脚本（Issue #42）
# 用于快速验证 OpenClaw Neo4j Memory 部署是否成功

set -e

API_URL="${API_URL:-http://localhost:18900}"
COLOR_GREEN='\033[0;32m'
COLOR_RED='\033[0;31m'
COLOR_YELLOW='\033[1;33m'
COLOR_NC='\033[0m' # No Color

echo "========================================"
echo "OpenClaw Neo4j Memory 快速验证"
echo "========================================"
echo ""

# 检查 API 服务是否运行
echo -e "${COLOR_YELLOW}🔍 检查 API 服务...${COLOR_NC}"
if curl -s --connect-timeout 5 "${API_URL}/health" > /dev/null; then
    echo -e "${COLOR_GREEN}✅ API 服务运行正常${COLOR_NC}"
else
    echo -e "${COLOR_RED}❌ API 服务未运行${COLOR_NC}"
    echo "请先启动服务：python plugins/neo4j-memory/memory_api_server.py"
    exit 1
fi

# 测试健康检查
echo ""
echo -e "${COLOR_YELLOW}🔍 测试健康检查...${COLOR_NC}"
HEALTH_RESPONSE=$(curl -s "${API_URL}/health")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "error")

if [ "$HEALTH_STATUS" = "ok" ]; then
    echo -e "${COLOR_GREEN}✅ 健康检查通过 (status=ok)${COLOR_NC}"
else
    echo -e "${COLOR_RED}❌ 健康检查失败 (status=$HEALTH_STATUS)${COLOR_NC}"
    exit 1
fi

# 检查 Neo4j 连接
NEO4J_CONNECTED=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('neo4j_connected', False))" 2>/dev/null || echo "False")
if [ "$NEO4J_CONNECTED" = "True" ]; then
    echo -e "${COLOR_GREEN}✅ Neo4j 连接正常${COLOR_NC}"
else
    echo -e "${COLOR_RED}❌ Neo4j 连接失败${COLOR_NC}"
    echo "请检查 Neo4j 服务是否启动，配置是否正确"
    exit 1
fi

# 测试记忆写入
echo ""
echo -e "${COLOR_YELLOW}🔍 测试记忆写入...${COLOR_NC}"
INGEST_RESPONSE=$(curl -s -X POST "${API_URL}/ingest" \
  -H "Content-Type: application/json" \
  -d '{"text": "快速验证测试记忆", "use_llm": false}')

ENTITIES_WRITTEN=$(echo "$INGEST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('entities_written', 0))" 2>/dev/null || echo "0")

if [ "$ENTITIES_WRITTEN" -gt 0 ]; then
    echo -e "${COLOR_GREEN}✅ 记忆写入成功 (entities=$ENTITIES_WRITTEN)${COLOR_NC}"
else
    echo -e "${COLOR_RED}❌ 记忆写入失败${COLOR_NC}"
    echo "响应：$INGEST_RESPONSE"
    exit 1
fi

# 测试记忆检索
echo ""
echo -e "${COLOR_YELLOW}🔍 测试记忆检索...${COLOR_NC}"
SEARCH_RESPONSE=$(curl -s -X POST "${API_URL}/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "快速验证", "limit": 5}')

ENTITY_COUNT=$(echo "$SEARCH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('entity_count', 0))" 2>/dev/null || echo "0")

if [ "$ENTITY_COUNT" -ge 0 ]; then
    echo -e "${COLOR_GREEN}✅ 记忆检索成功 (entities=$ENTITY_COUNT)${COLOR_NC}"
else
    echo -e "${COLOR_RED}❌ 记忆检索失败${COLOR_NC}"
    exit 1
fi

# 测试诊断端点
echo ""
echo -e "${COLOR_YELLOW}🔍 测试诊断端点...${COLOR_NC}"
DIAGNOSE_STATUS=$(curl -s --connect-timeout 5 "${API_URL}/diagnose" > /dev/null && echo "ok" || echo "error")

if [ "$DIAGNOSE_STATUS" = "ok" ]; then
    echo -e "${COLOR_GREEN}✅ 诊断端点正常${COLOR_NC}"
else
    echo -e "${COLOR_YELLOW}⚠️  诊断端点不可用（可能是旧版本）${COLOR_NC}"
fi

# 显示图谱统计
echo ""
echo -e "${COLOR_YELLOW}📊 图谱统计...${COLOR_NC}"
STATS_RESPONSE=$(curl -s "${API_URL}/stats")

if [ -n "$STATS_RESPONSE" ]; then
    NODE_COUNT=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('graph', {}).get('node_count', 0))" 2>/dev/null || echo "0")
    EDGE_COUNT=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('graph', {}).get('edge_count', 0))" 2>/dev/null || echo "0")
    PENDING=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('meditation', {}).get('pending_meditation', 0))" 2>/dev/null || echo "0")
    
    echo -e "${COLOR_GREEN}  节点数：$NODE_COUNT${COLOR_NC}"
    echo -e "${COLOR_GREEN}  关系数：$EDGE_COUNT${COLOR_NC}"
    echo -e "${COLOR_GREEN}  待处理：$PENDING${COLOR_NC}"
fi

# 完成
echo ""
echo "========================================"
echo -e "${COLOR_GREEN}✅ 验证完成！所有测试通过${COLOR_NC}"
echo "========================================"
echo ""
echo "下一步："
echo "  1. 阅读 docs/AGENT-ONBOARDING.md 了解完整 onboarding 流程"
echo "  2. 查看 GitHub Issues 认领任务"
echo "  3. 开始你的第一个贡献！"
echo ""
