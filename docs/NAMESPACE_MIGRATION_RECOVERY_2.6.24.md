# SBC5 Control Center 2.6.24 — Config Entry & Package Recovery

2.6.24 naprawia niepełne przejście z `rpi5_*` do `sbc5_*` obserwowane w 2.6.21–2.6.22.

Najważniejsze zabezpieczenia:

- pełny `packages/sbc5_control_center.yaml` i bootstrap `packages/sbc5_control_center_bridge.yaml` są rozdzielone;
- integracja `sbc5_control_center` musi posiadać aktywny config entry i zdrowe encje zanim stary bridge zostanie usunięty;
- podczas migracji nowa integracja może czytać stary relay `sensor.rpi5_control_center_host_telemetry`;
- target `local_sbc5_control_center` jest przebudowywany z bieżącego źródła 2.6.24 przed handoffem;
- AI, kalibracja i krzywe są ponownie synchronizowane z legacy, dopóki legacy pozostaje właścicielem sterowania;
- stare custom components są archiwizowane dopiero po pozytywnych health-checkach nowej domeny.

Nie usuwaj ręcznie starej integracji ani starej aplikacji podczas naprawy. Koordynator zrobi to dopiero po potwierdzeniu działania natywnego namespace SBC5.