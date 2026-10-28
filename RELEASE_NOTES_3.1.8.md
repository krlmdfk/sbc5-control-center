# SBC5 Control Center 3.1.8

> Introduce AI Cooling v5 hierarchical continuous learning for transferable medium/high workload modeling without requiring long sustained CPU load.

## English

### Highlights

- Introduce AI Cooling v5 hierarchical continuous learning for transferable medium/high workload modeling without requiring long sustained CPU load.

### Added

- Added a hierarchical global cooling model above the proven bucket-aware v4 learner, with continuous CPU-load anchors and conservative knowledge transfer between workload ranges.
- Added direct, global and effective confidence surfaces so sparse medium/high buckets no longer appear as having no usable model.

### Changed

- Short real-world workload bursts can contribute bounded low-weight evidence to the global model; fully qualified v4 samples retain the strongest learning weight.
- Mature direct bucket models remain authoritative; hierarchical assist is used only when direct bucket evidence is sparse and all existing Adaptive PWM sign/safety limits still apply.

### Performance & reliability

- No additional polling loop was introduced; v5 runs inside the existing AI evaluator cadence and preserves the v4 fail-open fallback.

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

- Wprowadza AI Cooling v5 z hierarchicznym ciągłym uczeniem, aby modelować medium/high bez wymagania długotrwałego obciążenia CPU.

### Dodano

- Dodano hierarchiczny globalny model chłodzenia nad sprawdzonym learnerem v4, z ciągłymi anchorami obciążenia CPU i konserwatywnym transferem wiedzy między zakresami obciążenia.
- Dodano osobne wskaźniki direct, global i effective confidence, dzięki czemu rzadkie buckety medium/high nie są już traktowane jak całkowity brak modelu.

### Zmieniono

- Krótkie rzeczywiste skoki obciążenia mogą wnosić ograniczone dane o małej wadze do modelu globalnego; w pełni zakwalifikowane próbki v4 zachowują najwyższą wagę uczenia.
- Dojrzałe bezpośrednie modele bucketów pozostają nadrzędne; hierarchiczny assist jest używany tylko przy małej liczbie danych lokalnych, z zachowaniem istniejących ograniczeń kierunku i bezpieczeństwa Adaptive PWM.

### Wydajność i niezawodność

- Nie dodano nowej pętli pollingu; v5 działa w istniejącym cyklu ewaluatora AI i zachowuje fail-open fallback do v4.

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
