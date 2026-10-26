# SBC5 Control Center — łatwe wydawanie kolejnych wersji

Od tej wersji walidacja lokalna i GitHub Actions używają **tego samego** `scripts/validate_release.py`. Numer wersji nie jest wpisany na sztywno w workflow — źródłem prawdy jest `local_apps/sbc5_control_center/release.json`.

## Przygotowanie wydania

Z głównego repozytorium:

```bash
python scripts/release_easy.py prepare \
  --version 2.8.29 \
  --summary-en "Short English summary" \
  --summary-pl "Krótki opis po polsku" \
  --restart home_assistant \
  --push
```

Polecenie:

1. wymaga czystych repozytoriów main i HACS;
2. wykonuje `git pull --ff-only` w obu repozytoriach;
3. podnosi wersję we wszystkich aktualnych powierzchniach;
4. generuje repo HACS z kanonicznej integracji i szablonów;
5. przelicza `update-manifest.json`;
6. uruchamia tę samą walidację co CI;
7. wykonuje `git diff --check`;
8. tworzy commit w obu repozytoriach;
9. z `--push` wysyła oba branche `main`.

Po zielonym CI:

```bash
python scripts/release_easy.py publish --version 2.8.29
```

To tworzy i wysyła tag w obu repozytoriach.

Jeśli w Termux jest zainstalowany i zalogowany GitHub CLI (`gh`):

```bash
python scripts/release_easy.py publish --version 2.8.29 --github-release
```

wtedy skrypt tworzy również oba GitHub Releases z gotowych `RELEASE_NOTES_<wersja>.md`.

## Zasada bezpieczeństwa

Tagi są tworzone dopiero w fazie `publish`, czyli **po zielonym CI**. Skrypt odmawia tagowania, jeśli lokalny `HEAD` nie jest identyczny z `origin/main`.
