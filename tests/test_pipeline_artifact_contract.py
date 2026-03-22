from __future__ import annotations

import json
from pathlib import Path

from text2sql_eval.config import (
    AppConfig,
    DatasetConfig,
    ExperimentConfig,
    LLMConfig,
    LLMModelConfig,
)
from text2sql_eval.dataset.models import EvalQuestion
from text2sql_eval.dataset.schema import SchemaContext
from text2sql_eval.executor.sql_executor import ExecutionResult
from text2sql_eval.llm.base import LLMResponse
from text2sql_eval.pipeline.runner import run as run_pipeline


def test_pipeline_run_json_contains_analysis_ready_raw_facts(monkeypatch, tmp_path):
    config = AppConfig(
        llm=LLMConfig(
            models=[
                LLMModelConfig(
                    provider="openai",
                    model="gpt-4o",
                    temperature=0.0,
                    max_tokens=128,
                )
            ]
        ),
        dataset=DatasetConfig(questions="data/dev.json", db="data/database.sqlite"),
        experiment=ExperimentConfig(
            tracks=["a"],
            limit=2,
            output_dir=str(tmp_path / "results"),
        ),
    )

    questions = [
        EvalQuestion(
            question_id="q001",
            question="How many employees?",
            reference_sql="SELECT COUNT(*) FROM employees",
            schema=SchemaContext(),
            db_path=Path("/tmp/fake.sqlite"),
        ),
        EvalQuestion(
            question_id="q002",
            question="List all employees",
            reference_sql="SELECT name FROM employees",
            schema=SchemaContext(),
            db_path=Path("/tmp/fake.sqlite"),
        ),
    ]

    class FakeProvider:
        def __init__(self):
            self._calls = 0

        def generate(self, prompt: str) -> LLMResponse:
            _ = prompt
            self._calls += 1
            if self._calls == 1:
                return LLMResponse(
                    content="```sql\nSELECT COUNT(*) FROM employees\n```",
                    input_tokens=11,
                    output_tokens=4,
                    latency_ms=18,
                )
            return LLMResponse(
                content="```sql\nSELEC name FROM employees\n```",
                input_tokens=12,
                output_tokens=5,
                latency_ms=22,
            )

    class FakeTrack:
        name = "track_a"

        def pre_fetch(self, question: str, vector_store=None) -> list[str]:
            _ = vector_store
            return [f"context:{question}"]

        def build_prompt(
            self,
            question: str,
            schema_context: SchemaContext,
            extra_context=None,
        ) -> str:
            _ = schema_context
            return f"Question={question}; extra={extra_context}"

        def build_artifacts(
            self,
            question: str,
            schema_context: SchemaContext,
            extra_context=None,
        ) -> dict[str, str]:
            _ = schema_context
            return {
                "question_echo": question,
                "extra_count": str(len(extra_context or [])),
            }

    execution_results = iter(
        [
            ExecutionResult(True, [(42,)], None, None),
            ExecutionResult(True, [(42,)], None, None),
            ExecutionResult(False, None, "near SELECT: syntax error", "SYNTAX_ERROR"),
            ExecutionResult(True, [("Alice",), ("Bob",)], None, None),
        ]
    )

    from text2sql_eval.pipeline import runner

    monkeypatch.setattr(runner, "load_questions", lambda *args, **kwargs: questions)
    monkeypatch.setattr(runner, "get_provider", lambda model_config: FakeProvider())
    monkeypatch.setattr(runner, "get_track", lambda name: FakeTrack())
    monkeypatch.setattr(
        runner,
        "execute_sql",
        lambda sql, db_path: next(execution_results),
    )

    run_id = run_pipeline(config)
    run_json = tmp_path / "results" / run_id / "run.json"
    payload = json.loads(run_json.read_text(encoding="utf-8"))

    metadata = payload["run_metadata"]
    assert metadata["schema_version"] == "v1"
    assert metadata["run_id"] == run_id
    assert metadata["dataset_path"] == "data/dev.json"
    assert metadata["db_path"] == "data/database.sqlite"
    assert metadata["tracks_requested"] == ["a"]
    assert metadata["models_requested"] == [{"provider": "openai", "model": "gpt-4o"}]
    assert "config_snapshot" in metadata

    records = payload["records"]
    assert len(records) == 2

    success = records[0]
    assert success["question_id"] == "q001"
    assert success["track"] == "track_a"
    assert success["provider"] == "openai"
    assert success["model"] == "gpt-4o"
    assert success["extra_context"] == ["context:How many employees?"]
    assert success["track_artifacts"]["question_echo"] == "How many employees?"
    assert success["raw_response"].startswith("```sql")
    assert success["normalized_sql"] == "SELECT COUNT(*) FROM employees"
    assert success["generated"]["success"] is True
    assert success["generated"]["row_count"] == 1
    assert success["generated"]["rows_sample"] == [[42]]
    assert success["reference"]["success"] is True
    assert success["rows_equal"] is True
    assert success["generated_rows_hash"] == success["reference_rows_hash"]

    failure = records[1]
    assert failure["question_id"] == "q002"
    assert failure["normalized_sql"] == "SELEC name FROM employees"
    assert failure["generated"]["success"] is False
    assert failure["generated"]["error_type_raw"] == "SYNTAX_ERROR"
    assert failure["generated"]["error_message"] == "near SELECT: syntax error"
    assert failure["generated"]["row_count"] is None
    assert failure["generated"]["rows_sample"] == []
    assert failure["reference"]["success"] is True
    assert failure["rows_equal"] is None
    assert failure["generated_rows_hash"] is None
    assert failure["reference_rows_hash"] is not None
