from __future__ import annotations

import os
from pathlib import Path

from .models import RagChunk, RetrievedChunk


class ChromaVectorStore:
    def __init__(
        self,
        *,
        index_path: Path,
        embedding_model: str,
        api_key: str,
    ) -> None:
        try:
            import chromadb
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
        except ImportError as exc:  # pragma: no cover - depends on local install
            raise RuntimeError(
                "chromadb is not installed. Install project dependencies before "
                "building or using the RAG index."
            ) from exc

        index_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(index_path))
        embedding_function = OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name=embedding_model,
        )
        self._collection = self._client.get_or_create_collection(
            name="rag_chunks",
            embedding_function=embedding_function,
        )

    @classmethod
    def from_env(cls, *, index_path: Path, embedding_model: str) -> ChromaVectorStore:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY must be set to build or use the Chroma RAG index"
            )
        return cls(
            index_path=index_path,
            embedding_model=embedding_model,
            api_key=api_key,
        )

    def reset(self) -> None:
        existing = self._collection.get(include=[])
        ids = existing.get("ids", [])
        if ids:
            self._collection.delete(ids=ids)

    def upsert(self, chunks: list[RagChunk]) -> None:
        if not chunks:
            return
        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "source_path": chunk.source_path,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ],
        )

    def retrieve(self, query: str, *, top_k: int) -> list[RetrievedChunk]:
        result = self._collection.query(query_texts=[query], n_results=top_k)
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            RetrievedChunk(
                chunk_id=str(chunk_id),
                source_path=str(metadata["source_path"]),
                text=str(document),
                score=float(distance),
                chunk_index=int(metadata["chunk_index"]),
            )
            for chunk_id, document, metadata, distance in zip(
                ids, documents, metadatas, distances, strict=True
            )
        ]
