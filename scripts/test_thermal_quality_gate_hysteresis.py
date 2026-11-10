#!/usr/bin/env python3
"""Conservative promotion-only thermal quality gate regression tests."""
import importlib.util
from pathlib import Path

src = Path(__file__).resolve().parents[1] / "local_apps/sbc5_control_center/thermal_active_policy.py"
spec = importlib.util.spec_from_file_location("thermal_hysteresis", src)
assert spec and spec.loader
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

# Replay gate output from Nov 10: a single active sample cannot expand authority.
raw_modes = ["probation", "active", "probation", "active", "active", "probation"]
state = {}
actual = [
    policy.stabilize_quality_gate(
        state,
        raw_mode=mode,
        raw_reason="eligible" if mode == "active" else "quality_probation",
        raw_max_delta=2 if mode == "active" else 1,
    )
    for mode in raw_modes
]
assert [a[0] for a in actual] == [
    "probation", "probation", "probation", "probation", "active", "probation"
], actual
assert [a[2] for a in actual] == [1, 1, 1, 1, 2, 1], actual
assert actual[1][1] == "active_waiting_confirmation"
assert actual[4][1] == "eligible"
assert actual[5][1] == "quality_probation"

# Immediate loss of active permission on quality degradation or safety.
for degraded in ("probation", "observe"):
    s = {}
    for _ in range(2):
        assert policy.stabilize_quality_gate(
            s, raw_mode="active", raw_reason="eligible", raw_max_delta=2
        )[0] in ("active", "probation")
    assert s["quality_gate_effective_mode"] == "active"
    result = policy.stabilize_quality_gate(
        s, raw_mode=degraded, raw_reason="safety_action_active", raw_max_delta=0,
    )
    assert result == (degraded, "safety_action_active", 0), result
    assert s["quality_gate_active_candidate_cycles"] == 0
    # Returning to eligibility must require another confirmation.
    again = policy.stabilize_quality_gate(
        s, raw_mode="active", raw_reason="eligible", raw_max_delta=2,
    )
    assert again == ("probation", "active_waiting_confirmation", 1), again

# Repeated active eligibility remains active; never extends above the raw limit.
state = {}
for i in range(10):
    mode, _, delta = policy.stabilize_quality_gate(
        state, raw_mode="active", raw_reason="eligible", raw_max_delta=2,
    )
    assert delta <= 2
    if i:
        assert mode == "active"
assert state["quality_gate_active_candidate_cycles"] == 2

# A partially restored state with an old active flag cannot bypass promotion.
# This can occur after a legacy model handoff or a truncated state migration.
for damaged in (
    {"quality_gate_effective_mode": "active"},
    {"quality_gate_effective_mode": "active", "quality_gate_active_candidate_cycles": 0},
    {"quality_gate_effective_mode": "active", "quality_gate_active_candidate_cycles": float("nan")},
):
    first = policy.stabilize_quality_gate(
        damaged, raw_mode="active", raw_reason="eligible", raw_max_delta=2,
    )
    assert first == ("probation", "active_waiting_confirmation", 1), first
    second = policy.stabilize_quality_gate(
        damaged, raw_mode="active", raw_reason="eligible", raw_max_delta=2,
    )
    assert second == ("active", "eligible", 2), second

# Lost or stale context must revoke any previously earned promotion.
s = {}
policy.refresh_stability_context(
    s, sample_epoch=100.0, target=49.0, regime="low",
    ai_mode="assist", control_mode="automatic",
)
policy.stabilize_forecast(
    s, raw_forecast=49.5, target=49.0, confidence=90, average_mae=1,
)
policy.stabilize_quality_gate(s, raw_mode="active", raw_reason="eligible", raw_max_delta=2)
policy.refresh_stability_context(
    s, sample_epoch=110.0, target=49.0, regime="low",
    ai_mode="assist", control_mode="automatic",
)
policy.stabilize_forecast(
    s, raw_forecast=49.5, target=49.0, confidence=90, average_mae=1,
)
assert policy.stabilize_quality_gate(
    s, raw_mode="active", raw_reason="eligible", raw_max_delta=2,
)[0] == "active"
assert policy.refresh_stability_context(
    s, sample_epoch=160.0, target=49.0, regime="low",
    ai_mode="assist", control_mode="automatic",
) == "sample_gap"
policy.stabilize_forecast(
    s, raw_forecast=49.5, target=49.0, confidence=90, average_mae=1,
)
assert policy.stabilize_quality_gate(
    s, raw_mode="active", raw_reason="eligible", raw_max_delta=2,
) == ("probation", "active_waiting_confirmation", 1)

# In an ordinary predictor, stale values are still observe before hysteresis.
p = {
    "updated_epoch": 100.0, "confidence_percent": 95,
    "average_mae_c": 0.5, "validated_samples": {"30": 50, "60": 50, "120": 50},
}
assert policy.gate(
    predictor=p, now=200.0, ai_mode="assist", control_mode="automatic",
    controller_action="model_agrees",
)[:2] == ("observe", "predictor_stale")
assert policy.gate(
    predictor=p, now=100.0, ai_mode="assist", control_mode="automatic",
    controller_action="thermal_fast",
)[:2] == ("observe", "safety_action_active")

print("Thermal quality-gate promotion-only hysteresis: PASS")
