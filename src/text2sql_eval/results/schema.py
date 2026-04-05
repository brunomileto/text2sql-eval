from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RequestedModel:
    provider: str
    model: str


@dataclass
class RunMetadata:
    schema_version: str
    run_id: str
    created_at: str
    dataset_path: str
    db_path: str
    limit: int | None
    tracks_requested: list[str]
    models_requested: list[RequestedModel]
    git_commit: str | None
    config_snapshot: dict[str, Any]
    schema_artifact_path: str | None = None
    rag_manifest_path: str | None = None


@dataclass
class ExecutionFacts:
    success: bool
    error_type_raw: str | None
    error_message: str | None
    row_count: int | None
    rows_sample: list[list[Any]] = field(default_factory=list)


@dataclass
class PipelineRecord:
    question_id: str
    question: str
    track: str
    provider: str
    model: str
    prompt: str
    extra_context: list[str] = field(default_factory=list)
    track_artifacts: dict[str, Any] = field(default_factory=dict)
    raw_response: str = ""
    normalized_sql: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    generated: ExecutionFacts = field(
        default_factory=lambda: ExecutionFacts(
            success=False,
            error_type_raw=None,
            error_message=None,
            row_count=None,
        )
    )
    reference: ExecutionFacts = field(
        default_factory=lambda: ExecutionFacts(
            success=False,
            error_type_raw=None,
            error_message=None,
            row_count=None,
        )
    )
    rows_equal: bool | None = None
    generated_rows_hash: str | None = None
    reference_rows_hash: str | None = None
    pipeline_latency_ms: int = 0
    timestamps: dict[str, str] = field(default_factory=dict)


@dataclass
class RunArtifact:
    run_metadata: RunMetadata
    records: list[PipelineRecord]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
