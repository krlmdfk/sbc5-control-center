# SBC5 Control Center 3.1.15

> Fix sparse-bucket AI diagnostics in Card UI without changing cooling control or learning.

## English

### Highlights

- Fix sparse-bucket AI diagnostics in Card UI without changing cooling control or learning.

### Changed

- Transient learning c/n/s diagnostics are shown on a separate readable line in the AI prediction tile.

### Fixed

- Card UI no longer substitutes effective/general confidence for direct confidence when a bucket has zero qualified samples.
- Direct PWM prediction now renders as an em dash when no direct model prediction exists.

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

- Naprawiono diagnostykę AI dla rzadkich bucketów w Card UI bez zmian sterowania chłodzeniem ani uczenia.

### Zmieniono

- Diagnostyka transient learning c/n/s jest wyświetlana w osobnej czytelnej linii kafelka predykcji AI.

### Naprawiono

- Card UI nie podstawia już pewności effective/ogólnej jako direct, gdy bucket ma zero próbek jakościowych.
- Predykcja PWM direct jest teraz wyświetlana jako myślnik, gdy bezpośredni model nie ma predykcji.

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
