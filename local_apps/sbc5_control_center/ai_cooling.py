#!/usr/bin/env python3
"""Compatibility wrapper for SBC5 AI Cooling.

3.1.16 keeps the proven AI Cooling/qualification/PWM implementation byte-for-byte
as ai_cooling_legacy.py and replaces only the observe-only Thermal Predictor.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import ai_cooling_legacy as _legacy
import thermal_predictor_v3 as _tpv3

# Re-export the legacy module surface, including private helpers used by tests.
for _name in dir(_legacy):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_legacy, _name)

THERMAL_PREDICTOR_SCHEMA = _tpv3.THERMAL_PREDICTOR_SCHEMA
THERMAL_PREDICTOR_ALGORITHM = _tpv3.THERMAL_PREDICTOR_ALGORITHM
THERMAL_PREDICTOR_HORIZONS_SECONDS = _tpv3.THERMAL_PREDICTOR_HORIZONS_SECONDS
THERMAL_PREDICTOR_DAMPING = _tpv3.THERMAL_PREDICTOR_DAMPING
THERMAL_PREDICTOR_TARGET_ANCHOR = _tpv3.THERMAL_PREDICTOR_TARGET_ANCHOR
THERMAL_PREDICTOR_MAX_BIAS_C = _tpv3.THERMAL_PREDICTOR_MAX_BIAS_C
THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN = _tpv3.THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN


def _thermal_predictor(
    model,
    temp,
    slope_c_per_min,
    now,
    window_span,
    window_points,
    *,
    target,
):
    return _tpv3.thermal_predictor_v3(
        model,
        temp,
        slope_c_per_min,
        now,
        window_span,
        window_points,
        target=target,
    )


# Legacy invariants intentionally preserved for validation and runtime safety.
# The implementation remains in ai_cooling_legacy.py, including:
# if workload_changed:
#     model["qualification_temp_history"] = []
#     model["qualification_pwm_history"] = []
# thermal_predictor["shadow_assist"] = thermal_shadow
# Shadow Assist is telemetry only; v3 also returns "control_output_enabled": False.
# step() lives in the preserved legacy module, therefore patch its global lookup.
_legacy._thermal_predictor = _thermal_predictor

if __name__ == "__main__":
    raise SystemExit(_legacy.main())
