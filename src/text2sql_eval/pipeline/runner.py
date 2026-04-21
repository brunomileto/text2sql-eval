from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path

from ..config import AppConfig
from ..dataset.loader import load_questions
from ..dataset.schema import SchemaContext, parse_schema
from ..executor.sql_executor import execute_sql
from ..llm.registry import get_provider
from ..rag import build_retriever, rag_manifest_path
from ..rag.models import RetrievedChunk
from ..results.reporter import Reporter
from ..results.schema import PipelineRecord
from ..tracks.registry import get_track
from .normalization import extract_sql, rows_hash, to_execution_facts


def run(config: AppConfig) -> str:
    """Run experiment for all configured tracks and models and return run_id."""
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    reporter = Reporter(config)
    tracks = [get_track(name) for name in config.run_defaults.tracks]
    needs_schema_context = any(
        getattr(track, "uses_schema_context", False) for track in tracks
    )
    needs_retrieval_context = any(
        getattr(track, "uses_retrieval_context", False) for track in tracks
    )
    shared_schema = (
        parse_schema(Path(config.inputs.database_file))
        if needs_schema_context
        else SchemaContext()
    )
    retriever = build_retriever(config) if needs_retrieval_context else None

    questions = load_questions(
        Path(config.inputs.questions_file),
        Path(config.inputs.database_file),
        config.run_defaults.limit,
        schema_context=shared_schema,
    )
    if needs_schema_context:
        reporter.set_schema_context(shared_schema)
    if needs_retrieval_context:
        reporter.set_rag_manifest_path(rag_manifest_path(config))
    providers = [
        (model_config, get_provider(model_config)) for model_config in config.models
    ]
    retrieval_cache: dict[str, list[RetrievedChunk]] = {}

    for question in questions:
        retrieved_chunks = (
            retrieval_cache.setdefault(
                question.question,
                retriever.retrieve(question.question),
            )
            if retriever is not None
            else []
        )
        for model_config, provider in providers:
            for track in tracks:
                pipeline_started = time.perf_counter()
                started_at = datetime.now(UTC).isoformat(timespec="milliseconds")
                extra_context = track.pre_fetch(question.question, retrieved_chunks)
                prompt = track.build_prompt(
                    question.question, question.schema, extra_context
                )
                track_artifacts = track.build_artifacts(
                    question.question,
                    question.schema,
                    extra_context,
                )
                if hasattr(track, "build_retrieval_artifacts"):
                    track_artifacts |= track.build_retrieval_artifacts(
                        retrieved_chunks=retrieved_chunks
                    )
                llm_response = provider.generate(prompt)
                sql = extract_sql(llm_response.content)
                generated_result = execute_sql(sql, question.db_path)
                reference_result = execute_sql(question.reference_sql, question.db_path)
                finished_at = datetime.now(UTC).isoformat(timespec="milliseconds")

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
                        track_artifacts=track_artifacts,
                        raw_response=llm_response.content,
                        normalized_sql=sql,
                        reference_sql=question.reference_sql,
                        input_tokens=llm_response.input_tokens,
                        output_tokens=llm_response.output_tokens,
                        latency_ms=llm_response.latency_ms,
                        generated=to_execution_facts(generated_result),
                        reference=to_execution_facts(reference_result),
                        rows_equal=rows_equal,
                        generated_rows_hash=rows_hash(generated_result.rows),
                        reference_rows_hash=rows_hash(reference_result.rows),
                        pipeline_latency_ms=int(
                            (time.perf_counter() - pipeline_started) * 1000
                        ),
                        timestamps={
                            "started_at": started_at,
                            "finished_at": finished_at,
                        },
                    )
                )

    reporter.flush(run_id=run_id, output_dir=config.run_defaults.output_dir)
    return run_id
