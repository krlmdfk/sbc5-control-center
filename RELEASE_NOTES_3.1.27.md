# SBC5 Control Center 3.1.27

> Recover the REST-backed AI Runtime relay immediately after Home Assistant Core restarts, preventing temporary unavailable AI and Thermal Predictor sensors.

## English

### Highlights

- Recover the REST-backed AI Runtime relay immediately after Home Assistant Core restarts, preventing temporary unavailable AI and Thermal Predictor sensors.

### Changed

- Recover the REST-backed AI Runtime relay immediately after Home Assistant Core restarts, preventing temporary unavailable AI and Thermal Predictor sensors.

### Fixed

- Detect a missing sensor.sbc5_control_center_ai_runtime on the existing 30-second relay cadence and republish it without waiting for the 5-minute keepalive.

### Performance & reliability

- No additional background loop; the existence probe reuses the existing AI relay cadence and does not change cooling control.

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

- Natychmiast odtwarza relay AI Runtime oparty o REST po restarcie Home Assistant Core, eliminując czasową niedostępność sensorów AI i Thermal Predictora.

### Zmieniono

- Natychmiast odtwarza relay AI Runtime oparty o REST po restarcie Home Assistant Core, eliminując czasową niedostępność sensorów AI i Thermal Predictora.

### Naprawiono

- Wykrywa brak sensor.sbc5_control_center_ai_runtime w istniejącym 30-sekundowym cyklu relay i publikuje go ponownie bez oczekiwania na 5-minutowy keepalive.

### Wydajność i niezawodność

- Bez dodatkowej pętli w tle; sprawdzenie istnienia encji wykorzystuje istniejący cykl AI relay i nie zmienia sterowania chłodzeniem.

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
