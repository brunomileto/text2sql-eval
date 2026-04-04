# Track C RAG Infra and Bootstrap Plan

## Summary

This plan covers the infrastructure and setup work required before or alongside
Track C implementation.

It is intentionally separate from `docs/track-c-plan.md`, which defines the
Track C feature behavior. This document focuses on dependencies, local setup,
runtime prerequisites, and operational conventions for the reusable RAG
subsystem.

V1 choices:

- use Chroma as the only supported vector backend
- use the existing OpenAI SDK for embeddings
- require `OPENAI_API_KEY` only for index build, not for fake-provider tests
- keep corpus sources in `docs/rag/`
- keep built index files in `data/rag_index/`

## Infra Changes

### Python dependencies

- Add `chromadb` as a runtime dependency.
- Do not add a second embedding SDK; reuse the existing `openai` dependency.
- Do not add a heavy chunking dependency in v1 unless implementation proves it
  necessary. Prefer deterministic in-house chunking first.
- Update `uv.lock` as part of the same change set that introduces RAG code.

### Repository folders and ownership

- Create and document `docs/rag/` as the curated source corpus directory.
- Keep `docs/rag/` fully repo-managed and human-editable.
- Keep `data/rag_index/` as generated local index output, not as hand-edited
  source content.
- Treat `data/rag_index/` as rebuildable derived state.
- Ensure the repo keeps any needed placeholder files only for directory
  discoverability, not as part of runtime logic.

### Environment and credentials

- Require `OPENAI_API_KEY` for index-building commands and API helpers.
- Do not require `OPENAI_API_KEY` for Track A or Track B runs.
- Do not require `OPENAI_API_KEY` for Track C runs when a ready index already
  exists and the selected model provider is `fake`.
- Fail fast with a clear message when index build is requested without
  `OPENAI_API_KEY`.
- Keep embedding model fixed to `text-embedding-3-small` in config and docs.

### Config contract

- Keep the existing `rag` block in `config/config.yaml`.
- Formalize these fields as required for RAG-enabled flows:
  - `backend`
  - `top_k`
  - `embedding_model`
  - `index_path`
- Accept only `backend: chroma` in v1.
- Validate the presence and basic shape of the RAG config during config loading
  or before index build / Track C execution.

## Bootstrap and Operational Flow

### Local developer setup

Required bootstrap sequence for a new developer using Track C:

1. run `uv sync`
2. set `OPENAI_API_KEY`
3. place curated corpus files under `docs/rag/`
4. run the explicit RAG index build command
5. run Track C experiments against the generated index

This flow should be documented in the README and Track C docs.

### Index lifecycle

- The index is built explicitly, not lazily during experiment execution.
- Rebuilding the index is the supported path after corpus edits.
- If corpus files change, users must rerun the index build command.
- Track C execution must not attempt to silently repair or refresh the index.
- Missing index should produce a clear instruction to run the build command.

### CLI and API bootstrap surface

- Add a dedicated CLI command for index build.
- Add a matching Python API helper so notebooks can rebuild the index without
  shelling out.
- Keep both entrypoints thin over one shared implementation.
- CLI and API should report:
  - index location
  - number of source files indexed
  - number of chunks written

## Validation and Test Plan

- Dependency/bootstrap tests:
  - import path for Chroma-backed RAG module works once dependencies are
    installed
  - missing `OPENAI_API_KEY` fails clearly for index build
- Config validation tests:
  - missing `rag` fields fail clearly for Track C / build-index flows
  - unsupported backend values fail clearly
- Bootstrap integration tests:
  - build command creates `data/rag_index/` contents from fixture files under a
    temporary corpus directory
  - rebuild overwrites or refreshes the index deterministically
- Runtime separation tests:
  - Track A/B runs do not require Chroma index presence
  - Track C run requires a built index
  - fake-provider Track C runs still work without model API keys once the index
    already exists
- Documentation acceptance:
  - README includes a minimal RAG setup path
  - Track C docs reference both corpus location and index-build command

## Assumptions and Defaults

- Dependency installation is part of the Track C implementation branch, not a
  separate pre-migration branch.
- `data/rag_index/` remains local derived state and should not be treated as
  durable source-of-truth content.
- Corpus curation is manual in v1; there is no sync process from notebooks,
  databases, or external sources.
- Chroma persistence details are implementation-owned as long as the index lives
  under `config.rag.index_path` and is rebuildable.
