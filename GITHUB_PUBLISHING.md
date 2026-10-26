# Publikacja SBC5 Control Center na GitHub

Repozytorium: `https://github.com/krlmdfk/sbc5-control-center`

## Cel

To repozytorium zawiera kompletny projekt SBC5 Control Center 2.8.25: aplikację Home Assistant, runtime, integrację natywną, package, dashboardy, branding, dokumentację, migracje i narzędzia aktualizacji.

Integracja przeznaczona do instalacji przez HACS jest publikowana oddzielnie w `krlmdfk/sbc5-control-center-integration`.

## Pierwsza publikacja

1. Utwórz publiczne, puste repo `sbc5-control-center` na koncie `krlmdfk`.
2. Nie twórz README, .gitignore ani licencji z kreatora GitHub.
3. Wgraj zawartość paczki repozytorium, nie sam katalog nadrzędny i nie ZIP.
4. Commit: `Initial public release 2.8.25`.
5. Sprawdź zakładkę Actions. Workflow `Validate build` powinien zakończyć się na zielono.
6. Utwórz Release z tagiem `2.8.25` i tytułem `SBC5 Control Center 2.8.25`.

## Zalecany opis repo

`Raspberry Pi 5 control, cooling, diagnostics and optimization center for Home Assistant OS.`

## Zalecane topics

`home-assistant`, `raspberry-pi-5`, `raspberry-pi`, `cooling`, `monitoring`, `overclocking`, `hacs`, `sbc5`


## Automatyczne artefakty wydania

Po zielonym `Validate build` workflow `Auto release after green CI` tworzy tag/Release i buduje przez `scripts/build_local_update.py` zweryfikowaną paczkę `SBC5_UPDATE_<version>.zip`. Paczka jest tworzona z listy plików `update-manifest.json`, dlatego obejmuje także ukryte ścieżki `.github` i przed publikacją przechodzi kontrolę SHA-256. Ponowne uruchomienie workflow odświeża artefakt przez `gh release upload --clobber`.
