#!/usr/bin/env python3
"""Regression test for Thermal Predictor effectiveness persistence in 3.1.26."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"

with tempfile.TemporaryDirectory() as tmp:
    checkpoint = Path(tmp) / "thermal_effectiveness.json"
    os.environ["SBC5_THERMAL_EFFECTIVENESS_STATE"] = str(checkpoint)

    spec = importlib.util.spec_from_file_location("thermal_effectiveness_3126", APP / "thermal_effectiveness.py")
    assert spec and spec.loader
    eff = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(eff)

    model: dict = {}
    summary = eff.update(
        model=model,
        now=1000.0,
        temperature_c=50.5,
        target_c=49.0,
        applied_delta_pp=1,
        decision_reason="forecast_hot",
    )
    assert summary["interventions_total"] == 1, summary
    assert summary["pending"] == 1, summary
    assert checkpoint.is_file(), checkpoint

    # Simulate a process restart and a wrapper/model rebuild. The dedicated
    # checkpoint must restore the intervention even if the model mirror is empty.
    restarted_model: dict = {}
    summary = eff.update(
        model=restarted_model,
        now=1031.0,
        temperature_c=49.7,
        target_c=49.0,
        applied_delta_pp=0,
        decision_reason="near_target",
    )
    assert summary["interventions_total"] == 1, summary
    assert summary["horizons"]["30"]["samples"] == 1, summary
    assert summary["storage"] == "durable_checkpoint", summary

    # Simulate migration from 3.1.25 schema-1 model state when no checkpoint
    # exists yet. Counters and horizon evidence must be retained and upgraded.
    checkpoint.unlink()
    legacy_model = {
        "thermal_effectiveness": {
            "schema": 1,
            "pending": [],
            "recent": [],
            "horizons": {
                "30": {"samples": 4, "improved": 3, "neutral": 1, "worsened": 0, "avg_improvement_c": 0.42},
                "60": {"samples": 3, "improved": 2, "neutral": 1, "worsened": 0, "avg_improvement_c": 0.31},
                "120": {"samples": 2, "improved": 1, "neutral": 1, "worsened": 0, "avg_improvement_c": 0.18},
            },
            "interventions_total": 5,
            "interventions_up": 4,
            "interventions_down": 1,
        }
    }
    summary = eff.update(
        model=legacy_model,
        now=2000.0,
        temperature_c=49.0,
        target_c=49.0,
        applied_delta_pp=0,
    )
    assert legacy_model["thermal_effectiveness"]["schema"] == 2, legacy_model
    assert summary["interventions_total"] == 5, summary
    assert summary["samples"] == 9, summary

print("Thermal Predictor effectiveness persistence 3.1.26: PASS")
