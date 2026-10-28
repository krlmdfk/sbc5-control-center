# SBC5 Control Center 3.1.11

> AI Cooling v5.1 learns bounded transient thermal evidence from short medium/high workload bursts without changing steady-state PWM predictions.

## English

### Highlights

- AI Cooling v5.1 learns bounded transient thermal evidence from short medium/high workload bursts without changing steady-state PWM predictions.

### Added

- AI Cooling v5.1 transient-response learning for short medium/high workload bursts.

### Changed

- Dynamic evidence raises transfer confidence only; it does not increment qualified counters or directly alter steady-state PWM prediction.

### Fixed

- Medium/high bursts rejected by the quasi-steady v4 qualifier can now contribute bounded learning evidence instead of being discarded completely.

### Performance & reliability

- No new polling loop; v5.1 runs inside the existing 10-second AI evaluator.

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

- AI Cooling v5.1 uczy się ograniczonych dowodów dynamicznej odpowiedzi cieplnej z krótkich obciążeń medium/high bez zmiany predykcji steady-state PWM.

### Dodano

- AI Cooling v5.1 z uczeniem odpowiedzi przejściowej dla krótkich obciążeń medium/high.

### Zmieniono

- Dowody dynamiczne zwiększają wyłącznie pewność transferu; nie zwiększają liczników qualified i nie zmieniają bezpośrednio predykcji steady-state PWM.

### Naprawiono

- Krótkie obciążenia medium/high odrzucone przez kwalifikator quasi-steady v4 mogą teraz wnosić ograniczony sygnał uczący zamiast być całkowicie pomijane.

### Wydajność i niezawodność

- Brak nowej pętli pollingu; v5.1 działa wewnątrz istniejącego ewaluatora AI co 10 s.

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
