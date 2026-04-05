from __future__ import annotations

from typing import Any

from ..dataset.schema import SchemaContext
from ..prompts.loader import render_prompt
from ..rag.models import RetrievedChunk
from .base import BaseTrack


class TrackC(BaseTrack):
    @property
    def name(self) -> str:
        return "track_c"

    @property
    def uses_schema_context(self) -> bool:
        return True

    @property
    def uses_retrieval_context(self) -> bool:
        return True

    def pre_fetch(
        self,
        question: str,
        retrieved_chunks: list[RetrievedChunk] | None = None,
    ) -> list[str]:
        _ = question
        return [chunk.text for chunk in (retrieved_chunks or [])]

    def build_prompt(
        self,
        question: str,
        schema_context: SchemaContext,
        extra_context: list[str] | None = None,
    ) -> str:
        retrieval_context = "\n\n".join(extra_context or [])
        return render_prompt(
            "track_c",
            {
                "question": question,
                "schema": schema_context.to_markdown(),
                "retrieved_context": retrieval_context,
            },
        )

    def build_artifacts(
        self,
        question: str,
        schema_context: SchemaContext,
        extra_context: list[str] | None = None,
    ) -> dict[str, Any]:
        _ = question
        _ = schema_context
        chunks = extra_context or []
        return {"retrieved_context_count": len(chunks)}

    def build_retrieval_artifacts(
        self,
        retrieved_chunks: list[RetrievedChunk] | None = None,
    ) -> dict[str, Any]:
        return {
            "retrieved_chunks": [
                {
                    "chunk_id": chunk.chunk_id,
                    "source_path": chunk.source_path,
                    "text": chunk.text,
                    "score": chunk.score,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in (retrieved_chunks or [])
            ]
        }
