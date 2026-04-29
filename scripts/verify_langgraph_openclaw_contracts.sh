#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> LangGraph × OpenClaw compatibility verification"
echo "Repo: $ROOT_DIR"

echo
echo "[1/3] Plugin host smoke + helper/runtime contract tests"
node --test \
  plugins/langgraph-orchestrator/runtime-helpers.test.mjs \
  plugins/langgraph-orchestrator/runtime-client.test.mjs \
  plugins/langgraph-orchestrator/plugin-host-smoke.test.mjs

echo
echo "[2/3] TypeScript typecheck"
if [ -x ./node_modules/.bin/tsc ]; then
  ./node_modules/.bin/tsc --noEmit
else
  echo "SKIP: ./node_modules/.bin/tsc not found"
  echo "      Install project dependencies before using typecheck as a hard gate."
fi

echo
echo "[3/3] Runtime endpoint contract checklist"
cat <<'CHECKLIST'
Manual/runtime-backed checks to run when validating a real version pair:
- GET /health succeeds against the LangGraph runtime
- POST /runtime/before-agent-start returns a compatible payload
- POST /runtime/agent-end degrades safely on runtime failure
- POST /runtime/before-compaction returns a compatible archive/checkpoint payload
- OpenClaw main reply path stays non-blocking if the runtime is unavailable
CHECKLIST

echo
echo "✅ Local contract verification completed"
