from __future__ import annotations

from typing import Any

from .models import RagConfig


def parse_rag_config(raw: dict[str, Any]) -> RagConfig:
    if not raw:
        raise ValueError("Missing required 'rag' configuration")

    backend = str(_require(raw, "backend", "rag")).strip().lower()
    if backend != "chroma":
        raise ValueError(f"Unsupported RAG backend '{backend}'. Allowed: chroma")

    top_k = int(_require(raw, "top_k", "rag"))
    if top_k <= 0:
        raise ValueError("'rag.top_k' must be >= 1")

    embedding_model = str(_require(raw, "embedding_model", "rag")).strip()
    if not embedding_model:
        raise ValueError("'rag.embedding_model' cannot be empty")

    index_path = str(_require(raw, "index_path", "rag")).strip()
    if not index_path:
        raise ValueError("'rag.index_path' cannot be empty")

    return RagConfig(
        backend=backend,
        top_k=top_k,
        embedding_model=embedding_model,
        index_path=index_path,
    )


def _require(mapping: dict[str, Any], key: str, section: str) -> Any:
    if key not in mapping:
        raise ValueError(f"Missing required key '{key}' in '{section}'")
    return mapping[key]
