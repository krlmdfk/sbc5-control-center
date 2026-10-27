# SBC5 Control Center 3.1.4

> Fix runtime version/status consistency, reconcile legacy CPU restart markers, and calibrate AI Thermal Predictor confidence to measured error.

## English

### Highlights

- Fix runtime version/status consistency, reconcile legacy CPU restart markers, and calibrate AI Thermal Predictor confidence to measured error.

### Added

- Expose AI Thermal Predictor quality state as a native Home Assistant sensor and on the expanded AI card.

### Changed

- Reweight AI Thermal Predictor confidence so prediction accuracy contributes 35 percent of the score; MAE around 2-3 C can no longer report confidence above 90 percent.

### Fixed

- Normalize SBC5 Package Version and current runtime version surfaces structurally during every release so stale literals such as 2.8.34 cannot survive future version bumps.
- Reconcile legacy generic restart=host CPU/OC markers only when the marker reason identifies CPU configuration and Boot Verification proves the persisted requested profile is already active.
- Use persistent host telemetry as a Lovelace fallback for platform compatibility and show the known installed version while transient update-state publication resynchronizes after Home Assistant Core restart.

### Performance & reliability

- No new polling loops and no Adaptive PWM or AI Cooling control changes; all fixes reuse existing telemetry, coordinator and runtime paths.

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

- Naprawa spójności wersji i statusów runtime, uzgadnianie legacy markerów restartu CPU oraz kalibracja confidence AI Thermal Predictor do rzeczywistego błędu.

### Dodano

- Udostępniono stan jakości AI Thermal Predictor jako natywny sensor Home Assistant i na rozwijanej karcie AI.

### Zmieniono

- Zmieniono wagę confidence AI Thermal Predictor: dokładność predykcji odpowiada za 35 procent wyniku, więc MAE około 2-3 C nie może już generować confidence powyżej 90 procent.

### Naprawiono

- Każde wydanie strukturalnie normalizuje wersję pakietu SBC5 i bieżące powierzchnie runtime, dzięki czemu stare wartości takie jak 2.8.34 nie mogą przetrwać kolejnych aktualizacji.
- Legacy marker restart=host o ogólnym scope jest zamykany tylko wtedy, gdy powód jednoznacznie wskazuje CPU/OC, a Boot Verification potwierdza zgodność zapisanego żądanego profilu ze stanem aktywnym.
- Karta Lovelace korzysta z trwałej telemetrii hosta jako fallbacku zgodności platformy i pokazuje znaną wersję zainstalowaną podczas ponownej synchronizacji chwilowego statusu aktualizacji po restarcie Home Assistant Core.

### Wydajność i niezawodność

- Bez nowych pętli odpytywania i bez zmian sterowania Adaptive PWM ani AI Cooling; poprawki wykorzystują istniejącą telemetrię, koordynator i ścieżki runtime.

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
