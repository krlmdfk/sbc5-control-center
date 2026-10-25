# SBC5 Control Center

> Local control, diagnostics and configuration center for Raspberry Pi 5 running Home Assistant OS.

**App release:** 2.8.25 · **Card UI:** 2.8.25 · **HA OS:** `>= 18.3` · **Core:** `>= 2026.10.1` · **License:** Apache-2.0

SBC5 Control Center combines Active Cooler control, Adaptive PWM, local AI Cooling, CPU/PMIC/USB telemetry, guarded CPU overclocking profiles, managed `config.txt`, restart orchestration, local ZIP updates and Lovelace diagnostics.
**Configuration UI:** save and refresh actions expose busy/success/error feedback and prevent duplicate clicks while a request is running.

## Fan profile reconciliation

At startup SBC5 validates the requested fan profile against the cooling device actually loaded by the kernel. `custom1` requires the 1% grid (`max_state >= 100`). If the factory grid is active, SBC5 verifies `config.txt` and `rpi5-custom1.dtbo`, performs at most one boot-artifact repair per host boot ID, and leaves cooling under kernel control until a host reboot activates the grid. Update Health Check Phase B includes this cooling-profile validation.

## Highlights
- Factory/custom Active Cooler control with calibration and kernel fallback.
- Curve-anchored Adaptive PWM with bounded ±12 pp trim, direction guard and slew limiting.
- Local AI Cooling with workload buckets and qualified-sample learning.
- CPU profiles: Factory 2400, Mild 2500, Balanced 2600, Performance 2800 and Experimental 3000 MHz; Advanced mode is selectable from the web UI, Lovelace and native Configuration; manual values are edited in Configuration.
- CPU Profile Single Source of Truth plus host-reboot Boot Verification.
- Live CPU0–CPU3 frequency and usage sensors, exposed on the diagnostics card.
- Managed `config.txt` blocks with backup/rollback.
- Restart priority `host > home_assistant > app` and Home Assistant Repairs integration.
- Local update ZIP verification, two-phase health checks and retention cleanup.

## Quick setup
1. Install the app and the `sbc5_control_center` bridge.
2. Verify `Platform Guard: OK` and `Host Access: SUKCES`.
3. Configure the target temperature and use Automatic/Balanced as the recommended starting point.
4. Calibrate the Active Cooler before lowering PWM limits manually.
5. Add or synchronize the Lovelace diagnostics card.
6. If using CPU OC, select a preset, save, reboot the Raspberry Pi when requested, then confirm `Boot Verification PASS`.

See `QUICK_SETUP.md` and `DOCS.en.md` for the full guide.

### GPU profiles
The main Lovelace card exposes the GPU / V3D / ISP profiles directly. Choose **Factory, Eco, Balanced, Performance, Experimental or Advanced**, then press **Apply preset**. The selector is synchronized with the app profile. Advanced keeps using the manual values from configuration position 22; Factory restores firmware-managed clocks. A full Raspberry Pi reboot is requested only if the boot configuration changed.


## Hardware identity and firmware diagnostics

The Home Assistant device registry receives the Raspberry Pi model, board revision/model ID, hardware revision, SBC5 software version, serial number and MAC. Diagnostic entities expose Home Assistant OS, kernel, architecture, Raspberry Pi firmware and EEPROM bootloader version. Static identity collection is cached for 300 seconds.
