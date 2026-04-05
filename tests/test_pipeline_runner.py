from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from text2sql_eval.config import (
    AppConfig,
    InputsConfig,
    LLMModelConfig,
    RunDefaultsConfig,
)
from text2sql_eval.dataset.models import EvalQuestion
from text2sql_eval.dataset.schema import SchemaContext
from text2sql_eval.executor.sql_executor import ExecutionResult
from text2sql_eval.llm.base import LLMResponse
from text2sql_eval.pipeline.runner import extract_sql
from text2sql_eval.pipeline.runner import run as run_pipeline
from text2sql_eval.rag.models import RetrievedChunk
from text2sql_eval.results.schema import PipelineRecord


def test_extract_sql_strips_markdown_fences():
    raw = "```sql\nSELECT 1\n```"

    assert extract_sql(raw) == "SELECT 1"


def test_extract_sql_passthrough_plain_sql():
    assert extract_sql("SELECT 1") == "SELECT 1"


def test_extract_sql_handles_generic_code_fence():
    raw = "```\nSELECT id FROM users\n```"

    assert extract_sql(raw) == "SELECT id FROM users"


def test_run_collects_raw_execution_facts_in_record_payload(monkeypatch):
    captured: dict[str, Any] = {}

    config = AppConfig(
        models=[
            LLMModelConfig(
                provider="openai",
                model="gpt-4o",
                temperature=0.0,
                max_tokens=128,
            )
        ],
        inputs=InputsConfig(
            questions_file="data/dev.json",
            database_file="data/database.sqlite",
        ),
        run_defaults=RunDefaultsConfig(tracks=["a"], limit=1, output_dir="results"),
        rag={},
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
        uses_schema_context = False

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

        def set_schema_context(self, schema_context: SchemaContext) -> None:
            captured["schema_context"] = schema_context

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


def test_run_reuses_retrieval_once_per_question_across_models(monkeypatch):
    captured: dict[str, Any] = {"retrieval_calls": 0, "records": []}

    config = AppConfig(
        models=[
            LLMModelConfig(
                provider="openai",
                model="gpt-4o",
                temperature=0.0,
                max_tokens=128,
            ),
            LLMModelConfig(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                temperature=0.0,
                max_tokens=128,
            ),
        ],
        inputs=InputsConfig(
            questions_file="data/dev.json",
            database_file="data/database.sqlite",
        ),
        run_defaults=RunDefaultsConfig(tracks=["c"], limit=1, output_dir="results"),
        rag={
            "backend": "chroma",
            "top_k": 2,
            "embedding_model": "text-embedding-3-small",
            "index_path": "data/rag_index",
        },
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
        name = "track_c"
        uses_schema_context = True
        uses_retrieval_context = True

        def pre_fetch(self, question: str, retrieved_chunks=None) -> list[str]:
            return [chunk.text for chunk in (retrieved_chunks or [])]

        def build_artifacts(
            self,
            question: str,
            schema_context: SchemaContext,
            extra_context=None,
        ) -> dict[str, str]:
            _ = question
            _ = schema_context
            return {"extra_count": str(len(extra_context or []))}

        def build_retrieval_artifacts(self, retrieved_chunks=None) -> dict[str, Any]:
            return {
                "retrieved_chunks": [
                    {"text": chunk.text, "source_path": chunk.source_path}
                    for chunk in (retrieved_chunks or [])
                ]
            }

        def build_prompt(
            self, question: str, schema_context: SchemaContext, extra_context=None
        ) -> str:
            _ = schema_context
            return f"Q: {question}; C: {extra_context}"

    class FakeReporter:
        def __init__(self, config: AppConfig):
            _ = config

        def set_schema_context(self, schema_context: SchemaContext) -> None:
            captured["schema_context"] = schema_context

        def set_rag_manifest_path(self, rag_manifest_path: str) -> None:
            captured["rag_manifest_path"] = rag_manifest_path

        def record(self, record) -> None:
            captured["records"].append(record)

        def flush(self, run_id: str, output_dir: str) -> None:
            captured["run_id"] = run_id
            captured["output_dir"] = output_dir

    class FakeRetriever:
        def retrieve(self, question_text: str) -> list[RetrievedChunk]:
            captured["retrieval_calls"] += 1
            return [
                RetrievedChunk(
                    chunk_id="chunk-1",
                    source_path="docs/rag/a.md",
                    text=f"context for {question_text}",
                    score=0.1,
                    chunk_index=0,
                )
            ]

    exec_results = iter(
        [
            ExecutionResult(True, [(42,)], None, None),
            ExecutionResult(True, [(42,)], None, None),
            ExecutionResult(True, [(42,)], None, None),
            ExecutionResult(True, [(42,)], None, None),
        ]
    )

    from text2sql_eval.pipeline import runner

    monkeypatch.setattr(runner, "parse_schema", lambda path: SchemaContext())
    monkeypatch.setattr(runner, "load_questions", lambda *args, **kwargs: [question])
    monkeypatch.setattr(runner, "get_provider", lambda model_config: FakeProvider())
    monkeypatch.setattr(runner, "get_track", lambda name: FakeTrack())
    monkeypatch.setattr(runner, "build_retriever", lambda config: FakeRetriever())
    monkeypatch.setattr(
        runner,
        "rag_manifest_path",
        lambda config: "data/rag_index/manifest.json",
    )
    monkeypatch.setattr(runner, "Reporter", FakeReporter)
    monkeypatch.setattr(runner, "execute_sql", lambda sql, db_path: next(exec_results))

    run_pipeline(config)

    assert captured["retrieval_calls"] == 1
    assert captured["rag_manifest_path"] == "data/rag_index/manifest.json"
    assert len(captured["records"]) == 2
    assert (
        captured["records"][0]
        .track_artifacts["retrieved_chunks"][0]["text"]
        .startswith(
            "context for How many rows?",
        )
    )
