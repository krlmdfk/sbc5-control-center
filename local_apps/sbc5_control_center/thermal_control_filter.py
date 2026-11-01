#!/usr/bin/env python3
"""SBC5 thermal control signal conditioning for Adaptive PWM.

This module turns the raw CPU temperature into a control-grade signal without
weakening the safety path. Raw temperature remains authoritative for emergency
handoff; only the normal Adaptive PWM error/curve path consumes T_control.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
import time
from pathlib import Path
from statistics import median
from typing import Any

SCHEMA = 2
HISTORY_SECONDS = 180.0
MAX_HISTORY = 96
ALPHA_RISE = 0.56
ALPHA_FALL = 0.30
SPIKE_THRESHOLD_C = 1.35
TREND_FAST_WINDOW = 30.0
TREND_SLOW_WINDOW = 120.0
TREND_CONFIRM_FAST_C_PER_MIN = 0.12
TREND_CONFIRM_SLOW_C_PER_MIN = 0.05
TREND_FUSED_FAST_WEIGHT = 0.65
TREND_FUSED_SLOW_WEIGHT = 0.35
REVERSAL_HOLD_CYCLES = 2
DIRECTION_CONFIRM_CYCLES = 2


def _num(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except (TypeError, ValueError):
        return default


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _load(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass


def _history(raw: Any, now: float) -> list[list[float]]:
    cutoff = now - HISTORY_SECONDS
    out: list[list[float]] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                continue
            ts, temp = _num(item[0], -1.0), _num(item[1], -273.0)
            if ts >= cutoff and -40.0 <= temp <= 150.0:
                out.append([ts, temp])
    return out[-MAX_HISTORY:]


def _robust_slope(history: list[list[float]], now: float, window: float) -> float:
    cutoff = now - window
    pts = [(float(ts), float(temp)) for ts, temp in history if float(ts) >= cutoff]
    if len(pts) < 3:
        return 0.0
    slopes: list[float] = []
    for i, (t0, y0) in enumerate(pts[:-1]):
        for t1, y1 in pts[i + 1 :]:
            dt = t1 - t0
            if dt >= 2.0:
                slopes.append((y1 - y0) / dt * 60.0)
    if not slopes:
        return 0.0
    return round(_clamp(float(median(slopes)), -6.0, 6.0), 3)


def update_signal(state: dict[str, Any], *, raw_c: float, target_c: float, now: float) -> dict[str, Any]:
    history = _history(state.get("control_history"), now)
    raw_history = _history(state.get("raw_history"), now)
    raw_history.append([now, raw_c])
    raw_history = raw_history[-MAX_HISTORY:]

    last_raw = [float(v) for _, v in raw_history[-3:]]
    median3 = float(median(last_raw)) if last_raw else raw_c
    previous_control = _num(state.get("control_c"), median3)
    spike_rejected = bool(len(last_raw) >= 3 and abs(raw_c - median3) >= SPIKE_THRESHOLD_C)
    conditioned = median3 if spike_rejected else raw_c
    alpha = ALPHA_RISE if conditioned >= previous_control else ALPHA_FALL
    control_c = previous_control + alpha * (conditioned - previous_control)
    control_c = round(_clamp(control_c, -20.0, 120.0), 3)

    history.append([now, control_c])
    history = history[-MAX_HISTORY:]
    trend30 = _robust_slope(history, now, TREND_FAST_WINDOW)
    trend120 = _robust_slope(history, now, TREND_SLOW_WINDOW)
    trend_fused = round(
        _clamp(
            TREND_FUSED_FAST_WEIGHT * trend30 + TREND_FUSED_SLOW_WEIGHT * trend120,
            -6.0,
            6.0,
        ),
        3,
    )
    trend_fused_milli = int(round(trend_fused * 1000.0))

    candidate = "neutral"
    if (
        trend30 >= TREND_CONFIRM_FAST_C_PER_MIN
        and trend120 >= TREND_CONFIRM_SLOW_C_PER_MIN
    ) or control_c >= target_c + 0.85:
        candidate = "hot"
    elif (
        trend30 <= -TREND_CONFIRM_FAST_C_PER_MIN
        and trend120 <= -TREND_CONFIRM_SLOW_C_PER_MIN
        and control_c <= target_c - 0.15
    ):
        candidate = "cool"

    previous_candidate = str(state.get("candidate_direction") or "neutral")
    streak = int(_num(state.get("candidate_streak"), 0))
    if candidate == previous_candidate:
        streak += 1
    else:
        streak = 1

    confirmed = str(state.get("confirmed_direction") or "neutral")
    reverse_hold = max(0, int(_num(state.get("reverse_hold_cycles"), 0)))
    if reverse_hold > 0:
        reverse_hold -= 1

    if candidate in {"hot", "cool"} and streak >= DIRECTION_CONFIRM_CYCLES:
        if confirmed in {"hot", "cool"} and candidate != confirmed:
            if reverse_hold <= 0:
                reverse_hold = REVERSAL_HOLD_CYCLES
            confirmed = "neutral"
        elif reverse_hold <= 0:
            confirmed = candidate
    elif candidate == "neutral" and reverse_hold <= 0:
        confirmed = "neutral"

    quality = "good"
    if spike_rejected:
        quality = "spike_filtered"
    elif len(history) < 4:
        quality = "warming_up"
    elif abs(trend30 - trend120) > 1.5:
        quality = "transient"

    return {
        "schema": SCHEMA,
        "updated_epoch": round(now, 3),
        "raw_c": round(raw_c, 3),
        "median3_c": round(median3, 3),
        "control_c": control_c,
        "target_c": round(target_c, 3),
        "trend_30s_c_per_min": trend30,
        "trend_120s_c_per_min": trend120,
        "trend_fused_c_per_min": trend_fused,
        "trend_fused_milli_c_per_min": trend_fused_milli,
        "trend_fused_fast_weight": TREND_FUSED_FAST_WEIGHT,
        "trend_fused_slow_weight": TREND_FUSED_SLOW_WEIGHT,
        "candidate_direction": candidate,
        "candidate_streak": streak,
        "confirmed_direction": confirmed,
        "reverse_hold_cycles": reverse_hold,
        "spike_rejected": spike_rejected,
        "quality": quality,
        "alpha_used": alpha,
        "raw_history": raw_history,
        "control_history": history,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--temp-milli", type=int, required=True)
    parser.add_argument("--target-milli", type=int, required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--mirror", required=True)
    parser.add_argument("--now", type=float, default=0.0)
    args = parser.parse_args()

    now = args.now if args.now > 0 else time.time()
    state_path = Path(args.state)
    mirror_path = Path(args.mirror)
    state = _load(state_path)
    result = update_signal(
        state,
        raw_c=args.temp_milli / 1000.0,
        target_c=args.target_milli / 1000.0,
        now=now,
    )
    _atomic_write(state_path, result)
    public = {k: v for k, v in result.items() if k not in {"raw_history", "control_history"}}
    _atomic_write(mirror_path, public)

    print(
        "\t".join(
            [
                str(int(round(result["control_c"] * 1000.0))),
                str(result["trend_30s_c_per_min"]),
                str(result["trend_120s_c_per_min"]),
                str(result["trend_fused_c_per_min"]),
                str(result["trend_fused_milli_c_per_min"]),
                str(result["confirmed_direction"]),
                "1" if result["spike_rejected"] else "0",
                str(result["candidate_streak"]),
                str(result["reverse_hold_cycles"]),
                str(result["quality"]),
                str(int(round(result["median3_c"] * 1000.0))),
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
