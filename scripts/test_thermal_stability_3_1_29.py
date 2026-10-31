#!/usr/bin/env python3
"""Regression tests for SBC5 3.1.29 thermal control stability."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


filter_mod = load_module("thermal_control_filter", APP / "thermal_control_filter.py")
policy = load_module("thermal_active_policy_3129", APP / "thermal_active_policy.py")
patch_mod = load_module("patch_thermal_stability_3129", APP / "patch_thermal_stability_3_1_29.py")

# Median-of-3 rejects an isolated raw sensor spike before it reaches T_control.
state = {}
state = filter_mod.update_signal(state, raw_c=50.0, target_c=50.0, now=0.0)
state = filter_mod.update_signal(state, raw_c=50.1, target_c=50.0, now=10.0)
state = filter_mod.update_signal(state, raw_c=54.0, target_c=50.0, now=20.0)
assert state["spike_rejected"] is True, state
assert state["median3_c"] < 51.0, state
assert state["control_c"] < 51.0, state

# Rise is intentionally faster than fall: thermal safety reacts faster than noise-driven cooldown.
rise = filter_mod.update_signal({}, raw_c=49.0, target_c=50.0, now=0.0)
rise = filter_mod.update_signal(rise, raw_c=51.0, target_c=50.0, now=10.0)
fall = filter_mod.update_signal({}, raw_c=51.0, target_c=50.0, now=0.0)
fall = filter_mod.update_signal(fall, raw_c=49.0, target_c=50.0, now=10.0)
assert rise["alpha_used"] > fall["alpha_used"], (rise, fall)

# Direction changes need persistent evidence and a reversal hold.
state = {}
for i, temp in enumerate((49.0, 49.2, 49.5, 49.8, 50.2, 50.6, 50.9)):
    state = filter_mod.update_signal(state, raw_c=temp, target_c=50.0, now=float(i * 10))
assert state["confirmed_direction"] == "hot", state
hot_state = state
state = filter_mod.update_signal(state, raw_c=50.4, target_c=50.0, now=70.0)
assert state["confirmed_direction"] != "cool", state
assert state["reverse_hold_cycles"] >= 0, state

# Predictor forecast must agree with robust thermal trend before it can nudge PWM.
predictor = {
    "forecast_30s_c": 52.0,
    "forecast_60s_c": 52.2,
    "forecast_120s_c": 52.4,
    "model_mae_ema_c": {"30": 0.5, "60": 0.8, "120": 1.0},
    "validated_samples": {"30": 20, "60": 20, "120": 20},
    "fast_slope_c_per_min": 0.35,
    "slow_slope_c_per_min": 0.18,
}
decision = policy.decide(
    predictor=predictor, target=50.0, temp=50.3, slope=0.25, mode="active", max_delta=2
)
assert decision["requested_delta_pp"] > 0, decision
assert decision["forecast_confirmed"] is True, decision
assert decision["quality_gate"]["trend_30s_c_per_min"] > 0, decision

unconfirmed = dict(predictor)
unconfirmed.update({"fast_slope_c_per_min": -0.05, "slow_slope_c_per_min": 0.0})
decision = policy.decide(
    predictor=unconfirmed, target=50.0, temp=50.2, slope=0.0, mode="active", max_delta=2
)
assert decision["requested_delta_pp"] == 0, decision
assert decision["decision_reason"] == "hot_forecast_unconfirmed", decision

# Apply the audited image-time patch to the current compatibility controller and
# verify the resulting Bash syntax. This prevents source drift from silently
# creating an unpatched or syntactically invalid production image.
legacy = (APP / "run_legacy.sh").read_text(encoding="utf-8")
patched = patch_mod.patch(legacy)
assert 'THERMAL_CONTROL_FILTER_SCRIPT="/thermal_control_filter.py"' in patched
assert 'error=$((temp_control_milli - target_milli))' in patched
assert 'T_raw=$(millideg_to_c_1dp "$temp_milli")' in patched
assert 'T_control=$(millideg_to_c_1dp "$temp_control_milli")' in patched
assert 'temperature_control_c' in patched
assert 'temperature_trend_30s_c_per_min' in patched
assert 'temperature_trend_120s_c_per_min' in patched
assert 'thermal_direction' in patched
assert 'emergency_handoff_milli=70000' in patched
assert '[ "$temp_milli" -ge "$emergency_handoff_milli" ]' in patched
assert 'adaptive_pwm_curve_state_for_temp "$temp_control_milli"' in patched

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "run_legacy.sh"
    path.write_text(patched, encoding="utf-8")
    subprocess.run(["bash", "-n", str(path)], check=True)

print("Thermal stability 3.1.29: PASS")
