#!/usr/bin/env python3
"""SBC5 AI Cooling v5.2 — Thermal Predictor guided assist.

Thermal Predictor participates in the existing AI Cooling assist path instead of
owning a second actuator loop. Adaptive PWM and the proven AI assist guards remain
authoritative. Predictor guidance is evaluated on every AI cycle; no extra polling
or background process is created.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import time
from typing import Any

import thermal_active_policy as policy
import thermal_effectiveness as effectiveness


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
_original_apply = base._apply_hierarchical_step


def _num(value: Any, default: float = 0.0) -> float:
    return policy.num(value, default)


def _guided_runtime(status: dict[str, Any]) -> dict[str, Any]:
    """Evaluate bounded Thermal Predictor guidance for the current AI cycle."""
    predictor = status.get("thermal_predictor")
    predictor = predictor if isinstance(predictor, dict) else {}
    target = _num(status.get("target_temp_c"), 49.0)
    weighted, weights = policy.dynamic_forecast(predictor, target)

    confidence = _num(predictor.get("confidence_percent"), 0.0)
    avg_mae = _num(predictor.get("average_mae_c"), 99.0)
    maturity = policy.clamp((confidence - 55.0) / 40.0, 0.0, 1.0)
    accuracy = policy.clamp((3.0 - avg_mae) / 2.0, 0.0, 1.0)
    gain = 0.22 * maturity * accuracy

    ai_mode = str(status.get("mode") or "observe")
    control_mode = str(base._argv_value("--control-mode", "automatic") or "automatic")
    controller_action = str(status.get("controller_action") or status.get("reason") or "none")
    outcome_samples = int(round(_num(status.get("thermal_outcome_samples"), 0.0)))
    outcome_success = _num(status.get("thermal_outcome_success_percent"), 100.0)

    gate_mode, gate_reason, max_delta = policy.gate(
        predictor=predictor,
        now=time.time(),
        ai_mode=ai_mode,
        control_mode=control_mode,
        controller_action=controller_action,
        outcome_samples=outcome_samples,
        outcome_success_percent=outcome_success,
    )
    decision = policy.decide(
        predictor=predictor,
        target=target,
        temp=_num(status.get("temperature_c"), target),
        slope=_num(status.get("temperature_slope_c_per_min"), 0.0),
        mode=gate_mode,
        max_delta=max_delta,
    )
    return {
        "weighted_forecast_c": round(weighted, 2),
        "weighted_forecast_error_c": round(weighted - target, 2),
        "horizon_weights": weights,
        "candidate_gain": round(gain, 3),
        "gate_mode": gate_mode,
        "gate_reason": gate_reason,
        "decision_reason": str(decision.get("decision_reason") or "near_target"),
        "requested_delta_pp": int(_num(decision.get("requested_delta_pp"), 0.0)),
    }


def _apply_guided_step(model: dict[str, Any], status: dict[str, Any], fields: list[str]):
    model, status, fields = _original_apply(model, status, fields)
    predictor = status.get("thermal_predictor")
    predictor = predictor if isinstance(predictor, dict) else {}

    guidance = _guided_runtime(status)
    requested_delta = int(guidance["requested_delta_pp"])
    applied_delta = 0

    # Keep the existing AI result authoritative, then apply only the bounded
    # predictor nudge. The final value remains inside the existing AI assist
    # envelope; Adaptive PWM/safety logic downstream remains authoritative.
    if str(status.get("mode")) == "assist" and requested_delta:
        baseline = int(round(_num(status.get("baseline_pwm_percent"), status.get("output_pwm_percent", 0))))
        output = int(round(_num(status.get("output_pwm_percent"), baseline)))
        assist_limit = max(0, int(round(_num(base._argv_value("--assist-limit", "5"), 5.0))))
        min_safe = int(round(_num(base._argv_value("--min-safe", "0"), 0.0)))
        maximum = int(round(_num(base._argv_value("--maximum", "100"), 100.0)))
        lo = max(min_safe, baseline - assist_limit)
        hi = min(maximum, baseline + assist_limit)
        guided_output = int(round(policy.clamp(output + requested_delta, lo, hi)))
        applied_delta = guided_output - output
        if applied_delta:
            status["output_pwm_percent"] = guided_output
            status["correction_pwm_percent"] = guided_output - baseline
            if len(fields) >= 7:
                fields[0] = str(guided_output)
                fields[6] = str(guided_output - baseline)

    guidance["applied_delta_pp"] = applied_delta
    guidance["ai_output_pwm_percent"] = status.get("output_pwm_percent")
    guidance["ai_correction_pwm_percent"] = status.get("correction_pwm_percent")
    guidance["guard_reason"] = status.get("reason")
    status["thermal_predictor_guidance"] = guidance

    # 3.1.25: observe post-intervention outcomes using the existing AI cycle.
    # This diagnostic score intentionally does NOT feed thermal_outcome_* gate
    # inputs yet, so it cannot alter Thermal Predictor eligibility or PWM policy.
    effectiveness_summary = effectiveness.update(
        model=model,
        now=time.time(),
        temperature_c=_num(status.get("temperature_c"), _num(status.get("target_temp_c"), 49.0)),
        target_c=_num(status.get("target_temp_c"), 49.0),
        applied_delta_pp=applied_delta,
        decision_reason=str(guidance.get("decision_reason") or ""),
    )

    active = str(status.get("mode")) == "assist"
    predictor["guided_assist"] = {
        "mode": guidance.get("gate_mode", "observe"),
        "control_output_enabled": active and guidance.get("gate_mode") in {"active", "probation"},
        "weighted_forecast_c": guidance.get("weighted_forecast_c"),
        "weighted_forecast_error_c": guidance.get("weighted_forecast_error_c"),
        "horizon_weights": guidance.get("horizon_weights", {}),
        "candidate_gain": guidance.get("candidate_gain", 0.0),
        "requested_delta_pp": requested_delta,
        "applied_delta_pp": applied_delta,
        "gate_reason": guidance.get("gate_reason"),
        "decision_reason": guidance.get("decision_reason"),
        "ai_output_pwm_percent": status.get("output_pwm_percent"),
        "ai_correction_pwm_percent": status.get("correction_pwm_percent"),
        "guard_reason": status.get("reason"),
    }
    predictor["effectiveness"] = effectiveness_summary
    predictor["mode"] = "guided_assist" if active else "observe_only"
    predictor["control_output_enabled"] = bool(predictor["guided_assist"]["control_output_enabled"])
    status["thermal_predictor"] = predictor
    status["thermal_predictor_effectiveness"] = effectiveness_summary

    if len(fields) >= 21:
        source = str(fields[20] or status.get("transfer_source") or "none").split("+thermal[", 1)[0]
        source += "+thermal[guided]"
        fields[20] = source
        status["transfer_source"] = source

    weights = guidance.get("horizon_weights") if isinstance(guidance.get("horizon_weights"), dict) else {}
    diagnostic_fields = [
        str(predictor.get("mode") or "observe_only"),
        str(_num(predictor.get("forecast_30s_c"), 0.0)),
        str(_num(predictor.get("forecast_60s_c"), 0.0)),
        str(_num(predictor.get("forecast_120s_c"), 0.0)),
        str(int(round(_num(predictor.get("confidence_percent"), 0.0)))),
        str(_num(predictor.get("average_mae_c"), 99.0)),
        str(_num(guidance.get("weighted_forecast_c"), 0.0)),
        str(_num(guidance.get("weighted_forecast_error_c"), 0.0)),
        str(_num(guidance.get("candidate_gain"), 0.0)),
        f"{_num(weights.get('30'),0.0):.3f},{_num(weights.get('60'),0.0):.3f},{_num(weights.get('120'),0.0):.3f}",
        str(int(round(_num(predictor.get("accepted_samples_total"), 0.0)))),
        str(int(round(_num(predictor.get("rejected_samples_total"), 0.0)))),
        str(int(_num(guidance.get("requested_delta_pp"), 0.0))),
        str(int(_num(guidance.get("applied_delta_pp"), 0.0))),
        str(guidance.get("gate_mode") or "observe"),
        str(guidance.get("gate_reason") or "unknown"),
        str(guidance.get("decision_reason") or "near_target"),
    ]
    if len(fields) < 39:
        fields.extend(diagnostic_fields)
    else:
        fields[22:39] = diagnostic_fields
    return model, status, fields


base._apply_hierarchical_step = _apply_guided_step
base.V5_POLICY = "hierarchical_continuous_v5_2_thermal_guided_runtime_effectiveness"


def main() -> int:
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
