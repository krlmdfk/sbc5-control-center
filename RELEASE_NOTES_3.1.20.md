# SBC5 Control Center 3.1.20

> AI runtime & Thermal Predictor history hotfix.

## English

### Highlights
- Repairs the application-image AI Cooling chain so v5 uses the v4 compatibility wrapper that injects Thermal Predictor v3.x.
- Packages the Thermal Predictor module explicitly and protects the wiring with a CI regression test.
- Adds a 24-hour Thermal Predictor graph with actual CPU temperature plus +30/+60/+120 s forecasts.
- Keeps the predictor strictly `observe_only`; physical PWM authority is unchanged.
- Avoids forced duplicate Recorder writes to preserve Home Assistant performance.

### Restart
No Raspberry Pi host reboot is required. The application restarts as part of the update. Restart Home Assistant Core after updating the HACS integration.

## Polski

### Najważniejsze zmiany
- Naprawia łańcuch AI Cooling w obrazie aplikacji, tak aby v5 korzystało z wrappera v4 wstrzykującego Thermal Predictor v3.x.
- Jawnie pakuje moduł Thermal Predictora i zabezpiecza ścieżkę testem regresyjnym CI.
- Dodaje 24-godzinny wykres Thermal Predictora: rzeczywista temperatura CPU oraz prognozy +30/+60/+120 s.
- Predictor nadal działa wyłącznie jako `observe_only`; fizyczne sterowanie PWM pozostaje bez zmian.
- Nie wymusza duplikowania identycznych stanów w Recorderze, dzięki czemu nie zwiększa obciążenia Home Assistanta.

### Restart
Pełny restart Raspberry Pi nie jest wymagany. Aplikacja restartuje się w ramach aktualizacji. Po aktualizacji integracji HACS należy zrestartować Home Assistant Core.
