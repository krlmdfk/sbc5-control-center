#!/usr/bin/env python3
"""Regression tests for Thermal Predictor short-term context resets."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
spec = importlib.util.spec_from_file_location("thermal_active_policy_context", APP / "thermal_active_policy.py")
assert spec and spec.loader
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


def tick(state: dict, epoch: float, *, target: float = 49.0,
         regime: str = "low", ai_mode: str = "assist",
         control_mode: str = "automatic", forecast: float = 50.0) -> str:
    reason = policy.refresh_stability_context(
        state, sample_epoch=epoch, target=target,
        regime=regime, ai_mode=ai_mode, control_mode=control_mode,
    )
    policy.stabilize_forecast(
        state, raw_forecast=forecast, target=target,
        confidence=90.0, average_mae=1.0,
    )
    return reason


# Continuous operation preserves smoothing and the two-cycle confirmation.
state = {}
assert tick(state, 100.0) == "none"
assert state["hot_confirm_cycles"] == 1
assert tick(state, 110.0) == "none"
assert state["hot_confirm_cycles"] == 2
assert state["context_reset_reason"] == "none"
assert state.get("context_reset_count", 0) == 0

# Small target jitter should not cause a reset.
assert tick(state, 120.0, target=49.2) == "none"

# Setpoint changes invalidate old forecasts and directional confirmation.
assert tick(state, 130.0, target=50.0, forecast=48.0) == "target_changed"
assert state["hot_confirm_cycles"] == 0
assert state["cool_confirm_cycles"] == 1
assert state["forecast_history_c"] == [48.0]
assert state["context_reset_count"] == 1

# Workload regime changes also invalidate short-term stabilization.
assert tick(state, 140.0, target=50.0, regime="high", forecast=51.0) == "regime_changed"
assert state["forecast_history_c"] == [51.0]

# The assist state and control mode are independent reset dimensions.
assert tick(state, 150.0, target=50.0, regime="high", ai_mode="learning") == "ai_mode_changed"
assert tick(state, 160.0, target=50.0, regime="high", ai_mode="learning",
            control_mode="manual") == "control_mode_changed"

# A sufficiently long gap or backwards clock leap must not reuse confirmations.
assert tick(state, 200.1, target=50.0, regime="high", ai_mode="learning",
            control_mode="manual") == "sample_gap"
assert tick(state, 195.0, target=50.0, regime="high", ai_mode="learning",
            control_mode="manual") == "clock_moved_backwards"

# Older persisted state has no context metadata: fail closed once, then continue.
legacy = {"forecast_history_c": [52.0, 53.0], "stable_forecast_c": 52.5,
          "hot_confirm_cycles": 19}
assert tick(legacy, 100.0) == "unversioned_history"
assert legacy["forecast_history_c"] == [50.0]
assert legacy["hot_confirm_cycles"] == 1

# The quality/authority gate is unchanged by short-term context resets.
assert policy.ACTIVE_MAX_DELTA_PP == 2
assert policy.PROBATION_MAX_DELTA_PP == 1
assert policy.ACTIVE_MIN_CONFIDENCE == 80
assert policy.PROBATION_MIN_CONFIDENCE == 68

runtime = (APP / "ai_cooling_v5_2.py").read_text(encoding="utf-8")
assert "policy.refresh_stability_context(" in runtime
assert '"stability_context_reset_reason"' in runtime
assert '"stability_context_reset_count"' in runtime

print("Thermal guidance context reset: PASS")
