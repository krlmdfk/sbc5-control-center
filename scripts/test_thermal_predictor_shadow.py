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

base = {
    "quality_state": "excellent",
    "confidence_percent": 92,
    "average_mae_c": 0.6,
    "validated_samples": {"30": 12, "60": 12, "120": 12},
    "forecast_30s_c": 52.0,
    "forecast_60s_c": 52.5,
    "forecast_120s_c": 52.0,
    "slope_c_per_min": 1.0,
}
shadow = mod._thermal_shadow_assist(base, target=49.0, baseline=44, min_safe=9, maximum=100, control_mode="automatic", controller_action="hold")
assert shadow["eligible"] is True
assert shadow["suggested_delta_pp"] == 2
assert shadow["suggested_pwm_percent"] == 46
assert shadow["control_output_enabled"] is False

poor = dict(base, quality_state="weak", confidence_percent=55, average_mae_c=2.4)
shadow = mod._thermal_shadow_assist(poor, target=49.0, baseline=44, min_safe=9, maximum=100, control_mode="automatic", controller_action="hold")
assert shadow["eligible"] is False
assert shadow["gate_reason"] == "quality_below_good"
assert -2 <= shadow["suggested_delta_pp"] <= 2

text = AI.read_text(encoding="utf-8")
assert 'thermal_predictor["shadow_assist"] = thermal_shadow' in text
assert 'Shadow Assist is telemetry only' in text
assert 'control_output_enabled": False' in text
print("Thermal Predictor Shadow Assist tests: PASS")
