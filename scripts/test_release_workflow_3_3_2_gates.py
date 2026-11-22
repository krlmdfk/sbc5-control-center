#!/usr/bin/env python3
"""3.3.2 field-test publication requires explicit authorization and validated artifacts."""
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
workflow = yaml.safe_load((root / ".github/workflows/release.yml").read_text(encoding="utf-8"))
inputs = workflow.get("on", workflow.get(True))["workflow_dispatch"]["inputs"]
steps = {s["name"]: s for s in workflow["jobs"]["release"]["steps"] if "name" in s}
gate = steps["Block unverified publication"]
run = gate["run"]
assert '3.3.2) ;;' in run
assert gate["if"] == "${{ !inputs.dry_run }}"
assert inputs["dry_run"]["default"] is True
assert inputs["release_channel"]["default"] == "field_test"
assert inputs["field_test_acknowledged"]["default"] is False
assert inputs["hardware_verified"]["default"] is False
assert 'test "$FIELD_TEST_ACKNOWLEDGED" = "true"' in run
assert 'test "$HARDWARE_VERIFIED" = "true"' in run
assert "--strict-manifest-hashes" in steps["Validate prepared release strictly"]["run"]
assert "zip_security_preflight.py" in steps["Build and verify install/update package"]["run"]
assert "Wait for HACS/Hassfest/Syntax validation" in steps
assert "--prerelease" in steps["Publish main GitHub Release"]["run"]
assert "--prerelease" in steps["Publish HACS integration Release"]["run"]
assert "SBC5_Control_Center_Integration.zip" in steps["Publish HACS integration Release"]["run"]
assert "can_guide_output" in (root / "local_apps/sbc5_control_center/ai_cooling_v5_2.py").read_text(encoding="utf-8")
print("SBC5 3.3.2 guarded pre-release publication: PASS")
