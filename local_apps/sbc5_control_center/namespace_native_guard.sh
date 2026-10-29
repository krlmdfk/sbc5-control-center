#!/bin/bash
set -u
VERSION="3.1.18"
MIG="/homeassistant/sbc5_control_center/migration"
TARGET="local_sbc5_control_center"
LEGACY="local_rpi5_fan_manager"
mkdir -p "$MIG" "$MIG/backups" 2>/dev/null || true
log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] Namespace Guard: $*"; }
if [ "$(jq -r '.phase // empty' "$MIG/state.json" 2>/dev/null || true)" = "COMPLETE" ]; then
  log "Migration state COMPLETE — guard kończy pracę bez health-checków i cleanupu."
  exit 0
fi
spost(){ local ep="$1" body="${2:-{}}"; curl -fsS --max-time 180 -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H 'Content-Type: application/json' -d "$body" "http://supervisor${ep}" >/tmp/sbc5_guard_post.json 2>&1; }
sget(){ local ep="$1" out="$2"; curl -fsS --max-time 30 -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" "http://supervisor${ep}" >"$out" 2>/dev/null; }
ha_get(){ curl -fsS --max-time 20 -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" "http://supervisor/core/api$1" 2>/dev/null; }

detect_target_slug(){
  local addons candidate
  addons="$(curl -fsS --max-time 10 -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" "http://supervisor/addons" 2>/dev/null || true)"
  candidate="$(printf '%s' "$addons" | jq -r '
    (.data.addons // .addons // [])[]? |
    select((.name // "") == "SBC5 Control Center" or (.slug // "") == "local_sbc5_control_center" or ((.slug // "") | endswith("_sbc5_control_center"))) |
    select((.installed // true) == true) |
    select((.state // "") == "started" or (.state // "") == "running") |
    .slug' 2>/dev/null | head -n1)"
  [ -n "$candidate" ] && [ "$candidate" != null ] && printf '%s\n' "$candidate" || printf '%s\n' 'local_sbc5_control_center'
}
TARGET="$(detect_target_slug)"

# Fresh installations from the Apps store have no legacy namespace to migrate.
if [ ! -f "$MIG/control_owner.json" ] && [ ! -f "$MIG/final_cleanup_required.json" ] && \
   [ ! -d /homeassistant/rpi5_control_center ] && [ ! -d /homeassistant/rpi5_fan_manager ] && \
   ! sget "/addons/${LEGACY}/info" /tmp/sbc5_guard_legacy_probe.json; then
  jq -cn --arg at "$(date -Iseconds)" --arg version "$VERSION" --arg target "$TARGET" \
    '{schema:2,version:$version,phase:"COMPLETE",owner:"sbc5",fresh_install:true,target:$target,at:$at}' \
    > "$MIG/state.json"
  log "Fresh Apps-store installation detected (${TARGET}) — legacy namespace migration not required."
  exit 0
fi


import_legacy_state(){
  # Refresh target /data while legacy owns control; after commit this becomes immutable migration input.
  owner="$(jq -r '.owner // "legacy"' "$MIG/control_owner.json" 2>/dev/null || echo legacy)"
  if [ "$owner" != sbc5 ] || [ ! -f /data/sbc5_namespace_import_complete.json ]; then
    for f in ai_cooling_model.json ai_cooling_status.json ai_grid_profile.json fan_calibration.json custom_curve_editor.json custom_curve_config_signature last_fan_profile_code; do
      [ -e "$MIG/data_export/$f" ] && cp -a "$MIG/data_export/$f" "/data/$f" 2>/dev/null || true
    done
    [ -e "$MIG/data_export/fan_control_owner.json" ] && cp -f "$MIG/data_export/fan_control_owner.json" /data/fan_control_owner.json 2>/dev/null || true
    jq -cn --arg at "$(date -Iseconds)" --arg version "$VERSION" '{imported:true,version:$version,source:"legacy_shared_stage",at:$at}' > /data/sbc5_namespace_import_complete.json
  fi
}

wait_native_ready(){
  ok=0
  for i in $(seq 1 120); do
    temp="$(ha_get /states/sensor.sbc5_cpu_temperature | jq -r '.state // empty' 2>/dev/null || true)"
    relay="$(ha_get /states/sensor.sbc5_control_center_host_telemetry | jq -r '.state // empty' 2>/dev/null || true)"
    if [ -n "$temp" ] && [ "$temp" != unknown ] && [ "$temp" != unavailable ] && [ "$temp" != 0 ] && [ -n "$relay" ] && [ "$relay" != unavailable ]; then ok=$((ok+1)); else ok=0; fi
    [ "$ok" -ge 3 ] && return 0
    sleep 5
  done
  return 1
}

remove_legacy_config_entries(){
  # Official Core config-entry endpoint; best effort. Never edit .storage directly.
  for domain in rpi5_control_center_bridge rpi5_fan_manager_bridge; do
    entries="$(ha_get "/config/config_entries/entry?domain=${domain}" || true)"
    echo "$entries" | jq -r '.[].entry_id? // empty' 2>/dev/null | while read -r eid; do
      [ -n "$eid" ] || continue
      code="$(curl -sS --max-time 60 -o /tmp/sbc5_cfg_delete.json -w '%{http_code}' -X DELETE -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" "http://supervisor/core/api/config/config_entries/entry/${eid}" 2>/dev/null || echo 000)"
      log "Legacy config entry ${domain}/${eid}: DELETE HTTP ${code}."
    done
  done
}

migrate_update_dirs(){
  mkdir -p /homeassistant/sbc5_control_center_updates/processed /homeassistant/sbc5_control_center_updates/failed
  for old in /homeassistant/rpi5_control_center_updates /homeassistant/rpi5_fan_manager_updates; do
    [ -d "$old" ] || continue
    find "$old" -maxdepth 1 -type f -name '*.zip' -exec cp -n {} /homeassistant/sbc5_control_center_updates/ \; 2>/dev/null || true
    find "$old/processed" -maxdepth 1 -type f -name '*.zip' -exec cp -n {} /homeassistant/sbc5_control_center_updates/processed/ \; 2>/dev/null || true
    find "$old/failed" -maxdepth 1 -type f -name '*.zip' -exec cp -n {} /homeassistant/sbc5_control_center_updates/failed/ \; 2>/dev/null || true
  done
}

archive_legacy_files(){
  backup="$MIG/backups/final_legacy_purge_$(date +%Y%m%d_%H%M%S)"
  mkdir -p "$backup/config" "$backup/custom_components" "$backup/packages" "$backup/local_apps" 2>/dev/null || true
  # Preserve complete old runtime mirrors for emergency recovery, then remove active dirs.
  for d in rpi5_control_center rpi5_fan_manager; do
    if [ -d "/homeassistant/$d" ]; then cp -a "/homeassistant/$d" "$backup/config/$d" 2>/dev/null || true; rm -rf "/homeassistant/$d"; fi
  done
  for d in rpi5_control_center_updates rpi5_fan_manager_updates; do
    if [ -d "/homeassistant/$d" ]; then cp -a "/homeassistant/$d" "$backup/config/$d" 2>/dev/null || true; rm -rf "/homeassistant/$d"; fi
  done
  for d in rpi5_control_center_bridge rpi5_fan_manager_bridge; do
    if [ -d "/homeassistant/custom_components/$d" ]; then cp -a "/homeassistant/custom_components/$d" "$backup/custom_components/$d" 2>/dev/null || true; rm -rf "/homeassistant/custom_components/$d"; fi
  done
  for f in rpi5_control_center.yaml rpi5_control_center_bridge.yaml rpi5_fan_manager_bridge.yaml rpi5_fan.yaml sbc5_fan.yaml; do
    if [ -f "/homeassistant/packages/$f" ]; then cp -a "/homeassistant/packages/$f" "$backup/packages/$f" 2>/dev/null || true; rm -f "/homeassistant/packages/$f"; fi
  done
  mkdir -p /local_apps/.sbc5_migration_backup
  for d in rpi5_fan_manager rpi5_control_center; do
    if [ -d "/local_apps/$d" ]; then rm -rf "/local_apps/.sbc5_migration_backup/$d" 2>/dev/null || true; mv "/local_apps/$d" "/local_apps/.sbc5_migration_backup/$d" 2>/dev/null || true; fi
  done
  echo "$backup" > "$MIG/final_purge_backup_path"
}

final_cleanup(){
  marker="$MIG/final_cleanup_required.json"
  owner="$(jq -r '.owner // empty' "$MIG/control_owner.json" 2>/dev/null || true)"
  [ -f "$marker" ] || [ "$owner" = sbc5 ] || return 1
  wait_native_ready || { log "Native health incomplete; legacy cleanup postponed."; return 1; }
  migrate_update_dirs
  remove_legacy_config_entries
  # Stop then uninstall old Supervisor identity; preserve app_config until archived from /homeassistant above.
  spost "/addons/${LEGACY}/stop" '{}' || true
  sleep 5
  spost "/addons/${LEGACY}/uninstall" '{"remove_config":false}' || true
  sleep 5
  archive_legacy_files
  spost /store/reload '{}' || true
  spost /addons/reload '{}' || true
  sleep 5
  # Verify old installed identity is really gone and target is the only running SBC5 app.
  legacy_gone=true
  if sget "/addons/${LEGACY}/info" /tmp/sbc5_2632_legacy_info.json; then
    lv="$(jq -r '.data.version // .version // empty' /tmp/sbc5_2632_legacy_info.json 2>/dev/null || true)"
    ls="$(jq -r '.data.state // .state // empty' /tmp/sbc5_2632_legacy_info.json 2>/dev/null || true)"
    [ -n "$lv" ] && legacy_gone=false
  fi
  target_ok=false
  if sget "/addons/${TARGET}/info" /tmp/sbc5_2632_target_info.json; then
    tv="$(jq -r '.data.version // .version // empty' /tmp/sbc5_2632_target_info.json 2>/dev/null || true)"; ts="$(jq -r '.data.state // .state // empty' /tmp/sbc5_2632_target_info.json 2>/dev/null || true)"
    [ "$tv" = "$VERSION" ] && { [ "$ts" = started ] || [ "$ts" = running ]; } && target_ok=true
  fi
  if [ "$legacy_gone" = true ] && [ "$target_ok" = true ]; then
    jq -cn --arg at "$(date -Iseconds)" --arg version "$VERSION" '{schema:2,version:$version,phase:"COMPLETE",owner:"sbc5",legacy_app_removed:true,legacy_config_purged:true,legacy_integrations_removed:true,target_verified:true,at:$at}' > "$MIG/state.json.tmp" && mv -f "$MIG/state.json.tmp" "$MIG/state.json"
    rm -f "$marker" 2>/dev/null || true
    log "FINAL PURGE COMPLETE: aktywny jest wyłącznie kanoniczny runtime SBC5 (${TARGET}); rpi5_* przeniesione do backupu migracji."
    spost /core/check '{}' || { log "Core check po purge nie przeszedł; backup zachowany."; return 0; }
    ( sleep 5; spost /core/restart '{}' || true ) &
    return 0
  fi
  log "Cleanup pending: legacy_gone=$legacy_gone target_ok=$target_ok. Marker pozostaje do ponowienia."
  return 1
}

import_legacy_state
# Ready marker only when target is healthy while still in standby.
if wait_native_ready; then
  jq -cn --arg at "$(date -Iseconds)" --arg version "$VERSION" '{ready:true,version:$version,at:$at}' > "$MIG/native_ready_for_handoff.json"
fi
# Wait for owner commit from legacy coordinator.
for i in $(seq 1 900); do owner="$(jq -r '.owner // "legacy"' "$MIG/control_owner.json" 2>/dev/null || echo legacy)"; [ "$owner" = sbc5 ] && break; sleep 2; done
owner="$(jq -r '.owner // "legacy"' "$MIG/control_owner.json" 2>/dev/null || echo legacy)"
if [ "$owner" = sbc5 ]; then
  jq -cn --arg at "$(date -Iseconds)" '{ack:true,owner:"sbc5",at:$at}' > "$MIG/native_handoff_ack.json"
  final_cleanup || true
fi
