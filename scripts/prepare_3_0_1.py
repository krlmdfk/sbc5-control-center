#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
VERSION = "3.0.1"
DATE = "2026-10-27"
SUMMARY_EN = (
    "Maintenance optimization: reduce steady-state Supervisor/profile reconciliation churn, "
    "deduplicate startup update checks and align all Rust/App/integration version surfaces."
)
SUMMARY_PL = (
    "Optymalizacja utrzymaniowa: ograniczenie cyklicznych odczytów Supervisor/profili, "
    "deduplikacja sprawdzania aktualizacji przy starcie oraz wyrównanie wersji Rust/App/integracji."
)


def replace(path: Path, old: str, new: str, *, count: int = 0) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"pattern not found in {path}: {old!r}")
    text = text.replace(old, new, count if count else -1)
    path.write_text(text, encoding="utf-8")


# Runtime optimization.
run = APP / "run_legacy.sh"
text = run.read_text(encoding="utf-8")
text = re.sub(r'^APP_VERSION="[^"]+"$', f'APP_VERSION="{VERSION}"', text, flags=re.M)
text = re.sub(r'^REQUIRED_PACKAGE_VERSION="[^"]+"$', f'REQUIRED_PACKAGE_VERSION="{VERSION}"', text, flags=re.M)
text = text.replace(
    'PROFILE_STATE_RECONCILE_INTERVAL_SECONDS=30',
    'PROFILE_STATE_RECONCILE_INTERVAL_SECONDS=300',
)
# HA availability restoration already refreshes UI/runtime state; the dedicated update loop
# owns update discovery. Removing this duplicate call prevents back-to-back checks on startup.
needle = '          ha_sync_selected_profile_to_requested || true\n          check_app_update || true\n          log "UX Runtime: Home Assistant dostępny — odtworzono stany Curve Editora, Restart Manager, profil i status aktualizacji."'
replacement = '          ha_sync_selected_profile_to_requested || true\n          log "UX Runtime: Home Assistant dostępny — odtworzono stany Curve Editora, Restart Manager, profil i status aktualizacji."'
if needle not in text:
    raise SystemExit("UX duplicate update-check pattern not found")
text = text.replace(needle, replacement, 1)
# Stagger local package watcher away from the full startup update check.
text = text.replace('local_update_watch_loop() {\n  sleep 15', 'local_update_watch_loop() {\n  sleep 45', 1)
run.write_text(text, encoding="utf-8")

# Native bootstrap.
run_sh = APP / "run.sh"
text = run_sh.read_text(encoding="utf-8")
text = re.sub(r'SBC5 Control Center \d+\.\d+\.\d+ native runtime bootstrap', f'SBC5 Control Center {VERSION} native runtime bootstrap', text)
text = re.sub(r'^APP_VERSION="[^"]+"$', f'APP_VERSION="{VERSION}"', text, flags=re.M)
text = re.sub(r'^REQUIRED_PACKAGE_VERSION="[^"]+"$', f'REQUIRED_PACKAGE_VERSION="{VERSION}"', text, flags=re.M)
run_sh.write_text(text, encoding="utf-8")

# Rust crate version parity.
cargo = APP / "rust-core" / "Cargo.toml"
text = cargo.read_text(encoding="utf-8")
text = re.sub(r'(?m)^version = "[^"]+"$', f'version = "{VERSION}"', text, count=1)
cargo.write_text(text, encoding="utf-8")

# App metadata.
cfg_path = APP / "config.yaml"
cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
cfg["version"] = VERSION
cfg["description"] = (
    f"SBC5 Control Center {VERSION} — maintenance optimization: lower steady-state Supervisor/profile "
    "reconciliation churn and deduplicated startup update checks; Adaptive PWM, AI Cooling and fan safety logic unchanged."
)
cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")

release_path = APP / "release.json"
release = json.loads(release_path.read_text(encoding="utf-8"))
release.update({
    "version": VERSION,
    "release_date": DATE,
    "restart_required": "none",
    "summary": SUMMARY_EN,
    "summary_pl": SUMMARY_PL,
    "package_version": VERSION,
    "card_ui_version": VERSION,
})
release_path.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Integration version parity in canonical and packaged bridge copies.
for base in (ROOT / "custom_components" / "sbc5_control_center", APP / "bridge"):
    manifest = base / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["version"] = VERSION
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    const = base / "const.py"
    c = const.read_text(encoding="utf-8")
    c = re.sub(r'^APP_VERSION = "[^"]+"$', f'APP_VERSION = "{VERSION}"', c, flags=re.M)
    const.write_text(c, encoding="utf-8")

legacy = APP / "legacy_bridge" / "manifest.json"
data = json.loads(legacy.read_text(encoding="utf-8"))
data["version"] = VERSION
legacy.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Unified update manifest metadata; hashes are rebuilt by the workflow after all edits.
um_path = ROOT / "update-manifest.json"
um = json.loads(um_path.read_text(encoding="utf-8"))
um.update({
    "version": VERSION,
    "package_version": VERSION,
    "card_ui_version": VERSION,
    "release_date": DATE,
    "restart_required": "none",
    "summary": SUMMARY_EN,
})
um_path.write_text(json.dumps(um, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Changelog: history only, per project policy.
for changelog in (ROOT / "CHANGELOG.md", APP / "CHANGELOG.md"):
    ch = changelog.read_text(encoding="utf-8")
    entry = f"""## {VERSION} — {DATE}\n\n### Optimized / Zoptymalizowano\n- Increased steady-state CPU/GPU profile reconciliation from 30 s to 300 s, reducing Supervisor API reads and repeated profile synchronization work when configuration is unchanged.\n- Removed the redundant update check from Home Assistant availability restoration and staggered the local-package watcher startup, preventing back-to-back update discovery during startup.\n- Aligned Rust Core, App/runtime, integration, package and Card UI version surfaces to {VERSION}.\n\n### Safety / Bezpieczeństwo\n- Adaptive PWM control logic, AI Cooling model/qualification, fan calibration and the verified 15-point 49°C boot curve are unchanged.\n- No host restart is required by this App-only maintenance update.\n\n"""
    if f"## {VERSION} " not in ch:
        if ch.startswith("#"):
            first_nl = ch.find("\n") + 1
            ch = ch[:first_nl] + "\n" + entry + ch[first_nl:].lstrip("\n")
        else:
            ch = entry + ch
        changelog.write_text(ch, encoding="utf-8")

notes = ROOT / f"RELEASE_NOTES_{VERSION}.md"
notes.write_text(f"""# SBC5 Control Center {VERSION}\n\n## English\n\nMaintenance release focused on reducing steady-state Home Assistant/Supervisor churn without changing cooling behavior.\n\n- CPU/GPU profile reconciliation: **30 s → 300 s** in steady state.\n- Removed duplicate update discovery during Home Assistant availability restoration.\n- Staggered local-package scanning away from the normal startup update check.\n- Unified Rust Core, App/runtime, integration and Card UI version metadata at **{VERSION}**.\n- Adaptive PWM, AI Cooling, fan calibration and the verified 49°C custom boot curve are unchanged.\n- **No Raspberry Pi host restart is required by this update.**\n\n## Polski\n\nWydanie utrzymaniowe skupione na ograniczeniu cyklicznego obciążenia Home Assistant/Supervisor bez zmiany sposobu chłodzenia.\n\n- Reconciler profili CPU/GPU: **30 s → 300 s** w stanie ustalonym.\n- Usunięto podwójne sprawdzanie aktualizacji podczas odzyskiwania dostępności Home Assistant.\n- Rozdzielono czasowo start skanera lokalnych paczek i standardowego sprawdzania aktualizacji.\n- Ujednolicono wersję Rust Core, App/runtime, integracji i Card UI do **{VERSION}**.\n- Adaptive PWM, AI Cooling, kalibracja wentylatora i zweryfikowana krzywa boot 49°C pozostają bez zmian.\n- **Ta aktualizacja nie wymaga restartu hosta Raspberry Pi.**\n""", encoding="utf-8")

print(f"Prepared SBC5 Control Center {VERSION}")
