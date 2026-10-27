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

# A falling short-term trend near the setpoint must not be extrapolated linearly
# through the full 120 s horizon. Closed-loop target anchoring should pull the
# long-horizon forecast back toward the configured target.
model: dict = {}
out = mod._thermal_predictor(
    model,
    temp=49.2,
    slope_c_per_min=-2.0,
    now=1000.0,
    window_span=60.0,
    window_points=8,
    target=49.0,
)
raw_120 = 49.2 + (-2.0) * (120.0 / 60.0) * mod.THERMAL_PREDICTOR_DAMPING[120]
assert out["schema"] == 2
assert out["algorithm"] == "closed_loop_calibrated_v2"
assert out["forecast_120s_c"] > raw_120
assert abs(out["forecast_120s_c"] - 49.0) < abs(raw_120 - 49.0)
assert out["control_output_enabled"] is False

# Predictor metrics are algorithm-specific. A v1 predictor state must be archived
# and its queue/error counters reset instead of contaminating v2 quality scoring.
legacy = {
    "thermal_predictor": {
        "schema": 1,
        "mae_ema_c": {"30": 2.0, "60": 2.4, "120": 2.8},
        "validated_samples": {"30": 100, "60": 100, "120": 100},
        "validated_samples_total": 300,
        "average_mae_c": 2.4,
        "queue": [],
    }
}
out = mod._thermal_predictor(
    legacy,
    temp=49.0,
    slope_c_per_min=0.0,
    now=2000.0,
    window_span=60.0,
    window_points=8,
    target=49.0,
)
assert out["validated_samples_total"] == 0
assert out["quality_state"] == "learning"
assert legacy.get("thermal_predictor_history"), "v1 predictor metrics should be archived"

# Signed online bias must correct systematic under/over-prediction only after
# enough v2 evidence exists. The correction remains bounded.
biased = {
    "thermal_predictor": {
        "schema": 2,
        "queue": [],
        "mae_ema_c": {"30": 0.5, "60": 0.5, "120": 0.5},
        "bias_ema_c": {"30": 1.0, "60": 1.0, "120": 1.0},
        "validated_samples": {"30": 8, "60": 8, "120": 8},
        "last_error_c": {},
    }
}
out = mod._thermal_predictor(
    biased,
    temp=49.0,
    slope_c_per_min=0.0,
    now=3000.0,
    window_span=60.0,
    window_points=8,
    target=49.0,
)
assert 49.0 < out["forecast_30s_c"] <= 50.0
assert 49.0 < out["forecast_120s_c"] <= 50.0
assert all(abs(v) <= mod.THERMAL_PREDICTOR_MAX_BIAS_C for v in out["bias_ema_c"].values())

print("Thermal Predictor Accuracy Calibration tests: PASS")
