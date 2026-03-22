# text2sql-eval

`text2sql-eval` is an experiment runner for Text-to-SQL research.

It executes tracks and models, runs generated SQL and reference SQL against the same SQLite database, and writes one canonical artifact:

- `results/{run_id}/run.json`

The runtime is intentionally focused on evidence collection. Evaluation logic and analysis are done in Jupyter notebooks.

## Why this architecture

We intentionally separate execution from evaluation.

- Runtime stays stable and reproducible.
- Notebook analysis can evolve quickly without changing execution code.
- Every run stores raw facts (prompts, SQL, execution outcomes, hashes, timing), so metrics can be recomputed later.
- CLI and notebook use the same code path to avoid drift.

In short: one execution pipeline, many analysis iterations.

## Current interface model

- Primary interface: Python API (`run_experiment`) for notebook workflows.
- Secondary interface: CLI (`text2sql-eval`) as a thin wrapper over the same API.

## Track definitions

Tracks are contextualization strategies. A track changes prompt/context, not the core execution pipeline.

- `a` - question only (no metadata, no retrieval)
- `b` - question + schema metadata enrichment
- `c` - question + metadata + retrieved context (RAG pre-fetch)

Current implementation includes Track A. Track B/C are reserved by contract and are kept in the typed API so notebooks and callers can rely on stable track semantics.

## Repository map (important paths)

- `config/config.yaml`: default experiment configuration.
- `data/dev.json`: input questions with reference SQL.
- `data/database.sqlite`: active SQLite database used by runs.
- `mini-dev/original/financial.sqlite`: original source database.
- `mini-dev/pt-br/financial.sqlite`: translated variant database.
- `results/{run_id}/run.json`: output artifact per run.

## Local setup

### 1) Prerequisites

- Python `3.11+`
- `uv` installed

Verify:

```bash
python --version
uv --version
```

### 2) Install dependencies

From repository root:

```bash
uv sync --extra dev
```

### 3) Prepare the active database

This project runs against `data/database.sqlite`.

Copy one database variant into that location:

```bash
# Option A: original dataset
cp mini-dev/original/financial.sqlite data/database.sqlite

# Option B: translated dataset
# cp mini-dev/pt-br/financial.sqlite data/database.sqlite
```

This step is critical. If `data/database.sqlite` does not exist, runs will fail.

### 4) Understand and verify `data/dev.json`

`data/dev.json` is the question set for experiments. Each item must have:

- `question_id`
- `question`
- `sql` (reference SQL executed on `data/database.sqlite`)

Current repo includes a small 3-question sample (simple, medium, hard) in `data/dev.json`.

Why this file matters:

- It defines what the model is asked.
- It defines the reference SQL baseline.
- It directly controls experiment scope and quality.

If you change DB variant, validate that reference SQL still works.

### 5) Choose provider strategy

For local development and tests, prefer the built-in fake provider (no API keys needed).

In `config/config.yaml`, set:

```yaml
models:
  - provider: fake
    model: local-test
    temperature: 0.0
    max_tokens: 32

inputs:
  questions_file: data/dev.json
  database_file: data/database.sqlite

run_defaults:
  tracks: [a]
  limit: null
  output_dir: results/
```

For real providers (`openai`, `anthropic`), add keys in `.env`:

```bash
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

### 6) Run tests

```bash
uv run pytest
```

## Run experiments

### CLI (thin wrapper)

```bash
uv run text2sql-eval run-experiment --track a --limit 10
```

Single-model override:

```bash
uv run text2sql-eval run-experiment --provider openai --model gpt-4o
```

### Python API (recommended for notebooks)

```python
from text2sql_eval import run_experiment

run_id = run_experiment(
    config_path="config/config.yaml",
    track="a",
    limit=10,
)

print(run_id)
```

Supported overrides:

- `track="a,c"` or `track="all"`
- `limit=<int>`
- `provider="..."` to run all configured models for that provider
- `provider="...", model="..."` to run one exact configured pair

## Jupyter workflow

This repository currently contains domain exploration notebook(s) under `notebooks/`.

Typical usage:

1. Run pipeline via `run_experiment(...)`.
2. Open `results/{run_id}/run.json` in notebook.
3. Compute EX/error metrics and visualizations there.

Notebook cell example (execute run + load artifact):

```python
import json
from pathlib import Path

from text2sql_eval import run_experiment

run_id = run_experiment(
    config_path="config/config.yaml",
    track="a",
    limit=10,
)

artifact_path = Path(f"results/{run_id}/run.json")
payload = json.loads(artifact_path.read_text())

print("Run ID:", run_id)
print("Records:", len(payload["records"]))
```

Notebook cell example (inspect configured providers/models before running):

```python
from text2sql_eval.app import TRACK_DESCRIPTIONS
from text2sql_eval.config import load_config

cfg = load_config("config/config.yaml")

print("Available tracks:")
for track_name, description in TRACK_DESCRIPTIONS.items():
    print(f"  {track_name}: {description}")

print("\nConfigured models:")
for model_cfg in cfg.models:
    print(
        f"  provider={model_cfg.provider}, model={model_cfg.model}, "
        f"temperature={model_cfg.temperature}, max_tokens={model_cfg.max_tokens}"
    )
```

Then run using one of those provider/model pairs:

```python
run_id = run_experiment(
    config_path="config/config.yaml",
    track="a",
    provider="openai",
    model="gpt-4o",
    limit=10,
)
```

Minimal load example:

```python
import json
from pathlib import Path

run_id = "<your-run-id>"
payload = json.loads(Path(f"results/{run_id}/run.json").read_text())

metadata = payload["run_metadata"]
records = payload["records"]
print(metadata["schema_version"], len(records))
```

## Output artifact contract (`run.json`)

Top-level keys:

- `run_metadata`
- `records`

`run_metadata` contains run config and provenance (`schema_version`, `config_snapshot`, requested tracks/models, timestamps, etc.).

Each `records[]` item contains analysis-ready raw evidence:

- prompt and track context
- raw LLM output and normalized SQL
- generated/reference execution facts
- row equality and row hashes
- latency and timestamps

## Common failure modes

- `Database file not found`: ensure `data/database.sqlite` exists.
- SQL errors in reference queries: ensure `data/dev.json` matches chosen DB variant.
- API key errors: either configure keys or switch to `provider: fake`.
- Empty/invalid config: validate `config/config.yaml` structure.

## Development notes

- Keep runtime policy-light; do not add notebook scoring logic into pipeline.
- Keep CLI thin; add behavior in API layer (`app.py`) first.
- Treat `run.json` schema as a contract; evolve with explicit versioning.
