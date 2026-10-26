#!/usr/bin/env python3
"""Validate SBC5 repository/release consistency.

Normal CI validates repository structure and unified version metadata while allowing
post-release documentation drift. A release build must pass
``--strict-manifest-hashes`` so the update package remains byte-for-byte reproducible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
DOMAIN = "sbc5_control_center"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def parse_app_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', text, re.M)
    expect(bool(m), f"APP_VERSION not found: {path}")
    return m.group(1)


def compare_trees(a: Path, b: Path) -> list[str]:
    def rel_files(root: Path):
        return {
            p.relative_to(root): p
            for p in root.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        }

    af, bf = rel_files(a), rel_files(b)
    issues: list[str] = []
    for rel in sorted(set(af) | set(bf), key=str):
        if rel not in af:
            issues.append(f"bridge-only: {rel}")
        elif rel not in bf:
            issues.append(f"canonical-only: {rel}")
        elif af[rel].read_bytes() != bf[rel].read_bytes():
            issues.append(f"different: {rel}")
    return issues


def manifest_drift(um: dict) -> list[str]:
    bad: list[str] = []
    files = um.get("files", {})
    expect(isinstance(files, dict) and files, "update-manifest.json: missing files mapping")
    for rel, wanted in files.items():
        p = ROOT / rel
        if not p.is_file():
            bad.append(f"missing: {rel}")
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        if got != wanted:
            bad.append(f"hash mismatch: {rel}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--strict-manifest-hashes",
        action="store_true",
        help="fail when repository files differ from update-manifest.json; required for a release build",
    )
    args = ap.parse_args()

    # Parse all structured files first.
    for p in ROOT.rglob("*.json"):
        if "__pycache__" not in p.parts:
            load_json(p)
    for pattern in ("*.yaml", "*.yml"):
        for p in ROOT.rglob(pattern):
            if "__pycache__" not in p.parts:
                yaml.safe_load(p.read_text(encoding="utf-8"))

    # Home Assistant Apps repository metadata.
    repo_meta_path = ROOT / "repository.yaml"
    expect(repo_meta_path.is_file(), "repository.yaml missing at repository root")
    repo_meta = yaml.safe_load(repo_meta_path.read_text(encoding="utf-8"))
    expect(isinstance(repo_meta, dict), "repository.yaml must contain a mapping")
    expect(repo_meta.get("name") == "SBC5 Control Center", f"repository.yaml: unexpected name={repo_meta.get('name')!r}")
    expect(repo_meta.get("url") == "https://github.com/krlmdfk/sbc5-control-center", f"repository.yaml: unexpected url={repo_meta.get('url')!r}")
    expect(bool(repo_meta.get("maintainer")), "repository.yaml: maintainer is required")

    release = load_json(APP / "release.json")
    expected = str(release["version"])
    expect(bool(re.fullmatch(r"\d+\.\d+\.\d+", expected)), f"Invalid release version: {expected}")

    # Canonical/bridge integration manifests.
    manifests = [
        ROOT / "custom_components" / DOMAIN / "manifest.json",
        APP / "bridge" / "manifest.json",
    ]
    for p in manifests:
        data = load_json(p)
        expect(data.get("domain") == DOMAIN, f"{p}: domain={data.get('domain')!r}")
        expect(str(data.get("version")) == expected, f"{p}: version={data.get('version')!r}, expected={expected}")
        expect(data.get("config_flow") is True, f"{p}: config_flow must be true")

    legacy = load_json(APP / "legacy_bridge" / "manifest.json")
    expect(str(legacy.get("version")) == expected, f"legacy bridge version={legacy.get('version')!r}, expected={expected}")

    # Migration/Hybrid runtime must be packaged into the App image.
    migration_script = APP / "migration_manager.py"
    expect(migration_script.is_file(), "migration_manager.py missing")
    dockerfile = (APP / "Dockerfile").read_text(encoding="utf-8")
    expect("COPY migration_manager.py /migration_manager.py" in dockerfile, "Dockerfile does not package migration_manager.py")
    expect("/migration_manager.py" in dockerfile and "chmod" in dockerfile, "Dockerfile does not make migration_manager.py executable")

    migration_text = migration_script.read_text(encoding="utf-8")
    run_text = (APP / "run.sh").read_text(encoding="utf-8")
    expect("store_migration_profile_guard.json" in migration_text, "migration profile guard is missing")
    expect("PROFILE_SYNC_MARKER.unlink()" in migration_text, "migration does not reset stale Supervisor profile marker")
    expect("migration_profile_guard_active" in run_text, "run.sh does not enforce migration profile guard")
    expect("migration_profile_guard_sync" in run_text, "run.sh does not synchronize durable profiles under migration guard")

    packer = ROOT / "scripts" / "build_local_update.py"
    expect(packer.is_file(), "verified local-update packer missing")
    auto_release = (ROOT / ".github" / "workflows" / "auto-release.yml").read_text(encoding="utf-8")
    expect("build_local_update.py" in auto_release, "auto-release does not build verified local-update asset")
    expect("gh release create" in auto_release, "auto-release does not create GitHub releases")

    # App metadata.
    app_cfg = yaml.safe_load((APP / "config.yaml").read_text(encoding="utf-8"))
    expect(str(app_cfg.get("version")) == expected, f"config.yaml version={app_cfg.get('version')!r}, expected={expected}")
    expect(app_cfg.get("slug") == DOMAIN, f"config.yaml slug={app_cfg.get('slug')!r}")

    for path in [ROOT / "custom_components" / DOMAIN / "const.py", APP / "bridge" / "const.py"]:
        expect(parse_app_version(path) == expected, f"{path}: APP_VERSION mismatch")

    for key in ("package_version", "card_ui_version"):
        expect(str(release.get(key)) == expected, f"release.json {key}={release.get(key)!r}, expected={expected}")

    um_path = ROOT / "update-manifest.json"
    um = load_json(um_path)
    for key in ("version", "package_version", "card_ui_version"):
        expect(str(um.get(key)) == expected, f"update-manifest {key}={um.get(key)!r}, expected={expected}")
    expect(um.get("migration") == "local-to-store-hybrid-v1", f"update-manifest migration={um.get('migration')!r}")
    channels = um.get("installation_channels", [])
    expect("local" in channels and "home_assistant_apps" in channels, "update-manifest installation_channels incomplete")

    # Canonical integration must remain mirrored by App bridge.
    tree_issues = compare_trees(ROOT / "custom_components" / DOMAIN, APP / "bridge")
    expect(not tree_issues, "Integration/bridge mismatch:\n" + "\n".join(tree_issues))

    drift = manifest_drift(um)
    if args.strict_manifest_hashes:
        expect(not drift, "Update manifest validation failed:\n" + "\n".join(drift))
        print(f"SBC5 strict release validation PASS — version {expected}; hashes {len(um['files'])}/{len(um['files'])}")
    else:
        if drift:
            print("Repository validation PASS with release-manifest drift.")
            print("This is expected after post-release documentation/development commits.")
            print("A new release must rebuild hashes and pass --strict-manifest-hashes.")
            for item in drift:
                print(f"  - {item}")
        else:
            print(f"SBC5 repository validation PASS — version {expected}; manifest currently exact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
