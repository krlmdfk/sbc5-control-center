#!/usr/bin/env python3
"""Regression tests for SBC5 3.1.30 Thermal Predictor Stability v2."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


policy = load_module("thermal_active_policy_3130", APP / "thermal_active_policy.py")

# A single high raw forecast must be conditioned before it reaches control policy.
state: dict = {}
s1 = policy.stabilize_forecast(
    state, raw_forecast=49.10, target=49.0, confidence=90.0, average_mae=1.0
)
s2 = policy.stabilize_forecast(
    state, raw_forecast=52.57, target=49.0, confidence=90.0, average_mae=1.0
)
assert s2["stable_forecast_c"] < 50.5, s2
assert s2["median_forecast_c"] < 51.0, s2

# Directional confirmation must require two consecutive conditioned hot forecasts.
predictor = {
    "forecast_30s_c": 50.2,
    "forecast_60s_c": 50.2,
    "forecast_120s_c": 50.2,
    "model_mae_ema_c": {"30": 0.6, "60": 0.8, "120": 1.0},
    "validated_samples": {"30": 20, "60": 20, "120": 20},
    "confidence_percent": 90,
    "fast_slope_c_per_min": 0.30,
    "slow_slope_c_per_min": 0.12,
}
waiting = policy.decide(
    predictor=predictor,
    target=49.0,
    temp=49.4,
    slope=0.3,
    mode="active",
    max_delta=2,
    stability={
        "stable_forecast_c": 50.2,
        "hot_confirm_cycles": 1,
        "cool_confirm_cycles": 0,
        "fast_path": False,
    },
)
assert waiting["requested_delta_pp"] == 0, waiting
assert waiting["decision_reason"] == "hot_forecast_waiting_confirmation", waiting

confirmed = policy.decide(
    predictor=predictor,
    target=49.0,
    temp=49.4,
    slope=0.3,
    mode="active",
    max_delta=2,
    stability={
        "stable_forecast_c": 50.2,
        "hot_confirm_cycles": 2,
        "cool_confirm_cycles": 0,
        "fast_path": False,
    },
)
assert confirmed["requested_delta_pp"] > 0, confirmed

# High-quality >=2.5 C forecast gets the bounded fast path without waiting two cycles.
fast_state: dict = {}
fast = policy.stabilize_forecast(
    fast_state, raw_forecast=52.0, target=49.0, confidence=88.0, average_mae=1.0
)
fast_predictor = dict(predictor)
fast_predictor.update({
    "forecast_30s_c": 52.0,
    "forecast_60s_c": 52.0,
    "forecast_120s_c": 52.0,
    "confidence_percent": 88,
})
fast_decision = policy.decide(
    predictor=fast_predictor,
    target=49.0,
    temp=49.4,
    slope=0.4,
    mode="active",
    max_delta=2,
    stability=fast,
)
assert fast["fast_path"] is True, fast
assert fast_decision["requested_delta_pp"] == 2, fast_decision

# If temperature is already cooling rapidly, a positive TP correction is blocked
# even when measured temperature remains above target.
cooling_predictor = dict(predictor)
cooling_predictor.update({
    "fast_slope_c_per_min": -1.20,
    "slow_slope_c_per_min": -0.30,
    "confidence_percent": 90,
})
cooling = policy.decide(
    predictor=cooling_predictor,
    target=49.0,
    temp=50.0,
    slope=-1.2,
    mode="active",
    max_delta=2,
    stability={
        "stable_forecast_c": 50.0,
        "hot_confirm_cycles": 2,
        "cool_confirm_cycles": 0,
        "fast_path": False,
    },
)
assert cooling["requested_delta_pp"] == 0, cooling
assert cooling["decision_reason"] == "trend_guard_cooling", cooling

# Thermal state must distinguish position from direction.
assert policy.thermal_state(temp=49.9, target=49.0, trend=-1.78) == "above_target_cooling"
assert policy.thermal_state(temp=49.0, target=49.0, trend=0.0) == "near_target_stable"

print("Thermal Predictor Stability 3.1.30: PASS")
