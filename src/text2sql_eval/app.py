from __future__ import annotations

from .config import load_config
from .pipeline.runner import run


def run_experiment(
    config_path: str = "config/config.yaml",
    *,
    track: str | None = None,
    limit: int | None = None,
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """Run one experiment and return the generated run_id.

    This API is the notebook-first entrypoint.
    Override parameters are reserved for a following step.
    """
    if any(value is not None for value in (track, limit, provider, model)):
        raise ValueError(
            "Overrides are not implemented yet. "
            "Use config_path-only invocation for now."
        )

    config = load_config(config_path)
    return run(config)
