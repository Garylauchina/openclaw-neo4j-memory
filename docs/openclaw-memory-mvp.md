# OpenClaw Neo4j Memory MVP

This document defines the first OpenClaw-first MVP packaging of the current Neo4j memory mainline.

## Positioning

- **tool** = atomic capability interface
- **skill** = task-level orchestration / workflow

This MVP does not introduce a new memory architecture. It only exposes the current stable mainline through a small OpenClaw-facing surface.

## Mainline sources

Current mainline:
- `meditation_memory/`
- `memory_api_server.py`
- selected `scripts/`

## MVP tool surface

### 1. `ingest_memory(text, metadata?, use_llm?)`
Use for writing important conversation facts into memory.

Maps to:
- `MemorySystem.ingest(...)`

### 2. `retrieve_context(query, options?)`
Use before answering when relevant memory may exist.

Maps to:
- `MemorySystem.retrieve_context(...)`

### 3. `build_prompt_context(query, options?)`
Use when the caller wants a ready-to-inject prompt augmentation.

Maps to:
- `MemorySystem.build_prompt(...)`

### 4. `memory_stats()`
Use for health / observability / memory-scale checks.

Maps to:
- `MemorySystem.get_stats()`

## Suggested skill workflow

### Skill: conversation memory assist
1. Before answering, optionally call `retrieve_context`
2. If richer injection is needed, call `build_prompt_context`
3. After the interaction, if durable information appeared, call `ingest_memory`
4. Occasionally inspect `memory_stats`

### Skill: low-frequency maintenance
- Trigger meditation separately and infrequently
- Keep meditation outside the core answer path
- Do not mix meditation scheduling into the basic conversation-memory skill

## Explicit non-goals

This MVP does not include:
- MCP re-abstraction
- workspace bulk import
- relation/world-model expansion
- plugin rewrite
- full deployment packaging refresh

## Repo delivery in this MVP

- minimal wrapper: `openclaw_memory_mvp.py`
- MVP mapping doc: `docs/openclaw-memory-mvp.md`
- skill guidance update: `skills/neo4j-memory.md`
- external corpus test import script: `scripts/test_corpus_import.py`
- local backup/restore helper: `scripts/neo4j_backup_restore.sh`

## Safe experiment flow for external corpora

When testing external corpora, use this order:

1. create a backup
2. run a dry-run corpus import
3. run a small real import
4. validate retrieval / stats
5. restore if the experiment polluted the graph

### Backup

```bash
bash scripts/neo4j_backup_restore.sh backup
```

### List existing backups

```bash
bash scripts/neo4j_backup_restore.sh list
```

### Dry-run corpus import

```bash
python scripts/test_corpus_import.py ./sample-corpus --dry-run
```

### Small real import

```bash
python scripts/test_corpus_import.py ./sample-corpus --limit-files 5 --chunk-chars 1200
```

### Single-file import

```bash
python scripts/test_corpus_import.py ./sample-corpus/example.md
```

### Restore

```bash
bash scripts/neo4j_backup_restore.sh restore backups/<your-dump>.dump
```

## Minimal usage examples

### Example A: safe first experiment

```bash
bash scripts/neo4j_backup_restore.sh backup
python scripts/test_corpus_import.py ./sample-corpus --dry-run
python scripts/test_corpus_import.py ./sample-corpus --limit-files 3
```

### Example B: restore after a noisy import

```bash
bash scripts/neo4j_backup_restore.sh list
bash scripts/neo4j_backup_restore.sh restore backups/neo4j-20260415-153000.dump
```

### Example C: import without LLM extraction

```bash
python scripts/test_corpus_import.py ./sample-corpus --no-llm --limit-files 2
```

Note: the backup/restore helper uses an offline `neo4j-admin` dump/load flow against the docker volume, so it will briefly stop Neo4j during backup and restore.

These helpers are intentionally for MVP experimentation, not a final production migration pipeline.
