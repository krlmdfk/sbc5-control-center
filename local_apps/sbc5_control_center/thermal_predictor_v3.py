#!/usr/bin/env python3
"""SBC5 Thermal Predictor v3 — regime-aware, observe-only thermal forecasting.

This module intentionally has no physical control authority. It consumes the same
model dictionary as ai_cooling.py and returns diagnostic forecasts only.
"""
from __future__ import annotations

import math
from typing import Any

THERMAL_PREDICTOR_HORIZONS_SECONDS = (30, 60, 120)
THERMAL_PREDICTOR_SCHEMA = 3
THERMAL_PREDICTOR_ALGORITHM = "regime_aware_dual_slope_v3"
THERMAL_PREDICTOR_QUEUE_MAX = 72
THERMAL_PREDICTOR_ERROR_ALPHA = 0.16
THERMAL_PREDICTOR_BIAS_ALPHA = 0.10
THERMAL_PREDICTOR_MAX_BIAS_C = 1.5
THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN = 4.0
THERMAL_PREDICTOR_DAMPING = {30: 0.92, 60: 0.70, 120: 0.46}
THERMAL_PREDICTOR_TARGET_ANCHOR = {30: 0.07, 60: 0.16, 120: 0.30}
_FAST_WINDOW_SECONDS = 25.0
_SLOW_WINDOW_SECONDS = 75.0
_CONTEXT_LOAD_LIMIT = {30: 18.0, 60: 22.0, 120: 28.0}
_CONTEXT_PWM_LIMIT = {30: 20.0, 60: 26.0, 120: 35.0}
_HORIZON_WEIGHTS = {30: 0.50, 60: 0.35, 120: 0.15}
_SLOPE_FAST_WEIGHT = {30: 0.72, 60: 0.48, 120: 0.28}


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


def _linear_slope(history: list[list[float]], now: float, window: float, fallback: float) -> tuple[float, float, int]:
    cutoff = now - window
    pts = [(float(ts), float(temp)) for ts, temp in history if float(ts) >= cutoff]
    if len(pts) < 3:
        return fallback, 0.0, len(pts)
    span = pts[-1][0] - pts[0][0]
    if span < min(8.0, window * 0.35):
        return fallback, span, len(pts)
    x0 = pts[0][0]
    xs = [ts - x0 for ts, _ in pts]
    ys = [temp for _, temp in pts]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    den = sum((x - mx) ** 2 for x in xs)
    if den <= 0:
        return fallback, span, len(pts)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den * 60.0
    return _clamp(slope, -THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN, THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN), span, len(pts)


def _context(model: dict[str, Any], state: dict[str, Any], target: float) -> dict[str, Any]:
    bucket = str(model.get("workload_bucket") or model.get("last_workload_bucket") or "low")
    if bucket not in {"idle", "low", "medium", "high"}:
        bucket = "low"
    load = _num(model.get("workload_load_smoothed_percent"), _num(model.get("last_cpu_load_percent"), 0.0))
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


def _context_is_stable(created: dict[str, Any], current: dict[str, Any], horizon: int) -> tuple[bool, str]:
    if str(created.get("bucket")) != str(current.get("bucket")):
        return False, "bucket_changed"
    if abs(_num(created.get("target")) - _num(current.get("target"))) > 0.25:
        return False, "target_changed"
    if abs(_num(created.get("load")) - _num(current.get("load"))) > _CONTEXT_LOAD_LIMIT[horizon]:
        return False, "load_shift"
    if abs(_num(created.get("pwm")) - _num(current.get("pwm"))) > _CONTEXT_PWM_LIMIT[horizon]:
        return False, "pwm_shift"
    return True, "stable"


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
    stats["mae_ema_c"] = round(_ema(stats.get("mae_ema_c"), err, THERMAL_PREDICTOR_ERROR_ALPHA), 3)
    stats["bias_ema_c"] = round(_clamp(_ema(stats.get("bias_ema_c"), signed_error, THERMAL_PREDICTOR_BIAS_ALPHA), -THERMAL_PREDICTOR_MAX_BIAS_C, THERMAL_PREDICTOR_MAX_BIAS_C), 3)
    stats["samples"] = int(_num(stats.get("samples"), 0)) + 1
    stats["last_error_c"] = round(err, 3)
    stats["last_signed_error_c"] = round(signed_error, 3)


def _effective_stats(state: dict[str, Any], bucket: str, horizon: str) -> tuple[float | None, float, int, int]:
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


def thermal_predictor_v3(model: dict[str, Any], temp: float, slope_c_per_min: float, now: float, window_span: float, window_points: int, *, target: float) -> dict[str, Any]:
    raw_state = model.get("thermal_predictor")
    state = raw_state if isinstance(raw_state, dict) else {}
    if int(_num(state.get("schema"), 0)) != THERMAL_PREDICTOR_SCHEMA:
        if state:
            history = model.get("thermal_predictor_history")
            if not isinstance(history, list):
                history = []
            history.append({"schema": int(_num(state.get("schema"), 0)), "algorithm": str(state.get("algorithm") or "unknown"), "archived_epoch": int(now), "average_mae_c": state.get("average_mae_c"), "confidence_percent": state.get("confidence_percent"), "quality_state": state.get("quality_state"), "validated_samples_total": state.get("validated_samples_total")})
            model["thermal_predictor_history"] = history[-4:]
        state = {"schema": THERMAL_PREDICTOR_SCHEMA, "algorithm": THERMAL_PREDICTOR_ALGORITHM, "queue": [], "temp_history": [], "regime_stats": {}, "global_stats": {}, "mae_all_ema_c": {}, "context_rejected_samples": {}, "context_rejected_reasons": {}}

    history = state.get("temp_history")
    if not isinstance(history, list): history = []
    cutoff = now - 90.0
    clean_history = []
    for item in history:
        if not isinstance(item, (list, tuple)) or len(item) != 2: continue
        ts, value = _num(item[0], 0.0), _num(item[1], -273.0)
        if ts >= cutoff and -40.0 <= value <= 150.0: clean_history.append([ts, value])
    clean_history.append([float(now), float(temp)])
    clean_history = clean_history[-32:]
    state["temp_history"] = clean_history

    fallback_slope = _clamp(slope_c_per_min, -THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN, THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN)
    fast_slope, fast_span, fast_points = _linear_slope(clean_history, now, _FAST_WINDOW_SECONDS, fallback_slope)
    slow_slope, slow_span, slow_points = _linear_slope(clean_history, now, _SLOW_WINDOW_SECONDS, fallback_slope)
    context = _context(model, state, target)
    queue = state.get("queue") if isinstance(state.get("queue"), list) else []
    pending = []
    mae_all = state.get("mae_all_ema_c") if isinstance(state.get("mae_all_ema_c"), dict) else {}
    rejected = state.get("context_rejected_samples") if isinstance(state.get("context_rejected_samples"), dict) else {}
    rejected_reasons = state.get("context_rejected_reasons") if isinstance(state.get("context_rejected_reasons"), dict) else {}
    last_error, last_signed_error = {}, {}
    for item in queue:
        if not isinstance(item, dict): continue
        due = _num(item.get("due_epoch"), 0.0); horizon = int(_num(item.get("horizon_seconds"), 0)); key = str(horizon)
        if horizon not in THERMAL_PREDICTOR_HORIZONS_SECONDS: continue
        predicted = _num(item.get("predicted_c"), temp)
        if due > 0 and due <= now:
            signed_error = temp - predicted; err = abs(signed_error)
            mae_all[key] = round(_ema(mae_all.get(key), err, THERMAL_PREDICTOR_ERROR_ALPHA), 3)
            last_error[key] = round(err, 3); last_signed_error[key] = round(signed_error, 3)
            created_context = item.get("context") if isinstance(item.get("context"), dict) else {}
            stable, reason = _context_is_stable(created_context, context, horizon)
            if stable:
                bucket = str(created_context.get("bucket") or context["bucket"])
                _update_stats(_global_bucket(state, key), signed_error); _update_stats(_stats_bucket(state, bucket, key), signed_error)
            else:
                rejected[key] = int(_num(rejected.get(key), 0)) + 1
                reasons = rejected_reasons.setdefault(key, {})
                if not isinstance(reasons, dict): reasons = {}; rejected_reasons[key] = reasons
                reasons[reason] = int(_num(reasons.get(reason), 0)) + 1
        elif due > now - 10.0:
            pending.append(item)

    forecasts={}; raw_forecasts={}; anchored_forecasts={}; applied_bias={}; anchors={}; forcing_map={}; selected_slopes={}; mae_effective={}; bias_effective={}; samples_effective={}; samples_global={}; confidence_by_horizon={}
    bucket=context["bucket"]
    for horizon in THERMAL_PREDICTOR_HORIZONS_SECONDS:
        key=str(horizon); wf=_SLOPE_FAST_WEIGHT[horizon]
        selected_slope=_clamp(fast_slope*wf+slow_slope*(1.0-wf),-THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN,THERMAL_PREDICTOR_MAX_SLOPE_C_PER_MIN)
        selected_slopes[key]=round(selected_slope,3); forcing=_context_forcing(horizon,context); forcing_map[key]=round(forcing,3)
        raw_linear=temp+selected_slope*(horizon/60.0)*THERMAL_PREDICTOR_DAMPING[horizon]+forcing
        anchor=_dynamic_anchor(horizon,fast_slope,context); anchors[key]=round(anchor,3); anchored=raw_linear+(target-raw_linear)*anchor
        eff_mae,eff_bias,regime_samples,global_samples=_effective_stats(state,bucket,key); maturity=_clamp(regime_samples/8.0,0.0,1.0)
        correction=eff_bias*(0.35+0.65*maturity); predicted=round(_clamp(anchored+correction,-20.0,100.0),2)
        forecasts[key]=predicted; raw_forecasts[key]=round(raw_linear,2); anchored_forecasts[key]=round(anchored,2); applied_bias[key]=round(correction,3); bias_effective[key]=round(eff_bias,3); samples_effective[key]=regime_samples; samples_global[key]=global_samples
        if eff_mae is not None: mae_effective[key]=round(eff_mae,3)
        accuracy=0.35 if eff_mae is None else _clamp(1.0-eff_mae/3.0,0.0,1.0); sample_maturity=_clamp((regime_samples+min(global_samples,8)*0.35)/12.0,0.0,1.0); trend_maturity=_clamp(min(fast_span/18.0,slow_span/45.0),0.0,1.0)
        confidence_by_horizon[key]=int(round(_clamp(100.0*(0.48*accuracy+0.32*sample_maturity+0.20*trend_maturity),0.0,97.0)))
        pending.append({"created_epoch":int(now),"due_epoch":int(now+horizon),"horizon_seconds":horizon,"predicted_c":predicted,"context":{"bucket":bucket,"load":context["load"],"pwm":context["pwm"],"target":context["target"]}})

    pending=pending[-THERMAL_PREDICTOR_QUEUE_MAX:]; state["queue"]=pending; state["mae_all_ema_c"]={k:round(_num(v),3) for k,v in mae_all.items()}; state["context_rejected_samples"]={k:int(_num(v)) for k,v in rejected.items()}; state["context_rejected_reasons"]=rejected_reasons
    weighted_mae_num=weighted_mae_den=weighted_all_num=weighted_all_den=weighted_conf=0.0
    for horizon in THERMAL_PREDICTOR_HORIZONS_SECONDS:
        key=str(horizon); weight=_HORIZON_WEIGHTS[horizon]; weighted_conf+=confidence_by_horizon[key]*weight
        if key in mae_effective: weighted_mae_num+=mae_effective[key]*weight; weighted_mae_den+=weight
        if key in mae_all: weighted_all_num+=_num(mae_all[key])*weight; weighted_all_den+=weight
    avg_mae=weighted_mae_num/weighted_mae_den if weighted_mae_den>0 else None; avg_mae_all=weighted_all_num/weighted_all_den if weighted_all_den>0 else None; confidence=int(round(_clamp(weighted_conf,0.0,97.0)))
    if avg_mae is None: quality_state="learning"
    elif avg_mae<=0.75: quality_state="excellent"
    elif avg_mae<=1.25: quality_state="good"
    elif avg_mae<=2.0: quality_state="fair"
    elif avg_mae<=3.0: quality_state="weak"
    else: quality_state="poor"
    state.update({"schema":THERMAL_PREDICTOR_SCHEMA,"algorithm":THERMAL_PREDICTOR_ALGORITHM,"mode":"observe_only","forecast_30s_c":forecasts["30"],"forecast_60s_c":forecasts["60"],"forecast_120s_c":forecasts["120"],"raw_forecast_c":raw_forecasts,"anchored_forecast_c":anchored_forecasts,"dynamic_anchor":anchors,"context_forcing_c":forcing_map,"selected_slope_c_per_min":selected_slopes,"fast_slope_c_per_min":round(fast_slope,3),"slow_slope_c_per_min":round(slow_slope,3),"fast_window_span_seconds":round(fast_span,1),"slow_window_span_seconds":round(slow_span,1),"fast_window_points":fast_points,"slow_window_points":slow_points,"applied_bias_c":applied_bias,"effective_bias_c":bias_effective,"temperature_c":round(temp,2),"target_c":round(target,2),"slope_c_per_min":round(fallback_slope,3),"confidence_percent":confidence,"confidence_by_horizon_percent":confidence_by_horizon,"quality_state":quality_state,"mae_ema_c":mae_effective,"mae_all_ema_c":{k:round(_num(v),3) for k,v in mae_all.items()},"bias_ema_c":bias_effective,"last_error_c":last_error,"last_signed_error_c":last_signed_error,"validated_samples":samples_effective,"validated_samples_global":samples_global,"validated_samples_total":sum(samples_effective.values()),"average_mae_c":round(avg_mae,3) if avg_mae is not None else None,"average_mae_all_c":round(avg_mae_all,3) if avg_mae_all is not None else None,"current_regime":bucket,"context":context,"window_span_seconds":int(round(window_span)),"window_points":int(window_points),"control_output_enabled":False,"updated_epoch":int(now)})
    state["last_context"]={"bucket":bucket,"load":context["load"],"pwm":context["pwm"],"target":context["target"]}; model["thermal_predictor"]=state
    public=dict(state)
    for private_key in ("queue","temp_history","regime_stats","global_stats","last_context"): public.pop(private_key,None)
    return public
