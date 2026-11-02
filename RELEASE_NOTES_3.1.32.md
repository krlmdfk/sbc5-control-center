# SBC5 Control Center 3.1.32

> Improve Adaptive PWM stability around the configured setpoint with graded trim recovery, bounded actuator reversal handling and clearer physical PWM diagnostics while preserving AI Cooling and Thermal Predictor authority.

## English

### Highlights

- Improve Adaptive PWM stability around the configured setpoint with graded trim recovery, bounded actuator reversal handling and clearer physical PWM diagnostics while preserving AI Cooling and Thermal Predictor authority.

### Added

- Two-cycle actuator reversal guard that limits near-target opposite-direction PWM movement to 1 pp while preserving immediate safety response.
- Explicit physical PWM, pre-actuator request and applied PWM fields in Adaptive PWM runtime logs.
- Regression coverage for graded trim recovery, reversal handling, Bash syntax and unchanged Thermal Predictor authority limits.

### Changed

- The 2 pp fast positive-trim release is now reserved for errors up to +0.30 C; between +0.30 and +0.80 C a confirmed cooling trend releases at most 1 pp per cycle.
- Opposite-direction PWM changes are damped for two control cycles near target, but a genuine >=2 C thermal error bypasses the guard.
- Thermal Predictor unconfirmed forecast diagnostics now explicitly report confirmation rejection without changing prediction policy.

### Performance & reliability

- No new polling loop or background process is added; the guard reuses the existing 10-second Adaptive PWM controller cycle.

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

- Poprawia stabilność Adaptive PWM wokół temperatury docelowej dzięki stopniowanemu wygaszaniu trimu, ograniczeniu szybkich odwróceń aktuatora i czytelniejszej diagnostyce fizycznego PWM, bez zmiany wpływu AI Cooling ani Thermal Predictora.

### Dodano

- Dwucyklowy guard odwrócenia aktuatora ograniczający przy celu ruch PWM w przeciwnym kierunku do 1 pp, z zachowaniem natychmiastowej reakcji bezpieczeństwa.
- Jawne pola fizycznego PWM, żądania przed ograniczeniami aktuatora oraz zastosowanego PWM w logach Adaptive PWM.
- Testy regresyjne stopniowanego wygaszania trimu, odwróceń aktuatora, składni Bash i niezmienionych limitów Thermal Predictora.

### Zmieniono

- Szybkie wygaszanie dodatniego trimu o 2 pp działa teraz tylko do błędu +0,30 C; pomiędzy +0,30 a +0,80 C potwierdzony trend chłodzenia wygasza maksymalnie 1 pp na cykl.
- Zmiany PWM w przeciwnym kierunku są tłumione przez dwa cykle przy celu, ale rzeczywisty błąd termiczny >=2 C omija guard.
- Diagnostyka niepotwierdzonych prognoz Thermal Predictora jawnie wskazuje odrzucenie przez guard potwierdzenia bez zmiany polityki predykcji.

### Wydajność i niezawodność

- Nie dodano nowej pętli odpytywania ani procesu w tle; guard wykorzystuje istniejący 10-sekundowy cykl regulatora Adaptive PWM.

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
