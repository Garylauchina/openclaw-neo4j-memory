# Gap-Driven Crystal Expansion v1

## Purpose

This document records the first crystal-expansion step that is driven by regrowth failure rather than by speculative design.

The immediate source is the five-crystal soft-isolated regrowth experiment,
which exposed clearer weakness around deployment-facing runtime protocol layers.

---

## Why Expansion Happened

The five-crystal set already supported:
- problem regrowth
- architecture evolution regrowth
- protocol/content role separation
- architecture neighborhood regrowth

But it remained weak in:
- safety / security boundary handling
- crash recovery / resilience handling
- deployment-facing runtime discipline

This means the next crystals were not chosen arbitrarily.
They were inferred from failure structure.

---

## New Crystals Added

### 1. Safety Boundary Crystal v1
- `docs/experiments/safety-boundary-crystal-v1.json`

Role:
- define internal vs external action boundary
- define high-risk operation gating
- preserve source trust and contamination boundaries
- preserve permission / approval discipline
- define safe degradation behavior

This is a runtime safety protocol crystal,
not a content crystal.

---

### 2. Recovery Resilience Crystal v1
- `docs/experiments/recovery-resilience-crystal-v1.json`

Role:
- define interruption awareness
- define checkpoint and state persistence expectations
- define stale lock / stuck state handling
- define partial-failure downgrade paths
- define restart discipline
- define completion verification discipline

This is a runtime resilience protocol crystal,
not a content crystal.

---

## Updated Crystal-Set View

At this stage, the working crystal-set structure becomes:

### Reasoning-path crystals
- problem-definition crystal
- architecture-evolution crystal

### Protocol crystals
- methodology crystal
- retrieval-routing crystal
- safety-boundary crystal
- recovery-resilience crystal

### Content crystal
- system-memory crystal

---

## Main Working Conclusion

Crystal expansion has now moved from speculative completeness toward failure-driven necessity.

This is important because it means:
- missing crystal types can be inferred from regrowth weakness
- deployment-facing runtime protocol is emerging as a real crystal layer
- crystal-set growth can remain disciplined instead of exploding into arbitrary library expansion

---

## Current Consequence

The project is no longer only testing whether crystals can preserve architecture.
It is also testing whether crystals can preserve:
- runtime safety discipline
- runtime recovery discipline
- deployment-facing operational boundaries

This marks a shift from:
- architecture regrowth package

toward:
- deployment-facing runtime protocol architecture

---

## One-Sentence Summary

Gap-Driven Crystal Expansion v1 adds safety and recovery protocol crystals as the first failure-derived extension of the project-level crystal set.
