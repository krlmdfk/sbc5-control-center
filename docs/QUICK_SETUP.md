# SBC5 Control Center — Quick Setup Guide

## 1. Wymagania

- Raspberry Pi 5 / `aarch64`;
- Home Assistant OS `>= 18.3`;
- Home Assistant Core `>= 2026.10.1`;
- Mushroom, card-mod i ApexCharts Card dla pełnej karty Lovelace.

## 2. Pierwszy start

1. Uruchom SBC5 Control Center.
2. Sprawdź `Platform Guard: OK`.
3. Sprawdź `Host Access: SUKCES`.
4. Zweryfikuj, czy urządzenie **SBC5 Control Center** jest widoczne w Home Assistant.
5. Jeśli package/integracja wymaga przeładowania, wykonaj restart Home Assistant.

## 3. Chłodzenie

1. Zacznij od trybu Automatic i zbalansowanej konfiguracji.
2. Wykonaj kalibrację Active Coolera.
3. Sprawdź RPM, PWM i temperaturę CPU.
4. Nie obniżaj minimalnego PWM poniżej stabilnej wartości wynikającej z kalibracji.

## 4. Karta Lovelace

Dodaj `dashboard/sbc5_control_center_diagnostics_card.yaml`. Opcjonalną kartę aktualizacji znajdziesz w `dashboard/update_status_card.yaml`.

Sekcje **SBC5 Control Center**, **AI Cooling** i **Zegar CPU** są domyślnie zwinięte. Dotknięcie kafelka rozwija szczegóły, ponowne dotknięcie je chowa.

## 5. CPU / OC

1. Otwórz sekcję pod wykresem temperatury CPU/PWM.
2. Dotknij kafelka profilu CPU, aby rozwinąć wybór i przycisk zastosowania.
3. Zacznij od profilu Balanced, jeśli potrzebujesz umiarkowanego OC.
4. Po realnej zmianie `config.txt` wykonaj pełny restart Raspberry Pi, jeśli zażąda go Restart Manager.
5. Po boot sprawdź zapisane i aktywne taktowanie.
6. Dotknij **Zegar CPU**, aby rozwinąć CPU0–CPU3.

## 6. GPU / V3D / ISP

1. Dotknij kafelka profilu GPU.
2. Wybierz preset.
3. Zastosuj profil.
4. Jeśli wynikowa konfiguracja boot się zmieniła, wykonaj pełny restart hosta.
5. Factory przywraca zarządzanie zegarami przez firmware.

## 7. AI Cooling

1. Włącz sekcję AI w konfiguracji aplikacji.
2. Pozostaw tryb Learning do zebrania próbek jakościowych.
3. Dotknij kafelka **AI Cooling**, aby zobaczyć dojrzałość bucketu, predykcję, kwalifikację próbki i siatkę.
4. Assist włączaj dopiero po uzyskaniu wystarczającej jakości danych.

## 8. Aktualizacje

1. Skopiuj paczkę ZIP do `/config/sbc5_control_center_updates/`.
2. Dotknij kafelka **SBC5 Control Center** na karcie aktualizacji.
3. Wybierz **Sprawdź teraz**.
4. Zainstaluj paczkę tylko po poprawnej weryfikacji.
5. Wykonaj wyłącznie restart wskazany przez Restart Manager.

Pełny restart Raspberry Pi nie jest wymagany przez samą zmianę numeru wersji; jest wymagany tylko po realnej zmianie konfiguracji boot.

## 9. Gdy coś nie działa

Sprawdź kolejno: log aplikacji → Host Access → Cooling Problem → zasilanie/throttling → Config Differs From Active → Restart Required → wersję package/Card UI.

Pełna dokumentacja: `DOCUMENTATION.md`.
