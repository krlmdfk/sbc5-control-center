#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "local_apps" / "sbc5_control_center" / "ai_cooling_v5_1.py"
spec = importlib.util.spec_from_file_location("ai_cooling_v5_1_test", MODULE)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

status = {
    "qualified_sample": False,
    "training_sample_due": True,
    "mode": "assist",
    "workload_bucket": "medium",
    "workload_bucket_age_seconds": 45,
    "temperature_error_c": 8.0,
    "temperature_slope_c_per_min": 3.2,
    "pwm_range_30s_percent": 12.0,
    "current_pwm_percent": 100.0,
    "baseline_pwm_percent": 100.0,
}
weight = mod._transient_observation_weight(status)
assert 0.04 <= weight <= mod.TRANSIENT_DYNAMIC_WEIGHT_MAX, weight
assert mod._transient_observation_weight({**status, "workload_bucket": "low"}) == 0.0
assert mod._transient_observation_weight({**status, "workload_bucket_age_seconds": 5}) == 0.0
assert mod._transient_observation_weight({**status, "temperature_error_c": 16.0}) == 0.0

# Use sparse steady anchors similar to the first real MEDIUM test. Dynamic
# evidence must increase confidence but never move the predicted PWM itself.
target = {
    "anchors": {
        "50": {"mean_pwm": 83.5, "dev_pwm": 2.0, "weight": 0.25},
        "60": {"mean_pwm": 84.0, "dev_pwm": 2.5, "weight": 0.20},
    }
}
pred_before, conf_before, _, _ = mod._original_global_prediction(target, 55.0)
for _ in range(6):
    mod._update_transient_evidence(target, 55.0, status, weight)
pred_after, conf_after, _, source_after = mod._global_prediction_v5_1(target, 55.0)
transient_conf, support, samples = mod._transient_confidence(target, 55.0)
assert pred_before == pred_after, (pred_before, pred_after)
assert conf_after > conf_before, (conf_before, conf_after)
assert transient_conf > 0
assert support > 0
assert samples >= 6
assert source_after.endswith("+transient")

# A short burst must not make a sparse bucket assist-ready on confidence alone.
effective = mod.base._effective_confidence(
    direct_conf=24,
    global_conf=conf_after,
    predictor_conf=59,
    observations=273,
    direct_qn=0,
    min_samples=30,
    distance=0.0,
)
assert effective < mod.base.ASSIST_MIN_EFFECTIVE_CONFIDENCE, effective

# The old quasi-steady learner intentionally rejects this hot transient while
# v5.1 still extracts bounded dynamic evidence from it.
assert mod._transient_observation_weight({**status, "temperature_error_c": 10.0}) > 0
assert mod.base._observation_weight({**status, "temperature_error_c": 10.0}) == 0.0

print("AI Cooling v5.1 transient learning guards: PASS")
