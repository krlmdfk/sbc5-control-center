# SBC5 Control Center 3.1.9

> Fix Restart Manager startup race and duplicate HACS restart repairs while keeping AI Cooling v5 unchanged.

## English

### Highlights

- Fix Restart Manager startup race and duplicate HACS restart repairs while keeping AI Cooling v5 unchanged.

### Changed

- Refresh Adaptive PWM startup diagnostics to show +8 pp thermal-fast, +12 pp thermal-critical and -5 pp fast-down limits.

### Fixed

- Distinguish a package already synchronized on disk from an older package version still loaded by Home Assistant Core.
- Suppress the duplicate SBC5 native Repair when HACS already owns and has installed the matching bridge version.

### Performance & reliability

- No new polling loop; restart ownership checks only reuse existing startup/restart evaluation.

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

- Naprawa wyścigu Restart Managera przy starcie i podwójnych zgłoszeń restartu HACS bez zmian w AI Cooling v5.

### Zmieniono

- Zaktualizowano diagnostykę startową Adaptive PWM: +8 pp thermal-fast, +12 pp thermal-critical i -5 pp fast-down.

### Naprawiono

- Rozróżniono package już zsynchronizowany na dysku od starszej wersji nadal załadowanej w Home Assistant Core.
- Usunięto podwójny Repair SBC5, gdy HACS zarządza integracją i ma już zainstalowaną zgodną wersję bridge.

### Wydajność i niezawodność

- Bez nowej pętli pollingu; sprawdzenie własności restartu wykorzystuje istniejącą ścieżkę startową/Restart Managera.

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
