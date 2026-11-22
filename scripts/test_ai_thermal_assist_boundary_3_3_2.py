#!/usr/bin/env python3
"""Regression: TP cannot command PWM when AI is only ready/learning."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
sys.path.insert(0, str(APP))

spec = importlib.util.spec_from_file_location("ai_guidance_boundary_test", APP / "ai_cooling_v5_2.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

original_apply = module._original_apply
original_guidance = module._guided_runtime
original_effectiveness = module.effectiveness.update
original_argv = module.base._argv_value
try:
    module._original_apply = lambda model, status, fields: (model, status, fields)
    module._guided_runtime = lambda model, status: {
        "requested_delta_pp": 1, "gate_mode": "active", "gate_reason": "eligible",
        "decision_reason": "forecast_hot", "weighted_forecast_c": 52.0,
    }
    module.effectiveness.update = lambda **kwargs: {"mode": "observe_only"}
    module.base._argv_value = lambda name, default=None: {
        "--control-mode": "automatic", "--assist-limit": "5",
        "--min-safe": "9", "--maximum": "100",
    }.get(name, default)

    for ai_state, expected_delta in [
        ("ready", 0), ("learning", 0), ("disabled", 0), ("assist", 1)
    ]:
        status = {
            "mode": "assist", "state": ai_state, "reason": "outside_assist_window",
            "baseline_pwm_percent": 60, "output_pwm_percent": 60,
            "correction_pwm_percent": 0, "target_temp_c": 49.0,
            "temperature_c": 52.0, "thermal_predictor": {},
        }
        fields = ["60", ai_state, "outside_assist_window", "70", "60", "0", "0"] + [""] * 34
        _, result, output_fields = module._apply_guided_step({}, status, fields)
        expected_output = 60 + expected_delta
        assert result["output_pwm_percent"] == expected_output, (ai_state, result)
        assert result["correction_pwm_percent"] == expected_delta, (ai_state, result)
        assert result["thermal_predictor_guidance"]["applied_delta_pp"] == expected_delta
        assert output_fields[0] == str(expected_output), (ai_state, output_fields)
        assert output_fields[6] == str(expected_delta), (ai_state, output_fields)

    # Even in state=assist, a non-automatic controller has no AI authority.
    module.base._argv_value = lambda name, default=None: {
        "--control-mode": "hybrid", "--assist-limit": "5",
        "--min-safe": "9", "--maximum": "100",
    }.get(name, default)
    status = {
        "mode": "assist", "state": "assist", "baseline_pwm_percent": 60,
        "output_pwm_percent": 60, "correction_pwm_percent": 0,
        "target_temp_c": 49.0, "temperature_c": 52.0, "thermal_predictor": {},
    }
    fields = ["60", "assist", "model_agrees", "80", "60", "0", "0"] + [""] * 34
    _, result, _ = module._apply_guided_step({}, status, fields)
    assert result["output_pwm_percent"] == 60
finally:
    module._original_apply = original_apply
    module._guided_runtime = original_guidance
    module.effectiveness.update = original_effectiveness
    module.base._argv_value = original_argv

print("SBC5 3.3.2 AI/TP assist boundary: PASS")
