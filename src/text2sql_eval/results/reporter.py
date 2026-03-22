from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from ..config import AppConfig, LLMModelConfig
from ..dataset.models import EvalQuestion
from ..evaluator.execution_accuracy import EXScore
from ..llm.base import LLMResponse


class Reporter:
    def __init__(self, config: AppConfig):
        self._config = config
        self._records: list[dict[str, Any]] = []

    def record(
        self,
        question: EvalQuestion,
        model_config: LLMModelConfig,
        track: str,
        prompt: str,
        generated_sql: str,
        llm_response: LLMResponse,
        score: EXScore,
    ) -> None:
        """Append one result record to the in-memory buffer."""
        self._records.append(
            {
                "question_id": question.question_id,
                "db_id": question.db_path.stem,
                "question": question.question,
                "track": track,
                "model": model_config.model,
                "provider": model_config.provider,
                "prompt": prompt,
                "generated_sql": generated_sql,
                "reference_sql": question.reference_sql,
                "ex": score.ex,
                "error_type": score.error_type,
                "latency_ms": llm_response.latency_ms,
                "input_tokens": llm_response.input_tokens,
                "output_tokens": llm_response.output_tokens,
            }
        )

    def flush(self, run_id: str, output_dir: str) -> None:
        run_dir = Path(output_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        by_track: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_group: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

        for record in self._records:
            by_track[record["track"]].append(record)
            group_key = (record["track"], record["model"], record["provider"])
            by_group[group_key].append(record)

        for track, records in by_track.items():
            (run_dir / f"{track}.json").write_text(
                json.dumps(records, indent=2),
                encoding="utf-8",
            )

        summary_path = run_dir / "summary.csv"
        with summary_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "run_id",
                    "track",
                    "model",
                    "provider",
                    "total_questions",
                    "ex_count",
                    "ex_pct",
                    "syntax_errors",
                    "logic_errors",
                    "correct",
                    "avg_latency_ms",
                    "avg_input_tokens",
                    "avg_output_tokens",
                ]
            )

            for (track, model, provider), records in sorted(by_group.items()):
                total = len(records)
                ex_count = sum(int(record["ex"]) for record in records)
                syntax_errors = sum(
                    1 for record in records if record["error_type"] == "SYNTAX_ERROR"
                )
                logic_errors = sum(
                    1 for record in records if record["error_type"] == "LOGIC_ERROR"
                )
                correct = sum(
                    1 for record in records if record["error_type"] == "CORRECT"
                )
                avg_latency_ms = sum(record["latency_ms"] for record in records) / total
                avg_input_tokens = (
                    sum(record["input_tokens"] for record in records) / total
                )
                avg_output_tokens = (
                    sum(record["output_tokens"] for record in records) / total
                )

                writer.writerow(
                    [
                        run_id,
                        track,
                        model,
                        provider,
                        total,
                        ex_count,
                        f"{(ex_count / total) * 100:.1f}",
                        syntax_errors,
                        logic_errors,
                        correct,
                        f"{avg_latency_ms:.2f}",
                        f"{avg_input_tokens:.2f}",
                        f"{avg_output_tokens:.2f}",
                    ]
                )

        config_snapshot_path = run_dir / "config_snapshot.yaml"
        config_snapshot_path.write_text(
            yaml.safe_dump(asdict(self._config), sort_keys=False),
            encoding="utf-8",
        )
