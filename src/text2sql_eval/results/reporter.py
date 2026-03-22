from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import AppConfig
from .schema import PipelineRecord, RequestedModel, RunArtifact, RunMetadata


class Reporter:
    def __init__(self, config: AppConfig):
        self._config = config
        self._records: list[PipelineRecord] = []

    def record(self, record: PipelineRecord) -> None:
        """Append one result record to the in-memory buffer."""
        self._records.append(record)

    @staticmethod
    def _git_commit() -> str | None:
        try:
            completed = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

        commit = completed.stdout.strip()
        return commit or None

    def _build_metadata(self, run_id: str) -> RunMetadata:
        return RunMetadata(
            schema_version="v1",
            run_id=run_id,
            created_at=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            dataset_path=self._config.dataset.questions,
            db_path=self._config.dataset.db,
            limit=self._config.experiment.limit,
            tracks_requested=list(self._config.experiment.tracks),
            models_requested=[
                RequestedModel(provider=model.provider, model=model.model)
                for model in self._config.llm.models
            ],
            git_commit=self._git_commit(),
            config_snapshot=asdict(self._config),
        )

    def flush(self, run_id: str, output_dir: str) -> None:
        run_dir = Path(output_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        artifact = RunArtifact(
            run_metadata=self._build_metadata(run_id),
            records=list(self._records),
        )
        payload: dict[str, Any] = artifact.to_dict()

        (run_dir / "run.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
