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
python scripts/test_corpus_import.py ./sample-corpus --limit-files 5 --chunk-chars 1200 --source-tag my-test-corpus
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
python scripts/test_corpus_import.py ./sample-corpus --dry-run --source-tag my-test-corpus
python scripts/test_corpus_import.py ./sample-corpus --limit-files 3 --source-tag my-test-corpus
```

### Example B: restore after a noisy import

```bash
bash scripts/neo4j_backup_restore.sh list
bash scripts/neo4j_backup_restore.sh restore backups/neo4j-20260415-153000.dump
```

### Example C: import without LLM extraction

```bash
python scripts/test_corpus_import.py ./sample-corpus --no-llm --limit-files 2 --source-tag my-test-corpus
```

## Minimal source scoping

The MVP import script now supports minimal experiment tracking metadata:

- `--source-tag` to label the corpus or experiment
- `--import-batch` to force a stable batch id when needed

Example:

```bash
python scripts/test_corpus_import.py ./sample-corpus \
  --limit-files 2 \
  --source-tag longtest-dialogue-v1 \
  --import-batch run-001
```

This does not provide full graph isolation yet. It only ensures experiment metadata is attached consistently during import.

Note: the backup/restore helper uses an offline `neo4j-admin` dump/load flow against the docker volume, so it will briefly stop Neo4j during backup and restore.

These helpers are intentionally for MVP experimentation, not a final production migration pipeline.

## LongMemEval sample preparation

A minimal preparation helper is available for the first long-memory benchmark entry:

```bash
python scripts/prepare_longmemeval_sample.py path/to/longmemeval_oracle.json --limit 2
```

Then run a dry-run import:

```bash
python scripts/test_corpus_import.py tmp/longmemeval-sample \
  --dry-run \
  --source-tag longmemeval-sample \
  --import-batch longmemeval-oracle-run-001
```

See also:
- `docs/longmemeval-sample-plan.md`

## Source-scoped probe audit

After a source-tagged import probe, you can inspect the resulting entity shape with:

```bash
python scripts/audit_source_entities.py \
  --source-tag longmemeval-probe-v4 \
  --import-batch longmemeval-oracle-run-004
```

This is intended for probe analysis, not graph mutation.

You can also inspect whether a probe retained any non-anchoring graph relations:

```bash
python scripts/audit_source_relations.py \
  --source-tag longmemeval-probe-v6 \
  --import-batch longmemeval-oracle-run-006
```

To diagnose whether the rules extractor produced any relations before ingest, use:

```bash
python scripts/diagnose_rule_relation_retention.py \
  tmp/longmemeval-sample-noscaffold/gpt4_2487a7cb.md \
  --chunk-chars 1200 \
  --limit-chunks 5
```
