# SBC5 Control Center 3.1.33

> Synchronize the SBC5 Control Center App release with the companion HACS integration 3.1.33; no runtime behavior changes.

## English

### Highlights

- Synchronize the App, package metadata and bundled integration with HACS integration 3.1.33.
- No Adaptive PWM, AI Cooling, Thermal Predictor or fan-control behavior changes.

### Changed

- Align App, package and integration version surfaces with 3.1.33.

### Fixed

- Carry the HACS review fixes into the canonical integration copy: marker-file read/delete operations run in the Home Assistant executor while issue deletion stays on the event loop.
- Point integration documentation and issue tracker links to `krlmdfk/sbc5-control-center-integration`.

### Security

No security-specific changes.

### Upgrade notes

- No restart is required.
- Existing configuration and durable SBC5 state should be preserved.

### Compatibility

- Raspberry Pi 5
- Home Assistant OS >= 18.3
- Home Assistant Core >= 2026.10.1
- Architecture: aarch64
- Companion HACS integration: 3.1.33

---

## Polski

### Najważniejsze zmiany

- Synchronizacja aplikacji, metadanych pakietu i dołączonej integracji z HACS 3.1.33.
- Brak zmian w Adaptive PWM, AI Cooling, Thermal Predictorze i sterowaniu wentylatorem.

### Zmieniono

- Ujednolicono wersje aplikacji, pakietu i integracji do 3.1.33.

### Naprawiono

- Przeniesiono do kanonicznej integracji poprawki z przeglądu HACS: odczyt/usuwanie pliku znacznika przez executor, a usuwanie issue pozostaje w event loop.
- Poprawiono linki dokumentacji i zgłoszeń integracji na repo `sbc5-control-center-integration`.

### Bezpieczeństwo

Brak zmian dotyczących bezpieczeństwa.

### Informacje o aktualizacji

- Restart nie jest wymagany.
- Istniejąca konfiguracja i trwały stan SBC5 powinny zostać zachowane.
- Integracja HACS: 3.1.33
