#!/usr/bin/env python3
"""Synchronize the HACS distribution repository from the canonical main repository."""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "sbc5_control_center"


def render(text: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--summary-en", required=True)
    ap.add_argument("--summary-pl", required=True)
    args = ap.parse_args()
    dest = Path(args.dest).resolve()
    if not (dest / ".git").exists():
        raise SystemExit(f"Destination is not a git clone: {dest}")

    release = json.loads((ROOT / "local_apps" / "sbc5_control_center" / "release.json").read_text(encoding="utf-8"))
    values = {
        "VERSION": args.version,
        "HA_CORE_MIN": str(release.get("minimum_home_assistant_core", "2026.10.1")),
        "SUMMARY_EN": args.summary_en.strip(),
        "SUMMARY_PL": args.summary_pl.strip(),
    }

    src = ROOT / "custom_components" / DOMAIN
    target = dest / "custom_components" / DOMAIN
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, target)
    (target / ".hacs_managed").write_text("managed-by=hacs\n", encoding="utf-8")

    tmpl_dir = ROOT / "distribution" / "hacs"
    for name in ("README.md", "info.md"):
        text = render((tmpl_dir / (name + ".template")).read_text(encoding="utf-8"), values)
        (dest / name).write_text(text, encoding="utf-8")

    notes = render((tmpl_dir / "RELEASE_NOTES.md.template").read_text(encoding="utf-8"), values)
    (dest / f"RELEASE_NOTES_{args.version}.md").write_text(notes, encoding="utf-8")

    # Keep HACS metadata stable, but create it when bootstrapping a new clone.
    hacs_json = dest / "hacs.json"
    if not hacs_json.exists():
        hacs_json.write_text(json.dumps({"name": "SBC5 Control Center", "homeassistant": values["HA_CORE_MIN"]}, indent=2) + "\n", encoding="utf-8")
    else:
        h = json.loads(hacs_json.read_text(encoding="utf-8"))
        h["homeassistant"] = values["HA_CORE_MIN"]
        hacs_json.write_text(json.dumps(h, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Synchronized HACS repo to {args.version}: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
