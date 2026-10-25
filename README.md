[![Validate build](https://github.com/krlmdfk/sbc5-control-center/actions/workflows/validate.yml/badge.svg)](https://github.com/krlmdfk/sbc5-control-center/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/krlmdfk/sbc5-control-center?display_name=tag)](https://github.com/krlmdfk/sbc5-control-center/releases)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

# SBC5 Control Center

> **Lokalne centrum sterowania, diagnostyki i optymalizacji Raspberry Pi 5 dla Home Assistant OS.**

**Stable · v2.8.25 · Card UI 2.8.25 · aarch64 · HA OS ≥ 18.3 · Core ≥ 2026.10.1 · Apache-2.0**

SBC5 Control Center łączy Active Cooler, Adaptive PWM, lokalne AI Cooling, telemetrię Raspberry Pi 5, profile CPU/OC i GPU/V3D/ISP, zarządzanie `config.txt`, Restart Manager oraz bezpieczne lokalne aktualizacje.


## Repozytoria projektu

- **Pełny projekt:** `krlmdfk/sbc5-control-center` — aplikacja, runtime, integracja, karty, package, dokumentacja i narzędzia aktualizacji.
- **Dystrybucja HACS:** `krlmdfk/sbc5-control-center-integration` — wydzielona integracja Home Assistant przeznaczona do instalacji przez HACS.

> Repozytorium główne jest źródłem kompletnego projektu. Repo HACS zawiera wyłącznie część `custom_components/sbc5_control_center`, aby zachować poprawny model dystrybucji HACS.

## Najważniejsze możliwości

| Obszar | Zakres |
|---|---|
| **Cooling** | Active Cooler, `custom1`, Automatic / Hybrid / Manual, kalibracja PWM→RPM |
| **Adaptive PWM** | baza `custom1(T)`, bounded trim, deadband, anti-windup, Sign Guard, slew limiter |
| **AI Cooling** | lokalny Learning/Assist, buckety obciążenia, kwalifikacja próbek, historia predykcji |
| **CPU / OC** | profile Factory → Experimental + Advanced, Boot Verification, taktowanie CPU0–CPU3 |
| **GPU / V3D / ISP** | profile Factory / Eco / Balanced / Performance / Experimental / Advanced |
| **System** | zasilanie, PMIC, pamięć, storage, throttling, sieć, firmware, bootloader |
| **`config.txt`** | zarządzane bloki, backup, walidacja, rollback, semantyczne wykrywanie zmian |
| **Updates** | lokalne ZIP, manifest, SHA-256, Health Check, Restart Manager |

## Mobile-first Lovelace

Karta jest zaprojektowana tak, aby na telefonie pokazywać najpierw stan, a szczegóły dopiero na żądanie:

- **SBC5 Control Center** rozwija opcje aktualizacji;
- **AI Cooling** rozwija diagnostykę uczenia i siatki;
- **Zegar CPU** rozwija cztery rdzenie;
- profile CPU i GPU mają własne, niezależne rozwijane sterowanie.

Układ części wydajnościowej: **wykres temperatury CPU/PWM → CPU / Overclocking → GPU/V3D/ISP**.

## Architektura

```text
Home Assistant OS
├── SBC5 Control Center App
│   ├── cooling / AI / profiles / config.txt
│   ├── update + restart manager
│   └── host telemetry
├── native integration: sbc5_control_center
├── Home Assistant package
└── Lovelace cards
```

## Quick start

1. Zainstaluj i uruchom aplikację.
2. Sprawdź `Platform Guard` i `Host Access`.
3. Uruchom kalibrację Active Coolera przed agresywnym obniżaniem PWM.
4. Dodaj/synchronizuj główną kartę Lovelace.
5. Zmieniaj profile CPU/GPU etapami i restartuj host tylko wtedy, gdy Restart Manager zgłosi realną zmianę boot.

Pełna ścieżka: [`docs/QUICK_SETUP.md`](docs/QUICK_SETUP.md).

## Dokumentacja

- [Informacje o aktualnym stanie](INFO.md)
- [Pełna dokumentacja](DOCUMENTATION.md)
- [Quick Setup](docs/QUICK_SETUP.md)
- [Changelog](CHANGELOG.md)
- [Reference `config.txt`](docs/CONFIG_TXT_REFERENCE.md)
- [Aktualizacje lokalne](docs/LOCAL_ZIP_UPDATE.md)

## Zgodność i bezpieczeństwo

SBC5 jest przeznaczony dla Raspberry Pi 5 z Home Assistant OS. Aplikacja ma rozszerzony dostęp do hosta, ponieważ zarządza chłodzeniem i opcjonalnie konfiguracją boot. Overclocking i zmiany Device Tree mogą wpływać na stabilność — zawsze weryfikuj temperatury, zasilanie i stan throttlingu.

SBC5 Control Center jest niezależnym projektem. Raspberry Pi i Home Assistant są nazwami/znakami odpowiednich właścicieli; projekt nie jest przez nich sponsorowany ani zatwierdzony. Zobacz `LICENSE`, `NOTICE`, `TRADEMARKS.md` i `THIRD_PARTY_NOTICES.md`.
