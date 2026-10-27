# SBC5 Control Center 3.1.1

> Add AI Thermal Predictor telemetry to the main YAML dashboard card with responsive history-ready tiles.

## English

### Highlights

- Add AI Thermal Predictor telemetry to the main YAML dashboard card with responsive history-ready tiles.

### Added

- Main YAML dashboard card now shows AI Thermal Predictor forecasts for +30 s, +60 s and +120 s plus predictor confidence.

### Changed

- Thermal Predictor tiles use native More Info history and remain observe-only; Adaptive PWM and AI Cooling control behavior is unchanged.

### Fixed

- Card UI version markers are synchronized with the unified 3.1.1 release instead of the stale 2.8.34 marker.

### Performance & reliability

- No additional polling loop, frontend background renderer or host restart is introduced.

### Security

No security-specific changes.

### Upgrade notes

- No restart is required.
- Existing configuration and durable SBC5 state should be preserved unless a release-specific migration note says otherwise.

### Compatibility

- Raspberry Pi 5
- Home Assistant OS >= 18.3
- Home Assistant Core >= 2026.10.1
- Architecture: aarch64
- Companion HACS integration is distributed separately.

### Verification

- Repository validation and runtime tests must pass before publication.
- Release manifest hashes are verified in strict mode.
- The local-update ZIP is rebuilt and SHA-256 verified before upload.

### Downloads & links

- Main project: https://github.com/krlmdfk/sbc5-control-center
- HACS integration: https://github.com/krlmdfk/sbc5-control-center-integration
- Documentation: https://krlmdfk.github.io/sbc5-control-center/
- Release history: `CHANGELOG.md`
- Issues: https://github.com/krlmdfk/sbc5-control-center/issues

---

## Polski

### Najważniejsze zmiany

- Dodano telemetrię AI Thermal Predictor do głównej karty YAML w formie responsywnych kafelków z dostępem do historii.

### Dodano

- Główna karta YAML pokazuje prognozy AI Thermal Predictor +30 s, +60 s i +120 s oraz pewność predyktora.

### Zmieniono

- Kafelki Thermal Predictor korzystają z natywnej historii More Info i pozostają obserwacyjne; sterowanie Adaptive PWM i AI Cooling nie zostało zmienione.

### Naprawiono

- Znaczniki wersji Card UI są synchronizowane z wydaniem 3.1.1 zamiast starego oznaczenia 2.8.34.

### Wydajność i niezawodność

- Nie dodano dodatkowej pętli pollingu, procesu renderującego w tle ani wymogu restartu hosta.

### Bezpieczeństwo

Brak zmian dotyczących bezpieczeństwa.

### Informacje o aktualizacji

- Restart nie jest wymagany.
- Istniejąca konfiguracja i trwały stan SBC5 powinny zostać zachowane, o ile dana wersja nie zawiera osobnej informacji migracyjnej.

### Zgodność

- Raspberry Pi 5
- Home Assistant OS >= 18.3
- Home Assistant Core >= 2026.10.1
- Architektura: aarch64
- Integracja HACS jest dystrybuowana osobno.

### Weryfikacja

- Przed publikacją muszą przejść walidacja repozytorium i testy runtime.
- Hashe manifestu wydania są sprawdzane w trybie ścisłym.
- Lokalna paczka aktualizacji ZIP jest ponownie budowana i weryfikowana SHA-256 przed wysłaniem.

### Pobieranie i linki

- Projekt główny: https://github.com/krlmdfk/sbc5-control-center
- Integracja HACS: https://github.com/krlmdfk/sbc5-control-center-integration
- Dokumentacja: https://krlmdfk.github.io/sbc5-control-center/
- Historia wersji: `CHANGELOG.md`
- Zgłoszenia: https://github.com/krlmdfk/sbc5-control-center/issues
