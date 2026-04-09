#!/bin/bash
# Quick verification script for memory migration
# Usage: ./quick-verify.sh <source_uri> <target_uri> <password>

set -e

SOURCE_URI=${1:-bolt://localhost:7687}
TARGET_URI=${2:-bolt://localhost:7688}
PASSWORD=${3:-neo4j}
USER="neo4j"

echo "🔍 Neo4j Memory Migration Quick Verification"
echo "============================================"
echo "Source: $SOURCE_URI"
echo "Target: $TARGET_URI"
echo ""

# Run verification
python3 neo4j_migrate.py verify \
    --src-uri "$SOURCE_URI" \
    --src-user "$USER" \
    --src-password "$PASSWORD" \
    --dst-uri "$TARGET_URI" \
    --dst-user "$USER" \
    --dst-password "$PASSWORD"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All checks passed!"
else
    echo ""
    echo "❌ Verification failed!"
    exit 1
fi
