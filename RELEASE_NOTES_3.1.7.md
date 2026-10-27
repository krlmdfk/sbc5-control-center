# SBC5 Control Center 3.1.7

> Improve AI Cooling learning for medium/high workloads and accelerate safe fan response during large thermal excursions.

## English

### Highlights

- Improve AI Cooling learning for medium/high workloads and accelerate safe fan response during large thermal excursions.

### Changed

- AI Cooling qualification is bucket-aware: bucket transitions reset only short stability windows while learned bins, counters and confidence remain preserved.
- Medium/high use workload-specific temperature, slope and PWM quality limits while idle/low retain the stricter steady-state gates.
- Adaptive PWM adds an upward-only thermal fast path: up to +8 pp per cycle from target+5C and +12 pp per cycle from target+7C; downward slew is unchanged.

### Fixed

- Prevent low-load qualification history from contaminating medium/high windows, which could leave higher workload buckets with observations but zero qualified samples.
- Restart Manager cards now identify whether a pending restart comes from CPU/OC, GPU, cooling/Device Tree, boot configuration, the current update, or an earlier independent request.

### Performance & reliability

- No new polling loop is added; bucket-aware qualification reuses the existing 10-second AI evaluator and preserves the current durable checkpoint cadence.

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

- Poprawa uczenia AI Cooling dla obciążeń medium/high oraz szybsza, bezpieczna reakcja wentylatora przy dużym odchyleniu temperatury.

### Zmieniono

- Kwalifikacja AI Cooling jest zależna od bucketa: przejście między bucketami zeruje wyłącznie krótkie okna stabilności, a wyuczone biny, liczniki i confidence pozostają zachowane.
- Medium/high używają limitów jakości temperatury, trendu i PWM dopasowanych do obciążenia, a idle/low zachowują bardziej rygorystyczne kryteria stanu ustalonego.
- Adaptive PWM otrzymuje thermal fast path wyłącznie w górę: do +8 pp/cykl od target+5C i +12 pp/cykl od target+7C; tempo zmniejszania PWM pozostaje bez zmian.

### Naprawiono

- Usunięto wpływ historii kwalifikacji z niskiego obciążenia na okna medium/high, który mógł pozostawiać wyższe buckety z obserwacjami, ale bez próbek jakościowych.
- Karty Restart Managera wskazują, czy oczekujący restart pochodzi z CPU/OC, GPU, chłodzenia/Device Tree, konfiguracji boot, bieżącej aktualizacji czy wcześniejszego niezależnego żądania.

### Wydajność i niezawodność

- Nie dodano nowej pętli pollingowej; kwalifikacja zależna od bucketa wykorzystuje istniejący evaluator AI co 10 s i zachowuje dotychczasową częstotliwość trwałych checkpointów.

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
