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
