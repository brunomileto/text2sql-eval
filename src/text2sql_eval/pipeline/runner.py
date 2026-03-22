from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import AppConfig
from ..dataset.loader import load_questions
from ..executor import ExecutionResult
from ..executor.sql_executor import execute_sql
from ..llm.registry import get_provider
from ..results.reporter import Reporter
from ..results.schema import ExecutionFacts, PipelineRecord
from ..tracks.registry import get_track


def extract_sql(raw: str) -> str:
    """Strip markdown code fences and surrounding whitespace."""
    text = raw.strip()
    if not text.startswith("```"):
        return text

    text = text[3:]
    if text.lower().startswith("sql"):
        text = text[3:]
    text = text.strip()
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _normalize_rows(rows: list[tuple[Any, ...]] | None) -> list[list[Any]]:
    if not rows:
        return []
    return [list(row) for row in rows]


def _rows_hash(rows: list[tuple[Any, ...]] | None) -> str | None:
    if rows is None:
        return None
    normalized = _normalize_rows(rows)
    payload = json.dumps(normalized, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _to_execution_facts(
    result: ExecutionResult, sample_size: int = 50
) -> ExecutionFacts:
    normalized_rows = _normalize_rows(result.rows)
    return ExecutionFacts(
        success=result.success,
        error_type_raw=result.error_type,
        error_message=result.error_message,
        row_count=len(normalized_rows) if result.success else None,
        rows_sample=normalized_rows[:sample_size] if result.success else [],
    )


def run(config: AppConfig) -> str:
    """Run experiment for all configured tracks and models and return run_id."""
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    reporter = Reporter(config)

    questions = load_questions(
        Path(config.dataset.questions),
        Path(config.dataset.db),
        config.experiment.limit,
    )

    tracks = [get_track(name) for name in config.experiment.tracks]
    providers = [
        (model_config, get_provider(model_config)) for model_config in config.llm.models
    ]

    for question in questions:
        for model_config, provider in providers:
            for track in tracks:
                pipeline_started = time.perf_counter()
                started_at = datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                )
                extra_context = track.pre_fetch(question.question, vector_store=None)
                prompt = track.build_prompt(
                    question.question, question.schema, extra_context
                )
                llm_response = provider.generate(prompt)
                sql = extract_sql(llm_response.content)
                generated_result = execute_sql(sql, question.db_path)
                reference_result = execute_sql(question.reference_sql, question.db_path)
                finished_at = datetime.now(timezone.utc).isoformat(
                    timespec="milliseconds"
                )

                rows_equal = None
                if generated_result.success and reference_result.success:
                    rows_equal = (generated_result.rows or []) == (
                        reference_result.rows or []
                    )

                reporter.record(
                    PipelineRecord(
                        question_id=question.question_id,
                        question=question.question,
                        track=track.name,
                        provider=model_config.provider,
                        model=model_config.model,
                        prompt=prompt,
                        extra_context=extra_context,
                        raw_response=llm_response.content,
                        normalized_sql=sql,
                        input_tokens=llm_response.input_tokens,
                        output_tokens=llm_response.output_tokens,
                        latency_ms=llm_response.latency_ms,
                        generated=_to_execution_facts(generated_result),
                        reference=_to_execution_facts(reference_result),
                        rows_equal=rows_equal,
                        generated_rows_hash=_rows_hash(generated_result.rows),
                        reference_rows_hash=_rows_hash(reference_result.rows),
                        pipeline_latency_ms=int(
                            (time.perf_counter() - pipeline_started) * 1000
                        ),
                        timestamps={
                            "started_at": started_at,
                            "finished_at": finished_at,
                        },
                    )
                )

    reporter.flush(run_id=run_id, output_dir=config.experiment.output_dir)
    return run_id
