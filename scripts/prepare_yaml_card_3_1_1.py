#!/usr/bin/env python3
"""Prepare SBC5 Control Center 3.1.1 Card UI changes.

Release-specific helper: adds AI Thermal Predictor telemetry to the Lovelace/YAML
card and regenerates dashboard_card.json from the canonical YAML. It does not
modify Adaptive PWM or AI Cooling control logic.
"""
from __future__ import annotations

import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / "dashboard" / "sbc5_control_center_diagnostics_card.yaml"
CARD_JSON = ROOT / "local_apps" / "sbc5_control_center" / "dashboard_card.json"

THERMAL_BLOCK = r'''
        # AI Thermal Predictor 3.1.1 — observe-only telemetry on the YAML card.
        # Each parameter tile opens native Home Assistant history (More Info).
        - type: markdown
          content: |
            ### 🌡️ AI Thermal Predictor
            Prognoza temperatury CPU · tryb obserwacyjny · bez wpływu na PWM
          card_mod:
            style: |
              ha-card { background: transparent; box-shadow: none; padding: 4px 6px 0 6px; margin: 0; }
              ha-markdown { padding: 0 !important; }
              h3 { margin: 0 !important; font-size: 16px !important; line-height: 1.1 !important; }
              p { margin: 4px 0 0 0 !important; color: var(--secondary-text-color); font-size: 10.5px; }

        - type: grid
          columns: 2
          square: false
          cards:
            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_forecast_30s
              primary: Prognoza +30 s
              secondary: >-
                {% set v = states('sensor.sbc5_ai_thermal_forecast_30s') %}
                {{ v if v not in ['unknown','unavailable','none',''] else '—' }} °C
              icon: mdi:thermometer-chevron-up
              icon_color: cyan
              layout: horizontal
              tap_action: { action: more-info }

            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_forecast_60s
              primary: Prognoza +60 s
              secondary: >-
                {% set v = states('sensor.sbc5_ai_thermal_forecast_60s') %}
                {{ v if v not in ['unknown','unavailable','none',''] else '—' }} °C
              icon: mdi:thermometer-chevron-up
              icon_color: cyan
              layout: horizontal
              tap_action: { action: more-info }

            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_forecast_120s
              primary: Prognoza +120 s
              secondary: >-
                {% set v = states('sensor.sbc5_ai_thermal_forecast_120s') %}
                {{ v if v not in ['unknown','unavailable','none',''] else '—' }} °C
              icon: mdi:thermometer-chevron-up
              icon_color: blue
              layout: horizontal
              tap_action: { action: more-info }

            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_confidence
              primary: Pewność predyktora
              secondary: >-
                {% set v = states('sensor.sbc5_ai_thermal_predictor_confidence') %}
                {{ v if v not in ['unknown','unavailable','none',''] else '—' }}% · observe-only
              icon: mdi:brain
              icon_color: >-
                {% set c = states('sensor.sbc5_ai_thermal_predictor_confidence') | int(0) %}
                {% if c >= 80 %}green{% elif c >= 55 %}cyan{% else %}blue{% endif %}
              layout: horizontal
              tap_action: { action: more-info }
          card_mod:
            style: |
              #root { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)) !important; gap: clamp(6px, 1.8vw, 10px) !important; align-items: stretch !important; }
              #root > * { min-width: 0 !important; height: 100% !important; }
              @media (max-width: 339px) { #root { grid-template-columns: 1fr !important; } }
'''


def main() -> int:
    text = CARD.read_text(encoding="utf-8")
    text = text.replace("Card UI v2.8.34", "Card UI v3.1.0")
    text = text.replace("SBC5CC 2.8.34", "SBC5CC 3.1.0")

    marker = "        - type: custom:mushroom-template-card\n\n          multiline_secondary: true\n          primary: Postęp według obciążenia"
    if "AI Thermal Predictor 3.1.1 — observe-only telemetry" not in text:
        if marker not in text:
            raise SystemExit("Thermal Predictor insertion marker not found in canonical YAML card")
        text = text.replace(marker, THERMAL_BLOCK.rstrip() + "\n" + marker, 1)

    CARD.write_text(text, encoding="utf-8")
    parsed = yaml.safe_load(text)
    CARD_JSON.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Prepared 3.1.1 YAML card and dashboard_card.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
