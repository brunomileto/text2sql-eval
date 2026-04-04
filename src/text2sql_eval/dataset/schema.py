from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Column:
    name: str
    data_type: str
    description: str = ""
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: str | None = None


@dataclass
class Table:
    name: str
    description: str = ""
    columns: list[Column] = field(default_factory=list)


@dataclass
class SchemaContext:
    tables: list[Table] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render schema as markdown for prompt injection (Track B+)."""
        if not self.tables:
            return ""

        sections: list[str] = []
        for table in self.tables:
            sections.append(f"## Table: {table.name}")
            if table.description:
                sections.append(table.description)
            sections.append("| Column | Type | PK | FK | References | Description |")
            sections.append("|---|---|---|---|---|---|")

            for column in table.columns:
                pk = "yes" if column.is_primary_key else "no"
                fk = "yes" if column.is_foreign_key else "no"
                references = column.references or ""
                sections.append(
                    f"| {column.name} | {column.data_type} "
                    f"| {pk} | {fk} "
                    f"| {references} "
                    f"| {column.description} |"
                )

            sections.append("")

        return "\n".join(sections).strip()

    def table_names(self) -> list[str]:
        """Return all table names — used by error classifier."""
        return [table.name for table in self.tables]

    def column_names(self) -> list[str]:
        """Return all 'table.column' strings — used by error classifier."""
        return [
            f"{table.name}.{column.name}"
            for table in self.tables
            for column in table.columns
        ]


def parse_schema(db_path: Path) -> SchemaContext:
    """Introspect the SQLite database and build schema metadata."""
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row

        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        tables: list[Table] = []
        for table_row in table_rows:
            table_name = str(table_row["name"])
            foreign_keys = connection.execute(
                f"PRAGMA foreign_key_list('{table_name}')"
            ).fetchall()
            references_by_column: dict[str, list[str]] = defaultdict(list)
            for fk_row in foreign_keys:
                from_column = str(fk_row["from"])
                target = f"{fk_row['table']}.{fk_row['to']}"
                references_by_column[from_column].append(target)

            columns: list[Column] = []
            for column_row in connection.execute(
                f"PRAGMA table_info('{table_name}')"
            ).fetchall():
                column_name = str(column_row["name"])
                references = references_by_column.get(column_name, [])
                columns.append(
                    Column(
                        name=column_name,
                        data_type=str(column_row["type"]),
                        is_primary_key=bool(column_row["pk"]),
                        is_foreign_key=bool(references),
                        references=", ".join(references) or None,
                    )
                )

            tables.append(Table(name=table_name, columns=columns))

    return SchemaContext(tables=tables)
