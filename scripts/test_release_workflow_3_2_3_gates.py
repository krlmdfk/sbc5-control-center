#!/usr/bin/env python3
"""3.2.3: ensure gated App + HACS ZIP release remains safe and installable."""
from __future__ import annotations
import ast
from pathlib import Path
import yaml

root = Path(__file__).resolve().parents[1]
release = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
workflow = yaml.safe_load(release)
steps = {step["name"]: step for step in workflow["jobs"]["release"]["steps"] if "name" in step}
guard = steps["Block unverified publication"]
assert "3.2.1|3.2.2|3.2.3|3.2.4|3.2.5|3.2.6|3.2.7)" in guard["run"]
assert 'test "$HARDWARE_VERIFIED" = "true"' in guard["run"]
assert 'test "$FIELD_TEST_ACKNOWLEDGED" = "true"' in guard["run"]
assert guard["if"] == "${{ !inputs.dry_run }}"
inputs = workflow.get("on", workflow.get(True))["workflow_dispatch"]["inputs"]
assert inputs["dry_run"]["default"] is True
assert inputs["hardware_verified"]["default"] is False
assert inputs["field_test_acknowledged"]["default"] is False

asset = "SBC5_Control_Center_Integration.zip"
build = steps["Build and verify HACS installation ZIP"]
publish = steps["Publish HACS integration Release"]
assert build["if"] == "${{ !inputs.dry_run }}"
assert publish["if"] == "${{ !inputs.dry_run }}"
assert asset in build["env"]["HACS_ASSET"]
assert asset in publish["run"]
assert "archive.testzip()" in build["run"]
assert "manifest.json" in build["run"]
assert "download_counts.py" in build["run"]
assert "--prerelease" in publish["run"]
assert "Validate prepared release strictly" in steps
assert "--strict-manifest-hashes" in steps["Validate prepared release strictly"]["run"]
assert "zip_security_preflight.py" in steps["Build and verify install/update package"]["run"]
assert list(steps).index("Build and verify HACS installation ZIP") > list(steps).index("Wait for HACS/Hassfest/Syntax validation")
assert list(steps).index("Build and verify HACS installation ZIP") < list(steps).index("Publish HACS integration Release")

sync = (root / "scripts/sync_hacs_repo.py").read_text(encoding="utf-8")
ast.parse(sync)
assert 'h["zip_release"] = True' in sync
assert 'h["filename"] = "' + asset + '"' in sync
assert '>= (3, 2, 3)' in sync
print("SBC5 3.2.3 guarded ZIP release: PASS")
