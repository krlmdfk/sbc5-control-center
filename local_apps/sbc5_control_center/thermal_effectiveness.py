#!/usr/bin/env python3
"""Observed post-intervention effectiveness tracker for Thermal Predictor.

The tracker is diagnostic only. It reuses the existing AI cycle and stores compact
aggregates in a dedicated durable checkpoint as well as the AI model mirror. It
never changes PWM, gate thresholds or control policy.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

HORIZONS = (30, 60, 120)
DEADBAND_C = 0.75
IMPROVEMENT_EPS_C = 0.15
WORSEN_EPS_C = 0.25
EVENT_COOLDOWN_SECONDS = 25
MAX_PENDING = 24
MAX_RECENT = 12
SCHEMA = 2
STATE_PATH = Path(os.environ.get("SBC5_THERMAL_EFFECTIVENESS_STATE", "/data/thermal_effectiveness.json"))


def _num(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except (TypeError, ValueError):
        return default


def _bucket() -> dict[str, Any]:
    return {"samples": 0, "improved": 0, "neutral": 0, "worsened": 0, "avg_improvement_c": 0.0}


def _new_state() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "pending": [],
        "recent": [],
        "horizons": {str(h): _bucket() for h in HORIZONS},
        "interventions_total": 0,
        "interventions_up": 0,
        "interventions_down": 0,
    }


def _normalize(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    schema = int(_num(raw.get("schema"), 0))
    if schema not in {1, SCHEMA}:
        return None
    state = dict(raw)
    state["schema"] = SCHEMA
    state.setdefault("pending", [])
    state.setdefault("recent", [])
    horizons = state.setdefault("horizons", {})
    if not isinstance(horizons, dict):
        horizons = {}
        state["horizons"] = horizons
    for horizon in HORIZONS:
        bucket = horizons.get(str(horizon))
        if not isinstance(bucket, dict):
            bucket = _bucket()
            horizons[str(horizon)] = bucket
        for key in ("samples", "improved", "neutral", "worsened"):
            bucket[key] = max(0, int(_num(bucket.get(key), 0)))
        bucket["avg_improvement_c"] = round(_num(bucket.get("avg_improvement_c"), 0.0), 3)
    for key in ("interventions_total", "interventions_up", "interventions_down"):
        state[key] = max(0, int(_num(state.get(key), 0)))
    return state


def _read_checkpoint() -> dict[str, Any] | None:
    try:
        return _normalize(json.loads(STATE_PATH.read_text(encoding="utf-8")))
    except Exception:
        return None


def _write_checkpoint(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=STATE_PATH.name + ".", suffix=".tmp", dir=str(STATE_PATH.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, STATE_PATH)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def _state(model: dict[str, Any]) -> dict[str, Any]:
    """Load the most durable tracker state without resetting on wrapper restarts."""
    checkpoint = _read_checkpoint()
    model_state = _normalize(model.get("thermal_effectiveness"))
    if checkpoint is not None and model_state is not None:
        # Prefer the source with more completed evidence. This also allows a
        # seamless schema-1 migration from the 3.1.25 model mirror.
        checkpoint_score = sum(int(_num(b.get("samples"), 0)) for b in checkpoint.get("horizons", {}).values() if isinstance(b, dict))
        model_score = sum(int(_num(b.get("samples"), 0)) for b in model_state.get("horizons", {}).values() if isinstance(b, dict))
        state = checkpoint if (checkpoint_score, checkpoint.get("interventions_total", 0)) >= (model_score, model_state.get("interventions_total", 0)) else model_state
    else:
        state = checkpoint or model_state or _new_state()
    state["schema"] = SCHEMA
    model["thermal_effectiveness"] = state
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
        "storage": "durable_checkpoint",
        "schema": SCHEMA,
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
    changed = False

    kept: list[dict[str, Any]] = []
    for event in pending:
        if not isinstance(event, dict):
            changed = True
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
            changed = True
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
        else:
            changed = True

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
            changed = True

    state["pending"] = kept[-MAX_PENDING:]
    state["recent"] = recent[-MAX_RECENT:]
    state["horizons"] = horizons
    if changed:
        state["updated_epoch"] = round(now, 3)
        _write_checkpoint(state)
    model["thermal_effectiveness"] = state
    return _summary(state)
