#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "local_apps" / "sbc5_control_center" / "ai_cooling.py"
spec = importlib.util.spec_from_file_location("sbc5_ai_cooling", AI)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

model: dict = {"workload_bucket": "low", "workload_load_smoothed_percent": 15.0, "last_pwm": 43}
out = mod._thermal_predictor(model, temp=49.2, slope_c_per_min=-2.0, now=1000.0, window_span=60.0, window_points=8, target=49.0)
raw_120 = 49.2 + (-2.0) * (120.0 / 60.0) * mod.THERMAL_PREDICTOR_DAMPING[120]
assert out["schema"] == 3
assert out["algorithm"] == "regime_aware_dual_slope_v3"
assert out["forecast_120s_c"] > raw_120
assert abs(out["forecast_120s_c"] - 49.0) < abs(raw_120 - 49.0)
assert out["control_output_enabled"] is False
assert "confidence_by_horizon_percent" in out

legacy = {"workload_bucket": "low", "workload_load_smoothed_percent": 15.0, "last_pwm": 43, "thermal_predictor": {"schema": 2, "algorithm": "closed_loop_calibrated_v2", "mae_ema_c": {"30": 2.0, "60": 2.4, "120": 2.8}, "validated_samples": {"30": 100, "60": 100, "120": 100}, "validated_samples_total": 300, "average_mae_c": 2.4, "queue": []}}
out = mod._thermal_predictor(legacy, temp=49.0, slope_c_per_min=0.0, now=2000.0, window_span=60.0, window_points=8, target=49.0)
assert out["validated_samples_total"] == 0
assert out["quality_state"] == "learning"
assert legacy.get("thermal_predictor_history"), "v2 predictor metrics should be archived"

shifted = {"workload_bucket": "low", "workload_load_smoothed_percent": 18.0, "last_pwm": 43}
mod._thermal_predictor(shifted, temp=49.0, slope_c_per_min=0.0, now=3000.0, window_span=60.0, window_points=8, target=49.0)
shifted["workload_bucket"] = "high"
shifted["workload_load_smoothed_percent"] = 82.0
shifted["last_pwm"] = 95
out = mod._thermal_predictor(shifted, temp=56.0, slope_c_per_min=3.0, now=3031.0, window_span=60.0, window_points=8, target=49.0)
assert out["context_rejected_samples"].get("30", 0) >= 1
assert out["validated_samples_global"].get("30", 0) == 0
assert out["mae_all_ema_c"].get("30", 0) > 0

continuous = {"workload_bucket": "medium", "workload_load_smoothed_percent": 50.0, "last_pwm": 70}
for i, temp in enumerate((49.0, 49.4, 49.9, 50.4, 50.9)):
    continuous["qualification_temp_history"] = []
    out = mod._thermal_predictor(continuous, temp=temp, slope_c_per_min=0.0, now=4000.0 + i * 10.0, window_span=0.0, window_points=1, target=49.0)
assert out["fast_slope_c_per_min"] > 0.0
assert out["slow_window_points"] >= 5

print("Thermal Predictor v3 Accuracy/Context tests: PASS")
