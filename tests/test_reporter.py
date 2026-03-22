from __future__ import annotations

import csv
import json

import yaml

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


def test_reporter_flush_writes_track_summary_and_config_snapshot(tmp_path):
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
    assert (run_dir / "track_a.json").exists()
    assert (run_dir / "summary.csv").exists()
    assert (run_dir / "config_snapshot.yaml").exists()

    track_records = json.loads((run_dir / "track_a.json").read_text(encoding="utf-8"))
    assert len(track_records) == 2
    assert track_records[0]["track"] == "track_a"
    assert track_records[0]["provider"] == "openai"
    assert track_records[0]["model"] == "gpt-4o"
    assert "generated" in track_records[0]
    assert "reference" in track_records[0]

    with (run_dir / "summary.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    row = rows[0]
    assert row["run_id"] == "20260319-120000"
    assert row["track"] == "track_a"
    assert row["model"] == "gpt-4o"
    assert row["provider"] == "openai"
    assert row["total_questions"] == "2"
    assert row["ex_count"] == "1"
    assert row["ex_pct"] == "50.0"
    assert row["syntax_errors"] == "1"
    assert row["logic_errors"] == "0"
    assert row["correct"] == "1"

    snapshot = yaml.safe_load(
        (run_dir / "config_snapshot.yaml").read_text(encoding="utf-8")
    )
    assert snapshot["experiment"]["output_dir"] == output_dir
    assert snapshot["llm"]["models"][0]["provider"] == "openai"
