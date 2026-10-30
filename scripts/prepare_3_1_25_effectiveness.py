#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
DASH = ROOT / "dashboard" / "sbc5_control_center_diagnostics_card.yaml"
TEST = ROOT / "scripts" / "test_thermal_predictor_guided_3_1_21.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected marker not found in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


marker = '''        - type: history-graph
          title: Thermal Predictor · temperatura i prognozy · 24 h
'''
insert = '''        - type: markdown
          content: |
            #### 📈 Skuteczność interwencji Thermal Predictora
            {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
            {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
            {% set e = p.get('effectiveness', {}) if p is mapping else {} %}
            {% set score = e.get('score_percent') if e is mapping else none %}
            {% if score is not none %}
            Wynik obserwacyjny {{ score }}% · {{ e.get('samples',0) }} ocen · średnia poprawa {{ e.get('avg_improvement_c','—') }} °C
            {% else %}
            Zbieranie wyników po interwencjach · pierwsze oceny pojawią się po 30/60/120 s
            {% endif %}
          card_mod:
            style: |
              ha-card { background: transparent; box-shadow: none; padding: 4px 6px 0 6px; margin: 0; }
              ha-markdown { padding: 0 !important; }
              h4 { margin: 0 !important; font-size: 14px !important; line-height: 1.1 !important; }
              p { margin: 4px 0 0 0 !important; color: var(--secondary-text-color); font-size: 10.5px; }

        - type: grid
          columns: 2
          square: false
          cards:
            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_confidence
              primary: Effectiveness score
              multiline_secondary: true
              secondary: >-
                {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
                {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
                {% set e = p.get('effectiveness', {}) if p is mapping else {} %}
                {% set score = e.get('score_percent') if e is mapping else none %}
                {% if score is not none %}{{ score }}% · poprawa {{ e.get('improved',0) }} · neutralne {{ e.get('neutral',0) }} · pogorszenie {{ e.get('worsened',0) }}{% else %}oczekiwanie na próbki{% endif %}
              icon: mdi:target-account
              icon_color: >-
                {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
                {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
                {% set e = p.get('effectiveness', {}) if p is mapping else {} %}
                {% set s = e.get('score_percent') if e is mapping else none %}
                {% if s is none %}blue{% elif s | float(0) >= 70 %}green{% elif s | float(0) >= 55 %}cyan{% else %}orange{% endif %}
              layout: horizontal
              tap_action: { action: more-info }

            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_confidence
              primary: Interwencje TP
              multiline_secondary: true
              secondary: >-
                {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
                {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
                {% set e = p.get('effectiveness', {}) if p is mapping else {} %}
                razem {{ e.get('interventions_total',0) }} · ↑ {{ e.get('interventions_up',0) }} · ↓ {{ e.get('interventions_down',0) }} · oczekuje {{ e.get('pending',0) }}
              icon: mdi:swap-vertical-bold
              icon_color: cyan
              layout: horizontal
              tap_action: { action: more-info }

            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_confidence
              primary: Wynik +30 / +60 s
              multiline_secondary: true
              secondary: >-
                {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
                {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
                {% set e = p.get('effectiveness', {}) if p is mapping else {} %}
                {% set h = e.get('horizons', {}) if e is mapping else {} %}
                {% set h30 = h.get('30', {}) if h is mapping else {} %}
                {% set h60 = h.get('60', {}) if h is mapping else {} %}
                30 s: {{ h30.get('score_percent','—') }}% ({{ h30.get('samples',0) }}) · Δerr {{ h30.get('avg_improvement_c','—') }} °C
                · 60 s: {{ h60.get('score_percent','—') }}% ({{ h60.get('samples',0) }}) · Δerr {{ h60.get('avg_improvement_c','—') }} °C
              icon: mdi:timer-sand-complete
              icon_color: teal
              layout: horizontal
              tap_action: { action: more-info }

            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_confidence
              primary: Wynik +120 s
              multiline_secondary: true
              secondary: >-
                {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
                {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
                {% set e = p.get('effectiveness', {}) if p is mapping else {} %}
                {% set h = e.get('horizons', {}) if e is mapping else {} %}
                {% set h120 = h.get('120', {}) if h is mapping else {} %}
                {{ h120.get('score_percent','—') }}% · {{ h120.get('samples',0) }} prób · Δerr {{ h120.get('avg_improvement_c','—') }} °C
                · metryka obserwacyjna, bez wpływu na gate
              icon: mdi:timer-check-outline
              icon_color: blue
              layout: horizontal
              tap_action: { action: more-info }
          card_mod:
            style: |
              #root { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)) !important; gap: clamp(6px, 1.8vw, 10px) !important; align-items: stretch !important; }
              #root > * { min-width: 0 !important; height: 100% !important; }
              @media (max-width: 339px) { #root { grid-template-columns: 1fr !important; } }

        - type: history-graph
          title: Thermal Predictor · temperatura i prognozy · 24 h
'''
replace_once(DASH, marker, insert)

# Strengthen regression coverage for the diagnostic-only outcome tracker.
text = TEST.read_text(encoding="utf-8")
needle = 'assert "Prognoza temperatury CPU · tryb obserwacyjny · bez wpływu na PWM" not in dashboard_text\n\nprint("Thermal Predictor guided runtime wiring: PASS")\n'
replacement = '''assert "Prognoza temperatury CPU · tryb obserwacyjny · bez wpływu na PWM" not in dashboard_text
assert "Skuteczność interwencji Thermal Predictora" in dashboard_text
assert "Effectiveness score" in dashboard_text
assert "thermal_effectiveness as effectiveness" in v52
assert 'predictor["effectiveness"] = effectiveness_summary' in v52
assert 'status["thermal_predictor_effectiveness"] = effectiveness_summary' in v52
assert 'status["thermal_outcome_samples"]' not in v52
assert 'status["thermal_outcome_success_percent"]' not in v52

eff_text = (APP / "thermal_effectiveness.py").read_text(encoding="utf-8")
assert 'HORIZONS = (30, 60, 120)' in eff_text
assert 'EVENT_COOLDOWN_SECONDS = 25' in eff_text
assert '"mode": "observe_only"' in eff_text

print("Thermal Predictor guided runtime wiring: PASS")
'''
if needle not in text:
    raise SystemExit("Test insertion point not found")
TEST.write_text(text.replace(needle, replacement, 1), encoding="utf-8")

# Rebuild the packaged dashboard JSON from canonical YAML.
try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required to rebuild dashboard_card.json") from exc
card = yaml.safe_load(DASH.read_text(encoding="utf-8"))
(APP / "dashboard_card.json").write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("3.1.25 Thermal Predictor effectiveness diagnostics prepared")
