# SBC5 Control Center 2.8.34

> Migration-routing hotfix: a completed legacy handoff no longer blocks exporting preserved stable state to a newer stopped Rust canary.

## English

### Highlights

- Migration-routing hotfix: a completed legacy handoff no longer blocks exporting preserved stable state to a newer stopped Rust canary.

### Changed

- Migration-routing hotfix: a completed legacy handoff no longer blocks exporting preserved stable state to a newer stopped Rust canary.

### Fixed

- Treat an already imported legacy handoff addressed to the current Store identity as historical when a newer stopped canary is available.
- Preserve the legacy backup and audit trail while allowing a fresh schema 2 canary handoff to be created.

### Security

- No fan-control, Adaptive PWM, AI Cooling, CPU/GPU profile or boot-control algorithm changes.

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

- Hotfix routingu migracji: zakończony starszy handoff nie blokuje już eksportu zachowanego stanu stabilnej aplikacji do nowszej zatrzymanej canary Rust.

### Zmieniono

- Hotfix routingu migracji: zakończony starszy handoff nie blokuje już eksportu zachowanego stanu stabilnej aplikacji do nowszej zatrzymanej canary Rust.

### Naprawiono

- Traktuj już zaimportowany starszy handoff skierowany do bieżącej instancji Store jako historyczny, gdy dostępna jest nowsza zatrzymana canary.
- Zachowaj starszy backup i ślad audytowy, jednocześnie umożliwiając utworzenie świeżego handoffu schema 2 do canary.

### Bezpieczeństwo

- Brak zmian algorytmów sterowania wentylatorem, Adaptive PWM, AI Cooling, profili CPU/GPU i konfiguracji boot.

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
