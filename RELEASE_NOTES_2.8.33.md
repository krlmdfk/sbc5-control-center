# SBC5 Control Center 2.8.33

> Maintenance release adding a verified, fail-closed durable-state handoff for safe Rust 3.0.0 canary migration; cooling and AI control behavior is unchanged.

## English

### Highlights

- Maintenance release adding a verified, fail-closed durable-state handoff for safe Rust 3.0.0 canary migration; cooling and AI control behavior is unchanged.

### Added

- Added schema-2 durable-state handoff for stable Store to newer stopped canary instances with exact target, target-version and SHA-256 fingerprint validation.

### Changed

- Stable 2.8.x Store instances can act as read-only migration sources for an installed newer canary without deprecating or modifying their private /data state.

### Fixed

- Foreign or stale migration handoffs are ignored instead of being treated as destructive import failures; a targeted canary waits fail-closed while the stable source is running or verification is incomplete.

### Security

- Canary import is restricted to an allow-list of durable state files and requires exact per-file SHA-256 hashes plus a complete aggregate fingerprint before data is accepted.

### Upgrade notes

- Restart Home Assistant after installation/update.
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

- Wydanie serwisowe dodające zweryfikowany, bezpiecznie blokowany handoff trwałego stanu do testowej migracji Rust 3.0.0; działanie chłodzenia i sterowania AI pozostaje bez zmian.

### Dodano

- Dodano handoff trwałego stanu schema 2 ze stabilnej instancji Store do nowszej zatrzymanej instancji canary, z dokładną walidacją celu, wersji docelowej i fingerprintu SHA-256.

### Zmieniono

- Stabilna instancja Store 2.8.x może działać jako źródło migracji tylko do odczytu dla zainstalowanej nowszej wersji canary, bez deprecjonowania ani modyfikowania własnego prywatnego /data.

### Naprawiono

- Obce lub nieaktualne handoffy migracyjne są ignorowane zamiast powodować destrukcyjne błędy importu; docelowa instancja canary oczekuje w trybie fail-closed, gdy stabilne źródło działa lub weryfikacja nie jest kompletna.

### Bezpieczeństwo

- Import canary jest ograniczony do listy dozwolonych plików trwałego stanu i wymaga dokładnych hashy SHA-256 każdego pliku oraz pełnego fingerprintu zbiorczego przed zaakceptowaniem danych.

### Informacje o aktualizacji

- Po instalacji/aktualizacji uruchom ponownie Home Assistant.
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
