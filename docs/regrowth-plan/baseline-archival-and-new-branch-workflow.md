# Baseline Archival and New Branch Workflow

## Purpose

Preserve the current architecture/crystal line as a baseline while starting a new phase-driven regrowth line from a minimal executable kernel.

## Working rule

Do not replace the existing line immediately.
Treat the current branch/PR/doc/code set as a baseline and comparison target.
Build the new line in parallel.

## Baseline archival policy

The current PR 90 line becomes:
- baseline
- reference implementation/documentation cluster
- comparison target
- fallback point

Archive means:
- preserve docs, experiments, code, and comment trail
- stop treating it as the only forward path
- keep it available for comparison during regrowth

Suggested labels/phrasing:
- `prototype-baseline`
- `architecture-regrowth-baseline`

## New branch policy

Create a fresh branch for the regrowth line.
Suggested names:
- `regrowth/phase-driven-mainline`
- `rebuild/recursive-skill-driven`
- `regrowth/minimal-memory-kernel`

The new branch should start from explicit phase goals, not from total feature parity.

## New mainline constraints

The new line must:
- be phase-driven
- use recursive-research style outputs as inputs to implementation planning
- require a runnable artifact before phase merge
- keep governance/object inflation out until the executable kernel exists

## Merge rule for each phase

Each phase merge must contain all of the following:
1. phase goal document
2. runnable implementation for that phase
3. minimal verification or smoke test
4. comparison note against baseline
5. explicit boundary for what is deferred to the next phase

## Recommended early phases

### Stage 0 - Baseline freeze
- mark PR 90 line as baseline/reference
- stop broadening that line further as the only mainline
- keep issue/PR/docs available as memory and comparison target

### Stage 1 - Regrowth bootstrap
- create the recursive research skill/process
- define stop rules and compression rules
- define phase contracts
- define merge gates

### Stage 2 - Minimal executable memory kernel
- implement raw write/read
- implement minimal structure extraction
- implement minimal retrieval
- implement minimal injection
- implement lightweight async consolidation

### Stage 3 - Controlled expansion
Only after Stage 2 is runnable:
- provenance improvements
- hypothesis/stable distinction
- bounded validation
- stronger retrieval routing

## Anti-drift rules

The new line should reject these before the minimal kernel exists:
- governance kernel expansion
- root axiom layer
- structural debt economy
- full self-modification protocol
- crystal transfer machinery
- predictive prophylaxis layer

## Comparison workflow

At each phase close, compare new line against baseline on:
- runnable capability
- conceptual simplification
- implementation clarity
- retained useful ideas
- avoided inflation

## Success condition for the reboot strategy

The reboot strategy succeeds if:
- the baseline remains available and intelligible,
- the new line reaches a smaller runnable core faster,
- each phase produces mergeable implementation,
- and the new line avoids immediately regrowing the full governance stack.
