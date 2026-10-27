#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "local_apps" / "sbc5_control_center" / "ai_cooling.py"
text = AI.read_text(encoding="utf-8")

old_constants = '''THERMAL_PREDICTOR_ERROR_ALPHA = 0.18\nTHERMAL_PREDICTOR_DAMPING = {30: 0.90, 60: 0.72, 120: 0.52}\n'''
new_constants = '''THERMAL_PREDICTOR_ERROR_ALPHA = 0.18\nTHERMAL_PREDICTOR_BIAS_ALPHA = 0.12\nTHERMAL_PREDICTOR_MAX_BIAS_C = 1.0\nTHERMAL_PREDICTOR_DAMPING = {30: 0.90, 60: 0.72, 120: 0.52}\nTHERMAL_PREDICTOR_TARGET_ANCHOR = {30: 0.10, 60: 0.25, 120: 0.45}\nTHERMAL_PREDICTOR_SCHEMA = 2\nTHERMAL_PREDICTOR_ALGORITHM = "closed_loop_calibrated_v2"\n'''
if old_constants not in text:
    raise SystemExit("Predictor constants anchor not found")
text = text.replace(old_constants, new_constants, 1)

new_function = r'''def _thermal_predictor(
    model: dict[str, Any],
    temp: float,
    slope_c_per_min: float,
    now: float,
    window_span: float,
    window_points: int,
    *,
    target: float,
) -> dict[str, Any]:
    """Closed-loop aware observe-only thermal forecast with online calibration.

    v2 keeps the Predictor strictly outside the physical control path. Compared with
    the original linear extrapolator it adds two accuracy mechanisms suited to the
    SBC5 closed loop: horizon-specific target anchoring and bounded signed online
    bias correction. Predictor quality metrics are algorithm-specific, therefore a
    legacy v1 state is archived and v2 starts with fresh error statistics.
    """
    raw_state = model.get("thermal_predictor")
    state = raw_state if isinstance(raw_state, dict) else {}
    if int(_num(state.get("schema"), 0)) != THERMAL_PREDICTOR_SCHEMA:
        if state:
            history = model.get("thermal_predictor_history")
            if not isinstance(history, list):
                history = []
            history.append({
                "schema": int(_num(state.get("schema"), 0)),
                "algorithm": str(state.get("algorithm") or "linear_damped_v1"),
                "archived_epoch": int(now),
                "average_mae_c": state.get("average_mae_c"),
                "confidence_percent": state.get("confidence_percent"),
                "quality_state": state.get("quality_state"),
                "validated_samples_total": state.get("validated_samples_total"),
            })
            model["thermal_predictor_history"] = history[-3:]
        state = {}

    queue = state.get("queue")
    if not isinstance(queue, list):
        queue = []
    mae = state.get("mae_ema_c")
    if not isinstance(mae, dict):
        mae = {}
    bias = state.get("bias_ema_c")
    if not isinstance(bias, dict):
        bias = {}
    samples = state.get("validated_samples")
    if not isinstance(samples, dict):
        samples = {}
    last_error = state.get("last_error_c")
    if not isinstance(last_error, dict):
        last_error = {}
    last_signed_error = state.get("last_signed_error_c")
    if not isinstance(last_signed_error, dict):
        last_signed_error = {}

    pending: list[dict[str, Any]] = []
    for item in queue:
        if not isinstance(item, dict):
            continue
        due = _num(item.get("due_epoch"), 0.0)
        horizon = str(int(_num(item.get("horizon_seconds"), 0)))
        predicted = _num(item.get("predicted_c"), temp)
        if due > 0 and due <= now:
            signed_err = temp - predicted
            err = abs(signed_err)
            old_mae = _num(mae.get(horizon), err)
            mae[horizon] = round(old_mae + THERMAL_PREDICTOR_ERROR_ALPHA * (err - old_mae), 3)
            old_bias = _num(bias.get(horizon), signed_err)
            learned_bias = old_bias + THERMAL_PREDICTOR_BIAS_ALPHA * (signed_err - old_bias)
            bias[horizon] = round(_clamp(learned_bias, -THERMAL_PREDICTOR_MAX_BIAS_C, THERMAL_PREDICTOR_MAX_BIAS_C), 3)
            last_error[horizon] = round(err, 3)
            last_signed_error[horizon] = round(signed_err, 3)
            samples[horizon] = int(_num(samples.get(horizon), 0)) + 1
        elif due > now - 10.0:
            pending.append(item)

    slope = _clamp(slope_c_per_min, -THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN, THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN)
    forecasts: dict[str, float] = {}
    raw_forecasts: dict[str, float] = {}
    anchored_forecasts: dict[str, float] = {}
    applied_bias: dict[str, float] = {}
    for horizon in THERMAL_PREDICTOR_HORIZONS_SECONDS:
        key = str(horizon)
        damping = THERMAL_PREDICTOR_DAMPING[horizon]
        raw_linear = temp + slope * (horizon / 60.0) * damping
        anchor = THERMAL_PREDICTOR_TARGET_ANCHOR[horizon]
        anchored = raw_linear + (target - raw_linear) * anchor
        horizon_samples = int(_num(samples.get(key), 0))
        bias_maturity = _clamp(horizon_samples / float(THERMAL_SHADOW_MIN_VALIDATED_PER_HORIZON), 0.0, 1.0)
        correction = _clamp(_num(bias.get(key), 0.0), -THERMAL_PREDICTOR_MAX_BIAS_C, THERMAL_PREDICTOR_MAX_BIAS_C) * bias_maturity
        predicted = anchored + correction
        predicted = round(_clamp(predicted, -20.0, 100.0), 2)
        forecasts[key] = predicted
        raw_forecasts[key] = round(raw_linear, 2)
        anchored_forecasts[key] = round(anchored, 2)
        applied_bias[key] = round(correction, 3)
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
        "schema": THERMAL_PREDICTOR_SCHEMA,
        "algorithm": THERMAL_PREDICTOR_ALGORITHM,
        "mode": "observe_only",
        "forecast_30s_c": forecasts["30"],
        "forecast_60s_c": forecasts["60"],
        "forecast_120s_c": forecasts["120"],
        "raw_forecast_c": raw_forecasts,
        "anchored_forecast_c": anchored_forecasts,
        "applied_bias_c": applied_bias,
        "temperature_c": round(temp, 2),
        "target_c": round(target, 2),
        "slope_c_per_min": round(slope, 3),
        "confidence_percent": confidence,
        "quality_state": quality_state,
        "mae_ema_c": {k: round(_num(v), 3) for k, v in mae.items()},
        "bias_ema_c": {k: round(_clamp(_num(v), -THERMAL_PREDICTOR_MAX_BIAS_C, THERMAL_PREDICTOR_MAX_BIAS_C), 3) for k, v in bias.items()},
        "last_error_c": {k: round(_num(v), 3) for k, v in last_error.items()},
        "last_signed_error_c": {k: round(_num(v), 3) for k, v in last_signed_error.items()},
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


'''
pattern = re.compile(r"def _thermal_predictor\(.*?\n\n\ndef _thermal_shadow_assist\(", re.S)
match = pattern.search(text)
if not match:
    raise SystemExit("_thermal_predictor block not found")
text = text[:match.start()] + new_function + "def _thermal_shadow_assist(" + text[match.end():]

old_call = "thermal_predictor = _thermal_predictor(model, temp, slope, now, temp_window_span, temp_window_points)"
new_call = "thermal_predictor = _thermal_predictor(model, temp, slope, now, temp_window_span, temp_window_points, target=target)"
if old_call not in text:
    raise SystemExit("Predictor call anchor not found")
text = text.replace(old_call, new_call, 1)

AI.write_text(text, encoding="utf-8")
print("Applied Thermal Predictor v2 accuracy calibration patch")
