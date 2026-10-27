# SBC5 Control Center 3.0.0

> Hybrid Rust Core release with verified preserved-state migration and rollback on Raspberry Pi 5 / Home Assistant OS.

## English

- Native Rust core handles lightweight host telemetry and runtime health.
- Proven compatibility/control plane remains authoritative for fan safety, Adaptive PWM and AI Cooling.
- Preserved-state Store migration keeps the 49°C custom curve, AI model/counters, fan calibration and CPU/GPU profiles.
- Adaptive PWM safely recovers orphaned userspace thermal ownership after an App rebuild/update.
- Card UI version synchronization is dynamic and verified after storage-mode Lovelace updates.
- Gate 2 passed on Raspberry Pi 5 with Core 2026.10.4 / HA OS 18.4.rc2.
- App-only update requires no Home Assistant or host restart.

## Polski

- Natywny rdzeń Rust obsługuje lekką telemetrię hosta i runtime health.
- Sprawdzona warstwa zgodności/sterowania nadal odpowiada za bezpieczeństwo wentylatora, Adaptive PWM i AI Cooling.
- Migracja Store z zachowaniem stanu utrzymuje krzywą 49°C, model/liczniki AI, kalibrację wentylatora oraz profile CPU/GPU.
- Adaptive PWM bezpiecznie odzyskuje osierocone przejęcie sterowania termicznego po przebudowie/aktualizacji aplikacji.
- Wersja Card UI jest synchronizowana dynamicznie i weryfikowana po zapisie Lovelace w trybie storage.
- Gate 2 przeszedł na Raspberry Pi 5 z Core 2026.10.4 / HA OS 18.4.rc2.
- Aktualizacja samej aplikacji nie wymaga restartu Home Assistant ani hosta.
