# PR Draft - regrowth/minimal-memory-kernel

## Suggested PR title

`Establish the phase-driven minimal memory kernel regrowth line through Phase 5`

## Suggested PR description

### Summary

This PR establishes the new lightweight regrowth line on top of a minimal executable memory kernel.

It does **not** continue the earlier heavy architecture/governance expansion directly.
Instead, it builds and freezes a phase-driven alternative line that remains runnable at each stage.

The branch now includes completed and frozen work through:
- Phase 1 - lightweight memory structure + prompt-level orchestration
- Phase 2 - credibility and usefulness expansion
- Phase 3 - distillation and memory quality refinement
- Phase 4 - stronger reusable memory products
- Phase 5 - stronger routing and product/raw-memory coordination

Phase 6 has been scoped and documented, but is currently paused in evidence-gathering mode rather than admitted into governance intervention implementation.

### What this PR adds

#### Minimal memory kernel implementation
- `minimal_memory_kernel/memory_store.py`
- `minimal_memory_kernel/structure.py`
- `minimal_memory_kernel/retrieval.py`
- `minimal_memory_kernel/orchestration.py`
- `minimal_memory_kernel/consolidation.py`
- `minimal_memory_kernel/revision.py`
- `minimal_memory_kernel/note_feedback.py`
- `minimal_memory_kernel/routing.py`
- `minimal_memory_kernel/__init__.py`

#### Regrowth verification suite
- `tests_regrowth/test_minimal_memory_store.py`
- `tests_regrowth/test_minimal_structure_and_retrieval.py`
- `tests_regrowth/test_minimal_orchestration.py`
- `tests_regrowth/test_lightweight_consolidation.py`
- all added Phase 2 to Phase 5 regrowth tests

#### Regrowth planning and stage-boundary docs
- Phase 1 closeout/freeze docs
- Phase 2 closeout/freeze docs
- Phase 3 scope/breakdown/boundary/closeout/freeze docs
- Phase 4 scope/breakdown/boundary/closeout/freeze docs
- Phase 5 scope/breakdown/boundary/closeout/freeze docs
- Phase 6 scope/breakdown/boundary plus failure-case catalog, entry decision, evidence plan, and evidence log

### Why this line exists

The purpose of this branch is to create a runnable, phase-disciplined regrowth line that can be merged and evaluated stage by stage, instead of continuing uncontrolled growth on the older heavy architecture line.

### Positioning relative to the crystal line

This branch should be treated as the **engineering baseline** for a minimal memory kernel built directly through staged implementation.

The crystal line should be treated separately as the **growth-derived line** whose role is to test whether a crystal-guided system can regrow into functionally comparable memory, product, and routing capabilities.

In other words:

- **PR #91 / regrowth line** = direct engineering construction of the lightweight baseline
- **crystal line** = test of whether crystal-guided regrowth can reach comparable functional structure

These two lines are therefore complementary rather than interchangeable: one provides the runnable engineering reference, and the other provides the regrowth/comparison target.

Key design commitments:
- phase-driven development
- runnable implementation at each merge
- explicit working boundaries and non-goals
- closeout/freeze artifacts at stage boundaries
- product-first and routing-first growth before governance
- no governance expansion without concrete failure pressure

### Current architectural position

This branch currently proves a lightweight line that can grow through:
- raw memory write/read
- minimal structure extraction
- retrieval and orchestration
- lightweight consolidation
- provenance and bounded status distinctions
- bounded revision/update behavior
- stronger note/product distillation
- reusable product forms
- explicit mixed-routing behavior

without reopening:
- root axiom systems
- structural debt systems
- self-modification layers
- crystal-transfer implementation
- operating-system style governance layers
- broad policy/governance shells

### Important Phase 6 status

Phase 6 is **not** implemented as governance logic in this PR.

Instead, this branch explicitly stops at:
- failure-case cataloging
- governance entry decision
- evidence collection planning
- initial evidence logging

Current Phase 6 status is:
- governance is possible in principle
- governance is not yet justified in practice
- Phase 6 remains paused after Merge 1 pending repeated concrete failure evidence

### Recommended review frame

Please review this branch as:
- a new minimal regrowth baseline
- a stage-disciplined alternative line
- a comparison and merge candidate against the older heavy baseline

Please do **not** review it as if it were trying to complete the full long-term governance architecture in one pass.

### Smoke-check status

The branch includes direct smoke-check validation across the staged regrowth tests, used in place of full `pytest` because `pytest` was unavailable in the current environment.

### Non-goals of this PR

This PR is not trying to:
- complete the full governance architecture
- replace the crystal line conceptually
- solve all future conflict/update problems now
- introduce autonomous self-evolution layers
- reintroduce heavy architectural abstractions under new names

### Proposed merge interpretation

Treat this PR as:
- the lightweight regrowth baseline through Phase 5,
- with Phase 6 intentionally paused,
- and with future governance work blocked on concrete failure evidence.
