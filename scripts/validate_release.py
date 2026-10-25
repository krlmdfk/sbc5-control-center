#!/usr/bin/env python3
"""Repository-level release validation for SBC5 Control Center."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
DOMAIN = "sbc5_control_center"


def fail(msg: str) -> None:
    raise SystemExit(msg)


def run(*cmd: str) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def json_data(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    release = json_data(APP / "release.json")
    version = str(release["version"])
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail(f"Invalid release version: {version}")

    run("bash", "-n", str(APP / "run.sh"))
    run("bash", "-n", str(APP / "namespace_native_guard.sh"))
    run(sys.executable, "-m", "compileall", "-q", str(ROOT / "custom_components" / DOMAIN), str(APP))

    # Parse all JSON/YAML files except GitHub workflow YAML, where `on` is YAML-1.1-sensitive.
    for p in ROOT.rglob("*.json"):
        json_data(p)
    for pattern in ("*.yaml", "*.yml"):
        for p in ROOT.rglob(pattern):
            if ".github/workflows" in p.as_posix():
                continue
            yaml.safe_load(p.read_text(encoding="utf-8"))

    app_cfg = yaml.safe_load((APP / "config.yaml").read_text(encoding="utf-8"))
    if str(app_cfg.get("version")) != version:
        fail(f"config.yaml version mismatch: {app_cfg.get('version')} != {version}")
    if app_cfg.get("slug") != DOMAIN:
        fail(f"Unexpected app slug: {app_cfg.get('slug')}")

    manifests = [
        ROOT / "custom_components" / DOMAIN / "manifest.json",
        APP / "bridge" / "manifest.json",
        APP / "legacy_bridge" / "manifest.json",
    ]
    for p in manifests:
        data = json_data(p)
        if str(data.get("version")) != version:
            fail(f"Manifest version mismatch: {p}: {data.get('version')} != {version}")

    # Canonical integration and app bridge must be identical.
    diff = subprocess.run(
        ["diff", "-qr", "--exclude=__pycache__", str(ROOT / "custom_components" / DOMAIN), str(APP / "bridge")],
        cwd=ROOT, text=True, capture_output=True
    )
    if diff.returncode != 0:
        fail("Native integration/bridge drift:\n" + diff.stdout + diff.stderr)

    # Hassfest-sensitive manifest order.
    manifest = json_data(ROOT / "custom_components" / DOMAIN / "manifest.json")
    keys = list(manifest)
    expected_keys = [k for k in ("domain", "name") if k in manifest] + sorted(k for k in manifest if k not in {"domain", "name"})
    if keys != expected_keys:
        fail(f"Manifest keys not normalized: {keys}")

    for lang in ("en", "pl"):
        tr = json_data(ROOT / "custom_components" / DOMAIN / "translations" / f"{lang}.json")
        if not isinstance(tr.get("config", {}).get("step"), dict):
            fail(f"translations/{lang}.json missing config.step")

    run_sh = (APP / "run.sh").read_text(encoding="utf-8")
    if f'APP_VERSION="{version}"' not in run_sh or f'REQUIRED_PACKAGE_VERSION="{version}"' not in run_sh:
        fail("run.sh unified version metadata mismatch")

    package = (ROOT / "packages" / "sbc5_control_center.yaml").read_text(encoding="utf-8")
    if f"Package Version: {version}" not in package or f'state: "{version}"' not in package:
        fail("Package version metadata mismatch")

    # Verify update-manifest hashes.
    um = json_data(ROOT / "update-manifest.json")
    for key in ("version", "package_version", "card_ui_version"):
        if str(um.get(key)) != version:
            fail(f"update-manifest {key} mismatch: {um.get(key)} != {version}")
    bad = []
    for rel, expected in um.get("files", {}).items():
        p = ROOT / rel
        if not p.is_file():
            bad.append(f"missing: {rel}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            bad.append(f"hash mismatch: {rel}")
    if bad:
        fail("\n".join(bad))

    # compileall creates caches during validation; remove them so they can never leak into artifacts.
    for cache in list(ROOT.rglob("__pycache__")):
        import shutil
        shutil.rmtree(cache, ignore_errors=True)
    for pyc in list(ROOT.rglob("*.pyc")):
        pyc.unlink(missing_ok=True)

    print(f"PASS: SBC5 {version}; update-manifest {len(um['files'])}/{len(um['files'])}; integration bridge synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
