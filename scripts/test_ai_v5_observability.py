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
assert card_yaml == card_json
print("AI v5 observability + idempotent Restart Manager logging: PASS")
