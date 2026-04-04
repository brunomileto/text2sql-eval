from __future__ import annotations

import json
from pathlib import Path

from ..config import AppConfig
from .chroma_store import ChromaVectorStore
from .chunking import chunk_documents
from .config import parse_rag_config
from .corpus import DEFAULT_CORPUS_DIR, load_corpus_documents
from .models import RagIndexBuildResult


def build_rag_index(
    config: AppConfig,
    *,
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
) -> RagIndexBuildResult:
    rag_config = parse_rag_config(config.rag)
    documents = load_corpus_documents(corpus_dir)
    chunks = chunk_documents(documents)
    index_path = Path(rag_config.index_path)
    index_path.mkdir(parents=True, exist_ok=True)
    vector_store = ChromaVectorStore.from_env(
        index_path=index_path,
        embedding_model=rag_config.embedding_model,
    )
    vector_store.reset()
    vector_store.upsert(chunks)

    manifest_path = index_path / "manifest.json"
    manifest = {
        "backend": rag_config.backend,
        "embedding_model": rag_config.embedding_model,
        "source_count": len(documents),
        "chunk_count": len(chunks),
        "sources": [
            {
                "source_path": document.source_path,
                "char_count": len(document.content),
            }
            for document in documents
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return RagIndexBuildResult(
        index_path=str(index_path),
        manifest_path=str(manifest_path),
        source_count=len(documents),
        chunk_count=len(chunks),
    )
