from __future__ import annotations

from ..dataset.schema import SchemaContext
from ..prompts.loader import render_prompt
from .base import BaseTrack


class TrackB(BaseTrack):
    @property
    def name(self) -> str:
        return "track_b"

    @property
    def uses_schema_context(self) -> bool:
        return True

    def build_prompt(
        self,
        question: str,
        schema_context: SchemaContext,
        extra_context: list[str] | None = None,
    ) -> str:
        _ = extra_context
        return render_prompt(
            "track_b",
            {
                "question": question,
                "schema": schema_context.to_markdown(),
            },
        )
