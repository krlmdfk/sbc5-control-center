<p align="center">
  <a href="https://github.com/krlmdfk/sbc5-control-center">
    <img src="branding/icon-256.png" alt="SBC5 Control Center" width="128">
  </a>
</p>

# SBC5 Control Center — Documentation / Dokumentacja

**[Main App / Główna aplikacja](https://github.com/krlmdfk/sbc5-control-center)** · **[HACS Integration / Integracja HACS](https://github.com/krlmdfk/sbc5-control-center-integration)**

> **English:** This document describes the current installation, configuration, operation, diagnostics, and recovery procedures. Release history is maintained exclusively in `CHANGELOG.md`.
>
> **Polski:** Ten dokument opisuje aktualną instalację, konfigurację, obsługę, diagnostykę i odzyskiwanie. Historia wydań znajduje się wyłącznie w `CHANGELOG.md`.

---

## English

### 1. Requirements

#### Core

- Raspberry Pi 5 / `aarch64`;
- Home Assistant OS `>= 18.3`;
- Home Assistant Core `>= 2026.10.1`;
- SBC5 Control Center App with host access;
- native `sbc5_control_center` integration (HACS-managed installation recommended).

#### Complete Lovelace dashboard

Install through HACS:

- **Mushroom** — SBC5 tiles, selectors and controls;
- **card-mod** — card styling and dynamic layout;
- **ApexCharts Card** — CPU temperature/PWM, AI prediction and history charts.

The native SBC5 integration can expose device information, telemetry and control entities without these frontend cards; they are required for the complete dashboard.

### 2. Architecture

SBC5 consists of four layers:

1. **Home Assistant App** — runtime, host access, Ingress, updates, `config.txt`, cooling, and hardware profiles.
2. **Native `sbc5_control_center` integration** — device, sensors, binary sensors, Update entity, services, and Repairs.
3. **Home Assistant Package** — UI helpers, scripts, and safe actions used by Lovelace.
4. **Lovelace** — diagnostics card and update card.

Persistent AI model data, calibration data, profiles, and update markers are stored in the App's `/data` directory.

### 3. Installation and first start

For a **first installation from zero**, use **[`docs/FIRST_INSTALL.md`](docs/FIRST_INSTALL.md)**. It includes the Home Assistant App repository path, App/runtime installation, first-start checks, HACS integration installation, required frontend dependencies and final verification.

For an already prepared SBC5 environment:

1. Install the SBC5 Control Center App.
2. Start it and verify that `Platform Guard` and `Host Access` report a healthy state.
3. Restart Home Assistant if the installer requires the package or integration to be reloaded.
4. Add `dashboard/sbc5_control_center_diagnostics_card.yaml` and, optionally, `dashboard/update_status_card.yaml`.
5. Verify that the **SBC5 Control Center** device is present in the Home Assistant device registry.

A concise first-start procedure is available in `docs/QUICK_SETUP.md`.

### 4. Active Cooler

SBC5 supports the factory profile and the `custom1` profile. For `custom1`, the runtime verifies that the kernel exposes the expected 1% grid (`max_state >= 100`). If the factory profile is active, Adaptive PWM does not take over control and cooling remains managed by the kernel.

#### Control modes

- **Automatic** — the controller selects PWM automatically;
- **Hybrid** — automatic control with a limited user correction;
- **Manual** — control based on the manual configuration.

#### Calibration

PWM→RPM calibration is used to determine the safe minimum fan operating point. It should be repeated after mechanical changes or after replacing the cooler.

### 5. Adaptive PWM

The base is the `custom1(T)` curve. The controller may apply a limited trim, but it does not replace the curve with an unrestricted controller state. Protection mechanisms include deadband, confirmation cycles, anti-windup, Sign Guard, direction limits, and a slew limiter. The emergency 100% path remains immediate.

### 6. AI Cooling

AI runs locally and does not send the model to external services. Learning uses qualified samples assigned to the `idle`, `low`, `medium`, and `high` load buckets. The model can operate in Learning mode or in a limited Assist mode.

On the card, the **AI Cooling** tile expands the complete diagnostics view: bucket maturity, samples, prediction, model coverage, load classification, sample qualification diagnostics, and grid suggestions. The section is collapsed by default.

### 7. CPU / Overclocking

Available presets are Factory, Mild, Balanced, Performance, Experimental, and Advanced. Profiles do not force `over_voltage` manually; voltage remains under firmware/DVFS control unless the user explicitly configures advanced settings otherwise.

Changing a profile writes the boot configuration only when the resulting configuration actually differs from the current managed file. After a real change, a full Raspberry Pi restart is required, followed by saved/runtime verification.

On the card, the CPU/OC section is located **directly below the CPU/PWM temperature chart and above GPU/V3D/ISP**.

#### CPU clock

The **CPU Clock** tile shows a compact status of all four core frequencies. Tapping it expands individual CPU0–CPU3 tiles with frequency and usage. Long-press opens the standard `more-info` dialog.

### 8. GPU / V3D / ISP

GPU profiles include Factory, Eco, Balanced, Performance, Experimental, and Advanced. Frequency changes are boot settings and, after a real write, require a full Raspberry Pi restart. The Factory profile leaves clock management under firmware control.

### 9. `config.txt` management

SBC5 writes its own managed configuration fragments, creates a backup before changes, and should not overwrite user entries outside blocks owned by the App. Comparison is semantic: changing the version number in a header comment is not treated as a boot configuration change.

### 10. Restart Manager

Restart Manager distinguishes between:

- App restart;
- Home Assistant restart;
- full Raspberry Pi host restart.

Priority is monotonic: `host > home_assistant > app`. An App update cannot by itself escalate the required restart to `host` if there is no real boot configuration change.

### 11. Local updates

The canonical directory for local ZIP packages is `/config/sbc5_control_center_updates/`. A package is verified using the manifest and SHA-256, and after installation the Health Check verifies the runtime, bridge, and Home Assistant entities.

The **SBC5 Control Center** tile on the update card expands only after tapping and then shows package status, check action, log, installation controls, and any Restart Manager messages. The section starts collapsed.

### 12. Telemetry and Recorder

Fast control data is separated from heavier diagnostics. Typical cadences are:

| Data | Cadence |
|---|---:|
| Temperature / RPM / PWM | 5 s |
| Adaptive PWM / AI evaluator | 10 s |
| Full bridge telemetry | 15 s |
| Host relay | 30 s |
| System diagnostics | 60 s |
| Hardware/firmware identification | 300 s |

Heavy transport entities are not stored in Recorder. Dedicated measurement entities are provided for AI parameter history.

### 13. Hardware and firmware identification

The SBC5 device publishes the Raspberry Pi model, model ID/revision, HW Rev, serial number, MAC addresses, and software version. Diagnostics expose the operating system, kernel, architecture, Raspberry Pi firmware, and EEPROM bootloader information.

### 14. Diagnostics

If a problem occurs, check the following in order:

1. App status and runtime log;
2. `Platform Guard` and `Host Access`;
3. `SBC5 Cooling Problem`, `Throttling Status`, and power state;
4. `Config Differs From Active` and `Restart Required`;
5. saved and active profile after boot;
6. bridge status and Package/Card UI version.

### 15. Backup and recovery

Before boot changes, SBC5 creates a backup of the managed configuration. A rollback is used if a write or verification fails. For cooling-related problems, a safe fallback to kernel control remains available if the user profile cannot be activated.

### 16. Safety

Overclocking, Device Tree settings, USB limits, and boot configuration can affect system stability. Change them incrementally and verify the actual runtime state after every full restart. Do not ignore throttling, power, or temperature warnings.

### 17. Reference files

- `docs/QUICK_SETUP.md` — quick setup;
- `docs/CONFIG_TXT_REFERENCE.md` — `config.txt` parameters;
- `docs/LOCAL_ZIP_UPDATE.md` — local updates;
- `docs/GPU_V3D_ISP_PROFILES.md` — GPU profiles;
- `CHANGELOG.md` — release history.

---

## Polski

### 1. Wymagania

#### Rdzeń

- Raspberry Pi 5 / `aarch64`;
- Home Assistant OS `>= 18.3`;
- Home Assistant Core `>= 2026.10.1`;
- aplikacja SBC5 Control Center z dostępem do hosta;
- natywna integracja `sbc5_control_center` (zalecana instalacja zarządzana przez HACS).

#### Kompletny dashboard Lovelace

Zainstaluj przez HACS:

- **Mushroom** — kafelki, selektory i elementy sterujące SBC5;
- **card-mod** — stylowanie kart i dynamiczny układ;
- **ApexCharts Card** — wykresy temperatury CPU/PWM, predykcji AI oraz historii.

Natywna integracja SBC5 może udostępniać informacje o urządzeniu, telemetrię i encje sterujące bez tych kart frontendowych; są one wymagane do kompletnego dashboardu.

### 2. Architektura

SBC5 składa się z czterech warstw:

1. **Home Assistant App** — runtime, host access, Ingress, aktualizacje, `config.txt`, chłodzenie i profile sprzętowe.
2. **Natywna integracja `sbc5_control_center`** — urządzenie, sensory, binary sensory, encja Update, usługi i Repairs.
3. **Package Home Assistant** — helpery UI, skrypty i bezpieczne akcje z Lovelace.
4. **Lovelace** — karta diagnostyczna oraz karta aktualizacji.

Dane trwałe modelu AI, kalibracji, profili i markerów aktualizacji są przechowywane w `/data` aplikacji.

### 3. Instalacja i pierwszy start

Przy **pierwszej instalacji od zera** użyj **[`docs/FIRST_INSTALL.md`](docs/FIRST_INSTALL.md)**. Przewodnik obejmuje dodanie repozytorium aplikacji w Home Assistant, instalację App/runtime, kontrolę pierwszego startu, integrację HACS, wymagane zależności frontendowe i końcową weryfikację.

Dla przygotowanego już środowiska SBC5:

1. Zainstaluj aplikację SBC5 Control Center.
2. Uruchom ją i sprawdź, czy `Platform Guard` oraz `Host Access` zgłaszają stan prawidłowy.
3. Zrestartuj Home Assistant, jeśli instalator wymaga przeładowania package lub integracji.
4. Dodaj kartę `dashboard/sbc5_control_center_diagnostics_card.yaml` oraz opcjonalną `dashboard/update_status_card.yaml`.
5. Zweryfikuj obecność urządzenia **SBC5 Control Center** w rejestrze urządzeń.

Szczegółowa ścieżka startowa znajduje się w `docs/QUICK_SETUP.md`.

### 4. Active Cooler

SBC5 obsługuje profil fabryczny oraz profil `custom1`. Dla `custom1` runtime sprawdza, czy kernel udostępnia oczekiwaną siatkę 1% (`max_state >= 100`). Jeśli aktywny jest profil fabryczny, Adaptive PWM nie przejmuje sterowania i chłodzenie pozostaje po stronie kernela.

#### Tryby sterowania

- **Automatic** — regulator dobiera PWM automatycznie;
- **Hybrid** — automat z ograniczoną korektą użytkownika;
- **Manual** — sterowanie według ręcznej konfiguracji.

#### Kalibracja

Kalibracja PWM→RPM służy do wyznaczenia bezpiecznego minimum pracy wentylatora. Po zmianach mechanicznych lub wymianie coolera warto wykonać ją ponownie.

### 5. Adaptive PWM

Bazą jest krzywa `custom1(T)`. Regulator może nakładać ograniczony trim, ale nie zastępuje krzywej nieograniczonym stanem sterownika. Mechanizmy ochronne obejmują deadband, confirm cycles, anti-windup, Sign Guard, limity kierunku i slew limiter. Ścieżka awaryjna 100% pozostaje natychmiastowa.

### 6. AI Cooling

AI działa lokalnie i nie wysyła modelu do usług zewnętrznych. Uczenie wykorzystuje próbki jakościowe przypisane do bucketów obciążenia `idle`, `low`, `medium`, `high`. Model może pracować w trybie Learning lub ograniczonym Assist.

Na karcie kafelek **AI Cooling** rozwija pełną diagnostykę: dojrzałość bucketu, próbki, predykcję, pokrycie modelu, klasyfikację obciążenia, diagnostykę kwalifikacji i sugestie siatki. Sekcja jest domyślnie zwinięta.

### 7. CPU / Overclocking

Dostępne są presety Factory, Mild, Balanced, Performance, Experimental oraz Advanced. Profile nie wymuszają ręcznie `over_voltage`; napięcie pozostaje pod kontrolą firmware/DVFS, o ile użytkownik nie skonfiguruje inaczej ustawień zaawansowanych.

Zmiana profilu zapisuje konfigurację boot tylko wtedy, gdy wynik faktycznie różni się od bieżącego pliku zarządzanego. Po realnej zmianie wymagany jest pełny restart Raspberry Pi i późniejsza weryfikacja saved/runtime.

Na karcie sekcja CPU/OC znajduje się **bezpośrednio pod wykresem temperatury CPU/PWM i nad GPU/V3D/ISP**.

#### Zegar CPU

Kafelek **Zegar CPU** pokazuje skrócony stan częstotliwości czterech rdzeni. Dotknięcie rozwija osobne kafelki CPU0–CPU3 z częstotliwością i obciążeniem. Długie przytrzymanie otwiera standardowe `more-info`.

### 8. GPU / V3D / ISP

Profile GPU obejmują Factory, Eco, Balanced, Performance, Experimental i Advanced. Zmiany częstotliwości są ustawieniami boot i po realnym zapisie wymagają pełnego restartu Raspberry Pi. Profil Factory pozostawia zegary pod kontrolą firmware.

### 9. Zarządzanie `config.txt`

SBC5 zapisuje własne, zarządzane fragmenty konfiguracji, wykonuje backup przed zmianą i nie powinien nadpisywać wpisów użytkownika poza blokami należącymi do aplikacji. Porównanie jest semantyczne: zmiana numeru wersji w komentarzu nagłówka nie jest traktowana jako zmiana boot.

### 10. Restart Manager

Restart Manager rozróżnia:

- restart aplikacji;
- restart Home Assistant;
- pełny restart hosta Raspberry Pi.

Priorytet jest monotoniczny: `host > home_assistant > app`. Aktualizacja aplikacji nie może sama podnieść restartu do `host`, jeśli nie istnieje rzeczywista zmiana konfiguracji boot.

### 11. Aktualizacje lokalne

Kanoniczny katalog lokalnych ZIP-ów to `/config/sbc5_control_center_updates/`. Paczka jest weryfikowana przez manifest i SHA-256, a po instalacji Health Check sprawdza runtime, bridge i encje Home Assistanta.

Kafelek **SBC5 Control Center** na karcie aktualizacji rozwija dopiero po dotknięciu status paczki, akcję sprawdzenia, log, instalację i ewentualne komunikaty Restart Managera. Sekcja startuje zwinięta.

### 12. Telemetria i Recorder

Szybkie dane sterujące są odseparowane od cięższej diagnostyki. Typowe kadencje:

| Dane | Kadencja |
|---|---:|
| Temperatura / RPM / PWM | 5 s |
| Adaptive PWM / AI evaluator | 10 s |
| Pełna telemetria bridge | 15 s |
| Relay hosta | 30 s |
| Diagnostyka systemowa | 60 s |
| Identyfikacja sprzętu/firmware | 300 s |

Ciężkie encje transportowe nie są zapisywane w Recorder. Dla historii parametrów AI istnieją osobne encje pomiarowe.

### 13. Identyfikacja sprzętu i firmware

Urządzenie SBC5 publikuje model Raspberry Pi, model ID/rewizję, HW Rev, serial, MAC i wersję oprogramowania. Diagnostyka udostępnia system operacyjny, kernel, architekturę, firmware Raspberry Pi oraz bootloader EEPROM.

### 14. Diagnostyka

W razie problemu sprawdź kolejno:

1. stan aplikacji i log runtime;
2. `Platform Guard` i `Host Access`;
3. `SBC5 Cooling Problem`, `Throttling Status` i zasilanie;
4. `Config Differs From Active` i `Restart Required`;
5. profil zapisany oraz aktywny po boot;
6. status bridge i wersję package/Card UI.

### 15. Backup i odzyskiwanie

Przed zmianami boot SBC5 tworzy backup zarządzanej konfiguracji. Przy błędzie zapisu lub weryfikacji używany jest rollback. Dla problemów z chłodzeniem zawsze zachowany jest bezpieczny fallback do sterowania kernela, jeśli użytkownikowy profil nie może zostać aktywowany.

### 16. Bezpieczeństwo

Overclocking, Device Tree, limity USB i ustawienia boot mogą wpływać na stabilność. Zmieniaj je etapami i po każdym pełnym restarcie weryfikuj rzeczywisty stan runtime. Nie ignoruj komunikatów o throttlingu, problemach z zasilaniem lub temperaturze.

### 17. Pliki referencyjne

- `docs/QUICK_SETUP.md` — szybka konfiguracja;
- `docs/CONFIG_TXT_REFERENCE.md` — parametry `config.txt`;
- `docs/LOCAL_ZIP_UPDATE.md` — lokalne aktualizacje;
- `docs/GPU_V3D_ISP_PROFILES.md` — profile GPU;
- `CHANGELOG.md` — historia zmian.
