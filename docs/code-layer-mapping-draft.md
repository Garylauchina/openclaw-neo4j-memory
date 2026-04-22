# Code Layer Mapping Draft

## Purpose

This draft maps the current repository code areas into the new four-stage mainline:

- memory
- experience
- knowledge crystal
- Agent-to-Agent transfer

This is a descriptive map of the current codebase, not a final refactor plan.

---

## Four-Layer Mainline Reminder

### Layer 1. Memory
Retention, provenance, graph persistence, source integrity.

### Layer 2. Experience
Reflection, meditation, candidate generation, processed cognition, feedback integration.

### Layer 3. Knowledge Crystal
Fold / unfold, crystal structure, convergence fidelity, calibration-aware crystal design.

### Layer 4. Agent-to-Agent Transfer
Cross-agent reconstruction, crystal injection, target-side adaptation rebuild, transfer-side understanding.

---

## Current Repository Areas

### `meditation_memory/`
**Primary layer:** Experience
**Secondary layer:** Memory

Why:
- this is the operational heart of reflection / meditation / candidate generation
- includes processing logic that turns stored material into processed cognition
- also touches graph persistence and stored memory state

Sub-reading:
- `graph_store.py` -> Memory / Experience boundary
- `memory_system.py` -> Memory / Experience boundary
- `subgraph_context.py` -> Experience / injection support
- `meditation_worker.py` -> Experience runtime orchestration
- `meditation_scheduler.py` -> Experience process scheduling
- `entity_extractor.py` -> Memory-to-Experience material extraction

Current interpretation:

## `meditation_memory/` is mostly the Experience layer,
with strong dependencies on the Memory layer.

---

### `memory_api_server.py`
**Primary layer:** Memory
**Secondary layer:** Experience

Why:
- API surface for storage, retrieval, meditation triggering, and runtime inspection
- serves both raw memory operations and processed cognition control

Current interpretation:
- operational gateway into lower layers
- not itself a crystal/transfer layer yet

---

### `cognitive_engine/`
**Primary layer:** Experience
**Secondary layer:** Knowledge Crystal

Why:
- contains higher-order behavior/guidance pieces such as:
  - `strategy_distiller.py`
  - `learning_guard.py`
  - `belief_integration.py`
  - `meta_learning_system.py`
- these are mostly about processed cognition and adaptation signals
- some pieces are conceptually upstream of crystal-layer rules

Current interpretation:

## `cognitive_engine/` is mostly an Experience-layer reference / adaptation reservoir,
with some future crystal-facing relevance.

---

### `scripts/run_crystal_drift.py`
**Primary layer:** Knowledge Crystal

Why:
- explicit fold/unfold experimentation
- crystal prompt design
- model-specific unfold rules
- drift comparison
- reasoning-frame induction experiments

Current interpretation:

## this is one of the clearest current crystal-layer files.

---

### `scripts/run_growth_drift.py`
**Primary layer:** Knowledge Crystal

Why:
- recursive growth / drift behavior
- fold/unfold control and misfolding analysis

---

### `scripts/run_raw_reflection.py`
**Primary layer:** Experience
**Secondary layer:** Knowledge Crystal

Why:
- direct reflection from raw slices
- upstream experiment for better experience formation
- feeds crystal thinking but is not itself the final crystal object

---

### `scripts/build_raw_reflection_input.py`
**Primary layer:** Experience
**Secondary layer:** Memory

Why:
- builds source-near experiment inputs from retained material
- helps transform stored material into reflection-ready form

---

### `scripts/prepare_longmemeval_sample.py`
**Primary layer:** Memory
**Secondary layer:** Knowledge Crystal

Why:
- corpus preparation
- benchmark substrate preparation
- supports later crystal evaluation

---

### `scripts/test_corpus_import.py`
**Primary layer:** Memory

Why:
- import pipeline verification
- source-side integrity and ingestion testing

---

### `scripts/workspace_import.py`
**Primary layer:** Memory

Why:
- import from workspace material into graph memory substrate

---

### `scripts/migrate_workspace_to_neo4j.py`
**Primary layer:** Memory

Why:
- memory import / migration logic

---

### `scripts/audit_*`
**Primary layer:** mixed

More precise reading:
- graph-quality / truncation / source audits -> Memory
- meditation-outcome / binding / probe-overlap audits -> Experience
- claim-layer / higher-order outcome / crystal-adjacent audits -> Experience / Knowledge Crystal boundary

Current interpretation:
- audits are diagnostic tools across layers
- they should eventually be grouped by the four-layer model

---

### `openclaw_memory_mvp.py`
**Primary layer:** Cross-layer packaging

Why:
- MVP wrapper surface
- packages capabilities spanning memory and experience, with future crystal relevance

---

### `skills/neo4j-memory.md`
**Primary layer:** Cross-layer packaging / interface

Why:
- user-facing entry layer
- operational interface across multiple deeper layers

---

### `docs/`
**Primary layer:** mixed, increasingly architectural

Important current docs by layer:

#### Memory / Experience leaning
- `docs/openclaw-memory-mvp.md`
- `docs/longmemeval-sample-plan.md`

#### Knowledge Crystal / Transfer leaning
- `docs/convergence-fidelity-draft.md`
- `docs/rule-discovery-bench-draft.md`
- `docs/two-layer-crystal-boundary-draft.md`
- `docs/architecture-mainline-draft.md`
- `docs/issue-layer-mapping-draft.md`

Current interpretation:

## the docs directory is already becoming the main place where the new architecture is being clarified before code movement.

---

### `tmp/`
**Primary layer:** experimental workspace

Why:
- contains experiment artifacts across layers
- many current crystal / unfold / calibration outputs live here

Current interpretation:
- temporary but strategically important
- should later be split conceptually into memory-, experience-, crystal-, and transfer-experiment outputs

---

### `plugins/neo4j-memory/`
**Primary layer:** historical / compatibility mirror

Why:
- no longer the main development path
- useful for reference and comparison
- should not be treated as the active architecture center

Current interpretation:

## historical reference layer, not current mainline.

---

### `archive/`
**Primary layer:** historical reference

### `meditation-deployment/`
**Primary layer:** operational / deployment history

These are not core mainline architecture layers.

---

## Current High-Level Reading of the Codebase

### Memory-heavy current areas
- parts of `meditation_memory/graph_store.py`
- parts of `meditation_memory/memory_system.py`
- `memory_api_server.py`
- migration / import scripts
- corpus preparation and import tests

### Experience-heavy current areas
- most of `meditation_memory/`
- most of `cognitive_engine/`
- raw reflection scripts
- meditation worker / scheduler
- outcome/binding audits

### Knowledge Crystal-heavy current areas
- `scripts/run_crystal_drift.py`
- `scripts/run_growth_drift.py`
- crystal / convergence / bench docs
- two-layer crystal boundary work
- calibration crystal prototype files in `tmp/`

### Agent-to-Agent Transfer-heavy current areas
Currently much more conceptual than code-heavy.
Mainly represented by:
- crystal injection experiments
- two-layer crystal thinking
- transfer-oriented docs
- #89 framing and current prototype work

---

## Immediate Architectural Consequence

The repo does not yet have a clean directory split matching the new mainline.

But the conceptual centers are already visible:
- Memory center
- Experience center
- Crystal experiment center
- Transfer concept center

This suggests that future code refactor, if done, should follow these centers rather than forcing arbitrary package moves too early.

---

## Status

This is a first descriptive code map for the architecture refactor branch.
Later versions should distinguish:
- stable structural areas
- active experiment areas
- legacy reference areas
- future migration targets
