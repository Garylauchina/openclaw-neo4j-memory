# LongMemEval Sample Plan

This note defines the first minimal LongMemEval entry path for the Neo4j Memory MVP.

## Goal

Do not integrate the full benchmark yet.
First, create a tiny and inspectable sample that can flow through the current MVP import path.

## Why LongMemEval first

Compared with JRE or large open chat corpora, LongMemEval is a better first long-test entry because:

- it is explicitly built for long-term interactive memory
- question types are structured and interpretable
- history sessions are already segmented
- timestamps are included
- evidence sessions are annotated

## Minimal plan

1. obtain `longmemeval_oracle.json` or a tiny subset of `longmemeval_s_cleaned.json`
2. export 1-2 instances into markdown files, by default **without evaluation scaffolding**
3. inspect the generated sample files manually
4. run `test_corpus_import.py` in dry-run mode with:
   - `--source-tag longmemeval-sample`
   - an explicit `--import-batch`
5. only after that, decide whether to do a real import

## Helper script

Use:

```bash
python scripts/prepare_longmemeval_sample.py path/to/longmemeval_oracle.json --limit 2
```

If you explicitly want to keep benchmark framing text for manual inspection only:

```bash
python scripts/prepare_longmemeval_sample.py path/to/longmemeval_oracle.json --limit 2 --include-scaffolding
```

This creates:
- markdown files in `tmp/longmemeval-sample/`
- `manifest.json`

## Recommended first dry-run

```bash
python scripts/test_corpus_import.py tmp/longmemeval-sample \
  --dry-run \
  --source-tag longmemeval-sample \
  --import-batch longmemeval-oracle-run-001
```

## Explicit non-goals

This step does not yet include:
- benchmark scoring
- retrieval metric integration
- full LongMemEval pipeline support
- automatic oracle/evidence evaluation
- large-scale dataset download automation

It is only the first sample-adaptation step.

## Why scaffolding is excluded by default

The benchmark question / reference answer / sample title are useful for human inspection,
but they are not ideal as online memory input. By default, the helper now exports only the conversation-history-oriented content for import probing.
