# SBC5 Control Center 3.1.24

> Align Thermal Predictor diagnostics and dashboard with the active guided-assist runtime without changing cooling control policy.

## English

### Highlights

- Align Thermal Predictor diagnostics and dashboard with the active guided-assist runtime without changing cooling control policy.

### Changed

- Align Thermal Predictor diagnostics and dashboard with the active guided-assist runtime without changing cooling control policy.

### Fixed

- Report Thermal Predictor requested/applied delta separately from the overall AI correction in runtime logs.
- Replace stale observe-only dashboard copy with the real guided-assist gate and control-output state.
- Expose weighted forecast, forecast error, horizon weights, gate reason and decision reason on the dashboard.

### Performance & reliability

- No new polling loop or control calculation was added; the hotfix reuses data already produced by the existing AI cycle.

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

- Ujednolicono diagnostykę i kartę Thermal Predictora z aktywnym runtime guided-assist bez zmiany polityki sterowania chłodzeniem.

### Zmieniono

- Ujednolicono diagnostykę i kartę Thermal Predictora z aktywnym runtime guided-assist bez zmiany polityki sterowania chłodzeniem.

### Naprawiono

- Rozdzielono w logach korektę żądaną/zastosowaną przez Thermal Predictor od całkowitej korekty AI.
- Zastąpiono nieaktualny tekst observe-only rzeczywistym stanem gate i wpływu guided-assist.
- Dodano na karcie prognozę ważoną, błąd, wagi horyzontów, powód gate i powód decyzji.

### Wydajność i niezawodność

- Nie dodano nowej pętli odpytywania ani obliczeń sterujących; hotfix wykorzystuje dane już generowane w istniejącym cyklu AI.

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
