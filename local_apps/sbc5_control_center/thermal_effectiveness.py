#!/usr/bin/env python3
"""Observed post-intervention effectiveness tracker for Thermal Predictor.

The tracker is diagnostic only. It reuses the existing AI cycle and stores compact
aggregates in the durable AI model state. It never changes PWM, gate thresholds or
control policy.
"""
from __future__ import annotations

import math
from typing import Any

HORIZONS = (30, 60, 120)
DEADBAND_C = 0.75
IMPROVEMENT_EPS_C = 0.15
WORSEN_EPS_C = 0.25
EVENT_COOLDOWN_SECONDS = 25
MAX_PENDING = 24
MAX_RECENT = 12
SCHEMA = 1


def _num(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except (TypeError, ValueError):
        return default


def _bucket() -> dict[str, Any]:
    return {"samples": 0, "improved": 0, "neutral": 0, "worsened": 0, "avg_improvement_c": 0.0}


def _state(model: dict[str, Any]) -> dict[str, Any]:
    state = model.get("thermal_effectiveness")
    if not isinstance(state, dict) or int(_num(state.get("schema"), 0)) != SCHEMA:
        state = {
            "schema": SCHEMA,
            "pending": [],
            "recent": [],
            "horizons": {str(h): _bucket() for h in HORIZONS},
            "interventions_total": 0,
            "interventions_up": 0,
            "interventions_down": 0,
        }
        model["thermal_effectiveness"] = state
    state.setdefault("pending", [])
    state.setdefault("recent", [])
    horizons = state.setdefault("horizons", {})
    for horizon in HORIZONS:
        horizons.setdefault(str(horizon), _bucket())
    return state


def _classify(start_error: float, current_error: float) -> tuple[str, float]:
    improvement = start_error - current_error
    if current_error <= DEADBAND_C or improvement >= IMPROVEMENT_EPS_C:
        return "improved", improvement
    if current_error > start_error + WORSEN_EPS_C:
        return "worsened", improvement
    return "neutral", improvement


def _update_bucket(bucket: dict[str, Any], outcome: str, improvement: float) -> None:
    old_n = max(0, int(_num(bucket.get("samples"), 0)))
    old_avg = _num(bucket.get("avg_improvement_c"), 0.0)
    new_n = old_n + 1
    bucket["samples"] = new_n
    bucket[outcome] = max(0, int(_num(bucket.get(outcome), 0))) + 1
    bucket["avg_improvement_c"] = round(((old_avg * old_n) + improvement) / new_n, 3)


def _score(bucket: dict[str, Any]) -> float | None:
    samples = max(0, int(_num(bucket.get("samples"), 0)))
    if samples <= 0:
        return None
    improved = max(0, int(_num(bucket.get("improved"), 0)))
    neutral = max(0, int(_num(bucket.get("neutral"), 0)))
    return round(100.0 * (improved + 0.5 * neutral) / samples, 1)


def _summary(state: dict[str, Any]) -> dict[str, Any]:
    horizons = state.get("horizons") if isinstance(state.get("horizons"), dict) else {}
    per_horizon: dict[str, Any] = {}
    total_samples = improved = neutral = worsened = 0
    weighted_improvement = 0.0
    for horizon in HORIZONS:
        bucket = horizons.get(str(horizon)) if isinstance(horizons.get(str(horizon)), dict) else _bucket()
        samples = max(0, int(_num(bucket.get("samples"), 0)))
        imp = max(0, int(_num(bucket.get("improved"), 0)))
        neu = max(0, int(_num(bucket.get("neutral"), 0)))
        bad = max(0, int(_num(bucket.get("worsened"), 0)))
        avg_imp = _num(bucket.get("avg_improvement_c"), 0.0)
        per_horizon[str(horizon)] = {
            "samples": samples,
            "improved": imp,
            "neutral": neu,
            "worsened": bad,
            "score_percent": _score(bucket),
            "avg_improvement_c": round(avg_imp, 3),
        }
        total_samples += samples
        improved += imp
        neutral += neu
        worsened += bad
        weighted_improvement += avg_imp * samples
    score = None if total_samples <= 0 else round(100.0 * (improved + 0.5 * neutral) / total_samples, 1)
    return {
        "mode": "observe_only",
        "samples": total_samples,
        "score_percent": score,
        "improved": improved,
        "neutral": neutral,
        "worsened": worsened,
        "avg_improvement_c": None if total_samples <= 0 else round(weighted_improvement / total_samples, 3),
        "interventions_total": max(0, int(_num(state.get("interventions_total"), 0))),
        "interventions_up": max(0, int(_num(state.get("interventions_up"), 0))),
        "interventions_down": max(0, int(_num(state.get("interventions_down"), 0))),
        "pending": len(state.get("pending") or []),
        "horizons": per_horizon,
        "recent": list(state.get("recent") or [])[-MAX_RECENT:],
    }


def update(
    *, model: dict[str, Any], now: float, temperature_c: float, target_c: float,
    applied_delta_pp: int, decision_reason: str = "",
) -> dict[str, Any]:
    """Update observed effectiveness and return a read-only summary.

    Each non-zero Thermal Predictor intervention becomes one observation event.
    Existing events are sampled at +30/+60/+120 s by the normal AI cycle. Multiple
    overlapping interventions are allowed, but identical-direction events are
    rate-limited so one sustained nudge does not dominate the score.
    """
    state = _state(model)
    pending = state.get("pending") if isinstance(state.get("pending"), list) else []
    recent = state.get("recent") if isinstance(state.get("recent"), list) else []
    horizons = state.get("horizons") if isinstance(state.get("horizons"), dict) else {}

    kept: list[dict[str, Any]] = []
    for event in pending:
        if not isinstance(event, dict):
            continue
        started = _num(event.get("started_epoch"), now)
        elapsed = max(0.0, now - started)
        start_error = max(0.0, _num(event.get("start_abs_error_c"), 0.0))
        sampled = event.get("sampled") if isinstance(event.get("sampled"), dict) else {}
        for horizon in HORIZONS:
            key = str(horizon)
            if sampled.get(key) or elapsed < horizon:
                continue
            current_error = abs(temperature_c - _num(event.get("target_c"), target_c))
            outcome, improvement = _classify(start_error, current_error)
            bucket = horizons.setdefault(key, _bucket())
            _update_bucket(bucket, outcome, improvement)
            sampled[key] = True
            recent.append({
                "horizon_s": horizon,
                "delta_pp": int(_num(event.get("delta_pp"), 0)),
                "outcome": outcome,
                "improvement_c": round(improvement, 3),
                "start_abs_error_c": round(start_error, 3),
                "end_abs_error_c": round(current_error, 3),
                "decision_reason": str(event.get("decision_reason") or ""),
                "resolved_epoch": round(now, 3),
            })
        event["sampled"] = sampled
        if not all(sampled.get(str(h)) for h in HORIZONS) and elapsed <= 180:
            kept.append(event)

    delta = int(applied_delta_pp)
    if delta:
        last_same = None
        for event in reversed(kept):
            if int(_num(event.get("delta_pp"), 0)) * delta > 0:
                last_same = event
                break
        can_add = last_same is None or now - _num(last_same.get("started_epoch"), 0.0) >= EVENT_COOLDOWN_SECONDS
        if can_add:
            kept.append({
                "started_epoch": round(now, 3),
                "target_c": round(target_c, 3),
                "start_temp_c": round(temperature_c, 3),
                "start_abs_error_c": round(abs(temperature_c - target_c), 3),
                "delta_pp": delta,
                "decision_reason": str(decision_reason or ""),
                "sampled": {},
            })
            state["interventions_total"] = max(0, int(_num(state.get("interventions_total"), 0))) + 1
            key = "interventions_up" if delta > 0 else "interventions_down"
            state[key] = max(0, int(_num(state.get(key), 0))) + 1

    state["pending"] = kept[-MAX_PENDING:]
    state["recent"] = recent[-MAX_RECENT:]
    state["horizons"] = horizons
    state["updated_epoch"] = round(now, 3)
    model["thermal_effectiveness"] = state
    return _summary(state)
