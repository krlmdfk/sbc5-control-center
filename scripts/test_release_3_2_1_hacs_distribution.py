#!/usr/bin/env python3
"""Verify a prepared 3.2.1 App + HACS distribution in an offline staging clone.

Run only after scripts/release_prepare.py has created version 3.2.1 in an
ephemeral CI checkout. Never pushes tags or branches to any repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "sbc5_control_center"
NATIVE = ROOT / "custom_components" / DOMAIN
BRIDGE = ROOT / "local_apps" / DOMAIN / "bridge"
RELEASE = ROOT / "local_apps" / DOMAIN / "release.json"
MANIFEST = ROOT / "update-manifest.json"


def files(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts and p.name != ".hacs_managed"
    }


def check() -> None:
    release = json.loads(RELEASE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert release["version"] == manifest["version"] == "3.2.1"
    assert files(NATIVE) == files(BRIDGE), "App and bridge differ"
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "hacs"
        dest.mkdir()
        subprocess.run(["git", "init", "-q", str(dest)], check=True)
        script = ROOT / "scripts" / "sync_hacs_repo.py"
        subprocess.run(
            [
                sys.executable, str(script),
                "--dest", str(dest),
                "--version", "3.2.1",
                "--summary-en", "SBC5 3.2.1 test candidate",
                "--summary-pl", "Kandydat testowy SBC5 3.2.1",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        hacs = dest / "custom_components" / DOMAIN
        assert files(NATIVE) == files(hacs), "HACS release differs from App"
        hacs_manifest = json.loads((hacs / "manifest.json").read_text(encoding="utf-8"))
        assert hacs_manifest["version"] == "3.2.1"
        assert (hacs / ".hacs_managed").is_file()
        assert (dest / "RELEASE_NOTES_3.2.1.md").is_file()
        assert (dest / "hacs.json").is_file()
        assert "2026.10.1" in (dest / "hacs.json").read_text(encoding="utf-8")
        # The dry-run must never create an HACS release/tag in the actual repo.
        assert not (ROOT / ".git" / "refs" / "tags" / "3.2.1").exists()

    print("3.2.1 isolated App/HACS distribution parity: PASS")


if __name__ == "__main__":
    check()
