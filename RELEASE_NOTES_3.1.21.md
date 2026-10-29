# SBC5 Control Center 3.1.21

> Thermal Predictor guided assist, MAE-aware horizon weighting and runtime diagnostics.

## English

### Thermal Predictor guided assist
- Thermal Predictor now contributes to the existing guarded AI Cooling assist path instead of remaining purely observational.
- It does **not** create a second independent fan-control path: Adaptive PWM, AI Cooling limits, deadband, sign guards and thermal safety remain authoritative.
- Forecast influence is deliberately small and is applied to the AI candidate model before the existing bounded assist logic.
- The guidance gain automatically shrinks when predictor confidence is low or average MAE is high.

### Accuracy-aware forecasting
- +30/+60/+120 s forecasts are combined with dynamic weights derived from each horizon's MAE.
- More accurate horizons receive more influence; less accurate horizons are automatically de-emphasized.
- The policy includes active/probation/observe quality gates for continued development and diagnostics.

### Diagnostics
- Adds a dedicated `Thermal Predictor:` runtime log approximately every 60 seconds.
- The log includes +30/+60/+120 forecasts, confidence, average MAE, weighted forecast, target error, horizon weights, guidance gain, accepted/rejected counts and the guarded AI correction.
- Diagnostics travel through the existing evaluator result; no additional polling loop is introduced.

### Safety / restart
- Thermal Predictor cannot bypass the existing AI/Adaptive PWM control envelope.
- No Raspberry Pi host reboot is required. The App restarts as part of the update.
- Restart Home Assistant Core after updating the companion HACS integration.

## Polski

### Thermal Predictor guided assist
- Thermal Predictor zaczyna uczestniczyć w istniejącej, zabezpieczonej ścieżce AI Cooling Assist zamiast pozostawać wyłącznie w trybie obserwacyjnym.
- **Nie powstaje drugi niezależny tor sterowania wentylatorem**: nadrzędne pozostają Adaptive PWM, limity AI Cooling, deadband, sign guard oraz zabezpieczenia termiczne.
- Wpływ prognozy jest celowo mały i trafia do modelu kandydata AI przed istniejącą ograniczoną logiką Assist.
- Wzmocnienie automatycznie maleje przy niższej pewności Predictora lub wyższym średnim MAE.

### Prognoza zależna od skuteczności
- Prognozy +30/+60/+120 s są łączone dynamicznymi wagami zależnymi od MAE każdego horyzontu.
- Dokładniejszy horyzont otrzymuje większy wpływ, a mniej dokładny jest automatycznie osłabiany.
- Polityka zawiera progi active/probation/observe do dalszego strojenia i diagnostyki.

### Diagnostyka
- Dodano osobny wpis `Thermal Predictor:` w logu runtime mniej więcej co 60 sekund.
- Log pokazuje prognozy +30/+60/+120 s, confidence, średnie MAE, prognozę ważoną, błąd względem celu, wagi horyzontów, gain, accepted/rejected oraz końcową korektę zabezpieczonej ścieżki AI.
- Dane diagnostyczne wykorzystują istniejący wynik evaluatora — bez dodatkowej pętli odpytywania.

### Bezpieczeństwo / restart
- Thermal Predictor nie może ominąć istniejących ograniczeń AI/Adaptive PWM.
- Pełny restart Raspberry Pi nie jest wymagany. Aplikacja restartuje się w ramach aktualizacji.
- Po aktualizacji integracji HACS należy zrestartować Home Assistant Core.
