#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
AI = APP / "ai_cooling_v5.py"
RUN = APP / "run_legacy.sh"
CARD_YAML = ROOT / "dashboard" / "sbc5_control_center_diagnostics_card.yaml"
CARD_JSON = APP / "dashboard_card.json"
TEST = ROOT / "scripts" / "test_ai_v5_observability.py"
VALIDATE = ROOT / ".github" / "workflows" / "validate.yml"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def main() -> int:
    # 1) AI v5: extend the existing TSV contract with observability fields.
    ai = AI.read_text(encoding="utf-8")
    old_ai = '''    if len(fields) >= 14:\n        fields[0] = str(output)\n        fields[1] = state\n        fields[2] = reason\n        fields[3] = str(status.get("confidence_percent", effective_conf))\n        pred = status.get("prediction_pwm_percent")\n        fields[4] = str(int(round(_num(pred, _num(fields[4], 0)))))\n        fields[6] = str(correction)\n    return model, status, fields\n'''
    new_ai = '''    if len(fields) >= 14:\n        fields[0] = str(output)\n        fields[1] = state\n        fields[2] = reason\n        fields[3] = str(status.get("confidence_percent", effective_conf))\n        pred = status.get("prediction_pwm_percent")\n        fields[4] = str(int(round(_num(pred, _num(fields[4], 0)))))\n        fields[6] = str(correction)\n\n    # v3.1.10 observability: append diagnostics to the existing evaluator TSV\n    # instead of making run_legacy perform extra jq/file reads every 10 seconds.\n    # The first 14 fields remain byte-for-byte compatible with v4 consumers.\n    def _obs(value: Any, fallback: str = "-1") -> str:\n        if value is None:\n            return fallback\n        return str(value)\n\n    observability_fields = [\n        str(int(_num(status.get("direct_confidence_percent"), direct_conf))),\n        str(int(_num(status.get("global_confidence_percent"), global_conf))),\n        str(int(_num(status.get("effective_confidence_percent"), effective_conf))),\n        _obs(status.get("direct_prediction_pwm_percent")),\n        _obs(status.get("global_prediction_pwm_percent")),\n        _obs(status.get("effective_prediction_pwm_percent")),\n        str(status.get("transfer_source") or "none"),\n        str(int(_num(status.get("effective_model_coverage_percent"), 0))),\n    ]\n    if len(fields) < 22:\n        fields.extend(observability_fields)\n    else:\n        fields[14:22] = observability_fields\n    return model, status, fields\n'''
    ai = replace_once(ai, old_ai, new_ai, "extend v5 evaluator TSV")
    AI.write_text(ai, encoding="utf-8")

    # 2) Runtime: consume appended fields with safe fallbacks for legacy/fail-open v4.
    run = RUN.read_text(encoding="utf-8")
    old_locals = '  local ai_cycle="$AI_COOLING_EVAL_CYCLES" ai_result="" ai_output="" ai_state="" ai_reason="" ai_conf=0 ai_prediction=-1 ai_qualified_samples=0 ai_correction=0 ai_bucket="" ai_observations_total=0 ai_bin_observations=0 ai_qualified_total=0 ai_qualified_flag=0 ai_qualification_reason="" ai_stable_streak=0 ai_last_log="" ai_log_tick=0\n'
    new_locals = '  local ai_cycle="$AI_COOLING_EVAL_CYCLES" ai_result="" ai_output="" ai_state="" ai_reason="" ai_conf=0 ai_prediction=-1 ai_qualified_samples=0 ai_correction=0 ai_bucket="" ai_observations_total=0 ai_bin_observations=0 ai_qualified_total=0 ai_qualified_flag=0 ai_qualification_reason="" ai_stable_streak=0 ai_last_log="" ai_log_tick=0 ai_direct_conf=0 ai_global_conf=0 ai_effective_conf=0 ai_direct_prediction=-1 ai_global_prediction=-1 ai_effective_prediction=-1 ai_transfer_source="legacy" ai_effective_coverage=0\n'
    run = replace_once(run, old_locals, new_locals, "add v5 observability locals")

    old_read = '          IFS=$\'\\t\' read -r ai_output ai_state ai_reason ai_conf ai_prediction ai_qualified_samples ai_correction ai_bucket ai_observations_total ai_bin_observations ai_qualified_total ai_qualified_flag ai_qualification_reason ai_stable_streak <<< "$ai_result"\n'
    new_read = '          IFS=$\'\\t\' read -r ai_output ai_state ai_reason ai_conf ai_prediction ai_qualified_samples ai_correction ai_bucket ai_observations_total ai_bin_observations ai_qualified_total ai_qualified_flag ai_qualification_reason ai_stable_streak ai_direct_conf ai_global_conf ai_effective_conf ai_direct_prediction ai_global_prediction ai_effective_prediction ai_transfer_source ai_effective_coverage <<< "$ai_result"\n'
    run = replace_once(run, old_read, new_read, "read v5 observability fields")

    anchor = '          case "$ai_qualified_total" in \'\'|*[!0-9]*) ai_qualified_total=0 ;; esac\n'
    fallback = '''          case "$ai_qualified_total" in ''|*[!0-9]*) ai_qualified_total=0 ;; esac\n          case "$ai_direct_conf" in ''|*[!0-9]*) ai_direct_conf="$ai_conf" ;; esac\n          case "$ai_global_conf" in ''|*[!0-9]*) ai_global_conf=0 ;; esac\n          case "$ai_effective_conf" in ''|*[!0-9]*) ai_effective_conf="$ai_conf" ;; esac\n          case "$ai_direct_prediction" in ''|-|*[!0-9.-]*) ai_direct_prediction="$ai_prediction" ;; esac\n          case "$ai_global_prediction" in ''|-|*[!0-9.-]*) ai_global_prediction=-1 ;; esac\n          case "$ai_effective_prediction" in ''|-|*[!0-9.-]*) ai_effective_prediction="$ai_prediction" ;; esac\n          [ -n "$ai_transfer_source" ] || ai_transfer_source="legacy"\n          case "$ai_effective_coverage" in ''|*[!0-9]*) ai_effective_coverage=0 ;; esac\n'''
    run = replace_once(run, anchor, fallback, "normalize observability fields")

    old_qualified_log = '            log "AI Cooling: qualified sample; bucket=${ai_bucket}; quality=${ai_qualified_samples}/${AI_COOLING_MIN_SAMPLES}; observations=${ai_bin_observations}; confidence=${ai_conf}%; prediction=${ai_prediction}%."\n'
    new_qualified_log = '            log "AI Cooling: qualified sample; bucket=${ai_bucket}; quality=${ai_qualified_samples}/${AI_COOLING_MIN_SAMPLES}; observations=${ai_bin_observations}; confidence=${ai_conf}% [direct=${ai_direct_conf}% global=${ai_global_conf}% effective=${ai_effective_conf}%]; prediction=${ai_prediction}% [direct=${ai_direct_prediction}% global=${ai_global_prediction}% effective=${ai_effective_prediction}%]; transfer=${ai_transfer_source}; effective_coverage=${ai_effective_coverage}%."\n'
    run = replace_once(run, old_qualified_log, new_qualified_log, "expand qualified AI log")

    old_state_log = '            log "AI Cooling: state=${ai_state}; reason=${ai_reason}; bucket=${ai_bucket}; observations=${ai_bin_observations}; qualified=${ai_qualified_samples}/${AI_COOLING_MIN_SAMPLES}; confidence=${ai_conf}%; prediction=${ai_prediction}%; qualification=${ai_qualification_reason}."\n            ai_last_log="${ai_state}:${ai_bucket}:${ai_conf}:${ai_prediction}:${ai_qualified_samples}"\n'
    new_state_log = '            log "AI Cooling: state=${ai_state}; reason=${ai_reason}; bucket=${ai_bucket}; observations=${ai_bin_observations}; qualified=${ai_qualified_samples}/${AI_COOLING_MIN_SAMPLES}; confidence=${ai_conf}% [direct=${ai_direct_conf}% global=${ai_global_conf}% effective=${ai_effective_conf}%]; prediction=${ai_prediction}% [direct=${ai_direct_prediction}% global=${ai_global_prediction}% effective=${ai_effective_prediction}%]; transfer=${ai_transfer_source}; effective_coverage=${ai_effective_coverage}%; qualification=${ai_qualification_reason}."\n            ai_last_log="${ai_state}:${ai_bucket}:${ai_conf}:${ai_prediction}:${ai_qualified_samples}:${ai_effective_conf}:${ai_transfer_source}:${ai_effective_coverage}"\n'
    run = replace_once(run, old_state_log, new_state_log, "expand AI state log")

    # 3) Restart Manager: report cleanup only when a posted Repair marker really existed.
    old_clear_head = '''native_restart_repair_clear() {\n  # Najpierw usuń trwały marker, aby kolejny start HA nie odtworzył starego Repair.\n  rm -f "$NATIVE_RESTART_MARKER" 2>/dev/null || true\n'''
    new_clear_head = '''native_restart_repair_clear() {\n  local had_posted_repair=false\n  [ -r "$NATIVE_REPAIR_POSTED_FILE" ] && had_posted_repair=true\n  # Najpierw usuń trwały marker, aby kolejny start HA nie odtworzył starego Repair.\n  rm -f "$NATIVE_RESTART_MARKER" 2>/dev/null || true\n'''
    run = replace_once(run, old_clear_head, new_clear_head, "capture Repair cleanup state")
    old_clear_log = '      log "Restart Manager: wyczyszczono zakończone zgłoszenie Repairs."\n'
    new_clear_log = '      [ "$had_posted_repair" = "true" ] && log "Restart Manager: wyczyszczono zakończone zgłoszenie Repairs."\n'
    run = replace_once(run, old_clear_log, new_clear_log, "make Repair cleanup log idempotent")
    RUN.write_text(run, encoding="utf-8")

    # 4) Dashboard: expose direct/global/effective confidence and prediction.
    card = CARD_YAML.read_text(encoding="utf-8")
    old_conf = '''              secondary: >-\n                {% set ai_raw = state_attr('sensor.sbc5_control_center_ai_runtime', 'ai_cooling') %} {% set ai = ai_raw if ai_raw is mapping else {} %}\n                {{ ai.confidence_percent | default(0, true) }}% · {{ ai.workload_bucket | default('—', true) }}\n                · CPU avg {{ ai.cpu_load_smoothed_percent | default(ai.cpu_load_percent | default(0, true), true) }}%\n              icon: mdi:brain\n'''
    new_conf = '''              secondary: >-\n                {% set ai_raw = state_attr('sensor.sbc5_control_center_ai_runtime', 'ai_cooling') %} {% set ai = ai_raw if ai_raw is mapping else {} %}\n                {% set direct = ai.direct_confidence_percent | default(ai.confidence_percent | default(0, true), true) %}\n                {% set global = ai.global_confidence_percent | default(0, true) %}\n                {% set effective = ai.effective_confidence_percent | default(ai.confidence_percent | default(0, true), true) %}\n                direct {{ direct }}% · global {{ global }}% · effective {{ effective }}%\n                · {{ ai.workload_bucket | default('—', true) }} · CPU avg {{ ai.cpu_load_smoothed_percent | default(ai.cpu_load_percent | default(0, true), true) }}%\n              icon: mdi:brain\n'''
    card = replace_once(card, old_conf, new_conf, "dashboard AI confidence")

    old_pred = '''              secondary: >-\n                {% set ai_raw = state_attr('sensor.sbc5_control_center_ai_runtime', 'ai_cooling') %} {% set ai = ai_raw if ai_raw is mapping else {} %}\n                {% if ai.prediction_available | default(false, true) %}\n                  model {{ ai.prediction_pwm_percent | default('—', true) }}% · baza regulatora {{ ai.baseline_pwm_percent | default('—', true) }}%\n                {% else %}\n'''
    new_pred = '''              secondary: >-\n                {% set ai_raw = state_attr('sensor.sbc5_control_center_ai_runtime', 'ai_cooling') %} {% set ai = ai_raw if ai_raw is mapping else {} %}\n                {% if ai.prediction_available | default(false, true) %}\n                  direct {{ ai.direct_prediction_pwm_percent | default(ai.prediction_pwm_percent | default('—', true), true) }}%\n                  · global {{ ai.global_prediction_pwm_percent | default('—', true) }}%\n                  · effective {{ ai.effective_prediction_pwm_percent | default(ai.prediction_pwm_percent | default('—', true), true) }}%\n                  · {{ ai.transfer_source | default('direct', true) }} · baza {{ ai.baseline_pwm_percent | default('—', true) }}%\n                {% else %}\n'''
    card = replace_once(card, old_pred, new_pred, "dashboard AI prediction")

    old_progress_tail = '''            · high {{ bp.get('high',{}).get('observations',0) }}/{{ bp.get('high',{}).get('qualified',0) }}\n            · próg {{ req }} kwal./bucket · globalnie {{ ai.model_coverage_percent | default(0, true) }}% · używany zakres {{ ai.used_model_coverage_percent | default(0, true) }}%\n          icon: mdi:chart-timeline-variant-shimmer\n'''
    new_progress_tail = '''            · high {{ bp.get('high',{}).get('observations',0) }}/{{ bp.get('high',{}).get('qualified',0) }}\n            · eff.conf idle {{ bp.get('idle',{}).get('effective_confidence_percent', bp.get('idle',{}).get('confidence_percent',0)) }}%\n            / low {{ bp.get('low',{}).get('effective_confidence_percent', bp.get('low',{}).get('confidence_percent',0)) }}%\n            / medium {{ bp.get('medium',{}).get('effective_confidence_percent', bp.get('medium',{}).get('confidence_percent',0)) }}%\n            / high {{ bp.get('high',{}).get('effective_confidence_percent', bp.get('high',{}).get('confidence_percent',0)) }}%\n            · próg {{ req }} kwal./bucket · pokrycie direct {{ ai.model_coverage_percent | default(0, true) }}% / effective {{ ai.effective_model_coverage_percent | default(ai.model_coverage_percent | default(0, true), true) }}%\n          icon: mdi:chart-timeline-variant-shimmer\n'''
    card = replace_once(card, old_progress_tail, new_progress_tail, "dashboard effective bucket progress")
    CARD_YAML.write_text(card, encoding="utf-8")

    # Keep Card Sync JSON semantically identical to the canonical YAML.
    parsed = yaml.safe_load(card)
    CARD_JSON.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 5) Regression coverage.
    TEST.write_text('''#!/usr/bin/env python3\nfrom pathlib import Path\nimport json\nimport yaml\n\nROOT = Path(__file__).resolve().parents[1]\nAPP = ROOT / "local_apps/sbc5_control_center"\nai = (APP / "ai_cooling_v5.py").read_text(encoding="utf-8")\nrun = (APP / "run_legacy.sh").read_text(encoding="utf-8")\ncard_text = (ROOT / "dashboard/sbc5_control_center_diagnostics_card.yaml").read_text(encoding="utf-8")\ncard_yaml = yaml.safe_load(card_text)\ncard_json = json.loads((APP / "dashboard_card.json").read_text(encoding="utf-8"))\n\nfor token in (\n    "observability_fields",\n    "direct_confidence_percent",\n    "global_confidence_percent",\n    "effective_confidence_percent",\n    "effective_model_coverage_percent",\n):\n    assert token in ai, token\n\nfor token in (\n    "ai_direct_conf", "ai_global_conf", "ai_effective_conf",\n    "ai_direct_prediction", "ai_global_prediction", "ai_effective_prediction",\n    "ai_transfer_source", "ai_effective_coverage",\n    "effective_coverage=${ai_effective_coverage}%",\n):\n    assert token in run, token\n\nassert "local had_posted_repair=false" in run\nassert '[ "$had_posted_repair" = "true" ] && log "Restart Manager: wyczyszczono zakończone zgłoszenie Repairs."' in run\nfor token in ("direct {{ direct }}%", "global {{ global }}%", "effective {{ effective }}%", "eff.conf idle", "pokrycie direct"):\n    assert token in card_text, token\nassert card_yaml == card_json\nprint("AI v5 observability + idempotent Restart Manager logging: PASS")\n''', encoding="utf-8")

    workflow = VALIDATE.read_text(encoding="utf-8")
    needle = "      - name: Test Restart Manager HACS handoff\n        run: python scripts/test_restart_manager_hacs_handoff.py\n\n"
    step = "      - name: Test AI v5 observability and log cleanup\n        run: python scripts/test_ai_v5_observability.py\n\n"
    if step not in workflow:
        workflow = replace_once(workflow, needle, needle + step, "add observability regression test")
        VALIDATE.write_text(workflow, encoding="utf-8")

    print("Prepared 3.1.10 AI v5 observability source changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
