#!/usr/bin/env python3
"""Read-only regression audit for SBC5 Thermal Predictor gate/diagnostics.

This file intentionally documents the 3.2.1 baseline. In particular,
the gate has no hysteresis yet; any future hysteresis patch must update
the baseline sequence test *deliberately*, with independent hardware checks.
No application state, AI checkpoints, configuration or PWM is written.
"""
from __future__ import annotations

import importlib.util
import inspect
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
SOURCE = APP / "thermal_active_policy.py"

spec = importlib.util.spec_from_file_location("sbc5_thermal_gate_audit", SOURCE)
assert spec and spec.loader
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


def predictor(confidence: int, mae: float, *, now: float = 1000.0) -> dict:
    return {
        "updated_epoch": now - 1.0,
        "confidence_percent": confidence,
        "average_mae_c": mae,
        "validated_samples": {"30": 20, "60": 20, "120": 20},
        "model_mae_ema_c": {"30": 1.0, "60": 1.0, "120": 1.0},
        "forecast_30s_c": 50.5,
        "forecast_60s_c": 50.5,
        "forecast_120s_c": 50.5,
        "fast_slope_c_per_min": 0.30,
        "slow_slope_c_per_min": 0.15,
    }


def mode_for(confidence: int, mae: float) -> tuple[str, str, int]:
    return policy.gate(
        predictor=predictor(confidence, mae),
        now=1000.0,
        ai_mode="assist",
        control_mode="automatic",
        controller_action="model_agrees",
    )


# The actual 10 November log samples cross the hard 80% cutoff repeatedly.
# This is a *baseline characterization*, not endorsement of gate flapping.
samples = [
    (77, 1.458, "probation"),
    (80, 1.249, "active"),
    (77, 1.411, "probation"),
    (83, 1.017, "active"),
    (82, 1.122, "active"),
    (79, 1.273, "probation"),
]
modes = [mode_for(c, mae)[0] for c, mae, _ in samples]
assert modes == [expected for _, _, expected in samples], modes
assert sum(a != b for a, b in zip(modes, modes[1:])) == 4, modes
assert mode_for(79, 1.0) == ("probation", "quality_probation", 1)
assert mode_for(80, 1.0) == ("active", "eligible", 2)
assert mode_for(85, 1.51) == ("probation", "quality_probation", 1)
assert mode_for(85, 2.51)[0] == "observe"
assert mode_for(67, 1.0)[0] == "observe"

# Inadequately validated, stale and unsafe requests must not reach active.
for reason, changes in [
    ("predictor_stale", {"updated_epoch": 900.0}),
    ("insufficient_validated_forecasts", {"validated_samples": {"30": 7, "60": 7, "120": 7}}),
]:
    item = predictor(90, 0.8)
    item.update(changes)
    result = policy.gate(
        predictor=item, now=1000.0, ai_mode="assist",
        control_mode="automatic", controller_action="model_agrees",
    )
    assert result[0] == "observe" and result[1] == reason, (reason, result)
assert policy.gate(
    predictor=predictor(90, 0.8), now=1000.0, ai_mode="assist",
    control_mode="automatic", controller_action="thermal_fast",
)[0] == "observe"
assert policy.gate(
    predictor=predictor(90, 0.8), now=1000.0, ai_mode="assist",
    control_mode="automatic", controller_action="model_agrees",
    outcome_samples=6, outcome_success_percent=40.0,
)[0] == "observe"

# Median-of-three + EMA alpha 0.35 damp a one-off spike, independently
# of the displayed candidate_gain.
state = {}
first = policy.stabilize_forecast(
    state, raw_forecast=49.1, target=49.0,
    confidence=90.0, average_mae=1.0,
)
second = policy.stabilize_forecast(
    state, raw_forecast=52.57, target=49.0,
    confidence=90.0, average_mae=1.0,
)
assert first["stable_forecast_c"] == 49.1
assert second["stable_forecast_c"] == 49.1, second
third = policy.stabilize_forecast(
    state, raw_forecast=52.57, target=49.0,
    confidence=90.0, average_mae=1.0,
)
assert math.isclose(third["stable_forecast_c"], 50.3145, abs_tol=0.002), third

# The 0.093 log value is exactly the diagnostic quality heuristic.
conf, mae = 77, 1.458
maturity = policy.clamp((conf - 55.0) / 40.0, 0.0, 1.0)
accuracy = policy.clamp((3.0 - mae) / 2.0, 0.0, 1.0)
candidate_gain = 0.22 * maturity * accuracy
assert round(candidate_gain, 3) == 0.093, candidate_gain
assert "gain" not in inspect.signature(policy.decide).parameters
assert "candidate_gain" not in inspect.signature(policy.decide).parameters

# The probation gate must not reduce cooling even on a strong cold forecast.
p = predictor(79, 1.0)
p.update({
    "fast_slope_c_per_min": -0.4,
    "slow_slope_c_per_min": -0.2,
    "forecast_30s_c": 47.0,
    "forecast_60s_c": 47.0,
    "forecast_120s_c": 47.0,
})
cold_state = {"stable_forecast_c": 47.0, "cool_confirm_cycles": 3, "fast_path": False}
cold_probation = policy.decide(
    predictor=p, target=49.0, temp=48.0, slope=-0.4,
    mode="probation", max_delta=1, stability=cold_state,
)
assert cold_probation["requested_delta_pp"] == 0, cold_probation
cold_active = policy.decide(
    predictor=p, target=49.0, temp=48.0, slope=-0.4,
    mode="active", max_delta=2, stability=cold_state,
)
assert -2 <= cold_active["requested_delta_pp"] <= 0, cold_active

# The trend guard blocks added fan power during strong cooling.
p_hot = predictor(90, 1.0)
p_hot["fast_slope_c_per_min"] = -1.2
p_hot["slow_slope_c_per_min"] = -0.3
guarded = policy.decide(
    predictor=p_hot, target=49.0, temp=50.0, slope=-1.2,
    mode="active", max_delta=2,
    stability={"stable_forecast_c": 50.2, "hot_confirm_cycles": 2, "fast_path": False},
)
assert guarded["requested_delta_pp"] == 0, guarded
assert guarded["decision_reason"] == "trend_guard_cooling", guarded

print("SBC5 3.2.1 Thermal Gate/Diagnostic baseline: PASS")
