[![Validate build](https://github.com/krlmdfk/sbc5-control-center/actions/workflows/validate.yml/badge.svg)](https://github.com/krlmdfk/sbc5-control-center/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/krlmdfk/sbc5-control-center?display_name=tag)](https://github.com/krlmdfk/sbc5-control-center/releases)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

# SBC5 Control Center

**English** · [Polski](#polski)

> Local control, cooling, diagnostics and optimization center for Raspberry Pi 5 running Home Assistant OS.

**Stable · v2.8.25 · aarch64 · Home Assistant OS ≥ 18.3 · Core ≥ 2026.10.1 · Apache-2.0**

## English

### Project overview

SBC5 Control Center combines Raspberry Pi 5 host telemetry, Active Cooler management, Adaptive PWM, local AI Cooling, CPU/OC and GPU/V3D/ISP profiles, managed `config.txt`, Restart Manager and verified local updates in one Home Assistant OS-oriented project.

### Project repositories

| Repository | Purpose |
|---|---|
| **[krlmdfk/sbc5-control-center](https://github.com/krlmdfk/sbc5-control-center)** | **Main project.** App/runtime, cooling and AI logic, CPU/GPU profiles, host telemetry, Lovelace cards, package, documentation, update tooling and source files. |
| **[krlmdfk/sbc5-control-center-integration](https://github.com/krlmdfk/sbc5-control-center-integration)** | **HACS companion integration.** Installs `custom_components/sbc5_control_center` and exposes SBC5 entities, device information, diagnostics and update/restart state to Home Assistant. |

> **Dependency:** the HACS integration is a companion to the SBC5 Control Center App and **requires the SBC5 Control Center App/runtime to be installed and running**. The App provides host telemetry and control services; the integration exposes them natively in Home Assistant.

### Main capabilities

- Active Cooler control with Automatic, Hybrid and Manual modes.
- Adaptive PWM based on the `custom1(T)` curve, bounded trim, deadband, anti-windup, Sign Guard and slew limiting.
- Local AI Cooling with learning/assist modes, workload buckets, sample qualification and prediction history.
- CPU/OC profiles with boot verification and per-core CPU0–CPU3 telemetry.
- GPU/V3D/ISP profiles including Factory, Eco, Balanced, Performance, Experimental and Advanced modes.
- Power, PMIC, storage, memory, network, throttling, firmware and bootloader diagnostics.
- Managed `config.txt` workflow with backup, validation, rollback and semantic restart detection.
- Local ZIP update pipeline with manifest and SHA-256 verification.
- Mobile-first Lovelace cards with collapsible AI, CPU-core and update sections.

### Installation model

The complete project consists of two cooperating layers:

```text
Home Assistant OS
├── SBC5 Control Center App/runtime        ← required
│   ├── cooling / AI / profiles / config.txt
│   ├── update + Restart Manager
│   └── Raspberry Pi 5 host telemetry
└── SBC5 Control Center HACS Integration   ← companion
    └── native Home Assistant entities and device registry
```

For the full project and App releases, use this repository. For the HACS-managed Home Assistant integration, use the companion repository linked above.

### Documentation

- [Current product information](INFO.md)
- [Full documentation](DOCUMENTATION.md)
- [Quick Setup](docs/QUICK_SETUP.md)
- [Changelog](CHANGELOG.md)
- [`config.txt` reference](docs/CONFIG_TXT_REFERENCE.md)
- [Local ZIP updates](docs/LOCAL_ZIP_UPDATE.md)
- [HACS integration](https://github.com/krlmdfk/sbc5-control-center-integration)

### Compatibility and safety

SBC5 Control Center is designed for Raspberry Pi 5 with Home Assistant OS. The App requires extended host access because it manages cooling and can optionally modify boot configuration. Overclocking and Device Tree changes can affect stability; always verify temperatures, power quality and throttling state.

SBC5 Control Center is an independent project and is not endorsed by Raspberry Pi Ltd., Home Assistant, or the Open Home Foundation. See `LICENSE`, `NOTICE`, `TRADEMARKS.md` and `THIRD_PARTY_NOTICES.md`.

---

<a id="polski"></a>

## Polski

> Lokalne centrum sterowania, chłodzenia, diagnostyki i optymalizacji Raspberry Pi 5 dla Home Assistant OS.

**Stable · v2.8.25 · aarch64 · Home Assistant OS ≥ 18.3 · Core ≥ 2026.10.1 · Apache-2.0**

### O projekcie

SBC5 Control Center łączy telemetrię hosta Raspberry Pi 5, obsługę Active Coolera, Adaptive PWM, lokalne AI Cooling, profile CPU/OC i GPU/V3D/ISP, zarządzanie `config.txt`, Restart Manager oraz weryfikowane aktualizacje lokalne w jednym projekcie przeznaczonym dla Home Assistant OS.

### Repozytoria projektu

| Repozytorium | Przeznaczenie |
|---|---|
| **[krlmdfk/sbc5-control-center](https://github.com/krlmdfk/sbc5-control-center)** | **Główny projekt.** Aplikacja/runtime, chłodzenie i AI, profile CPU/GPU, telemetria hosta, karty Lovelace, package, dokumentacja, updater i źródła. |
| **[krlmdfk/sbc5-control-center-integration](https://github.com/krlmdfk/sbc5-control-center-integration)** | **Integracja towarzysząca HACS.** Instaluje `custom_components/sbc5_control_center` i udostępnia encje SBC5, informacje o urządzeniu, diagnostykę oraz stan aktualizacji/restartów w Home Assistant. |

> **Zależność:** integracja HACS jest dodatkiem do SBC5 Control Center i **wymaga zainstalowanej oraz uruchomionej aplikacji/runtime SBC5 Control Center**. Aplikacja dostarcza telemetrię hosta i usługi sterujące, a integracja udostępnia je natywnie w Home Assistant.

### Najważniejsze możliwości

- Sterowanie Active Coolerem w trybach Automatic, Hybrid i Manual.
- Adaptive PWM oparty o krzywą `custom1(T)`, ograniczony trim, deadband, anti-windup, Sign Guard i limiter szybkości zmian.
- Lokalne AI Cooling z trybem Learning/Assist, bucketami obciążenia, kwalifikacją próbek i historią predykcji.
- Profile CPU/OC z Boot Verification oraz telemetrią CPU0–CPU3.
- Profile GPU/V3D/ISP: Factory, Eco, Balanced, Performance, Experimental i Advanced.
- Diagnostyka zasilania, PMIC, pamięci, storage, sieci, throttlingu, firmware i bootloadera.
- Zarządzany `config.txt` z backupem, walidacją, rollbackiem i semantycznym wykrywaniem konieczności restartu.
- Aktualizacje lokalne ZIP z manifestem i weryfikacją SHA-256.
- Mobilne karty Lovelace ze zwijanymi sekcjami AI, rdzeni CPU i aktualizacji.

### Model instalacji

Kompletny projekt składa się z dwóch współpracujących warstw:

```text
Home Assistant OS
├── SBC5 Control Center App/runtime        ← wymagane
│   ├── chłodzenie / AI / profile / config.txt
│   ├── updater + Restart Manager
│   └── telemetria hosta Raspberry Pi 5
└── SBC5 Control Center HACS Integration   ← integracja towarzysząca
    └── natywne encje i Device Registry Home Assistant
```

Pełny projekt i wydania aplikacji znajdują się w tym repozytorium. Integracja zarządzana przez HACS znajduje się w osobnym repozytorium podanym wyżej.

### Dokumentacja

- [Informacje o aktualnym stanie](INFO.md)
- [Pełna dokumentacja](DOCUMENTATION.md)
- [Quick Setup](docs/QUICK_SETUP.md)
- [Changelog](CHANGELOG.md)
- [Reference `config.txt`](docs/CONFIG_TXT_REFERENCE.md)
- [Aktualizacje lokalne](docs/LOCAL_ZIP_UPDATE.md)
- [Integracja HACS](https://github.com/krlmdfk/sbc5-control-center-integration)

### Zgodność i bezpieczeństwo

SBC5 Control Center jest przeznaczony dla Raspberry Pi 5 z Home Assistant OS. Aplikacja wymaga rozszerzonego dostępu do hosta, ponieważ zarządza chłodzeniem i może opcjonalnie modyfikować konfigurację boot. Overclocking i zmiany Device Tree mogą wpływać na stabilność — zawsze kontroluj temperatury, jakość zasilania i stan throttlingu.

SBC5 Control Center jest niezależnym projektem i nie jest sponsorowany ani zatwierdzony przez Raspberry Pi Ltd., Home Assistant ani Open Home Foundation. Zobacz `LICENSE`, `NOTICE`, `TRADEMARKS.md` i `THIRD_PARTY_NOTICES.md`.
