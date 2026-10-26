<p align="center">
  <a href="https://github.com/krlmdfk/sbc5-control-center">
    <img src="branding/icon-256.png" alt="SBC5 Control Center" width="128">
  </a>
</p>

# SBC5 Control Center — Information / Informacje

| Parameter / Parametr | Value / Wartość |
|---|---|
| App version / Wersja aplikacji | **2.8.28** |
| Card UI | **2.8.28** |
| Status / Stan | **stable** |
| Architecture / Architektura | `aarch64` |
| Home Assistant OS | `>= 18.3` |
| Home Assistant Core | `>= 2026.10.1` |
| License / Licencja | Apache-2.0 |

**[Main App / Główna aplikacja](https://github.com/krlmdfk/sbc5-control-center)** · **[HACS Integration / Integracja HACS](https://github.com/krlmdfk/sbc5-control-center-integration)** · **[First Installation / Pierwsza instalacja](docs/FIRST_INSTALL.md)**

---

## English

### Purpose

For a new installation, the canonical step-by-step entry point is **[`docs/FIRST_INSTALL.md`](docs/FIRST_INSTALL.md)**.

SBC5 Control Center combines Active Cooler control, Adaptive PWM, local AI Cooling, CPU/OC and GPU/V3D/ISP profiles, managed `config.txt`, hardware telemetry, Restart Manager and local updates in one runtime running locally on Raspberry Pi 5 with Home Assistant OS.

### Current operating model

- CPU temperature, RPM and PWM: lightweight path every **5 s**;
- Adaptive PWM and AI evaluator: **10 s** cycle;
- full native bridge telemetry: **15 s**;
- compact AI transport: evaluation every **15 s**, publish on change plus stable-state keepalive;
- host compatibility relay: **30 s**;
- system diagnostics: **60 s**;
- static hardware and firmware identity: **300 s**;
- Supervisor profile synchronization: **30 s**.

Fast cooling-control paths remain independent from heavier diagnostics. Host/AI transport entities are excluded from Recorder, while values intended for history use dedicated numeric entities.

### Cooling

Active Cooler supports the factory profile and configurable `custom1`. Adaptive PWM uses `custom1(T)` as the absolute base and applies bounded trim, deadband, anti-windup, Sign Guard and rate limiting. Emergency 100% output remains immediate.

AI Cooling runs locally and is secondary to the classical controller. The model distinguishes `idle`, `low`, `medium` and `high` workload buckets, qualifies samples and can operate in a limited Assist mode.

### CPU, GPU and `config.txt`

CPU/OC and GPU/V3D/ISP profiles maintain persistent desired state synchronized between Ingress, Lovelace, `config.txt` and native Home Assistant configuration. A real boot-parameter change requests a full Raspberry Pi restart. Managed files are compared semantically, so changing only an App version/comment must not trigger a host restart.

### Lovelace interface

The complete Lovelace interface requires **Mushroom**, **card-mod**, and **ApexCharts Card** installed through HACS. The native SBC5 integration can expose its entities without these frontend cards.

The main card is mobile-first. Dense sections are collapsed by default and expanded from tiles: **SBC5 Control Center**, **AI Cooling**, **CPU Clock**, **CPU / Overclocking**, and **GPU / V3D / ISP**. Performance order is CPU/PWM chart → CPU / Overclocking → GPU/V3D/ISP.

### Device identity

Home Assistant's device registry receives Raspberry Pi model, board revision, hardware version, serial number, MAC address and SBC5 version. Diagnostic entities also expose operating system, kernel, architecture, Raspberry Pi firmware and EEPROM bootloader information.

### Updates and Restart Manager

Local ZIP packages are verified against a manifest and SHA-256. A full update may require a Home Assistant restart, while a complete Raspberry Pi restart is requested only when the effective boot configuration actually changed.

### Companion HACS integration

Native Home Assistant entities are distributed through the companion repository:

**[SBC5 Control Center — HACS Integration](https://github.com/krlmdfk/sbc5-control-center-integration)**

The HACS integration requires this App/runtime to be installed and running.

---

## Polski

### Przeznaczenie

Dla nowej instalacji kanonicznym przewodnikiem krok po kroku jest **[`docs/FIRST_INSTALL.md`](docs/FIRST_INSTALL.md)**.

SBC5 Control Center łączy obsługę Active Coolera, Adaptive PWM, lokalne AI Cooling, profile CPU/OC i GPU/V3D/ISP, zarządzanie `config.txt`, telemetrię sprzętową, Restart Manager oraz lokalne aktualizacje w jednym runtime działającym lokalnie na Raspberry Pi 5 z Home Assistant OS.

### Aktualny model pracy

- temperatura CPU, RPM i PWM: lekka ścieżka co **5 s**;
- Adaptive PWM i evaluator AI: cykl **10 s**;
- pełna telemetria natywnego bridge: **15 s**;
- kompaktowy transport AI: ocena co **15 s**, publikacja po zmianie i keepalive przy stanie stabilnym;
- duży relay zgodności hosta: **30 s**;
- diagnostyka systemowa: **60 s**;
- statyczna identyfikacja sprzętu i firmware: **300 s**;
- synchronizacja profili Supervisor: **30 s**.

Szybkie ścieżki sterowania chłodzeniem pozostają niezależne od cięższej diagnostyki. Encje transportowe host/AI są wyłączone z Recorder, a dane przeznaczone do historii mają osobne encje liczbowe.

### Chłodzenie

Active Cooler obsługuje profil fabryczny oraz konfigurowalny `custom1`. Adaptive PWM używa krzywej `custom1(T)` jako bezwzględnej bazy i stosuje ograniczony trim, deadband, anti-windup, Sign Guard oraz limiter szybkości zmian. Awaryjne sterowanie 100% pozostaje natychmiastowe.

AI Cooling działa lokalnie i wtórnie wobec klasycznego regulatora. Model rozróżnia buckety `idle`, `low`, `medium` i `high`, kwalifikuje próbki jakościowe oraz może pracować w ograniczonym trybie Assist.

### CPU, GPU i `config.txt`

Profile CPU/OC oraz GPU/V3D/ISP mają trwały stan żądany synchronizowany między Ingress, kartą Lovelace, `config.txt` i natywną Konfiguracją Home Assistanta. Rzeczywista zmiana parametrów boot powoduje żądanie pełnego restartu Raspberry Pi. Pliki zarządzane są porównywane semantycznie, więc sama zmiana wersji aplikacji lub komentarza nie powoduje restartu hosta.

### Interfejs Lovelace

Kompletny interfejs Lovelace wymaga zainstalowania przez HACS **Mushroom**, **card-mod** i **ApexCharts Card**. Natywna integracja SBC5 może udostępniać swoje encje bez tych kart frontendowych.

Główna karta jest zoptymalizowana pod telefon. Sekcje o dużej liczbie szczegółów są domyślnie zwinięte i rozwijane przez kafelki: **SBC5 Control Center**, **AI Cooling**, **Zegar CPU**, **CPU / Overclocking** i **GPU / V3D / ISP**. Kolejność części wydajnościowych: wykres CPU/PWM → CPU / Overclocking → GPU/V3D/ISP.

### Identyfikacja urządzenia

Rejestr urządzeń Home Assistant otrzymuje model Raspberry Pi, rewizję płyty, wersję sprzętu, numer seryjny, MAC oraz wersję SBC5. Encje diagnostyczne udostępniają również system operacyjny, kernel, architekturę, firmware Raspberry Pi i bootloader EEPROM.

### Aktualizacje i Restart Manager

Lokalne paczki ZIP są sprawdzane przez manifest i SHA-256. Aktualizacja pełna może wymagać restartu Home Assistant, natomiast pełny restart Raspberry Pi jest zgłaszany wyłącznie wtedy, gdy wynikowa konfiguracja boot faktycznie się zmieniła.

### Towarzysząca integracja HACS

Natywne encje Home Assistant są dystrybuowane przez repozytorium:

**[SBC5 Control Center — Integracja HACS](https://github.com/krlmdfk/sbc5-control-center-integration)**

Integracja HACS wymaga zainstalowanej i uruchomionej tej aplikacji/runtime.
