#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected block missing in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# ---------------------------------------------------------------------------
# AI Thermal Predictor Shadow Assist — diagnostics only, never writes PWM.
# ---------------------------------------------------------------------------
ai = APP / "ai_cooling.py"
replace_once(
    ai,
    'THERMAL_PREDICTOR_DAMPING = {30: 0.90, 60: 0.72, 120: 0.52}\n',
    '''THERMAL_PREDICTOR_DAMPING = {30: 0.90, 60: 0.72, 120: 0.52}\nTHERMAL_SHADOW_MAX_DELTA_PP = 2\nTHERMAL_SHADOW_MIN_CONFIDENCE = 80\nTHERMAL_SHADOW_MAX_MAE_C = 1.25\nTHERMAL_SHADOW_MIN_VALIDATED_PER_HORIZON = 8\nTHERMAL_SHADOW_NEUTRAL_BAND_C = 0.60\nTHERMAL_SHADOW_STRONG_BAND_C = 1.80\n''',
)

insert_point = '''def _controller_hold(action: str) -> bool:\n'''
shadow_fn = '''def _thermal_shadow_assist(\n    predictor: dict[str, Any],\n    *,\n    target: float,\n    baseline: int,\n    min_safe: int,\n    maximum: int,\n    control_mode: str,\n    controller_action: str,\n) -> dict[str, Any]:\n    \"\"\"Return a bounded hypothetical PWM correction without changing control output.\n\n    Shadow Assist is deliberately non-authoritative. It evaluates the thermal\n    forecasts and records what a future predictive controller *would* request.\n    Adaptive PWM + AI Cooling remain the only control path and the returned\n    suggestion is never applied to ``output_pwm_percent``.\n    \"\"\"\n    quality = str(predictor.get("quality_state") or "learning")\n    confidence = int(round(_num(predictor.get("confidence_percent"), 0.0)))\n    avg_mae = predictor.get("average_mae_c")\n    avg_mae_num = _num(avg_mae, 999.0) if avg_mae is not None else 999.0\n    samples = predictor.get("validated_samples")\n    samples = samples if isinstance(samples, dict) else {}\n    per_horizon = {str(h): int(_num(samples.get(str(h)), 0)) for h in THERMAL_PREDICTOR_HORIZONS_SECONDS}\n\n    forecasts = [\n        _num(predictor.get("forecast_30s_c"), target),\n        _num(predictor.get("forecast_60s_c"), target),\n        _num(predictor.get("forecast_120s_c"), target),\n    ]\n    weighted_forecast = 0.55 * forecasts[0] + 0.30 * forecasts[1] + 0.15 * forecasts[2]\n    forecast_error = weighted_forecast - target\n    slope = _num(predictor.get("slope_c_per_min"), 0.0)\n\n    suggested_delta = 0\n    reason = "near_target"\n    if forecast_error >= THERMAL_SHADOW_STRONG_BAND_C:\n        suggested_delta = 2\n        reason = "forecast_hot_strong"\n    elif forecast_error >= THERMAL_SHADOW_NEUTRAL_BAND_C:\n        suggested_delta = 1\n        reason = "forecast_hot"\n    elif forecast_error <= -THERMAL_SHADOW_STRONG_BAND_C and slope <= 0.0:\n        suggested_delta = -2\n        reason = "forecast_cool_strong"\n    elif forecast_error <= -THERMAL_SHADOW_NEUTRAL_BAND_C and slope <= 0.0:\n        suggested_delta = -1\n        reason = "forecast_cool"\n    elif forecast_error < -THERMAL_SHADOW_NEUTRAL_BAND_C:\n        reason = "cool_forecast_but_rising"\n\n    suggested_delta = int(_clamp(suggested_delta, -THERMAL_SHADOW_MAX_DELTA_PP, THERMAL_SHADOW_MAX_DELTA_PP))\n    suggested_pwm = int(_clamp(baseline + suggested_delta, min_safe, maximum))\n    suggested_delta = suggested_pwm - baseline\n\n    gate_reason = "eligible"\n    eligible = True\n    if control_mode != "automatic":\n        eligible = False; gate_reason = "automatic_mode_required"\n    elif "safety" in str(controller_action or "").lower():\n        eligible = False; gate_reason = "safety_action_active"\n    elif quality not in {"good", "excellent"}:\n        eligible = False; gate_reason = "quality_below_good"\n    elif confidence < THERMAL_SHADOW_MIN_CONFIDENCE:\n        eligible = False; gate_reason = "confidence_below_threshold"\n    elif avg_mae_num > THERMAL_SHADOW_MAX_MAE_C:\n        eligible = False; gate_reason = "mae_above_threshold"\n    elif min(per_horizon.values(), default=0) < THERMAL_SHADOW_MIN_VALIDATED_PER_HORIZON:\n        eligible = False; gate_reason = "insufficient_validated_forecasts"\n\n    return {\n        "mode": "shadow",\n        "control_output_enabled": False,\n        "eligible": eligible,\n        "gate_reason": gate_reason,\n        "decision_reason": reason,\n        "suggested_delta_pp": suggested_delta,\n        "suggested_pwm_percent": suggested_pwm,\n        "baseline_pwm_percent": baseline,\n        "weighted_forecast_c": round(weighted_forecast, 2),\n        "weighted_forecast_error_c": round(forecast_error, 2),\n        "max_delta_pp": THERMAL_SHADOW_MAX_DELTA_PP,\n        "minimum_confidence_percent": THERMAL_SHADOW_MIN_CONFIDENCE,\n        "maximum_mae_c": THERMAL_SHADOW_MAX_MAE_C,\n        "minimum_validated_per_horizon": THERMAL_SHADOW_MIN_VALIDATED_PER_HORIZON,\n        "validated_per_horizon": per_horizon,\n    }\n\n\n'''
text = ai.read_text(encoding="utf-8")
if insert_point not in text:
    raise SystemExit("Shadow Assist insertion point missing")
ai.write_text(text.replace(insert_point, shadow_fn + insert_point, 1), encoding="utf-8")

replace_once(
    ai,
    '''    thermal_predictor = _thermal_predictor(model, temp, slope, now, temp_window_span, temp_window_points)\n    status = {\n''',
    '''    thermal_predictor = _thermal_predictor(model, temp, slope, now, temp_window_span, temp_window_points)\n    thermal_shadow = _thermal_shadow_assist(\n        thermal_predictor,\n        target=target, baseline=baseline, min_safe=min_safe, maximum=maximum,\n        control_mode=control_mode, controller_action=controller_action,\n    )\n    thermal_predictor["shadow_assist"] = thermal_shadow\n    # Shadow Assist is telemetry only. Do not mutate `output`, `correction` or the\n    # physical controller target from this block.\n    status = {\n''',
)

# ---------------------------------------------------------------------------
# Native integration sensors for Shadow Assist telemetry.
# ---------------------------------------------------------------------------
sensor = ROOT / "custom_components" / "sbc5_control_center" / "sensor.py"
text = sensor.read_text(encoding="utf-8")
needle = '''    SensorSpec(unique_id="sbc5_ai_thermal_predictor_age", name="SBC5 AI Thermal Predictor Data Age", value_fn=_predictor_age_seconds, icon="mdi:timer-sand", unit="s", state_class=SensorStateClass.MEASUREMENT),\n'''
addition = needle + '''    SensorSpec(unique_id="sbc5_ai_thermal_shadow_delta", name="SBC5 AI Thermal Shadow Delta", value_fn=lambda d: _predictor_nested_number(d, "shadow_assist", "suggested_delta_pp"), icon="mdi:plus-minus-variant", unit="pp", state_class=SensorStateClass.MEASUREMENT),\n    SensorSpec(unique_id="sbc5_ai_thermal_shadow_pwm", name="SBC5 AI Thermal Shadow PWM", value_fn=lambda d: _predictor_nested_number(d, "shadow_assist", "suggested_pwm_percent"), icon="mdi:fan-auto", unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),\n    SensorSpec(unique_id="sbc5_ai_thermal_shadow_state", name="SBC5 AI Thermal Shadow State", value_fn=lambda d: (d.thermal_predictor.get("shadow_assist") or {}).get("gate_reason") if isinstance(d.thermal_predictor.get("shadow_assist"), dict) else None, icon="mdi:shield-search"),\n    SensorSpec(unique_id="sbc5_ai_thermal_shadow_decision", name="SBC5 AI Thermal Shadow Decision", value_fn=lambda d: (d.thermal_predictor.get("shadow_assist") or {}).get("decision_reason") if isinstance(d.thermal_predictor.get("shadow_assist"), dict) else None, icon="mdi:brain"),\n    SensorSpec(unique_id="sbc5_ai_thermal_shadow_weighted_forecast", name="SBC5 AI Thermal Shadow Weighted Forecast", value_fn=lambda d: _predictor_nested_number(d, "shadow_assist", "weighted_forecast_c"), icon="mdi:thermometer-lines", unit=UnitOfTemperature.CELSIUS, device_class=SensorDeviceClass.TEMPERATURE, state_class=SensorStateClass.MEASUREMENT),\n'''
if needle not in text:
    raise SystemExit("Shadow sensor insertion point missing")
sensor.write_text(text.replace(needle, addition, 1), encoding="utf-8")

# Bundled bridge follows canonical integration.
bridge_sensor = APP / "bridge" / "sensor.py"
bridge_sensor.write_text(sensor.read_text(encoding="utf-8"), encoding="utf-8")

# ---------------------------------------------------------------------------
# YAML card: show Shadow Assist directly below predictor quality diagnostics.
# ---------------------------------------------------------------------------
card = ROOT / "dashboard" / "sbc5_control_center_diagnostics_card.yaml"
text = card.read_text(encoding="utf-8")
anchor = '''        - type: custom:mushroom-template-card\n          entity: sensor.sbc5_network_mac\n          primary: Tożsamość sieciowa SBC5\n'''
shadow_card = '''        - type: markdown\n          content: |\n            #### Thermal Predictor · Shadow Assist\n            Symulacja wpływu na PWM · brak fizycznego sterowania\n          card_mod:\n            style: |\n              ha-card { background: transparent; box-shadow: none; padding: 2px 6px 0 6px; margin: 0; }\n              ha-markdown { padding: 0 !important; }\n              h4 { margin: 0 !important; font-size: 14px !important; line-height: 1.1 !important; }\n\n        - type: grid\n          columns: 2\n          square: false\n          cards:\n            - type: custom:mushroom-template-card\n              entity: sensor.sbc5_ai_thermal_shadow_delta\n              primary: Sugerowana korekta PWM\n              secondary: >-\n                {{ states('sensor.sbc5_ai_thermal_shadow_delta') }} pp · hipotetycznie {{ states('sensor.sbc5_ai_thermal_shadow_pwm') }}%\n                · fizyczny PWM pozostaje bez zmian\n              icon: mdi:plus-minus-variant\n              icon_color: >-\n                {% set d = states('sensor.sbc5_ai_thermal_shadow_delta') | float(0) %}\n                {% if d > 0 %}orange{% elif d < 0 %}blue{% else %}green{% endif %}\n              multiline_secondary: true\n              tap_action: { action: more-info }\n            - type: custom:mushroom-template-card\n              entity: sensor.sbc5_ai_thermal_shadow_state\n              primary: Bramka aktywacji\n              secondary: >-\n                {{ states('sensor.sbc5_ai_thermal_shadow_state') }} · decyzja {{ states('sensor.sbc5_ai_thermal_shadow_decision') }}\n                · prognoza ważona {{ states('sensor.sbc5_ai_thermal_shadow_weighted_forecast') }} °C\n              icon: mdi:shield-search\n              icon_color: >-\n                {% if is_state('sensor.sbc5_ai_thermal_shadow_state','eligible') %}green{% else %}orange{% endif %}\n              multiline_secondary: true\n              tap_action: { action: more-info }\n          card_mod:\n            style: |\n              #root { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)) !important; gap: clamp(6px, 1.8vw, 10px) !important; align-items: stretch !important; }\n              #root > * { min-width: 0 !important; height: 100% !important; }\n              @media (max-width: 339px) { #root { grid-template-columns: 1fr !important; } }\n\n'''
if anchor not in text:
    raise SystemExit("Shadow card insertion point missing")
card.write_text(text.replace(anchor, shadow_card + anchor, 1), encoding="utf-8")

# Regenerate JSON from canonical YAML.
obj = yaml.safe_load(card.read_text(encoding="utf-8"))
(APP / "dashboard_card.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# Tests: prove bounded recommendation and prove no physical control output.
# ---------------------------------------------------------------------------
test = ROOT / "scripts" / "test_thermal_predictor_shadow.py"
test.write_text('''#!/usr/bin/env python3\nfrom __future__ import annotations\n\nimport importlib.util\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nAI = ROOT / "local_apps" / "sbc5_control_center" / "ai_cooling.py"\nspec = importlib.util.spec_from_file_location("sbc5_ai_cooling", AI)\nmod = importlib.util.module_from_spec(spec)\nassert spec and spec.loader\nspec.loader.exec_module(mod)\n\nbase = {\n    "quality_state": "excellent",\n    "confidence_percent": 92,\n    "average_mae_c": 0.6,\n    "validated_samples": {"30": 12, "60": 12, "120": 12},\n    "forecast_30s_c": 52.0,\n    "forecast_60s_c": 52.5,\n    "forecast_120s_c": 52.0,\n    "slope_c_per_min": 1.0,\n}\nshadow = mod._thermal_shadow_assist(base, target=49.0, baseline=44, min_safe=9, maximum=100, control_mode="automatic", controller_action="hold")\nassert shadow["eligible"] is True\nassert shadow["suggested_delta_pp"] == 2\nassert shadow["suggested_pwm_percent"] == 46\nassert shadow["control_output_enabled"] is False\n\npoor = dict(base, quality_state="weak", confidence_percent=55, average_mae_c=2.4)\nshadow = mod._thermal_shadow_assist(poor, target=49.0, baseline=44, min_safe=9, maximum=100, control_mode="automatic", controller_action="hold")\nassert shadow["eligible"] is False\nassert shadow["gate_reason"] == "quality_below_good"\nassert -2 <= shadow["suggested_delta_pp"] <= 2\n\ntext = AI.read_text(encoding="utf-8")\nassert 'thermal_predictor["shadow_assist"] = thermal_shadow' in text\nassert 'Shadow Assist is telemetry only' in text\nassert 'control_output_enabled": False' in text\nprint("Thermal Predictor Shadow Assist tests: PASS")\n''', encoding="utf-8")

workflow = ROOT / ".github" / "workflows" / "validate.yml"
replace_once(
    workflow,
    '''      - name: Test runtime robustness\n        run: python scripts/test_runtime_robustness.py\n\n''',
    '''      - name: Test runtime robustness\n        run: python scripts/test_runtime_robustness.py\n\n      - name: Test Thermal Predictor Shadow Assist\n        run: python scripts/test_thermal_predictor_shadow.py\n\n''',
)

print("Applied SBC5 3.1.5 Thermal Predictor Shadow Assist source patch")
