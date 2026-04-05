from __future__ import annotations

import json
import sqlite3
from textwrap import dedent

from typer.testing import CliRunner

from text2sql_eval.app import run_experiment
from text2sql_eval.cli import app as cli_app
from text2sql_eval.rag.models import RetrievedChunk


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


def test_api_runs_end_to_end_with_local_fake_provider(tmp_path):
    config_path, output_dir = _write_fixture_files(tmp_path)

    run_id = run_experiment(config_path=str(config_path))

    run_json = output_dir / run_id / "run.json"
    schema_json = output_dir / run_id / "schema_context.json"
    assert run_json.exists()
    assert not schema_json.exists()

    payload = json.loads(run_json.read_text(encoding="utf-8"))
    assert payload["run_metadata"]["schema_version"] == "v1"
    assert payload["run_metadata"]["schema_artifact_path"] is None
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
    assert not (output_dir / run_id / "schema_context.json").exists()


def test_api_runs_mixed_track_a_and_b_with_one_schema_artifact(tmp_path):
    config_path, output_dir = _write_fixture_files(tmp_path)
    config_text = config_path.read_text(encoding="utf-8").replace(
        "tracks: [a]",
        "tracks: [a, b]",
    )
    config_path.write_text(config_text, encoding="utf-8")

    run_id = run_experiment(config_path=str(config_path))

    run_dir = output_dir / run_id
    payload = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    schema_json = run_dir / "schema_context.json"

    assert payload["run_metadata"]["schema_artifact_path"] == "schema_context.json"
    assert schema_json.exists()
    assert len(payload["records"]) == 2

    record_a = next(
        record for record in payload["records"] if record["track"] == "track_a"
    )
    record_b = next(
        record for record in payload["records"] if record["track"] == "track_b"
    )

    assert "Schema:" not in record_a["prompt"]
    assert "Question: Return a constant one." in record_a["prompt"]
    assert "Schema:" in record_b["prompt"]
    assert "## Table: demo" in record_b["prompt"]


def test_api_runs_track_c_with_schema_and_retrieval_artifacts(tmp_path, monkeypatch):
    config_path, output_dir = _write_fixture_files(tmp_path)
    config_text = config_path.read_text(encoding="utf-8").replace(
        "tracks: [a]",
        "tracks: [c]",
    )
    config_text = config_text.replace(
        "rag:\n  backend: chroma\n",
        dedent(
            """
            rag:
              backend: chroma
              top_k: 5
              embedding_model: text-embedding-3-small
              index_path: data/rag_index/
            """
        ).strip()
        + "\n",
    )
    config_path.write_text(config_text, encoding="utf-8")

    class FakeRetriever:
        def retrieve(self, question_text: str) -> list[RetrievedChunk]:
            return [
                RetrievedChunk(
                    chunk_id="chunk-1",
                    source_path="docs/rag/demo.md",
                    text=f"retrieved context for {question_text}",
                    score=0.1,
                    chunk_index=0,
                )
            ]

    from text2sql_eval.pipeline import runner

    monkeypatch.setattr(runner, "build_retriever", lambda config: FakeRetriever())
    monkeypatch.setattr(
        runner,
        "rag_manifest_path",
        lambda config: "data/rag_index/manifest.json",
    )

    run_id = run_experiment(config_path=str(config_path))

    run_json = output_dir / run_id / "run.json"
    schema_json = output_dir / run_id / "schema_context.json"
    payload = json.loads(run_json.read_text(encoding="utf-8"))
    record = payload["records"][0]

    assert schema_json.exists()
    assert payload["run_metadata"]["schema_artifact_path"] == "schema_context.json"
    assert (
        payload["run_metadata"]["rag_manifest_path"] == "data/rag_index/manifest.json"
    )
    assert record["track"] == "track_c"
    assert "Schema:" in record["prompt"]
    assert "Retrieved Context:" in record["prompt"]
    assert "## Table: demo" in record["prompt"]
    assert "retrieved context for Return a constant one." in record["prompt"]
    assert (
        record["track_artifacts"]["retrieved_chunks"][0]["text"]
        == "retrieved context for Return a constant one."
    )


def test_api_runs_mixed_track_b_and_c_with_one_schema_and_shared_retrieval(
    tmp_path,
    monkeypatch,
):
    config_path, output_dir = _write_fixture_files(tmp_path)
    config_text = config_path.read_text(encoding="utf-8").replace(
        "tracks: [a]",
        "tracks: [b, c]",
    )
    config_text = config_text.replace(
        "rag:\n  backend: chroma\n",
        dedent(
            """
            rag:
              backend: chroma
              top_k: 5
              embedding_model: text-embedding-3-small
              index_path: data/rag_index/
            """
        ).strip()
        + "\n",
    )
    config_path.write_text(config_text, encoding="utf-8")

    calls = {"count": 0}

    class FakeRetriever:
        def retrieve(self, question_text: str) -> list[RetrievedChunk]:
            calls["count"] += 1
            return [
                RetrievedChunk(
                    chunk_id="chunk-1",
                    source_path="docs/rag/demo.md",
                    text=f"retrieved context for {question_text}",
                    score=0.1,
                    chunk_index=0,
                )
            ]

    from text2sql_eval.pipeline import runner

    monkeypatch.setattr(runner, "build_retriever", lambda config: FakeRetriever())
    monkeypatch.setattr(
        runner,
        "rag_manifest_path",
        lambda config: "data/rag_index/manifest.json",
    )

    run_id = run_experiment(config_path=str(config_path))

    run_dir = output_dir / run_id
    payload = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    schema_json = run_dir / "schema_context.json"

    assert calls["count"] == 1
    assert schema_json.exists()
    assert (
        payload["run_metadata"]["rag_manifest_path"] == "data/rag_index/manifest.json"
    )
    assert len(payload["records"]) == 2

    record_b = next(
        record for record in payload["records"] if record["track"] == "track_b"
    )
    record_c = next(
        record for record in payload["records"] if record["track"] == "track_c"
    )

    assert "Retrieved Context:" not in record_b["prompt"]
    assert "Retrieved Context:" in record_c["prompt"]
