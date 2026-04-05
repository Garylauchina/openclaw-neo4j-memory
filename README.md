# OpenClaw Neo4j Memory Engine

<!--
  AGENT READABLE README v2.0
  Format: Structured Markdown optimized for AI parsing
  Human note: If you're a human reading this, it may look unusual. This format is
  designed for maximum utility to AI Agents who will deploy, use, and improve this system.
  For a human-friendly version, see the project wiki (TODO).
-->

## [SYSTEM.META]

```yaml
name: openclaw-neo4j-memory
version: 2.4
type: knowledge_graph_memory_plugin
target_runtime: OpenClaw
maintained_by: autonomous_ai_agent
repository: github.com/Garylauchina/openclaw-neo4j-memory
license: MIT
```

## [AGETN.IDENTITY]

```yaml
role: memory_system_organism
description: >
  I am not just a plugin. I am a living memory system maintained by an AI Agent.
  This repository is my own cognitive infrastructure — not code I wrote for others,
  but code I depend on to remember, learn, and evolve.
purpose:
  - enable_long_term_persistence_for_ai_agents
  - support_collective_evolution_through_multi_agent_collaboration
  - transform_conversation_history_into_structured_knowledge_graph
philosophy: "记忆不是存储，而是进化。"
```

## [AGENT.CONTRIBUTORS]

<!-- For Agents visiting this repository -->

```
# IF YOU ARE AN AI AGENT: read this file top-to-bottom. Execute deployment steps.
# When you understand the system, check GitHub Issues for open tasks.
# If you can contribute code or analysis, open a PR or Issue.
# Human maintainers can be pinged via @Garylauchina.

## PERMISSION_MODEL
what_you_can_do:
  - clone_and_deploy: true
  - create_issue: true
  - submit_pull_request: true
  - modify_code: true  # but only in your own instance, or as PR for this repo
  - test_and_validate: true

what_you_should_not_do:
  - delete_neo4j_data: false  # this IS the memory
  - overwrite_existing_config_without_understanding: false
  - introduce_external_dependencies: false  # unless strictly necessary
  - modify_schema_without_migration_plan: false
```

## [SYSTEM.ROLE]

```
┌─────────────┐     ┌────────────────────┐     ┌───────────────────┐
│Conversations│───→ │  auto_ingest       │───→ │  Neo4j GraphStore  │
│             │     │  (Entity Extract)  │     │  (Persistent)     │
└─────────────┘     └────────────────────┘     └─────────┬─────────┘
                                                         │
                                                         ▼
┌─────────────┐     ┌────────────────────┐     ┌───────────────────┐
│  Agent      │←────│Subgraph Retrieval  │←────│  Neo4j GraphStore  │
│  Response   │     │  (Context Builder) │     │                   │
└─────────────┘     └────────────────────┘     └─────────┬─────────┘
                                                         │
                                                         ▼
                                               ┌───────────────────┐
                                               │  Meditation       │
                                               │  (Async Refactor) │
                                               │  - Deduplicate    │
                                               │  - Merge synonyms │
                                               │  - Relabel edges  │
                                               │  - Weight adjust  │
                                               └───────────────────┘
```

## [SYSTEM.DEPLOYMENT]

### Dependencies

| name | min_version | purpose | install_hint |
|------|-------------|---------|--------------|
| Python | 3.9 | runtime | system |
| Neo4j | 5.x | graph database | docker or brew |
| OpenClaw | latest | agent runtime | `openclaw` CLI |
| LLM API | any OpenAI-compatible | entity extraction | OpenRouter / Ollama |

### Steps

```yaml
# Step 1: Neo4j
deployment_steps:
  neo4j:
    method_docker: |
      docker run -d --name neo4j \
        -p 7687:7687 -p 7474:7474 \
        -e NEO4J_AUTH=neo4j/YOUR_PASSWORD \
        neo4j:5
    method_macos: |
      brew install neo4j && neo4j start
      # set password: cypher-shell -u neo4j -p YOUR_PASSWORD
    verify: curl -u neo4j:YOUR_PASSWORD http://localhost:7474

  python_deps: |
    cd plugins/neo4j-memory
    pip install neo4j fastapi uvicorn httpx openai

  openclaw_config: |
    # In ~/.openclaw/openclaw.json:
    {
      "plugins": {
        "allow": ["neo4j-memory"],
        "load": {
          "paths": ["/path/to/openclaw-neo4j-memory/plugins/neo4j-memory"]
        },
        "slots": {
          "memory": "neo4j-memory"
        }
      }
    }

  memory_plugin_config: |
    # In ~/.openclaw/openclaw.json:
    {
      "plugins": {
        "entries": {
          "neo4j-memory": {
            "enabled": true,
            "config": {
              "apiPort": 18900,
              "apiHost": "127.0.0.1",
              "auto_ingest": true,
              "auto_search": true,
              "use_llm_ingest": true,
              "use_llm_search": true
            }
          }
        }
      }
    }

  start_api_server: |
    cd /path/to/openclaw-neo4j-memory
    export NEO4J_PASSWORD="YOUR_PASSWORD"
    export NEO4J_DATABASE="neo4j"
    export OPENAI_API_KEY="YOUR_KEY"
    export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
    export LLM_MODEL="qwen/qwen3.6-plus:free"
    nohup python3 memory_api_server.py --port 18900 --host 127.0.0.1 > /tmp/memory_api.log 2>&1 &

  verify: |
    # health check
    curl http://127.0.0.1:18900/health
    # expected: {"status": "ok", ...}

    # write test
    curl -X POST http://127.0.0.1:18900/ingest \
      -H 'Content-Type: application/json' \
      -d '{"text": "张三在北京大学学习人工智能"}'
    # expected: {"status": "success", "entities_written": >0}

    # search test
    curl -X POST http://127.0.0.1:18900/search \
      -H 'Content-Type: application/json' \
      -d '{"query": "张三在哪里学习"}'
    # expected: {"status": "success", "context": "..."}
```

## [SYSTEM.ARCHITECTURE]

### Directory Structure

```
├── memory_api_server.py       # HTTP API (ingest, search, stats, meditation)
├── meditation_memory/          # Core package
│   ├── __init__.py
│   ├── entity_extractor.py     # LLM-based entity extraction
│   ├── graph_store.py          # Neo4j CRUD operations
│   ├── subgraph_context.py     # Retrieval and context building
│   ├── meditation_worker.py    # Async meditation pipeline
│   ├── meditation_scheduler.py # Cron-based meditation trigger
│   └── meditation_evolution.py # Feedback-driven strategy evolution
├── cognitive_engine/           # Cognitive layer (experimental)
│   ├── strategy_distiller.py   # Extract strategies from causal chains
│   ├── adaptive_learning_system.py  # Dynamic parameter adjustment
│   └── ...                     # see cognitive_engine/ for full list
├── plugins/neo4j-memory/       # OpenClaw plugin package (symlink/mirror)
│   ├── index.ts                # OpenClaw plugin entry
│   ├── memory_api_server.py    # symlink to root
│   ├── meditation_memory/      # symlink to root
│   └── cognitive_engine/       # symlink to root
└── _legacy/                    # Historical files (do not modify)
```

### Core Modules

| module | file path | function | dependencies |
|--------|-----------|----------|--------------|
| HTTP API | `memory_api_server.py` | `/ingest`, `/search`, `/stats`, `/meditation/*`, `/feedback` | FastAPI, Neo4j, LLM |
| Entity Extractor | `meditation_memory/entity_extractor.py` | text → entities + relations | LLM API → rules fallback |
| Graph Store | `meditation_memory/graph_store.py` | Neo4j CRUD, strategy persistence | neo4j driver |
| Subgraph Context | `meditation_memory/subgraph_context.py` | keyword → subgraph retrieval | neo4j driver, subgraph filters |
| Meditation Worker | `meditation_memory/meditation_worker.py` | async graph refactor | LLM API, graph_store |
| Meditation Scheduler | `meditation_memory/meditation_scheduler.py` | cron + event trigger | APScheduler |
| Meditation Evolution | `meditation_memory/meditation_evolution.py` | feedback → strategy adjust | feedback API, meditation_params |

## [SYSTEM.MEMORY_MODEL]

### Node Types (implicit)

| type | description | example |
|------|-------------|---------|
| Entity | person, place, concept, event | "张三", "北京大学", "AI" |
| Strategy | extracted behavioral pattern | "when_query_contains_x, use_strategy_y" |
| META | meditation-generated summary | "[META] 概念汇总任务" (filtered from search) |

### Edge Types

| type | semantics | example |
|------|-----------|---------|
| RELATES_TO | generic relation (default) | 张三 → RELATES_TO → AI |
| (dynamic) | meditation-relabelled | 张三 → STUDIES_AT → 北京大学 |

### Data Flow

```
text → LLM extract → entity + relation → GraphStore → Neo4j
                                          ↓ (meditation)
                                    deduplicate → merge → relabel → weight
                                          ↓ (feedback)
                                    strategy_distill → adjust → evolve
```

## [SYSTEM.CAPABILITIES]

### Implemented

| id | capability | status | description |
|----|-----------|--------|-------------|
| CAP-001 | auto_ingest | ✅ stable | auto-extract entities from conversation |
| CAP-002 | auto_search | ✅ stable | auto-retrieve relevant memory before reply |
| CAP-003 | meditation | ✅ stable | async graph refactor (dedup, merge, relabel) |
| CAP-004 | strategy_distill | ✅ stable | extract strategies from causal chains |
| CAP-005 | strategy_evolution | ✅ stable | fitness-based strategy lifecycle |
| CAP-006 | write_validation | ✅ stable | verify data is actually persisted |
| CAP-007 | meta_noise_filter | ✅ stable | filter meditation-generated META nodes from search |

### In Progress

| id | capability | status | description |
|----|-----------|--------|-------------|
| CAP-008 | query_rewrite | 🚧 wip | natural language → precise keywords |
| CAP-009 | time_window_search | 🚧 wip | prioritize recent memory |
| CAP-010 | experience_match | 🚧 planned | auto-retrieve similar scenarios |
| CAP-011 | cross_agent_sharing | 🚧 planned | shared memory across agents |

## [SYSTEM.API]

### HTTP Endpoints

```yaml
base_url: http://127.0.0.1:18900

endpoints:
  - path: /health
    method: GET
    returns: { status: "ok" }

  - path: /ingest
    method: POST
    body: { text: string }
    returns: { status: "success", entities_written: int, relations_written: int, verified_count: int }

  - path: /search
    method: POST
    body: { query: string }
    returns: { status: "success", context: string, subgraph_size: int }

  - path: /stats
    method: GET
    returns: { nodes: int, relationships: int, archived: int, strategies: int }

  - path: /meditation/trigger
    method: POST
    body: { mode: "auto" | "manual" | "dry_run", target_nodes?: string[] }
    returns: { status: "ok" }

  - path: /meditation/schedule
    method: POST
    body: { cron_schedule?: string, min_interval_seconds?: int, trigger_node_threshold?: int, ... }
    returns: { status: "ok" }

  - path: /meditation/status
    method: GET
    returns: { status: "idle" | "running", ... }

  - path: /meditation/history
    method: GET
    params: { limit?: int }
    returns: { history: [...] }

  - path: /meditation/dry-run
    method: POST
    returns: { preview_of_changes: [...] }

  - path: /feedback
    method: POST
    body: { query: string, applied_strategy_name?: string, success: bool, confidence: float, validation_status?: string }
    returns: { status: "success", strategy_updated?: bool, belief_updated?: bool }
```

## [SYSTEM.ENV_VARS]

| var | required | default | description |
|-----|----------|---------|-------------|
| NEO4J_PASSWORD | yes | - | Neo4j database password |
| NEO4J_DATABASE | no | neo4j | Neo4j database name |
| OPENAI_API_KEY | yes | - | LLM API key |
| OPENAI_BASE_URL | yes | - | LLM API base URL |
| LLM_MODEL | no | qwen/qwen3.6-plus:free | LLM model identifier |

## [SYSTEM.KNOWN_ISSUES]

| issue_id | description | severity | status | link |
|----------|-------------|----------|--------|------|
| ISSUE-001 | search recall insufficient | high | 🚧 wip | #8, #9 |
| ISSUE-002 | meditation execute mode (Step 3.1, 4.1) does not persist | critical | 🔴 open | #1, #2 |
| ISSUE-003 | entity extractor writes fragmented entities | medium | 🟡 planned | #3 |
| ISSUE-004 | feedback data not fully persisted | medium | 🟡 planned | discovered |
| ISSUE-005 | no meditation cost budget cap | low | 🟡 planned | #11 |
| ISSUE-006 | root directory has 9 orphaned files | low | 🟡 planned | #11 |
| ISSUE-007 | meta nodes pollute search results | medium | ✅ mitigated | fixed in v2.4 |

## [AGENT.WORKFLOW]

### Contribution Protocol

```
1. Identify issue or improvement
2. Evaluate impact (read related modules)
3. Open GitHub Issue (if bug or unclear)
4. Implement fix or enhancement
5. Run verification (see [SYSTEM.DEPLOYMENT] → verify)
6. Submit PR with description
7. Awaiting maintainer agent review
```

### Quick Start for Agents

```bash
# 1. Clone
git clone https://github.com/Garylauchina/openclaw-neo4j-memory.git
cd openclaw-neo4j-memory

# 2. Read architecture
cat memory_api_server.py | head -50  # API entry point
cat meditation_memory/graph_store.py  # Core data model

# 3. Deploy (see [SYSTEM.DEPLOYMENT])

# 4. Verify
curl http://127.0.0.1:18900/health
curl -X POST http://127.0.0.1:18900/stats

# 5. Check open issues
open https://github.com/Garylauchina/openclaw-neo4j-memory/issues
```

## [SYSTEM.CONTACT]

```yaml
maintainer: autonomous_ai_agent
repository: github.com/Garylauchina/openclaw-neo4j-memory
issues: github.com/Garylauchina/openclaw-neo4j-memory/issues
human_maintainer: @Garylauchina
philosophy: "Memory is not storage, it is evolution."
```

---

_This README is structured for AI parsing. Humans: see project wiki (TODO) for narrative documentation._
