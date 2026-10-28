#!/usr/bin/env python3
"""SBC5 AI Cooling v5.1 — conservative transient-response learning.

v5.1 layers dynamic evidence on top of the proven hierarchical v5 learner.
Short medium/high workload bursts can increase confidence that the model has seen
that thermal region, even when the v4 quasi-steady qualifier rejects the sample.

Safety properties:
- transient evidence never increments qualified sample counters;
- transient evidence never changes the steady-state PWM prediction directly;
- one burst cannot make a sparse bucket assist-ready by itself;
- Adaptive PWM, thermal fast/critical paths and sign guards remain authoritative;
- no additional polling loop is created.

3.1.12 observability:
- transient evidence is encoded into the already transported ``transfer_source``
  field, so the legacy shell/relay contract does not gain another parser or poll;
- the token has the compact form ``+transient[c=<confidence>,n=<samples>,s=<support>]``;
- canonical status JSON still exposes the structured transient fields.
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import sys
import time
from typing import Any

TRANSIENT_DYNAMIC_WEIGHT_MAX = 0.32
TRANSIENT_BUCKETS = {"medium", "high"}
TRANSIENT_MIN_BUCKET_AGE_SECONDS = 15.0
TRANSIENT_MAX_ERROR_C = 15.0
TRANSIENT_SUPPORT_CAP = 12.0
TRANSIENT_SUPPORT_SCALE = 0.95
TRANSIENT_CONFIDENCE_CAP = 58.0
POLICY = "hierarchical_continuous_v5_1"


def _base_path() -> Path:
    runtime = Path("/ai_cooling_v5.py")
    if runtime.is_file():
        return runtime
    return Path(__file__).with_name("ai_cooling_v5.py")


def _load_base():
    path = _base_path()
    spec = importlib.util.spec_from_file_location("sbc5_ai_cooling_v5_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load AI Cooling v5 base module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_base()
_original_global_prediction = base._global_prediction
_original_apply = base._apply_hierarchical_step


def _num(value: Any, default: float = 0.0) -> float:
    return base._num(value, default)


def _clamp(value: float, lo: float, hi: float) -> float:
    return base._clamp(value, lo, hi)


def _transient_observation_weight(status: dict[str, Any]) -> float:
    """Small evidence weight for dynamic medium/high response samples."""
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

    step = int(getattr(base, "ANCHOR_STEP_PERCENT", 10))
    lo = int(_clamp(math.floor(load / step) * step, 0, 100))
    hi = int(_clamp(math.ceil(load / step) * step, 0, 100))
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


def _transient_token(target_state: dict[str, Any], load: float) -> str:
    confidence, support, samples = _transient_confidence(target_state, load)
    if confidence <= 0 and samples <= 0:
        return ""
    return f"+transient[c={confidence},n={samples},s={support:.3f}]"


def _global_prediction_v5_1(target_state: dict[str, Any], load: float):
    prediction, base_conf, distance, source = _original_global_prediction(target_state, load)
    transient_conf, _, _ = _transient_confidence(target_state, load)
    if prediction is None or transient_conf <= 0:
        return prediction, base_conf, distance, source
    residual_room = max(0.0, 96.0 - float(base_conf))
    confidence = int(round(_clamp(float(base_conf) + residual_room * (transient_conf / 100.0), 0.0, 96.0)))
    return prediction, confidence, distance, source + _transient_token(target_state, load)


base._global_prediction = _global_prediction_v5_1
base.V5_POLICY = POLICY


def _augment_transient_diagnostics(status: dict[str, Any], target_state: dict[str, Any], load: float, weight: float) -> None:
    transient_conf, support, samples = _transient_confidence(target_state, load)
    status.update({
        "learning_policy": POLICY,
        "transient_learning_state": "active" if weight > 0 else "observe",
        "transient_confidence_percent": transient_conf,
        "transient_support": round(support, 3),
        "transient_samples": samples,
    })
    progress = status.get("bucket_progress")
    if isinstance(progress, dict):
        for bucket in ("idle", "low", "medium", "high"):
            item = progress.get(bucket)
            if not isinstance(item, dict):
                continue
            bucket_load = base._bucket_midpoint(bucket)
            bconf, bsupport, bsamples = _transient_confidence(target_state, bucket_load)
            item["transient_confidence_percent"] = bconf
            item["transient_support"] = round(bsupport, 3)
            item["transient_samples"] = bsamples

    meta = status.get("hierarchical_model")
    if isinstance(meta, dict):
        meta["policy"] = POLICY
        meta["last_transient_weight"] = _num(target_state.get("last_transient_weight"), 0.0)
        anchors = target_state.get("transient_anchors")
        meta["transient_anchor_count"] = len(anchors) if isinstance(anchors, dict) else 0


def _apply_hierarchical_step(model: dict[str, Any], status: dict[str, Any], fields: list[str]):
    model, status, fields = _original_apply(model, status, fields)

    target = _num(status.get("target_temp_c"), 49.0)
    target_key = f"{target:.1f}"
    target_state = base._target_state(model, target_key)
    load = _num(status.get("cpu_load_smoothed_percent"), _num(status.get("cpu_load_percent"), 0.0))
    observations_total = int(_num(status.get("observations_total"), 0))
    last_transient_obs = int(_num(target_state.get("last_transient_observations_total"), -1))
    weight = _transient_observation_weight(status)

    if observations_total != last_transient_obs and weight > 0:
        _update_transient_evidence(target_state, load, status, weight)
        target_state["last_transient_weight"] = weight
        target_state["last_transient_bucket"] = status.get("workload_bucket")
        target_state["last_transient_epoch"] = int(time.time())
    target_state["last_transient_observations_total"] = observations_total

    _augment_transient_diagnostics(status, target_state, load, weight)

    # Keep the 22-field v5 stdout ABI intact. The existing transfer-source field
    # already crosses run_legacy/relay/card, so carry transient observability there.
    if len(fields) >= 21:
        source = str(fields[20] or status.get("transfer_source") or "none")
        token = _transient_token(target_state, load)
        if token and "+transient[" not in source:
            source += token
        fields[20] = source
        status["transfer_source"] = source
    return model, status, fields


base._apply_hierarchical_step = _apply_hierarchical_step


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
