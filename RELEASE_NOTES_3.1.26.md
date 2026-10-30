# SBC5 Control Center 3.1.26

> Persist Thermal Predictor effectiveness diagnostics across add-on and process restarts without changing cooling policy.

## English

### Highlights

- Persist Thermal Predictor effectiveness diagnostics across add-on and process restarts without changing cooling policy.

### Changed

- Persist Thermal Predictor effectiveness diagnostics across add-on and process restarts without changing cooling policy.

### Fixed

- Persist Thermal Predictor effectiveness counters, pending observations and 30/60/120-second horizon results in a dedicated atomic checkpoint.
- Migrate the 3.1.25 schema-1 effectiveness state without losing collected diagnostic evidence.

### Performance & reliability

- No additional polling loop or background worker; persistence runs only when effectiveness state changes.

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

- Zachowano statystyki skuteczności Thermal Predictora między restartami aplikacji i procesu bez zmiany polityki chłodzenia.

### Zmieniono

- Zachowano statystyki skuteczności Thermal Predictora między restartami aplikacji i procesu bez zmiany polityki chłodzenia.

### Naprawiono

- Dodano trwały atomowy checkpoint dla liczników skuteczności Thermal Predictora, oczekujących obserwacji oraz wyników 30/60/120 s.
- Dodano migrację stanu skuteczności schema 1 z wersji 3.1.25 bez utraty zebranych danych diagnostycznych.

### Wydajność i niezawodność

- Bez dodatkowej pętli odpytywania i procesu w tle; zapis trwały wykonywany jest tylko po zmianie stanu skuteczności.

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
