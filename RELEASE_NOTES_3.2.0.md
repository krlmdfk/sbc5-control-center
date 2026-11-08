# SBC5 Control Center 3.2.0

> Global Community Edition for Raspberry Pi 5: international installation guide, explicit host-access security disclosure and platform-specific installation.

## English

### Highlights

- Global Community Edition for Raspberry Pi 5: international installation guide, explicit host-access security disclosure and platform-specific installation.

### Added

- Document global installation, security review and mandatory real-device release gates in English and Polish.

### Changed

- Target raspberrypi5-64 explicitly to avoid offering the App on unsupported aarch64 boards.

### Security

- Disclose full_access, host_pid, AppArmor disablement and elevated Supervisor/kernel privileges; do not reduce privileges without hardware validation.

### Upgrade notes

- No restart is required.
- Existing configuration and durable SBC5 state should be preserved unless a release-specific migration note says otherwise.

### Compatibility

- Raspberry Pi 5
- Home Assistant OS >= 18.3
- Home Assistant Core >= 2026.10.1
- Architecture: aarch64
- Companion HACS integration is distributed separately.

### Verification and limitations

- Repository validation, runtime, Rust Core, HACS and Hassfest checks passed on release candidates; final publication workflows verify their respective commits.
- Release manifest hashes are verified in strict mode and the local-update ZIP is rebuilt and SHA-256 checked before upload.
- A clean installation on a second physical Raspberry Pi 5 **was not tested**.
- The first in-place 3.1.37 → 3.2.0 upgrade on the existing Raspberry Pi 5 **has not been tested prior to publication**; it will be verified after release through the Home Assistant Apps channel.
- User confirmed a backup and working cooling/telemetry baseline, but this is not a substitute for a successful 3.2.0 upgrade.
- The App requests broad host privileges (full_access, host_pid, SYS_ADMIN, SYS_PTRACE, Supervisor manager, AppArmor disabled). It is a community App, **not accepted into the official Home Assistant Apps catalog**.

### Downloads & links

- Main project: https://github.com/krlmdfk/sbc5-control-center
- HACS integration: https://github.com/krlmdfk/sbc5-control-center-integration
- Documentation: https://krlmdfk.github.io/sbc5-control-center/
- Release history: `CHANGELOG.md`
- Issues: https://github.com/krlmdfk/sbc5-control-center/issues

---

## Polski

### Najważniejsze zmiany

- Wydanie społecznościowe Global Edition dla Raspberry Pi 5: globalna instalacja, jawny audyt uprawnień i ograniczenie platformy docelowej.

### Dodano

- Dodano dwujęzyczną instrukcję instalacji globalnej, audyt bezpieczeństwa oraz wymagane testy na urządzeniu.

### Zmieniono

- Ograniczono dostępność aplikacji do raspberrypi5-64 zamiast wszystkich urządzeń aarch64.

### Bezpieczeństwo

- Jawnie opisano full_access, host_pid, wyłączenie AppArmor oraz uprawnienia Supervisor i systemu; bez zmiany uprawnień przed testami sprzętowymi.

### Informacje o aktualizacji

- Restart nie jest wymagany.
- Istniejąca konfiguracja i trwały stan SBC5 powinny zostać zachowane, o ile dana wersja nie zawiera osobnej informacji migracyjnej.

### Zgodność

- Raspberry Pi 5
- Home Assistant OS >= 18.3
- Home Assistant Core >= 2026.10.1
- Architektura: aarch64
- Integracja HACS jest dystrybuowana osobno.

### Weryfikacja i ograniczenia

- Testy kodu, runtime, Rust Core, HACS i Hassfest zakończyły się sukcesem dla kandydatów; procesy publikacji sprawdzają finalne commity.
- Sumy kontrolne manifestu są weryfikowane w trybie ścisłym; paczka ZIP jest ponownie budowana i sprawdzana SHA-256.
- **Nie wykonano czystej instalacji na drugim fizycznym Raspberry Pi 5.**
- **Nie przetestowano jeszcze na sprzęcie aktualizacji 3.1.37 → 3.2.0 przed publikacją** — weryfikacja nastąpi po udostępnieniu nowej wersji w kanale Apps.
- Wykonano kopię zapasową i zapisano stan chłodzenia, ale nie zastępuje to testu aktualizacji 3.2.0.
- Aplikacja wymaga szerokich uprawnień hosta (full_access, host_pid, SYS_ADMIN, SYS_PTRACE, rola Supervisor manager, wyłączony AppArmor). Jest to aplikacja **społecznościowa**, nie przyjęta do oficjalnego katalogu Home Assistant Apps.

### Pobieranie i linki

- Projekt główny: https://github.com/krlmdfk/sbc5-control-center
- Integracja HACS: https://github.com/krlmdfk/sbc5-control-center-integration
- Dokumentacja: https://krlmdfk.github.io/sbc5-control-center/
- Historia wersji: `CHANGELOG.md`
- Zgłoszenia: https://github.com/krlmdfk/sbc5-control-center/issues
