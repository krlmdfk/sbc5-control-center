#!/usr/bin/env python3
from pathlib import Path
import json
import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps/sbc5_control_center"
ai = (APP / "ai_cooling_v5.py").read_text(encoding="utf-8")
run = (APP / "run_legacy.sh").read_text(encoding="utf-8")
card_text = (ROOT / "dashboard/sbc5_control_center_diagnostics_card.yaml").read_text(encoding="utf-8")
card_yaml = yaml.safe_load(card_text)
card_json = json.loads((APP / "dashboard_card.json").read_text(encoding="utf-8"))

for token in (
    "observability_fields",
    "direct_confidence_percent",
    "global_confidence_percent",
    "effective_confidence_percent",
    "effective_model_coverage_percent",
):
    assert token in ai, token

for token in (
    "ai_direct_conf", "ai_global_conf", "ai_effective_conf",
    "ai_direct_prediction", "ai_global_prediction", "ai_effective_prediction",
    "ai_transfer_source", "ai_effective_coverage",
    "effective_coverage=${ai_effective_coverage}%",
):
    assert token in run, token

assert "local had_posted_repair=false" in run
assert '[ "$had_posted_repair" = "true" ] && log "Restart Manager: wyczyszczono zakończone zgłoszenie Repairs."' in run
for token in ("direct {{ direct }}%", "global {{ global }}%", "effective {{ effective }}%", "eff.conf idle", "pokrycie direct"):
    assert token in card_text, token

# sparse_direct_ui_guard_v315
assert "ai.direct_confidence_percent | default(ai.confidence_percent" not in card_text
assert "ai.direct_prediction_pwm_percent | default(ai.prediction_pwm_percent" not in card_text
assert "ai.direct_confidence_percent if ai.direct_confidence_percent is defined else '—'" in card_text
assert "replace(',', ' · ')" in card_text and "transient" in card_text
assert card_yaml == card_json
# 3.2.1: distinguish all-time counters from current-target/bucket counters in logs.
# The controller receives four independent values from the AI evaluator TSV.
expected_read_fields = (
    "ai_observations_total ai_bin_observations ai_qualified_total "
    "ai_qualified_flag"
)
assert expected_read_fields in run, "AI evaluator TSV counters no longer aligned"
assert 'case "$ai_observations_total" in' in run
assert 'case "$ai_bin_observations" in' in run
assert 'case "$ai_qualified_total" in' in run
assert 'case "$ai_qualified_samples" in' in run

log_lines = [line.strip() for line in run.splitlines() if 'log "AI Cooling:' in line]
assert len([line for line in log_lines if "qualified sample; bucket=" in line]) == 1
assert len([line for line in log_lines if "state=${ai_state}; reason=" in line]) == 1
for line in log_lines:
    if "qualified sample; bucket=" not in line and "state=${ai_state}; reason=" not in line:
        continue
    for field in (
        "observations_total=${ai_observations_total}",
        "bin_observations=${ai_bin_observations}",
        "qualified_samples_total=${ai_qualified_total}",
        "bin_qualified_samples=${ai_qualified_samples}/${AI_COOLING_MIN_SAMPLES}",
    ):
        assert field in line, (field, line)
    assert "; observations=${ai_bin_observations}" not in line
    assert "; qualified=${ai_qualified_samples}" not in line

legacy = (APP / "ai_cooling_legacy.py").read_text(encoding="utf-8")
assert '"observations_total": int(_num(model.get("observations_total"), 0))' in legacy
assert '"bin_observations": int(_num(b.get("observations"), 0))' in legacy
assert '"qualified_samples_total": int(_num(model.get("qualified_samples_total"), 0))' in legacy
assert '"bin_qualified_samples": qn' in legacy
assert "ai.observations_total | default(0, true)" in card_text
assert "ai.qualified_samples_total | default(0, true)" in card_text
assert "ai.observations_total | default(0, true)" in json.dumps(card_json)
assert "ai.qualified_samples_total | default(0, true)" in json.dumps(card_json)

print("AI v5 observability + idempotent Restart Manager logging: PASS")
