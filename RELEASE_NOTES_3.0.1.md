# SBC5 Control Center 3.0.1

## English

Maintenance release focused on reducing steady-state Home Assistant/Supervisor churn without changing cooling behavior.

- CPU/GPU profile reconciliation: **30 s → 300 s** in steady state.
- Removed duplicate update discovery during Home Assistant availability restoration.
- Staggered local-package scanning away from the normal startup update check.
- Unified Rust Core, App/runtime, integration and Card UI version metadata at **3.0.1**.
- Adaptive PWM, AI Cooling, fan calibration and the verified 49°C custom boot curve are unchanged.
- **No Raspberry Pi host restart is required by this update.**

## Polski

Wydanie utrzymaniowe skupione na ograniczeniu cyklicznego obciążenia Home Assistant/Supervisor bez zmiany sposobu chłodzenia.

- Reconciler profili CPU/GPU: **30 s → 300 s** w stanie ustalonym.
- Usunięto podwójne sprawdzanie aktualizacji podczas odzyskiwania dostępności Home Assistant.
- Rozdzielono czasowo start skanera lokalnych paczek i standardowego sprawdzania aktualizacji.
- Ujednolicono wersję Rust Core, App/runtime, integracji i Card UI do **3.0.1**.
- Adaptive PWM, AI Cooling, kalibracja wentylatora i zweryfikowana krzywa boot 49°C pozostają bez zmian.
- **Ta aktualizacja nie wymaga restartu hosta Raspberry Pi.**
