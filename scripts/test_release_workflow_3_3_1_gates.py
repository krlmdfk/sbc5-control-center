#!/usr/bin/env python3
"""SBC5 3.3.1: publish only after guarded preflight and explicit approval."""
from pathlib import Path
import yaml

root=Path(__file__).resolve().parents[1]
wf=yaml.safe_load((root/".github/workflows/release.yml").read_text(encoding="utf-8"))
inputs=wf.get("on",wf.get(True))["workflow_dispatch"]["inputs"]
steps={s["name"]:s for s in wf["jobs"]["release"]["steps"] if "name" in s}
gate=steps["Block unverified publication"]
assert "3.2.9|3.3.0|3.3.1)" in gate["run"]
assert gate["if"]=="${{ !inputs.dry_run }}"
assert 'test "$FIELD_TEST_ACKNOWLEDGED" = "true"' in gate["run"]
assert 'test "$HARDWARE_VERIFIED" = "true"' in gate["run"]
assert inputs["dry_run"]["default"] is True
assert inputs["hardware_verified"]["default"] is False
assert inputs["field_test_acknowledged"]["default"] is False
assert inputs["release_channel"]["default"]=="field_test"
assert "--strict-manifest-hashes" in steps["Validate prepared release strictly"]["run"]
assert "zip_security_preflight.py" in steps["Build and verify install/update package"]["run"]
assert "--prerelease" in steps["Publish main GitHub Release"]["run"]
assert "--prerelease" in steps["Publish HACS integration Release"]["run"]
assert "Wait for HACS/Hassfest/Syntax validation" in steps
assert "SBC5_Control_Center_Integration.zip" in steps["Publish HACS integration Release"]["run"]
js=(root/"local_apps/sbc5_control_center/config_ui/diagnostics.js").read_text(encoding="utf-8")
html=(root/"local_apps/sbc5_control_center/config_ui/index.html").read_text(encoding="utf-8")
assert "function renderHighlights()" in js and "function setCompact(value)" in js
assert "sbc5DiagnosticsSearch" in html
assert "api/save" not in js and "SUPERVISOR_TOKEN" not in js
print("SBC5 3.3.1 guarded App/HACS diagnostics field-test release: PASS")
