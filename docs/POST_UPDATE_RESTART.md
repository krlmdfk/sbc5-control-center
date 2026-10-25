# Restart po aktualizacji

Od 2.8.13 każda publiczna poprawka, także dotycząca kart, jest wydawana jako pełny build ze wspólnym numerem App/Card UI.

`restart_required` w manifeście określa wymagany zakres:
- `none` — bez restartu;
- `home_assistant` — restart Home Assistant;
- `host` — pełny restart hosta/Raspberry Pi.

Sama zmiana YAML nie wymaga technicznie restartu hosta, ale jeśli jest częścią pełnego buildu podnoszącego package/integrację, build może wymagać restartu Home Assistant.

## Profil chłodzenia po restarcie
Jeśli `custom1` jest profilem żądanym, lecz po bootowaniu kernel zgłasza `max_state<100`, SBC5 nie uruchamia Adaptive PWM. Fan Profile Reconciliation sprawdza `config.txt` i DTBO, może wykonać jedną naprawę na `boot_id` i zgłasza wymagany restart hosta. Sam restart Home Assistant nie aktywuje Device Tree.
