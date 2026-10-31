#!/usr/bin/env python3
"""Pure decision policy for SBC5 Thermal Predictor Active Assist."""
from __future__ import annotations

import math
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


def forecast_confirmation(
    *, predictor: dict[str, Any], temp: float, target: float, slope: float, direction: str
) -> tuple[bool, str, dict[str, float]]:
    """Confirm forecast direction against short/long thermal trends.

    The predictor already exposes robust Theil-Sen fast/slow slopes.  Older model
    snapshots may not have them, so the current measured slope remains a safe
    fallback.  Hot guidance may also confirm when the measured temperature is
    already materially above target; cool guidance never gets that shortcut.
    """
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


def decide(*, predictor: dict[str, Any], target: float, temp: float, slope: float, mode: str, max_delta: int) -> dict[str, Any]:
    weighted, weights = dynamic_forecast(predictor, target)
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
        "weighted_forecast_error_c": round(error, 2),
        "horizon_weights": weights,
        "forecast_direction": requested_direction,
        "forecast_confirmed": bool(confirmed),
        "forecast_confirmation_reason": confirmation_reason,
        "quality_gate": {
            "mode": mode,
            "max_delta_pp": int(max_delta),
            "forecast_direction": requested_direction,
            "forecast_confirmed": bool(confirmed),
            "confirmation_reason": confirmation_reason,
            "trend_30s_c_per_min": trends["fast_c_per_min"],
            "trend_120s_c_per_min": trends["slow_c_per_min"],
        },
    }
