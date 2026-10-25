## 2.7.1 — CPU Profile Single Source of Truth & Web UI Verification (2026-10-22)

## 2.7.3 — Lovelace CPU/OC Profiles + 4-Core Clocks

- **Karta YAML:** dodano aktualny profil CPU/OC, zapisane i aktywne MHz oraz stan Boot Verification/restartu.
- **Sterowanie z Lovelace:** nowy helper profilu CPU/OC i bezpieczny przycisk zastosowania presetów Factory / 2500 / 2600 / 2800 / 3000 MHz.
- **Telemetria 4 rdzeni:** karta pokazuje osobno bieżące MHz i obciążenie CPU0–CPU3, wykorzystując istniejącą telemetrię bez zwiększania częstotliwości próbkowania.
- **CPU Profile Manager:** nowa komenda `set_cpu_profile` zapisuje wybór przez trwały Single Source of Truth i korzysta z istniejącego Restart Manager + Boot Verification.
- **UI Card Sync:** Card UI podniesione do 2.7.3; wzorzec JSON i YAML są synchronizowane.
- Mechanizmy Boot Verification 2.7.2, Sign Guard i deadband trim decay pozostają bez zmian.

## 2.7.2 — CPU Boot Verification Retry/Fallback

- **Boot Verification fix:** replaced the invalid `read_cpu_freq max` call with the host-aware `read_cpu_frequency_bound_khz max` path used by telemetry.
- **Retry + fallback:** verification retries up to 5 times and falls back to `cpuinfo_max_freq` / policy0 `scaling_max_freq` before reporting `active_max=unknown`.
- **Self-healing Repairs:** a CPU marker that previously failed verification is rechecked on the same host boot, so a valid profile can close the stale Repair after updating the app without another unnecessary reboot.
- **Adaptive PWM:** deadband trim leakage is accelerated from ~30 s to ~10 s per 1 pp while preserving sign guard, curve anchoring and slew limiting.
- **Web UI:** CPU profile layout and requested/saved/runtime status model retained; version/status text updated for 2.7.2.

- **CPU Single Source of Truth:** `config_cpu_profile` is authoritative for presets; `mild/balanced/performance/experimental` generate 2500/2600/2800/3000 MHz directly and never depend on stale `config_cpu` fields.
- **Persistent CPU Profile State:** `/data/cpu_profile_state.json` survives app restarts and protects the requested profile from transient/default `factory` values during startup.
- **Factory Destructive Guard:** startup/default `factory` with `explicit=false` can no longer remove an existing SBC5 CPU profile; Factory removal requires an explicitly persisted request.
- **Boot Verification Guard:** `restart=host` for CPU changes is cleared only after the new boot confirms the expected saved `arm_freq` and active maximum frequency. A failed verification keeps Repairs active.
- **Native Config Compatibility:** the Supervisor Configuration tab may leave manual CPU fields at `auto`; preset mapping no longer depends on those fields.
- **Web UI Verification:** CPU card now shows requested profile plus `Aktywny`, `Oczekuje na restart` or `Niespójność` from saved/runtime telemetry.
- Adaptive PWM Sign Guard from 2.7.0 is retained unchanged.

## 2.7.0 — 2026-10-22

- **CPU Profile Commit:** profile CPU/OC są zapisywane niezależnie od ogólnego Config.txt Managera do dedykowanego `sbc5cc-cpu-profile.txt`; `Balanced` zapisuje `arm_freq=2600`.
- **Host Restart Enforcement:** każda realna zmiana profilu CPU tworzy backup, weryfikuje zapis i ustawia `restart_required=host`; Factory usuwa wyłącznie wpisy CPU należące do SBC5.
- **Ownership migration:** ogólny `sbc5cc-managed.txt` nie zarządza już kluczami CPU; przy pierwszym commicie stare wpisy CPU należące do SBC5 są bezpiecznie usuwane z tego pliku.
- **Adaptive Trim Sign Guard:** trim nie może mieć przeciwnego znaku względem błędu temperatury poza deadbandem; usunięto rekonstrukcję trimu z `controller_state-curve_state`, która mogła powodować skoki `+12 -> -12`.
- **Anti-overshoot:** w deadbandzie trim jest wygaszany znakowo o 2 pp, a neutralny leak działa co około 30 s; istniejący slew limiter pozostaje bez zmian.

## 2.6.35 — Safe CPU OC Profiles & Advanced Guardrails (2026-10-22)

- Dodano profile CPU dla Raspberry Pi 5: **Fabryczny**, **OC Łagodny 2500 MHz**, **OC Zbalansowany 2600 MHz**, **OC Wydajność 2800 MHz** i **OC 3.0 GHz (eksperymentalny)**.
- Gotowe profile pozostawiają napięcie pod kontrolą firmware/DVFS (`over_voltage=auto`, `over_voltage_delta=auto`) i nie wymuszają `force_turbo`.
- Dodano osobny tryb **Zaawansowany** z ręcznym `arm_freq`, `arm_freq_min`, `over_voltage_delta`, `force_turbo` i `temp_limit`.
- Dodano twarde limity bezpieczeństwa UI/backend: CPU maks. 3000 MHz, `over_voltage_delta` 0–50000 µV, `temp_limit` 70–85°C; `arm_freq_min` nie może przekroczyć `arm_freq`.
- `over_voltage`, `over_voltage_min` i `initial_turbo` przeniesiono do ostrzeganej sekcji Legacy.
- Dodano OC Safety Check przed zapisem dla profilu 3.0 GHz, `force_turbo=1`, ręcznego `over_voltage`, undervoltage i wysokiej bieżącej temperatury.
- Migracja z 2.6.34 zachowuje istniejące ręczne wartości: znane konfiguracje mapowane są na profil, pozostałe automatycznie trafiają do trybu Zaawansowanego.
- Nie zmieniano treści Info/README/Dokumentacji ani Card UI; wersja karty Lovelace pozostaje 2.6.34.

## 2.6.34 — Post-Migration Stabilization & Performance

- wyłącza Namespace Guard po trwałym `phase=COMPLETE`, dzięki czemu po każdym restarcie nie uruchamia ponownie health-checków i cleanupu migracyjnego;
- blokuje ponowną instalację `sbc5_fan_manager_bridge` po zakończonej migracji i usuwa ewentualną pozostałość przy starcie;
- utrzymuje realtime chłodzenia 5 s, Adaptive PWM 10 s i AI evaluator 30 s bez zmian;
- redukuje koszt diagnostyki: PMIC 30 s, rozszerzona telemetria systemowa 60 s, polling Config UI 10 s;
- przy braku host access stosuje diagnostyczny backoff dla ciężkich odczytów zamiast częstych bezskutecznych prób;
- czyści natywne karty z odwołań do starego Supervisor sluga i starego katalogu aktualizacji;
- zachowuje pełny host access (`full_access`, `host_pid`, `SYS_ADMIN`, `SYS_PTRACE`) oraz wszystkie ustawienia Adaptive PWM, AI, custom1 i kalibracji.

# Changelog

## 2.6.33 — Final Legacy Purge & Deterministic Supervisor Cutover
- Zmiana sluga nie jest już traktowana jak zwykła aktualizacja: legacy coordinator wystawia `local_sbc5_control_center` jako osobną aplikację lokalnego Store i czeka na jej wykrycie przed instalacją.
- Stan AI, kalibracji, krzywej i ownership jest eksportowany do wspólnego stagingu; target startuje w standby i nie steruje PWM przed handoffem.
- Cleanup po zdrowym handoffie usuwa z aktywnego HA `local_rpi5_fan_manager`, katalogi `/config/rpi5_*`, legacy bridge/package i stare katalogi update, zachowując pełny backup migracyjny.
- Legacy config entries są usuwane przez oficjalny endpoint Core (best effort); `.storage` nie jest modyfikowane ręcznie.
- Końcowa weryfikacja wymaga działającego `local_sbc5_control_center` 2.6.33 i braku zainstalowanego legacy sluga.

## 2.6.33 — Final Supervisor Namespace Migration, CPU Optimization & SBC5 Installation Packages

- Kończy migrację Supervisor: `local_rpi5_fan_manager` jest zatrzymywany i odinstalowywany dopiero po potwierdzonym zdrowiu `local_sbc5_control_center`.
- Naprawiono cleanup źródeł: archiwizowane są oba historyczne katalogi `rpi5_fan_manager` i `rpi5_control_center`, dzięki czemu stary slug nie wraca po `addons/reload`.
- Dla instalacji z wcześniejszym markerem `COMPLETE` dodano idempotentny Final Namespace Repair 2.6.33, który aktualizuje native app i kończy zaległy cleanup bez ponownej migracji danych AI/kalibracji.
- Legacy `rpi5_control_center_bridge` / `rpi5_fan_manager_bridge` są wycofywane po zdrowym native handoff; pozostaje jedna aktywna integracja `sbc5_control_center`.
- CPU: główny coordinator telemetrii HA działa co 10 s (realtime pozostaje 5 s), AI evaluator co 30 s przy regulatorze Adaptive PWM nadal co 10 s, Config UI dirty-token polling co 5 s, a `multicore_workers=auto` ma limit 2 workerów.
- Przywrócono kanoniczne paczki instalacyjne nazwane `sbc5...`: local app, HACS integration i pełny installation kit.
- Native updater akceptuje od kolejnych wersji manifest `slug=sbc5_control_center`; 2.6.33 zachowuje jednorazową zgodność z przejściowym manifestem dla aktualnie zainstalowanego legacy sluga.
- Bez zmian w algorytmie Curve-Anchored Adaptive PWM, trim ±12 pp, safety handoff i zapisanym modelu AI.

## 2.6.30 — Update Card Version Synchronization & Release Guard Hotfix

- Zsynchronizowano wersję głównej karty i karty aktualizacji do `Card UI v2.6.30`.
- Wszystkie osadzone `update_status_card.json`, łącznie z kopiami `successor_source`, są generowane z jednego kanonicznego `dashboard/update_status_card.yaml`.
- Synchronizator nie odrzuca już karty update z powodu pozostawionego markera `Update Card v2.6.25`.
- Walidator wydania wymaga identycznej wersji w `CARD_UI_VERSION`, `CARD_VERSION`, obu kartach YAML i wszystkich osadzonych kartach JSON.
- Dodano guard wykrywający stare znaczniki `Update Card v*` / `SBC5CC *` inne niż bieżąca wersja.
- Bez zmian w Adaptive PWM, AI Cooling, telemetrii, krzywej `custom1` i dwufazowym Update Health Check.

# 2.6.26 — Recovery / Startup Hotfix

- Naprawiono krytyczny błąd Bash `APP_VERSION = "2.6.25"`, który powodował `APP_VERSION: command not found` i `unbound variable` po aktualizacji.
- Update Guard sprawdza teraz nie tylko `bash -n`, ale również semantyczną zgodność `APP_VERSION` i `REQUIRED_PACKAGE_VERSION` z `update-manifest.json`.
- Lokalny updater nie oznacza paczki jako `install_success` przed uruchomieniem nowego runtime; ZIP jest finalizowany dopiero po przejściu checkpointu startowego nowej wersji.
- Blue/green Migration Coordinator waliduje successor `run.sh` przed zmianą źródeł i wymaga, aby target 2.6.26 utrzymał stan `started/running` przed dalszą migracją.
- Native runtime akceptuje tę samą kanoniczną paczkę aktualizacyjną (`slug=rpi5_fan_manager`, `target_slug=sbc5_control_center`).
- AI Cooling zachowuje pełną diagnostykę, ale nie loguje każdej zmiany krótkotrwałego powodu odrzucenia próbki; heartbeat pozostaje co około 60 s, a próbki qualified są logowane osobno.
- Adaptive PWM, bounded trim ±12 pp, slew limiter, seamless handoff, kalibracja i zebrane dane AI pozostają bez zmian.

# 2.6.25 — UI State, Lovelace Verification & Command Routing Recovery

- Naprawiono Config UI: backend `/api/state` i Card UI raportują rzeczywistą wersję 2.6.25, bez zaległego 2.6.23.
- Wszystkie kopie `sbc5_control_center` (root, migration assets i successor) mają zsynchronizowany `APP_VERSION=2.6.25`; koordynator nie może już po restarcie skopiować starszej integracji 2.6.21.
- Weryfikacja synchronizacji Lovelace jest odporna na normalizację obiektów przez Home Assistant: sprawdzana jest wersja, typ karty i krytyczne referencje SBC5, zamiast pełnej równości JSON.
- Package przejściowy kieruje `hassio.app_stdin` do faktycznie zainstalowanego `local_rpi5_fan_manager`; po udanym handoffie native package przełącza routing na `local_sbc5_control_center`.
- Koordynator wykonuje dodatkowy reload Store przed instalacją natywnej aplikacji i zapisuje odpowiedź instalatora do logu migracji.
- Adaptive PWM, AI Cooling, kalibracja, krzywa i dane treningowe pozostają bez zmian.

# 2.6.24 — Config Entry & Package Recovery Hotfix

- Naprawiono `NameError: APP_VERSION is not defined` w `sbc5_control_center.async_setup_entry`.
- Dodano brakujący `sensor.sbc5_package_version`, dzięki czemu Restart Manager może potwierdzić rzeczywistą wersję package.
- Migracja entity registry jest teraz niedestrukcyjna: legacy `rpi5_*` pozostają aktywne aż do potwierdzenia zdrowych encji `sbc5_*`.
- Stare config entries i wpisy registry są usuwane dopiero po pozytywnym health-checku `sensor.sbc5_cpu_temperature`, `sensor.sbc5_fan_rpm` i `sensor.sbc5_control_center_update`.
- Runtime Adaptive PWM, AI Cooling, kalibracja oraz geometria krzywej pozostają bez zmian.

# 2.6.23 — Native Integration Bootstrap Recovery

- Naprawiono krytyczny błąd migracji namespace: pełny `packages/sbc5_control_center.yaml` nie jest już nadpisywany bootstrapem integracji.
- Bootstrap `sbc5_control_center` używa osobnego `packages/sbc5_control_center_bridge.yaml`.
- Koordynator migracji aktywuje nową domenę przed oczekiwaniem na encje i wymaga `integration_ready.ready=true`.
- Nowy bridge korzysta z `sensor.rpi5_control_center_host_telemetry` jako fallbacku podczas przejścia.
- Legacy config entry jest usuwany dopiero po potwierdzeniu zdrowych encji `sbc5_*`.
- Post-update nie uznaje już starego bridge za dowód zakończenia migracji SBC5.
- Logika Adaptive PWM/AI nie została zmieniona.



## 2.6.29 — Legacy Bridge Compatibility Cleanup Hotfix

- Naprawiono `NameError` w `rpi5_control_center_bridge`: dodano brakujące stałe ścieżek `NAMESPACE_COMPAT_SHARED_TELEMETRY_PATH` i `NAMESPACE_COMPAT_REALTIME_TELEMETRY_PATH`.
- Legacy bridge obsługuje równolegle telemetrię `/config/rpi5_control_center` i `/config/sbc5_control_center` podczas migracji namespace.
- Walidator wydania wykrywa teraz użycie niezdefiniowanych stałych UPPER_CASE w modułach telemetrii legacy i wykonuje bezpośredni smoke-import tych modułów.
- Bez zmian w Adaptive PWM, AI Cooling, krzywej `custom1`, seamless handoff i dwufazowym Update Health Check.

## 2.6.28 — Native Telemetry Recovery & End-to-End Health Hotfix

- Naprawia natywne sensory SBC5 po migracji namespace: integracja czyta teraz także `/config/rpi5_control_center/{telemetry,realtime}.json`.
- Canonical host relay akceptuje `fan_pwm` oraz historyczne `fan_pwm_raw`; brak różnicy nazwy pola nie odrzuca już całego snapshotu.
- Realtime sensory CPU/wentylatora mają dodatkowy fallback bezpośrednio do canonical/legacy host relay.
- Active/requested/profile-activation są publikowane równolegle jako `sbc5_*` i `rpi5_*`, a karta ma fallback migracyjny.
- Card UI podniesiono do 2.6.28, aby synchronizacja dashboardu rozpoznawała nową wersję.
- Update Health Check ma Phase A (runtime) i Phase B (po restarcie HA: relay + natywne sensory); ZIP jest usuwany dopiero po pełnym PASS.
- Adaptive PWM, bounded trim ±12 pp, seamless handoff i model AI pozostają bez zmian algorytmicznych.

## 2.6.27 — Namespace Relay & UI Synchronization Hotfix

- Publikuje telemetrykę hosta równolegle jako `sensor.sbc5_control_center_host_telemetry`, `sensor.rpi5_control_center_host_telemetry` i `sensor.rpi5_fan_manager_host_telemetry`.
- Publikuje stan aktualizacji równolegle jako `sensor.sbc5_control_center_update` oraz aliasy legacy, z atrybutem `runtime_app_slug`.
- Skrypty `hassio.app_stdin` wybierają działający slug podczas migracji namespace zamiast zakładać obecność `local_sbc5_control_center`.
- Karty Lovelace kierują do rzeczywiście zainstalowanego legacy sluga do czasu zakończenia blue/green handoff.
- Zachowuje Adaptive PWM, bounded trim ±12 pp, seamless handoff i trwały model AI bez zmian algorytmicznych.

## 2.6.23 — Migration UI & Card Sync Hotfix

- Naprawiono fałszywy rollback synchronizacji Lovelace: zapisane karty są teraz porównywane semantycznie z kanoniczną kolejnością kluczy zamiast surowego `JSON.stringify()`.
- Detektor karty głównej rozpoznaje zarówno legacy `rpi5_*`, jak i natywne `sbc5_*` encje.
- Detektor opcjonalnej karty aktualizacji rozpoznaje stare i nowe sensory oraz nie wymaga już kruchego tekstu `Aktualizacje lokalne`.
- `api/state` publikuje rzeczywistą wersję aplikacji 2.6.23; usunięto zaległe `2.6.19`.
- `dashboard_sync.py` i Card UI zostały ujednolicone do 2.6.23; usunięto zaległe `2.6.16`.
- Kafel zgodności platformy nie zawiera już twardo wpisanej wersji produktu; pokazuje zgodność z wymaganiami SBC5 Control Center.
- Naprawiono komunikat ścieżki legacy aktualizacji: dla 2.6.19 i starszych wskazuje `/config/rpi5_control_center_updates/`.
- Logika chłodzenia, Adaptive PWM, AI i blue/green namespace migration pozostają bez zmian.

## 2.6.21 — 2026-10-22 — Full Namespace Migration Coordinator

- Dodano automatyczną migrację blue/green z technicznej tożsamości `rpi5_*` do natywnego namespace **SBC5**.
- Nowa aplikacja ma slug `sbc5_control_center` (Supervisor: `local_sbc5_control_center`), a nowa domena integracji to `sbc5_control_center`.
- Nowe encje, helpery, skrypty i sensory używają prefiksu `sbc5_*`; kanoniczny package to `packages/sbc5_control_center.yaml`.
- Migrator instaluje nową aplikację obok starej, kopiuje options i trwały stan AI/kalibracji, uruchamia nową integrację i synchronizuje helpery przed przejęciem sterowania.
- Handoff PWM jest transakcyjny: legacy pozostaje właścicielem do `READY_FOR_HANDOFF`, następnie native przejmuje stan ownera i potwierdza trzy kolejne health-checki. W razie błędu `control_owner` wraca do `legacy`.
- Po sukcesie stara aplikacja `local_rpi5_fan_manager` jest zatrzymywana i odinstalowywana z zachowaniem konfiguracji, a jej źródło trafia do `.sbc5_migration_backup`.
- `packages/rpi5_control_center.yaml` zostaje automatycznie zastąpiony lekkim compatibility shimem: stare `rpi5_*` odwołania nadal działają jako aliasy/forwardery do `sbc5_*`.
- Integracja `sbc5_control_center` przejmuje customizacje encji z `rpi5_control_center_bridge`, usuwa stary config entry dopiero po aktywacji nowej domeny i zapisuje markery migracji.
- Brak zmian w Curve-Anchored Adaptive PWM, AI Qualified Sampling v3 i zasadach bezpieczeństwa termicznego poza mechanizmem ownership handoff.


## 2.6.20 — 2026-10-22 — SBC5 namespace compatibility migration

- Naprawiono migrację po rebrandingu: aplikacja obsługuje teraz kanoniczny katalog lokalnych aktualizacji `/config/sbc5_control_center_updates/` oraz równolegle legacy `/config/rpi5_control_center_updates/`.
- Przy starcie zawartość starszych katalogów aktualizacji jest bezpiecznie scalana do nowego katalogu SBC5; istniejące pliki docelowe mają pierwszeństwo.
- Sensor aktualizacji publikuje `local_update_dir=/config/sbc5_control_center_updates/` i osobny `legacy_local_update_dir` dla diagnostyki migracji.
- Config UI oraz odczyt release notes uwzględniają oba namespace podczas okresu przejściowego.
- Zachowano `slug: rpi5_fan_manager`, domenę `rpi5_control_center_bridge`, encje `rpi5_*`, package `rpi5_control_center.yaml` oraz źródłowy katalog kompatybilności. Są to stabilne identyfikatory techniczne i ich zmiana zerwałaby istniejące instalacje.
- Dla aktualizacji z 2.6.19 i starszych pierwsza paczka 2.6.20 nadal musi być umieszczona w `/config/rpi5_control_center_updates/`; dopiero runtime 2.6.20 zna nowy katalog SBC5.
- Brak zmian w regulatorze Curve-Anchored Adaptive PWM, AI Qualified Sampling v3, konfiguracji OC i logice chłodzenia.

## 2.6.19 — SBC5 Public Brand & Legal Publication

- Publiczna marka projektu została zmieniona na **SBC5 Control Center** z opisowym podtytułem **for Raspberry Pi 5**.
- Zachowano wszystkie techniczne domeny, encje, katalogi i identyfikatory `rpi5_*` jako warstwę zgodności wstecznej — bez migracji entity_id i bez łamania automatyzacji.
- Zaktualizowano Info/README oraz pełną Dokumentację PL/EN do stanu 2.6.19.
- Dodano `TRADEMARKS.md` i `LEGAL.md`; zaktualizowano `NOTICE`, `LICENSE_AUDIT.md`, `THIRD_PARTY_NOTICES.md` i zapisy Apache-2.0.
- Wprowadzono jawny disclaimer niezależności projektu oraz opisowe użycie „for Raspberry Pi 5”; branding nie używa oficjalnego logo Raspberry Pi.
- Karty Lovelace zostały prze-brandowane do SBC5 i podniesione do **Card UI 2.6.19**; synchronizacja rozpoznaje również dotychczasową kartę update z nazwą RPi5, aby umożliwić migrację in-place.
- Zaktualizowano branding aplikacji, bundled bridge, HACS assets i Dynamic Config UI.
- Logika chłodzenia, Qualified Sampling v3, Curve-Anchored Adaptive PWM, AI Assist i Config.txt Manager pozostają funkcjonalnie bez zmian względem 2.6.18.

## 2.6.18 — Brand Identity Refresh

- Zastosowano nową, spójną identyfikację wizualną RPi5 Control Center w aplikacji Home Assistant, bundled bridge, bridge HACS/Marketplace oraz paczkach publikacyjnych.
- Nowy znak wykorzystuje autorską ilustrację płytki SBC z Active Coolerem i nie reprodukuje oficjalnego znaku maliny Raspberry Pi.
- Wygenerowano zsynchronizowane warianty 128×128, 256×256 i 512×512 oraz master brand asset.
- Zachowano Apache-2.0 i dotychczasowe informacje o niezależności projektu; nie zmieniono logiki chłodzenia, AI, Config.txt Managera ani Card UI (pozostaje 2.6.16).
- Numer aplikacji i bridge podniesiono do 2.6.18, aby branding został poprawnie dostarczony przez aktualizację.

## 2.6.17 — GitHub/HACS Publishing Preparation

- Przygotowano architekturę dystrybucji publicznej: osobne repozytorium aplikacji Home Assistant i osobne repozytorium bridge dla HACS/Home Assistant Marketplace.
- Dodano mechanizm własności bridge: marker `.hacs_managed` powoduje, że aplikacja nie nadpisuje integracji zarządzanej zewnętrznie przy starcie ani podczas lokalnej aktualizacji ZIP.
- Bundled bridge pozostaje pełnym fallbackiem dla instalacji bez HACS/Marketplace.
- Zsynchronizowano publiczne README/DOCS z wersją 2.6.17 i opisano migrację do modelu GitHub + HACS.
- Dodano do pakietu publikacyjnego `repository.yaml`, `hacs.json`, GitHub Actions, skrypty konfiguracji/preflight i checklistę wydania.
- Logika chłodzenia, Adaptive PWM, Qualified Sampling v3, AI Grid Advisor i obie karty Lovelace pozostają funkcjonalnie bez zmian względem 2.6.16; Card UI pozostaje 2.6.16.

## 2.6.16 — Integration Branding & Logo Fix

- Dodano lokalny branding Home Assistant dla `rpi5_control_center_bridge` zgodny z HA 2026.3+: `brand/icon.png`, `icon@2x.png`, `logo.png` i `logo@2x.png`.
- Branding jest dostarczany również wewnątrz kopii bridge instalowanej przez aplikację, więc aktualizacja/reinstalacja integracji nie usuwa logo.
- Dodano branding także do compatibility bridge `rpi5_fan_manager_bridge`, aby ekran migracyjny/starszy wpis nie pokazywał placeholdera.
- `DeviceInfo` publikuje teraz `sw_version` zgodne z wersją bridge.
- Walidator release sprawdza obecność brandingu oraz wymagane rozmiary 256×256 i 512×512, blokując regresję „icon/logo not available”.
- Logika chłodzenia, Qualified Sampling v3, synchronizacja kart i Automatic Update Package Cleanup pozostają bez zmian względem 2.6.15.
- Info / README / Dokumentacja pozostają bez zmian.

## 2.6.15 — Automatic Update Package Cleanup

- Dodano automatyczną retencję lokalnych paczek aktualizacji, aby `/config/rpi5_control_center_updates` nie rósł bez końca. Domyślnie zachowywane są **2 ostatnie poprawnie przetworzone ZIP-y** i **2 ostatnie nieudane ZIP-y**.
- Cleanup jest wykonywany przy starcie aplikacji, po udanej instalacji i po przeniesieniu wadliwej paczki do `failed/`. Operacja dotyczy wyłącznie plików `*.zip` w `processed/` i `failed/`; nie usuwa backupów konfiguracji, AI, kalibracji, Lovelace ani update backupów.
- Przy błędzie walidacji paczka jest teraz **przenoszona** do `failed/` zamiast kopiowana, dzięki czemu nie pozostaje drugi egzemplarz w katalogu wejściowym i nie jest ponownie skanowana.
- Dynamic Config UI otrzymał ustawienia retencji, status zajętości archiwum oraz ręczną akcję **Wyczyść stare paczki**.
- Zachowano zgodność z `local_package_keep_processed`: po jego wyłączeniu poprawnie zainstalowany ZIP jest usuwany, a istniejące archiwum `processed/` jest czyszczone do zera przy kolejnym cleanupie.
- Logika Control Stability, Qualified Sampling v3, AI Grid Advisor i synchronizacji kart Lovelace pozostaje bez zmian względem 2.6.14.
- Info / README / Dokumentacja pozostają bez zmian.

## 2.6.14 — Control Stability & Qualified Sampling v3

- **Adaptive PWM:** deadband jest teraz rzeczywistym `actuator hold`. W paśmie celu regulator nie śledzi każdego skwantowanego punktu `custom1(T)`; utrzymuje fizyczny PWM i zbliża trim do krzywej maksymalnie o około 1 pp/min. Safety 100% i slew limit pozostają nadrzędne.
- **Curve cache / hot reload:** interpolacja nie przebudowuje `custom1` co 10 s. Proces regulatora buforuje 15 punktów i odświeża je po tokenie `config_ui_reload.request`, zmianie setpointu/ustawień oraz po AI Grid Apply/Clear.
- **Qualified Sampling v3:** kwalifikacja AI używa okna około 60 s, regresji trendu (≤0,60°C/min), rozrzutu temperatury (≤2,0°C), pasma średniej ±1,25°C i zakresu PWM ≤8 pp/30 s. Eliminowany jest fałszywy reject wynikający z pojedynczych skoków sensora 0,5–0,6°C.
- Dodano dwa poziomy jakości: **GOLD** oraz konserwatywnie ważony **QUASI_STEADY**; minimum 30 próbek jakościowych nie zostało obniżone.
- **AI Grid Advisor** wyznacza region zagęszczenia z rozkładu próbek jakościowych, a nie wszystkich obserwacji.
- Status AI rozdziela pokrycie globalne od pokrycia faktycznie używanego zakresu workload; `Predykcja AI` nie udaje modelu przed pierwszą próbką jakościową.
- Ograniczono I/O: `fsync` modelu wykonywany jest przy próbce jakościowej lub checkpointcie ~60 s, mirror statusu maks. co ~30 s; bieżący status pozostaje aktualizowany bez wymuszonego fsync.
- Pełna telemetria została zmniejszona z 5 s do 10 s przy zachowaniu lekkiego toru realtime 5 s. Usunięto podwójny identyczny POST do `sensor.rpi5_control_center_host_telemetry`.
- Ograniczono logowanie AI do zmian stanu/powodu i podsumowania około raz na minutę; usunięto redundantną linię `Fan Write` dla tego samego zapisu Adaptive PWM.
- **Config UI / Lovelace:** dodano wykrywanie i synchronizację `update_status_card`, ale tylko jeżeli karta już istnieje na którymś dashboardzie. Aplikacja nigdy nie dodaje jej automatycznie. Przed podmianą wykonywany jest backup, wielokrotne dopasowania blokują zapis, a wynik jest weryfikowany i ma rollback.
- Info / README / Dokumentacja pozostają bez zmian.

## 2.6.13 — Config UI Runtime Sync

- Naprawiono panel **Konfiguracja**, który nadal zawierał zaszyte oznaczenia `2.6.5` mimo nowszej wersji aplikacji. Numer wersji panelu jest teraz pobierany dynamicznie z backendu.
- Naprawiono status **Kalibracja** w nagłówku Config UI: trwały stan przechowuje mapę w `rpm_map`, a UI oczekiwał `map_points`, przez co gotowa mapa 92-punktowa była prezentowana jako `0 pkt`. Backend normalizuje teraz `map_points = len(rpm_map)` i ma fallback do bieżącego snapshotu telemetrii.
- Status **AI** zachowuje poprawną informację o próbkach jakościowych bieżącego bucketa, ale dodatkowo pokazuje `observations_total`, aby odróżnić brak jakościowych próbek od braku uczenia.
- Naprawiono mechanizm **Sprawdź kartę / Synchronizuj kartę**: frontend nie porównuje już karty do zaszytego `Card UI v2.6.5`; używa wersji wzorca zwracanej przez backend.
- Potwierdzenie synchronizacji karty również pokazuje dynamiczną wersję Card UI.
- Curve-Anchored Adaptive PWM, Quasi-Steady AI Learning, Workload Buckets v2 i AI Grid Apply pozostają bez zmian.
- Info / README / Dokumentacja pozostają bez zmian.

## 2.6.12 — Ingress Navigation Fix

- Naprawiono routing skrótów **Konfiguracja** i **Config.txt** na głównej karcie Lovelace.
- Zamiast strony aplikacji Home Assistant `/config/app/local_rpi5_fan_manager` przyciski otwierają bezpośrednio panel Ingress `/app/local_rpi5_fan_manager`, czyli właściwy webowy interfejs RPi5 Control Center.
- Przycisk **Log** pozostaje przy natywnej trasie Supervisor `/config/app/local_rpi5_fan_manager/logs`.
- Zachowano responsywne kafelki i zabezpieczenia Jinja z 2.6.11.
- Logika Curve-Anchored Adaptive PWM, Quasi-Steady AI Learning, Workload Buckets v2 i AI Grid Apply pozostaje bez zmian.
- Info / README / Dokumentacja pozostają bez zmian.

## 2.6.11 — Responsive UI & Template Safety

- Utwardzono wszystkie odwołania Lovelace do `sensor.rpi5_control_center_host_telemetry`: bezpośrednie `states.sensor...attributes` zastąpiono bezpiecznym `state_attr()` oraz walidacją map dla `ai_cooling`, `grid_suggestion`, `grid_application` i `platform_compatibility`.
- Karta diagnostyczna i karta aktualizacji dostały responsywne siatki `auto-fit`, automatyczne przejście do jednej kolumny na bardzo wąskich ekranach oraz większe kafelki na szerszych ekranach.
- Kafelki w każdym wierszu są rozciągane do równej wysokości; długie opisy zawijają się bez ellipsis i bez wychodzenia poza kartę.
- Dodano osłony szerokości `min-width: 0`, `max-width: 100%`, `box-sizing: border-box` oraz responsywną typografię dla kafelków siatkowych.
- Logika Curve-Anchored Adaptive PWM, Workload Buckets v2, Quasi-Steady AI Learning i AI Grid Apply pozostaje bez zmian względem 2.6.10.
- Info, README i Dokumentacja nie zostały zmienione.

## 2.6.10 — Quasi-Steady AI Learning

- usunięto twardy warunek `controller_action == hold` z kwalifikacji próbek AI; `hold` pozostaje metadanym najwyższej jakości, ale brak hold nie blokuje nauki,
- kwalifikacja działa jako `quasi_steady_v2`: temperatura musi pozostawać w paśmie co najmniej ±1,0°C od celu, trend termiczny ≤0,20°C/min, a zakres fizycznego PWM w oknie 30 s ≤5 pp,
- zachowano wymaganie 30 s stabilnego bucketu Workload v2 i 30 s ciągłej stabilności przed zaliczeniem próbki jakościowej,
- migracja polityki zachowuje wcześniejsze prawidłowe próbki/EMA, ale czyści historyczne liczniki odrzuceń związane ze starym warunkiem hold,
- telemetria AI publikuje teraz `qualification_policy`, `qualification_tier`, `controller_hold`, `current_pwm_percent` i zakres PWM z 30 s,
- karta rozdziela `model`, `baza regulatora`, `AI Δ` i `PWM fiz.`, dzięki czemu predykcja AI nie wygląda jak bezpośredni odczyt końcowego sterowania,
- nie zmieniono architektury Curve-Anchored Adaptive PWM 2.6.9: `custom1(T)` pozostaje bazą, Adaptive ma ±12 pp, a końcowy slew guard pozostaje aktywny,
- zakładki Info/README/Dokumentacja nie zostały zmienione.

## 2.6.9 — Curve-Anchored Adaptive PWM

- przebudowano Adaptive PWM z historycznego akumulatora `controller_state` na regulator zakotwiczony w `custom1(T)`,
- korekta Adaptive jest ograniczona do ±12 punktów procentowych wokół bieżącej wartości krzywej, co eliminuje wind-up do 80–87% w pobliżu setpointu,
- po kalibracji/rebuildzie regulator zachowuje bieżący PWM, ale zbliża się do nowego punktu pracy przez limiter szybkości zamiast skoku np. 78→28%,
- standardowy slew wynosi +3/-4 pp na cykl 10 s, a dla dużego błędu temperatury +5/-5 pp; awaryjne 100% pozostaje natychmiastowe,
- AI Assist nadal jest wtórny wobec klasycznego regulatora i jego wynik przechodzi przez końcowy corridor oraz slew guard,
- telemetria `base_level` reprezentuje teraz bieżącą bazę `custom1(T)`, a log Adaptive pokazuje `curve` i `trim`,
- zachowano Seamless Adaptive PWM Update Handoff, Workload Buckets v2 i wszystkie zabezpieczenia ownership z 2.6.8.

## 2.6.8 — Seamless Adaptive PWM Update Handoff
- Naprawiono źródłową regresję widoczną przy lokalnym update/rebuild: stary proces Adaptive PWM nie oddaje już bezwarunkowo thermal zone kernelowi tuż przed planowaną przebudową aplikacji.
- Przed rebuildem tworzony jest krótkotrwały marker handoff tylko wtedy, gdy `custom1` jest profilem żądanym, cooling device ma `max_state >= 100`, `cur_state` jest zapisywalny i Adaptive PWM faktycznie posiada wyłączne sterowanie.
- Nowa wersja na tym samym `boot_id` waliduje istniejący ownership, zachowuje ostatni bezpieczny PWM i przejmuje regulator bez chwilowego powrotu do fabrycznego kroku około 29%.
- Handoff jest fail-safe: zwykłe zatrzymanie aplikacji, niezgodny boot, przeterminowany marker, brak siatki 1% albo niewłaściwy stan thermal zone nadal powodują oddanie sterowania kernelowi.
- Zachowano rozdzielenie desired/runtime z 2.6.7, Workload Buckets v2 i fail-closed AI Assist.
- Zakładki Info/README/Dokumentacja nie zostały zmienione.

## 2.6.7 — Desired vs Runtime Fan Profile
- Rozdzielono profil żądany przez użytkownika od profilu faktycznie załadowanego przez kernel; `input_select.rpi5_fan_profile` nie jest już nadpisywany stanem runtime.
- `sensor.rpi5_requested_fan_profile` publikuje trwały profil żądany z `/data/last_fan_profile_code`, a `sensor.rpi5_active_fan_profile` pozostaje wyłącznie stanem runtime kernela.
- Dodano `sensor.rpi5_fan_profile_activation` z jednoznacznym stanem `ready` / `pending_host_reboot`, przyczyną rozjazdu i `runtime_max_state`.
- Przy `max_state < 100` kalibracja i Adaptive PWM jawnie logują, że siatka 1% nie jest aktywna i wymagany jest pełny restart hosta po zastosowaniu `custom1`.
- Karta 2.6.7 pokazuje jednocześnie profil żądany, runtime kernela i wymagany restart hosta.
- Nie zmieniono logiki Workload Buckets v2 ani kryteriów termicznych AI. Błąd integracji `roomba`/`roombapy` pozostaje poza zakresem RPi5 Control Center.
- Zakładki Info/README/Dokumentacja nie zostały zmienione.

## 2.6.6 — Adaptive PWM Runtime Reconciliation
- Naprawiono ponowne wejście Adaptive PWM po restarcie aplikacji/HA, gdy kernel zachowuje inne progi niż `custom1`, ale aktywna jest zapisywalna siatka 1% (`max_state >= 100`).
- Regulator przy rozjeździe progów startuje curve-guided z poziomu wynikającego z `custom1`, zamiast dziedziczyć niski stan kernela.
- AI Assist przechodzi fail-closed do `paused`, gdy Adaptive PWM nie ma bezpiecznej kontroli nad wentylatorem.
- Zakładki Info/README/Dokumentacja nie zostały zmienione.

## 2.6.5 — Workload Buckets v2
- Przebudowano klasyfikację obciążenia AI: `idle <10%`, `low 10–30%`, `medium 30–60%`, `high ≥60%` dla 0–100% średniego wykorzystania CPU.
- Workload jest wygładzany w oknie 30 s, klasyfikowany z histerezą ±5 pp i wymaga 30 s stabilności bucketu; usunięto dawny warunek zmiany surowego CPU ≤12 pp.
- Zachowano konserwatywne kryteria termiczne, stabilność PWM i stan `hold`; dodano diagnostykę obserwacji/jakościowych próbek oraz powodów odrzucenia.
- Model przeszedł na schema 5; stare zbiorcze biny workloadu są archiwizowane i zerowane, a historia gęstości temperatury pozostaje zachowana.
- Zakładki Info/README/Dokumentacja nie zostały zmienione.

## 2.6.4 — Native Mushroom Multiline
- Naprawiono faktyczną przyczynę obcinania treści na aktualnych kartach Mushroom: `custom:mushroom-template-card` domyślnie używa `multiline_secondary: false`.
- Wszystkie karty Mushroom w głównej karcie diagnostycznej i karcie aktualizacji mają teraz jawnie `multiline_secondary: true`, dzięki czemu tekst wtórny może natywnie zajmować wiele linii.
- Zachowano dynamiczną wysokość i mobilne odstępy z 2.6.3; nie zmieniono backendu AI Cooling ani AI Grid Apply.
- Zakładki Info/README/Dokumentacja nie zostały zmienione.

## 2.6.3 — Mobile Text Wrap
- Mobile UI nie obcina już treści drugich linii wielokropkiem; teksty Mushroom są zawijane i kafle rosną dynamicznie wraz z treścią.
- Poprawiono sekcje „Postęp według obciążenia”, „AI · sugestia zagęszczenia siatki”, „Zastosuj sugestię”, „Przywróć siatkę Auto” oraz „Aktualizacje lokalne”.
- Dwukolumnowe kafle akcji AI i aktualizacji mają większą minimalną wysokość na ekranach do 600 px, bez ograniczania pełnej treści.
- Kanoniczny YAML i wzorzec Card Sync pozostają identyczne funkcjonalnie; backend AI Grid Apply z 2.6.2 nie został zmieniony.
- Zakładki Info/README/Dokumentacja nie zostały zmienione.

## 2.6.2 — AI Grid Apply
- AI Grid Advisor rozróżnia pewność lokalną od pokrycia modelu dla idle/low/medium/high.
- Dojrzały, skoncentrowany region pracy może otrzymać realne zagęszczenie do 0,25°C, ale tylko gdy jest gęstsze od bieżącej geometrii.
- Dodano bezpieczne „Zastosuj sugestię” i „Przywróć siatkę Auto”; backend wymaga jawnego potwierdzenia, waliduje target/pewność i zachowuje rezerwę termiczną.
- Zastosowanie zmienia wyłącznie rozmieszczenie punktów temperatury; PWM nadal wynika z konfiguracji użytkownika i zachowuje monotoniczność.
- Zapis geometrii przebudowuje overlay custom1 i korzysta z Restart Managera; nieudany zapis automatycznie przywraca poprzednią siatkę.

## 2.6.1 — 2026-10-21

- Naprawiono integralność lokalnej paczki ZIP: manifest wydania nie zawiera już tymczasowych plików `__pycache__` / `*.pyc`.
- Dodano walidację builda blokującą publikację paczki, gdy manifest wskazuje plik nieobecny w ZIP-ie lub ma niezgodną sumę SHA-256.
- Zachowano funkcje 2.6.0: Mobile UI Stability oraz AI Grid Density Advisor.

## 2.5.9 — 2026-10-21

## 2.6.0 — 2026-10-21
- Mobile UI Stability: główna karta diagnostyczna nie otwiera już natywnego `more-info` dla telemetryki realtime, dzięki czemu przypadkowe dotknięcie nie uruchamia ciężkiego widoku Historia/Aktywność.
- `sensor.rpi5_control_center_host_telemetry` pozostaje sensorem transportowym wyłączonym z Recorder; karty AI/Platform nie wiążą go już jako encji klikalnej.
- AI Grid Density Advisor: AI gromadzi histogram temperatury w krokach 0,25°C i po odpowiednim okresie nauki sugeruje region zagęszczenia oraz krok 0,25/0,5/0,75°C. Sugestia jest tylko doradcza i nie zmienia krzywej bez decyzji użytkownika.
- Karta AI pokazuje postęp nauki regionu pracy oraz gotową rekomendację wraz z pewnością i koncentracją próbek.
- Usunięto z Info/Dokumentacji wewnętrzne uwagi redakcyjne i projektowe; pozostawiono wyłącznie treść użytkową.


### Template Transport Recovery
- Przebudowano dostęp karty Lovelace do `sensor.rpi5_control_center_host_telemetry`: AI Cooling, Platform Guard oraz fallback PMIC nie używają już bezpośredniego `state_attr('sensor.rpi5_control_center_host_telemetry', ...)`.
- Atrybuty host relay są odczytywane przez obiekt stanu `states.sensor.rpi5_control_center_host_telemetry.attributes`, co omija ścieżkę powodującą powtarzający się `TemplateSyntaxError: unexpected char "'" at 23` w szablonie AI.
- Zachowano funkcjonalność AI Qualified Learning, Adaptive PWM, kalibracji i PMIC; zmiana dotyczy warstwy transportu/renderowania Lovelace.
- Walidator wydania blokuje ponowne pojawienie się bezpośrednich wywołań `state_attr` dla host relay i nadal parsuje wszystkie szablony Jinja przed zbudowaniem ZIP.
- Card UI otrzymał wersję 2.5.9, więc Card Sync jednoznacznie wykryje kartę 2.5.8 jako wymagającą synchronizacji.
- `UnknownHandler` pozostaje traktowany jako osobny błąd discovery/config-flow; ten build nie modyfikuje go bez identyfikacji domeny integracji.
- Zakładki Info/README/Dokumentacja nie zostały zmienione.

## 2.5.8 — 2026-10-21

### Calibration Card Recovery
- Przebudowano trzy szablony karty kalibracji Active Cooler (`primary`, `secondary`, `icon_color`) tak, aby nie zależały od złożonego fallbacku `host_telemetry -> fan_calibration` w pierwszej instrukcji Jinja.
- Karta korzysta bezpośrednio z `sensor.rpi5_fan_calibration` i jego atrybutów; eliminuje to ścieżkę, która generowała powtarzający się `TemplateSyntaxError: unexpected char "'" at 26`.
- Card UI otrzymał wersję 2.5.8, dzięki czemu istniejąca karta 2.5.7 zostanie jednoznacznie wykryta jako wymagająca synchronizacji.
- Weryfikacja Card Sync sprawdza teraz nie tylko numer `Card UI`, ale pełną zgodność zapisanej karty ze wzorcem. Przy rozbieżności wykonywany jest rollback.
- AI Cooling, Adaptive PWM, Qualified Learning i ustawienia chłodzenia pozostają funkcjonalnie bez zmian.
- Zakładki Info/README/Dokumentacja nie zostały zmienione.

## 2.5.7 — 2026-10-21

### Template Hotfix
- Usunięto błąd `TemplateSyntaxError: unexpected char "'"` w karcie kalibracji Active Cooler na Home Assistant Core 2026.10.2.
- Zastąpiono parser-wrażliwy inline `not in [...]` prostym blokiem `if/else`; analogicznie uproszczono warunek koloru błędu kalibracji.
- Poprawiono zarówno kanoniczny YAML karty, jak i `dashboard_card.json` używany przez Lovelace Card Sync.
- AI Cooling, Adaptive PWM, kwalifikowane uczenie i mechanizm Browser Session Card Sync pozostają funkcjonalnie bez zmian.
- Błąd integracji Roomba/`roombapy` jest niezależny od RPi5 Control Center i nie jest modyfikowany przez ten build.

## 2.5.6 — 2026-10-21

### Lovelace Card Sync — zapis przez sesję użytkownika
- Synchronizacja karty nie używa już tokenu backendu aplikacji do operacji `lovelace/config/save`.
- Odczyt i zapis dashboardu wykonuje aktywna sesja administratora Home Assistant z interfejsu Ingress.
- Przed zapisem aplikacja wykonuje pełny backup dashboardu do `/data/lovelace_backups`.
- Po zapisie karta jest ponownie odczytywana i weryfikowany jest znacznik `Card UI v2.5.6`; przy błędzie wykonywana jest próba rollbacku.
- Diagnostyka pokazuje nazwę dashboardu, widoku, wykrytą wersję karty i szczegółowy błąd odczytu/zapisu.

## 2.5.5 — 2026-10-21

### Info i Dokumentacja
- Zaktualizowano zakładki **Info** i **Dokumentacja** do aktualnego stanu projektu: AI Qualified Learning, Dynamic Config UI, synchronizacja Lovelace, Active Cooler i recovery.
- Usunięto mieszanie języka polskiego i angielskiego w jednym dokumencie.
- Aktywne natywne pliki `README.md` i `DOCS.md` są w całości po polsku.
- Dodano osobne, kompletne wersje językowe `README.pl.md`, `DOCS.pl.md`, `README.en.md` i `DOCS.en.md`.
- Historia wersji pozostaje wyłącznie w `CHANGELOG.md`; Info i Dokumentacja opisują bieżący stan aplikacji.
- Algorytm AI, Adaptive PWM i mechanizm Lovelace Card Sync pozostają bez zmian funkcjonalnych.

## 2.5.4 — 2026-10-21

### Lovelace Card Sync
- Dodano bezpieczne wykrywanie aktywnej karty **RPi5 Control Center** w dashboardach Lovelace storage przez oficjalny WebSocket API Home Assistant.
- Dynamic Config UI pokazuje wersję aktywnej karty i wzorca aplikacji oraz udostępnia akcje **Sprawdź kartę projektu** i **Synchronizuj kartę**.
- Synchronizacja wymaga jawnego potwierdzenia, tworzy pełny backup dashboardu w `/data/lovelace_backups` i zastępuje tylko jednoznacznie rozpoznaną kartę RPi5.
- Przy braku dopasowania lub wielu kartach zapis jest blokowany; przy błędzie weryfikacji aplikacja próbuje automatycznie przywrócić backup.
- Wzorzec głównej karty ma niezależny znacznik **Card UI v2.5.4** i zawiera sprawdzony panel **AI Adaptive Cooling**.
- Algorytm AI Qualified Learning i Adaptive PWM pozostają bez zmian.

## 2.5.3 — 2026-10-21

- Osadzono w głównej karcie dokładnie zweryfikowany w praktyce panel **AI Adaptive Cooling**, który poprawnie wyświetla telemetrię uczenia.
- Panel AI jest zawsze renderowany bez dodatkowego warunku widoczności i znajduje się bezpośrednio po statusie kalibracji Active Cooler.
- Dodano niezależny od backendu znacznik **Card UI v2.5.3** w HERO oraz nagłówku sekcji AI, aby łatwo wykryć starą kopię YAML Lovelace.
- Zachowano widoki: postęp uczenia, pewność AI, dane treningowe, predykcja PWM oraz postęp `idle/low/medium/high`.
- Brak zmian w algorytmie AI Qualified Learning, Adaptive PWM i zabezpieczeniach chłodzenia.

## 2.5.2 — 2026-10-21

- Rozbudowano główną kartę projektu o sekcję **AI Adaptive Cooling** z czytelnym statusem uczenia.
- Dodano osobne kafelki: postęp bieżącego bucketu, pewność AI, dane treningowe i predykcja PWM.
- Karta pokazuje obserwacje i próbki jakościowe oraz aktualny stan kwalifikacji próbki.
- Dodano zbiorczy postęp uczenia dla `idle`, `low`, `medium` i `high`, aby było widać gotowość modelu dla każdego poziomu obciążenia.
- Brak zmian w algorytmie AI, Adaptive PWM i zabezpieczeniach chłodzenia — 2.5.2 jest wydaniem prezentacyjnym/telemetrycznym.

## 2.5.1 — 2026-10-21

- AI Cooling rozdziela teraz wszystkie obserwacje od kwalifikowanych próbek treningowych.
- Pewność modelu i gotowość Assist rosną wyłącznie na podstawie próbek jakościowych zebranych w stabilnym punkcie pracy.
- Próbka jest kwalifikowana dopiero gdy temperatura mieści się w deadbandzie, trend temperatury jest mały, PWM i obciążenie są stabilne, a klasyczny regulator jest w stanie hold przez co najmniej dwa cykle oceny AI.
- Dodano osobne liczniki `observations_total`, `qualified_samples_total`, postęp bieżącego bucketu oraz postęp idle/low/medium/high.
- Model schema 1 z 2.5.0 jest bezpiecznie migrowany do schema 2: stare próbki pozostają jako obserwacje historyczne, ale nie podnoszą pewności nowego modelu.
- AI Assist wymaga teraz minimalnej liczby kwalifikowanych próbek i nie może zostać odblokowany przez dane ze stanów przejściowych.
- Karta diagnostyczna pokazuje obserwacje, próbki jakościowe i postęp aktualnego bucketu.

## 2.5.0 — 2026-10-21

- Dodano lokalny/offline model uczący się punktów równowagi PWM dla temperatury docelowej i poziomów obciążenia CPU.
- Tryb `Learning` tylko obserwuje i zapisuje model; nie wpływa na PWM.
- Tryb `Assist` działa wyłącznie z profilem Własnym w trybie Automatycznym i dopiero po uzyskaniu wymaganej liczby próbek/pewności.
- AI Assist nie zastępuje Adaptive PWM: korekta jest ograniczona do konfigurowanego okna ±1–10% oraz maks. 2 punkty PWM na ocenę.
- AI ma blokadę kierunku: powyżej deadbandu nie może zmniejszać decyzji chłodzenia, a poniżej deadbandu nie może jej zwiększać.
- Twarde zabezpieczenia, `min_safe`, 100% safety i przekazanie sterowania kernelowi pozostają nadrzędne.
- Model i status są przechowywane w `/data`; status jest publikowany do telemetrii schema 9, Dynamic Config UI i karty diagnostycznej.
- Dodano reset modelu AI z potwierdzeniem w Dynamic Config UI.

## 2.4.4 — 2026-10-21

- Poprawiono trasę przycisku **Log** na karcie diagnostycznej.
- Przycisk korzysta teraz z natywnej ścieżki frontendu Home Assistant `/config/app/local_rpi5_fan_manager/logs`, czyli tej samej trasy co zakładka **Log** w ekranie aplikacji Supervisor.
- Zachowano wyłączenie szybkozmiennych sensorów relay z Recorder wprowadzone w 2.4.3.
- Brak zmian w sterowaniu Active Cooler, Dynamic Config UI i konfiguracji sprzętowej.

## 2.4.3 — 2026-10-21

- Naprawiono zawieszanie aplikacji mobilnej Home Assistant po użyciu przycisku **Log** na karcie diagnostycznej.
- Przycisk **Log** nie otwiera już `more-info` dla szybkozmiennego sensora `sensor.rpi5_fan_manager_host_telemetry`; przechodzi bezpośrednio do zakładki Log aplikacji RPi5 Control Center.
- `sensor.rpi5_control_center_host_telemetry` oraz legacy `sensor.rpi5_fan_manager_host_telemetry` są wyłączone z Recorder, aby nie generować zbędnej historii co kilka sekund.
- Bieżąca telemetria i dashboard nadal korzystają z tych sensorów jako transportu runtime.

## 2.4.2 — 2026-10-21

- Usunięto zbiorczy obiekt `sections` z natywnej zakładki Konfiguracja Supervisor.
- Każdy przełącznik aktywacji jest teraz osobnym polem i znajduje się bezpośrednio przed grupą ustawień, którą kontroluje.
- Zachowano migrację stanów ze starego `sections` oraz automatyczne wykrywanie aktywnych sekcji z istniejących parametrów `config.txt`.
- Backend i Dynamic Config UI korzystają z tych samych nowych przełączników top-level; stary format pozostaje obsługiwany jako fallback migracyjny.
- Natywny Supervisor nie obsługuje dynamicznego ukrywania pól zależnie od przełącznika; pełne chowanie nieaktywnych parametrów pozostaje dostępne w Dynamic Config UI.

## 2.4.1 — 2026-10-21

- Zoptymalizowano Dynamic Configuration UI: przełącznik aktywacji znajduje się bezpośrednio w nagłówku każdej opcjonalnej sekcji.
- Wyłączona sekcja jest całkowicie zwinięta — jej parametry nie są renderowane i nie zajmują miejsca; pojawiają się natychmiast po włączeniu.
- Sekcje podstawowe profilu oraz bezpieczeństwa pozostają zawsze widoczne.
- Przycisk „Domyślne” jest pokazywany tylko dla aktywnej sekcji, co upraszcza widok mobilny.
- Dodano czytelny status „Włączona / Wyłączona” oraz skrócone komunikaty przy nieaktywnych sekcjach.
- Natywna zakładka Konfiguracja Supervisor pozostaje warstwą zgodności; zalecanym interfejsem do zarządzania sekcjami jest panel Ingress.

## 2.4.0 — 2026-10-21

- Dodano dynamiczny interfejs konfiguracji Ingress zoptymalizowany pod telefon.
- Sekcje zaawansowane można włączać i wyłączać; wyłączone parametry pozostają zapisane, ale backend ich nie stosuje.
- Tryby Active Cooler są dynamiczne: Automatyczny, Hybrydowy i Ręczny pokazują tylko właściwe dla siebie ustawienia.
- Każda sekcja ma niezależną akcję „Domyślne” z obowiązkowym potwierdzeniem użytkownika.
- Menedżer `config.txt` synchronizuje wyłącznie aktywne sekcje CPU/OC, GPU, USB, PCIe, boot/kernel, sprzęt, UART, wideo, Device Tree, kompatybilność i własne parametry.
- Dodano bezpieczną migrację aktywności sekcji z wcześniejszej konfiguracji, aby istniejące niestandardowe parametry nie zostały przypadkowo wyłączone po aktualizacji.
- Natywna zakładka Konfiguracja Supervisor pozostaje warstwą zgodności/recovery; podstawowym interfejsem użytkownika jest nowy panel Ingress.

## 2.3.1 — 2026-10-20

- Uporządkowano początek zakładki Konfiguracja: **Nazwa profilu → Temperatura docelowa → Tryb sterowania**.
- Skrócono opisy codziennych ustawień Active Cooler i jednoznacznie oznaczono pola Auto / Hybryda / Ręczny.
- Parametry techniczne Adaptive i bazowych histerez przesunięto logicznie do sekcji `90 · EKSPERT`.
- Zaktualizowano Info i Dokumentację dla modelu sterowania 2.3.x.

## 2.3.0 — 2026-10-20

- Przebudowano `update_status_card.yaml` w stylu głównej karty RPi5 Control Center: ciemny gradient, turkusowe obramowania, Mushroom i spójna typografia.
- Zoptymalizowano UX pod telefon: status → wersja/paczka → szybkie akcje → instalacja/restart tylko wtedy, gdy są potrzebne.
- Usunięto natywną kartę `entities`, która przy brakującej/chwilowo niedostępnej encji generowała komunikat „Nie znaleziono encji”; nowa karta używa odpornych szablonów i czytelnych fallbacków.
- Usunięto duży blok przycisku odświeżania; `Sprawdź teraz` jest kompaktową akcją obok `Szczegóły`.
- Instalacja lokalnego ZIP oraz Restart Manager zachowują potwierdzenia bezpieczeństwa.
- Info i Dokumentacja pozostają bez zmian — wydanie dotyczy warstwy Update UX.

## 2.2.2 — 2026-10-20

- Przywrócono profil `Fabryczny` jako drugi wspierany profil użytkowy obok `custom1`.
- Dodano akcję `RPi5 - przywróć fabryczne chłodzenie Active Cooler`, która zapisuje fabryczną 4-punktową charakterystykę Raspberry Pi 5, zwalnia Adaptive PWM i oddaje sterowanie kernelowi do pełnego restartu hosta.
- Przywracanie fabrycznego chłodzenia nie kasuje zapisanej kalibracji 1% ani konfiguracji `custom1`, dzięki czemu można później wrócić do profilu własnego.
- Dodano marker bezpieczeństwa blokujący ponowne przejęcie thermal ownera przez Adaptive PWM pomiędzy wyborem profilu Fabrycznego a restartem hosta.
- Dodano przycisk awaryjnego przywrócenia chłodzenia w kanonicznej karcie diagnostycznej.
- Profile historyczne pozostają ukryte i dostępne wyłącznie dla migracji/diagnostyki.

## 2.2.0 — 2026-10-20

- Uproszczono model profili Active Cooler do jednego profilu użytkowego: `custom1` / „Własna 1”.
- Usunięto z selektora Home Assistant historyczne profile: Fabryczny, Cichy, Normalny, Chłodny, Poniżej 50°C, Stabilne 50°C oraz warianty 10/15 pkt.
- Edytor krzywych udostępnia użytkownikowi wyłącznie krzywą `custom1`; dane starszych krzywych pozostają tylko dla zgodności migracyjnej.
- Backend nadal potrafi rozpoznać stare profile załadowane przez kernel, ale nie udostępnia ich do ponownego wyboru.
- Zastosowanie profilu z UI zawsze kieruje do `custom1`, eliminując przypadkowy powrót do historycznych charakterystyk.
- Nie zmieniono Adaptive PWM, ownera thermal, kalibracji ani parametrów bezpieczeństwa z 2.1.9.

# RPi5 Control Center — CHANGELOG

## 2.1.9 — 2026-10-20

- Przeniesiono kanoniczny stan kalibracji Active Cooler do trwałego `/data/fan_calibration.json`; dotychczasowy plik w konfiguracji HA jest automatycznie migrowany i utrzymywany jako kopia diagnostyczna.
- Naprawiono błąd składania parametrów JSON w Bash (`${4:-{}}`), który doklejał dodatkowy znak `}` i powodował odrzucenie końcowego zapisu kalibracji mimo komunikatu „gotowe”.
- Poprawiono analogiczny bezpieczny domyślny payload JSON w `supervisor_post`, aby wywołania Supervisor API nie otrzymywały nadmiarowego `}`.
- Zapis końcowego wyniku kalibracji jest ponownie odczytywany i weryfikowany przed wznowieniem Adaptive PWM; regulator korzysta z `min_safe` wyłącznie z poprawnego stanu `ready`.
- Po zakończeniu kalibracji natychmiast synchronizowane są `sensor.rpi5_fan_calibration` i host relay, dzięki czemu karta nie powinna pozostawać przy `mapa 0 pkt`.
- Karta diagnostyczna używa bezpośredniego sensora kalibracji z fallbackiem do host relay oraz pewnej ikony `mdi:fan` dla przycisku kalibracji.
- Mechanizm ownerów, `mode_disabled` i strojenie Adaptive PWM z 2.1.8 pozostają bez zmian.

## 2.1.8 — 2026-10-20

- Zmieniono domyślną i minimalną efektywną martwą strefę Adaptive PWM na ±0,75°C, aby regulator był odporny na skokową rozdzielczość temperatury Raspberry Pi 5.
- Dodano potwierdzanie małych korekt w górę i anti-windup hold; powtarzające się próbki tuż powyżej setpointu nie powodują już ciągłego narastania PWM.
- Zachowano szybką reakcję przy większym przekroczeniu temperatury oraz asymetryczne schodzenie PWM przy przechłodzeniu.
- Stan kalibracji jest zapisywany atomowo i zachowuje wcześniej wyznaczone pola podczas aktualizacji postępu; blokada kalibracji jest zwalniana dopiero po trwałym zapisaniu kompletnego stanu `ready`.
- Kanoniczny host relay schema 8 publikuje zagnieżdżone `fan_calibration` oraz `platform_compatibility`, co umożliwia niezależną od przeładowania bridge synchronizację diagnostyki Home Assistant.
- Karta diagnostyczna korzysta z relay dla kalibracji/Platform Guard i jako fallback PMIC; nagłówek wykresu PWM pokazuje bieżący surowy stan zamiast minutowej średniej.
- Zaktualizowano Info i Dokumentację do aktualnego modelu Active Coolera, kalibracji, thermal ownera, Adaptive PWM, telemetrii i diagnostyki.

## 2.1.7 — 2026-10-20

- Po zakończeniu kalibracji Adaptive PWM nie dziedziczy już wcześniejszego `cur_state`; wyznacza nowy `controller_state` z aktualnej temperatury i aktywnej krzywej `custom1`, z ograniczeniem przez skalibrowane `min_safe`.
- Dodano asymetryczną redukcję chłodzenia: przy temperaturze co najmniej 1°C poniżej celu regulator zmniejsza PWM o 1 punkt procentowy na cykl bez dodatkowego potwierdzenia, a przy co najmniej 2°C poniżej celu — o 2 punkty procentowe na cykl.
- W strefie pomiędzy deadband a -1°C pozostaje dotychczasowe potwierdzanie spadku (`down_confirm`), co ogranicza oscylacje blisko temperatury zadanej.
- Zachowano wyłącznego ownera PWM, fallback `thermal_zone/mode=disabled`, safety handoff ≥70°C oraz kompletną kalibrację 1% PWM.

## 2.1.6 — 2026-10-20

- Dodano zgodny z HA OS fallback wyłącznego sterowania Active Cooler: gdy kernel nie udostępnia governor `user_space`, aplikacja przejmuje strefę przez `thermal_zone/mode=disabled` i steruje `cooling_device/cur_state` bez nadpisywania przez `step_wise`.
- Po zakończeniu Adaptive PWM, kalibracji, błędzie lub restarcie aplikacji oryginalny tryb/polityka thermal są automatycznie przywracane.
- Kalibracja nie kończy się już błędem `userspace_governor_unavailable` na kernelach HA OS bez governor `user_space`.
- Dodano awaryjne przekazanie sterowania do kernela przy temperaturze CPU ≥70°C: aplikacja żąda 100% wentylatora i rezygnuje z ręcznego ownera.
- Zachowano trwały `controller_state`, arbitraż ownera oraz pełny format `update-manifest.json` wymagany przez lokalny skaner ZIP.


## 2.1.5 — 2026-10-20

- Naprawiono lokalne wykrywanie aktualizacji ZIP: główny `update-manifest.json` ponownie zawiera wymagane pola identyfikacyjne (`slug`, `package_version`, `project`, `layout`) i wymagania platformy.
- Zachowano mechanizm wyłącznego właściciela PWM oraz poprawki kalibracji z 2.1.4.

## 2.1.4 — 2026-10-20
- Adaptive PWM ma teraz wyłącznego właściciela `cur_state`: po aktywacji `custom1` przejmuje powiązaną `thermal_zone` przez governor `user_space`, dzięki czemu kernelowa krzywa nie nadpisuje poziomu pomiędzy cyklami regulatora.
- Regulator utrzymuje własny `controller_state`; rzeczywisty `cur_state` służy do weryfikacji wykonania, a nie jako baza kolejnej korekty. Eliminuje to skoki 29/33/38/46/55/60% obserwowane przy małych zmianach temperatury.
- Stan krzywej kernela w chwili przejęcia jest zachowywany jako `base_state`, po czym Adaptive PWM wykonuje wyłącznie małe korekty względem własnego stanu roboczego.
- Dodano centralny arbitraż `fan_control_owner` dla Adaptive PWM i kalibracji. Kalibracja najpierw blokuje regulator, odbiera mu ownera, a następnie sama przejmuje `user_space`; po zakończeniu sterowanie jest zwracane kernelowi.
- Dodano trwały marker właściciela thermal i odzyskiwanie po restarcie aplikacji. Przy wyłączeniu Adaptive PWM, zmianie profilu, błędzie zapisu lub zakończeniu procesu oryginalna polityka thermal jest przywracana.
- Diagnostyka `adaptive_pwm.json` raportuje `control_owner`, `controller_level`, `base_level`, `thermal_zone` i `original_policy`; log zapisów zawiera `Fan Write: source=adaptive`.
- Brak zmian Device Tree względem 2.1.3; pełny restart hosta po aktualizacji 2.1.3 -> 2.1.4 nie jest wymagany.

## 2.1.3 — 2026-10-20
- Kalibracja Active Cooler wykrywa `thermal_zone` powiązaną z wentylatorem i na czas pomiaru przełącza jej governor z bieżącej polityki na `user_space`, aby kernel nie nadpisywał zadanych poziomów 1%.
- Po zakończeniu lub kontrolowanym przerwaniu kalibracji oryginalna polityka thermal jest automatycznie przywracana.
- Kalibracja rozpoczyna skan od 1% PWM zamiast 10%, dzięki czemu może rzeczywiście wyznaczyć minimalny próg startu i minimalną stabilną pracę coolera.
- Sensor kalibracji raportuje thermal zone, oryginalną politykę, politykę kalibracji i status własności sterowania.
- Brak zmian Device Tree względem 2.1.0; pełny restart hosta po aktualizacji 2.1.2 -> 2.1.3 nie jest wymagany.

## 2.1.2 — 2026-10-20
- Poprawiono sterowanie Active Cooler w środowisku Home Assistant App: aplikacja preferuje hostowy sysfs przez `/proc/1/root/sys`.
- `calibrate_fan` i Adaptive PWM nie polegają już wyłącznie na kontenerowym `/sys`, który może być zamontowany read-only.
- Dodano logowanie wykrytej ścieżki `cooling_device`, tachometru oraz statusu RW przed rozpoczęciem kalibracji.
- Brak zmian Device Tree względem 2.1.0; po aktualizacji 2.1.0 -> 2.1.2 pełny restart hosta nie jest wymagany.

## 2.1.0 — 2026-10-20

- Dodano natywną siatkę sterowania Active Cooler 0–100, gdzie jeden stan kernela odpowiada około 1% PWM.
- Dodano ręczną, bezpieczną kalibrację Active Cooler: automatyczne wykrycie progu startu, minimalnego stabilnego PWM i marginesu `min_safe`.
- Kalibracja buduje mapę RPM dla każdego 1% PWM od minimalnego bezpiecznego poziomu do 100% i zapisuje ją w `/config/rpi5_control_center/fan_calibration.json`.
- Adaptive PWM wykorzystuje skalibrowany minimalny bezpieczny poziom, a bez kalibracji zachowuje `custom_min_pwm_percent` jako fallback.
- Podczas kalibracji Adaptive PWM jest wstrzymany; limit temperatury przerywa procedurę i wymusza 100% chłodzenia.
- Dodano `sensor.rpi5_fan_calibration`, skrypty uruchomienia/odświeżenia kalibracji oraz elementy statusu w karcie diagnostycznej.
- Zmieniono generator overlay `custom1` tak, aby 15 punktów temperaturowych wskazywało bezpośrednio stany procentowe z 101-poziomowej tabeli PWM.
- Jest to warstwa przygotowująca dane dla przyszłego Adaptive Cooling AI; AI nie otrzymuje jeszcze autonomicznej kontroli nad sprzętem.

- Przebudowano generator `custom1`, aby wszystkie punkty charakterystyki były wyznaczane jako przesunięcia względem aktualnej temperatury zadanej. Zmiana setpointu automatycznie przesuwa pełną charakterystykę bez zmiany jej zasady regulacji.
- Złagodzono górną część 15-punktowej krzywej: punkt +4°C wykorzystuje tylko część dostępnej rezerwy PWM, +6°C zwiększa chłodzenie dalej, a maksymalna wartość krzywej jest osiągana około +10°C względem setpointu.
- Adaptive PWM nie wymusza już maksymalnego poziomu `cooling_device` przy +4°C. Do +6°C zwiększa chłodzenie pojedynczymi krokami; szybsza korekta zaczyna się od +6°C, a pełne chłodzenie awaryjne od +10°C lub 80°C temperatury CPU.
- Podniesiono rewizję generatora krzywej, dzięki czemu `custom1` zostanie przebudowany po aktualizacji. Zastosowanie nowej tabeli progów wymaga restartu hosta, gdy zgłosi to Restart Manager.
- Zachowano ustawienia użytkownika `custom_min_pwm_percent`, `custom_target_pwm_percent` i `custom_max_pwm_percent`; zmieniono sposób rozłożenia punktów pomiędzy tymi wartościami, bez wymuszania nowych wartości PWM.

# 2.0.2 — 2026-10-19

- Dodano **Adaptive PWM / Auto-Trim** dla profilu `custom1`: regulator koryguje poziom `cooling_device` wokół temperatury zadanej z domyślną martwą strefą ±0,20°C.
- Zwiększanie chłodzenia reaguje szybciej niż jego zmniejszanie; obniżenie biegu wymaga domyślnie dwóch kolejnych pomiarów poniżej martwej strefy, co ogranicza oscylacje.
- Przy przekroczeniu setpointu o ≥1°C regulator może podnieść poziom o dwa stopnie, a przy +4°C żąda pełnego chłodzenia. Kernelowa 15-punktowa krzywa nadal pozostaje aktywnym zabezpieczeniem termicznym.
- Gdy `cooling_device/cur_state` nie jest zapisywalny, Auto-Trim przechodzi w tryb monitor-only bez wyłączania standardowej krzywej kernela.
- Przebudowano geometrię generatora `precise`: 15 punktów jest jeszcze gęściej rozmieszczonych wokół setpointu i ma łagodniejszy przebieg po stronie temperatur niższych od zadanej.
- Podniesiono rewizję generatora krzywej, dlatego po aktualizacji `custom1` jest automatycznie przebudowywany; aktywacja nowej tabeli tripów wymaga pełnego restartu Raspberry Pi 5.
- Dodano plik stanu `/config/rpi5_control_center/adaptive_pwm.json` oraz nowe opcje: włączenie Auto-Trim, deadband, interwał i potwierdzenie redukcji obrotów.
- Zachowano dokładnie dwie karty YAML: `rpi5_control_center_optimized_v5_diagnostics_card.yaml` i `update_status_card.yaml`.

# 2.0.1 — 2026-10-16

- Podniesiono numer wydania z **2.0.0** do **2.0.1**, aby mechanizm lokalnych aktualizacji poprawnie rozpoznawał poprawioną paczkę jako nowszy build.
- Rozbudowano **Info / README** w stylu dojrzałego projektu GitHub/HACS: overview, capability matrix, architektura, quick start, wymagania, bezpieczeństwo i kompatybilność.
- Rozbudowano **Dokumentację / DOCS** o katalog encji, klasyfikację encji kanonicznych/runtime/legacy, konfigurację aplikacji i funkcji, Active Cooler, CPU/OC, USB, `config.txt`, Restart Manager, aktualizacje, diagnostykę i troubleshooting.
- Dodano macierz stosowania zmian: przeładowanie konfiguracji, restart aplikacji, restart Home Assistant i pełny reboot Raspberry Pi 5.
- Brak zmian w logice sterowania sprzętem względem 2.0.0; wydanie 2.0.1 jest aktualizacją numeru buildu i warstwy dokumentacyjnej.

# 2.0.0 — 2026-10-16

- Zaktualizowano Info i Dokumentację do aktualnego stanu projektu.
- Ustalono minimalne wymagania: Home Assistant OS 18.3 i Home Assistant Core 2026.10.1; starsze wersje są nieprzetestowane i niewspierane.
- Dodano natywną blokadę minimalnego Core w `config.yaml`, Platform Guard dla HA OS/Core oraz walidację wymagań przy lokalnych aktualizacjach ZIP.
- Build zawiera dokładnie dwie wspierane karty YAML: `rpi5_control_center_optimized_v5_diagnostics_card.yaml` i `update_status_card.yaml`.
- Uporządkowano nazwy i kolejność opcji Konfiguracji według grup funkcjonalnych bez zmiany kompatybilnych kluczy opcji.
- Zoptymalizowano paczkę: usunięto zbędne kopie zasobów dashboardu, ograniczono tłumaczenia aplikacji do PL + EN fallback i zoptymalizowano logo bez zmiany funkcji runtime.

## 1.9.33 — 2026-10-16

- Naprawiono trwałość jedynej własnej krzywej Active Cooler: wartości zapisane w zakładce **Konfiguracja** są nadrzędne dla `custom1` i nie są już nadpisywane przez historyczny `/data/custom_curve_editor.json`.
- Dodano wykrywanie zmiany parametrów własnej krzywej. Po zapisaniu zmienionej konfiguracji aplikacja przygotowuje overlay `custom1`, zapisuje profil i ustawia wymagany pełny restart hosta.
- Uproszczono konfigurację aplikacji do jednej własnej krzywej; dodatkowe krzywe 2–5 pozostają wyłącznie jako wewnętrzna zgodność legacy i nie są prezentowane w głównym selektorze profili.
- Zbudowano od podstaw `dashboard/rpi5_control_center.yaml` jako kartę modułową. W tej wersji zawiera wyłącznie **Blok 01 — Active Cooler**.
- Blok Active Cooler pokazuje temperaturę CPU, RPM, PWM, poziom `cooling_device`, aktywny profil, stan restartu i parametry własnej krzywej oraz udostępnia akcje zastosowania profilu i zastosowania z restartem.
- Zaktualizowano README/DOCS tak, aby opisywały bieżący model jednej krzywej i modułowej karty bez historii zmian poza CHANGELOG.

## 1.9.32 — 2026-10-16

## 1.9.32 — Single Stable Curve UX

- Interfejs udostępnia tylko jedną własną charakterystykę wentylatora: **Własna — Stabilna**.
- Użytkownik ustawia tylko temperaturę docelową; pozostałe parametry generatora są dobierane automatycznie.
- Generator używa trybu **Precyzyjna**, 15 punktów i największego zagęszczenia wokół setpointu.
- Usunięto z nowej karty wybór pięciu krzywych, edycję pojedynczych punktów i dodatkowe parametry eksperckie.
- Profile historyczne custom2–custom5 pozostają jedynie jako warstwa zgodności wstecznej backendu i nie są dostępne z nowego UX.

## 1.9.32 — 2026-10-16

- Naprawiono instalację lokalnej paczki ZIP po przebudowie Unified UX.
- Manifest integralności jest generowany dopiero po finalnym oczyszczeniu paczki, dzięki czemu nie odwołuje się do usuniętych kart YAML.
- W paczce pozostaje jedna karta Lovelace: `dashboard/rpi5_control_center.yaml`.
- Zachowano nowy Unified UX bez zmian logiki backendu.

- Całkowicie nowa, jednokartowa architektura Lovelace opracowana od zera.
- Uproszczone i ujednolicone akcje: wszystkie skrypty wywoływane przez `script.turn_on`.
- Nowy układ UX: Hero, status live, nawigacja, osiem paneli warunkowych.
- Edytor krzywych zachowuje generator 15 punktów, setpoint, punkt pracy i tryb ekspercki.
- Paczka zawiera tylko jedną kartę Lovelace: `dashboard/rpi5_control_center.yaml`.
- Usunięto stare, alternatywne i diagnostyczne karty dashboardu.

## 1.9.29 — 2026-10-16

### Naprawiono
- usunięto problematyczny długi warunek Jinja w statusie wybranego profilu chłodzenia; ikona i kolor używają teraz jawnego bloku `if/else`, co eliminuje błąd `TemplateSyntaxError: unexpected char` zgłaszany przez Home Assistant;
- karta statusu wybranego profilu nie uruchamia już synchronizacji po dotknięciu, dzięki czemu przypadkowe kliknięcie nie cofa profilu wybranego przez użytkownika do profilu aktywnego;
- dodano jawne zależności `entity_id` dla statusu profilu, aby zmiana selektora i aktywnego profilu natychmiast odświeżała kartę;
- walidator wydania kompiluje wszystkie ciągi Jinja w Complete UX i blokuje ponowne wprowadzenie wadliwego wariantu statusu profilu.

## 1.9.28 — 2026-10-16

### Zmieniono
- Przywrócono kompaktową, spójną szatę graficzną akcji w Complete UX z użyciem kart Mushroom zamiast dużych natywnych przycisków.
- Zachowano stabilne, rozdzielone wykresy historii temperatury CPU i PWM w zakładce Chłodzenie; dopasowano ich obramowanie i nagłówki do stylu Control Center.
- Na Pulpicie przywrócono wspólny dwuskalowy wykres temperatury CPU i PWM w stylu Control Center, bez agregacji `group_by`, która mogła powodować brak wartości CPU.
- Ujednolicono wygląd akcji aktualizacji oraz Restart Managera z pozostałymi sekcjami panelu.

### Zachowano
- Poprawki funkcjonalne v1.9.27: synchronizację profilu, działające akcje skryptów, rozdzielenie historii o różnych jednostkach w Chłodzeniu oraz stabilną nawigację zakładek.

## 1.9.27 — 2026-10-16

### Naprawiono
- zsynchronizowano selektor profilu chłodzenia z faktycznie aktywnym profilem po starcie Home Assistant;
- karta Chłodzenie używa tej samej sprawdzonej konfiguracji ApexCharts co działający wykres Pulpitu;
- karta aktualizacji nie pokazuje pustej wersji przy stanie `current` i poprawnie opisuje źródło `local_zip_scan`;
- sensor stanu aktualizacji jest automatycznie odtwarzany po każdym restarcie Home Assistant, więc źródło, wersja i szczegóły nie znikają po restarcie Core;
- przycisk odświeżenia aktualizacji uruchamia rzeczywiste sprawdzenie wersji zamiast `homeassistant.update_entity` dla sensora publikowanego przez aplikację;
- uporządkowano komunikację aktywnego i wybranego profilu w Complete UX.
- usunięto problematyczną drugą instancję ApexCharts z sekcji Chłodzenie; historia w tej sekcji używa natywnej karty Home Assistant, a zaawansowany ApexCharts pozostaje na Pulpicie;
- ujednolicono warunki kart warunkowych do aktualnej składni Home Assistant;
- wartości bieżące CPU/PWM są prezentowane w kafelkach, a wykres historii nie udaje bieżącego odczytu z uśrednionego koszyka;
- rozdzielono samodzielną kartę aktualizacji od Complete UX, aby nie pozostawała stale nad nawigacją sekcji.

### Zmieniono
- dodano kompatybilne atrybuty sensora aktualizacji: `current_version`, `version`, `source_display`, `status_message` i `message`;
- samodzielna karta aktualizacji używa kanonicznego katalogu `/config/rpi5_control_center_updates`.

## 1.9.25 — UX Runtime Consistency

- dodano `sensor.rpi5_curve_editor_runtime` jako wspólne źródło stanu dla wybranej krzywej, punktu edycji, temperatury CPU, rzeczywistego PWM i aktywnego profilu;
- aktywna krzywa korzysta z rzeczywistego `cooling_device`, a nieaktywna jest wyraźnie oznaczana jako podgląd przewidywany;
- setpoint na wykresie jest wyliczany przez interpolację sąsiednich punktów, także po ręcznej edycji P1–P15;
- wykres odświeża się po zmianie krzywej, punktu lub telemetrii dzięki sensorowi runtime, zamiast czekać wyłącznie na odświeżenie sensora edytora;
- P5–P11 są osobno wizualizowane jako rdzeń zagęszczenia, a punkt pracy, punkt edycji i setpoint mają niezależne znaczniki;
- rozszerzono UX Health Check i `ux_self_test` o temperaturę CPU, obciążenie CPU, PWM, poziom wentylatora, aktywny profil i runtime Curve Editora;
- usunięto fałszywe przechodzenie braku `fan_level` do stanu 0 w opisie punktu pracy.

## 1.9.24 — Curve Working Point Visualization

- przebudowano wykres edytora własnych krzywych: położenie P1–P15 na osi X odpowiada teraz rzeczywistym odstępom temperatury, dzięki czemu zagęszczenie przy setpoincie jest widoczne bezpośrednio;
- dodano osobny marker **Punkt pracy**; gdy wybrana krzywa jest aktywna, wykorzystuje rzeczywisty `sensor.rpi5_fan_level` / stan `cooling_device`, a dla nieaktywnej krzywej pokazuje podgląd poziomu wynikającego z bieżącej temperatury CPU;
- zachowano niezależny marker punktu wybranego do edycji i dodano marker temperatury zadanej, aby nie mylić edycji z rzeczywistą pracą chłodzenia;
- dodano kafelek pod wykresem z numerem aktywnego/oczekiwanego punktu, temperaturą progu, PWM, bieżącą temperaturą CPU, rzeczywistym PWM i zakresem rdzenia zagęszczenia P5–P11;
- lista P1–P15 wyróżnia bieżący punkt pracy i centralny rdzeń zagęszczenia;
- uporządkowano Info/README/DOCS: opis i dokumentacja przedstawiają wyłącznie aktualny stan funkcji i sposób użycia; historia zmian pozostaje wyłącznie w CHANGELOG.

## 1.9.23 — CPU Usage + Adaptive Setpoint Density

- dodano `sensor.rpi5_cpu_usage` pokazujący bieżące, uśrednione wykorzystanie całego CPU Raspberry Pi 5 w zakresie 0–100%;
- kafelek **CPU** w Complete UX pokazuje teraz jednocześnie obciążenie %, taktowanie i liczbę rdzeni;
- generator pięciu własnych krzywych Active Cooler automatycznie zagęszcza 15 punktów pracy wokół temperatury zadanej, a punkty odległe od celu rozmieszcza szerzej;
- dodano trzy charakterystyki rozmieszczenia punktów: **Łagodna**, **Zbalansowana** i **Precyzyjna**; domyślna **Precyzyjna** zapewnia największą rozdzielczość w bezpośrednim rejonie setpointu;
- zmiana temperatury zadanej lub charakterystyki generatora automatycznie przelicza układ punktów i zachowuje monotoniczny przebieg PWM;
- histereza gęsta jest stosowana w rejonie setpointu, a histereza zewnętrzna dla dalszych punktów, co ogranicza niepotrzebne oscylacje wentylatora;
- edytor krzywych zapisuje `response_mode` w trwałym stanie i udostępnia jego reset do wartości fabrycznej;
- Complete UX zaktualizowano do v7, dodając wybór charakterystyki oraz czytelny opis adaptacyjnego generatora;
- README i dokumentacja użytkownika zostały zaktualizowane pod kątem nowych funkcji CPU i chłodzenia.

## 1.9.22 — Restart State Machine

- naprawiono krytyczny błąd czyszczenia Repairs po aktualizacji: runtime używa teraz kanonicznych usług `rpi5_control_center_bridge.set_restart_required` i `rpi5_control_center_bridge.clear_restart_required`;
- trwały marker restartu jest usuwany przed cleanupem issue, więc kolejny start Home Assistant nie odtwarza nieaktualnego zgłoszenia;
- jeśli Core chwilowo nie przyjmie operacji `clear`, cleanup jest ponawiany dzięki `native_restart_repair_posted.json`;
- stan `Bez restartu` w Control Center i wpis w Ustawienia → Naprawy korzystają teraz z tego samego źródła prawdy;
- zachowano fallback do starego domain wyłącznie dla instalacji będących jeszcze w trakcie migracji;
- uproszczono `supervisor_post()` usuwając zduplikowaną gałąź kontroli HTTP;
- dodano test regresji release, który pilnuje kanonicznych endpointów Repairs i mechanizmu retry cleanup;
- Complete UX v6 pozostaje zgodna z dotychczasową szatą i prezentuje spójny stan restartu po aktualizacji.

# 1.9.21 — UX Polish + Cooling Card Fix

- naprawiono sekcję **Chłodzenie** w Complete UX: wykres korzysta teraz z tej samej sprawdzonej konfiguracji ApexCharts co działający wykres Pulpitu; usunięto wariant `stepline`, dodano jawny typ serii, grupowanie i pełną konfigurację osi,
- poprawiono pole „dostępna wersja” w Complete UX (`latest_version` zamiast nieistniejącego `available_version`),
- sensor aktualizacji publikuje teraz kanoniczny `local_update_dir=/config/rpi5_control_center_updates/`,
- migrator scala paczki pozostawione w starym `/config/rpi5_fan_manager_updates/` do kanonicznego katalogu również wtedy, gdy oba katalogi już istnieją,
- zaktualizowano Complete UX do v5 i zachowano dotychczasową szatę graficzną oraz układ nawigacji,

# 1.9.20 — UX Core Fix

- Naprawiono `sensor.rpi5_control_center_ux_status`: szablon nie używa już niedozwolonego `states.get()`.
- Naprawiono skrypt resetu pojedynczego parametru krzywej; usunięto selektor powodujący wyłączenie skryptu przez Home Assistant.
- Curve Editor ma kanoniczną encję `sensor.rpi5_control_center_curve_editor`; alias `sensor.rpi5_fan_curve_editor` pozostaje dla zgodności.
- Dodano watchdog odtwarzający dynamiczne stany Curve Editora po restarcie Home Assistant Core.
- Ostatni wynik akcji UX jest zapisywany w `/data` i publikowany ponownie po restarcie Core.
- Complete UX v4 nie uruchamia ApexCharts, dopóki dane edytora nie mają stanu `ready`; zamiast błędu pokazuje bezpieczny komunikat synchronizacji.
- Rozszerzono walidator buildu o regresje `states.get()`, legacy Curve Editor entity i nieprawidłowy selector.

# 1.9.19 — UX Reliability Hotfix

- dodano kontrolę gotowości backendu (`sensor.rpi5_control_center_ux_status`),
- dodano test UX/backend uruchamiany z karty,
- dodano `sensor.rpi5_control_center_last_action` z wynikiem operacji,
- zastąpiono przekazywanie parametrów resetu z frontendu dedykowanymi wrapperami,
- odświeżanie edytora synchronizuje również nazwy profili,
- Complete UX v3 ostrzega o niezgodności wersji app/package i potrzebie restartu HA,
- karta Optimized v5 pozostaje bez zmian.

# CHANGELOG — RPi5 Control Center

## 1.9.18 — Factory Defaults + Profile/Curve Sync + UX Optimization

- dodano fabryczne wartości dla każdej z 5 własnych krzywych; pełny reset krzywej nie zależy już od bieżących opcji Supervisor,
- dodano reset pojedynczych parametrów generatora: nazwa, temperatura docelowa, obie histerezy oraz min/target/max PWM,
- dodano jedną akcję przywracającą wszystkie 5 krzywych,
- logiczne nazwy startowe: **Zbalansowana, Chłodna, Komfortowa, Cicha, Ultra cicha**,
- lista profili chłodzenia i lista krzywych edytora synchronizują te same nazwy użytkownika,
- sensor edytora publikuje `factory_defaults` i `is_factory`, dzięki czemu karta pokazuje czy krzywa jest domyślna czy zmodyfikowana,
- Complete UX Card v2 otrzymała kompaktowe przyciski resetu parametrów, reset wybranej/wszystkich krzywych oraz reset formularza CPU/USB,
- usunięcie parametru `config.txt` jest w UI opisane jako powrót do **Domyślne / Auto**,


## 1.9.17 — Complete UX + Graphical Fan Curve Editor

- Dodano **graficzny edytor 5 własnych krzywych Active Cooler** dostępny bezpośrednio z Home Assistant.
- Każda krzywa ma podgląd 15 punktów na wykresie temperatura → PWM oraz dwa poziomy edycji: generator parametrów i tryb ekspercki punkt-po-punkcie.
- Tryb ekspercki pozwala indywidualnie zmieniać temperaturę, histerezę i PWM każdego z 15 punktów z walidacją monotonicznej temperatury i niemalejącego PWM.
- Ręczne ustawienia edytora są przechowywane w `/data/custom_curve_editor.json`, dzięki czemu przetrwają rebuild aplikacji bez nadpisywania ustawień Supervisor.
- Dodano sensor `sensor.rpi5_fan_curve_editor` publikujący pięć krzywych, punkty, tryb (`generated`/`points`) i parametry generatora.
- Dodano komplet helperów, skryptów i automatyzacji Home Assistant do wyboru krzywej/punktu, generowania, zapisu punktu, resetu, zastosowania i restartu hosta.
- Dodano `dashboard/rpi5_control_center_complete_ux_card.yaml` — kompletną kartę UX z nawigacją: Pulpit, Chłodzenie, Edytor krzywych, CPU/OC, Zasilanie/USB, Config.txt, Diagnostyka i Aktualizacje.
- Pełna karta wykorzystuje dotychczasową ciemną szatę z turkusowymi akcentami, Mushroom, card-mod i ApexCharts oraz jest zoptymalizowana pod telefon/tablet.
- `rpi5_control_center_optimized_v5_diagnostics_card.yaml` pozostaje **byte-for-byte bez zmian** i nadal jest domyślną/rekomendowaną kartą diagnostyczną.

## 1.9.16 — Five Custom Fan Curves

- Dodano **5 niezależnych własnych krzywych sterowania Active Cooler** (`custom1`…`custom5`).
- Każda krzywa ma własną nazwę, temperaturę docelową, dwie histerezy oraz trzy kotwice PWM; z nich generowane jest 15 punktów pracy.
- Krzywa 1 zachowuje dotychczasowe klucze `custom_*`, więc istniejąca konfiguracja użytkownika nie jest tracona.
- Krzywe 2–5 są konfigurowane jako zagnieżdżona lista w ustawieniach aplikacji.
- Dodano oddzielne overlaye `rpi5-custom1`…`rpi5-custom5`, dynamiczną listę profili Home Assistant i wykrywanie aktywnej krzywej.
- Dodano `apply_custom_curve_on_start: off|1|2|3|4|5`; stare `apply_custom_on_start` pozostaje zgodne i mapuje się na krzywą 1.
- Rozszerzono Info/Dokumentację zgodnie ze standardem projektu.
- Karta `rpi5_control_center_optimized_v5_diagnostics_card.yaml` pozostaje bez zmian.

## 1.9.15 — Documentation Standard

- przebudowano zakładkę **Info** jako profesjonalną stronę projektu w stylu GitHub/Home Assistant/HACS: opis, capability matrix, architektura, bezpieczeństwo, Quick Start, kompatybilność i telemetria,
- wyraźnie opisano, że RPi5 Control Center służy nie tylko do monitoringu, ale również do konfiguracji **OC oraz innych parametrów Raspberry Pi 5**,
- przebudowano zakładkę **Dokumentacja** jako kompletny przewodnik krok po kroku od instalacji Local App/bridge/package przez konfigurację, Active Cooler, Multicore, Config.txt Manager i OC aż do gotowych kart Lovelace,
- wszystkie instrukcje używają kanonicznych nazw `rpi5_control_center`, `rpi5_control_center_bridge`, `rpi5_control_center.yaml` i `rpi5_control_center_updates`; stare nazwy przeniesiono do sekcji migracji,
- historia recovery 1.9.11–1.9.14 nie dominuje już głównego opisu aplikacji i pozostaje w CHANGELOG / sekcji migracji,
- nagłówki dokumentacji pokazują bieżącą wersję 1.9.15,
- runtime, Multicore Telemetry, Bridge Bootstrap Recovery i logika sterowania pozostają funkcjonalnie bez zmian względem 1.9.14,
- `dashboard/rpi5_control_center_optimized_v5_diagnostics_card.yaml` pozostaje byte-for-byte bez zmian.


## 1.9.14 — Bridge Bootstrap Recovery

- restart Home Assistant jest zlecany przede wszystkim przez stabilny endpoint Supervisor `/core/restart`,
- zerwanie HTTP podczas restartu nie jest już traktowane automatycznie jako błąd,
- przygotowany `rpi5_control_center_bridge.yaml` nie jest wycofywany po timeoutcie — pozostaje do następnego startu Core,
- stan post-update nie jest czyszczony tylko dlatego, że Core zniknął i wrócił; wymagane jest faktyczne załadowanie canonical bridge i bieżącej wersji package,
- naprawiono pętlę migracji, w której 1.9.11–1.9.13 uruchamiały HA bez bootstrapu nowego bridge, przez co encje pozostawały `unavailable`,
- zachowano compatibility bridge wyłącznie do momentu potwierdzonego przejęcia encji przez `rpi5_control_center_bridge`,


## 1.9.13 — Universal Recovery

- paczka ma jednocześnie układ wymagany przez updater 1.9.10 (`rpi5_fan_manager`) i 1.9.11+ (`rpi5_control_center`),
- aplikacja sama instaluje tymczasowy `rpi5_fan_manager_bridge` z poprawnym `config_flow.py`, dopóki stary wpis konfiguracji nie zostanie bezpiecznie usunięty,
- naprawiono zapętlony stan „Dokończ aktualizację — restart HA”: nowa wersja rozpoznaje zakończony restart po rzeczywiście załadowanej wersji bridge/package,
- zachowano fallback telemetrii ze starych i nowych ścieżek podczas migracji,
- nie przenosimy katalogu źródłowego uruchomionej Local App w trakcie jej własnego rebuild,


## 1.9.12 — Migration Recovery

- naprawiono błąd `rpi5_fan_manager_bridge.config_flow not found` po migracji domeny integracji,
- dodano bezpieczny compatibility bridge dla istniejącego wpisu konfiguracyjnego Home Assistant,
- nowy bridge akceptuje podczas migracji telemetrię z 1.9.10 (`rpi5_fan_manager`) oraz z nowych ścieżek `rpi5_control_center`,
- wyłączono ryzykowne przenoszenie katalogu źródłowego działającej Local App podczas jej własnego rebuild,
- stary bridge jest usuwany dopiero po potwierdzonym usunięciu starego config entry,

# Changelog

## 1.9.11 — Canonical Layout + Multicore Profiler

- Ujednolicono katalogi projektu: `local_apps/rpi5_control_center/`, `custom_components/rpi5_control_center_bridge/`, `packages/rpi5_control_center.yaml`.
- Dodano migrację układu z nazw `rpi5_fan_manager*`; techniczny Supervisor slug pozostaje zachowany dla kompatybilności aktualizacji.
- Bridge działa pod domeną `rpi5_control_center_bridge` i przejmuje istniejące identyfikatory encji z poprzedniej domeny.
- Dodano trwałe statystyki multicore: ostatni cykl SLOW, średni/maksymalny etap równoległy, suma zadań, estymowany czas sekwencyjny, zysk i sprawność równoległości.
- Zmieniono katalog aktualizacji na `/config/rpi5_control_center_updates/` i stan telemetrii na `/config/rpi5_control_center/`.
- Karta `rpi5_control_center_optimized_v5_diagnostics_card.yaml` pozostaje bez zmian.

## Historia wcześniejszych wersji

## 1.9.10 — 2026-10-16

### Multicore Telemetry
- Dodano opcjonalną architekturę wieloprocesową dla cięższych, niezależnych collectorów diagnostycznych. Linux może rozdzielać pracę na wszystkie dostępne rdzenie Raspberry Pi 5.
- Domyślnie `multicore_telemetry_enabled: true`, a `multicore_workers: auto` wykrywa dostępne CPU i używa maksymalnie 4 workerów.
- W cyklu SLOW PMIC, USB, boot/config oraz rozszerzona diagnostyka systemowa mogą być wykonywane równolegle. Szybka ścieżka FAST pozostaje lekka i sekwencyjna, gdy równoległość nie daje korzyści.
- Dodano bezpieczny mechanizm workerów: każdy proces potomny zwraca wyłącznie zmienione zmienne `SYS_*`, które są scalane po `wait()`. Operacje modyfikujące `config.txt` nie są równoleglone.
- Rozszerzono `sensor.rpi5_control_center_cpu_usage` o `cpu_total_percent`, `cpu_available_cores`, `cpu_allowed_list`, konfigurację/effective workerów oraz liczbę i czas ostatnich zadań równoległych.
- Dodano ustawienia aplikacji **Telemetria wielordzeniowa** i **Liczba workerów telemetrii**.
- Zaktualizowano Info, README i Dokumentację o architekturę multicore oraz sposób interpretacji użycia CPU.

## 1.9.9 — 2026-10-15

### Documentation UX Refresh
- Uporządkowano zakładkę **Info**: krótszy opis projektu, czytelniejsza tabela możliwości, prostsza sekcja bezpieczeństwa, Quick Start i jednoznaczne wskazanie funkcji konfiguracji OC oraz innych parametrów Raspberry Pi 5.
- Przebudowano zakładkę **Dokumentacja** pod szybkie użycie na telefonie: krótsze sekcje, checklisty, tabele decyzji, „pierwsze uruchomienie”, zależności Lovelace, konfiguracja, aktualizacje i troubleshooting.
- Zoptymalizowano polskie opisy w zakładce **Konfiguracja**: usunięto powtórzenia, skrócono tekst i ujednolicono format „zakres / domyślnie / efekt / restart”.
- Doprecyzowano, że HACS jest obecnie używany do zależności Lovelace, natomiast RPi5 Control Center pozostaje instalacją typu Local App.
- Skrócono opis aplikacji widoczny na liście Apps.
- Runtime, Balanced Telemetry, logika aktualizacji i Config.txt Manager pozostają bez zmian funkcjonalnych.
- `dashboard/rpi5_control_center_optimized_v5_diagnostics_card.yaml` pozostaje byte-for-byte bez zmian (SHA-256 `510a4bdea2ed4c87f320d6723b4403d679c22391b2b1820593a4a3cb7a86c373`).

## 1.9.8 — 2026-10-15

### GitHub / HACS Developer Style
- Przebudowano zakładkę **Info** w układzie typowym dla dojrzałych projektów GitHub/Home Assistant: krótki tagline, tabela statusu, capability matrix, architektura, safety-first configuration, Quick Start, Lovelace, telemetria i linki do dokumentacji.
- Przebudowano zakładkę **Dokumentacja** jako przewodnik z nawigacją: instalacja → bootstrap → bridge → HACS/Lovelace → chłodzenie → Restart Manager → Config.txt Manager → OC/GPU/USB → aktualizacja → backup → troubleshooting.
- Dodano `docs/GITHUB_HACS_PUBLISHING.md` z rekomendowanym modelem publikacji projektu hybrydowego i checklistą HACS bez wprowadzania fikcyjnych URL-i lub codeowners.
- Dodano pliki community/repository: `CONTRIBUTING.md`, `SECURITY.md`, `.editorconfig`, `.gitignore`, szablony Issues/PR oraz GitHub Actions `validate.yml`.
- Runtime Balanced Telemetry, Config.txt Manager i logika sterowania pozostają bez zmian funkcjonalnych.
- `dashboard/rpi5_control_center_optimized_v5_diagnostics_card.yaml` pozostaje byte-for-byte bez zmian (SHA-256 `510a4bdea2ed4c87f320d6723b4403d679c22391b2b1820593a4a3cb7a86c373`).

## 1.9.7 — 2026-10-15

### Info + pełna dokumentacja wdrożeniowa
- Przebudowano zakładkę **Info**: zamiast historii zmian zawiera profesjonalny opis RPi5 Control Center i jego głównych funkcji.
- W opisie wyraźnie wskazano, że Control Center jest również narzędziem do konfiguracji **overclockingu (OC)** oraz innych parametrów Raspberry Pi 5 przez Config.txt Manager.
- Zakładkę **Dokumentacja** zastąpiono pełną instrukcją krok po kroku: instalacja, bootstrap integracji, aktualizacje ZIP, pierwsza kontrola, wentylator, Restart Manager, Config.txt Manager, OC, GPU, USB i pozostałe parametry RPi5 oraz gotowe karty Lovelace.
- Do paczki dodano kompletną dokumentację instalacji i konfiguracji.
- Przywrócono i ustawiono jako domyślną/rekomendowaną kartę `dashboard/rpi5_control_center_optimized_v5_diagnostics_card.yaml`.
- Karta Optimized v5 została skopiowana **bez jakichkolwiek zmian**; jej kanoniczny SHA-256 to `510a4bdea2ed4c87f320d6723b4403d679c22391b2b1820593a4a3cb7a86c373`.
- `dashboard/rpi5_control_center.yaml` jest teraz identyczną kopią karty Optimized v5.
- Zachowano bez zmian logikę Balanced Telemetry i sensory 4 rdzeni z wersji 1.9.6.


## 1.9.6 — 2026-10-15

- **Balanced Telemetry:** temperatura CPU, RPM, PWM, procent PWM i poziom wentylatora odświeżają się standardowo co **5 s** zamiast co 1 s.
- **4 rdzenie CPU:** dodano sensory częstotliwości i chwilowego użycia dla rdzeni **0–3**; użycie jest liczone z delty `/proc/stat`, a częstotliwość z `cpufreq`.
- **Wykres:** domyślny ApexCharts odświeża widok co **5 s**, a punkty linii grupuje co **10 s** funkcją `last`, co daje bieżący i czytelny obraz bez nadmiernej liczby punktów.
- Realtime cache toleruje do 12 s wieku próbki, aby uniknąć chwilowych `unavailable` przy standardowym interwale 5 s.
- Nie dodano temperatur osobnych rdzeni: Raspberry Pi 5 standardowo udostępnia wspólną strefę temperatury CPU/SoC, a nie wiarygodne cztery temperatury per-core.

## 1.9.5 — 2026-10-15

### Startup Hotfix + Add-on Branding
- Naprawiono krytyczny restart loop wersji 1.9.4: `publish_telemetry_snapshot()` używał `temp_sign` bez inicjalizacji przy dodatniej temperaturze CPU, a `set -u` kończył `/run.sh` komunikatem `temp_sign: unbound variable`.
- `temp_sign`, `temp_abs`, `temp_tenths`, `fan_type` i pozostałe zmienne pomocnicze szybkich pętli mają teraz jawne wartości początkowe, co zabezpiecza także krótkotrwałe błędy/race przy odczycie sysfs.
- Zachowano 1-sekundowe próbkowanie temperatury CPU, RPM, PWM i procentu PWM.
- Dodano `icon.png` dla kafla na liście aplikacji Home Assistant.
- Zmieniono `logo.png`: zawartość została wizualnie powiększona o ok. 20% przy zachowaniu wymiaru pliku.


## 1.9.4 — 2026-10-15

### Realtime Cooling Telemetry
- Temperatura CPU, RPM, surowe PWM, procent PWM oraz poziom/max poziom wentylatora są próbkowane co 1 s.
- Dodano lekki `/config/rpi5_fan_manager/realtime.json`; ścieżka realtime nie uruchamia `jq`, `curl`, `vcgencmd` ani diagnostyki PMIC/USB/config.txt.
- Dodano osobny koordynator Home Assistant 1 s wyłącznie dla szybkich sensorów chłodzenia, aby nie odświeżać wszystkich encji co sekundę.
- Pełna telemetria pozostaje co 5 s, relay 10 s, PMIC 15 s, system 30 s i SLOW 120 s.
- Sensor Performance raportuje `realtime_refresh_s: 1`.

## 1.9.3 — 2026-10-15

### CPU Spike Fix
- Zoptymalizowano szybką ścieżkę odczytu temperatury, wentylatora i taktowania CPU: sysfs/proc używa `read` zamiast `cat|tr|head`.
- `generate_custom_arrays()` wykonuje jeden proces `awk` zamiast dziesiątek procesów; `report_active_profile()` nie generuje tablic przy każdym raporcie.
- Raport profilu wydłużono z 30 s do 300 s.
- PMIC: 15 s, system: 30 s, USB/zasilanie/config.txt: 120 s, boot cache: 300 s.
- Host relay HA działa co 10 s i używa gotowego `telemetry.json`, eliminując drugi duży `jq` co 5 s.
- Restart Manager kontroluje stan co 120 s i nie wywołuje `clear_restart_required`, gdy stan `none` się nie zmienił.
- Poprawiono `last_cycle_tier`, aby odświeżenie rozszerzonego systemu klasyfikowało cykl jako NORMAL.
- Pętle telemetryczna, profilu i Restart Managera mają przesunięte starty, co ogranicza zbieganie cięższych zadań.

## 1.9.2 — 2026-10-15

### Performance Optimization
- Zachowano komplet funkcji i diagnostyki z 1.9.1, ale rozdzielono częstotliwości odświeżania danych na warstwy FAST/NORMAL/SLOW.
- Telemetria podstawowa jest publikowana co 5 s; CPU jest odczytywany lekką ścieżką bez skanowania USB, Device Tree i `config.txt`.
- PMIC oraz rozszerzone zasoby systemowe są odświeżane co 10 s.
- Pełna diagnostyka zasilania, USB i konfiguracji jest wykonywana co 30 s; pełna analiza konfiguracji boot korzysta dodatkowo z 60-sekundowego cache.
- Zmiana `config.txt` usuwa cache, dzięki czemu nowy stan może zostać odczytany od razu.
- `load_boot_config_cache()` wykonuje jeden proces `jq` zamiast wielu kolejnych wywołań dla każdego pola.
- Gdy Config.txt Manager jest wyłączony, jego pętla kontrolna odpytywana jest co 15 s i używa pojedynczego odczytu `jq`.
- Dodano wpis startowy `Performance:` pokazujący aktywne interwały telemetrii w logu aplikacji.
- Dodano `sensor.rpi5_control_center_cpu_usage` z użyciem CPU/RAM całej cgroup aplikacji, czasami etapów telemetrii i licznikami cykli FAST/NORMAL/SLOW.
- Dodano sekcję **Performance** do głównego dashboardu.

### Cel
- Ograniczenie użycia CPU przez RPi5 Control Center po rozbudowie diagnostyki 1.9.x bez usuwania informacji ani funkcji sterujących.

## 1.9.1 — 2026-10-15

### Diagnostyka rozszerzona
- Dodano liczbę rdzeni i model CPU, hostname oraz szczegóły sieciowe.
- Dodano liczniki RX/TX aktywnego interfejsu sieciowego.
- Dodano strefy termiczne z `/sys/class/thermal` i sensor maksymalnej temperatury strefy.
- Dodano odczyt `vcgencmd get_throttled`: undervoltage, frequency cap, throttling i soft temperature limit — stan bieżący i historia, jeśli firmware udostępnia dane.
- Dodano `sensor.rpi5_system_info`, `sensor.rpi5_throttling_status` oraz dodatkowe sensory CPU/sieci/termiki.
- Dodano `binary_sensor.rpi5_throttling_problem` i `binary_sensor.rpi5_power_issue_history`.
- Telemetria RAM/swap/rootfs/load/uptime z 1.9.0 jest teraz publikowana również przez hostowy relay aplikacji.

### Interfejs i dokumentacja
- Zachowano logo projektu.
- Rozszerzono dashboard o sekcje System/CPU, Pamięć i dysk, Sieć, Chłodzenie/energia/USB oraz Stan systemu/diagnostyka.
- README i DOCS zaczynają się od krótkiego opisu aplikacji oraz listy jej możliwości.

## 1.9.0 — 2026-10-15

### Logo i zasoby systemowe
- Dodano logo projektu RPi5 Control Center.
- Dodano telemetrię RAM, swap, rootfs/dysku, load average i uptime.
- Dodano alarmy wysokiego użycia pamięci i małej ilości miejsca na rootfs.
- Rozszerzono dashboard o diagnostykę zasobów.

## 1.8.1 — 2026-10-15

### Naprawiono — Config.txt Manager w ekranie Konfiguracja
- Poprawiono błąd v1.8.0: backend i dashboard `rpi5_config_txt_manager.yaml` istniały, ale `config.yaml` nie wystawiał żadnych pól Config.txt Managera, dlatego użytkownik widział tylko dotychczasowe opcje wentylatora/restartów/aktualizacji.
- Dodano bloki `CONFIG.TXT` bezpośrednio do konfiguracji aplikacji: CPU/OC/termika, GPU/V3D/ISP, zasilanie/USB, PCIe/RP1, boot/kernel, sprzęt, UART/debug, wideo/KMS, Device Tree oraz compatibility/legacy.
- Dodano listę `Własne parametry / dtoverlay / dtparam` dla wpisów dynamicznych i spoza katalogu.
- Wszystkie statyczne pola używają wartości `auto` jako bezpiecznego braku ingerencji.
- Menedżer opcji jest domyślnie wyłączony po aktualizacji; użytkownik musi jawnie włączyć zarządzanie z tej zakładki.
- Po włączeniu opcje są synchronizowane do `rpi5cc-managed.txt`; zapis jest wykonywany tylko przy realnej zmianie, z backupem i oznaczeniem pełnego restartu hosta jako wymaganego.
- Zachowano blokadę `usb_max_current_enable=1` bez wykrytego zasilania 5 A.
- Naprawiono obraz aplikacji: `config_txt_catalog.json` jest teraz kopiowany do kontenera, dzięki czemu walidacja znanych parametrów działa również po zbudowaniu aplikacji.

### Dokumentacja
- README i DOCS zaczynają się od krótkiego opisu aplikacji oraz listy jej najważniejszych możliwości.
- Zaktualizowano referencję Config.txt Managera i dokumentację wydania 1.8.

## 1.8.0 — 2026-10-15

### Config.txt Manager
- Dodano centralny menedżer `config.txt` z osobnym plikiem `rpi5cc-managed.txt` dołączanym przez kontrolowany `include`.
- Dodano bloki tematyczne konfiguracji i panel `dashboard/rpi5_config_txt_manager.yaml`.
- Dodano katalog `config_txt_catalog.json` z opisami, typami, wartościami domyślnymi, zakresami, ryzykiem i informacją o restarcie.
- Dodano polecenia `apply_config_txt_parameter`, `remove_config_txt_parameter` i `restore_config_manager_backup`.
- `dtoverlay`, `dtparam` i `include` są obsługiwane jako wpisy powtarzalne.
- Parametry spoza katalogu wymagają Trybu zaawansowanego; nadal obowiązuje kontrola składni i limit 98 znaków.
- Wysoki limit USB nadal jest blokowany bez potwierdzonego zasilania 5 A.
- Każda modyfikacja wykonuje backup i oznacza pełny restart hosta jako wymagany, ale go nie wykonuje.

### Dokumentacja
- Dodano `docs/CONFIG_TXT_REFERENCE.md` oraz `docs/CONTROL_CENTER_1_8.md`.
- Zaktualizowano README i DOCS.
- Od 1.8.0 aktualizacja dokumentacji jest obowiązkową częścią każdego wydania.

## 1.7.10 — 2026-10-15

### Naprawiono — odczyt hosta / config.txt
- Dodano wspólny odczyt hostowych plików przez lokalny namespace, `/proc/1/root` i `nsenter`.
- CPU MHz, min/max, governor i model Raspberry Pi 5 mają fallback do hostowego `/sys` i `/proc`.
- Rozszerzono wyszukiwanie boot o `/mnt/boot`, `/boot/firmware`, `/boot`, `/flash`, istniejące mounty, LABEL/PARTLABEL i skan partycji.
- Snapshot `nsenter` pobiera główny `config.txt` i brakujące pliki `include` rekursywnie podczas parsowania.
- Fallback odczytu `usb_max_current_enable` korzysta z tego samego mechanizmu wykrywania boot zamiast stałej listy urządzeń.

### Naprawiono — encje i dashboard
- Nowe encje integracji dostają kanoniczne `entity_id`, dzięki czemu dashboard nie zależy od automatycznego slugowania nazw.
- Kafelki konfiguracji są wyświetlane dopiero, gdy natywna integracja po restarcie HA rzeczywiście istnieje; wcześniej karta pokazuje dane host relay i komunikat o wymaganym restarcie.
- Dodano czytelne rozróżnienie `Brak dostępu do konfiguracji boot` zamiast sugerowania pustej konfiguracji.

### USB
- Zachowano tryby Auto / 1600 mA / 600 mA. Nie dodano pozornego limitu 1800 mA, ponieważ Raspberry Pi 5 udostępnia sprzętowo dwa poziomy limitera: 600 i 1600 mA.

## 1.7.9 — 2026-10-15

### Dodano
- kontrolowany zapis `arm_freq`, `over_voltage_delta` i `usb_max_current_enable` do hostowego `config.txt`,
- osobny blok `# BEGIN RPI5 CONTROL CENTER SYSTEM` / `# END RPI5 CONTROL CENTER SYSTEM`, bez mieszania z konfiguracją wentylatora,
- tryby CPU **Fabryczne** i **Ręczne**; zakres v1.7.9: 2400–2800 MHz co 50 MHz,
- zakres `over_voltage_delta`: 0–50 000 µV co 5000 µV,
- tryby USB: **Auto**, **Wysoki 1600 mA**, **Niski 600 mA**,
- blokadę wymuszenia USB 1600 mA, gdy telemetria nie potwierdza zasilania 5 A,
- obowiązkowy backup przed każdą zmianą oraz przed przywróceniem,
- maksymalnie 10 historycznych kopii w `/data/boot_config_backups/` i kopię `config.txt.rpi5cc-system.bak` na partycji boot,
- polecenia `apply_system_config` oraz `restore_system_config_backup` wymagające `confirm=true`,
- helpery i skrypty Home Assistant oraz kontrolki dashboardu do zapisu/przywracania.

### Bezpieczeństwo
- zapis jest odrzucany przy wykryciu kolidujących ręcznych wpisów zarządzanych parametrów poza blokiem Control Center,
- plik wynikowy i markery są walidowane przed podmianą,
- każda zmiana oznacza `restart_required=host`; aplikacja nie restartuje hosta automatycznie.

## 1.7.8 — 2026-10-15

### Host boot access — diagnostyka i uprawnienia
- Naprawiono fałszywie dodatni log `Host Access` z 1.7.7: warunek nie traktuje już pustego wyniku `host_pid_boot_root` jako sukcesu.
- Dodano jawne uprawnienie `SYS_PTRACE`, potrzebne do niezawodnego dereferencjonowania `/proc/1/root` przy dostępie do hostowego systemu plików.
- Dodano dwie linie `Host Probe` raportujące osobno dostęp przez `/proc/1/root` i `nsenter`, widoczność `config.txt`, prawa R/W, źródło montowania i skróconą listę plików `/mnt/boot`.
- Zachowano kolejność fallbacków: `/proc/1/root/mnt/boot` → `nsenter` → istniejące mounty → skan partycji boot tylko do odczytu.
- Parametry overclockingu i limitu USB pozostają wyłącznie diagnostyczne; 1.7.8 nie zapisuje ustawień CPU/OC.

## 1.7.7 — 2026-10-15

### Dostęp do konfiguracji boot HAOS
- Dodano `host_pid: true`, aby aplikacja mogła widzieć PID 1 systemu HAOS i jego root filesystem.
- Główna ścieżka odczytu konfiguracji to `/proc/1/root/mnt/boot/config.txt`, odpowiadająca hostowemu `/mnt/boot/config.txt`.
- Dodano fallback przez `nsenter` (snapshot tylko do odczytu), a następnie dotychczasowy skan urządzeń blokowych.
- `find_boot_config` używany przez istniejące profile wentylatora potrafi korzystać z hostowego `/mnt/boot`; nadal tworzy kopię `.rpi5fan.bak` przed zmianą.
- Poprawiono obsługę montowań: aplikacja odmontowuje wyłącznie partycje, które sama zamontowała.
- Kontener omija S6 jako proces init (`ENTRYPOINT /run.sh`), zgodnie z wymaganiem Home Assistant dla `host_pid`.
- Dodano log `Host Access`, który od razu pokazuje PID1 oraz dostępność `/mnt/boot`.
- Ustawienia CPU/overclockingu i limitu USB nadal nie są modyfikowane przez Control Center; pozostają diagnostyczne.

## 1.7.6 — 2026-10-15

### Odczyt konfiguracji boot
- Rozszerzono wykrywanie konfiguracji Raspberry Pi 5 poza stałe `/dev/*p1`: aplikacja sprawdza istniejące punkty montowania, etykiety `hassos-boot`/`haos-boot`, `PARTLABEL`, znane urządzenia i partycje FAT.
- Obsługiwane są `config.txt`, `usercfg.txt` oraz warianty w `firmware/`, `boot/`, `slot-A/` i `slot-B/`.
- Odczyt urządzeń blokowych odbywa się tylko do odczytu (`ro,nosuid,nodev,noexec`). Brak partycji lub pliku nie zatrzymuje aplikacji.
- Sensor konfiguracji pokazuje źródło wykrycia i dokładną lokalizację pliku boot.

### Porównanie zapisane ↔ aktywne
- Do porównania dodano `over_voltage_delta` oraz `usb_max_current_enable`.
- `binary_sensor.rpi5_config_pending_restart` uwzględnia teraz także rozbieżność tych parametrów.
- Zachowano dotychczasowe porównanie `arm_freq`, `core_freq`, `gpu_freq`, `over_voltage` i `arm_64bit`.
- Nadal jest to tryb diagnostyczny: 1.7.6 nie zapisuje parametrów overclockingu ani limitu USB.

### Aktualizacje
- `check_app_update` zawsze kończy się jednoznacznym wpisem w logu: dostępna wersja / wersja aktualna / brak źródła / funkcja wyłączona.
- Lokalny skan ZIP jest raportowany jako osobne źródło zamiast mylącego `supervisor_store`, gdy Supervisor nie zwróci katalogu dodatków.

### Stabilność
- Zachowano zabezpieczenia 1.7.5 dla `set -u`, brakującego Device Tree i opcjonalnych wartości konfiguracji.
- Wentylator, PMIC, USB, Restart Manager i Local ZIP Update Manager pozostają funkcjonalnie bez zmian.
- Aktualizacja wymaga restartu Home Assistant; sam odczyt boot nie wymaga pełnego restartu Raspberry Pi.

## 1.7.5 — 2026-10-15

### Poprawiono
- Usunięto crash-loop `saved_ov: unbound variable` w `collect_boot_configuration`, występujący przy braku dostępnego `config.txt`/partycji boot.
- Zainicjalizowano wszystkie opcjonalne zmienne parsera konfiguracji przed rozgałęzieniem odczytu, pozostawiając ochronne `set -u`.
- Odczyt modelu Raspberry Pi nie zakłada już istnienia `/proc/device-tree/model`; sprawdzane są alternatywne ścieżki Device Tree i prywatny mount sysfs.
- Brak modelu sprzętu jest raportowany jako `N/D`, zamiast generować błąd przekierowania i przerywać diagnostykę.
- Zabezpieczono użycie `saved_ov`, `active_ov`, `saved_arm64` i `active_arm64` bez utraty porównania zapisane ↔ aktywne.

### Bez zmian funkcjonalnych
- Odczyt `config.txt`, `include`, `dtoverlay`, `dtparam`, `vcgencmd` i konfiguracji bootloadera pozostaje tylko do odczytu.
- Sterowanie wentylatorem, PMIC, USB, Restart Manager i Local ZIP Update Manager pozostają bez zmian.
- Aktualizacja wymaga restartu Home Assistant; pełny reboot Raspberry Pi nie jest wymagany przez sam hotfix.

## 1.7.4 — 2026-10-15

### Dodano — konfiguracja Raspberry Pi 5
- Odczyt `config.txt` bez zapisu, z partycji boot montowanej tylko do odczytu.
- Parser zachowuje plik, numer linii i sekcję (`[all]`, `[pi5]` itd.) oraz śledzi `include` do 8 poziomów.
- Publikowane są osobno wpisy `dtoverlay`, `dtparam`, lista `include`, SHA-256 pliku głównego oraz liczba odczytanych wpisów.
- Odczyt aktywnych ustawień przez `vcgencmd get_config int` i `vcgencmd get_config str`.
- Odczyt konfiguracji EEPROM/bootloadera przez `vcgencmd bootloader_config`, jeśli firmware udostępnia polecenie.
- Nowe sensory `sensor.rpi5_boot_configuration` i `sensor.rpi5_overclock_status` oraz `binary_sensor.rpi5_config_pending_restart`.
- Porównanie `arm_freq`, `core_freq`, `gpu_freq`, `over_voltage` i `arm_64bit` zapisane ↔ aktywne. Rozbieżność jest sygnalizowana, ale sekcje warunkowe `config.txt` pozostają widoczne do interpretacji.
- Informacje boot/hardware: model RPi, architektura, kernel i `/proc/cmdline`.
- Cache konfiguracji 60 s; szybka telemetria CPU/PMIC/USB pozostaje co 5 s, więc partycja boot nie jest montowana przy każdej próbce.

### Dashboard
- Dodano `dashboard/rpi5_configuration.yaml` z podglądem konfiguracji.
- Dodano `dashboard/rpi5_configuration_views.yaml` — trzy gotowe widoki: **Konfiguracja**, **CPU / Overclocking**, **Boot / Hardware**.
- Główny panel otrzymał kafelki konfiguracji boot i statusu overclockingu.

### Bezpieczeństwo
- 1.7.4 jest nadal wersją odczytową dla CPU/overclockingu i bootloadera: nie zmienia `arm_freq`, `over_voltage` ani ustawień EEPROM.
- Sterowanie wentylatorem, PMIC, USB i hotfix sysfs z 1.7.3 pozostają bez zmian.

## 1.7.3 — 2026-10-15

### Hotfix USB / sysfs
- Naprawiono spam logu `No such file or directory` przy urządzeniach USB bez opcjonalnych pól `manufacturer` lub `product`.
- Odczyty atrybutów USB nie korzystają już z przekierowania `< plik`; wszystkie pola są czytane przez odporną na zniknięcie węzła funkcję `read_usb_sysfs_attr`.
- Skaner toleruje hot-plug/hot-unplug: jeżeli `idVendor`/`idProduct` znikną w trakcie skanu, urządzenie jest pomijane do następnej próbki zamiast generować błąd.
- Brak `manufacturer`, `product` lub `bMaxPower` jest traktowany jako prawidłowy stan urządzenia, odpowiednio z fallbackiem nazwy i `0 mA`.
- Częstotliwość telemetrii pozostaje 5 s; logika wentylatora, PMIC, zasilania, limitu USB i aktualizacji nie została zmieniona.

## 1.7.2 — 2026-10-15

### Dodano — aktywna telemetria energii
- Do obrazu aplikacji dodano `raspberrypi-utils-vcgencmd`; co 5 s odczytywane jest `vcgencmd pmic_read_adc`.
- Nowe sensory: napięcie wejściowe `EXT5V`, suma mocy szyn PMIC, prąd równoważny PMIC, temperatura PMIC, prąd/napięcie/moc `VDD_CORE`.
- `sensor.rpi5_pmic_power` zawiera atrybut `rails` z prądem, napięciem i mocą każdej mierzonej szyny.
- Prąd równoważny jest liczony jako `suma mocy szyn PMIC / EXT5V_V`; jest oznaczony jako estymacja i **nie jest** całkowitym prądem z zasilacza.

### Dodano — diagnostyka urządzeń USB
- Aplikacja skanuje `/sys/bus/usb/devices` i publikuje urządzenia USB, ścieżkę portu, VID/PID, prędkość i `bMaxPower`.
- `sensor.rpi5_usb_declared_current` pokazuje sumę deklarowanego `bMaxPower`; to nie jest chwilowy pomiar prądu.
- `sensor.rpi5_usb_device_count` pokazuje liczbę urządzeń USB z pominięciem root-hubów kontrolera.
- Atrybut `devices` zawiera szczegóły wykrytych urządzeń.

### Dashboard
- Dodano `dashboard/rpi5_energy.yaml` z kafelkami energii, dwoma wykresami ApexCharts oraz listą urządzeń USB.
- Główna karta `rpi5_control_center.yaml` została rozszerzona o najważniejsze sensory energii.

### Porządki aktualizacji
- Usunięto z natywnej integracji dodatkową `UpdateEntity`, ponieważ Supervisor już pokazuje aktualizację aplikacji `RPi5 Control Center`; migrator usuwa stary zduplikowany wpis z Entity Registry.
- Lokalny ZIP Update Manager i przycisk instalacji na dashboardzie pozostają bez zmian funkcjonalnych.
- Cooldown polecenia instalacji zwiększono do 300 s i ograniczono hałaśliwe logowanie powtórnych wywołań.

### Bezpieczeństwo pomiarów
- PMIC Raspberry Pi 5 nie mierzy prądu urządzeń USB ani innych odbiorników podłączonych bezpośrednio do 5 V. Dlatego aplikacja nie przedstawia sumy PMIC jako rzeczywistego całkowitego poboru z zasilacza.
- Sterowanie wentylatorem, progi 15-punktowe, PWM oraz konfiguracja limitu USB nie zostały zmienione.

## 1.7.1 — 2026-10-15

### Poprawiono
- Wykrywanie zasilania Raspberry Pi 5 w Home Assistant OS: oprócz standardowych ścieżek Device Tree aplikacja próbuje własnego, niezamaskowanego montowania `sysfs`, co omija ograniczenie kontenera ukrywające `/sys/firmware/devicetree`.
- Dodano odczyt `/chosen/power/max_current` (mA), zgodny z dokumentacją Raspberry Pi 5.
- Limit USB 600/1600 mA jest ustalany kolejno z `usb_max_current_enable` w Device Tree, `vcgencmd`, aktywnego wpisu `config.txt`, a na końcu z `max_current`.
- Sensory zasilania pokazują źródło detekcji, źródło limitu USB i źródło informacji o over-current.
- `usb_over_current_detected` jest traktowany jako zdarzenie wykryte podczas bootowania, a nie bieżący pomiar prądu.
- Local ZIP Update Manager ma atomową blokadę i 20-sekundowy cooldown, dzięki czemu wielokrotne wywołania `install_local_update` nie uruchamiają kolejnych prób.
- Repairs nie jest ponownie wysyłane dla identycznego oczekującego restartu; integracja odtwarza je po restarcie z trwałego markera.

### Bez zmian
- Logika profili wentylatora, 15 punktów, PWM i CPU pozostaje taka jak w 1.7.0.
- Wersja 1.7.1 nadal tylko odczytuje ustawienia zasilania/USB; nie zmienia `usb_max_current_enable`.

## 1.7.0 — 2026-10-15

### RPi5 Control Center
- Produkt w interfejsie otrzymał nazwę **RPi5 Control Center**.
- Zachowano techniczny `slug` `rpi5_fan_manager`, domenę `rpi5_fan_manager_bridge`, dotychczasowe `entity_id`, skrypty, profile i mechanizm lokalnych aktualizacji.
- Sterowanie wentylatorem z 1.6.4 pozostaje bez zmian.

### Dodano — CPU
- `sensor.rpi5_cpu_frequency` pokazujący bieżące taktowanie CPU w MHz.
- Atrybuty sensora: `min_mhz`, `max_mhz`, `governor`, źródło telemetrii i wiek próbki.
- Odczyt korzysta z hostowego `cpufreq` (`scaling_cur_freq`, `scaling_min_freq`, `scaling_max_freq`, `scaling_governor`).

### Dodano — zasilanie i USB
- `sensor.rpi5_power_supply` identyfikujący zasilanie na podstawie danych bootloadera w Device Tree.
- Wykrywanie oficjalnego zasilacza Raspberry Pi 27 W przez właściwość `rpi_power_supply`.
- Odczyt surowych USB-PD Power Data Objects i wykrywanie profilu 5 V / 5 A, jeśli jest ogłaszany przez zasilacz.
- `sensor.rpi5_usb_current_limit` pokazujący aktywny łączny limit portów USB-A: **600 mA** lub **1600 mA**.
- Atrybut `over_current_detected` informujący o zdarzeniu przeciążenia USB raportowanym przez bootloader.
- Jeżeli wysoki limit USB jest aktywny, ale nie można jednoznacznie rozpoznać źródła zasilania, sensor nie zgaduje typu zasilacza i pokazuje stan „Nierozpoznany — wysoki limit USB”.

### Telemetria i bezpieczeństwo
- Snapshot hosta rozszerzono do schematu 2 o CPU MHz, dane zasilania i limit USB.
- Zachowano ścieżkę `addon_host_relay` → `app_shared_json`; integracja nadal nie opiera telemetrii wentylatora na namespace `/sys` Home Assistant Core.
- Nowe funkcje 1.7.0 są tylko diagnostyczne: **nie zapisują overclockingu ani `usb_max_current_enable`**.
- Aktualizacja wymaga restartu **Home Assistant**, ale nie wymaga pełnego restartu hosta.


## 1.6.4 — 2026-10-14

### Naprawiono źródło PWM po potwierdzeniu diagnostyką
- Log `status` potwierdził rzeczywisty stan hosta: `poziom=8/15`, `PWM=130`, przy jednoczesnym błędnym `100%` w Home Assistant.
- Przyczyną jest różnica namespace `/sys`: kontener Home Assistant Core może widzieć `pwm1=255`, mimo że uprzywilejowana aplikacja Fan Manager odczytuje z hosta prawidłowe `130`.
- Usunięto telemetrię `command_line` z Core jako źródło prawdy. Wszystkie encje CPU/RPM/RAW PWM/bieg/max bieg/%/status są ponownie natywne.
- Aplikacja co 5 s publikuje jeden spójny hostowy snapshot przez Supervisor API do `sensor.rpi5_fan_manager_host_telemetry`; integracja odczytuje jego atrybuty jako źródło nadrzędne.
- Jeżeli relay chwilowo nie istnieje, integracja używa pliku `/config/rpi5_fan_manager/telemetry.json`; **nie wraca już do `/sys` Home Assistant Core**.
- `PWM=130` jest zawsze przeliczane jako `round(130 / 255 * 100) = 51%`.
- Status chłodzenia korzysta z tego samego snapshotu, więc `8/15` daje `Średnie chłodzenie`, a nie `Maksymalne chłodzenie`.

### Migracja i zgodność
- Migrator ponownie przejmuje pięć surowych `command_line` `unique_id` do `rpi5_fan_manager_bridge` i naprawia ewentualne sufiksy `_2`.
- Zachowano kanoniczne `entity_id`, historię, nazwy, ikony i obszary, o ile rejestr HA na to pozwala.
- Nie zmieniono krzywej 15-punktowej, progów, histerezy ani parametrów `custom15`.
- Wymagany jest restart **Home Assistant**, ale nie restart całego Raspberry Pi.

## 1.6.3 — 2026-10-14

### Poprawiono po wdrożeniu 1.6.2
- Usunięto stan, w którym `sensor.rpi5_fan_pwm` pozostawał osieroconym wpisem platformy `command_line` i był `unavailable`, podczas gdy natywne `%` i status chłodzenia mogły pracować na innym źródle danych.
- Surowa telemetria CPU/RPM/PWM/bieg/max_bieg wraca do sprawdzonych sensorów `command_line`, które w tym środowisku HAOS poprawnie odczytywały hostowy sysfs przed migracją 1.6.
- Natywna integracja nie tworzy już pięciu surowych sensorów, więc `command_line` i `rpi5_fan_manager_bridge` nie konkurują o te same `unique_id`.
- `sensor.rpi5_fan_percent`, `sensor.rpi5_cooling_status`, sensory bezpieczeństwa, wersja pakietu oraz `update.rpi5_fan_manager` pozostają natywne.
- Procent PWM jest nadal liczony wyłącznie jako `round(RAW_PWM / 255 * 100)` i ograniczany do 0–100%.

### Naprawa Entity Registry
- Migrator 1.6.3 skanuje wpisy po dokładnym `unique_id`, dzięki czemu wykrywa również osierocone/stare rekordy, których nie znajdowała wcześniejsza migracja platformowa.
- Dla surowych sensorów usuwa ewentualne natywne duplikaty `*_2` i przywraca `command_line` do kanonicznych `entity_id` (`sensor.rpi5_fan_pwm`, `sensor.rpi5_fan_rpm` itd.).
- Dla encji pochodnych usuwa stare wpisy `template`, zachowuje istniejącą natywną encję i, jeśli trzeba, przenosi ją z sufiksu `*_2` na poprzedni kanoniczny `entity_id`.
- Zachowywane są nazwy, ikony, obszar i stan `disabled_by` dla migrowanych encji pochodnych.

### Źródło danych i zgodność
- `DataUpdateCoordinator` preferuje teraz wartości pięciu surowych sensorów HA (`telemetry_source: ha_command_line`).
- Snapshot aplikacji z `/config/rpi5_fan_manager/telemetry.json` pozostaje zapasowym źródłem na czas startu. Jeżeli ani sensory `command_line`, ani świeży snapshot nie są jeszcze dostępne, integracja publikuje neutralny stan oczekiwania zamiast używać potencjalnie błędnego widoku sysfs Core.
- Nie zmieniono krzywej 15-punktowej, progów, histerezy ani PWM profilu `custom15`.
- Aktualizacja wymaga restartu **Home Assistant**. Pełny restart Raspberry Pi nie jest wymagany, jeśli Restart Manager nie zgłasza `host`.

## 1.6.2 — 2026-10-14

### Poprawiono
- Naprawiono błędne wskazanie `sensor.rpi5_fan_percent` jako 100% przy rzeczywistym PWM niższym od 255.
- Natywna integracja nie opiera już podstawowej telemetrii wyłącznie na widoku `/sys` kontenera Home Assistant Core. Uprzywilejowana aplikacja zapisuje atomowo świeży snapshot hosta do `/config/rpi5_fan_manager/telemetry.json`, a integracja używa go jako źródła nadrzędnego.
- PWM jest zawsze interpretowane jako wartość RAW `0..255` i jawnie przeliczane na `0..100%` według `round(PWM / 255 * 100)`, z ograniczeniem wyniku do 0–100%.
- `sensor.rpi5_cooling_status` korzysta z tej samej spójnej próbki `RPM/PWM/bieg/max_bieg`, dzięki czemu nie raportuje „Maksymalne chłodzenie” na podstawie niespójnych danych z dwóch przestrzeni sysfs.
- Dodano odrzucanie przeterminowanego snapshotu po 45 s i bezpieczny fallback do bezpośredniego sysfs Home Assistant Core.

### Diagnostyka
- `sensor.rpi5_fan_percent` otrzymał atrybuty `raw_pwm`, `telemetry_source` i `sample_age_s`.
- `sensor.rpi5_cooling_status` udostępnia te same informacje diagnostyczne obok biegu, maksymalnego biegu, PWM% i RPM.
- Aplikacja publikuje telemetrię hosta co 5 s, natomiast natywna integracja nadal odświeża encje przez wspólny `DataUpdateCoordinator` co 15 s.

### Zgodność i restart
- Nie zmieniono krzywej 15-punktowej, progów temperatury, histerezy ani wartości konfiguracyjnych profilu `custom15`.
- Aktualizacja wymaga restartu **Home Assistant**, aby załadować nową wersję custom component. Pełny restart Raspberry Pi 5 nie jest wymagany, ponieważ 1.6.2 nie zmienia DTBO ani `config.txt`.

## 1.6.1 — 2026-10-14

### Poprawiono
- Naprawiono Local ZIP Update Manager, który w 1.5.10/1.6.0 kopiował pliki nowej wersji, ale nie mógł wykonać Supervisor `/addons/reload` ani `/addons/<app>/rebuild`.
- Przyczyną był `hassio_role: homeassistant`; zgodnie z modelem uprawnień Supervisor operacje zarządzania aplikacjami wymagają roli `manager`.
- `config.yaml` używa teraz `hassio_role: manager`, aby aplikacja mogła kontrolowanie odświeżyć listę lokalnych aplikacji i zlecić własny rebuild.
- Błąd `/addons/reload` nie jest już ignorowany bez informacji: aplikacja zapisuje czytelny log i tworzy powiadomienie z instrukcją ręcznego przebudowania.

### Migracja
- Przy przejściu **1.5.10 → 1.6.1** może być wymagany jeden ręczny rebuild. Wynika to z tego, że działający kontener 1.5.10 ma token nadany jeszcze z rolą `homeassistant`; zmiana roli zaczyna obowiązywać dopiero po przebudowie i ponownym uruchomieniu aplikacji.
- Po uruchomieniu 1.6.1 kolejne aktualizacje lokalne ZIP mogą wykonać reload/rebuild automatycznie.

### Zachowano
- Całą architekturę 1.6: natywne sensory, `update.rpi5_fan_manager`, migrację Entity Registry, Repairs i Restart Manager.
- Aktualizacja 1.6.1 wymaga restartu Home Assistant po migracji package/integracji, ale sama nie wymaga restartu całego RPi5.

## 1.6.0 — 2026-10-14

### Najważniejsza zmiana architektury
- Telemetria RPi5 została przeniesiona z YAML `command_line` / `template` do natywnej integracji `rpi5_fan_manager_bridge`.
- Integracja jest teraz konfigurowana jako pojedynczy Config Entry i ładuje natywne platformy `sensor`, `binary_sensor` oraz `update`.
- Package `packages/rpi5_fan.yaml` nie definiuje już encji telemetrycznych, dzięki czemu eliminuje klasę błędów `ID ... already exists` obserwowanych przy ponownej rejestracji platform YAML.

### Dodano
- Natywne sensory zachowujące dotychczasowe identyfikatory encji:
  - `sensor.rpi5_cpu_temperature`,
  - `sensor.rpi5_fan_rpm`,
  - `sensor.rpi5_fan_pwm`,
  - `sensor.rpi5_fan_level`,
  - `sensor.rpi5_fan_max_level`,
  - `sensor.rpi5_fan_percent`,
  - `sensor.rpi5_cooling_status`,
  - `sensor.rpi5_fan_package_version`.
- Natywne sensory binarne:
  - `binary_sensor.rpi5_cooling_problem`,
  - `binary_sensor.rpi5_high_temperature`,
  - `binary_sensor.rpi5_local_package_update_available`.
- Natywną encję **`update.rpi5_fan_manager`** widoczną w standardowym systemie aktualizacji Home Assistant.
- Instalację lokalnej paczki ZIP bezpośrednio przez encję Update (`update.install`) — po potwierdzeniu użytkownika akcja przekazuje instalację do Local ZIP Update Managera.
- Pełne release notes dla lokalnej paczki ZIP odczytywane z jej `CHANGELOG.md`.
- Wspólny `DataUpdateCoordinator`, który wykonuje jeden skoordynowany odczyt telemetrii co 15 s dla wszystkich natywnych encji.
- Jednorazową migrację Entity Registry z platform `command_line` / `template` do `rpi5_fan_manager_bridge`.
- Migracja zachowuje dotychczasowe `entity_id` (również ręcznie zmienione) oraz podstawowe ustawienia użytkownika, więc dashboardy i automatyzacje nie powinny wymagać zmian.

### Zmieniono
- `rpi5_fan_manager_bridge` nie jest już wyłącznie bridge'em Repairs; od 1.6 jest pełną natywną integracją RPi5 Fan Managera.
- `manifest.json` integracji ma `config_flow: true` i `iot_class: local_polling`.
- YAML bridge służy wyłącznie do automatycznego utworzenia jednego Config Entry; wszystkie encje są tworzone przez platformy integracji.
- `sensor.rpi5_fan_package_version` jest teraz encją natywną i raportuje `1.6.0`.
- `packages/rpi5_fan.yaml` zawiera teraz tylko helper profilu, skrypty i automatyzacje — bez `command_line` i `template` telemetrii.
- App Update Manager nadal może odczytywać dane Supervisor Store, ale **nie wywołuje już `/store/reload`**. Usuwa to timeouty `/store/reload` obserwowane w logach przy instalacji lokalnej.
- Lokalna paczka ZIP pozostaje źródłem o najwyższym priorytecie dla instalacji lokalnej.
- README, DOCS i opisy konfiguracji PL/EN zostały dostosowane do architektury 1.6.

### Bezpieczeństwo i zgodność
- Aktualizacja 1.5.10 → 1.6.0 może być wykonana przez istniejący Local ZIP Update Manager.
- Wydanie wymaga restartu **Home Assistant**, ale nie wymaga pełnego restartu Raspberry Pi, jeśli nie zmieniano profilu/DTBO/config.txt.
- Restart nadal wymaga jawnej akceptacji użytkownika i może być poprzedzony `/core/check`.
- Stare wpisy Entity Registry są usuwane tylko wtedy, gdy ich `unique_id` i platforma dokładnie odpowiadają historycznym encjom RPi5 Fan Managera.
- Historia stanów pozostaje przypisana do tych samych `entity_id`.

### Konfiguracja
- Nie dodano nowych opcji w `config.yaml`; dotychczasowe zakresy i wartości domyślne pozostają bez zmian.
- Zmieniono opisy `update_check_enabled` i `native_restart_repair`, aby odpowiadały architekturze 1.6. Opcja `native_restart_repair` steruje teraz wyłącznie zgłoszeniami Repairs; natywna integracja i telemetria pozostają zawsze aktywne.

### Wymagane działania po aktualizacji
1. Skopiuj `rpi5_fan_manager_v1.6.0.zip` do `/config/rpi5_fan_manager_updates/` albo zainstaluj paczkę dotychczasową metodą.
2. Potwierdź instalację.
3. Po przebudowie aplikacji zaakceptuj restart Home Assistant zgłoszony przez Restart Manager / Repairs.
4. Po restarcie sprawdź, czy `update.rpi5_fan_manager` oraz dotychczasowe encje RPi5 mają zachowane `entity_id`.
5. Pełny restart RPi5 wykonuj tylko wtedy, gdy Restart Manager zgłasza `host`.

## 1.5.10 — 2026-10-14

### Poprawiono
- Usunięto błąd bootstrapu `Setup of package 'rpi5_fan_manager_bridge' failed: Integration 'rpi5_fan_manager_bridge' not found`.
- Fan Manager nie pozostawia już `packages/rpi5_fan_manager_bridge.yaml` w aktywnej konfiguracji, dopóki bieżący proces Home Assistant nie rozpozna integracji.
- Stary/stale package bridge jest automatycznie usuwany przy starcie, jeśli usługa bridge nie jest jeszcze dostępna.
- Walidacja `/core/check` wykonywana jest przed przygotowaniem bridge package.
- Bridge package jest zapisywany dopiero bezpośrednio przed zatwierdzonym restartem HA, dzięki czemu przy następnym starcie Core custom component i package są obecne od początku procesu.
- Jeżeli restart HA nie wystartuje, przygotowany package bridge jest automatycznie wycofywany.

### Migracja z 1.5.8/1.5.9
- Po uruchomieniu 1.5.10 odczekaj kilka sekund i ponownie wybierz **Sprawdź konfigurację**. Ostrzeżenie o brakującej integracji bridge powinno zniknąć.
- Następnie użyj Restart Managera. Bezpośrednio przed restartem aplikacja przygotuje package bridge i po kolejnym uruchomieniu natywny Repairs będzie aktywny.
- Nie jest wymagany pełny restart Raspberry Pi 5.

## 1.5.9 — 2026-10-14

### Poprawiono
- Usunięto błąd startowy `Setup of package 'rpi5_fan' failed: Integration 'rpi5_fan_manager_bridge' not found`.
- Rozdzielono instalację głównego package i bootstrap package integracji Repairs.
- Główny `packages/rpi5_fan.yaml` nie odwołuje się już bezpośrednio do bridge przed jego instalacją.
- Fan Manager najpierw kopiuje `rpi5_fan_manager_bridge` do `/config/custom_components`, weryfikuje `manifest.json`, a dopiero potem tworzy `/config/packages/rpi5_fan_manager_bridge.yaml`.
- Wyłączenie `native_restart_repair` usuwa zarządzany package bridge.

### Zmieniono
- Dodano `bridge-package.yaml` jako szablon bootstrap używany przez aplikację.
- Docker image zawiera teraz osobny szablon package dla bridge.
- Kolejność startowa to: instalacja custom component → instalacja package bridge → publikacja Restart Managera.

### Wymagane działania po aktualizacji
- Podmień aplikację i `packages/rpi5_fan.yaml` wersją 1.5.10.
- Uruchom aplikację i sprawdź w logu wpis `Zainstalowano package bootstrap rpi5_fan_manager_bridge`.
- Następnie wykonaj restart Home Assistant. Ostrzeżenie o brakującej integracji nie powinno już wystąpić.
- Pełny restart Raspberry Pi nie jest wymagany przez sam hotfix 1.5.10.

## 1.5.8 — 2026-10-14

### Dodano
- **Local ZIP Update Manager** skanujący `/config/rpi5_fan_manager_updates` i wykrywający nowsze paczki RPi5 Fan Managera.
- `update-manifest.json` w paczce wydania z numerem wersji, typem wymaganego restartu i sumami SHA-256.
- Bezpieczny instalator lokalnej paczki: kontrola niebezpiecznych ścieżek ZIP, odrzucanie dowiązań symbolicznych, kontrola `slug`, wersji, składni `run.sh` oraz SHA-256.
- Automatyczny backup źródła aplikacji, package Home Assistant i integracji bridge przed podmianą.
- Automatyczna podmiana `/local_apps/rpi5_fan_manager`, `/config/packages/rpi5_fan.yaml` i `/config/custom_components/rpi5_fan_manager_bridge`.
- Automatyczny Supervisor `/addons/reload` i przebudowa lokalnej aplikacji po instalacji paczki.
- `binary_sensor.rpi5_local_package_update_available`.
- Skrypt `script.rpi5_fan_install_local_update_confirmed` i przycisk instalacji na karcie aktualizacji.
- **RPi5 Fan Manager Bridge** — pomocnicza integracja custom component korzystająca z natywnego Home Assistant Repairs.
- Natywne zgłoszenie **„Oczekiwanie na restart”** po aktualizacji, z repair flow pozwalającym użytkownikowi potwierdzić restart Home Assistant lub pełny restart RPi5.
- Dokument `docs/LOCAL_ZIP_UPDATE.md`.

### Nowa konfiguracja
- `local_package_updates_enabled`: `true/false`, domyślnie `true`. Włącza skanowanie lokalnych ZIP.
- `local_package_scan_interval_minutes`: 1–60 min, domyślnie 2 min.
- `local_package_keep_processed`: `true/false`, domyślnie `true`. Zachowuje zainstalowane paczki w `processed/`.
- `native_restart_repair`: `true/false`, domyślnie `true`. Włącza natywne zgłoszenia Repairs.

### Zmieniono
- App Update Manager preferuje nowszą lokalną paczkę ZIP, a następnie może porównywać Supervisor Store i zdalny manifest.
- `sensor.rpi5_fan_manager_update` dla paczki lokalnej raportuje `source: local_zip`, `local_package_file` i `local_install_supported`.
- Powiadomienie Companion App dla lokalnej paczki może zawierać przycisk **Zainstaluj aktualizację**.
- Konfiguracja aplikacji otrzymała mapowanie `homeassistant_config`, `local_apps` i `app_config` wymagane przez kontrolowaną podmianę plików.
- Docker image zawiera `unzip` oraz źródła bridge Repairs.
- README, DOCS, dokumentacja aktualizacji i tłumaczenia PL/EN zostały zaktualizowane.

### Bezpieczeństwo
- Lokalna paczka jest wyłącznie **wykrywana automatycznie**; instalacja zawsze wymaga akcji użytkownika.
- Przed instalacją tworzony jest backup w trwałych danych aplikacji `/data/update_backups/`.
- Niepoprawna paczka nie jest instalowana.
- Restart po aktualizacji nadal wymaga jawnego potwierdzenia użytkownika.

### Wymagane działania przy pierwszym przejściu na 1.5.10
- Wersje 1.5.7 i starsze nie mają jeszcze instalatora ZIP ani bridge Repairs, dlatego pierwsze przejście do 1.5.10 wykonaj dotychczasową metodą.
- Najpierw podmień/przebuduj aplikację 1.5.10, aby mogła skopiować bridge do `/config/custom_components`.
- Następnie podmień `packages/rpi5_fan.yaml` i uruchom ponownie Home Assistant.
- Od następnych wydań wystarczy skopiować nowy ZIP do `/config/rpi5_fan_manager_updates` i potwierdzić instalację.

## 1.5.7 — 2026-10-14

### Dodano
- Automatyczną synchronizację **Wybranego profilu** z **Aktywnym profilem** po pełnym restarcie Raspberry Pi 5.
- Trwały znacznik `/data/last_profile_sync_boot_id`, dzięki któremu synchronizacja wykonywana jest tylko raz dla danego uruchomienia hosta.
- Mechanizm oczekiwania do 5 minut na dostępność Home Assistant po restarcie hosta, aby synchronizacja działała również wtedy, gdy aplikacja uruchomi się wcześniej niż Home Assistant Core.

### Zmieniono
- Po załadowaniu profilu przez Device Tree/kernel Fan Manager odczytuje faktycznie aktywny profil i ustawia `input_select.rpi5_fan_profile` na tę samą nazwę.
- Zwykły restart samej aplikacji nie nadpisuje profilu wybranego przez użytkownika. Dzięki temu można nadal wybrać nowy profil i dopiero później nacisnąć **Zapisz/Zastosuj**.
- Synchronizacja korzysta z kanonicznych nazw profili, w tym dynamicznej nazwy `Konfigurowalny <temperatura>°C · 15 pkt`.
- Zaktualizowano README oraz DOCS.

### Wymagane działania po aktualizacji
- Podmień aplikację oraz `packages/rpi5_fan.yaml` wersją 1.5.7.
- Uruchom ponownie Home Assistant, aby wczytać package 1.5.7.
- Przy następnym pełnym restarcie Raspberry Pi 5 wybrany profil zostanie automatycznie ustawiony zgodnie z profilem aktywnym.

## 1.5.6 — 2026-10-14

### Dodano
- Mechanizm **Post-Update Restart** wykrywający zmianę wersji aplikacji po zakończeniu aktualizacji.
- Trwałe zapamiętywanie ostatnio uruchomionej wersji w `/data/last_app_version`.
- Plik `release.json` z metadanymi bieżącego wydania, w tym `restart_required`.
- Obsługę typów restartu po aktualizacji: `none`, `home_assistant` i `host`.
- Automatyczne wystawianie wymaganej akcji w `sensor.rpi5_fan_restart_required` po aktualizacji.
- Atrybuty `post_update`, `updated_from` i `updated_to` w sensorze Restart Managera.
- Automatyczne wykrywanie zakończenia restartu Home Assistant na podstawie cyklu niedostępny → dostępny API Core.
- Przycisk **Dokończ aktualizację — restart HA/RPi5** w `dashboard/update_status_card.yaml`.
- Dokument `docs/POST_UPDATE_RESTART.md`.

### Nowa konfiguracja
- `post_update_restart_prompt`: `true` / `false`; domyślnie `true`. Włącza automatyczne proponowanie właściwego restartu po aktualizacji aplikacji.

### Zmieniono
- Po aktualizacji aplikacja nie ogranicza się już do informacji o wymaganym restarcie package — rozpoznaje sam fakt zmiany wersji i wymagania bieżącego wydania.
- Powiadomienie o restarcie po aktualizacji otrzymuje tytuł z numerem nowej wersji.
- Karta stanu aktualizacji została połączona funkcjonalnie z Restart Managerem.
- Zaktualizowano opisy konfiguracji PL/EN, README i DOCS.

### Bezpieczeństwo
- Restart nadal wymaga jawnej akceptacji użytkownika.
- Dla restartu Home Assistant zachowano dodatkową kontrolę konfiguracji i natywną akcję `homeassistant.restart`.
- Pełny restart RPi5 jest proponowany tylko wtedy, gdy metadane wydania wskazują `restart_required: host`.

### Wymagane działania po aktualizacji
- Podmień aplikację i `packages/rpi5_fan.yaml` wersją 1.5.6.
- Pierwszy restart HA po przejściu na 1.5.6 jest wymagany, aby wczytać package 1.5.6.
- Kolejne wydania będą mogły same wystawić właściwy przycisk restartu po aktualizacji na podstawie swoich metadanych `release.json`.

Historia jest kumulacyjna. Nowe wersje są dopisywane na górze bez usuwania wcześniejszych wpisów.
Jeżeli wydanie dodaje lub zmienia ustawienia, równolegle aktualizowane są `config.yaml`, tłumaczenia,
`DOCS.md` i `README.md`.

## 1.5.5 — 2026-10-14

### Dodano
- **App Update Manager** sprawdzający aktualizacje samego RPi5 Fan Managera.
- `sensor.rpi5_fan_manager_update` ze stanami `available`, `current`, `not_configured` i `disabled`.
- Natywne odczytywanie `version_latest` z Supervisor Store dla wersji dostępnych w repozytorium Home Assistant.
- Opcjonalne źródło aktualizacji `app_update_manifest_url` dla instalacji lokalnej/manualnej.
- Obsługę metadanych wydania: `release_url`, `download_url`, `changelog_url`, `release_date`, `restart_required` i `summary`.
- Powiadomienie Companion App z przyciskiem **Pokaż wydanie**, jeżeli źródło aktualizacji udostępnia `release_url`.
- `docs/APP_UPDATE.md` i `docs/app_update_manifest.example.json`.
- Skrypt HA `script.rpi5_fan_check_app_update` i zaktualizowaną kartę `dashboard/update_status_card.yaml`.

### Zmieniono
- Usunięto monitor aktualizacji Home Assistant Core / Supervisor / OS z logiki Fan Managera.
- Dotychczasowe opcje `update_check_enabled`, `update_check_interval_hours` i `update_notify` zostały zachowane, ale od 1.5.5 dotyczą aktualizacji **RPi5 Fan Managera**, co pozwala zachować zgodność istniejącej konfiguracji.
- Komenda `check_updates` pozostaje zgodnościowym aliasem, ale sprawdza teraz własną aplikację.
- README, DOCS oraz tłumaczenia konfiguracji PL/EN zostały dostosowane do App Update Managera.

### Nowa konfiguracja
- `app_update_manifest_url`: pusty ciąg lub adres HTTP/HTTPS; domyślnie pusty. Dla instalacji z repozytorium Home Assistant nie jest wymagany. Dla instalacji lokalnej stanowi zdalne źródło informacji o nowej wersji.

### Ważne
- Obecna lokalna instalacja nie może samodzielnie wykryć przyszłego wydania bez zewnętrznego repozytorium lub manifestu. W takim przypadku sensor pokazuje `not_configured` zamiast błędnie zgłaszać brak aktualizacji.
- Aktualizacje nie są instalowane automatycznie.

### Wymagane działania po aktualizacji
- Podmień aplikację oraz `packages/rpi5_fan.yaml` wersją 1.5.5.
- Uruchom ponownie Home Assistant, aby wczytać nowy skrypt i wersję package 1.5.5.
- Jeżeli pozostajesz przy instalacji lokalnej, ustaw `app_update_manifest_url` na rzeczywisty, publicznie dostępny manifest.
- Pełny restart RPi5 nie jest wymagany przez samą aktualizację 1.5.5.

## 1.5.4 — 2026-10-14

### Dodano
- Powiadomienia Home Assistant Companion z przyciskiem **Restart Home Assistant** lub **Restart RPi5**.
- Automatyczne wykrywanie usługi `notify.mobile_app_*`, gdy skonfigurowano dokładnie jedno urządzenie Companion.
- Konfigurację `mobile_notify_service` pozwalającą ręcznie wskazać telefon przy wielu urządzeniach.
- Automatyczne sprawdzanie aktualizacji Home Assistant Core, Supervisor i Home Assistant OS przez natywny Supervisor Update Manager.
- `sensor.rpi5_home_assistant_updates` ze stanem `current` / `available`, liczbą aktualizacji i wersjami installed/latest.
- Skrypt `script.rpi5_fan_check_ha_updates` oraz kartę `dashboard/update_status_card.yaml`.
- Obsługę zdarzeń `mobile_app_notification_action` dla potwierdzonego restartu.

### Zmieniono
- Restart Home Assistant jest wykonywany przez natywną akcję `homeassistant.restart` zamiast bezpośredniego `/core/restart`.
- Home Assistant sam wykonuje kontrolę konfiguracji przed restartem i blokuje restart przy błędzie.
- Wewnętrzne trwałe powiadomienie pozostaje informacyjne; przycisk akcji jest realizowany przez Companion App, ponieważ `persistent_notification` nie obsługuje własnych przycisków.
- Poprawiono formatowanie powiadomień — znaki `\n\n` nie są już wyświetlane dosłownie.

### Nowa konfiguracja
- `actionable_mobile_notifications`: `true` / `false`; domyślnie `true`.
- `mobile_notify_service`: `auto` lub nazwa usługi `mobile_app_*`; domyślnie `auto`.
- `update_check_enabled`: `true` / `false`; domyślnie `true`.
- `update_check_interval_hours`: 1–24 h; domyślnie 6 h.
- `update_notify`: `true` / `false`; domyślnie `true`.

### Bezpieczeństwo
- Restart nadal wymaga jawnej akcji użytkownika.
- Przycisk w powiadomieniu mobilnym wymaga odblokowania urządzenia, jeśli platforma Companion App to obsługuje.
- Aktualizacje są wyłącznie wykrywane i raportowane — Fan Manager ich automatycznie nie instaluje.

### Wymagane działania po aktualizacji
- Podmień aplikację oraz `packages/rpi5_fan.yaml` wersją 1.5.4.
- Uruchom ponownie Home Assistant, aby wczytać nowe skrypty i automatyzację obsługi przycisków.
- Jeżeli masz więcej niż jedno urządzenie Companion App, ustaw `mobile_notify_service` ręcznie.
- Sam update 1.5.4 nie wymaga restartu całego RPi5.

## 1.5.3 — 2026-10-14

### Zmieniono
- Ujednolicono nazwy w `input_select.rpi5_fan_profile` i `sensor.rpi5_active_fan_profile` — wybrany i aktywny profil używają teraz tej samej nazwy.
- Profil konfigurowalny otrzymał nazwę zależną od temperatury zadanej, np. **Konfigurowalny 50°C · 15 pkt** lub **Konfigurowalny 51,5°C · 15 pkt**.
- Fan Manager synchronizuje listę opcji `input_select.rpi5_fan_profile` z aktualną temperaturą docelową po starcie, po `reload_config` oraz okresowo po restarcie Home Assistant.
- Jeżeli przed zmianą temperatury wybrany był profil konfigurowalny, po aktualizacji listy pozostaje wybrany pod nową nazwą.
- Zachowano zgodność ze starszą nazwą `Konfigurowalny · 15 pkt`.
- Opis ustawienia **Temperatura docelowa** informuje teraz również, że wartość wpływa na nazwę profilu.

### Wymagane działania po aktualizacji
- Podmień `packages/rpi5_fan.yaml` wersją 1.5.3 i uruchom ponownie Home Assistant, aby wczytać wersję pakietu 1.5.3.
- Pełny restart RPi5 nie jest wymagany przez samą aktualizację 1.5.3; jest potrzebny dopiero po zapisaniu profilu zmieniającego Device Tree/config.txt.

## 1.5.2 — 2026-10-14

### Dodano
- **Restart Manager** rozróżniający wymagany restart Home Assistant i pełny restart hosta RPi5.
- `sensor.rpi5_fan_restart_required` ze stanami `none`, `home_assistant` lub `host` oraz atrybutami z powodem i wersjami.
- `sensor.rpi5_fan_package_version` — znacznik wersji pakietu Home Assistant.
- Automatyczne wykrywanie, że nowy `packages/rpi5_fan.yaml` nie został jeszcze wczytany przez Home Assistant.
- Zapamiętywanie wymaganego restartu hosta w `/data/restart_required.json`.
- Rozpoznawanie wykonanego restartu hosta po zmianie Linux `boot_id`.
- Sprawdzenie konfiguracji przez Supervisor `/core/check` przed restartem Home Assistant.
- Restart Home Assistant przez Supervisor `/core/restart` dopiero po poleceniu potwierdzonym przez użytkownika.
- Trwałe powiadomienia o wymaganym restarcie.
- Nowe skrypty HA: `rpi5_fan_restart_manager_status` oraz `rpi5_fan_restart_home_assistant_confirmed`.
- Karta `dashboard/restart_manager_card.yaml` z potwierdzeniem restartu.

### Nowa konfiguracja
- `restart_policy`: `ask` / `notify_only`; domyślnie `ask`.
- `pre_restart_config_check`: `true` / `false`; domyślnie `true`.
- `restart_notice_on_start`: `true` / `false`; domyślnie `true`.

### Zmieniono
- Aplikacja otrzymuje dostęp do Supervisor API (`hassio_api: true`, rola `homeassistant`) wymagany do kontroli konfiguracji i restartu Core.
- Zapis profilu 4-, 10-, 15-punktowego lub custom15 automatycznie oznacza wymagany pełny restart hosta.
- Przywrócenie kopii `config.txt` również ustawia wymagany restart hosta.
- Opisy konfiguracji PL/EN rozszerzono o ustawienia Restart Managera i zasady bezpieczeństwa.
- `README.md` i `DOCS.md` zostały zaktualizowane do funkcji wersji 1.5.2.

### Bezpieczeństwo
- Aplikacja **nie wykonuje automatycznego restartu Home Assistant bez działania użytkownika**.
- Przy `restart_policy=notify_only` aplikacja jedynie informuje i odrzuca polecenie restartu.
- Przy włączonym `pre_restart_config_check` błędna konfiguracja blokuje restart.
- Zmiany Device Tree nadal wymagają pełnego restartu hosta; restart samego Core nie jest traktowany jako wystarczający.

### Wymagane działania po aktualizacji
- Podmień `packages/rpi5_fan.yaml` wersją 1.5.2.
- Uruchom ponownie Home Assistant, aby wczytać nowe sensory i skrypty.
- Pełny restart hosta jest potrzebny tylko wtedy, gdy Restart Manager zgłasza stan `host`.

## 1.5.1 — 2026-10-14

### Dodano
- Polskie opisy wszystkich ustawień w zakładce Konfiguracja.
- Angielskie tłumaczenia nazw i opisów ustawień.
- Angielski interfejs konfiguracji dla pozostałych kodów językowych Home Assistant.
- Jawne zakresy konfiguracji parametrów typu `float` i `int` w `schema`.
- Informacje o wartościach domyślnych, wpływie ustawienia i zależnościach między PWM.

### Zmieniono
- `custom_target_temp_c`: walidacja 46–65 °C.
- `custom_hysteresis_dense_c`: walidacja 0,25–3,0 °C.
- `custom_hysteresis_outer_c`: walidacja 0,25–5,0 °C.
- Dokumentacja konfiguracji została rozszerzona.

## 1.5.0 — 2026-10-14

### Dodano
- Profil **Konfigurowalny · 15 pkt**.
- Regulowana temperatura docelowa.
- Osobna histereza gęstego zakresu i punktów zewnętrznych.
- Regulowane PWM minimalne, docelowe i maksymalne.
- Generowanie DTS i kompilowanie własnego DTBO przy zastosowaniu profilu custom15.
- Opcja `apply_custom_on_start`.

### Zmieniono
- Krzywa 15-punktowa może być przesuwana względem temperatury docelowej.
- PWM punktów pośrednich jest interpolowane między PWM minimalnym, docelowym i maksymalnym.

## 1.4.0 — 2026-10-14

### Dodano
- Profil **Stabilne 50°C · 15 pkt**.
- 15 aktywnych poziomów + stan 0.
- Punkty co 0,5°C w kluczowym zakresie 48,5–52,5°C.
- Histereza 0,75°C w gęstym zakresie i 1,0°C poza nim.
- `sensor.rpi5_fan_max_level` i status chłodzenia liczony względem rzeczywistego `max_state`.
- Wykres ApexCharts z zakresem biegu 0–15.

### Zachowano
- Profil 10-punktowy do porównań.

## 1.3.1 — 2026-10-14

### Dodano
- Polecenie `diagnose` dla własnego Device Tree Overlay.
- Diagnostykę `os_prefix`, `overlay_prefix`, `config.txt`, live FDT i `cooling-levels`.
- Kontrolę katalogów `/overlays`, `/slot-A/overlays`, `/slot-B/overlays`.
- Kopiowanie DTBO do wszystkich istniejących katalogów overlay HAOS.
- Automatyczny wpis `dtparam=cooling_fan=on`.

### Poprawiono
- Obsługę systemu A/B Home Assistant OS, gdzie firmware może korzystać z overlay w aktywnym slocie.

## 1.3.0 — 2026-10-14

### Dodano
- Pierwszy własny profil **Stabilne 50°C · 10 pkt**.
- 10 aktywnych punktów 44–53°C z histerezą 1°C.
- Własny `rpi5-stable50-10step.dtbo`.
- Natywne sterowanie Linux thermal + pwm-fan bez cyklicznego sterowania PWM przez Home Assistant.
- Kopię bezpieczeństwa `config.txt.rpi5fan.bak`.
- Wykres ApexCharts dla biegu 0–10.
