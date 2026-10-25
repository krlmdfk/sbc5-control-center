# SBC5 Control Center — Technical Documentation

**Documentation version:** 2.8.25  
**Card UI:** 2.8.25  

**Load model:** temperature/RPM/PWM use the lightweight 5 s path, Adaptive PWM runs every 10 s, full bridge telemetry every 15 s, the compact AI relay is evaluated every 15 s and published on change with a 5-minute keepalive, the heavy host relay every 30 s, and Supervisor profile reconciliation every 30 s. Diagnostic AI history entities remain sampled every 30 s.
**Minimum:** HA OS 18.3, Home Assistant Core 2026.10.1

The complete first-run procedure is maintained separately in `QUICK_SETUP.md`.

## Architecture
The project consists of the Home Assistant App runtime, the native `sbc5_control_center` bridge, a helper package, Lovelace cards and persistent `/data` state.

## Cooling
Adaptive PWM uses the generated/custom `custom1(T)` curve as its absolute base and adds bounded ±12 pp trim. It includes deadband, confirmation cycles, anti-windup, sign guard, deadband decay, slew limiting and emergency full-fan behavior. Local AI Cooling is secondary to these safeguards.

## CPU/OC
Presets map directly to Factory/2400, Mild/2500, Balanced/2600, Performance/2800 and Experimental/3000 MHz. Presets are a Single Source of Truth. Advanced manual fields are only used in Advanced mode. Real boot changes require a host reboot and are confirmed by Boot Verification using saved `arm_freq` plus live maximum CPU frequency.

## Telemetry
The bridge exposes CPU temperature, current/min/max clocks, PMIC/power/USB data and per-core CPU0–CPU3 frequency and utilization. Lovelace reuses these existing sensors and does not add a second high-frequency sampling loop.

## Restart Manager
Restart priority is monotonic: `host > home_assistant > app > none`. Home Assistant Repairs remains open until the required action is actually verified.

## Updates
Canonical local update path: `/config/sbc5_control_center_updates/`. Historical aliases `/config/rpi5_control_center_updates/` and `/config/rpi5_fan_manager_updates/` are migration-only fallbacks. Packages are manifest/SHA-256 validated and finalized after two-phase health checks.

## Web UI and Lovelace

The **Save configuration** and **Refresh** buttons expose busy, success and error states directly on the button. The active request disables its button to prevent duplicate submissions, and the feedback automatically returns to the default label.
The web UI manages cooling, AI, CPU/OC, config.txt, updates and card synchronization. Managed config.txt synchronization compares boot content semantically; a version-only header comment change does not request a Raspberry Pi reboot. Card UI 2.8.25 exposes CPU OC status/profile controls, four-core clocks and cooling-profile reconciliation status. Advanced OC is selectable from both the web UI and Lovelace; manual values remain editable in Configuration.

CPU/OC and GPU/V3D/ISP profile controls are collapsed by default on the Lovelace card. Tapping the corresponding status tile expands or collapses its controls independently; holding the tile opens More Info.

## Safety
Keep firmware thermal protections enabled, calibrate the fan, test OC incrementally, reboot after boot-parameter changes and return to Factory if stability is uncertain.

See `QUICK_SETUP.md` and `CHANGELOG.md` for operational steps and release history.

## AI parameter history
Home Assistant Recorder persists dedicated numeric AI entities including `sensor.sbc5_ai_prediction_pwm`, `sensor.sbc5_ai_baseline_pwm`, `sensor.sbc5_ai_correction_pwm`, `sensor.sbc5_ai_physical_pwm` and `sensor.sbc5_ai_confidence`. Tapping the **Predykcja AI** tile expands a native 24-hour graph with AI Model, Regulator, AI Delta and Physical PWM; tapping it again hides the graph. Browser Mod is not required.

## GPU / V3D / ISP from the Lovelace card
The main SBC5 card provides Factory, Eco, Balanced, Performance, Experimental and Advanced profiles. A card selection is reconciled with Ingress and Supervisor native Configuration. Advanced uses the manual values configured in position 22. A full Raspberry Pi reboot is requested only when the resulting boot configuration changes.

## Fan Profile Reconciliation
When `custom1` is requested, SBC5 requires `cooling_device/max_state >= 100` before Adaptive PWM may take userspace ownership. On a factory-grid boot it verifies the managed `config.txt` block and `rpi5-custom1.dtbo`, repairs missing boot artifacts at most once per host boot ID and requests a host reboot. Existing boot artifacts are not rewritten repeatedly. Phase B update health validation also requires the requested cooling profile to be active.


### Supervisor profile option synchronization
The requested CPU/GPU state is reconciled with Supervisor's persistent app options. The native Configuration form is backed by Supervisor rather than `/data/options.json`; SBC5 reads `/addons/self/info`, writes only profile-related fields through `/addons/self/options`, and stores the last synchronized profile signature in `/data/profile_supervisor_sync_state.json` to distinguish explicit native edits from stale defaults.


## Hardware identity and firmware diagnostics

The Home Assistant device registry receives the Raspberry Pi model, board revision/model ID, hardware revision, SBC5 software version, serial number and MAC. Diagnostic entities expose Home Assistant OS, kernel, architecture, Raspberry Pi firmware and EEPROM bootloader version. Static identity collection is cached for 300 seconds.
