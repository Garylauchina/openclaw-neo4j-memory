# Adapter Layer Emergence v1

## Why This Exists

The first composition-case pressure test produced a non-trivial result:

## `require_adapter`

This means adapter logic is no longer only a speculative future concept.
It has now emerged as an experiment-backed next-layer requirement.

---

## Core Observation

Some external crystal sets may be:
- not fully compatible
- not cleanly rejectable
- role-overlapping but structurally weaker
- partially mappable but unsafe to directly compose

This creates a middle zone between:
- `compose`
- `reject`

The first composition-case pressure test showed that this middle zone is real.

---

## What an Adapter Layer Would Need To Do

A minimal adapter layer would likely need to support:

### 1. Framing translation
Translate weaker or differently structured external framing assumptions into the current crystal set's stronger framing discipline.

### 2. Routing translation
Map a weaker or flatter routing model into the current crystal system's layered routing structure.

### 3. Replaceability guard
Prevent external crystals from silently replacing foundational internal crystals merely because their role labels look similar.

### 4. Conflict isolation
Localize framing, dependency, or ordering conflicts so they do not corrupt the entire crystal set.

---

## What an Adapter Is Not

An adapter should not be treated as:
- a free pass to compose incompatible crystal sets
- a silent replacement mechanism
- a generic compatibility magic layer

Its role is narrower:

## an adapter makes specific mismatches explicit and managed.

---

## First Open Questions

- Is an adapter itself a crystal?
- Is it a protocol object generated during composition?
- Should adapters be versioned and verified like ordinary crystals?
- When should `require_adapter` collapse into `reject` instead?

---

## Current Working Direction

The next meaningful step is not yet a full adapter system.
It is a minimal adapter-definition pass that clarifies:
- object type
- role
- activation point
- verification requirement

---

## One-Sentence Summary

Adapter Layer Emergence v1 records the point at which `require_adapter` became an experiment-backed signal that the crystal system now needs an explicit middle-layer object between direct composition and rejection.
