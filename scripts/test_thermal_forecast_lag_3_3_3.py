#!/usr/bin/env python3
"""Regression: confirmed forecast acceleration and direction conflict guard."""
import importlib.util
from pathlib import Path
path = Path(__file__).resolve().parents[1] / "local_apps/sbc5_control_center/thermal_active_policy.py"
spec = importlib.util.spec_from_file_location("thermal_policy_333", path)
assert spec and spec.loader
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

def sample(state, raw, confidence=90, mae=1.0):
    return policy.stabilize_forecast(state, raw_forecast=raw, target=49.0,
                                     confidence=confidence, average_mae=mae)

for sign in (-1, 1):
    state = {}
    for _ in range(3):
        sample(state, 49.0)
    first = sample(state, 49.0 + sign * 4)
    assert first["stable_forecast_c"] == 49.0, first
    second = sample(state, 49.0 + sign * 4)
    assert second["forecast_ema_alpha"] == 0.65, second
    assert abs(second["stable_forecast_c"] - 49.0) == 2.6 or abs(abs(second["stable_forecast_c"] - 49.0) - 2.6) < 0.001, second
    state = {}
    for raw in (49.0, 49.0, 49.0, 49.0 + sign * 4):
        sample(state, raw)
    low_quality = sample(state, 49.0 + sign * 4, confidence=77, mae=1.6)
    assert low_quality["forecast_ema_alpha"] == 0.35, low_quality

def decision(raw, stable, temp, slope):
    predictor = {f"forecast_{h}s_c": raw for h in (30, 60, 120)}
    predictor.update(confidence_percent=90, fast_slope_c_per_min=slope,
                     slow_slope_c_per_min=slope)
    return policy.decide(predictor=predictor, target=49.0, temp=temp,
                         slope=slope, mode="active", max_delta=2,
                         stability={"stable_forecast_c": stable,
                                    "hot_confirm_cycles": 3,
                                    "cool_confirm_cycles": 3,
                                    "fast_path": True})

for result in (decision(47.0, 52.0, 50.5, 0.3),
               decision(51.0, 46.0, 48.0, -0.3)):
    assert result["requested_delta_pp"] == 0, result
    assert result["decision_reason"] == "raw_forecast_direction_conflict", result
assert decision(52.0, 52.0, 50.5, 0.3)["requested_delta_pp"] == 2
assert decision(46.0, 46.0, 48.0, -0.3)["requested_delta_pp"] == -2
assert policy.ACTIVE_MAX_DELTA_PP == 2
assert policy.PROBATION_MAX_DELTA_PP == 1
print("Thermal forecast lag regression: PASS")
