#!/usr/bin/env python3
"""SBC5 AI Cooling v5.2 — Thermal Predictor guided assist.

Thermal Predictor participates in the existing AI Cooling assist path instead of
owning a second actuator path. Adaptive PWM and the proven AI assist guards remain
authoritative.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import thermal_active_policy as policy


def _base_path() -> Path:
    runtime = Path("/ai_cooling_v5_1.py")
    if runtime.is_file():
        return runtime
    return Path(__file__).with_name("ai_cooling_v5_1.py")


def _load_base():
    path = _base_path()
    spec = importlib.util.spec_from_file_location("sbc5_ai_cooling_v5_1_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load AI Cooling v5.1 base module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


layer = _load_base()
base = layer.base
_original_candidate_pwm = base._candidate_pwm
_original_apply = base._apply_hierarchical_step


def _num(value: Any, default: float = 0.0) -> float:
    return policy.num(value, default)


def _predictive_candidate_pwm(status: dict[str, Any]) -> float:
    candidate = float(_original_candidate_pwm(status))
    predictor = status.get("thermal_predictor")
    predictor = predictor if isinstance(predictor, dict) else {}
    target = _num(status.get("target_temp_c"), 49.0)
    weighted, weights = policy.dynamic_forecast(predictor, target)
    confidence = _num(predictor.get("confidence_percent"), 0.0)
    avg_mae = _num(predictor.get("average_mae_c"), 99.0)
    maturity = policy.clamp((confidence - 55.0) / 40.0, 0.0, 1.0)
    accuracy = policy.clamp((3.0 - avg_mae) / 2.0, 0.0, 1.0)
    gain = 0.22 * maturity * accuracy
    candidate += gain * (weighted - target)
    status["thermal_predictor_guidance"] = {
        "weighted_forecast_c": round(weighted, 2),
        "weighted_forecast_error_c": round(weighted - target, 2),
        "horizon_weights": weights,
        "candidate_gain": round(gain, 3),
    }
    return candidate


def _apply_guided_step(model: dict[str, Any], status: dict[str, Any], fields: list[str]):
    model, status, fields = _original_apply(model, status, fields)
    predictor = status.get("thermal_predictor")
    predictor = predictor if isinstance(predictor, dict) else {}
    guidance = status.get("thermal_predictor_guidance")
    guidance = guidance if isinstance(guidance, dict) else {}
    predictor["guided_assist"] = {
        "mode": "ai_guarded_assist",
        "control_output_enabled": str(status.get("mode")) == "assist",
        "weighted_forecast_c": guidance.get("weighted_forecast_c"),
        "weighted_forecast_error_c": guidance.get("weighted_forecast_error_c"),
        "horizon_weights": guidance.get("horizon_weights", {}),
        "candidate_gain": guidance.get("candidate_gain", 0.0),
        "ai_output_pwm_percent": status.get("output_pwm_percent"),
        "ai_correction_pwm_percent": status.get("correction_pwm_percent"),
        "guard_reason": status.get("reason"),
    }
    predictor["mode"] = "guided_assist" if str(status.get("mode")) == "assist" else "observe_only"
    status["thermal_predictor"] = predictor
    if len(fields) >= 21:
        source = str(fields[20] or status.get("transfer_source") or "none").split("+thermal[", 1)[0]
        source += "+thermal[guided]"
        fields[20] = source
        status["transfer_source"] = source
    return model, status, fields


base._candidate_pwm = _predictive_candidate_pwm
base._apply_hierarchical_step = _apply_guided_step
base.V5_POLICY = "hierarchical_continuous_v5_2_thermal_guided"


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
