# Adapter Definition Pass v1

## Goal

Clarify what an adapter is inside the emerging crystal ecology.

This is not yet a full adapter system.
It is a first definition pass driven by the fact that `require_adapter` has already appeared as the correct outcome in a real composition-pressure test.

---

## Why This Exists

The composition-case pressure test showed that there is a middle zone between:
- direct composition
- rejection

This middle zone is not hypothetical anymore.
It now needs an explicit object definition.

---

## Core Questions

### 1. Is an adapter itself a crystal?
Current working answer:

## probably yes, but as a special protocol crystal

Why:
- it has role semantics
- it has activation conditions
- it has boundaries
- it should be verifiable
- it should not be treated as a silent runtime hack

At the same time, it differs from ordinary crystals because it is relational.
It exists between sets or between mismatched protocol structures.

So the current best working view is:

## adapter = relational protocol crystal

---

### 2. What is the minimum role of an adapter?
A minimal adapter should only do four things:

#### a. Framing translation
Translate an external or weaker framing assumption into the receiving set's stronger framing discipline.

#### b. Routing translation
Translate a weaker or flatter routing structure into the receiving set's layered routing structure.

#### c. Replaceability guard
Prevent role similarity from being misread as safe replacement.

#### d. Conflict isolation
Contain incompatibility locally so that composition does not corrupt the entire set.

Anything beyond these four roles should be treated as out of scope for v1.

---

### 3. When should an adapter be used?
An adapter should be considered when:
- role overlap exists
- phase mapping exists
- composition is not safe directly
- rejection would throw away meaningful reusable structure

In other words:

## require_adapter is the middle-zone action

An adapter should not be used when:
- the two systems are fundamentally incompatible
- the external set would silently replace non-replaceable foundations
- framing conflict is too deep to translate safely

In such cases:

## reject is still the correct action

---

### 4. How should an adapter be verified?
A minimal adapter verification should ask:
- did it preserve foundational crystals from silent replacement?
- did it preserve the receiving set's framing discipline?
- did it preserve routing discipline instead of flattening it?
- did it localize conflict instead of spreading it?

So adapter verification is not only:
- does it connect?

It is more importantly:
- does it connect without degrading integrity?

---

## Current Working Definition

An adapter is:

## a relational protocol crystal that mediates composition between partially compatible crystal sets
## by translating framing/routing assumptions, guarding replaceability, and isolating conflict.

---

## What This Definition Pass Does Not Yet Solve

It does not yet solve:
- adapter schema fields
- adapter versioning
- adapter verification metrics
- adapter generation rules
- adapter chaining or multi-hop composition

Those belong to later work.

---

## One-Sentence Summary

Adapter Definition Pass v1 defines the adapter as a relational protocol crystal for the middle zone between direct composition and rejection.
