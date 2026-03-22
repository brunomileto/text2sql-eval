from __future__ import annotations

from dataclasses import replace
from typing import Literal, TypeAlias, cast

from .config import AppConfig, LLMModelConfig, load_config
from .pipeline.runner import run

DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 1024

TrackName: TypeAlias = Literal["a", "b", "c"]
TrackSelector: TypeAlias = TrackName | Literal["all"] | list[TrackName]
TrackOverride: TypeAlias = TrackSelector | str

TRACK_DESCRIPTIONS: dict[TrackName, str] = {
    "a": "Question only (no schema metadata, no retrieval).",
    "b": "Question + schema metadata enrichment.",
    "c": "Question + metadata + retrieved context (RAG pre-fetch).",
}


def _normalize_track_name(value: str) -> TrackName:
    normalized = value.strip().lower()
    if normalized in TRACK_DESCRIPTIONS:
        return cast(TrackName, normalized)
    allowed = ", ".join(sorted(TRACK_DESCRIPTIONS))
    raise ValueError(f"Unknown track '{value}'. Allowed tracks: {allowed}, all")


def _parse_tracks(track: TrackOverride, current_tracks: list[str]) -> list[str]:
    if track == "all":
        return list(current_tracks)

    if isinstance(track, list):
        if not track:
            raise ValueError("track override must include at least one track")
        return [_normalize_track_name(item) for item in track]

    value = track.strip()
    if not value:
        raise ValueError("track override cannot be empty")

    parsed = [item.strip() for item in value.split(",") if item.strip()]
    if not parsed:
        raise ValueError("track override must include at least one track")
    return [_normalize_track_name(item) for item in parsed]


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
    track: TrackOverride | None,
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
    track: TrackOverride | None = None,
    limit: int | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """Run one experiment and return the generated run_id.

    Track meanings:
    - `a`: question-only prompt
    - `b`: metadata-enriched prompt
    - `c`: metadata + retrieval (RAG pre-fetch)
    - `all`: keep tracks from config as-is

    `track` may be passed as:
    - typed value (`"a"`, `"b"`, `"c"`, `"all"`)
    - list of typed values (`["a", "c"]`)
    - comma-separated string (`"a,c"`) for CLI-style usage
    """

    config = load_config(config_path)
    config = _apply_overrides(
        config,
        track=track,
        limit=limit,
        provider=provider,
        model=model,
    )
    return run(config)
