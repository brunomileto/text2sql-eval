# text2sql-eval

`text2sql-eval` is an execution pipeline for Text-to-SQL experiments.

It runs configured tracks and models, executes generated and reference SQL, and writes a rich artifact at `results/{run_id}/run.json`.

Evaluation and analysis are notebook-owned and intentionally out of runtime scope.

## Interface Model

- Primary interface: Python API (`run_experiment`) for notebook workflows.
- Secondary interface: CLI (`text2sql-eval`) as a thin wrapper over the same API.
- One execution path: the CLI delegates to the API; business logic is not duplicated.

## Notebook-First Usage

```python
from text2sql_eval import run_experiment

run_id = run_experiment(
    config_path="config/config.yaml",
    track="a",
    limit=10,
)

print(run_id)
# read results/{run_id}/run.json in your notebook for analysis
```

Optional overrides:

- `track="a,c"` or `track="all"`
- `limit=<int>`
- `provider="openai", model="gpt-4o"` (must be provided together)

## CLI Wrapper Usage

The CLI calls the same `run_experiment` API.

```bash
uv run text2sql-eval run-experiment --track a --limit 10
```

Single model override:

```bash
uv run text2sql-eval run-experiment --provider openai --model gpt-4o
```

## Output Artifact

Each run writes:

- `results/{run_id}/run.json`

The artifact includes:

- `run_metadata` (schema version, config snapshot, tracks/models requested)
- `records` (prompt, raw response, normalized SQL, execution facts, row hashes, timings)
