#!/usr/bin/env python3
from __future__ import annotations

import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"


def sub_once(path: Path, pattern: str, repl: str, flags: int = 0) -> None:
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"pattern count={count} in {path}: {pattern[:100]}")
    path.write_text(updated, encoding="utf-8")

# Restart Manager — conservative same-boot CPU-profile reconciliation only.
run = APP / "run_legacy.sh"
sub_once(
    run,
    re.escape('''  [ "$type" = "host" ] && [ -n "$saved_boot" ] || return 0
  # Normal pending changes must wait for a new host boot. A marker that already
  # failed verification may be revalidated on the same boot; this lets 2.7.2
  # close the false 2.7.1 Repair without forcing an unnecessary second reboot.
  if [ "$saved_boot" = "$CURRENT_BOOT_ID" ] && [ "$verification_failed" != "true" ]; then return 0; fi
  scope="$(jq -r '.scope // "generic"' "$RESTART_STATE_FILE" 2>/dev/null || echo generic)"
  if [ "$scope" = "cpu_profile" ]; then
    profile="$(jq -r '.expected_profile // "factory"' "$RESTART_STATE_FILE" 2>/dev/null || echo factory)"
    expected_arm="$(jq -r 'if .expected_arm_freq == null then "" else (.expected_arm_freq|tostring) end' "$RESTART_STATE_FILE" 2>/dev/null || true)"
    if cpu_profile_verify_after_boot "$profile" "$expected_arm"; then
      log "Restart Manager: nowy boot hosta potwierdził profil CPU/OC — zamykam żądanie restartu."
      rm -f "$RESTART_STATE_FILE"
    else
'''),
    '''  [ "$type" = "host" ] && [ -n "$saved_boot" ] || return 0
  scope="$(jq -r '.scope // "generic"' "$RESTART_STATE_FILE" 2>/dev/null || echo generic)"

  # 3.1.3: same-boot cleanup is permitted only for a deterministic CPU profile
  # marker whose expected saved+active state can be proven by Boot Verification.
  # Generic config.txt/Device Tree markers still require a real host boot.
  if [ "$saved_boot" = "$CURRENT_BOOT_ID" ] && [ "$verification_failed" != "true" ]; then
    if [ "$scope" = "cpu_profile" ]; then
      profile="$(jq -r '.expected_profile // "factory"' "$RESTART_STATE_FILE" 2>/dev/null || echo factory)"
      expected_arm="$(jq -r 'if .expected_arm_freq == null then "" else (.expected_arm_freq|tostring) end' "$RESTART_STATE_FILE" 2>/dev/null || true)"
      if { [ "$profile" = "factory" ] || [[ "$expected_arm" =~ ^[0-9]+$ ]]; } && cpu_profile_verify_after_boot "$profile" "$expected_arm"; then
        log "Restart Manager: bieżący boot już spełnia oczekiwany profil CPU/OC — usuwam osierocony marker restart=host."
        rm -f "$RESTART_STATE_FILE"
      fi
    fi
    return 0
  fi

  if [ "$scope" = "cpu_profile" ]; then
    profile="$(jq -r '.expected_profile // "factory"' "$RESTART_STATE_FILE" 2>/dev/null || echo factory)"
    expected_arm="$(jq -r 'if .expected_arm_freq == null then "" else (.expected_arm_freq|tostring) end' "$RESTART_STATE_FILE" 2>/dev/null || true)"
    if cpu_profile_verify_after_boot "$profile" "$expected_arm"; then
      log "Restart Manager: nowy boot hosta potwierdził profil CPU/OC — zamykam żądanie restartu."
      rm -f "$RESTART_STATE_FILE"
    else
''',
)

# Predictor scoring diagnostics.
ai = APP / "ai_cooling.py"
sub_once(ai, re.escape('''    samples = state.get("validated_samples")
    if not isinstance(samples, dict):
        samples = {}

    pending: list[dict[str, Any]] = []
'''), '''    samples = state.get("validated_samples")
    if not isinstance(samples, dict):
        samples = {}
    last_error = state.get("last_error_c")
    if not isinstance(last_error, dict):
        last_error = {}

    pending: list[dict[str, Any]] = []
''')
sub_once(ai, re.escape('''            mae[horizon] = round(old + THERMAL_PREDICTOR_ERROR_ALPHA * (err - old), 3)
            samples[horizon] = int(_num(samples.get(horizon), 0)) + 1
'''), '''            mae[horizon] = round(old + THERMAL_PREDICTOR_ERROR_ALPHA * (err - old), 3)
            last_error[horizon] = round(err, 3)
            samples[horizon] = int(_num(samples.get(horizon), 0)) + 1
''')
sub_once(ai, re.escape('''        "mae_ema_c": {k: round(_num(v), 3) for k, v in mae.items()},
        "validated_samples": {k: int(_num(v)) for k, v in samples.items()},
        "average_mae_c": round(avg_mae, 3) if avg_mae is not None else None,
'''), '''        "mae_ema_c": {k: round(_num(v), 3) for k, v in mae.items()},
        "last_error_c": {k: round(_num(v), 3) for k, v in last_error.items()},
        "validated_samples": {k: int(_num(v)) for k, v in samples.items()},
        "validated_samples_total": sum(int(_num(samples.get(str(h)), 0)) for h in THERMAL_PREDICTOR_HORIZONS_SECONDS),
        "average_mae_c": round(avg_mae, 3) if avg_mae is not None else None,
''')

# Native sensor diagnostics. Match compact 3.1.2 formatting.
sensor = ROOT / "custom_components" / "sbc5_control_center" / "sensor.py"
text = sensor.read_text(encoding="utf-8")
text = text.replace("from dataclasses import dataclass\n", "from dataclasses import dataclass\nimport time\n", 1)
helper_anchor = "def _cpu_usage_percent(data: SBC5CoordinatorData) -> float | None:\n"
helpers = '''def _predictor_nested_number(data: SBC5CoordinatorData, group: str, key: str) -> float | None:
    values = data.thermal_predictor.get(group)
    if not isinstance(values, dict):
        return None
    try:
        value = values.get(key)
        return round(float(value), 3) if value is not None else None
    except (TypeError, ValueError):
        return None


def _predictor_validated_total(data: SBC5CoordinatorData) -> int | None:
    direct = data.thermal_predictor.get("validated_samples_total")
    try:
        if direct is not None:
            return int(direct)
    except (TypeError, ValueError):
        pass
    values = data.thermal_predictor.get("validated_samples")
    if not isinstance(values, dict):
        return None
    total = 0
    found = False
    for horizon in ("30", "60", "120"):
        try:
            value = values.get(horizon)
            if value is not None:
                total += int(value)
                found = True
        except (TypeError, ValueError):
            continue
    return total if found else None


def _predictor_age_seconds(data: SBC5CoordinatorData) -> float | None:
    try:
        updated = float(data.thermal_predictor.get("updated_epoch"))
    except (TypeError, ValueError):
        return None
    if updated <= 0:
        return None
    return round(max(0.0, time.time() - updated), 1)


'''
if helper_anchor not in text:
    raise SystemExit("helper anchor missing")
text = text.replace(helper_anchor, helpers + helper_anchor, 1)
confidence_line = '    SensorSpec(unique_id="sbc5_ai_thermal_predictor_confidence", name="SBC5 AI Thermal Predictor Confidence", value_fn=lambda d: _predictor_number(d, "confidence_percent"), icon="mdi:brain", unit=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),\n'
extra = confidence_line + '''    SensorSpec(unique_id="sbc5_ai_thermal_predictor_mae", name="SBC5 AI Thermal Predictor Average MAE", value_fn=lambda d: _predictor_number(d, "average_mae_c"), icon="mdi:chart-bell-curve", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_mae_30s", name="SBC5 AI Thermal Predictor MAE 30s", value_fn=lambda d: _predictor_nested_number(d, "mae_ema_c", "30"), icon="mdi:chart-timeline-variant", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_mae_60s", name="SBC5 AI Thermal Predictor MAE 60s", value_fn=lambda d: _predictor_nested_number(d, "mae_ema_c", "60"), icon="mdi:chart-timeline-variant", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_mae_120s", name="SBC5 AI Thermal Predictor MAE 120s", value_fn=lambda d: _predictor_nested_number(d, "mae_ema_c", "120"), icon="mdi:chart-timeline-variant", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_last_error_30s", name="SBC5 AI Thermal Predictor Last Error 30s", value_fn=lambda d: _predictor_nested_number(d, "last_error_c", "30"), icon="mdi:delta", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_last_error_60s", name="SBC5 AI Thermal Predictor Last Error 60s", value_fn=lambda d: _predictor_nested_number(d, "last_error_c", "60"), icon="mdi:delta", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_last_error_120s", name="SBC5 AI Thermal Predictor Last Error 120s", value_fn=lambda d: _predictor_nested_number(d, "last_error_c", "120"), icon="mdi:delta", unit=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_slope", name="SBC5 AI Thermal Predictor Slope", value_fn=lambda d: _predictor_number(d, "slope_c_per_min"), icon="mdi:trending-up", unit="°C/min", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_samples", name="SBC5 AI Thermal Predictor Validated Samples", value_fn=_predictor_validated_total, icon="mdi:counter", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_ai_thermal_predictor_age", name="SBC5 AI Thermal Predictor Data Age", value_fn=_predictor_age_seconds, icon="mdi:timer-sand", unit="s", state_class=SensorStateClass.MEASUREMENT),
    SensorSpec(unique_id="sbc5_network_mac", name="SBC5 Network MAC", value_fn=lambda d: d.telemetry.network_mac or None, icon="mdi:lan-connect"),
    SensorSpec(unique_id="sbc5_network_interface", name="SBC5 Network Interface", value_fn=lambda d: d.telemetry.network_interface or None, icon="mdi:ethernet"),
'''
if confidence_line not in text:
    raise SystemExit("confidence sensor anchor missing")
text = text.replace(confidence_line, extra, 1)
sensor.write_text(text, encoding="utf-8")

# Main card diagnostics.
card = ROOT / "dashboard" / "sbc5_control_center_diagnostics_card.yaml"
text = card.read_text(encoding="utf-8")
anchor = '''        - type: custom:mushroom-template-card

          multiline_secondary: true
          primary: Postęp według obciążenia
'''
if anchor not in text:
    raise SystemExit("card anchor missing")
block = '''        - type: markdown
          content: |
            #### Jakość predykcji
            Błąd prognozy, trend i dojrzałość modelu · dane tylko diagnostyczne
          card_mod:
            style: |
              ha-card { background: transparent; box-shadow: none; padding: 2px 6px 0 6px; margin: 0; }
              ha-markdown { padding: 0 !important; }
              h4 { margin: 0 !important; font-size: 14px !important; line-height: 1.1 !important; }

        - type: grid
          columns: 2
          square: false
          cards:
            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_mae_30s
              primary: MAE +30 s
              secondary: "{{ states('sensor.sbc5_ai_thermal_predictor_mae_30s') }} °C · ostatni błąd {{ states('sensor.sbc5_ai_thermal_predictor_last_error_30s') }} °C"
              icon: mdi:chart-timeline-variant
              icon_color: cyan
              multiline_secondary: true
              tap_action: { action: more-info }
            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_mae_60s
              primary: MAE +60 s
              secondary: "{{ states('sensor.sbc5_ai_thermal_predictor_mae_60s') }} °C · ostatni błąd {{ states('sensor.sbc5_ai_thermal_predictor_last_error_60s') }} °C"
              icon: mdi:chart-timeline-variant
              icon_color: cyan
              multiline_secondary: true
              tap_action: { action: more-info }
            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_mae_120s
              primary: MAE +120 s
              secondary: "{{ states('sensor.sbc5_ai_thermal_predictor_mae_120s') }} °C · ostatni błąd {{ states('sensor.sbc5_ai_thermal_predictor_last_error_120s') }} °C"
              icon: mdi:chart-timeline-variant
              icon_color: blue
              multiline_secondary: true
              tap_action: { action: more-info }
            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_mae
              primary: Jakość modelu
              secondary: >-
                MAE śr. {{ states('sensor.sbc5_ai_thermal_predictor_mae') }} °C
                · trend {{ states('sensor.sbc5_ai_thermal_predictor_slope') }} °C/min
                · walidacje {{ states('sensor.sbc5_ai_thermal_predictor_samples') }}
                · wiek {{ states('sensor.sbc5_ai_thermal_predictor_age') }} s
              icon: mdi:brain-check-outline
              icon_color: >-
                {% set m = states('sensor.sbc5_ai_thermal_predictor_mae') | float(99) %}
                {% if m <= 0.75 %}green{% elif m <= 1.5 %}cyan{% else %}orange{% endif %}
              multiline_secondary: true
              tap_action: { action: more-info }
          card_mod:
            style: |
              #root { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)) !important; gap: clamp(6px, 1.8vw, 10px) !important; align-items: stretch !important; }
              #root > * { min-width: 0 !important; height: 100% !important; }
              @media (max-width: 339px) { #root { grid-template-columns: 1fr !important; } }

        - type: custom:mushroom-template-card
          entity: sensor.sbc5_network_mac
          primary: Tożsamość sieciowa SBC5
          secondary: "MAC hosta {{ states('sensor.sbc5_network_mac') }} · interfejs {{ states('sensor.sbc5_network_interface') }}"
          icon: mdi:lan-connect
          icon_color: teal
          multiline_secondary: true
          tap_action: { action: more-info }

'''
text = text.replace(anchor, block + anchor, 1)
card.write_text(text, encoding="utf-8")
print("Applied SBC5 3.1.3 patch (retry)")
