# SBC5 Control Center — Full Namespace Migration 2.6.21

## Goal

Version 2.6.21 migrates the technical identity of the project from the historical `rpi5_*` namespace to native `sbc5_*` identifiers without requiring manual recreation of the installation.

## Automatic sequence

1. Snapshot legacy options, package, bridge and selected persistent AI/calibration state.
2. Publish `local_apps/sbc5_control_center/` and reload Supervisor local apps.
3. Install `local_sbc5_control_center`, copy validated options and start it in migration standby.
4. Install `custom_components/sbc5_control_center/` and `packages/sbc5_control_center.yaml`.
5. Restart Home Assistant and migrate entity-registry customizations to the new `sbc5_*` IDs.
6. Copy current helper states from `rpi5_*` to `sbc5_*`.
7. Replace the old package with `sbc5_legacy_compatibility.yaml`, which forwards legacy references.
8. Export thermal ownership state and commit a blue/green PWM handoff only after the native app reports ready.
9. Require three consecutive native health checks.
10. Stop/uninstall the old app and archive its source only after verification.

## Rollback

Any failed pre-handoff stage leaves the legacy app controlling the fan. If post-handoff health verification fails, `control_owner.json` is atomically returned to `legacy`; the old app remains installed for recovery.

## Compatibility

Legacy `rpi5_*` entity/helper/script IDs remain available through a compatibility shim so existing dashboards and automations keep working. New cards and documentation use only `sbc5_*`. The shim can be removed in a later major release after the legacy-reference report is empty.
