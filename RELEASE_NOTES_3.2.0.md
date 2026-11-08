# SBC5 Control Center 3.2.0

> Global Community Edition for Raspberry Pi 5: international installation guide, explicit host-access security disclosure and platform-specific installation.

## English

### Highlights

- Global Community Edition for Raspberry Pi 5: international installation guide, explicit host-access security disclosure and platform-specific installation.

### Added

- Document global installation, security review and mandatory real-device release gates in English and Polish.

### Changed

- Target raspberrypi5-64 explicitly to avoid offering the App on unsupported aarch64 boards.

### Security

- Disclose full_access, host_pid, AppArmor disablement and elevated Supervisor/kernel privileges; do not reduce privileges without hardware validation.

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

- Wydanie społecznościowe Global Edition dla Raspberry Pi 5: globalna instalacja, jawny audyt uprawnień i ograniczenie platformy docelowej.

### Dodano

- Dodano dwujęzyczną instrukcję instalacji globalnej, audyt bezpieczeństwa oraz wymagane testy na urządzeniu.

### Zmieniono

- Ograniczono dostępność aplikacji do raspberrypi5-64 zamiast wszystkich urządzeń aarch64.

### Bezpieczeństwo

- Jawnie opisano full_access, host_pid, wyłączenie AppArmor oraz uprawnienia Supervisor i systemu; bez zmiany uprawnień przed testami sprzętowymi.

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
