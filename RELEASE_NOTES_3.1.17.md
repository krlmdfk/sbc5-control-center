# SBC5 Control Center 3.1.17

> Add Raspberry Pi 5 Ethernet EEE stability control and end0 link-flap diagnostics.

## English

### Highlights

- Add Raspberry Pi 5 Ethernet EEE stability control and end0 link-flap diagnostics.

### Added

- Add opt-in Energy Efficient Ethernet control with auto and off modes; off writes dtparam=eee=off to a dedicated SBC5-managed boot block.
- Add Ethernet Health, Ethernet Link Flaps and Ethernet EEE Status sensors through the native SBC5 integration.

### Changed

- App Configuration now exposes Ethernet monitoring, flap window and DEGRADED threshold without changing EEE unless the user explicitly selects off.

### Fixed

- Prevent duplicate SBC5 EEE entries, preserve user-managed EEE settings and refuse conflicting external dtparam=eee=on configuration.

### Performance & reliability

- Ethernet health is sampled from host sysfs by the app guard and relayed through a small JSON state file, avoiding additional Home Assistant network polling.

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

- Dodano kontrolę stabilności Ethernet EEE dla Raspberry Pi 5 oraz diagnostykę zrywania linku end0.

### Dodano

- Dodano opcjonalne sterowanie Energy Efficient Ethernet z trybami auto i off; tryb off zapisuje dtparam=eee=off w osobnym bloku zarządzanym przez SBC5.
- Dodano sensory Ethernet Health, Ethernet Link Flaps oraz Ethernet EEE Status w natywnej integracji SBC5.

### Zmieniono

- Konfiguracja aplikacji udostępnia monitorowanie Ethernet, okno flappingu i próg DEGRADED bez zmiany EEE, dopóki użytkownik jawnie nie wybierze off.

### Naprawiono

- Zapobiegnięto duplikowaniu wpisów EEE, zachowano ręczne ustawienia użytkownika i dodano odmowę zapisu przy konflikcie z zewnętrznym dtparam=eee=on.

### Wydajność i niezawodność

- Stan Ethernet jest próbkowany z hostowego sysfs przez lekki guard aplikacji i przekazywany małym plikiem JSON, bez dodatkowego odpytywania sieci przez Home Assistant.

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
