#!/usr/bin/env python3
"""SBC5 AI Cooling v5 — hierarchical continuous learning layer.

This module intentionally wraps the proven bucket-aware v4 learner instead of
replacing it. v4 remains responsible for qualification, persistence, grid advice,
Thermal Predictor and all existing safety metadata. v5 adds a conservative global
continuous-load model above the v4 state and can transfer learned cooling behavior
between workload buckets when direct qualified samples are sparse.

No additional polling loop is created. The wrapper runs only when the existing
AI evaluator invokes ``step`` and preserves the legacy stdout contract consumed by
run_legacy.sh.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any

V5_SCHEMA = 1
V5_POLICY = "hierarchical_continuous_v5"
ANCHOR_STEP_PERCENT = 10
ANCHOR_MAX_WEIGHT = 180.0
DIRECT_BLEND_MAX = 0.78
ASSIST_MIN_EFFECTIVE_CONFIDENCE = 72
TRANSIENT_WEIGHT_MAX = 0.28
WORKLOAD_CENTERS = {"idle": 5.0, "low": 20.0, "medium": 45.0, "high": 75.0}


def _legacy_path() -> Path:
    """Return the v4 compatibility layer that injects Thermal Predictor v3.x.

    Runtime images expose that wrapper as /ai_cooling_v4.py.  Loading the raw
    /ai_cooling_legacy.py here would bypass the predictor injection and leave the
    transported thermal_predictor payload frozen at its last persisted value.
    """
    runtime_v4 = Path("/ai_cooling_v4.py")
    if runtime_v4.is_file():
        return runtime_v4
    return Path(__file__).with_name("ai_cooling.py")


def _load_legacy():
    path = _legacy_path()
    spec = importlib.util.spec_from_file_location("sbc5_ai_cooling_v4", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load legacy AI Cooling module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = _load_legacy()


def _num(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except (TypeError, ValueError):
        return default


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_json(path: str | Path, payload: dict[str, Any], *, durable: bool = False) -> None:
    writer = getattr(legacy, "_atomic_json", None)
    if callable(writer):
        writer(Path(path), payload, durable=durable)
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".v5.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if durable:
        with tmp.open("r+") as handle:
            handle.flush()
            os.fsync(handle.fileno())
    os.replace(tmp, p)


def _bucket_midpoint(bucket: str) -> float:
    return WORKLOAD_CENTERS.get(str(bucket or "low"), 20.0)


def _target_state(model: dict[str, Any], target_key: str) -> dict[str, Any]:
    v5 = model.setdefault("hierarchical_v5", {})
    if not isinstance(v5, dict):
        v5 = {}
        model["hierarchical_v5"] = v5
    targets = v5.setdefault("targets", {})
    if not isinstance(targets, dict):
        targets = {}
        v5["targets"] = targets
    target = targets.setdefault(target_key, {})
    if not isinstance(target, dict):
        target = {}
        targets[target_key] = target
    target.setdefault("anchors", {})
    target.setdefault("bucket_stats", {})
    return target


def _anchor_pairs(load: float) -> list[tuple[int, float]]:
    load = _clamp(load, 0.0, 100.0)
    lo = int(math.floor(load / ANCHOR_STEP_PERCENT) * ANCHOR_STEP_PERCENT)
    hi = int(math.ceil(load / ANCHOR_STEP_PERCENT) * ANCHOR_STEP_PERCENT)
    lo = max(0, min(100, lo))
    hi = max(0, min(100, hi))
    if lo == hi:
        return [(lo, 1.0)]
    frac = (load - lo) / float(hi - lo)
    return [(lo, 1.0 - frac), (hi, frac)]


def _update_anchor(anchors: dict[str, Any], key: int, prediction: float, weight: float, now: float) -> None:
    raw = anchors.get(str(key))
    item = raw if isinstance(raw, dict) else {}
    old_weight = _num(item.get("weight"), 0.0)
    old_pwm = _num(item.get("ema_pwm"), prediction)
    effective = max(0.0, min(1.0, weight))
    alpha = _clamp(effective / max(1.0 + old_weight, 1.0), 0.03, 0.24)
    item["ema_pwm"] = round(old_pwm + alpha * (prediction - old_pwm), 3)
    item["weight"] = round(min(ANCHOR_MAX_WEIGHT, old_weight + effective), 3)
    item["samples"] = int(_num(item.get("samples"), 0)) + 1
    item["updated_epoch"] = int(now)
    anchors[str(key)] = item


def _update_global_model(target_state: dict[str, Any], load: float, prediction: float, weight: float, now: float) -> None:
    anchors = target_state.setdefault("anchors", {})
    if not isinstance(anchors, dict):
        anchors = {}
        target_state["anchors"] = anchors
    for key, share in _anchor_pairs(load):
        if share > 0:
            _update_anchor(anchors, key, prediction, weight * share, now)


def _global_prediction(target_state: dict[str, Any], load: float):
    anchors = target_state.get("anchors")
    if not isinstance(anchors, dict) or not anchors:
        return None, 0, 100.0, "none"
    parsed: list[tuple[float, dict[str, Any]]] = []
    for raw_key, raw_item in anchors.items():
        if not isinstance(raw_item, dict):
            continue
        try:
            x = float(raw_key)
        except (TypeError, ValueError):
            continue
        if _num(raw_item.get("weight"), 0.0) > 0:
            parsed.append((x, raw_item))
    if not parsed:
        return None, 0, 100.0, "none"
    parsed.sort(key=lambda pair: pair[0])
    left = None
    right = None
    for x, item in parsed:
        if x <= load:
            left = (x, item)
        if x >= load and right is None:
            right = (x, item)
    if left is None:
        left = parsed[0]
    if right is None:
        right = parsed[-1]
    lx, li = left
    rx, ri = right
    if lx == rx:
        prediction = _num(li.get("ema_pwm"), 0.0)
        weight = _num(li.get("weight"), 0.0)
        distance = abs(load - lx)
        source = f"anchor:{int(lx)}"
    else:
        frac = _clamp((load - lx) / (rx - lx), 0.0, 1.0)
        prediction = _num(li.get("ema_pwm"), 0.0) * (1.0 - frac) + _num(ri.get("ema_pwm"), 0.0) * frac
        weight = min(_num(li.get("weight"), 0.0), _num(ri.get("weight"), 0.0))
        distance = min(abs(load - lx), abs(load - rx))
        source = f"interp:{int(lx)}-{int(rx)}"
    evidence = 1.0 - math.exp(-max(0.0, weight) / 8.0)
    distance_factor = _clamp(1.0 - distance / 35.0, 0.25, 1.0)
    confidence = int(round(_clamp(96.0 * evidence * distance_factor, 0.0, 96.0)))
    return prediction, confidence, distance, source


def _bucket_stats(target_state: dict[str, Any], bucket: str) -> dict[str, Any]:
    stats = target_state.setdefault("bucket_stats", {})
    if not isinstance(stats, dict):
        stats = {}
        target_state["bucket_stats"] = stats
    item = stats.setdefault(bucket, {})
    if not isinstance(item, dict):
        item = {}
        stats[bucket] = item
    return item


def _update_bucket_stats(target_state: dict[str, Any], bucket: str, direct_prediction: float, qualified_n: int, confidence: int) -> None:
    item = _bucket_stats(target_state, bucket)
    item.update({"prediction": round(direct_prediction, 2), "qualified_n": qualified_n, "confidence": confidence, "updated_epoch": int(time.time())})


def _transfer_prediction(target_state: dict[str, Any], bucket: str, global_prediction: float | None, global_confidence: int):
    if global_prediction is None:
        return None, 0, "none"
    stats = target_state.get("bucket_stats")
    if not isinstance(stats, dict):
        return global_prediction, global_confidence, "global"
    candidates: list[tuple[float, dict[str, Any]]] = []
    center = _bucket_midpoint(bucket)
    for name, item in stats.items():
        if name == bucket or not isinstance(item, dict):
            continue
        qn = int(_num(item.get("qualified_n"), 0))
        if qn <= 0:
            continue
        candidates.append((abs(center - _bucket_midpoint(name)), item))
    if not candidates:
        return global_prediction, global_confidence, "global"
    candidates.sort(key=lambda pair: pair[0])
    distance, item = candidates[0]
    neighbor = _num(item.get("prediction"), global_prediction)
    neighbor_conf = int(_num(item.get("confidence"), 0))
    weight = _clamp(neighbor_conf / 100.0 * (1.0 - distance / 100.0), 0.0, 0.45)
    prediction = global_prediction * (1.0 - weight) + neighbor * weight
    confidence = int(round(_clamp(global_confidence * (1.0 - weight * 0.25) + neighbor_conf * weight * 0.45, 0.0, 96.0)))
    return prediction, confidence, "global_plus_neighbor"


def _apply_hierarchical_step(model: dict[str, Any], status: dict[str, Any], fields: list[str]):
    target = _num(status.get("target_temp_c"), 49.0)
    target_key = f"{target:.1f}"
    bucket = str(status.get("workload_bucket") or "low")
    load = _num(status.get("cpu_load_smoothed_percent"), _num(status.get("cpu_load_percent"), 0.0))
    target_state = _target_state(model, target_key)

    direct_qn = int(_num(status.get("bin_qualified_samples"), 0))
    direct_conf = int(_num(status.get("confidence_percent"), 0))
    direct_prediction = _num(status.get("prediction_pwm_percent"), _num(status.get("baseline_pwm_percent"), 0.0))
    qualified = bool(status.get("qualified_sample"))
    if direct_qn > 0:
        _update_bucket_stats(target_state, bucket, direct_prediction, direct_qn, direct_conf)
    if qualified:
        _update_global_model(target_state, load, direct_prediction, 1.0, time.time())

    global_prediction, global_confidence, global_distance, source = _global_prediction(target_state, load)
    transfer_prediction, transfer_confidence, transfer_source = _transfer_prediction(target_state, bucket, global_prediction, global_confidence)

    maturity = _clamp(direct_qn / 30.0, 0.0, 1.0)
    direct_blend = DIRECT_BLEND_MAX * maturity
    if transfer_prediction is None:
        effective_prediction = direct_prediction
        effective_confidence = direct_conf
        transfer_used = False
    elif direct_qn <= 0:
        effective_prediction = transfer_prediction
        effective_confidence = transfer_confidence
        transfer_used = True
    else:
        effective_prediction = direct_prediction * direct_blend + transfer_prediction * (1.0 - direct_blend)
        effective_confidence = int(round(_clamp(direct_conf * direct_blend + transfer_confidence * (1.0 - direct_blend), 0.0, 96.0)))
        transfer_used = direct_blend < 0.999

    status.update({
        "hierarchical_model": {
            "schema": V5_SCHEMA,
            "policy": V5_POLICY,
            "target_key": target_key,
            "global_prediction_pwm_percent": round(global_prediction, 2) if global_prediction is not None else None,
            "global_confidence_percent": global_confidence,
            "global_distance_percent": round(global_distance, 1),
            "global_source": source,
            "transfer_prediction_pwm_percent": round(transfer_prediction, 2) if transfer_prediction is not None else None,
            "transfer_confidence_percent": transfer_confidence,
            "transfer_source": transfer_source,
        },
        "direct_prediction_pwm_percent": round(direct_prediction, 2),
        "direct_confidence_percent": direct_conf,
        "direct_model_maturity_percent": int(round(maturity * 100.0)),
        "direct_blend_percent": int(round(direct_blend * 100.0)),
        "global_prediction_pwm_percent": round(global_prediction, 2) if global_prediction is not None else None,
        "global_confidence_percent": global_confidence,
        "transfer_prediction_pwm_percent": round(transfer_prediction, 2) if transfer_prediction is not None else None,
        "transfer_confidence_percent": transfer_confidence,
        "transfer_source": transfer_source,
        "effective_prediction_pwm_percent": round(effective_prediction, 2),
        "effective_confidence_percent": effective_confidence,
        "transfer_used": transfer_used,
        "learning_policy": V5_POLICY,
    })

    if str(status.get("mode")) == "assist" and str(status.get("control_mode")) == "automatic" and effective_confidence >= ASSIST_MIN_EFFECTIVE_CONFIDENCE:
        baseline = int(_num(status.get("baseline_pwm_percent"), 0))
        min_safe = int(_num(status.get("min_safe_pwm_percent"), 0))
        maximum = int(_num(status.get("max_pwm_percent"), 100))
        assist_limit = int(_num(status.get("assist_limit_percent"), 10))
        temp_error = _num(status.get("temperature_error_c"), 0.0)
        deadband = _num(status.get("deadband_c"), 0.75)
        bounded_target = int(round(_clamp(effective_prediction, baseline - assist_limit, baseline + assist_limit)))
        if temp_error > deadband and bounded_target < baseline:
            bounded_target = baseline
        elif temp_error < -deadband and bounded_target > baseline:
            bounded_target = baseline
        delta = int(_clamp(bounded_target - baseline, -2, 2))
        output = int(_clamp(baseline + delta, min_safe, maximum))
        status["output_pwm_percent"] = output
        status["correction_percent"] = output - baseline
        status["state"] = "assist"
        status["reason"] = "hierarchical_nudge" if output != baseline else "hierarchical_agrees"
        if len(fields) >= 4:
            fields[0] = str(output)
            fields[1] = str(output - baseline)
            fields[2] = "assist"
            fields[3] = status["reason"]

    if len(fields) < 22:
        fields.extend([""] * (22 - len(fields)))
    fields[14] = str(int(_num(status.get("direct_confidence_percent"), 0)))
    fields[15] = str(int(_num(status.get("effective_confidence_percent"), 0)))
    fields[16] = str(int(_num(status.get("global_confidence_percent"), 0)))
    fields[17] = str(round(_num(status.get("direct_prediction_pwm_percent"), -1.0), 2))
    fields[18] = str(round(_num(status.get("global_prediction_pwm_percent"), -1.0), 2))
    fields[19] = str(round(_num(status.get("effective_prediction_pwm_percent"), -1.0), 2))
    fields[20] = str(status.get("transfer_source") or "none")
    fields[21] = str(int(_num(status.get("direct_blend_percent"), 0)))
    return model, status, fields


def step_capture(args) -> tuple[int, dict[str, Any], list[str]]:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        rc = legacy.step(args)
    line = stream.getvalue().strip().splitlines()[-1] if stream.getvalue().strip() else ""
    fields = line.split("|") if line else []
    status_path = Path(args.status)
    status = _read_json(status_path)
    model_path = Path(args.model)
    model = _read_json(model_path)
    if rc != 0 or not isinstance(status, dict):
        return rc, status, fields
    model, status, fields = _apply_hierarchical_step(model, status, fields)
    _write_json(model_path, model, durable=True)
    _write_json(status_path, status, durable=True)
    if getattr(args, "mirror", None):
        _write_json(Path(args.mirror), status, durable=False)
    print("|".join(fields))
    return rc, status, fields


def main() -> int:
    parser = legacy.build_parser()
    args = parser.parse_args()
    rc, _, _ = step_capture(args)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())