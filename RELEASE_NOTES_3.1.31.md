# SBC5 Control Center 3.1.31

> Reduce Adaptive PWM positive-trim persistence with fused thermal trends and bounded near-target anti-windup recovery while preserving AI Cooling and Thermal Predictor authority.

## English

### Highlights

- Reduce Adaptive PWM positive-trim persistence with fused thermal trends and bounded near-target anti-windup recovery while preserving AI Cooling and Thermal Predictor authority.

### Added

- Fused thermal trend for Adaptive PWM using 65% of the robust 30-second trend and 35% of the robust 120-second trend.
- Adaptive Trim Recovery states for blocked trim growth, cooling recovery and fast near-target trim release.
- Regression coverage for Trend Fusion, anti-windup behavior and unchanged AI/Thermal Predictor authority limits.

### Changed

- Positive trim accumulation is blocked when the fused thermal trend already indicates meaningful cooling.
- Near the target, stale positive trim can decay by up to 2 pp per control cycle when thermal direction is neutral or cooling.
- Adaptive PWM logs now expose trendF alongside trend30 and trend120 for runtime diagnosis.

### Performance & reliability

- No new polling loop or background process is added; Trend Fusion reuses the existing conditioned-temperature history and Adaptive PWM cycle.

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

- Ogranicza bezwładność dodatniego trimu Adaptive PWM przez łączony trend termiczny i ograniczony anti-windup w pobliżu celu, bez zmiany wpływu AI Cooling ani Thermal Predictora.

### Dodano

- Łączony trend termiczny Adaptive PWM wykorzystujący 65% odpornego trendu 30-sekundowego i 35% trendu 120-sekundowego.
- Stany Adaptive Trim Recovery dla blokowania narastania trimu, odzyskiwania podczas chłodzenia i szybkiego wygaszania trimu przy celu.
- Testy regresyjne Trend Fusion, anti-windup oraz niezmienionych limitów wpływu AI/Thermal Predictora.

### Zmieniono

- Narastanie dodatniego trimu jest blokowane, gdy łączony trend termiczny wskazuje już wyraźne chłodzenie.
- W pobliżu celu nieaktualny dodatni trim może maleć do 2 pp na cykl sterowania, gdy kierunek termiczny jest neutralny lub chłodzący.
- Logi Adaptive PWM pokazują teraz trendF obok trend30 i trend120 dla diagnostyki runtime.

### Wydajność i niezawodność

- Nie dodano nowej pętli odpytywania ani procesu w tle; Trend Fusion wykorzystuje istniejącą historię filtrowanej temperatury i cykl Adaptive PWM.

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
