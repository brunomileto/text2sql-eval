from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..config import AppConfig
from ..dataset.loader import load_questions
from ..evaluator import execution_accuracy as evaluator
from ..executor.sql_executor import execute_sql
from ..llm.registry import get_provider
from ..results.reporter import Reporter
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
                extra_context = track.pre_fetch(question.question, vector_store=None)
                prompt = track.build_prompt(
                    question.question, question.schema, extra_context
                )
                llm_response = provider.generate(prompt)
                sql = extract_sql(llm_response.content)
                generated_result = execute_sql(sql, question.db_path)
                reference_result = execute_sql(question.reference_sql, question.db_path)
                score = evaluator.score(generated_result, reference_result)
                reporter.record(
                    question=question,
                    model_config=model_config,
                    track=track.name,
                    prompt=prompt,
                    generated_sql=sql,
                    llm_response=llm_response,
                    score=score,
                )

    reporter.flush(run_id=run_id, output_dir=config.experiment.output_dir)
    return run_id
