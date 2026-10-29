#!/usr/bin/env python3
"""SBC5 Thermal Predictor v3.1 — path-aware, observe-only thermal forecasting.

The predictor has no physical control authority.  It forecasts CPU temperature and
measures its own quality while keeping model error separate from changing runtime
conditions.  Forecasts are validated at their exact +30/+60/+120 second due time
using interpolated temperature samples instead of the temperature of a later poll.
"""
from __future__ import annotations

import math
from statistics import median
from typing import Any

THERMAL_PREDICTOR_HORIZONS_SECONDS = (30, 60, 120)
THERMAL_PREDICTOR_SCHEMA = 4
THERMAL_PREDICTOR_ALGORITHM = "path_aware_robust_slope_v3_1"
THERMAL_PREDICTOR_QUEUE_MAX = 72
THERMAL_PREDICTOR_ERROR_ALPHA = 0.16
THERMAL_PREDICTOR_BIAS_ALPHA = 0.10
THERMAL_PREDICTOR_MAX_BIAS_C = 1.5
THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN = 4.0
THERMAL_PREDICTOR_DAMPING = {30: 0.92, 60: 0.70, 120: 0.46}
THERMAL_PREDICTOR_TARGET_ANCHOR = {30: 0.07, 60: 0.16, 120: 0.30}
THERMAL_PREDICTOR_ACCURACY_TARGET_C = {30: 1.0, 60: 1.5, 120: 2.5}
THERMAL_PREDICTOR_HISTORY_SECONDS = 180.0
THERMAL_PREDICTOR_MAX_INTERPOLATION_GAP_SECONDS = 30.0
THERMAL_PREDICTOR_MAX_CONTEXT_GAP_SECONDS = 35.0
_FAST_WINDOW_SECONDS = 25.0
_SLOW_WINDOW_SECONDS = 75.0
_CONTEXT_LOAD_LIMIT = {30: 18.0, 60: 22.0, 120: 28.0}
_CONTEXT_PWM_LIMIT = {30: 20.0, 60: 26.0, 120: 35.0}
_HORIZON_WEIGHTS = {30: 0.50, 60: 0.35, 120: 0.15}
_SLOPE_FAST_WEIGHT = {30: 0.72, 60: 0.48, 120: 0.28}
_CONTEXT_REJECTION_REASONS = {"bucket_changed", "target_changed", "load_shift", "pwm_shift"}


def _num(value: Any, default: float = 0.0) -> float:
    try:
        x = float(value)
        return x if math.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _ema(old: Any, new: float, alpha: float) -> float:
    old_num = _num(old, new)
    return old_num + alpha * (new - old_num)


def _robust_slope(
    history: list[list[float]], now: float, window: float, fallback: float
) -> tuple[float, float, int]:
    """Return a Theil-Sen style median slope, robust to isolated sensor spikes."""
    cutoff = now - window
    pts = [(float(ts), float(temp)) for ts, temp in history if float(ts) >= cutoff]
    if len(pts) < 3:
        return fallback, 0.0, len(pts)
    span = pts[-1][0] - pts[0][0]
    if span < min(8.0, window * 0.35):
        return fallback, span, len(pts)
    slopes: list[float] = []
    for i, (ts0, temp0) in enumerate(pts[:-1]):
        for ts1, temp1 in pts[i + 1 :]:
            dt = ts1 - ts0
            if dt >= 2.0:
                slopes.append((temp1 - temp0) / dt * 60.0)
    if not slopes:
        return fallback, span, len(pts)
    slope = float(median(slopes))
    return (
        _clamp(
            slope,
            -THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN,
            THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN,
        ),
        span,
        len(pts),
    )


def _append_temperature(history: Any, now: float, temp: float) -> list[list[float]]:
    cutoff = now - THERMAL_PREDICTOR_HISTORY_SECONDS
    clean: list[list[float]] = []
    if isinstance(history, list):
        for item in history:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            ts, value = _num(item[0], 0.0), _num(item[1], -273.0)
            if ts >= cutoff and -40.0 <= value <= 150.0:
                if clean and abs(clean[-1][0] - ts) < 0.001:
                    clean[-1] = [ts, value]
                else:
                    clean.append([ts, value])
    if clean and abs(clean[-1][0] - now) < 0.001:
        clean[-1] = [float(now), float(temp)]
    else:
        clean.append([float(now), float(temp)])
    return clean[-96:]


def _temperature_at(
    history: list[list[float]], due_epoch: float
) -> tuple[float | None, float | None, str]:
    """Interpolate temperature at the exact forecast due time."""
    before: tuple[float, float] | None = None
    after: tuple[float, float] | None = None
    for item in history:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            continue
        ts, value = _num(item[0], 0.0), _num(item[1], -273.0)
        if abs(ts - due_epoch) < 0.001:
            return value, 0.0, "exact"
        if ts < due_epoch and (before is None or ts > before[0]):
            before = (ts, value)
        elif ts > due_epoch and (after is None or ts < after[0]):
            after = (ts, value)
    if before is None or after is None:
        return None, None, "missing_bracket"
    gap = after[0] - before[0]
    if gap <= 0.0 or gap > THERMAL_PREDICTOR_MAX_INTERPOLATION_GAP_SECONDS:
        return None, gap, "interpolation_gap"
    ratio = (due_epoch - before[0]) / gap
    actual = before[1] + (after[1] - before[1]) * ratio
    return actual, gap, "interpolated"


def _context(model: dict[str, Any], state: dict[str, Any], target: float) -> dict[str, Any]:
    bucket = str(model.get("workload_bucket") or model.get("last_workload_bucket") or "low")
    if bucket not in {"idle", "low", "medium", "high"}:
        bucket = "low"
    load = _num(
        model.get("workload_load_smoothed_percent"),
        _num(model.get("last_cpu_load_percent"), 0.0),
    )
    raw_load = _num(model.get("last_cpu_load_raw_percent"), load)
    current_pwm = _num(model.get("last_pwm"), 0.0)
    pwm_history = model.get("qualification_pwm_history")
    if isinstance(pwm_history, list) and pwm_history:
        item = pwm_history[-1]
        if isinstance(item, (list, tuple)) and len(item) == 2:
            current_pwm = _num(item[1], current_pwm)
    previous = state.get("last_context") if isinstance(state.get("last_context"), dict) else {}
    return {
        "bucket": bucket,
        "load": round(_clamp(load, 0.0, 100.0), 2),
        "raw_load": round(_clamp(raw_load, 0.0, 100.0), 2),
        "pwm": round(_clamp(current_pwm, 0.0, 100.0), 2),
        "target": round(float(target), 2),
        "load_delta": round(load - _num(previous.get("load"), load), 2),
        "pwm_delta": round(current_pwm - _num(previous.get("pwm"), current_pwm), 2),
    }


def _append_context(history: Any, now: float, context: dict[str, Any]) -> list[dict[str, Any]]:
    cutoff = now - THERMAL_PREDICTOR_HISTORY_SECONDS
    clean: list[dict[str, Any]] = []
    if isinstance(history, list):
        for item in history:
            if not isinstance(item, dict):
                continue
            ts = _num(item.get("epoch"), 0.0)
            if ts >= cutoff:
                clean.append(item)
    sample = {
        "epoch": float(now),
        "bucket": str(context.get("bucket") or "low"),
        "load": round(_num(context.get("load")), 2),
        "pwm": round(_num(context.get("pwm")), 2),
        "target": round(_num(context.get("target")), 2),
    }
    if clean and abs(_num(clean[-1].get("epoch")) - now) < 0.001:
        clean[-1] = sample
    else:
        clean.append(sample)
    return clean[-96:]


def _path_context_is_stable(
    created: dict[str, Any],
    context_history: list[dict[str, Any]],
    created_epoch: float,
    due_epoch: float,
    horizon: int,
) -> tuple[bool, str, dict[str, Any]]:
    """Validate the whole context path, not only creation/current endpoints."""
    samples = [
        item
        for item in context_history
        if created_epoch - 0.001 <= _num(item.get("epoch"), -1.0) <= due_epoch + 0.001
    ]
    details: dict[str, Any] = {"path_samples": len(samples)}
    if not samples:
        return False, "context_path_missing", details

    epochs = [created_epoch] + [_num(item.get("epoch"), created_epoch) for item in samples]
    epochs.append(due_epoch)
    max_gap = max((b - a for a, b in zip(epochs, epochs[1:]) if b >= a), default=0.0)
    details["max_context_gap_seconds"] = round(max_gap, 2)
    if max_gap > THERMAL_PREDICTOR_MAX_CONTEXT_GAP_SECONDS:
        return False, "context_path_gap", details

    created_bucket = str(created.get("bucket") or "low")
    if any(str(item.get("bucket") or "low") != created_bucket for item in samples):
        return False, "bucket_changed", details

    created_target = _num(created.get("target"))
    target_excursion = max((abs(_num(item.get("target")) - created_target) for item in samples), default=0.0)
    details["target_excursion_c"] = round(target_excursion, 3)
    if target_excursion > 0.25:
        return False, "target_changed", details

    created_load = _num(created.get("load"))
    load_excursion = max((abs(_num(item.get("load")) - created_load) for item in samples), default=0.0)
    details["load_excursion_percent"] = round(load_excursion, 2)
    if load_excursion > _CONTEXT_LOAD_LIMIT[horizon]:
        return False, "load_shift", details

    created_pwm = _num(created.get("pwm"))
    pwm_excursion = max((abs(_num(item.get("pwm")) - created_pwm) for item in samples), default=0.0)
    details["pwm_excursion_pp"] = round(pwm_excursion, 2)
    if pwm_excursion > _CONTEXT_PWM_LIMIT[horizon]:
        return False, "pwm_shift", details

    return True, "stable", details


def _stats_bucket(container: dict[str, Any], bucket: str, horizon: str) -> dict[str, Any]:
    regimes = container.setdefault("regime_stats", {})
    if not isinstance(regimes, dict):
        regimes = {}
        container["regime_stats"] = regimes
    regime = regimes.setdefault(bucket, {})
    if not isinstance(regime, dict):
        regime = {}
        regimes[bucket] = regime
    stats = regime.setdefault(horizon, {})
    if not isinstance(stats, dict):
        stats = {}
        regime[horizon] = stats
    return stats


def _global_bucket(container: dict[str, Any], horizon: str) -> dict[str, Any]:
    global_stats = container.setdefault("global_stats", {})
    if not isinstance(global_stats, dict):
        global_stats = {}
        container["global_stats"] = global_stats
    stats = global_stats.setdefault(horizon, {})
    if not isinstance(stats, dict):
        stats = {}
        global_stats[horizon] = stats
    return stats


def _update_stats(stats: dict[str, Any], signed_error: float) -> None:
    err = abs(signed_error)
    stats["mae_ema_c"] = round(
        _ema(stats.get("mae_ema_c"), err, THERMAL_PREDICTOR_ERROR_ALPHA), 3
    )
    stats["bias_ema_c"] = round(
        _clamp(
            _ema(stats.get("bias_ema_c"), signed_error, THERMAL_PREDICTOR_BIAS_ALPHA),
            -THERMAL_PREDICTOR_MAX_BIAS_C,
            THERMAL_PREDICTOR_MAX_BIAS_C,
        ),
        3,
    )
    stats["samples"] = int(_num(stats.get("samples"), 0)) + 1
    stats["last_error_c"] = round(err, 3)
    stats["last_signed_error_c"] = round(signed_error, 3)


def _effective_stats(
    state: dict[str, Any], bucket: str, horizon: str
) -> tuple[float | None, float, int, int]:
    global_stats = _global_bucket(state, horizon)
    regime_stats = _stats_bucket(state, bucket, horizon)
    gs = int(_num(global_stats.get("samples"), 0))
    rs = int(_num(regime_stats.get("samples"), 0))
    maturity = _clamp(rs / 12.0, 0.0, 1.0)
    g_mae = global_stats.get("mae_ema_c")
    r_mae = regime_stats.get("mae_ema_c")
    if r_mae is None and g_mae is None:
        mae = None
    elif r_mae is None:
        mae = _num(g_mae)
    elif g_mae is None:
        mae = _num(r_mae)
    else:
        mae = _num(g_mae) * (1.0 - maturity) + _num(r_mae) * maturity
    g_bias = _num(global_stats.get("bias_ema_c"), 0.0)
    r_bias = _num(regime_stats.get("bias_ema_c"), g_bias)
    bias = g_bias * (1.0 - maturity) + r_bias * maturity
    return mae, _clamp(bias, -THERMAL_PREDICTOR_MAX_BIAS_C, THERMAL_PREDICTOR_MAX_BIAS_C), rs, gs


def _dynamic_anchor(horizon: int, fast_slope: float, context: dict[str, Any]) -> float:
    base = THERMAL_PREDICTOR_TARGET_ANCHOR[horizon]
    pwm = _clamp(_num(context.get("pwm")), 0.0, 100.0) / 100.0
    load_delta = _num(context.get("load_delta"))
    rising_pressure = max(0.0, fast_slope) / 3.0 + max(0.0, load_delta) / 35.0
    cooling_gain = 0.72 + 0.78 * pwm
    falling_gain = 1.18 if fast_slope < -0.35 and pwm >= 0.50 else 1.0
    anchor = base * cooling_gain * falling_gain / (1.0 + 0.72 * rising_pressure)
    limits = {30: (0.02, 0.25), 60: (0.04, 0.42), 120: (0.08, 0.62)}
    return _clamp(anchor, *limits[horizon])


def _context_forcing(horizon: int, context: dict[str, Any]) -> float:
    load_delta = _clamp(_num(context.get("load_delta")), -40.0, 40.0)
    pwm_delta = _clamp(_num(context.get("pwm_delta")), -40.0, 40.0)
    load_coeff = {30: 0.008, 60: 0.010, 120: 0.012}[horizon]
    pwm_coeff = {30: 0.006, 60: 0.008, 120: 0.010}[horizon]
    return _clamp(load_delta * load_coeff - pwm_delta * pwm_coeff, -0.75, 0.75)


def _empty_state() -> dict[str, Any]:
    return {
        "schema": THERMAL_PREDICTOR_SCHEMA,
        "algorithm": THERMAL_PREDICTOR_ALGORITHM,
        "queue": [],
        "temp_history": [],
        "context_history": [],
        "regime_stats": {},
        "global_stats": {},
        "mae_all_ema_c": {},
        "conditions_mae_ema_c": {},
        "accepted_samples": {},
        "context_rejected_samples": {},
        "context_rejected_reasons": {},
        "rejected_samples_by_category": {},
        "last_validation": {},
    }


def _migrate_state(model: dict[str, Any], state: dict[str, Any], now: float) -> dict[str, Any]:
    old_schema = int(_num(state.get("schema"), 0))
    if old_schema == THERMAL_PREDICTOR_SCHEMA:
        return state

    history = model.get("thermal_predictor_history")
    if not isinstance(history, list):
        history = []
    if state:
        history.append(
            {
                "schema": old_schema,
                "algorithm": str(state.get("algorithm") or "unknown"),
                "archived_epoch": int(now),
                "average_mae_c": state.get("average_mae_c"),
                "confidence_percent": state.get("confidence_percent"),
                "quality_state": state.get("quality_state"),
                "validated_samples_total": state.get("validated_samples_total"),
            }
        )
        model["thermal_predictor_history"] = history[-4:]

    migrated = _empty_state()
    # v3 -> v3.1 keeps learned stable-regime calibration but deliberately drops the
    # old pending queue because exact-time validation semantics changed.
    if old_schema == 3:
        for key in ("temp_history", "regime_stats", "global_stats", "mae_all_ema_c"):
            value = state.get(key)
            if isinstance(value, type(migrated[key])):
                migrated[key] = value
        migrated["migrated_from_schema"] = 3
    return migrated


def thermal_predictor_v3(
    model: dict[str, Any],
    temp: float,
    slope_c_per_min: float,
    now: float,
    window_span: float,
    window_points: int,
    *,
    target: float,
) -> dict[str, Any]:
    raw_state = model.get("thermal_predictor")
    state = raw_state if isinstance(raw_state, dict) else {}
    state = _migrate_state(model, state, now)

    clean_history = _append_temperature(state.get("temp_history"), now, temp)
    state["temp_history"] = clean_history

    fallback_slope = _clamp(
        slope_c_per_min,
        -THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN,
        THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN,
    )
    fast_slope, fast_span, fast_points = _robust_slope(
        clean_history, now, _FAST_WINDOW_SECONDS, fallback_slope
    )
    slow_slope, slow_span, slow_points = _robust_slope(
        clean_history, now, _SLOW_WINDOW_SECONDS, fallback_slope
    )

    context = _context(model, state, target)
    context_history = _append_context(state.get("context_history"), now, context)
    state["context_history"] = context_history

    queue = state.get("queue") if isinstance(state.get("queue"), list) else []
    pending: list[dict[str, Any]] = []
    mae_all = state.get("mae_all_ema_c") if isinstance(state.get("mae_all_ema_c"), dict) else {}
    conditions_mae = (
        state.get("conditions_mae_ema_c")
        if isinstance(state.get("conditions_mae_ema_c"), dict)
        else {}
    )
    accepted = state.get("accepted_samples") if isinstance(state.get("accepted_samples"), dict) else {}
    rejected = (
        state.get("context_rejected_samples")
        if isinstance(state.get("context_rejected_samples"), dict)
        else {}
    )
    rejected_reasons = (
        state.get("context_rejected_reasons")
        if isinstance(state.get("context_rejected_reasons"), dict)
        else {}
    )
    rejected_categories = (
        state.get("rejected_samples_by_category")
        if isinstance(state.get("rejected_samples_by_category"), dict)
        else {}
    )
    last_validation = state.get("last_validation") if isinstance(state.get("last_validation"), dict) else {}
    last_error: dict[str, float] = {}
    last_signed_error: dict[str, float] = {}

    def reject(key: str, reason: str, category: str) -> None:
        rejected[key] = int(_num(rejected.get(key), 0)) + 1
        reasons = rejected_reasons.setdefault(key, {})
        if not isinstance(reasons, dict):
            reasons = {}
            rejected_reasons[key] = reasons
        reasons[reason] = int(_num(reasons.get(reason), 0)) + 1
        categories = rejected_categories.setdefault(key, {})
        if not isinstance(categories, dict):
            categories = {}
            rejected_categories[key] = categories
        categories[category] = int(_num(categories.get(category), 0)) + 1

    for item in queue:
        if not isinstance(item, dict):
            continue
        due = _num(item.get("due_epoch"), 0.0)
        created_epoch = _num(item.get("created_epoch"), due)
        horizon = int(_num(item.get("horizon_seconds"), 0))
        key = str(horizon)
        if horizon not in THERMAL_PREDICTOR_HORIZONS_SECONDS:
            continue
        if due > now:
            pending.append(item)
            continue
        predicted = _num(item.get("predicted_c"), temp)
        actual, interpolation_gap, actual_source = _temperature_at(clean_history, due)
        validation = {
            "status": "rejected",
            "reason": "missing_actual_bracket",
            "category": "sampling",
            "due_epoch": int(round(due)),
            "evaluated_epoch": int(round(now)),
            "evaluation_lag_seconds": round(max(0.0, now - due), 2),
            "predicted_c": round(predicted, 3),
            "actual_source": actual_source,
            "interpolation_gap_seconds": (
                round(interpolation_gap, 2) if interpolation_gap is not None else None
            ),
        }
        if actual is None:
            reason = "interpolation_gap" if actual_source == "interpolation_gap" else "missing_actual_bracket"
            reject(key, reason, "sampling")
            validation["reason"] = reason
            last_validation[key] = validation
            continue

        signed_error = actual - predicted
        err = abs(signed_error)
        mae_all[key] = round(_ema(mae_all.get(key), err, THERMAL_PREDICTOR_ERROR_ALPHA), 3)
        last_error[key] = round(err, 3)
        last_signed_error[key] = round(signed_error, 3)
        validation.update(
            {
                "actual_c": round(actual, 3),
                "absolute_error_c": round(err, 3),
                "signed_error_c": round(signed_error, 3),
            }
        )

        created_context = item.get("context") if isinstance(item.get("context"), dict) else {}
        stable, reason, path_details = _path_context_is_stable(
            created_context, context_history, created_epoch, due, horizon
        )
        validation["path"] = path_details
        if stable:
            bucket = str(created_context.get("bucket") or context["bucket"])
            _update_stats(_global_bucket(state, key), signed_error)
            _update_stats(_stats_bucket(state, bucket, key), signed_error)
            accepted[key] = int(_num(accepted.get(key), 0)) + 1
            validation.update({"status": "accepted", "reason": "stable", "category": "model"})
        else:
            category = "conditions" if reason in _CONTEXT_REJECTION_REASONS else "sampling"
            reject(key, reason, category)
            validation.update({"reason": reason, "category": category})
            if category == "conditions":
                conditions_mae[key] = round(
                    _ema(conditions_mae.get(key), err, THERMAL_PREDICTOR_ERROR_ALPHA), 3
                )
        last_validation[key] = validation

    forecasts: dict[str, float] = {}
    raw_forecasts: dict[str, float] = {}
    anchored_forecasts: dict[str, float] = {}
    applied_bias: dict[str, float] = {}
    anchors: dict[str, float] = {}
    forcing_map: dict[str, float] = {}
    selected_slopes: dict[str, float] = {}
    mae_effective: dict[str, float] = {}
    bias_effective: dict[str, float] = {}
    samples_effective: dict[str, int] = {}
    samples_global: dict[str, int] = {}
    confidence_by_horizon: dict[str, int] = {}
    accuracy_target_met: dict[str, bool] = {}
    rejection_ratio: dict[str, float] = {}
    bucket = context["bucket"]

    for horizon in THERMAL_PREDICTOR_HORIZONS_SECONDS:
        key = str(horizon)
        wf = _SLOPE_FAST_WEIGHT[horizon]
        selected_slope = _clamp(
            fast_slope * wf + slow_slope * (1.0 - wf),
            -THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN,
            THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN,
        )
        selected_slopes[key] = round(selected_slope, 3)
        forcing = _context_forcing(horizon, context)
        forcing_map[key] = round(forcing, 3)
        raw_linear = (
            temp
            + selected_slope * (horizon / 60.0) * THERMAL_PREDICTOR_DAMPING[horizon]
            + forcing
        )
        anchor = _dynamic_anchor(horizon, fast_slope, context)
        anchors[key] = round(anchor, 3)
        anchored = raw_linear + (target - raw_linear) * anchor
        eff_mae, eff_bias, regime_samples, global_samples = _effective_stats(state, bucket, key)
        maturity = _clamp(regime_samples / 8.0, 0.0, 1.0)
        correction = eff_bias * (0.35 + 0.65 * maturity)
        predicted = round(_clamp(anchored + correction, -20.0, 100.0), 2)
        forecasts[key] = predicted
        raw_forecasts[key] = round(raw_linear, 2)
        anchored_forecasts[key] = round(anchored, 2)
        applied_bias[key] = round(correction, 3)
        bias_effective[key] = round(eff_bias, 3)
        samples_effective[key] = regime_samples
        samples_global[key] = global_samples
        if eff_mae is not None:
            mae_effective[key] = round(eff_mae, 3)
        accuracy_target_met[key] = bool(
            eff_mae is not None and eff_mae <= THERMAL_PREDICTOR_ACCURACY_TARGET_C[horizon]
        )
        accuracy = 0.35 if eff_mae is None else _clamp(1.0 - eff_mae / 3.0, 0.0, 1.0)
        sample_maturity = _clamp(
            (regime_samples + min(global_samples, 8) * 0.35) / 12.0, 0.0, 1.0
        )
        trend_maturity = _clamp(min(fast_span / 18.0, slow_span / 45.0), 0.0, 1.0)
        confidence_by_horizon[key] = int(
            round(
                _clamp(
                    100.0 * (0.48 * accuracy + 0.32 * sample_maturity + 0.20 * trend_maturity),
                    0.0,
                    97.0,
                )
            )
        )
        accepted_count = int(_num(accepted.get(key), 0))
        rejected_count = int(_num(rejected.get(key), 0))
        total_count = accepted_count + rejected_count
        rejection_ratio[key] = round(
            100.0 * rejected_count / total_count if total_count else 0.0, 1
        )
        pending.append(
            {
                "created_epoch": float(now),
                "due_epoch": float(now + horizon),
                "horizon_seconds": horizon,
                "predicted_c": predicted,
                "context": {
                    "bucket": bucket,
                    "load": context["load"],
                    "pwm": context["pwm"],
                    "target": context["target"],
                },
            }
        )

    pending = pending[-THERMAL_PREDICTOR_QUEUE_MAX:]
    state["queue"] = pending
    state["mae_all_ema_c"] = {k: round(_num(v), 3) for k, v in mae_all.items()}
    state["conditions_mae_ema_c"] = {k: round(_num(v), 3) for k, v in conditions_mae.items()}
    state["accepted_samples"] = {k: int(_num(v)) for k, v in accepted.items()}
    state["context_rejected_samples"] = {k: int(_num(v)) for k, v in rejected.items()}
    state["context_rejected_reasons"] = rejected_reasons
    state["rejected_samples_by_category"] = rejected_categories
    state["last_validation"] = last_validation

    weighted_mae_num = weighted_mae_den = weighted_all_num = weighted_all_den = weighted_conf = 0.0
    for horizon in THERMAL_PREDICTOR_HORIZONS_SECONDS:
        key = str(horizon)
        weight = _HORIZON_WEIGHTS[horizon]
        weighted_conf += confidence_by_horizon[key] * weight
        if key in mae_effective:
            weighted_mae_num += mae_effective[key] * weight
            weighted_mae_den += weight
        if key in mae_all:
            weighted_all_num += _num(mae_all[key]) * weight
            weighted_all_den += weight
    avg_mae = weighted_mae_num / weighted_mae_den if weighted_mae_den > 0 else None
    avg_mae_all = weighted_all_num / weighted_all_den if weighted_all_den > 0 else None
    confidence = int(round(_clamp(weighted_conf, 0.0, 97.0)))
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

    state.update(
        {
            "schema": THERMAL_PREDICTOR_SCHEMA,
            "algorithm": THERMAL_PREDICTOR_ALGORITHM,
            "mode": "observe_only",
            "forecast_30s_c": forecasts["30"],
            "forecast_60s_c": forecasts["60"],
            "forecast_120s_c": forecasts["120"],
            "raw_forecast_c": raw_forecasts,
            "anchored_forecast_c": anchored_forecasts,
            "dynamic_anchor": anchors,
            "context_forcing_c": forcing_map,
            "selected_slope_c_per_min": selected_slopes,
            "fast_slope_c_per_min": round(fast_slope, 3),
            "slow_slope_c_per_min": round(slow_slope, 3),
            "slope_estimator": "theil_sen_median",
            "fast_window_span_seconds": round(fast_span, 1),
            "slow_window_span_seconds": round(slow_span, 1),
            "fast_window_points": fast_points,
            "slow_window_points": slow_points,
            "applied_bias_c": applied_bias,
            "effective_bias_c": bias_effective,
            "temperature_c": round(temp, 2),
            "target_c": round(target, 2),
            "slope_c_per_min": round(fallback_slope, 3),
            "confidence_percent": confidence,
            "confidence_by_horizon_percent": confidence_by_horizon,
            "quality_state": quality_state,
            "mae_ema_c": mae_effective,
            "model_mae_ema_c": mae_effective,
            "mae_all_ema_c": {k: round(_num(v), 3) for k, v in mae_all.items()},
            "conditions_mae_ema_c": {
                k: round(_num(v), 3) for k, v in conditions_mae.items()
            },
            "bias_ema_c": bias_effective,
            "last_error_c": last_error,
            "last_signed_error_c": last_signed_error,
            "validated_samples": samples_effective,
            "validated_samples_global": samples_global,
            "accepted_samples": {k: int(_num(v)) for k, v in accepted.items()},
            "rejected_samples": {k: int(_num(v)) for k, v in rejected.items()},
            "rejection_ratio_percent": rejection_ratio,
            "context_rejected_samples": {k: int(_num(v)) for k, v in rejected.items()},
            "context_rejected_reasons": rejected_reasons,
            "rejected_samples_by_category": rejected_categories,
            "last_validation": last_validation,
            "validated_samples_total": sum(samples_effective.values()),
            "accepted_samples_total": sum(int(_num(v)) for v in accepted.values()),
            "rejected_samples_total": sum(int(_num(v)) for v in rejected.values()),
            "average_mae_c": round(avg_mae, 3) if avg_mae is not None else None,
            "average_mae_all_c": round(avg_mae_all, 3) if avg_mae_all is not None else None,
            "accuracy_target_c": {
                str(h): THERMAL_PREDICTOR_ACCURACY_TARGET_C[h]
                for h in THERMAL_PREDICTOR_HORIZONS_SECONDS
            },
            "accuracy_target_met": accuracy_target_met,
            "validation_mode": "exact_due_interpolation",
            "context_guard": "path_aware",
            "current_regime": bucket,
            "context": context,
            "window_span_seconds": int(round(window_span)),
            "window_points": int(window_points),
            "control_output_enabled": False,
            "updated_epoch": int(now),
        }
    )
    state["last_context"] = {
        "bucket": bucket,
        "load": context["load"],
        "pwm": context["pwm"],
        "target": context["target"],
    }
    model["thermal_predictor"] = state
    public = dict(state)
    for private_key in (
        "queue",
        "temp_history",
        "context_history",
        "regime_stats",
        "global_stats",
        "last_context",
    ):
        public.pop(private_key, None)
    return public
