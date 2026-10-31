# SBC5 Control Center 3.1.29

> Stabilize Adaptive PWM and Thermal Predictor decisions with a raw-versus-control temperature path, spike filtering, asymmetric smoothing, 30/120-second trend confirmation and direction hysteresis.

## English

### Highlights

- Stabilize Adaptive PWM and Thermal Predictor decisions with a raw-versus-control temperature path, spike filtering, asymmetric smoothing, 30/120-second trend confirmation and direction hysteresis.

### Added

- Add T_raw/T_control diagnostics, 30/120-second thermal trends, signal quality, spike rejection and confirmed thermal direction to Adaptive PWM runtime state.

### Changed

- Use median-of-3 plus asymmetric EWMA for normal Adaptive PWM control while preserving raw CPU temperature as the authoritative safety and emergency signal.
- Require Thermal Predictor forecast direction to agree with robust short/long temperature trends before a guided PWM correction is allowed.

### Fixed

- Prevent isolated temperature spikes and short cooling dips from causing rapid PWM direction reversals or unnecessary fan hunting near the target.

### Performance & reliability

- Reuse the existing 10-second Adaptive PWM cycle; no additional background polling loop is introduced.

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

- Stabilizuje decyzje Adaptive PWM i Thermal Predictora przez rozdzielenie temperatury surowej i sterującej, filtr pików, asymetryczne wygładzanie, potwierdzanie trendu 30/120 s oraz bezwładność zmiany kierunku.

### Dodano

- Dodaje diagnostykę T_raw/T_control, trendy termiczne 30/120 s, jakość sygnału, odrzucanie pików i potwierdzony kierunek termiczny do stanu runtime Adaptive PWM.

### Zmieniono

- W zwykłym sterowaniu Adaptive PWM używa mediany z 3 próbek i asymetrycznego EWMA, zachowując surową temperaturę CPU jako nadrzędny sygnał bezpieczeństwa i awaryjnego handoffu.
- Wymaga zgodności kierunku prognozy Thermal Predictora z odpornymi trendami krótkim i długim przed dopuszczeniem korekty PWM.

### Naprawiono

- Ogranicza wpływ pojedynczych pików temperatury i krótkich spadków na szybkie odwracanie kierunku PWM oraz oscylacje wentylatora w pobliżu temperatury docelowej.

### Wydajność i niezawodność

- Wykorzystuje istniejący 10-sekundowy cykl Adaptive PWM; nie dodaje nowej pętli odpytywania w tle.

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
