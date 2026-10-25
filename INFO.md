# SBC5 Control Center — Informacje

> Lokalne centrum sterowania, diagnostyki i konfiguracji Raspberry Pi 5 dla Home Assistant OS.

| Parametr | Wartość |
|---|---|
| Wersja aplikacji | **2.8.25** |
| Card UI | **2.8.25** |
| Stan | **stable** |
| Architektura | `aarch64` |
| Home Assistant OS | `>= 18.3` |
| Home Assistant Core | `>= 2026.10.1` |
| Licencja | Apache-2.0 |

## Przeznaczenie

SBC5 Control Center łączy obsługę Active Coolera, Adaptive PWM, lokalne AI Cooling, profile CPU/OC i GPU/V3D/ISP, zarządzanie `config.txt`, telemetrię sprzętową, Restart Manager oraz lokalne aktualizacje w jednym runtime działającym lokalnie na Raspberry Pi 5.

## Aktualny model pracy

- temperatura CPU, RPM i PWM: lekka ścieżka co **5 s**;
- Adaptive PWM i evaluator AI: cykl **10 s**;
- pełna telemetria natywnego bridge: **15 s**;
- kompaktowy transport AI: ocena co **15 s**, publikacja po zmianie i keepalive przy stanie stabilnym;
- duży relay zgodności hosta: **30 s**;
- diagnostyka systemowa: **60 s**;
- statyczna identyfikacja sprzętu i firmware: **300 s**;
- synchronizacja profili Supervisor: **30 s**.

Szybkie ścieżki sterowania chłodzeniem pozostają niezależne od cięższej diagnostyki. Encje transportowe host/AI są wyłączone z Recorder, a dane przeznaczone do historii mają osobne encje liczbowe.

## Chłodzenie

Active Cooler obsługuje profil fabryczny oraz konfigurowalny `custom1`. Adaptive PWM używa krzywej `custom1(T)` jako bezwzględnej bazy i stosuje ograniczony trim, deadband, anti-windup, Sign Guard oraz limiter szybkości zmian. Awaryjne sterowanie 100% pozostaje natychmiastowe.

AI Cooling działa lokalnie i wtórnie wobec klasycznego regulatora. Model rozróżnia buckety `idle`, `low`, `medium` i `high`, kwalifikuje próbki jakościowe oraz może pracować w ograniczonym trybie Assist.

## CPU, GPU i `config.txt`

Profile CPU/OC oraz GPU/V3D/ISP mają trwały stan żądany synchronizowany między Ingress, kartą Lovelace, `config.txt` i natywną Konfiguracją Home Assistanta. Rzeczywista zmiana parametrów boot powoduje żądanie pełnego restartu Raspberry Pi. Pliki zarządzane, w tym dedykowany profil CPU/OC, są porównywane semantycznie: sama zmiana wersji aplikacji lub komentarza nie powoduje restartu hosta.

## Interfejs Lovelace

Główna karta jest zoptymalizowana pod telefon. Sekcje o dużej liczbie szczegółów są domyślnie zwinięte i rozwijane przez kafelki:

- **SBC5 Control Center** — szczegóły aktualizacji i akcje;
- **AI Cooling** — diagnostyka uczenia, predykcji i siatki;
- **Zegar CPU** — częstotliwość i obciążenie CPU0–CPU3;
- **CPU / Overclocking** — wybór profilu po dotknięciu kafelka profilu;
- **GPU / V3D / ISP** — wybór presetu po dotknięciu kafelka profilu.

Kolejność części wydajnościowych jest celowa: wykres temperatury CPU/PWM → CPU / Overclocking → GPU/V3D/ISP.

## Identyfikacja urządzenia

Rejestr urządzeń Home Assistant otrzymuje model Raspberry Pi, rewizję płyty, wersję sprzętu, numer seryjny, MAC oraz wersję SBC5. Encje diagnostyczne udostępniają również system operacyjny, kernel, architekturę, firmware Raspberry Pi i bootloader EEPROM.

## Aktualizacje i Restart Manager

Lokalne paczki ZIP są sprawdzane przez manifest i SHA-256. Aktualizacja pełna może wymagać restartu Home Assistant, natomiast pełny restart Raspberry Pi jest zgłaszany wyłącznie wtedy, gdy wynikowa konfiguracja boot faktycznie się zmieniła.

## Dokumentacja

- `README.md` — przegląd projektu;
- `DOCUMENTATION.md` — pełna dokumentacja użytkowa i techniczna;
- `docs/QUICK_SETUP.md` — szybkie uruchomienie krok po kroku;
- `CHANGELOG.md` — historia zmian.
