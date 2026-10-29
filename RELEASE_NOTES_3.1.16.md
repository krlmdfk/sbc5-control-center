# SBC5 Control Center 3.1.16

> Introduce Thermal Predictor v3 with regime-aware dual-slope forecasting and context-safe online calibration.

## English

### Highlights

- Introduce Thermal Predictor v3 with regime-aware dual-slope forecasting and context-safe online calibration.

### Added

- Thermal Predictor v3 with separate fast and slow temperature trends that persist across workload bucket changes.
- Per-bucket and per-horizon calibration for LOW, MEDIUM and HIGH operating regimes.

### Changed

- Forecasts now account for CPU workload context, physical PWM state and recent context deltas instead of relying mainly on one temperature slope.
- Quality scoring weights +30 s and +60 s forecasts more strongly while still tracking +120 s accuracy separately.

### Fixed

- Prevented workload-bucket transitions from erasing the thermal trend history used by the predictor.
- Context-shift guard prevents abrupt CPU/PWM changes from contaminating predictor bias and MAE calibration.

### Performance & reliability

- Thermal Predictor v3 remains observe-only and adds no new polling loop or physical PWM authority.

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

- Wprowadzono Thermal Predictor v3 z predykcją zależną od reżimu pracy, dwoma trendami temperatury i bezpieczną kalibracją kontekstową.

### Dodano

- Thermal Predictor v3 z osobnym szybkim i wolnym trendem temperatury, zachowywanym przy zmianach bucketów obciążenia.
- Kalibrację per bucket i per horyzont dla reżimów LOW, MEDIUM i HIGH.

### Zmieniono

- Prognozy uwzględniają teraz kontekst obciążenia CPU, fizyczny PWM i ostatnie zmiany kontekstu zamiast opierać się głównie na jednym trendzie temperatury.
- Ocena jakości mocniej uwzględnia prognozy +30 s i +60 s, zachowując osobne monitorowanie dokładności +120 s.

### Naprawiono

- Zmiana bucketu obciążenia nie zeruje już historii trendu temperatury używanej przez Predictor.
- Context-shift guard zapobiega zanieczyszczaniu kalibracji bias/MAE przez nagłe zmiany obciążenia CPU lub PWM.

### Wydajność i niezawodność

- Thermal Predictor v3 pozostaje w trybie observe-only, bez nowej pętli pollingu i bez wpływu na fizyczne sterowanie PWM.

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
