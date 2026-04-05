from __future__ import annotations

import json

from text2sql_eval.config import (
    AppConfig,
    InputsConfig,
    LLMModelConfig,
    RunDefaultsConfig,
)
from text2sql_eval.dataset.schema import SchemaContext
from text2sql_eval.results.reporter import Reporter
from text2sql_eval.results.schema import ExecutionFacts, PipelineRecord


def _build_config(output_dir: str) -> AppConfig:
    return AppConfig(
        models=[
            LLMModelConfig(
                provider="openai",
                model="gpt-4o",
                temperature=0.0,
                max_tokens=1024,
            )
        ],
        inputs=InputsConfig(
            questions_file="data/dev.json",
            database_file="data/database.sqlite",
        ),
        run_defaults=RunDefaultsConfig(tracks=["a"], limit=None, output_dir=output_dir),
        rag={},
    )


def test_reporter_flush_writes_run_artifact_json(tmp_path):
    output_dir = str(tmp_path / "results")
    reporter = Reporter(config=_build_config(output_dir))
    reporter.set_schema_context(SchemaContext())

    reporter.record(
        PipelineRecord(
            question_id="q001",
            question="How many employees are there?",
            track="track_a",
            provider="openai",
            model="gpt-4o",
            prompt="prompt-1",
            raw_response="SELECT COUNT(*) FROM employees",
            normalized_sql="SELECT COUNT(*) FROM employees",
            input_tokens=100,
            output_tokens=20,
            latency_ms=400,
            generated=ExecutionFacts(
                success=True,
                error_type_raw=None,
                error_message=None,
                row_count=1,
                rows_sample=[[1]],
            ),
            reference=ExecutionFacts(
                success=True,
                error_type_raw=None,
                error_message=None,
                row_count=1,
                rows_sample=[[1]],
            ),
            rows_equal=True,
        ),
    )
    reporter.record(
        PipelineRecord(
            question_id="q001",
            question="How many employees are there?",
            track="track_a",
            provider="openai",
            model="gpt-4o",
            prompt="prompt-2",
            raw_response="SELEC COUNT(*) FROM employees",
            normalized_sql="SELEC COUNT(*) FROM employees",
            input_tokens=120,
            output_tokens=10,
            latency_ms=600,
            generated=ExecutionFacts(
                success=False,
                error_type_raw="SYNTAX_ERROR",
                error_message="syntax error",
                row_count=None,
                rows_sample=[],
            ),
            reference=ExecutionFacts(
                success=True,
                error_type_raw=None,
                error_message=None,
                row_count=1,
                rows_sample=[[1]],
            ),
            rows_equal=False,
        ),
    )

    reporter.flush(run_id="20260319-120000", output_dir=output_dir)

    run_dir = tmp_path / "results" / "20260319-120000"
    run_json = run_dir / "run.json"
    schema_json = run_dir / "schema_context.json"
    assert run_json.exists()
    assert schema_json.exists()

    payload = json.loads(run_json.read_text(encoding="utf-8"))
    schema_payload = json.loads(schema_json.read_text(encoding="utf-8"))

    assert payload["run_metadata"]["schema_version"] == "v1"
    assert payload["run_metadata"]["run_id"] == "20260319-120000"
    assert payload["run_metadata"]["dataset_path"] == "data/dev.json"
    assert payload["run_metadata"]["db_path"] == "data/database.sqlite"
    assert payload["run_metadata"]["tracks_requested"] == ["a"]
    assert payload["run_metadata"]["models_requested"] == [
        {"provider": "openai", "model": "gpt-4o"}
    ]
    assert payload["run_metadata"]["schema_artifact_path"] == "schema_context.json"
    assert payload["run_metadata"]["rag_manifest_path"] is None
    assert (
        payload["run_metadata"]["config_snapshot"]["run_defaults"]["output_dir"]
        == output_dir
    )
    assert schema_payload == {"tables": []}

    records = payload["records"]
    assert len(records) == 2
    assert records[0]["track"] == "track_a"
    assert records[0]["provider"] == "openai"
    assert records[0]["model"] == "gpt-4o"
    assert "generated" in records[0]
    assert "reference" in records[0]


def test_reporter_flush_omits_schema_artifact_when_schema_not_set(tmp_path):
    output_dir = str(tmp_path / "results")
    reporter = Reporter(config=_build_config(output_dir))

    reporter.record(
        PipelineRecord(
            question_id="q001",
            question="How many employees are there?",
            track="track_a",
            provider="openai",
            model="gpt-4o",
            prompt="prompt-1",
            raw_response="SELECT COUNT(*) FROM employees",
            normalized_sql="SELECT COUNT(*) FROM employees",
            generated=ExecutionFacts(
                success=True,
                error_type_raw=None,
                error_message=None,
                row_count=1,
                rows_sample=[[1]],
            ),
            reference=ExecutionFacts(
                success=True,
                error_type_raw=None,
                error_message=None,
                row_count=1,
                rows_sample=[[1]],
            ),
            rows_equal=True,
        )
    )

    reporter.flush(run_id="20260319-120001", output_dir=output_dir)

    run_dir = tmp_path / "results" / "20260319-120001"
    payload = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))

    assert payload["run_metadata"]["schema_artifact_path"] is None
    assert payload["run_metadata"]["rag_manifest_path"] is None
    assert not (run_dir / "schema_context.json").exists()
