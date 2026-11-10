# SBC5 Thermal Predictor quality gate — Pi 5 validation plan / Plan walidacji

Status: **pre-release, manual acceptance only**. Related draft PRs: [#74](https://github.com/krlmdfk/sbc5-control-center/pull/74) and [#75](https://github.com/krlmdfk/sbc5-control-center/pull/75). This document does not trigger an update.

## PL — plan testu na rzeczywistym urządzeniu

**Cel:** potwierdzić brak regresji bezpieczeństwa, zachowanie temperatury CPU, płynności PWM i trwałości wyuczonego modelu. Wyniki CI i symulacji 720 cykli nie zastępują pomiaru urządzenia.

### Przed testem

1. Zachowaj oryginalną, sprawdzoną wersję aplikacji i istniejące kopie danych AI zgodnie z mechanizmem backupu aplikacji. Nie uruchamiaj „reset AI” i nie usuwaj modelu ani kalibracji.
2. Zapisz wersję SBC5, wersję HAOS, profil CPU/GPU, tryb AI, temperaturę docelową, aktywną krzywą i konfigurację PWM. Nie zmieniaj tych parametrów podczas porównania.
3. Zapisz logi z **minimum 2 godzin** pracy dotychczasowej wersji: spoczynek i typowe obciążenie. Nie generuj celowo niebezpiecznej temperatury. Zwróć uwagę na restart aplikacji i urządzenia tylko podczas normalnego użytkowania.
4. Upewnij się, że jest możliwy powrót do wcześniej działającej wersji aplikacji. Nie zmieniaj jednocześnie wersji Home Assistant, konfiguracji wentylatora i Thermal Predictora.

### Po kontrolowanym wdrożeniu zatwierdzonego wydania

1. Zachowaj identyczne ustawienia i zbierz co najmniej 2 godziny logów przy porównywalnym obciążeniu. Preferowane są 24 godziny rzeczywistej eksploatacji, bez świadomego przeciążania sprzętu.
2. Obserwuj, czy nie występują komunikaty `safety_max`, `AI Cooling: evaluator nie zwrócił wyniku`, `predictor_stale`, powtarzane restarty albo utrata sterowania wentylatorem. W razie takich objawów zatrzymaj eksperyment, pozostaw sprawdzone zabezpieczenia i przywróć poprzednie stabilne wydanie.
3. Porównaj w logach: odchylenie `T_raw` od targetu, rozrzut i skoki PWM, `confidence`, `MAE_avg`, udział stanów bramki, przyrost `qualified_samples_total` oraz poprawność powrotu z trybu `observe`.
4. Zweryfikuj, że wartości `qualified_samples_total` i liczebność koszyków AI nie cofają się po standardowym restarcie aplikacji.
5. Nie traktuj obniżenia liczby zmian bramki jako dowodu lepszego chłodzenia. Najważniejsze są rzeczywista temperatura CPU, niezawodność wentylatora, brak nowych alarmów i zachowanie granic PWM.

### Narzędzie offline (tylko odczyt)

Na komputerze z kopią repozytorium i wyeksportowanym logiem:

```bash
python scripts/analyze_thermal_control_logs.py SBC5_before.log --json
python scripts/analyze_thermal_control_logs.py SBC5_after.log --json
```

Skrypt nie wymaga dostępu do Raspberry Pi i nie modyfikuje modelu. Zestawia **próbki zawarte w logach**; ich nieregularność może zniekształcać średnie. Nie wylicza faktycznej dokładności prognoz F30/F60/F120, jeśli nie ma dopasowanych pomiarów temperatury.

### Kryteria akceptacji

- Brak nowych alarmów, nieprzewidzianego wyłączenia wentylatora, regresji bezpieczeństwa i wzrostu temperatury przy porównywalnym obciążeniu.
- Działa ograniczenie PWM i natychmiastowe przejście `active → probation/observe`, gdy surowa decyzja jakości tego wymaga.
- Model zachowuje wcześniejsze statystyki uczenia. Zmiany wersji nie wymagają resetu modelu.
- Oddzielnie odnotowano różnice w obciążeniu i liczebności próbek. Porównanie wyłącznie na podstawie CI/symulacji oznacza **brak potwierdzenia sprzętowego**.

## EN — real-device validation

**Goal:** confirm temperature, PWM authority, AI learning persistence, and fail-closed behavior under normal Raspberry Pi 5 operation. CI and a 720-cycle synthetic replay do **not** establish actual hardware improvement.

1. Before any deployment, preserve the known-good application and its supported model backups; record SBC5/HAOS versions, CPU profile, PWM curve, setpoint, and AI mode. Do **not** reset AI or calibration.
2. Export at least two hours of baseline logs from ordinary low and typical load. Avoid intentionally hazardous thermal tests.
3. Only after normal release approval, repeat logging with the same settings and comparable load (24 hours is preferable).
4. Compare measured CPU temperature deviation, PWM steps, logged quality states, predictor confidence and MAE, AI sample counters, and fallback/safety messages using the read-only CLI above.
5. Check a normal restart does not lose learning and a poor/stale/unsafe predictor immediately loses active authority.
6. Stop the trial and restore the proven release on fan-control anomalies, repeated errors, abnormal heating or lost persistence.

**Acceptance is manual:** no new safety problems, no temperature regression at comparable load, unchanged actuator limits and preserved model state. Reduced gate transitions alone are insufficient evidence.
