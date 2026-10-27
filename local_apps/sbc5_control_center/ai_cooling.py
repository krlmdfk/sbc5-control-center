#!/usr/bin/env python3
"""Local qualified online learner for SBC5 Control Center Active Cooler.

v2.8.4 keeps Workload Buckets v2 and quasi-steady quality qualification. The evaluator
runs every controller cycle while training observations remain rate-limited, allowing the
rolling temperature/PWM windows to become mathematically complete. A controller hold action is a high-quality diagnostic
signal, not a hard prerequisite. Training requires a stable workload bucket, a
near-target temperature, a low thermal slope and a bounded 30 s PWM window.
The classic Adaptive PWM controller remains authoritative; safety stays in run.sh.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
import time
from pathlib import Path
from typing import Any

SCHEMA = 5
TEMP_DENSITY_STEP_C = 0.25
GRID_DENSITY_SHARE = 0.70
GRID_MIN_OBSERVATIONS_FLOOR = 120
GRID_MIN_QUALIFIED_FLOOR = 30
WORKLOADS = ("idle", "low", "medium", "high")
WORKLOAD_IDLE_MAX = 10.0
WORKLOAD_LOW_MAX = 30.0
WORKLOAD_MEDIUM_MAX = 60.0
WORKLOAD_HYSTERESIS_PERCENT = 5.0
WORKLOAD_WINDOW_SECONDS = 30.0
WORKLOAD_STABLE_SECONDS = 30.0
TRAIN_SAMPLE_INTERVAL_SECONDS = 30.0
QUALIFICATION_POLICY = "quasi_steady_v3"
QUALIFY_STABLE_SECONDS = 30.0
QUALIFY_TEMP_BAND_MIN_C = 1.25 # window mean must stay close to the setpoint
QUALIFY_TEMP_WINDOW_SECONDS = 60.0
QUALIFY_TEMP_WINDOW_MIN_SPAN_SECONDS = 40.0
QUALIFY_TEMP_WINDOW_MIN_POINTS = 4
QUALIFY_TEMP_RANGE_MAX_C = 2.0
QUALIFY_SLOPE_MAX = 0.60       # degC/min from rolling linear regression
QUALIFY_GOLD_SLOPE_MAX = 0.30
QUALIFY_GOLD_TEMP_RANGE_MAX_C = 1.25
QUALIFY_PWM_WINDOW_SECONDS = 30.0
QUALIFY_PWM_RANGE_MAX = 8      # pp; physical slew is allowed while settling
QUALIFY_GOLD_PWM_RANGE_MAX = 5
QUALIFY_STREAK_REQUIRED = 3    # compatibility/diagnostic counter; time gate is authoritative

# 3.1.0 AI Thermal Predictor — observe-only forecast layer.
THERMAL_PREDICTOR_HORIZONS_SECONDS = (30, 60, 120)
THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN = 3.0
THERMAL_PREDICTOR_QUEUE_MAX = 48
THERMAL_PREDICTOR_ERROR_ALPHA = 0.18
THERMAL_PREDICTOR_DAMPING = {30: 0.90, 60: 0.72, 120: 0.52}
THERMAL_SHADOW_MAX_DELTA_PP = 2
THERMAL_SHADOW_MIN_CONFIDENCE = 80
THERMAL_SHADOW_MAX_MAE_C = 1.25
THERMAL_SHADOW_MIN_VALIDATED_PER_HORIZON = 8
THERMAL_SHADOW_NEUTRAL_BAND_C = 0.60
THERMAL_SHADOW_STRONG_BAND_C = 1.80


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _atomic_json(path: Path, payload: Any, *, durable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
            f.flush()
            if durable:
                os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def _num(v: Any, default: float = 0.0) -> float:
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def _cpu_load(telemetry: dict[str, Any]) -> float:
    values = telemetry.get("cpu_core_usage_percent") or []
    if isinstance(values, dict):
        values = list(values.values())
    nums = [_num(v, -1.0) for v in values] if isinstance(values, list) else []
    nums = [v for v in nums if 0.0 <= v <= 100.0]
    if nums:
        return round(sum(nums) / len(nums), 1)
    load1 = _num(telemetry.get("load_1m"), 0.0)
    cores = max(1.0, _num(telemetry.get("cpu_core_count"), 4.0))
    return round(max(0.0, min(100.0, load1 / cores * 100.0)), 1)


def _base_bucket(load: float) -> str:
    if load < WORKLOAD_IDLE_MAX:
        return "idle"
    if load < WORKLOAD_LOW_MAX:
        return "low"
    if load < WORKLOAD_MEDIUM_MAX:
        return "medium"
    return "high"


def _hysteretic_bucket(load: float, previous: str) -> str:
    """Classify smoothed CPU load while preventing boundary chatter."""
    previous = previous if previous in WORKLOADS else _base_bucket(load)
    h = WORKLOAD_HYSTERESIS_PERCENT
    if previous == "idle":
        return "idle" if load < WORKLOAD_IDLE_MAX + h else _base_bucket(load)
    if previous == "low":
        if load < WORKLOAD_IDLE_MAX - h:
            return "idle"
        if load >= WORKLOAD_LOW_MAX + h:
            return _base_bucket(load)
        return "low"
    if previous == "medium":
        if load < WORKLOAD_LOW_MAX - h:
            return _base_bucket(load)
        if load >= WORKLOAD_MEDIUM_MAX + h:
            return "high"
        return "medium"
    if load < WORKLOAD_MEDIUM_MAX - h:
        return _base_bucket(load)
    return "high"


def _update_workload_state(model: dict[str, Any], raw_load: float, now: float) -> tuple[float, str, float, bool]:
    """Return 30 s moving-average load, hysteretic bucket, bucket age and change flag."""
    history = model.get("workload_load_history")
    if not isinstance(history, list):
        history = []
    clean: list[list[float]] = []
    cutoff = now - WORKLOAD_WINDOW_SECONDS
    for item in history:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        ts = _num(item[0], 0.0)
        value = _num(item[1], -1.0)
        if ts >= cutoff and 0.0 <= value <= 100.0:
            clean.append([ts, value])
    clean.append([now, raw_load])
    # Bound state size even if a user configures a very short controller interval.
    clean = clean[-16:]
    smoothed = round(sum(item[1] for item in clean) / max(1, len(clean)), 1)
    previous = str(model.get("workload_bucket") or model.get("last_workload_bucket") or _base_bucket(smoothed))
    bucket = _hysteretic_bucket(smoothed, previous)
    changed = bucket != previous
    since = _num(model.get("workload_bucket_since_epoch"), now)
    if changed or since <= 0 or since > now:
        since = now
    age = max(0.0, now - since)
    model["workload_load_history"] = clean
    model["workload_load_smoothed_percent"] = smoothed
    model["workload_bucket"] = bucket
    model["workload_bucket_since_epoch"] = since
    return smoothed, bucket, age, changed


def _update_pwm_stability(model: dict[str, Any], current: int, now: float) -> tuple[int, float]:
    """Track physical PWM over the qualification window and return range/span."""
    history = model.get("qualification_pwm_history")
    if not isinstance(history, list):
        history = []
    cutoff = now - QUALIFY_PWM_WINDOW_SECONDS
    clean: list[list[float]] = []
    for item in history:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        ts = _num(item[0], 0.0)
        value = _num(item[1], -1.0)
        if ts >= cutoff and 0.0 <= value <= 100.0:
            clean.append([ts, value])
    clean.append([now, float(current)])
    clean = clean[-16:]
    values = [item[1] for item in clean]
    pwm_range = int(round(max(values) - min(values))) if values else 0
    span = max(0.0, now - clean[0][0]) if clean else 0.0
    model["qualification_pwm_history"] = clean
    return pwm_range, span


def _update_temp_stability(model: dict[str, Any], temp: float, now: float) -> tuple[float, float, float, float, int]:
    """Return rolling linear-regression slope, range, span, mean and point count."""
    history = model.get("qualification_temp_history")
    if not isinstance(history, list):
        history = []
    cutoff = now - QUALIFY_TEMP_WINDOW_SECONDS
    clean: list[list[float]] = []
    for item in history:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        ts = _num(item[0], 0.0)
        value = _num(item[1], -273.0)
        if ts >= cutoff and -40.0 <= value <= 150.0:
            clean.append([ts, value])
    clean.append([now, temp])
    clean = clean[-16:]
    values = [item[1] for item in clean]
    span = max(0.0, clean[-1][0] - clean[0][0]) if len(clean) >= 2 else 0.0
    mean_temp = sum(values) / max(1, len(values))
    temp_range = (max(values) - min(values)) if values else 0.0
    slope = 0.0
    if len(clean) >= 3 and span > 0:
        x0 = clean[0][0]
        xs = [item[0] - x0 for item in clean]
        mx = sum(xs) / len(xs)
        my = mean_temp
        den = sum((x - mx) ** 2 for x in xs)
        if den > 0:
            slope = sum((x - mx) * (y - my) for x, y in zip(xs, values)) / den * 60.0
    slope = _clamp(slope, -15.0, 15.0)
    model["qualification_temp_history"] = clean
    return slope, temp_range, span, mean_temp, len(clean)


def _thermal_predictor(model: dict[str, Any], temp: float, slope_c_per_min: float, now: float, window_span: float, window_points: int) -> dict[str, Any]:
    """Observe-only short-horizon thermal forecast with online error scoring.

    The predictor never changes PWM. It reuses the existing temperature window and
    stores only a small bounded forecast queue inside the AI model. Mature forecasts
    are compared with the measured temperature and update an EMA MAE per horizon.
    """
    state = model.get("thermal_predictor")
    if not isinstance(state, dict):
        state = {}
    queue = state.get("queue")
    if not isinstance(queue, list):
        queue = []

    mae = state.get("mae_ema_c")
    if not isinstance(mae, dict):
        mae = {}
    samples = state.get("validated_samples")
    if not isinstance(samples, dict):
        samples = {}
    last_error = state.get("last_error_c")
    if not isinstance(last_error, dict):
        last_error = {}

    pending: list[dict[str, Any]] = []
    for item in queue:
        if not isinstance(item, dict):
            continue
        due = _num(item.get("due_epoch"), 0.0)
        horizon = str(int(_num(item.get("horizon_seconds"), 0)))
        predicted = _num(item.get("predicted_c"), temp)
        if due > 0 and due <= now:
            err = abs(temp - predicted)
            old = _num(mae.get(horizon), err)
            mae[horizon] = round(old + THERMAL_PREDICTOR_ERROR_ALPHA * (err - old), 3)
            last_error[horizon] = round(err, 3)
            samples[horizon] = int(_num(samples.get(horizon), 0)) + 1
        elif due > now - 10.0:
            pending.append(item)

    slope = _clamp(slope_c_per_min, -THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN, THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN)
    forecasts: dict[str, float] = {}
    for horizon in THERMAL_PREDICTOR_HORIZONS_SECONDS:
        damping = THERMAL_PREDICTOR_DAMPING[horizon]
        predicted = temp + slope * (horizon / 60.0) * damping
        predicted = round(_clamp(predicted, -20.0, 100.0), 2)
        forecasts[str(horizon)] = predicted
        pending.append({
            "created_epoch": int(now),
            "due_epoch": int(now + horizon),
            "horizon_seconds": horizon,
            "predicted_c": predicted,
        })

    pending = pending[-THERMAL_PREDICTOR_QUEUE_MAX:]
    span_factor = _clamp(window_span / QUALIFY_TEMP_WINDOW_MIN_SPAN_SECONDS, 0.0, 1.0)
    point_factor = _clamp(window_points / float(QUALIFY_TEMP_WINDOW_MIN_POINTS), 0.0, 1.0)
    maturity = min(1.0, sum(int(_num(samples.get(str(h)), 0)) for h in THERMAL_PREDICTOR_HORIZONS_SECONDS) / 24.0)
    known_errors = [_num(mae.get(str(h)), 0.0) for h in THERMAL_PREDICTOR_HORIZONS_SECONDS if int(_num(samples.get(str(h)), 0)) > 0]
    avg_mae = sum(known_errors) / len(known_errors) if known_errors else None
    # 3.1.4: confidence is a quality score, not only a data-volume score.
    # Prediction error now carries 35% of the result; a mature model with MAE
    # around 2-3 C can no longer advertise >90% confidence. Observe-only remains.
    accuracy_factor = 0.35 if avg_mae is None else _clamp(1.0 - avg_mae / 3.0, 0.0, 1.0)
    confidence = int(round(_clamp(100.0 * (
        0.25 * span_factor + 0.15 * point_factor + 0.25 * maturity + 0.35 * accuracy_factor
    ), 0.0, 97.0)))
    if avg_mae is None:
        quality_state = "learning"
    elif avg_mae <= 0.75:
        quality_state = "excellent"
    elif avg_mae <= 1.25:
        quality_state = "good"
    elif avg_mae <= 2.0:
        quality_state = "fair"
    elif avg_mae <= 3.0:
        quality_state = "weak"
    else:
        quality_state = "poor"

    state = {
        "schema": 1,
        "mode": "observe_only",
        "forecast_30s_c": forecasts["30"],
        "forecast_60s_c": forecasts["60"],
        "forecast_120s_c": forecasts["120"],
        "temperature_c": round(temp, 2),
        "slope_c_per_min": round(slope, 3),
        "confidence_percent": confidence,
        "quality_state": quality_state,
        "mae_ema_c": {k: round(_num(v), 3) for k, v in mae.items()},
        "last_error_c": {k: round(_num(v), 3) for k, v in last_error.items()},
        "validated_samples": {k: int(_num(v)) for k, v in samples.items()},
        "validated_samples_total": sum(int(_num(samples.get(str(h)), 0)) for h in THERMAL_PREDICTOR_HORIZONS_SECONDS),
        "average_mae_c": round(avg_mae, 3) if avg_mae is not None else None,
        "window_span_seconds": int(round(window_span)),
        "window_points": int(window_points),
        "control_output_enabled": False,
        "updated_epoch": int(now),
        "queue": pending,
    }
    model["thermal_predictor"] = state
    public = dict(state)
    public.pop("queue", None)
    return public


def _thermal_shadow_assist(
    predictor: dict[str, Any],
    *,
    target: float,
    baseline: int,
    min_safe: int,
    maximum: int,
    control_mode: str,
    controller_action: str,
) -> dict[str, Any]:
    """Return a bounded hypothetical PWM correction without changing control output.

    Shadow Assist is deliberately non-authoritative. It evaluates the thermal
    forecasts and records what a future predictive controller *would* request.
    Adaptive PWM + AI Cooling remain the only control path and the returned
    suggestion is never applied to ``output_pwm_percent``.
    """
    quality = str(predictor.get("quality_state") or "learning")
    confidence = int(round(_num(predictor.get("confidence_percent"), 0.0)))
    avg_mae = predictor.get("average_mae_c")
    avg_mae_num = _num(avg_mae, 999.0) if avg_mae is not None else 999.0
    samples = predictor.get("validated_samples")
    samples = samples if isinstance(samples, dict) else {}
    per_horizon = {str(h): int(_num(samples.get(str(h)), 0)) for h in THERMAL_PREDICTOR_HORIZONS_SECONDS}

    forecasts = [
        _num(predictor.get("forecast_30s_c"), target),
        _num(predictor.get("forecast_60s_c"), target),
        _num(predictor.get("forecast_120s_c"), target),
    ]
    weighted_forecast = 0.55 * forecasts[0] + 0.30 * forecasts[1] + 0.15 * forecasts[2]
    forecast_error = weighted_forecast - target
    slope = _num(predictor.get("slope_c_per_min"), 0.0)

    suggested_delta = 0
    reason = "near_target"
    if forecast_error >= THERMAL_SHADOW_STRONG_BAND_C:
        suggested_delta = 2
        reason = "forecast_hot_strong"
    elif forecast_error >= THERMAL_SHADOW_NEUTRAL_BAND_C:
        suggested_delta = 1
        reason = "forecast_hot"
    elif forecast_error <= -THERMAL_SHADOW_STRONG_BAND_C and slope <= 0.0:
        suggested_delta = -2
        reason = "forecast_cool_strong"
    elif forecast_error <= -THERMAL_SHADOW_NEUTRAL_BAND_C and slope <= 0.0:
        suggested_delta = -1
        reason = "forecast_cool"
    elif forecast_error < -THERMAL_SHADOW_NEUTRAL_BAND_C:
        reason = "cool_forecast_but_rising"

    suggested_delta = int(_clamp(suggested_delta, -THERMAL_SHADOW_MAX_DELTA_PP, THERMAL_SHADOW_MAX_DELTA_PP))
    suggested_pwm = int(_clamp(baseline + suggested_delta, min_safe, maximum))
    suggested_delta = suggested_pwm - baseline

    gate_reason = "eligible"
    eligible = True
    if control_mode != "automatic":
        eligible = False; gate_reason = "automatic_mode_required"
    elif "safety" in str(controller_action or "").lower():
        eligible = False; gate_reason = "safety_action_active"
    elif quality not in {"good", "excellent"}:
        eligible = False; gate_reason = "quality_below_good"
    elif confidence < THERMAL_SHADOW_MIN_CONFIDENCE:
        eligible = False; gate_reason = "confidence_below_threshold"
    elif avg_mae_num > THERMAL_SHADOW_MAX_MAE_C:
        eligible = False; gate_reason = "mae_above_threshold"
    elif min(per_horizon.values(), default=0) < THERMAL_SHADOW_MIN_VALIDATED_PER_HORIZON:
        eligible = False; gate_reason = "insufficient_validated_forecasts"

    return {
        "mode": "shadow",
        "control_output_enabled": False,
        "eligible": eligible,
        "gate_reason": gate_reason,
        "decision_reason": reason,
        "suggested_delta_pp": suggested_delta,
        "suggested_pwm_percent": suggested_pwm,
        "baseline_pwm_percent": baseline,
        "weighted_forecast_c": round(weighted_forecast, 2),
        "weighted_forecast_error_c": round(forecast_error, 2),
        "max_delta_pp": THERMAL_SHADOW_MAX_DELTA_PP,
        "minimum_confidence_percent": THERMAL_SHADOW_MIN_CONFIDENCE,
        "maximum_mae_c": THERMAL_SHADOW_MAX_MAE_C,
        "minimum_validated_per_horizon": THERMAL_SHADOW_MIN_VALIDATED_PER_HORIZON,
        "validated_per_horizon": per_horizon,
    }


def _controller_hold(action: str) -> bool:
    """Hold is useful quality metadata, but no longer gates learning."""
    action = str(action or "").lower()
    return "hold" in action and "safety" not in action


def _reason_label(reason: str) -> str:
    return {
        "qualified": "zaakceptowana",
        "sampling_interval": "oczekiwanie na kolejną próbkę",
        "stabilizing": "stabilizacja",
        "mode": "tryb AI nie pozwala na naukę",
        "pwm_range": "PWM poza zakresem uczenia",
        "temperature": "temperatura poza pasmem celu",
        "temperature_trend": "trend temperatury poza limitem",
        "temperature_range": "rozrzut temperatury jest zbyt duży",
        "window_building": "budowanie okna jakości",
        "pwm_change": "PWM nie jest stabilne",
        "workload_stabilizing": "bucket obciążenia jeszcze się stabilizuje",
        "controller_action": "historyczny warunek hold",
    }.get(reason, reason or "—")


def _rejection_summary(counts: Any, limit: int = 3) -> str:
    if not isinstance(counts, dict) or not counts:
        return "brak"
    ranked = sorted(((str(k), int(_num(v, 0))) for k, v in counts.items() if int(_num(v, 0)) > 0), key=lambda x: (-x[1], x[0]))
    if not ranked:
        return "brak"
    return " · ".join(f"{_reason_label(k)} {v}" for k, v in ranked[:limit])


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _fresh_model(now: float) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "created_epoch": int(now),
        "observations_total": 0,
        "qualified_samples_total": 0,
        "legacy_samples_total": 0,
        "bins": {},
        "temperature_density": {},
        "workload_load_history": [],
        "workload_load_smoothed_percent": 0.0,
        "workload_bucket": "idle",
        "workload_bucket_since_epoch": now,
        "last_training_sample_epoch": 0,
        "qualification_policy": QUALIFICATION_POLICY,
        "qualification_pwm_history": [],
        "qualification_temp_history": [],
    }


def _migrate_model(raw: Any, now: float) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return _fresh_model(now)
    if raw.get("schema") == SCHEMA:
        model = raw
        model.setdefault("observations_total", 0)
        model.setdefault("qualified_samples_total", 0)
        model.setdefault("legacy_samples_total", 0)
        model.setdefault("bins", {})
        model.setdefault("temperature_density", {})
        model.setdefault("workload_load_history", [])
        model.setdefault("workload_load_smoothed_percent", _num(model.get("last_cpu_load_percent"), 0.0))
        model.setdefault("workload_bucket", str(model.get("last_workload_bucket") or "idle"))
        model.setdefault("workload_bucket_since_epoch", now)
        model.setdefault("last_training_sample_epoch", 0)
        model.setdefault("qualification_pwm_history", [])
        model.setdefault("qualification_temp_history", [])
        if model.get("qualification_policy") != QUALIFICATION_POLICY:
            # Preserve valid learned EMA/qualified samples from the stricter hold policy,
            # but reset policy-specific diagnostics so historical hold rejections do not
            # dominate the new quasi-steady qualification view.
            bins = model.get("bins") if isinstance(model.get("bins"), dict) else {}
            for item in bins.values():
                if isinstance(item, dict):
                    item.pop("rejection_counts", None)
                    item.pop("stable_since_epoch", None)
                    item["stable_streak"] = 0
                    item["last_rejection_reason"] = "policy_migrated"
            model["qualification_pwm_history"] = []
            model["qualification_temp_history"] = []
            model["qualification_policy"] = QUALIFICATION_POLICY
            model["qualification_policy_migrated_epoch"] = int(now)
        return model

    # Workload Buckets v2 changes both bucket boundaries and qualification semantics.
    # Old aggregate bins cannot be redistributed safely because individual samples
    # are unavailable. Keep them as an archive, reset workload learning, and retain
    # temperature-density history because it is independent of workload labels.
    old_schema = int(_num(raw.get("schema"), 0))
    model = _fresh_model(now)
    model["created_epoch"] = int(_num(raw.get("created_epoch"), now))
    model["temperature_density"] = raw.get("temperature_density") if isinstance(raw.get("temperature_density"), dict) else {}
    old_obs = int(_num(raw.get("observations_total"), raw.get("samples_total", 0)))
    old_qual = int(_num(raw.get("qualified_samples_total"), 0))
    model["legacy_samples_total"] = int(_num(raw.get("legacy_samples_total"), 0)) + old_qual
    old_bins = raw.get("bins") if isinstance(raw.get("bins"), dict) else {}
    model["legacy_workload_v1"] = {
        "schema": old_schema,
        "observations_total": old_obs,
        "qualified_samples_total": old_qual,
        "bins": old_bins,
    }
    model["migrated_from_schema"] = old_schema
    model["migrated_epoch"] = int(now)
    model["workload_model_reset_reason"] = "workload_buckets_v2"
    return model

def _bin_confidence(b: dict[str, Any], min_samples: int) -> int:
    qn = int(_num(b.get("qualified_n"), 0))
    if qn <= 0:
        return 0
    sample_factor = min(1.0, qn / float(max(1, min_samples)))
    dev = _num(b.get("ema_dev"), 8.0)
    quality = _clamp(1.0 - dev / 8.0, 0.35, 1.0)
    return int(round(_clamp(sample_factor * (80.0 + 20.0 * quality), 0.0, 100.0)))


def _progress(model: dict[str, Any], target_key: str, min_samples: int) -> dict[str, Any]:
    out: dict[str, Any] = {}
    bins = model.get("bins") or {}
    for workload in WORKLOADS:
        b = bins.get(f"{target_key}|{workload}", {}) if isinstance(bins, dict) else {}
        qn = int(_num(b.get("qualified_n"), 0))
        obs = int(_num(b.get("observations"), 0))
        conf = _bin_confidence(b, min_samples)
        rejection_counts = b.get("rejection_counts") if isinstance(b.get("rejection_counts"), dict) else {}
        out[workload] = {
            "observations": obs,
            "qualified": qn,
            "required": min_samples,
            "confidence_percent": conf,
            "ready": qn >= min_samples and conf >= 70,
            "rejection_counts": rejection_counts,
            "rejection_summary": _rejection_summary(rejection_counts),
        }
    return out


def _density_group(model: dict[str, Any], target_key: str) -> dict[str, Any]:
    all_density = model.setdefault("temperature_density", {})
    if not isinstance(all_density, dict):
        all_density = {}
        model["temperature_density"] = all_density
    group = all_density.setdefault(target_key, {"observations": 0, "qualified": 0, "bins": {}})
    if not isinstance(group, dict):
        group = {"observations": 0, "qualified": 0, "bins": {}}
        all_density[target_key] = group
    group.setdefault("observations", 0)
    group.setdefault("qualified", 0)
    group.setdefault("bins", {})
    return group


def _update_density(model: dict[str, Any], target_key: str, temp: float, qualified: bool) -> None:
    group = _density_group(model, target_key)
    group["observations"] = int(_num(group.get("observations"), 0)) + 1
    if qualified:
        group["qualified"] = int(_num(group.get("qualified"), 0)) + 1
    bucket = round(round(temp / TEMP_DENSITY_STEP_C) * TEMP_DENSITY_STEP_C, 2)
    bins = group.setdefault("bins", {})
    key = f"{bucket:.2f}"
    item = bins.setdefault(key, {"observations": 0, "qualified": 0})
    item["observations"] = int(_num(item.get("observations"), 0)) + 1
    if qualified:
        item["qualified"] = int(_num(item.get("qualified"), 0)) + 1


def _parse_curve_points_csv(raw: str) -> list[float]:
    out: list[float] = []
    for item in str(raw or "").split(","):
        try:
            value = float(item)
        except (TypeError, ValueError):
            continue
        # run.sh normally sends millidegrees; accept Celsius for diagnostics/tests.
        if abs(value) > 200.0:
            value /= 1000.0
        if math.isfinite(value):
            out.append(round(value, 3))
    return sorted(set(out))


def _grid_gap(points: list[float], lo: float, hi: float) -> float | None:
    if hi <= lo:
        return None
    local = [p for p in points if lo <= p <= hi]
    local.extend((lo, hi))
    local = sorted(set(round(x, 3) for x in local))
    if len(local) < 2:
        return None
    return round(max(local[i + 1] - local[i] for i in range(len(local) - 1)), 3)


def _model_coverage(progress: dict[str, Any]) -> tuple[int, list[str]]:
    ready = [name for name in WORKLOADS if bool((progress.get(name) or {}).get("ready"))]
    return int(round(100.0 * len(ready) / len(WORKLOADS))), ready


def _weighted_model_coverage(progress: dict[str, Any]) -> int:
    total = 0
    ready_weight = 0
    for name in WORKLOADS:
        item = progress.get(name) or {}
        obs = int(_num(item.get("observations"), 0))
        total += obs
        if bool(item.get("ready")):
            ready_weight += obs
    return int(round(100.0 * ready_weight / total)) if total > 0 else 0


def _interp(x: float, xs: list[float], ys: list[float]) -> float:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            span = xs[i + 1] - xs[i]
            if span <= 0:
                return ys[i]
            f = (x - xs[i]) / span
            return ys[i] + f * (ys[i + 1] - ys[i])
    return ys[-1]


def _build_applied_grid(target: float, suggestion: dict[str, Any]) -> tuple[list[float], list[float]]:
    dense = []
    for raw in suggestion.get("suggested_points_c") or []:
        try:
            value = round(float(raw), 2)
        except (TypeError, ValueError):
            continue
        if target - 4.0 <= value <= target + 4.0:
            dense.append(value)
    dense = sorted(set(dense))
    # custom1 intentionally remains a 15-point thermal curve. Use at most nine
    # points for the learned operating region and reserve six points for thermal
    # headroom outside it. For mature 0.25 C advice this gives a 2 C-wide dense
    # band around the actual setpoint without sacrificing +2/+4/+6/+10 C safety.
    if len(dense) > 9:
        dense = sorted(sorted(dense, key=lambda x: (abs(x - target), x))[:9])
    outer_priority = [target - 5, target - 3, target + 2, target + 4, target + 6, target + 10,
                      target - 2, target + 3, target - 1.5, target + 1]
    points = list(dense)
    for raw in outer_priority:
        value = round(raw, 2)
        if value not in points:
            points.append(value)
        if len(points) >= 15:
            break
    # Fill any remaining slots from the proven v2.0.3 geometry.
    for off in [-5, -3, -2, -1.5, -1, -0.5, -0.25, 0, 0.5, 1, 2, 3, 4, 6, 10]:
        value = round(target + off, 2)
        if value not in points:
            points.append(value)
        if len(points) >= 15:
            break
    points = sorted(set(points))
    if len(points) > 15:
        # Preserve the chosen dense band and strongest outer safety anchors.
        keep_dense = set(dense)
        outer = [x for x in points if x not in keep_dense]
        outer = sorted(outer, key=lambda x: (0 if x in {round(target-5,2), round(target+10,2), round(target+2,2), round(target+4,2), round(target+6,2)} else 1, abs(x-target)))
        points = sorted([*dense, *outer[:max(0, 15-len(dense))]])
    return [round(x, 2) for x in points[:15]], [round(x, 2) for x in dense]


def _grid_profile_state(path: str, target: float) -> dict[str, Any]:
    raw = _read_json(Path(path), {}) if path else {}
    if not isinstance(raw, dict) or not raw.get("active"):
        return {"active": False}
    try:
        profile_target = float(raw.get("target_temp_c"))
    except (TypeError, ValueError):
        return {"active": False, "reason": "invalid_profile"}
    if abs(profile_target - target) > 0.11:
        return {"active": False, "reason": "target_changed", "profile_target_temp_c": profile_target}
    points = raw.get("points_c") or []
    if not isinstance(points, list) or len(points) != 15:
        return {"active": False, "reason": "invalid_points"}
    return {
        "active": True,
        "target_temp_c": profile_target,
        "region_from_c": raw.get("region_from_c"),
        "region_to_c": raw.get("region_to_c"),
        "step_c": raw.get("step_c"),
        "confidence_percent": raw.get("confidence_percent"),
        "model_coverage_percent": raw.get("model_coverage_percent"),
        "source_workload": raw.get("source_workload"),
        "points_c": points,
        "applied_epoch": raw.get("applied_epoch"),
    }


def _grid_suggestion(
    model: dict[str, Any],
    target_key: str,
    min_samples: int,
    curve_points: list[float],
    progress: dict[str, Any],
    workload: str,
) -> dict[str, Any]:
    group = _density_group(model, target_key)
    obs = int(_num(group.get("observations"), 0))
    qual = int(_num(group.get("qualified"), 0))
    req_obs = max(GRID_MIN_OBSERVATIONS_FLOOR, int(min_samples) * 4)
    req_qual = max(GRID_MIN_QUALIFIED_FLOOR, int(min_samples))
    coverage, ready_workloads = _model_coverage(progress)
    base = {
        "available": False,
        "apply_supported": False,
        "reason": "learning",
        "scope_workload": workload,
        "model_coverage_percent": coverage,
        "ready_workloads": ready_workloads,
        "observations": obs,
        "qualified_samples": qual,
        "required_observations": req_obs,
        "required_qualified_samples": req_qual,
    }
    if obs < req_obs or qual < req_qual:
        return base
    points: list[tuple[float, int]] = []
    for raw_t, item in (group.get("bins") or {}).items():
        try:
            t = float(raw_t)
        except (TypeError, ValueError):
            continue
        n = int(_num((item or {}).get("qualified"), 0)) if isinstance(item, dict) else 0
        if n > 0:
            points.append((t, n))
    points.sort()
    total = sum(n for _, n in points)
    if total <= 0:
        base["reason"] = "no_qualified_density_data"
        return base
    need = max(1, int(math.ceil(total * GRID_DENSITY_SHARE)))
    best = None
    left = 0
    running = 0
    for right, (t_r, n_r) in enumerate(points):
        running += n_r
        while left < right and running - points[left][1] >= need:
            running -= points[left][1]
            left += 1
        if running >= need:
            lo, hi = points[left][0], t_r
            width = hi - lo
            score = (width, abs(((lo + hi) / 2.0) - float(target_key)))
            if best is None or score < best[0]:
                best = (score, lo, hi, running)
    if best is None:
        base["reason"] = "insufficient_distribution"
        return base
    _, lo, hi, covered = best
    lo -= TEMP_DENSITY_STEP_C
    hi += TEMP_DENSITY_STEP_C
    target = float(target_key)
    lo = max(target - 4.0, lo)
    hi = min(target + 4.0, hi)
    if hi - lo < 1.0:
        mid = (lo + hi) / 2.0
        lo, hi = mid - 0.5, mid + 0.5
    span = hi - lo
    concentration = int(round(100.0 * covered / total))
    # Strong, mature concentration earns 0.25 C resolution even for a region up
    # to 3 C wide. This is what turns long-term learning into a real density gain.
    if span <= 3.0 and qual >= req_qual * 4 and concentration >= 70:
        step = 0.25
    elif span <= 1.5 and qual >= req_qual * 2:
        step = 0.25
    elif span <= 3.0:
        step = 0.5
    else:
        step = 0.75
    lo = round(lo / step) * step
    hi = round(hi / step) * step
    if hi <= lo:
        hi = lo + step
    suggested = []
    x = lo
    while x <= hi + 1e-9 and len(suggested) < 13:
        suggested.append(round(x, 2))
        x += step
    confidence = int(round(_clamp(55 + min(20, obs / req_obs * 10) + min(15, qual / req_qual * 8) + concentration * 0.08, 0, 96)))
    current_gap = _grid_gap(curve_points, lo, hi)
    improvement = round((current_gap / step), 2) if current_gap and step > 0 else None
    common = {
        **base,
        "region_from_c": round(lo, 2),
        "region_to_c": round(hi, 2),
        "recommended_step_c": step,
        "suggested_points_c": suggested,
        "concentration_percent": concentration,
        "confidence_percent": confidence,
        "current_max_gap_c": current_gap,
        "density_improvement_factor": improvement,
        "observations": obs,
        "qualified_samples": qual,
    }
    if current_gap is not None and current_gap <= step + 1e-6:
        return {**common, "available": False, "apply_supported": False, "reason": "grid_already_dense"}
    return {
        **common,
        "available": True,
        "apply_supported": True,
        "reason": "operating_region_concentrated",
        "advisory_only": False,
    }

def step(args: argparse.Namespace) -> int:
    now = time.time()
    model_path = Path(args.model)
    status_path = Path(args.status)
    mirror_path = Path(args.mirror) if args.mirror else None
    telemetry = _read_json(Path(args.telemetry), {})
    model = _migrate_model(_read_json(model_path, {}), now)

    temp = args.temp_milli / 1000.0
    target = float(args.target)
    current = int(args.pwm)
    baseline = int(args.baseline)
    min_safe = int(args.min_safe)
    maximum = int(args.maximum)
    assist_limit = max(0, int(args.assist_limit))
    deadband = max(0.1, float(args.deadband))
    min_samples = max(5, int(args.min_samples))
    mode = args.mode
    control_mode = args.control_mode
    controller_action = str(args.controller_action or "unknown")
    raw_load = _cpu_load(telemetry)
    smoothed_load, workload, workload_age, workload_changed = _update_workload_state(model, raw_load, now)
    pmic_power = telemetry.get("pmic_power_w")
    freq = telemetry.get("cpu_frequency_mhz")

    slope, temp_window_range, temp_window_span, temp_window_mean, temp_window_points = _update_temp_stability(model, temp, now)

    target_key = f"{target:.1f}"
    key = f"{target_key}|{workload}"
    bins = model.setdefault("bins", {})
    b = bins.get(key, {}) if isinstance(bins, dict) else {}
    if not isinstance(b, dict):
        b = {}
    b.setdefault("observations", 0)
    b.setdefault("qualified_n", 0)
    b.setdefault("stable_streak", 0)
    error = temp - target

    train_allowed = mode in {"learning", "assist"} and control_mode in {"automatic", "hybrid"}
    valid_operating = min_safe <= current <= maximum
    last_training_sample = _num(model.get("last_training_sample_epoch"), 0.0)
    sample_due = last_training_sample <= 0 or (now - last_training_sample) >= TRAIN_SAMPLE_INTERVAL_SECONDS
    observation_added = False
    if train_allowed and valid_operating and sample_due:
        b["observations"] = int(_num(b.get("observations"), 0)) + 1
        model["observations_total"] = int(_num(model.get("observations_total"), 0)) + 1
        model["last_training_sample_epoch"] = now
        observation_added = True

    qualification_band = max(deadband, QUALIFY_TEMP_BAND_MIN_C)
    window_ready = temp_window_span >= QUALIFY_TEMP_WINDOW_MIN_SPAN_SECONDS and temp_window_points >= QUALIFY_TEMP_WINDOW_MIN_POINTS
    window_error = temp_window_mean - target
    # Current value may move by one sensor quantum while the minute-long operating
    # point remains stable. The window mean is therefore authoritative for quality.
    near_target = abs(window_error) <= qualification_band and abs(error) <= max(2.0, qualification_band * 1.6)
    slope_stable = abs(slope) <= QUALIFY_SLOPE_MAX
    temp_range_stable = temp_window_range <= QUALIFY_TEMP_RANGE_MAX_C
    pwm_window_range, pwm_window_span = _update_pwm_stability(model, current, now)
    pwm_stable = pwm_window_range <= QUALIFY_PWM_RANGE_MAX
    workload_stable = workload_age >= WORKLOAD_STABLE_SECONDS
    controller_hold = _controller_hold(controller_action)

    reject_reasons: list[str] = []
    if not train_allowed:
        reject_reasons.append("mode")
    if not valid_operating:
        reject_reasons.append("pwm_range")
    if not window_ready:
        reject_reasons.append("window_building")
    if not near_target:
        reject_reasons.append("temperature")
    if window_ready and not slope_stable:
        reject_reasons.append("temperature_trend")
    if window_ready and not temp_range_stable:
        reject_reasons.append("temperature_range")
    if not pwm_stable:
        reject_reasons.append("pwm_change")
    if not workload_stable:
        reject_reasons.append("workload_stabilizing")

    stable_candidate = not reject_reasons
    gold_candidate = stable_candidate and abs(window_error) <= 0.75 and abs(slope) <= QUALIFY_GOLD_SLOPE_MAX and temp_window_range <= QUALIFY_GOLD_TEMP_RANGE_MAX_C and pwm_window_range <= QUALIFY_GOLD_PWM_RANGE_MAX
    stable_streak = int(_num(b.get("stable_streak"), 0))
    stable_since = _num(b.get("stable_since_epoch"), 0.0)
    if stable_candidate:
        if workload_changed or stable_since <= 0 or stable_since > now:
            stable_since = now
            stable_streak = 1
        else:
            stable_streak += 1
    else:
        stable_since = 0.0
        stable_streak = 0
    stable_seconds = max(0.0, now - stable_since) if stable_since > 0 else 0.0
    b["stable_streak"] = stable_streak
    b["stable_since_epoch"] = stable_since
    qualified = observation_added and stable_candidate and stable_seconds >= QUALIFY_STABLE_SECONDS
    qualification_tier = ("gold" if qualified and gold_candidate else ("quasi_steady" if qualified else ("candidate" if stable_candidate else "rejected")))
    if qualified:
        rejection_reason = "qualified"
    elif reject_reasons:
        rejection_reason = reject_reasons[0]
    elif not sample_due:
        rejection_reason = "sampling_interval"
    else:
        rejection_reason = "stabilizing"

    if observation_added and not qualified:
        counts = b.setdefault("rejection_counts", {})
        if not isinstance(counts, dict):
            counts = {}
            b["rejection_counts"] = counts
        reasons_to_count = reject_reasons or ["stabilizing"]
        for item in reasons_to_count:
            counts[item] = int(_num(counts.get(item), 0)) + 1

    if qualified:
        qn = int(_num(b.get("qualified_n"), 0))
        # Learn the equilibrium PWM from the minute-long operating point. GOLD
        # samples get full weight; usable quasi-steady samples get a conservative
        # weight so the model can mature without learning transient spikes.
        candidate = current + (0.50 * window_error) + (0.05 * slope)
        candidate = _clamp(candidate, min_safe, maximum)
        quality_weight = 1.0 if qualification_tier == "gold" else 0.55
        alpha_base = 0.25 if qn < 6 else (0.14 if qn < 30 else 0.07)
        alpha = alpha_base * quality_weight
        old = _num(b.get("ema_pwm"), candidate)
        ema = old + alpha * (candidate - old)
        dev_old = _num(b.get("ema_dev"), 0.0 if qn == 0 else abs(candidate - ema))
        dev = dev_old + alpha * (abs(candidate - ema) - dev_old)
        qn += 1
        b.update({
            "qualified_n": qn,
            "ema_pwm": round(ema, 3),
            "ema_dev": round(dev, 3),
            "last_qualified_epoch": int(now),
            "last_qualified_temp_c": round(temp, 2),
            "last_qualified_cpu_load_percent": smoothed_load,
            "last_qualified_cpu_load_raw_percent": raw_load,
            "last_qualified_pwm_percent": current,
            "last_qualified_controller_hold": controller_hold,
            "last_qualified_tier": qualification_tier,
            "last_qualified_weight": round(quality_weight, 2),
            "last_qualified_window_mean_c": round(temp_window_mean, 2),
            "last_qualified_window_range_c": round(temp_window_range, 2),
        })
        model["qualified_samples_total"] = int(_num(model.get("qualified_samples_total"), 0)) + 1

    b.update({
        "last_evaluation_epoch": int(now),
        "last_temp_c": round(temp, 2),
        "last_cpu_load_percent": smoothed_load,
        "last_cpu_load_raw_percent": raw_load,
        "last_pwm_percent": current,
        "last_rejection_reason": rejection_reason,
    })
    if observation_added:
        b["last_observation_epoch"] = int(now)
    bins[key] = b

    qn = int(_num(b.get("qualified_n"), 0))
    if qn > 0:
        prediction = int(round(_num(b.get("ema_pwm"), baseline)))
    else:
        prediction = baseline
    prediction = int(_clamp(prediction, min_safe, maximum))
    confidence = _bin_confidence(b, min_samples)
    ready = qn >= min_samples and confidence >= 70

    output = baseline
    correction = 0
    ai_state = "disabled"
    reason = "disabled"
    if mode == "learning":
        ai_state = "ready" if ready else "learning"
        reason = "qualified_learning" if qualified else "observe_only"
    elif mode == "assist":
        if control_mode != "automatic":
            ai_state = "learning"
            reason = "assist_only_in_automatic"
        elif not ready:
            ai_state = "learning"
            reason = "insufficient_qualified_samples"
        elif abs(error) > 4.0:
            ai_state = "ready"
            reason = "outside_assist_window"
        else:
            bounded_target = int(_clamp(prediction, baseline - assist_limit, baseline + assist_limit))
            if error > deadband and bounded_target < baseline:
                bounded_target = baseline
            elif error < -deadband and bounded_target > baseline:
                bounded_target = baseline
            delta = int(_clamp(bounded_target - baseline, -2, 2))
            output = int(_clamp(baseline + delta, min_safe, maximum))
            correction = output - baseline
            ai_state = "assist"
            reason = "model_nudge" if correction else "model_agrees"

    if observation_added:
        _update_density(model, target_key, temp, qualified)
    progress = _progress(model, target_key, min_samples)
    curve_points = _parse_curve_points_csv(args.curve_points_csv)
    grid_application = _grid_profile_state(args.grid_profile, target)
    grid_suggestion = _grid_suggestion(model, target_key, min_samples, curve_points, progress, workload)
    if grid_application.get("active"):
        grid_suggestion = {**grid_suggestion, "available": False, "apply_supported": False, "reason": "grid_applied"}
    thermal_predictor = _thermal_predictor(model, temp, slope, now, temp_window_span, temp_window_points)
    thermal_shadow = _thermal_shadow_assist(
        thermal_predictor,
        target=target, baseline=baseline, min_safe=min_safe, maximum=maximum,
        control_mode=control_mode, controller_action=controller_action,
    )
    thermal_predictor["shadow_assist"] = thermal_shadow
    # Shadow Assist is telemetry only. Do not mutate `output`, `correction` or the
    # physical controller target from this block.
    status = {
        "schema": SCHEMA,
        "thermal_predictor": thermal_predictor,
        "state": ai_state,
        "mode": mode,
        "reason": reason,
        "target_temp_c": round(target, 2),
        "temperature_c": round(temp, 2),
        "temperature_error_c": round(error, 2),
        "temperature_slope_c_per_min": round(slope, 2),
        "temperature_window_mean_c": round(temp_window_mean, 2),
        "temperature_window_range_c": round(temp_window_range, 2),
        "temperature_window_span_seconds": int(round(temp_window_span)),
        "temperature_window_points": temp_window_points,
        "cpu_load_percent": raw_load,
        "cpu_load_raw_percent": raw_load,
        "cpu_load_smoothed_percent": smoothed_load,
        "workload_bucket": workload,
        "workload_bucket_age_seconds": int(round(workload_age)),
        "workload_bucket_stable": workload_stable,
        "workload_window_seconds": int(WORKLOAD_WINDOW_SECONDS),
        "workload_hysteresis_percent": WORKLOAD_HYSTERESIS_PERCENT,
        "workload_thresholds_percent": {
            "idle_max": WORKLOAD_IDLE_MAX,
            "low_max": WORKLOAD_LOW_MAX,
            "medium_max": WORKLOAD_MEDIUM_MAX,
        },
        "controller_action": controller_action,
        "controller_hold": controller_hold,
        "qualification_policy": QUALIFICATION_POLICY,
        "qualification_tier": qualification_tier,
        "current_pwm_percent": current,
        "pwm_range_30s_percent": pwm_window_range,
        "pwm_window_span_seconds": int(round(pwm_window_span)),
        "pmic_power_w": pmic_power,
        "cpu_frequency_mhz": freq,
        "observations_total": int(_num(model.get("observations_total"), 0)),
        "qualified_samples_total": int(_num(model.get("qualified_samples_total"), 0)),
        "legacy_samples_total": int(_num(model.get("legacy_samples_total"), 0)),
        "bin_observations": int(_num(b.get("observations"), 0)),
        "bin_qualified_samples": qn,
        "qualified_sample": qualified,
        "qualification_state": "qualified" if qualified else ("stabilizing" if stable_candidate else "rejected"),
        "qualification_reason": rejection_reason,
        "qualification_reason_label": _reason_label(rejection_reason),
        "qualification_rejection_counts": b.get("rejection_counts", {}) if isinstance(b.get("rejection_counts"), dict) else {},
        "qualification_rejection_summary": _rejection_summary(b.get("rejection_counts", {})),
        "stable_streak": stable_streak,
        "stable_streak_required": QUALIFY_STREAK_REQUIRED,
        "stable_seconds": int(round(stable_seconds)),
        "stable_seconds_required": int(QUALIFY_STABLE_SECONDS),
        "training_sample_due": sample_due,
        "training_sample_interval_seconds": int(TRAIN_SAMPLE_INTERVAL_SECONDS),
        "qualification_limits": {
            "temperature_band_c": qualification_band,
            "slope_abs_max_c_per_min": QUALIFY_SLOPE_MAX,
            "temperature_range_max_c": QUALIFY_TEMP_RANGE_MAX_C,
            "temperature_window_seconds": QUALIFY_TEMP_WINDOW_SECONDS,
            "temperature_window_min_span_seconds": QUALIFY_TEMP_WINDOW_MIN_SPAN_SECONDS,
            "temperature_window_min_points": QUALIFY_TEMP_WINDOW_MIN_POINTS,
            "pwm_range_max_percent": QUALIFY_PWM_RANGE_MAX,
            "pwm_window_seconds": QUALIFY_PWM_WINDOW_SECONDS,
            "workload_window_seconds": WORKLOAD_WINDOW_SECONDS,
            "workload_stable_seconds": WORKLOAD_STABLE_SECONDS,
            "workload_hysteresis_percent": WORKLOAD_HYSTERESIS_PERCENT,
        },
        "confidence_percent": confidence,
        "prediction_pwm_percent": prediction if qn > 0 else None,
        "prediction_available": qn > 0,
        "baseline_pwm_percent": baseline,
        "output_pwm_percent": output,
        "correction_pwm_percent": correction,
        "assist_limit_percent": assist_limit,
        "min_samples": min_samples,
        "model_key": key,
        "learned_bins": sum(1 for x in bins.values() if isinstance(x, dict) and int(_num(x.get("qualified_n"), 0)) > 0),
        "bucket_progress": progress,
        "model_coverage_percent": _model_coverage(progress)[0],
        "used_model_coverage_percent": _weighted_model_coverage(progress),
        "current_bucket_ready": bool((progress.get(workload) or {}).get("ready")),
        "grid_suggestion": grid_suggestion,
        "grid_application": grid_application,
        "updated_epoch": int(now),
    }
    model.update({
        "last_epoch": now,
        "last_temp_c": temp,
        "last_pwm": current,
        "last_cpu_load_percent": smoothed_load,
        "last_cpu_load_raw_percent": raw_load,
        "last_workload_bucket": workload,
        "last_key": key,
        "last_prediction_pwm": prediction,
        "updated_epoch": int(now),
    })
    last_durable = _num(model.get("last_durable_checkpoint_epoch"), 0.0)
    durable_checkpoint = qualified or last_durable <= 0 or (now - last_durable) >= 60.0
    if durable_checkpoint:
        model["last_durable_checkpoint_epoch"] = int(now)
    last_mirror = _num(model.get("last_status_mirror_epoch"), 0.0)
    mirror_due = qualified or last_mirror <= 0 or (now - last_mirror) >= 30.0
    if mirror_due:
        model["last_status_mirror_epoch"] = int(now)
    _atomic_json(model_path, model, durable=durable_checkpoint)
    _atomic_json(status_path, status, durable=False)
    if mirror_path and mirror_due:
        _atomic_json(mirror_path, status, durable=False)

    print(
        f"{output}\t{ai_state}\t{reason}\t{confidence}\t{prediction}\t{qn}\t{correction}\t{workload}"
        f"\t{int(status['observations_total'])}\t{int(status['bin_observations'])}\t{int(status['qualified_samples_total'])}"
        f"\t{1 if qualified else 0}\t{rejection_reason}\t{stable_streak}"
    )
    return 0



def apply_grid(args: argparse.Namespace) -> int:
    status = _read_json(Path(args.status), {})
    suggestion = status.get("grid_suggestion") if isinstance(status, dict) else None
    if not isinstance(suggestion, dict) or not suggestion.get("available") or not suggestion.get("apply_supported"):
        print("no_actionable_suggestion")
        return 2
    target = float(args.target)
    if abs(_num(status.get("target_temp_c"), target) - target) > 0.11:
        print("target_mismatch")
        return 3
    existing = _grid_profile_state(args.profile, target)
    if existing.get("active"):
        print("grid_already_applied")
        return 6
    confidence = int(_num(suggestion.get("confidence_percent"), 0))
    if confidence < int(args.min_confidence):
        print("confidence_too_low")
        return 4
    points, dense_points = _build_applied_grid(target, suggestion)
    if len(points) != 15 or len(dense_points) < 2 or any(points[i] >= points[i + 1] for i in range(14)):
        print("invalid_generated_grid")
        return 5
    payload = {
        "schema": 1,
        "active": True,
        "target_temp_c": round(target, 2),
        "region_from_c": min(dense_points),
        "region_to_c": max(dense_points),
        "step_c": suggestion.get("recommended_step_c"),
        "advisor_region_from_c": suggestion.get("region_from_c"),
        "advisor_region_to_c": suggestion.get("region_to_c"),
        "dense_points_c": dense_points,
        "confidence_percent": confidence,
        "concentration_percent": suggestion.get("concentration_percent"),
        "model_coverage_percent": suggestion.get("model_coverage_percent"),
        "source_workload": suggestion.get("scope_workload") or status.get("workload_bucket"),
        "points_c": points,
        "applied_epoch": int(time.time()),
    }
    _atomic_json(Path(args.profile), payload, durable=True)
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0


def clear_grid(args: argparse.Namespace) -> int:
    try:
        Path(args.profile).unlink()
    except FileNotFoundError:
        pass
    print("cleared")
    return 0


def render_grid(args: argparse.Namespace) -> int:
    profile = _read_json(Path(args.profile), {})
    if not isinstance(profile, dict) or not profile.get("active"):
        return 2
    target = float(args.target)
    if abs(_num(profile.get("target_temp_c"), target) - target) > 0.11:
        return 3
    points = profile.get("points_c") or []
    if not isinstance(points, list) or len(points) != 15:
        return 4
    try:
        points = [float(x) for x in points]
    except (TypeError, ValueError):
        return 4
    if any(points[i] >= points[i + 1] for i in range(14)):
        return 4
    hd, ho = float(args.hd), float(args.ho)
    pmin, ptgt, pmax = float(args.pmin), float(args.ptgt), float(args.pmax)
    lo = _num(profile.get("region_from_c"), target - 1.5)
    hi = _num(profile.get("region_to_c"), target + 1.5)
    pre_x = [-5, -3, -2, -1.5, -1, -0.5, -0.25, 0]
    pre_y = [0, 0, 0, 0.05, 0.15, 0.35, 0.65, 1.0]
    post_x = [0, 0.5, 1, 2, 3, 4, 6, 10]
    post_y = [0, 0.05, 0.10, 0.18, 0.27, 0.36, 0.58, 1.0]
    for i, t in enumerate(points, 1):
        off = t - target
        if off <= 0:
            frac = _interp(off, pre_x, pre_y)
            pct = pmin + (ptgt - pmin) * frac
        else:
            frac = _interp(off, post_x, post_y)
            pct = ptgt + (pmax - ptgt) * frac
        pct = _clamp(pct, 0, 100)
        raw = int(round(pct * 255 / 100.0))
        hyst = hd if (lo <= t <= hi or abs(off) <= 1.5) else ho
        tm = int(round(t * 1000))
        hm = int(round(hyst * 1000))
        print(f"{i}|{tm}|{hm}|{raw}|{t:.2f}")
    return 0


def reset(args: argparse.Namespace) -> int:
    for raw in (args.model, args.status, args.mirror):
        if not raw:
            continue
        try:
            Path(raw).unlink()
        except FileNotFoundError:
            pass
    print("reset")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("step")
    s.add_argument("--model", required=True)
    s.add_argument("--status", required=True)
    s.add_argument("--mirror", default="")
    s.add_argument("--telemetry", required=True)
    s.add_argument("--mode", choices=("disabled", "learning", "assist"), required=True)
    s.add_argument("--control-mode", choices=("automatic", "hybrid", "manual"), required=True)
    s.add_argument("--controller-action", default="unknown")
    s.add_argument("--temp-milli", type=int, required=True)
    s.add_argument("--target", type=float, required=True)
    s.add_argument("--pwm", type=int, required=True)
    s.add_argument("--baseline", type=int, required=True)
    s.add_argument("--min-safe", type=int, required=True)
    s.add_argument("--maximum", type=int, required=True)
    s.add_argument("--assist-limit", type=int, required=True)
    s.add_argument("--deadband", type=float, required=True)
    s.add_argument("--min-samples", type=int, required=True)
    s.add_argument("--grid-profile", default="")
    s.add_argument("--curve-points-csv", default="")
    s.set_defaults(func=step)
    a = sub.add_parser("apply-grid")
    a.add_argument("--status", required=True)
    a.add_argument("--profile", required=True)
    a.add_argument("--target", type=float, required=True)
    a.add_argument("--min-confidence", type=int, default=75)
    a.set_defaults(func=apply_grid)
    c = sub.add_parser("clear-grid")
    c.add_argument("--profile", required=True)
    c.set_defaults(func=clear_grid)
    g = sub.add_parser("render-grid")
    g.add_argument("--profile", required=True)
    g.add_argument("--target", type=float, required=True)
    g.add_argument("--hd", type=float, required=True)
    g.add_argument("--ho", type=float, required=True)
    g.add_argument("--pmin", type=float, required=True)
    g.add_argument("--ptgt", type=float, required=True)
    g.add_argument("--pmax", type=float, required=True)
    g.set_defaults(func=render_grid)
    r = sub.add_parser("reset")
    r.add_argument("--model", required=True)
    r.add_argument("--status", required=True)
    r.add_argument("--mirror", default="")
    r.set_defaults(func=reset)
    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
