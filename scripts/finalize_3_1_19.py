#!/usr/bin/env python3
"""Finalize SBC5 Control Center 3.1.19 release metadata on the feature branch."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
OLD = "3.1.18"
NEW = "3.1.19"
SUMMARY_EN = "Improve Thermal Predictor accuracy with exact due-time validation, path-aware context filtering and robust thermal trend estimation."
SUMMARY_PL = "Poprawiono dokładność Thermal Predictor przez walidację dokładnie w terminie prognozy, ścieżkową filtrację kontekstu i odporny estymator trendu termicznego."

CURRENT_SURFACES = [
    ROOT / "README.md",
    ROOT / "INFO.md",
    ROOT / "custom_components/sbc5_control_center/const.py",
    ROOT / "custom_components/sbc5_control_center/manifest.json",
    ROOT / "dashboard/update_status_card.yaml",
    ROOT / "dashboard/sbc5_control_center_diagnostics_card.yaml",
    ROOT / "packages/sbc5_control_center.yaml",
    APP / "bridge/const.py",
    APP / "bridge/manifest.json",
    APP / "legacy_bridge/manifest.json",
    APP / "config.yaml",
    APP / "config_ui.py",
    APP / "namespace_native_guard.sh",
    APP / "run.sh",
    APP / "update_status_card.json",
    APP / "dashboard_card.json",
    APP / "migration_assets/sbc5_control_center.yaml",
    APP / "migration_assets/rpi5_control_center.yaml",
]


def replace_version(path: Path) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if OLD not in text:
        return
    path.write_text(text.replace(OLD, NEW), encoding="utf-8")


def update_release_json() -> None:
    path = APP / "release.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(
        {
            "version": NEW,
            "release_date": "2026-10-29",
            "restart_required": "none",
            "summary": SUMMARY_EN,
            "package_version": NEW,
            "card_ui_version": NEW,
            "summary_pl": SUMMARY_PL,
        }
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_config_description() -> None:
    path = APP / "config.yaml"
    text = path.read_text(encoding="utf-8")
    old_line = 'description: "SBC5 Control Center 3.1.19 — Persist Ethernet EEE choices across host reboots and correct userspace-managed custom1 fan profile status."'
    new_line = f'description: "SBC5 Control Center 3.1.19 — {SUMMARY_EN}"'
    if old_line in text:
        text = text.replace(old_line, new_line, 1)
    path.write_text(text, encoding="utf-8")


def update_changelog() -> None:
    section = """## 3.1.19 — 2026-10-29

### English

#### Changed

- Thermal Predictor v3.1 validates +30/+60/+120 s forecasts against the interpolated CPU temperature at the exact forecast due timestamp instead of a later polling sample.
- Replaced ordinary linear trend estimation with a robust median pairwise slope estimator to reduce sensitivity to isolated temperature spikes.
- Predictor context validation now covers the complete forecast path, so transient workload, target or PWM changes cannot be mistaken for model error after conditions return to their starting point.
- Compatible Thermal Predictor v3 regime/global calibration is retained during migration to v3.1, while the old pending forecast queue is discarded because validation semantics changed.
- Added separate accepted/rejected forecast counters, rejection categories and reasons, exact validation diagnostics, condition-shift MAE and per-horizon accuracy targets.

#### Fixed

- Prevented late or irregular telemetry polling from inflating Predictor MAE by evaluating a forecast at the poll time rather than its intended horizon.

#### Restart

- No Raspberry Pi host reboot is required. The application is restarted normally by the update process.

### Polski

#### Zmieniono

- Thermal Predictor v3.1 waliduje prognozy +30/+60/+120 s względem interpolowanej temperatury CPU dokładnie w czasie zapadalności prognozy, a nie względem późniejszej próbki pollingu.
- Zwykłe liniowe wyznaczanie trendu zastąpiono odpornym estymatorem medianowym nachylenia, ograniczając wpływ pojedynczych skoków temperatury.
- Walidacja kontekstu Predictora obejmuje teraz całą ścieżkę prognozy, dzięki czemu chwilowe zmiany obciążenia, celu lub PWM nie są traktowane jako błąd modelu po powrocie warunków do stanu początkowego.
- Przy migracji z Thermal Predictor v3 zachowywana jest zgodna kalibracja regime/global, natomiast stara kolejka oczekujących prognoz jest odrzucana ze względu na zmianę semantyki walidacji.
- Dodano osobne liczniki prognoz zaakceptowanych i odrzuconych, kategorie i przyczyny odrzuceń, diagnostykę dokładnej walidacji, MAE zmian warunków oraz cele dokładności dla każdego horyzontu.

#### Naprawiono

- Usunięto zawyżanie MAE Predictora przy opóźnionym lub nieregularnym pollingu, gdy prognoza była oceniana w chwili odczytu zamiast dla właściwego horyzontu.

#### Restart

- Pełny restart hosta Raspberry Pi nie jest wymagany. Aplikacja jest standardowo restartowana przez proces aktualizacji.

"""
    marker = "# Changelog — SBC5 Control Center\n\n"
    for path in (ROOT / "CHANGELOG.md", APP / "CHANGELOG.md"):
        text = path.read_text(encoding="utf-8")
        if "## 3.1.19 — 2026-10-29" not in text:
            if not text.startswith(marker):
                raise SystemExit(f"Unexpected changelog header: {path}")
            text = marker + section + text[len(marker):]
            path.write_text(text, encoding="utf-8")


def write_release_notes() -> None:
    path = ROOT / "RELEASE_NOTES_3.1.19.md"
    path.write_text(
        """# SBC5 Control Center 3.1.19

> Thermal Predictor v3.1 — exact-time forecast validation, path-aware context filtering and robust thermal trend estimation.

## English

### Highlights

- Forecasts at +30/+60/+120 seconds are now scored against the temperature at the exact due timestamp using bounded interpolation between telemetry samples.
- The context guard evaluates the entire forecast path, catching transient workload/PWM/target shifts even when the endpoint returns to its original state.
- Thermal trend estimation uses a robust median pairwise slope, reducing sensitivity to isolated sensor spikes.
- Existing compatible v3 calibration is preserved; the pending v3 queue is intentionally reset because validation semantics changed.
- Diagnostics now separate model-quality samples from condition/sampling rejections and expose per-horizon accuracy targets.

### Safety / control authority

Thermal Predictor v3.1 remains `observe_only` and reports `control_output_enabled=false`. Adaptive PWM, AI Cooling, Sign Guard, slew limits and emergency behavior retain physical fan-control authority.

### Restart

No Raspberry Pi host reboot is required. The application is restarted normally by the update process. If the HACS integration is updated separately, restart Home Assistant Core so the new integration version is loaded.

## Polski

### Najważniejsze zmiany

- Prognozy +30/+60/+120 s są oceniane względem temperatury dokładnie w czasie zapadalności, wyznaczanej przez ograniczoną interpolację pomiędzy próbkami telemetrii.
- Guard kontekstu analizuje całą ścieżkę prognozy i wykrywa chwilowe zmiany obciążenia/PWM/celu nawet wtedy, gdy końcowy stan wrócił do wartości początkowych.
- Trend termiczny wykorzystuje odporną medianę nachyleń par punktów, dzięki czemu pojedynczy skok czujnika ma znacznie mniejszy wpływ na prognozę.
- Zgodna kalibracja v3 jest zachowywana; oczekująca kolejka v3 jest celowo resetowana, ponieważ zmieniła się semantyka walidacji.
- Diagnostyka oddziela próbki jakości modelu od odrzuceń spowodowanych zmianą warunków lub próbkowaniem oraz pokazuje cele dokładności dla poszczególnych horyzontów.

### Bezpieczeństwo / sterowanie

Thermal Predictor v3.1 nadal działa jako `observe_only` i raportuje `control_output_enabled=false`. Fizyczne sterowanie wentylatorem pozostaje po stronie Adaptive PWM, AI Cooling, Sign Guard, ograniczeń slew oraz zabezpieczeń awaryjnych.

### Restart

Pełny restart hosta Raspberry Pi nie jest wymagany. Aplikacja jest standardowo restartowana przez proces aktualizacji. Po osobnej aktualizacji integracji HACS należy zrestartować Home Assistant Core, aby wczytał nową wersję integracji.
""",
        encoding="utf-8",
    )


def update_manifest_metadata_and_hashes() -> None:
    path = ROOT / "update-manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = NEW
    data["package_version"] = NEW
    data["card_ui_version"] = NEW
    data["release_date"] = "2026-10-29"
    data["restart_required"] = "none"
    data["summary"] = SUMMARY_EN
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["python", str(ROOT / "scripts/update_manifest_hashes.py")], cwd=ROOT, check=True)


def main() -> int:
    release = json.loads((APP / "release.json").read_text(encoding="utf-8"))
    if str(release.get("version")) == NEW:
        print("3.1.19 release surfaces already finalized")
        return 0
    if str(release.get("version")) != OLD:
        raise SystemExit(f"Expected base version {OLD}, got {release.get('version')!r}")

    for path in CURRENT_SURFACES:
        replace_version(path)
    update_release_json()
    update_config_description()
    update_changelog()
    write_release_notes()
    update_manifest_metadata_and_hashes()
    print("SBC5 Control Center 3.1.19 release surfaces finalized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
