from __future__ import annotations

import json
import sqlite3
from textwrap import dedent

from text2sql_eval.app import run_experiment


def _write_fixture_files(tmp_path):
    db_path = tmp_path / "fixture.sqlite"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT)")
        connection.execute("INSERT INTO demo (id, name) VALUES (1, 'Alice')")
        connection.commit()

    questions_path = tmp_path / "dev.json"
    questions_path.write_text(
        json.dumps(
            [
                {
                    "question_id": "q001",
                    "question": "Return a constant one.",
                    "sql": "SELECT 1",
                }
            ]
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "results"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        dedent(
            f"""
            models:
              - provider: fake
                model: local-test
                temperature: 0.0
                max_tokens: 32

            inputs:
              questions_file: {questions_path}
              database_file: {db_path}

            run_defaults:
              tracks: [a]
              limit: null
              output_dir: {output_dir}

            rag:
              backend: chroma
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    return config_path, output_dir


def test_pipeline_uses_external_track_a_prompt_template(tmp_path, monkeypatch):
    config_path, output_dir = _write_fixture_files(tmp_path)

    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / "track_a.txt").write_text(
        dedent(
            """
            CUSTOM TEMPLATE ACTIVE
            Question payload: {question}
            SQL:
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    from text2sql_eval.prompts import loader

    monkeypatch.setattr(loader, "_PROMPTS_DIR", prompts_dir)
    loader.load_prompt_template.cache_clear()

    try:
        run_id = run_experiment(
            config_path=str(config_path), provider="fake", model="local-test"
        )
    finally:
        loader.load_prompt_template.cache_clear()

    run_json = output_dir / run_id / "run.json"
    payload = json.loads(run_json.read_text(encoding="utf-8"))
    record = payload["records"][0]

    assert "CUSTOM TEMPLATE ACTIVE" in record["prompt"]
    assert "Question payload: Return a constant one." in record["prompt"]


def test_pipeline_uses_external_track_b_prompt_template(tmp_path, monkeypatch):
    config_path, output_dir = _write_fixture_files(tmp_path)
    config_text = config_path.read_text(encoding="utf-8").replace(
        "tracks: [a]",
        "tracks: [b]",
    )
    config_path.write_text(config_text, encoding="utf-8")

    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / "track_b.txt").write_text(
        dedent(
            """
            CUSTOM TRACK B TEMPLATE
            Schema payload:
            {schema}
            Question payload: {question}
            SQL:
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    from text2sql_eval.prompts import loader

    monkeypatch.setattr(loader, "_PROMPTS_DIR", prompts_dir)
    loader.load_prompt_template.cache_clear()

    try:
        run_id = run_experiment(
            config_path=str(config_path), provider="fake", model="local-test"
        )
    finally:
        loader.load_prompt_template.cache_clear()

    run_json = output_dir / run_id / "run.json"
    payload = json.loads(run_json.read_text(encoding="utf-8"))
    record = payload["records"][0]
    schema_json = output_dir / run_id / "schema_context.json"

    assert "CUSTOM TRACK B TEMPLATE" in record["prompt"]
    assert "Question payload: Return a constant one." in record["prompt"]
    assert "## Table: demo" in record["prompt"]
    assert payload["run_metadata"]["schema_artifact_path"] == "schema_context.json"
    assert schema_json.exists()
