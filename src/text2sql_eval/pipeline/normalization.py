from __future__ import annotations

import hashlib
import json
from typing import Any

from ..executor import ExecutionResult
from ..results.schema import ExecutionFacts


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


def normalize_rows(rows: list[tuple[Any, ...]] | None) -> list[list[Any]]:
    if not rows:
        return []
    return [list(row) for row in rows]


def rows_hash(rows: list[tuple[Any, ...]] | None) -> str | None:
    if rows is None:
        return None
    normalized = normalize_rows(rows)
    payload = json.dumps(normalized, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def to_execution_facts(
    result: ExecutionResult,
    sample_size: int = 50,
) -> ExecutionFacts:
    normalized_rows = normalize_rows(result.rows)
    if not result.success:
        return ExecutionFacts(
            success=False,
            error_type_raw=result.error_type,
            error_message=result.error_message,
            row_count=None,
            rows_sample=[],
        )

    return ExecutionFacts(
        success=True,
        error_type_raw=result.error_type,
        error_message=result.error_message,
        row_count=len(normalized_rows),
        rows_sample=normalized_rows[:sample_size],
    )
