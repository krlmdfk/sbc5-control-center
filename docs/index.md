---
layout: default
title: SBC5 Control Center — Raspberry Pi 5 Cooling, Monitoring & Control for Home Assistant
---

<p align="center">
  <img src="../branding/logo-512.png" alt="SBC5 Control Center" width="180">
</p>

# SBC5 Control Center

**Raspberry Pi 5 fan control, AI-assisted cooling, system monitoring, CPU/GPU profiles, overclocking and diagnostics for Home Assistant OS.**

**Sterowanie wentylatorem Raspberry Pi 5, chłodzenie wspomagane AI, monitoring systemu, profile CPU/GPU, overclocking i diagnostyka dla Home Assistant OS.**

[Main repository](https://github.com/krlmdfk/sbc5-control-center) · [HACS integration](https://github.com/krlmdfk/sbc5-control-center-integration) · [Releases](https://github.com/krlmdfk/sbc5-control-center/releases) · [Issues](https://github.com/krlmdfk/sbc5-control-center/issues)

---

**English** · [Polski](#polski)

## English

### What is SBC5 Control Center?

SBC5 Control Center is a Raspberry Pi 5 management platform built for Home Assistant OS. It combines hardware telemetry, Active Cooler control, Adaptive PWM, local AI Cooling, performance profiles, `config.txt` management, diagnostics and update/recovery workflows in one project.

It is designed for users who want **more than a temperature sensor**: the App/runtime manages the host-facing logic while the companion HACS integration exposes SBC5 state as native Home Assistant entities.

### Core capabilities

| Area | What SBC5 provides |
|---|---|
| **Cooling** | Active Cooler control, PWM, RPM telemetry, fan calibration and custom fan curves |
| **Adaptive PWM** | Target-temperature control with deadband, bounded trim, anti-windup and slew limiting |
| **AI Cooling** | Local Learning/Assist model, workload buckets, confidence and prediction history |
| **CPU / OC** | CPU0–CPU3 telemetry, frequency/load monitoring and managed CPU/overclocking profiles |
| **GPU / V3D / ISP** | Monitoring and managed Factory/Eco/Balanced/Performance/Advanced profiles |
| **System diagnostics** | PMIC, power, memory, storage, throttling, network, firmware and bootloader state |
| **Boot configuration** | Managed `config.txt` blocks with backup, validation, rollback and restart awareness |
| **Home Assistant** | Native integration, device entities, Lovelace dashboard and diagnostics |
| **Updates & recovery** | Verified ZIP updates, SHA-256 validation, Restart Manager and recovery mechanisms |

### Architecture

```text
Raspberry Pi 5 + Home Assistant OS
│
├── SBC5 Control Center App/runtime
│   ├── host telemetry
│   ├── cooling + Adaptive PWM + AI Cooling
│   ├── CPU/GPU profiles
│   ├── config.txt / restart / recovery
│   └── update services
│
├── SBC5 Control Center Integration (HACS)
│   ├── native Home Assistant device
│   ├── sensors / binary sensors
│   ├── diagnostics / repairs
│   └── update & restart entities
│
└── Lovelace dashboard
    ├── Mushroom
    ├── card-mod
    └── ApexCharts Card
```

### Start here

1. [First installation](FIRST_INSTALL.md)
2. [Quick Setup](QUICK_SETUP.md)
3. [Full project documentation](../DOCUMENTATION.md)
4. [Fan control & Active Cooler](fan-control.md)
5. [AI Cooling & Adaptive PWM](ai-cooling.md)
6. [Monitoring & diagnostics](monitoring.md)
7. [CPU/GPU profiles & overclocking](overclocking.md)

### Release quality

SBC5 uses a defined release process with:

- semantic versioning;
- bilingual English/Polish release notes;
- categorized changelog entries;
- repository/runtime validation before publication;
- strict update-manifest hash checks for new releases;
- SHA-256 verified local-update ZIP packages;
- immutable published GitHub Releases.

See the [Release Standard](RELEASE_STANDARD.md).

### Compatibility

- Raspberry Pi 5
- Home Assistant OS
- aarch64
- Home Assistant Core and OS minimum versions are documented per release

### Project repositories

| Repository | Purpose |
|---|---|
| [sbc5-control-center](https://github.com/krlmdfk/sbc5-control-center) | Main App/runtime, integration source, dashboard, documentation and release tooling |
| [sbc5-control-center-integration](https://github.com/krlmdfk/sbc5-control-center-integration) | HACS-managed native Home Assistant integration |

---

## Polski

### Czym jest SBC5 Control Center?

SBC5 Control Center to platforma zarządzania Raspberry Pi 5 przygotowana dla Home Assistant OS. Łączy telemetrię sprzętową, sterowanie Active Coolerem, Adaptive PWM, lokalne AI Cooling, profile wydajności, zarządzanie `config.txt`, diagnostykę oraz mechanizmy aktualizacji i recovery.

Projekt jest przeznaczony dla użytkowników, którzy potrzebują **więcej niż samego odczytu temperatury**: App/runtime obsługuje logikę wymagającą dostępu do hosta, a integracja HACS wystawia stan SBC5 jako natywne encje Home Assistant.

### Najważniejsze możliwości

| Obszar | Co oferuje SBC5 |
|---|---|
| **Chłodzenie** | Active Cooler, PWM, telemetria RPM, kalibracja wentylatora i własne krzywe |
| **Adaptive PWM** | Regulacja do temperatury zadanej z deadband, bounded trim, anti-windup i slew limiterem |
| **AI Cooling** | Lokalny model Learning/Assist, buckety obciążenia, confidence i historia predykcji |
| **CPU / OC** | Telemetria CPU0–CPU3, częstotliwość/obciążenie i zarządzane profile CPU/overclocking |
| **GPU / V3D / ISP** | Monitoring oraz profile Factory/Eco/Balanced/Performance/Advanced |
| **Diagnostyka systemu** | PMIC, zasilanie, pamięć, storage, throttling, sieć, firmware i bootloader |
| **Konfiguracja boot** | Zarządzane bloki `config.txt`, backup, walidacja, rollback i kontrola restartu |
| **Home Assistant** | Natywna integracja, encje urządzenia, dashboard Lovelace i diagnostyka |
| **Aktualizacje i recovery** | Weryfikowane ZIP-y, SHA-256, Restart Manager i mechanizmy odzyskiwania |

### Architektura

```text
Raspberry Pi 5 + Home Assistant OS
│
├── SBC5 Control Center App/runtime
│   ├── telemetria hosta
│   ├── chłodzenie + Adaptive PWM + AI Cooling
│   ├── profile CPU/GPU
│   ├── config.txt / restart / recovery
│   └── usługi aktualizacji
│
├── SBC5 Control Center Integration (HACS)
│   ├── natywne urządzenie Home Assistant
│   ├── sensory / binary sensors
│   ├── diagnostyka / repairs
│   └── encje aktualizacji i restartu
│
└── Dashboard Lovelace
    ├── Mushroom
    ├── card-mod
    └── ApexCharts Card
```

### Zacznij tutaj

1. [Pierwsza instalacja](FIRST_INSTALL.md)
2. [Quick Setup](QUICK_SETUP.md)
3. [Pełna dokumentacja projektu](../DOCUMENTATION.md)
4. [Sterowanie wentylatorem i Active Cooler](fan-control.md)
5. [AI Cooling i Adaptive PWM](ai-cooling.md)
6. [Monitoring i diagnostyka](monitoring.md)
7. [Profile CPU/GPU i overclocking](overclocking.md)

### Standard wydań

SBC5 korzysta ze zdefiniowanego procesu wydań obejmującego:

- semantic versioning;
- dwujęzyczne notatki EN/PL;
- changelog z kategoriami zmian;
- walidację repozytorium i runtime przed publikacją;
- ścisłą kontrolę hashy manifestu dla nowej wersji;
- paczkę aktualizacji ZIP weryfikowaną SHA-256;
- niezmienność już opublikowanych GitHub Releases.

Zobacz [Release Standard](RELEASE_STANDARD.md).

### Zgodność

- Raspberry Pi 5
- Home Assistant OS
- aarch64
- minimalne wersje Home Assistant Core i OS są podawane dla każdego wydania

### Repozytoria projektu

| Repozytorium | Przeznaczenie |
|---|---|
| [sbc5-control-center](https://github.com/krlmdfk/sbc5-control-center) | Główna aplikacja/runtime, źródło integracji, dashboard, dokumentacja i tooling release |
| [sbc5-control-center-integration](https://github.com/krlmdfk/sbc5-control-center-integration) | Natywna integracja Home Assistant zarządzana przez HACS |

---

SBC5 Control Center is an independent open-source project. Raspberry Pi and Home Assistant are names/trademarks of their respective owners. The project is not sponsored, endorsed or maintained by Raspberry Pi Ltd., Home Assistant or the Open Home Foundation.


## AI Thermal Predictor v2

SBC5 includes a closed-loop-aware Thermal Predictor for +30/+60/+120 second CPU temperature forecasts. Predictor v2 combines trend extrapolation with target anchoring and bounded online bias correction. Its quality gate uses MAE, confidence and validated samples. Shadow Assist is telemetry-only and evaluates a bounded ±2 pp PWM recommendation without changing physical fan output.

The Predictor uses the existing AI runtime cadence; no additional fast polling loop is created.
