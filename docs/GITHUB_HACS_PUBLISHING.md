# GitHub + HACS / Home Assistant Marketplace — publikacja SBC5 Control Center

**Wersja projektu:** 2.6.17  
**Data przygotowania:** 2026-10-22

## Model publikacji

SBC5 Control Center jest projektem hybrydowym. Nie należy publikować całego pakietu jako jednej integracji HACS. Docelowy model używa dwóch repozytoriów:

1. **Repozytorium aplikacji Home Assistant** — aplikacja `rpi5_fan_manager` (nazwa produktu: SBC5 Control Center), obrazy GHCR, dashboardy i package.
2. **Repozytorium bridge HACS/Marketplace** — jedna integracja `custom_components/rpi5_control_center_bridge`.

## Własność bridge

Wersja 2.6.17 wprowadza marker `.hacs_managed`. Jeżeli marker znajduje się w zainstalowanym `custom_components/rpi5_control_center_bridge`, aplikacja nie kopiuje na niego bridge dołączonego do obrazu i nie zastępuje go podczas lokalnej aktualizacji ZIP.

Dzięki temu:

- HACS/Marketplace może aktualizować integrację niezależnie,
- aplikacja nie wykonuje downgrade'u nowszego bridge,
- użytkownicy bez HACS nadal mają automatyczny bootstrap bridge z pakietu aplikacji.

## Repozytorium aplikacji

Repozytorium zawiera `repository.yaml` oraz katalog `rpi5_fan_manager/`, ponieważ ten slug jest zachowany ze względu na zgodność aktualizacji istniejących instalacji. Nazwa widoczna dla użytkownika to **SBC5 Control Center**; techniczny slug `rpi5_fan_manager` pozostaje wyłącznie dla kompatybilności.

Dla publicznych wydań preferowany jest prebuilt image w GHCR. `config.yaml` powinien wskazywać `image: ghcr.io/<owner>/sbc5-control-center`.

## Repozytorium HACS/Marketplace

Repozytorium bridge zawiera tylko jedną integrację:

```text
custom_components/
└── rpi5_control_center_bridge/
    ├── manifest.json
    ├── .hacs_managed
    ├── brand/
    └── ...
hacs.json
README.md
.github/workflows/
```

`manifest.json` przed publikacją musi otrzymać prawdziwe `documentation`, `issue_tracker` i `codeowners`. Pakiet publikacyjny zawiera skrypt `configure_publication.py`, który uzupełnia je po podaniu GitHub ownera.

## Kolejność pierwszej publikacji

1. Utwórz dwa publiczne repozytoria GitHub.
2. Uruchom `configure_publication.py --owner <github-user-or-org>`.
3. Uruchom `preflight.py`.
4. Wypchnij repozytoria i sprawdź GitHub Actions.
5. W repo aplikacji utwórz release/tag `v2.6.17`; workflow buduje obraz GHCR.
6. Ustaw pakiet GHCR jako publiczny.
7. W repo bridge utwórz pełny GitHub Release `v2.6.17` po przejściu HACS Action i Hassfest.
8. Najpierw testuj bridge jako custom repository w HACS, a dopiero potem zgłaszaj go do katalogu HACS/Marketplace.

## Licencja

Pakiet nie wybiera za właściciela projektu licencji open-source. Przed publiczną publikacją należy świadomie dodać `LICENSE` do obu repozytoriów.


## Branding i prawo

Publiczne repozytoria powinny używać marki `SBC5`, a `Raspberry Pi 5` wyłącznie w opisie kompatybilności. Szczegóły: `TRADEMARKS.md`, `LEGAL.md`, `NOTICE`.
