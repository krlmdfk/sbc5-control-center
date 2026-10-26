#!/usr/bin/env python3
"""Render/update the separate HACS repository from the main repository source of truth."""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
DOMAIN = "sbc5_control_center"


def render(text: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Path to local sbc5-control-center-integration git repository")
    ap.add_argument("--summary-en", required=True)
    ap.add_argument("--summary-pl", required=True)
    args = ap.parse_args()

    target = Path(args.repo).expanduser().resolve()
    if not (target / ".git").exists():
        raise SystemExit(f"Not a Git repository: {target}")

    release = json.loads((APP / "release.json").read_text(encoding="utf-8"))
    version = str(release["version"])
    values = {
        "VERSION": version,
        "HA_CORE_MIN": str(release.get("minimum_home_assistant_core", "2026.10.1")),
        "SUMMARY_EN": args.summary_en.strip(),
        "SUMMARY_PL": args.summary_pl.strip(),
    }

    # Canonical integration is the source of truth.
    src = ROOT / "custom_components" / DOMAIN
    dst = target / "custom_components" / DOMAIN
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    (dst / ".hacs_managed").touch()

    templates = ROOT / "distribution" / "hacs"
    for source_name, target_name in [
        ("README.md.template", "README.md"),
        ("info.md.template", "info.md"),
        ("RELEASE_NOTES.md.template", f"RELEASE_NOTES_{version}.md"),
    ]:
        text = (templates / source_name).read_text(encoding="utf-8")
        (target / target_name).write_text(render(text, values), encoding="utf-8")

    # Keep HACS changelog concise and release-history only.
    ch = target / "CHANGELOG.md"
    old = ch.read_text(encoding="utf-8") if ch.exists() else "# Changelog — SBC5 Control Center Integration\n\n"
    heading = f"## {version}"
    if heading not in old:
        intro = (
            f"## {version}\n\n"
            f"- {args.summary_en.strip()}\n"
            f"- {args.summary_pl.strip()}\n\n"
        )
        if old.startswith("#") and "\n\n" in old:
            pos = old.index("\n\n") + 2
            old = old[:pos] + intro + old[pos:]
        else:
            old = intro + old
        ch.write_text(old, encoding="utf-8")

    print(f"Rendered HACS repository for {version}: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
