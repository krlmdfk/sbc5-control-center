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
    runtime = Path("/ai_cooling_legacy.py")
    if runtime.is_file():
        return runtime
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
    # Reuse the proven atomic writer from v4 when available.
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


def _argv_value(name: str, default: str = "") -> str:
    try:
        idx = sys.argv.index(name)
        return sys.argv[idx + 1]
    except (ValueError, IndexError):
        return default


def _anchor_key(load: float) -> int:
    return int(_clamp(round(load / ANCHOR_STEP_PERCENT) * ANCHOR_STEP_PERCENT, 0, 100))


def _update_anchor(target_state: dict[str, Any], load: float, candidate_pwm: float, weight: float) -> None:
    if weight <= 0:
        return
    anchors = target_state.setdefault("anchors", {})
    if not isinstance(anchors, dict):
        anchors = {}
        target_state["anchors"] = anchors

    lo = int(_clamp(math.floor(load / ANCHOR_STEP_PERCENT) * ANCHOR_STEP_PERCENT, 0, 100))
    hi = int(_clamp(math.ceil(load / ANCHOR_STEP_PERCENT) * ANCHOR_STEP_PERCENT, 0, 100))
    pairs: list[tuple[int, float]]
    if lo == hi:
        pairs = [(lo, 1.0)]
    else:
        frac = (load - lo) / float(hi - lo)
        pairs = [(lo, 1.0 - frac), (hi, frac)]

    for key, share in pairs:
        effective = max(0.0, weight * share)
        if effective <= 0:
            continue
        raw = anchors.get(str(key))
        item = raw if isinstance(raw, dict) else {}
        old_weight = _num(item.get("weight"), 0.0)
        old_mean = _num(item.get("mean_pwm"), candidate_pwm)
        old_dev = _num(item.get("dev_pwm"), 0.0)
        alpha = effective / max(effective + min(old_weight, ANCHOR_MAX_WEIGHT), 1e-6)
        alpha = _clamp(alpha, 0.015, 0.35)
        mean = old_mean + alpha * (candidate_pwm - old_mean)
        dev = old_dev + alpha * (abs(candidate_pwm - mean) - old_dev)
        item.update({
            "mean_pwm": round(mean, 3),
            "dev_pwm": round(max(0.0, dev), 3),
            "weight": round(min(ANCHOR_MAX_WEIGHT, old_weight + effective), 3),
            "updates": int(_num(item.get("updates"), 0)) + 1,
            "last_load_percent": round(load, 1),
            "last_candidate_pwm": round(candidate_pwm, 2),
            "updated_epoch": int(time.time()),
        })
        anchors[str(key)] = item


def _nearest_anchor_items(target_state: dict[str, Any], load: float) -> list[tuple[float, dict[str, Any]]]:
    anchors = target_state.get("anchors")
    if not isinstance(anchors, dict):
        return []
    out: list[tuple[float, dict[str, Any]]] = []
    for raw_key, raw_item in anchors.items():
        if not isinstance(raw_item, dict) or _num(raw_item.get("weight"), 0.0) <= 0:
            continue
        try:
            x = float(raw_key)
        except (TypeError, ValueError):
            continue
        out.append((x, raw_item))
    return sorted(out, key=lambda pair: pair[0])


def _global_prediction(target_state: dict[str, Any], load: float) -> tuple[float | None, int, float, str]:
    items = _nearest_anchor_items(target_state, load)
    if not items:
        return None, 0, 100.0, "none"

    left = None
    right = None
    for x, item in items:
        if x <= load:
            left = (x, item)
        if x >= load and right is None:
            right = (x, item)
    if left is None:
        left = items[0]
    if right is None:
        right = items[-1]

    lx, li = left
    rx, ri = right
    if lx == rx:
        prediction = _num(li.get("mean_pwm"), 0.0)
        support = _num(li.get("weight"), 0.0)
        dev = _num(li.get("dev_pwm"), 6.0)
    else:
        frac = _clamp((load - lx) / (rx - lx), 0.0, 1.0)
        prediction = _num(li.get("mean_pwm"), 0.0) * (1.0 - frac) + _num(ri.get("mean_pwm"), 0.0) * frac
        support = _num(li.get("weight"), 0.0) * (1.0 - frac) + _num(ri.get("weight"), 0.0) * frac
        dev = _num(li.get("dev_pwm"), 6.0) * (1.0 - frac) + _num(ri.get("dev_pwm"), 6.0) * frac

    nearest_distance = min(abs(load - x) for x, _ in items)
    evidence = _clamp(support / 18.0, 0.0, 1.0)
    distance_factor = _clamp(1.0 - nearest_distance / 45.0, 0.20, 1.0)
    quality = _clamp(1.0 - dev / 12.0, 0.35, 1.0)
    confidence = int(round(_clamp(96.0 * evidence * distance_factor * quality, 0.0, 96.0)))
    source = "interpolation" if lx != rx and lx <= load <= rx else ("anchor" if nearest_distance <= 5.0 else "extrapolation")
    return prediction, confidence, nearest_distance, source


def _bucket_midpoint(bucket: str) -> float:
    return WORKLOAD_CENTERS.get(bucket, 50.0)


def _seed_from_v4(target_state: dict[str, Any], model: dict[str, Any], target_key: str) -> None:
    if target_state.get("seeded_from_v4"):
        return
    bins = model.get("bins")
    bins = bins if isinstance(bins, dict) else {}
    seeded_q = 0
    seeded_sparse = 0
    for bucket in ("idle", "low", "medium", "high"):
        raw = bins.get(f"{target_key}|{bucket}")
        if not isinstance(raw, dict):
            continue
        qn = int(_num(raw.get("qualified_n"), 0))
        observations = int(_num(raw.get("observations"), 0))
        load = _num(raw.get("last_qualified_cpu_load_percent"), _num(raw.get("last_cpu_load_percent"), _bucket_midpoint(bucket)))
        if qn > 0 and raw.get("ema_pwm") is not None:
            weight = min(60.0, max(2.0, qn * 0.32))
            _update_anchor(target_state, load, _num(raw.get("ema_pwm"), 0.0), weight)
            seeded_q += qn
        elif observations >= 10 and raw.get("last_pwm_percent") is not None:
            # Old rejected observations are not promoted to qualified samples. We
            # only retain a very small prior around the last actually observed
            # operating point, allowing future short bursts to refine it quickly.
            last_temp = _num(raw.get("last_temp_c"), float(target_key))
            candidate = _num(raw.get("last_pwm_percent"), 0.0) + 0.35 * (last_temp - float(target_key))
            weight = min(3.5, max(0.5, observations / 120.0))
            _update_anchor(target_state, load, candidate, weight)
            seeded_sparse += observations
    target_state.update({
        "seeded_from_v4": True,
        "seeded_qualified_samples": seeded_q,
        "seeded_sparse_observations": seeded_sparse,
        "seeded_epoch": int(time.time()),
    })


def _observation_weight(status: dict[str, Any]) -> float:
    if bool(status.get("qualified_sample")):
        return 1.0
    if not bool(status.get("training_sample_due")):
        return 0.0
    if str(status.get("mode")) not in {"learning", "assist"}:
        return 0.0
    error = abs(_num(status.get("temperature_error_c"), 99.0))
    if error > 6.0:
        return 0.0
    slope = abs(_num(status.get("temperature_slope_c_per_min"), 10.0))
    temp_range = abs(_num(status.get("temperature_window_range_c"), 10.0))
    pwm_range = abs(_num(status.get("pwm_range_30s_percent"), 30.0))
    bucket_age = _num(status.get("workload_bucket_age_seconds"), 0.0)
    near_factor = _clamp(1.0 - error / 6.0, 0.0, 1.0)
    slope_factor = _clamp(1.0 - slope / 5.0, 0.15, 1.0)
    range_factor = _clamp(1.0 - temp_range / 7.0, 0.15, 1.0)
    pwm_factor = _clamp(1.0 - pwm_range / 28.0, 0.20, 1.0)
    age_factor = _clamp(bucket_age / 20.0, 0.25, 1.0)
    weight = TRANSIENT_WEIGHT_MAX * near_factor * slope_factor * range_factor * pwm_factor * age_factor
    if str(status.get("qualification_state")) == "stabilizing":
        weight = max(weight, 0.18)
    return round(_clamp(weight, 0.0, TRANSIENT_WEIGHT_MAX), 4)


def _candidate_pwm(status: dict[str, Any]) -> float:
    current = _num(status.get("current_pwm_percent"), _num(status.get("baseline_pwm_percent"), 0.0))
    target = _num(status.get("target_temp_c"), 49.0)
    mean_temp = _num(status.get("temperature_window_mean_c"), _num(status.get("temperature_c"), target))
    window_error = mean_temp - target
    slope = _num(status.get("temperature_slope_c_per_min"), 0.0)
    predictor = status.get("thermal_predictor")
    predictor = predictor if isinstance(predictor, dict) else {}
    forecast_60 = _num(predictor.get("forecast_60s_c"), target)
    forecast_error = forecast_60 - target
    candidate = current + 0.50 * window_error + 0.07 * slope + 0.16 * forecast_error
    lo = _num(status.get("minimum_pwm_percent"), 0.0)
    hi = 100.0
    return _clamp(candidate, lo, hi)


def _target_state(model: dict[str, Any], target_key: str) -> dict[str, Any]:
    root = model.setdefault("hierarchical_v5", {})
    if not isinstance(root, dict):
        root = {}
        model["hierarchical_v5"] = root
    if int(_num(root.get("schema"), 0)) != V5_SCHEMA:
        root.clear()
        root.update({"schema": V5_SCHEMA, "policy": V5_POLICY, "targets": {}, "created_epoch": int(time.time())})
    root["policy"] = V5_POLICY
    targets = root.setdefault("targets", {})
    if not isinstance(targets, dict):
        targets = {}
        root["targets"] = targets
    state = targets.get(target_key)
    if not isinstance(state, dict):
        state = {"anchors": {}, "created_epoch": int(time.time())}
        targets[target_key] = state
    return state


def _effective_confidence(
    *, direct_conf: int, global_conf: int, predictor_conf: int, observations: int,
    direct_qn: int, min_samples: int, distance: float,
) -> int:
    exposure = _clamp(observations / 120.0, 0.0, 1.0)
    transfer = _clamp(1.0 - distance / 55.0, 0.25, 1.0)
    transferred = (0.62 * global_conf + 0.23 * predictor_conf + 0.15 * (70.0 * exposure)) * transfer
    direct_maturity = _clamp(direct_qn / float(max(1, min_samples)), 0.0, 1.0)
    combined = transferred * (1.0 - 0.55 * direct_maturity) + direct_conf * (0.55 * direct_maturity)
    return int(round(_clamp(max(float(direct_conf), combined), 0.0, 97.0)))


def _augment_progress(
    progress: dict[str, Any], target_state: dict[str, Any], predictor_conf: int, min_samples: int,
) -> tuple[dict[str, Any], int]:
    out: dict[str, Any] = {}
    ready_count = 0
    for bucket in ("idle", "low", "medium", "high"):
        raw = progress.get(bucket)
        item = dict(raw) if isinstance(raw, dict) else {}
        direct = int(_num(item.get("confidence_percent"), 0))
        qn = int(_num(item.get("qualified"), 0))
        obs = int(_num(item.get("observations"), 0))
        _, global_conf, distance, source = _global_prediction(target_state, _bucket_midpoint(bucket))
        effective = _effective_confidence(
            direct_conf=direct, global_conf=global_conf, predictor_conf=predictor_conf,
            observations=obs, direct_qn=qn, min_samples=min_samples, distance=distance,
        )
        ready = effective >= ASSIST_MIN_EFFECTIVE_CONFIDENCE
        if ready:
            ready_count += 1
        item.update({
            "direct_confidence_percent": direct,
            "global_confidence_percent": global_conf,
            "effective_confidence_percent": effective,
            "effective_ready": ready,
            "transfer_source": source,
            "transfer_distance_percent": round(distance, 1),
        })
        out[bucket] = item
    return out, int(round(100.0 * ready_count / 4.0))


def _apply_hierarchical_step(model: dict[str, Any], status: dict[str, Any], fields: list[str]) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    target = _num(status.get("target_temp_c"), 49.0)
    target_key = f"{target:.1f}"
    target_state = _target_state(model, target_key)
    _seed_from_v4(target_state, model, target_key)

    load = _num(status.get("cpu_load_smoothed_percent"), _num(status.get("cpu_load_percent"), 0.0))
    legacy_obs_total = int(_num(status.get("observations_total"), 0))
    last_seen = int(_num(target_state.get("last_legacy_observations_total"), -1))
    obs_weight = _observation_weight(status)
    if legacy_obs_total != last_seen and obs_weight > 0:
        candidate = _candidate_pwm(status)
        _update_anchor(target_state, load, candidate, obs_weight)
        target_state["last_learning_weight"] = obs_weight
        target_state["last_candidate_pwm"] = round(candidate, 2)
        target_state["last_learning_bucket"] = status.get("workload_bucket")
        target_state["last_learning_epoch"] = int(time.time())
    target_state["last_legacy_observations_total"] = legacy_obs_total

    global_pred, global_conf, distance, source = _global_prediction(target_state, load)
    direct_conf = int(_num(status.get("confidence_percent"), 0))
    direct_qn = int(_num(status.get("bin_qualified_samples"), 0))
    min_samples = max(1, int(_num(status.get("min_samples"), 30)))
    observations = int(_num(status.get("bin_observations"), 0))
    predictor = status.get("thermal_predictor")
    predictor = predictor if isinstance(predictor, dict) else {}
    predictor_conf = int(_num(predictor.get("confidence_percent"), 0))

    direct_prediction = status.get("prediction_pwm_percent")
    direct_prediction_num = _num(direct_prediction, _num(status.get("baseline_pwm_percent"), 0.0))
    direct_maturity = _clamp(direct_qn / float(min_samples), 0.0, 1.0)
    direct_share = DIRECT_BLEND_MAX * direct_maturity
    if global_pred is None:
        effective_prediction = direct_prediction_num if direct_qn > 0 else None
        source = "direct_only" if direct_qn > 0 else "none"
        global_conf = 0
        distance = 100.0
    elif direct_qn > 0:
        effective_prediction = global_pred * (1.0 - direct_share) + direct_prediction_num * direct_share
        source = "global_plus_direct"
    else:
        effective_prediction = global_pred

    effective_conf = _effective_confidence(
        direct_conf=direct_conf, global_conf=global_conf, predictor_conf=predictor_conf,
        observations=observations, direct_qn=direct_qn, min_samples=min_samples, distance=distance,
    )
    effective_ready = effective_prediction is not None and effective_conf >= ASSIST_MIN_EFFECTIVE_CONFIDENCE

    progress = status.get("bucket_progress")
    progress = progress if isinstance(progress, dict) else {}
    effective_progress, effective_coverage = _augment_progress(progress, target_state, predictor_conf, min_samples)

    status.update({
        "learning_policy": V5_POLICY,
        "hierarchical_schema": V5_SCHEMA,
        "direct_confidence_percent": direct_conf,
        "global_confidence_percent": global_conf,
        "effective_confidence_percent": effective_conf,
        "global_prediction_pwm_percent": round(global_pred, 1) if global_pred is not None else None,
        "effective_prediction_pwm_percent": round(effective_prediction, 1) if effective_prediction is not None else None,
        "direct_prediction_pwm_percent": direct_prediction,
        "direct_model_maturity_percent": int(round(100.0 * direct_maturity)),
        "direct_blend_percent": int(round(100.0 * direct_share)),
        "transfer_source": source,
        "transfer_distance_percent": round(distance, 1),
        "effective_current_bucket_ready": effective_ready,
        "effective_model_coverage_percent": effective_coverage,
        "bucket_progress": effective_progress,
        "hierarchical_model": {
            "policy": V5_POLICY,
            "schema": V5_SCHEMA,
            "target_key": target_key,
            "anchor_count": len(_nearest_anchor_items(target_state, load)),
            "seeded_qualified_samples": int(_num(target_state.get("seeded_qualified_samples"), 0)),
            "seeded_sparse_observations": int(_num(target_state.get("seeded_sparse_observations"), 0)),
            "last_learning_weight": _num(target_state.get("last_learning_weight"), 0.0),
        },
    })

    # Keep legacy direct behavior authoritative when the current bucket already
    # has a mature qualified model. v5 only takes over the sparse-bucket assist
    # path; Adaptive PWM safety/sign guards remain unchanged.
    legacy_ready = bool(status.get("current_bucket_ready"))
    output = int(_num(status.get("output_pwm_percent"), _num(status.get("baseline_pwm_percent"), 0.0)))
    correction = int(_num(status.get("correction_pwm_percent"), 0))
    state = str(status.get("state") or "learning")
    reason = str(status.get("reason") or "observe_only")

    if (
        not legacy_ready
        and effective_ready
        and str(status.get("mode")) == "assist"
        and _argv_value("--control-mode", "automatic") == "automatic"
        and abs(_num(status.get("temperature_error_c"), 99.0)) <= 4.0
    ):
        baseline = int(_num(status.get("baseline_pwm_percent"), output))
        assist_limit = max(0, int(_num(_argv_value("--assist-limit", "5"), 5)))
        min_safe = int(_num(_argv_value("--min-safe", "0"), 0))
        maximum = int(_num(_argv_value("--maximum", "100"), 100))
        deadband = max(0.1, _num(_argv_value("--deadband", "0.75"), 0.75))
        desired = int(round(_clamp(float(effective_prediction), baseline - assist_limit, baseline + assist_limit)))
        error = _num(status.get("temperature_error_c"), 0.0)
        if error > deadband and desired < baseline:
            desired = baseline
        elif error < -deadband and desired > baseline:
            desired = baseline
        delta = int(_clamp(desired - baseline, -2, 2))
        output = int(_clamp(baseline + delta, min_safe, maximum))
        correction = output - baseline
        state = "assist"
        reason = "hierarchical_nudge" if correction else "hierarchical_agrees"
        status.update({
            "state": state,
            "reason": reason,
            "output_pwm_percent": output,
            "correction_pwm_percent": correction,
            "prediction_pwm_percent": int(round(float(effective_prediction))),
            "prediction_available": True,
            "confidence_percent": effective_conf,
            "current_bucket_ready": True,
        })
    else:
        # Expose effective confidence/prediction in the canonical presentation
        # fields without changing mature v4 physical behavior.
        status["confidence_percent"] = max(direct_conf, effective_conf)
        if effective_prediction is not None and not legacy_ready:
            status["prediction_pwm_percent"] = int(round(float(effective_prediction)))
            status["prediction_available"] = True

    target_state.update({
        "last_load_percent": round(load, 1),
        "last_global_prediction_pwm": round(global_pred, 2) if global_pred is not None else None,
        "last_global_confidence_percent": global_conf,
        "last_effective_confidence_percent": effective_conf,
        "last_transfer_source": source,
        "updated_epoch": int(time.time()),
    })
    root = model.get("hierarchical_v5")
    if isinstance(root, dict):
        root["updated_epoch"] = int(time.time())

    if len(fields) >= 14:
        fields[0] = str(output)
        fields[1] = state
        fields[2] = reason
        fields[3] = str(status.get("confidence_percent", effective_conf))
        pred = status.get("prediction_pwm_percent")
        fields[4] = str(int(round(_num(pred, _num(fields[4], 0)))))
        fields[6] = str(correction)

    # v3.1.10 observability: append diagnostics to the existing evaluator TSV
    # instead of making run_legacy perform extra jq/file reads every 10 seconds.
    # The first 14 fields remain byte-for-byte compatible with v4 consumers.
    def _obs(value: Any, fallback: str = "-1") -> str:
        if value is None:
            return fallback
        return str(value)

    observability_fields = [
        str(int(_num(status.get("direct_confidence_percent"), direct_conf))),
        str(int(_num(status.get("global_confidence_percent"), global_conf))),
        str(int(_num(status.get("effective_confidence_percent"), effective_conf))),
        _obs(status.get("direct_prediction_pwm_percent")),
        _obs(status.get("global_prediction_pwm_percent")),
        _obs(status.get("effective_prediction_pwm_percent")),
        str(status.get("transfer_source") or "none"),
        str(int(_num(status.get("effective_model_coverage_percent"), 0))),
    ]
    if len(fields) < 22:
        fields.extend(observability_fields)
    else:
        fields[14:22] = observability_fields
    return model, status, fields


def _run_step() -> int:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = legacy.main()
    captured = buffer.getvalue()
    lines = [line for line in captured.splitlines() if line.strip()]
    if rc != 0 or not lines:
        if captured:
            print(captured, end="")
        return rc

    final = lines[-1]
    fields = final.split("\t")
    if len(fields) < 14:
        print(captured, end="")
        return rc

    model_path = _argv_value("--model")
    status_path = _argv_value("--status")
    mirror_path = _argv_value("--mirror")
    if not model_path or not status_path:
        print(captured, end="")
        return rc

    model = _read_json(model_path)
    status = _read_json(status_path)
    try:
        model, status, fields = _apply_hierarchical_step(model, status, fields)
        _write_json(model_path, model, durable=bool(status.get("qualified_sample")))
        _write_json(status_path, status, durable=False)
        if mirror_path:
            # v4 rate-limits the mirror; v5 writes only on the same evaluator call
            # and does not add any polling activity.
            _write_json(mirror_path, status, durable=False)
    except Exception as exc:
        # Fail open to the proven v4 output. A v5 diagnostic error must never
        # prevent Adaptive PWM or the legacy AI learner from operating.
        print(f"AI Cooling v5 wrapper fallback: {exc}", file=sys.stderr)
        print(captured, end="")
        return rc

    for line in lines[:-1]:
        print(line)
    print("\t".join(fields))
    return rc


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "step":
        return _run_step()
    return legacy.main()


if __name__ == "__main__":
    raise SystemExit(main())
