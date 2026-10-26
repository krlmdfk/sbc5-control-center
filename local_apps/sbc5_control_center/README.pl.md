# SBC5 Control Center

> **Lokalne centrum sterowania, diagnostyki i optymalizacji Raspberry Pi 5 dla Home Assistant OS.**

**Stable · v2.8.31 · Card UI 2.8.31 · aarch64 · HA OS ≥ 18.3 · Core ≥ 2026.10.1 · Apache-2.0**

SBC5 Control Center łączy Active Cooler, Adaptive PWM, lokalne AI Cooling, telemetrię Raspberry Pi 5, profile CPU/OC i GPU/V3D/ISP, zarządzanie `config.txt`, Restart Manager oraz bezpieczne lokalne aktualizacje.

## Instalacja ze sklepu Apps Home Assistant

1. Otwórz **Ustawienia → Apps → Install app / Zainstaluj aplikację → ⋮ → Repositories / Repozytoria**.
2. Dodaj `https://github.com/krlmdfk/sbc5-control-center`.
3. Odśwież sklep, zainstaluj **SBC5 Control Center**, włącz **Start on boot / Uruchamiaj przy starcie** i uruchom aplikację.
4. Integrację towarzyszącą zainstaluj osobno przez HACS z `https://github.com/krlmdfk/sbc5-control-center-integration`.


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


## Hybrid update channel / Hybrydowy kanał aktualizacji

Store-managed SBC5 uses Home Assistant Apps as the canonical full-runtime update channel. Verified local ZIPs remain supported for UI-only updates and, for a Store installation, may trigger the native Apps update when the exact same version is published. Historical local installations retain direct full-ZIP rebuilds. The 2.8.31 Migration Manager provides a SHA-256-protected Local → Store handoff with rollback.

Instalacja sklepowa SBC5 używa Home Assistant Apps jako kanonicznego kanału pełnych aktualizacji runtime. Zweryfikowane lokalne ZIP-y pozostają obsługiwane dla UI-only, a w instalacji sklepowej mogą wyzwolić natywną aktualizację Apps, gdy identyczna wersja jest opublikowana. Historyczna instalacja lokalna zachowuje bezpośrednie pełne przebudowy ZIP. Migration Manager 2.8.31 zapewnia handoff Local → Store zabezpieczony SHA-256 i rollback.
