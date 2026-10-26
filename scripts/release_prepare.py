#!/usr/bin/env python3
"""Prepare one unified SBC5 release in the main repository.

The script updates only current-version metadata/runtime surfaces. It does not rewrite
historical changelog/archive entries. After modifications it rebuilds update-manifest hashes.
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
DOMAIN = "sbc5_control_center"

# Files where the previous *current build* version is expected to move with the release.
# Historical changelogs and old release notes are intentionally excluded.
VERSIONED_TEXT_FILES = [
    ROOT / "README.md",
    ROOT / "INFO.md",
    ROOT / "DOCUMENTATION.md",
    ROOT / "dashboard" / "sbc5_control_center_diagnostics_card.yaml",
    ROOT / "dashboard" / "update_status_card.yaml",
    ROOT / "packages" / "sbc5_control_center.yaml",
    ROOT / "custom_components" / DOMAIN / "const.py",
    APP / "DOCS.en.md",
    APP / "DOCS.md",
    APP / "DOCS.pl.md",
    APP / "README.en.md",
    APP / "README.md",
    APP / "README.pl.md",
    APP / "bridge-package.yaml",
    APP / "bridge" / "const.py",
    APP / "config_ui.py",
    APP / "config_ui" / "index.html",
    APP / "dashboard_card.json",
    APP / "dashboard_sync.py",
    APP / "migration_assets" / "rpi5_control_center.yaml",
    APP / "migration_assets" / "sbc5_control_center.yaml",
    APP / "namespace_native_guard.sh",
    APP / "run.sh",
    APP / "update_status_card.json",
    ROOT / "docs" / "INSTALLATION_AND_CONFIGURATION.md",
]


def semver(v: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"\d+\.\d+\.\d+", v):
        raise ValueError(f"Invalid version: {v}; expected X.Y.Z")
    return tuple(map(int, v.split(".")))


def replace_current_version(path: Path, old: str, new: str) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if old in text:
        updated = text.replace(old, new)
        # Keep release-generated diffs compatible with `git diff --check`.
        # Historical files are not touched because this function only runs on
        # VERSIONED_TEXT_FILES.
        had_final_newline = updated.endswith("\n")
        updated = "\n".join(line.rstrip() for line in updated.splitlines())
        if had_final_newline:
            updated += "\n"
        path.write_text(updated, encoding="utf-8")


def update_json_version(path: Path, version: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_manifest(path: Path, version: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    # Hassfest order: domain, name, then alphabetical.
    ordered = {}
    for key in ("domain", "name"):
        if key in data:
            ordered[key] = data[key]
    for key in sorted(k for k in data if k not in {"domain", "name"}):
        ordered[key] = data[key]
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_config_translation(path: Path, title: str, description: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    config = data.setdefault("config", {})
    step = config.setdefault("step", {})
    step.setdefault("user", {"title": title, "description": description})
    # Keep deterministic config ordering: step first, then remaining keys.
    config_ordered = {"step": config["step"]}
    for key in config:
        if key != "step":
            config_ordered[key] = config[key]
    data["config"] = config_ordered
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepend_changelog(version: str, release_date: str, summary_en: str, summary_pl: str, restart: str) -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if re.search(rf"^##\s+{re.escape(version)}\b", text, re.M):
        return
    entry = (
        f"## {version} — {release_date}\n\n"
        f"### English\n\n- {summary_en}\n- Restart requirement: `{restart}`.\n\n"
        f"### Polski\n\n- {summary_pl}\n- Wymagany restart: `{restart}`.\n\n"
    )
    # Insert after the first H1 and introductory blank line when possible.
    m = re.match(r"(#[^\n]*\n(?:\n)?)", text)
    if m:
        text = text[: m.end()] + entry + text[m.end():]
    else:
        text = entry + text
    path.write_text(text, encoding="utf-8")
    shutil.copy2(path, APP / "CHANGELOG.md")


def write_release_notes(version: str, summary_en: str, summary_pl: str, restart: str) -> Path:
    path = ROOT / f"RELEASE_NOTES_{version}.md"
    target_en = {"none": "No restart required.", "home_assistant": "Restart Home Assistant after installation.", "host": "A full Raspberry Pi 5 restart is required after installation."}[restart]
    target_pl = {"none": "Restart nie jest wymagany.", "home_assistant": "Po instalacji uruchom ponownie Home Assistant.", "host": "Po instalacji wymagany jest pełny restart Raspberry Pi 5."}[restart]
    body = f"""# SBC5 Control Center {version}\n\n## English\n\n{summary_en}\n\n### Restart\n\n{target_en}\n\n### Related repository\n\nHACS companion integration: https://github.com/krlmdfk/sbc5-control-center-integration\n\nThe HACS integration requires the SBC5 Control Center App/runtime to be installed and running.\n\nSee `CHANGELOG.md` for release history and `DOCUMENTATION.md` / `docs/QUICK_SETUP.md` for current documentation.\n\n---\n\n## Polski\n\n{summary_pl}\n\n### Restart\n\n{target_pl}\n\n### Powiązane repozytorium\n\nIntegracja HACS: https://github.com/krlmdfk/sbc5-control-center-integration\n\nIntegracja HACS wymaga zainstalowanej i uruchomionej aplikacji/runtime SBC5 Control Center.\n\nPełna historia znajduje się w `CHANGELOG.md`, a aktualna dokumentacja w `DOCUMENTATION.md` / `docs/QUICK_SETUP.md`.\n"""
    path.write_text(body, encoding="utf-8")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--release-date", default="")
    ap.add_argument("--restart-required", choices=["none", "home_assistant", "host"], default="home_assistant")
    ap.add_argument("--summary-en", required=True)
    ap.add_argument("--summary-pl", required=True)
    args = ap.parse_args()

    release_path = APP / "release.json"
    release = json.loads(release_path.read_text(encoding="utf-8"))
    old = str(release["version"])
    new = args.version.strip()
    if semver(new) <= semver(old):
        raise SystemExit(f"New version {new} must be greater than current version {old}")
    release_date = args.release_date.strip() or date.today().isoformat()

    for path in VERSIONED_TEXT_FILES:
        replace_current_version(path, old, new)

    # Keep the native integration and app bridge byte-for-byte aligned.
    canonical = ROOT / "custom_components" / DOMAIN
    bridge = APP / "bridge"
    if bridge.exists():
        shutil.rmtree(bridge)
    shutil.copytree(canonical, bridge)

    # Normalize HACS/Hassfest-sensitive files in canonical integration, then mirror again.
    normalize_manifest(canonical / "manifest.json", new)
    ensure_config_translation(
        canonical / "translations" / "en.json",
        "Add SBC5 Control Center",
        "Add the local SBC5 Control Center integration to Home Assistant.",
    )
    ensure_config_translation(
        canonical / "translations" / "pl.json",
        "Dodaj SBC5 Control Center",
        "Dodaj lokalną integrację SBC5 Control Center do Home Assistant.",
    )
    if bridge.exists():
        shutil.rmtree(bridge)
    shutil.copytree(canonical, bridge)

    normalize_manifest(APP / "legacy_bridge" / "manifest.json", new)

    # Structured release metadata.
    release = json.loads(release_path.read_text(encoding="utf-8"))
    release.update({
        "version": new,
        "release_date": release_date,
        "restart_required": args.restart_required,
        "summary": args.summary_en.strip(),
        "package_version": new,
        "card_ui_version": new,
    })
    release_path.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # App config: version + release description.
    config_path = APP / "config.yaml"
    text = config_path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^version:\s*[^\n]+$", f"version: {new}", text, count=1)
    desc = f"SBC5 Control Center {new} — {args.summary_en.strip()}"
    # Quote the YAML scalar so release summaries may safely contain ':', '#', quotes,
    # Unicode punctuation, or other characters with YAML syntax meaning.
    yaml_desc = json.dumps(desc, ensure_ascii=False)
    text = re.sub(r"(?m)^description:\s*.*$", f"description: {yaml_desc}", text, count=1)
    config_path.write_text(text, encoding="utf-8")

    # Manifest metadata (hashes are rebuilt at the end).
    um_path = ROOT / "update-manifest.json"
    um = json.loads(um_path.read_text(encoding="utf-8"))
    um.update({
        "version": new,
        "package_version": new,
        "card_ui_version": new,
        "restart_required": args.restart_required,
        "release_date": release_date,
        "summary": args.summary_en.strip(),
    })
    um_path.write_text(json.dumps(um, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    prepend_changelog(new, release_date, args.summary_en.strip(), args.summary_pl.strip(), args.restart_required)
    write_release_notes(new, args.summary_en.strip(), args.summary_pl.strip(), args.restart_required)

    # Re-run exact version replacement after bridge copy for fallback/version constants.
    for path in VERSIONED_TEXT_FILES:
        replace_current_version(path, old, new)

    subprocess.run(["python", str(ROOT / "scripts" / "update_manifest_hashes.py")], cwd=ROOT, check=True)
    print(f"Prepared SBC5 Control Center {old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
