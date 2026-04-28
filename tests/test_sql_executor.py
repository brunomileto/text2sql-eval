from __future__ import annotations

import sqlite3

from text2sql_eval.executor.sql_executor import execute_sql


def _build_test_db(tmp_path):
    db_path = tmp_path / "test.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE employees "
            "(id INTEGER PRIMARY KEY, name TEXT, department TEXT)"
        )
        connection.executemany(
            "INSERT INTO employees (id, name, department) VALUES (?, ?, ?)",
            [
                (2, "Bob", "sales"),
                (1, "Alice", "engineering"),
                (3, "Carol", "engineering"),
            ],
        )
        connection.commit()
    return db_path


def test_valid_select_returns_rows(tmp_path):
    db_path = _build_test_db(tmp_path)

    result = execute_sql("SELECT id, name FROM employees", db_path)

    assert result.success is True
    assert result.error_message is None
    assert result.error_type is None
    assert result.rows == [(1, "Alice"), (2, "Bob"), (3, "Carol")]


def test_invalid_sql_returns_syntax_error(tmp_path):
    db_path = _build_test_db(tmp_path)

    result = execute_sql("SELEC id FROM employees", db_path)

    assert result.success is False
    assert result.rows is None
    assert result.error_type == "SYNTAX_ERROR"
    assert result.error_message


def test_nonexistent_table_returns_error(tmp_path):
    db_path = _build_test_db(tmp_path)

    result = execute_sql("SELECT * FROM ghost_table", db_path)

    assert result.success is False
    assert result.rows is None
    assert result.error_type == "SYNTAX_ERROR"


def test_result_rows_are_sorted(tmp_path):
    db_path = _build_test_db(tmp_path)

    result = execute_sql("SELECT id FROM employees ORDER BY id DESC", db_path)

    assert result.success is True
    assert result.rows == [(1,), (2,), (3,)]


def test_result_rows_with_nulls_are_sorted(tmp_path):
    db_path = _build_test_db(tmp_path)

    with sqlite3.connect(db_path) as connection:
        connection.execute("ALTER TABLE employees ADD COLUMN score REAL")
        connection.execute("UPDATE employees SET score = 10.0 WHERE id = 1")
        connection.execute("UPDATE employees SET score = NULL WHERE id = 2")
        connection.execute("UPDATE employees SET score = 5.0 WHERE id = 3")
        connection.commit()

    result = execute_sql("SELECT score FROM employees", db_path)

    assert result.success is True
    assert result.error_message is None
    assert result.error_type is None
    assert result.rows == [(5.0,), (10.0,), (None,)]


def test_read_only_connection_blocks_writes(tmp_path):
    db_path = _build_test_db(tmp_path)

    result = execute_sql(
        "INSERT INTO employees (id, name, department) VALUES (4, 'Dave', 'sales')",
        db_path,
    )

    assert result.success is False
    assert result.rows is None
    assert result.error_type == "SYNTAX_ERROR"
    assert (
        "readonly" in result.error_message.lower()
        or "read-only" in result.error_message.lower()
    )
