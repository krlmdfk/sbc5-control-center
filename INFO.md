<p align="center">
  <a href="https://github.com/krlmdfk/sbc5-control-center">
    <img src="branding/icon-256.png" alt="SBC5 Control Center" width="128">
  </a>
</p>


> Update delivery: Home Assistant Apps uses the repository `config.yaml` version; HACS uses published GitHub Releases. Both repositories publish releases automatically after green CI.
# SBC5 Control Center — Information / Informacje

| Parameter / Parametr | Value / Wartość |
|---|---|
| App version / Wersja aplikacji | **3.1.26** |
| Card UI | **3.1.26** |
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

### Installation and distribution model

- The **App/runtime** is installed from Home Assistant **Apps** after adding `https://github.com/krlmdfk/sbc5-control-center` under **Settings → Apps → Install app → ⋮ → Repositories**.
- The native **Home Assistant integration** is distributed separately through HACS from `https://github.com/krlmdfk/sbc5-control-center-integration`.
- The complete Lovelace dashboard additionally requires Mushroom, card-mod and ApexCharts Card through HACS.

The two repositories are intentionally separate: Apps owns the host runtime, while HACS owns `custom_components/sbc5_control_center`.

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

AI Cooling runs locally and is secondary to the classical controller. The model distinguishes `idle`, `low`, `medium` and `high` workload buckets. Qualified learning uses bucket-local stability windows: `idle/low` keep strict steady-state gates, while `medium/high` use workload-aware thermal/PWM limits. Assist remains bounded and the learned model is persistent.

AI Thermal Predictor v2 forecasts CPU temperature 30/60/120 seconds ahead and scores itself using per-horizon MAE, signed online bias, confidence and validated-sample maturity. Shadow Assist converts that forecast into a bounded hypothetical PWM delta while remaining telemetry-only (`control_output_enabled=false`); Adaptive PWM and AI Cooling remain authoritative. Predictor v1 quality statistics are archived when v2 starts so old errors do not contaminate the new model, while the AI Cooling model and counters are preserved.

### CPU, GPU and `config.txt`

CPU/OC and GPU/V3D/ISP profiles maintain persistent desired state synchronized between Ingress, Lovelace, `config.txt` and native Home Assistant configuration. A real boot-parameter change requests a full Raspberry Pi restart. Managed files are compared semantically, so changing only an App version/comment must not trigger a host restart.

Host-level boot, PMIC and firmware access requires the App to run with **Protection Mode disabled**, matching its declared `host_pid`, `full_access`, `SYS_ADMIN` and `SYS_PTRACE` permissions. If Host Access is unavailable, SBC5 keeps cooling telemetry/control on safe available paths, suspends boot/config writes, throttles repeated warnings and reports the Supervisor protection/Host PID state explicitly. Runtime scratch files are created in a guaranteed writable temporary directory.

### Lovelace interface

The complete Lovelace interface requires **Mushroom**, **card-mod**, and **ApexCharts Card** installed through HACS. The native SBC5 integration can expose its entities without these frontend cards.

The main card is mobile-first. Dense sections are collapsed by default and expanded from tiles: **SBC5 Control Center**, **AI Cooling**, **CPU Clock**, **CPU / Overclocking**, and **GPU / V3D / ISP**. Performance order is CPU/PWM chart → CPU / Overclocking → GPU/V3D/ISP.

### Device identity

Home Assistant's device registry receives Raspberry Pi model, board revision, hardware version, serial number, MAC address and SBC5 version. Diagnostic entities also expose operating system, kernel, architecture, Raspberry Pi firmware and EEPROM bootloader information.

### Updates and Restart Manager

Local ZIP packages are verified against a manifest and SHA-256. A full update may require a Home Assistant restart, while a complete Raspberry Pi restart is requested only when the effective boot configuration actually changed.

SBC5 supports a hybrid update model. Store-managed installations use Home Assistant Apps as the canonical full-runtime channel; verified local ZIP packages can still apply UI-only updates directly and can trigger a full Store update when the exact same version is published in Apps. Historical local installations keep direct full-ZIP updates. The Local → Store Migration Manager transfers only allow-listed durable state through a SHA-256-protected handoff and creates rollback data before import. During first Store startup a finalization guard keeps imported CPU/GPU profile state authoritative until native Supervisor options are synchronized, so stale Factory/off defaults cannot overwrite the migrated request.

### Companion HACS integration

Native Home Assistant entities are distributed through the companion repository:

**[SBC5 Control Center — HACS Integration](https://github.com/krlmdfk/sbc5-control-center-integration)**

The HACS integration requires this App/runtime to be installed and running.

---

## Polski

### Przeznaczenie

Dla nowej instalacji kanonicznym przewodnikiem krok po kroku jest **[`docs/FIRST_INSTALL.md`](docs/FIRST_INSTALL.md)**.

### Model instalacji i dystrybucji

- **App/runtime** instaluje się ze sklepu **Apps** Home Assistant po dodaniu `https://github.com/krlmdfk/sbc5-control-center` w **Ustawienia → Apps → Install app / Zainstaluj aplikację → ⋮ → Repositories / Repozytoria**.
- Natywna **integracja Home Assistant** jest dystrybuowana osobno przez HACS z `https://github.com/krlmdfk/sbc5-control-center-integration`.
- Kompletny dashboard Lovelace wymaga dodatkowo Mushroom, card-mod i ApexCharts Card przez HACS.

Rozdzielenie repozytoriów jest celowe: Apps zarządza runtime hosta, a HACS zarządza `custom_components/sbc5_control_center`.

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

AI Cooling działa lokalnie i wtórnie wobec klasycznego regulatora. Model rozróżnia buckety `idle`, `low`, `medium` i `high`. Uczenie jakościowe korzysta z okien stabilności bieżącego bucketa: `idle/low` zachowują ścisłe kryteria, a `medium/high` używają limitów temperatury/PWM dopasowanych do obciążenia. Assist pozostaje ograniczony, a wyuczony model jest trwały.

AI Thermal Predictor v2 prognozuje temperaturę CPU z wyprzedzeniem 30/60/120 sekund i ocenia się przez MAE dla horyzontów, znakowaną korektę błędu online, confidence oraz dojrzałość zweryfikowanych próbek. Shadow Assist zamienia prognozę na ograniczoną hipotetyczną korektę PWM, ale pozostaje wyłącznie telemetryczny (`control_output_enabled=false`); Adaptive PWM i AI Cooling pozostają nadrzędne. Przy starcie v2 statystyki jakości Predictora v1 są archiwizowane, aby stare błędy nie zafałszowały nowego modelu, natomiast model i liczniki AI Cooling są zachowane.

### CPU, GPU i `config.txt`

Profile CPU/OC oraz GPU/V3D/ISP mają trwały stan żądany synchronizowany między Ingress, kartą Lovelace, `config.txt` i natywną Konfiguracją Home Assistanta. Rzeczywista zmiana parametrów boot powoduje żądanie pełnego restartu Raspberry Pi. Pliki zarządzane są porównywane semantycznie, więc sama zmiana wersji aplikacji lub komentarza nie powoduje restartu hosta.

Dostęp do konfiguracji boot, PMIC i firmware hosta wymaga uruchomienia aplikacji z **wyłączonym Protection Mode**, zgodnie z deklarowanymi uprawnieniami `host_pid`, `full_access`, `SYS_ADMIN` i `SYS_PTRACE`. Gdy Host Access jest niedostępny, SBC5 zachowuje bezpieczne dostępne ścieżki chłodzenia/telemetrii, wstrzymuje zapisy konfiguracji boot, ogranicza powtarzane komunikaty i jawnie raportuje stan Protection/Host PID z Supervisora. Pliki tymczasowe runtime są tworzone w gwarantowanym zapisywalnym katalogu roboczym.

### Interfejs Lovelace

Kompletny interfejs Lovelace wymaga zainstalowania przez HACS **Mushroom**, **card-mod** i **ApexCharts Card**. Natywna integracja SBC5 może udostępniać swoje encje bez tych kart frontendowych.

Główna karta jest zoptymalizowana pod telefon. Sekcje o dużej liczbie szczegółów są domyślnie zwinięte i rozwijane przez kafelki: **SBC5 Control Center**, **AI Cooling**, **Zegar CPU**, **CPU / Overclocking** i **GPU / V3D / ISP**. Kolejność części wydajnościowych: wykres CPU/PWM → CPU / Overclocking → GPU/V3D/ISP.

### Identyfikacja urządzenia

Rejestr urządzeń Home Assistant otrzymuje model Raspberry Pi, rewizję płyty, wersję sprzętu, numer seryjny, MAC oraz wersję SBC5. Encje diagnostyczne udostępniają również system operacyjny, kernel, architekturę, firmware Raspberry Pi i bootloader EEPROM.

### Aktualizacje i Restart Manager

Lokalne paczki ZIP są sprawdzane przez manifest i SHA-256. Aktualizacja pełna może wymagać restartu Home Assistant, natomiast pełny restart Raspberry Pi jest zgłaszany wyłącznie wtedy, gdy wynikowa konfiguracja boot faktycznie się zmieniła.

SBC5 obsługuje hybrydowy model aktualizacji. Instalacja sklepowa traktuje Home Assistant Apps jako kanoniczny kanał pełnego runtime; zweryfikowane lokalne ZIP-y nadal mogą bezpośrednio aktualizować UI-only i mogą wyzwolić pełną aktualizację sklepową, gdy identyczna wersja jest opublikowana w Apps. Historyczna instalacja lokalna zachowuje bezpośrednie pełne aktualizacje ZIP. Migration Manager Local → Store przenosi wyłącznie jawnie dozwolony trwały stan przez handoff zabezpieczony SHA-256 i przed importem tworzy dane rollback. Przy pierwszym starcie wersji sklepowej guard finalizacji utrzymuje zaimportowany stan profili CPU/GPU jako nadrzędny do czasu synchronizacji natywnych opcji Supervisor, więc stare wartości Factory/off nie mogą nadpisać migracji.

### Towarzysząca integracja HACS

Natywne encje Home Assistant są dystrybuowane przez repozytorium:

**[SBC5 Control Center — Integracja HACS](https://github.com/krlmdfk/sbc5-control-center-integration)**

Integracja HACS wymaga zainstalowanej i uruchomionej tej aplikacji/runtime.
