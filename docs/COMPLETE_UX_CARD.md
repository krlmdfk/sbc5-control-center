# Karty Lovelace

Wspierane są dokładnie dwie karty YAML: `rpi5_control_center_optimized_v5_diagnostics_card.yaml` i `update_status_card.yaml`. Pierwsza prezentuje monitoring i diagnostykę, druga aktualizacje oraz Restart Manager.

## Rozwijana historia Predykcji AI (2.8.12)

Dotknięcie kafelka `Predykcja AI` przełącza `input_boolean.sbc5_ai_prediction_chart_visible`. Natywny `history-graph` Home Assistanta jest domyślnie ukryty i po rozwinięciu pokazuje 24 h historii czterech sygnałów: Model AI, Regulator, AI Delta i PWM fizyczny. Ponowne dotknięcie ukrywa wykres. Ta funkcja nie wymaga Browser Mod.

## AI Prediction History (2.8.4)

The diagnostics card includes a native 24-hour Home Assistant history graph backed by Recorder-friendly numeric entities:

- `sensor.sbc5_ai_prediction_pwm` — AI model PWM prediction,
- `sensor.sbc5_ai_baseline_pwm` — classic controller baseline,
- `sensor.sbc5_ai_physical_pwm` — physical PWM observed by AI,
- `sensor.sbc5_ai_correction_pwm` — bounded AI correction,
- `sensor.sbc5_ai_confidence` — AI confidence.

The graph uses the first three signals for a readable comparison. History begins when these entities are first created and is retained according to the Home Assistant Recorder policy.



## 2.8.13 GPU card controls
The dashboard includes a synchronized GPU/V3D/ISP preset selector, an apply action and a shortcut to position 22 for Advanced/manual configuration.

Kafelki stanu CPU/OC oraz GPU/V3D/ISP sterują niezależnymi sekcjami konfiguracji. Pola wyboru i zastosowania profilu są domyślnie zwinięte (`initial: false`); zwykłe dotknięcie kafelka przełącza widoczność, a długie przytrzymanie otwiera More Info.
