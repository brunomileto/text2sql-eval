from __future__ import annotations

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
    """
    MVP: return an empty SchemaContext().
    Stage 4: introspect the .sqlite file using PRAGMA table_info
    to populate tables and columns.
    """
    _ = db_path
    return SchemaContext()
