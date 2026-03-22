from __future__ import annotations

from pathlib import Path
from typing import Any, cast

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
from text2sql_eval.pipeline.runner import extract_sql
from text2sql_eval.pipeline.runner import run as run_pipeline
from text2sql_eval.results.schema import PipelineRecord


def test_extract_sql_strips_markdown_fences():
    raw = "```sql\nSELECT 1\n```"

    assert extract_sql(raw) == "SELECT 1"


def test_extract_sql_passthrough_plain_sql():
    assert extract_sql("SELECT 1") == "SELECT 1"


def test_extract_sql_handles_generic_code_fence():
    raw = "```\nSELECT id FROM users\n```"

    assert extract_sql(raw) == "SELECT id FROM users"


def test_run_collects_raw_execution_facts_without_evaluator_dependency(monkeypatch):
    captured: dict[str, Any] = {}

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
        experiment=ExperimentConfig(tracks=["a"], limit=1, output_dir="results"),
    )

    question = EvalQuestion(
        question_id="q001",
        question="How many rows?",
        reference_sql="SELECT COUNT(*) FROM employees",
        schema=SchemaContext(),
        db_path=Path("/tmp/fake.sqlite"),
    )

    class FakeProvider:
        def generate(self, prompt: str) -> LLMResponse:
            return LLMResponse(
                content="```sql\nSELECT COUNT(*) FROM employees\n```",
                input_tokens=10,
                output_tokens=5,
                latency_ms=20,
            )

    class FakeTrack:
        name = "track_a"

        def pre_fetch(self, question: str, vector_store=None) -> list[str]:
            return ["context-a"]

        def build_artifacts(
            self,
            question: str,
            schema_context: SchemaContext,
            extra_context=None,
        ) -> dict[str, str]:
            _ = question
            _ = schema_context
            _ = extra_context
            return {"retrieval_backend": "none"}

        def build_prompt(
            self, question: str, schema_context: SchemaContext, extra_context=None
        ) -> str:
            return f"Q: {question}; C: {extra_context}"

    class FakeReporter:
        def __init__(self, config: AppConfig):
            _ = config

        def record(self, record) -> None:
            captured["record"] = record

        def flush(self, run_id: str, output_dir: str) -> None:
            captured["run_id"] = run_id
            captured["output_dir"] = output_dir

    exec_results = iter(
        [
            ExecutionResult(True, [(42,)], None, None),
            ExecutionResult(True, [(42,)], None, None),
        ]
    )

    from text2sql_eval.pipeline import runner

    monkeypatch.setattr(runner, "load_questions", lambda *args, **kwargs: [question])
    monkeypatch.setattr(runner, "get_provider", lambda model_config: FakeProvider())
    monkeypatch.setattr(runner, "get_track", lambda name: FakeTrack())
    monkeypatch.setattr(runner, "Reporter", FakeReporter)
    monkeypatch.setattr(runner, "execute_sql", lambda sql, db_path: next(exec_results))

    run_pipeline(config)

    record = cast(PipelineRecord, captured["record"])
    assert record.question_id == "q001"
    assert record.track == "track_a"
    assert record.provider == "openai"
    assert record.model == "gpt-4o"
    assert record.extra_context == ["context-a"]
    assert record.track_artifacts == {"retrieval_backend": "none"}
    assert record.raw_response.startswith("```sql")
    assert record.normalized_sql == "SELECT COUNT(*) FROM employees"
    assert record.generated.success is True
    assert record.reference.success is True
    assert record.rows_equal is True
    assert record.generated_rows_hash
    assert record.reference_rows_hash == record.generated_rows_hash
