#!/usr/bin/env python3
"""Pure decision policy for SBC5 Thermal Predictor Active Assist."""
from __future__ import annotations

import math
from statistics import median
from typing import Any

ACTIVE_MAX_DELTA_PP = 2
PROBATION_MAX_DELTA_PP = 1
ACTIVE_MIN_CONFIDENCE = 80
PROBATION_MIN_CONFIDENCE = 68
ACTIVE_MAX_MAE_C = 1.50
PROBATION_MAX_MAE_C = 2.50
ACTIVE_MIN_VALIDATED_PER_HORIZON = 12
PROBATION_MIN_VALIDATED_PER_HORIZON = 8
MAX_PREDICTOR_AGE_SECONDS = 35
BASE_HORIZON_WEIGHTS = {30: 0.50, 60: 0.35, 120: 0.15}
ACCURACY_TARGETS = {30: 1.0, 60: 1.5, 120: 2.5}
HOT_FAST_CONFIRM_C_PER_MIN = 0.10
HOT_SLOW_CONFIRM_C_PER_MIN = 0.04
COOL_FAST_CONFIRM_C_PER_MIN = -0.10
COOL_SLOW_CONFIRM_C_PER_MIN = -0.04

# 3.1.30 — Thermal Predictor Stability v2.
FORECAST_HISTORY_SIZE = 3
FORECAST_EMA_ALPHA = 0.35
FORECAST_CONFIRM_CYCLES = 2
FORECAST_FAST_PATH_ERROR_C = 2.50
FORECAST_FAST_PATH_MIN_CONFIDENCE = 82
FORECAST_FAST_PATH_MAX_MAE_C = 1.30
TREND_GUARD_C_PER_MIN = 0.80
TREND_OVERRIDE_ERROR_C = 1.50
TREND_OVERRIDE_MIN_CONFIDENCE = 82


def num(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except (TypeError, ValueError):
        return default


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def mae_map(predictor: dict[str, Any]) -> dict[str, float]:
    raw = predictor.get("model_mae_ema_c")
    if not isinstance(raw, dict) or not raw:
        raw = predictor.get("mae_ema_c")
    raw = raw if isinstance(raw, dict) else {}
    return {str(h): max(0.05, num(raw.get(str(h)), 99.0)) for h in (30, 60, 120)}


def validated_map(predictor: dict[str, Any]) -> dict[str, int]:
    raw = predictor.get("validated_samples")
    raw = raw if isinstance(raw, dict) else {}
    return {str(h): max(0, int(round(num(raw.get(str(h)), 0.0)))) for h in (30, 60, 120)}


def dynamic_forecast(predictor: dict[str, Any], target: float) -> tuple[float, dict[str, float]]:
    maes = mae_map(predictor)
    scores: dict[str, float] = {}
    forecasts: dict[str, float] = {}
    for horizon in (30, 60, 120):
        key = str(horizon)
        forecasts[key] = num(predictor.get(f"forecast_{horizon}s_c"), target)
        reliability = clamp(ACCURACY_TARGETS[horizon] / max(maes[key], 0.05), 0.20, 2.25)
        scores[key] = BASE_HORIZON_WEIGHTS[horizon] * reliability
    total = sum(scores.values()) or 1.0
    weights = {key: round(value / total, 4) for key, value in scores.items()}
    weighted = sum(forecasts[key] * weights[key] for key in weights)
    return round(weighted, 3), weights



STABILITY_CONTEXT_MAX_GAP_SECONDS = 35.0
STABILITY_TARGET_RESET_DELTA_C = 0.25


def refresh_stability_context(
    state: dict[str, Any], *, sample_epoch: float, target: float,
    regime: str, ai_mode: str, control_mode: str,
) -> str:
    """Reset only short-term forecast smoothing/confirmation after context changes.

    Model calibration, validated samples, and AI Cooling learning live elsewhere
    and must not be cleared by a context transition.
    """
    context = {
        "target_c": round(target, 2),
        "regime": str(regime),
        "ai_mode": str(ai_mode),
        "control_mode": str(control_mode),
    }
    previous = state.get("context") if isinstance(state.get("context"), dict) else {}
    last_epoch = num(state.get("last_sample_epoch"), 0.0)
    has_history = bool(state.get("forecast_history_c"))
    reason = "none"
    if has_history:
        if not previous or last_epoch <= 0.0:
            reason = "unversioned_history"
        elif sample_epoch < last_epoch:
            reason = "clock_moved_backwards"
        elif sample_epoch - last_epoch > STABILITY_CONTEXT_MAX_GAP_SECONDS:
            reason = "sample_gap"
        elif abs(target - num(previous.get("target_c"), target)) > STABILITY_TARGET_RESET_DELTA_C:
            reason = "target_changed"
        elif str(previous.get("regime")) != context["regime"]:
            reason = "regime_changed"
        elif str(previous.get("ai_mode")) != context["ai_mode"]:
            reason = "ai_mode_changed"
        elif str(previous.get("control_mode")) != context["control_mode"]:
            reason = "control_mode_changed"

    if reason != "none":
        reset_count = max(0, int(round(num(state.get("context_reset_count"), 0.0))))
        state.clear()
        state["context_reset_count"] = reset_count + 1
    state["context"] = context
    state["last_sample_epoch"] = round(sample_epoch, 3)
    state["context_reset_reason"] = reason
    return reason


def stabilize_forecast(
    state: dict[str, Any], *, raw_forecast: float, target: float,
    confidence: float, average_mae: float,
) -> dict[str, Any]:
    """Median-of-3 + EMA forecast conditioner with persistent confirmation state.

    The caller stores ``state`` in the durable AI model.  No extra timer/polling loop
    is required; the existing AI cycle advances the conditioner once per sample.
    """
    history_raw = state.get("forecast_history_c")
    history = []
    if isinstance(history_raw, list):
        for value in history_raw[-(FORECAST_HISTORY_SIZE - 1):]:
            v = num(value, float("nan"))
            if math.isfinite(v):
                history.append(v)
    history.append(float(raw_forecast))
    history = history[-FORECAST_HISTORY_SIZE:]

    median_forecast = float(median(history))
    previous = num(state.get("stable_forecast_c"), median_forecast)
    stable_forecast = previous + FORECAST_EMA_ALPHA * (median_forecast - previous)
    stable_error = stable_forecast - target

    direction = "neutral"
    if stable_error >= 0.45:
        direction = "hot"
    elif stable_error <= -0.70:
        direction = "cool"

    hot_confirm = max(0, int(round(num(state.get("hot_confirm_cycles"), 0.0))))
    cool_confirm = max(0, int(round(num(state.get("cool_confirm_cycles"), 0.0))))
    if direction == "hot":
        hot_confirm = min(99, hot_confirm + 1)
        cool_confirm = 0
    elif direction == "cool":
        cool_confirm = min(99, cool_confirm + 1)
        hot_confirm = 0
    else:
        hot_confirm = 0
        cool_confirm = 0

    fast_path = (
        abs(stable_error) >= FORECAST_FAST_PATH_ERROR_C
        and confidence >= FORECAST_FAST_PATH_MIN_CONFIDENCE
        and average_mae <= FORECAST_FAST_PATH_MAX_MAE_C
    )

    state.update({
        "forecast_history_c": [round(v, 3) for v in history],
        "median_forecast_c": round(median_forecast, 3),
        "stable_forecast_c": round(stable_forecast, 3),
        "raw_forecast_c": round(raw_forecast, 3),
        "stable_error_c": round(stable_error, 3),
        "direction": direction,
        "hot_confirm_cycles": hot_confirm,
        "cool_confirm_cycles": cool_confirm,
        "fast_path": bool(fast_path),
    })
    return dict(state)


def thermal_state(*, temp: float, target: float, trend: float) -> str:
    if temp > target + 0.35:
        position = "above_target"
    elif temp < target - 0.35:
        position = "below_target"
    else:
        position = "near_target"
    if trend > 0.15:
        movement = "heating"
    elif trend < -0.15:
        movement = "cooling"
    else:
        movement = "stable"
    return f"{position}_{movement}"


def gate(
    *, predictor: dict[str, Any], now: float, ai_mode: str, control_mode: str,
    controller_action: str, outcome_samples: int = 0, outcome_success_percent: float = 100.0,
) -> tuple[str, str, int]:
    if ai_mode != "assist":
        return "observe", "ai_assist_required", 0
    if control_mode != "automatic":
        return "observe", "automatic_mode_required", 0
    action = controller_action.lower()
    if any(token in action for token in ("safety", "critical", "thermal_fast")):
        return "observe", "safety_action_active", 0
    age = max(0.0, now - num(predictor.get("updated_epoch"), 0.0))
    if age > MAX_PREDICTOR_AGE_SECONDS:
        return "observe", "predictor_stale", 0
    if outcome_samples >= 6 and outcome_success_percent < 45.0:
        return "observe", "outcome_quality_low", 0

    confidence = int(round(num(predictor.get("confidence_percent"), 0.0)))
    avg_mae_raw = predictor.get("average_mae_c")
    avg_mae = num(avg_mae_raw, 99.0) if avg_mae_raw is not None else 99.0
    min_validated = min(validated_map(predictor).values(), default=0)
    if confidence >= ACTIVE_MIN_CONFIDENCE and avg_mae <= ACTIVE_MAX_MAE_C and min_validated >= ACTIVE_MIN_VALIDATED_PER_HORIZON:
        return "active", "eligible", ACTIVE_MAX_DELTA_PP
    if confidence >= PROBATION_MIN_CONFIDENCE and avg_mae <= PROBATION_MAX_MAE_C and min_validated >= PROBATION_MIN_VALIDATED_PER_HORIZON:
        return "probation", "quality_probation", PROBATION_MAX_DELTA_PP
    if min_validated < PROBATION_MIN_VALIDATED_PER_HORIZON:
        return "observe", "insufficient_validated_forecasts", 0
    if confidence < PROBATION_MIN_CONFIDENCE:
        return "observe", "confidence_below_threshold", 0
    return "observe", "mae_above_threshold", 0



def stabilize_quality_gate(
    state: dict[str, Any], *, raw_mode: str, raw_reason: str,
    raw_max_delta: int, enter_cycles: int = 2,
) -> tuple[str, str, int]:
    """Require consecutive high-quality cycles before expanding PWM authority.

    Crucially, downgrades are *immediate*. A probation/observe decision is never
    promoted or retained as active by history, so safety gates are authoritative.
    State belongs to the short-lived guidance context, not predictor calibration.
    """
    if raw_mode != "active":
        state["quality_gate_active_candidate_cycles"] = 0
        state["quality_gate_effective_mode"] = raw_mode
        return raw_mode, raw_reason, raw_max_delta

    previous_mode = str(state.get("quality_gate_effective_mode") or "observe")
    pending = max(0, int(round(num(state.get("quality_gate_active_candidate_cycles"), 0))))
    pending = min(enter_cycles, pending + 1)
    state["quality_gate_active_candidate_cycles"] = pending
    if previous_mode == "active" or pending >= enter_cycles:
        state["quality_gate_effective_mode"] = "active"
        return "active", raw_reason, raw_max_delta
    state["quality_gate_effective_mode"] = "probation"
    return "probation", "active_waiting_confirmation", min(raw_max_delta, PROBATION_MAX_DELTA_PP)


def forecast_confirmation(
    *, predictor: dict[str, Any], temp: float, target: float, slope: float, direction: str
) -> tuple[bool, str, dict[str, float]]:
    """Confirm forecast direction against short/long thermal trends."""
    fast = num(predictor.get("fast_slope_c_per_min"), slope)
    slow = num(predictor.get("slow_slope_c_per_min"), slope)
    details = {"fast_c_per_min": round(fast, 3), "slow_c_per_min": round(slow, 3)}
    if direction == "hot":
        if temp >= target + 0.85:
            return True, "measured_hot", details
        if fast >= HOT_FAST_CONFIRM_C_PER_MIN and slow >= HOT_SLOW_CONFIRM_C_PER_MIN:
            return True, "trend_hot_confirmed", details
        return False, "hot_forecast_unconfirmed", details
    if direction == "cool":
        if fast <= COOL_FAST_CONFIRM_C_PER_MIN and slow <= COOL_SLOW_CONFIRM_C_PER_MIN:
            return True, "trend_cool_confirmed", details
        return False, "cool_forecast_unconfirmed", details
    return True, "near_target", details


def decide(
    *, predictor: dict[str, Any], target: float, temp: float, slope: float,
    mode: str, max_delta: int, stability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw_weighted, weights = dynamic_forecast(predictor, target)
    stability = stability if isinstance(stability, dict) else {}
    weighted = num(stability.get("stable_forecast_c"), raw_weighted)
    error = weighted - target
    delta = 0
    reason = "near_target"
    requested_direction = "neutral"
    if max_delta > 0:
        if error >= 1.20:
            delta, reason, requested_direction = max_delta, "forecast_hot_strong", "hot"
        elif error >= 0.45:
            delta, reason, requested_direction = 1, "forecast_hot", "hot"
        elif mode == "active" and error <= -1.35 and slope <= -0.20:
            delta, reason, requested_direction = -max_delta, "forecast_cool_strong", "cool"
        elif mode == "active" and error <= -0.70 and slope <= 0.0:
            delta, reason, requested_direction = -1, "forecast_cool", "cool"
        elif error < -0.70:
            reason, requested_direction = "cool_forecast_but_not_falling", "cool"

    confirmed, confirmation_reason, trends = forecast_confirmation(
        predictor=predictor,
        temp=temp,
        target=target,
        slope=slope,
        direction=requested_direction,
    )
    if delta != 0 and not confirmed:
        delta = 0
        reason = confirmation_reason

    # Stability v2 requires two consecutive conditioned forecasts in the same
    # direction. A high-quality >=2.5 C forecast may use the bounded fast path.
    fast_path = bool(stability.get("fast_path"))
    if delta > 0 and not fast_path:
        cycles = int(round(num(stability.get("hot_confirm_cycles"), FORECAST_CONFIRM_CYCLES)))
        if cycles < FORECAST_CONFIRM_CYCLES:
            delta, reason = 0, "hot_forecast_waiting_confirmation"
            confirmed = False
            confirmation_reason = reason
    elif delta < 0 and not fast_path:
        cycles = int(round(num(stability.get("cool_confirm_cycles"), FORECAST_CONFIRM_CYCLES)))
        if cycles < FORECAST_CONFIRM_CYCLES:
            delta, reason = 0, "cool_forecast_waiting_confirmation"
            confirmed = False
            confirmation_reason = reason

    confidence = num(predictor.get("confidence_percent"), 0.0)
    fast_trend = trends["fast_c_per_min"]
    override = (
        abs(error) >= TREND_OVERRIDE_ERROR_C
        and confidence >= TREND_OVERRIDE_MIN_CONFIDENCE
        and (
            fast_path
            or (requested_direction == "hot" and int(num(stability.get("hot_confirm_cycles"), 0)) >= FORECAST_CONFIRM_CYCLES)
            or (requested_direction == "cool" and int(num(stability.get("cool_confirm_cycles"), 0)) >= FORECAST_CONFIRM_CYCLES)
        )
    )
    if delta > 0 and fast_trend <= -TREND_GUARD_C_PER_MIN and not override:
        delta, reason = 0, "trend_guard_cooling"
        confirmed = False
        confirmation_reason = reason
    elif delta < 0 and fast_trend >= TREND_GUARD_C_PER_MIN and not override:
        delta, reason = 0, "trend_guard_heating"
        confirmed = False
        confirmation_reason = reason

    if delta < 0 and (temp > target + 0.10 or slope > 0.0):
        delta, reason = 0, "downward_sign_guard"
        confirmed = False
        confirmation_reason = "downward_sign_guard"
    if mode == "probation" and delta < 0:
        delta, reason = 0, "probation_upward_only"
        confirmed = False
        confirmation_reason = "probation_upward_only"

    return {
        "requested_delta_pp": int(clamp(delta, -max_delta, max_delta)) if max_delta else 0,
        "decision_reason": reason,
        "weighted_forecast_c": round(weighted, 2),
        "weighted_forecast_raw_c": round(raw_weighted, 2),
        "weighted_forecast_error_c": round(error, 2),
        "horizon_weights": weights,
        "forecast_direction": requested_direction,
        "forecast_confirmed": bool(confirmed),
        "forecast_confirmation_reason": confirmation_reason,
        "stability": stability,
        "quality_gate": {
            "mode": mode,
            "max_delta_pp": int(max_delta),
            "forecast_direction": requested_direction,
            "forecast_confirmed": bool(confirmed),
            "confirmation_reason": confirmation_reason,
            "trend_30s_c_per_min": trends["fast_c_per_min"],
            "trend_120s_c_per_min": trends["slow_c_per_min"],
            "fast_path": fast_path,
        },
    }
