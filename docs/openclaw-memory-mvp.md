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
