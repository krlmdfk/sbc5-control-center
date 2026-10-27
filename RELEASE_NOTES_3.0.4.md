# SBC5 Control Center 3.0.4

> Lower steady-state polling overhead without changing cooling control cadence.

## English

### Highlights

- Lower steady-state polling overhead without changing cooling control cadence.

### Changed

- Default Config.txt Manager sync interval is now 30 seconds; existing values below 30 seconds remain accepted for compatibility but are clamped to a 30-second runtime watchdog.

### Performance & reliability

- Raised the effective Config.txt Manager watchdog floor from 5 seconds to 30 seconds while preserving immediate event-driven UI reloads.
- Reduced compact AI relay signature checks from every 15 seconds to every 30 seconds; the AI evaluator remains at 10 seconds.

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

- Zmniejszono stałe obciążenie pollingiem bez zmiany częstotliwości sterowania chłodzeniem.

### Zmieniono

- Domyślny interwał synchronizacji Config.txt Manager wynosi teraz 30 sekund; starsze wartości poniżej 30 sekund pozostają akceptowane dla zgodności, ale runtime stosuje minimum 30 sekund.

### Wydajność i niezawodność

- Podniesiono efektywne minimum watchdoga Config.txt Manager z 5 do 30 sekund, zachowując natychmiastowe przeładowanie po zapisie z UI.
- Zmniejszono częstotliwość sprawdzania podpisu kompaktowego relay AI z 15 do 30 sekund; evaluator AI nadal działa co 10 sekund.

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
