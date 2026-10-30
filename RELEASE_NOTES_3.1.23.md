# SBC5 Control Center 3.1.23

> Fix Thermal Predictor guided-assist runtime wiring so forecast guidance is evaluated on every AI control cycle.

## English

### Highlights

- Fix Thermal Predictor guided-assist runtime wiring so forecast guidance is evaluated on every AI control cycle.

### Changed

- Fix Thermal Predictor guided-assist runtime wiring so forecast guidance is evaluated on every AI control cycle.

### Fixed

- Evaluate Thermal Predictor dynamic forecast, gate and decision on every AI assist cycle instead of only during model-learning candidate updates.
- Keep predictor correction bounded to ±2 pp and inside the existing AI assist-limit, min-safe and maximum envelope.
- Expose real weighted forecast, horizon weights and requested/applied predictor delta instead of zero fallback diagnostics.

### Performance & reliability

- No additional polling loop or background process is added; the predictor reuses the existing AI cycle.

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

- Naprawiono podłączenie Thermal Predictor guided assist w runtime, aby wskazówki prognozy były oceniane w każdym cyklu sterowania AI.

### Zmieniono

- Naprawiono podłączenie Thermal Predictor guided assist w runtime, aby wskazówki prognozy były oceniane w każdym cyklu sterowania AI.

### Naprawiono

- Thermal Predictor dynamic forecast, gate i decyzja są teraz oceniane w każdym cyklu AI assist, a nie tylko podczas aktualizacji kandydata modelu uczącego.
- Korekta predictora pozostaje ograniczona do ±2 pp oraz do istniejącego zakresu assist-limit, min-safe i maximum.
- Diagnostyka pokazuje rzeczywistą prognozę ważoną, wagi horyzontów i żądaną/zastosowaną korektę zamiast wartości zerowych z fallbacku.

### Wydajność i niezawodność

- Nie dodano nowej pętli odpytywania ani procesu w tle; predictor wykorzystuje istniejący cykl AI.

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
