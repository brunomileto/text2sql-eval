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
class InputsConfig:
    questions_file: str
    database_file: str


@dataclass
class RunDefaultsConfig:
    tracks: list[str]
    limit: int | None
    output_dir: str


@dataclass
class AppConfig:
    models: list[LLMModelConfig]
    inputs: InputsConfig
    run_defaults: RunDefaultsConfig
    rag: dict[str, Any]


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
    """Load config.yaml and return a typed AppConfig."""

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if raw is None:
        raise ValueError(f"Config file is empty: {config_path}")

    root = _expect_mapping(raw, "root")

    model_items = _expect_list(_require(root, "models", "root"), "models")
    models: list[LLMModelConfig] = []
    for index, item in enumerate(model_items):
        model_raw = _expect_mapping(item, f"models[{index}]")
        models.append(
            LLMModelConfig(
                provider=str(_require(model_raw, "provider", f"models[{index}]")),
                model=str(_require(model_raw, "model", f"models[{index}]")),
                temperature=float(
                    _require(model_raw, "temperature", f"models[{index}]")
                ),
                max_tokens=int(_require(model_raw, "max_tokens", f"models[{index}]")),
            )
        )

    inputs_raw = _expect_mapping(_require(root, "inputs", "root"), "inputs")
    inputs = InputsConfig(
        questions_file=str(_require(inputs_raw, "questions_file", "inputs")),
        database_file=str(_require(inputs_raw, "database_file", "inputs")),
    )

    run_raw = _expect_mapping(_require(root, "run_defaults", "root"), "run_defaults")
    tracks_raw = _expect_list(
        _require(run_raw, "tracks", "run_defaults"), "run_defaults.tracks"
    )
    limit_raw = _require(run_raw, "limit", "run_defaults")
    if limit_raw is not None:
        limit_raw = int(limit_raw)

    run_defaults = RunDefaultsConfig(
        tracks=[str(track) for track in tracks_raw],
        limit=limit_raw,
        output_dir=str(_require(run_raw, "output_dir", "run_defaults")),
    )

    rag_raw = root.get("rag", {})
    rag = _expect_mapping(rag_raw, "rag")

    return AppConfig(
        models=models,
        inputs=inputs,
        run_defaults=run_defaults,
        rag=rag,
    )
