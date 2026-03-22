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
from text2sql_eval.dataset.models import EvalQuestion
from text2sql_eval.dataset.schema import SchemaContext
from text2sql_eval.evaluator.execution_accuracy import EXScore
from text2sql_eval.llm.base import LLMResponse
from text2sql_eval.results.reporter import Reporter


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

    question = EvalQuestion(
        question_id="q001",
        question="How many employees are there?",
        reference_sql="SELECT COUNT(*) FROM employees",
        schema=SchemaContext(),
        db_path=tmp_path / "company.sqlite",
    )
    model_config = LLMModelConfig(
        provider="openai",
        model="gpt-4o",
        temperature=0.0,
        max_tokens=1024,
    )

    reporter.record(
        question=question,
        model_config=model_config,
        track="track_a",
        prompt="prompt-1",
        generated_sql="SELECT COUNT(*) FROM employees",
        llm_response=LLMResponse(
            content="SELECT COUNT(*) FROM employees",
            input_tokens=100,
            output_tokens=20,
            latency_ms=400,
        ),
        score=EXScore(ex=1, error_type="CORRECT"),
    )
    reporter.record(
        question=question,
        model_config=model_config,
        track="track_a",
        prompt="prompt-2",
        generated_sql="SELEC COUNT(*) FROM employees",
        llm_response=LLMResponse(
            content="SELEC COUNT(*) FROM employees",
            input_tokens=120,
            output_tokens=10,
            latency_ms=600,
        ),
        score=EXScore(ex=0, error_type="SYNTAX_ERROR"),
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
