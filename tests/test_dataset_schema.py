from __future__ import annotations

from text2sql_eval.dataset.schema import Column, SchemaContext, Table, parse_schema


def test_parse_schema_returns_empty_context_for_mvp(tmp_path):
    db_path = tmp_path / "database.sqlite"
    db_path.write_bytes(b"")

    schema = parse_schema(db_path)

    assert schema.tables == []


def test_schema_name_helpers_return_table_and_qualified_column_names():
    schema = SchemaContext(
        tables=[
            Table(
                name="employees",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="name", data_type="TEXT"),
                ],
            ),
            Table(
                name="departments",
                columns=[Column(name="id", data_type="INTEGER")],
            ),
        ]
    )

    assert schema.table_names() == ["employees", "departments"]
    assert schema.column_names() == ["employees.id", "employees.name", "departments.id"]


def test_schema_to_markdown_includes_core_table_and_column_details():
    schema = SchemaContext(
        tables=[
            Table(
                name="employees",
                description="employee records",
                columns=[
                    Column(
                        name="id",
                        data_type="INTEGER",
                        is_primary_key=True,
                        description="surrogate key",
                    ),
                    Column(
                        name="department_id",
                        data_type="INTEGER",
                        is_foreign_key=True,
                        references="departments.id",
                    ),
                ],
            )
        ]
    )

    markdown = schema.to_markdown()

    assert "## Table: employees" in markdown
    assert "employee records" in markdown
    assert "| id | INTEGER | yes | no |  | surrogate key |" in markdown
    assert "| department_id | INTEGER | no | yes | departments.id |  |" in markdown


def test_schema_to_markdown_returns_empty_string_for_empty_schema():
    assert SchemaContext().to_markdown() == ""
