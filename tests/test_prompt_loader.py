from __future__ import annotations

import pytest

from text2sql_eval.prompts.loader import load_prompt_template, render_prompt


def test_load_prompt_template_reads_track_a_file():
    template = load_prompt_template("track_a")

    assert "You are an expert SQL assistant." in template
    assert "Question: {question}" in template


def test_load_prompt_template_raises_for_missing_file():
    with pytest.raises(FileNotFoundError, match="Prompt template not found"):
        load_prompt_template("track_missing")


def test_render_prompt_fills_question_placeholder():
    prompt = render_prompt("track_a", {"question": "How many accounts exist?"})

    assert "How many accounts exist?" in prompt
    assert "{question}" not in prompt


def test_render_prompt_raises_for_missing_template_variables():
    with pytest.raises(ValueError, match="Missing template variables"):
        render_prompt("track_a", {})
