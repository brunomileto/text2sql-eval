from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

import yaml

from ..config import AppConfig
from .schema import PipelineRecord


class Reporter:
    def __init__(self, config: AppConfig):
        self._config = config
        self._records: list[PipelineRecord] = []

    def record(self, record: PipelineRecord) -> None:
        """Append one result record to the in-memory buffer."""
        self._records.append(record)

    @staticmethod
    def _legacy_outcome(record: PipelineRecord) -> tuple[int, str]:
        if not record.generated.success:
            return 0, "SYNTAX_ERROR"
        if record.rows_equal:
            return 1, "CORRECT"
        return 0, "LOGIC_ERROR"

    @staticmethod
    def _average(values: Iterable[int]) -> float:
        items = list(values)
        if not items:
            return 0.0
        return sum(items) / len(items)

    def flush(self, run_id: str, output_dir: str) -> None:
        run_dir = Path(output_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        by_track: dict[str, list[PipelineRecord]] = defaultdict(list)
        by_group: dict[tuple[str, str, str], list[PipelineRecord]] = defaultdict(list)

        for record in self._records:
            by_track[record.track].append(record)
            group_key = (record.track, record.model, record.provider)
            by_group[group_key].append(record)

        for track, records in by_track.items():
            payload: list[dict[str, Any]] = []
            for record in records:
                ex, error_type = self._legacy_outcome(record)
                row = asdict(record)
                row["ex"] = ex
                row["error_type"] = error_type
                payload.append(row)

            (run_dir / f"{track}.json").write_text(
                json.dumps(payload, indent=2),
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
                outcomes = [self._legacy_outcome(record) for record in records]
                ex_count = sum(ex for ex, _ in outcomes)
                syntax_errors = sum(1 for _, err in outcomes if err == "SYNTAX_ERROR")
                logic_errors = sum(1 for _, err in outcomes if err == "LOGIC_ERROR")
                correct = sum(1 for _, err in outcomes if err == "CORRECT")
                avg_latency_ms = self._average(record.latency_ms for record in records)
                avg_input_tokens = self._average(
                    record.input_tokens for record in records
                )
                avg_output_tokens = self._average(
                    record.output_tokens for record in records
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
