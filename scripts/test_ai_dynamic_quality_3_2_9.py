#!/usr/bin/env python3
"""3.2.9 separate quasi-steady qualification from validated thermal response.

Offline, deterministic exercise of repeated medium backup bursts and safety gates.
No hardware writes, no changes to the 22-field AI ABI or PWM output.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "local_apps/sbc5_control_center/ai_cooling_v5_1.py"
spec = importlib.util.spec_from_file_location("ai_dynamic_quality_329", path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def sample(temp, slope, bucket="medium", pwm=78, load=45, action="trim_up_direct"):
    return {
        "workload_bucket": bucket, "mode": "assist",
        "temperature_c": temp,
        "temperature_slope_c_per_min": slope,
        "cpu_load_smoothed_percent": load,
        "current_pwm_percent": pwm, "controller_action": action,
        # Existing steady-state learner still has no qualified evidence.
        "bin_qualified_samples": 0,
    }

model = {"bins": {"49.0|medium": {"qualified_n": 0}},
         "qualified_samples_total": 2349}
target = {}
first = mod._dynamic_quality_step(target, sample(54.0, 1.8), 100, 1000.0)
assert first["validated_pairs"] == 0 and first["last_reason"] == "window_building"
second = mod._dynamic_quality_step(target, sample(55.0, 2.0, pwm=82), 101, 1030.0)
assert second["validated_pairs"] == 1 and second["warming_pairs"] == 1
assert second["qualified_sample"] is True and second["control_output_enabled"] is False
assert second["independent_of_steady_samples"] is True
# The same observation may be evaluated on multiple AI/relay cycles.
same = mod._dynamic_quality_step(target, sample(55.0, 2.0, pwm=82), 101, 1040.0)
assert same["validated_pairs"] == 1
third = mod._dynamic_quality_step(target, sample(54.5, -1.0, pwm=77), 102, 1060.0)
assert third["validated_pairs"] == 2 and third["cooling_pairs"] == 1
assert -0.5 < third["temperature_rate_ema_c_per_min"] < 2

# A new burst after returning to low does not pair with an old medium sample.
mod._dynamic_quality_step(target, sample(50.0, -1.0, bucket="low", pwm=60, load=20), 103, 1090.0)
restart = mod._dynamic_quality_step(target, sample(54.0, 3.0), 104, 1120.0)
assert restart["last_reason"] == "window_building"
assert restart["validated_pairs"] == 2

# Reject erratic/unsafe observations without contaminating validated evidence.
checks = [
    (sample(58.0, 2.0, load=90), "load_change"),
    (sample(64.0, 12.0), "temperature_trend"),
    (sample(56.0, 2.0, action="safety_max"), "unsafe_action"),
]
for i, (bad, reason) in enumerate(checks):
    state = {}
    mod._dynamic_quality_step(state, sample(54.0, 2.0), 400 + 2*i, 2000.0)
    value = mod._dynamic_quality_step(state, bad, 401 + 2*i, 2030.0)
    assert reason in value["rejection_counts"], (reason, value)
    assert value["validated_pairs"] == 0

# Warming but no measurable change is not evidence of thermal response.
s = {}
mod._dynamic_quality_step(s, sample(55.0, 0.0), 800, 4000.0)
flat = mod._dynamic_quality_step(s, sample(55.05, 0.0), 801, 4030.0)
assert flat["last_reason"] == "no_temperature_response"

# Verify state survives a restart as an ordinary serializable v5 target object.
import json
serialized = json.loads(json.dumps(target))
assert serialized["dynamic_quality_v1"]["bins"]["medium"]["validated_pairs"] == 2
assert model["qualified_samples_total"] == 2349
assert model["bins"]["49.0|medium"]["qualified_n"] == 0
assert mod.POLICY == "hierarchical_continuous_v5_1"
assert "fields[20]" in path.read_text(encoding="utf-8")  # ABI still intact
print("SBC5 3.2.9 dynamic quality separate learning, restart, safety: PASS")
