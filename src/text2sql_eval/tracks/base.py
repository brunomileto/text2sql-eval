from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..dataset.schema import SchemaContext


class BaseTrack(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in output files and logs."""

    @property
    def uses_schema_context(self) -> bool:
        """Whether this track requires run-scoped schema metadata."""
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
        vector_store=None,
    ) -> list[str]:
        """Optional RAG pre-step. Default is no retrieval."""
        _ = question
        _ = vector_store
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
