#!/usr/bin/env python3
"""3.2.8: release is field-test only until real RPi5 thermal validation."""
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
workflow = yaml.safe_load((root / ".github/workflows/release.yml").read_text(encoding="utf-8"))
inputs = workflow.get("on", workflow.get(True))["workflow_dispatch"]["inputs"]
steps = {step["name"]: step for step in workflow["jobs"]["release"]["steps"] if "name" in step}
guard = steps["Block unverified publication"]
assert "3.2.1|3.2.2|3.2.3|3.2.4|3.2.5|3.2.6|3.2.7|3.2.8|3.2.9|3.3.0|3.3.1)" in guard["run"]
assert "Only the audited" in guard["run"]
assert guard["if"] == "${{ !inputs.dry_run }}"
assert 'test "$FIELD_TEST_ACKNOWLEDGED" = "true"' in guard["run"]
assert 'test "$HARDWARE_VERIFIED" = "true"' in guard["run"]
assert inputs["dry_run"]["default"] is True
assert inputs["hardware_verified"]["default"] is False
assert inputs["field_test_acknowledged"]["default"] is False
assert inputs["release_channel"]["default"] == "field_test"
for name in (
    "Require HACS token for publication",
    "Preflight HACS release",
    "Clone and synchronize HACS repository",
    "Wait for HACS/Hassfest/Syntax validation",
    "Publish main GitHub Release",
    "Publish HACS integration Release",
):
    assert steps[name]["if"] == "${{ !inputs.dry_run }}", name
assert "--prerelease" in steps["Publish main GitHub Release"]["run"]
assert "--prerelease" in steps["Publish HACS integration Release"]["run"]
assert "--strict-manifest-hashes" in steps["Validate prepared release strictly"]["run"]
assert "zip_security_preflight.py" in steps["Build and verify install/update package"]["run"]
assert "SBC5_Control_Center_Integration.zip" in steps["Publish HACS integration Release"]["run"]
assert "gh release view" in steps["Preflight HACS release"]["run"]
print("SBC5 3.2.8 guarded pre-release App/HACS gates: PASS")
