# Raw Reflection and Growth Drift Plan

## Purpose

This experiment line explores whether raw local material can be:
1. sliced into bounded reflection inputs,
2. turned into local candidate regularities,
3. compressed into a denser crystal-like form,
4. and then grown again without losing local identity or drifting too far from the source.

This is an exploratory experiment line.
It is **not** part of the current minimal memory kernel baseline.
It should be treated as a separate follow-up experiment track.

## Why this line exists

The current regrowth baseline now covers:
- lightweight memory write/retrieve
- note/product formation
- mixed routing behavior

What it does **not** yet answer is:
- how local raw material should be reflected into bounded candidate regularities,
- how compression changes what is preserved,
- how later growth drifts away from source material,
- and whether anchor constraints reduce that drift.

This experiment line exists to probe those questions directly.

## Main components

### 1. `scripts/build_raw_reflection_input.py`
Purpose:
- split a source text into bounded slices
- attach lightweight graph hints
- produce structured reflection input JSON

Role:
- preprocessing step for local reflection experiments

### 2. `scripts/run_raw_reflection.py`
Purpose:
- take the reflection input JSON
- ask a model to produce 1-3 bounded local candidate regularities
- keep claims local rather than global

Role:
- first-stage local reflection / induction step

### 3. `scripts/run_growth_drift.py`
Purpose:
- compress source material into a denser crystal-like representation
- regrow from that compressed form across rounds
- compare free growth vs anchored growth

Role:
- drift and preservation experiment step

## Experimental questions

This line is meant to help answer questions such as:
- does local reflection preserve local identity?
- what gets lost during compression?
- what kinds of drift appear during repeated growth?
- do source anchors and relation-path anchors materially reduce drift?
- what should count as acceptable regrowth versus harmful abstraction drift?

## Inputs and outputs

### Inputs
- local text material
- optional graph hints extracted from the source slices
- model configuration via environment variables

### Outputs
By default, outputs are written to `tmp/`, including:
- raw reflection input JSON
- raw reflection output JSON
- growth drift JSON traces

These outputs should be treated as experiment artifacts, not stable repository data.

## Environment expectations

These scripts currently assume access to an OpenAI-compatible endpoint, typically through environment variables such as:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `RAW_REFLECTION_MODEL`

The default local assumption is an Ollama-compatible endpoint.

## Boundary

This experiment line should **not** be confused with:
- the minimal memory kernel baseline,
- the Phase 1-5 regrowth line already merged,
- or the paused Phase 6 governance track.

It is a separate exploratory line for studying:
- local reflection,
- compression,
- regrowth,
- and drift control.

## Current status

Current status is:
- useful enough to preserve,
- not yet mature enough to merge into the main baseline by default,
- and best treated as a separate experiment track until results justify tighter integration.

## Recommended next step

If this line continues, the next useful step is:
- run a few explicit examples,
- record the outputs,
- and summarize whether the drift behavior is informative enough to justify a dedicated experimental commit.
