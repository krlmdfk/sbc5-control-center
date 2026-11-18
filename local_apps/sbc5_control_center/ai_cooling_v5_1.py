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

3.1.13 diagnostics hardening:
- ``direct_confidence_percent`` is normalized to 0 whenever the current bucket has
  zero qualified samples, preventing effective/transfer confidence from being
  presented as direct model maturity;
- direct prediction is hidden for a bucket with zero qualified samples;
- transient structured diagnostics remain independent from this normalization.
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


# 3.2.9: independent *observational* quality for short medium/high bursts.
# These samples describe measured thermal response; they do NOT train the
# quasi-steady equilibrium EMA, increment bin_qualified_samples, change model
# confidence/assist readiness, or produce actuator commands.
DYNAMIC_MIN_PAIR_SECONDS = 20.0
DYNAMIC_MAX_PAIR_SECONDS = 120.0
DYNAMIC_MAX_TEMP_C = 65.0
DYNAMIC_MAX_ABS_RATE_C_PER_MIN = 8.0
DYNAMIC_MAX_PWM_DELTA_PP = 18.0
DYNAMIC_MAX_LOAD_DELTA_PP = 16.0
DYNAMIC_MIN_DELTA_TEMP_C = 0.15
DYNAMIC_MAX_TREND_DISAGREEMENT_C_PER_MIN = 4.0
DYNAMIC_REASONS = (
    "window_building", "bucket_changed", "load_change", "pwm_change",
    "temperature_range", "temperature_trend", "sensor_or_trend_disagreement",
    "no_temperature_response", "mode", "unsafe_action",
)


def _dynamic_quality_step(
    target_state: dict[str, Any], status: dict[str, Any],
    observations_total: int, now: float,
) -> dict[str, Any]:
    """Validate measured temperature response for a *pair* of observations.

    Counter is independent of steady-state qualified_n. Evidence is descriptive
    only and must never feed the PWM prediction or confidence.
    """
    state = target_state.setdefault("dynamic_quality_v1", {})
    if not isinstance(state, dict):
        state = {}
        target_state["dynamic_quality_v1"] = state
    bins = state.setdefault("bins", {})
    if not isinstance(bins, dict):
        bins = {}
        state["bins"] = bins
    bucket = str(status.get("workload_bucket") or "unknown")
    entry = bins.setdefault(bucket, {})
    if not isinstance(entry, dict):
        entry = {}
        bins[bucket] = entry
    entry.setdefault("validated_pairs", 0)
    entry.setdefault("rejection_counts", {})
    entry.setdefault("response_warming", 0)
    entry.setdefault("response_cooling", 0)
    entry.setdefault("temperature_rate_ema_c_per_min", 0.0)

    result = {
        "policy": "dynamic_response_observe_only_v1",
        "bucket": bucket,
        "validated_pairs": int(_num(entry.get("validated_pairs"), 0)),
        "warming_pairs": int(_num(entry.get("response_warming"), 0)),
        "cooling_pairs": int(_num(entry.get("response_cooling"), 0)),
        "last_reason": str(entry.get("last_reason") or "window_building"),
        "rejection_counts": dict(entry.get("rejection_counts") or {}),
        "qualified_sample": False,
        "control_output_enabled": False,
        "independent_of_steady_samples": True,
        "temperature_rate_ema_c_per_min": _num(entry.get("temperature_rate_ema_c_per_min"), 0.0),
    }
    # Legacy samples are recorded at 30s intervals. Don't add multiple
    # "validated" samples on evaluator/relay cycles that reuse an observation.
    if observations_total <= int(_num(state.get("last_observations_total"), -1)):
        return result
    state["last_observations_total"] = observations_total
    if bucket not in TRANSIENT_BUCKETS:
        # Clear the pair on exit; do not compare a new morning's burst with
        # yesterday's observation from a different workload regime.
        state["previous"] = None
        return result
    if str(status.get("mode")) not in {"learning", "assist"}:
        state["previous"] = None
        result["last_reason"] = "mode"
        return result

    candidate = {
        "time": float(now),
        "bucket": bucket,
        "load": _num(status.get("cpu_load_smoothed_percent"), -1.0),
        "temperature": _num(status.get("temperature_c"), -273.0),
        "pwm": _num(status.get("current_pwm_percent"), -1.0),
    }
    previous = state.get("previous")
    state["previous"] = candidate
    reasons = []
    if not isinstance(previous, dict):
        reasons.append("window_building")
    elif str(previous.get("bucket")) != bucket:
        reasons.append("bucket_changed")
    else:
        dt = now - _num(previous.get("time"), now)
        if not DYNAMIC_MIN_PAIR_SECONDS <= dt <= DYNAMIC_MAX_PAIR_SECONDS:
            reasons.append("window_building")
        if abs(candidate["load"] - _num(previous.get("load"))) > DYNAMIC_MAX_LOAD_DELTA_PP:
            reasons.append("load_change")
        if abs(candidate["pwm"] - _num(previous.get("pwm"))) > DYNAMIC_MAX_PWM_DELTA_PP:
            reasons.append("pwm_change")
        older_temp = _num(previous.get("temperature"), -273.0)
        if not (0.0 < candidate["temperature"] < DYNAMIC_MAX_TEMP_C and
                0.0 < older_temp < DYNAMIC_MAX_TEMP_C):
            reasons.append("temperature_range")
        if dt > 0:
            rate = 60.0 * (candidate["temperature"] - older_temp) / dt
            if abs(rate) > DYNAMIC_MAX_ABS_RATE_C_PER_MIN:
                reasons.append("temperature_trend")
            # The rolling 60-second estimate is independent support that the
            # paired readings represent an actual heating/cooling response.
            rolling = _num(status.get("temperature_slope_c_per_min"), 99.0)
            if (not math.isfinite(rolling) or
                    abs(rolling - rate) > DYNAMIC_MAX_TREND_DISAGREEMENT_C_PER_MIN):
                reasons.append("sensor_or_trend_disagreement")
            if abs(candidate["temperature"] - older_temp) < DYNAMIC_MIN_DELTA_TEMP_C:
                reasons.append("no_temperature_response")
    action = str(status.get("controller_action") or "")
    if any(token in action for token in ("safety_max", "emergency", "sensor_invalid", "fan_fault")):
        reasons.append("unsafe_action")
    if not 0 <= candidate["load"] <= 100 or not 0 <= candidate["pwm"] <= 100:
        reasons.append("load_change")

    # Count all failed gates, not just the first priority reason; existing
    # legacy qualifier and its 0/30 maturity counter remain unchanged.
    if reasons:
        counts = entry.setdefault("rejection_counts", {})
        for reason in dict.fromkeys(reasons):
            counts[reason] = int(_num(counts.get(reason), 0)) + 1
        entry["last_reason"] = reasons[0]
    else:
        rate = 60.0 * (candidate["temperature"] - older_temp) / dt
        entry["validated_pairs"] = int(_num(entry.get("validated_pairs"), 0)) + 1
        if rate > 0:
            entry["response_warming"] = int(_num(entry.get("response_warming"), 0)) + 1
        else:
            entry["response_cooling"] = int(_num(entry.get("response_cooling"), 0)) + 1
        old_rate = _num(entry.get("temperature_rate_ema_c_per_min"), rate)
        entry["temperature_rate_ema_c_per_min"] = round(0.2 * rate + 0.8 * old_rate, 3)
        entry["last_reason"] = "validated"
        entry["last_validated_epoch"] = int(now)
        result["qualified_sample"] = True

    result.update({
        "validated_pairs": int(_num(entry.get("validated_pairs"), 0)),
        "warming_pairs": int(_num(entry.get("response_warming"), 0)),
        "cooling_pairs": int(_num(entry.get("response_cooling"), 0)),
        "last_reason": entry["last_reason"],
        "rejection_counts": dict(entry.get("rejection_counts") or {}),
        "temperature_rate_ema_c_per_min": _num(entry.get("temperature_rate_ema_c_per_min"), 0.0),
    })
    return result


def _normalize_direct_diagnostics(status: dict[str, Any], fields: list[str]) -> None:
    """Keep direct diagnostics tied strictly to direct qualified evidence.

    v4 defines direct confidence from ``qualified_n`` and therefore a bucket with
    zero qualified samples must never expose a non-zero direct confidence. This
    normalization is presentation/diagnostics only; it does not alter effective
    confidence, global transfer, transient learning, or physical PWM control.
    """
    qn = int(_num(status.get("bin_qualified_samples"), 0))
    if qn > 0:
        return
    status["direct_confidence_percent"] = 0
    status["direct_prediction_pwm_percent"] = None
    status["direct_model_maturity_percent"] = 0
    status["direct_blend_percent"] = 0
    if len(fields) >= 18:
        fields[14] = "0"
        fields[17] = "-1"


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
    dynamic = _dynamic_quality_step(target_state, status, observations_total, time.time())
    status["dynamic_quality"] = dynamic
    # Keep the legacy direct 0/30 counter untouched: it means steady-state
    # quality and must not be repurposed as dynamic response maturity.
    _normalize_direct_diagnostics(status, fields)

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
