from __future__ import annotations

from text2sql_eval.evaluator.error_classifier import classify
from text2sql_eval.executor.sql_executor import ExecutionResult


def test_classify_returns_syntax_error_on_failed_execution():
    result = ExecutionResult(
        success=False,
        rows=None,
        error_message="near FROM: syntax error",
        error_type="SYNTAX_ERROR",
    )

    assert classify("SELEC * FROM t", result) == "SYNTAX_ERROR"


def test_classify_returns_correct_on_successful_execution():
    result = ExecutionResult(
        success=True,
        rows=[(1,)],
        error_message=None,
        error_type=None,
    )

    assert classify("SELECT 1", result) == "CORRECT"
