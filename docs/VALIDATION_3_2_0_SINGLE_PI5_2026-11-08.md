# SBC5 Control Center 3.2.0 — Single Raspberry Pi 5 post-release verification
# SBC5 Control Center 3.2.0 — Weryfikacja po wydaniu na jednym Raspberry Pi 5

Date / Data: 2026-11-08
Status / Status: **On-device upgrade and configuration persistence PASS; long-term and independent-device checks remain unverified / Aktualizacja i trwałość konfiguracji na urządzeniu zaliczone; testy długoterminowe i niezależny sprzęt niezweryfikowane.**

## English

### Scope and source
A user tested an in-place update from **3.1.37 to 3.2.0** on their existing Raspberry Pi 5 with Home Assistant Core 2026.11.0. They confirmed a backup before updating and reported that the HACS companion integration was updated. The following numerical observations came from user-provided UI screenshots around the update. No original screenshots, hardware identifiers, IP/MAC addresses, personal information or backup content are stored here.

### Pre-update baseline (App/Card UI 3.1.37)
- CPU temperature: **49.6 °C** against a **49.0 °C** cooling target.
- Fan: **58% PWM**, **6027 RPM**.
- Supply voltage: **5.1456 V**.
- CPU profile: **Mild OC / 2500 MHz**.
- AI Cooling: **Assist**, **low workload bucket**, **97% confidence**, **1358 qualified samples**.
- Active Cooler calibration: **92 points**, **minimum safe PWM 9%** (subsequently confirmed in post-update UI).
- GPU: **Balanced**, 950/950/1000 MHz (subsequently confirmed in post-update UI).

### Post-update observations (App / Card UI 3.2.0)
- UI displays **3.2.0** for both App and Card UI; Raspberry Pi 5 system card indicates normal operation and matching requested/runtime cooling profile.
- CPU: **49.1 °C** against the same **49.0 °C** target.
- Fan: **49% PWM**, **5162 RPM**.
- Supply voltage: **5.1215 V**.
- CPU profile: **Mild OC / 2500 MHz**, preserved.
- AI Cooling: **Assist**, **low bucket**, **97% confidence**, **1358 qualified samples**, **45769 total observations**, bucket maturity **100%**.
- AI prediction: **50.9% effective**; near-time reported AI contribution **-2 percentage points** with physical PWM **54%** in one separate snapshot.
- Thermal Predictor: **Guided Assist active**, **83% confidence**, overall **MAE ~1.1 °C**, validated observations **242862**; horizon MAE +30s **0.964 °C**, +60s **1.307 °C**, +120s **1.071 °C**. In displayed example, requested/applied predictor PWM correction **0 pp / 0 pp** and decision `hot_forecast_unconfirmed`.
- Predictor's **75.8% observational effectiveness** is a historical diagnostic statistic, **not** independently verified physical improvement attributable to 3.2.0.
- Sample qualification can be **rejected** when temperature trend exceeds the threshold; such a rejected sample is not evidence of data loss.

### Follow-up screenshots (same installed 3.2.0, about 13:28 local time)
- **Active Cooler calibration preserved:** 1% PWM steps, startup **9%**, minimum safe **9%**, **92-point map**; normal system status and matching requested/runtime profile (**Custom 1, Balanced, 49 °C, Automatic**).
- **GPU profile preserved:** Balanced preset at **950/950/1000 MHz**, verified in expanded GPU/V3D/ISP section.
- **CPU Mild OC preserved:** configured/runtime maximum **2500 MHz**, verified in expanded CPU/OC section; instantaneous frequency can vary with load.
- **AI Cooling continues learning:** still **Assist**, low bucket, **96% direct/effective confidence**, qualified observations increased to **1359** from 1358 and total observations to **45794** from 45769; maturity **100%**. A one-point confidence change is ordinary variation, not evidence of model reset.
- **Cooling at follow-up:** CPU **49.6 °C**, **50% PWM**, **5268 RPM**, supply voltage **5.1376 V**; another near-time system-status view reports **56% PWM / 5742 RPM** at the same displayed CPU temperature as the control adjusts.

### Assessment
- **PASS, observed:** in-place App upgrade reached 3.2.0; cooling continued; Mild OC CPU and Balanced GPU profiles survived; 92-point Active Cooler calibration and AI mode/qualified learning data were retained.
- **USER-REPORTED, not independently checked:** HACS companion update completed to 3.2.0.
- **NOT YET VERIFIED:** longer-duration thermal behavior; backup-restore/rollback execution; fresh install on a second physical Raspberry Pi 5.
- **Important limitation:** lower fan speed/PWM with a slightly lower temperature is an encouraging snapshot, but different workloads may explain the difference. It is **not** causal proof of better cooling efficiency in 3.2.0.

### Release disclosure
Version 3.2.0 is a **community release**, not accepted into the official Home Assistant Apps catalog. The App requests broad host privileges; refer to `docs/SECURITY_PRIVILEGE_AUDIT_3_2_0.md`. No claim is made that a second-Pi clean installation or independent penetration test has been completed.

## Polski

### Zakres
Użytkownik wykonał aktualizację **3.1.37 → 3.2.0** na dotychczasowym Raspberry Pi 5 z Home Assistant Core 2026.11.0. Potwierdził wykonanie kopii zapasowej przed aktualizacją i poinformował o zaktualizowaniu integracji HACS. Podane parametry odczytano ze zrzutów interfejsu. Raport nie zawiera oryginalnych zrzutów, MAC/IP ani danych identyfikujących urządzenie.

### Przed aktualizacją
- Temperatura CPU **49,6°C**, cel **49,0°C**; wentylator **58% PWM / 6027 RPM**; zasilanie **5,1456 V**.
- CPU: **OC Łagodny 2500 MHz**.
- AI Cooling: **Assist**, **bucket low**, **97%** pewności, **1358** próbek jakościowych.
- Kalibracja Active Cooler: **92 punkty**, min. bezpieczny PWM **9%**; po aktualizacji wymaga ponownego potwierdzenia.
- GPU: **Zbalansowany 950/950/1000 MHz**; po aktualizacji wymaga ponownego potwierdzenia.

### Po aktualizacji
- Aplikacja i Card UI wskazują **3.2.0**; system pokazuje normalną pracę i zgodność profilu chłodzenia.
- CPU **49,1°C**, cel **49,0°C**; wentylator **49% PWM / 5162 RPM**; zasilanie **5,1215 V**.
- Zachowany profil **OC Łagodny 2500 MHz**.
- AI Cooling zachował **Assist**, **low**, **97%** pewności i **1358** próbek jakościowych; **45 769** obserwacji łącznie, dojrzałość bucketa **100%**.
- Thermal Predictor: **Guided Assist**, **83%** pewności, MAE średnie ok. **1,1°C**, **242 862** walidacje; MAE +30/+60/+120 s: **0,964 / 1,307 / 1,071°C**.
- W pokazanym cyklu TP zażądał i zastosował **0 pp** korekty PWM, przy decyzji `hot_forecast_unconfirmed`.
- Wynik **75,8%** skuteczności to metryka obserwacyjna, nie pomiar rzeczywistego zysku przypisanego wersji 3.2.0.

### Dodatkowa kontrola po aktualizacji (około 13:28 czasu lokalnego)
- **Kalibracja Active Cooler zachowana:** siatka PWM 1%, start 9%, bezpieczne minimum 9%, mapa **92 punktów**.
- **Profil GPU zachowany:** Zbalansowany **950/950/1000 MHz**, potwierdzony w rozwiniętym panelu GPU/V3D/ISP.
- **CPU zachowany:** OC Łagodny, zapisane i maksymalne taktowanie **2500 MHz**, potwierdzone w panelu CPU/OC.
- **AI nadal się uczy:** Assist, low, pewność direct/effective **96%**; liczba jakościowych wzrosła z 1358 do **1359**, a wszystkich obserwacji z 45 769 do **45 794**. Dojrzałość bucketa 100%.
- **Chłodzenie:** CPU **49,6°C**, PWM **50%**, wentylator **5268 RPM**, napięcie **5,1376 V**. Inny odczyt z tego samego okresu pokazuje PWM **56%** i **5742 RPM** przy tej samej wyświetlanej temperaturze CPU.

### Wniosek
**Pozytywnie potwierdzono aktualizację aplikacji oraz zachowanie podstawowego chłodzenia, kalibracji Active Cooler, profili CPU/GPU i danych AI.** Nadal niezweryfikowane są długoterminowa stabilność, przywrócenie kopii/rollback oraz czysta instalacja na niezależnym urządzeniu. Aktualizacja HACS została potwierdzona słownie przez użytkownika, a nie osobnym zrzutem wersji.

**Zastrzeżenie:** porównanie dwóch chwilowych odczytów przy różnym możliwym obciążeniu nie dowodzi poprawy efektywności chłodzenia po aktualizacji. Global Edition to wydanie społecznościowe, bez oficjalnego zatwierdzenia aplikacji przez Home Assistant.
