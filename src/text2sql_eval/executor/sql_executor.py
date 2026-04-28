from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ExecutionResult:
    success: bool
    rows: list[tuple] | None
    error_message: str | None
    error_type: str | None


def _cell_sort_key(value: Any) -> tuple:
    if value is None:
        return (1, "", "")
    if isinstance(value, int | float) and not isinstance(value, bool):
        return (0, "number", value)
    if isinstance(value, str):
        return (0, "str", value)
    if isinstance(value, bytes):
        return (0, "bytes", value)
    return (0, type(value).__name__, repr(value))


def _row_sort_key(row: tuple) -> tuple:
    return tuple(_cell_sort_key(value) for value in row)


def execute_sql(sql: str, db_path: Path) -> ExecutionResult:
    """
    Execute sql against the SQLite database at db_path.
    - Opens a read-only connection: sqlite3.connect("file:{db_path}?mode=ro", uri=True)
    - Returns rows as a sorted list of tuples for order-insensitive comparison.
    - Timeout: PRAGMA busy_timeout = 30000
    - Catches sqlite3.OperationalError and sqlite3.DatabaseError.
    - Never raises — always returns ExecutionResult.
    """
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as connection:
            connection.execute("PRAGMA busy_timeout = 30000")
            cursor = connection.execute(sql)
            fetched_rows = cursor.fetchall()
            normalized_rows = sorted(
                (tuple(row) for row in fetched_rows),
                key=_row_sort_key,
            )
            return ExecutionResult(
                success=True,
                rows=normalized_rows,
                error_message=None,
                error_type=None,
            )
    except (sqlite3.OperationalError, sqlite3.DatabaseError) as exc:
        return ExecutionResult(
            success=False,
            rows=None,
            error_message=str(exc),
            error_type="SYNTAX_ERROR",
        )
    except Exception as exc:  # pragma: no cover - safety net for runtime stability
        return ExecutionResult(
            success=False,
            rows=None,
            error_message=str(exc),
            error_type="SYNTAX_ERROR",
        )
