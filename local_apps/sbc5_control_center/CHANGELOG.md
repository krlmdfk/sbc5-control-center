# Changelog — SBC5 Control Center

Historia zmian projektu. Aktualny stan, instalacja i obsługa są opisane w `INFO.md`, `DOCUMENTATION.md` oraz `docs/QUICK_SETUP.md`. Starsza historia sprzed gałęzi 2.8.x pozostaje w `docs/CHANGELOG_ARCHIVE_PRE_2.8.0.md`.

## 2.8.25 — CPU Profile Restart Guard Hotfix

- Naprawiono fałszywe żądanie pełnego restartu Raspberry Pi po aktualizacji przy niezmienionym profilu CPU/OC: `sbc5cc-cpu-profile.txt` nie jest już porównywany bajt-po-bajcie względem komentarza zawierającego wersję aplikacji.
- Dodano semantyczne porównanie dedykowanego profilu CPU/OC. Zmiana samego nagłówka wersji jest ignorowana, natomiast rzeczywiste zmiany `arm_freq`, parametrów OC lub obecności `include` nadal prawidłowo powodują `restart=host`.
- Nowo zapisywane pliki profilu CPU używają stabilnego nagłówka bez numeru wersji, aby kolejne aktualizacje aplikacji nie modyfikowały konfiguracji boot wyłącznie z powodu metadanych.
- Dodano bezpieczne czyszczenie znanego fałszywego markera z 2.8.24. Marker jest usuwany tylko wtedy, gdy jego zakres to `cpu_profile`, pochodzi z 2.8.24, bieżący profil i bezpośredni backup są semantycznie identyczne oraz `include sbc5cc-cpu-profile.txt` istniał zarówno przed, jak i po zapisie.
- Zachowano ochronę dla prawdziwych zmian CPU/OC: zmiana np. Mild 2500 MHz → Balanced 2600 MHz nadal wymaga pełnego restartu Raspberry Pi i Boot Verification.
- Aktualizacja 2.8.25 wymaga restartu Home Assistant w celu przeładowania pełnego buildu. **Restart Raspberry Pi nie jest wymagany przez ten hotfix**, jeśli użytkownik nie zmienił rzeczywistej konfiguracji boot.
- Adaptive PWM, AI Cooling, kwalifikacja próbek, kalibracja i układ karty 2.8.24 pozostają funkcjonalnie bez zmian.

## 2.8.24 — Collapsible Mobile Card Sections

- Przebudowano kartę aktualizacji: kafelek **SBC5 Control Center** przełącza widoczność pozostałych opcji; status paczki, akcje, instalacja i Restart Manager są domyślnie schowane.
- Przebudowano sekcję **AI Cooling**: główny kafelek pozostaje zawsze widoczny, a diagnostyka uczenia, historia predykcji, pokrycie, kwalifikacja próbki i narzędzia siatki są rozwijane dopiero po dotknięciu.
- Dodano kafelek **Zegar CPU**, który rozwija osobne kafelki CPU0–CPU3; szczegóły rdzeni są domyślnie schowane.
- Przeniesiono sekcję **CPU / Overclocking** bezpośrednio pod wykres temperatury CPU/PWM i nad **GPU / V3D / ISP**. Dotychczasowe niezależne rozwijanie wyboru profilu CPU oraz GPU zostało zachowane.
- Dodano trzy helpery UI: `input_boolean.sbc5_update_controls_visible`, `input_boolean.sbc5_ai_controls_visible` i `input_boolean.sbc5_cpu_clock_details_visible`; wszystkie startują jako `off`.
- Uporządkowano `README`, `INFO`, dokumentację i Quick Setup w spójny układ GitHub-style; usunięto z dokumentacji treści historyczne i zduplikowane nagłówki, pozostawiając historię wyłącznie w changelogu.
- Zmiany dotyczą warstwy UI/package i dokumentacji. Adaptive PWM, AI Cooling, kwalifikacja próbek, profile sprzętowe, Restart Guard i szybkie ścieżki telemetrii pozostają bez zmian.
- Aktualizacja pełnego buildu wymaga restartu Home Assistant z powodu nowych helperów Package. Restart Raspberry Pi nie jest wymagany przez tę zmianę.

## 2.8.23 — Config Restart Guard Hotfix

- Naprawiono fałszywe żądanie pełnego restartu Raspberry Pi po aktualizacji: automatyczna synchronizacja `sbc5cc-managed.txt` nie traktuje już zmiany numeru wersji w komentarzu nagłówka jako zmiany semantyki `config.txt`.
- Porównanie pliku zarządzanego jest teraz semantyczne dla nagłówka wersji; rzeczywista zmiana parametrów boot nadal tworzy `restart=host` bez osłabiania zabezpieczeń Restart Managera.
- Dodano bezpieczną migrację dla błędu 2.8.22: marker restartu hosta jest automatycznie usuwany tylko wtedy, gdy pochodzi z dokładnie znanego zapisu Config Options 2.8.22, bieżący plik i jego bezpośredni backup różnią się wyłącznie numerem wersji komentarza, a telemetria nie wykrywa różnicy `saved != active`.
- Post-update state zachowuje typ restartu zadeklarowany przez wydanie i nie jest już sztucznie promowany do `host` przez niezależne, wcześniej istniejące żądanie restartu boot. Niezależny restart hosta nadal ma priorytet w bieżącym stanie Restart Managera.
- Zmieniono tytuł flow Home Assistant Repairs z mylącego „Dokończ aktualizację” na neutralny komunikat o wymaganym restarcie, ponieważ to samo Repair obsługuje także zmiany konfiguracji boot.
- Aktualizacja 2.8.23 wymaga restartu Home Assistant w celu przeładowania bridge/package. **Pełny restart Raspberry Pi nie jest wymagany przez ten hotfix** i pozostaje wymagany wyłącznie po realnej zmianie konfiguracji boot/Device Tree.
- Adaptive PWM, AI Cooling, limity bezpieczeństwa i częstotliwości telemetrii pozostają bez zmian.

## 2.8.22 — Raspberry Pi Device Identity & Firmware Diagnostics

- Rozszerzono natywne `DeviceInfo` Home Assistant o pełny model Raspberry Pi, identyfikator rewizji płyty (`model_id`), wersję sprzętu, numer seryjny i połączenie MAC; wersja oprogramowania urządzenia nadal odpowiada zunifikowanej wersji SBC5 Control Center.
- Dodano lekkie, buforowane (300 s) zbieranie statycznej identyfikacji hosta: rewizji płyty, numeru seryjnego, MAC, Home Assistant OS, firmware Raspberry Pi i wersji bootloadera EEPROM.
- Dodano encje diagnostyczne `SBC5 Operating System`, `SBC5 Kernel`, `SBC5 Architecture`, `SBC5 Raspberry Pi Firmware` i `SBC5 Bootloader Firmware`; `SBC5 System Info` zawiera również model, model ID, HW Rev, serial, MAC, OS i firmware.
- Schemat telemetrii hosta podniesiono do 11; natywna integracja i fallback REST obsługują nowe pola z zachowaniem zgodności ze starszymi snapshotami.
- Nie zmieniono Adaptive PWM, AI Cooling, zabezpieczeń termicznych ani częstotliwości szybkiej telemetrii. Dane identyfikacyjne są odświeżane co 300 s, aby zachować optymalizacje obciążenia z 2.8.21.
- Aktualizacja wymaga restartu Home Assistant, aby przeładować integrację i zarejestrować nowe encje. Restart Raspberry Pi nie jest wymagany przez tę zmianę.

## 2.8.21 — Lightweight HA Runtime

- Rozdzielono szybki stan AI od ciężkiego `sensor.sbc5_control_center_host_telemetry`: AI korzysta z kompaktowego `sensor.sbc5_control_center_ai_runtime` ocenianego co 15 s i publikowanego po zmianie (z 5-minutowym keepalive), a pełny relay hosta co 30 s.
- Native bridge pobiera pełną telemetrię przede wszystkim z pliku współdzielonego zamiast wymagać częstego dużego wpisu REST w maszynie stanów Home Assistanta; główny coordinator pracuje co 15 s, natomiast temperatura i wentylator pozostają na lekkiej ścieżce 5 s.
- Szablony AI i karta Lovelace zostały odpięte od dużego host-relay; stan profili CPU/GPU korzysta z już synchronizowanych `input_select`, dzięki czemu zmiany profili nie wymagają cyklicznego renderowania od pełnej telemetrii.
- Usunięto zmienny `sample_age_s` z atrybutów encji i wyłączono wiek próbki z porównania snapshotów, ograniczając puste aktualizacje stanu przy niezmienionych wartościach.
- Keepalive stanów UX zmniejszono z 30 s do 5 min przy zachowaniu 10-sekundowego wykrywania restartu Core; test dostępności używa lekkiego `/api/` zamiast pełnego `/api/config`.
- Po zakończeniu migracji namespace Curve Editor nie publikuje już równolegle nieużywanego aliasu `sensor.sbc5_fan_curve_editor`; alias pozostaje wyłącznie na czas migracji.
- Reconciler profili Supervisor pracuje co 30 s zamiast 15 s, diagnostyka zużycia procesu jest publikowana co 60 s zamiast 30 s, a Restart Manager pomija ponowną publikację identycznego stanu.
- Usunięto podwójny odczyt cgroup CPU w pomiarze wydajności. Bezczynny watcher zdrowia aktualizacji przechodzi na 60 s i wraca do 10 s wyłącznie podczas oczekiwania na Phase B. Adaptive PWM pozostaje na 10 s, lekka telemetria temperatury/RPM/PWM na 5 s, a algorytm AI Cooling i zabezpieczenia termiczne nie zostały spowolnione.
- Aktualizacja wymaga restartu Home Assistant w celu przeładowania bridge/package. Restart Raspberry Pi nie jest wymagany, o ile osobno nie oczekuje na niego zmiana `config.txt` lub profilu sprzętowego.

## 2.8.20 — Configuration Action Feedback

- Przycisk **Zapisz konfigurację** w interfejsie Ingress pokazuje teraz stan „Zapisywanie…”, zielone potwierdzenie `✓ Zapisano` po sukcesie oraz czerwone `✕ Błąd zapisu` po niepowodzeniu.
- Przycisk **Odśwież** pokazuje analogicznie „Odświeżanie…”, zielone `✓ Odświeżono` lub czerwone `✕ Błąd`.
- Podczas wykonywania operacji odpowiedni przycisk jest czasowo blokowany, co zapobiega wielokrotnemu wysłaniu tej samej akcji.
- Potwierdzenie pozostaje widoczne około 2,6 s, po czym przycisk automatycznie wraca do zwykłego wyglądu i etykiety.
- Zmiana jest lokalna dla warstwy Ingress UI i nie dodaje nowych timerów sieciowych ani częstszej telemetrii; zachowane są optymalizacje obciążenia 2.8.18 oraz zachowanie profili z 2.8.19.
- Aktualizacja nie wymaga restartu Raspberry Pi. Pełny build wymaga standardowego restartu Home Assistant, aby wszystkie składowe wersji były spójne.

## 2.8.19 — Collapsible CPU/GPU Profile Controls

- Kafelek stanu CPU/OC przełącza teraz widoczność pól wyboru profilu i przycisku zastosowania; po uruchomieniu Home Assistanta sekcja jest domyślnie zwinięta.
- Kafelek stanu GPU/V3D/ISP niezależnie przełącza widoczność wyboru presetu, przycisku zastosowania oraz skrótu do ustawień zaawansowanych; sekcja również startuje zwinięta.
- Długie przytrzymanie kafelka stanu CPU lub GPU zachowuje akcję More Info, dzięki czemu historia i atrybuty encji pozostają dostępne.
- Dodano helpery `input_boolean.sbc5_cpu_profile_controls_visible` i `input_boolean.sbc5_gpu_profile_controls_visible`, oba z `initial: false`.
- Zmiana dotyczy wyłącznie warstwy Lovelace/Package; Adaptive PWM, AI Cooling, profile CPU/GPU, synchronizacja Supervisor i optymalizacje obciążenia 2.8.18 pozostają bez zmian.
- Aktualizacja wymaga restartu Home Assistant z powodu nowych helperów Package; restart Raspberry Pi nie jest wymagany.

## 2.8.18 — HA Load Optimization

- Usunięto stały zapis `/data/profile_supervisor_sync_state.json` w bezczynnej pętli synchronizacji profili; stan zgodny nie generuje już zapisu pliku co cykl.
- Reconciler CPU/GPU wykonuje jeden odczyt Supervisor na cykl zamiast dwóch i pracuje co 15 s zamiast co 5 s; natychmiastowe ścieżki zmian z YAML/Ingress pozostają bez zmian.
- Live-sync strony Konfiguracja został ograniczony z 5 s do 15 s i nadal działa tylko przy otwartej, aktywnej stronie.
- Siedem diagnostycznych encji historii AI dodanych wcześniej do Recorder jest teraz próbkowanych co 30 s zamiast renderować się przy każdym 10-sekundowym snapshotcie telemetrii.
- Adaptive PWM, AI Cooling, kwalifikacja próbek, telemetria sterująca 5/10 s, limity bezpieczeństwa, kalibracja oraz profile CPU/GPU nie zostały spowolnione.
- Aktualizacja wymaga restartu Home Assistant; restart Raspberry Pi jest potrzebny tylko wtedy, gdy wybrany profil zmieni `config.txt`.

## 2.8.17 — Synchronizacja natywnej Konfiguracji Supervisor

- Poprawiono rozbieżność, w której karta YAML i telemetria pokazywały aktywny profil CPU/GPU, natomiast natywna zakładka **Konfiguracja** Home Assistanta nadal prezentowała stare wartości `factory/off`.
- Profile CPU/GPU są teraz zapisywane do trwałego magazynu opcji Supervisor przez oficjalny endpoint `/addons/self/options`; `/data/options.json` pozostaje lokalnym plikiem runtime, a nie źródłem formularza Supervisor.
- Dodano dwukierunkowe uzgadnianie stanu: wybór z YAML lub Ingress jest propagowany do Supervisor, a jawna zmiana w natywnej Konfiguracji — również `Factory` i wyłączenie sekcji — jest importowana do trwałego stanu SBC5.
- Dodano `/data/profile_supervisor_sync_state.json`, który przechowuje podpis ostatniego stanu zapisanego przez SBC5. Dzięki temu po aktualizacji/reboocie stare wartości domyślne nie są mylone ze świadomą zmianą użytkownika.
- Synchronizacja modyfikuje w Supervisor wyłącznie pola profili CPU/GPU i zachowuje pozostałe opcje aplikacji. Dla aktywnego profilu GPU nadal automatycznie utrzymywany jest włączony Config.txt Manager.
- Przy pierwszym uruchomieniu 2.8.17 trwały stan CPU/GPU ma pierwszeństwo nad niesynchronizowanym formularzem ze starszej wersji i jest do niego jednorazowo zapisany.
- Adaptive PWM, AI Cooling, kwalifikacja próbek, limity bezpieczeństwa wentylatora i kalibracja nie zostały zmienione.
- Po instalacji wymagany jest restart Home Assistant zgodnie ze standardowym pełnym zakresem aktualizacji; sam mechanizm synchronizacji profili nie wymaga restartu Raspberry Pi, chyba że wybrany profil zmieni `config.txt`.

## 2.8.16 — Profile State Reconciliation & History Everywhere

- CPU and GPU requested profiles now use one persistent source of truth across Lovelace/YAML, Ingress WWW and the native Supervisor Configuration tab.
- Startup restores the durable CPU/GPU request before the first options snapshot, preventing transient schema defaults from falsely reverting an existing profile.
- A stable 5-second reconciler detects real later Configuration changes, including an explicit switch to Factory, canonicalizes preset values and propagates the result to telemetry and Lovelace selectors.
- Ingress Configuration live-syncs external profile changes every 5 seconds while the form is clean; unsaved local edits are never overwritten.
- CPU Advanced is now a valid Lovelace selector option, matching the web/native profile set.
- Canonical host telemetry schema 10 publishes `config_cpu_profile` and `config_gpu_profile` from persistent requested state.
- Parameter tiles that previously had no history action now open Home Assistant More Info / Recorder history. AI maturity, observations, qualified samples, model coverage, workload, stable time and grid coverage gained dedicated numeric Recorder entities.
- The existing expandable 24-hour AI Prediction graph is retained; its tile also keeps More Info on hold.
- Adaptive PWM, AI qualification/control law, fan safety bounds, slew limits and calibration logic are unchanged.

## 2.8.15 — Persistent GPU Profile State & Reboot Recovery

- Added `/data/gpu_profile_state.json` as the durable source of truth for GPU / V3D / ISP presets, mirroring the proven CPU Profile Manager persistence model.
- Dashboard selections such as **Balanced** now survive a full Raspberry Pi reboot even if Supervisor/App options temporarily return their schema default (`factory`, Config Manager disabled).
- Added upgrade recovery for 2.8.12–2.8.14: when no GPU state file exists, SBC5 inspects its existing `sbc5cc-managed.txt` and imports the already-written core / ISP / V3D preset instead of reverting it to Factory.
- Dynamic Configuration UI reads and writes the same persistent GPU state; reset/save operations update it atomically.
- A persisted GPU request re-enables Config Manager before boot configuration synchronization, preserving the requested preset and dashboard selector after restart.
- `set_gpu_profile` now stores the requested profile and resolved preset values before synchronizing `config.txt`; success is reported only after durable state and Config Manager synchronization both succeed.
- CPU Profile Manager, Adaptive PWM, AI Cooling, fan reconciliation and calibration algorithms are unchanged.

## 2.8.14 — Fan Profile Reconciliation & Cooling Health Guard

- Added startup reconciliation for the requested Active Cooler profile. When `custom1` is requested but the kernel exposes `max_state < 100`, SBC5 checks the active `config.txt` and `rpi5-custom1.dtbo` before allowing Adaptive PWM to resume.
- Missing `custom1` boot artifacts are repaired automatically **once per host boot_id**. The repair creates the normal backup, rewrites the managed fan block and requests a full Raspberry Pi restart; repeated app restarts do not rewrite `config.txt` in a loop.
- If `config.txt` and DTBO are already present but the kernel still reports the factory grid, SBC5 reports `overlay_written_not_loaded` instead of blindly rewriting the boot configuration. If this persists across a new boot after an automatic repair, the state escalates to `overlay_not_loaded_after_reboot`.
- Adaptive PWM keeps the existing safety rule: it never takes userspace ownership while `max_state < 100`; kernel cooling remains the fallback. Once the 1% grid becomes active, the existing controller loop can safely retake ownership.
- Update Health Check Phase B now validates the requested cooling profile in addition to runtime, relay, bridge and native HA entities. A full update is not finalized while `custom1` is requested but the 1% cooling grid is inactive.
- The Lovelace profile-status tile now exposes the reconciliation reason/message, making automatic repair, pending reboot and overlay-load failures visible without reading logs.
- GPU/V3D/ISP presets, dashboard selector and Advanced mode from 2.8.13 are retained unchanged.
- No changes to the Adaptive PWM control law, AI Cooling model/qualification, slew limits, emergency handoff or fan calibration algorithm.

## 2.8.13 — GPU presets directly from the dashboard

- Added a Lovelace selector for GPU / V3D / ISP profiles: Factory, Eco, Balanced, Performance, Experimental and Advanced.
- Added `script.sbc5_gpu_apply_profile` and `set_gpu_profile` stdin command so the dashboard selection is applied to `config.txt`, not only displayed in UI.
- The GPU selector is synchronized with the profile stored by the app through canonical host telemetry.
- Applying a GPU preset from Lovelace explicitly enables the GPU section and Config.txt Manager, creates the normal backup path and lets Restart Manager request a full Raspberry Pi reboot only when the generated boot configuration changes.
- Advanced remains the manual profile; its values are edited in position 22 of the Configuration tab. Factory is the one-click restore to firmware-managed clocks.
- Updated Info, Documentation, Quick Setup and GPU profile reference for the dashboard workflow.
- Adaptive PWM, AI Cooling and fan calibration algorithms are unchanged.

## 2.8.12 — GPU / V3D / ISP Profile Manager

- Position 22 now has Factory, Eco, Balanced, Performance, Experimental and Advanced profiles.
- Added manual max/min controls for core, ISP and V3D plus an explicit Factory restore action.
- Added cross-field validation (`*_freq_min <= *_freq` and `gpu_freq_min` safety checks).
- Native Supervisor options and the SBC5 configuration UI resolve the same GPU profile values.
- Presets rely on Raspberry Pi firmware DVFS and do not force `over_voltage`.
- Added Pi 5 reference values and documentation; GPU changes still require a full host reboot.
- Adaptive PWM and AI Cooling control logic are unchanged.

## 2.8.11 — 2026-10-24

### AI History Reliability + Lightweight Runtime
- pełny, zunifikowany build: App, package/integracja i Card UI mają wspólną wersję **2.8.11**;
- rozwijana historia **Predykcja AI** korzysta teraz z natywnego `history-graph` Home Assistanta zamiast drugiego renderera ApexCharts; kafelek nadal przełącza widoczność wykresu, a historia obejmuje **Model AI, Regulator, AI Delta i PWM fizyczny**;
- po zakończonej migracji namespace telemetria hosta jest publikowana tylko do kanonicznej encji SBC5; stare aliasy są utrzymywane wyłącznie do czasu zakończenia migracji;
- odciążono watchdog Core (5 s → 10 s) przy zachowaniu 30-sekundowego keepalive oraz watchdog opcji profilu (60 s → 300 s, bez zmian w natychmiastowej synchronizacji po zmianach);
- lokalny watcher ZIP korzysta z trybu `local_only`, dzięki czemu nie wykonuje przy każdym skanie dodatkowego pełnego sprawdzenia Store/remote;
- synchronizacja Lovelace kończy się jako `already_current`, jeśli wersja i zawartość karty są już identyczne — bez niepotrzebnego backupu i ponownego zapisu;
- drobne operacje plikowe integracji wykonywane podczas ścieżek `async` zostały przeniesione do executora, aby nie blokować event loop Home Assistanta;
- **Adaptive PWM, limity bezpieczeństwa, deadband, slew-rate, AI Assist bounds i awaryjne 100% pozostają bez zmian**;
- wymagany jest restart Home Assistant po instalacji pełnego buildu; restart Raspberry Pi nie jest wymagany.

## 2.8.7 — 2026-10-24

### AI Prediction History Toggle
- wykres historii predykcji AI jest domyślnie ukryty;
- naciśnięcie kafelka **Predykcja AI** rozwija wykres w głównym widoku, ponowne naciśnięcie go ukrywa;
- wykres jest pełnej szerokości i zawiera cztery przebiegi: **Model AI**, **Regulator**, **AI Delta** oraz **PWM fizyczny**;
- `AI Delta` korzysta z osobnej prawej osi, aby małe korekty były czytelne przy skali PWM 0–100%;
- dodano helper `input_boolean.sbc5_ai_prediction_chart_visible`, inicjalizowany jako `off`;
- usunięto zależność tej funkcji od popupu Browser Mod;
- instalacja 2.8.7 wymaga jednorazowego restartu Home Assistant z powodu nowego helpera/package; restart Raspberry Pi nie jest wymagany.

## 2.8.6 — 2026-10-24

### Restart-aware Update Scope
- Dodano `update_scope` do lokalnego manifestu aktualizacji.
- Paczki `dashboard_only` / `ui_only` nie podmieniają runtime aplikacji, package ani bridge, nie wywołują rebuild i nie tworzą żądania restartu.
- Card UI ma niezależną wersję zapisywaną w `/data/card_ui_version`; wzorce kart mogą być aktualizowane przez trwały `/data/ui_updates`.
- Aktualizacja samych kart może automatycznie zsynchronizować aktywną kartę Lovelace przez WebSocket i działa bez restartu Home Assistant oraz bez restartu Raspberry Pi.
- Pełne aktualizacje nadal zachowują backup, SHA-256, health-check i Restart Manager.
- Dodano ochronę: paczka `dashboard_only` jest odrzucana, jeśli deklaruje restart inny niż `none` albo zawiera niedozwolone pliki wykonawcze.

## 2.8.5 — AI Prediction Popup + Delta (2026-10-24)
- Kafelek **Predykcja AI** otwiera po dotknięciu 24-godzinny wykres ApexCharts w oknie Browser Mod zamiast stale zajmować miejsce na głównym dashboardzie.
- Wykres pokazuje **Predykcję AI**, **Bazę regulatora**, **PWM fizyczny** oraz **AI Delta**; AI Delta korzysta z osobnej prawej osi, aby małe korekty były czytelne przy skali PWM 0–100%.
- Długie przytrzymanie kafelka nadal otwiera standardowe `more-info`.
- Synchronizacja Card UI została podniesiona do **2.8.5**; pełna lokalna paczka ma spójne metadane wersji i jest wykrywana przez lokalny skaner ZIP jako aktualizacja z 2.8.4.
- Bez zmian w AI Cooling, Adaptive PWM, kwalifikacji próbek, modelu oraz zapisanych danych uczenia.
- Popup wymaga zainstalowanych kart **ApexCharts Card** oraz **Browser Mod** w Home Assistant.

## 2.8.4 — AI Prediction History (2026-10-24)
- Dodano osobne sensory liczbowe `sensor.sbc5_ai_prediction_pwm`, `sensor.sbc5_ai_baseline_pwm`, `sensor.sbc5_ai_correction_pwm`, `sensor.sbc5_ai_physical_pwm` i `sensor.sbc5_ai_confidence` z `state_class: measurement`, aby Home Assistant Recorder mógł trwale zapisywać historię AI.
- Główna karta diagnostyczna otrzymała natywny wykres **Historia predykcji AI · 24 h** pokazujący predykcję modelu, bazę regulatora i fizyczne PWM.
- Kafelek **Predykcja AI** jest powiązany z encją predykcji; dotknięcie otwiera `more-info` z historią tej wartości.
- Historia zaczyna się od momentu instalacji 2.8.4; istniejące próbki/model AI nie są resetowane ani modyfikowane.
- Bez zmian w algorytmach AI Cooling, Adaptive PWM, kwalifikacji próbek i ograniczeniach bezpieczeństwa.

## 2.8.3 — Runtime App Routing Recovery (2026-10-23)
- Naprawiono przekazywanie poleceń z kanonicznego pakietu Home Assistant do faktycznie uruchomionej instancji aplikacji podczas/po migracji namespace.
- Wszystkie akcje `hassio.app_stdin` wybierają teraz `runtime_app_slug` publikowany przez SBC5 zamiast sztywnego `local_sbc5_control_center`, z bezpiecznym fallbackiem do `local_rpi5_fan_manager`.
- Natywna encja Update również korzysta z wykrytego runtime slug i automatycznie próbuje drugi dozwolony slug, jeśli pierwszy nie jest zainstalowany.
- Instalator po odświeżeniu lokalnego Store potrafi zainstalować i uruchomić `local_sbc5_control_center`, gdy źródła kanoniczne są już przygotowane, ale tożsamość aplikacji nie jest jeszcze zainstalowana; w przeciwnym razie wykonuje normalny rebuild.
- Zachowano poprawkę AI Quality Window z 2.8.2 i wszystkie dotychczasowe dane/model AI.

## 2.8.2 — AI Quality Window Recovery (2026-10-23)

- Naprawiono regresję, przez którą AI było oceniane co 30 s przy wymaganiu minimum 4 punktów w 60-sekundowym oknie temperatury; takie okno nie mogło osiągnąć stanu `ready`.
- Evaluator AI działa teraz w każdym cyklu Adaptive PWM (~10 s), natomiast zapis obserwacji treningowych pozostaje ograniczony do ~30 s, więc nie zwiększa się tempo uczenia ani zapisów modelu.
- Zachowano istniejący model, obserwacje i próbki jakościowe — aktualizacja nie resetuje danych AI.
- Diagnostyka karty pokazuje liczbę punktów i czas okna temperatury oraz prawidłowo wyświetla zakres PWM równy `0 pp`.
- Card UI i wersja pakietu zostały zsynchronizowane do **2.8.2**.

## 2.8.1 — Card UI Version Sync (2026-10-23)

- Podniesiono wersję głównej karty Lovelace oraz karty aktualizacji do **2.8.1**, zgodnie z wersją aplikacji.
- `config_ui.py` i `dashboard_sync.py` pobierają oczekiwaną wersję karty z wersji wydania aplikacji (`/release.json`, z dodatkowym przekazaniem `SBC5CC_APP_VERSION` z `run.sh`) zamiast utrzymywać niezależny, ręcznie wpisany numer Card UI.
- Po aktualizacji karta **2.7.3** jest prawidłowo oznaczana jako wymagająca synchronizacji, a po podmianie jako **Card UI v2.8.1 · AKTUALNA**.
- Zachowano dotychczasowy bezpieczny przepływ synchronizacji: wykrycie → backup Lovelace → zapis przez sesję administratora HA → weryfikacja → rollback przy błędzie.
- Bez zmian w algorytmach AI Cooling, Adaptive PWM, kalibracji, CPU Profile Manager i telemetrii.

## 2.8.0 — Runtime Quality, Documentation & Quick Setup (2026-10-22)

### Runtime / optymalizacja
- Wprowadzono **monotoniczny priorytet restartów**: `host > home_assistant > app > none`. Trwające żądanie pełnego restartu Raspberry Pi nie może już zostać opisane ani zastąpione słabszym restartem Home Assistant podczas aktualizacji.
- Ograniczono powtarzalne logi wykrywania `notify.mobile_app_*`: ten sam wynik wykrywania jest raportowany raz na runtime zamiast przy każdym wywołaniu ścieżki powiadomień.
- Pasywny odczyt opcjonalnego katalogu Supervisor `/addons` jest teraz **quiet/best-effort**. Brak tego endpointu nie zaśmieca logów `HTTP 400` i nie wpływa na lokalne aktualizacje ZIP.
- Naprawiono historyczne aliasy katalogów aktualizacji: runtime ponownie rozpoznaje `/config/rpi5_control_center_updates/` oraz `/config/rpi5_fan_manager_updates/` obok kanonicznego `/config/sbc5_control_center_updates/`.
- Naprawiono **podwójne liczenie paczek** w statusie retencji/cleanup: Config UI agreguje teraz unikalne katalogi zamiast dwukrotnie skanować kanoniczną ścieżkę.
- Legacy katalogi aktualizacji są migrowane, ale nie są ponownie tworzone przy każdym starcie; puste aliasy są usuwane best-effort.

### Dokumentacja / UX projektu
- Przebudowano **Info / README** pod aktualny stan aplikacji: CPU Profile Manager, Boot Verification, Lovelace OC, telemetria 4 rdzeni, Adaptive PWM Sign Guard, lokalne AI i Update Health Check.
- Przebudowano **Dokumentację** do aktualnej architektury 2.8.0 oraz dodano sekcję szybkiego uruchomienia.
- Dodano osobny `docs/QUICK_SETUP.md` z minimalną ścieżką instalacja → host access → chłodzenie → karta → CPU/OC → weryfikacja restartu.
- Uporządkowano główny changelog: usunięto zduplikowane nagłówki, błędną kolejność 2.7.x i powtarzające się wpisy; pełną historię zachowano w archiwum.

### Bez zmian w algorytmach bezpieczeństwa
- CPU Profile Manager Single Source of Truth, Boot Verification retry/fallback, Adaptive PWM Sign Guard, bounded trim ±12 pp, slew limiter, kalibracja i AI Cooling pozostają funkcjonalnie zgodne z 2.7.3.
- **Card UI pozostaje 2.7.3** — w tym wydaniu nie zmieniono struktury karty Lovelace.

## 2.7.3 — Lovelace CPU/OC Profiles + 4-Core Clocks (2026-10-22)
- Dodano na karcie diagnostycznej aktualny profil CPU/OC, saved/runtime MHz i stan restartu/Boot Verification.
- Dodano bezpieczny wybór presetów CPU/OC z Lovelace przez CPU Profile Manager.
- Dodano osobne kafelki CPU0–CPU3 z częstotliwością i obciążeniem, bez zwiększania częstotliwości próbkowania.
- `Advanced` pozostawiono wyłącznie w interfejsie WWW.

## 2.7.2 — Boot Verification Retry/Fallback + Trim Decay (2026-10-22)
- Naprawiono odczyt `active_max` po restarcie hosta i dodano do 5 prób oraz fallback `cpuinfo_max_freq` / `policy0/scaling_max_freq`.
- Stary fałszywy Repair może zostać zamknięty na tym samym bootowaniu po poprawnej weryfikacji.
- Deadband trim decay przyspieszono do około 1 pp / 10 s z zachowaniem Sign Guard i slew-limitera.

## 2.7.1 — CPU Profile Single Source of Truth & Boot Verification (2026-10-22)
- `config_cpu_profile` stał się jedynym źródłem prawdy dla presetów: 2500 / 2600 / 2800 / 3000 MHz.
- Dodano trwały `/data/cpu_profile_state.json` oraz ochronę przed destrukcyjnym `factory` podczas startupu.
- Restart hosta dla CPU jest zamykany dopiero po potwierdzeniu zapisu i runtime max.
- WWW pokazuje stan `Aktywny / Oczekuje na restart / Niespójność`.

## 2.7.0 — CPU Profile Commit + Adaptive Trim Sign Guard (2026-10-22)
- Profile CPU/OC zaczęły zapisywać dedykowany `sbc5cc-cpu-profile.txt` niezależnie od ogólnego Config.txt Managera.
- Realna zmiana profilu CPU wymusza `restart=host`.
- Dodano Adaptive Trim Sign Guard i usunięto rekonstrukcję trimu, która mogła powodować skoki `+12 → -12 pp`.

## 2.6.35 — Safe CPU OC Profiles & Advanced Guardrails (2026-10-22)
- Dodano presety Factory / 2500 / 2600 / 2800 / 3000 MHz oraz osobny tryb Advanced.
- Presety pozostawiają napięcie pod kontrolą firmware/DVFS i nie wymuszają `force_turbo`.
- Dodano limity bezpieczeństwa i walidację ustawień ręcznych.

## 2.6.34 — Post-Migration Stabilization & Performance (2026-10-22)
- Wyłączono zbędne ponawianie Namespace Guard po `COMPLETE`.
- Zredukowano koszt wolnej telemetrii i diagnostyki przy zachowaniu realtime chłodzenia/Adaptive PWM.
- Ustabilizowano finalny namespace `sbc5_control_center`.

## 2.6.33 — Final Namespace Cutover (2026-10-22)
- Zakończono migrację do natywnego `local_sbc5_control_center` i canonical bridge `sbc5_control_center`.
- Dodano deterministyczny handoff, cleanup legacy i paczki instalacyjne App/HACS/Installation Kit.

## 2.6.0–2.6.32 — Adaptive PWM, AI Grid, Mobile UI, Publishing
Najważniejsze etapy tej serii: Curve-Anchored Adaptive PWM ±12 pp, seamless handoff, AI workload buckets i grid advisor, responsywny Mobile UI, synchronizacja kart, lokalny updater z health-checkiem oraz migracja/publication tooling dla SBC5.

## 2.0.0–2.5.x — Modularizacja i AI Cooling
Seria wprowadziła modularną kartę diagnostyczną, rozdzielenie Info/Dokumentacji/CHANGELOG, lokalny model AI Cooling, wydajniejszą telemetrię wielordzeniową oraz kolejne zabezpieczenia regulatora.

## 1.x — Fundament projektu
Pierwsza generacja obejmowała host access, Dynamic Config UI, krzywe Active Coolera, kalibrację PWM/RPM, Restart Manager, bridge Home Assistant, lokalne aktualizacje i kolejne kroki migracji nazw/namespace.
