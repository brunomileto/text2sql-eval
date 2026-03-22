from __future__ import annotations

from text2sql_eval.pipeline.runner import extract_sql


def test_extract_sql_strips_markdown_fences():
    raw = "```sql\nSELECT 1\n```"

    assert extract_sql(raw) == "SELECT 1"


def test_extract_sql_passthrough_plain_sql():
    assert extract_sql("SELECT 1") == "SELECT 1"


def test_extract_sql_handles_generic_code_fence():
    raw = "```\nSELECT id FROM users\n```"

    assert extract_sql(raw) == "SELECT id FROM users"
