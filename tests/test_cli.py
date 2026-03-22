from __future__ import annotations

from typer.testing import CliRunner

from text2sql_eval import cli
from text2sql_eval.config import (
    AppConfig,
    DatasetConfig,
    ExperimentConfig,
    LLMConfig,
    LLMModelConfig,
)


def _base_config() -> AppConfig:
    return AppConfig(
        llm=LLMConfig(
            models=[
                LLMModelConfig(
                    provider="openai",
                    model="gpt-4o",
                    temperature=0.0,
                    max_tokens=1024,
                )
            ]
        ),
        dataset=DatasetConfig(questions="data/dev.json", db="data/database.sqlite"),
        experiment=ExperimentConfig(tracks=["a"], limit=None, output_dir="results/"),
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
        raise ValueError("provider and model must be provided together")

    monkeypatch.setattr(cli, "run_experiment_api", fake_run_experiment)

    result = runner.invoke(cli.app, ["run-experiment", "--provider", "openai"])

    assert result.exit_code != 0
    assert isinstance(result.exception, ValueError)
    assert str(result.exception) == "provider and model must be provided together"
