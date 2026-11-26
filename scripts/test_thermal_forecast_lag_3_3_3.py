#!/usr/bin/env python3
"""Regression: confirmed forecast acceleration and direction conflict guard."""
import importlib.util
from pathlib import Path
path = Path(__file__).resolve().parents[1] / "local_apps/sbc5_control_center/thermal_active_policy.py"
spec = importlib.util.spec_from_file_location("thermal_policy_333", path)
assert spec and spec.loader
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

def sample(state, raw, confidence=90, mae=1.0):
    return policy.stabilize_forecast(state, raw_forecast=raw, target=49.0,
                                     confidence=confidence, average_mae=mae)

for sign in (-1, 1):
    state = {}
    for _ in range(3):
        sample(state, 49.0)
    first = sample(state, 49.0 + sign * 4)
    assert first["stable_forecast_c"] == 49.0, first
    second = sample(state, 49.0 + sign * 4)
    assert second["forecast_ema_alpha"] == 0.65, second
    assert abs(second["stable_forecast_c"] - 49.0) == 2.6 or abs(abs(second["stable_forecast_c"] - 49.0) - 2.6) < 0.001, second
    state = {}
    for raw in (49.0, 49.0, 49.0, 49.0 + sign * 4):
        sample(state, raw)
    low_quality = sample(state, 49.0 + sign * 4, confidence=77, mae=1.6)
    assert low_quality["forecast_ema_alpha"] == 0.35, low_quality

def decision(raw, stable, temp, slope):
    predictor = {f"forecast_{h}s_c": raw for h in (30, 60, 120)}
    predictor.update(confidence_percent=90, fast_slope_c_per_min=slope,
                     slow_slope_c_per_min=slope)
    return policy.decide(predictor=predictor, target=49.0, temp=temp,
                         slope=slope, mode="active", max_delta=2,
                         stability={"stable_forecast_c": stable,
                                    "hot_confirm_cycles": 3,
                                    "cool_confirm_cycles": 3,
                                    "fast_path": True})

for result in (decision(47.0, 52.0, 50.5, 0.3),
               decision(51.0, 46.0, 48.0, -0.3)):
    assert result["requested_delta_pp"] == 0, result
    assert result["decision_reason"] == "raw_forecast_direction_conflict", result
assert decision(52.0, 52.0, 50.5, 0.3)["requested_delta_pp"] == 2
assert decision(46.0, 46.0, 48.0, -0.3)["requested_delta_pp"] == -2
assert policy.ACTIVE_MAX_DELTA_PP == 2
assert policy.PROBATION_MAX_DELTA_PP == 1

# 3.3.4: a severe upward lag may be corrected only when all horizons,
# measured temperature, measured trend and the active quality gate agree.
def hot_predictor(values=(53.5, 53.8, 53.2), confidence=83, mae=1.2):
    p = {f"forecast_{h}s_c": v for h, v in zip((30, 60, 120), values)}
    p.update(confidence_percent=confidence, average_mae_c=mae,
             fast_slope_c_per_min=0.3, slow_slope_c_per_min=0.2,
             validated_samples={"30": 15, "60": 15, "120": 15},
             updated_epoch=100)
    return p

def corroborated(p, mode="active", temp=50.1, slope=0.3):
    return policy.confirmed_hot_transition(
        predictor=p, target=49.0, temp=temp, slope=slope, mode=mode)

p = hot_predictor()
assert corroborated(p)
for mode in ("observe", "probation"):
    assert not corroborated(p, mode=mode)
for temp, slope in ((49.2, 0.3), (50.1, -0.3), (float("nan"), 0.3),
                    (50.1, float("nan"))):
    assert not corroborated(p, temp=temp, slope=slope)
for bad in (hot_predictor(confidence=54, mae=3.12),
            hot_predictor(mae=1.31),
            hot_predictor(values=(54, 53, 49)),
            hot_predictor(values=(54, 56, 54)),
            hot_predictor(values=(53, float("nan"), 53))):
    assert not corroborated(bad), bad
missing = hot_predictor()
del missing["forecast_120s_c"]
assert not corroborated(missing)

# Independent baseline must remain identical with and without the attack.
a, b = {}, {}
for raw in (49., 49., 49., 54., 54., 54., 48., 48., 49.):
    baseline = policy.stabilize_forecast(a, raw_forecast=raw, target=49.,
                                        confidence=83, average_mae=1.2)
    result = policy.stabilize_forecast(b, raw_forecast=raw, target=49.,
                                      confidence=83, average_mae=1.2,
                                      hot_transition_confirmed=raw > 52)
    attack = result["forecast_lag_attack_c"]
    assert result["ema_baseline_forecast_c"] == baseline["stable_forecast_c"]
    assert 0 <= attack <= 1.5
    assert abs(result["stable_forecast_c"] -
               baseline["stable_forecast_c"] - attack) < 0.002
    if raw < 50:
        assert attack == 0
    if attack:
        assert not result["fast_path"] or baseline["fast_path"]
        assert result["stable_forecast_c"] <= raw

# First isolated jump, even when corroborated, cannot instantly bypass the
# existing two-cycle confirmation or extend the +/-2 pp active authority.
state = {}
for _ in range(3):
    sample(state, 49.0)
result = policy.stabilize_forecast(state, raw_forecast=54.0, target=49.,
                                   confidence=83, average_mae=1.2,
                                   hot_transition_confirmed=True)
assert result["forecast_lag_attack_c"] == 1.5
assert result["stable_forecast_c"] == 50.5
assert result["fast_path"] is False
decision = policy.decide(predictor=p, target=49., temp=50.1, slope=0.3,
                         mode="active", max_delta=2, stability=result)
assert decision["requested_delta_pp"] == 0, decision

# Poor quality remains observation-only; even a mistaken true flag must
# not activate the extra correction at low confidence or high MAE.
for confidence, mae in ((54, 3.12), (79, 1.2), (83, 1.31)):
    state = {}
    for _ in range(3):
        sample(state, 49.)
    result = policy.stabilize_forecast(
        state, raw_forecast=61.45, target=49., confidence=confidence,
        average_mae=mae, hot_transition_confirmed=True)
    assert result["forecast_lag_attack_c"] == 0

runtime = (path.parent / "ai_cooling_v5_2.py").read_text(encoding="utf-8")
assert runtime.index("gate_mode, gate_reason, max_delta = policy.gate(") < runtime.index("hot_transition = (")
assert 'str(status.get("state")) == "assist"' in runtime
assert "hot_transition_confirmed=hot_transition" in runtime
assert 'guided_output = int(round(policy.clamp(output + requested_delta, lo, hi)))' in runtime
for key in ("forecast_lag_attack_c", "forecast_lag_attack_confirmed", "ema_baseline_forecast_c"):
    assert runtime.count(f'"{key}"') >= 2

print("Thermal forecast lag regression: PASS")
