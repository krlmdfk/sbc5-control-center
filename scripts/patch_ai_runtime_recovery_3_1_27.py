#!/usr/bin/env python3
from pathlib import Path

RUN = Path("local_apps/sbc5_control_center/run_legacy.sh")
VALIDATE = Path(".github/workflows/validate.yml")
TEST = Path("scripts/test_ai_runtime_relay_recovery_3_1_27.py")

text = RUN.read_text(encoding="utf-8")
old = '''      if [ -z "${AI_RUNTIME_LAST_SIGNATURE:-}" ] || [ "$ai_runtime_signature" != "$AI_RUNTIME_LAST_SIGNATURE" ]; then
        ai_runtime_due=true
      elif [ "${TELEMETRY_LAST_AI_RELAY_PUBLISH:-0}" -eq 0 ] 2>/dev/null || [ $((relay_now - TELEMETRY_LAST_AI_RELAY_PUBLISH)) -ge "$AI_RUNTIME_RELAY_KEEPALIVE_SECONDS" ] 2>/dev/null; then
        ai_runtime_due=true
      fi
'''
new = '''      # 3.1.27: REST-created states disappear on a Home Assistant Core restart.
      # A short Core restart can happen entirely between UX availability polls, leaving
      # the unchanged-payload signature cached and delaying recreation until keepalive.
      # Probe only on the existing 30 s AI-relay cadence and force a publish when the
      # canonical runtime entity is missing; this adds no new loop and no duplicate
      # Recorder writes while the state exists.
      local ai_runtime_entity_present=true
      if ! curl -fsS -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \\
        http://supervisor/core/api/states/sensor.sbc5_control_center_ai_runtime >/dev/null 2>&1; then
        ai_runtime_entity_present=false
      fi
      if [ "$ai_runtime_entity_present" != "true" ]; then
        ai_runtime_due=true
      elif [ -z "${AI_RUNTIME_LAST_SIGNATURE:-}" ] || [ "$ai_runtime_signature" != "$AI_RUNTIME_LAST_SIGNATURE" ]; then
        ai_runtime_due=true
      elif [ "${TELEMETRY_LAST_AI_RELAY_PUBLISH:-0}" -eq 0 ] 2>/dev/null || [ $((relay_now - TELEMETRY_LAST_AI_RELAY_PUBLISH)) -ge "$AI_RUNTIME_RELAY_KEEPALIVE_SECONDS" ] 2>/dev/null; then
        ai_runtime_due=true
      fi
'''
if old not in text:
    raise SystemExit("AI runtime relay decision block not found")
RUN.write_text(text.replace(old, new, 1), encoding="utf-8")

TEST.write_text('''#!/usr/bin/env python3
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
assert "curl -fsS -H \"Authorization: Bearer ${SUPERVISOR_TOKEN}\"" in text
print("AI runtime relay recovery regression: PASS")
''', encoding="utf-8")

v = VALIDATE.read_text(encoding="utf-8")
anchor = '''      - name: Test AI runtime layer wiring
        run: python scripts/test_ai_runtime_wiring_3_1_20.py
'''
insert = anchor + '''
      - name: Test AI runtime relay recovery after Home Assistant restart
        run: python scripts/test_ai_runtime_relay_recovery_3_1_27.py
'''
if anchor not in v:
    raise SystemExit("validate workflow anchor not found")
if "test_ai_runtime_relay_recovery_3_1_27.py" not in v:
    VALIDATE.write_text(v.replace(anchor, insert, 1), encoding="utf-8")

print("3.1.27 AI runtime relay patch prepared")
