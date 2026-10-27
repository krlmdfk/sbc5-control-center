#!/usr/bin/env python3
from __future__ import annotations
import json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'local_apps' / 'sbc5_control_center'
BASE = 'origin/migration/rust-3.0.0'


def show(path: str) -> str:
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], text=True)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def restore_public_surfaces() -> None:
    for rel in [
        'local_apps/sbc5_control_center/config.yaml',
        'CHANGELOG.md',
        'local_apps/sbc5_control_center/CHANGELOG.md',
        'update-manifest.json',
        'local_apps/sbc5_control_center/release.json',
    ]:
        write(ROOT / rel, show(rel))
    for rel in [
        'local_apps/sbc5_control_center/CANARY_TEST.md',
        'local_apps/sbc5_control_center/canary_runtime_diag.sh',
        'RELEASE_NOTES_3.0.1.md','RELEASE_NOTES_3.0.2.md','RELEASE_NOTES_3.0.3.md','RELEASE_NOTES_3.0.4.md','RELEASE_NOTES_3.0.5.md',
    ]:
        p = ROOT / rel
        if p.exists():
            p.unlink()


def normalize_runtime() -> None:
    p = APP / 'run.sh'
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'\n# Canary-only one-shot diagnostics\..*?\n\[ -x /canary_runtime_diag\.sh \] && /canary_runtime_diag\.sh &\n', '\n', s, flags=re.S)
    s = s.replace('3.0.5', '3.0.0')
    write(p, s)

    p = APP / 'Dockerfile'
    s = p.read_text(encoding='utf-8').replace('COPY canary_runtime_diag.sh /\n', '').replace(' /canary_runtime_diag.sh', '')
    write(p, s)

    for raw in subprocess.check_output(['git','ls-files','-z']).split(b'\0'):
        if not raw:
            continue
        p = ROOT / raw.decode()
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        if '3.0.5' in text:
            write(p, text.replace('3.0.5','3.0.0'))


def write_metadata() -> None:
    rp = APP / 'release.json'
    rel = json.loads(rp.read_text(encoding='utf-8'))
    rel.update({
        'version':'3.0.0','release_date':'2026-10-27','restart_required':'none',
        'summary':'Hybrid Rust Core release: native low-overhead host telemetry and runtime health with the proven compatibility control plane, verified preserved-state migration, Adaptive PWM/AI Cooling recovery and rollback safety.',
        'summary_pl':'Hybrydowe wydanie Rust Core: natywna lekka telemetria hosta i kontrola zdrowia runtime ze sprawdzoną warstwą zgodności, zweryfikowaną migracją stanu, odzyskiwaniem Adaptive PWM/AI Cooling i bezpiecznym rollbackiem.',
        'package_version':'3.0.0','card_ui_version':'3.0.0',
    })
    write(rp, json.dumps(rel, ensure_ascii=False, indent=2)+'\n')

    mp = ROOT / 'update-manifest.json'
    man = json.loads(mp.read_text(encoding='utf-8'))
    man.update({'version':'3.0.0','package_version':'3.0.0','card_ui_version':'3.0.0','slug':'sbc5_control_center','target_slug':'sbc5_control_center','restart_required':'none','release_date':'2026-10-27','summary':rel['summary']})
    write(mp, json.dumps(man, ensure_ascii=False, indent=2)+'\n')


def write_changelog_and_notes() -> None:
    changelog = (ROOT/'CHANGELOG.md').read_text(encoding='utf-8')
    entry = '''## 3.0.0 — 2026-10-27\n\n### English\n\n#### Added\n\n- Hybrid Rust Core for low-overhead Raspberry Pi 5 host telemetry and runtime-health reporting, with automatic fallback to the proven compatibility/control plane.\n- Verified Store migration handoff with SHA-256 validation, target backup and rollback for AI Cooling data, fan calibration, CPU/GPU profiles, custom-curve state and user options.\n\n#### Changed\n\n- The proven shell/Python control plane remains authoritative for fan safety, Adaptive PWM, AI Cooling, CPU/GPU profiles and update/recovery workflows while the Rust core owns lightweight native telemetry/runtime health.\n- Card UI release version is rendered dynamically before Lovelace synchronization so the stored dashboard and App release remain aligned.\n\n#### Fixed\n\n- Persist the complete imported App option set into the Supervisor option store before migration finalization, preventing stale target defaults from replacing migrated 49°C / AI Assist settings after an App restart.\n- Treat completed namespace migration as authoritative for canonical SBC5 control ownership while retaining the explicit owner interlock during incomplete migration.\n- Recover a safe orphaned `mode=disabled` thermal-zone takeover after App rebuild/update when `custom1` is active, `max_state >= 100`, `cur_state` is writable and namespace migration is complete.\n- Align Rust, bootstrap and image version surfaces at build time so package/runtime version checks use the same public release version.\n\n#### Performance\n\n- Native Rust telemetry/runtime-health path uses a small dependency-free release binary while preserving the existing optimized Home Assistant relay intervals and control-loop cadence.\n\n#### Upgrade notes\n\n- The App-only 3.0.0 update does not require a Home Assistant or Raspberry Pi host restart. A separately managed HACS integration follows its own release/restart requirements.\n- Real-device Gate 2 passed on Raspberry Pi 5 with Home Assistant Core 2026.10.4 / HA OS 18.4.rc2: preserved 49°C custom1, AI Assist/model data, CPU Mild 2500 MHz, GPU Balanced, Adaptive PWM ownership/control, Card UI synchronization and stable fallback were verified.\n\n### Polski\n\n#### Dodano\n\n- Hybrydowy Rust Core do lekkiej telemetrii hosta Raspberry Pi 5 i kontroli zdrowia runtime, z automatycznym fallbackiem do sprawdzonej warstwy zgodności/sterowania.\n- Zweryfikowany handoff migracji Store z walidacją SHA-256, backupem celu i rollbackiem dla danych AI Cooling, kalibracji wentylatora, profili CPU/GPU, stanu krzywej custom1 i opcji użytkownika.\n\n#### Zmieniono\n\n- Sprawdzona warstwa shell/Python pozostaje nadrzędna dla bezpieczeństwa wentylatora, Adaptive PWM, AI Cooling, profili CPU/GPU oraz aktualizacji/recovery, natomiast Rust obsługuje lekką natywną telemetrię i runtime health.\n- Wersja Card UI jest podstawiana dynamicznie przed synchronizacją Lovelace, dzięki czemu zapisany dashboard pozostaje zgodny z wersją aplikacji.\n\n#### Naprawiono\n\n- Pełny zestaw zaimportowanych opcji aplikacji jest utrwalany w natywnym magazynie opcji Supervisor przed zakończeniem migracji, dzięki czemu stare wartości domyślne celu nie zastępują po restarcie ustawień 49°C / AI Assist.\n- Zakończona migracja namespace jest nadrzędnym potwierdzeniem prawa sterowania dla kanonicznego SBC5, przy zachowaniu jawnego interlocka właściciela podczas niedokończonej migracji.\n- Bezpiecznie odzyskiwane jest osierocone przejęcie thermal zone `mode=disabled` po przebudowie/aktualizacji aplikacji, gdy aktywny jest `custom1`, `max_state >= 100`, `cur_state` jest zapisywalny i migracja namespace ma stan COMPLETE.\n- Ujednolicono wersję Rust, bootstrapu i obrazu podczas budowania, aby kontrole wersji pakietu/runtime korzystały z jednej publicznej wersji wydania.\n\n#### Wydajność\n\n- Natywna ścieżka Rust telemetrii/runtime health korzysta z małego binarium release bez zewnętrznych zależności, zachowując zoptymalizowane interwały relay Home Assistant i częstotliwość pętli sterowania.\n\n#### Informacje o aktualizacji\n\n- Aktualizacja samej aplikacji do 3.0.0 nie wymaga restartu Home Assistant ani hosta Raspberry Pi. Osobno zarządzana integracja HACS ma własne wymagania wersji/restartu.\n- Gate 2 na realnym Raspberry Pi 5 z Home Assistant Core 2026.10.4 / HA OS 18.4.rc2 przeszedł poprawnie: zweryfikowano zachowanie custom1 49°C, AI Assist/modelu, CPU Mild 2500 MHz, GPU Balanced, przejęcie i pracę Adaptive PWM, synchronizację Card UI oraz bezpieczny powrót do stabilnej wersji.\n\n'''
    if '## 3.0.0 ' not in changelog:
        pos = changelog.find('\n') + 1
        changelog = changelog[:pos] + '\n' + entry + changelog[pos:].lstrip('\n')
    write(ROOT/'CHANGELOG.md', changelog)
    write(APP/'CHANGELOG.md', changelog)

    notes = '''# SBC5 Control Center 3.0.0\n\n> Hybrid Rust Core release with verified preserved-state migration and rollback on Raspberry Pi 5 / Home Assistant OS.\n\n## English\n\n- Native Rust core handles lightweight host telemetry and runtime health.\n- Proven compatibility/control plane remains authoritative for fan safety, Adaptive PWM and AI Cooling.\n- Preserved-state Store migration keeps the 49°C custom curve, AI model/counters, fan calibration and CPU/GPU profiles.\n- Adaptive PWM safely recovers orphaned userspace thermal ownership after an App rebuild/update.\n- Card UI version synchronization is dynamic and verified after storage-mode Lovelace updates.\n- Gate 2 passed on Raspberry Pi 5 with Core 2026.10.4 / HA OS 18.4.rc2.\n- App-only update requires no Home Assistant or host restart.\n\n## Polski\n\n- Natywny rdzeń Rust obsługuje lekką telemetrię hosta i runtime health.\n- Sprawdzona warstwa zgodności/sterowania nadal odpowiada za bezpieczeństwo wentylatora, Adaptive PWM i AI Cooling.\n- Migracja Store z zachowaniem stanu utrzymuje krzywą 49°C, model/liczniki AI, kalibrację wentylatora oraz profile CPU/GPU.\n- Adaptive PWM bezpiecznie odzyskuje osierocone przejęcie sterowania termicznego po przebudowie/aktualizacji aplikacji.\n- Wersja Card UI jest synchronizowana dynamicznie i weryfikowana po zapisie Lovelace w trybie storage.\n- Gate 2 przeszedł na Raspberry Pi 5 z Core 2026.10.4 / HA OS 18.4.rc2.\n- Aktualizacja samej aplikacji nie wymaga restartu Home Assistant ani hosta.\n'''
    write(ROOT/'RELEASE_NOTES_3.0.0.md', notes)


def main() -> int:
    restore_public_surfaces()
    normalize_runtime()
    write_metadata()
    write_changelog_and_notes()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
