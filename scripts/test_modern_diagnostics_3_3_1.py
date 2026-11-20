#!/usr/bin/env python3
"""SBC5 3.3.1 modern diagnostics: read-only UI regression/security checks."""
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
js=(root/"local_apps/sbc5_control_center/config_ui/diagnostics.js").read_text(encoding="utf-8")
html=(root/"local_apps/sbc5_control_center/config_ui/index.html").read_text(encoding="utf-8")
api=(root/"local_apps/sbc5_control_center/config_ui.py").read_text(encoding="utf-8")
# All controls must be backed by a real DOM input and event callback.
for control in ("sbc5DiagnosticsHighlights","sbc5DiagnosticsSearch","sbc5DiagnosticsCompact","sbc5DiagnosticsFull","sbc5DiagnosticsGroups"):
    assert f'id="{control}"' in html, control
    assert f"$('{control}')" in js, control
assert 'type="search"' in html
assert 'aria-pressed="true"' in html and 'aria-pressed="false"' in html
assert "function renderHighlights()" in js
assert "function setCompact(value)" in js
assert "function shortName(entity)" in js
assert "function tone(entity)" in js
assert "function valueBadge(entity)" in js
assert "function displayValue(entity)" in js
assert "const shown=compact&&!search?entries.slice(0,8):entries" in js
assert "if(search&&!fold(" in js
assert "aria-hidden" in js
assert "Pokaż wszystkie" in js
assert ".replaceChildren(" in js and ".textContent" in js
assert "innerHTML" not in js and "outerHTML" not in js
assert "eval(" not in js and "localStorage" not in js
assert "SUPERVISOR_TOKEN" not in js
assert "api/save" not in js and "callService(" not in js and "callWS(" not in js
assert "api/diagnostics/entities" in js
assert "read_sbc5_sensor_states" in api
assert "SBC5_ENTITY_ID" in api
assert "if not self._require_ingress_peer(): return" in api
# No changed entity IDs or new backend writable endpoints for UI cosmetics.
assert "sbc5-diag-metric" in html
assert ".tone-danger" in html and ".tone-good" in html
assert "sbc5-diag-progress-fill" in html
assert "@media(max-width:580px)" in html
check=subprocess.run(["node","--check",str(root/"local_apps/sbc5_control_center/config_ui/diagnostics.js")],
                     capture_output=True,text=True,timeout=20)
assert check.returncode==0,check.stderr
print("SBC5 3.3.1 responsive diagnostics, safe renderer, read-only controls: PASS")
