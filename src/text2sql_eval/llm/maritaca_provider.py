from __future__ import annotations

import os
import time

from openai import OpenAI

from ..config import LLMModelConfig
from .base import LLMProvider, LLMResponse


class MaritacaProvider(LLMProvider):
    def __init__(self, model_config: LLMModelConfig):
        self._model_config = model_config

        api_key = os.getenv("MARITACA_API_KEY")
        if not api_key:
            raise ValueError("MARITACA_API_KEY environment variable is required")

        base_url = os.getenv("MARITACA_BASE_URL", "https://chat.maritaca.ai/api")

        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str) -> LLMResponse:
        print("heeeeeeeere")
        started = time.perf_counter()
        response = self._client.chat.completions.create(
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

        content = response.choices[0].message.content or ""
        usage = response.usage
        input_tokens = int(usage.prompt_tokens) if usage and usage.prompt_tokens else 0
        output_tokens = (
            int(usage.completion_tokens) if usage and usage.completion_tokens else 0
        )

        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )
