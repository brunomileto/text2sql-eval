from __future__ import annotations

from ..dataset.schema import SchemaContext
from .base import BaseTrack

TRACK_A_PROMPT = """\
You are an expert SQL assistant.
Given the following question, write a valid SQL SELECT query that answers it.
Return only the SQL query, with no explanation or markdown formatting.

Question: {question}

SQL:"""


class TrackA(BaseTrack):
    @property
    def name(self) -> str:
        return "track_a"

    def build_prompt(
        self,
        question: str,
        schema_context: SchemaContext,
        extra_context: list[str] | None = None,
    ) -> str:
        _ = schema_context
        _ = extra_context
        return TRACK_A_PROMPT.format(question=question)
