from __future__ import annotations

import os
import time

from anthropic import Anthropic

from ..config import LLMModelConfig
from .base import LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    def __init__(self, model_config: LLMModelConfig):
        self._model_config = model_config

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self._client = Anthropic(api_key=api_key)

    def generate(self, prompt: str) -> LLMResponse:
        started = time.perf_counter()
        response = self._client.messages.create(
            model=self._model_config.model,
            temperature=self._model_config.temperature,
            max_tokens=self._model_config.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        latency_ms = int((time.perf_counter() - started) * 1000)

        content = ""
        for block in response.content:
            block_text = getattr(block, "text", None)
            if block_text:
                content = block_text
                break

        usage = response.usage
        input_tokens = int(usage.input_tokens) if usage and usage.input_tokens else 0
        output_tokens = int(usage.output_tokens) if usage and usage.output_tokens else 0

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )
