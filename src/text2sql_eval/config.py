from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class LLMModelConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int


@dataclass
class LLMConfig:
    models: list[LLMModelConfig]


@dataclass
class DatasetConfig:
    questions: str
    db: str


@dataclass
class ExperimentConfig:
    tracks: list[str]
    limit: int | None
    output_dir: str


@dataclass
class AppConfig:
    llm: LLMConfig
    dataset: DatasetConfig
    experiment: ExperimentConfig


def _expect_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"'{field_name}' must be a mapping")
    return value


def _expect_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"'{field_name}' must be a list")
    return value


def _require(mapping: dict[str, Any], key: str, section: str) -> Any:
    if key not in mapping:
        raise ValueError(f"Missing required key '{key}' in '{section}'")
    return mapping[key]


def load_config(path: str = "config/config.yaml") -> AppConfig:
    """Load config.yaml and return a typed AppConfig.

    API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY) are read directly
    by the LLM providers from the environment and are not stored here.
    """

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if raw is None:
        raise ValueError(f"Config file is empty: {config_path}")

    root = _expect_mapping(raw, "root")

    llm_raw = _expect_mapping(_require(root, "llm", "root"), "llm")
    model_items = _expect_list(_require(llm_raw, "models", "llm"), "llm.models")
    models: list[LLMModelConfig] = []
    for index, item in enumerate(model_items):
        model_raw = _expect_mapping(item, f"llm.models[{index}]")
        models.append(
            LLMModelConfig(
                provider=str(_require(model_raw, "provider", f"llm.models[{index}]")),
                model=str(_require(model_raw, "model", f"llm.models[{index}]")),
                temperature=float(
                    _require(model_raw, "temperature", f"llm.models[{index}]")
                ),
                max_tokens=int(
                    _require(model_raw, "max_tokens", f"llm.models[{index}]")
                ),
            )
        )

    dataset_raw = _expect_mapping(_require(root, "dataset", "root"), "dataset")
    dataset = DatasetConfig(
        questions=str(_require(dataset_raw, "questions", "dataset")),
        db=str(_require(dataset_raw, "db", "dataset")),
    )

    experiment_raw = _expect_mapping(_require(root, "experiment", "root"), "experiment")
    tracks_raw = _expect_list(
        _require(experiment_raw, "tracks", "experiment"), "experiment.tracks"
    )
    limit_raw = _require(experiment_raw, "limit", "experiment")
    if limit_raw is not None:
        limit_raw = int(limit_raw)

    experiment = ExperimentConfig(
        tracks=[str(track) for track in tracks_raw],
        limit=limit_raw,
        output_dir=str(_require(experiment_raw, "output_dir", "experiment")),
    )

    return AppConfig(
        llm=LLMConfig(models=models),
        dataset=dataset,
        experiment=experiment,
    )
