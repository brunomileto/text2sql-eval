from __future__ import annotations

from dataclasses import replace

from .config import AppConfig, LLMModelConfig, load_config
from .pipeline.runner import run

DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 1024


def _parse_tracks(track: str, current_tracks: list[str]) -> list[str]:
    value = track.strip().lower()
    if not value:
        raise ValueError("track override cannot be empty")
    if value == "all":
        return list(current_tracks)

    parsed = [item.strip().lower() for item in value.split(",") if item.strip()]
    if not parsed:
        raise ValueError("track override must include at least one track")
    return parsed


def _select_model_override(
    current_models: list[LLMModelConfig],
    provider: str,
    model: str,
) -> LLMModelConfig:
    for candidate in current_models:
        if candidate.provider == provider and candidate.model == model:
            return candidate

    return LLMModelConfig(
        provider=provider,
        model=model,
        temperature=DEFAULT_TEMPERATURE,
        max_tokens=DEFAULT_MAX_TOKENS,
    )


def _apply_overrides(
    config: AppConfig,
    *,
    track: str | None,
    limit: int | None,
    provider: str | None,
    model: str | None,
) -> AppConfig:
    tracks = list(config.experiment.tracks)
    models = list(config.llm.models)
    effective_limit = config.experiment.limit if limit is None else limit

    if track is not None:
        tracks = _parse_tracks(track, tracks)

    if effective_limit is not None and effective_limit < 0:
        raise ValueError("limit must be >= 0")

    has_provider = provider is not None
    has_model = model is not None
    if has_provider != has_model:
        raise ValueError("provider and model must be provided together")

    if provider is not None and model is not None:
        models = [_select_model_override(models, provider=provider, model=model)]

    return replace(
        config,
        llm=replace(config.llm, models=models),
        experiment=replace(config.experiment, tracks=tracks, limit=effective_limit),
    )


def run_experiment(
    config_path: str = "config/config.yaml",
    *,
    track: str | None = None,
    limit: int | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """Run one experiment and return the generated run_id."""

    config = load_config(config_path)
    config = _apply_overrides(
        config,
        track=track,
        limit=limit,
        provider=provider,
        model=model,
    )
    return run(config)
