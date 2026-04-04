from __future__ import annotations

from typer.testing import CliRunner

from text2sql_eval import cli
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
                temperature=0.0,
                max_tokens=1024,
            )
        ],
        inputs=InputsConfig(
            questions_file="data/dev.json",
            database_file="data/database.sqlite",
        ),
        run_defaults=RunDefaultsConfig(tracks=["a"], limit=None, output_dir="results/"),
        rag={},
    )


def test_cli_run_experiment_delegates_to_app(monkeypatch):
    runner = CliRunner()
    captured: dict[str, object] = {}

    def fake_run_experiment(**kwargs):
        captured.update(kwargs)
        return "20260322-130000"

    monkeypatch.setattr(cli, "run_experiment_api", fake_run_experiment)
    monkeypatch.setattr(cli, "load_config", lambda path: _base_config())

    result = runner.invoke(
        cli.app,
        [
            "run-experiment",
            "--track",
            "a,c",
            "--limit",
            "5",
            "--provider",
            "openai",
            "--model",
            "gpt-4o",
            "--config-path",
            "config/custom.yaml",
        ],
    )

    assert result.exit_code == 0
    assert captured == {
        "config_path": "config/custom.yaml",
        "track": "a,c",
        "limit": 5,
        "provider": "openai",
        "model": "gpt-4o",
    }
    assert "Run ID: 20260322-130000" in result.stdout
    assert "Artifact: results/20260322-130000/run.json" in result.stdout


def test_cli_surfaces_api_errors(monkeypatch):
    runner = CliRunner()

    def fake_run_experiment(**kwargs):
        _ = kwargs
        raise ValueError(
            "provider and model must be provided together, or provider only"
        )

    monkeypatch.setattr(cli, "run_experiment_api", fake_run_experiment)

    result = runner.invoke(cli.app, ["run-experiment", "--provider", "openai"])

    assert result.exit_code != 0
    assert isinstance(result.exception, ValueError)
    assert (
        str(result.exception)
        == "provider and model must be provided together, or provider only"
    )


def test_cli_passes_defaults_and_uses_same_config_path_for_artifact_print(monkeypatch):
    runner = CliRunner()
    captured: dict[str, object] = {}

    def fake_run_experiment(**kwargs):
        captured["kwargs"] = kwargs
        return "20260322-131500"

    def fake_load_config(path: str) -> AppConfig:
        captured["config_path"] = path
        return _base_config()

    monkeypatch.setattr(cli, "run_experiment_api", fake_run_experiment)
    monkeypatch.setattr(cli, "load_config", fake_load_config)

    result = runner.invoke(cli.app, ["run-experiment"])

    assert result.exit_code == 0
    assert captured["kwargs"] == {
        "config_path": "config/config.yaml",
        "track": None,
        "limit": None,
        "provider": None,
        "model": None,
    }
    assert captured["config_path"] == "config/config.yaml"
    assert "Artifact: results/20260322-131500/run.json" in result.stdout


def test_cli_build_rag_index_delegates_to_app(monkeypatch):
    runner = CliRunner()

    class Result:
        index_path = "data/rag_index"
        manifest_path = "data/rag_index/manifest.json"
        source_count = 3
        chunk_count = 12

    monkeypatch.setattr(cli, "build_rag_index_api", lambda config_path: Result())

    result = runner.invoke(
        cli.app,
        ["build-rag-index", "--config-path", "config/custom.yaml"],
    )

    assert result.exit_code == 0
    assert "RAG Index: data/rag_index" in result.stdout
    assert "Manifest: data/rag_index/manifest.json" in result.stdout
    assert "Source Files: 3" in result.stdout
    assert "Chunks: 12" in result.stdout
