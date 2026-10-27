#!/usr/bin/env python3
"""Prepare one unified, bilingual SBC5 release in the main repository.

The script updates current-version surfaces, writes a professional EN/PL changelog
entry and GitHub Release notes, rebuilds update-manifest hashes, and performs strict
release validation. Historical release content is never rewritten.
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
    if old not in text:
        return
    updated = text.replace(old, new)
    had_final_newline = updated.endswith("\n")
    updated = "\n".join(line.rstrip() for line in updated.splitlines())
    if had_final_newline:
        updated += "\n"
    path.write_text(updated, encoding="utf-8")


def normalize_current_version_surfaces(version: str) -> None:
    """Normalize current runtime/package version markers independent of release history.

    A stale literal can survive generic old->new replacement indefinitely once it
    misses one release. Keep these authoritative current-state surfaces structural.
    """
    package_files = [
        ROOT / "packages" / "sbc5_control_center.yaml",
        APP / "migration_assets" / "sbc5_control_center.yaml",
        APP / "migration_assets" / "rpi5_control_center.yaml",
    ]
    for path in package_files:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r"(?m)^(# SBC5 Control Center Package Version:)\s*\d+\.\d+\.\d+\s*$",
            rf"\1 {version}",
            text,
            count=1,
        )
        text = re.sub(
            r'(?ms)(- name: SBC5 Package Version\n\s+unique_id: sbc5_package_version\n\s+icon: mdi:package-variant-closed-check\n\s+state:)\s*"\d+\.\d+\.\d+"',
            rf'\1 "{version}"',
            text,
            count=1,
        )
        path.write_text(text, encoding="utf-8")

    current_literals = [
        (APP / "namespace_native_guard.sh", r'(?m)^VERSION="\d+\.\d+\.\d+"$', f'VERSION="{version}"'),
        (APP / "config_ui.py", r"return ['\"]\d+\.\d+\.\d+['\"]", f"return '{version}'"),
    ]
    for path, pattern, replacement in current_literals:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        text, count = re.subn(pattern, replacement, text, count=1)
        if count != 1:
            raise SystemExit(f"Could not normalize current version surface: {path}")
        path.write_text(text, encoding="utf-8")


def normalize_manifest(path: Path, version: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    ordered: dict[str, object] = {}
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
    ordered = {"step": config["step"]}
    for key in config:
        if key != "step":
            ordered[key] = config[key]
    data["config"] = ordered
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bullets(values: list[str] | None, fallback: str | None = None) -> list[str]:
    result = [v.strip() for v in (values or []) if v and v.strip()]
    if not result and fallback:
        result = [fallback.strip()]
    return result


def restart_text(restart: str, lang: str) -> str:
    en = {
        "none": "No restart is required.",
        "home_assistant": "Restart Home Assistant after installation/update.",
        "host": "A full Raspberry Pi 5 host restart is required after installation/update.",
    }
    pl = {
        "none": "Restart nie jest wymagany.",
        "home_assistant": "Po instalacji/aktualizacji uruchom ponownie Home Assistant.",
        "host": "Po instalacji/aktualizacji wymagany jest pełny restart hosta Raspberry Pi 5.",
    }
    return (en if lang == "en" else pl)[restart]


def release_sections(args, lang: str) -> dict[str, list[str]]:
    suffix = "en" if lang == "en" else "pl"
    summary = getattr(args, f"summary_{suffix}").strip()
    return {
        "added": bullets(getattr(args, f"added_{suffix}")),
        "changed": bullets(getattr(args, f"changed_{suffix}"), summary),
        "fixed": bullets(getattr(args, f"fixed_{suffix}")),
        "performance": bullets(getattr(args, f"performance_{suffix}")),
        "security": bullets(getattr(args, f"security_{suffix}")),
    }


def prepend_changelog(version: str, release_date: str, args) -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if re.search(rf"^##\s+{re.escape(version)}\b", text, re.M):
        return

    en = release_sections(args, "en")
    pl = release_sections(args, "pl")
    entry = [f"## {version} — {release_date}", "", "### English", ""]
    for title, key in [
        ("Added", "added"),
        ("Changed", "changed"),
        ("Fixed", "fixed"),
        ("Performance", "performance"),
        ("Security", "security"),
    ]:
        if en[key]:
            entry.extend([f"#### {title}", "", *(f"- {x}" for x in en[key]), ""])
    entry.extend(["#### Upgrade notes", "", f"- {restart_text(args.restart_required, 'en')}", ""])

    entry.extend(["### Polski", ""])
    for title, key in [
        ("Dodano", "added"),
        ("Zmieniono", "changed"),
        ("Naprawiono", "fixed"),
        ("Wydajność", "performance"),
        ("Bezpieczeństwo", "security"),
    ]:
        if pl[key]:
            entry.extend([f"#### {title}", "", *(f"- {x}" for x in pl[key]), ""])
    entry.extend(["#### Informacje o aktualizacji", "", f"- {restart_text(args.restart_required, 'pl')}", "", ""])
    block = "\n".join(entry)

    m = re.match(r"(#[^\n]*\n(?:\n)?)", text)
    text = text[: m.end()] + block + text[m.end():] if m else block + text
    path.write_text(text, encoding="utf-8")
    shutil.copy2(path, APP / "CHANGELOG.md")


def write_release_notes(version: str, args, release: dict) -> Path:
    path = ROOT / f"RELEASE_NOTES_{version}.md"
    en = release_sections(args, "en")
    pl = release_sections(args, "pl")
    security_en = [f"- {x}" for x in en["security"]] or ["No security-specific changes."]
    security_pl = [f"- {x}" for x in pl["security"]] or ["Brak zmian dotyczących bezpieczeństwa."]

    ha_os = str(release.get("minimum_home_assistant_os", "18.3"))
    ha_core = str(release.get("minimum_home_assistant_core", "2026.10.1"))

    out: list[str] = [
        f"# SBC5 Control Center {version}",
        "",
        f"> {args.summary_en.strip()}",
        "",
        "## English",
        "",
        "### Highlights",
        "",
        f"- {args.summary_en.strip()}",
        "",
    ]
    for title, key in [
        ("Added", "added"),
        ("Changed", "changed"),
        ("Fixed", "fixed"),
        ("Performance & reliability", "performance"),
    ]:
        if en[key]:
            out.extend([f"### {title}", "", *(f"- {x}" for x in en[key]), ""])
    out.extend([
        "### Security",
        "",
        *security_en,
        "",
        "### Upgrade notes",
        "",
        f"- {restart_text(args.restart_required, 'en')}",
        "- Existing configuration and durable SBC5 state should be preserved unless a release-specific migration note says otherwise.",
        "",
        "### Compatibility",
        "",
        "- Raspberry Pi 5",
        f"- Home Assistant OS >= {ha_os}",
        f"- Home Assistant Core >= {ha_core}",
        "- Architecture: aarch64",
        "- Companion HACS integration is distributed separately.",
        "",
        "### Verification",
        "",
        "- Repository validation and runtime tests must pass before publication.",
        "- Release manifest hashes are verified in strict mode.",
        "- The local-update ZIP is rebuilt and SHA-256 verified before upload.",
        "",
        "### Downloads & links",
        "",
        "- Main project: https://github.com/krlmdfk/sbc5-control-center",
        "- HACS integration: https://github.com/krlmdfk/sbc5-control-center-integration",
        "- Documentation: https://krlmdfk.github.io/sbc5-control-center/",
        "- Release history: `CHANGELOG.md`",
        "- Issues: https://github.com/krlmdfk/sbc5-control-center/issues",
        "",
        "---",
        "",
        "## Polski",
        "",
        "### Najważniejsze zmiany",
        "",
        f"- {args.summary_pl.strip()}",
        "",
    ])
    for title, key in [
        ("Dodano", "added"),
        ("Zmieniono", "changed"),
        ("Naprawiono", "fixed"),
        ("Wydajność i niezawodność", "performance"),
    ]:
        if pl[key]:
            out.extend([f"### {title}", "", *(f"- {x}" for x in pl[key]), ""])
    out.extend([
        "### Bezpieczeństwo",
        "",
        *security_pl,
        "",
        "### Informacje o aktualizacji",
        "",
        f"- {restart_text(args.restart_required, 'pl')}",
        "- Istniejąca konfiguracja i trwały stan SBC5 powinny zostać zachowane, o ile dana wersja nie zawiera osobnej informacji migracyjnej.",
        "",
        "### Zgodność",
        "",
        "- Raspberry Pi 5",
        f"- Home Assistant OS >= {ha_os}",
        f"- Home Assistant Core >= {ha_core}",
        "- Architektura: aarch64",
        "- Integracja HACS jest dystrybuowana osobno.",
        "",
        "### Weryfikacja",
        "",
        "- Przed publikacją muszą przejść walidacja repozytorium i testy runtime.",
        "- Hashe manifestu wydania są sprawdzane w trybie ścisłym.",
        "- Lokalna paczka aktualizacji ZIP jest ponownie budowana i weryfikowana SHA-256 przed wysłaniem.",
        "",
        "### Pobieranie i linki",
        "",
        "- Projekt główny: https://github.com/krlmdfk/sbc5-control-center",
        "- Integracja HACS: https://github.com/krlmdfk/sbc5-control-center-integration",
        "- Dokumentacja: https://krlmdfk.github.io/sbc5-control-center/",
        "- Historia wersji: `CHANGELOG.md`",
        "- Zgłoszenia: https://github.com/krlmdfk/sbc5-control-center/issues",
        "",
    ])
    path.write_text("\n".join(out), encoding="utf-8")
    return path


def add_category_args(ap: argparse.ArgumentParser) -> None:
    for category in ("added", "changed", "fixed", "performance", "security"):
        ap.add_argument(f"--{category}-en", action="append", default=[])
        ap.add_argument(f"--{category}-pl", action="append", default=[])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--release-date", default="")
    ap.add_argument("--restart-required", choices=["none", "home_assistant", "host"], default="home_assistant")
    ap.add_argument("--summary-en", required=True)
    ap.add_argument("--summary-pl", required=True)
    add_category_args(ap)
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
    normalize_current_version_surfaces(new)

    canonical = ROOT / "custom_components" / DOMAIN
    bridge = APP / "bridge"
    if bridge.exists():
        shutil.rmtree(bridge)
    shutil.copytree(canonical, bridge)

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

    release = json.loads(release_path.read_text(encoding="utf-8"))
    release.update({
        "version": new,
        "release_date": release_date,
        "restart_required": args.restart_required,
        "summary": args.summary_en.strip(),
        "summary_pl": args.summary_pl.strip(),
        "package_version": new,
        "card_ui_version": new,
    })
    release_path.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    config_path = APP / "config.yaml"
    text = config_path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^version:\s*[^\n]+$", f"version: {new}", text, count=1)
    desc = f"SBC5 Control Center {new} — {args.summary_en.strip()}"
    text = re.sub(
        r"(?ms)^description:\s*.*?(?=^[A-Za-z_][A-Za-z0-9_-]*:\s|\Z)",
        f"description: {json.dumps(desc, ensure_ascii=False)}\n",
        text,
        count=1,
    )
    config_path.write_text(text, encoding="utf-8")

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

    prepend_changelog(new, release_date, args)
    write_release_notes(new, args, release)

    for path in VERSIONED_TEXT_FILES:
        replace_current_version(path, old, new)

    subprocess.run(["python", str(ROOT / "scripts" / "update_manifest_hashes.py")], cwd=ROOT, check=True)
    subprocess.run(["python", str(ROOT / "scripts" / "validate_release.py"), "--strict-manifest-hashes"], cwd=ROOT, check=True)
    print(f"Prepared professional bilingual SBC5 release {old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
