# SBC5 Control Center — Current Information / Informacje

**English** · [Polski](#polski)

## English

SBC5 Control Center is a local Raspberry Pi 5 control, cooling, diagnostics and optimization platform for Home Assistant OS.

| Parameter | Value |
|---|---|
| App version | **2.8.25** |
| Card UI | **2.8.25** |
| Status | **stable** |
| Architecture | `aarch64` |
| Home Assistant OS | `>= 18.3` |
| Home Assistant Core | `>= 2026.10.1` |
| License | Apache-2.0 |

### Components and dependency

- **Main App/runtime:** [krlmdfk/sbc5-control-center](https://github.com/krlmdfk/sbc5-control-center)
- **HACS integration:** [krlmdfk/sbc5-control-center-integration](https://github.com/krlmdfk/sbc5-control-center-integration)

The HACS integration is a companion component and **requires the SBC5 Control Center App/runtime to be installed and running**. The App provides Raspberry Pi 5 host telemetry and control services; the integration exposes them through Home Assistant entities and the device registry.

### Runtime model

- CPU temperature, RPM and PWM: lightweight **5 s** path;
- Adaptive PWM and AI evaluator: **10 s** cycle;
- native bridge full telemetry: **15 s**;
- compact AI transport: evaluated every **15 s**, published on change with stable-state keepalive;
- compatibility host relay: **30 s**;
- system diagnostics: **60 s**;
- static hardware and firmware identity: **300 s**;
- Supervisor profile reconciliation: **30 s**.

Fast cooling-control paths remain independent from heavier diagnostics. Transport entities are excluded from Recorder while history-relevant values use dedicated numeric entities.

### Core capabilities

SBC5 Control Center provides Active Cooler control, Adaptive PWM, local AI Cooling, CPU/OC and GPU/V3D/ISP profiles, managed `config.txt`, Raspberry Pi 5 hardware telemetry, Restart Manager, firmware/device identification and verified local updates.

Real boot-configuration changes request a Raspberry Pi restart. Version/comment-only changes are compared semantically and do not request a host reboot.

### User interface

The Lovelace card is mobile-first. Large sections are collapsed by default and expanded through the **SBC5 Control Center**, **AI Cooling** and **CPU Clock** tiles. CPU/OC is positioned below the CPU/PWM temperature chart and above GPU/V3D/ISP.

---

<a id="polski"></a>

## Polski

SBC5 Control Center jest lokalną platformą sterowania, chłodzenia, diagnostyki i optymalizacji Raspberry Pi 5 dla Home Assistant OS.

| Parametr | Wartość |
|---|---|
| Wersja aplikacji | **2.8.25** |
| Card UI | **2.8.25** |
| Stan | **stable** |
| Architektura | `aarch64` |
| Home Assistant OS | `>= 18.3` |
| Home Assistant Core | `>= 2026.10.1` |
| Licencja | Apache-2.0 |

### Składniki i zależność

- **Główna aplikacja/runtime:** [krlmdfk/sbc5-control-center](https://github.com/krlmdfk/sbc5-control-center)
- **Integracja HACS:** [krlmdfk/sbc5-control-center-integration](https://github.com/krlmdfk/sbc5-control-center-integration)

Integracja HACS jest komponentem towarzyszącym i **wymaga zainstalowanej oraz uruchomionej aplikacji/runtime SBC5 Control Center**. Aplikacja dostarcza telemetrię hosta Raspberry Pi 5 i usługi sterujące, a integracja udostępnia je jako encje i urządzenie w Home Assistant.

### Aktualny model pracy

- temperatura CPU, RPM i PWM: lekka ścieżka co **5 s**;
- Adaptive PWM i evaluator AI: cykl **10 s**;
- pełna telemetria native bridge: **15 s**;
- kompaktowy transport AI: ocena co **15 s**, publikacja po zmianie i keepalive przy stabilnym stanie;
- relay zgodności hosta: **30 s**;
- diagnostyka systemowa: **60 s**;
- statyczna identyfikacja sprzętu i firmware: **300 s**;
- synchronizacja profili Supervisor: **30 s**.

Szybkie ścieżki sterowania chłodzeniem pozostają niezależne od cięższej diagnostyki. Encje transportowe są wyłączone z Recorder, a wartości przeznaczone do historii mają osobne encje liczbowe.

### Główne możliwości

SBC5 Control Center obsługuje Active Cooler, Adaptive PWM, lokalne AI Cooling, profile CPU/OC i GPU/V3D/ISP, zarządzany `config.txt`, telemetrię Raspberry Pi 5, Restart Manager, identyfikację urządzenia/firmware oraz weryfikowane aktualizacje lokalne.

Rzeczywiste zmiany konfiguracji boot wymagają restartu Raspberry Pi. Zmiany dotyczące wyłącznie wersji/komentarza są porównywane semantycznie i nie generują restartu hosta.

### Interfejs użytkownika

Karta Lovelace jest zoptymalizowana pod telefon. Rozbudowane sekcje są domyślnie zwinięte i rozwijane przez kafelki **SBC5 Control Center**, **AI Cooling** i **Zegar CPU**. Sekcja CPU/OC znajduje się pod wykresem temperatury CPU/PWM i nad GPU/V3D/ISP.
