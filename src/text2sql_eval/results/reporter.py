from __future__ import annotations

import json
import subprocess  # nosec B404
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..config import AppConfig
from ..dataset.schema import SchemaContext
from .schema import PipelineRecord, RequestedModel, RunArtifact, RunMetadata


class Reporter:
    def __init__(self, config: AppConfig):
        self._config = config
        self._records: list[PipelineRecord] = []
        self._schema_context: SchemaContext | None = None

    def record(self, record: PipelineRecord) -> None:
        """Append one result record to the in-memory buffer."""
        self._records.append(record)

    def set_schema_context(self, schema_context: SchemaContext) -> None:
        self._schema_context = schema_context

    @staticmethod
    def _git_commit() -> str | None:
        try:
            completed = subprocess.run(  # nosec B603 B607
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

        commit = completed.stdout.strip()
        return commit or None

    def _build_metadata(
        self,
        run_id: str,
        *,
        schema_artifact_path: str | None = None,
    ) -> RunMetadata:
        return RunMetadata(
            schema_version="v1",
            run_id=run_id,
            created_at=datetime.now(UTC).isoformat(timespec="milliseconds"),
            dataset_path=self._config.inputs.questions_file,
            db_path=self._config.inputs.database_file,
            limit=self._config.run_defaults.limit,
            tracks_requested=list(self._config.run_defaults.tracks),
            models_requested=[
                RequestedModel(provider=model.provider, model=model.model)
                for model in self._config.models
            ],
            git_commit=self._git_commit(),
            config_snapshot=asdict(self._config),
            schema_artifact_path=schema_artifact_path,
        )

    def flush(self, run_id: str, output_dir: str) -> None:
        run_dir = Path(output_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        schema_artifact_path: str | None = None
        if self._schema_context is not None:
            schema_artifact_path = "schema_context.json"
            (run_dir / schema_artifact_path).write_text(
                json.dumps(asdict(self._schema_context), indent=2),
                encoding="utf-8",
            )

        artifact = RunArtifact(
            run_metadata=self._build_metadata(
                run_id,
                schema_artifact_path=schema_artifact_path,
            ),
            records=list(self._records),
        )
        payload: dict[str, Any] = artifact.to_dict()

        (run_dir / "run.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )
