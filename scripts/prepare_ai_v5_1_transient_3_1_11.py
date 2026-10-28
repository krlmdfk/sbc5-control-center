#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
AI = APP / "ai_cooling_v5.py"
CARD_YAML = ROOT / "dashboard" / "sbc5_control_center_diagnostics_card.yaml"
CARD_JSON = APP / "dashboard_card.json"
TEST = ROOT / "scripts" / "test_ai_v5_transient_learning.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    ai = AI.read_text(encoding="utf-8")

    ai = replace_once(
        ai,
        'V5_POLICY = "hierarchical_continuous_v5"\nANCHOR_STEP_PERCENT = 10\n',
        'V5_POLICY = "hierarchical_continuous_v5_1"\nANCHOR_STEP_PERCENT = 10\n',
        "bump v5 policy",
    )
    ai = replace_once(
        ai,
        'TRANSIENT_WEIGHT_MAX = 0.28\nWORKLOAD_CENTERS = {"idle": 5.0, "low": 20.0, "medium": 45.0, "high": 75.0}\n',
        'TRANSIENT_WEIGHT_MAX = 0.28\nTRANSIENT_DYNAMIC_WEIGHT_MAX = 0.32\nTRANSIENT_BUCKETS = {"medium", "high"}\nTRANSIENT_MIN_BUCKET_AGE_SECONDS = 15.0\nTRANSIENT_MAX_ERROR_C = 15.0\nTRANSIENT_SUPPORT_CAP = 12.0\nTRANSIENT_SUPPORT_SCALE = 0.95\nTRANSIENT_CONFIDENCE_CAP = 58.0\nWORKLOAD_CENTERS = {"idle": 5.0, "low": 20.0, "medium": 45.0, "high": 75.0}\n',
        "add transient constants",
    )

    anchor = '''def _candidate_pwm(status: dict[str, Any]) -> float:\n'''
    transient_helpers = r'''def _transient_observation_weight(status: dict[str, Any]) -> float:
    """Return small dynamic evidence weight for short medium/high bursts.

    This evidence is intentionally separate from qualified steady-state samples.
    It may raise confidence that we understand the thermal response around a load
    level, but it never increments v4 qualified counters and never directly moves
    the steady-state PWM prediction.
    """
    if bool(status.get("qualified_sample")):
        return 0.0
    if not bool(status.get("training_sample_due")):
        return 0.0
    if str(status.get("mode")) not in {"learning", "assist"}:
        return 0.0
    bucket = str(status.get("workload_bucket") or "")
    if bucket not in TRANSIENT_BUCKETS:
        return 0.0
    age = _num(status.get("workload_bucket_age_seconds"), 0.0)
    if age < TRANSIENT_MIN_BUCKET_AGE_SECONDS:
        return 0.0
    error = abs(_num(status.get("temperature_error_c"), 99.0))
    if error > TRANSIENT_MAX_ERROR_C:
        return 0.0
    slope = abs(_num(status.get("temperature_slope_c_per_min"), 0.0))
    pwm_range = abs(_num(status.get("pwm_range_30s_percent"), 0.0))

    # We deliberately reward a clear thermal response instead of rejecting it.
    # A hot/rising transient is useful evidence for capacity/confidence, but the
    # bounded weight prevents one burst from making a bucket assist-ready.
    age_factor = _clamp((age - 10.0) / 40.0, 0.20, 1.0)
    signal_factor = _clamp((error + 0.45 * slope) / 5.0, 0.30, 1.0)
    actuator_factor = _clamp(1.0 - pwm_range / 65.0, 0.45, 1.0)
    bucket_factor = 1.0 if bucket == "medium" else 0.90
    weight = TRANSIENT_DYNAMIC_WEIGHT_MAX * age_factor * signal_factor * actuator_factor * bucket_factor
    return round(_clamp(weight, 0.04, TRANSIENT_DYNAMIC_WEIGHT_MAX), 4)


def _update_transient_evidence(
    target_state: dict[str, Any], load: float, status: dict[str, Any], weight: float
) -> None:
    if weight <= 0:
        return
    anchors = target_state.setdefault("transient_anchors", {})
    if not isinstance(anchors, dict):
        anchors = {}
        target_state["transient_anchors"] = anchors

    lo = int(_clamp(math.floor(load / ANCHOR_STEP_PERCENT) * ANCHOR_STEP_PERCENT, 0, 100))
    hi = int(_clamp(math.ceil(load / ANCHOR_STEP_PERCENT) * ANCHOR_STEP_PERCENT, 0, 100))
    if lo == hi:
        pairs = [(lo, 1.0)]
    else:
        frac = (load - lo) / float(hi - lo)
        pairs = [(lo, 1.0 - frac), (hi, frac)]

    error = _num(status.get("temperature_error_c"), 0.0)
    slope = _num(status.get("temperature_slope_c_per_min"), 0.0)
    pwm = _num(status.get("current_pwm_percent"), _num(status.get("baseline_pwm_percent"), 0.0))
    bucket = str(status.get("workload_bucket") or "unknown")
    now = int(time.time())

    for key, share in pairs:
        effective = max(0.0, weight * share)
        if effective <= 0:
            continue
        raw = anchors.get(str(key))
        item = raw if isinstance(raw, dict) else {}
        old_support = _num(item.get("support"), 0.0)
        old_error = _num(item.get("ema_abs_error_c"), abs(error))
        old_slope = _num(item.get("ema_abs_slope_c_per_min"), abs(slope))
        old_pwm = _num(item.get("ema_pwm_percent"), pwm)
        alpha = _clamp(effective / max(0.35 + old_support, 0.35), 0.04, 0.30)
        item.update({
            "support": round(min(TRANSIENT_SUPPORT_CAP, old_support + effective), 4),
            "samples": int(_num(item.get("samples"), 0)) + 1,
            "ema_abs_error_c": round(old_error + alpha * (abs(error) - old_error), 3),
            "ema_abs_slope_c_per_min": round(old_slope + alpha * (abs(slope) - old_slope), 3),
            "ema_pwm_percent": round(old_pwm + alpha * (pwm - old_pwm), 2),
            "last_bucket": bucket,
            "last_load_percent": round(load, 1),
            "last_error_c": round(error, 2),
            "last_slope_c_per_min": round(slope, 3),
            "last_pwm_percent": round(pwm, 1),
            "updated_epoch": now,
        })
        anchors[str(key)] = item


def _transient_at_load(target_state: dict[str, Any], load: float) -> tuple[float, int, float]:
    anchors = target_state.get("transient_anchors")
    if not isinstance(anchors, dict) or not anchors:
        return 0.0, 0, 100.0
    items: list[tuple[float, dict[str, Any]]] = []
    for raw_key, raw_item in anchors.items():
        if not isinstance(raw_item, dict) or _num(raw_item.get("support"), 0.0) <= 0:
            continue
        try:
            x = float(raw_key)
        except (TypeError, ValueError):
            continue
        items.append((x, raw_item))
    if not items:
        return 0.0, 0, 100.0
    items.sort(key=lambda pair: pair[0])
    left = None
    right = None
    for x, item in items:
        if x <= load:
            left = (x, item)
        if x >= load and right is None:
            right = (x, item)
    if left is None:
        left = items[0]
    if right is None:
        right = items[-1]
    lx, li = left
    rx, ri = right
    if lx == rx:
        support = _num(li.get("support"), 0.0)
        samples = int(_num(li.get("samples"), 0))
    else:
        frac = _clamp((load - lx) / (rx - lx), 0.0, 1.0)
        support = _num(li.get("support"), 0.0) * (1.0 - frac) + _num(ri.get("support"), 0.0) * frac
        samples = int(round(_num(li.get("samples"), 0.0) * (1.0 - frac) + _num(ri.get("samples"), 0.0) * frac))
    distance = min(abs(load - x) for x, _ in items)
    return support, samples, distance


def _transient_confidence(target_state: dict[str, Any], load: float) -> tuple[int, float, int]:
    support, samples, distance = _transient_at_load(target_state, load)
    if support <= 0:
        return 0, 0.0, 0
    evidence = 1.0 - math.exp(-support / TRANSIENT_SUPPORT_SCALE)
    distance_factor = _clamp(1.0 - distance / 35.0, 0.25, 1.0)
    confidence = int(round(_clamp(TRANSIENT_CONFIDENCE_CAP * evidence * distance_factor, 0.0, TRANSIENT_CONFIDENCE_CAP)))
    return confidence, support, samples


'''
    if "def _transient_observation_weight" not in ai:
        ai = replace_once(ai, anchor, transient_helpers + anchor, "insert transient helpers")

    old_conf = '''    evidence = _clamp(support / 18.0, 0.0, 1.0)\n    distance_factor = _clamp(1.0 - nearest_distance / 45.0, 0.20, 1.0)\n    quality = _clamp(1.0 - dev / 12.0, 0.35, 1.0)\n    confidence = int(round(_clamp(96.0 * evidence * distance_factor * quality, 0.0, 96.0)))\n    source = "interpolation" if lx != rx and lx <= load <= rx else ("anchor" if nearest_distance <= 5.0 else "extrapolation")\n    return prediction, confidence, nearest_distance, source\n'''
    new_conf = '''    evidence = _clamp(support / 18.0, 0.0, 1.0)\n    distance_factor = _clamp(1.0 - nearest_distance / 45.0, 0.20, 1.0)\n    quality = _clamp(1.0 - dev / 12.0, 0.35, 1.0)\n    base_confidence = 96.0 * evidence * distance_factor * quality\n    transient_confidence, _, _ = _transient_confidence(target_state, load)\n    # Dynamic evidence can raise confidence in a sparse range, but it does not\n    # alter the steady-state prediction itself. Repeated bursts are required\n    # before the boost becomes material and the overall cap stays below 96%.\n    residual_room = max(0.0, 96.0 - base_confidence)\n    confidence = int(round(_clamp(base_confidence + residual_room * (transient_confidence / 100.0), 0.0, 96.0)))\n    source = "interpolation" if lx != rx and lx <= load <= rx else ("anchor" if nearest_distance <= 5.0 else "extrapolation")\n    if transient_confidence > 0:\n        source += "+transient"\n    return prediction, confidence, nearest_distance, source\n'''
    ai = replace_once(ai, old_conf, new_conf, "blend transient confidence")

    old_step = '''    obs_weight = _observation_weight(status)\n    if legacy_obs_total != last_seen and obs_weight > 0:\n        candidate = _candidate_pwm(status)\n        _update_anchor(target_state, load, candidate, obs_weight)\n        target_state["last_learning_weight"] = obs_weight\n        target_state["last_candidate_pwm"] = round(candidate, 2)\n        target_state["last_learning_bucket"] = status.get("workload_bucket")\n        target_state["last_learning_epoch"] = int(time.time())\n    target_state["last_legacy_observations_total"] = legacy_obs_total\n\n    global_pred, global_conf, distance, source = _global_prediction(target_state, load)\n'''
    new_step = '''    obs_weight = _observation_weight(status)\n    transient_weight = _transient_observation_weight(status)\n    if legacy_obs_total != last_seen:\n        if obs_weight > 0:\n            candidate = _candidate_pwm(status)\n            _update_anchor(target_state, load, candidate, obs_weight)\n            target_state["last_learning_weight"] = obs_weight\n            target_state["last_candidate_pwm"] = round(candidate, 2)\n            target_state["last_learning_bucket"] = status.get("workload_bucket")\n            target_state["last_learning_epoch"] = int(time.time())\n        if transient_weight > 0:\n            _update_transient_evidence(target_state, load, status, transient_weight)\n            target_state["last_transient_weight"] = transient_weight\n            target_state["last_transient_bucket"] = status.get("workload_bucket")\n            target_state["last_transient_epoch"] = int(time.time())\n    target_state["last_legacy_observations_total"] = legacy_obs_total\n\n    global_pred, global_conf, distance, source = _global_prediction(target_state, load)\n    transient_conf, transient_support, transient_samples = _transient_confidence(target_state, load)\n'''
    ai = replace_once(ai, old_step, new_step, "learn dynamic transient evidence")

    old_progress = '''        _, global_conf, distance, source = _global_prediction(target_state, _bucket_midpoint(bucket))\n        effective = _effective_confidence(\n'''
    new_progress = '''        bucket_load = _bucket_midpoint(bucket)\n        _, global_conf, distance, source = _global_prediction(target_state, bucket_load)\n        transient_conf, transient_support, transient_samples = _transient_confidence(target_state, bucket_load)\n        effective = _effective_confidence(\n'''
    ai = replace_once(ai, old_progress, new_progress, "add transient bucket progress")

    old_item = '''            "transfer_source": source,\n            "transfer_distance_percent": round(distance, 1),\n        })\n'''
    new_item = '''            "transfer_source": source,\n            "transfer_distance_percent": round(distance, 1),\n            "transient_confidence_percent": transient_conf,\n            "transient_support": round(transient_support, 3),\n            "transient_samples": transient_samples,\n        })\n'''
    ai = replace_once(ai, old_item, new_item, "publish transient bucket progress")

    old_status = '''        "transfer_source": source,\n        "transfer_distance_percent": round(distance, 1),\n        "effective_current_bucket_ready": effective_ready,\n'''
    new_status = '''        "transfer_source": source,\n        "transfer_distance_percent": round(distance, 1),\n        "transient_confidence_percent": transient_conf,\n        "transient_support": round(transient_support, 3),\n        "transient_samples": transient_samples,\n        "transient_learning_state": "active" if transient_weight > 0 else "observe",\n        "effective_current_bucket_ready": effective_ready,\n'''
    ai = replace_once(ai, old_status, new_status, "publish current transient diagnostics")

    old_model = '''            "last_learning_weight": _num(target_state.get("last_learning_weight"), 0.0),\n        },\n'''
    new_model = '''            "last_learning_weight": _num(target_state.get("last_learning_weight"), 0.0),\n            "last_transient_weight": _num(target_state.get("last_transient_weight"), 0.0),\n            "transient_anchor_count": len(target_state.get("transient_anchors", {})) if isinstance(target_state.get("transient_anchors"), dict) else 0,\n        },\n'''
    ai = replace_once(ai, old_model, new_model, "publish transient model metadata")

    AI.write_text(ai, encoding="utf-8")

    card = CARD_YAML.read_text(encoding="utf-8")
    needle = '''            / high {{ bp.get('high',{}).get('effective_confidence_percent', bp.get('high',{}).get('confidence_percent',0)) }}%\n            · próg {{ req }} kwal./bucket · pokrycie direct {{ ai.model_coverage_percent | default(0, true) }}% / effective {{ ai.effective_model_coverage_percent | default(ai.model_coverage_percent | default(0, true), true) }}%\n'''
    replacement = '''            / high {{ bp.get('high',{}).get('effective_confidence_percent', bp.get('high',{}).get('confidence_percent',0)) }}%\n            · transient medium {{ bp.get('medium',{}).get('transient_confidence_percent',0) }}%/{{ bp.get('medium',{}).get('transient_samples',0) }}\n            / high {{ bp.get('high',{}).get('transient_confidence_percent',0) }}%/{{ bp.get('high',{}).get('transient_samples',0) }}\n            · próg {{ req }} kwal./bucket · pokrycie direct {{ ai.model_coverage_percent | default(0, true) }}% / effective {{ ai.effective_model_coverage_percent | default(ai.model_coverage_percent | default(0, true), true) }}%\n'''
    card = replace_once(card, needle, replacement, "show transient progress")
    CARD_YAML.write_text(card, encoding="utf-8")
    parsed = yaml.safe_load(card)
    CARD_JSON.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    TEST.write_text(r'''#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "local_apps/sbc5_control_center/ai_cooling_v5.py"
spec = importlib.util.spec_from_file_location("ai_v5_transient_test", path)
assert spec and spec.loader
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

# Transient evidence must raise confidence but must not change the steady PWM
# prediction itself.
target = {
    "anchors": {
        "50": {"mean_pwm": 83.5, "dev_pwm": 2.0, "weight": 0.25},
        "60": {"mean_pwm": 84.0, "dev_pwm": 2.5, "weight": 0.20},
    }
}
pred_before, conf_before, _, _ = mod._global_prediction(target, 55.0)
for _ in range(6):
    mod._update_transient_evidence(target, 55.0, status, weight)
pred_after, conf_after, _, source_after = mod._global_prediction(target, 55.0)
transient_conf, support, samples = mod._transient_confidence(target, 55.0)
assert pred_before == pred_after, (pred_before, pred_after)
assert conf_after > conf_before, (conf_before, conf_after)
assert transient_conf > 0
assert support > 0
assert samples >= 6
assert "+transient" in source_after

# One short burst must not make the sparse medium bucket assist-ready by itself.
effective = mod._effective_confidence(
    direct_conf=24,
    global_conf=conf_after,
    predictor_conf=59,
    observations=273,
    direct_qn=0,
    min_samples=30,
    distance=0.0,
)
assert effective < mod.ASSIST_MIN_EFFECTIVE_CONFIDENCE, effective

# High/medium dynamic samples are useful even outside the old ±6 C steady band.
assert mod._transient_observation_weight({**status, "temperature_error_c": 10.0}) > 0
assert mod._observation_weight({**status, "temperature_error_c": 10.0}) == 0.0
print("AI Cooling v5.1 transient learning: PASS")
''', encoding="utf-8")

    print("Prepared AI Cooling v5.1 transient learning source changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
