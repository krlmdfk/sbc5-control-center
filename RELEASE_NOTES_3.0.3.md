# SBC5 Control Center 3.0.3

> Reduce steady-state log I/O while preserving Adaptive PWM and AI execution cadence.

## English

### Highlights

- Reduce steady-state log I/O while preserving Adaptive PWM and AI execution cadence.

### Changed

- Expose the effective control-log sampling and AI-log keepalive policy in the startup Performance line.

### Performance & reliability

- Sample routine Adaptive PWM write logs while preserving immediate safety/action logs and unchanged 10-second control execution.
- Reduce AI Cooling steady-state logging to state/model changes plus a 5-minute keepalive; evaluator cadence remains unchanged.

### Security

- Safety-critical ownership, write-failure, fast-response and sign-guard logs remain immediate.

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

- Ograniczenie I/O logów w stanie ustalonym bez zmiany częstotliwości działania Adaptive PWM i AI.

### Zmieniono

- Pokazanie efektywnej polityki próbkowania logów regulatora i keepalive AI w linii Performance przy starcie.

### Wydajność i niezawodność

- Próbkowanie rutynowych logów zapisów Adaptive PWM przy zachowaniu natychmiastowych logów bezpieczeństwa i niezmienionego cyklu sterowania 10 s.
- Ograniczenie logów AI Cooling w stanie ustalonym do zmian stanu/modelu i 5-minutowego keepalive; częstotliwość ewaluatora pozostaje bez zmian.

### Bezpieczeństwo

- Krytyczne logi ownership, błędów zapisu, szybkiej reakcji i sign-guard pozostają natychmiastowe.

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
