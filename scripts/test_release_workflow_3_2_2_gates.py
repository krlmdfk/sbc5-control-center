#!/usr/bin/env python3
"""Release 3.2.2 must use the established gated App + HACS publisher.

This validates the published workflow structure only. It never pushes or deploys.
"""
from __future__ import annotations

from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
workflow = yaml.safe_load(source)
steps = {step["name"]: step for step in workflow["jobs"]["release"]["steps"] if "name" in step}
guard = steps["Block unverified publication"]

assert "3.2.1|3.2.2)" in guard["run"], "3.2.2 must be explicitly allowlisted"
assert "Only the audited 3.2.1 and 3.2.2 release paths" in guard["run"]
assert 'test "$HARDWARE_VERIFIED" = "true"' in guard["run"]
assert 'test "$FIELD_TEST_ACKNOWLEDGED" = "true"' in guard["run"]
assert 'if [ "$RELEASE_CHANNEL" = "stable" ]; then' in guard["run"]
assert 'elif [ "$RELEASE_CHANNEL" = "field_test" ]; then' in guard["run"]
assert guard["if"] == "${{ !inputs.dry_run }}"

inputs = workflow.get("on", workflow.get(True))["workflow_dispatch"]["inputs"]
assert inputs["dry_run"]["default"] is True
assert inputs["hardware_verified"]["default"] is False
assert inputs["field_test_acknowledged"]["default"] is False
assert "OFF-DEVICE backups" in inputs["field_test_acknowledged"]["description"]

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
package = steps["Build and verify install/update package"]["run"]
for required in ("--verify-only", "zip_security_preflight.py", "sha256sum"):
    assert required in package, required
assert "--prerelease" in steps["Publish main GitHub Release"]["run"]
assert "--prerelease" in steps["Publish HACS integration Release"]["run"]
print("Guarded 3.2.2 field-test release workflow: PASS")
