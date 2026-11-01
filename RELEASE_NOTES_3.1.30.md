# SBC5 Control Center 3.1.30

> Stabilize Thermal Predictor control decisions with conditioned forecasts, confirmation guards and richer diagnostics while preserving the existing AI authority limits.

## English

### Highlights

- Stabilize Thermal Predictor control decisions with conditioned forecasts, confirmation guards and richer diagnostics while preserving the existing AI authority limits.

### Added

- Thermal Predictor Stability v2 with median-of-3 weighted-forecast conditioning and EMA smoothing.
- Persistent two-cycle hot/cool forecast confirmation with a bounded high-quality fast path.
- Detailed thermal-state diagnostics including raw, median and stable forecasts plus confirmation state.

### Changed

- Thermal Predictor now uses the filtered control temperature and the 30-second control trend when available.
- Positive predictor corrections are suppressed during rapid cooling and negative corrections during rapid heating unless a strong confirmed forecast qualifies for override.

### Performance & reliability

- No new polling loop or background process is added; Stability v2 advances inside the existing AI Cooling cycle.

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

- Stabilizacja decyzji Thermal Predictora przez kondycjonowanie prognoz, guardy potwierdzeń i bogatszą diagnostykę przy zachowaniu dotychczasowych limitów wpływu AI.

### Dodano

- Thermal Predictor Stability v2 z kondycjonowaniem ważonej prognozy medianą z 3 próbek i wygładzaniem EMA.
- Trwałe dwucyklowe potwierdzanie prognoz hot/cool z ograniczoną szybką ścieżką dla prognoz wysokiej jakości.
- Szczegółowa diagnostyka stanu termicznego obejmująca prognozę surową, medianę, prognozę stabilną i stan potwierdzenia.

### Zmieniono

- Thermal Predictor korzysta teraz z filtrowanej temperatury sterującej i 30-sekundowego trendu sterującego, gdy są dostępne.
- Dodatnie korekty predyktora są blokowane podczas szybkiego chłodzenia, a ujemne podczas szybkiego grzania, chyba że silna potwierdzona prognoza spełnia warunki wyjątku.

### Wydajność i niezawodność

- Nie dodano nowej pętli odpytywania ani procesu w tle; Stability v2 działa w istniejącym cyklu AI Cooling.

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
