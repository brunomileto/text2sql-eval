# Track C and Track-Independent RAG Plan

## Summary

Implement Track C as `question + schema + retrieved context`, while making
indexing and retrieval reusable outside Track C so future tracks such as Track D
can opt into the same RAG flow without duplicating logic.

V1 choices:

- Chroma is the only supported vector backend
- OpenAI embeddings are fixed to `text-embedding-3-small`
- corpus is curated local documents under `docs/rag/`
- index build is explicit, not automatic during experiment runs
- retrieval runs once per question per run and is reused across all models and
  retrieval-enabled tracks
- `run.json` stores full retrieved text per record for notebook analysis

## Key Changes

### Track-independent RAG subsystem

- Add a dedicated RAG module with three responsibilities:
  - load corpus documents from `docs/rag/`
  - chunk and embed them into a Chroma index at `config.rag.index_path`
  - retrieve top-k chunks for a question from that prebuilt index
- Keep this subsystem independent of any track class. Tracks consume retrieval
  results; they do not own indexing or vector-store setup.
- Introduce a small typed contract for retrieved chunks, with fields sufficient
  for runtime and artifact use:
  - stable chunk id
  - source document path
  - chunk text
  - retrieval score/distance
  - optional chunk order/index within source
- Add a run-level RAG service/factory in the pipeline that:
  - is created once from config
  - opens the existing Chroma index
  - is called once per question
  - caches retrieval results in memory for the rest of the run

### Track capability model and pipeline flow

- Extend the track contract so tracks can declare retrieval usage explicitly,
  similar to the existing schema capability.
- Track C should declare:
  - uses schema context
  - uses retrieval context
- Update the pipeline to:
  - initialize schema once only if any selected track needs schema
  - initialize the RAG retriever once only if any selected track needs retrieval
  - retrieve once per question only if at least one selected track needs
    retrieval
  - pass the retrieved chunk texts into `pre_fetch(...)` consumers or replace
    that hook with a cleaner retrieval-aware hook if needed, but keep the end
    result track-independent
- Reuse the same retrieved results for all models in the run.

### Track C behavior

- Add `TrackC` and register `"c"`.
- Track C prompt should combine:
  - question
  - schema markdown from `SchemaContext.to_markdown()`
  - retrieved context text assembled from the retrieved chunks
- Add `config/prompts/track_c.txt`.
- Track C `track_artifacts` should include full retrieval evidence for the
  record:
  - retrieved source paths
  - scores/distances
  - full retrieved chunk texts
- Keep Track C prompt assembly consistent with Track B patterns: prompt text is
  still externalized; Python only provides context variables.

### Index build and public interfaces

- Add an explicit index-build entrypoint, available through both:
  - Python API helper
  - CLI command
- Recommended command shape:
  - `text2sql-eval build-rag-index --config-path ...`
- Build command behavior:
  - reads files from `docs/rag/`
  - chunks them deterministically
  - embeds with OpenAI using `OPENAI_API_KEY`
  - writes/replaces the Chroma index under `config.rag.index_path`
  - writes a compact index manifest alongside the index with source file list
    and chunk counts
- Experiment-run behavior when Track C is requested and the index is missing:
  - fail fast with a clear error telling the user to run the build command first
- Keep the existing `rag` config block and formalize these fields as required for
  Track C:
  - `backend`
  - `top_k`
  - `embedding_model`
  - `index_path`

### Artifact and docs contract

- Keep `run.json` schema version as `v1`.
- Keep retrieval results record-scoped because retrieval is per question and
  needed for notebook inspection.
- Add a run-level metadata field for the RAG index manifest path if one exists,
  using the same additive approach already used for schema artifacts.
- Document the new run folder artifacts and CLI/API usage:
  - schema artifact remains run-scoped
  - RAG index is external, prebuilt, and referenced by metadata
  - Track C records contain full retrieved text in `track_artifacts`
- Add a dedicated Track C design doc under `docs/`.

## Test Plan

- Config tests:
  - validate required RAG fields for Track C usage
  - reject unsupported backend values
- RAG indexing tests:
  - reads files from `docs/rag/`
  - chunks deterministically
  - writes index and manifest
  - fails clearly without `OPENAI_API_KEY`
- RAG retrieval tests:
  - top-k retrieval returns typed chunk records
  - retrieval is cached once per question during a run
  - missing or unbuilt index raises a clear error
- Pipeline tests:
  - Track C run initializes schema and retrieval, but Track A/B-only runs do not
    initialize retrieval
  - mixed runs such as `[a, c]` perform retrieval once per question and reuse it
    across models
  - `track_artifacts` for Track C contain full retrieved text, source paths, and
    scores
- Prompt tests:
  - `track_c.txt` loads and renders with `{question}`, `{schema}`, and retrieval
    context placeholders
- End-to-end integration tests:
  - build index from local fixture docs
  - run Track C with fake LLM provider
  - verify prompt contains schema and retrieved context
  - verify record artifact contains full retrieved text
  - verify future-style mixed run `[b, c]` reuses schema once and retrieval once

## Assumptions and Defaults

- Corpus is a curated, repo-managed set of text documents under `docs/rag/`;
  arbitrary repo-wide indexing is out of scope for v1.
- Chroma is the only backend in v1 even though config keeps a `backend` field.
- OpenAI embeddings are fixed to `text-embedding-3-small`; provider choice for
  embeddings is not configurable in v1.
- Retrieval is question-scoped and reused across all models and
  retrieval-enabled tracks in the same run.
- Track C is the first consumer of the reusable RAG subsystem, but the subsystem
  must remain generic so future tracks can opt into retrieval without code
  duplication.
- Full retrieved text is stored in each Track C record even though this
  increases artifact size; inspection value for research notebooks takes
  priority in v1.
