from __future__ import annotations

import json
import sqlite3

import pytest

from text2sql_eval.dataset.loader import load_questions
from text2sql_eval.dataset.schema import parse_schema


def _write_questions(tmp_path, records):
    questions_path = tmp_path / "questions.json"
    questions_path.write_text(json.dumps(records), encoding="utf-8")
    return questions_path


def _write_db_file(tmp_path):
    db_path = tmp_path / "database.sqlite"
    db_path.write_bytes(b"")
    return db_path


def test_load_questions_returns_typed_eval_questions(tmp_path):
    questions_path = _write_questions(
        tmp_path,
        [
            {
                "question_id": "q001",
                "question": "How many employees?",
                "sql": "SELECT COUNT(*) FROM employees",
            },
            {
                "question_id": "q002",
                "question": "List department names",
                "sql": "SELECT name FROM departments",
            },
        ],
    )
    db_path = _write_db_file(tmp_path)

    questions = load_questions(questions_path=questions_path, db_path=db_path)

    assert len(questions) == 2
    assert questions[0].question_id == "q001"
    assert questions[0].reference_sql == "SELECT COUNT(*) FROM employees"
    assert questions[1].question == "List department names"
    assert all(question.db_path == db_path for question in questions)
    assert all(question.schema.tables == [] for question in questions)


def test_load_questions_applies_limit(tmp_path):
    questions_path = _write_questions(
        tmp_path,
        [
            {"question_id": "q001", "question": "Q1", "sql": "SELECT 1"},
            {"question_id": "q002", "question": "Q2", "sql": "SELECT 2"},
            {"question_id": "q003", "question": "Q3", "sql": "SELECT 3"},
        ],
    )
    db_path = _write_db_file(tmp_path)

    questions = load_questions(questions_path=questions_path, db_path=db_path, limit=2)

    assert [question.question_id for question in questions] == ["q001", "q002"]


def test_load_questions_raises_for_missing_files(tmp_path):
    missing_questions = tmp_path / "questions.json"
    existing_db = _write_db_file(tmp_path)

    with pytest.raises(FileNotFoundError, match="Questions file not found"):
        load_questions(questions_path=missing_questions, db_path=existing_db)

    existing_questions = _write_questions(
        tmp_path,
        [{"question_id": "q001", "question": "Q1", "sql": "SELECT 1"}],
    )
    missing_db = tmp_path / "missing.sqlite"

    with pytest.raises(FileNotFoundError, match="Database file not found"):
        load_questions(questions_path=existing_questions, db_path=missing_db)


def test_load_questions_raises_for_invalid_shapes(tmp_path):
    db_path = _write_db_file(tmp_path)
    not_a_list = tmp_path / "questions.json"
    not_a_list.write_text(json.dumps({"question_id": "q001"}), encoding="utf-8")

    with pytest.raises(ValueError, match="must contain a JSON list"):
        load_questions(questions_path=not_a_list, db_path=db_path)

    bad_item_path = _write_questions(tmp_path, ["not-an-object"])

    with pytest.raises(ValueError, match="must be an object"):
        load_questions(questions_path=bad_item_path, db_path=db_path)


def test_load_questions_raises_for_missing_required_keys(tmp_path):
    db_path = _write_db_file(tmp_path)
    questions_path = _write_questions(
        tmp_path, [{"question_id": "q001", "question": "Q1"}]
    )

    with pytest.raises(ValueError, match="Missing key 'sql'"):
        load_questions(questions_path=questions_path, db_path=db_path)


def test_load_questions_rejects_negative_limit(tmp_path):
    db_path = _write_db_file(tmp_path)
    questions_path = _write_questions(
        tmp_path,
        [{"question_id": "q001", "question": "Q1", "sql": "SELECT 1"}],
    )

    with pytest.raises(ValueError, match="limit must be >= 0"):
        load_questions(questions_path=questions_path, db_path=db_path, limit=-1)


def test_load_questions_uses_provided_schema_context_without_parsing(tmp_path):
    questions_path = _write_questions(
        tmp_path,
        [{"question_id": "q001", "question": "Q1", "sql": "SELECT 1"}],
    )
    db_path = _write_db_file(tmp_path)
    schema = parse_schema(db_path)

    questions = load_questions(
        questions_path=questions_path,
        db_path=db_path,
        schema_context=schema,
    )

    assert questions[0].schema is schema


def test_parse_schema_reads_tables_columns_and_foreign_keys(tmp_path):
    db_path = tmp_path / "database.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
        connection.execute(
            """
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                department_id INTEGER NOT NULL,
                name TEXT,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
            """
        )
        connection.commit()

    schema = parse_schema(db_path)

    assert [table.name for table in schema.tables] == ["departments", "employees"]
    employees = next(table for table in schema.tables if table.name == "employees")
    department_id = next(
        column for column in employees.columns if column.name == "department_id"
    )
    id_column = next(column for column in employees.columns if column.name == "id")

    assert id_column.is_primary_key is True
    assert department_id.is_foreign_key is True
    assert department_id.references == "departments.id"


def test_parse_schema_ignores_internal_sqlite_tables(tmp_path):
    db_path = tmp_path / "database.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "CREATE TABLE demo (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)"
        )
        connection.commit()

    schema = parse_schema(db_path)

    assert [table.name for table in schema.tables] == ["demo"]


def test_parse_schema_returns_empty_context_for_database_without_user_tables(tmp_path):
    db_path = tmp_path / "database.sqlite"
    with sqlite3.connect(db_path):
        pass

    schema = parse_schema(db_path)

    assert schema.tables == []


def test_parse_schema_groups_composite_foreign_key_references_by_column(tmp_path):
    db_path = tmp_path / "database.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """
            CREATE TABLE parent (
                tenant_id INTEGER NOT NULL,
                id INTEGER NOT NULL,
                PRIMARY KEY (tenant_id, id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE child (
                tenant_id INTEGER NOT NULL,
                parent_id INTEGER NOT NULL,
                FOREIGN KEY (tenant_id, parent_id) REFERENCES parent(tenant_id, id)
            )
            """
        )
        connection.commit()

    schema = parse_schema(db_path)

    child = next(table for table in schema.tables if table.name == "child")
    tenant_id = next(column for column in child.columns if column.name == "tenant_id")
    parent_id = next(column for column in child.columns if column.name == "parent_id")

    assert tenant_id.is_foreign_key is True
    assert parent_id.is_foreign_key is True
    assert tenant_id.references == "parent.tenant_id"
    assert parent_id.references == "parent.id"
