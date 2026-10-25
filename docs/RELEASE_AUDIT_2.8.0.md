# SBC5 Control Center 2.8.0 — Release Audit

## Zakres
Audyt wykonano na źródle 2.7.3 przed zbudowaniem 2.8.0. Celem było znalezienie regresji, zbędnych kosztów runtime, niespójności wersji/dokumentacji i problemów w ścieżce aktualizacji/restartów bez zmiany sprawdzonych algorytmów chłodzenia.

## Poprawki wprowadzone

### Restart Manager
- dodano monotoniczny priorytet `host > home_assistant > app > none`,
- post-update `home_assistant` nie może obniżyć istniejącego `host`,
- Boot Verification CPU pozostaje źródłem zamknięcia CPU host reboot Repair.

### Update Manager
- poprawiono legacy aliasy katalogów aktualizacji:
  - `/config/sbc5_control_center_updates/` — canonical,
  - `/config/rpi5_control_center_updates/` — legacy,
  - `/config/rpi5_fan_manager_updates/` — oldest legacy,
- opcjonalny Supervisor Store probe `/addons` działa quiet/best-effort,
- lokalny ZIP updater nadal pozostaje źródłem niezależnym od Supervisor Store,
- legacy katalogi nie są odtwarzane po migracji; puste aliasy są usuwane best-effort.

### Cleanup / retencja
- usunięto podwójne skanowanie tego samego katalogu w Config UI,
- status count/bytes i cleanup są liczone dla unikalnych ścieżek,
- zachowano osobną retencję `processed` i `failed`.

### Powiadomienia
- discovery `notify.mobile_app_*` nie loguje wielokrotnie identycznego wyniku w jednym runtime,
- funkcjonalność actionable notification pozostaje bez zmian.

### Dokumentacja
- główny CHANGELOG został uporządkowany i skrócony,
- pełna stara historia została zachowana w `CHANGELOG_ARCHIVE_PRE_2.8.0.md`,
- Info/README i DOCS opisują aktualną architekturę 2.8.0,
- dodano Quick Setup Guide.

## Walidacje wykonane przed pakowaniem
- `bash -n` dla `run.sh` i migration guard,
- `compileall` dla kodu Python aplikacji i integracji,
- parsowanie wszystkich JSON,
- parsowanie wszystkich YAML,
- kontrola zduplikowanych definicji funkcji Bash,
- kontrola wersji App/Package/Bridge,
- statyczna kontrola encji Lovelace CPU/OC i CPU0–CPU3,
- test jednostkowy priorytetu restartów,
- test agregacji/retencji ZIP dla trzech katalogów,
- test deduplikacji logów discovery mobilnego,
- test API Config UI `/api/state` z wersją aplikacji 2.8.0 i Card UI 2.7.3.

## Elementy celowo bez zmian
- Card UI pozostaje 2.7.3 — struktura karty nie wymagała zmian,
- Curve-Anchored Adaptive PWM, trim ±12 pp, Sign Guard, slew limiter i deadband decay pozostają zgodne z 2.7.3,
- CPU Profile Manager, Single Source of Truth i Boot Verification pozostają zgodne z 2.7.3,
- częstotliwość próbkowania per-core nie została zwiększona.

## Wynik
Źródło 2.8.0 kwalifikuje się do zbudowania jako release jakościowy/dokumentacyjny z poprawkami runtime, bez celowego naruszania działających algorytmów chłodzenia i CPU Profile Managera.
