from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .schema import SchemaContext


@dataclass
class EvalQuestion:
    question_id: str
    question: str
    reference_sql: str
    schema: SchemaContext
    db_path: Path
