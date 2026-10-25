#!/usr/bin/env python3
"""One-time/bootstrap normalization of the canonical Home Assistant integration."""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
DOMAIN = "sbc5_control_center"


def normalize_manifest(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    ordered = {}
    for key in ("domain", "name"):
        if key in data:
            ordered[key] = data[key]
    for key in sorted(k for k in data if k not in {"domain", "name"}):
        ordered[key] = data[key]
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_step(path: Path, title: str, description: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    cfg = data.setdefault("config", {})
    cfg.setdefault("step", {}).setdefault("user", {"title": title, "description": description})
    ordered = {"step": cfg["step"]}
    for key in cfg:
        if key != "step":
            ordered[key] = cfg[key]
    data["config"] = ordered
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    canonical = ROOT / "custom_components" / DOMAIN
    normalize_manifest(canonical / "manifest.json")
    ensure_step(canonical / "translations" / "en.json", "Add SBC5 Control Center", "Add the local SBC5 Control Center integration to Home Assistant.")
    ensure_step(canonical / "translations" / "pl.json", "Dodaj SBC5 Control Center", "Dodaj lokalną integrację SBC5 Control Center do Home Assistant.")
    bridge = APP / "bridge"
    if bridge.exists():
        shutil.rmtree(bridge)
    shutil.copytree(canonical, bridge)
    subprocess.run(["python", str(ROOT / "scripts" / "update_manifest_hashes.py")], cwd=ROOT, check=True)
    print("Canonical integration normalized and App bridge synchronized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
