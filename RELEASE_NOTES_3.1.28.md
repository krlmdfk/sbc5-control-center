# SBC5 Control Center 3.1.28

> Restore AI Cooling v5.2 and Thermal Predictor runtime evaluation by packaging the missing thermal_effectiveness dependency in the application image.

## English

### Highlights

- Restore AI Cooling v5.2 and Thermal Predictor runtime evaluation by packaging the missing thermal_effectiveness dependency in the application image.

### Changed

- Restore AI Cooling v5.2 and Thermal Predictor runtime evaluation by packaging the missing thermal_effectiveness dependency in the application image.

### Fixed

- Package thermal_effectiveness.py alongside the v5.2 AI runtime and strengthen Docker runtime validation so project-local imports cannot be omitted from future images.

### Performance & reliability

- No new polling loop and no cooling-policy change; Adaptive PWM and existing AI evaluator cadence remain unchanged.

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

- Przywraca działanie evaluatora AI Cooling v5.2 i Thermal Predictora przez dołączenie brakującej zależności thermal_effectiveness do obrazu aplikacji.

### Zmieniono

- Przywraca działanie evaluatora AI Cooling v5.2 i Thermal Predictora przez dołączenie brakującej zależności thermal_effectiveness do obrazu aplikacji.

### Naprawiono

- Dołącza thermal_effectiveness.py do runtime AI v5.2 i wzmacnia walidację obrazu Docker, aby lokalne moduły importowane przez runtime nie mogły zostać pominięte w kolejnych wydaniach.

### Wydajność i niezawodność

- Bez nowej pętli odpytywania i bez zmian polityki chłodzenia; Adaptive PWM oraz dotychczasowy cykl evaluatora AI pozostają bez zmian.

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
