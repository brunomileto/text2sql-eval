from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..dataset.schema import SchemaContext
from ..rag.models import RetrievedChunk


class BaseTrack(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in output files and logs."""

    @property
    def uses_schema_context(self) -> bool:
        """Whether this track requires run-scoped schema metadata."""
        return False

    @property
    def uses_retrieval_context(self) -> bool:
        """Whether this track requires run-scoped retrieval context."""
        return False

    @abstractmethod
    def build_prompt(
        self,
        question: str,
        schema_context: SchemaContext,
        extra_context: list[str] | None = None,
    ) -> str:
        """Return the final prompt string to send to the LLM."""

    def pre_fetch(
        self,
        question: str,
        retrieved_chunks: list[RetrievedChunk] | None = None,
    ) -> list[str]:
        """Optional RAG pre-step. Default is no retrieval."""
        _ = question
        _ = retrieved_chunks
        return []

    def build_artifacts(
        self,
        question: str,
        schema_context: SchemaContext,
        extra_context: list[str] | None = None,
    ) -> dict[str, Any]:
        """Optional structured metadata captured in pipeline output."""
        _ = question
        _ = schema_context
        _ = extra_context
        return {}

    def build_retrieval_artifacts(
        self,
        retrieved_chunks: list[RetrievedChunk] | None = None,
    ) -> dict[str, Any]:
        _ = retrieved_chunks
        return {}
