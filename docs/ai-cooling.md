---
layout: default
title: Raspberry Pi 5 AI Cooling & Adaptive PWM
---

# Raspberry Pi 5 AI Cooling & Adaptive PWM

SBC5 Control Center combines a classical temperature-aware fan controller with a bounded local AI Cooling assist layer.

## Adaptive PWM

The configured `custom1(T)` fan curve remains the control base. Adaptive PWM can apply bounded trim with deadband, anti-windup behavior, confirmation logic and slew limiting.

## AI Cooling

The local AI layer can learn from qualified thermal observations and workload buckets, expose confidence and prediction history, and assist cooling within a limited correction range.

This makes SBC5 relevant to searches for **Raspberry Pi 5 AI cooling**, **adaptive fan control**, **predictive cooling**, **AI temperature prediction**, **workload-aware cooling** and **smart PWM fan control**.

[Back to SBC5 Control Center](index.md)


## AI Thermal Predictor v2

SBC5 includes a closed-loop-aware Thermal Predictor for +30/+60/+120 second CPU temperature forecasts. Predictor v2 combines trend extrapolation with target anchoring and bounded online bias correction. Its quality gate uses MAE, confidence and validated samples. Shadow Assist is telemetry-only and evaluates a bounded ±2 pp PWM recommendation without changing physical fan output.

The Predictor uses the existing AI runtime cadence; no additional fast polling loop is created.


## Bucket-aware qualified learning / Uczenie jakościowe zależne od bucketa

**EN.** A workload-bucket transition starts a fresh short-term qualification window while learned PWM estimates, counters and confidence history remain persistent. `idle/low` retain strict steady-state gates. `medium/high` permit wider thermal/PWM ripple but still reject fast temperature ramps, wide ranges and unstable workload. Adaptive PWM remains curve-anchored; normal upward slew is +3 pp/cycle, target+5°C permits up to +8 pp/cycle, and target+7°C permits up to +12 pp/cycle. Emergency 100% cooling and kernel handoff remain authoritative; downward slew remains conservative.

**PL.** Zmiana bucketa rozpoczyna świeże krótkie okno kwalifikacji, ale wyuczone estymaty PWM, liczniki i historia confidence pozostają trwałe. `idle/low` zachowują ścisłe kryteria stanu ustalonego. `medium/high` dopuszczają większe tętnienia temperatury/PWM, lecz nadal odrzucają szybkie trendy temperatury, zbyt szeroki zakres i niestabilne obciążenie. Adaptive PWM pozostaje zakotwiczony w krzywej; normalny wzrost to +3 pp/cykl, od target+5°C maks. +8 pp/cykl, a od target+7°C maks. +12 pp/cykl. Awaryjne 100% i przekazanie sterowania kernelowi pozostają nadrzędne; zmniejszanie PWM pozostaje zachowawcze.
