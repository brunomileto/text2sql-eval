from __future__ import annotations

import json
import sqlite3
from textwrap import dedent

from typer.testing import CliRunner

from text2sql_eval.app import run_experiment
from text2sql_eval.cli import app as cli_app


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
            llm:
              models:
                - provider: fake
                  model: local-test
                  temperature: 0.0
                  max_tokens: 32

            dataset:
              questions: {questions_path}
              db: {db_path}

            experiment:
              tracks: [a]
              limit: null
              output_dir: {output_dir}
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    return config_path, output_dir


def test_api_runs_end_to_end_with_local_fake_provider(tmp_path):
    config_path, output_dir = _write_fixture_files(tmp_path)

    run_id = run_experiment(config_path=str(config_path))

    run_json = output_dir / run_id / "run.json"
    assert run_json.exists()

    payload = json.loads(run_json.read_text(encoding="utf-8"))
    assert payload["run_metadata"]["schema_version"] == "v1"
    assert payload["run_metadata"]["models_requested"] == [
        {"provider": "fake", "model": "local-test"}
    ]
    assert len(payload["records"]) == 1

    record = payload["records"][0]
    assert record["provider"] == "fake"
    assert record["normalized_sql"] == "SELECT 1"
    assert record["generated"]["success"] is True
    assert record["reference"]["success"] is True
    assert record["rows_equal"] is True


def test_cli_runs_end_to_end_with_same_local_fixture(tmp_path):
    config_path, output_dir = _write_fixture_files(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        cli_app,
        ["run-experiment", "--config-path", str(config_path)],
    )

    assert result.exit_code == 0
    run_id_line = next(
        line
        for line in result.stdout.splitlines()
        if line.startswith("[text2sql-eval] Run ID:")
    )
    run_id = run_id_line.split(":", 1)[1].strip()

    run_json = output_dir / run_id / "run.json"
    assert run_json.exists()
