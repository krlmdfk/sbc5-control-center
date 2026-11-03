# SBC5 Control Center 3.1.34

> Synchronize the SBC5 App and bundled integration with reviewed HACS Integration 3.1.34; protect other integrations from AI predictor migration cleanup.

## English

### Highlights

- Synchronize the SBC5 App and bundled integration with reviewed HACS Integration 3.1.34; protect other integrations from AI predictor migration cleanup.

### Changed

- Align App runtime metadata, package, Card UI, embedded integration, release notes and update-manifest hashes with HACS 3.1.34.

### Fixed

- Restrict AI Thermal Predictor migration to exact unique IDs owned by the legacy template platform; never remove unrelated integrations.

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

- Synchronizacja aplikacji SBC5 i dołączonej integracji z HACS 3.1.34; ochrona encji innych integracji podczas migracji AI Predictora.

### Zmieniono

- Ujednolicono metadane runtime, pakiet, Card UI, zintegrowany kod, notatki wydania i sumy kontrolne z HACS 3.1.34.

### Naprawiono

- Ograniczono migrację AI Thermal Predictora do identyfikatorów legacy platformy template; bez usuwania encji innych integracji.

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
