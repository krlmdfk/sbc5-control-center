# SBC5 Control Center 3.1.5

> Add AI Thermal Predictor Shadow Assist to evaluate bounded predictive PWM corrections before control activation.

## English

### Highlights

- Add AI Thermal Predictor Shadow Assist to evaluate bounded predictive PWM corrections before control activation.

### Added

- Add Thermal Predictor Shadow Assist with hypothetical PWM correction telemetry, activation gate diagnostics and weighted 30/60/120-second thermal forecast.
- Expose native Home Assistant Shadow Assist sensors for suggested delta, hypothetical PWM, gate state, decision reason and weighted forecast.

### Changed

- Gate future predictive control on automatic mode, good/excellent Predictor quality, confidence >=80%, average MAE <=1.25 C and at least 8 validated forecasts per horizon.
- Bound every Shadow Assist recommendation to +/-2 percentage points and prevent negative prediction corrections while temperature trend is rising.

### Performance & reliability

- Reuse the existing AI evaluator, thermal windows, relay and Home Assistant coordinator; no new polling loop or control write path is added.

### Security

- Shadow Assist remains telemetry-only: control_output_enabled=false; Adaptive PWM and AI Cooling remain authoritative and all physical fan writes are unchanged.

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

- Dodano AI Thermal Predictor Shadow Assist do oceny ograniczonych korekt predykcyjnych PWM przed aktywacją sterowania.

### Dodano

- Dodano Thermal Predictor Shadow Assist z telemetrią hipotetycznej korekty PWM, diagnostyką bramki aktywacji i ważoną prognozą temperatury 30/60/120 s.
- Udostępniono natywne sensory Home Assistant Shadow Assist: sugerowana delta, hipotetyczny PWM, stan bramki, powód decyzji i prognoza ważona.

### Zmieniono

- Przyszłe sterowanie predykcyjne jest blokowane do czasu spełnienia warunków: tryb automatyczny, jakość Predictora good/excellent, confidence >=80%, średnie MAE <=1,25 C i co najmniej 8 zweryfikowanych prognoz na każdy horyzont.
- Każda rekomendacja Shadow Assist jest ograniczona do +/-2 pp, a ujemna korekta predykcyjna jest blokowana przy rosnącym trendzie temperatury.

### Wydajność i niezawodność

- Wykorzystano istniejący evaluator AI, okna termiczne, relay i koordynator Home Assistant; nie dodano nowej pętli pollingowej ani ścieżki zapisu sterowania.

### Bezpieczeństwo

- Shadow Assist pozostaje wyłącznie telemetrią: control_output_enabled=false; Adaptive PWM i AI Cooling pozostają nadrzędne, a fizyczne zapisy wentylatora nie zostały zmienione.

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
