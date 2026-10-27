#!/bin/bash
set -u

sleep 12

log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] Canary Diagnostics: $*"; }

phase="$(jq -r '.phase // empty' /homeassistant/sbc5_control_center/migration/state.json 2>/dev/null || true)"
factory_pending=false
[ -e /data/factory_restore_pending ] && factory_pending=true

dev=""
for root in /proc/1/root/sys/class/thermal /sys/class/thermal; do
  [ -d "$root" ] || continue
  for d in "$root"/cooling_device*; do
    [ -r "$d/type" ] || continue
    type="$(cat "$d/type" 2>/dev/null || true)"
    case "${type,,}" in *fan*) dev="$d"; break 2 ;; esac
  done
done

max_state=0
cur_state="?"
cur_state_writable=false
if [ -n "$dev" ]; then
  max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"
  cur_state="$(cat "$dev/cur_state" 2>/dev/null || echo '?')"
  [ -w "$dev/cur_state" ] && cur_state_writable=true
fi

adaptive_state="missing"
adaptive_action="missing"
adaptive_owner="missing"
if [ -s /homeassistant/sbc5_control_center/adaptive_pwm.json ]; then
  adaptive_state="$(jq -r '.state // "unknown"' /homeassistant/sbc5_control_center/adaptive_pwm.json 2>/dev/null || echo unknown)"
  adaptive_action="$(jq -r '.action // "unknown"' /homeassistant/sbc5_control_center/adaptive_pwm.json 2>/dev/null || echo unknown)"
  adaptive_owner="$(jq -r '.control_owner // "unknown"' /homeassistant/sbc5_control_center/adaptive_pwm.json 2>/dev/null || echo unknown)"
fi

log "Adaptive probe: phase=${phase:-missing}; factory_restore_pending=${factory_pending}; dev=${dev:-none}; max_state=${max_state}; cur_state=${cur_state}; cur_state_writable=${cur_state_writable}; adaptive_state=${adaptive_state}; adaptive_action=${adaptive_action}; adaptive_owner=${adaptive_owner}."

if [ -x /dashboard_sync.py ]; then
  card_status="$(SBC5CC_APP_VERSION="${SBC5_RUST_CORE_VERSION:-unknown}" python3 /dashboard_sync.py 2>&1 || true)"
  compact="$(printf '%s' "$card_status" | tr '\n' ' ' | sed 's/[[:space:]]\+/ /g')"
  log "Card UI probe: ${compact}"
fi
