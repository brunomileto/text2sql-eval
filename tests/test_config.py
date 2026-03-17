from __future__ import annotations

from textwrap import dedent

import pytest

from text2sql_eval.config import load_config


def _write_config(tmp_path, content: str):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(dedent(content), encoding="utf-8")
    return config_path


def test_load_config_parses_expected_sections_and_values(tmp_path):
    config_path = _write_config(
        tmp_path,
        """
        llm:
          models:
            - provider: openai
              model: gpt-4o
              temperature: 0.0
              max_tokens: 1024
            - provider: anthropic
              model: claude-3-5-sonnet-20241022
              temperature: 0.2
              max_tokens: 512

        rag:
          backend: chroma

        dataset:
          questions: data/dev.json
          db: data/database.sqlite

        experiment:
          tracks: [a]
          limit: 10
          output_dir: results/

        constraints:
          restricted_tables_file: config/restricted_tables.yaml
        """,
    )

    config = load_config(str(config_path))

    assert len(config.llm.models) == 2
    assert config.llm.models[0].provider == "openai"
    assert config.llm.models[0].model == "gpt-4o"
    assert config.llm.models[1].provider == "anthropic"
    assert config.dataset.questions == "data/dev.json"
    assert config.dataset.db == "data/database.sqlite"
    assert config.experiment.tracks == ["a"]
    assert config.experiment.limit == 10
    assert config.experiment.output_dir == "results/"


def test_load_config_supports_null_limit(tmp_path):
    config_path = _write_config(
        tmp_path,
        """
        llm:
          models:
            - provider: openai
              model: gpt-4o
              temperature: 0.0
              max_tokens: 1024
        dataset:
          questions: data/dev.json
          db: data/database.sqlite
        experiment:
          tracks: [a]
          limit: null
          output_dir: results/
        """,
    )

    config = load_config(str(config_path))

    assert config.experiment.limit is None


def test_load_config_raises_for_missing_file(tmp_path):
    missing = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config(str(missing))


def test_load_config_raises_for_empty_file(tmp_path):
    config_path = _write_config(tmp_path, "")

    with pytest.raises(ValueError, match="Config file is empty"):
        load_config(str(config_path))


@pytest.mark.parametrize(
    ("yaml_text", "message"),
    [
        (
            """
            dataset:
              questions: data/dev.json
              db: data/database.sqlite
            experiment:
              tracks: [a]
              limit: null
              output_dir: results/
            """,
            "Missing required key 'llm'",
        ),
        (
            """
            llm:
              models: not-a-list
            dataset:
              questions: data/dev.json
              db: data/database.sqlite
            experiment:
              tracks: [a]
              limit: null
              output_dir: results/
            """,
            "'llm.models' must be a list",
        ),
        (
            """
            llm:
              models:
                - provider: openai
                  model: gpt-4o
                  temperature: 0.0
                  max_tokens: 1024
            dataset:
              questions: data/dev.json
              db: data/database.sqlite
            experiment:
              tracks: a
              limit: null
              output_dir: results/
            """,
            "'experiment.tracks' must be a list",
        ),
    ],
)
def test_load_config_raises_clear_validation_errors(tmp_path, yaml_text, message):
    config_path = _write_config(tmp_path, yaml_text)

    with pytest.raises(ValueError, match=message):
        load_config(str(config_path))
