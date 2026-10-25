# SBC5 Control Center — Dokumentacja

> Dokument opisuje aktualną instalację, konfigurację, obsługę, diagnostykę i odzyskiwanie. Historia wydań znajduje się wyłącznie w `CHANGELOG.md`.

## 1. Wymagania

- Raspberry Pi 5 / `aarch64`;
- Home Assistant OS `>= 18.3`;
- Home Assistant Core `>= 2026.10.1`;
- aplikacja SBC5 Control Center z dostępem do hosta;
- dla pełnej karty Lovelace: Mushroom, card-mod i ApexCharts Card.

## 2. Architektura

SBC5 składa się z czterech warstw:

1. **Home Assistant App** — runtime, host access, Ingress, aktualizacje, `config.txt`, chłodzenie i profile sprzętowe.
2. **Natywna integracja `sbc5_control_center`** — urządzenie, sensory, binary sensory, encja Update, usługi i Repairs.
3. **Package Home Assistant** — helpery UI, skrypty i bezpieczne akcje z Lovelace.
4. **Lovelace** — karta diagnostyczna oraz karta aktualizacji.

Dane trwałe modelu AI, kalibracji, profili i markerów aktualizacji są przechowywane w `/data` aplikacji.

## 3. Instalacja i pierwszy start

1. Zainstaluj aplikację SBC5 Control Center.
2. Uruchom ją i sprawdź, czy `Platform Guard` oraz `Host Access` zgłaszają stan prawidłowy.
3. Zrestartuj Home Assistant, jeśli instalator wymaga przeładowania package lub integracji.
4. Dodaj kartę `dashboard/sbc5_control_center_diagnostics_card.yaml` oraz opcjonalną `dashboard/update_status_card.yaml`.
5. Zweryfikuj obecność urządzenia **SBC5 Control Center** w rejestrze urządzeń.

Szczegółowa ścieżka startowa znajduje się w `docs/QUICK_SETUP.md`.

## 4. Active Cooler

SBC5 obsługuje profil fabryczny oraz profil `custom1`. Dla `custom1` runtime sprawdza, czy kernel udostępnia oczekiwaną siatkę 1% (`max_state >= 100`). Jeśli aktywny jest profil fabryczny, Adaptive PWM nie przejmuje sterowania i chłodzenie pozostaje po stronie kernela.

### Tryby sterowania

- **Automatic** — regulator dobiera PWM automatycznie;
- **Hybrid** — automat z ograniczoną korektą użytkownika;
- **Manual** — sterowanie według ręcznej konfiguracji.

### Kalibracja

Kalibracja PWM→RPM służy do wyznaczenia bezpiecznego minimum pracy wentylatora. Po zmianach mechanicznych lub wymianie coolera warto wykonać ją ponownie.

## 5. Adaptive PWM

Bazą jest krzywa `custom1(T)`. Regulator może nakładać ograniczony trim, ale nie zastępuje krzywej nieograniczonym stanem sterownika. Mechanizmy ochronne obejmują deadband, confirm cycles, anti-windup, Sign Guard, limity kierunku i slew limiter. Ścieżka awaryjna 100% pozostaje natychmiastowa.

## 6. AI Cooling

AI działa lokalnie i nie wysyła modelu do usług zewnętrznych. Uczenie wykorzystuje próbki jakościowe przypisane do bucketów obciążenia `idle`, `low`, `medium`, `high`. Model może pracować w trybie Learning lub ograniczonym Assist.

Na karcie kafelek **AI Cooling** rozwija pełną diagnostykę: dojrzałość bucketu, próbki, predykcję, pokrycie modelu, klasyfikację obciążenia, diagnostykę kwalifikacji i sugestie siatki. Sekcja jest domyślnie zwinięta.

## 7. CPU / Overclocking

Dostępne są presety Factory, Mild, Balanced, Performance, Experimental oraz Advanced. Profile nie wymuszają ręcznie `over_voltage`; napięcie pozostaje pod kontrolą firmware/DVFS, o ile użytkownik nie skonfiguruje inaczej ustawień zaawansowanych.

Zmiana profilu zapisuje konfigurację boot tylko wtedy, gdy wynik faktycznie różni się od bieżącego pliku zarządzanego. Po realnej zmianie wymagany jest pełny restart Raspberry Pi i późniejsza weryfikacja saved/runtime.

Na karcie sekcja CPU/OC znajduje się **bezpośrednio pod wykresem temperatury CPU/PWM i nad GPU/V3D/ISP**.

### Zegar CPU

Kafelek **Zegar CPU** pokazuje skrócony stan częstotliwości czterech rdzeni. Dotknięcie rozwija osobne kafelki CPU0–CPU3 z częstotliwością i obciążeniem. Długie przytrzymanie otwiera standardowe `more-info`.

## 8. GPU / V3D / ISP

Profile GPU obejmują Factory, Eco, Balanced, Performance, Experimental i Advanced. Zmiany częstotliwości są ustawieniami boot i po realnym zapisie wymagają pełnego restartu Raspberry Pi. Profil Factory pozostawia zegary pod kontrolą firmware.

## 9. Zarządzanie `config.txt`

SBC5 zapisuje własne, zarządzane fragmenty konfiguracji, wykonuje backup przed zmianą i nie powinien nadpisywać wpisów użytkownika poza blokami należącymi do aplikacji. Porównanie jest semantyczne: zmiana numeru wersji w komentarzu nagłówka nie jest traktowana jako zmiana boot.

## 10. Restart Manager

Restart Manager rozróżnia:

- restart aplikacji;
- restart Home Assistant;
- pełny restart hosta Raspberry Pi.

Priorytet jest monotoniczny: `host > home_assistant > app`. Aktualizacja aplikacji nie może sama podnieść restartu do `host`, jeśli nie istnieje rzeczywista zmiana konfiguracji boot.

## 11. Aktualizacje lokalne

Kanoniczny katalog lokalnych ZIP-ów to `/config/sbc5_control_center_updates/`. Paczka jest weryfikowana przez manifest i SHA-256, a po instalacji Health Check sprawdza runtime, bridge i encje Home Assistanta.

Kafelek **SBC5 Control Center** na karcie aktualizacji rozwija dopiero po dotknięciu status paczki, akcję sprawdzenia, log, instalację i ewentualne komunikaty Restart Managera. Sekcja startuje zwinięta.

## 12. Telemetria i Recorder

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

## 13. Identyfikacja sprzętu i firmware

Urządzenie SBC5 publikuje model Raspberry Pi, model ID/rewizję, HW Rev, serial, MAC i wersję oprogramowania. Diagnostyka udostępnia system operacyjny, kernel, architekturę, firmware Raspberry Pi oraz bootloader EEPROM.

## 14. Diagnostyka

W razie problemu sprawdź kolejno:

1. stan aplikacji i log runtime;
2. `Platform Guard` i `Host Access`;
3. `SBC5 Cooling Problem`, `Throttling Status` i zasilanie;
4. `Config Differs From Active` i `Restart Required`;
5. profil zapisany oraz aktywny po boot;
6. status bridge i wersję package/Card UI.

## 15. Backup i odzyskiwanie

Przed zmianami boot SBC5 tworzy backup zarządzanej konfiguracji. Przy błędzie zapisu lub weryfikacji używany jest rollback. Dla problemów z chłodzeniem zawsze zachowany jest bezpieczny fallback do sterowania kernela, jeśli użytkownikowy profil nie może zostać aktywowany.

## 16. Bezpieczeństwo

Overclocking, Device Tree, limity USB i ustawienia boot mogą wpływać na stabilność. Zmieniaj je etapami i po każdym pełnym restarcie weryfikuj rzeczywisty stan runtime. Nie ignoruj komunikatów o throttlingu, problemach z zasilaniem lub temperaturze.

## 17. Pliki referencyjne

- `docs/QUICK_SETUP.md` — szybka konfiguracja;
- `docs/CONFIG_TXT_REFERENCE.md` — parametry `config.txt`;
- `docs/LOCAL_ZIP_UPDATE.md` — lokalne aktualizacje;
- `docs/GPU_V3D_ISP_PROFILES.md` — profile GPU;
- `CHANGELOG.md` — historia zmian.
