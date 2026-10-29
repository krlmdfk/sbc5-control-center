# SBC5 Control Center 3.1.19

> Thermal Predictor v3.1 — exact-time forecast validation, path-aware context filtering and robust thermal trend estimation.

## English

### Highlights

- Forecasts at +30/+60/+120 seconds are now scored against the temperature at the exact due timestamp using bounded interpolation between telemetry samples.
- The context guard evaluates the entire forecast path, catching transient workload/PWM/target shifts even when the endpoint returns to its original state.
- Thermal trend estimation uses a robust median pairwise slope, reducing sensitivity to isolated sensor spikes.
- Existing compatible v3 calibration is preserved; the pending v3 queue is intentionally reset because validation semantics changed.
- Diagnostics now separate model-quality samples from condition/sampling rejections and expose per-horizon accuracy targets.

### Safety / control authority

Thermal Predictor v3.1 remains `observe_only` and reports `control_output_enabled=false`. Adaptive PWM, AI Cooling, Sign Guard, slew limits and emergency behavior retain physical fan-control authority.

### Restart

No Raspberry Pi host reboot is required. The application is restarted normally by the update process. If the HACS integration is updated separately, restart Home Assistant Core so the new integration version is loaded.

## Polski

### Najważniejsze zmiany

- Prognozy +30/+60/+120 s są oceniane względem temperatury dokładnie w czasie zapadalności, wyznaczanej przez ograniczoną interpolację pomiędzy próbkami telemetrii.
- Guard kontekstu analizuje całą ścieżkę prognozy i wykrywa chwilowe zmiany obciążenia/PWM/celu nawet wtedy, gdy końcowy stan wrócił do wartości początkowych.
- Trend termiczny wykorzystuje odporną medianę nachyleń par punktów, dzięki czemu pojedynczy skok czujnika ma znacznie mniejszy wpływ na prognozę.
- Zgodna kalibracja v3 jest zachowywana; oczekująca kolejka v3 jest celowo resetowana, ponieważ zmieniła się semantyka walidacji.
- Diagnostyka oddziela próbki jakości modelu od odrzuceń spowodowanych zmianą warunków lub próbkowaniem oraz pokazuje cele dokładności dla poszczególnych horyzontów.

### Bezpieczeństwo / sterowanie

Thermal Predictor v3.1 nadal działa jako `observe_only` i raportuje `control_output_enabled=false`. Fizyczne sterowanie wentylatorem pozostaje po stronie Adaptive PWM, AI Cooling, Sign Guard, ograniczeń slew oraz zabezpieczeń awaryjnych.

### Restart

Pełny restart hosta Raspberry Pi nie jest wymagany. Aplikacja jest standardowo restartowana przez proces aktualizacji. Po osobnej aktualizacji integracji HACS należy zrestartować Home Assistant Core, aby wczytał nową wersję integracji.
