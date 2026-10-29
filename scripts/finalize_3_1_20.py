#!/usr/bin/env python3
"""Finalize SBC5 Control Center 3.1.20 release surfaces on the feature branch."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "3.1.20"
PREVIOUS = "3.1.19"
DATE = "2026-10-29"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_current_version_surfaces() -> None:
    skip_names = {"CHANGELOG.md", f"RELEASE_NOTES_{PREVIOUS}.md"}
    skip_parts = {".git", "__pycache__"}
    text_suffixes = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt"}
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in text_suffixes:
            continue
        rel = p.relative_to(ROOT)
        if any(part in skip_parts for part in rel.parts):
            continue
        if p.name in skip_names or p.name.startswith("RELEASE_NOTES_"):
            continue
        if "CHANGELOG_ARCHIVE" in p.name:
            continue
        try:
            s = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if PREVIOUS in s:
            p.write_text(s.replace(PREVIOUS, VERSION), encoding="utf-8")


def predictor_history_card_json() -> dict:
    return {
        "type": "history-graph",
        "title": "Thermal Predictor · temperatura i prognozy · 24 h",
        "hours_to_show": 24,
        "entities": [
            {"entity": "sensor.sbc5_cpu_temperature", "name": "CPU rzeczywista"},
            {"entity": "sensor.sbc5_ai_thermal_forecast_30s", "name": "Prognoza +30 s"},
            {"entity": "sensor.sbc5_ai_thermal_forecast_60s", "name": "Prognoza +60 s"},
            {"entity": "sensor.sbc5_ai_thermal_forecast_120s", "name": "Prognoza +120 s"},
        ],
    }


def insert_json_predictor_history() -> None:
    path = ROOT / "local_apps/sbc5_control_center/dashboard_card.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    title = "Thermal Predictor · temperatura i prognozy · 24 h"

    def walk(node) -> bool:
        if isinstance(node, list):
            if any(isinstance(x, dict) and x.get("title") == title for x in node):
                return True
            for idx, item in enumerate(node):
                if isinstance(item, dict) and item.get("type") == "markdown" and "#### Jakość predykcji" in str(item.get("content", "")):
                    node.insert(idx, predictor_history_card_json())
                    return True
            for item in node:
                if walk(item):
                    return True
        elif isinstance(node, dict):
            for value in node.values():
                if walk(value):
                    return True
        return False

    if not walk(data):
        raise SystemExit("dashboard_card.json: predictor quality anchor not found")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def insert_yaml_predictor_history() -> None:
    path = ROOT / "dashboard/sbc5_control_center_diagnostics_card.yaml"
    s = path.read_text(encoding="utf-8")
    title = "Thermal Predictor · temperatura i prognozy · 24 h"
    if title in s:
        return
    anchor = "        - type: markdown\n          content: |\n            #### Jakość predykcji"
    block = """        - type: history-graph
          title: Thermal Predictor · temperatura i prognozy · 24 h
          hours_to_show: 24
          entities:
            - entity: sensor.sbc5_cpu_temperature
              name: CPU rzeczywista
            - entity: sensor.sbc5_ai_thermal_forecast_30s
              name: Prognoza +30 s
            - entity: sensor.sbc5_ai_thermal_forecast_60s
              name: Prognoza +60 s
            - entity: sensor.sbc5_ai_thermal_forecast_120s
              name: Prognoza +120 s

"""
    if anchor not in s:
        raise SystemExit("diagnostics YAML: predictor quality anchor not found")
    path.write_text(s.replace(anchor, block + anchor, 1), encoding="utf-8")


def update_release_json() -> None:
    path = ROOT / "local_apps/sbc5_control_center/release.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update({
        "version": VERSION,
        "release_date": DATE,
        "restart_required": "none",
        "summary": "Fix AI Cooling runtime layer wiring so Thermal Predictor remains live and add a combined 24-hour CPU/forecast history view.",
        "package_version": VERSION,
        "card_ui_version": VERSION,
        "summary_pl": "Naprawiono łańcuch warstw runtime AI Cooling, aby Thermal Predictor pozostawał aktywny, oraz dodano wspólny 24-godzinny wykres temperatury CPU i prognoz.",
    })
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_changelog() -> None:
    section = f"""## {VERSION} — {DATE}

### English

#### Fixed
- Fixed the packaged AI Cooling runtime chain: v5 now loads the v4 compatibility wrapper from `/ai_cooling_v4.py` instead of bypassing Thermal Predictor injection through the raw legacy module.
- Packaged `thermal_predictor_v3.py` explicitly in the application image and added a CI regression guard for the full AI runtime path.

#### Changed
- Added a dedicated **Thermal Predictor · temperature and forecasts · 24 h** history graph combining actual CPU temperature with +30/+60/+120 second forecasts.
- Kept Recorder load low: no forced duplicate-state writes were introduced; freshness remains observable through the existing Predictor data-age sensor.
- No Raspberry Pi host reboot is required. The application restarts normally during update; restart Home Assistant Core after updating the HACS integration.

### Polski

#### Naprawiono
- Naprawiono łańcuch warstw runtime AI Cooling w obrazie aplikacji: v5 ładuje teraz wrapper zgodności v4 z `/ai_cooling_v4.py`, zamiast omijać wstrzyknięcie Thermal Predictora przez surowy moduł legacy.
- `thermal_predictor_v3.py` jest jawnie pakowany do obrazu aplikacji, a CI otrzymało test regresyjny całej ścieżki runtime AI.

#### Zmieniono
- Dodano osobny wykres **Thermal Predictor · temperatura i prognozy · 24 h**, łączący rzeczywistą temperaturę CPU z prognozami +30/+60/+120 s.
- Nie wprowadzono wymuszonych duplikatów stanów do Recordera, aby nie zwiększać obciążenia HA; świeżość danych nadal pokazuje istniejący sensor wieku danych Predictora.
- Pełny restart Raspberry Pi nie jest wymagany. Aplikacja jest standardowo restartowana podczas aktualizacji; po aktualizacji integracji HACS należy zrestartować Home Assistant Core.

"""
    for rel in ("CHANGELOG.md", "local_apps/sbc5_control_center/CHANGELOG.md"):
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        if f"## {VERSION} —" in s:
            continue
        header = "# Changelog — SBC5 Control Center\n\n"
        if not s.startswith(header):
            raise SystemExit(f"{rel}: changelog header mismatch")
        p.write_text(header + section + s[len(header):], encoding="utf-8")


def write_release_notes() -> None:
    text = f"""# SBC5 Control Center {VERSION}

> AI runtime & Thermal Predictor history hotfix.

## English

### Highlights
- Repairs the application-image AI Cooling chain so v5 uses the v4 compatibility wrapper that injects Thermal Predictor v3.x.
- Packages the Thermal Predictor module explicitly and protects the wiring with a CI regression test.
- Adds a 24-hour Thermal Predictor graph with actual CPU temperature plus +30/+60/+120 s forecasts.
- Keeps the predictor strictly `observe_only`; physical PWM authority is unchanged.
- Avoids forced duplicate Recorder writes to preserve Home Assistant performance.

### Restart
No Raspberry Pi host reboot is required. The application restarts as part of the update. Restart Home Assistant Core after updating the HACS integration.

## Polski

### Najważniejsze zmiany
- Naprawia łańcuch AI Cooling w obrazie aplikacji, tak aby v5 korzystało z wrappera v4 wstrzykującego Thermal Predictor v3.x.
- Jawnie pakuje moduł Thermal Predictora i zabezpiecza ścieżkę testem regresyjnym CI.
- Dodaje 24-godzinny wykres Thermal Predictora: rzeczywista temperatura CPU oraz prognozy +30/+60/+120 s.
- Predictor nadal działa wyłącznie jako `observe_only`; fizyczne sterowanie PWM pozostaje bez zmian.
- Nie wymusza duplikowania identycznych stanów w Recorderze, dzięki czemu nie zwiększa obciążenia Home Assistanta.

### Restart
Pełny restart Raspberry Pi nie jest wymagany. Aplikacja restartuje się w ramach aktualizacji. Po aktualizacji integracji HACS należy zrestartować Home Assistant Core.
"""
    write(f"RELEASE_NOTES_{VERSION}.md", text)


def rebuild_update_manifest() -> None:
    path = ROOT / "update-manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update({
        "version": VERSION,
        "package_version": VERSION,
        "card_ui_version": VERSION,
        "release_date": DATE,
        "restart_required": "none",
        "summary": "Fix AI Cooling runtime layer wiring so Thermal Predictor remains live and add a combined 24-hour CPU/forecast history view.",
    })
    files = data.get("files")
    if not isinstance(files, dict):
        raise SystemExit("update-manifest files mapping missing")
    rebuilt = {}
    for rel in sorted(files):
        p = ROOT / rel
        if not p.is_file():
            raise SystemExit(f"update-manifest listed file missing: {rel}")
        rebuilt[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    data["files"] = rebuilt
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    replace_current_version_surfaces()
    insert_json_predictor_history()
    insert_yaml_predictor_history()
    update_release_json()
    update_changelog()
    write_release_notes()
    rebuild_update_manifest()
    print("SBC5 3.1.20 release finalization complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
