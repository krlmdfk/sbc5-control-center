---
layout: default
title: SBC5 Control Center — Raspberry Pi 5 Cooling & Monitoring for Home Assistant
---

# SBC5 Control Center

**Raspberry Pi 5 fan control, AI-assisted cooling, system monitoring, CPU/GPU profiles, overclocking and diagnostics for Home Assistant OS.**

SBC5 Control Center turns Home Assistant into a practical Raspberry Pi 5 control and monitoring dashboard. It combines Active Cooler management, Adaptive PWM, local AI Cooling, temperature and RPM telemetry, CPU/GPU/V3D/ISP profiles, managed `config.txt`, diagnostics, recovery and safe update workflows.

## Main use cases

- **Raspberry Pi 5 fan control for Home Assistant** — Active Cooler management, PWM control, calibration and RPM monitoring.
- **Adaptive thermal management** — temperature-aware PWM control with bounded correction, deadband, anti-windup and slew limiting.
- **AI-assisted cooling** — local Learning/Assist logic, workload buckets, qualification, confidence and prediction history.
- **CPU and GPU monitoring** — CPU0–CPU3 telemetry plus GPU/V3D/ISP monitoring and managed profiles.
- **Raspberry Pi 5 overclocking profiles** — managed CPU/OC and GPU profiles with boot verification and restart awareness.
- **Hardware diagnostics** — power, PMIC, memory, storage, throttling, network, firmware and bootloader diagnostics.
- **Home Assistant dashboard** — Lovelace views with Mushroom, card-mod and ApexCharts Card.

## Explore SBC5

- [Fan control & Active Cooler](fan-control.md)
- [AI Cooling & Adaptive PWM](ai-cooling.md)
- [Monitoring & diagnostics](monitoring.md)
- [CPU/GPU profiles & overclocking](overclocking.md)
- [First installation](FIRST_INSTALL.md)
- [Quick Setup](QUICK_SETUP.md)
- [Full documentation](../DOCUMENTATION.md)
- [Search & discoverability coverage](../DISCOVERABILITY.md)

## Project repositories

- **Main App/runtime:** [krlmdfk/sbc5-control-center](https://github.com/krlmdfk/sbc5-control-center)
- **HACS integration:** [krlmdfk/sbc5-control-center-integration](https://github.com/krlmdfk/sbc5-control-center-integration)

## Compatibility

SBC5 Control Center targets **Raspberry Pi 5** running **Home Assistant OS**. The project is independent and is not sponsored, endorsed or maintained by Raspberry Pi Ltd., Home Assistant or the Open Home Foundation.
