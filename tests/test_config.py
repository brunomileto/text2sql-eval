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

        inputs:
          questions_file: data/dev.json
          database_file: data/database.sqlite

        run_defaults:
          tracks: [a]
          limit: 10
          output_dir: results/
        """,
    )

    config = load_config(str(config_path))

    assert len(config.models) == 2
    assert config.models[0].provider == "openai"
    assert config.models[0].model == "gpt-4o"
    assert config.models[1].provider == "anthropic"
    assert config.inputs.questions_file == "data/dev.json"
    assert config.inputs.database_file == "data/database.sqlite"
    assert config.run_defaults.tracks == ["a"]
    assert config.run_defaults.limit == 10
    assert config.run_defaults.output_dir == "results/"


def test_load_config_supports_null_limit(tmp_path):
    config_path = _write_config(
        tmp_path,
        """
        models:
          - provider: openai
            model: gpt-4o
            temperature: 0.0
            max_tokens: 1024
        inputs:
          questions_file: data/dev.json
          database_file: data/database.sqlite
        run_defaults:
          tracks: [a]
          limit: null
          output_dir: results/
        """,
    )

    config = load_config(str(config_path))

    assert config.run_defaults.limit is None


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
            inputs:
              questions_file: data/dev.json
              database_file: data/database.sqlite
            run_defaults:
              tracks: [a]
              limit: null
              output_dir: results/
            """,
            "Missing required key 'models'",
        ),
        (
            """
            models: not-a-list
            inputs:
              questions_file: data/dev.json
              database_file: data/database.sqlite
            run_defaults:
              tracks: [a]
              limit: null
              output_dir: results/
            """,
            "'models' must be a list",
        ),
        (
            """
            models:
              - provider: openai
                model: gpt-4o
                temperature: 0.0
                max_tokens: 1024
            inputs:
              questions_file: data/dev.json
              database_file: data/database.sqlite
            run_defaults:
              tracks: a
              limit: null
              output_dir: results/
            """,
            "'run_defaults.tracks' must be a list",
        ),
    ],
)
def test_load_config_raises_clear_validation_errors(tmp_path, yaml_text, message):
    config_path = _write_config(tmp_path, yaml_text)

    with pytest.raises(ValueError, match=message):
        load_config(str(config_path))
