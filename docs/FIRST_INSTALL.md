# SBC5 Control Center — First Installation / Pierwsza instalacja

> This guide is for users installing SBC5 Control Center in Home Assistant for the first time. It assumes no previous SBC5 installation.
>
> Ten przewodnik jest przeznaczony dla osób instalujących SBC5 Control Center w Home Assistant po raz pierwszy. Nie zakłada wcześniejszej instalacji SBC5.

---

## English

### 1. What you are installing

SBC5 Control Center has two required project layers and one optional dashboard layer:

1. **SBC5 Control Center App/runtime** — runs on Raspberry Pi 5 and provides host telemetry, cooling control, profiles, update handling and Restart Manager.
2. **SBC5 Control Center Home Assistant integration** — installed through HACS and exposes SBC5 devices, sensors and controls natively in Home Assistant.
3. **Lovelace/dashboard frontend dependencies** — Mushroom, card-mod and ApexCharts Card. These are required only for the complete SBC5 dashboard.

Install them in exactly that order: **App/runtime → integration → frontend dependencies/dashboard**.

### Installation in 5 minutes

[![Add SBC5 Control Center App repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fkrlmdfk%2Fsbc5-control-center)

1. **Settings → Apps → Install app → ⋮ → Repositories** → add `https://github.com/krlmdfk/sbc5-control-center`.
2. Install **SBC5 Control Center**, disable **Protection Mode**, enable **Start on boot**, start the App and verify `Platform Guard: OK` + `Host Access: SUCCESS`.
3. **HACS → ⋮ → Custom repositories** → add `https://github.com/krlmdfk/sbc5-control-center-integration` as **Integration**.
4. Install the SBC5 integration and, for the full dashboard, **Mushroom**, **card-mod**, and **ApexCharts Card**.
5. Restart Home Assistant when requested and add/verify **SBC5 Control Center** under **Settings → Devices & services**.

> The main App repository belongs in the Home Assistant **Apps repository list**. The integration repository belongs in **HACS Custom repositories**. They are not interchangeable.

### 2. Requirements

Before starting, verify:

- Raspberry Pi 5 / `aarch64`;
- Home Assistant OS `>= 18.3`;
- Home Assistant Core `>= 2026.10.1`;
- Internet access from Home Assistant;
- administrator access to Home Assistant.

For the complete Lovelace dashboard you will also need HACS.

### 3. Add the SBC5 App repository to Home Assistant

1. Open **Settings → Apps**.
2. Choose **Install app**.
3. Open the **⋮** menu in the upper-right corner.
4. Choose **Repositories**.
5. Add:

   `https://github.com/krlmdfk/sbc5-control-center`

6. Confirm the repository and wait for the App store to refresh.
7. Search for **SBC5 Control Center**.

If the App does not appear, refresh the App store and verify that the repository URL was entered exactly as shown above.

### 4. Install and start SBC5 Control Center App/runtime

1. Open **SBC5 Control Center** in the App store.
2. Choose **Install**.
3. In **Info**, disable **Protection Mode**. SBC5 needs Host PID/full host access for `config.txt`, PMIC and firmware diagnostics.
4. Enable **Start on boot**.
5. Optionally enable **Show in sidebar**.
6. Choose **Start**.
7. Open the **Log** tab.

A healthy first start should show, among other messages:

- `Platform Guard: OK`;
- `Host Access: SUCCESS`.

Do not continue with CPU/GPU tuning if Platform Guard or Host Access reports a problem.

### 5. Open the SBC5 Web UI

Choose **Open Web UI** on the App page.

Verify that SBC5 shows Raspberry Pi 5 information and live telemetry. On a first installation leave CPU/GPU profiles and advanced boot options at their defaults.

### 6. Install HACS if it is not already installed

SBC5 uses HACS for the native Home Assistant integration and for the complete Lovelace dashboard dependencies.

If HACS is not installed yet, install it first using the official HACS instructions: **https://www.hacs.xyz/**. Finish HACS onboarding in Home Assistant before continuing.

If HACS is already working, continue to the next step.

### 7. Add the SBC5 integration repository to HACS

1. Open **HACS**.
2. Open **⋮ → Custom repositories**.
3. Repository:

   `https://github.com/krlmdfk/sbc5-control-center-integration`

4. Category: **Integration**.
5. Choose **Add**.
6. Open **SBC5 Control Center** in HACS.
7. Choose **Download / Install** and install the newest stable release.
8. Restart Home Assistant if HACS requests it.

The HACS integration requires the SBC5 App/runtime to be installed and running. Installing the integration alone is not enough.

### 8. Add the integration to Home Assistant

After the Home Assistant restart:

1. Open **Settings → Devices & services**.
2. If **SBC5 Control Center** is discovered, choose **Configure / Add**.
3. If it is not discovered automatically, choose **Add integration** and search for **SBC5 Control Center**.
4. Finish the configuration flow.

A device named **SBC5 Control Center** should appear in the device registry.

### 9. Verify native SBC5 entities

Open the **SBC5 Control Center** device and verify that live values are available, for example:

- CPU temperature;
- fan PWM;
- fan RPM;
- CPU load;
- CPU clock information;
- SBC5 version/update state;
- diagnostics and Restart Manager entities.

If the values update, the path **App/runtime → integration → Home Assistant** is working correctly.

### 10. Install the frontend dependencies for the complete dashboard

In HACS install the newest stable versions of:

- **Mushroom** — SBC5 tiles, selectors and controls;
- **card-mod** — styling and dynamic card layout;
- **ApexCharts Card** — CPU temperature/PWM, AI prediction and history charts.

Restart Home Assistant if HACS requests it.

These three frontend components are not required for the native integration itself, but they are required for the complete SBC5 Lovelace interface.

### 11. Add the SBC5 dashboard cards

The project provides:

- `dashboard/sbc5_control_center_diagnostics_card.yaml` — main diagnostics/control card;
- `dashboard/update_status_card.yaml` — update/status card.

Before adding the main card, make sure Mushroom, card-mod and ApexCharts Card are installed. If a dependency is missing, Home Assistant may display errors such as `Custom element doesn't exist`.

### 12. First cooling check

Before changing overclocking or advanced settings:

1. verify CPU temperature;
2. verify fan RPM and PWM;
3. verify that the fan reacts to temperature changes;
4. check power/throttling diagnostics;
5. run Active Cooler PWM→RPM calibration before reducing minimum PWM aggressively.

Do not set minimum PWM below a value at which the fan is mechanically stable.

### 13. Restart rules

- HACS integration installation/update may require a **Home Assistant restart**.
- A normal integration update does **not** require a Raspberry Pi restart.
- Perform a full Raspberry Pi restart only when **SBC5 Restart Manager** requests it after a real boot/configuration change.

### 14. Final checklist

Installation is complete when:

- SBC5 Control Center App/runtime is running;
- `Platform Guard: OK`;
- `Host Access: SUCCESS`;
- SBC5 Control Center integration is configured in Home Assistant;
- the SBC5 device has live entities;
- Mushroom, card-mod and ApexCharts Card are installed if you use the complete dashboard;
- the SBC5 card renders without missing-element errors.

After this baseline works, continue with Adaptive PWM, AI Cooling, CPU/GPU profiles and advanced configuration.

---

## Polski

### 1. Co właściwie instalujesz

SBC5 Control Center składa się z dwóch wymaganych warstw projektu oraz opcjonalnej warstwy dashboardu:

1. **SBC5 Control Center App/runtime** — działa na Raspberry Pi 5 i zapewnia telemetrię hosta, sterowanie chłodzeniem, profile sprzętowe, aktualizacje i Restart Manager.
2. **Integracja SBC5 Control Center dla Home Assistant** — instalowana przez HACS; udostępnia urządzenie, sensory i sterowanie SBC5 natywnie w Home Assistant.
3. **Zależności frontendowe Lovelace/dashboardu** — Mushroom, card-mod i ApexCharts Card. Są wymagane do pełnego dashboardu SBC5.

Instaluj dokładnie w tej kolejności: **App/runtime → integracja → zależności frontendowe/dashboard**.

### Instalacja w 5 minut

1. **Ustawienia → Apps → Install app / Zainstaluj aplikację → ⋮ → Repositories / Repozytoria** → dodaj `https://github.com/krlmdfk/sbc5-control-center`.
2. Zainstaluj **SBC5 Control Center**, wyłącz **Protection Mode**, włącz **Start on boot / Uruchamiaj przy starcie**, uruchom aplikację i sprawdź `Platform Guard: OK` + `Host Access: SUCCESS`.
3. **HACS → ⋮ → Custom repositories / Niestandardowe repozytoria** → dodaj `https://github.com/krlmdfk/sbc5-control-center-integration` jako **Integration / Integracja**.
4. Zainstaluj integrację SBC5 oraz, dla pełnego dashboardu, **Mushroom**, **card-mod** i **ApexCharts Card**.
5. Uruchom ponownie Home Assistant, gdy będzie to wymagane, a następnie dodaj/sprawdź **SBC5 Control Center** w **Ustawienia → Urządzenia i usługi**.

> Główne repozytorium App dodaje się do listy repozytoriów sklepu **Apps** Home Assistant. Repozytorium integracji dodaje się do **HACS → Niestandardowe repozytoria**. Nie są zamienne.

### 2. Wymagania

Przed rozpoczęciem sprawdź:

- Raspberry Pi 5 / `aarch64`;
- Home Assistant OS `>= 18.3`;
- Home Assistant Core `>= 2026.10.1`;
- dostęp Home Assistant do Internetu;
- uprawnienia administratora Home Assistant.

Do kompletnego dashboardu Lovelace potrzebny będzie również HACS.

### 3. Dodaj repozytorium aplikacji SBC5 do Home Assistant

1. Otwórz **Ustawienia → Apps**.
2. Wybierz **Install app / Zainstaluj aplikację**.
3. Otwórz menu **⋮** w prawym górnym rogu.
4. Wybierz **Repositories / Repozytoria**.
5. Dodaj:

   `https://github.com/krlmdfk/sbc5-control-center`

6. Zatwierdź repozytorium i poczekaj na odświeżenie sklepu aplikacji.
7. Wyszukaj **SBC5 Control Center**.

Jeżeli aplikacja nie pojawia się na liście, odśwież sklep i sprawdź, czy adres repozytorium został wpisany dokładnie tak jak powyżej.

### 4. Zainstaluj i uruchom SBC5 Control Center App/runtime

1. Otwórz **SBC5 Control Center** w sklepie aplikacji.
2. Wybierz **Install / Zainstaluj**.
3. W **Info** wyłącz **Protection Mode**. SBC5 wymaga Host PID/pełnego dostępu hosta dla `config.txt`, PMIC i diagnostyki firmware.
4. Włącz **Start on boot / Uruchamiaj przy starcie**.
5. Opcjonalnie włącz **Show in sidebar / Pokaż na pasku bocznym**.
6. Wybierz **Start / Uruchom**.
7. Otwórz zakładkę **Log**.

Prawidłowy pierwszy start powinien pokazać między innymi:

- `Platform Guard: OK`;
- `Host Access: SUCCESS`.

Jeśli Platform Guard lub Host Access zgłasza problem, nie przechodź jeszcze do konfiguracji CPU/GPU.

### 5. Otwórz interfejs WWW SBC5

Na stronie aplikacji wybierz **Open Web UI / Otwórz interfejs WWW**.

Sprawdź, czy SBC5 pokazuje informacje o Raspberry Pi 5 i aktualną telemetrię. Przy pierwszej instalacji pozostaw profile CPU/GPU oraz zaawansowane opcje boot w ustawieniach domyślnych.

### 6. Zainstaluj HACS, jeśli jeszcze go nie masz

SBC5 korzysta z HACS do instalacji natywnej integracji Home Assistant oraz zależności kompletnego dashboardu Lovelace.

Jeżeli HACS nie jest jeszcze zainstalowany, zainstaluj go według oficjalnej instrukcji HACS: **https://www.hacs.xyz/**. Zakończ konfigurację HACS w Home Assistant, zanim przejdziesz dalej.

Jeśli HACS już działa, przejdź do następnego kroku.

### 7. Dodaj repozytorium integracji SBC5 do HACS

1. Otwórz **HACS**.
2. Otwórz **⋮ → Custom repositories / Niestandardowe repozytoria**.
3. Repozytorium:

   `https://github.com/krlmdfk/sbc5-control-center-integration`

4. Kategoria: **Integration / Integracja**.
5. Wybierz **Add / Dodaj**.
6. Otwórz **SBC5 Control Center** w HACS.
7. Wybierz **Download / Install** i zainstaluj najnowsze stabilne wydanie.
8. Uruchom ponownie Home Assistant, jeśli HACS o to poprosi.

Integracja HACS wymaga wcześniej zainstalowanej i uruchomionej aplikacji/runtime SBC5. Sama integracja nie ma dostępu do telemetrii hosta bez App/runtime.

### 8. Dodaj integrację w Home Assistant

Po ponownym uruchomieniu Home Assistant:

1. Otwórz **Ustawienia → Urządzenia i usługi**.
2. Jeżeli **SBC5 Control Center** zostanie wykryty automatycznie, wybierz **Configure / Dodaj**.
3. Jeśli nie został wykryty, wybierz **Dodaj integrację** i wyszukaj **SBC5 Control Center**.
4. Zakończ konfigurację.

W rejestrze urządzeń powinno pojawić się urządzenie **SBC5 Control Center**.

### 9. Sprawdź natywne encje SBC5

Otwórz urządzenie **SBC5 Control Center** i sprawdź, czy widoczne są aktualne wartości, np.:

- temperatura CPU;
- PWM wentylatora;
- RPM wentylatora;
- obciążenie CPU;
- informacje o taktowaniu CPU;
- wersja i stan aktualizacji SBC5;
- encje diagnostyczne oraz Restart Manager.

Jeśli wartości aktualizują się, ścieżka **App/runtime → integracja → Home Assistant** działa prawidłowo.

### 10. Zainstaluj zależności frontendowe pełnego dashboardu

W HACS zainstaluj najnowsze stabilne wersje:

- **Mushroom** — kafelki, selektory i elementy sterujące SBC5;
- **card-mod** — stylowanie i dynamiczny układ kart;
- **ApexCharts Card** — wykresy temperatury CPU/PWM, predykcji AI oraz historii.

Uruchom ponownie Home Assistant, jeśli HACS o to poprosi.

Te trzy komponenty nie są wymagane do działania samej natywnej integracji, ale są wymagane przez kompletny interfejs Lovelace SBC5.

### 11. Dodaj karty dashboardu SBC5

Projekt dostarcza:

- `dashboard/sbc5_control_center_diagnostics_card.yaml` — główna karta diagnostyczno-sterująca;
- `dashboard/update_status_card.yaml` — karta aktualizacji i statusu.

Przed dodaniem głównej karty upewnij się, że Mushroom, card-mod i ApexCharts Card są zainstalowane. Brak zależności może powodować komunikaty typu `Custom element doesn't exist`.

### 12. Pierwsza kontrola chłodzenia

Zanim zmienisz overclocking lub ustawienia zaawansowane:

1. sprawdź temperaturę CPU;
2. sprawdź RPM i PWM wentylatora;
3. sprawdź reakcję wentylatora na zmianę temperatury;
4. sprawdź diagnostykę zasilania/throttlingu;
5. wykonaj kalibrację Active Cooler PWM→RPM przed mocnym obniżaniem minimalnego PWM.

Nie ustawiaj minimalnego PWM poniżej wartości, przy której wentylator pracuje mechanicznie stabilnie.

### 13. Zasady restartów

- Instalacja/aktualizacja integracji HACS może wymagać **restartu Home Assistant**.
- Zwykła aktualizacja integracji **nie wymaga** restartu Raspberry Pi.
- Pełny restart Raspberry Pi wykonuj tylko wtedy, gdy **SBC5 Restart Manager** zażąda go po rzeczywistej zmianie konfiguracji boot/sprzętowej.

### 14. Lista kontrolna po instalacji

Instalacja jest zakończona, gdy:

- SBC5 Control Center App/runtime działa;
- `Platform Guard: OK`;
- `Host Access: SUCCESS`;
- integracja SBC5 Control Center jest skonfigurowana w Home Assistant;
- urządzenie SBC5 ma aktualizujące się encje;
- Mushroom, card-mod i ApexCharts Card są zainstalowane, jeśli korzystasz z pełnego dashboardu;
- karta SBC5 wyświetla się bez błędów brakujących elementów.

Dopiero po takim uruchomieniu bazowym przechodź do Adaptive PWM, AI Cooling, profili CPU/GPU i konfiguracji zaawansowanej.
## Automatic update detection / Automatyczne wykrywanie aktualizacji

**Apps:** Home Assistant Supervisor refreshes custom Git repositories and exposes a native App update when the repository `config.yaml` version is newer than the installed version. Use **Check for updates / Sprawdź aktualizacje** only when you want an immediate refresh.

**HACS:** HACS stable versions come from published GitHub Releases; a tag alone is not enough. SBC5 repositories now publish their tag and GitHub Release automatically after successful CI. Custom HACS repositories are refreshed automatically by HACS; **Update information / Aktualizuj informacje** forces an immediate check.

**SBC5:** the App additionally checks the canonical GitHub release metadata every 6 hours, so its own update sensor can notify independently of the store refresh cycles.
