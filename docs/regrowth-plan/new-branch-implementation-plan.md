# New Branch Implementation Plan

## Suggested branch name

Preferred:
- `regrowth/minimal-memory-kernel`

Alternatives:
- `regrowth/phase-driven-mainline`
- `rebuild/recursive-skill-driven`

## Branch purpose

This branch exists to regrow a new mainline from a lightweight memory structure plus prompt-level orchestration.
It is not a continuation of the full architecture/crystal/governance expansion line.

## First working rule

Before adding any higher-order design objects, produce a runnable minimal memory loop.

## Initial implementation order

### Step 1
Create the minimal raw memory path:
- raw write
- raw readback
- small write decision rule

### Step 2
Create minimal structure and retrieval:
- entities
- small relation set
- retrieval scoring and top-k selection
- retrieval trigger rule

### Step 3
Create injection and prompt orchestration:
- compact memory context
- source attribution
- ignore/suppress rule
- prompt-level memory use policy

### Step 4
Create lightweight async consolidation:
- dedupe
- frequent-entity marking
- small consolidated notes or retrieval anchors

## Required artifacts per merge

For each merge, produce:
1. implementation changes
2. a minimal verification method
3. a short progress note
4. explicit non-goals for the next merge

## Comparison against baseline

After each merge, compare the new line against the baseline on:
- runnable capability
- simplicity
- implementation clarity
- avoided inflation
- retained useful ideas

## What this branch should not do early

Do not introduce these before the minimal memory loop is runnable:
- belief governance
- root axiom layers
- structural debt systems
- self-modification systems
- crystal transfer machinery
- deep policy/governance kernels

## Phase 1 completion condition

Phase 1 is complete only when the branch demonstrates:
- retained raw experience
- minimal reusable structure
- successful retrieval on later relevant input
- actual memory injection into current execution
- useful prompt-level memory orchestration
- lightweight background consolidation

## Phase 1 output

At the end of the branch's first phase, produce a closeout note that states:
- what is now runnable
- what remained intentionally deferred
- what inflation was avoided
- what Phase 2 should add next
