# Prompt Template Guide

This project keeps prompts in external template files under `config/prompts/`.

Goal:

- make prompt iteration easy
- keep prompt edits separate from runtime code changes
- preserve a stable rendering contract

## Location and naming

Prompt files live in:

- `config/prompts/`

Naming convention:

- `track_<key>.txt`

Current files:

- `config/prompts/track_a.txt`
- `config/prompts/track_b.txt`

## Rendering contract

Prompt templates are rendered with Python `str.format(...)`.

Current required variables:

- `track_a.txt` requires `{question}`
- `track_b.txt` requires `{question}` and `{schema}`

If a required variable is missing, runtime raises a clear `ValueError`.

If a prompt file is missing, runtime raises a clear `FileNotFoundError`.

## How Track A uses prompt templates

Track A calls the shared loader with key `track_a`.

Flow:

1. load template from `config/prompts/track_a.txt`
2. validate required variables
3. render with context `{"question": <question text>}`

## How Track B uses prompt templates

Track B calls the shared loader with key `track_b`.

Flow:

1. load template from `config/prompts/track_b.txt`
2. introspect the active SQLite database into `SchemaContext`
3. render schema markdown via `SchemaContext.to_markdown()`
4. validate required variables
5. render with context `{"question": <question text>, "schema": <schema markdown>}`

## Editing guidance

When editing `track_a.txt`:

- keep `{question}` in the template
- keep instructions explicit about returning SQL only
- avoid introducing markdown wrappers unless intentionally testing that behavior

When editing `track_b.txt`:

- keep `{question}` and `{schema}` in the template
- keep instructions explicit about returning SQL only
- assume `{schema}` contains markdown generated from the active SQLite database

Recommended validation after edits:

```bash
uv run pytest
```

If you only want prompt-specific checks:

```bash
uv run pytest tests/test_prompt_loader.py tests/test_tracks.py
```

## Future tracks

For new tracks beyond B:

- add `config/prompts/track_<key>.txt`
- define required variables per track
- keep rendering in track code through the shared loader
