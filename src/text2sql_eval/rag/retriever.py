from __future__ import annotations

import json
from pathlib import Path

from ..config import AppConfig
from .chroma_store import ChromaVectorStore
from .config import parse_rag_config
from .models import RetrievedChunk


class RagRetriever:
    def __init__(self, *, vector_store: ChromaVectorStore, top_k: int) -> None:
        self._vector_store = vector_store
        self._top_k = top_k

    def retrieve(self, question: str) -> list[RetrievedChunk]:
        return self._vector_store.retrieve(question, top_k=self._top_k)


def rag_manifest_path(config: AppConfig) -> str:
    rag_config = parse_rag_config(config.rag)
    return str(Path(rag_config.index_path) / "manifest.json")


def build_retriever(config: AppConfig) -> RagRetriever:
    rag_config = parse_rag_config(config.rag)
    index_path = Path(rag_config.index_path)
    manifest_path = index_path / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"RAG index not found at {index_path}. "
            "Run 'text2sql-eval build-rag-index' first."
        )

    # Basic manifest shape validation to fail early on partial/broken indexes.
    json.loads(manifest_path.read_text(encoding="utf-8"))
    vector_store = ChromaVectorStore.from_env(
        index_path=index_path,
        embedding_model=rag_config.embedding_model,
    )
    return RagRetriever(vector_store=vector_store, top_k=rag_config.top_k)
