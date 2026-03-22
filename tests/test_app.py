from __future__ import annotations

import pytest

from text2sql_eval.app import run_experiment


def test_run_experiment_loads_config_and_runs_pipeline(monkeypatch):
    calls: dict[str, object] = {}

    def fake_load_config(path: str):
        calls["config_path"] = path
        return "CONFIG"

    def fake_run(config):
        calls["config"] = config
        return "20260322-120000"

    from text2sql_eval import app

    monkeypatch.setattr(app, "load_config", fake_load_config)
    monkeypatch.setattr(app, "run", fake_run)

    run_id = run_experiment(config_path="config/custom.yaml")

    assert run_id == "20260322-120000"
    assert calls["config_path"] == "config/custom.yaml"
    assert calls["config"] == "CONFIG"


def test_run_experiment_rejects_overrides_until_step_two():
    with pytest.raises(ValueError, match="Overrides are not implemented yet"):
        run_experiment(track="a")
