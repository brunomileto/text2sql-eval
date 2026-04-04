from __future__ import annotations

import pytest

from text2sql_eval.dataset.schema import Column, SchemaContext, Table
from text2sql_eval.tracks.registry import get_track
from text2sql_eval.tracks.track_a import TrackA
from text2sql_eval.tracks.track_b import TrackB


def test_track_a_prompt_contains_question():
    track = TrackA()

    prompt = track.build_prompt(
        question="How many employees are there?",
        schema_context=SchemaContext(),
    )

    assert "How many employees are there?" in prompt
    assert "Return only the SQL query" in prompt


def test_track_a_prompt_ignores_schema():
    track = TrackA()
    empty_schema = SchemaContext()
    rich_schema = SchemaContext(
        tables=[
            Table(
                name="employees",
                columns=[
                    Column(name="id", data_type="INTEGER"),
                    Column(name="name", data_type="TEXT"),
                ],
            )
        ]
    )

    prompt_without_schema = track.build_prompt("List all names", empty_schema)
    prompt_with_schema = track.build_prompt("List all names", rich_schema)

    assert prompt_without_schema == prompt_with_schema


def test_track_b_prompt_contains_question_and_schema():
    track = TrackB()
    schema = SchemaContext(
        tables=[
            Table(
                name="employees",
                columns=[
                    Column(name="id", data_type="INTEGER", is_primary_key=True),
                    Column(name="department_id", data_type="INTEGER"),
                ],
            )
        ]
    )

    prompt = track.build_prompt(
        question="How many employees are there?",
        schema_context=schema,
    )

    assert "How many employees are there?" in prompt
    assert "## Table: employees" in prompt
    assert "| id | INTEGER | yes | no |  |  |" in prompt


def test_track_schema_usage_flags_match_behavior():
    assert TrackA().uses_schema_context is False
    assert TrackB().uses_schema_context is True


def test_track_a_pre_fetch_returns_empty():
    track = TrackA()
    assert track.pre_fetch("anything") == []


def test_track_a_build_artifacts_returns_empty_mapping():
    track = TrackA()
    artifacts = track.build_artifacts(
        question="anything",
        schema_context=SchemaContext(),
        extra_context=[],
    )

    assert artifacts == {}


def test_get_track_returns_track_a_instance_for_a():
    track = get_track("a")
    assert isinstance(track, TrackA)
    assert track.name == "track_a"


def test_get_track_returns_track_b_instance_for_b():
    track = get_track("b")
    assert isinstance(track, TrackB)
    assert track.name == "track_b"


def test_get_track_raises_for_unknown_track():
    with pytest.raises(ValueError, match="Unknown track"):
        get_track("c")
