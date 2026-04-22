# Five-Crystal Soft-Isolated Self-Regrowth Experiment v1

## Purpose

This document records the first five-crystal soft-isolated self-regrowth experiment.

The central question is whether a project-level crystal set can support meaningful architecture regrowth without access to source code, Docker assets, database state, or historical implementation files.

The five-crystal set used here is:
- problem-definition crystal
- architecture-evolution crystal
- methodology crystal
- retrieval-routing crystal
- system-memory crystal

---

## Inputs

### Reasoning-path crystals
- `docs/experiments/problem-definition-crystal-v1.json`
- `docs/experiments/architecture-evolution-crystal-v1.json`

### Protocol crystals
- `docs/experiments/methodology-crystal-v1.json`
- `docs/experiments/retrieval-routing-crystal-v1.json`

### Content crystal
- `docs/experiments/system-memory-crystal-v1.json`

### Protocol
- `docs/experiments/five-crystal-soft-isolated-regrowth-protocol-v1.md`

### Model
- `openai-codex/gpt-5.4`
- prompt-fed self-experiment

---

## Experimental Question

Can a new agent recover the project architecture neighborhood from the crystal set alone,
without implementation reference?

---

## Main Observation

### 1. The five-crystal set already supports project-level architecture regrowth
Using only the crystals,
the model could recover:
- the actual project problem definition
- why the project is not ordinary RAG, ordinary memory, or foundation-model replacement
- the architectural evolution path
- the layered protocol/content split inside the crystal set
- the system architecture skeleton
- the main shaping tensions

This is a strong signal that the crystal set has crossed an important threshold.

---

### 2. The current success level is architecture regrowth, not implementation regeneration
The experiment supports a clear distinction:
- architecture neighborhood regrowth is already possible
- implementation body regeneration is not yet reliable

The crystal set can recover:
- what the system is for
- how it evolved
- what layers and modules it needs
- what tensions and boundaries matter

But it cannot yet fully recover:
- exact APIs
- exact storage contracts
- exact process wiring
- deployment-complete operational behavior

---

### 3. Failure now becomes crystal-gap evidence
The parts that remain weak or missing are not random.
They cluster around:
- safety / security boundary
- resilience / recovery protocol
- verification / deployment discipline
- runtime-to-experience-to-protocol update loop

This means the experiment is already useful not only for regrowth validation,
but also for identifying the next crystal candidates.

---

### 4. Crystal-set role differentiation becomes more stable
After this experiment, the working role split becomes more stable:

#### Reasoning-path crystals
- problem-definition crystal
- architecture-evolution crystal

#### Protocol crystals
- methodology crystal
- retrieval-routing crystal

#### Content crystal
- system-memory crystal

This should still be treated as experimental working language,
but it now rests on multiple connected experiments.

---

## Main Working Conclusion

The first five-crystal soft-isolated self-regrowth experiment suggests that a project-level crystal set can already support architecture regrowth without source code.

What it currently does best:
- preserve problem identity
- preserve architecture evolution logic
- preserve protocol/content layering
- regrow a coherent architecture neighborhood

What it does not yet fully do:
- regenerate implementation details
- restore deployment-complete operational structure

---

## Current Consequences

This result directly supports the next line of work:
- treating crystal failures as crystal-gap evidence
- extending the crystal set with protocol-oriented deployment crystals
- keeping architecture regrowth and implementation regeneration explicitly separate

It also strengthens the view that the project now has:
- reasoning-path crystals
- protocol crystals
- content crystals

as distinct but cooperating roles.

---

## Current Risk

This remains a self-experiment on one model.
What is supported:
- project-level architecture regrowth from five crystals
- stable layered interpretation of the crystal set

What is not yet fully proven:
- that all models can regrow equally well from the same crystal set
- that the current crystal set is sufficient for implementation regeneration
- that the current crystal inventory is near complete

---

## One-Sentence Summary

The first five-crystal soft-isolated self-regrowth experiment suggests that a small project-level crystal set can already recover the architecture neighborhood without source code, while regrowth failures expose the next missing crystal types.
