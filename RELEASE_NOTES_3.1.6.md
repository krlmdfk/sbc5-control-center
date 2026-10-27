# SBC5 Control Center 3.1.6

> Improve AI Thermal Predictor accuracy with closed-loop target anchoring and online per-horizon bias calibration while keeping Shadow Assist observe-only.

## English

### Highlights

- Improve AI Thermal Predictor accuracy with closed-loop target anchoring and online per-horizon bias calibration while keeping Shadow Assist observe-only.

### Changed

- Thermal Predictor v2 uses horizon-specific target anchoring and bounded signed online bias calibration for +30/+60/+120 s forecasts.
- Shadow Assist remains telemetry-only with control_output_enabled=false and the existing ±2 pp recommendation limit.

### Fixed

- Archive Predictor v1 quality statistics when migrating to v2 so historical errors cannot distort the new accuracy gate.

### Performance & reliability

- Reuse the existing AI runtime cadence; no new fast polling loop or physical PWM write path is added.

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

- Poprawa dokładności AI Thermal Predictor przez uwzględnienie zamkniętej pętli, dociąganie do celu termicznego i korektę błędu online dla każdego horyzontu przy zachowaniu Shadow Assist bez wpływu na PWM.

### Zmieniono

- Thermal Predictor v2 wykorzystuje zależne od horyzontu dociąganie do celu i ograniczoną znakowaną korektę błędu online dla prognoz +30/+60/+120 s.
- Shadow Assist pozostaje wyłącznie telemetryczny z control_output_enabled=false i dotychczasowym limitem rekomendacji ±2 pp.

### Naprawiono

- Archiwizacja statystyk jakości Predictora v1 podczas migracji do v2, aby historyczne błędy nie zafałszowały nowej bramki jakości.

### Wydajność i niezawodność

- Wykorzystanie istniejącego cyklu AI runtime bez nowej szybkiej pętli odpytywania i bez nowej ścieżki zapisu fizycznego PWM.

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
