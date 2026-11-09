#!/usr/bin/env python3
"""Preflight for the SBC5 3.2.0 Global Community Edition candidate.

This static gate is intentionally not a substitute for real Pi 5 installation,
host-access or fan safety testing. Do not publish based on this script alone.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
conf = yaml.safe_load((APP / "config.yaml").read_text(encoding="utf-8"))
assert conf["arch"] == ["aarch64"], conf["arch"]
assert conf["machine"] == ["raspberrypi5-64"], conf["machine"]
assert conf["slug"] == "sbc5_control_center"
assert conf["homeassistant"] == "2026.10.1"

# Audit high privileges; they must not be removed during a version-only release
# until we have evidence that all host-facing functions still work.
assert conf["full_access"] is True
assert conf["host_pid"] is True
assert conf["apparmor"] is False
assert {"SYS_ADMIN", "SYS_PTRACE"} <= set(conf["privileged"])
assert conf["hassio_role"] == "manager"

release = json.loads((APP / "release.json").read_text(encoding="utf-8"))
version = release["version"]
# The 3.2.0 privilege disclosure remains the baseline for 3.2.x.
# Keep 3.1.37 compatibility for the previously published release archive.
assert version == "3.1.37" or (
    version.startswith("3.2.") and version.split(".")[2].isdigit()
), version
if version != "3.1.37":
    assert conf["version"] == version
    assert release["package_version"] == version
    assert release["card_ui_version"] == version
    assert json.loads((ROOT / "custom_components/sbc5_control_center/manifest.json").read_text())["version"] == version

audit = (ROOT / "docs/SECURITY_PRIVILEGE_AUDIT_3_2_0.md").read_text(encoding="utf-8")
global_doc = (ROOT / "docs/GLOBAL_RELEASE_3_2_0.md").read_text(encoding="utf-8")
install = (ROOT / "docs/GLOBAL_INSTALL.md").read_text(encoding="utf-8")
for key in ("full_access", "SYS_ADMIN", "SYS_PTRACE", "host_pid", "apparmor", "hassio_role"):
    assert key in audit, key
for required in ("release candidate", "not published", "Raspberry Pi 5", "rollback", "HACS", "security"):
    assert required.lower() in global_doc.lower(), required
assert "raspberrypi5-64" in install
assert "Protection Mode" in install
assert "official" in install.lower()
print("SBC5 Global Edition static preflight: PASS (hardware gates still pending)")
