from __future__ import annotations

from text2sql_eval.evaluator.execution_accuracy import score
from text2sql_eval.executor.sql_executor import ExecutionResult


def _ok(rows):
    return ExecutionResult(success=True, rows=rows, error_message=None, error_type=None)


def _fail():
    return ExecutionResult(
        success=False,
        rows=None,
        error_message="bad sql",
        error_type="SYNTAX_ERROR",
    )


def test_identical_rows_returns_correct():
    generated = _ok([(1, "a"), (2, "b")])
    reference = _ok([(1, "a"), (2, "b")])

    result = score(generated, reference)

    assert result.ex == 1
    assert result.error_type == "CORRECT"


def test_different_rows_returns_logic_error():
    generated = _ok([(1, "a")])
    reference = _ok([(2, "b")])

    result = score(generated, reference)

    assert result.ex == 0
    assert result.error_type == "LOGIC_ERROR"


def test_failed_generated_sql_returns_syntax_error():
    generated = _fail()
    reference = _ok([(1,)])

    result = score(generated, reference)

    assert result.ex == 0
    assert result.error_type == "SYNTAX_ERROR"


def test_order_insensitive_match():
    generated = _ok([(1,), (2,), (3,)])
    reference = _ok([(3,), (2,), (1,)])

    result = score(generated, reference)

    assert result.ex == 1
    assert result.error_type == "CORRECT"


def test_empty_result_sets_match():
    generated = _ok([])
    reference = _ok([])

    result = score(generated, reference)

    assert result.ex == 1
    assert result.error_type == "CORRECT"
