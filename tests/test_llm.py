from __future__ import annotations

from types import SimpleNamespace

import pytest

from text2sql_eval.config import LLMModelConfig
from text2sql_eval.llm.anthropic_provider import AnthropicProvider
from text2sql_eval.llm.openai_provider import OpenAIProvider
from text2sql_eval.llm.registry import get_provider


def test_openai_provider_generate_returns_content_usage_and_latency(monkeypatch):
    captured: dict[str, object] = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="SELECT 1"))],
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
        )

    class FakeOpenAI:
        def __init__(self, api_key: str):
            captured["api_key"] = api_key
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=fake_create),
            )

    perf_values = iter([10.0, 10.123])

    from text2sql_eval.llm import openai_provider

    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr(openai_provider, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(openai_provider.time, "perf_counter", lambda: next(perf_values))

    provider = OpenAIProvider(
        LLMModelConfig(
            provider="openai",
            model="gpt-4o",
            temperature=0.0,
            max_tokens=256,
        )
    )
    response = provider.generate("Count users")

    assert captured["api_key"] == "test-openai-key"
    assert captured["model"] == "gpt-4o"
    assert captured["temperature"] == 0.0
    assert captured["max_completion_tokens"] == 256
    assert captured["messages"] == [{"role": "user", "content": "Count users"}]
    assert response.content == "SELECT 1"
    assert response.input_tokens == 11
    assert response.output_tokens == 7
    assert 120 <= response.latency_ms <= 130


def test_anthropic_provider_generate_returns_content_usage_and_latency(monkeypatch):
    captured: dict[str, object] = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="SELECT 2")],
            usage=SimpleNamespace(input_tokens=13, output_tokens=5),
        )

    class FakeAnthropic:
        def __init__(self, api_key: str):
            captured["api_key"] = api_key
            self.messages = SimpleNamespace(create=fake_create)

    perf_values = iter([20.0, 20.250])

    from text2sql_eval.llm import anthropic_provider

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setattr(anthropic_provider, "Anthropic", FakeAnthropic)
    monkeypatch.setattr(
        anthropic_provider.time, "perf_counter", lambda: next(perf_values)
    )

    provider = AnthropicProvider(
        LLMModelConfig(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            temperature=0.0,
            max_tokens=256,
        )
    )
    response = provider.generate("List active accounts")

    assert captured["api_key"] == "test-anthropic-key"
    assert captured["model"] == "claude-3-5-sonnet-20241022"
    assert captured["temperature"] == 0.0
    assert captured["max_tokens"] == 256
    assert captured["messages"] == [{"role": "user", "content": "List active accounts"}]
    assert response.content == "SELECT 2"
    assert response.input_tokens == 13
    assert response.output_tokens == 5
    assert response.latency_ms == 250


@pytest.mark.parametrize(
    ("provider", "env_key", "provider_cls"),
    [
        ("openai", "OPENAI_API_KEY", OpenAIProvider),
        ("anthropic", "ANTHROPIC_API_KEY", AnthropicProvider),
    ],
)
def test_provider_init_requires_api_key(monkeypatch, provider, env_key, provider_cls):
    monkeypatch.delenv(env_key, raising=False)
    model_config = LLMModelConfig(
        provider=provider,
        model="dummy",
        temperature=0.0,
        max_tokens=128,
    )

    with pytest.raises(ValueError, match=env_key):
        provider_cls(model_config)


def test_get_provider_returns_matching_provider_type(monkeypatch):
    from text2sql_eval.llm import anthropic_provider, openai_provider

    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setattr(openai_provider, "OpenAI", lambda api_key: SimpleNamespace())
    monkeypatch.setattr(
        anthropic_provider, "Anthropic", lambda api_key: SimpleNamespace()
    )

    openai_instance = get_provider(
        LLMModelConfig(
            provider="openai",
            model="gpt-4o",
            temperature=0.0,
            max_tokens=128,
        )
    )
    anthropic_instance = get_provider(
        LLMModelConfig(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            temperature=0.0,
            max_tokens=128,
        )
    )

    assert isinstance(openai_instance, OpenAIProvider)
    assert isinstance(anthropic_instance, AnthropicProvider)


def test_get_provider_raises_for_unknown_provider():
    model_config = LLMModelConfig(
        provider="unknown",
        model="x",
        temperature=0.0,
        max_tokens=128,
    )

    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_provider(model_config)
