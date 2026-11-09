#!/usr/bin/env python3
"""Protect persistent AI learning from silent clobber on malformed model input."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "local_apps" / "sbc5_control_center" / "ai_cooling_legacy.py"

spec = importlib.util.spec_from_file_location("sbc5_test_ai_legacy", LEGACY)
assert spec is not None and spec.loader is not None
ai = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def must_reject(model: Path, value: str) -> None:
    model.write_text(value, encoding="utf-8")
    before = digest(model)
    try:
        ai._load_model_for_step(model, 42.0)
    except RuntimeError as exc:
        assert "preserving file" in str(exc)
    else:
        raise AssertionError("invalid existing model was accepted")
    assert digest(model) == before, "invalid model was modified"


with tempfile.TemporaryDirectory() as td:
    model = Path(td) / "ai_cooling_model.json"
    assert ai._load_model_for_step(model, 42.0)["observations_total"] == 0
    model.write_text(json.dumps({
        "schema": ai.SCHEMA, "observations_total": 40072,
        "qualified_samples_total": 1169, "bins": {},
    }), encoding="utf-8")
    state = ai._load_model_for_step(model, 42.0)
    assert state["observations_total"] == 40072
    assert state["qualified_samples_total"] == 1169

    model.write_text(json.dumps({
        "schema": ai.SCHEMA - 1, "observations_total": 40072,
        "qualified_samples_total": 1169, "bins": {},
    }), encoding="utf-8")
    migrated = ai._load_model_for_step(model, 42.0)
    assert migrated["legacy_workload_v1"]["observations_total"] == 40072
    assert migrated["legacy_samples_total"] == 1169
    assert migrated["migrated_from_schema"] == ai.SCHEMA - 1

    for bad in ("", "not json", "{}", "[]", "null", '"hello"',
                '{"broken":true}', '{"schema":999}', '{"schema":"bad"}',
                '{"schema":5,'):
        must_reject(model, bad)

    # The evaluator must stop before writing either model or status on bad input.
    must_reject(model, "bad json")
    before = digest(model)
    status_path = Path(td) / "status.json"
    args = argparse.Namespace(model=str(model), status=str(status_path),
                              mirror="", telemetry=str(Path(td) / "telemetry.json"),
                              require_private_telemetry=False)
    try:
        ai.step(args)
    except RuntimeError as exc:
        assert "preserving file" in str(exc)
    else:
        raise AssertionError("evaluator unexpectedly processed an invalid model")
    assert digest(model) == before
    assert not status_path.exists()

    shell = (ROOT / "local_apps" / "sbc5_control_center" / "run_legacy.sh").read_text(encoding="utf-8")
    assert "ai_eval_empty_warned=false" in shell
    assert "AI Cooling: evaluator nie zwrócił wyniku" in shell

print("AI model integrity fail-closed: PASS")
