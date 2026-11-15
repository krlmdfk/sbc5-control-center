# SBC5 Control Center 3.2.4 — Odbiór sprzętowy / Hardware acceptance

**Status: NOT VERIFIED — owner-operated Raspberry Pi 5 testing pending.**

This document records the required checks for declaring 3.2.4 *stable*. GitHub Actions CI cannot replace real-device evidence. The developer maintains code/CI; the Raspberry Pi 5 owner performs all physical tests. Do not set `hardware_verified=true` until the checks relevant to the actual deployment and recovery path have been completed.

## A. Dowody przed aktualizacją

- [ ] Zapisano dokładne wersje SBC5 App, HACS integration, Home Assistant Core i HA OS.
- [ ] Potwierdzono kopię Home Assistant **i rzeczywistą możliwość odzyskania danych**. (Kopia została zadeklarowana przez właściciela, test odtworzenia nie jest potwierdzony.)
- [ ] Zapisano istniejące nastawy: CPU/GPU, profil `custom1`, temperaturę docelową, tryb PWM i ustawienia AI Cooling/Adaptive PWM.
- [ ] Zachowano niezależną kopię pliku modelu AI z właściwego kontenera aplikacji i jego SHA-256; nie kopiować jej publicznie.
- [ ] Sprawdzono fizyczny wentylator i przygotowano bezpieczną procedurę powrotu do poprzedniej wersji.
- [ ] Zanotowano **pre-update**: temperaturę CPU, rzeczywisty PWM, RPM i stan regulatora przy normalnym obciążeniu.

## B. Testy automatyczne — odpowiedzialność deweloperska

- [x] CI `Validate build` i App/HACS companion parity dla PR przygotowującego ścieżkę 3.2.4: zaliczone 2026-11-15.
- [x] Zabezpieczenie publikacji `stable` pozostaje uzależnione od jawnego `hardware_verified=true`.
- [x] Wydanie `field_test` pozostaje osobnym kanałem i wymaga potwierdzenia kopii oraz ryzyka.
- [ ] Walidacja `release_prepare.py` **dla dokładnej wersji 3.2.4** ze zaktualizowanym manifestem.
- [ ] Strict manifest SHA-256, ZIP integrity, ZIP security preflight **dla końcowego kandydata 3.2.4**.
- [ ] HACS ZIP 3.2.4: `manifest.json`, `download_counts.py`, zgodne wydanie i właściwy `filename`/`zip_release`.
- [ ] Zweryfikowana tożsamość źródeł App i HACS oraz zachowanie publikacji do dwóch repozytoriów.

## C. Testy na Twoim Raspberry Pi 5 — odpowiedzialność właściciela

Testuj tylko zweryfikowaną paczkę wydaniową; nie instaluj archiwum CI oznaczonego jako *offline inspection only*.

- [ ] Zmiana wersji aplikacji oraz integracji do 3.2.4 jest widoczna; nie ma rozbieżnych wersji.
- [ ] Po aktualizacji działają sensory temperatury CPU, PWM i RPM; wentylator pracuje bezpiecznie w normalnym zakresie.
- [ ] Zachowano profil `custom1`, konfigurację CPU/GPU, docelową temperaturę i wszystkie ustawienia regulatora.
- [ ] AI Cooling i Thermal Predictor czytają dotychczasowy model; liczniki uczenia nie zostały niespodziewanie wyzerowane.
- [ ] Logi nie wskazują nieoczekiwanych zmian właściciela PWM, błędów migracji ani błędów konfiguracji sterowania.
- [ ] Sensory pobrań ZIP: `sensor.sbc5_app_release_downloads` i `sensor.sbc5_hacs_release_downloads` dają wartości albo prawidłowy stan braku danych.
- [ ] W HACS integracja ma właściwą wersję; rozumiesz, że „Downloaded X times” jest statystyką pobrań **wybranego wydania ZIP**, a nie sumą historycznych instalacji.
- [ ] Restart aplikacji i Home Assistant nie powoduje utraty modelu AI, ustawień ani encji.
- [ ] Potwierdzono scenariusz bezpiecznego przywrócenia 3.2.3 i danych **bez wywoływania resetowania modelu AI**.

## D. Końcowa decyzja o `stable`

| Pole | Wynik |
| --- | --- |
| Commit i SHA-256 paczki 3.2.4 | NOT VERIFIED |
| Końcowe CI, HACS, manifest i ZIP | NOT VERIFIED |
| Test na rzeczywistym RPi5 | NOT VERIFIED |
| Zachowanie modelu AI i PWM | NOT VERIFIED |
| Odzyskiwanie / rollback | NOT VERIFIED |
| Decyzja właściciela o publikacji stabilnej | NOT VERIFIED |

**Zasada:** udane PR/CI i wykonana kopia nie stanowią potwierdzenia testu sprzętowego. Ustaw `hardware_verified=true` wyłącznie po rzeczywistym, udokumentowanym odbiorze na Raspberry Pi 5. Nie prowokuj przegrzania ani awarii regulatora w ramach tych testów.
