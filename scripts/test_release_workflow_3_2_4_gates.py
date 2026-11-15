#!/usr/bin/env python3
"""Safety regression: 3.2.4 stable requires real hardware and rollback verification.

This test checks release policy; it does not claim hardware has been tested.
"""
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
source = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
workflow = yaml.safe_load(source)
inputs = workflow.get("on", workflow.get(True))["workflow_dispatch"]["inputs"]
steps = {step["name"]: step for step in workflow["jobs"]["release"]["steps"] if "name" in step}

guard = steps["Block unverified publication"]
script = guard["run"]
assert "3.2.1|3.2.2|3.2.3|3.2.4)" in script
assert 'if [ "$RELEASE_CHANNEL" = "stable" ]; then' in script
assert 'test "$HARDWARE_VERIFIED" = "true"' in script
assert "real RPi5 hardware and rollback testing is required" in script
assert 'elif [ "$RELEASE_CHANNEL" = "field_test" ]; then' in script
assert 'test "$FIELD_TEST_ACKNOWLEDGED" = "true"' in script
assert guard["if"] == "${{ !inputs.dry_run }}"
assert guard["env"]["HARDWARE_VERIFIED"] == "${{ inputs.hardware_verified }}"
assert guard["env"]["RELEASE_CHANNEL"] == "${{ inputs.release_channel }}"
assert inputs["hardware_verified"]["default"] is False
assert inputs["field_test_acknowledged"]["default"] is False
assert inputs["dry_run"]["default"] is True
assert inputs["release_channel"]["default"] == "field_test"
assert set(inputs["release_channel"]["options"]) == {"field_test", "stable"}

for name in (
    "Require HACS token for publication",
    "Preflight HACS release",
    "Clone and synchronize HACS repository",
    "Wait for HACS/Hassfest/Syntax validation",
    "Commit and push main release metadata",
    "Publish main GitHub Release",
    "Publish HACS integration Release",
):
    assert steps[name]["if"] == "${{ !inputs.dry_run }}", name

assert "--strict-manifest-hashes" in steps["Validate prepared release strictly"]["run"]
assert "zip_security_preflight.py" in steps["Build and verify install/update package"]["run"]
assert "SBC5_Control_Center_Integration.zip" in steps["Publish HACS integration Release"]["run"]
assert "--prerelease" in steps["Publish main GitHub Release"]["run"]
assert "--prerelease" in steps["Publish HACS integration Release"]["run"]
print("3.2.4 stable release safety gates: PASS (hardware still unverified)")
