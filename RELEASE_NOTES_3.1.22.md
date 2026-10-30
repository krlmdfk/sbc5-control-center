# SBC5 Control Center 3.1.22

> Hotfix for the 3.1.21 container image build failure.

## English

- Fixed the Dockerfile runtime path for AI Cooling v5.2. Version 3.1.21 copied `ai_cooling_v5_2.py` only to `/ai_cooling.py`, while the later `chmod` step also referenced `/ai_cooling_v5_2.py`, causing Supervisor image builds to fail.
- AI Cooling v5.2 is now packaged both as `/ai_cooling_v5_2.py` and as the public `/ai_cooling.py` entry point.
- Added CI validation for Dockerfile runtime paths so a chmod target cannot silently reference a file that is not present in the image.
- Thermal Predictor guided assist behavior from 3.1.21 is unchanged.
- No Raspberry Pi host reboot is required; the App restarts as part of the update.

## Polski

- Naprawiono ścieżkę runtime w Dockerfile dla AI Cooling v5.2. Wersja 3.1.21 kopiowała `ai_cooling_v5_2.py` tylko jako `/ai_cooling.py`, natomiast późniejszy krok `chmod` odwoływał się również do `/ai_cooling_v5_2.py`, przez co Supervisor przerywał budowanie obrazu.
- AI Cooling v5.2 jest teraz pakowany zarówno jako `/ai_cooling_v5_2.py`, jak i publiczny punkt wejścia `/ai_cooling.py`.
- Dodano test CI ścieżek runtime Dockerfile, aby brakujący plik używany przez `chmod` nie mógł ponownie przejść walidacji.
- Działanie Thermal Predictor guided assist z 3.1.21 pozostaje bez zmian.
- Restart hosta Raspberry Pi nie jest wymagany; aplikacja restartuje się w ramach aktualizacji.
