#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "local_apps" / "sbc5_control_center" / "ai_cooling_v5.py"

spec = importlib.util.spec_from_file_location("ai_cooling_v5_test", MODULE_PATH)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def main() -> None:
    target = "49.0"
    model = {
        "schema": 5,
        "observations_total": 15543,
        "qualified_samples_total": 197,
        "bins": {
            f"{target}|idle": {
                "observations": 51,
                "qualified_n": 0,
                "last_pwm_percent": 38,
                "last_temp_c": 49.0,
                "last_cpu_load_percent": 7.0,
            },
            f"{target}|low": {
                "observations": 15200,
                "qualified_n": 197,
                "ema_pwm": 43.0,
                "ema_dev": 1.0,
                "last_qualified_cpu_load_percent": 10.6,
                "last_cpu_load_percent": 10.6,
                "last_pwm_percent": 43,
                "last_temp_c": 49.1,
            },
            f"{target}|medium": {
                "observations": 261,
                "qualified_n": 0,
                "last_cpu_load_percent": 45.0,
                "last_pwm_percent": 58,
                "last_temp_c": 50.5,
            },
            f"{target}|high": {
                "observations": 31,
                "qualified_n": 0,
                "last_cpu_load_percent": 75.0,
                "last_pwm_percent": 72,
                "last_temp_c": 52.0,
            },
        },
    }

    state = mod._target_state(model, target)
    mod._seed_from_v4(state, model, target)

    # Existing learned v4 data must remain untouched.
    assert model["bins"][f"{target}|low"]["qualified_n"] == 197
    assert model["qualified_samples_total"] == 197
    assert int(state["seeded_qualified_samples"]) == 197

    low_pred, low_conf, _, _ = mod._global_prediction(state, 10.6)
    med_pred, med_conf, med_distance, med_source = mod._global_prediction(state, 45.0)
    high_pred, high_conf, _, _ = mod._global_prediction(state, 75.0)

    assert low_pred is not None and 35 <= low_pred <= 55
    assert med_pred is not None and 40 <= med_pred <= 75
    assert high_pred is not None and 45 <= high_pred <= 90
    assert low_conf > 0 and med_conf > 0 and high_conf > 0
    assert med_distance <= 10.0
    assert med_source in {"anchor", "interpolation", "global_plus_direct", "extrapolation"}

    # Medium/high receive transferable effective confidence even with zero direct
    # qualified samples. They must not be represented as "no model" anymore.
    direct_medium = 0
    effective_medium = mod._effective_confidence(
        direct_conf=direct_medium,
        global_conf=med_conf,
        predictor_conf=88,
        observations=261,
        direct_qn=0,
        min_samples=30,
        distance=med_distance,
    )
    assert effective_medium > direct_medium
    assert effective_medium >= 20

    # Mature direct evidence must still dominate once the bucket learns locally.
    mature = mod._effective_confidence(
        direct_conf=96,
        global_conf=50,
        predictor_conf=88,
        observations=400,
        direct_qn=30,
        min_samples=30,
        distance=0.0,
    )
    assert mature >= 90

    # Short/transient observations are bounded below a qualified sample weight.
    status = {
        "training_sample_due": True,
        "mode": "assist",
        "temperature_error_c": 1.2,
        "temperature_slope_c_per_min": 1.2,
        "temperature_window_range_c": 2.5,
        "pwm_range_30s_percent": 10,
        "workload_bucket_age_seconds": 12,
        "qualification_state": "rejected",
    }
    w = mod._observation_weight(status)
    assert 0 < w <= mod.TRANSIENT_WEIGHT_MAX < 1.0

    print("AI Cooling v5 hierarchical transfer: PASS")


if __name__ == "__main__":
    main()
