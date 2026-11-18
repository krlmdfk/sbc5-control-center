#!/usr/bin/env python3
"""SBC5 3.2.7 test release guards: release candidate is NOT hardware validated."""
from pathlib import Path
import yaml

root=Path(__file__).resolve().parents[1]
wf=yaml.safe_load((root/".github/workflows/release.yml").read_text(encoding="utf-8"))
inputs=wf.get("on",wf.get(True))["workflow_dispatch"]["inputs"]
steps={s["name"]:s for s in wf["jobs"]["release"]["steps"] if "name" in s}
gate=steps["Block unverified publication"]
assert "3.2.1|3.2.2|3.2.3|3.2.4|3.2.5|3.2.6|3.2.7|3.2.8|3.2.9)" in gate["run"]
assert gate["if"] == "${{ !inputs.dry_run }}"
assert 'test "$FIELD_TEST_ACKNOWLEDGED" = "true"' in gate["run"]
assert 'test "$HARDWARE_VERIFIED" = "true"' in gate["run"]
assert inputs["dry_run"]["default"] is True
assert inputs["field_test_acknowledged"]["default"] is False
assert inputs["hardware_verified"]["default"] is False
assert inputs["release_channel"]["default"] == "field_test"
assert "--prerelease" in steps["Publish main GitHub Release"]["run"]
assert "--prerelease" in steps["Publish HACS integration Release"]["run"]
assert "SBC5_Control_Center_Integration.zip" in steps["Publish HACS integration Release"]["run"]
assert "--strict-manifest-hashes" in steps["Validate prepared release strictly"]["run"]
assert "zip_security_preflight.py" in steps["Build and verify install/update package"]["run"]
assert "Wait for HACS/Hassfest/Syntax validation" in steps
assert steps["Require HACS token for publication"]["if"] == "${{ !inputs.dry_run }}"
print("SBC5 3.2.7 hardware-gated prerelease workflow: PASS")
