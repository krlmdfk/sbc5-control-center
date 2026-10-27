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
