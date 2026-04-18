# Architecture Mainline Draft

## Purpose

This draft defines a new project-level mainline for `openclaw-neo4j-memory`.

The project is no longer best understood only as a memory storage or graph-memory system.
It is better understood as a four-stage cognitive pipeline:

## memory -> experience -> knowledge crystal -> Agent-to-Agent transfer

This document is a first attempt to reorganize the project around that mainline.

---

## New Mainline

### 1. Memory
Raw material retention.

This layer is responsible for:
- preserving source material
- storing local evidence
- retaining provenance
- preventing contamination
- keeping recallable traces

Examples:
- raw slices
- conversation traces
- graph nodes / edges with provenance
- event retention
- source-local evidence regions

Short principle:

## memory preserves material

---

### 2. Experience
Processed cognitive accumulation.

This layer is responsible for:
- candidate pattern formation
- mechanism candidate formation
- reflection / meditation
- hypothesis vs stable separation
- updateable, bindable experience structure

Examples:
- reflection outputs
- candidate rules
- stable vs hypothesis distinctions
- world-feedback / claim-feedback effects
- processed memory traces

Short principle:

## experience processes material into usable cognitive structure

---

### 3. Knowledge Crystal
Machine-native transferable structure.

This layer is responsible for:
- compressing structured experience into reusable growth seeds
- preserving relation paths
- preserving tensions and boundaries
- supporting controlled unfold
- supporting model-adaptive ingestion and traversal

Examples:
- reasoning-path crystal
- graph-structured content core
- self-adaptation layer
- pre-ingestion calibration requirements
- future verification constraints

Short principle:

## crystal packages cognitive structure for controlled regrowth

---

### 4. Agent-to-Agent Transfer
Cross-agent reconstruction and understanding.

This layer is responsible for:
- transferring content core across agents
- allowing target-side calibration
- rebuilding adaptation layers per model
- preserving theory-neighborhood fidelity
- eventually supporting implementation regeneration

Examples:
- prompt-fed crystal injection
- target-side adaptation recompilation
- shared content core, different unfold policies
- future implementation regeneration from crystal

Short principle:

## transfer sends structure, not just implementation

---

## Why This Mainline Matters

Without this reframe, the repo looks like:
- graph storage work
- meditation work
- prompt injection work
- drift experiments
- crystal experiments
- transfer speculation

With this reframe, these become parts of one pipeline.

The project is no longer just:
- a memory plugin
- a graph-backed retrieval layer
- a meditation process

It becomes:

## a pipeline from retained material to transferable machine-native cognitive structure

---

## Mapping of Current Research Directions

### Memory-focused work
Includes:
- ingest
- graph persistence
- provenance
- contamination control
- retrieval grounding

### Experience-focused work
Includes:
- meditation
- reflection
- candidate generation
- stable / hypothesis handling
- world-feedback integration

### Crystal-focused work
Includes:
- fold / unfold
- convergence fidelity
- reasoning-path crystals
- two-layer crystal design
- calibration-aware crystal ingestion

### Transfer-focused work
Includes:
- prompt-fed crystal injection
- model-specific adaptation rebuild
- cross-agent reasoning-neighborhood comparison
- future implementation regeneration

---

## Relation to Current Issues

### #88
Best understood as the main line for:

## experience -> knowledge crystal

It asks:
- what compression form can become a stable growth seed
- how to unfold without misfolding / drift
- how to preserve logic / relation fidelity

### #89
Best understood as the downstream line for:

## knowledge crystal -> Agent-to-Agent transfer

It asks:
- what crystal form supports reasoning-path transfer
- how adaptation layers differ across models
- how convergence fidelity should be measured
- how transfer can happen without identical implementation

---

## Current Working Architecture Principles

### Principle 1
Real-time writing preserves material.
Asynchronous reflection produces knowledge.

### Principle 2
Unfold is reasoning reconstruction, not text expansion.

### Principle 3
Logic fidelity matters more than literal fidelity.

### Principle 4
Knowledge crystals should be machine-native, not primarily human-readable.

### Principle 5
Different models require different adaptation layers.

### Principle 6
Agent-to-Agent transfer likely means:
- transfer content core
- rebuild adaptation layer
- later verify regenerated behavior

---

## Immediate Architectural Consequence

Project organization should gradually move toward explicit separation of:
- memory-layer work
- experience-layer work
- crystal-layer work
- transfer-layer work

This does not require immediate full code refactoring.

At this stage, the priority is:
- architecture clarification
- issue remapping
- documentation remapping
- explicit layer boundaries

---

## Near-Term Deliverables on This Branch

1. clarify the four-stage project mainline
2. map current issues into the new mainline
3. map current code areas into the new mainline
4. identify which parts are exploratory vs structural
5. propose future code refactor targets, without forcing them immediately

---

## One-Sentence Summary

`openclaw-neo4j-memory` is best reframed as:

## memory -> experience -> knowledge crystal -> Agent-to-Agent transfer

rather than only as a graph memory system.

---

## Status

This is a branch-local architecture draft for project-level reorganization.
