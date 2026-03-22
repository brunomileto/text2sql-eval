from __future__ import annotations

import time

from ..config import LLMModelConfig
from .base import LLMProvider, LLMResponse


class FakeProvider(LLMProvider):
    """Local deterministic provider for tests and offline integration runs."""

    def __init__(self, model_config: LLMModelConfig):
        self._model_config = model_config

    def generate(self, prompt: str) -> LLMResponse:
        _ = prompt
        started = time.perf_counter()
        sql = "SELECT 1"
        latency_ms = int((time.perf_counter() - started) * 1000)
        return LLMResponse(
            content=sql,
            input_tokens=1,
            output_tokens=2,
            latency_ms=latency_ms,
        )
