# SBC5 Control Center 3.1.3

> Reconcile stale CPU restart markers and add AI Thermal Predictor quality diagnostics.

## English

### Highlights

- Reconcile stale CPU restart markers and add AI Thermal Predictor quality diagnostics.

### Added

- Expose Predictor MAE, per-horizon last error, temperature slope, validated-sample count and data age through native Home Assistant sensors and the expanded AI card.
- Expose verified Raspberry Pi host network MAC and interface diagnostics for Device Registry verification.

### Changed

- Reconcile stale CPU restart markers and add AI Thermal Predictor quality diagnostics.

### Fixed

- Clear stale same-boot CPU-profile restart=host markers only when Boot Verification proves the requested preset is already saved and active; generic boot/config markers remain protected until a real host reboot.

### Performance & reliability

- No new polling loops; diagnostics reuse the existing AI runtime relay and 15-second native coordinator.

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

- Uzgodnienie osieroconych markerów restartu CPU i rozszerzona diagnostyka jakości AI Thermal Predictor.

### Dodano

- Udostępniono MAE Predictora, ostatni błąd dla każdego horyzontu, trend temperatury, liczbę zweryfikowanych prognoz i wiek danych jako natywne sensory Home Assistant oraz na rozwijanej karcie AI.
- Udostępniono diagnostykę zweryfikowanego fizycznego MAC i interfejsu sieciowego hosta Raspberry Pi do kontroli Device Registry.

### Zmieniono

- Uzgodnienie osieroconych markerów restartu CPU i rozszerzona diagnostyka jakości AI Thermal Predictor.

### Naprawiono

- Osierocony marker restart=host profilu CPU jest czyszczony na bieżącym boot tylko wtedy, gdy Boot Verification potwierdzi zapisany i aktywny profil; ogólne markery boot/config nadal wymagają rzeczywistego restartu hosta.

### Wydajność i niezawodność

- Bez nowych pętli odpytywania; diagnostyka wykorzystuje istniejący relay AI runtime i 15-sekundowy natywny koordynator.

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
