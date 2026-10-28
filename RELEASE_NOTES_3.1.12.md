# SBC5 Control Center 3.1.12

> Expose AI Cooling v5.1 transient-learning evidence through the existing transfer diagnostics path without changing cooling behavior or adding polling.

## English

### Highlights

- Expose AI Cooling v5.1 transient-learning evidence through the existing transfer diagnostics path without changing cooling behavior or adding polling.

### Changed

- Expose AI Cooling v5.1 transient-learning evidence through the existing transfer diagnostics path without changing cooling behavior or adding polling.

### Fixed

- Expose transient confidence, sample count and support in the existing transfer_source telemetry token so medium/high burst learning is visible end to end.
- Keep the existing 22-field evaluator ABI intact; no run_legacy parser expansion or new telemetry loop is required.

### Performance & reliability

- No additional polling, Home Assistant REST reads or control-loop work is introduced.

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

- Udostępnia diagnostykę uczenia transient AI Cooling v5.1 przez istniejącą ścieżkę transferu bez zmiany sterowania chłodzeniem i bez dodatkowego pollingu.

### Zmieniono

- Udostępnia diagnostykę uczenia transient AI Cooling v5.1 przez istniejącą ścieżkę transferu bez zmiany sterowania chłodzeniem i bez dodatkowego pollingu.

### Naprawiono

- Udostępniono pewność transient, liczbę próbek i support w istniejącym tokenie transfer_source, dzięki czemu uczenie z krótkich obciążeń medium/high jest widoczne end-to-end.
- Zachowano istniejące 22-polowe ABI ewaluatora; nie rozszerzano parsera run_legacy ani nie dodawano nowej pętli telemetrii.

### Wydajność i niezawodność

- Nie dodano pollingu, odczytów REST Home Assistant ani dodatkowej pracy w pętli sterowania.

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
