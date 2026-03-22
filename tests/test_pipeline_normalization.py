from __future__ import annotations

from text2sql_eval.executor.sql_executor import ExecutionResult
from text2sql_eval.pipeline.normalization import (
    extract_sql,
    normalize_rows,
    rows_hash,
    to_execution_facts,
)


def test_normalize_rows_converts_tuples_to_json_safe_lists():
    rows = [(1, "a"), (2, "b")]
    assert normalize_rows(rows) == [[1, "a"], [2, "b"]]


def test_rows_hash_is_deterministic_for_same_rows():
    rows = [(1, "a"), (2, "b")]
    first = rows_hash(rows)
    second = rows_hash(rows)

    assert first is not None
    assert first == second


def test_rows_hash_distinguishes_none_from_empty_rows():
    assert rows_hash(None) is None
    assert rows_hash([]) is not None


def test_to_execution_facts_applies_sample_cap_and_row_count():
    result = ExecutionResult(
        success=True,
        rows=[(1,), (2,), (3,)],
        error_message=None,
        error_type=None,
    )

    facts = to_execution_facts(result, sample_size=2)

    assert facts.success is True
    assert facts.row_count == 3
    assert facts.rows_sample == [[1], [2]]


def test_to_execution_facts_failure_keeps_errors_and_no_rows():
    result = ExecutionResult(
        success=False,
        rows=None,
        error_message="near FROM: syntax error",
        error_type="SYNTAX_ERROR",
    )

    facts = to_execution_facts(result)

    assert facts.success is False
    assert facts.error_type_raw == "SYNTAX_ERROR"
    assert facts.error_message == "near FROM: syntax error"
    assert facts.row_count is None
    assert facts.rows_sample == []


def test_extract_sql_cleanup_behavior():
    assert extract_sql("```sql\nSELECT 1\n```") == "SELECT 1"
    assert extract_sql("```\nSELECT 2\n```") == "SELECT 2"
    assert extract_sql("SELECT 3") == "SELECT 3"
