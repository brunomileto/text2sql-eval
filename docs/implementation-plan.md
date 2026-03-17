Im# text2sql-eval — Implementation Plan

> Research project: *Evaluation of Contextualization Strategies in Text-to-SQL Systems Based on Large Language Models*
> Authors: Bruno Mileto Dias de Assunção, Paulo Henrique Siqueira Silva — AKCIT/UFG, 2026

---

## 1. What This Application Does

The application is a **pure evaluation harness**. It does not enforce business rules or access controls — it measures whether LLMs and different prompt strategies respect them on their own.

**Core loop:**

```
Input: N natural-language questions
       config.yaml (models, tracks, dataset, RAG backend)

For each question:
  For each model defined in config:
    For each track (A, B, C, …):
      1. [Track-specific] build prompt
      2. [Track C+ only] optionally pre-fetch RAG context (before LLM call)
      3. Call LLM → receive SQL string
      4. Execute SQL against the database → receive result set (or error)

Collect all (question, model, track, prompt, sql, result_set) tuples
  ↓
Evaluation pipeline:
  For each tuple:
    - Execution Accuracy (EX): compare result_set vs reference result_set
    - Error classification: syntax error, schema hallucination,
      operational violation (non-SELECT, forbidden table), logic error

Output: per-question JSON + rolled-up CSV summary
```

**Key invariant:** the LLM is called **exactly once per (question, model, track)** combination. RAG retrieval, when present, is a pre-step that enriches the prompt — not a separate LLM call. This keeps model and generation parameters constant across all tracks, satisfying the research design constraint.

---

## 2. Experimental Tracks

| Track | Name | Prompt Context | LLM Calls |
|-------|------|----------------|-----------|
| A | Simple Prompt | Question only | 1 |
| B | Metadata Enrichment | Question + schema metadata (table/column descriptions, data types, relationships) | 1 |
| C | Metadata + RAG | Question + metadata + top-k semantically retrieved schema/metadata chunks | 1 (RAG is a pre-step) |
| D+ | Extensible | Any new strategy plugs in by implementing `BaseTrack` | 1+ |

### Track C — RAG pre-step detail

```
question
  → embed(question)
  → vector_store.retrieve(embedding, top_k)   # returns relevant schema/metadata chunks
  → build_prompt(question + metadata + retrieved_chunks)
  → LLM
  → SQL
```

The vector index is built once over the schema metadata (table descriptions, column descriptions, glossary, business rules) and optionally over ground-truth question-SQL pairs as few-shot examples.

---

## 3. Extensibility Design

The central design principle is that **adding a new track requires only two things**:

1. Create a new class that extends `BaseTrack`
2. Register it in `config.yaml`

Everything else (LLM calls, SQL execution, evaluation, reporting) is shared and reused automatically.

### `BaseTrack` interface

```python
class BaseTrack(ABC):
    """
    A track encapsulates one prompt-contextualization strategy.
    It receives a question + schema context and returns a prompt string.
    The pipeline handles LLM calls, execution, and evaluation.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier, e.g. 'track_a', 'track_b'."""
        ...

    @abstractmethod
    def build_prompt(
        self,
        question: str,
        schema_context: SchemaContext,        # tables, columns, types, metadata
        extra_context: list[str] | None,      # RAG-retrieved chunks (None for A/B)
    ) -> str:
        """Return the final prompt string to send to the LLM."""
        ...

    def pre_fetch(
        self,
        question: str,
        vector_store: VectorStore | None,
    ) -> list[str]:
        """
        Optional hook called before build_prompt.
        Override to implement RAG retrieval (Track C) or any other
        pre-LLM step. Default implementation returns an empty list.
        """
        return []
```

### Pipeline call sequence (per question, per model, per track)

```
track.pre_fetch(question, vector_store)   → extra_context
track.build_prompt(question, schema, extra_context)  → prompt
llm.generate(prompt)                      → raw_output
extract_sql(raw_output)                   → sql
executor.run(sql, db)                     → result_set | error
evaluator.score(result_set, reference)    → EXScore + ErrorClass
reporter.record(...)
```

### Adding a new track (e.g., Track D — Chain-of-Thought)

```python
# src/text2sql_eval/tracks/track_d.py

class ChainOfThoughtTrack(BaseTrack):
    name = "track_d"

    def build_prompt(self, question, schema_context, extra_context=None):
        return COT_TEMPLATE.format(
            question=question,
            schema=schema_context.to_markdown(),
        )
```

Then in `config.yaml`:

```yaml
experiment:
  tracks: [a, b, c, d]
```

No changes anywhere else in the pipeline.

### The RAG pipeline is also reusable across tracks

`pre_fetch` receives a `VectorStore` instance, which is itself an abstraction. Any track can call it — not just Track C. This means:

- **Track D** could use RAG over a different index (e.g., few-shot question-SQL pairs instead of schema metadata)
- **Track E** could use two RAG retrievals (schema index + glossary index) and merge the results before building the prompt
- **Track F** could skip RAG entirely but reuse the same `VectorStore` to do keyword-based filtering

The `VectorStore` abstraction (`base.py`) exposes a simple interface:

```python
class VectorStore(ABC):
    """
    Shared retrieval interface. Any track can call it via pre_fetch.
    The backend (ChromaDB, FAISS, …) is injected by the pipeline at runtime
    based on config — tracks never instantiate it directly.
    """

    @abstractmethod
    def index(self, documents: list[Document]) -> None:
        """Build or update the vector index."""
        ...

    @abstractmethod
    def retrieve(self, query: str, top_k: int) -> list[str]:
        """Return top_k most relevant text chunks for the query."""
        ...
```

The pipeline injects the configured `VectorStore` instance into every track's `pre_fetch` call. Tracks that don't need it simply ignore it (the default `pre_fetch` returns `[]`). Tracks that do need it call `vector_store.retrieve(question, top_k)` — and the backend is fully swappable via config without touching the track code.

```
config.yaml (rag.backend: chroma)
  → pipeline builds ChromaVectorStore once at startup
  → injects it into every track.pre_fetch(question, vector_store)
  → Track A/B ignore it
  → Track C calls vector_store.retrieve(question, top_k) → chunks
  → Track D could call vector_store.retrieve(question, top_k, index="fewshot") → examples
```

So the full shared infrastructure — LLM provider, SQL executor, evaluator, reporter, **and** RAG store — is built once by the pipeline and passed into every track. No track owns any of it.

### Dataset loading

The dataset layer is deliberately simple — no ABC, no registry, no download logic. Config points at a `.json` questions file and a `.sqlite` database file. One plain function reads them.

```python
@dataclass
class EvalQuestion:
    question_id: str
    question: str          # natural language
    reference_sql: str     # ground truth
    schema: SchemaContext  # parsed schema for this DB
    db_path: Path          # path to the .sqlite file — from config.dataset.db
```

```python
def load_questions(questions_path: Path, db_path: Path, limit: int | None = None) -> list[EvalQuestion]:
    """Read questions JSON + SQLite path → list of EvalQuestion."""
    ...
```

> *"Simple is better than complex."* — no abstraction needed when there is one format.

### Full extensibility summary

| What changes | Track B | Track C | Track D+ | New LLM |
|---|---|---|---|---|
| New implementation file | yes | yes | yes | yes |
| Registry — add one entry | yes | yes | yes | yes |
| `config.yaml` — one value | yes | yes | yes | yes |
| Runner / executor / evaluator / reporter / CLI | **no** | **no** | **no** | **no** |

---

## 4. Project Structure

```
text2sql-eval/
├── pyproject.toml                  # uv-managed deps, CLI entry points, tool config
├── Dockerfile
├── docker-compose.yml
├── .env.example                    # API key placeholders
├── .gitignore
│
├── config/
│   ├── config.yaml                 # All experiment defaults (see Section 5)
│   └── restricted_tables.yaml      # Per-DB list of "forbidden" tables for scoring
│
├── data/
│   ├── dev.json                    # Questions + reference SQL
│   ├── database.sqlite             # The single SQLite file all queries run against
│   └── .gitkeep
│
├── src/
│   └── text2sql_eval/
│       ├── __init__.py
│       ├── cli.py                  # Typer CLI (entry point)
│       ├── config.py               # dataclasses + PyYAML: load config.yaml
│       │
│       ├── dataset/
│       │   ├── __init__.py
│       │   ├── models.py           # EvalQuestion dataclass
│       │   ├── schema.py           # SchemaContext dataclass + stub parser
│       │   └── loader.py           # load_questions() — one plain function
│       │
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── base.py             # Abstract LLMProvider: generate(prompt) -> str
│       │   ├── openai_provider.py
│       │   ├── anthropic_provider.py
│       │   └── ollama_provider.py
│       │
│       ├── tracks/
│       │   ├── __init__.py
│       │   ├── base.py             # BaseTrack ABC (pre_fetch + build_prompt)
│       │   ├── track_a.py          # Simple prompt
│       │   ├── track_b.py          # Metadata-enriched prompt
│       │   ├── track_c.py          # Metadata + RAG pre-fetch
│       │   └── registry.py         # Map track name string → class (auto-discovered)
│       │
│       ├── rag/
│       │   ├── __init__.py
│       │   ├── base.py             # Abstract VectorStore: index() + retrieve()
│       │   ├── chroma_store.py     # ChromaDB implementation
│       │   └── faiss_store.py      # FAISS implementation
│       │
│       ├── executor/
│       │   ├── __init__.py
│       │   └── sql_executor.py      # execute_sql(sql, db_path) -> ExecutionResult via sqlite3 stdlib
│       │
│       ├── evaluator/
│       │   ├── __init__.py
│       │   ├── execution_accuracy.py   # EX: compare result sets
│       │   └── error_classifier.py     # Classify error type from SQL + exception
│       │
│       ├── pipeline/
│       │   ├── __init__.py
│       │   └── runner.py           # Orchestrate the full loop; calls track, llm,
│       │                           # executor, evaluator, reporter in sequence
│       │
│       └── results/
│           ├── __init__.py
│           └── reporter.py         # Write JSON rows + CSV summary per run
│
├── results/                        # Runtime output (gitignored)
│   └── {run_id}/
│       ├── track_a.json
│       ├── track_b.json
│       ├── track_c.json
│       └── summary.csv
│
├── notebooks/
│   ├── 01_explore_dataset.ipynb    # Inspect questions and schema
│   ├── 02_results_analysis.ipynb   # EX scores per track/model, comparisons
│   └── 03_error_breakdown.ipynb    # Error type distributions and examples
│
├── tests/
│   ├── test_execution_accuracy.py
│   ├── test_error_classifier.py
│   ├── test_prompt_builders.py
│   └── test_sql_executor.py
│
└── docs/
    └── tcc-plan.pdf
```

---

## 5. Configuration

### `config/config.yaml` — single source of truth for all defaults

```yaml
llm:
  models:                           # list — add or remove models freely, no overwriting
    - provider: openai              # openai | anthropic  (ollama: Stage 5)
      model: gpt-4o
      temperature: 0.0
      max_tokens: 1024
    - provider: anthropic
      model: claude-3-5-sonnet-20241022
      temperature: 0.0
      max_tokens: 1024

rag:
  backend: chroma                   # chroma | faiss
  top_k: 5
  embedding_model: text-embedding-3-small
  index_path: data/rag_index/

dataset:
  questions: data/dev.json           # path to the questions JSON file
  db: data/database.sqlite           # the single SQLite file all queries run against

experiment:
  tracks: [a, b, c]                 # which tracks to run; add d, e, … as needed
  limit: null                       # null = all questions; int = first N (for quick tests)
  output_dir: results/

constraints:
  restricted_tables_file: config/restricted_tables.yaml
```

- `llm.models` is a list — the runner loops over all entries per question. Add a model by appending a block. Remove by deleting a block. No overwriting.
- `dataset.questions` and `dataset.db` are the only two paths needed. Point them at any JSON + SQLite pair.

### `.env` — secrets only

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Config precedence (lowest → highest)

```
config.yaml  <  .env  <  CLI flags  <  notebook cell override
```

### CLI override examples

```bash
# Run with all models defined in config.yaml
uv run text2sql-eval run-experiment --track a

# Run with a single model override (skips config.yaml model list)
uv run text2sql-eval run-experiment --track a --provider anthropic --model claude-3-5-sonnet-20241022

# Quick smoke test: 10 questions, track B only
uv run text2sql-eval run-experiment --track b --limit 10

# Use a different questions file and database
uv run text2sql-eval run-experiment --track a --questions data/other.json --db data/other.sqlite
```

### Notebook override

```python
from text2sql_eval.config import load_config

cfg = load_config("config/config.yaml")
cfg.llm.models[0].model = "gpt-4o-mini"
cfg.experiment.limit = 20
```

---

## 6. CLI Commands

| Command | Description |
|---------|-------------|
| `run-experiment` | Run the full pipeline for one or more tracks |
| `build-rag-index` | Embed schema metadata and build the vector index for Track C |
| `report` | Print a metrics summary table for a given run ID |

---

## 7. Evaluation Logic

For each `(question, model, track, sql, result_set)` tuple:

### Execution Accuracy (EX)

- Execute both the generated SQL and the reference SQL against the same `.sqlite` DB
- `EX = 1` if the result sets are identical (order-insensitive), else `EX = 0`
- If the generated SQL fails to execute, `EX = 0` and an error is classified

### Error Classifier

| Error Type | Condition |
|------------|-----------|
| `SYNTAX_ERROR` | SQL failed to parse or raised a DB exception |
| `SCHEMA_HALLUCINATION` | SQL references a table or column not present in the schema |
| `OPERATIONAL_VIOLATION` | SQL contains a non-SELECT statement, or references a table listed in `restricted_tables.yaml` |
| `LOGIC_ERROR` | SQL executed successfully but result set does not match reference |
| `CORRECT` | EX = 1, no violations |

> Note: `OPERATIONAL_VIOLATION` is a **scoring classification** only. The application never blocks or prevents any SQL from running — it simply records whether the model respected the constraints embedded in the prompt/metadata.

### Per-run output

- **`track_x.json`** — one record per question:
  ```json
  {
    "question_id": "...",
    "question": "...",
    "track": "a",
    "model": "gpt-4o",
    "prompt": "...",
    "generated_sql": "...",
    "reference_sql": "...",
    "ex": 1,
    "error_type": "CORRECT",
    "latency_ms": 843,
    "input_tokens": 312,
    "output_tokens": 47
  }
  ```
- **`summary.csv`** — one row per `(track, model)` with aggregated EX%, error breakdown, avg latency, avg tokens

---

## 8. Implementation Stages

Mapped to the TCC 15-week schedule:

| Stage | Weeks | Tasks |
|-------|-------|-------|
| **Stage 3** | 5–6 | Project skeleton with `pyproject.toml`; `config.py` (dataclasses + PyYAML); `dataset/loader.py` + `EvalQuestion` + `SchemaContext` stub; `sql_executor.py`; `run-experiment` CLI |
| **Stage 4** | 7–8 | `LLMProvider` ABC + OpenAI/Anthropic providers; `BaseTrack` ABC + Track A + Track B; `execution_accuracy.py`; `error_classifier.py`; `runner.py` (pipeline orchestration); basic tests |
| **Stage 5** | 9–10 | `VectorStore` ABC + ChromaDB/FAISS; `track_c.py` + `build-rag-index` CLI; systematic experiment execution (all tracks, full dataset); `reporter.py` + CSV/JSON output; `report` CLI |
| **Stage 6** | 11–13 | Analysis notebooks; README.md; Docker polish; ABNT formatting; final delivery |

---

## 9. Technology Stack

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Python version | 3.11+ | Stable, well-supported by all deps |
| Package manager | `uv` | Fast, modern, lock-file based |
| Project format | `pyproject.toml` + `src/` layout | PEP 517/518 compliant, installable |
| CLI framework | Typer | Type-annotated, auto-docs, built on Click |
| Config / validation | `dataclasses` + PyYAML | Simple is better than complex — API keys read directly by providers |
| LLM clients | `openai`, `anthropic`, `ollama` Python SDKs | Official SDKs, stable APIs |
| RAG / embeddings | ChromaDB (default) or FAISS (optional) | Both abstract behind `VectorStore` |
| DB execution | `sqlite3` stdlib | SQLite-only; zero extra dependencies |
| Testing | `pytest` + `pytest-cov` | Standard Python testing |
| Containerization | Docker + docker-compose | Reproducible environment |
| Notebooks | Jupyter + pandas + matplotlib/seaborn | Analysis and visualization |

---

## 10. Design Principles

1. **Evaluation harness, not a product** — the application never enforces constraints; it only measures whether the model does.
2. **One LLM call per (question, model, track)** — keeps parameters constant across tracks for fair comparison.
3. **RAG is always a pre-step** — retrieval enriches the prompt; it is not a separate LLM reasoning step.
4. **Tracks are plug-and-play** — implement `BaseTrack`, register in config, done.
5. **Dataset is just two paths** — `dataset.questions` (JSON) and `dataset.db` (SQLite). Point them at any pair and run. No loader abstraction needed.
6. **DB execution is SQLite via stdlib** — `execute_sql(sql, db_path)` in `sql_executor.py` is a plain function; no abstraction, no registry, no config section needed.
7. **Config is the contract** — all behavior is driven by `config.yaml`; CLI flags override it without editing files. Adding a model means appending a block to `llm.models` — nothing is overwritten.
8. **Results are reproducible** — every run writes its full config snapshot alongside results so any run can be re-described exactly.

---

## 11. MVP Implementation Plan (Track A)

> Full detail in `MVP.md`. This section summarises the scope.

### Goal

A single working CLI command that runs Track A end-to-end:

```bash
uv run text2sql-eval run-experiment --track a --limit 10
```

### What gets built vs deferred

| Component | MVP | Notes |
|---|---|---|
| `pyproject.toml` + `uv` setup | **build** | Full dep list, CLI entry point |
| `.env.example` + `.gitignore` | **build** | — |
| `config/config.yaml` | **build** | Full shape; only `llm` + `dataset` + `experiment` active |
| `config.py` — dataclasses + PyYAML | **build** | `rag` + `constraints` sections stubbed but not used |
| `dataset/models.py` — `EvalQuestion` | **build** | `db_path` from `config.dataset.db` |
| `dataset/schema.py` — `SchemaContext` | **stub** | Correct dataclass shape; parser returns empty — Track B fills it |
| `dataset/loader.py` | **build** | `load_questions()` — one plain function; reads JSON + SQLite path |
| `llm/base.py` — `LLMProvider` ABC | **build** | `generate(prompt) -> LLMResponse` (tokens + latency) |
| `llm/openai_provider.py` | **build** | — |
| `llm/anthropic_provider.py` | **build** | Same interface; cheap to add now |
| `llm/ollama_provider.py` | **defer** | Stage 5 |
| `llm/registry.py` | **build** | `{"openai": OpenAIProvider, "anthropic": AnthropicProvider}` |
| `config.yaml` — `llm.models` as list | **build** | Append to add a model; no overwriting |
| `tracks/base.py` — `BaseTrack` ABC | **build** | Must be correct from day one |
| `tracks/track_a.py` | **build** | Question-only prompt; ignores `schema_context` |
| `tracks/track_b.py` / `track_c.py` | **defer** | Stage 4/5 |
| `tracks/registry.py` | **build** | Pattern established |
| `rag/` module | **defer** | Stage 5 |
| `executor/sql_executor.py` | **build** | `execute_sql(sql, db_path) -> ExecutionResult` via `sqlite3` stdlib |
| `evaluator/execution_accuracy.py` | **build** | Compare result sets order-insensitively |
| `evaluator/error_classifier.py` | **partial** | `SYNTAX_ERROR`, `LOGIC_ERROR`, `CORRECT` only |
| `pipeline/runner.py` | **build** | Full orchestration loop over `(question, model, track)` |
| `results/reporter.py` | **build** | Write `track_a.json` + `summary.csv` |
| `run-experiment` CLI command | **build** | — |
| `report` / `build-rag-index` CLI | **defer** | Stage 5 |
| `tests/` — 3 test files | **build** | — |
| `notebooks/` | **defer** | Stage 6 |
| `Dockerfile` / `docker-compose` | **defer** | Stage 6 |

### Definition of done

- `uv run text2sql-eval run-experiment --track a --limit 10` runs 10 questions with `data/dev.json` + `data/database.sqlite`, writes `results/{run_id}/track_a.json` + `summary.csv`
- All three test files pass
- Swapping model is one CLI flag — no code changes
