#!/usr/bin/env python3
"""Regression gate: release ZIP allow-list must cover Dockerfile build inputs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_local_update import missing_runtime_files, required_runtime_files

manifest = json.loads((ROOT / "update-manifest.json").read_text(encoding="utf-8"))
tracked = set(manifest["files"])
required = required_runtime_files()

for name in (
    "local_apps/sbc5_control_center/ai_model_lock.py",
    "local_apps/sbc5_control_center/zip_security_preflight.py",
    "local_apps/sbc5_control_center/ai_cooling_v5.py",
    "local_apps/sbc5_control_center/ai_cooling_v5_1.py",
    "local_apps/sbc5_control_center/thermal_effectiveness.py",
    "local_apps/sbc5_control_center/rust-core/src/main.rs",
    "local_apps/sbc5_control_center/config_ui/index.html",
):
    assert name in required, f"Missing Dockerfile dependency detection: {name}"

# Simulate an update manifest which omits critical new dependencies.
exposed = tracked - {
    "local_apps/sbc5_control_center/ai_model_lock.py",
    "local_apps/sbc5_control_center/zip_security_preflight.py",
}
gaps = missing_runtime_files(exposed)
assert "local_apps/sbc5_control_center/ai_model_lock.py" in gaps, gaps
assert "local_apps/sbc5_control_center/zip_security_preflight.py" in gaps, gaps

# The release-preparation script must be able to include all of them without
# silently changing the running release. This check itself is read-only.
complete = tracked | required
assert not missing_runtime_files(complete)

hashes = (ROOT / "scripts/update_manifest_hashes.py").read_text(encoding="utf-8")
assert "required_runtime_files(ROOT)" in hashes
build = (ROOT / "scripts/build_local_update.py").read_text(encoding="utf-8")
assert "missing_runtime_files(files)" in build
gate = (ROOT / "scripts/validate_release.py").read_text(encoding="utf-8")
assert "if args.strict_manifest_hashes:" in gate
assert "Release manifest omits Dockerfile COPY inputs" in gate
print(f"Release ZIP runtime input coverage: PASS ({len(required)} required; {len(gaps)} not yet in development manifest)")
