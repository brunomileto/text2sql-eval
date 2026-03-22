from __future__ import annotations

import json

from text2sql_eval.results.schema import (
    ExecutionFacts,
    PipelineRecord,
    RequestedModel,
    RunArtifact,
    RunMetadata,
)


def test_run_artifact_to_dict_contains_expected_contract_fields():
    artifact = RunArtifact(
        run_metadata=RunMetadata(
            schema_version="v1",
            run_id="20260322-100000",
            created_at="2026-03-22T10:00:00Z",
            dataset_path="data/dev.json",
            db_path="data/database.sqlite",
            limit=10,
            tracks_requested=["a", "b"],
            models_requested=[
                RequestedModel(provider="openai", model="gpt-4o"),
                RequestedModel(
                    provider="anthropic", model="claude-3-5-sonnet-20241022"
                ),
            ],
            git_commit="abc123",
            config_snapshot={"experiment": {"output_dir": "results/"}},
        ),
        records=[
            PipelineRecord(
                question_id="q001",
                question="How many employees?",
                track="track_a",
                provider="openai",
                model="gpt-4o",
                prompt="Question: How many employees?",
                raw_response="SELECT COUNT(*) FROM employees",
                normalized_sql="SELECT COUNT(*) FROM employees",
                input_tokens=100,
                output_tokens=20,
                latency_ms=300,
                generated=ExecutionFacts(
                    success=True,
                    error_type_raw=None,
                    error_message=None,
                    row_count=1,
                    rows_sample=[[42]],
                ),
                reference=ExecutionFacts(
                    success=True,
                    error_type_raw=None,
                    error_message=None,
                    row_count=1,
                    rows_sample=[[42]],
                ),
                rows_equal=True,
                generated_rows_hash="hash-a",
                reference_rows_hash="hash-a",
                pipeline_latency_ms=420,
                timestamps={"started_at": "2026-03-22T10:00:00Z"},
            )
        ],
    )

    payload = artifact.to_dict()

    assert "run_metadata" in payload
    assert "records" in payload
    assert payload["run_metadata"]["schema_version"] == "v1"
    assert payload["run_metadata"]["tracks_requested"] == ["a", "b"]
    assert payload["records"][0]["track"] == "track_a"
    assert payload["records"][0]["generated"]["row_count"] == 1
    assert payload["records"][0]["rows_equal"] is True


def test_run_artifact_to_json_is_valid_and_roundtrips():
    artifact = RunArtifact(
        run_metadata=RunMetadata(
            schema_version="v1",
            run_id="20260322-100001",
            created_at="2026-03-22T10:00:01Z",
            dataset_path="data/dev.json",
            db_path="data/database.sqlite",
            limit=None,
            tracks_requested=["a"],
            models_requested=[RequestedModel(provider="openai", model="gpt-4o")],
            git_commit=None,
            config_snapshot={},
        ),
        records=[],
    )

    encoded = artifact.to_json()
    decoded = json.loads(encoded)

    assert decoded["run_metadata"]["run_id"] == "20260322-100001"
    assert decoded["run_metadata"]["models_requested"][0]["provider"] == "openai"
    assert decoded["records"] == []
