# Run Artifact Guide (`run.json`)

This document explains the output file written by each experiment run:

- `results/{run_id}/run.json`

The artifact is designed for analysis notebooks. It stores raw facts collected during execution so metrics can be computed later without re-running models.

## High-level structure

`run.json` has two top-level keys:

- `run_metadata`
- `records`

Think of it as:

- `run_metadata`: "What run was executed?"
- `records`: "What happened for each question/model/track combination?"

## `run_metadata`

`run_metadata` describes run context and provenance.

Key fields:

- `schema_version`: artifact contract version (currently `v1`)
- `run_id`: unique run identifier used in output folder naming
- `created_at`: UTC timestamp for run creation
- `dataset_path`: questions file path used during run
- `db_path`: SQLite database file path used during run
- `limit`: effective question limit (`null` means no limit)
- `tracks_requested`: track names requested for this run
- `models_requested`: provider/model list requested for this run
- `git_commit`: current repository commit hash (best effort)
- `config_snapshot`: full resolved config serialized into the artifact
- `schema_artifact_path`: run-relative path to the saved schema JSON artifact

Why this matters:

- You can always reconstruct run conditions from a single file.
- Notebook analysis can group/compare runs safely.
- Reproducibility does not depend on local memory or shell history.

Each run folder may also include sibling artifacts referenced by `run_metadata`.
Current additional artifact:

- `schema_context.json`: structured schema introspected from the active SQLite database used for the run

## `records`

`records` is a list. Each item represents one execution unit:

- one question
- one track
- one model

In other words, one record is one full model attempt + SQL execution pair.

### Core identity fields

- `question_id`
- `question`
- `track`
- `provider`
- `model`

### Prompt/context fields

- `prompt`: final prompt sent to the model
- `extra_context`: pre-fetched context returned by track hook (if any)
- `track_artifacts`: optional structured metadata produced by the track

### LLM output fields

- `raw_response`: original model text output
- `normalized_sql`: SQL extracted/cleaned from raw response
- `input_tokens`
- `output_tokens`
- `latency_ms`

### Execution facts

The pipeline executes both generated SQL and reference SQL.

- `generated`: execution facts for model SQL
- `reference`: execution facts for ground-truth SQL

Each has:

- `success` (boolean)
- `error_type_raw` (if failed)
- `error_message` (if failed)
- `row_count` (if successful)
- `rows_sample` (bounded sample for inspection)

### Comparison helpers

- `rows_equal`: `true`/`false` when both executions succeed, otherwise `null`
- `generated_rows_hash`: deterministic hash of generated result rows (or `null`)
- `reference_rows_hash`: deterministic hash of reference result rows (or `null`)

These helpers support fast notebook comparisons without storing full large result sets.

### Timing fields

- `pipeline_latency_ms`: elapsed runtime for this full unit
- `timestamps`: start/finish timestamps for traceability
