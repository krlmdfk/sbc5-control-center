# SBC5 Control Center 3.0.2

> Runtime efficiency hotfix: event-style local ZIP detection and correct Supervisor profile signature comparison eliminate redundant steady-state work.

## English

### Highlights

- Runtime efficiency hotfix: event-style local ZIP detection and correct Supervisor profile signature comparison eliminate redundant steady-state work.

### Changed

- Runtime efficiency hotfix: event-style local ZIP detection and correct Supervisor profile signature comparison eliminate redundant steady-state work.

### Fixed

- Canonicalized Supervisor profile signatures so unchanged native profile options no longer trigger false imports every reconciliation cycle.

### Performance & reliability

- Replaced full local ZIP parsing every two minutes with a lightweight filename/size/mtime signature; full ZIP validation now runs only when the local update directory actually changes.
- Adaptive PWM, AI Cooling, fan calibration and the verified 49°C boot curve are unchanged.

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

- Hotfix wydajności runtime: zdarzeniowe wykrywanie lokalnych ZIP i poprawne porównanie podpisu profili Supervisor eliminują zbędną pracę w stanie ustalonym.

### Zmieniono

- Hotfix wydajności runtime: zdarzeniowe wykrywanie lokalnych ZIP i poprawne porównanie podpisu profili Supervisor eliminują zbędną pracę w stanie ustalonym.

### Naprawiono

- Ujednolicono podpisy profili Supervisor, dzięki czemu niezmienione opcje natywne nie wywołują już pozornego importu w każdym cyklu uzgadniania.

### Wydajność i niezawodność

- Zastąpiono pełne parsowanie lokalnych ZIP co dwie minuty lekkim podpisem nazwa/rozmiar/mtime; pełna walidacja ZIP uruchamia się tylko po rzeczywistej zmianie katalogu aktualizacji.
- Adaptive PWM, AI Cooling, kalibracja wentylatora i zweryfikowana krzywa boot 49°C pozostają bez zmian.

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
