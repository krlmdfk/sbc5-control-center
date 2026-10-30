#!/usr/bin/env python3
from pathlib import Path

text = Path("local_apps/sbc5_control_center/run_legacy.sh").read_text(encoding="utf-8")
probe = "http://supervisor/core/api/states/sensor.sbc5_control_center_ai_runtime"
force = 'if [ "$ai_runtime_entity_present" != "true" ]; then'
sig = 'elif [ -z "${AI_RUNTIME_LAST_SIGNATURE:-}" ]'
assert probe in text, "missing AI runtime existence probe"
assert "ai_runtime_entity_present=false" in text
assert force in text
assert text.index(probe) < text.index(force) < text.index(sig)
assert "AI_RUNTIME_RELAY_INTERVAL_SECONDS=30" in text
assert "AI_RUNTIME_RELAY_KEEPALIVE_SECONDS=300" in text
assert 'curl -fsS -H "Authorization: Bearer ${SUPERVISOR_TOKEN}"' in text
print("AI runtime relay recovery regression: PASS")
