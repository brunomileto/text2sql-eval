from __future__ import annotations

import pytest

from text2sql_eval.app import run_experiment
from text2sql_eval.config import (
    AppConfig,
    InputsConfig,
    LLMModelConfig,
    RunDefaultsConfig,
)


def _base_config() -> AppConfig:
    return AppConfig(
        models=[
            LLMModelConfig(
                provider="openai",
                model="gpt-4o",
                temperature=0.3,
                max_tokens=333,
            ),
            LLMModelConfig(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                temperature=0.1,
                max_tokens=444,
            ),
        ],
        inputs=InputsConfig(
            questions_file="data/dev.json",
            database_file="data/database.sqlite",
        ),
        run_defaults=RunDefaultsConfig(
            tracks=["a", "b"], limit=None, output_dir="results/"
        ),
        rag={},
    )


def test_run_experiment_loads_config_and_runs_pipeline(monkeypatch):
    calls: dict[str, object] = {}

    def fake_load_config(path: str):
        calls["config_path"] = path
        return _base_config()

    def fake_run(config: AppConfig):
        calls["config"] = config
        return "20260322-120000"

    from text2sql_eval import app

    monkeypatch.setattr(app, "load_config", fake_load_config)
    monkeypatch.setattr(app, "run", fake_run)

    run_id = run_experiment(config_path="config/custom.yaml")

    assert run_id == "20260322-120000"
    assert calls["config_path"] == "config/custom.yaml"
    config = calls["config"]
    assert isinstance(config, AppConfig)
    assert config.run_defaults.tracks == ["a", "b"]


def test_run_experiment_applies_track_and_limit_overrides(monkeypatch):
    captured: dict[str, AppConfig] = {}

    from text2sql_eval import app

    monkeypatch.setattr(app, "load_config", lambda path: _base_config())
    monkeypatch.setattr(
        app,
        "run",
        lambda config: captured.setdefault("config", config) and "run-id",
    )

    run_experiment(track="a,c", limit=5)

    assert captured["config"].run_defaults.tracks == ["a", "c"]
    assert captured["config"].run_defaults.limit == 5


def test_run_experiment_supports_track_all(monkeypatch):
    captured: dict[str, AppConfig] = {}

    from text2sql_eval import app

    monkeypatch.setattr(app, "load_config", lambda path: _base_config())
    monkeypatch.setattr(
        app,
        "run",
        lambda config: captured.setdefault("config", config) and "run-id",
    )

    run_experiment(track="all")

    assert captured["config"].run_defaults.tracks == ["a", "b"]


def test_run_experiment_supports_typed_track_list_input(monkeypatch):
    captured: dict[str, AppConfig] = {}

    from text2sql_eval import app

    monkeypatch.setattr(app, "load_config", lambda path: _base_config())
    monkeypatch.setattr(
        app,
        "run",
        lambda config: captured.setdefault("config", config) and "run-id",
    )

    run_experiment(track=["a", "c"])

    assert captured["config"].run_defaults.tracks == ["a", "c"]


def test_run_experiment_applies_single_model_override(monkeypatch):
    captured: dict[str, AppConfig] = {}

    from text2sql_eval import app

    monkeypatch.setattr(app, "load_config", lambda path: _base_config())
    monkeypatch.setattr(
        app,
        "run",
        lambda config: captured.setdefault("config", config) and "run-id",
    )

    run_experiment(provider="openai", model="gpt-4o")

    models = captured["config"].models
    assert len(models) == 1
    assert models[0].provider == "openai"
    assert models[0].model == "gpt-4o"
    assert models[0].temperature == 0.3
    assert models[0].max_tokens == 333


def test_run_experiment_requires_provider_and_model_together():
    with pytest.raises(ValueError, match="provider and model"):
        run_experiment(model="gpt-4o")


def test_run_experiment_provider_only_runs_all_models_for_provider(monkeypatch):
    captured: dict[str, AppConfig] = {}

    from text2sql_eval import app

    monkeypatch.setattr(app, "load_config", lambda path: _base_config())
    monkeypatch.setattr(
        app,
        "run",
        lambda config: captured.setdefault("config", config) and "run-id",
    )

    run_experiment(provider="openai")

    models = captured["config"].models
    assert len(models) == 1
    assert models[0].provider == "openai"
    assert models[0].model == "gpt-4o"


def test_run_experiment_provider_only_rejects_unknown_provider(monkeypatch):
    from text2sql_eval import app

    monkeypatch.setattr(app, "load_config", lambda path: _base_config())

    with pytest.raises(ValueError, match="Unknown provider"):
        run_experiment(provider="fake")


def test_run_experiment_provider_and_model_reject_unknown_pair(monkeypatch):
    from text2sql_eval import app

    monkeypatch.setattr(app, "load_config", lambda path: _base_config())

    with pytest.raises(ValueError, match="Unknown provider/model pair"):
        run_experiment(provider="openai", model="gpt-4o-mini")


def test_run_experiment_rejects_negative_limit():
    with pytest.raises(ValueError, match="limit must be >= 0"):
        run_experiment(limit=-1)


def test_run_experiment_rejects_empty_track_override():
    with pytest.raises(ValueError, match="track override"):
        run_experiment(track="   ")


def test_run_experiment_rejects_unknown_track_name():
    with pytest.raises(ValueError, match="Unknown track"):
        run_experiment(track="z")
