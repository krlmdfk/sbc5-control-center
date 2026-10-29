# SBC5 Control Center 3.1.18

> Persist Ethernet EEE choices across host reboots and correct userspace-managed custom1 fan profile status.

## English

### Highlights

- Persist Ethernet EEE choices across host reboots and correct userspace-managed custom1 fan profile status.

### Changed

- Persist Ethernet EEE choices across host reboots and correct userspace-managed custom1 fan profile status.

### Fixed

- Persist Ethernet EEE settings in a dedicated /data state so Supervisor-restored defaults cannot revert EEE after host reboot.
- Report custom1 + runtime custom + 1% grid + Adaptive PWM as active_runtime_managed instead of a false pending_host_reboot.
- Report actual Ethernet guard startup state and relay guard logs to the main App log while retaining the dedicated guard log.

### Performance & reliability

- Keep Ethernet monitoring file-based and event-light; no additional Home Assistant network polling is introduced.

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

- Utrwalono wybór Ethernet EEE po restartach hosta i poprawiono status profilu custom1 zarządzanego przez Adaptive PWM.

### Zmieniono

- Utrwalono wybór Ethernet EEE po restartach hosta i poprawiono status profilu custom1 zarządzanego przez Adaptive PWM.

### Naprawiono

- Zapisano ustawienia Ethernet EEE w osobnym trwałym stanie /data, dzięki czemu domyślne opcje odtworzone przez Supervisor nie cofają EEE po restarcie hosta.
- Dla custom1 + runtime custom + siatki 1% + Adaptive PWM raportowany jest active_runtime_managed zamiast fałszywego pending_host_reboot.
- Start Ethernet Guard pokazuje faktyczny żądany stan, a log guardu trafia także do głównego logu aplikacji przy zachowaniu osobnego logu diagnostycznego.

### Wydajność i niezawodność

- Diagnostyka Ethernet pozostaje lekka i plikowa; nie dodano dodatkowego odpytywania sieci przez Home Assistant.

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
