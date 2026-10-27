# SBC5 Control Center 3.1.2

> Fix AI Thermal Predictor delivery, Lovelace card version synchronization and Raspberry Pi network identity.

## English

### Highlights

- Fix AI Thermal Predictor delivery, Lovelace card version synchronization and Raspberry Pi network identity.

### Changed

- AI Thermal Predictor recorder entities are now owned by the native SBC5 integration and reuse the existing AI runtime relay without an additional polling loop.

### Fixed

- Fixed browser-session Lovelace synchronization so runtime templates normalize Card UI, Update Card and SBC5CC version markers to the installed release.
- Fixed the stale 2.8.34 Update Card marker that caused verification rollback after a successful 3.1.1 update.
- Raspberry Pi device identity now uses the physical host network interface instead of ephemeral App/container MAC addresses.
- Device Registry migration replaces accumulated stale MAC connections with the single verified host MAC.

### Performance & reliability

- No new high-frequency polling loop was added; Predictor sensors reuse the existing 15-second native coordinator and AI runtime relay.

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

- Naprawa udostępniania AI Thermal Predictor, synchronizacji wersji kart Lovelace i identyfikacji sieciowej Raspberry Pi.

### Zmieniono

- Encje Recordera AI Thermal Predictor są teraz obsługiwane przez natywną integrację SBC5 i korzystają z istniejącego przekaźnika AI runtime bez dodatkowej pętli odpytywania.

### Naprawiono

- Naprawiono synchronizację Lovelace przez sesję przeglądarki: znaczniki wersji Card UI, Update Card i SBC5CC są normalizowane do zainstalowanego wydania.
- Naprawiono stary znacznik Update Card 2.8.34, który powodował rollback weryfikacji po poprawnej aktualizacji 3.1.1.
- Identyfikacja urządzenia Raspberry Pi korzysta teraz z fizycznego interfejsu sieciowego hosta zamiast zmiennych adresów MAC aplikacji/kontenera.
- Migracja Device Registry zastępuje nagromadzone stare połączenia MAC jednym zweryfikowanym adresem MAC hosta.

### Wydajność i niezawodność

- Nie dodano nowej pętli szybkiego odpytywania; sensory Predictora wykorzystują istniejący 15-sekundowy koordynator natywny i przekaźnik AI runtime.

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
