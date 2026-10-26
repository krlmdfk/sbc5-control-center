# SBC5 Control Center 3.0.1

> Rust canary validation build fixing persistence of the complete migrated Supervisor option set across App restarts.

## English

### Highlights

- Rust canary validation build fixing persistence of the complete migrated Supervisor option set across App restarts.

### Changed

- Rust canary validation build fixing persistence of the complete migrated Supervisor option set across App restarts.

### Fixed

- Persist the complete imported option tree to the target canary Supervisor store before migration guard finalization.
- Preserve imported 49°C custom1, AI Assist and other migrated App options across canary container restarts.

### Security

- Stable 2.8.34 and main are unchanged; this build remains isolated to the manual experimental Rust canary.

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

- Testowy build Rust canary naprawiający trwałość pełnego zestawu opcji zmigrowanych do Supervisor po restartach aplikacji.

### Zmieniono

- Testowy build Rust canary naprawiający trwałość pełnego zestawu opcji zmigrowanych do Supervisor po restartach aplikacji.

### Naprawiono

- Zapisuj pełne drzewo zaimportowanych opcji do trwałego magazynu Supervisor canary przed finalizacją guardu migracji.
- Zachowuj po restartach canary zmigrowane ustawienia custom1 49°C, AI Assist oraz pozostałe opcje aplikacji.

### Bezpieczeństwo

- Stabilna 2.8.34 i main pozostają bez zmian; build jest nadal odizolowany do ręcznej eksperymentalnej Rust canary.

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
