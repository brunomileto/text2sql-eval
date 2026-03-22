from __future__ import annotations

import json

from text2sql_eval.config import (
    AppConfig,
    DatasetConfig,
    ExperimentConfig,
    LLMConfig,
    LLMModelConfig,
)
from text2sql_eval.results.reporter import Reporter
from text2sql_eval.results.schema import ExecutionFacts, PipelineRecord


def _build_config(output_dir: str) -> AppConfig:
    return AppConfig(
        llm=LLMConfig(
            models=[
                LLMModelConfig(
                    provider="openai",
                    model="gpt-4o",
                    temperature=0.0,
                    max_tokens=1024,
                )
            ]
        ),
        dataset=DatasetConfig(questions="data/dev.json", db="data/database.sqlite"),
        experiment=ExperimentConfig(tracks=["a"], limit=None, output_dir=output_dir),
    )


def test_reporter_flush_writes_run_artifact_json(tmp_path):
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
    assert run_json.exists()

    payload = json.loads(run_json.read_text(encoding="utf-8"))

    assert payload["run_metadata"]["schema_version"] == "v1"
    assert payload["run_metadata"]["run_id"] == "20260319-120000"
    assert payload["run_metadata"]["dataset_path"] == "data/dev.json"
    assert payload["run_metadata"]["db_path"] == "data/database.sqlite"
    assert payload["run_metadata"]["tracks_requested"] == ["a"]
    assert payload["run_metadata"]["models_requested"] == [
        {"provider": "openai", "model": "gpt-4o"}
    ]
    assert (
        payload["run_metadata"]["config_snapshot"]["experiment"]["output_dir"]
        == output_dir
    )

    records = payload["records"]
    assert len(records) == 2
    assert records[0]["track"] == "track_a"
    assert records[0]["provider"] == "openai"
    assert records[0]["model"] == "gpt-4o"
    assert "generated" in records[0]
    assert "reference" in records[0]
