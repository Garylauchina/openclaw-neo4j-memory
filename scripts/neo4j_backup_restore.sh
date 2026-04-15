#!/usr/bin/env bash
set -euo pipefail

# Minimal backup/restore helper for docker-compose Neo4j experiments.
# Intended for local MVP testing before importing external corpora.

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${PROJECT_DIR}/backups"
SERVICE_NAME="neo4j"
CONTAINER_NAME="neo4j-memory"
DATABASE_NAME="${NEO4J_DATABASE:-neo4j}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DUMP_NAME_DEFAULT="${DATABASE_NAME}-${TIMESTAMP}.dump"

usage() {
  cat <<EOF
Usage:
  $(basename "$0") backup [dump-name]
  $(basename "$0") restore <dump-file>
  $(basename "$0") list

Examples:
  $(basename "$0") backup
  $(basename "$0") backup before-corpus-test.dump
  $(basename "$0") restore backups/neo4j-20260415-153000.dump
EOF
}

ensure_backup_dir() {
  mkdir -p "$BACKUP_DIR"
}

backup_db() {
  ensure_backup_dir
  local dump_name="${1:-$DUMP_NAME_DEFAULT}"
  local dump_path="$BACKUP_DIR/$dump_name"

  echo "[1/3] stopping memory-api and mcp-server"
  docker compose -f "$PROJECT_DIR/docker-compose.yml" stop memory-api mcp-server >/dev/null

  echo "[2/3] creating dump: $dump_path"
  docker exec "$CONTAINER_NAME" neo4j-admin database dump "$DATABASE_NAME" --to-path=/tmp >/dev/null
  docker cp "$CONTAINER_NAME:/tmp/${DATABASE_NAME}.dump" "$dump_path"
  docker exec "$CONTAINER_NAME" rm -f "/tmp/${DATABASE_NAME}.dump"

  echo "[3/3] restarting memory-api and mcp-server"
  docker compose -f "$PROJECT_DIR/docker-compose.yml" start memory-api mcp-server >/dev/null

  echo "Backup created: $dump_path"
}

restore_db() {
  local source_dump="${1:-}"
  if [[ -z "$source_dump" ]]; then
    echo "restore requires a dump file" >&2
    usage
    exit 1
  fi
  if [[ ! -f "$source_dump" ]]; then
    echo "dump file not found: $source_dump" >&2
    exit 1
  fi

  echo "[1/4] stopping services"
  docker compose -f "$PROJECT_DIR/docker-compose.yml" stop memory-api mcp-server neo4j >/dev/null

  echo "[2/4] starting neo4j only"
  docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d neo4j >/dev/null
  sleep 8

  echo "[3/4] loading dump from $source_dump"
  docker cp "$source_dump" "$CONTAINER_NAME:/tmp/${DATABASE_NAME}.dump"
  docker exec "$CONTAINER_NAME" neo4j-admin database load "$DATABASE_NAME" --from-path=/tmp --overwrite-destination=true >/dev/null
  docker exec "$CONTAINER_NAME" rm -f "/tmp/${DATABASE_NAME}.dump"

  echo "[4/4] restarting all services"
  docker compose -f "$PROJECT_DIR/docker-compose.yml" restart neo4j >/dev/null
  sleep 8
  docker compose -f "$PROJECT_DIR/docker-compose.yml" start memory-api mcp-server >/dev/null

  echo "Restore completed from: $source_dump"
}

list_backups() {
  ensure_backup_dir
  ls -lh "$BACKUP_DIR"
}

cmd="${1:-}"
case "$cmd" in
  backup)
    backup_db "${2:-}"
    ;;
  restore)
    restore_db "${2:-}"
    ;;
  list)
    list_backups
    ;;
  *)
    usage
    exit 1
    ;;
esac
