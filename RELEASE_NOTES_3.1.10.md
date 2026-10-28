# SBC5 Control Center 3.1.10

> Expose AI Cooling v5 hierarchical direct/global/effective diagnostics and reduce duplicate Restart Manager cleanup noise without changing cooling control.

## English

### Highlights

- Expose AI Cooling v5 hierarchical direct/global/effective diagnostics and reduce duplicate Restart Manager cleanup noise without changing cooling control.

### Added

- Expose direct, global and effective AI confidence/prediction plus transfer source and effective coverage in runtime logs and dashboard telemetry.

### Changed

- AI v5 observability reuses the existing evaluator TSV and adds no extra polling or per-cycle JSON parsing.

### Fixed

- Log completed Repairs cleanup only when a native Repair marker actually existed.

### Performance & reliability

- No new polling loop; observability fields travel in the existing 10-second AI evaluator result.

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

- Pełna obserwowalność AI Cooling v5 direct/global/effective oraz ograniczenie powtarzających się logów czyszczenia Restart Managera bez zmian w sterowaniu chłodzeniem.

### Dodano

- Udostępniono bezpośrednią, globalną i efektywną pewność/predykcję AI, źródło transferu i efektywne pokrycie w logach runtime oraz na karcie.

### Zmieniono

- Diagnostyka AI v5 wykorzystuje istniejący TSV ewaluatora bez dodatkowego pollingu i bez dodatkowego parsowania JSON w każdym cyklu.

### Naprawiono

- Log czyszczenia zakończonego Repairs pojawia się tylko wtedy, gdy faktycznie istniał marker natywnego Repair.

### Wydajność i niezawodność

- Bez nowej pętli pollingu; pola observability są przekazywane w istniejącym wyniku ewaluatora AI co 10 s.

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
