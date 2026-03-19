from __future__ import annotations

from ..executor.sql_executor import ExecutionResult


def classify(
    sql: str,
    result: ExecutionResult,
    schema_context=None,
    restricted_tables: list[str] | None = None,
) -> str:
    """
    MVP returns: "SYNTAX_ERROR" | "LOGIC_ERROR" | "CORRECT"
    Stage 4 adds: "SCHEMA_HALLUCINATION" | "OPERATIONAL_VIOLATION"
    """
    _ = sql
    _ = schema_context
    _ = restricted_tables

    if not result.success:
        return "SYNTAX_ERROR"

    return "CORRECT"
