# SBC5 Control Center — Local ZIP / Hybrid Update

## Current update model

SBC5 supports both Home Assistant Apps and verified local ZIP packages, but the full runtime remains owned by the installation channel recognized by Supervisor.

- **Historical local installation (`local_sbc5_control_center`)** — a verified full ZIP may replace the local App source and trigger a rebuild.
- **Store-managed installation (`*_sbc5_control_center`)** — a dashboard/UI-only ZIP is applied directly. A verified full ZIP is accepted as a trigger only when its version exactly matches the version currently published by Home Assistant Apps; SBC5 then delegates the actual runtime replacement to Supervisor's native Store update endpoint.
- **HACS integration** — remains independently managed by HACS.

This prevents a local ZIP from silently changing the runtime of a Store-managed App without Supervisor knowing about the version change.

Canonical ZIP directory: `/config/sbc5_control_center_updates/`.

The package is verified by `update-manifest.json`, SHA-256, platform requirements and update scope before any change is applied.

For the one-time Local → Apps Store handoff, see `STORE_MIGRATION.md`.


## Verified package generation

Release ZIPs are built from the exact `update-manifest.json` allow-list by `scripts/build_local_update.py`. The packer treats hidden paths such as `.github/...` as normal files, verifies every SHA-256 before writing the archive, embeds the exact manifest, and re-verifies the finished ZIP. The main GitHub auto-release workflow attaches `SBC5_UPDATE_<version>.zip` to every successful release.

## Generowanie zweryfikowanej paczki

Paczki wydaniowe ZIP są budowane z dokładnej listy `update-manifest.json` przez `scripts/build_local_update.py`. Generator traktuje ukryte ścieżki, np. `.github/...`, jak zwykłe pliki, sprawdza każdy SHA-256 przed zapisaniem archiwum, osadza dokładny manifest i ponownie weryfikuje gotowy ZIP. Główny workflow Auto Release dołącza `SBC5_UPDATE_<wersja>.zip` do każdego poprawnego wydania.
