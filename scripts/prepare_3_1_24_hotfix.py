#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected block not found in {path}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# 1) Extend the existing AI evaluator TSV with Thermal Predictor-specific guidance.
ai = APP / "ai_cooling_v5_2.py"
replace_once(
    ai,
    '''        str(int(round(_num(predictor.get("accepted_samples_total"), 0.0)))),
        str(int(round(_num(predictor.get("rejected_samples_total"), 0.0)))),
    ]
    if len(fields) < 34:
        fields.extend(diagnostic_fields)
    else:
        fields[22:34] = diagnostic_fields
''',
    '''        str(int(round(_num(predictor.get("accepted_samples_total"), 0.0)))),
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
''',
)

# 2) Parse and log the predictor delta separately from the overall AI correction.
legacy = APP / "run_legacy.sh"
replace_once(
    legacy,
    'tp_accepted=0 tp_rejected=0\n',
    'tp_accepted=0 tp_rejected=0 tp_req=0 tp_applied=0 tp_gate_mode="" tp_gate_reason="" tp_decision_reason=""\n',
)
replace_once(
    legacy,
    'tp_mode tp_f30 tp_f60 tp_f120 tp_conf tp_mae tp_weighted tp_error tp_gain tp_weights tp_accepted tp_rejected <<< "$ai_result"',
    'tp_mode tp_f30 tp_f60 tp_f120 tp_conf tp_mae tp_weighted tp_error tp_gain tp_weights tp_accepted tp_rejected tp_req tp_applied tp_gate_mode tp_gate_reason tp_decision_reason <<< "$ai_result"',
)
replace_once(
    legacy,
    '          case "$ai_correction" in \'\'|-|*[!0-9-]*) ai_correction=0 ;; esac\n',
    '          case "$ai_correction" in \'\'|-|*[!0-9-]*) ai_correction=0 ;; esac\n          case "$tp_req" in \'\'|-|*[!0-9-]*) tp_req=0 ;; esac\n          case "$tp_applied" in \'\'|-|*[!0-9-]*) tp_applied=0 ;; esac\n',
)
replace_once(
    legacy,
    'AI_delta=${ai_correction}pp; guard=${ai_reason}.',
    'AI_corr=${ai_correction}pp; TP_req=${tp_req}pp; TP_applied=${tp_applied}pp; gate=${tp_gate_mode:-observe}/${tp_gate_reason:-unknown}; decision=${tp_decision_reason:-near_target}; guard=${ai_reason}.',
)

# 3) Make the dashboard reflect actual guided-assist state instead of static observe-only copy.
dashboard = ROOT / "dashboard" / "sbc5_control_center_diagnostics_card.yaml"
replace_once(
    dashboard,
    '''        # AI Thermal Predictor 3.1.23 — observe-only telemetry on the YAML card.
        # Each parameter tile opens native Home Assistant history (More Info).
        - type: markdown
          content: |
            ### 🌡️ AI Thermal Predictor
            Prognoza temperatury CPU · tryb obserwacyjny · bez wpływu na PWM
''',
    '''        # AI Thermal Predictor 3.1.24 — runtime guided-assist status on the YAML card.
        # Each parameter tile opens native Home Assistant history (More Info).
        - type: markdown
          content: |
            ### 🌡️ AI Thermal Predictor
            {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
            {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
            {% set g = p.get('guided_assist', {}) if p is mapping else {} %}
            {% set gate = g.get('mode', 'observe') if g is mapping else 'observe' %}
            {% set enabled = g.get('control_output_enabled', false) if g is mapping else false %}
            {% if gate == 'active' and enabled %}
            Guided Assist aktywny · korekta predykcyjna do ±2 pp · Adaptive PWM nadrzędny
            {% elif gate == 'probation' and enabled %}
            Guided Assist · probation · tylko bezpieczne korekty w górę · Adaptive PWM nadrzędny
            {% else %}
            Tryb obserwacyjny · {{ g.get('gate_reason', 'oczekiwanie na kwalifikację') if g is mapping else 'oczekiwanie na dane' }}
            {% endif %}
''',
)
replace_once(
    dashboard,
    '''              secondary: >-
                {% set v = states('sensor.sbc5_ai_thermal_predictor_confidence') %}
                {% if v not in ['unknown','unavailable','none',''] %}
                  {{ v }}% · observe-only
                {% else %}
                  {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
                  {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
                  {{ p.get('confidence_percent', '—') }}% · observe-only
                {% endif %}
''',
    '''              secondary: >-
                {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
                {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
                {% set g = p.get('guided_assist', {}) if p is mapping else {} %}
                {% set v = states('sensor.sbc5_ai_thermal_predictor_confidence') %}
                {% set conf = v if v not in ['unknown','unavailable','none',''] else p.get('confidence_percent', '—') %}
                {% set gate = g.get('mode', 'observe') if g is mapping else 'observe' %}
                {% set enabled = g.get('control_output_enabled', false) if g is mapping else false %}
                {{ conf }}% · {% if gate == 'active' and enabled %}Guided Assist aktywny{% elif gate == 'probation' and enabled %}Probation{% else %}Observe only{% endif %}
''',
)
marker = '''          card_mod:
            style: |
              #root { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)) !important; gap: clamp(6px, 1.8vw, 10px) !important; align-items: stretch !important; }
              #root > * { min-width: 0 !important; height: 100% !important; }
              @media (max-width: 339px) { #root { grid-template-columns: 1fr !important; } }
        - type: history-graph
          title: Thermal Predictor · temperatura i prognozy · 24 h
'''
insert = '''          card_mod:
            style: |
              #root { grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)) !important; gap: clamp(6px, 1.8vw, 10px) !important; align-items: stretch !important; }
              #root > * { min-width: 0 !important; height: 100% !important; }
              @media (max-width: 339px) { #root { grid-template-columns: 1fr !important; } }

        - type: grid
          columns: 2
          square: false
          cards:
            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_confidence
              primary: Sygnał predyktora
              multiline_secondary: true
              secondary: >-
                {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
                {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
                {% set g = p.get('guided_assist', {}) if p is mapping else {} %}
                ważona {{ g.get('weighted_forecast_c', '—') }} °C · błąd {{ g.get('weighted_forecast_error_c', '—') }} °C
                · wagi 30/60/120 {{ (g.get('horizon_weights', {}) or {}).get('30', '—') }}/{{ (g.get('horizon_weights', {}) or {}).get('60', '—') }}/{{ (g.get('horizon_weights', {}) or {}).get('120', '—') }}
              icon: mdi:chart-bell-curve-cumulative
              icon_color: cyan
              layout: horizontal
              tap_action: { action: more-info }

            - type: custom:mushroom-template-card
              entity: sensor.sbc5_ai_thermal_predictor_confidence
              primary: Wpływ na PWM
              multiline_secondary: true
              secondary: >-
                {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
                {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
                {% set g = p.get('guided_assist', {}) if p is mapping else {} %}
                żądano {{ g.get('requested_delta_pp', 0) }} pp · zastosowano {{ g.get('applied_delta_pp', 0) }} pp
                · gate {{ g.get('mode', 'observe') }}/{{ g.get('gate_reason', '—') }} · decyzja {{ g.get('decision_reason', '—') }}
              icon: mdi:fan-chevron-up
              icon_color: >-
                {% set ai = state_attr('sensor.sbc5_control_center_ai_runtime','ai_cooling') %}
                {% set p = ai.get('thermal_predictor', {}) if ai is mapping else {} %}
                {% set g = p.get('guided_assist', {}) if p is mapping else {} %}
                {% set d = g.get('applied_delta_pp', 0) | int(0) %}
                {% if d > 0 %}orange{% elif d < 0 %}blue{% else %}green{% endif %}
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
replace_once(dashboard, marker, insert)

# 4) Strengthen regression coverage for the diagnostics contract.
test = ROOT / "scripts" / "test_thermal_predictor_guided_3_1_21.py"
text = test.read_text(encoding="utf-8")
needle = 'assert "hierarchical_continuous_v5_2_thermal_guided_runtime" in v52\n\nprint("Thermal Predictor guided runtime wiring: PASS")\n'
replacement = '''assert "hierarchical_continuous_v5_2_thermal_guided_runtime" in v52

legacy_text = (APP / "run_legacy.sh").read_text(encoding="utf-8")
dashboard_text = (ROOT / "dashboard" / "sbc5_control_center_diagnostics_card.yaml").read_text(encoding="utf-8")
assert 'TP_req=${tp_req}pp' in legacy_text
assert 'TP_applied=${tp_applied}pp' in legacy_text
assert 'AI_corr=${ai_correction}pp' in legacy_text
assert 'tp_gate_mode tp_gate_reason tp_decision_reason' in legacy_text
assert 'str(guidance.get("gate_mode") or "observe")' in v52
assert 'str(guidance.get("gate_reason") or "unknown")' in v52
assert 'str(guidance.get("decision_reason") or "near_target")' in v52
assert "Sygnał predyktora" in dashboard_text
assert "Wpływ na PWM" in dashboard_text
assert "guided_assist" in dashboard_text
assert "Prognoza temperatury CPU · tryb obserwacyjny · bez wpływu na PWM" not in dashboard_text

print("Thermal Predictor guided runtime wiring: PASS")
'''
if needle not in text:
    raise SystemExit("Test insertion point not found")
test.write_text(text.replace(needle, replacement, 1), encoding="utf-8")

# dashboard_card.json is the packaged JSON equivalent of the canonical YAML card.
try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required to rebuild dashboard_card.json") from exc
card = yaml.safe_load(dashboard.read_text(encoding="utf-8"))
(APP / "dashboard_card.json").write_text(json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("3.1.24 diagnostic/UI hotfix prepared")
