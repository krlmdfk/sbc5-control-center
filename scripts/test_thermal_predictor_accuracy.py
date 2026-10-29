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

# v3.1 keeps target anchoring and observe-only authority.
model: dict = {"workload_bucket": "low", "workload_load_smoothed_percent": 15.0, "last_pwm": 43}
out = mod._thermal_predictor(model, temp=49.2, slope_c_per_min=-2.0, now=1000.0, window_span=60.0, window_points=8, target=49.0)
raw_120 = 49.2 + (-2.0) * (120.0 / 60.0) * mod.THERMAL_PREDICTOR_DAMPING[120]
assert out["schema"] == 4
assert out["algorithm"] == "path_aware_robust_slope_v3_1"
assert out["forecast_120s_c"] > raw_120
assert abs(out["forecast_120s_c"] - 49.0) < abs(raw_120 - 49.0)
assert out["control_output_enabled"] is False
assert out["validation_mode"] == "exact_due_interpolation"
assert out["context_guard"] == "path_aware"
assert out["slope_estimator"] == "theil_sen_median"
assert "confidence_by_horizon_percent" in out
assert out["accuracy_target_c"] == {"30": 1.0, "60": 1.5, "120": 2.5}

# v2 statistics remain archived and are not imported into the current calibration.
legacy = {"workload_bucket": "low", "workload_load_smoothed_percent": 15.0, "last_pwm": 43, "thermal_predictor": {"schema": 2, "algorithm": "closed_loop_calibrated_v2", "mae_ema_c": {"30": 2.0, "60": 2.4, "120": 2.8}, "validated_samples": {"30": 100, "60": 100, "120": 100}, "validated_samples_total": 300, "average_mae_c": 2.4, "queue": []}}
out = mod._thermal_predictor(legacy, temp=49.0, slope_c_per_min=0.0, now=2000.0, window_span=60.0, window_points=8, target=49.0)
assert out["validated_samples_total"] == 0
assert out["quality_state"] == "learning"
assert legacy.get("thermal_predictor_history"), "v2 predictor metrics should be archived"

# v3 -> v3.1 migration preserves stable-regime calibration but drops the old queue,
# because due-time validation semantics changed in v3.1.
v3 = {
    "workload_bucket": "low",
    "workload_load_smoothed_percent": 20.0,
    "last_pwm": 45,
    "thermal_predictor": {
        "schema": 3,
        "algorithm": "regime_aware_dual_slope_v3",
        "queue": [{"created_epoch": 10, "due_epoch": 40, "horizon_seconds": 30, "predicted_c": 90}],
        "temp_history": [[900.0, 48.8], [910.0, 49.0]],
        "regime_stats": {"low": {"30": {"mae_ema_c": 0.7, "bias_ema_c": 0.1, "samples": 8}}},
        "global_stats": {"30": {"mae_ema_c": 0.8, "bias_ema_c": 0.0, "samples": 12}},
        "mae_all_ema_c": {"30": 1.0},
    },
}
out = mod._thermal_predictor(v3, temp=49.1, slope_c_per_min=0.0, now=920.0, window_span=60.0, window_points=8, target=49.0)
assert out["schema"] == 4
assert out.get("migrated_from_schema") == 3
assert out["validated_samples_global"].get("30", 0) == 12
assert out["validated_samples"].get("30", 0) == 8
assert out["rejected_samples_total"] == 0

# Exact due-time validation: the 30 s forecast must be compared against the
# interpolated temperature at t=3030, not the later poll temperature at t=3040.
exact = {"workload_bucket": "low", "workload_load_smoothed_percent": 20.0, "last_pwm": 45}
first = mod._thermal_predictor(exact, temp=49.0, slope_c_per_min=0.0, now=3000.0, window_span=60.0, window_points=8, target=49.0)
predicted_30 = first["forecast_30s_c"]
mod._thermal_predictor(exact, temp=50.0, slope_c_per_min=1.5, now=3020.0, window_span=60.0, window_points=8, target=49.0)
out = mod._thermal_predictor(exact, temp=51.0, slope_c_per_min=1.5, now=3040.0, window_span=60.0, window_points=8, target=49.0)
validation = out["last_validation"]["30"]
assert validation["actual_source"] == "interpolated"
assert abs(validation["actual_c"] - 50.5) < 0.001
assert abs(validation["absolute_error_c"] - abs(50.5 - predicted_30)) < 0.001
assert validation["evaluation_lag_seconds"] == 10.0

# A transient workload excursion must be rejected even when the endpoints return
# to the same bucket/load/PWM. Endpoint-only v3 validation could miss this case.
transient = {"workload_bucket": "low", "workload_load_smoothed_percent": 18.0, "last_pwm": 43}
mod._thermal_predictor(transient, temp=49.0, slope_c_per_min=0.0, now=4000.0, window_span=60.0, window_points=8, target=49.0)
transient["workload_bucket"] = "high"
transient["workload_load_smoothed_percent"] = 88.0
transient["last_pwm"] = 95
mod._thermal_predictor(transient, temp=52.0, slope_c_per_min=3.0, now=4015.0, window_span=60.0, window_points=8, target=49.0)
transient["workload_bucket"] = "low"
transient["workload_load_smoothed_percent"] = 18.0
transient["last_pwm"] = 43
out = mod._thermal_predictor(transient, temp=50.0, slope_c_per_min=0.0, now=4030.0, window_span=60.0, window_points=8, target=49.0)
assert out["rejected_samples"].get("30", 0) >= 1
assert out["last_validation"]["30"]["reason"] == "bucket_changed"
assert out["rejected_samples_by_category"]["30"]["conditions"] >= 1

# Robust slope estimator must resist one isolated temperature spike.
robust = {"workload_bucket": "medium", "workload_load_smoothed_percent": 50.0, "last_pwm": 70}
for i, temp in enumerate((49.0, 49.2, 60.0, 49.6, 49.8, 50.0)):
    out = mod._thermal_predictor(robust, temp=temp, slope_c_per_min=0.0, now=5000.0 + i * 10.0, window_span=60.0, window_points=6, target=49.0)
assert 0.5 < out["slow_slope_c_per_min"] < 2.0
assert out["slow_window_points"] >= 6

print("Thermal Predictor v3.1 Accuracy/Context tests: PASS")
