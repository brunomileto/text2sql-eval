from __future__ import annotations

from dataclasses import dataclass

from ..executor.sql_executor import ExecutionResult


@dataclass
class EXScore:
    ex: int
    error_type: str


def score(
    generated: ExecutionResult,
    reference: ExecutionResult,
) -> EXScore:
    """
    Compare generated vs reference result sets.
    - If generated.success is False -> SYNTAX_ERROR, ex=0
    - If rows match -> CORRECT, ex=1
    - If rows don't match -> LOGIC_ERROR, ex=0
    """
    if not generated.success:
        return EXScore(ex=0, error_type="SYNTAX_ERROR")

    generated_rows = sorted(generated.rows or [])
    reference_rows = sorted(reference.rows or [])

    if generated_rows == reference_rows:
        return EXScore(ex=1, error_type="CORRECT")

    return EXScore(ex=0, error_type="LOGIC_ERROR")
