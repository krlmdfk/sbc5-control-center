#!/usr/bin/env python3
"""Deterministic 10-second safety replay for SBC5 Thermal Predictor gate.

Does not touch device PWM, model files, state directories or Home Assistant.
Policy.gate remains authoritative; promotion confirmation may only *reduce*
the raw permission, never expand it or delay a downgrade.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "local_apps/sbc5_control_center/thermal_active_policy.py"
spec = importlib.util.spec_from_file_location("thermal_policy_replay", SOURCE)
assert spec and spec.loader
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

rng = Random(20261110)
state: dict = {}
raw_history: list[str] = []
effective_history: list[str] = []
reasons: list[str] = []
confidence_history: list[int] = []
mode_rank = {"observe": 0, "probation": 1, "active": 2}
last_active = False
for cycle in range(720):
    now = 1700000000.0 + cycle * 10.0  # two hours of virtual time
    # Concentrated near the 80%-confidence cutoff, with some steady periods.
    conf = (88 if cycle % 180 < 45 else
            77 + rng.randrange(0, 7))
    mae = 1.10 + rng.randrange(0, 7) * 0.04
    bucket = ("low" if cycle % 210 < 150 else "medium")
    target = 49.0 if cycle < 360 else 49.5
    ai_mode = "observe" if cycle in (60, 61, 400, 401) else "assist"
    controller_action = "thermal_fast" if cycle in (110, 111, 500) else "model_agrees"
    # Inject one stale forecast while leaving state machine intact.
    predictor_epoch = now - 50.0 if cycle in (300, 301) else now
    model = {
        "updated_epoch": predictor_epoch,
        "confidence_percent": conf,
        "average_mae_c": mae,
        "validated_samples": {"30": 40, "60": 40, "120": 40},
        "model_mae_ema_c": {"30": 0.8, "60": 1.1, "120": 1.3},
        "forecast_30s_c": 50.2,
        "forecast_60s_c": 50.2,
        "forecast_120s_c": 50.2,
        "fast_slope_c_per_min": 0.3,
        "slow_slope_c_per_min": 0.2,
    }
    context_reset = policy.refresh_stability_context(
        state, sample_epoch=now, target=target, regime=bucket,
        ai_mode=ai_mode, control_mode="automatic",
    )
    # Mirror runtime order: context refresh, forecast stabilization, quality gate.
    policy.stabilize_forecast(
        state, raw_forecast=50.2, target=target,
        confidence=conf, average_mae=mae,
    )
    raw_mode, raw_reason, raw_limit = policy.gate(
        predictor=model, now=now, ai_mode=ai_mode,
        control_mode="automatic", controller_action=controller_action,
    )
    effective_mode, effective_reason, effective_limit = policy.stabilize_quality_gate(
        state, raw_mode=raw_mode, raw_reason=raw_reason,
        raw_max_delta=raw_limit,
    )
    assert effective_limit <= raw_limit, (cycle, raw_limit, effective_limit)
    assert mode_rank[effective_mode] <= mode_rank[raw_mode], (cycle, raw_mode, effective_mode)
    assert effective_limit in (0, 1, 2), (cycle, effective_limit)
    if raw_mode != "active":
        assert effective_mode == raw_mode, (cycle, raw_mode, effective_mode)
        assert effective_limit == raw_limit, (cycle, raw_limit, effective_limit)
        assert state["quality_gate_active_candidate_cycles"] == 0
    elif raw_mode == "active" and effective_mode == "probation":
        assert effective_reason == "active_waiting_confirmation"
        assert effective_limit == 1
    if context_reset != "none":
        assert context_reset in {
            "regime_changed", "target_changed", "ai_mode_changed",
        }, (cycle, context_reset)
        # First cycle after changing thermal context must never immediately
        # inherit an active authorization from the old context.
        assert effective_mode != "active", (cycle, context_reset, effective_mode)
    raw_history.append(raw_mode)
    effective_history.append(effective_mode)
    reasons.append(raw_reason)
    confidence_history.append(conf)
    last_active = effective_mode == "active"

assert len(raw_history) == 720
assert "predictor_stale" in reasons
assert "safety_action_active" in reasons
assert "ai_assist_required" in reasons
raw_changes = sum(a != b for a, b in zip(raw_history, raw_history[1:]))
effective_changes = sum(a != b for a, b in zip(effective_history, effective_history[1:]))
assert effective_changes < raw_changes, (raw_changes, effective_changes)
assert "active" in effective_history and "probation" in effective_history
print(
    "Thermal Predictor quality gate 2 h virtual replay: PASS; "
    f"raw_transitions={raw_changes}; effective_transitions={effective_changes}; "
    f"stale/safety/observe checked"
)
