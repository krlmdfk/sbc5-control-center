# SBC5 Control Center — Dokumentacja techniczna

**Wersja dokumentacji:** 2.8.27
**Card UI:** 2.8.27

**Model obciążenia:** temperatura/RPM/PWM korzystają z lekkiej ścieżki 5 s, Adaptive PWM pracuje co 10 s, pełna telemetria bridge co 15 s, kompaktowy relay AI jest oceniany co 15 s i publikowany po zmianie z 5-minutowym keepalive, ciężki relay hosta co 30 s, a synchronizacja trwałych profili Supervisor co 30 s. Diagnostyczne encje historii AI pozostają próbkowane co 30 s.
**Platforma:** Raspberry Pi 5 / Home Assistant OS
**Minimalne wymagania:** HA OS 18.3, Home Assistant Core 2026.10.1

Pełny przewodnik pierwszej konfiguracji znajduje się w osobnym pliku `QUICK_SETUP.md`.

## 1. Cel i zakres
SBC5 Control Center jest lokalną warstwą zarządzania Raspberry Pi 5 pracującym pod Home Assistant OS. Obejmuje chłodzenie, CPU/OC, telemetrię, `config.txt`, aktualizacje, restart orchestration i integrację z Lovelace/Home Assistant Repairs.

## 2. Architektura
1. **App runtime** — `/local_apps/sbc5_control_center`, proces `run.sh`, Ingress WWW i dostęp do hosta.
2. **Bridge `sbc5_control_center`** — sensory, binary sensory, update entity, usługi i Repairs.
3. **Package** — helpery i skrypty wykorzystywane przez dashboard i część akcji użytkownika.
4. **Lovelace** — karta diagnostyczna Card UI 2.8.27 i opcjonalna karta aktualizacji.
5. **Persistent `/data`** — kalibracja, model AI, `cpu_profile_state.json`, backupy i markery restart/update.

## 3. Start i Health Checks
Zdrowy runtime powinien potwierdzić zgodność platformy i host access. Po aktualizacji używany jest dwufazowy Update Health Check:
- **Phase A** — nowy runtime osiągnął checkpoint startowy,
- **Phase B** — relay, bridge, natywne encje oraz żądany profil chłodzenia odpowiadają prawidłowo.
Dopiero po Phase B paczka jest finalizowana i może zostać objęta cleanupem retencyjnym.

### 3.1 Fan Profile Reconciliation
Dla `custom1` runtime musi udostępniać siatkę 1% (`cooling_device/max_state >= 100`). Jeżeli po starcie kernel zgłasza profil fabryczny, SBC5 sprawdza zarządzany blok `config.txt` i plik `rpi5-custom1.dtbo`. Brakujące artefakty są naprawiane tylko raz na bieżący `boot_id`; po naprawie Restart Manager wymaga pełnego restartu hosta. Gdy pliki są już obecne, aplikacja nie zapisuje ich w pętli — raportuje `overlay_written_not_loaded` lub, po kolejnym bootowaniu, `overlay_not_loaded_after_reboot`. Adaptive PWM pozostaje wyłączony do czasu aktywacji siatki 1%.

## 4. Active Cooler
### 4.1 Profile
- **Fabryczny** — sterowanie oddane do mechanizmu kernela/firmware.
- **Własna 1 / `custom1`** — jedyna konfigurowalna krzywa użytkownika.

### 4.2 Tryby
- **Automatic** — aplikacja generuje bazową krzywą wokół setpointu; Adaptive PWM ją koryguje.
- **Hybrid** — ręczna krzywa jest bazą, a Adaptive ma ograniczony zakres korekty.
- **Manual** — bez Adaptive PWM; obowiązuje ręczna krzywa i histereza.

### 4.3 Kalibracja
Kalibracja wyznacza próg startu, `min_run`, `min_safe` i mapę PWM→RPM. Wynik jest zapisywany w `/data/fan_calibration.json` oraz mirrorowany diagnostycznie do katalogu HA. Regulator nie powinien zejść poniżej potwierdzonego minimum bezpieczeństwa.

## 5. Adaptive PWM
Aktualny regulator jest **curve-anchored**: bazą jest `custom1(T)`, a Adaptive dodaje ograniczony trim ±12 pp. Ochrony obejmują:
- deadband (typowo ±0.75°C),
- confirm cycles,
- anti-windup,
- **Sign Guard** — korekta nie może wzmacniać niewłaściwego kierunku błędu,
- deadband trim decay około 1 pp / 10 s,
- slew limiter (+3/-4 pp standardowo; szybszy przy dużym błędzie),
- natychmiastowe zachowanie awaryjne 100%,
- seamless handoff przy aktualizacji aplikacji.

## 6. AI Cooling
AI działa lokalnie i nie wysyła modelu do usług zewnętrznych. Model utrzymuje buckety `idle`, `low`, `medium`, `high`. Obserwacja nie jest automatycznie próbką jakościową — próbka musi spełnić kryteria stabilności temperatury, trendu, PWM i obciążenia.

- **Learning** — nie zmienia PWM.
- **Assist** — może dodać ograniczoną korektę (domyślnie ±5%) dopiero po uzyskaniu wymaganej liczby próbek; zabezpieczenia kierunku mają pierwszeństwo.

## 7. CPU Profile Manager / Overclocking
### 7.1 Presety
| Profil | Oczekiwane `arm_freq` | Charakter |
|---|---:|---|
| Factory | auto / 2400 MHz | referencyjny |
| Mild | 2500 MHz | niskie OC |
| Balanced | 2600 MHz | rekomendowany preset |
| Performance | 2800 MHz | podwyższone |
| Experimental | 3000 MHz | eksperymentalny |

Presety są **Single Source of Truth**: nazwa profilu bezpośrednio wyznacza oczekiwane `arm_freq`. Ręczne pola `config_cpu.*` są używane wyłącznie przez **Advanced**.

### 7.2 Zapis
CPU Profile Manager tworzy/aktualizuje `sbc5cc-cpu-profile.txt`, utrzymuje `/data/cpu_profile_state.json`, wykonuje backup i ustawia `restart=host` tylko przy realnej zmianie konfiguracji.

Stan żądany CPU/GPU jest dodatkowo uzgadniany z trwałym magazynem opcji Supervisor. Natywna zakładka **Konfiguracja** nie jest odczytywana z `/data/options.json`; SBC5 używa `/addons/self/info` do odczytu i `/addons/self/options` do bezpiecznego zapisu tylko pól profili. Podpis ostatniej synchronizacji znajduje się w `/data/profile_supervisor_sync_state.json`, co pozwala odróżnić świadomą zmianę użytkownika w Supervisor od starej wartości domyślnej po aktualizacji.

### 7.3 Boot Verification
Po nowym bootowaniu verifier porównuje:
- oczekiwany profil,
- zapisany `arm_freq`,
- rzeczywisty max CPU z `scaling_max_freq` z fallbackami.
Ma do 5 prób. Repair jest zamykany dopiero po `PASS`.

### 7.4 Advanced
Tryb Advanced można wybrać w WWW, karcie YAML i natywnej Konfiguracji. Ręczne wartości są edytowane w sekcji CPU/OC; limity UI/backend chronią m.in. maks. 3000 MHz i `over_voltage_delta` do +50 mV. Gotowe presety nie ustawiają ręcznie `over_voltage`.

## 8. Telemetria CPU i 4 rdzeni
Bridge publikuje temperaturę, bieżące/min/max taktowanie oraz osobne częstotliwości i użycie CPU0–CPU3. Dane per-core są już częścią istniejącego cyklu telemetrii — karta nie uruchamia dodatkowego próbkowania.

## 9. `config.txt`
Menedżer zarządza tylko własnymi blokami SBC5. Wpisy użytkownika poza nimi mają pozostać nietknięte. Obsługiwane grupy obejmują CPU/OC, GPU/V3D/ISP, power/USB, PCIe/RP1, boot/kernel, hardware, UART, video, Device Tree, compatibility i parametry własne.

Każda operacja wymagająca firmware/kernel reboot powinna skutkować `restart=host`. Synchronizacja pliku zarządzanego porównuje jego treść semantycznie: sama zmiana numeru wersji SBC5 w komentarzu nagłówka nie jest zmianą konfiguracji boot i nie może wymusić restartu Raspberry Pi.

## 10. Restart Manager
Priorytet jest monotoniczny:

`host > home_assistant > app > none`

Pełny restart hosta obejmuje restart Home Assistant, dlatego słabsza potrzeba restartu nie może nadpisać istniejącego `host`. Przy polityce `ask` restart jest wykonywany dopiero po potwierdzeniu użytkownika. Stan jest synchronizowany z Home Assistant Repairs.

## 11. Dynamic Config UI / WWW

Przyciski **Zapisz konfigurację** i **Odśwież** pokazują bezpośrednio stan operacji: wykonywanie, zielone potwierdzenie sukcesu albo czerwony błąd. W trakcie żądania aktywny przycisk jest zablokowany przed ponownym kliknięciem, a po około 2,6 s wraca do zwykłej etykiety.
Ingress zapewnia konfigurację chłodzenia, AI, telemetrii, CPU/OC, `config.txt`, aktualizacji, powiadomień i synchronizacji kart. Sekcje opcjonalne zachowują zapisane wartości po wyłączeniu, ale backend ich nie stosuje.

CPU UI pokazuje stan `Aktywny`, `Oczekuje na restart` lub `Niespójność`, wraz z `saved` i `runtime max`.

## 12. Lovelace
Główna karta Card UI 2.8.27 pokazuje:
- stan chłodzenia i regulatora,
- AI Cooling,
- CPU/OC + wybór bezpiecznego presetu,
- saved/runtime max CPU,
- MHz i obciążenie wszystkich 4 rdzeni,
- diagnostykę systemową i aktualizacje.

Zmiana profilu z Lovelace wywołuje ten sam CPU Profile Manager co WWW; karta nie zapisuje `arm_freq` bezpośrednio.

Pola wyboru i zastosowania profilu CPU/OC są domyślnie zwinięte. Dotknięcie kafelka bieżącego stanu CPU rozwija lub zwija tę sekcję; długie przytrzymanie otwiera More Info. Sekcja GPU/V3D/ISP działa niezależnie w ten sam sposób i po rozwinięciu pokazuje wybór presetu, zastosowanie oraz skrót do ustawień zaawansowanych.

Synchronizacja karty w WWW pobiera aktywny dashboard przez sesję administratora, robi backup w `/data/lovelace_backups`, podmienia tylko jedno jednoznaczne dopasowanie i weryfikuje zapis.

## 13. Aktualizacje lokalne
Kanoniczny katalog:

`/config/sbc5_control_center_updates/`

Alias migracyjny:
- `/config/rpi5_control_center_updates/`
- `/config/rpi5_fan_manager_updates/`

Runtime rozróżnia katalog kanoniczny i aliasy migracyjne. Cleanup liczy każdy plik tylko raz i stosuje niezależną retencję dla `processed` i `failed`.

## 14. Powiadomienia
Jeżeli wykryta jest dokładnie jedna usługa `notify.mobile_app_*`, SBC5 może użyć jej automatycznie do akcji restartu. Przy wielu urządzeniach należy wskazać konkretną usługę. Identyczny wynik discovery nie jest wielokrotnie spamowany w logu w jednym runtime.

## 15. Diagnostyka
Sprawdź kolejno:
1. `Platform Guard`.
2. `Host Access Health`.
3. bridge i package version.
4. Restart Manager / Repairs.
5. CPU `saved_arm` i `active_max`.
6. owner/kalibrację wentylatora.
7. AI bucket/qualified samples.
8. Update Health Check A/B.
9. błędy innych custom integrations analizuj osobno od SBC5.

## 16. Backup i odzyskiwanie
Aplikacja utrzymuje backupy `config.txt`, dashboardów i wybranych stanów migracji. Dostępne są akcje przywracania System Config, config manager backup, profilu chłodzenia i ustawień fabrycznych.

## 17. Bezpieczeństwo
- nie wyłączaj zabezpieczeń termicznych firmware,
- nie obniżaj ręcznie PWM poniżej zweryfikowanego minimum,
- OC testuj stopniowo,
- po zmianach boot/OC wykonuj wymagany pełny reboot,
- przy niestabilności CPU wróć do Factory,
- AI Assist nie zastępuje klasycznych zabezpieczeń.

## 18. Wersjonowanie dokumentacji
- **App:** 2.8.27
- **Card UI:** 2.8.27
- szczegóły zmian: `CHANGELOG.md`
- szybki start: `QUICK_SETUP.md`

## 19. Historia parametrów AI
Recorder Home Assistanta zapisuje osobne encje liczbowe AI, m.in. `sensor.sbc5_ai_prediction_pwm`, `sensor.sbc5_ai_baseline_pwm`, `sensor.sbc5_ai_correction_pwm`, `sensor.sbc5_ai_physical_pwm` i `sensor.sbc5_ai_confidence`. Kafelek **Predykcja AI** rozwija natywny 24-godzinny wykres obejmujący Model AI, Regulator, AI Delta i PWM fizyczny; ponowne dotknięcie ukrywa wykres. Funkcja nie wymaga Browser Mod.

## 20. GPU / V3D / ISP z karty Lovelace
Główna karta SBC5 udostępnia selektor profilu GPU/V3D/ISP oraz przycisk **Zastosuj preset**. Dostępne są: Fabryczny, Eco 850/850/900 MHz, Zbalansowany 950/950/1000 MHz, Wydajność 1000/1000/1100 MHz, Eksperymentalny 1100/1100/1200 MHz i Zaawansowany.

Stan żądany GPU jest przechowywany w `/data/gpu_profile_state.json`. Wybór z YAML lub Ingress jest zapisywany także do trwałego magazynu opcji Supervisor, dzięki czemu natywna zakładka **Konfiguracja** pokazuje ten sam profil. Zmiana wykonana w natywnej Konfiguracji jest importowana do stanu SBC5, również przy przejściu do `Factory` lub wyłączeniu sekcji. Podpis ostatniej synchronizacji znajduje się w `/data/profile_supervisor_sync_state.json`.

Po zastosowaniu profilu SBC5 synchronizuje zarządzany `config.txt`, wykonuje backup i korzysta z Restart Managera. Pełny restart Raspberry Pi jest wymagany tylko wtedy, gdy wynikowa konfiguracja boot uległa zmianie.

## 21. Identyfikacja sprzętu, systemu i firmware
Natywna integracja rejestruje urządzenie Raspberry Pi 5 w Home Assistant z aktualnymi metadanymi sprzętowymi: pełnym modelem, `model_id`/rewizją płyty, wersją sprzętu, numerem seryjnym i adresem MAC aktywnego interfejsu. `sw_version` odpowiada zunifikowanej wersji SBC5 Control Center.

Dodatkowe encje diagnostyczne udostępniają:
- `SBC5 Operating System` — nazwę i wersję Home Assistant OS,
- `SBC5 Kernel` — wersję kernela hosta,
- `SBC5 Architecture` — architekturę systemu,
- `SBC5 Raspberry Pi Firmware` — identyfikator firmware Raspberry Pi,
- `SBC5 Bootloader Firmware` — wersję i datę bootloadera EEPROM.

`SBC5 System Info` agreguje ponadto model, serial, MAC, hostname, interfejs sieciowy, IPv4 oraz podstawowe dane pamięci i systemu plików. Dane identyfikacyjne i firmware są statyczne względem szybkiej pętli sterowania, dlatego runtime buforuje je i odświeża co 300 s. Nie zwiększa to częstotliwości 5-sekundowej telemetrii temperatury/wentylatora ani 10-sekundowego regulatora Adaptive PWM.
