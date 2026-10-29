#!/usr/bin/env python3
"""Regression tests for SBC5 3.1.21 Thermal Predictor guided assist."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"

spec = importlib.util.spec_from_file_location("thermal_active_policy", APP / "thermal_active_policy.py")
assert spec and spec.loader
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

predictor = {
    "forecast_30s_c": 51.0,
    "forecast_60s_c": 50.5,
    "forecast_120s_c": 50.0,
    "model_mae_ema_c": {"30": 0.6, "60": 1.4, "120": 2.4},
    "validated_samples": {"30": 20, "60": 20, "120": 20},
    "confidence_percent": 88,
    "average_mae_c": 1.2,
    "updated_epoch": 1000,
}
weighted, weights = policy.dynamic_forecast(predictor, 49.0)
assert weights["30"] > weights["60"] > weights["120"], weights
assert weighted > 50.0, weighted

mode, reason, limit = policy.gate(
    predictor=predictor, now=1010, ai_mode="assist", control_mode="automatic",
    controller_action="deadband_hold", outcome_samples=0, outcome_success_percent=100,
)
assert (mode, reason, limit) == ("active", "eligible", 2), (mode, reason, limit)

decision = policy.decide(predictor=predictor, target=49.0, temp=49.2, slope=0.4, mode=mode, max_delta=limit)
assert decision["requested_delta_pp"] > 0, decision

weak = dict(predictor)
weak.update({"confidence_percent": 60, "average_mae_c": 3.2})
mode, reason, limit = policy.gate(
    predictor=weak, now=1010, ai_mode="assist", control_mode="automatic",
    controller_action="hold", outcome_samples=0, outcome_success_percent=100,
)
assert mode == "observe" and limit == 0, (mode, reason, limit)

cool = dict(predictor)
cool.update({"forecast_30s_c": 47.0, "forecast_60s_c": 47.5, "forecast_120s_c": 48.0})
decision = policy.decide(predictor=cool, target=49.0, temp=49.4, slope=0.3, mode="active", max_delta=2)
assert decision["requested_delta_pp"] == 0, decision
assert decision["decision_reason"] == "downward_sign_guard", decision

docker = (APP / "Dockerfile").read_text(encoding="utf-8")
v52 = (APP / "ai_cooling_v5_2.py").read_text(encoding="utf-8")
assert "COPY ai_cooling_v5_1.py /ai_cooling_v5_1.py" in docker
assert "COPY ai_cooling_v5_2.py /ai_cooling.py" in docker
assert "COPY thermal_active_policy.py /thermal_active_policy.py" in docker
assert "base._candidate_pwm = _predictive_candidate_pwm" in v52
assert "base._apply_hierarchical_step = _apply_guided_step" in v52
assert "fields[0] =" not in v52, "v5.2 must not create a second direct PWM output path"
print("Thermal Predictor guided assist 3.1.21: PASS")
