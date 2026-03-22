from __future__ import annotations

from ..dataset.schema import SchemaContext
from ..prompts.loader import render_prompt
from .base import BaseTrack


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
        return render_prompt("track_a", {"question": question})
