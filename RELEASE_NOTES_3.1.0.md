# SBC5 Control Center 3.1.0

> Introduce AI Thermal Predictor as an observe-only short-horizon temperature forecasting module.

## English

### Highlights

- Introduce AI Thermal Predictor as an observe-only short-horizon temperature forecasting module.

### Added

- AI Thermal Predictor forecasts CPU temperature 30, 60 and 120 seconds ahead without controlling PWM.
- Online forecast validation measures prediction MAE and derives predictor confidence from real runtime outcomes.
- Recorder-friendly Home Assistant sensors expose 30/60/120-second forecasts and predictor confidence.

### Changed

- Adaptive PWM and AI Cooling remain authoritative; Thermal Predictor is observe-only in 3.1.0.

### Performance & reliability

- Thermal Predictor reuses the existing 10-second AI evaluation cycle and temperature window; no extra polling loop or background process is introduced.

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

- Wprowadzono AI Thermal Predictor jako obserwacyjny moduł krótkoterminowej prognozy temperatury.

### Dodano

- AI Thermal Predictor prognozuje temperaturę CPU z wyprzedzeniem 30, 60 i 120 sekund bez sterowania PWM.
- Walidacja online mierzy błąd MAE prognoz i wylicza confidence predyktora na podstawie rzeczywistych wyników runtime.
- Dodano sensory Home Assistant przyjazne Recorderowi dla prognoz 30/60/120 s oraz confidence predyktora.

### Zmieniono

- Adaptive PWM i AI Cooling pozostają nadrzędne; Thermal Predictor w 3.1.0 działa wyłącznie obserwacyjnie.

### Wydajność i niezawodność

- Thermal Predictor wykorzystuje istniejący 10-sekundowy cykl AI i okno temperatury; nie dodaje nowej pętli pollingu ani osobnego procesu.

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
