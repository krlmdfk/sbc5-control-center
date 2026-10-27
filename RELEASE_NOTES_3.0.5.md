# SBC5 Control Center 3.0.5

> Rust canary runtime fix: recover orphaned Adaptive PWM thermal ownership and render Card UI with the current release version before Lovelace synchronization.

## English

### Highlights

- Rust canary runtime fix: recover orphaned Adaptive PWM thermal ownership and render Card UI with the current release version before Lovelace synchronization.

### Changed

- Rust canary runtime fix: recover orphaned Adaptive PWM thermal ownership and render Card UI with the current release version before Lovelace synchronization.

### Fixed

- Adopt a safe orphaned mode=disabled thermal zone when custom1 is active, max_state is 100+, cur_state is writable and namespace migration is COMPLETE.
- Render packaged dashboard card version dynamically so automatic Lovelace verification no longer rolls back to the old Card UI literal.

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

- Poprawka runtime Rust canary: odzyskiwanie osieroconego przejęcia termicznego Adaptive PWM oraz dynamiczna wersja Card UI przed synchronizacją Lovelace.

### Zmieniono

- Poprawka runtime Rust canary: odzyskiwanie osieroconego przejęcia termicznego Adaptive PWM oraz dynamiczna wersja Card UI przed synchronizacją Lovelace.

### Naprawiono

- Bezpiecznie adoptuj osierocony thermal zone mode=disabled, gdy custom1 jest aktywny, max_state wynosi co najmniej 100, cur_state jest zapisywalny i migracja namespace ma stan COMPLETE.
- Dynamicznie podstawiaj wersję wzorca dashboardu, aby weryfikacja Lovelace nie cofała synchronizacji przez stary literal Card UI.

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
