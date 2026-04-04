from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import EvalQuestion
from .schema import SchemaContext, parse_schema


def _require(record: dict[str, Any], key: str, index: int) -> Any:
    if key not in record:
        raise ValueError(f"Missing key '{key}' in questions record at index {index}")
    return record[key]


def load_questions(
    questions_path: Path,
    db_path: Path,
    limit: int | None = None,
    schema_context: SchemaContext | None = None,
) -> list[EvalQuestion]:
    """
    Read the questions JSON and return EvalQuestion objects.

    Expected JSON format:
    [
      {
        "question_id": "q001",
        "question": "How many employees are in each department?",
        "sql": "SELECT department, COUNT(*) FROM employees GROUP BY department"
      }
    ]
    """
    if not questions_path.exists():
        raise FileNotFoundError(f"Questions file not found: {questions_path}")
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    if limit is not None and limit < 0:
        raise ValueError("limit must be >= 0")

    schema = schema_context if schema_context is not None else parse_schema(db_path)
    records = json.loads(questions_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Questions file must contain a JSON list")

    if limit is not None:
        records = records[:limit]

    questions: list[EvalQuestion] = []
    for index, item in enumerate(records):
        if not isinstance(item, dict):
            raise ValueError(f"Question record at index {index} must be an object")

        questions.append(
            EvalQuestion(
                question_id=str(_require(item, "question_id", index)),
                question=str(_require(item, "question", index)),
                reference_sql=str(_require(item, "sql", index)),
                schema=schema,
                db_path=db_path,
            )
        )

    return questions
