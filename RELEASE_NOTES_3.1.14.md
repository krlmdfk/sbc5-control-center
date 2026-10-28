# SBC5 Control Center 3.1.14

> Fix Active Cooler custom overlay reconciliation after HAOS A/B slot switches.

## English

### Highlights

- Fix Active Cooler custom overlay reconciliation after HAOS A/B slot switches.

### Changed

- Fix Active Cooler custom overlay reconciliation after HAOS A/B slot switches.

### Fixed

- Validate rpi5-custom1.dtbo in the currently booted HAOS RAUC slot instead of accepting a stale copy from any slot.
- Automatically rebuild the custom fan overlay when the active slot is missing it after an HAOS update.

### Performance & reliability

- No new polling loop; active-slot detection runs only during existing startup reconciliation.

### Security

No security-specific changes.

### Upgrade notes

- A full Raspberry Pi 5 host restart is required after installation/update.
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

- Naprawa aktywacji niestandardowego profilu Active Cooler po przełączeniu slotu A/B przez HAOS.

### Zmieniono

- Naprawa aktywacji niestandardowego profilu Active Cooler po przełączeniu slotu A/B przez HAOS.

### Naprawiono

- Walidacja rpi5-custom1.dtbo dotyczy teraz aktualnie uruchomionego slotu RAUC HAOS, a nie dowolnej starej kopii z innego slotu.
- Automatyczna odbudowa nakładki profilu wentylatora, gdy aktywny slot nie ma jej po aktualizacji HAOS.

### Wydajność i niezawodność

- Bez nowej pętli odpytywania; wykrywanie aktywnego slotu działa wyłącznie w istniejącej fazie uzgadniania przy starcie.

### Bezpieczeństwo

Brak zmian dotyczących bezpieczeństwa.

### Informacje o aktualizacji

- Po instalacji/aktualizacji wymagany jest pełny restart hosta Raspberry Pi 5.
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
