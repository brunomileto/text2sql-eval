from __future__ import annotations

from ..config import LLMModelConfig
from .anthropic_provider import AnthropicProvider
from .base import LLMProvider
from .fake_provider import FakeProvider
from .maritaca_provider import MaritacaProvider
from .openai_provider import OpenAIProvider

LLM_REGISTRY: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "maritaca": MaritacaProvider,
    "fake": FakeProvider,
}


def get_provider(model_config: LLMModelConfig) -> LLMProvider:
    """Instantiate the correct provider for a single model config entry."""
    name = model_config.provider
    provider_type = LLM_REGISTRY.get(name)
    if provider_type is None:
        raise ValueError(
            f"Unknown LLM provider '{name}'. Available: {list(LLM_REGISTRY)}"
        )
    return provider_type(model_config)
