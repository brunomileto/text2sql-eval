# text2sql-eval - Current Plan

> Research project: Evaluation of Contextualization Strategies in Text-to-SQL Systems Based on Large Language Models
> Authors: Bruno Mileto Dias de Assuncao, Paulo Henrique Siqueira Silva - AKCIT/UFG, 2026

---

## 1. Decision Log (What Changed)

This document reflects the current architecture after an intentional pivot.

- We moved from runtime scoring to notebook-first evaluation.
- Runtime now focuses on evidence collection only.
- The canonical output is a single artifact: `results/{run_id}/run.json`.
- CLI is no longer the primary interface; Python API is primary.
- CLI remains as a thin wrapper over the same API path.

This preserves reproducibility while making analysis iteration faster in notebooks.

---

## 2. System Responsibility Split

### Runtime pipeline (in scope)

- Load config, questions, and DB path.
- For each `(question, model, track)`:
  - build prompt
  - call LLM once
  - normalize SQL output
  - execute generated SQL and reference SQL
  - collect raw execution facts and metadata
- Write `run.json` with full run metadata and records.

### Notebook evaluation (out of scope for runtime)

- EX scoring policy and metric definitions.
- Error-taxonomy analysis and breakdowns.
- Aggregations, plots, comparisons, and reporting.

---

## 3. Primary Interfaces

### Python API (primary)

`text2sql_eval.app.run_experiment(...)`

- notebook-first entrypoint
- loads config
- applies overrides through pure helper functions
- runs pipeline and returns `run_id`

Supported overrides:

- `track="a,c"` or `track="all"`
- `limit=<int>`
- `provider + model` together for single-model override

### CLI (secondary)

`text2sql-eval run-experiment ...`

- thin wrapper only
- delegates directly to `run_experiment(...)`
- prints `run_id` and artifact path

No business logic is duplicated in CLI.

---

## 4. Current Output Contract

Each run writes exactly one canonical artifact:

- `results/{run_id}/run.json`

Top-level keys:

- `run_metadata`
- `records`

`run_metadata` includes:

- `schema_version` (`v1`)
- `run_id`, `created_at`
- `dataset_path`, `db_path`, `limit`
- `tracks_requested`, `models_requested`
- `git_commit` (best effort)
- `config_snapshot`

Each record includes raw facts for notebook evaluation:

- identity/context (`question_id`, `question`, `track`, `provider`, `model`)
- prompt/context (`prompt`, `extra_context`, `track_artifacts`)
- LLM output (`raw_response`, `normalized_sql`, token counts, latency)
- generated/reference execution facts
- comparison helpers (`rows_equal`, row hashes)
- timing (`pipeline_latency_ms`, `timestamps`)

---

## 5. Track and Extensibility Contract

Tracks implement `BaseTrack` and are resolved via registry.

Current hooks:

- `pre_fetch(...) -> list[str]`
- `build_prompt(...) -> str`
- `build_artifacts(...) -> dict[str, Any]`

`build_artifacts` is now the official extension seam for track-specific metadata in `run.json`.

Current enabled track set is Track A (`a`).

---

## 6. Provider Strategy

Implemented providers:

- `openai`
- `anthropic`
- `fake` (deterministic local provider for offline integration tests)

The `fake` provider is intentional and supports local end-to-end tests without external API keys.

---

## 7. Current Project Shape

Key modules in active use:

- `src/text2sql_eval/app.py` (API-first orchestration entry)
- `src/text2sql_eval/cli.py` (thin wrapper)
- `src/text2sql_eval/pipeline/runner.py` (execution loop)
- `src/text2sql_eval/pipeline/normalization.py` (SQL/result normalization)
- `src/text2sql_eval/results/schema.py` (typed artifact contract)
- `src/text2sql_eval/results/reporter.py` (single-file artifact writer)

The evaluator modules still exist in codebase but are not runtime-critical for notebook-first scoring.

---

## 8. Testing Strategy and Current State

Testing is behavior-first.

What is covered:

- config loading and validation
- dataset and schema stubs
- SQL execution behavior
- provider normalization and registry
- track behavior and registry
- pipeline normalization utilities
- run artifact contract
- app override behavior
- CLI delegation behavior
- integration tests with tiny local sqlite fixture and `fake` provider (API + CLI)

Current status: full suite passing.

---

## 9. Deferred Work

Still intentionally deferred:

- Track B/C prompt strategies and RAG execution path
- notebook artifacts and analysis notebooks in-repo
- optional `records.jsonl` scalability split (manifest + jsonl)
- docker packaging and operational hardening

---

## 10. Practical Run Commands

API-first:

```python
from text2sql_eval import run_experiment

run_id = run_experiment(config_path="config/config.yaml", track="a", limit=10)
```

CLI wrapper:

```bash
uv run text2sql-eval run-experiment --track a --limit 10
```

Single model override:

```bash
uv run text2sql-eval run-experiment --provider openai --model gpt-4o
```
