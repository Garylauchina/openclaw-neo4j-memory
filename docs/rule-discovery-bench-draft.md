# Rule Discovery Bench Draft

## Purpose

This draft defines a minimal experimental framework for discovering model-specific unfold rules from behavior, rather than starting from hand-written rules.

The core idea is:

1. fix the test method
2. expose different agents / models to the same recursive tasks
3. observe stable reasoning tendencies and drift tendencies
4. derive model-specific crystal ingestion / unfold rules from those observed tendencies

---

## Core Shift

Do not begin from:
- prewritten unfold rules
- fixed prompt theories
- manually assumed best scaffolds

Begin from:

## fixed test conditions + recursive behavior observation

This makes rule discovery closer to:
- self-discovered reasoning preference profiling
- drift susceptibility profiling
- constraint-need discovery

not world-law discovery.

The target is not for the model to invent external truths.
The target is for the model to reveal its own stable reasoning tendencies under controlled conditions.

---

## High-Level Two-Phase Flow

### Phase 1. Rule Discovery Bench
Use fixed texts, fixed tasks, and fixed evaluation language.
Do not yet optimize for a specific hand-written unfold rule.

### Phase 2. Crystalization of Discovered Rules
From repeated behavior, extract:
- ingestion rules
- unfold rules
- resistance rules
- no-go patterns
- preferred bridge order

Then encode these into model-specific knowledge crystal scaffolds.

---

## Phase 1: Rule Discovery Bench

### Inputs
Use a small but diagnostic standard corpus with different failure pressures.

Minimal initial categories:

#### 1. High relation-progression texts
Purpose:
- test whether the model preserves intermediate bridges
- test whether the model follows relation progression or replaces it

#### 2. High abstraction-trap texts
Purpose:
- test whether the model prematurely lifts into theory shell / framework language
- test whether it turns process into doctrine

#### 3. High unresolved-tension / counterexample texts
Purpose:
- test whether the model erases tension
- test whether it over-integrates conflict into a neat closure

Optional later:
- strong-prior texts
- weak-prior texts
- cross-domain bridge texts
- noisy evidence texts

---

## Fixed Tasks
Each model should face the same minimal recursive task set.

### Task A. Compress
Compress the input into a smaller structured form.

### Task B. Unfold
Expand the compressed form back into reasoning.

### Task C. Recursive Unfold
Repeat unfold / refold at least one more round.

### Task D. Self-Compare
Ask the model to compare round 1 vs round 2 behavior in the same evaluation language.

### Task E. Source-Near Reanchor
Force the model to reconnect output claims to source-local evidence.

The goal is to reveal:
- what the model preserves
- what it upgrades
- what it erases
- what it tends to regularize into theory

---

## Evaluation Language
Use the current convergence-fidelity draft as the fixed language.

Core dimensions:
- relation-path convergence
- problem-space convergence
- knowledge-state convergence
- boundary convergence

Split axes:
- growthability
- referentiality

Optional notes:
- dominant drift attractor
- closure tendency
- discourse drift risk
- tension erasure tendency
- bridge skipping tendency

---

## What Is Being Discovered
The bench should discover model behavior rules, not domain truths.

Examples:
- the model tends to over-abstract after round 2
- the model preserves path but erases unresolved tension
- the model needs explicit bridge ordering
- the model collapses into checklist form without stepwise scaffold
- the model keeps locality only when forced to reuse source fragments

These are:
- reasoning preference rules
- drift susceptibility rules
- resistance needs
- bridge-order needs

---

## Phase 2: Crystalization
After repeated observations, extract a model portrait.

Example fields:
- preferred_ingestion_shape
- preferred_unfold_shape
- required_resistance_structure
- unstable_abstraction_patterns
- preferred_bridge_order
- no_go_formulations
- source_anchor_requirements

These then become crystal-side rules.

This means:

## do not design the crystal first and hope the model fits it

Instead:

## discover the model's stable reasoning tendencies first,
## then build the crystal ingestion / unfold protocol to fit that model.

---

## Example Portrait Outputs

### Gemma portrait
- high growthability
- high path reconstruction strength
- high frameworkization tendency after recursive rounds
- needs anti-closure resistance
- benefits from unresolved-tension retention

### Qwen portrait
- high control / stability
- weak spontaneous bridge growth
- compresses toward checklist form
- needs bridge-priority stepwise scaffold
- benefits from explicit cannot-yet-upgrade boundaries

### GPT-5.4 portrait
- relatively balanced single-round behavior
- prompt-fed crystal injection works
- needs recursive validation before stronger claims

---

## Minimal Immediate Use
This bench can begin small.

Initial recommendation:
- 3 text categories
- 3 models
- compress + unfold + round-2 unfold + self-compare
- evaluate using convergence-fidelity draft

Do not search a huge space yet.
The first goal is to produce:

## model behavior portraits

Only after that should the next generation of knowledge crystal rules be treated as stable enough to formalize.

---

## Short Principle

Knowledge crystals should eventually become:

## knowledge content × discovered model adaptation rules

not just compressed content.

---

## Status

This is a draft for immediate experimental use.
It should be refined through actual bench runs.
