#!/usr/bin/env python3
"""Regression tests for SBC5 Control Center 3.1.31 Adaptive Trim Recovery."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = (APP / "run_legacy.sh").read_text(encoding="utf-8")
patch29 = load_module("patch29", APP / "patch_thermal_stability_3_1_29.py")
patch31 = load_module("patch31", APP / "patch_adaptive_trim_3_1_31.py")
patched = patch31.patch(patch29.patch(legacy))

assert "thermal_trend_fused" in patched
assert "thermal_trend_fused_milli" in patched
assert "trendF=${thermal_trend_fused}C/min" in patched
assert 'action="trim_up_blocked_cooling"' in patched
assert 'action="trim_up_blocked_fused_trend"' in patched
assert 'action="trim_recovery_cooling"' in patched
assert 'action="deadband_trim_recovery_fast"' in patched
assert '[ "$thermal_trend_fused_milli" -le -300 ]' in patched
assert 'adaptive_trim=$((adaptive_trim - 2))' in patched
assert "fused(65/35)" in patched

thermal = load_module("thermal_control_filter", APP / "thermal_control_filter.py")
state: dict = {}
# Deterministic cooling sequence: fused trend must be bounded and negative.
for ts, temp in [(0.0, 51.0), (10.0, 50.7), (20.0, 50.4), (30.0, 50.1), (40.0, 49.8)]:
    result = thermal.update_signal(state, raw_c=temp, target_c=49.0, now=ts + 1000.0)
    state = result
assert result["schema"] == 2
assert result["trend_fused_c_per_min"] < 0
expected = round(0.65 * result["trend_30s_c_per_min"] + 0.35 * result["trend_120s_c_per_min"], 3)
assert result["trend_fused_c_per_min"] == expected
assert result["trend_fused_milli_c_per_min"] == int(round(expected * 1000.0))
assert result["trend_fused_fast_weight"] == 0.65
assert result["trend_fused_slow_weight"] == 0.35

# Safety / authority invariants: this release must not alter AI/TP limits.
ai = (APP / "ai_cooling_v5_2.py").read_text(encoding="utf-8")
policy = (APP / "thermal_active_policy.py").read_text(encoding="utf-8")
assert "ACTIVE_MAX_DELTA_PP = 2" in policy
assert "PROBATION_MAX_DELTA_PP = 1" in policy
assert "hierarchical_continuous_v5_2_thermal_guided_stability_v2" in ai

print("Adaptive Trim Recovery 3.1.31: PASS")
