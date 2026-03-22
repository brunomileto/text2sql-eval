from __future__ import annotations

from pathlib import Path
from typing import cast

import typer

from .app import TRACK_DESCRIPTIONS, TrackOverride, run_experiment as run_experiment_api
from .config import load_config

app = typer.Typer()


@app.callback()
def main() -> None:
    """Text2SQL evaluation CLI."""


@app.command("run-experiment")
def run_experiment_command(
    track: str | None = typer.Option(
        None,
        help=(
            "Track(s): a,b,c or all. "
            f"a={TRACK_DESCRIPTIONS['a']} "
            f"b={TRACK_DESCRIPTIONS['b']} "
            f"c={TRACK_DESCRIPTIONS['c']}"
        ),
    ),
    limit: int | None = typer.Option(None, help="Number of questions"),
    provider: str | None = typer.Option(None, help="Single provider override"),
    model: str | None = typer.Option(None, help="Single model override"),
    config_path: str = typer.Option("config/config.yaml", help="Config file path"),
) -> None:
    """Run pipeline and write run.json artifact."""
    run_id = run_experiment_api(
        config_path=config_path,
        track=cast(TrackOverride | None, track),
        limit=limit,
        provider=provider,
        model=model,
    )

    output_dir = load_config(config_path).run_defaults.output_dir
    artifact_path = Path(output_dir) / run_id / "run.json"
    typer.echo(f"[text2sql-eval] Run ID: {run_id}")
    typer.echo(f"[text2sql-eval] Artifact: {artifact_path}")
