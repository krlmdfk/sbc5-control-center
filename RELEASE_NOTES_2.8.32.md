# SBC5 Control Center 2.8.32

## English

Runtime robustness hotfix: guarantees writable runtime scratch storage, hardens AI qualification templates against partial telemetry, throttles repeated boot/config write warnings when Host Access is unavailable, and adds explicit Protection Mode/Host PID diagnostics. No Adaptive PWM, AI Cooling model/qualification, fan calibration, CPU/GPU profile, or boot-control algorithm changes.

### Restart

Restart Home Assistant after installation.

### Related repository

HACS companion integration: https://github.com/krlmdfk/sbc5-control-center-integration

The HACS integration requires the SBC5 Control Center App/runtime to be installed and running.

See `CHANGELOG.md` for release history and `DOCUMENTATION.md` / `docs/QUICK_SETUP.md` for current documentation.

---

## Polski

Hotfix odporności runtime: gwarantuje zapisywalny katalog roboczy runtime, zabezpiecza szablony kwalifikacji AI na niepełną telemetrię, ogranicza powtarzane komunikaty o niedostępnym config.txt i dodaje jawną diagnostykę Protection Mode/Host PID. Bez zmian Adaptive PWM, modelu/kwalifikacji AI Cooling, kalibracji wentylatora, profili CPU/GPU ani algorytmów sterowania boot.

### Restart

Po instalacji uruchom ponownie Home Assistant.

### Powiązane repozytorium

Integracja HACS: https://github.com/krlmdfk/sbc5-control-center-integration

Integracja HACS wymaga zainstalowanej i uruchomionej aplikacji/runtime SBC5 Control Center.

Pełna historia znajduje się w `CHANGELOG.md`, a aktualna dokumentacja w `DOCUMENTATION.md` / `docs/QUICK_SETUP.md`.
