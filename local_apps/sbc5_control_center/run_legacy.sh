#!/bin/bash
set -u

# v2.8.32 Runtime Robustness: some HAOS/App container starts may expose no /tmp.
# SBC5 has historically used /tmp for short-lived lock/cache/TSV files, so create it
# deterministically before any runtime path is evaluated.
if [ ! -d /tmp ]; then
  mkdir -p /tmp 2>/dev/null || true
fi
chmod 1777 /tmp 2>/dev/null || true
export TMPDIR="${TMPDIR:-/tmp}"

APP_VERSION="3.0.3"
REQUIRED_PACKAGE_VERSION="3.0.3"
DEVICE_IDENTITY_REFRESH_SECONDS=300
DEVICE_IDENTITY_LAST_REFRESH=0
SYS_BOARD_REVISION=""
SYS_HARDWARE_REVISION=""
SYS_SERIAL_NUMBER=""
SYS_NETWORK_MAC=""
SYS_OS_NAME=""
SYS_OS_VERSION=""
SYS_OS_PRETTY_NAME=""
SYS_FIRMWARE_VERSION=""
SYS_FIRMWARE_BUILD=""
SYS_BOOTLOADER_VERSION=""
REQUIRED_HA_CORE="2026.10.1"
REQUIRED_HAOS="18.3"
NAMESPACE_RUNTIME_ROLE="sbc5"
NAMESPACE_MIGRATION_DIR="/homeassistant/sbc5_control_center/migration"
NAMESPACE_CONTROL_FILE="$NAMESPACE_MIGRATION_DIR/control_owner.json"
STORE_MIGRATION_SCRIPT="/migration_manager.py"
STORE_MIGRATION_STATUS_FILE="/data/store_migration_status.json"
STORE_MIGRATION_SHARED_DIR="/homeassistant/sbc5_control_center/migration/store_handoff_v1"
PLATFORM_COMPATIBILITY_FILE="/data/platform_compatibility.json"
RESTART_STATE_FILE="/data/restart_required.json"
RESTART_NOTIFICATION_ID="sbc5_restart_required"
UPDATE_NOTIFICATION_ID="sbc5_control_center_update_available"
UPDATE_STATE_FILE="/data/app_update_state.json"
LAST_APP_VERSION_FILE="/data/last_app_version"
POST_UPDATE_STATE_FILE="/data/post_update_restart.json"
LAST_PROFILE_SYNC_BOOT_FILE="/data/last_profile_sync_boot_id"
UX_LAST_ACTION_FILE="/data/ux_last_action.json"
CURVE_EDITOR_STATE_FILE="/data/curve_editor_state_payload.json"
LOCAL_UPDATE_CANDIDATE_FILE="/data/local_update_candidate.json"
LOCAL_UPDATE_LAST_INSTALL_FILE="/data/local_update_last_install.json"
LOCAL_UPDATE_LOCK_FILE="/tmp/sbc5_local_update_install.lock"
LOCAL_UPDATE_LAST_REQUEST_FILE="/data/local_update_last_request_epoch"
LOCAL_UPDATE_COOLDOWN_NOTICE_FILE="/data/local_update_cooldown_notice_epoch"
LOCAL_UPDATE_COOLDOWN_SECONDS=300
BOOT_ACCESS_WARN_LAST_EPOCH=0
BOOT_ACCESS_WARN_INTERVAL_SECONDS=120
NATIVE_REPAIR_POSTED_FILE="/data/native_restart_repair_posted.json"
HOST_SYSFS_MP="/tmp/sbc5_host_sysfs"
BOOT_CONFIG_CACHE_FILE="/tmp/sbc5_boot_config_cache.json"
BOOT_CONFIG_CACHE_SECONDS=300
LOCAL_UPDATE_DIR="/homeassistant/sbc5_control_center_updates"
LOCAL_UPDATE_PROCESSED_DIR="/homeassistant/sbc5_control_center_updates/processed"
LOCAL_UPDATE_FAILED_DIR="/homeassistant/sbc5_control_center_updates/failed"
CARD_UI_VERSION_FILE="/data/card_ui_version"
UI_OVERRIDE_DIR="/data/ui_updates"
UI_DASHBOARD_CARD_FILE="$UI_OVERRIDE_DIR/dashboard_card.json"
UI_UPDATE_STATUS_CARD_FILE="$UI_OVERRIDE_DIR/update_status_card.json"
UI_MANUAL_DIR="/homeassistant/sbc5_control_center_cards"
LEGACY_LOCAL_UPDATE_DIR="/homeassistant/rpi5_control_center_updates"
LEGACY_LOCAL_UPDATE_PROCESSED_DIR="/homeassistant/rpi5_control_center_updates/processed"
LEGACY_LOCAL_UPDATE_FAILED_DIR="/homeassistant/rpi5_control_center_updates/failed"
LEGACY_OLD_LOCAL_UPDATE_DIR="/homeassistant/rpi5_fan_manager_updates"
LEGACY_OLD_LOCAL_UPDATE_PROCESSED_DIR="/homeassistant/rpi5_fan_manager_updates/processed"
LEGACY_OLD_LOCAL_UPDATE_FAILED_DIR="/homeassistant/rpi5_fan_manager_updates/failed"
BRIDGE_SOURCE_DIR="/bridge"
BRIDGE_DEST_DIR="/homeassistant/custom_components/sbc5_control_center"
BRIDGE_EXTERNAL_MARKER="$BRIDGE_DEST_DIR/.hacs_managed"
BRIDGE_PACKAGE_TEMPLATE="/bridge-package.yaml"
BRIDGE_PACKAGE_DEST="/homeassistant/packages/sbc5_control_center_bridge.yaml"
BRIDGE_BOOTSTRAP_MARKER="/data/bridge_bootstrap_pending"
LEGACY_BRIDGE_DEST_DIR="/homeassistant/custom_components/sbc5_fan_manager_bridge"
LEGACY_BRIDGE_MIGRATION_MARKER="/homeassistant/sbc5_control_center/legacy_bridge_migrated.json"
LEGACY_BRIDGE_SOURCE_DIR="/legacy_bridge"
NATIVE_RESTART_MARKER="/homeassistant/sbc5_control_center/restart_required.json"
TELEMETRY_STATE_FILE="/homeassistant/sbc5_control_center/telemetry.json"
REALTIME_STATE_FILE="/homeassistant/sbc5_control_center/realtime.json"
ADAPTIVE_PWM_STATE_FILE="/homeassistant/sbc5_control_center/adaptive_pwm.json"
# v2.5.2 AI Adaptive Cooling Preview — local/offline online learner.
AI_COOLING_MODEL_FILE="/data/ai_cooling_model.json"
AI_COOLING_STATUS_FILE="/data/ai_cooling_status.json"
AI_COOLING_MIRROR_FILE="/homeassistant/sbc5_control_center/ai_cooling.json"
AI_COOLING_SCRIPT="/ai_cooling.py"
AI_GRID_PROFILE_FILE="/data/ai_grid_profile.json"
FAN_CONTROL_OWNER_FILE="/data/fan_control_owner.json"
FAN_CONTROL_HANDOFF_FILE="/data/fan_control_update_handoff.json"
FAN_CONTROL_HANDOFF_MAX_AGE_SECONDS=300
# v2.2.0: canonical calibration state lives in persistent app /data.
# A mirror under the HA config tree is maintained for diagnostics/backward compatibility.
FAN_CALIBRATION_DATA_FILE="/data/fan_calibration.json"
FAN_CALIBRATION_MIRROR_FILE="/homeassistant/sbc5_control_center/fan_calibration.json"
FAN_CALIBRATION_STATE_FILE="$FAN_CALIBRATION_DATA_FILE"
FAN_CALIBRATION_LOCK_FILE="/tmp/sbc5_fan_calibration.lock"
# v2.1.0 AI-ready fan calibration. The custom overlay exposes 0..100 cooling
# states, so one cooling state corresponds to approximately one PWM percent.
FAN_CALIBRATION_MIN_TEST_PCT=1
FAN_CALIBRATION_MAX_START_PCT=60
FAN_CALIBRATION_SPIN_RPM=100
FAN_CALIBRATION_START_MARGIN_PCT=2
FAN_CALIBRATION_RUN_MARGIN_PCT=1
FAN_CALIBRATION_SETTLE_SECONDS=1
FAN_CALIBRATION_SAMPLE_COUNT=2
FAN_CALIBRATION_MAX_START_TEMP_MILLI=60000
FAN_CALIBRATION_MAX_TEMP_MILLI=70000
# v1.9.6 Balanced Telemetry: standardowe sensory chłodzenia odświeżane co 5 s.
# Lightweight HA model: full telemetry=15 s, realtime cooling=5 s, host relay=30 s, AI relay=15 s on-change/5 min keepalive,
# PMIC=30 s, SYSTEM=60 s, SLOW USB/zasilanie/config=120 s.
TELEMETRY_PUBLISH_INTERVAL_SECONDS=15
REALTIME_PUBLISH_INTERVAL_SECONDS=5
HOST_RELAY_INTERVAL_SECONDS=30
TELEMETRY_PMIC_INTERVAL_SECONDS=30
TELEMETRY_EXTENDED_INTERVAL_SECONDS=60
TELEMETRY_POWER_INTERVAL_SECONDS=120
PROFILE_REPORT_INTERVAL_SECONDS=300
PROFILE_OPTIONS_SYNC_INTERVAL_SECONDS=300
UX_RUNTIME_POLL_SECONDS=10
UX_RUNTIME_REFRESH_TICKS=30
RESTART_MANAGER_INTERVAL_SECONDS=120
RESTART_LAST_PUBLISHED_SIGNATURE=""
CONFIG_DISABLED_POLL_SECONDS=30
TELEMETRY_LAST_POWER_REFRESH=0
TELEMETRY_LAST_PMIC_REFRESH=0
TELEMETRY_LAST_EXTENDED_REFRESH=0
PERF_CYCLE_COUNT=0
PERF_FAST_COUNT=0
PERF_NORMAL_COUNT=0
PERF_SLOW_COUNT=0
PERF_LAST_CYCLE_MS=0
PERF_LAST_POWER_MS=0
PERF_LAST_EXTENDED_MS=0
PERF_LAST_POWER_MODE="startup"
PERF_LAST_CYCLE_TIER="startup"
PERF_LAST_EXTENDED_REFRESHED="false"
PERF_LAST_STATE_PUBLISH=0
TELEMETRY_LAST_RELAY_PUBLISH=0
TELEMETRY_LAST_AI_RELAY_PUBLISH=0
TELEMETRY_LAST_AI_RELAY_CHECK=0
AI_RUNTIME_LAST_SIGNATURE=""
AI_RUNTIME_RELAY_INTERVAL_SECONDS=15
AI_RUNTIME_RELAY_KEEPALIVE_SECONDS=300
ADAPTIVE_PWM_LOG_KEEPALIVE_WRITES=6
AI_COOLING_LOG_KEEPALIVE_CYCLES=30
PERF_PREV_CGROUP_USAGE_USEC=0
PERF_PREV_WALL_USEC=0
# v1.9.10 Multicore Telemetry: read-only diagnostic stages may run in parallel.
MULTICORE_TELEMETRY_ENABLED="true"
MULTICORE_WORKERS_CONFIG="auto"
MULTICORE_WORKERS_EFFECTIVE=1
PERF_LAST_PARALLEL_JOBS=0
PERF_LAST_PARALLEL_MS=0
PERF_LAST_PARALLEL_MODE="sequential"
PERF_PARALLEL_CYCLES=0
PERF_MAX_PARALLEL_JOBS=0
PERF_EXTENDED_DONE_THIS_CYCLE="false"
# v1.9.14 persistent multicore profiler.
PERF_LAST_SLOW_CYCLE_MS=0
PERF_LAST_SLOW_PARALLEL_JOBS=0
PERF_LAST_SLOW_PARALLEL_MS=0
PERF_PARALLEL_SAMPLES=0
PERF_PARALLEL_MS_TOTAL=0
PERF_PARALLEL_JOBS_TOTAL=0
PERF_MAX_PARALLEL_MS=0
PERF_LAST_PARALLEL_EST_SEQ_MS=0
PERF_LAST_MULTICORE_GAIN_MS=0
PERF_LAST_MULTICORE_GAIN_PERCENT=0
PERF_LAST_PARALLEL_EFFICIENCY_PERCENT=0
# v1.9.6: lekka telemetria per-core. Usage jest liczone jako delta /proc/stat co 5 s.
CPU_CORE_PREV_TOTAL=(0 0 0 0)
CPU_CORE_PREV_IDLE=(0 0 0 0)
SYS_CPU_CORE_FREQS_JSON='[null,null,null,null]'
SYS_CPU_CORE_USAGE_JSON='[null,null,null,null]'
RELEASE_METADATA_FILE="/release.json"
CURRENT_BOOT_ID="$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || echo unknown)"
LAST_RESTART_STATE=""

MARK_BEGIN="# BEGIN SBC5 CONTROL CENTER"
MARK_END="# END SBC5 CONTROL CENTER"
SYSTEM_MARK_BEGIN="# BEGIN SBC5 CONTROL CENTER SYSTEM"
SYSTEM_MARK_END="# END SBC5 CONTROL CENTER SYSTEM"
SYSTEM_BACKUP_DIR="/data/boot_config_backups"
CONFIG_CATALOG_FILE="/config_txt_catalog.json"
CONFIG_MANAGER_FILENAME="sbc5cc-managed.txt"
CONFIG_MANAGER_MARK_BEGIN="# BEGIN SBC5 CONTROL CENTER CONFIG MANAGER"
CONFIG_MANAGER_MARK_END="# END SBC5 CONTROL CENTER CONFIG MANAGER"
CONFIG_MANAGER_ABSENT_FILE="/data/sbc5cc-managed.absent"
# v2.7.2: CPU Profile Manager uses a persistent single source of truth independent from generic Config.txt Manager.
CPU_PROFILE_FILENAME="sbc5cc-cpu-profile.txt"
CPU_PROFILE_MARK_BEGIN="# BEGIN SBC5 CONTROL CENTER CPU PROFILE"
CPU_PROFILE_MARK_END="# END SBC5 CONTROL CENTER CPU PROFILE"
CPU_PROFILE_STATE_FILE="/data/cpu_profile_state.json"
CPU_PROFILE_STATE_SCHEMA=2
# v2.8.15: GPU/V3D/ISP profile now has the same persistent requested-state model as CPU.
# This prevents transient/default Supervisor options from reverting a dashboard selection after host reboot.
GPU_PROFILE_STATE_FILE="/data/gpu_profile_state.json"
GPU_PROFILE_STATE_SCHEMA=1
# v2.8.18: canonical profile reconciliation across YAML, Ingress UI and native Supervisor options.
PROFILE_STATE_RECONCILE_INTERVAL_SECONDS=300
LAST_PROFILE_STATE_OPTIONS_SIGNATURE=""
# v2.8.18: tracks the last profile subset persisted in Supervisor so native Configuration edits
# can be distinguished from stale/default Supervisor values after an upgrade or reboot.
SUPERVISOR_PROFILE_SYNC_FILE="/data/profile_supervisor_sync_state.json"
STORE_MIGRATION_PROFILE_GUARD_FILE="/data/store_migration_profile_guard.json"
SUPERVISOR_PROFILE_SYNC_SCHEMA=1

OVERLAY_10_NAME="rpi5-stable50-10step"
OVERLAY_10_DTS="/rpi5-stable50-10step-overlay.dts"

OVERLAY_15_NAME="rpi5-stable50-15step"
OVERLAY_15_DTS="/rpi5-stable50-15step-overlay.dts"

OVERLAY_CUSTOM_LEGACY_NAME="rpi5-custom15"
OVERLAY_CUSTOM_LEGACY_DTS="/tmp/rpi5-custom15-overlay.dts"
OPTIONS_FILE="/data/options.json"
CONFIG_UI_RELOAD_FILE="/data/config_ui_reload.request"
CONFIG_UI_MIGRATION_MARKER="/data/config_ui_sections_migrated_242"
CONFIG_UI_PORT=8099

CURVE1_NAME="Zbalansowana"
CURVE1_TARGET_C="50.0"
CURVE1_HYST_DENSE_C="0.75"
CURVE1_HYST_OUTER_C="1.0"
CURVE1_MIN_PWM_PCT="29"
CURVE1_TARGET_PWM_PCT="55"
CURVE1_MAX_PWM_PCT="100"
CUSTOM_FAN_CURVES_JSON='[]'
CUSTOM_CURVE_INDEX="1"
CUSTOM_CURVE_NAME="Zbalansowana"
CUSTOM_TARGET_C="50.0"
CUSTOM_HYST_DENSE_C="0.75"
CUSTOM_HYST_OUTER_C="1.0"
CUSTOM_MIN_PWM_PCT="29"
CUSTOM_TARGET_PWM_PCT="55"
CUSTOM_MAX_PWM_PCT="100"
CUSTOM_RESPONSE_MODE="precise"
APPLY_CUSTOM_ON_START="false"
APPLY_CUSTOM_CURVE_ON_START="off"
# v2.0.3 Balanced Adaptive PWM: micro-regulator around the configured setpoint.
# v2.3.1: explicit control model.
COOLING_CONTROL_MODE="automatic"
COOLING_AUTO_STYLE="balanced"
HYBRID_CORRECTION_LIMIT_PCT="10"
MANUAL_HYSTERESIS_C="1.0"
ADAPTIVE_PWM_ENABLED="true"
ADAPTIVE_PWM_DEADBAND_C="0.75"
ADAPTIVE_PWM_INTERVAL_SECONDS="10"
ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES="2"
ADAPTIVE_PWM_LAST_ACTION="startup"
AI_COOLING_SECTION_ENABLED="false"
AI_COOLING_MODE="learning"
AI_COOLING_EFFECTIVE_MODE="disabled"
AI_COOLING_ASSIST_LIMIT_PCT="5"
AI_COOLING_MIN_SAMPLES="30"
AI_COOLING_EVAL_CYCLES="1"
FAN_CONTROL_ZONE=""
FAN_CONTROL_ORIGINAL_POLICY=""
FAN_CONTROL_OWNER="kernel"
RESTART_POLICY="ask"
PRE_RESTART_CONFIG_CHECK="true"
RESTART_NOTICE_ON_START="true"
POST_UPDATE_RESTART_PROMPT="true"
ACTIONABLE_MOBILE_NOTIFICATIONS="true"
MOBILE_NOTIFY_SERVICE="auto"
UPDATE_CHECK_ENABLED="true"
UPDATE_CHECK_INTERVAL_HOURS="6"
UPDATE_NOTIFY="true"
DEFAULT_APP_UPDATE_MANIFEST_URL="https://raw.githubusercontent.com/krlmdfk/sbc5-control-center/main/local_apps/sbc5_control_center/release.json"
APP_UPDATE_MANIFEST_URL="$DEFAULT_APP_UPDATE_MANIFEST_URL"
LOCAL_PACKAGE_UPDATES_ENABLED="true"
LOCAL_PACKAGE_SCAN_INTERVAL_MINUTES="2"
LOCAL_PACKAGE_KEEP_PROCESSED="true"
LOCAL_PACKAGE_CLEANUP_ENABLED="true"
LOCAL_PACKAGE_PROCESSED_RETENTION="2"
LOCAL_PACKAGE_FAILED_RETENTION="2"
NATIVE_RESTART_REPAIR="true"
SECTION_ADAPTIVE_ADVANCED_ENABLED="false"
SECTION_NOTIFICATIONS_ENABLED="true"
SECTION_UPDATES_ENABLED="true"
SECTION_TELEMETRY_ENABLED="true"
CONFIG_TXT_OPTIONS_ENABLED="false"
CONFIG_GPU_PROFILE="factory"
CONFIG_TXT_OPTIONS_SYNC_INTERVAL="5"
CONFIG_TXT_OPTIONS_ADVANCED="false"
LAST_CONFIG_OPTIONS_SIGNATURE=""
LAST_CUSTOM_OPTIONS_SIGNATURE=""
RESOLVED_MOBILE_NOTIFY_SERVICE=""
LAST_UPDATE_SIGNATURE=""
CUSTOM_TRIPS_CSV=""
CUSTOM_PRETTY=""
CUSTOM_PROFILE_LABEL="Własna 1 — Zbalansowana · 50°C · 15 pkt"
declare -a CUSTOM_T CUSTOM_H CUSTOM_PWM
declare -a CUSTOM_CURVE_LABELS CUSTOM_CURVE_SELECTOR_LABELS CUSTOM_CURVE_TRIPS CUSTOM_CURVE_PRETTIES
LAST_FAN_PROFILE_FILE="/data/last_fan_profile_code"
FACTORY_RESTORE_PENDING_FILE="/data/factory_restore_pending"
FAN_PROFILE_RECONCILE_FILE="/data/fan_profile_reconcile.json"
SYSTEM_DEFAULTS_LOCK_FILE="/data/sbc5_system_defaults_lock"
CUSTOM_CURVE_EDITOR_FILE="/data/custom_curve_editor.json"
CUSTOM_CURVE_CONFIG_SIGNATURE_FILE="/data/custom_curve_config_signature"
CUSTOM_CURVE_CONFIG_SIGNATURE=""
CUSTOM_CURVE_CONFIG_CHANGED="false"

ACTIVE_OVERLAY_NAME=""
ACTIVE_OVERLAY_DTS=""
ACTIVE_OVERLAY_DTBO=""


namespace_control_allowed() {
  # A completed namespace migration is authoritative: the canonical SBC5
  # runtime owns control even if an obsolete control_owner.json survived
  # an older migration/rollback cycle. During an unfinished migration the
  # explicit owner marker remains the safety interlock.
  if [ "$(jq -r '.phase // empty' "$NAMESPACE_MIGRATION_DIR/state.json" 2>/dev/null || true)" = "COMPLETE" ]; then
    return 0
  fi
  local owner="sbc5"
  if [ -s "$NAMESPACE_CONTROL_FILE" ]; then owner="$(jq -r '.owner // "legacy"' "$NAMESPACE_CONTROL_FILE" 2>/dev/null || echo legacy)"; fi
  [ "$owner" = "sbc5" ]
}

install_project_logo() {
  [ -r /logo.png ] || return 0
  mkdir -p /homeassistant/www/sbc5_control_center 2>/dev/null || return 0
  cp -f /logo.png /homeassistant/www/sbc5_control_center/logo.png 2>/dev/null || true
}

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

boot_access_warn_throttled() {
  local message="$1" now
  now="$(date +%s)"
  case "$now" in ''|*[!0-9]*) now=0 ;; esac
  if [ "$BOOT_ACCESS_WARN_LAST_EPOCH" -eq 0 ] || [ $((now - BOOT_ACCESS_WARN_LAST_EPOCH)) -ge "$BOOT_ACCESS_WARN_INTERVAL_SECONDS" ]; then
    log "$message"
    BOOT_ACCESS_WARN_LAST_EPOCH="$now"
  fi
}

# Bash 5 udostępnia EPOCHREALTIME bez uruchamiania zewnętrznego procesu.
epoch_us() {
  local v="${EPOCHREALTIME:-}"
  if [[ "$v" =~ ^([0-9]+)\.([0-9]{6})$ ]]; then
    printf '%s%s\n' "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
  else
    printf '%s000000\n' "$(date +%s)"
  fi
}

read_cgroup_cpu_usage_usec() {
  local key value raw
  if [ -r /sys/fs/cgroup/cpu.stat ]; then
    while read -r key value; do
      if [ "$key" = "usage_usec" ]; then
        printf '%s\n' "$value"
        return 0
      fi
    done < /sys/fs/cgroup/cpu.stat
  fi
  if [ -r /sys/fs/cgroup/cpuacct/cpuacct.usage ]; then
    IFS= read -r raw < /sys/fs/cgroup/cpuacct/cpuacct.usage || true
    case "$raw" in ''|*[!0-9]*) return 1 ;; esac
    printf '%s\n' "$((raw / 1000))"
    return 0
  fi
  return 1
}

read_cgroup_memory_bytes() {
  local raw
  if [ -r /sys/fs/cgroup/memory.current ]; then
    IFS= read -r raw < /sys/fs/cgroup/memory.current || true
  elif [ -r /sys/fs/cgroup/memory/memory.usage_in_bytes ]; then
    IFS= read -r raw < /sys/fs/cgroup/memory/memory.usage_in_bytes || true
  else
    return 1
  fi
  case "$raw" in ''|*[!0-9]*) return 1 ;; esac
  printf '%s\n' "$raw"
}

read_cpu_allowed_list() {
  local key value
  while IFS=$'\t:' read -r key value; do
    key="${key//[[:space:]]/}"
    if [ "$key" = "Cpus_allowed_list" ]; then
      value="${value#${value%%[![:space:]]*}}"
      printf '%s\n' "$value"
      return 0
    fi
  done < /proc/self/status 2>/dev/null || true
  printf 'unknown\n'
}

resolve_multicore_workers() {
  local cores=1 cfg="${MULTICORE_WORKERS_CONFIG:-auto}"
  if command -v nproc >/dev/null 2>&1; then
    cores="$(nproc 2>/dev/null || echo 1)"
  fi
  case "$cores" in ''|*[!0-9]*) cores=1 ;; esac
  [ "$cores" -lt 1 ] 2>/dev/null && cores=1
  [ "$cores" -gt 4 ] 2>/dev/null && cores=4
  if [ "$MULTICORE_TELEMETRY_ENABLED" != "true" ]; then
    MULTICORE_WORKERS_EFFECTIVE=1
  elif [ "$cfg" = "auto" ]; then
    MULTICORE_WORKERS_EFFECTIVE="$cores"
    [ "$MULTICORE_WORKERS_EFFECTIVE" -gt 2 ] 2>/dev/null && MULTICORE_WORKERS_EFFECTIVE=2
  else
    case "$cfg" in 1|2|3|4) MULTICORE_WORKERS_EFFECTIVE="$cfg" ;; *) MULTICORE_WORKERS_EFFECTIVE="$cores" ;; esac
    [ "$MULTICORE_WORKERS_EFFECTIVE" -gt "$cores" ] 2>/dev/null && MULTICORE_WORKERS_EFFECTIVE="$cores"
  fi
  [ "$MULTICORE_WORKERS_EFFECTIVE" -lt 1 ] 2>/dev/null && MULTICORE_WORKERS_EFFECTIVE=1
}

# A worker starts from the current shell state, executes one read-only collector and
# writes only changed SYS_* variables. Parent imports the delta after wait().
parallel_worker_capture() {
  local fn="$1" out="$2" v before_line after_line export_line worker_start_us worker_end_us
  worker_start_us="$(epoch_us)"
  declare -A before=()
  while IFS= read -r v; do
    before["$v"]="$(declare -p "$v" 2>/dev/null || true)"
  done < <(compgen -A variable SYS_)

  "$fn" || true
  : > "$out"
  while IFS= read -r v; do
    after_line="$(declare -p "$v" 2>/dev/null || true)"
    [ -n "$after_line" ] || continue
    [ "${before[$v]-}" = "$after_line" ] && continue
    export_line="$after_line"
    export_line="${export_line/#declare -- /declare -g -- }"
    export_line="${export_line/#declare -a /declare -g -a }"
    export_line="${export_line/#declare -A /declare -g -A }"
    printf '%s\n' "$export_line" >> "$out"
  done < <(compgen -A variable SYS_)
  worker_end_us="$(epoch_us)"
  printf '%s\n' "$(( (worker_end_us - worker_start_us) / 1000 ))" > "${out}.ms" 2>/dev/null || true
}

run_parallel_collectors() {
  local -a fns=("$@") pids=() outs=()
  local total="${#fns[@]}" limit start_us end_us idx fn out pid active=0 j worker_ms sequential_ms=0 gain_ms=0 gain_pct=0 efficiency=0
  PERF_LAST_PARALLEL_JOBS="$total"
  PERF_LAST_PARALLEL_MS=0
  PERF_LAST_PARALLEL_MODE="sequential"
  [ "$total" -gt 0 ] || return 0
  resolve_multicore_workers
  limit="$MULTICORE_WORKERS_EFFECTIVE"

  if [ "$MULTICORE_TELEMETRY_ENABLED" != "true" ] || [ "$limit" -le 1 ] 2>/dev/null || [ "$total" -le 1 ] 2>/dev/null; then
    for fn in "${fns[@]}"; do "$fn" || true; done
    return 0
  fi

  start_us="$(epoch_us)"
  PERF_LAST_PARALLEL_MODE="parallel"
  PERF_PARALLEL_CYCLES=$((PERF_PARALLEL_CYCLES + 1))
  if [ "$total" -gt "$PERF_MAX_PARALLEL_JOBS" ] 2>/dev/null; then PERF_MAX_PARALLEL_JOBS="$total"; fi
  idx=0
  for fn in "${fns[@]}"; do
    out="/tmp/rpi5cc_worker_${$}_${idx}.env"
    rm -f "$out" 2>/dev/null || true
    parallel_worker_capture "$fn" "$out" &
    pid=$!
    pids+=("$pid")
    outs+=("$out")
    active=$((active + 1))
    idx=$((idx + 1))
    if [ "$active" -ge "$limit" ] 2>/dev/null; then
      for j in "${pids[@]}"; do wait "$j" 2>/dev/null || true; done
      pids=()
      active=0
    fi
  done
  for j in "${pids[@]}"; do wait "$j" 2>/dev/null || true; done

  # Import in the same logical order in which collectors were requested.
  for out in "${outs[@]}"; do
    worker_ms=0
    if [ -r "${out}.ms" ]; then worker_ms="$(<"${out}.ms")"; fi
    case "$worker_ms" in ''|*[!0-9]*) worker_ms=0 ;; esac
    sequential_ms=$((sequential_ms + worker_ms))
    if [ -s "$out" ]; then
      # Generated by declare -p and rewritten to declare -g; no external input.
      # shellcheck disable=SC1090
      source "$out"
    fi
    rm -f "$out" "${out}.ms" 2>/dev/null || true
  done
  end_us="$(epoch_us)"
  PERF_LAST_PARALLEL_MS=$(( (end_us - start_us) / 1000 ))
  PERF_LAST_PARALLEL_EST_SEQ_MS="$sequential_ms"
  [ "$sequential_ms" -gt "$PERF_LAST_PARALLEL_MS" ] 2>/dev/null && gain_ms=$((sequential_ms - PERF_LAST_PARALLEL_MS))
  [ "$sequential_ms" -gt 0 ] 2>/dev/null && gain_pct=$((gain_ms * 100 / sequential_ms))
  if [ "$PERF_LAST_PARALLEL_MS" -gt 0 ] 2>/dev/null && [ "$total" -gt 0 ] 2>/dev/null; then
    efficiency=$((sequential_ms * 100 / (PERF_LAST_PARALLEL_MS * total)))
    [ "$efficiency" -gt 100 ] 2>/dev/null && efficiency=100
  fi
  PERF_LAST_MULTICORE_GAIN_MS="$gain_ms"
  PERF_LAST_MULTICORE_GAIN_PERCENT="$gain_pct"
  PERF_LAST_PARALLEL_EFFICIENCY_PERCENT="$efficiency"
  PERF_PARALLEL_SAMPLES=$((PERF_PARALLEL_SAMPLES + 1))
  PERF_PARALLEL_MS_TOTAL=$((PERF_PARALLEL_MS_TOTAL + PERF_LAST_PARALLEL_MS))
  PERF_PARALLEL_JOBS_TOTAL=$((PERF_PARALLEL_JOBS_TOTAL + total))
  [ "$PERF_LAST_PARALLEL_MS" -gt "$PERF_MAX_PARALLEL_MS" ] 2>/dev/null && PERF_MAX_PARALLEL_MS="$PERF_LAST_PARALLEL_MS"
}

yesno() {
  if [ "$1" = "1" ]; then echo "TAK"; else echo "NIE"; fi
}

# v1.7.10: wspólny, odporny odczyt plików hosta.
# Kolejność: bieżący namespace -> root hosta przez /proc/1/root -> nsenter.
host_read_text() {
  local path="$1" f value
  for f in "$path" "/proc/1/root${path}"; do
    [ -r "$f" ] || continue
    value="$(cat -- "$f" 2>/dev/null | tr -d '\000\r' || true)"
    [ -n "$value" ] && { printf '%s\n' "$value"; return 0; }
  done

  if command -v nsenter >/dev/null 2>&1; then
    value="$(nsenter -t 1 -m -r -- sh -c 'cat -- "$1"' sh "$path" 2>/dev/null | tr -d '\000\r' || true)"
    [ -n "$value" ] && { printf '%s\n' "$value"; return 0; }
  fi
  return 1
}


# v1.9.3: jednowierszowe sysfs/proc czytamy wbudowanym read zamiast cat|tr|head.
host_read_one_line() {
  local path="$1" f value=""
  for f in "$path" "/proc/1/root${path}"; do
    [ -r "$f" ] || continue
    IFS= read -r value < "$f" 2>/dev/null || true
    value="${value//$'\r'/}"
    [ -n "$value" ] && { printf '%s\n' "$value"; return 0; }
  done
  if command -v nsenter >/dev/null 2>&1; then
    value="$(nsenter -t 1 -m -r -- sh -c 'IFS= read -r v < "$1" 2>/dev/null || true; printf "%s" "$v"' sh "$path" 2>/dev/null || true)"
    [ -n "$value" ] && { printf '%s\n' "$value"; return 0; }
  fi
  return 1
}

khz_to_mhz_1dp() {
  local v="$1" t
  case "$v" in ''|*[!0-9]*) printf 'null\n'; return 1 ;; esac
  t=$(( (v + 50) / 100 ))
  printf '%d.%d\n' "$((t/10))" "$((t%10))"
}

millideg_to_c_1dp() {
  local v="$1" neg="" a t
  case "$v" in ''|*[!0-9-]*) printf '0.0\n'; return 1 ;; esac
  if [ "$v" -lt 0 ] 2>/dev/null; then neg="-"; a=$((-v)); else a=$v; fi
  t=$(( (a + 50) / 100 ))
  printf '%s%d.%d\n' "$neg" "$((t/10))" "$((t%10))"
}

host_uname() {
  local flag="$1" value
  value="$(uname "$flag" 2>/dev/null || true)"
  [ -n "$value" ] && { printf '%s\n' "$value"; return 0; }
  if command -v nsenter >/dev/null 2>&1; then
    value="$(nsenter -t 1 -m -r -- uname "$flag" 2>/dev/null || true)"
    [ -n "$value" ] && { printf '%s\n' "$value"; return 0; }
  fi
  return 1
}

num_in_range() {
  awk -v v="$1" -v lo="$2" -v hi="$3" 'BEGIN { exit !(v+0 >= lo+0 && v+0 <= hi+0) }'
}

curve_factory_defaults() {
  local idx="${1:-1}"
  case "$idx" in
    1) FACTORY_CURVE_NAME="Zbalansowana"; FACTORY_TARGET_C="50.0" ;;
    2) FACTORY_CURVE_NAME="Chłodna"; FACTORY_TARGET_C="48.0" ;;
    3) FACTORY_CURVE_NAME="Komfortowa"; FACTORY_TARGET_C="52.0" ;;
    4) FACTORY_CURVE_NAME="Cicha"; FACTORY_TARGET_C="55.0" ;;
    5) FACTORY_CURVE_NAME="Ultra cicha"; FACTORY_TARGET_C="58.0" ;;
    *) FACTORY_CURVE_NAME="Zbalansowana"; FACTORY_TARGET_C="50.0" ;;
  esac
  FACTORY_HYST_DENSE_C="0.75"
  FACTORY_HYST_OUTER_C="1.0"
  FACTORY_MIN_PWM_PCT="29"
  FACTORY_TARGET_PWM_PCT="55"
  FACTORY_MAX_PWM_PCT="100"
  FACTORY_RESPONSE_MODE="precise"
}

curve_selector_label() {
  local idx="$1" name="$2" target="${3:-}" pretty_target
  if [ -n "$target" ]; then
    pretty_target="$(awk -v t="$target" 'BEGIN{if(t==int(t))printf "%d",t;else printf "%.1f",t}' | sed 's/\./,/g')"
    printf 'Własna %s — %s · %s°C\n' "$idx" "$name" "$pretty_target"
  else
    printf 'Własna %s — %s\n' "$idx" "$name"
  fi
}

format_target_for_label() {
  awk -v t="$CUSTOM_TARGET_C" 'BEGIN {
    if (t == int(t)) printf "%d", t;
    else if ((t*10) == int(t*10)) printf "%.1f", t;
    else printf "%.2f", t;
  }' | sed 's/\./,/g'
}

refresh_custom_profile_label() {
  local mode_label="Auto"
  case "${COOLING_CONTROL_MODE:-automatic}" in
    hybrid) mode_label="Hybryda" ;;
    manual) mode_label="Ręczny" ;;
    *) mode_label="Auto" ;;
  esac
  CUSTOM_PROFILE_LABEL="Własna ${CUSTOM_CURVE_INDEX} — ${CUSTOM_CURVE_NAME} · $(format_target_for_label)°C · ${mode_label}"
}

sanitize_curve_name() {
  local value="$1" fallback="$2"
  value="$(printf '%s' "$value" | tr '\t\r\n' '   ' | sed 's/[[:space:]][[:space:]]*/ /g; s/^ //; s/ $//' | cut -c1-32)"
  [ -n "$value" ] || value="$fallback"
  printf '%s\n' "$value"
}

load_custom_curve() {
  local idx="${1:-1}" row pos default_target fallback_name
  case "$idx" in 1|2|3|4|5) ;; *) idx=1 ;; esac
  CUSTOM_CURVE_INDEX="$idx"
  CUSTOM_RESPONSE_MODE="precise"

  if [ "$idx" = "1" ]; then
    curve_factory_defaults "$idx"
    CUSTOM_CURVE_NAME="$(sanitize_curve_name "$CURVE1_NAME" "$FACTORY_CURVE_NAME")"
    CUSTOM_TARGET_C="$CURVE1_TARGET_C"
    CUSTOM_HYST_DENSE_C="$CURVE1_HYST_DENSE_C"
    CUSTOM_HYST_OUTER_C="$CURVE1_HYST_OUTER_C"
    CUSTOM_MIN_PWM_PCT="$CURVE1_MIN_PWM_PCT"
    CUSTOM_TARGET_PWM_PCT="$CURVE1_TARGET_PWM_PCT"
    CUSTOM_MAX_PWM_PCT="$CURVE1_MAX_PWM_PCT"
  else
    pos=$((idx - 2))
    curve_factory_defaults "$idx"
    default_target="$FACTORY_TARGET_C"
    fallback_name="$FACTORY_CURVE_NAME"
    row="$(jq -r --argjson p "$pos" --arg n "$fallback_name" --arg dt "$default_target" '
      (.[$p] // {}) as $c |
      [
        (($c.name // $n) | tostring | gsub("[\\t\\r\\n]"; " ")),
        ($c.target_temp_c // ($dt|tonumber)),
        ($c.hysteresis_dense_c // 0.75),
        ($c.hysteresis_outer_c // 1.0),
        ($c.min_pwm_percent // 29),
        ($c.target_pwm_percent // 55),
        ($c.max_pwm_percent // 100)
      ] | @tsv' <<<"$CUSTOM_FAN_CURVES_JSON" 2>/dev/null || true)"
    if [ -n "$row" ]; then
      IFS=$'\t' read -r CUSTOM_CURVE_NAME CUSTOM_TARGET_C CUSTOM_HYST_DENSE_C CUSTOM_HYST_OUTER_C CUSTOM_MIN_PWM_PCT CUSTOM_TARGET_PWM_PCT CUSTOM_MAX_PWM_PCT <<< "$row"
    else
      CUSTOM_CURVE_NAME="$fallback_name"; CUSTOM_TARGET_C="$default_target"; CUSTOM_HYST_DENSE_C="0.75"; CUSTOM_HYST_OUTER_C="1.0"; CUSTOM_MIN_PWM_PCT="29"; CUSTOM_TARGET_PWM_PCT="55"; CUSTOM_MAX_PWM_PCT="100"
    fi
    CUSTOM_CURVE_NAME="$(sanitize_curve_name "$CUSTOM_CURVE_NAME" "$fallback_name")"
  fi

  # v2.0.0: Krzywa 1 jest jedyną krzywą użytkownika widoczną w UI i jej
  # źródłem prawdy jest konfiguracja aplikacji (/data/options.json). Stary plik
  # edytora nie może nadpisywać wartości zapisanych w zakładce Konfiguracja.
  # Legacy override pozostaje obsługiwany wyłącznie dla ukrytych krzywych 2-5.
  if [ "$idx" != "1" ] && [ -r "$CUSTOM_CURVE_EDITOR_FILE" ]; then
    local editor_row
    editor_row="$(jq -r --arg idx "$idx" '
      (.curves[$idx] // {}) as $c |
      if ($c|length)==0 then empty else
      [($c.name // ""), ($c.target_temp_c // ""), ($c.hysteresis_dense_c // ""),
       ($c.hysteresis_outer_c // ""), ($c.min_pwm_percent // ""),
       ($c.target_pwm_percent // ""), ($c.max_pwm_percent // ""), ($c.response_mode // "precise")] | @tsv end
    ' "$CUSTOM_CURVE_EDITOR_FILE" 2>/dev/null || true)"
    if [ -n "$editor_row" ]; then
      local e_name e_target e_hd e_ho e_min e_target_pwm e_max e_response
      IFS=$'\t' read -r e_name e_target e_hd e_ho e_min e_target_pwm e_max e_response <<< "$editor_row"
      [ -n "$e_name" ] && CUSTOM_CURVE_NAME="$(sanitize_curve_name "$e_name" "$CUSTOM_CURVE_NAME")"
      [ -n "$e_target" ] && CUSTOM_TARGET_C="$e_target"
      [ -n "$e_hd" ] && CUSTOM_HYST_DENSE_C="$e_hd"
      [ -n "$e_ho" ] && CUSTOM_HYST_OUTER_C="$e_ho"
      [ -n "$e_min" ] && CUSTOM_MIN_PWM_PCT="$e_min"
      [ -n "$e_target_pwm" ] && CUSTOM_TARGET_PWM_PCT="$e_target_pwm"
      [ -n "$e_max" ] && CUSTOM_MAX_PWM_PCT="$e_max"
      case "$e_response" in gentle|balanced|precise) CUSTOM_RESPONSE_MODE="$e_response" ;; esac
    fi
  fi

  curve_factory_defaults "$idx"
  num_in_range "$CUSTOM_TARGET_C" 46 65 || CUSTOM_TARGET_C="$FACTORY_TARGET_C"
  num_in_range "$CUSTOM_HYST_DENSE_C" 0.25 3.0 || CUSTOM_HYST_DENSE_C="$FACTORY_HYST_DENSE_C"
  num_in_range "$CUSTOM_HYST_OUTER_C" 0.25 5.0 || CUSTOM_HYST_OUTER_C="$FACTORY_HYST_OUTER_C"
  num_in_range "$CUSTOM_MIN_PWM_PCT" 20 70 || CUSTOM_MIN_PWM_PCT="$FACTORY_MIN_PWM_PCT"
  num_in_range "$CUSTOM_TARGET_PWM_PCT" 25 90 || CUSTOM_TARGET_PWM_PCT="$FACTORY_TARGET_PWM_PCT"
  num_in_range "$CUSTOM_MAX_PWM_PCT" 70 100 || CUSTOM_MAX_PWM_PCT="$FACTORY_MAX_PWM_PCT"
  if ! awk -v a="$CUSTOM_MIN_PWM_PCT" -v b="$CUSTOM_TARGET_PWM_PCT" -v c="$CUSTOM_MAX_PWM_PCT" 'BEGIN { exit !(a < b && b < c) }'; then
    CUSTOM_MIN_PWM_PCT="$FACTORY_MIN_PWM_PCT"; CUSTOM_TARGET_PWM_PCT="$FACTORY_TARGET_PWM_PCT"; CUSTOM_MAX_PWM_PCT="$FACTORY_MAX_PWM_PCT"
  fi
  case "$CUSTOM_RESPONSE_MODE" in gentle|balanced|precise) ;; *) CUSTOM_RESPONSE_MODE="$FACTORY_RESPONSE_MODE" ;; esac
  refresh_custom_profile_label
  generate_custom_arrays
}

refresh_all_custom_curve_metadata() {
  local saved="${CUSTOM_CURVE_INDEX:-1}" i
  for i in 1 2 3 4 5; do
    load_custom_curve "$i"
    CUSTOM_CURVE_LABELS[$i]="$CUSTOM_PROFILE_LABEL"
    CUSTOM_CURVE_SELECTOR_LABELS[$i]="$(curve_selector_label "$i" "$CUSTOM_CURVE_NAME" "$CUSTOM_TARGET_C")"
    CUSTOM_CURVE_TRIPS[$i]="$CUSTOM_TRIPS_CSV"
    CUSTOM_CURVE_PRETTIES[$i]="$CUSTOM_PRETTY"
  done
  load_custom_curve "$saved"
}

migrate_dynamic_config_sections() {
  [ -r "$OPTIONS_FILE" ] || return 0
  [ -e "$CONFIG_UI_MIGRATION_MARKER" ] && return 0
  local tmp="${OPTIONS_FILE}.sections242.$$"
  jq '
    def section_flag($old; $new; $fallback):
      if (((.sections // {}) | type) == "object" and ((.sections // {}) | has($old))) then .sections[$old]
      elif has($new) then .[$new]
      else $fallback end;
    .section_adaptive_advanced_enabled = section_flag("adaptive_advanced"; "section_adaptive_advanced_enabled"; (((.adaptive_pwm_deadband_c // 0.75) != 0.75) or ((.adaptive_pwm_interval_seconds // 10) != 10) or ((.adaptive_pwm_down_confirm_cycles // 2) != 2))) |
    .section_notifications_enabled = section_flag("notifications"; "section_notifications_enabled"; true) |
    .section_updates_enabled = section_flag("updates"; "section_updates_enabled"; true) |
    .section_telemetry_enabled = section_flag("telemetry"; "section_telemetry_enabled"; true) |
    .section_cpu_enabled = section_flag("cpu"; "section_cpu_enabled"; (((.config_cpu // {}) | to_entries | map((.value|tostring) != "auto" and (.value|tostring) != "") | any))) |
    .section_gpu_enabled = section_flag("gpu"; "section_gpu_enabled"; (((.config_gpu // {}) | to_entries | map((.value|tostring) != "auto" and (.value|tostring) != "") | any))) |
    .section_power_usb_enabled = section_flag("power_usb"; "section_power_usb_enabled"; (((.config_power_usb // {}) | to_entries | map((.value|tostring) != "auto" and (.value|tostring) != "") | any))) |
    .section_pcie_rp1_enabled = section_flag("pcie_rp1"; "section_pcie_rp1_enabled"; (((.config_pcie_rp1 // {}) | to_entries | map((.value|tostring) != "auto" and (.value|tostring) != "") | any))) |
    .section_boot_kernel_enabled = section_flag("boot_kernel"; "section_boot_kernel_enabled"; (((.config_boot_kernel // {}) | to_entries | map((.value|tostring) != "auto" and (.value|tostring) != "") | any))) |
    .section_hardware_enabled = section_flag("hardware"; "section_hardware_enabled"; (((.config_hardware // {}) | to_entries | map((.value|tostring) != "auto" and (.value|tostring) != "") | any))) |
    .section_uart_debug_enabled = section_flag("uart_debug"; "section_uart_debug_enabled"; (((.config_uart_debug // {}) | to_entries | map((.value|tostring) != "auto" and (.value|tostring) != "") | any))) |
    .section_video_enabled = section_flag("video"; "section_video_enabled"; (((.config_video // {}) | to_entries | map((.value|tostring) != "auto" and (.value|tostring) != "") | any))) |
    .section_device_tree_enabled = section_flag("device_tree"; "section_device_tree_enabled"; (((.config_device_tree // {}) | to_entries | map((.value|tostring) != "auto" and (.value|tostring) != "") | any))) |
    .section_compatibility_enabled = section_flag("compatibility"; "section_compatibility_enabled"; (((.config_compatibility // {}) | to_entries | map((.value|tostring) != "auto" and (.value|tostring) != "") | any))) |
    .section_custom_parameters_enabled = section_flag("custom_parameters"; "section_custom_parameters_enabled"; ((.config_custom_parameters // []) | length > 0)) |
    del(.sections)
  ' "$OPTIONS_FILE" > "$tmp" 2>/dev/null && mv "$tmp" "$OPTIONS_FILE" || rm -f "$tmp"
  : > "$CONFIG_UI_MIGRATION_MARKER"
  log "Konfiguracja 2.4.2: rozdzielono przełączniki sekcji i przeniesiono ich stan ze starego bloku sections."
}

load_options() {
  local row
  if [ -r "$OPTIONS_FILE" ]; then
    row="$(jq -r '[
      (.custom_target_temp_c // 50.0),(.custom_hysteresis_dense_c // 0.75),(.custom_hysteresis_outer_c // 1.0),
      (.custom_min_pwm_percent // 29),(.custom_target_pwm_percent // 55),(.custom_max_pwm_percent // 100),
      (.apply_custom_on_start // false),(.restart_policy // "ask"),(.pre_restart_config_check // true),
      (.restart_notice_on_start // true),(.post_update_restart_prompt // true),(.actionable_mobile_notifications // true),
      (.mobile_notify_service // "auto"),(.update_check_enabled // true),(.update_check_interval_hours // 6),
      (.update_notify // true),((.app_update_manifest_url // "") | if . == "" then "__EMPTY__" else . end),(.local_package_updates_enabled // true),
      (.local_package_scan_interval_minutes // 2),(.local_package_keep_processed // true),(.local_package_cleanup_enabled // true),(.local_package_processed_retention // 2),(.local_package_failed_retention // 2),(.native_restart_repair // true),
      (.multicore_telemetry_enabled // true),(.multicore_workers // "auto"),
      (.config_txt_manager.enabled // false),(.config_txt_manager.sync_interval_seconds // 5),(.config_txt_manager.advanced_mode // false)
    ] | @tsv' "$OPTIONS_FILE" 2>/dev/null || true)"
    if [ -n "$row" ]; then
      IFS=$'\t' read -r CURVE1_TARGET_C CURVE1_HYST_DENSE_C CURVE1_HYST_OUTER_C CURVE1_MIN_PWM_PCT CURVE1_TARGET_PWM_PCT CURVE1_MAX_PWM_PCT APPLY_CUSTOM_ON_START RESTART_POLICY PRE_RESTART_CONFIG_CHECK RESTART_NOTICE_ON_START POST_UPDATE_RESTART_PROMPT ACTIONABLE_MOBILE_NOTIFICATIONS MOBILE_NOTIFY_SERVICE UPDATE_CHECK_ENABLED UPDATE_CHECK_INTERVAL_HOURS UPDATE_NOTIFY APP_UPDATE_MANIFEST_URL LOCAL_PACKAGE_UPDATES_ENABLED LOCAL_PACKAGE_SCAN_INTERVAL_MINUTES LOCAL_PACKAGE_KEEP_PROCESSED LOCAL_PACKAGE_CLEANUP_ENABLED LOCAL_PACKAGE_PROCESSED_RETENTION LOCAL_PACKAGE_FAILED_RETENTION NATIVE_RESTART_REPAIR MULTICORE_TELEMETRY_ENABLED MULTICORE_WORKERS_CONFIG CONFIG_TXT_OPTIONS_ENABLED CONFIG_TXT_OPTIONS_SYNC_INTERVAL CONFIG_TXT_OPTIONS_ADVANCED <<< "$row"
      [ "$APP_UPDATE_MANIFEST_URL" = "__EMPTY__" ] && APP_UPDATE_MANIFEST_URL="$DEFAULT_APP_UPDATE_MANIFEST_URL"
    fi
    CURVE1_NAME="$(jq -r '(.custom_curve_1_name // "Zbalansowana") | tostring' "$OPTIONS_FILE" 2>/dev/null || echo 'Zbalansowana')"
    COOLING_CONTROL_MODE="$(jq -r '.cooling_control_mode // "automatic"' "$OPTIONS_FILE" 2>/dev/null || echo automatic)"
    COOLING_AUTO_STYLE="$(jq -r '.cooling_auto_style // "balanced"' "$OPTIONS_FILE" 2>/dev/null || echo balanced)"
    HYBRID_CORRECTION_LIMIT_PCT="$(jq -r '.hybrid_correction_limit_percent // 10' "$OPTIONS_FILE" 2>/dev/null || echo 10)"
    MANUAL_HYSTERESIS_C="$(jq -r '.manual_hysteresis_c // 1.0' "$OPTIONS_FILE" 2>/dev/null || echo 1.0)"
    CUSTOM_FAN_CURVES_JSON="$(jq -c '.custom_fan_curves_2_5 // []' "$OPTIONS_FILE" 2>/dev/null || echo '[]')"
    APPLY_CUSTOM_CURVE_ON_START="$(jq -r '.apply_custom_curve_on_start // "off"' "$OPTIONS_FILE" 2>/dev/null || echo off)"
    ADAPTIVE_PWM_ENABLED="$(jq -r '.adaptive_pwm_enabled // true' "$OPTIONS_FILE" 2>/dev/null || echo true)"
    ADAPTIVE_PWM_DEADBAND_C="$(jq -r '.adaptive_pwm_deadband_c // 0.75' "$OPTIONS_FILE" 2>/dev/null || echo 0.75)"
    ADAPTIVE_PWM_INTERVAL_SECONDS="$(jq -r '.adaptive_pwm_interval_seconds // 10' "$OPTIONS_FILE" 2>/dev/null || echo 10)"
    ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES="$(jq -r '.adaptive_pwm_down_confirm_cycles // 2' "$OPTIONS_FILE" 2>/dev/null || echo 2)"
    AI_COOLING_SECTION_ENABLED="$(jq -r '.section_ai_cooling_enabled // false' "$OPTIONS_FILE" 2>/dev/null || echo false)"
    AI_COOLING_MODE="$(jq -r '.ai_cooling_mode // "learning"' "$OPTIONS_FILE" 2>/dev/null || echo learning)"
    CONFIG_GPU_PROFILE="$(jq -r '.config_gpu_profile // "factory"' "$OPTIONS_FILE" 2>/dev/null || echo factory)"
    AI_COOLING_ASSIST_LIMIT_PCT="$(jq -r '.ai_cooling_assist_limit_percent // 5' "$OPTIONS_FILE" 2>/dev/null || echo 5)"
    AI_COOLING_MIN_SAMPLES="$(jq -r '.ai_cooling_min_samples // 30' "$OPTIONS_FILE" 2>/dev/null || echo 30)"
    SECTION_ADAPTIVE_ADVANCED_ENABLED="$(jq -r 'if has("section_adaptive_advanced_enabled") then .section_adaptive_advanced_enabled elif ((.sections // {}) | has("adaptive_advanced")) then .sections.adaptive_advanced else false end' "$OPTIONS_FILE" 2>/dev/null || echo false)"
    SECTION_NOTIFICATIONS_ENABLED="$(jq -r 'if has("section_notifications_enabled") then .section_notifications_enabled elif ((.sections // {}) | has("notifications")) then .sections.notifications else true end' "$OPTIONS_FILE" 2>/dev/null || echo true)"
    SECTION_UPDATES_ENABLED="$(jq -r 'if has("section_updates_enabled") then .section_updates_enabled elif ((.sections // {}) | has("updates")) then .sections.updates else true end' "$OPTIONS_FILE" 2>/dev/null || echo true)"
    SECTION_TELEMETRY_ENABLED="$(jq -r 'if has("section_telemetry_enabled") then .section_telemetry_enabled elif ((.sections // {}) | has("telemetry")) then .sections.telemetry else true end' "$OPTIONS_FILE" 2>/dev/null || echo true)"
  fi

  CURVE1_NAME="$(sanitize_curve_name "$CURVE1_NAME" "Zbalansowana")"
  num_in_range "$CURVE1_TARGET_C" 46 65 || CURVE1_TARGET_C="50.0"
  num_in_range "$CURVE1_HYST_DENSE_C" 0.25 3.0 || CURVE1_HYST_DENSE_C="0.75"
  num_in_range "$CURVE1_HYST_OUTER_C" 0.25 5.0 || CURVE1_HYST_OUTER_C="1.0"
  num_in_range "$CURVE1_MIN_PWM_PCT" 20 70 || CURVE1_MIN_PWM_PCT="29"
  num_in_range "$CURVE1_TARGET_PWM_PCT" 25 90 || CURVE1_TARGET_PWM_PCT="55"
  num_in_range "$CURVE1_MAX_PWM_PCT" 70 100 || CURVE1_MAX_PWM_PCT="100"
  case "$ADAPTIVE_PWM_ENABLED" in true|false) ;; *) ADAPTIVE_PWM_ENABLED="true" ;; esac
  num_in_range "$ADAPTIVE_PWM_DEADBAND_C" 0.10 1.50 || ADAPTIVE_PWM_DEADBAND_C="0.75"
  # v2.1.8: protect the controller from Raspberry Pi temperature quantization.
  # Existing installations with a narrower historical value are migrated at runtime.
  if awk -v d="$ADAPTIVE_PWM_DEADBAND_C" 'BEGIN{exit !(d < 0.75)}'; then ADAPTIVE_PWM_DEADBAND_C="0.75"; fi
  case "$ADAPTIVE_PWM_INTERVAL_SECONDS" in ''|*[!0-9]*) ADAPTIVE_PWM_INTERVAL_SECONDS=10 ;; esac
  [ "$ADAPTIVE_PWM_INTERVAL_SECONDS" -ge 5 ] 2>/dev/null || ADAPTIVE_PWM_INTERVAL_SECONDS=5
  [ "$ADAPTIVE_PWM_INTERVAL_SECONDS" -le 60 ] 2>/dev/null || ADAPTIVE_PWM_INTERVAL_SECONDS=60
  case "$ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES" in ''|*[!0-9]*) ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES=2 ;; esac
  [ "$ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES" -ge 1 ] 2>/dev/null || ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES=1
  [ "$ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES" -le 6 ] 2>/dev/null || ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES=6
  case "$AI_COOLING_SECTION_ENABLED" in true|false) ;; *) AI_COOLING_SECTION_ENABLED="false" ;; esac
  case "$AI_COOLING_MODE" in learning|assist) ;; *) AI_COOLING_MODE="learning" ;; esac
  case "$AI_COOLING_ASSIST_LIMIT_PCT" in ''|*[!0-9]*) AI_COOLING_ASSIST_LIMIT_PCT=5 ;; esac
  [ "$AI_COOLING_ASSIST_LIMIT_PCT" -ge 1 ] 2>/dev/null || AI_COOLING_ASSIST_LIMIT_PCT=1
  [ "$AI_COOLING_ASSIST_LIMIT_PCT" -le 10 ] 2>/dev/null || AI_COOLING_ASSIST_LIMIT_PCT=10
  case "$AI_COOLING_MIN_SAMPLES" in ''|*[!0-9]*) AI_COOLING_MIN_SAMPLES=30 ;; esac
  [ "$AI_COOLING_MIN_SAMPLES" -ge 10 ] 2>/dev/null || AI_COOLING_MIN_SAMPLES=10
  [ "$AI_COOLING_MIN_SAMPLES" -le 300 ] 2>/dev/null || AI_COOLING_MIN_SAMPLES=300
  if ! awk -v a="$CURVE1_MIN_PWM_PCT" -v b="$CURVE1_TARGET_PWM_PCT" -v c="$CURVE1_MAX_PWM_PCT" 'BEGIN { exit !(a < b && b < c) }'; then
    CURVE1_MIN_PWM_PCT=29; CURVE1_TARGET_PWM_PCT=55; CURVE1_MAX_PWM_PCT=100
  fi
  case "$APPLY_CUSTOM_CURVE_ON_START" in off|1|2|3|4|5) ;; *) APPLY_CUSTOM_CURVE_ON_START="off" ;; esac
  case "$RESTART_POLICY" in ask|notify_only) ;; *) RESTART_POLICY="ask" ;; esac
  case "$PRE_RESTART_CONFIG_CHECK" in true|false) ;; *) PRE_RESTART_CONFIG_CHECK="true" ;; esac
  case "$RESTART_NOTICE_ON_START" in true|false) ;; *) RESTART_NOTICE_ON_START="true" ;; esac
  case "$POST_UPDATE_RESTART_PROMPT" in true|false) ;; *) POST_UPDATE_RESTART_PROMPT="true" ;; esac
  case "$ACTIONABLE_MOBILE_NOTIFICATIONS" in true|false) ;; *) ACTIONABLE_MOBILE_NOTIFICATIONS="true" ;; esac
  case "$UPDATE_CHECK_ENABLED" in true|false) ;; *) UPDATE_CHECK_ENABLED="true" ;; esac
  case "$UPDATE_NOTIFY" in true|false) ;; *) UPDATE_NOTIFY="true" ;; esac
  num_in_range "$UPDATE_CHECK_INTERVAL_HOURS" 1 24 || UPDATE_CHECK_INTERVAL_HOURS="6"
  [ -n "$MOBILE_NOTIFY_SERVICE" ] || MOBILE_NOTIFY_SERVICE="auto"
  case "$APP_UPDATE_MANIFEST_URL" in http://*|https://*) ;; *) APP_UPDATE_MANIFEST_URL="$DEFAULT_APP_UPDATE_MANIFEST_URL" ;; esac
  case "$LOCAL_PACKAGE_UPDATES_ENABLED" in true|false) ;; *) LOCAL_PACKAGE_UPDATES_ENABLED="true" ;; esac
  num_in_range "$LOCAL_PACKAGE_SCAN_INTERVAL_MINUTES" 1 60 || LOCAL_PACKAGE_SCAN_INTERVAL_MINUTES="2"
  case "$LOCAL_PACKAGE_KEEP_PROCESSED" in true|false) ;; *) LOCAL_PACKAGE_KEEP_PROCESSED="true" ;; esac
  case "$LOCAL_PACKAGE_CLEANUP_ENABLED" in true|false) ;; *) LOCAL_PACKAGE_CLEANUP_ENABLED="true" ;; esac
  num_in_range "$LOCAL_PACKAGE_PROCESSED_RETENTION" 0 20 || LOCAL_PACKAGE_PROCESSED_RETENTION="2"
  num_in_range "$LOCAL_PACKAGE_FAILED_RETENTION" 0 20 || LOCAL_PACKAGE_FAILED_RETENTION="2"
  case "$NATIVE_RESTART_REPAIR" in true|false) ;; *) NATIVE_RESTART_REPAIR="true" ;; esac
  case "$MULTICORE_TELEMETRY_ENABLED" in true|false) ;; *) MULTICORE_TELEMETRY_ENABLED="true" ;; esac
  case "$MULTICORE_WORKERS_CONFIG" in auto|1|2|3|4) ;; *) MULTICORE_WORKERS_CONFIG="auto" ;; esac
  resolve_multicore_workers
  case "$CONFIG_TXT_OPTIONS_ENABLED" in true|false) ;; *) CONFIG_TXT_OPTIONS_ENABLED="false" ;; esac
  num_in_range "$CONFIG_TXT_OPTIONS_SYNC_INTERVAL" 2 60 || CONFIG_TXT_OPTIONS_SYNC_INTERVAL="5"
  case "$CONFIG_TXT_OPTIONS_ADVANCED" in true|false) ;; *) CONFIG_TXT_OPTIONS_ADVANCED="false" ;; esac
  case "$CONFIG_GPU_PROFILE" in factory|eco|balanced|performance|experimental|advanced) ;; *) CONFIG_GPU_PROFILE="factory" ;; esac

  case "$COOLING_CONTROL_MODE" in automatic|hybrid|manual) ;; *) COOLING_CONTROL_MODE="automatic" ;; esac
  case "$COOLING_AUTO_STYLE" in quiet|balanced|performance) ;; *) COOLING_AUTO_STYLE="balanced" ;; esac
  case "$HYBRID_CORRECTION_LIMIT_PCT" in ''|*[!0-9]*) HYBRID_CORRECTION_LIMIT_PCT=10 ;; esac
  [ "$HYBRID_CORRECTION_LIMIT_PCT" -ge 0 ] 2>/dev/null || HYBRID_CORRECTION_LIMIT_PCT=0
  [ "$HYBRID_CORRECTION_LIMIT_PCT" -le 25 ] 2>/dev/null || HYBRID_CORRECTION_LIMIT_PCT=25
  num_in_range "$MANUAL_HYSTERESIS_C" 0.25 5.0 || MANUAL_HYSTERESIS_C="1.0"

  case "$SECTION_ADAPTIVE_ADVANCED_ENABLED" in true|false) ;; *) SECTION_ADAPTIVE_ADVANCED_ENABLED="false" ;; esac
  case "$AI_COOLING_SECTION_ENABLED" in true|false) ;; *) AI_COOLING_SECTION_ENABLED="false" ;; esac
  case "$SECTION_NOTIFICATIONS_ENABLED" in true|false) ;; *) SECTION_NOTIFICATIONS_ENABLED="true" ;; esac
  case "$SECTION_UPDATES_ENABLED" in true|false) ;; *) SECTION_UPDATES_ENABLED="true" ;; esac
  case "$SECTION_TELEMETRY_ENABLED" in true|false) ;; *) SECTION_TELEMETRY_ENABLED="true" ;; esac
  if [ "$SECTION_ADAPTIVE_ADVANCED_ENABLED" != "true" ]; then ADAPTIVE_PWM_DEADBAND_C="0.75"; ADAPTIVE_PWM_INTERVAL_SECONDS="10"; ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES="2"; fi
  if [ "$SECTION_NOTIFICATIONS_ENABLED" != "true" ]; then ACTIONABLE_MOBILE_NOTIFICATIONS="false"; MOBILE_NOTIFY_SERVICE="auto"; fi
  if [ "$SECTION_UPDATES_ENABLED" != "true" ]; then UPDATE_CHECK_ENABLED="false"; UPDATE_NOTIFY="false"; LOCAL_PACKAGE_UPDATES_ENABLED="false"; fi
  if [ "$SECTION_TELEMETRY_ENABLED" != "true" ]; then MULTICORE_TELEMETRY_ENABLED="false"; MULTICORE_WORKERS_CONFIG="1"; resolve_multicore_workers; fi

  # v2.4.1: mode is authoritative. Dynamic sections gate advanced behavior; disabled sections stay collapsed in the Ingress UI.
  case "$COOLING_CONTROL_MODE" in
    automatic)
      ADAPTIVE_PWM_ENABLED="true"
      CURVE1_HYST_DENSE_C="0.75"; CURVE1_HYST_OUTER_C="1.0"
      case "$COOLING_AUTO_STYLE" in
        quiet) CURVE1_MIN_PWM_PCT="20"; CURVE1_TARGET_PWM_PCT="38"; CURVE1_MAX_PWM_PCT="100" ;;
        performance) CURVE1_MIN_PWM_PCT="25"; CURVE1_TARGET_PWM_PCT="50"; CURVE1_MAX_PWM_PCT="100" ;;
        *) CURVE1_MIN_PWM_PCT="20"; CURVE1_TARGET_PWM_PCT="43"; CURVE1_MAX_PWM_PCT="100" ;;
      esac
      ;;
    hybrid)
      ADAPTIVE_PWM_ENABLED="true"
      ;;
    manual)
      ADAPTIVE_PWM_ENABLED="false"
      CURVE1_HYST_DENSE_C="$MANUAL_HYSTERESIS_C"; CURVE1_HYST_OUTER_C="$MANUAL_HYSTERESIS_C"
      ;;
  esac
  # AI Preview never bypasses the classic regulator. Assist is enabled only in
  # Automatic mode; Hybrid may still collect learning samples; Manual remains strict.
  AI_COOLING_EFFECTIVE_MODE="disabled"
  if [ "$AI_COOLING_SECTION_ENABLED" = "true" ]; then
    case "$COOLING_CONTROL_MODE" in
      automatic) AI_COOLING_EFFECTIVE_MODE="$AI_COOLING_MODE" ;;
      hybrid) AI_COOLING_EFFECTIVE_MODE="learning" ;;
      *) AI_COOLING_EFFECTIVE_MODE="disabled" ;;
    esac
  fi

  CUSTOM_CURVE_INDEX="1"
  refresh_all_custom_curve_metadata
}

custom_curve_config_payload() {
  jq -cn \
    --arg name "$CURVE1_NAME" \
    --argjson target "$CURVE1_TARGET_C" \
    --argjson hd "$CURVE1_HYST_DENSE_C" \
    --argjson ho "$CURVE1_HYST_OUTER_C" \
    --argjson pmin "$CURVE1_MIN_PWM_PCT" \
    --argjson ptgt "$CURVE1_TARGET_PWM_PCT" \
    --argjson pmax "$CURVE1_MAX_PWM_PCT" \
    --arg control_mode "$COOLING_CONTROL_MODE" \
    --arg auto_style "$COOLING_AUTO_STYLE" \
    --argjson hybrid_limit "$HYBRID_CORRECTION_LIMIT_PCT" \
    --argjson generator_revision 5 \
    '{name:$name,target_temp_c:$target,hysteresis_dense_c:$hd,hysteresis_outer_c:$ho,min_pwm_percent:$pmin,target_pwm_percent:$ptgt,max_pwm_percent:$pmax,control_mode:$control_mode,auto_style:$auto_style,hybrid_limit_percent:$hybrid_limit,generator_revision:$generator_revision}'
}

detect_custom_curve_config_change() {
  local payload previous factory
  payload="$(custom_curve_config_payload)" || return 0
  CUSTOM_CURVE_CONFIG_SIGNATURE="$(printf '%s' "$payload" | sha256sum | awk '{print $1}')"
  previous="$(cat "$CUSTOM_CURVE_CONFIG_SIGNATURE_FILE" 2>/dev/null || true)"
  CUSTOM_CURVE_CONFIG_CHANGED="false"

  if [ -n "$previous" ]; then
    [ "$previous" = "$CUSTOM_CURVE_CONFIG_SIGNATURE" ] || CUSTOM_CURVE_CONFIG_CHANGED="true"
    return 0
  fi

  # Migracja z <=1.9.32: jeżeli użytkownik ma ustawienia inne niż fabryczne,
  # uznajemy je za świadomie zapisane i przygotowujemy je do zastosowania.
  factory='{"name":"Zbalansowana","target_temp_c":50,"hysteresis_dense_c":0.75,"hysteresis_outer_c":1,"min_pwm_percent":29,"target_pwm_percent":55,"max_pwm_percent":100}'
  if [ "$(jq -cS . <<<"$payload" 2>/dev/null)" != "$(jq -cS . <<<"$factory" 2>/dev/null)" ]; then
    CUSTOM_CURVE_CONFIG_CHANGED="true"
  else
    mkdir -p "$(dirname "$CUSTOM_CURVE_CONFIG_SIGNATURE_FILE")" 2>/dev/null || true
    printf '%s\n' "$CUSTOM_CURVE_CONFIG_SIGNATURE" > "$CUSTOM_CURVE_CONFIG_SIGNATURE_FILE" 2>/dev/null || true
  fi
}

commit_custom_curve_config_signature() {
  [ -n "$CUSTOM_CURVE_CONFIG_SIGNATURE" ] || return 0
  printf '%s\n' "$CUSTOM_CURVE_CONFIG_SIGNATURE" > "$CUSTOM_CURVE_CONFIG_SIGNATURE_FILE" 2>/dev/null || true
}

apply_ai_grid_profile_arrays() {
  [ "$CUSTOM_CURVE_INDEX" = "1" ] || return 1
  [ -s "$AI_GRID_PROFILE_FILE" ] || return 1
  [ -x "$AI_COOLING_SCRIPT" ] || return 1
  local rows count i t h raw pretty
  rows="$(python3 "$AI_COOLING_SCRIPT" render-grid \
    --profile "$AI_GRID_PROFILE_FILE" --target "$CUSTOM_TARGET_C" \
    --hd "$CUSTOM_HYST_DENSE_C" --ho "$CUSTOM_HYST_OUTER_C" \
    --pmin "$CUSTOM_MIN_PWM_PCT" --ptgt "$CUSTOM_TARGET_PWM_PCT" --pmax "$CUSTOM_MAX_PWM_PCT" 2>/dev/null || true)"
  count="$(printf '%s\n' "$rows" | awk -F'|' 'NF==5{n++} END{print n+0}')"
  [ "$count" = "15" ] || return 1
  CUSTOM_T=(); CUSTOM_H=(); CUSTOM_PWM=(); CUSTOM_TRIPS_CSV=""; CUSTOM_PRETTY=""
  while IFS='|' read -r i t h raw pretty; do
    [ -n "$i" ] || continue
    CUSTOM_T[$i]="$t"; CUSTOM_H[$i]="$h"; CUSTOM_PWM[$i]="$raw"
    [ -n "$CUSTOM_TRIPS_CSV" ] && CUSTOM_TRIPS_CSV+=","; CUSTOM_TRIPS_CSV+="$t"
    [ -n "$CUSTOM_PRETTY" ] && CUSTOM_PRETTY+=" / "; CUSTOM_PRETTY+="$pretty"
  done <<< "$rows"
  return 0
}

generate_custom_arrays() {
  local i t h raw pretty
  CUSTOM_T=(); CUSTOM_H=(); CUSTOM_PWM=()
  CUSTOM_TRIPS_CSV=""; CUSTOM_PRETTY=""
  while IFS='|' read -r i t h raw pretty; do
    [ -n "$i" ] || continue
    CUSTOM_T[$i]="$t"; CUSTOM_H[$i]="$h"; CUSTOM_PWM[$i]="$raw"
    [ -n "$CUSTOM_TRIPS_CSV" ] && CUSTOM_TRIPS_CSV+=","; CUSTOM_TRIPS_CSV+="$t"
    [ -n "$CUSTOM_PRETTY" ] && CUSTOM_PRETTY+=" / "; CUSTOM_PRETTY+="$pretty"
  done < <(awk -v target="$CUSTOM_TARGET_C" -v hd="$CUSTOM_HYST_DENSE_C" -v ho="$CUSTOM_HYST_OUTER_C" -v pmin="$CUSTOM_MIN_PWM_PCT" -v ptgt="$CUSTOM_TARGET_PWM_PCT" -v pmax="$CUSTOM_MAX_PWM_PCT" -v mode="$CUSTOM_RESPONSE_MODE" 'BEGIN {
    # v1.9.23 Adaptive Setpoint Density: all generator modes concentrate work points
    # around the target. Precise is the default and places seven neighbouring levels
    # inside +/-1 C, while retaining outer reserve points for large thermal excursions.
    if(mode=="gentle") {
      split("-8 -6 -4 -3 -2 -1.5 -0.75 0 0.75 1.5 2 3 4 6 8",off," "); dense=3.0;
    } else if(mode=="balanced") {
      split("-7 -5 -3 -2 -1.25 -0.75 -0.5 0 0.5 0.75 1.25 2 3 5 7",off," "); dense=2.0;
    } else {
      # v2.0.3 Balanced Setpoint geometry: the curve is generated entirely as
      # offsets from the configured setpoint. Resolution remains dense around 0C,
      # while the upper reserve is deliberately spread out to +10C so +4C no
      # longer maps to maximum fan output.
      split("-5 -3 -2 -1.5 -1 -0.5 -0.25 0 0.5 1 2 3 4 6 10",off," "); dense=1.5;
    }
    # Below the target the curve stays conservative. Above the target it rises
    # progressively: +4C uses only 36% of the target->maximum PWM reserve,
    # +6C uses 58%, and 100% reserve is reached at +10C.
    split("0 0 0 5 15 35 65 100",pre," ");
    split("5 10 18 27 36 58 100",post," ");
    mn=int(pmin*255/100+0.5); tg=int(ptgt*255/100+0.5); mx=int(pmax*255/100+0.5);
    for(i=1;i<=15;i++){
      t=int((target+off[i])*1000+0.5);
      h=int(((off[i] >= -dense && off[i] <= dense)?hd:ho)*1000+0.5);
      if(i<=8) frac=pre[i]/100.0; else frac=post[i-8]/100.0;
      if(i<=8) r=int(mn+(tg-mn)*frac+0.5); else r=int(tg+(mx-tg)*frac+0.5);
      if(r<0)r=0;if(r>255)r=255;
      printf "%d|%d|%d|%d|%.2f\n",i,t,h,r,t/1000;
    }
  }')
  # custom1 keeps App Configuration as the PWM/setpoint source of truth. An
  # explicitly accepted AI grid may only redistribute temperature points; PWM
  # values are re-interpolated from the same configured curve parameters.
  if [ "$CUSTOM_CURVE_INDEX" = "1" ]; then
    apply_ai_grid_profile_arrays || true
  else
    # Legacy point overrides are retained only for hidden compatibility curves 2-5.
    apply_custom_curve_point_overrides
  fi
  CUSTOM_PRETTY+=" °C"
}

curve_editor_mode() {
  local idx="${1:-1}"
  if [ -r "$CUSTOM_CURVE_EDITOR_FILE" ] && jq -e --arg idx "$idx" '((.curves[$idx].points // []) | length) == 15' "$CUSTOM_CURVE_EDITOR_FILE" >/dev/null 2>&1; then
    printf 'points\n'
  else
    printf 'generated\n'
  fi
}

apply_custom_curve_point_overrides() {
  [ -r "$CUSTOM_CURVE_EDITOR_FILE" ] || return 0
  local points count i row tc hc pc tm hm raw prev_tm=-999999 prev_raw=-1 valid=true
  points="$(jq -c --arg idx "$CUSTOM_CURVE_INDEX" '.curves[$idx].points // []' "$CUSTOM_CURVE_EDITOR_FILE" 2>/dev/null || echo '[]')"
  count="$(jq -r 'length' <<<"$points" 2>/dev/null || echo 0)"
  [ "$count" = "15" ] || return 0

  local -a nt nh np
  local trips="" pretty=""
  for i in $(seq 1 15); do
    row="$(jq -r --argjson p "$((i-1))" '.[$p] | [(.temp_c // ""),(.hysteresis_c // ""),(.pwm_percent // "")] | @tsv' <<<"$points" 2>/dev/null || true)"
    IFS=$'\t' read -r tc hc pc <<< "$row"
    if ! num_in_range "$tc" 35 80 || ! num_in_range "$hc" 0.25 5.0 || ! num_in_range "$pc" 0 100; then valid=false; break; fi
    tm="$(awk -v v="$tc" 'BEGIN{printf "%d",v*1000+0.5}')"
    hm="$(awk -v v="$hc" 'BEGIN{printf "%d",v*1000+0.5}')"
    raw="$(awk -v v="$pc" 'BEGIN{printf "%d",v*255/100+0.5}')"
    if [ "$tm" -le "$prev_tm" ] 2>/dev/null || [ "$raw" -lt "$prev_raw" ] 2>/dev/null; then valid=false; break; fi
    prev_tm="$tm"; prev_raw="$raw"
    nt[$i]="$tm"; nh[$i]="$hm"; np[$i]="$raw"
    [ -n "$trips" ] && trips+=","; trips+="$tm"
    [ -n "$pretty" ] && pretty+=" / "; pretty+="$(awk -v v="$tm" 'BEGIN{printf "%.1f",v/1000}')"
  done
  if [ "$valid" != "true" ]; then
    log "Curve Editor: odrzucono nieprawidłowy zestaw punktów dla krzywej ${CUSTOM_CURVE_INDEX}; używam generatora parametrów."
    return 0
  fi
  for i in $(seq 1 15); do CUSTOM_T[$i]="${nt[$i]}"; CUSTOM_H[$i]="${nh[$i]}"; CUSTOM_PWM[$i]="${np[$i]}"; done
  CUSTOM_TRIPS_CSV="$trips"
  CUSTOM_PRETTY="${pretty} °C"
}

curve_points_json_current() {
  local points='[]' i t h p
  for i in $(seq 1 15); do
    t="$(awk -v v="${CUSTOM_T[$i]}" 'BEGIN{printf "%.2f",v/1000}')"
    h="$(awk -v v="${CUSTOM_H[$i]}" 'BEGIN{printf "%.2f",v/1000}')"
    p="$(awk -v v="${CUSTOM_PWM[$i]}" 'BEGIN{printf "%.1f",v*100/255}')"
    points="$(jq -c --argjson t "$t" --argjson h "$h" --argjson p "$p" '. + [{temp_c:$t,hysteresis_c:$h,pwm_percent:$p}]' <<<"$points")"
  done
  printf '%s\n' "$points"
}

curve_editor_write_json() {
  local json="$1" tmp="${CUSTOM_CURVE_EDITOR_FILE}.tmp"
  printf '%s\n' "$json" > "$tmp" || return 1
  jq -e . "$tmp" >/dev/null 2>&1 || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$CUSTOM_CURVE_EDITOR_FILE"
}

set_custom_curve_template() {
  local idx="$1" name="$2" target="$3" hd="$4" ho="$5" pmin="$6" ptgt="$7" pmax="$8" response="${9:-precise}" base updated
  case "$idx" in 1|2|3|4|5) ;; *) log "Curve Editor: nieprawidłowy numer krzywej."; return 1 ;; esac
  curve_factory_defaults "$idx"
  name="$(sanitize_curve_name "$name" "$FACTORY_CURVE_NAME")"
  num_in_range "$target" 46 65 || { log "Curve Editor: target_temp_c poza zakresem 46–65°C."; return 1; }
  num_in_range "$hd" 0.25 3.0 || { log "Curve Editor: hyst_dense poza zakresem."; return 1; }
  num_in_range "$ho" 0.25 5.0 || { log "Curve Editor: hyst_outer poza zakresem."; return 1; }
  num_in_range "$pmin" 20 70 || return 1
  num_in_range "$ptgt" 25 90 || return 1
  num_in_range "$pmax" 70 100 || return 1
  case "$response" in gentle|balanced|precise) ;; *) response="precise" ;; esac
  awk -v a="$pmin" -v b="$ptgt" -v c="$pmax" 'BEGIN { exit !(a < b && b < c) }' || { log "Curve Editor: wymagane min PWM < target PWM < max PWM."; return 1; }
  base='{}'; [ -r "$CUSTOM_CURVE_EDITOR_FILE" ] && base="$(cat "$CUSTOM_CURVE_EDITOR_FILE" 2>/dev/null || echo '{}')"
  updated="$(jq -c --arg idx "$idx" --arg name "$name" --argjson target "$target" --argjson hd "$hd" --argjson ho "$ho" --argjson pmin "$pmin" --argjson ptgt "$ptgt" --argjson pmax "$pmax" --arg response "$response" '
    .schema=3 | .curves=(.curves // {}) | .curves[$idx]=((.curves[$idx] // {}) + {name:$name,target_temp_c:$target,hysteresis_dense_c:$hd,hysteresis_outer_c:$ho,min_pwm_percent:$pmin,target_pwm_percent:$ptgt,max_pwm_percent:$pmax,response_mode:$response}) | del(.curves[$idx].points)' <<<"$base" 2>/dev/null)" || return 1
  curve_editor_write_json "$updated" || return 1
  load_custom_curve "$idx"
  log "Curve Editor: zapisano generator krzywej ${idx} (${CUSTOM_PROFILE_LABEL})."
  ha_sync_profile_options || true
  ha_publish_curve_editor_state || true
}

set_custom_curve_point() {
  local idx="$1" point="$2" temp="$3" hyst="$4" pwm="$5" base points pos tm raw prev_tm next_tm prev_raw next_raw updated
  case "$idx" in 1|2|3|4|5) ;; *) return 1 ;; esac
  case "$point" in 1|2|3|4|5|6|7|8|9|10|11|12|13|14|15) ;; *) return 1 ;; esac
  num_in_range "$temp" 35 80 || { log "Curve Editor: temperatura punktu poza zakresem 35–80°C."; return 1; }
  num_in_range "$hyst" 0.25 5.0 || return 1
  num_in_range "$pwm" 0 100 || return 1
  load_custom_curve "$idx"
  points="$(curve_points_json_current)"
  pos=$((point-1))
  tm="$(awk -v v="$temp" 'BEGIN{printf "%d",v*1000+0.5}')"
  raw="$(awk -v v="$pwm" 'BEGIN{printf "%d",v*255/100+0.5}')"
  if [ "$point" -gt 1 ]; then prev_tm="${CUSTOM_T[$((point-1))]}"; prev_raw="${CUSTOM_PWM[$((point-1))]}"; [ "$tm" -gt "$prev_tm" ] || { log "Curve Editor: temperatura musi być większa od poprzedniego punktu."; return 1; }; [ "$raw" -ge "$prev_raw" ] || { log "Curve Editor: PWM nie może maleć względem poprzedniego punktu."; return 1; }; fi
  if [ "$point" -lt 15 ]; then next_tm="${CUSTOM_T[$((point+1))]}"; next_raw="${CUSTOM_PWM[$((point+1))]}"; [ "$tm" -lt "$next_tm" ] || { log "Curve Editor: temperatura musi być mniejsza od następnego punktu."; return 1; }; [ "$raw" -le "$next_raw" ] || { log "Curve Editor: PWM nie może przekraczać następnego punktu."; return 1; }; fi
  points="$(jq -c --argjson p "$pos" --argjson t "$temp" --argjson h "$hyst" --argjson w "$pwm" '.[$p]={temp_c:$t,hysteresis_c:$h,pwm_percent:$w}' <<<"$points")"
  base='{}'; [ -r "$CUSTOM_CURVE_EDITOR_FILE" ] && base="$(cat "$CUSTOM_CURVE_EDITOR_FILE" 2>/dev/null || echo '{}')"
  updated="$(jq -c --arg idx "$idx" --argjson pts "$points" '.schema=3 | .curves=(.curves // {}) | .curves[$idx]=(.curves[$idx] // {}) | .curves[$idx].points=$pts' <<<"$base" 2>/dev/null)" || return 1
  curve_editor_write_json "$updated" || return 1
  load_custom_curve "$idx"
  log "Curve Editor: zapisano punkt ${point}/15 krzywej ${idx}: ${temp}°C, hyst=${hyst}°C, PWM=${pwm}%."
  ha_publish_curve_editor_state || true
}

reset_custom_curve_editor_override() {
  # Backward-compatible command: remove editor override and return to Supervisor app options.
  local idx="$1" base updated
  case "$idx" in 1|2|3|4|5) ;; *) return 1 ;; esac
  [ -r "$CUSTOM_CURVE_EDITOR_FILE" ] || { ha_publish_curve_editor_state || true; return 0; }
  base="$(cat "$CUSTOM_CURVE_EDITOR_FILE" 2>/dev/null || echo '{}')"
  updated="$(jq -c --arg idx "$idx" 'del(.curves[$idx])' <<<"$base" 2>/dev/null)" || return 1
  curve_editor_write_json "$updated" || return 1
  load_options
  load_custom_curve "$idx"
  log "Curve Editor: przywrócono konfigurację krzywej ${idx} z ustawień aplikacji."
  ha_sync_profile_options || true
  ha_publish_curve_editor_state || true
}

reset_custom_curve_factory() {
  local idx="$1" base updated
  case "$idx" in 1|2|3|4|5) ;; *) return 1 ;; esac
  curve_factory_defaults "$idx"
  base='{}'; [ -r "$CUSTOM_CURVE_EDITOR_FILE" ] && base="$(cat "$CUSTOM_CURVE_EDITOR_FILE" 2>/dev/null || echo '{}')"
  updated="$(jq -c --arg idx "$idx" --arg name "$FACTORY_CURVE_NAME" \
    --argjson target "$FACTORY_TARGET_C" --argjson hd "$FACTORY_HYST_DENSE_C" --argjson ho "$FACTORY_HYST_OUTER_C" \
    --argjson pmin "$FACTORY_MIN_PWM_PCT" --argjson ptgt "$FACTORY_TARGET_PWM_PCT" --argjson pmax "$FACTORY_MAX_PWM_PCT" '
    .schema=3 | .curves=(.curves // {}) |
    .curves[$idx]={name:$name,target_temp_c:$target,hysteresis_dense_c:$hd,hysteresis_outer_c:$ho,min_pwm_percent:$pmin,target_pwm_percent:$ptgt,max_pwm_percent:$pmax,response_mode:"precise"}
  ' <<<"$base" 2>/dev/null)" || return 1
  curve_editor_write_json "$updated" || return 1
  load_custom_curve "$idx"
  log "Curve Editor: krzywa ${idx} przywrócona do wartości fabrycznych (${CUSTOM_PROFILE_LABEL})."
  ha_sync_profile_options || true
  ha_publish_curve_editor_state || true
}

reset_custom_curve_parameter() {
  local idx="$1" parameter="$2" base updated name target hd ho pmin ptgt pmax response keep_points=false
  case "$idx" in 1|2|3|4|5) ;; *) return 1 ;; esac
  case "$parameter" in name|target_temp_c|hysteresis_dense_c|hysteresis_outer_c|min_pwm_percent|target_pwm_percent|max_pwm_percent|response_mode) ;; *) log "Curve Editor: nieznany parametr resetu: $parameter"; return 1 ;; esac

  load_custom_curve "$idx"
  name="$CUSTOM_CURVE_NAME"; target="$CUSTOM_TARGET_C"; hd="$CUSTOM_HYST_DENSE_C"; ho="$CUSTOM_HYST_OUTER_C"
  pmin="$CUSTOM_MIN_PWM_PCT"; ptgt="$CUSTOM_TARGET_PWM_PCT"; pmax="$CUSTOM_MAX_PWM_PCT"; response="$CUSTOM_RESPONSE_MODE"
  curve_factory_defaults "$idx"
  case "$parameter" in
    name) name="$FACTORY_CURVE_NAME"; keep_points=true ;;
    target_temp_c) target="$FACTORY_TARGET_C" ;;
    hysteresis_dense_c) hd="$FACTORY_HYST_DENSE_C" ;;
    hysteresis_outer_c) ho="$FACTORY_HYST_OUTER_C" ;;
    min_pwm_percent) pmin="$FACTORY_MIN_PWM_PCT" ;;
    target_pwm_percent) ptgt="$FACTORY_TARGET_PWM_PCT" ;;
    max_pwm_percent) pmax="$FACTORY_MAX_PWM_PCT" ;;
    response_mode) response="$FACTORY_RESPONSE_MODE" ;;
  esac

  # Keep a valid PWM ordering even if the user previously used extreme values.
  if ! awk -v a="$pmin" -v b="$ptgt" -v c="$pmax" 'BEGIN { exit !(a < b && b < c) }'; then
    pmin="$FACTORY_MIN_PWM_PCT"; ptgt="$FACTORY_TARGET_PWM_PCT"; pmax="$FACTORY_MAX_PWM_PCT"
  fi

  base='{}'; [ -r "$CUSTOM_CURVE_EDITOR_FILE" ] && base="$(cat "$CUSTOM_CURVE_EDITOR_FILE" 2>/dev/null || echo '{}')"
  updated="$(jq -c --arg idx "$idx" --arg name "$name" --argjson target "$target" --argjson hd "$hd" --argjson ho "$ho" \
    --argjson pmin "$pmin" --argjson ptgt "$ptgt" --argjson pmax "$pmax" --arg response "$response" --argjson keep "$keep_points" '
    .schema=3 | .curves=(.curves // {}) | .curves[$idx]=((.curves[$idx] // {}) +
      {name:$name,target_temp_c:$target,hysteresis_dense_c:$hd,hysteresis_outer_c:$ho,min_pwm_percent:$pmin,target_pwm_percent:$ptgt,max_pwm_percent:$pmax,response_mode:$response}) |
    if $keep then . else del(.curves[$idx].points) end
  ' <<<"$base" 2>/dev/null)" || return 1
  curve_editor_write_json "$updated" || return 1
  load_custom_curve "$idx"
  log "Curve Editor: parametr '${parameter}' krzywej ${idx} przywrócono do wartości domyślnej."
  ha_sync_profile_options || true
  ha_publish_curve_editor_state || true
}

reset_all_custom_curves_factory() {
  local base updated
  base='{}'; [ -r "$CUSTOM_CURVE_EDITOR_FILE" ] && base="$(cat "$CUSTOM_CURVE_EDITOR_FILE" 2>/dev/null || echo '{}')"
  updated="$(jq -c '
    .schema=3 | .curves={
      "1":{name:"Zbalansowana",target_temp_c:50.0,hysteresis_dense_c:0.75,hysteresis_outer_c:1.0,min_pwm_percent:29,target_pwm_percent:55,max_pwm_percent:100,response_mode:"precise"},
      "2":{name:"Chłodna",target_temp_c:48.0,hysteresis_dense_c:0.75,hysteresis_outer_c:1.0,min_pwm_percent:29,target_pwm_percent:55,max_pwm_percent:100,response_mode:"precise"},
      "3":{name:"Komfortowa",target_temp_c:52.0,hysteresis_dense_c:0.75,hysteresis_outer_c:1.0,min_pwm_percent:29,target_pwm_percent:55,max_pwm_percent:100,response_mode:"precise"},
      "4":{name:"Cicha",target_temp_c:55.0,hysteresis_dense_c:0.75,hysteresis_outer_c:1.0,min_pwm_percent:29,target_pwm_percent:55,max_pwm_percent:100,response_mode:"precise"},
      "5":{name:"Ultra cicha",target_temp_c:58.0,hysteresis_dense_c:0.75,hysteresis_outer_c:1.0,min_pwm_percent:29,target_pwm_percent:55,max_pwm_percent:100,response_mode:"precise"}
    }
  ' <<<"$base" 2>/dev/null)" || return 1
  curve_editor_write_json "$updated" || return 1
  load_options
  ha_sync_profile_options || true
  ha_publish_curve_editor_state || true
  log "Curve Editor: wszystkie 5 krzywych przywrócono do wartości fabrycznych jednym zapisem."
}

ha_publish_curve_editor_state() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  local saved="${CUSTOM_CURVE_INDEX:-1}" i curves='[]' pts mode curve payload local_is_factory selector_label
  for i in 1 2 3 4 5; do
    load_custom_curve "$i"
    pts="$(curve_points_json_current)"
    mode="$(curve_editor_mode "$i")"
    curve_factory_defaults "$i"
    local_is_factory=false
    if [ "$mode" = "generated" ] && [ "$CUSTOM_CURVE_NAME" = "$FACTORY_CURVE_NAME" ] && \
       awk -v a="$CUSTOM_TARGET_C" -v b="$FACTORY_TARGET_C" -v c="$CUSTOM_HYST_DENSE_C" -v d="$FACTORY_HYST_DENSE_C" \
           -v e="$CUSTOM_HYST_OUTER_C" -v f="$FACTORY_HYST_OUTER_C" -v g="$CUSTOM_MIN_PWM_PCT" -v h="$FACTORY_MIN_PWM_PCT" \
           -v j="$CUSTOM_TARGET_PWM_PCT" -v k="$FACTORY_TARGET_PWM_PCT" -v l="$CUSTOM_MAX_PWM_PCT" -v m="$FACTORY_MAX_PWM_PCT" \
           -v r="$CUSTOM_RESPONSE_MODE" -v fr="$FACTORY_RESPONSE_MODE" \
           'BEGIN{exit !((a+0)==(b+0)&&(c+0)==(d+0)&&(e+0)==(f+0)&&(g+0)==(h+0)&&(j+0)==(k+0)&&(l+0)==(m+0)&&r==fr)}'; then
      local_is_factory=true
    fi
    selector_label="$(curve_selector_label "$i" "$CUSTOM_CURVE_NAME" "$CUSTOM_TARGET_C")"
    curve="$(jq -cn --argjson index "$i" --arg name "$CUSTOM_CURVE_NAME" --arg mode "$mode" --arg selector "$selector_label" --argjson is_factory "$local_is_factory" \
      --argjson target "$CUSTOM_TARGET_C" --argjson hd "$CUSTOM_HYST_DENSE_C" --argjson ho "$CUSTOM_HYST_OUTER_C" --argjson pmin "$CUSTOM_MIN_PWM_PCT" --argjson ptgt "$CUSTOM_TARGET_PWM_PCT" --argjson pmax "$CUSTOM_MAX_PWM_PCT" --arg response "$CUSTOM_RESPONSE_MODE" \
      --arg fname "$FACTORY_CURVE_NAME" --argjson ftarget "$FACTORY_TARGET_C" --argjson fhd "$FACTORY_HYST_DENSE_C" --argjson fho "$FACTORY_HYST_OUTER_C" --argjson fpmin "$FACTORY_MIN_PWM_PCT" --argjson fptgt "$FACTORY_TARGET_PWM_PCT" --argjson fpmax "$FACTORY_MAX_PWM_PCT" --arg fresponse "$FACTORY_RESPONSE_MODE" --argjson points "$pts" \
      '{index:$index,name:$name,selector_label:$selector,mode:$mode,is_factory:$is_factory,target_temp_c:$target,hysteresis_dense_c:$hd,hysteresis_outer_c:$ho,min_pwm_percent:$pmin,target_pwm_percent:$ptgt,max_pwm_percent:$pmax,response_mode:$response,factory_defaults:{name:$fname,target_temp_c:$ftarget,hysteresis_dense_c:$fhd,hysteresis_outer_c:$fho,min_pwm_percent:$fpmin,target_pwm_percent:$fptgt,max_pwm_percent:$fpmax,response_mode:$fresponse},points:$points}')"
    curves="$(jq -cn --argjson arr "$curves" --argjson c "$curve" '$arr + [$c]')"
  done
  load_custom_curve "$saved"
  payload="$(jq -cn --arg state ready --argjson curves "$curves" --arg updated "$(date '+%Y-%m-%d %H:%M:%S')" '{state:$state,attributes:{friendly_name:"SBC5 Control Center Curve Editor",icon:"mdi:chart-bell-curve-cumulative",curve_count:5,point_count:15,curves:$curves,last_update:$updated,temperature_range_c:"35–80",pwm_range_percent:"0–100",validation:"temperatures strictly increasing; PWM non-decreasing"}}')"
  printf '%s\n' "$payload" > "$CURVE_EDITOR_STATE_FILE" 2>/dev/null || true
  local entity
  local -a editor_entities=(sensor.sbc5_control_center_curve_editor)
  if ! namespace_migration_complete; then editor_entities+=(sensor.sbc5_fan_curve_editor); fi
  for entity in "${editor_entities[@]}"; do
    curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$payload" \
      "http://supervisor/core/api/states/${entity}" >/dev/null 2>&1 || true
  done
}

ha_republish_curve_editor_state() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  if [ ! -s "$CURVE_EDITOR_STATE_FILE" ]; then
    ha_publish_curve_editor_state || true
    return 0
  fi
  local entity
  local -a editor_entities=(sensor.sbc5_control_center_curve_editor)
  if ! namespace_migration_complete; then editor_entities+=(sensor.sbc5_fan_curve_editor); fi
  for entity in "${editor_entities[@]}"; do
    curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" \
      --data-binary "@$CURVE_EDITOR_STATE_FILE" \
      "http://supervisor/core/api/states/${entity}" >/dev/null 2>&1 || true
  done
}

generate_custom_overlay() {
  generate_custom_arrays
  local f="$ACTIVE_OVERLAY_DTS" i state
  {
    echo '/dts-v1/;'
    echo '/plugin/;'
    echo
    echo '/ {'
    echo '    compatible = "brcm,bcm2712";'
    echo
    echo '    fragment@0 {'
    echo '        target = <&fan>;'
    echo '        __overlay__ {'
    echo '            status = "okay";'
    echo '            cooling-min-state = <0>;'
    echo '            cooling-max-state = <100>;'
    # v2.1.0: 1% PWM lattice for adaptive/AI-ready control. The fan driver keeps
    # the kernel thermal governor as the safety owner; cur_state becomes 0..100.
    printf '            cooling-levels = <0'
    for i in $(seq 1 100); do printf ' %s' "$(( (i * 255 + 50) / 100 ))"; done
    echo '>;'
    echo '        };'
    echo '    };'
    echo
    echo '    fragment@1 { target = <&rp1_pwm1>; __overlay__ { status = "okay"; }; };'
    echo
    local syms=(cpu_tepid cpu_warm cpu_hot cpu_vhot)
    for i in $(seq 1 4); do
      echo "    fragment@$((i+1)) {"
      echo "        target = <&${syms[$((i-1))]}>;"
      echo '        __overlay__ {'
      echo "            temperature = <${CUSTOM_T[$i]}>;"
      echo "            hysteresis = <${CUSTOM_H[$i]}>;"
      echo '            type = "active";'
      echo '        };'
      echo '    };'
      echo
    done
    echo '    fragment@6 {'
    echo '        target = <&thermal_trips>;'
    echo '        __overlay__ {'
    for i in $(seq 5 15); do
      echo "            customcurve_t${i}: customcurve-t${i} {"
      echo "                temperature = <${CUSTOM_T[$i]}>;"
      echo "                hysteresis = <${CUSTOM_H[$i]}>;"
      echo '                type = "active";'
      echo '            };'
      echo
    done
    echo '        };'
    echo '    };'
    echo
    echo '    fragment@7 {'
    echo '        target = <&cooling_maps>;'
    echo '        __overlay__ {'
    local mapnames=(tepid warm hot vhot)
    local tripsyms=(cpu_tepid cpu_warm cpu_hot cpu_vhot)
    for i in $(seq 1 4); do
      state="$(( (CUSTOM_PWM[$i] * 100 + 127) / 255 ))"
      echo "            ${mapnames[$((i-1))]} {"
      echo "                trip = <&${tripsyms[$((i-1))]}>;"
      echo "                cooling-device = <&fan ${state} ${state}>;"
      echo '            };'
      echo
    done
    for i in $(seq 5 15); do
      state="$(( (CUSTOM_PWM[$i] * 100 + 127) / 255 ))"
      echo "            customcurve-map${i} {"
      echo "                trip = <&customcurve_t${i}>;"
      echo "                cooling-device = <&fan ${state} ${state}>;"
      echo '            };'
      echo
    done
    echo '            melt {'
    echo '                trip = <&cpu_crit>;'
    echo '                cooling-device = <&fan 100 100>;'
    echo '            };'
    echo '        };'
    echo '    };'
    echo '};'
  } > "$f"

  log "Wygenerowano ${CUSTOM_PROFILE_LABEL}: target=${CUSTOM_TARGET_C}°C hyst=${CUSTOM_HYST_DENSE_C}/${CUSTOM_HYST_OUTER_C}°C PWM=${CUSTOM_MIN_PWM_PCT}/${CUSTOM_TARGET_PWM_PCT}/${CUSTOM_MAX_PWM_PCT}%"
}

select_overlay() {
  local profile="$1" idx
  case "$profile" in
    stable50_10)
      ACTIVE_OVERLAY_NAME="$OVERLAY_10_NAME"
      ACTIVE_OVERLAY_DTS="$OVERLAY_10_DTS"
      ;;
    stable50_15)
      ACTIVE_OVERLAY_NAME="$OVERLAY_15_NAME"
      ACTIVE_OVERLAY_DTS="$OVERLAY_15_DTS"
      ;;
    custom15)
      load_custom_curve 1
      ACTIVE_OVERLAY_NAME="rpi5-custom1"
      ACTIVE_OVERLAY_DTS="/tmp/rpi5-custom1-overlay.dts"
      ;;
    custom[1-5])
      idx="${profile#custom}"
      load_custom_curve "$idx"
      ACTIVE_OVERLAY_NAME="rpi5-custom${idx}"
      ACTIVE_OVERLAY_DTS="/tmp/rpi5-custom${idx}-overlay.dts"
      ;;
    *)
      log "Nieznany profil overlay: $profile"
      return 1
      ;;
  esac
  ACTIVE_OVERLAY_DTBO="/tmp/${ACTIVE_OVERLAY_NAME}.dtbo"
}

ha_set_active_profile() {
  local label="$1" code="$2" thresholds="$3"
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0

  local payload
  payload="$(jq -n \
    --arg state "$label" \
    --arg code "$code" \
    --arg thresholds "$thresholds" \
    --arg curve_index "$CUSTOM_CURVE_INDEX" \
    --arg curve_name "$CUSTOM_CURVE_NAME" \
    --arg target "$CUSTOM_TARGET_C" \
    --arg hyst_dense "$CUSTOM_HYST_DENSE_C" \
    --arg hyst_outer "$CUSTOM_HYST_OUTER_C" \
    --arg pwm_min "$CUSTOM_MIN_PWM_PCT" \
    --arg pwm_target "$CUSTOM_TARGET_PWM_PCT" \
    --arg pwm_max "$CUSTOM_MAX_PWM_PCT" \
    --arg response_mode "$CUSTOM_RESPONSE_MODE" \
    --arg control_mode "$COOLING_CONTROL_MODE" \
    --arg auto_style "$COOLING_AUTO_STYLE" \
    --argjson hybrid_limit "$HYBRID_CORRECTION_LIMIT_PCT" \
    --arg updated "$(date '+%Y-%m-%d %H:%M:%S')" \
    '{
      state: $state,
      attributes: {
        friendly_name: "SBC5 aktywny profil chłodzenia",
        icon: "mdi:tune-vertical",
        profile_code: $code,
        progi: $thresholds,
        custom_curve_index: $curve_index,
        custom_curve_name: $curve_name,
        custom_target_c: $target,
        custom_hysteresis_dense_c: $hyst_dense,
        custom_hysteresis_outer_c: $hyst_outer,
        custom_pwm_percent: ($pwm_min + " / " + $pwm_target + " / " + $pwm_max),
        custom_response_mode: $response_mode,
        control_mode: $control_mode,
        control_mode_label: (if $control_mode == "automatic" then "Automatyczny" elif $control_mode == "hybrid" then "Hybrydowy" else "Ręczny" end),
        automatic_style: $auto_style,
        hybrid_correction_limit_percent: $hybrid_limit,
        control_source: (if $control_mode == "automatic" then "adaptive" elif $control_mode == "hybrid" then "curve+adaptive" else "kernel_curve" end),
        last_update: $updated
      }
    }'
  )"

  for profile_entity in sensor.sbc5_active_fan_profile sensor.rpi5_active_fan_profile; do
    curl -fsS -X POST \
      -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$payload" \
      "http://supervisor/core/api/states/${profile_entity}" \
      >/dev/null 2>&1 || true
  done
}


ha_get_state() {
  local entity="$1"
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 1
  curl -fsS \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    "http://supervisor/core/api/states/${entity}" 2>/dev/null |
    jq -r '.state // empty' 2>/dev/null
}

ha_sync_profile_options() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  refresh_all_custom_curve_metadata

  local entity="input_select.sbc5_fan_profile"
  local current_json current_state current_options desired_options payload replacement=""

  current_json="$(curl -fsS \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    "http://supervisor/core/api/states/${entity}" 2>/dev/null || true)"

  [ -n "$current_json" ] || return 0
  current_state="$(printf '%s' "$current_json" | jq -r '.state // empty' 2>/dev/null || true)"
  current_options="$(printf '%s' "$current_json" | jq -c '.attributes.options // []' 2>/dev/null || echo '[]')"

  desired_options="$(jq -cn \
    --arg factory "Fabryczny" \
    --arg c1 "${CUSTOM_CURVE_LABELS[1]}" '[$factory,$c1]')"

  if [ "$current_options" != "$desired_options" ]; then
    if [ "$current_state" != "Fabryczny" ] && [ "$current_state" != "${CUSTOM_CURVE_LABELS[1]}" ]; then
      replacement="${CUSTOM_CURVE_LABELS[1]}"
    fi

    payload="$(jq -cn --arg entity "$entity" --argjson options "$desired_options" '{entity_id:$entity,options:$options}')"
    curl -fsS -X POST \
      -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$payload" \
      "http://supervisor/core/api/services/input_select/set_options" >/dev/null 2>&1 || return 0
    log "Ujednolicono listę profili HA: Fabryczny + jedna konfigurowalna krzywa custom1."

    if [ -n "$replacement" ]; then
      payload="$(jq -cn --arg entity "$entity" --arg option "$replacement" '{entity_id:$entity,option:$option}')"
      curl -fsS -X POST \
        -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "http://supervisor/core/api/services/input_select/select_option" >/dev/null 2>&1 || true
    fi
  fi

  # v1.9.19: Curve Editor and profile picker share the same user-facing names.
  local editor_entity="input_select.sbc5_curve_editor_curve" editor_json editor_state editor_options editor_desired editor_idx editor_replacement
  editor_json="$(curl -fsS -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" "http://supervisor/core/api/states/${editor_entity}" 2>/dev/null || true)"
  if [ -n "$editor_json" ]; then
    editor_state="$(printf '%s' "$editor_json" | jq -r '.state // empty' 2>/dev/null || true)"
    editor_options="$(printf '%s' "$editor_json" | jq -c '.attributes.options // []' 2>/dev/null || echo '[]')"
    editor_desired="$(jq -cn --arg c1 "${CUSTOM_CURVE_SELECTOR_LABELS[1]}" '[$c1]')"
    editor_idx="$(printf '%s' "$editor_state" | sed -n 's/^[^0-9]*\([1-5]\).*/\1/p')"
    [ -n "$editor_idx" ] || editor_idx=1
    editor_replacement="${CUSTOM_CURVE_SELECTOR_LABELS[1]}"
    if [ "$editor_options" != "$editor_desired" ]; then
      payload="$(jq -cn --arg entity "$editor_entity" --argjson options "$editor_desired" '{entity_id:$entity,options:$options}')"
      curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$payload" "http://supervisor/core/api/services/input_select/set_options" >/dev/null 2>&1 || true
      payload="$(jq -cn --arg entity "$editor_entity" --arg option "$editor_replacement" '{entity_id:$entity,option:$option}')"
      curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$payload" "http://supervisor/core/api/services/input_select/select_option" >/dev/null 2>&1 || true
      log "Curve Editor: uproszczono selektor do jedynej wspieranej krzywej custom1."
    fi
  fi
}

ha_requested_profile_code() {
  local requested=""
  requested="$(cat "$LAST_FAN_PROFILE_FILE" 2>/dev/null || true)"
  [ "$requested" = "custom15" ] && requested="custom1"
  case "$requested" in
    factory|custom1) printf '%s\n' "$requested" ;;
    custom[2-5]|stable50_10|stable50_15|quiet|normal|cool|sub50|stable50)
      # Profile legacy pozostają tylko migracyjnie; UX 2.6.x udostępnia factory/custom1.
      printf 'custom1\n' ;;
    *)
      # Brak trwałego wyboru oznacza bezpieczny stan początkowy: profil fabryczny.
      printf 'factory\n' ;;
  esac
}

ha_requested_profile_label() {
  local requested="${1:-$(ha_requested_profile_code)}"
  refresh_all_custom_curve_metadata
  case "$requested" in
    factory) printf 'Fabryczny\n' ;;
    custom1) printf '%s\n' "${CUSTOM_CURVE_LABELS[1]}" ;;
    *) printf '%s\n' "$requested" ;;
  esac
}

ha_sync_selected_profile_to_requested() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  local entity="input_select.sbc5_fan_profile" requested_code requested_label current_json options current payload

  ha_sync_profile_options || true
  requested_code="$(ha_requested_profile_code)"
  requested_label="$(ha_requested_profile_label "$requested_code")"
  current_json="$(curl -fsS \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    "http://supervisor/core/api/states/${entity}" 2>/dev/null || true)"
  [ -n "$current_json" ] || return 0
  current="$(printf '%s' "$current_json" | jq -r '.state // empty' 2>/dev/null || true)"
  options="$(printf '%s' "$current_json" | jq -c '.attributes.options // []' 2>/dev/null || echo '[]')"

  if jq -e --arg requested "$requested_label" 'index($requested) != null' <<<"$options" >/dev/null 2>&1; then
    if [ "$current" != "$requested_label" ]; then
      payload="$(jq -cn --arg entity "$entity" --arg option "$requested_label" '{entity_id:$entity,option:$option}')"
      if curl -fsS -X POST \
        -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "http://supervisor/core/api/services/input_select/select_option" >/dev/null 2>&1; then
        log "UX Runtime: selektor profilu przywrócono do profilu żądanego: ${requested_label} (${requested_code})."
      fi
    fi
  fi
}

ha_select_option_if_needed() {
  local entity="$1" option="$2" current options payload
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  current="$(ha_get_state "$entity" 2>/dev/null || true)"
  [ "$current" = "$option" ] && return 0
  options="$(curl -fsS -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" "http://supervisor/core/api/states/${entity}" 2>/dev/null | jq -c '.attributes.options // []' 2>/dev/null || echo '[]')"
  jq -e --arg option "$option" 'index($option) != null' <<<"$options" >/dev/null 2>&1 || return 0
  payload="$(jq -cn --arg entity "$entity" --arg option "$option" '{entity_id:$entity,option:$option}')"
  curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$payload" \
    "http://supervisor/core/api/services/input_select/select_option" >/dev/null 2>&1 || true
}

ha_sync_cpu_gpu_profile_selectors() {
  local cpu gpu cpu_label gpu_label
  cpu="$(cpu_profile_requested_profile 2>/dev/null || echo factory)"
  gpu="$(gpu_profile_requested_profile 2>/dev/null || echo factory)"
  case "$cpu" in
    mild) cpu_label="OC Łagodny · 2500 MHz" ;;
    balanced) cpu_label="OC Zbalansowany · 2600 MHz" ;;
    performance) cpu_label="OC Wydajność · 2800 MHz" ;;
    experimental) cpu_label="OC 3.0 GHz · 3000 MHz" ;;
    advanced) cpu_label="Zaawansowany · ustawienia ręczne" ;;
    *) cpu_label="Fabryczny · 2400 MHz" ;;
  esac
  case "$gpu" in
    eco) gpu_label="Eco · 850 / 850 / 900 MHz" ;;
    balanced) gpu_label="Zbalansowany · 950 / 950 / 1000 MHz" ;;
    performance) gpu_label="Wydajność · 1000 / 1000 / 1100 MHz" ;;
    experimental) gpu_label="Eksperymentalny · 1100 / 1100 / 1200 MHz" ;;
    advanced) gpu_label="Zaawansowany · ustawienia ręczne" ;;
    *) gpu_label="Fabryczny · Auto" ;;
  esac
  ha_select_option_if_needed input_select.sbc5_cpu_oc_profile "$cpu_label"
  ha_select_option_if_needed input_select.sbc5_gpu_profile "$gpu_label"
}

profile_state_options_signature() {
  [ -r "$OPTIONS_FILE" ] || { printf 'no-options\n'; return 0; }
  jq -cS '{section_cpu_enabled:(.section_cpu_enabled // false),config_cpu_profile:(.config_cpu_profile // "factory"),config_cpu:(.config_cpu // {}),section_gpu_enabled:(.section_gpu_enabled // false),config_gpu_profile:(.config_gpu_profile // "factory"),config_gpu:(.config_gpu // {})}' "$OPTIONS_FILE" 2>/dev/null | sha256sum | awk '{print $1}'
}

profile_options_subset_from_json() {
  jq -cS '{
    section_cpu_enabled:(.section_cpu_enabled // false),
    config_cpu_profile:(.config_cpu_profile // "factory"),
    config_cpu:(.config_cpu // {}),
    section_gpu_enabled:(.section_gpu_enabled // false),
    config_gpu_profile:(.config_gpu_profile // "factory"),
    config_gpu:(.config_gpu // {})
  }' 2>/dev/null
}

supervisor_own_options_json() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 1
  local tmp="/tmp/sbc5_supervisor_self_info.$$"
  if ! supervisor_get "/addons/self/info" "$tmp" true; then rm -f "$tmp"; return 1; fi
  jq -c '.data.options // .options // {}' "$tmp" 2>/dev/null
  local rc=$?
  rm -f "$tmp"
  return "$rc"
}

supervisor_self_security_json() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 1
  local tmp="/tmp/sbc5_supervisor_security.$$"
  if ! supervisor_get "/addons/self/info" "$tmp" true; then rm -f "$tmp"; return 1; fi
  jq -c '(.data // .) | {protected:(.protected // null),host_pid:(.host_pid // null),full_access:(.full_access // null),apparmor:(.apparmor // null),state:(.state // null)}' "$tmp" 2>/dev/null
  local rc=$?
  rm -f "$tmp"
  return "$rc"
}

supervisor_profile_signature_json() {
  local subset
  subset="$(profile_options_subset_from_json)" || return 1
  printf '%s' "$subset" | sha256sum | awk '{print $1}'
}

supervisor_profile_marker_signature() {
  [ -r "$SUPERVISOR_PROFILE_SYNC_FILE" ] || return 0
  jq -r '.signature // empty' "$SUPERVISOR_PROFILE_SYNC_FILE" 2>/dev/null || true
}

supervisor_profile_marker_write() {
  local options_json="$1" source="${2:-runtime}" subset sig tmp
  subset="$(printf '%s' "$options_json" | profile_options_subset_from_json)" || return 1
  sig="$(printf '%s' "$subset" | sha256sum | awk '{print $1}')"
  tmp="${SUPERVISOR_PROFILE_SYNC_FILE}.tmp.$$"
  jq -n --argjson schema "$SUPERVISOR_PROFILE_SYNC_SCHEMA" --arg signature "$sig" --arg source "$source" \
    --arg updated "$(date '+%Y-%m-%d %H:%M:%S')" --argjson profile_options "$subset" \
    '{schema:$schema,signature:$signature,source:$source,updated:$updated,profile_options:$profile_options}' > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$SUPERVISOR_PROFILE_SYNC_FILE"
}

supervisor_apply_native_profile_options() {
  # Import only profile-related fields from Supervisor; all unrelated runtime options remain local.
  local sup="$1" tmp
  [ -r "$OPTIONS_FILE" ] || return 1
  tmp="${OPTIONS_FILE}.supervisor_profile.$$"
  jq --argjson sup "$sup" '
    .section_cpu_enabled=($sup.section_cpu_enabled // false) |
    .config_cpu_profile=($sup.config_cpu_profile // "factory") |
    .config_cpu=($sup.config_cpu // {}) |
    .section_gpu_enabled=($sup.section_gpu_enabled // false) |
    .config_gpu_profile=($sup.config_gpu_profile // "factory") |
    .config_gpu=($sup.config_gpu // {}) |
    if (($sup.config_txt_manager.enabled // false) == true) then .config_txt_manager.enabled=true else . end
  ' "$OPTIONS_FILE" > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$OPTIONS_FILE"
  cpu_profile_sync_state_from_options_if_changed || true
  gpu_profile_sync_state_from_options_if_changed || true
  cpu_profile_restore_options_from_state || true
  gpu_profile_restore_options_from_state || true
  supervisor_profile_marker_write "$sup" "native_configuration" || true
  log "Profile State: zaimportowano zmianę profilu z natywnej Konfiguracji Supervisor."
}

supervisor_sync_profile_state_to_store() {
  # Persist the durable CPU/GPU request in Supervisor only when something actually differs.
  # An already fetched Supervisor options JSON may be supplied as $1 to avoid a duplicate API read.
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  [ -r "$CPU_PROFILE_STATE_FILE" ] && [ -r "$GPU_PROFILE_STATE_FILE" ] || return 0
  local sup="${1:-}" cpu_en cpu_p cpu_cfg gpu_en gpu_p gpu_cfg merged current_subset desired_subset payload out current_sig marker_sig
  [ -n "$sup" ] || sup="$(supervisor_own_options_json)" || return 1
  cpu_en="$(jq -r '.enabled // false' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo false)"
  cpu_p="$(jq -r '.requested_profile // "factory"' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo factory)"
  cpu_cfg="$(jq -c '.requested_config // {}' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo '{}')"
  gpu_en="$(jq -r '.enabled // false' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo false)"
  gpu_p="$(jq -r '.requested_profile // "factory"' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo factory)"
  gpu_cfg="$(jq -c '.requested_config // {}' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo '{}')"
  merged="$(jq -c --argjson cpu_en "$cpu_en" --arg cpu_p "$cpu_p" --argjson cpu_cfg "$cpu_cfg" \
      --argjson gpu_en "$gpu_en" --arg gpu_p "$gpu_p" --argjson gpu_cfg "$gpu_cfg" '
      .section_cpu_enabled=$cpu_en |
      .config_cpu_profile=$cpu_p |
      .config_cpu=$cpu_cfg |
      .section_gpu_enabled=$gpu_en |
      .config_gpu_profile=$gpu_p |
      .config_gpu=$gpu_cfg |
      if $gpu_en then .config_txt_manager.enabled=true else . end
    ' <<<"$sup" 2>/dev/null)" || return 1
  current_subset="$(printf '%s' "$sup" | profile_options_subset_from_json)"
  desired_subset="$(printf '%s' "$merged" | profile_options_subset_from_json)"
  if [ "$current_subset" = "$desired_subset" ]; then
    # Steady state must be read-only. v2.8.20 rewrote the marker every 5 s here.
    current_sig="$(printf '%s' "$current_subset" | sha256sum | awk '{print $1}')"
    marker_sig="$(supervisor_profile_marker_signature)"
    if [ -z "$marker_sig" ] || [ "$marker_sig" != "$current_sig" ]; then
      supervisor_profile_marker_write "$sup" "already_current" || true
    fi
    return 0
  fi
  payload="$(jq -cn --argjson options "$merged" '{options:$options}')"
  out="/tmp/sbc5_supervisor_profile_options.$$"
  if supervisor_post "/addons/self/options" "$payload" "$out"; then
    supervisor_profile_marker_write "$merged" "sbc5_profile_state" || true
    log "Profile State: zapisano profile CPU/GPU do Supervisor — natywna Konfiguracja jest zgodna ze stanem trwałym."
    rm -f "$out"
    return 0
  fi
  rm -f "$out"
  log "Profile State: nie udało się zapisać profili CPU/GPU do Supervisor; lokalny stan trwały pozostaje bez zmian."
  return 1
}

supervisor_sync_migrated_options_to_store() {
  # During Store/canary migration /data/options.json is imported after the
  # container has already started. Supervisor keeps a separate persistent
  # options store for each App slug and would otherwise restore its stale
  # defaults on the next container start. Persist the imported options into
  # Supervisor before finalizing the migration guard.
  #
  # Only keys already present in the target App's native options are copied.
  # This keeps target-only/new-schema defaults and prevents old/foreign keys
  # from being submitted to Supervisor. Objects are recursively overlaid;
  # arrays/scalars are replaced by the imported value.
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 1
  [ -r "$OPTIONS_FILE" ] || return 1
  local sup="${1:-}" imported merged current_norm desired_norm payload out
  [ -n "$sup" ] || sup="$(supervisor_own_options_json)" || return 1
  imported="$(jq -c 'if type == "object" then . else {} end' "$OPTIONS_FILE" 2>/dev/null)" || return 1
  merged="$(jq -cn --argjson base "$sup" --argjson src "$imported" '
    def overlay_known($b; $s):
      if (($b|type) == "object") and (($s|type) == "object") then
        reduce ($s | keys_unsorted[]) as $k ($b;
          if ($b | has($k)) then .[$k] = overlay_known($b[$k]; $s[$k]) else . end)
      else $s end;
    overlay_known($base; $src)
  ' 2>/dev/null)" || return 1
  current_norm="$(jq -cS . <<<"$sup" 2>/dev/null)" || return 1
  desired_norm="$(jq -cS . <<<"$merged" 2>/dev/null)" || return 1
  if [ "$current_norm" = "$desired_norm" ]; then
    supervisor_profile_marker_write "$merged" "migration_options_already_current" || true
    return 0
  fi
  payload="$(jq -cn --argjson options "$merged" '{options:$options}')"
  out="/tmp/sbc5_supervisor_migration_options.$$"
  if supervisor_post "/addons/self/options" "$payload" "$out"; then
    supervisor_profile_marker_write "$merged" "migration_options_handoff" || true
    log "Store Migration: pełny zaimportowany stan opcji zapisano do trwałej Konfiguracji Supervisor dla bieżącej instancji."
    rm -f "$out"
    return 0
  fi
  rm -f "$out"
  log "Store Migration: nie udało się utrwalić pełnych zaimportowanych opcji w Supervisor; guard pozostaje pending i nie dopuści do nadpisania stanu przy restarcie."
  return 1
}

migration_profile_guard_active() {
  [ -r "$STORE_MIGRATION_PROFILE_GUARD_FILE" ] || return 1
  jq -e '.state == "pending"' "$STORE_MIGRATION_PROFILE_GUARD_FILE" >/dev/null 2>&1
}

migration_profile_guard_finalize() {
  [ -r "$STORE_MIGRATION_PROFILE_GUARD_FILE" ] || return 0
  local tmp="${STORE_MIGRATION_PROFILE_GUARD_FILE}.tmp.$$"
  jq --arg completed "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '.state="finalized" | .completed_at=$completed' \
    "$STORE_MIGRATION_PROFILE_GUARD_FILE" > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$STORE_MIGRATION_PROFILE_GUARD_FILE"
  log "Store Migration: profile_sync_guard=finalized — pełne opcje migracji oraz trwałe profile CPU/GPU zapisano do natywnej Konfiguracji Supervisor."
}

migration_profile_guard_sync() {
  local sup="${1:-}"
  migration_profile_guard_active || return 1
  # Imported /data state is authoritative until the complete imported App
  # configuration is copied to this Store/canary slug's persistent Supervisor
  # options. CPU/GPU durable state is folded into options.json first, then the
  # whole known-schema option tree is persisted atomically through Supervisor.
  rm -f "$SUPERVISOR_PROFILE_SYNC_FILE" 2>/dev/null || true
  cpu_profile_restore_options_from_state || true
  gpu_profile_restore_options_from_state || true
  [ -n "$sup" ] || sup="$(supervisor_own_options_json 2>/dev/null || true)"
  [ -n "$sup" ] || return 0
  if supervisor_sync_migrated_options_to_store "$sup"; then
    migration_profile_guard_finalize || true
  fi
  return 0
}

supervisor_profile_reconcile_startup() {
  # A Store migration guard has absolute priority on the first post-import start.
  # It prevents stale Supervisor schema defaults (Factory/off) from overwriting the
  # durable CPU/GPU state imported from the historical local identity.
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  local sup sig last
  sup="$(supervisor_own_options_json)" || return 0
  if migration_profile_guard_active; then
    migration_profile_guard_sync "$sup" || true
    return 0
  fi

  # Normal two-way reconciliation after migration finalization.
  sig="$(printf '%s' "$sup" | supervisor_profile_signature_json)"
  last="$(supervisor_profile_marker_signature)"
  if [ -n "$last" ] && [ "$sig" != "$last" ]; then
    supervisor_apply_native_profile_options "$sup" || true
    load_options
    return 0
  fi
  supervisor_sync_profile_state_to_store "$sup" || true
}

profile_state_reconcile_loop() {
  # Low-overhead two-way reconciliation. Steady state performs one Supervisor read per cycle
  # and no writes. Local/YAML paths still synchronize immediately; native Configuration is
  # detected by this safety poll with a bounded delay.
  local sig stable sup sup_sig marker_sig native_changed=false
  LAST_PROFILE_STATE_OPTIONS_SIGNATURE="$(profile_state_options_signature)"
  while true; do
    sleep "$PROFILE_STATE_RECONCILE_INTERVAL_SECONDS"
    native_changed=false
    sup="$(supervisor_own_options_json 2>/dev/null || true)"
    if migration_profile_guard_active; then
      migration_profile_guard_sync "$sup" || true
      LAST_PROFILE_STATE_OPTIONS_SIGNATURE="$(profile_state_options_signature)"
      continue
    fi
    if [ -n "$sup" ]; then
      sup_sig="$(printf '%s' "$sup" | supervisor_profile_signature_json)"
      marker_sig="$(supervisor_profile_marker_signature)"
      if [ -n "$marker_sig" ] && [ -n "$sup_sig" ] && [ "$sup_sig" != "$marker_sig" ]; then
        supervisor_apply_native_profile_options "$sup" || true
        native_changed=true
      fi
    fi

    sig="$(profile_state_options_signature)"
    [ -n "$sig" ] || continue
    if [ "$sig" != "$LAST_PROFILE_STATE_OPTIONS_SIGNATURE" ] || [ "$native_changed" = "true" ]; then
      sleep 1
      stable="$(profile_state_options_signature)"
      [ "$sig" = "$stable" ] || continue
      cpu_profile_sync_state_from_options_if_changed || true
      gpu_profile_sync_state_from_options_if_changed || true
      cpu_profile_restore_options_from_state || true
      gpu_profile_restore_options_from_state || true
      load_options
      sync_cpu_profile_from_options true || true
      sync_gpu_profile_from_options true || true
      if [ "$CONFIG_TXT_OPTIONS_ENABLED" = "true" ]; then sync_config_txt_from_options true || true; fi
      supervisor_sync_profile_state_to_store "$sup" || true
      publish_telemetry_snapshot || true
      ha_sync_cpu_gpu_profile_selectors || true
      LAST_PROFILE_STATE_OPTIONS_SIGNATURE="$(profile_state_options_signature)"
      log "Profile State Reconciler: YAML / Ingress / Supervisor Configuration są zgodne z trwałym stanem CPU i GPU."
    fi
  done
}

ha_publish_action_result() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  local status="${1:-ok}" action_name="${2:-unknown}" message="${3:-}" payload
  payload="$(jq -cn --arg state "$status" --arg action "$action_name" --arg message "$message" --arg ts "$(date '+%Y-%m-%d %H:%M:%S')" \
    '{state:$state,attributes:{friendly_name:"SBC5 Control Center Last Action",icon:(if $state=="ok" then "mdi:check-circle-outline" else "mdi:alert-circle-outline" end),action:$action,message:$message,timestamp:$ts}}')"
  printf '%s\n' "$payload" > "$UX_LAST_ACTION_FILE" 2>/dev/null || true
  curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$payload" \
    http://supervisor/core/api/states/sensor.sbc5_control_center_last_action >/dev/null 2>&1 || true
}

ha_republish_last_action() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  [ -s "$UX_LAST_ACTION_FILE" ] || return 0
  curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" \
    --data-binary "@$UX_LAST_ACTION_FILE" \
    http://supervisor/core/api/states/sensor.sbc5_control_center_last_action >/dev/null 2>&1 || true
}

ux_self_test() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || { log "UX Self-test: brak SUPERVISOR_TOKEN."; return 1; }
  local missing="" e
  ha_publish_curve_editor_state || true
  ha_republish_last_action || true
  sleep 1
  for e in \
    input_select.sbc5_cc_panel \
    input_select.sbc5_fan_profile \
    input_select.sbc5_curve_editor_curve \
    input_select.sbc5_curve_editor_point \
    input_text.sbc5_curve_editor_name \
    input_number.sbc5_curve_editor_target_c \
    script.sbc5_curve_editor_refresh \
    script.sbc5_curve_editor_save_template \
    script.sbc5_curve_editor_apply_selected \
    script.sbc5_fan_calibrate \
    sensor.sbc5_package_version \
    sensor.sbc5_fan_calibration \
    sensor.sbc5_control_center_curve_editor \
    sensor.sbc5_curve_editor_runtime \
    sensor.sbc5_cpu_temperature \
    sensor.sbc5_cpu_usage \
    sensor.sbc5_fan_percent \
    sensor.sbc5_fan_level \
    sensor.sbc5_active_fan_profile \
    sensor.sbc5_requested_fan_profile \
    sensor.sbc5_fan_profile_activation; do
    if ! curl -fsS -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" \
      "http://supervisor/core/api/states/${e}" >/dev/null 2>&1; then
      missing="${missing}${missing:+, }${e}"
    fi
  done
  if [ -n "$missing" ]; then
    log "UX Self-test: BRAKI backendu: $missing. Najczęściej wymagany jest restart Home Assistant po aktualizacji package."
    ha_publish_action_result error ux_self_test "Brak encji/skryptów: $missing"
    return 1
  fi
  log "UX Self-test: OK — helpery, skrypty, package i podstawowa telemetria UX są dostępne."
  ha_publish_action_result ok ux_self_test "Backend UX gotowy; helpery, skrypty i podstawowa telemetria są dostępne."
  return 0
}

profile_options_sync_loop() {
  # Names/options are synchronized immediately after config changes and HA recovery.
  # This slow watchdog is only a safety keepalive, avoiding two REST reads every minute.
  while true; do
    ha_sync_profile_options
    sleep "$PROFILE_OPTIONS_SYNC_INTERVAL_SECONDS"
  done
}

# 1.9.21: states utworzone przez REST API znikają po restarcie Home Assistant Core,
# mimo że Local App nadal pracuje. Ten watchdog wykrywa powrót Core i natychmiast
# odtwarza stan Curve Editora oraz ostatniej akcji. Dodatkowo robi lekki refresh
# co 5 min jako bezpieczny keepalive, aby ograniczyć zbędne zapisy stanu w HA.
ux_runtime_state_loop() {
  local was_up=false ticks=0
  while true; do
    if core_api_available; then
      ticks=$((ticks + 1))
      if [ "$was_up" != "true" ] || [ "$ticks" -ge "$UX_RUNTIME_REFRESH_TICKS" ]; then
        ha_republish_curve_editor_state || true
        ha_republish_last_action || true
        fan_calibration_publish_state || true
        if [ "$was_up" != "true" ]; then
          # REST-created entities disappear with Core. Clear the semantic cache so
          # Restart Manager can recreate its entity even when the logical state did not change.
          RESTART_LAST_PUBLISHED_SIGNATURE=""
          AI_RUNTIME_LAST_SIGNATURE=""
          TELEMETRY_LAST_AI_RELAY_PUBLISH=0
          TELEMETRY_LAST_AI_RELAY_CHECK=0
          publish_restart_requirement false || true
          report_active_profile || true
          ha_sync_selected_profile_to_requested || true
          log "UX Runtime: Home Assistant dostępny — odtworzono stany Curve Editora, Restart Manager, profil i status aktualizacji."
        fi
        ticks=0
      fi
      was_up=true
    else
      was_up=false
      ticks=0
    fi
    sleep "$UX_RUNTIME_POLL_SECONDS"
  done
}

# Po pełnym restarcie hosta ustaw selektor profilu na profil faktycznie
# załadowany przez kernel. Synchronizacja jest wykonywana tylko raz na boot_id,
# aby zwykły restart aplikacji nie kasował profilu wybranego przez użytkownika
# przed jego zastosowaniem.
profile_boot_sync_loop() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0

  local saved_boot="" attempt requested_code requested_label runtime_label
  saved_boot="$(cat "$LAST_PROFILE_SYNC_BOOT_FILE" 2>/dev/null || true)"

  if [ "$saved_boot" = "$CURRENT_BOOT_ID" ]; then
    log "Synchronizacja profilu po restarcie: wykonana już dla bieżącego boot_id; selektor pozostaje profilem żądanym."
    return 0
  fi

  # Home Assistant może startować później niż aplikacja. Po powrocie Core
  # odtwarzamy profil ŻĄDANY, a nie profil aktualnie załadowany przez kernel.
  for attempt in $(seq 1 60); do
    if core_api_available; then
      ha_sync_profile_options || true
      report_active_profile || true
      ha_sync_selected_profile_to_requested || true
      requested_code="$(ha_requested_profile_code)"
      requested_label="$(ha_requested_profile_label "$requested_code")"
      runtime_label="$(ha_get_state sensor.sbc5_active_fan_profile 2>/dev/null || true)"
      printf '%s\n' "$CURRENT_BOOT_ID" > "$LAST_PROFILE_SYNC_BOOT_FILE"
      log "Synchronizacja po restarcie: profil żądany=${requested_label} (${requested_code}); runtime kernela=${runtime_label:-nieznany}. Selektor użytkownika nie jest nadpisywany runtime'em."
      return 0
    fi
    sleep 5
  done

  log "OSTRZEŻENIE: nie udało się odtworzyć profilu żądanego w UX w ciągu 5 minut. Kolejna próba nastąpi po powrocie Home Assistant."
}


supervisor_get() {
  local endpoint="$1" output="${2:-/tmp/sbc5_supervisor_get.json}" quiet="${3:-false}"
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 1
  local code
  code="$(curl -sS -o "$output" -w '%{http_code}' \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    "http://supervisor${endpoint}" 2>/dev/null || echo 000)"
  case "$code" in
    2??) return 0 ;;
    *) [ "$quiet" = "true" ] || log "Supervisor API GET ${endpoint}: HTTP ${code}"; return 1 ;;
  esac
}

MOBILE_NOTIFY_DISCOVERY_STATUS=""
log_mobile_notify_discovery_once() {
  local status="$1" message="$2"
  if [ "$status" != "$MOBILE_NOTIFY_DISCOVERY_STATUS" ]; then
    MOBILE_NOTIFY_DISCOVERY_STATUS="$status"
    log "$message"
  fi
}

resolve_mobile_notify_service() {
  RESOLVED_MOBILE_NOTIFY_SERVICE=""
  [ "$ACTIONABLE_MOBILE_NOTIFICATIONS" = "true" ] || return 0
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0

  if [ "$MOBILE_NOTIFY_SERVICE" != "auto" ]; then
    RESOLVED_MOBILE_NOTIFY_SERVICE="${MOBILE_NOTIFY_SERVICE#notify.}"
    return 0
  fi

  local services matches count
  services="$(curl -fsS \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    http://supervisor/core/api/services 2>/dev/null || true)"
  [ -n "$services" ] || return 0

  matches="$(printf '%s' "$services" | jq -r '
    .[]? | select(.domain == "notify") | .services // {} | keys[]? |
    select(startswith("mobile_app_"))
  ' 2>/dev/null || true)"
  count="$(printf '%s\n' "$matches" | sed '/^$/d' | wc -l | tr -d ' ')"

  if [ "$count" = "1" ]; then
    RESOLVED_MOBILE_NOTIFY_SERVICE="$(printf '%s\n' "$matches" | sed '/^$/d' | head -n1)"
    log_mobile_notify_discovery_once "single:${RESOLVED_MOBILE_NOTIFY_SERVICE}" "Powiadomienia mobilne: automatycznie wykryto notify.${RESOLVED_MOBILE_NOTIFY_SERVICE}."
  elif [ "$count" -gt 1 ] 2>/dev/null; then
    log_mobile_notify_discovery_once "multiple:${count}" "Powiadomienia mobilne: wykryto ${count} urządzeń. Ustaw mobile_notify_service w konfiguracji aplikacji, aby włączyć przyciski akcji."
  else
    log_mobile_notify_discovery_once "none" "Powiadomienia mobilne: nie wykryto usługi notify.mobile_app_*."
  fi
}

ha_mobile_restart_notification() {
  local state="$1" reason="$2"
  [ "$ACTIONABLE_MOBILE_NOTIFICATIONS" = "true" ] || return 0
  [ -n "$RESOLVED_MOBILE_NOTIFY_SERVICE" ] || resolve_mobile_notify_service
  [ -n "$RESOLVED_MOBILE_NOTIFY_SERVICE" ] || return 0
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0

  local title action_id action_title payload
  case "$state" in
    home_assistant)
      title="SBC5 Control Center — restart Home Assistant"
      action_id="RPI5_RESTART_HA"
      action_title="Restart Home Assistant"
      ;;
    host)
      title="SBC5 Control Center — restart Raspberry Pi 5"
      action_id="RPI5_REBOOT_HOST"
      action_title="Restart SBC5"
      ;;
    *) return 0 ;;
  esac

  payload="$(jq -cn \
    --arg title "$title" \
    --arg message "$reason" \
    --arg action_id "$action_id" \
    --arg action_title "$action_title" \
    '{
      title:$title,
      message:$message,
      data:{
        tag:"sbc5_restart_required",
        actions:[
          {action:$action_id,title:$action_title,authenticationRequired:true},
          {action:"RPI5_RESTART_LATER",title:"Później"}
        ]
      }
    }')"

  curl -fsS -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "http://supervisor/core/api/services/notify/${RESOLVED_MOBILE_NOTIFY_SERVICE}" \
    >/dev/null 2>&1 || {
      log "Nie udało się wysłać powiadomienia przez notify.${RESOLVED_MOBILE_NOTIFY_SERVICE}."
      return 1
    }
}

release_restart_required() {
  local v="none"
  if [ -r "$RELEASE_METADATA_FILE" ]; then
    v="$(jq -r '.restart_required // "none"' "$RELEASE_METADATA_FILE" 2>/dev/null || echo none)"
  fi
  case "$v" in none|home_assistant|host) echo "$v" ;; *) echo none ;; esac
}

release_summary() {
  if [ -r "$RELEASE_METADATA_FILE" ]; then
    jq -r '.summary // empty' "$RELEASE_METADATA_FILE" 2>/dev/null || true
  fi
}

restart_priority_rank() {
  case "${1:-none}" in host) echo 30 ;; home_assistant) echo 20 ;; app) echo 10 ;; *) echo 0 ;; esac
}

strongest_restart_type() {
  local a="${1:-none}" b="${2:-none}" ra rb
  ra="$(restart_priority_rank "$a")"; rb="$(restart_priority_rank "$b")"
  if [ "$ra" -ge "$rb" ]; then printf '%s\n' "$a"; else printf '%s\n' "$b"; fi
}

pending_boot_restart_type() {
  local t="none"
  if [ -r "$RESTART_STATE_FILE" ]; then
    t="$(jq -r '.type // "none"' "$RESTART_STATE_FILE" 2>/dev/null || echo none)"
  fi
  case "$t" in host|home_assistant|app) printf '%s\n' "$t" ;; *) printf 'none\n' ;; esac
}

detect_app_upgrade() {
  local previous="" restart_type summary reason
  previous="$(cat "$LAST_APP_VERSION_FILE" 2>/dev/null || true)"

  # Migracja z wersji starszych niż 1.5.6: jeśli plik historii jeszcze nie istnieje,
  # spróbuj użyć wersji aktualnie wczytanego package HA jako poprzedniej wersji.
  if [ -z "$previous" ]; then
    previous="$(ha_get_state sensor.sbc5_package_version 2>/dev/null || true)"
    case "$previous" in
      ""|unknown|unavailable|missing|none|"$APP_VERSION")
        printf '%s\n' "$APP_VERSION" > "$LAST_APP_VERSION_FILE"
        log "Post-update: zapisano wersję bazową ${APP_VERSION}."
        return 0
        ;;
      *)
        log "Post-update: migracja historii — jako poprzednią wersję wykryto package HA ${previous}."
        ;;
    esac
  fi

  if [ "$previous" = "$APP_VERSION" ]; then
    return 0
  fi

  restart_type="$(release_restart_required)"
  local pending_restart
  pending_restart="$(pending_boot_restart_type)"
  if [ "$pending_restart" != "none" ] && [ "$pending_restart" != "$restart_type" ]; then
    log "Restart Manager: istniejący restart ${pending_restart} pozostaje osobnym żądaniem; nie zmieniam deklarowanego restartu wydania ${restart_type}."
  fi
  summary="$(release_summary)"
  reason="SBC5 Control Center został zaktualizowany z wersji ${previous} do ${APP_VERSION}."
  [ -n "$summary" ] && reason="${reason} ${summary}"

  if [ "$POST_UPDATE_RESTART_PROMPT" = "true" ] && [ "$restart_type" != "none" ]; then
    jq -n \
      --arg from_version "$previous" \
      --arg to_version "$APP_VERSION" \
      --arg restart_required "$restart_type" \
      --arg reason "$reason" \
      --arg boot_id "$CURRENT_BOOT_ID" \
      --arg created "$(date '+%Y-%m-%d %H:%M:%S')" \
      '{from_version:$from_version,to_version:$to_version,restart_required:$restart_required,reason:$reason,boot_id:$boot_id,core_went_down:false,created:$created}' \
      > "$POST_UPDATE_STATE_FILE"
    log "Post-update: wykryto zmianę wersji ${previous} -> ${APP_VERSION}; wymagany restart=${restart_type}."
  else
    rm -f "$POST_UPDATE_STATE_FILE"
    log "Post-update: wykryto zmianę wersji ${previous} -> ${APP_VERSION}; restart nie jest wymagany albo monit jest wyłączony."
  fi

  printf '%s\n' "$APP_VERSION" > "$LAST_APP_VERSION_FILE"
}

clear_completed_post_update_host_restart() {
  [ -r "$POST_UPDATE_STATE_FILE" ] || return 0
  local t saved_boot
  t="$(jq -r '.restart_required // "none"' "$POST_UPDATE_STATE_FILE" 2>/dev/null || echo none)"
  saved_boot="$(jq -r '.boot_id // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)"
  if [ "$t" = "host" ] && [ -n "$saved_boot" ] && [ "$saved_boot" != "$CURRENT_BOOT_ID" ]; then
    log "Post-update: wykryto pełny restart hosta — zamykam akcję po aktualizacji."
    rm -f "$POST_UPDATE_STATE_FILE"
  fi
}

core_api_available() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 1
  curl -fsS --connect-timeout 2 --max-time 4 \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    http://supervisor/core/api/ >/dev/null 2>&1
}

post_update_restart_monitor_loop() {
  local seen_up=false seen_down=false restart_type loaded_version
  while true; do
    if [ -r "$POST_UPDATE_STATE_FILE" ]; then
      restart_type="$(jq -r '.restart_required // "none"' "$POST_UPDATE_STATE_FILE" 2>/dev/null || echo none)"
      if [ "$restart_type" = "home_assistant" ]; then
        if core_api_available; then
          if [ "$seen_down" = "true" ]; then
            # 1.9.14: sam fakt powrotu Core nie oznacza zakończonej migracji.
            # Marker czyścimy dopiero, gdy canonical bridge jest faktycznie załadowany
            # i raportuje bieżącą wersję package.
            loaded_version="$(ha_get_state sensor.sbc5_package_version 2>/dev/null || true)"
            if [ "$loaded_version" = "$REQUIRED_PACKAGE_VERSION" ] && ha_service_exists sbc5_control_center set_restart_required; then
              log "Post-update: Home Assistant wrócił z aktywnym bridge ${REQUIRED_PACKAGE_VERSION} — migracja zakończona."
              rm -f "$POST_UPDATE_STATE_FILE"
              rm -f "$BRIDGE_BOOTSTRAP_MARKER" 2>/dev/null || true
              seen_down=false
              publish_restart_requirement false || true
            else
              log "Post-update: Home Assistant wrócił, ale canonical bridge nie jest jeszcze aktywny (package=${loaded_version:-missing}); pozostawiam wymagany restart."
              seen_down=false
            fi
          fi
          seen_up=true
        else
          if [ "$seen_up" = "true" ]; then
            seen_down=true
          fi
        fi
      else
        seen_up=false
        seen_down=false
      fi
    else
      seen_up=false
      seen_down=false
    fi
    sleep 5
  done
}


migrate_project_layout() {
  local changed=false
  # Recovery 1.9.14: NIE przenosimy katalogu źródłowego uruchomionej Local App.
  # Supervisor identyfikuje aplikację po slug local_sbc5_control_center, a samoczynne
  # przeniesienie źródeł podczas pracy mogło przerwać rebuild w migracji 1.9.11.
  # Katalog /local_apps/sbc5_fan_manager pozostaje wyłącznie ścieżką zgodności
  # dla istniejącej instalacji; wszystkie dane runtime mają już nazwę Control Center.
  # State and update directories.
  if [ -d /homeassistant/sbc5_fan_manager ] && [ ! -e /homeassistant/sbc5_control_center ]; then
    mv /homeassistant/sbc5_fan_manager /homeassistant/sbc5_control_center 2>/dev/null || true
  fi
  # 2.6.21 namespace migration: public/local update path now uses the SBC5 brand.
  # Both earlier generations are imported into the new canonical directory. Existing
  # destination files always win, and the runtime still scans the legacy directory.
  mkdir -p "$LOCAL_UPDATE_DIR" "$LOCAL_UPDATE_PROCESSED_DIR" "$LOCAL_UPDATE_FAILED_DIR" 2>/dev/null || true
  for old_update_dir in "$LEGACY_LOCAL_UPDATE_DIR" "$LEGACY_OLD_LOCAL_UPDATE_DIR"; do
    [ -d "$old_update_dir" ] || continue
    for f in "$old_update_dir"/*.zip; do
      [ -f "$f" ] || continue
      dst="$LOCAL_UPDATE_DIR/$(basename "$f")"
      [ -e "$dst" ] || mv "$f" "$dst" 2>/dev/null || true
    done
    for sub in processed failed; do
      [ -d "$old_update_dir/$sub" ] || continue
      for f in "$old_update_dir/$sub"/*.zip; do
        [ -f "$f" ] || continue
        dst="$LOCAL_UPDATE_DIR/$sub/$(basename "$f")"
        [ -e "$dst" ] || mv "$f" "$dst" 2>/dev/null || true
      done
    done
    # Remove empty legacy update folders after a successful import. Non-ZIP
    # user files keep the directory intact and are never deleted.
    rmdir "$old_update_dir/processed" "$old_update_dir/failed" 2>/dev/null || true
    rmdir "$old_update_dir" 2>/dev/null || true
  done
  # Package file is renamed, content is delivered inside the app for legacy-updater migration.
  if [ -f /migration_assets/sbc5_control_center.yaml ]; then
    mkdir -p /homeassistant/packages
    if [ ! -f /homeassistant/packages/sbc5_control_center.yaml ] || ! cmp -s /migration_assets/sbc5_control_center.yaml /homeassistant/packages/sbc5_control_center.yaml; then
      cp -f /migration_assets/sbc5_control_center.yaml /homeassistant/packages/sbc5_control_center.yaml 2>/dev/null || true
      changed=true
    fi
    rm -f /homeassistant/packages/sbc5_fan.yaml 2>/dev/null || true
  fi
  rm -f /homeassistant/packages/sbc5_fan_manager_bridge.yaml 2>/dev/null || true
  if [ "$changed" = "true" ] && [ -n "${SUPERVISOR_TOKEN:-}" ]; then
    curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d '{}' \
      http://supervisor/addons/reload >/tmp/rpi5cc_layout_reload.json 2>&1 || true
  fi
}

namespace_migration_phase() {
  jq -r '.phase // empty' "$NAMESPACE_MIGRATION_DIR/state.json" 2>/dev/null || true
}

namespace_migration_complete() {
  [ "$(namespace_migration_phase)" = "COMPLETE" ]
}

ensure_legacy_bridge_shim_installed() {
  # Compatibility bridge jest dozwolony wyłącznie podczas niedokończonej migracji.
  # Po finalnym cutoverze nie może odtwarzać legacy custom_component przy restarcie.
  if namespace_migration_complete; then
    if [ -d "$LEGACY_BRIDGE_DEST_DIR" ]; then
      rm -rf "$LEGACY_BRIDGE_DEST_DIR" 2>/dev/null || true
      log "Universal Recovery: migracja COMPLETE — usunięto pozostały sbc5_fan_manager_bridge; ponowna instalacja zablokowana."
    fi
    return 0
  fi
  [ -f "$LEGACY_BRIDGE_MIGRATION_MARKER" ] && return 0
  [ -d "$LEGACY_BRIDGE_SOURCE_DIR" ] || return 0
  [ -d /homeassistant/custom_components ] || mkdir -p /homeassistant/custom_components 2>/dev/null || return 0

  local src_ver="" dst_ver="" tmp="${LEGACY_BRIDGE_DEST_DIR}.new.$$"
  src_ver="$(jq -r '.version // empty' "$LEGACY_BRIDGE_SOURCE_DIR/manifest.json" 2>/dev/null || true)"
  dst_ver="$(jq -r '.version // empty' "$LEGACY_BRIDGE_DEST_DIR/manifest.json" 2>/dev/null || true)"
  if [ -n "$src_ver" ] && [ "$src_ver" = "$dst_ver" ] && [ -f "$LEGACY_BRIDGE_DEST_DIR/config_flow.py" ]; then
    return 0
  fi

  rm -rf "$tmp"
  cp -a "$LEGACY_BRIDGE_SOURCE_DIR" "$tmp" 2>/dev/null || { rm -rf "$tmp"; return 0; }
  rm -rf "${LEGACY_BRIDGE_DEST_DIR}.old"
  [ -d "$LEGACY_BRIDGE_DEST_DIR" ] && mv "$LEGACY_BRIDGE_DEST_DIR" "${LEGACY_BRIDGE_DEST_DIR}.old" 2>/dev/null || true
  mv "$tmp" "$LEGACY_BRIDGE_DEST_DIR" 2>/dev/null || {
    [ -d "${LEGACY_BRIDGE_DEST_DIR}.old" ] && mv "${LEGACY_BRIDGE_DEST_DIR}.old" "$LEGACY_BRIDGE_DEST_DIR" 2>/dev/null || true
    return 0
  }
  rm -rf "${LEGACY_BRIDGE_DEST_DIR}.old"
  log "Universal Recovery: zainstalowano compatibility bridge sbc5_fan_manager_bridge ${src_ver:-?} z config_flow.py."
}

cleanup_legacy_bridge_if_migrated() {
  # Stary bridge usuwamy dopiero po potwierdzeniu przez nową integrację, że
  # legacy config entry został bezpiecznie usunięty z Home Assistant.
  if ! namespace_migration_complete && [ ! -f "$LEGACY_BRIDGE_MIGRATION_MARKER" ]; then return 0; fi
  if [ -d "$LEGACY_BRIDGE_DEST_DIR" ]; then
    rm -rf "$LEGACY_BRIDGE_DEST_DIR" 2>/dev/null || return 0
    log "Universal Recovery: usunięto stary custom_components/sbc5_fan_manager_bridge po bezpiecznej migracji wpisu."
  fi
}

ensure_runtime_directories() {
  # Only canonical runtime directories are created. Legacy update aliases are
  # scanned/migrated when they already exist, but are not recreated forever.
  mkdir -p "$LOCAL_UPDATE_DIR" "$LOCAL_UPDATE_PROCESSED_DIR" "$LOCAL_UPDATE_FAILED_DIR" \
    /homeassistant/sbc5_control_center /data/update_backups "$UI_OVERRIDE_DIR" "$UI_MANUAL_DIR" 2>/dev/null || true
}

release_card_ui_version() {
  # 2.8.12+: App version and Card UI version are one release identity.
  printf '%s\n' "$APP_VERSION"
}

current_card_ui_version() {
  local v=""
  if [ -r "$CARD_UI_VERSION_FILE" ]; then
    v="$(tr -d '\r\n' < "$CARD_UI_VERSION_FILE" 2>/dev/null || true)"
  fi
  [ -n "$v" ] || v="$APP_VERSION"
  printf '%s\n' "$v"
}

ensure_card_ui_override_state() {
  local current tmp
  current="$(current_card_ui_version)"
  mkdir -p "$UI_OVERRIDE_DIR" "$UI_MANUAL_DIR" 2>/dev/null || true

  # Any independent UI override with a different version would violate unified
  # release versioning. The packaged card for APP_VERSION becomes source of truth.
  if [ "$current" != "$APP_VERSION" ] || [ -f "$UI_DASHBOARD_CARD_FILE" ] || [ -f "$UI_UPDATE_STATUS_CARD_FILE" ]; then
    rm -f "$UI_DASHBOARD_CARD_FILE" "$UI_UPDATE_STATUS_CARD_FILE" 2>/dev/null || true
    tmp="${CARD_UI_VERSION_FILE}.tmp"
    printf '%s\n' "$APP_VERSION" > "$tmp" 2>/dev/null && mv -f "$tmp" "$CARD_UI_VERSION_FILE" || true
    log "Card UI: unified release ${APP_VERSION}; usunięto niezależny override ${current:-brak}."
  elif [ ! -r "$CARD_UI_VERSION_FILE" ]; then
    printf '%s\n' "$APP_VERSION" > "$CARD_UI_VERSION_FILE" 2>/dev/null || true
  fi
}

# After a full build, try to align the single stored Lovelace card with the packaged
# card. dashboard_sync.py already creates a backup and refuses ambiguous multi-card cases.
schedule_unified_dashboard_sync() {
  (
    local attempt=0 result=""
    while [ "$attempt" -lt 6 ]; do
      attempt=$((attempt + 1))
      sleep 10
      result="$(SBC5CC_APP_VERSION="$APP_VERSION" python3 /dashboard_sync.py sync --confirm 2>&1 || true)"
      if printf '%s' "$result" | grep -q '"ok": true'; then
        log "Card UI: dashboard zsynchronizowany automatycznie do buildu ${APP_VERSION}."
        return 0
      fi
      # No card / multiple cards are deterministic safety stops, not transient HA startup errors.
      if printf '%s' "$result" | grep -Eq 'Nie znaleziono karty|Znaleziono [0-9]+ kart projektu'; then
        log "Card UI: automatyczna synchronizacja pominięta: ${result//$'\n'/ }."
        return 0
      fi
    done
    log "Card UI: automatyczna synchronizacja do ${APP_VERSION} nie powiodła się po ${attempt} próbach; można użyć ręcznej synchronizacji karty."
  ) &
}


ensure_native_bridge_installed() {
  # Od 1.6 bridge jest pełną, wymaganą integracją telemetrii/update.
  # Opcja native_restart_repair steruje wyłącznie tworzeniem zgłoszeń Repairs.
  [ -d "$BRIDGE_SOURCE_DIR" ] || return 0
  [ -d /homeassistant ] || return 0

  local src_ver="" dst_ver=""
  src_ver="$(jq -r '.version // empty' "$BRIDGE_SOURCE_DIR/manifest.json" 2>/dev/null || true)"
  dst_ver="$(jq -r '.version // empty' "$BRIDGE_DEST_DIR/manifest.json" 2>/dev/null || true)"

  # Public distribution model: when the canonical bridge was installed by
  # HACS/Marketplace, custom_components belongs to that package manager.
  # The app keeps its bundled bridge only as a bootstrap/fallback and must not
  # race with or downgrade the externally managed integration.
  if [ -f "$BRIDGE_EXTERNAL_MARKER" ] && [ -f "$BRIDGE_DEST_DIR/manifest.json" ]; then
    log "Bridge Ownership: HACS/Marketplace zarządza sbc5_control_center (${dst_ver:-?}); aplikacja nie nadpisuje custom_components."
    if [ -n "$src_ver" ] && [ -n "$dst_ver" ] && [ "$src_ver" != "$dst_ver" ]; then
      log "Bridge Ownership: bridge=${dst_ver}, pakiet aplikacji=${src_ver}; aktualizuj bridge przez HACS/Marketplace."
    fi
    return 0
  fi

  if [ -n "$src_ver" ] && [ "$src_ver" = "$dst_ver" ]; then
    return 0
  fi

  local tmp="${BRIDGE_DEST_DIR}.new.$$"
  rm -rf "$tmp"
  mkdir -p "$(dirname "$BRIDGE_DEST_DIR")"
  cp -a "$BRIDGE_SOURCE_DIR" "$tmp" || { rm -rf "$tmp"; return 1; }
  rm -rf "${BRIDGE_DEST_DIR}.old"
  if [ -d "$BRIDGE_DEST_DIR" ]; then mv "$BRIDGE_DEST_DIR" "${BRIDGE_DEST_DIR}.old" || true; fi
  mv "$tmp" "$BRIDGE_DEST_DIR" || return 1
  rm -rf "${BRIDGE_DEST_DIR}.old"
  log "Zainstalowano/odświeżono integrację SBC5 Control Center sbc5_control_center (${src_ver:-?})."
}


ha_service_exists() {
  local domain="$1" service="$2"
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 1
  curl -fsS     -H "Authorization: Bearer ${SUPERVISOR_TOKEN}"     http://supervisor/core/api/services 2>/dev/null |     jq -e --arg d "$domain" --arg s "$service"       'any(.[]; .domain == $d and (.services | type == "object") and (.services | has($s)))'       >/dev/null 2>&1
}

stage_bridge_package_for_restart() {
  # Package bootstrap jest wymagany dla natywnej integracji niezależnie od
  # ustawienia powiadomień Repairs. Od 1.9.14 po przygotowaniu NIE jest wycofywany
  # przy zerwanym połączeniu z Core: podczas prawidłowego restartu zerwanie HTTP
  # jest normalnym skutkiem zatrzymania Home Assistant.
  [ -f "$BRIDGE_DEST_DIR/manifest.json" ] || {
    log "Bridge Bootstrap: brak plików integracji — nie mogę przygotować package do restartu."
    return 1
  }
  [ -f "$BRIDGE_PACKAGE_TEMPLATE" ] || return 1
  mkdir -p "$(dirname "$BRIDGE_PACKAGE_DEST")"
  cp -f "$BRIDGE_PACKAGE_TEMPLATE" "$BRIDGE_PACKAGE_DEST" || return 1
  printf '%s\n' "$APP_VERSION" > "$BRIDGE_BOOTSTRAP_MARKER" 2>/dev/null || true
  log "Bridge Bootstrap: package przygotowany i pozostanie aktywny do skutecznego załadowania canonical bridge."
}

ensure_bridge_package_installed() {
  # v1.6.1: bezpieczny bootstrap dwuetapowy + natywne platformy encji.
  # Home Assistant nie skanuje nowo skopiowanych custom_components w działającym procesie,
  # więc package nie może istnieć zanim integracja została rozpoznana przy starcie Core.
  # Od 1.6 package jest potrzebny do bootstrapu natywnej integracji również wtedy,
  # gdy użytkownik wyłączył same zgłoszenia Repairs.

  [ -f "$BRIDGE_DEST_DIR/manifest.json" ] || {
    rm -f "$BRIDGE_PACKAGE_DEST" 2>/dev/null || true
    log "Bridge Repairs: pliki integracji nie są jeszcze zainstalowane — package bootstrap usunięty."
    return 1
  }

  if ha_service_exists sbc5_control_center set_restart_required; then
    [ -f "$BRIDGE_PACKAGE_TEMPLATE" ] || return 1
    mkdir -p "$(dirname "$BRIDGE_PACKAGE_DEST")"
    if ! cmp -s "$BRIDGE_PACKAGE_TEMPLATE" "$BRIDGE_PACKAGE_DEST" 2>/dev/null; then
      cp -f "$BRIDGE_PACKAGE_TEMPLATE" "$BRIDGE_PACKAGE_DEST" || return 1
    fi
    rm -f "$BRIDGE_BOOTSTRAP_MARKER" 2>/dev/null || true
    log "Bridge Repairs: integracja jest aktywna; package pozostaje włączony."
    return 0
  fi

  # Integracja jest już na dysku, ale bieżący proces HA jej jeszcze nie zna.
  # Jeśli package został już przygotowany do migracji/restartu, pozostawiamy go.
  # Jest potrzebny przy NASTĘPNYM starcie Core. Usunięcie go po timeoutcie było
  # przyczyną pętli 1.9.11-1.9.13, w której HA restartował się bez bootstrapu bridge.
  if [ -f "$BRIDGE_PACKAGE_DEST" ] && [ -f "$BRIDGE_BOOTSTRAP_MARKER" ]; then
    log "Bridge Bootstrap: package oczekuje na restart HA — pozostawiam go aktywny."
    return 0
  fi

  # Przed pierwszym świadomym restartem package nie jest aktywowany automatycznie,
  # aby bieżący proces HA nie walidował świeżo skopiowanej integracji z cache loadera.
  return 0
}

native_restart_repair_set() {
  local restart_type="$1" reason="$2" from_version="${3:-}" to_version="${4:-$APP_VERSION}"
  [ "$NATIVE_RESTART_REPAIR" = "true" ] || return 0
  [ "$restart_type" != "none" ] || return 0

  local signature previous_signature=""
  signature="$(printf '%s\n%s\n%s\n%s' "$restart_type" "$reason" "$from_version" "$to_version" | sha256sum | awk '{print $1}')"
  if [ -r "$NATIVE_REPAIR_POSTED_FILE" ]; then
    previous_signature="$(jq -r '.signature // empty' "$NATIVE_REPAIR_POSTED_FILE" 2>/dev/null || true)"
  fi

  # Marker na dysku jest źródłem prawdy dla restartu Core: canonical bridge
  # odtworzy z niego Repair przy następnym starcie Home Assistant.
  mkdir -p "$(dirname "$NATIVE_RESTART_MARKER")" 2>/dev/null || true
  if [ "$signature" != "$previous_signature" ] || [ ! -r "$NATIVE_RESTART_MARKER" ]; then
    jq -n \
      --arg type "$restart_type" \
      --arg reason "$reason" \
      --arg from_version "$from_version" \
      --arg to_version "$to_version" \
      --arg created "$(date '+%Y-%m-%d %H:%M:%S')" \
      '{type:$type,reason:$reason,from_version:$from_version,to_version:$to_version,created:$created}' \
      > "$NATIVE_RESTART_MARKER" 2>/dev/null || true
  fi

  # Identyczne zgłoszenie już wysłane do bieżącego Core — nie duplikuj go.
  [ "$signature" != "$previous_signature" ] || return 0
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0

  local payload code endpoint
  payload="$(jq -cn --arg type "$restart_type" --arg reason "$reason" --arg from_version "$from_version" --arg to_version "$to_version" '{type:$type,reason:$reason,from_version:$from_version,to_version:$to_version}')"

  # Od 1.9.11 źródłem Repairs jest canonical domain. Wcześniej kod omyłkowo
  # wysyłał usługę do compatibility bridge, który nie rejestruje tych usług.
  endpoint="http://supervisor/core/api/services/sbc5_control_center/set_restart_required"
  code="$(curl -sS -o /tmp/sbc5_bridge_set.json -w '%{http_code}' -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$payload" "$endpoint" 2>/dev/null || echo 000)"

  # Fallback wyłącznie dla instalacji będących jeszcze w trakcie migracji.
  if ! [[ "$code" =~ ^2 ]]; then
    endpoint="http://supervisor/core/api/services/sbc5_fan_manager_bridge/set_restart_required"
    code="$(curl -sS -o /tmp/sbc5_bridge_set_legacy.json -w '%{http_code}' -X POST \
      -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$payload" "$endpoint" 2>/dev/null || echo 000)"
  fi

  case "$code" in
    2??)
      jq -n --arg signature "$signature" --arg type "$restart_type" --arg to_version "$to_version" \
        '{signature:$signature,type:$type,to_version:$to_version}' > "$NATIVE_REPAIR_POSTED_FILE" 2>/dev/null || true
      log "Restart Manager: zgłoszenie Repairs zsynchronizowane z Home Assistant (restart=${restart_type})."
      ;;
    *)
      # Marker pozostaje na dysku; kolejna iteracja spróbuje ponownie, a po
      # restarcie canonical bridge sam odtworzy Repair z pliku.
      log "Restart Manager: nie udało się zsynchronizować Repairs z bieżącym Core (HTTP ${code}); marker pozostaje aktywny."
      ;;
  esac
}

native_restart_repair_clear() {
  # Najpierw usuń trwały marker, aby kolejny start HA nie odtworzył starego Repair.
  rm -f "$NATIVE_RESTART_MARKER" 2>/dev/null || true

  if [ "$NATIVE_RESTART_REPAIR" != "true" ]; then
    rm -f "$NATIVE_REPAIR_POSTED_FILE" 2>/dev/null || true
    return 0
  fi
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 1

  local code endpoint
  endpoint="http://supervisor/core/api/services/sbc5_control_center/clear_restart_required"
  code="$(curl -sS -o /tmp/sbc5_bridge_clear.json -w '%{http_code}' -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{}' "$endpoint" 2>/dev/null || echo 000)"

  # Fallback dla starszego bridge podczas migracji.
  if ! [[ "$code" =~ ^2 ]]; then
    endpoint="http://supervisor/core/api/services/sbc5_fan_manager_bridge/clear_restart_required"
    code="$(curl -sS -o /tmp/sbc5_bridge_clear_legacy.json -w '%{http_code}' -X POST \
      -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{}' "$endpoint" 2>/dev/null || echo 000)"
  fi

  case "$code" in
    2??)
      rm -f "$NATIVE_REPAIR_POSTED_FILE" 2>/dev/null || true
      log "Restart Manager: wyczyszczono zakończone zgłoszenie Repairs."
      return 0
      ;;
    *)
      # Nie kasuj pliku posted: jest znacznikiem, że cleanup trzeba ponowić.
      # Jeżeli naprawiamy stary, osierocony Repair i pliku jeszcze nie było,
      # utwórz jawny znacznik cleanup_pending, aby następna iteracja retry nie zniknęła.
      if [ ! -r "$NATIVE_REPAIR_POSTED_FILE" ]; then
        jq -n --arg created "$(date '+%Y-%m-%d %H:%M:%S')" \
          '{cleanup_pending:true,created:$created}' > "$NATIVE_REPAIR_POSTED_FILE" 2>/dev/null || true
      fi
      log "Restart Manager: Repair jest już nieaktualny, ale Core nie przyjął operacji clear (HTTP ${code}); ponowię próbę."
      return 1
      ;;
  esac
}

zip_has_unsafe_paths() {
  local zip="$1"
  unzip -Z1 "$zip" 2>/dev/null | awk '
    /^\// {bad=1}
    /(^|\/)\.\.($|\/)/ {bad=1}
    END {exit bad ? 0 : 1}
  '
}

scan_local_update_candidate() {
  rm -f "$LOCAL_UPDATE_CANDIDATE_FILE"
  [ "$LOCAL_PACKAGE_UPDATES_ENABLED" = "true" ] || return 1
  ensure_runtime_directories

  local zip manifest_entry manifest root version slug target_slug restart summary release_date scope card_ui app_compat current_card
  local best_version="" best_zip="" best_manifest="" best_root="" best_restart="" best_summary="" best_date="" best_scope="" best_card=""
  local update_dir eligible=false
  current_card="$(current_card_ui_version)"
  shopt -s nullglob
  for update_dir in "$LOCAL_UPDATE_DIR" "$LEGACY_LOCAL_UPDATE_DIR" "$LEGACY_OLD_LOCAL_UPDATE_DIR"; do
    for zip in "$update_dir"/*.zip; do
      manifest_entry="$(unzip -Z1 "$zip" 2>/dev/null | awk '/(^|\/)update-manifest\.json$/ {print; exit}')"
      [ -n "$manifest_entry" ] || continue
      manifest="$(unzip -p "$zip" "$manifest_entry" 2>/dev/null || true)"
      [ -n "$manifest" ] || continue
      version="$(printf '%s' "$manifest" | jq -r '.version // empty' 2>/dev/null || true)"
      slug="$(printf '%s' "$manifest" | jq -r '.slug // empty' 2>/dev/null || true)"
      target_slug="$(printf '%s' "$manifest" | jq -r '.target_slug // empty' 2>/dev/null || true)"
      scope="$(printf '%s' "$manifest" | jq -r '.update_scope // "full"' 2>/dev/null || echo full)"
      card_ui="$(printf '%s' "$manifest" | jq -r '.card_ui_version // .version // empty' 2>/dev/null || true)"
      app_compat="$(printf '%s' "$manifest" | jq -r '.app_version // empty' 2>/dev/null || true)"
      restart="$(printf '%s' "$manifest" | jq -r '.restart_required // "home_assistant"' 2>/dev/null || echo home_assistant)"
      summary="$(printf '%s' "$manifest" | jq -r '.summary // empty' 2>/dev/null || true)"
      release_date="$(printf '%s' "$manifest" | jq -r '.release_date // empty' 2>/dev/null || true)"

      # Accept the final canonical SBC5 package identity; keep transition identity only for migration compatibility.
      { [ "$slug" = "sbc5_control_center" ] && { [ -z "$target_slug" ] || [ "$target_slug" = "sbc5_control_center" ]; }; } || \
      { [ "$slug" = "rpi5_fan_manager" ] && [ "$target_slug" = "sbc5_control_center" ]; } || continue

      eligible=false
      case "$scope" in
        dashboard_only|ui_only)
          # 2.8.12+: public releases use one build version. Separate UI releases are ignored
          # to guarantee App/Card UI version consistency.
          continue
          ;;
        full|"")
          version_gt "$version" "$APP_VERSION" || continue
          scope="full"
          eligible=true
          ;;
        *)
          continue
          ;;
      esac
      [ "$eligible" = "true" ] || continue

      if [ -z "$best_version" ] || version_gt "$version" "$best_version" || \
         { [ "$version" = "$best_version" ] && [ "$scope" = "full" ] && [ "$best_scope" != "full" ]; }; then
        root="${manifest_entry%update-manifest.json}"
        best_version="$version"; best_zip="$zip"; best_manifest="$manifest_entry"; best_root="$root"
        best_restart="$restart"; best_summary="$summary"; best_date="$release_date"; best_scope="$scope"; best_card="$card_ui"
      fi
    done
  done
  shopt -u nullglob

  [ -n "$best_zip" ] || return 1
  jq -n \
    --arg version "$best_version" --arg zip "$best_zip" --arg manifest "$best_manifest" --arg root "$best_root" \
    --arg restart_required "$best_restart" --arg summary "$best_summary" --arg release_date "$best_date" \
    --arg update_scope "$best_scope" --arg card_ui_version "$best_card" \
    '{version:$version,zip:$zip,manifest_entry:$manifest,root:$root,restart_required:$restart_required,summary:$summary,release_date:$release_date,update_scope:$update_scope,card_ui_version:$card_ui_version}' \
    > "$LOCAL_UPDATE_CANDIDATE_FILE"
  return 0
}

verify_local_update_package() {
  local zip="$1" stage="$2" root="$3" manifest_file="$4"
  zip_has_unsafe_paths "$zip" && { log "BŁĄD aktualizacji: paczka zawiera niedozwolone ścieżki."; return 1; }
  find "$stage" -type l -print -quit | grep -q . && { log "BŁĄD aktualizacji: paczka zawiera dowiązania symboliczne."; return 1; }

  local expected_version package_version slug target_slug scope restart card_ui app_compat
  expected_version="$(jq -r '.version // empty' "$manifest_file" 2>/dev/null || true)"
  package_version="$(jq -r '.package_version // .version // empty' "$manifest_file" 2>/dev/null || true)"
  slug="$(jq -r '.slug // empty' "$manifest_file" 2>/dev/null || true)"
  target_slug="$(jq -r '.target_slug // empty' "$manifest_file" 2>/dev/null || true)"
  scope="$(jq -r '.update_scope // "full"' "$manifest_file" 2>/dev/null || echo full)"
  restart="$(jq -r '.restart_required // "home_assistant"' "$manifest_file" 2>/dev/null || echo home_assistant)"
  card_ui="$(jq -r '.card_ui_version // .version // empty' "$manifest_file" 2>/dev/null || true)"
  app_compat="$(jq -r '.app_version // empty' "$manifest_file" 2>/dev/null || true)"

  if ! { { [ "$slug" = "sbc5_control_center" ] && { [ -z "$target_slug" ] || [ "$target_slug" = "sbc5_control_center" ]; }; } || \
           { [ "$slug" = "rpi5_fan_manager" ] && [ "$target_slug" = "sbc5_control_center" ]; }; }; then
    log "BŁĄD aktualizacji: nieobsługiwana tożsamość paczki slug=${slug}, target_slug=${target_slug}."; return 1
  fi
  case "$restart" in none|home_assistant|host) ;; *) log "BŁĄD aktualizacji: nieznany restart_required=${restart}."; return 1 ;; esac
  verify_release_platform_requirements "$manifest_file" || return 1

  # Weryfikacja SHA-256 wszystkich plików wymienionych w manifeście.
  local rel expected actual
  while IFS=$'\t' read -r rel expected; do
    [ -n "$rel" ] || continue
    [ -f "${stage}/${root}${rel}" ] || { log "BŁĄD aktualizacji: brakuje ${rel}."; return 1; }
    actual="$(sha256sum "${stage}/${root}${rel}" | awk '{print $1}')"
    [ "$actual" = "$expected" ] || { log "BŁĄD aktualizacji: suma SHA-256 nie zgadza się dla ${rel}."; return 1; }
  done < <(jq -r '.files // {} | to_entries[] | [.key,.value] | @tsv' "$manifest_file" 2>/dev/null)

  case "$scope" in
    dashboard_only|ui_only)
      log "BŁĄD aktualizacji: od 2.8.12 obowiązuje unified release versioning; poprawki kart muszą być wydane jako pełny build z tym samym numerem App/Card UI."
      return 1
      ;;
    full|"")
      ;;
    *)
      log "BŁĄD aktualizacji: nieobsługiwany update_scope=${scope}."; return 1
      ;;
  esac

  [ -n "$expected_version" ] && [ "$package_version" = "$expected_version" ] && [ "$card_ui" = "$expected_version" ] || {
    log "BŁĄD aktualizacji: unified version mismatch (version=${expected_version:-brak}, package_version=${package_version:-brak}, card_ui_version=${card_ui:-brak})."
    return 1
  }

  local app_dir="${stage}/${root}local_apps/sbc5_control_center"
  local pkg="${stage}/${root}packages/sbc5_control_center.yaml"
  [ -f "$app_dir/config.yaml" ] && [ -f "$app_dir/run.sh" ] && [ -f "$pkg" ] || {
    log "BŁĄD aktualizacji: brak wymaganych plików aplikacji/package."; return 1;
  }
  local actual_version run_version run_required
  actual_version="$(sed -n 's/^version:[[:space:]]*["'\'' ]*\([^"'\'' ]*\).*/\1/p' "$app_dir/config.yaml" | head -n1)"
  run_version="$(sed -n 's/^APP_VERSION="\([^"]*\)"$/\1/p' "$app_dir/run.sh" | head -n1)"
  run_required="$(sed -n 's/^REQUIRED_PACKAGE_VERSION="\([^"]*\)"$/\1/p' "$app_dir/run.sh" | head -n1)"
  if grep -qE '^APP_VERSION[[:space:]]+=' "$app_dir/run.sh"; then
    log "BŁĄD aktualizacji: run.sh zawiera niepoprawne przypisanie APP_VERSION ze spacją przed '='."; return 1
  fi
  bash -n "$app_dir/run.sh" || { log "BŁĄD aktualizacji: run.sh nie przechodzi kontroli składni."; return 1; }
  [ "$run_version" = "$expected_version" ] && [ "$run_required" = "$expected_version" ] || {
    log "BŁĄD aktualizacji: metadane run.sh nie zgadzają się z manifestem (APP_VERSION=${run_version:-brak}, REQUIRED_PACKAGE_VERSION=${run_required:-brak}, manifest=${expected_version})."; return 1;
  }
  [ -n "$expected_version" ] && [ "$actual_version" = "$expected_version" ] || {
    log "BŁĄD aktualizacji: wersja paczki nie zgadza się z manifestem (${actual_version} vs ${expected_version})."; return 1;
  }
  return 0
}


cleanup_local_update_archive_dir() {
  local dir="$1" keep="$2" label="$3" reason="$4"
  mkdir -p "$dir" 2>/dev/null || return 0
  case "$keep" in ''|*[!0-9]*) keep=2 ;; esac
  [ "$keep" -ge 0 ] 2>/dev/null || keep=0
  local files=() f i size deleted=0 freed=0
  shopt -s nullglob
  files=("$dir"/*.zip)
  shopt -u nullglob
  [ "${#files[@]}" -gt "$keep" ] || return 0
  # Sortuj po mtime malejąco; nazwy paczek projektu nie zawierają znaków nowej linii.
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    files[$deleted]="$f"
    deleted=$((deleted + 1))
  done < <(printf '%s\n' "${files[@]}" | while IFS= read -r f; do printf '%s\t%s\n' "$(stat -c '%Y' "$f" 2>/dev/null || echo 0)" "$f"; done | sort -rn | cut -f2-)
  local total="$deleted"; deleted=0; freed=0
  for ((i=keep; i<total; i++)); do
    f="${files[$i]}"; [ -f "$f" ] || continue
    size="$(stat -c '%s' "$f" 2>/dev/null || echo 0)"
    case "$size" in ''|*[!0-9]*) size=0 ;; esac
    if rm -f -- "$f"; then deleted=$((deleted + 1)); freed=$((freed + size)); fi
  done
  if [ "$deleted" -gt 0 ]; then
    log "Update Cleanup: ${label} — usunięto ${deleted} starych ZIP, zwolniono $((freed / 1024)) KiB; retencja=${keep}; trigger=${reason}."
  fi
}

cleanup_local_update_archives() {
  local reason="${1:-runtime}" processed_keep
  [ "$LOCAL_PACKAGE_CLEANUP_ENABLED" = "true" ] || return 0
  processed_keep="$LOCAL_PACKAGE_PROCESSED_RETENTION"
  [ "$LOCAL_PACKAGE_KEEP_PROCESSED" = "true" ] || processed_keep=0
  cleanup_local_update_archive_dir "$LOCAL_UPDATE_PROCESSED_DIR" "$processed_keep" processed "$reason"
  cleanup_local_update_archive_dir "$LOCAL_UPDATE_FAILED_DIR" "$LOCAL_PACKAGE_FAILED_RETENTION" failed "$reason"
}

archive_completed_local_update_zip() {
  local zip="$1"
  [ -n "$zip" ] && [ -f "$zip" ] || return 0
  if [ "$LOCAL_PACKAGE_KEEP_PROCESSED" = "true" ]; then
    mkdir -p "$LOCAL_UPDATE_PROCESSED_DIR"
    local processed_zip="$LOCAL_UPDATE_PROCESSED_DIR/$(basename "$zip")"
    mv -f "$zip" "$processed_zip" 2>/dev/null || { cp -f "$zip" "$processed_zip" 2>/dev/null || true; rm -f "$zip" 2>/dev/null || true; }
    touch "$processed_zip" 2>/dev/null || true
  else
    rm -f "$zip" 2>/dev/null || true
  fi
}

install_dashboard_only_update() {
  local zip="$1" version="$2" stage="$3" root="$4" manifest_file="$5"
  local card_ui current_ui ts backup diag_json update_json diag_yaml update_yaml tmp sync_result completed_at
  card_ui="$(jq -r '.card_ui_version // .version // empty' "$manifest_file" 2>/dev/null || true)"
  current_ui="$(current_card_ui_version)"
  diag_json="$(jq -r '.ui_assets.diagnostics_json // "ui/dashboard_card.json"' "$manifest_file" 2>/dev/null || true)"
  update_json="$(jq -r '.ui_assets.update_status_json // "ui/update_status_card.json"' "$manifest_file" 2>/dev/null || true)"
  diag_yaml="$(jq -r '.ui_assets.diagnostics_yaml // "dashboard/sbc5_control_center_diagnostics_card.yaml"' "$manifest_file" 2>/dev/null || true)"
  update_yaml="$(jq -r '.ui_assets.update_status_yaml // "dashboard/update_status_card.yaml"' "$manifest_file" 2>/dev/null || true)"

  ts="$(date '+%Y%m%d_%H%M%S')"
  backup="/data/update_backups/card_ui_${current_ui}_to_${card_ui}_${ts}"
  mkdir -p "$backup" "$UI_OVERRIDE_DIR" "$UI_MANUAL_DIR"
  [ -f "$UI_DASHBOARD_CARD_FILE" ] && cp -a "$UI_DASHBOARD_CARD_FILE" "$backup/dashboard_card.json" || true
  [ -f "$UI_UPDATE_STATUS_CARD_FILE" ] && cp -a "$UI_UPDATE_STATUS_CARD_FILE" "$backup/update_status_card.json" || true
  [ -f "$CARD_UI_VERSION_FILE" ] && cp -a "$CARD_UI_VERSION_FILE" "$backup/card_ui_version" || true
  cp -a "$manifest_file" "$backup/update-manifest.json" || true

  tmp="${UI_DASHBOARD_CARD_FILE}.tmp"
  cp -f "${stage}/${root}${diag_json}" "$tmp" && mv -f "$tmp" "$UI_DASHBOARD_CARD_FILE" || {
    log "BŁĄD aktualizacji UI: nie udało się zapisać wzorca dashboardu."; return 1;
  }
  if [ -n "$update_json" ] && [ -f "${stage}/${root}${update_json}" ]; then
    tmp="${UI_UPDATE_STATUS_CARD_FILE}.tmp"
    cp -f "${stage}/${root}${update_json}" "$tmp" && mv -f "$tmp" "$UI_UPDATE_STATUS_CARD_FILE" || true
  fi
  [ -n "$diag_yaml" ] && [ -f "${stage}/${root}${diag_yaml}" ] && cp -f "${stage}/${root}${diag_yaml}" "$UI_MANUAL_DIR/sbc5_control_center_diagnostics_card.yaml" || true
  [ -n "$update_yaml" ] && [ -f "${stage}/${root}${update_yaml}" ] && cp -f "${stage}/${root}${update_yaml}" "$UI_MANUAL_DIR/update_status_card.yaml" || true

  tmp="${CARD_UI_VERSION_FILE}.tmp"
  printf '%s\n' "$card_ui" > "$tmp" && mv -f "$tmp" "$CARD_UI_VERSION_FILE" || return 1
  sync

  # Storage-mode Lovelace can be updated live. A failed/ambiguous sync does not
  # roll back the installed template; the user can synchronize it later from the UI.
  if python3 /dashboard_sync.py sync --confirm >/tmp/sbc5_dashboard_ui_update.json 2>&1; then
    sync_result="synced_live"
    log "Aktualizacja UI ${current_ui} -> ${card_ui}: karta Lovelace zsynchronizowana na żywo; restart nie jest wymagany."
  else
    sync_result="template_installed_sync_pending"
    log "Aktualizacja UI ${current_ui} -> ${card_ui}: wzorzec zainstalowany bez restartu; automatyczna synchronizacja dashboardu nie była możliwa — użyj Synchronizuj kartę."
  fi

  completed_at="$(date -Iseconds)"
  jq -n --arg from "$APP_VERSION" --arg to "$APP_VERSION" --arg from_ui "$current_ui" --arg to_ui "$card_ui" \
    --arg zip "$zip" --arg backup "$backup" --arg sync_result "$sync_result" --arg completed_at "$completed_at" \
    '{from_version:$from,to_version:$to,from_card_ui_version:$from_ui,to_card_ui_version:$to_ui,package:$zip,update_scope:"dashboard_only",restart_required:"none",backup:$backup,status:"completed",dashboard_sync:$sync_result,completed_at:$completed_at}' \
    > "$LOCAL_UPDATE_LAST_INSTALL_FILE" 2>/dev/null || true

  archive_completed_local_update_zip "$zip"
  rm -f "$LOCAL_UPDATE_CANDIDATE_FILE"
  cleanup_local_update_archives "dashboard_only_success"
  check_app_update || true
  return 0
}

delegate_store_update_from_local_package() {
  local slug="$1" version="$2" zip="$3" info latest current_state response
  [ -n "$slug" ] || return 1
  # Refresh store metadata so a newly published release is visible before comparing.
  supervisor_post "/store/reload" '{}' /tmp/sbc5_store_reload.json || true
  info="$(curl -fsS --connect-timeout 3 --max-time 8 \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    "http://supervisor/addons/${slug}/info" 2>/dev/null || true)"
  latest="$(printf '%s' "$info" | jq -r '.data.version_latest // .version_latest // empty' 2>/dev/null || true)"
  current_state="$(printf '%s' "$info" | jq -r '.data.state // .state // empty' 2>/dev/null || true)"
  if [ -z "$latest" ]; then
    log "Hybrid Update: nie można odczytać version_latest dla ${slug}; pełna aktualizacja sklepowa nie została uruchomiona."
    return 1
  fi
  if [ "$latest" != "$version" ]; then
    log "Hybrid Update: lokalny ZIP ma wersję ${version}, a sklep Apps publikuje ${latest}. Pełny runtime może być aktualizowany lokalnym poleceniem tylko wtedy, gdy identyczna wersja jest już opublikowana w sklepie."
    return 1
  fi

  fan_control_prepare_update_handoff "$version" || true
  jq -n --arg from "$APP_VERSION" --arg to "$version" --arg zip "$zip" --arg slug "$slug" \
    '{from_version:$from,to_version:$to,package:$zip,update_scope:"full",channel:"store_delegate",target_slug:$slug,status:"delegated_to_store",staged_at:(now|todate)}' \
    > "$LOCAL_UPDATE_LAST_INSTALL_FILE" 2>/dev/null || true

  log "Hybrid Update: paczka ZIP ${version} została zweryfikowana; zlecam natywną aktualizację Apps dla ${slug} z backupem."
  if supervisor_post "/store/addons/${slug}/update" '{"backup":true,"background":false}' /tmp/sbc5_store_update.json; then
    log "Hybrid Update: Supervisor przyjął aktualizację sklepowa ${slug} -> ${version}."
    return 0
  fi
  rm -f "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true
  log "Hybrid Update: Supervisor odrzucił natywną aktualizację Apps. Lokalny ZIP pozostaje nienaruszony."
  return 1
}

install_local_update() (
  load_options
  [ "$LOCAL_PACKAGE_UPDATES_ENABLED" = "true" ] || { log "Lokalne aktualizacje ZIP są wyłączone."; return 1; }
  local active_runtime_slug installation_channel
  active_runtime_slug="$(resolve_runtime_app_slug)"
  installation_channel="local"
  case "$active_runtime_slug" in
    local_sbc5_control_center|local_rpi5_fan_manager) installation_channel="local" ;;
    *_sbc5_control_center) installation_channel="store" ;;
    *) installation_channel="unknown" ;;
  esac

  local now last=0
  now="$(date +%s)"
  if [ -r "$LOCAL_UPDATE_LAST_REQUEST_FILE" ]; then
    last="$(cat "$LOCAL_UPDATE_LAST_REQUEST_FILE" 2>/dev/null || echo 0)"
    case "$last" in ''|*[!0-9]*) last=0 ;; esac
  fi
  if [ $((now - last)) -lt "$LOCAL_UPDATE_COOLDOWN_SECONDS" ] 2>/dev/null; then
    local notice_last=0
    if [ -r "$LOCAL_UPDATE_COOLDOWN_NOTICE_FILE" ]; then
      notice_last="$(cat "$LOCAL_UPDATE_COOLDOWN_NOTICE_FILE" 2>/dev/null || echo 0)"
      case "$notice_last" in ''|*[!0-9]*) notice_last=0 ;; esac
    fi
    if [ $((now - notice_last)) -ge 30 ] 2>/dev/null; then
      log "Aktualizacja lokalna: pomijam serię powtórnych poleceń (blokada ${LOCAL_UPDATE_COOLDOWN_SECONDS} s)."
      printf '%s\n' "$now" > "$LOCAL_UPDATE_COOLDOWN_NOTICE_FILE" 2>/dev/null || true
    fi
    return 1
  fi

  # mkdir jest atomowy — równoległe wywołania nie przejdą jednocześnie.
  if ! mkdir "$LOCAL_UPDATE_LOCK_FILE" 2>/dev/null; then
    log "Aktualizacja lokalna jest już wykonywana."
    return 1
  fi
  trap 'rmdir "$LOCAL_UPDATE_LOCK_FILE" 2>/dev/null || true' EXIT
  printf '%s\n' "$now" > "$LOCAL_UPDATE_LAST_REQUEST_FILE" 2>/dev/null || true

  scan_local_update_candidate || { log "Brak nowszej lokalnej paczki ZIP do instalacji."; return 1; }

  local zip version root manifest_entry restart_required update_scope stage manifest_file ts backup app_src package_src bridge_src
  zip="$(jq -r '.zip' "$LOCAL_UPDATE_CANDIDATE_FILE")"
  version="$(jq -r '.version' "$LOCAL_UPDATE_CANDIDATE_FILE")"
  root="$(jq -r '.root' "$LOCAL_UPDATE_CANDIDATE_FILE")"
  manifest_entry="$(jq -r '.manifest_entry' "$LOCAL_UPDATE_CANDIDATE_FILE")"
  restart_required="$(jq -r '.restart_required // "home_assistant"' "$LOCAL_UPDATE_CANDIDATE_FILE")"
  update_scope="$(jq -r '.update_scope // "full"' "$LOCAL_UPDATE_CANDIDATE_FILE")"
  stage="/tmp/sbc5_update_${$}"
  rm -rf "$stage"; mkdir -p "$stage"
  unzip -q "$zip" -d "$stage" || { log "BŁĄD aktualizacji: nie można rozpakować ${zip}."; rm -rf "$stage"; return 1; }
  manifest_file="${stage}/${manifest_entry}"
  verify_local_update_package "$zip" "$stage" "$root" "$manifest_file" || {
    mkdir -p "$LOCAL_UPDATE_FAILED_DIR"
    failed_zip="$LOCAL_UPDATE_FAILED_DIR/$(basename "$zip")"
    mv -f "$zip" "$failed_zip" 2>/dev/null || { cp -f "$zip" "$failed_zip" 2>/dev/null || true; rm -f "$zip" 2>/dev/null || true; }
    touch "$failed_zip" 2>/dev/null || true
    cleanup_local_update_archives "verification_failed"
    rm -rf "$stage"; return 1;
  }

  if [ "$installation_channel" = "unknown" ]; then
    log "Hybrid Update: nieznany kanał instalacji (${active_runtime_slug}); odrzucam pełną aktualizację dla bezpieczeństwa."
    rm -rf "$stage"
    return 1
  fi

  # Store-managed full runtime updates remain owned by Supervisor. A local ZIP may
  # still be used as the user's trigger/verifier, but SBC5 delegates the actual app
  # replacement to the native Apps update endpoint when the same version is published.
  if [ "$installation_channel" = "store" ] && [ "$update_scope" != "dashboard_only" ] && [ "$update_scope" != "ui_only" ]; then
    rm -rf "$stage"
    if delegate_store_update_from_local_package "$active_runtime_slug" "$version" "$zip"; then
      rm -f "$LOCAL_UPDATE_CANDIDATE_FILE"
      return 0
    fi
    return 1
  fi

  if [ "$update_scope" = "dashboard_only" ] || [ "$update_scope" = "ui_only" ]; then
    if install_dashboard_only_update "$zip" "$version" "$stage" "$root" "$manifest_file"; then
      rm -rf "$stage"
      return 0
    fi
    rm -rf "$stage"
    return 1
  fi

  ts="$(date '+%Y%m%d_%H%M%S')"
  backup="/data/update_backups/${APP_VERSION}_to_${version}_${ts}"
  mkdir -p "$backup"
  [ -d /local_apps/sbc5_control_center ] && cp -a /local_apps/sbc5_control_center "$backup/app_source" || true
  [ -f /homeassistant/packages/sbc5_control_center.yaml ] && cp -a /homeassistant/packages/sbc5_control_center.yaml "$backup/sbc5_control_center.yaml" || true
  [ -d "$BRIDGE_DEST_DIR" ] && cp -a "$BRIDGE_DEST_DIR" "$backup/sbc5_control_center" || true
  cp -a "$manifest_file" "$backup/update-manifest.json" || true

  app_src="${stage}/${root}local_apps/sbc5_control_center"
  package_src="${stage}/${root}packages/sbc5_control_center.yaml"
  bridge_src="${stage}/${root}custom_components/sbc5_control_center"

  mkdir -p /local_apps /homeassistant/packages /homeassistant/custom_components
  rm -rf /local_apps/.sbc5_control_center.new
  cp -a "$app_src" /local_apps/.sbc5_control_center.new || { rm -rf "$stage"; return 1; }
  rm -rf /local_apps/.sbc5_control_center.old
  [ -d /local_apps/sbc5_control_center ] && mv /local_apps/sbc5_control_center /local_apps/.sbc5_control_center.old
  mv /local_apps/.sbc5_control_center.new /local_apps/sbc5_control_center || {
    [ -d /local_apps/.sbc5_control_center.old ] && mv /local_apps/.sbc5_control_center.old /local_apps/sbc5_control_center
    rm -rf "$stage"; return 1;
  }

  cp -f "$package_src" /homeassistant/packages/sbc5_control_center.yaml.new || return 1
  mv -f /homeassistant/packages/sbc5_control_center.yaml.new /homeassistant/packages/sbc5_control_center.yaml

  if [ -f "$BRIDGE_EXTERNAL_MARKER" ] && [ -f "$BRIDGE_DEST_DIR/manifest.json" ]; then
    log "Lokalna aktualizacja: bridge jest zarządzany przez HACS/Marketplace — pomijam podmianę custom_components."
  elif [ -d "$bridge_src" ]; then
    rm -rf "${BRIDGE_DEST_DIR}.new"
    cp -a "$bridge_src" "${BRIDGE_DEST_DIR}.new" || true
    if [ -d "${BRIDGE_DEST_DIR}.new" ]; then
      rm -rf "${BRIDGE_DEST_DIR}.old"
      [ -d "$BRIDGE_DEST_DIR" ] && mv "$BRIDGE_DEST_DIR" "${BRIDGE_DEST_DIR}.old" || true
      mv "${BRIDGE_DEST_DIR}.new" "$BRIDGE_DEST_DIR" || true
      rm -rf "${BRIDGE_DEST_DIR}.old"
    fi
  fi

  rm -rf /local_apps/.sbc5_control_center.old
  sync
  jq -n --arg from "$APP_VERSION" --arg to "$version" --arg zip "$zip" --arg restart "$restart_required" --arg backup "$backup" \
    '{from_version:$from,to_version:$to,package:$zip,restart_required:$restart,backup:$backup,status:"pending_startup",staged_at:(now|todate)}' \
    > "$LOCAL_UPDATE_LAST_INSTALL_FILE" 2>/dev/null || true

  # Nie archiwizuj/nie kasuj ZIP przed startem nowego runtime. Dopiero nowa wersja
  # może potwierdzić, że przeszła realny startup/health checkpoint.
  rm -f "$LOCAL_UPDATE_CANDIDATE_FILE"
  rm -rf "$stage"

  log "Lokalna aktualizacja ${APP_VERSION} -> ${version}: pliki zweryfikowano i podmieniono; status=pending_startup. Backup: ${backup}."
  log "Odświeżam lokalne aplikacje i zlecam przebudowę SBC5 Control Centera."
  if ! supervisor_post "/addons/reload" '{}' /tmp/sbc5_addons_reload.json; then
    log "BŁĄD aktualizacji: Supervisor odrzucił /addons/reload. Źródła zostały podmienione, ale aplikacja wymaga ręcznego przebudowania."
    ha_notify "SBC5 Control Center — wymagane ręczne przebudowanie" "Pliki nowej wersji zostały skopiowane, ale Supervisor nie zezwolił aplikacji na odświeżenie lokalnych aplikacji. Otwórz stronę SBC5 Control Center i wybierz Przebuduj/Rebuild. Od wersji 1.6.1 aplikacja używa roli Supervisor manager, więc kolejne lokalne aktualizacje będą mogły wykonać ten krok automatycznie."
    return 1
  fi

  # Wywołanie rebuild jest ostatnią czynnością starego kontenera. Jeśli Adaptive
  # PWM aktualnie posiada bezpieczne sterowanie 1%, zachowujemy ownership i PWM
  # przez restart kontenera, aby update nie powodował chwilowego powrotu do
  # fabrycznego kroku ~29%.
  fan_control_prepare_update_handoff "$version" || true
  (
    sleep 2
    target_slug="$(resolve_runtime_app_slug)"
    if curl -fsS --connect-timeout 2 --max-time 5 \
      -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
      "http://supervisor/addons/${target_slug}/info" >/tmp/sbc5_target_app_info.json 2>&1; then
      if ! curl -sS -X POST \
        -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"force":true}' \
        "http://supervisor/addons/${target_slug}/rebuild" \
        >/tmp/sbc5_self_rebuild.json 2>&1; then
        rm -f "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true
      fi
    else
      # Mixed namespace recovery: the canonical source has just been staged but
      # the native app identity may not yet be installed. Install it from the
      # refreshed local store instead of issuing a rebuild against a missing app.
      if curl -fsS -X POST \
        -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{}' \
        "http://supervisor/store/addons/${target_slug}/install" \
        >/tmp/sbc5_native_install.json 2>&1; then
        curl -fsS -X POST \
          -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
          -H "Content-Type: application/json" \
          -d '{}' \
          "http://supervisor/addons/${target_slug}/start" \
          >/tmp/sbc5_native_start.json 2>&1 || true
      else
        rm -f "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true
      fi
    fi
    # Jeżeli Supervisor przyjął żądanie, ale nowy runtime faktycznie nie wystartował,
    # marker nie może pozostać bezterminowo.
    sleep "$FAN_CONTROL_HANDOFF_MAX_AGE_SECONDS"
    rm -f "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true
  ) &
  return 0
)

finalize_local_update_after_startup() {
  [ -r "$LOCAL_UPDATE_LAST_INSTALL_FILE" ] || return 0
  local status to_version tmp startup_at
  status="$(jq -r '.status // empty' "$LOCAL_UPDATE_LAST_INSTALL_FILE" 2>/dev/null || true)"
  [ "$status" = "pending_startup" ] || return 0
  to_version="$(jq -r '.to_version // empty' "$LOCAL_UPDATE_LAST_INSTALL_FILE" 2>/dev/null || true)"
  [ -n "$to_version" ] && [ "$to_version" = "$APP_VERSION" ] || {
    log "Update Health Check Phase A: oczekiwano wersji ${to_version:-brak}, uruchomiono ${APP_VERSION}; nie przechodzę do Phase B."
    return 1
  }

  # Phase A verifies the new app runtime. Package retention/cleanup is deliberately
  # deferred until Home Assistant reloads the matching native integration and its
  # canonical telemetry entities pass the end-to-end validation.
  startup_at="$(date -Iseconds)"
  tmp="${LOCAL_UPDATE_LAST_INSTALL_FILE}.tmp"
  jq --arg status pending_ha_health --arg startup_at "$startup_at" \
    '.status=$status | .startup_health_checked_at=$startup_at' \
    "$LOCAL_UPDATE_LAST_INSTALL_FILE" > "$tmp" 2>/dev/null && mv -f "$tmp" "$LOCAL_UPDATE_LAST_INSTALL_FILE" || rm -f "$tmp" 2>/dev/null || true
  log "Update Health Check Phase A: PASS — SBC5 Control Center ${APP_VERSION} osiągnął checkpoint runtime; oczekuję na telemetrię natywnej integracji po restarcie HA."
  return 0
}

native_telemetry_health_check() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 1
  core_api_available || return 1

  local relay cpu cpu_freq fan_rpm pkg sample_epoch now age relay_temp relay_pwm
  relay="$(curl -fsS --connect-timeout 2 --max-time 4 -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    http://supervisor/core/api/states/sensor.sbc5_control_center_host_telemetry 2>/dev/null || true)"
  [ -n "$relay" ] || return 1
  sample_epoch="$(printf '%s' "$relay" | jq -r '.attributes.sample_epoch // 0' 2>/dev/null || echo 0)"
  relay_temp="$(printf '%s' "$relay" | jq -r '.attributes.cpu_temperature // 0' 2>/dev/null || echo 0)"
  relay_pwm="$(printf '%s' "$relay" | jq -r '.attributes.fan_pwm // .attributes.fan_pwm_raw // empty' 2>/dev/null || true)"
  now="$(date +%s)"
  age="$(awk -v n="$now" -v s="$sample_epoch" 'BEGIN{if(s<=0){print 9999}else{a=n-s;if(a<0)a=0;printf "%.0f",a}}')"
  awk -v t="$relay_temp" 'BEGIN{exit !(t>0 && t<150)}' || return 1
  [ -n "$relay_pwm" ] || return 1
  [ "$age" -le 30 ] 2>/dev/null || return 1

  cpu="$(ha_get_state sensor.sbc5_cpu_temperature 2>/dev/null || true)"
  cpu_freq="$(ha_get_state sensor.sbc5_cpu_frequency 2>/dev/null || true)"
  fan_rpm="$(ha_get_state sensor.sbc5_fan_rpm 2>/dev/null || true)"
  pkg="$(ha_get_state sensor.sbc5_package_version 2>/dev/null || true)"
  case "$cpu" in ''|unknown|unavailable|none) return 1 ;; esac
  case "$cpu_freq" in ''|unknown|unavailable|none) return 1 ;; esac
  case "$fan_rpm" in ''|unknown|unavailable|none) return 1 ;; esac
  [ "$pkg" = "$REQUIRED_PACKAGE_VERSION" ] || return 1
  awk -v t="$cpu" 'BEGIN{exit !(t>0 && t<150)}' || return 1
  awk -v f="$cpu_freq" 'BEGIN{exit !(f>0)}' || return 1
  awk -v r="$fan_rpm" 'BEGIN{exit !(r>=0)}' || return 1
  return 0
}

finalize_local_update_after_native_health() {
  [ -r "$LOCAL_UPDATE_LAST_INSTALL_FILE" ] || return 0
  local status to_version zip completed_at tmp processed_zip
  status="$(jq -r '.status // empty' "$LOCAL_UPDATE_LAST_INSTALL_FILE" 2>/dev/null || true)"
  [ "$status" = "pending_ha_health" ] || return 0
  to_version="$(jq -r '.to_version // empty' "$LOCAL_UPDATE_LAST_INSTALL_FILE" 2>/dev/null || true)"
  [ "$to_version" = "$APP_VERSION" ] || return 1
  native_telemetry_health_check || return 1
  fan_profile_runtime_health_check || return 2

  zip="$(jq -r '.package // empty' "$LOCAL_UPDATE_LAST_INSTALL_FILE" 2>/dev/null || true)"
  if [ -n "$zip" ] && [ -f "$zip" ]; then
    if [ "$LOCAL_PACKAGE_KEEP_PROCESSED" = "true" ]; then
      mkdir -p "$LOCAL_UPDATE_PROCESSED_DIR"
      processed_zip="$LOCAL_UPDATE_PROCESSED_DIR/$(basename "$zip")"
      mv -f "$zip" "$processed_zip" 2>/dev/null || { cp -f "$zip" "$processed_zip" 2>/dev/null || true; rm -f "$zip" 2>/dev/null || true; }
      touch "$processed_zip" 2>/dev/null || true
    else
      rm -f "$zip" 2>/dev/null || true
    fi
  fi

  completed_at="$(date -Iseconds)"
  tmp="${LOCAL_UPDATE_LAST_INSTALL_FILE}.tmp"
  jq --arg status completed --arg completed_at "$completed_at" \
    '.status=$status | .native_health_checked_at=$completed_at | .health_checked_at=$completed_at | .completed_at=$completed_at' \
    "$LOCAL_UPDATE_LAST_INSTALL_FILE" > "$tmp" 2>/dev/null && mv -f "$tmp" "$LOCAL_UPDATE_LAST_INSTALL_FILE" || rm -f "$tmp" 2>/dev/null || true
  cleanup_local_update_archives "install_success"
  log "Update Health Check Phase B: PASS — runtime → relay → integracja → natywne encje HA → profil chłodzenia dla ${APP_VERSION} są zdrowe; paczka została sfinalizowana."
  return 0
}

local_update_native_health_loop() {
  local ticks=0 rc=0 sleep_seconds=60
  sleep 10
  while true; do
    sleep_seconds=60
    if [ -r "$LOCAL_UPDATE_LAST_INSTALL_FILE" ] && [ "$(jq -r '.status // empty' "$LOCAL_UPDATE_LAST_INSTALL_FILE" 2>/dev/null || true)" = "pending_ha_health" ]; then
      sleep_seconds=10
      if finalize_local_update_after_native_health; then
        ticks=0
      else
        rc=$?
        ticks=$((ticks + 1))
        if [ $((ticks % 6)) -eq 0 ]; then
          if [ "$rc" -eq 2 ] 2>/dev/null; then
            log "Update Health Check Phase B: oczekiwanie — profil chłodzenia nie jest zgodny ze stanem żądanym ($(fan_profile_runtime_health_summary)); zachowuję ZIP i backup."
          else
            log "Update Health Check Phase B: oczekiwanie — canonical relay/native sensory nie są jeszcze kompletne; zachowuję ZIP i backup."
          fi
        fi
      fi
    else
      ticks=0
    fi
    sleep "$sleep_seconds"
  done
}

local_update_directory_signature() {
  local dir f
  {
    for dir in "$LOCAL_UPDATE_DIR" "$LEGACY_LOCAL_UPDATE_DIR" "$LEGACY_OLD_LOCAL_UPDATE_DIR"; do
      [ -d "$dir" ] || continue
      for f in "$dir"/*.zip; do
        [ -f "$f" ] || continue
        stat -c '%n|%s|%Y' "$f" 2>/dev/null || printf '%s|unknown\n' "$f"
      done
    done
  } | sort | sha256sum | awk '{print $1}'
}

local_update_watch_loop() {
  local last_sig current_sig
  last_sig="$(local_update_directory_signature)"
  sleep 45
  while true; do
    load_options
    current_sig="$(local_update_directory_signature)"
    if [ "$LOCAL_PACKAGE_UPDATES_ENABLED" = "true" ]; then
      if [ "$current_sig" != "$last_sig" ]; then
        last_sig="$current_sig"
        check_app_update local_only || true
      fi
    else
      last_sig="$current_sig"
    fi
    sleep "$((LOCAL_PACKAGE_SCAN_INTERVAL_MINUTES * 60))"
  done
}

version_gt() {
  local candidate="$1" current="$2"
  [ -n "$candidate" ] && [ -n "$current" ] || return 1
  [ "$candidate" != "$current" ] || return 1
  [ "$(printf '%s\n%s\n' "$current" "$candidate" | sort -V | tail -n1)" = "$candidate" ]
}


version_ge() {
  local candidate="$1" minimum="$2"
  [ -n "$candidate" ] && [ -n "$minimum" ] || return 1
  [ "$candidate" = "$minimum" ] || version_gt "$candidate" "$minimum"
}

publish_platform_compatibility() {
  local state="$1" core="$2" haos="$3" message="$4"
  jq -n     --arg state "$state" --arg core "$core" --arg haos "$haos"     --arg min_core "$REQUIRED_HA_CORE" --arg min_haos "$REQUIRED_HAOS"     --arg message "$message" --arg checked "$(date '+%Y-%m-%d %H:%M:%S')"     '{state:$state,installed_core:$core,installed_haos:$haos,minimum_core:$min_core,minimum_haos:$min_haos,message:$message,checked:$checked}'     > "$PLATFORM_COMPATIBILITY_FILE" 2>/dev/null || true

  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  local payload
  payload="$(jq -n     --arg state "$state" --arg core "$core" --arg haos "$haos"     --arg min_core "$REQUIRED_HA_CORE" --arg min_haos "$REQUIRED_HAOS"     --arg message "$message" --arg updated "$(date '+%Y-%m-%d %H:%M:%S')"     '{state:$state,attributes:{friendly_name:"SBC5 zgodność platformy",icon:(if $state=="compatible" then "mdi:shield-check" elif $state=="incompatible" then "mdi:shield-alert" else "mdi:shield-search" end),installed_core:$core,installed_haos:$haos,minimum_core:$min_core,minimum_haos:$min_haos,message:$message,last_update:$updated}}')"
  curl -fsS -X POST     -H "Authorization: Bearer ${SUPERVISOR_TOKEN}"     -H "Content-Type: application/json"     -d "$payload"     "http://supervisor/core/api/states/sensor.sbc5_platform_compatibility"     >/dev/null 2>&1 || true
}

read_platform_versions() {
  local output="${1:-/tmp/sbc5_platform_info.json}"
  supervisor_get "/info" "$output" || return 1
  PLATFORM_CORE_VERSION="$(jq -r '.data.homeassistant // .homeassistant // empty' "$output" 2>/dev/null || true)"
  PLATFORM_HAOS_VERSION="$(jq -r '.data.hassos // .hassos // empty' "$output" 2>/dev/null || true)"
  return 0
}

platform_preflight() {
  local attempt=1 message=""
  PLATFORM_CORE_VERSION=""; PLATFORM_HAOS_VERSION=""
  while [ "$attempt" -le 5 ]; do
    if read_platform_versions "/tmp/sbc5_platform_info.json"; then
      break
    fi
    sleep 2
    attempt=$((attempt + 1))
  done

  if [ -z "$PLATFORM_CORE_VERSION" ]; then
    message="Nie udało się potwierdzić wersji Home Assistant Core przez Supervisor API. Natywne wymaganie manifestu pozostaje aktywne."
    publish_platform_compatibility unknown "$PLATFORM_CORE_VERSION" "$PLATFORM_HAOS_VERSION" "$message"
    log "Platform Guard: ${message}"
    return 0
  fi

  if ! version_ge "$PLATFORM_CORE_VERSION" "$REQUIRED_HA_CORE"; then
    message="Wymagany Home Assistant Core >= ${REQUIRED_HA_CORE}; wykryto ${PLATFORM_CORE_VERSION}."
    publish_platform_compatibility incompatible "$PLATFORM_CORE_VERSION" "$PLATFORM_HAOS_VERSION" "$message"
    log "Platform Guard: BLOKADA — ${message}"
    return 1
  fi

  if [ -z "$PLATFORM_HAOS_VERSION" ] || ! version_ge "$PLATFORM_HAOS_VERSION" "$REQUIRED_HAOS"; then
    message="Wymagany Home Assistant OS >= ${REQUIRED_HAOS}; wykryto ${PLATFORM_HAOS_VERSION:-brak/nie-HAOS}."
    publish_platform_compatibility incompatible "$PLATFORM_CORE_VERSION" "$PLATFORM_HAOS_VERSION" "$message"
    log "Platform Guard: BLOKADA — ${message}"
    return 1
  fi

  message="Platforma spełnia wymagania: Core ${PLATFORM_CORE_VERSION}, HA OS ${PLATFORM_HAOS_VERSION}."
  publish_platform_compatibility compatible "$PLATFORM_CORE_VERSION" "$PLATFORM_HAOS_VERSION" "$message"
  log "Platform Guard: OK — ${message}"
  return 0
}

verify_release_platform_requirements() {
  local manifest="$1" min_core min_haos
  min_core="$(jq -r '.minimum_home_assistant_core // empty' "$manifest" 2>/dev/null || true)"
  min_haos="$(jq -r '.minimum_home_assistant_os // empty' "$manifest" 2>/dev/null || true)"
  [ -n "$min_core$min_haos" ] || return 0

  read_platform_versions "/tmp/sbc5_update_platform_info.json" || {
    log "BŁĄD aktualizacji: nie można potwierdzić wersji platformy przed instalacją paczki."
    return 1
  }
  if [ -n "$min_core" ] && ! version_ge "$PLATFORM_CORE_VERSION" "$min_core"; then
    log "BŁĄD aktualizacji: paczka wymaga Core >= ${min_core}, a zainstalowano ${PLATFORM_CORE_VERSION:-nieznane}."
    return 1
  fi
  if [ -n "$min_haos" ] && { [ -z "$PLATFORM_HAOS_VERSION" ] || ! version_ge "$PLATFORM_HAOS_VERSION" "$min_haos"; }; then
    log "BŁĄD aktualizacji: paczka wymaga HA OS >= ${min_haos}, a zainstalowano ${PLATFORM_HAOS_VERSION:-brak/nie-HAOS}."
    return 1
  fi
  return 0
}

resolve_runtime_app_slug() {
  # Custom App repositories prefix the configured slug with a repository hash.
  # Detect the installed/running SBC5 identity dynamically and retain local/legacy
  # fallbacks for older installations.
  local slug info state addons candidate
  [ -n "${SUPERVISOR_TOKEN:-}" ] || { printf '%s\n' 'local_sbc5_control_center'; return 0; }

  addons="$(curl -fsS --connect-timeout 3 --max-time 8 \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    "http://supervisor/addons" 2>/dev/null || true)"
  if [ -n "$addons" ]; then
    candidate="$(printf '%s' "$addons" | jq -r '
      (.data.addons // .addons // [])[]? |
      select((.name // "") == "SBC5 Control Center" or
             (.slug // "") == "local_sbc5_control_center" or
             ((.slug // "") | endswith("_sbc5_control_center"))) |
      select((.installed // true) == true) |
      select((.state // "") == "started" or (.state // "") == "running") |
      .slug' 2>/dev/null | head -n1)"
    if [ -z "$candidate" ]; then
      candidate="$(printf '%s' "$addons" | jq -r '
        (.data.addons // .addons // [])[]? |
        select((.name // "") == "SBC5 Control Center" or
               (.slug // "") == "local_sbc5_control_center" or
               ((.slug // "") | endswith("_sbc5_control_center"))) |
        select((.installed // true) == true) |
        .slug' 2>/dev/null | head -n1)"
    fi
    if [ -n "$candidate" ] && [ "$candidate" != "null" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  fi

  for slug in local_sbc5_control_center local_rpi5_fan_manager; do
    info="$(curl -fsS -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" "http://supervisor/addons/${slug}/info" 2>/dev/null || true)"
    [ -n "$info" ] || continue
    state="$(printf '%s' "$info" | jq -r '.data.state // .state // empty' 2>/dev/null || true)"
    if [ "$state" = "started" ] || [ "$state" = "running" ]; then
      printf '%s\n' "$slug"
      return 0
    fi
  done
  printf '%s\n' 'local_sbc5_control_center'
}

publish_app_update_state() {
  local state="$1" latest="$2" source="$3" repository="$4" release_url="$5" download_url="$6" changelog_url="$7" restart_required="$8" release_date="$9" summary="${10}" source_message="${11}"
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0

  local available=false
  [ "$state" = "available" ] && available=true

  local payload runtime_slug runtime_namespace installation_channel migration_state update_scope card_installed card_latest
  update_scope="full"
  card_installed="$(current_card_ui_version)"
  card_latest="$card_installed"
  if [ "$source" = "local_zip" ] && [ -r "$LOCAL_UPDATE_CANDIDATE_FILE" ]; then
    update_scope="$(jq -r '.update_scope // "full"' "$LOCAL_UPDATE_CANDIDATE_FILE" 2>/dev/null || echo full)"
    card_latest="$(jq -r '.card_ui_version // empty' "$LOCAL_UPDATE_CANDIDATE_FILE" 2>/dev/null || true)"
    [ -n "$card_latest" ] || card_latest="$card_installed"
  fi
  runtime_slug="$(resolve_runtime_app_slug)"
  runtime_namespace="legacy"
  installation_channel="unknown"
  case "$runtime_slug" in
    local_sbc5_control_center|local_rpi5_fan_manager) installation_channel="local" ;;
    *_sbc5_control_center) installation_channel="store" ;;
  esac
  case "$runtime_slug" in local_sbc5_control_center|*_sbc5_control_center) runtime_namespace="native" ;; esac
  migration_state="$(jq -r '.state // .migration_state // "idle"' "$STORE_MIGRATION_STATUS_FILE" 2>/dev/null || echo idle)"
  payload="$(jq -n \
    --arg state "$state" \
    --arg installed "$APP_VERSION" \
    --arg latest "$latest" \
    --arg source "$source" \
    --arg repository "$repository" \
    --arg release_url "$release_url" \
    --arg download_url "$download_url" \
    --arg changelog_url "$changelog_url" \
    --arg restart_required "$restart_required" \
    --arg release_date "$release_date" \
    --arg summary "$summary" \
    --arg source_message "$source_message" \
    --arg runtime_slug "$runtime_slug" \
    --arg runtime_namespace "$runtime_namespace" \
    --arg installation_channel "$installation_channel" \
    --arg migration_state "$migration_state" \
    --arg update_scope "$update_scope" \
    --arg card_installed "$card_installed" \
    --arg card_latest "$card_latest" \
    --argjson available "$available" \
    --arg checked "$(date '+%Y-%m-%d %H:%M:%S')" \
    '{
      state:$state,
      attributes:{
        friendly_name:"Aktualizacja SBC5 Control Center",
        icon:(if $state=="available" then "mdi:update" elif $state=="current" then "mdi:check-decagram" elif $state=="disabled" then "mdi:update-off" else "mdi:cloud-question" end),
        installed_version:$installed,
        current_version:$installed,
        version:$installed,
        latest_version:(if ($latest|length) > 0 then $latest else $installed end),
        update_available:$available,
        source:$source,
        source_display:(if $source=="local_zip" then "Lokalna paczka ZIP" elif $source=="local_zip_scan" then "Katalog lokalnych ZIP" elif $source=="supervisor_store" then "Sklep aplikacji Home Assistant" elif $source=="manifest" then "Manifest aktualizacji" elif $source=="disabled" then "Wyłączone" elif ($source|length)>0 then $source else "Brak danych" end),
        repository:$repository,
        local_update_dir:"/config/sbc5_control_center_updates/",
        legacy_local_update_dir:"/config/rpi5_control_center_updates/",
        legacy_update_dir:"/config/rpi5_fan_manager_updates/",
        local_package_file:(if $source == "local_zip" then $repository else "" end),
        local_install_supported:($source == "local_zip"),
        release_url:$release_url,
        download_url:$download_url,
        changelog_url:$changelog_url,
        restart_required:$restart_required,
        release_date:$release_date,
        summary:$summary,
        source_message:$source_message,
        runtime_app_slug:$runtime_slug,
        runtime_namespace:$runtime_namespace,
        installation_channel:$installation_channel,
        migration_state:$migration_state,
        update_scope:$update_scope,
        card_ui_installed_version:$card_installed,
        card_ui_latest_version:$card_latest,
        status_message:(if $state=="available" then ("Dostępna wersja " + (if ($latest|length)>0 then $latest else $installed end)) elif $state=="current" then ("Wersja " + $installed + " jest aktualna") elif $state=="disabled" then "Sprawdzanie aktualizacji jest wyłączone" elif $state=="not_configured" then "Brak skonfigurowanego źródła aktualizacji" else $source_message end),
        message:(if $state=="available" then ("Dostępna wersja " + (if ($latest|length)>0 then $latest else $installed end)) elif $state=="current" then ("Wersja " + $installed + " jest aktualna") elif ($source_message|length)>0 then $source_message else $state end),
        last_check:$checked
      }
    }')"

  # Canonical SBC5 state + compatibility aliases during namespace handoff.
  for update_entity in sensor.sbc5_control_center_update sensor.rpi5_fan_manager_update sensor.rpi5_control_center_update; do
    curl -fsS -X POST \
      -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$payload" \
      "http://supervisor/core/api/states/${update_entity}" \
      >/dev/null 2>&1 || true
  done
}

send_app_update_mobile_notification() {
  local latest="$1" summary="$2" release_url="$3" restart_required="$4"
  [ "$ACTIONABLE_MOBILE_NOTIFICATIONS" = "true" ] || return 0
  [ -n "$RESOLVED_MOBILE_NOTIFY_SERVICE" ] || resolve_mobile_notify_service
  [ -n "$RESOLVED_MOBILE_NOTIFY_SERVICE" ] || return 0
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0

  local message payload
  message="Zainstalowana: ${APP_VERSION}"$'\n'"Dostępna: ${latest}"
  [ -n "$summary" ] && message="${message}"$'\n\n'"${summary}"
  [ -n "$restart_required" ] && message="${message}"$'\n\n'"Wymagany restart po aktualizacji: ${restart_required}."

  local local_candidate=""
  local_candidate="$(jq -r '.version // empty' "$LOCAL_UPDATE_CANDIDATE_FILE" 2>/dev/null || true)"
  if [ -n "$local_candidate" ] && [ "$local_candidate" = "$latest" ]; then
    payload="$(jq -cn --arg title "SBC5 Control Center ${latest}" --arg message "$message" '{
      title:$title,
      message:$message,
      data:{
        tag:"sbc5_control_center_update",
        actions:[{action:"RPI5_INSTALL_LOCAL_UPDATE",title:"Zainstaluj aktualizację"}]
      }
    }')"
  elif [ -n "$release_url" ]; then
    payload="$(jq -cn --arg title "SBC5 Control Center ${latest}" --arg message "$message" --arg uri "$release_url" '{
      title:$title,
      message:$message,
      data:{
        tag:"sbc5_control_center_update",
        actions:[{action:"URI",title:"Pokaż wydanie",uri:$uri}]
      }
    }')"
  else
    payload="$(jq -cn --arg title "SBC5 Control Center ${latest}" --arg message "$message" '{title:$title,message:$message,data:{tag:"sbc5_control_center_update"}}')"
  fi

  curl -fsS -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "http://supervisor/core/api/services/notify/${RESOLVED_MOBILE_NOTIFY_SERVICE}" \
    >/dev/null 2>&1 || true
}

notify_app_update_available() {
  local latest="$1" source="$2" release_url="$3" changelog_url="$4" restart_required="$5" summary="$6"
  [ "$UPDATE_NOTIFY" = "true" ] || return 0
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0

  local message
  message="Zainstalowana wersja: ${APP_VERSION}"$'\n'"Dostępna wersja: ${latest}"$'\n'"Źródło: ${source}"
  [ -n "$summary" ] && message="${message}"$'\n\n'"${summary}"
  [ -n "$restart_required" ] && message="${message}"$'\n\n'"Restart po aktualizacji: ${restart_required}."
  [ -n "$release_url" ] && message="${message}"$'\n'"Wydanie: ${release_url}"
  [ -n "$changelog_url" ] && message="${message}"$'\n'"Changelog: ${changelog_url}"

  curl -fsS -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$(jq -cn --arg title "Dostępna aktualizacja SBC5 Control Center ${latest}" --arg message "$message" --arg id "$UPDATE_NOTIFICATION_ID" '{title:$title,message:$message,notification_id:$id}')" \
    http://supervisor/core/api/services/persistent_notification/create \
    >/dev/null 2>&1 || true

  send_app_update_mobile_notification "$latest" "$summary" "$release_url" "$restart_required"
}

dismiss_app_update_notification() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  curl -fsS -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$(jq -cn --arg id "$UPDATE_NOTIFICATION_ID" '{notification_id:$id}')" \
    http://supervisor/core/api/services/persistent_notification/dismiss \
    >/dev/null 2>&1 || true
}

check_app_update() {
  local check_mode="${1:-full}"
  load_options
  if [ "$UPDATE_CHECK_ENABLED" != "true" ]; then
    publish_app_update_state "disabled" "$APP_VERSION" "disabled" "" "" "" "" "" "" "" "Automatyczne sprawdzanie aktualizacji aplikacji jest wyłączone."
    dismiss_app_update_notification
    log "Sprawdzanie aktualizacji zakończone: funkcja jest wyłączona w konfiguracji."
    return 0
  fi

  log "Sprawdzam aktualizację SBC5 Control Center..."

  local best_version="$APP_VERSION"
  local best_source=""
  local best_repository=""
  local best_release_url=""
  local best_download_url=""
  local best_changelog_url=""
  local best_restart_required=""
  local best_release_date=""
  local best_summary=""
  local source_configured=false
  local source_message=""

  # 0. Lokalna paczka ZIP w /config/sbc5_control_center_updates (plus legacy rpi5_control_center/rpi5_fan_manager paths).
  if [ "$LOCAL_PACKAGE_UPDATES_ENABLED" = "true" ]; then
    source_configured=true
    if scan_local_update_candidate; then
      local lv lzip lrestart lsummary ldate
      lv="$(jq -r '.version // empty' "$LOCAL_UPDATE_CANDIDATE_FILE" 2>/dev/null || true)"
      lzip="$(jq -r '.zip // empty' "$LOCAL_UPDATE_CANDIDATE_FILE" 2>/dev/null || true)"
      lrestart="$(jq -r '.restart_required // "home_assistant"' "$LOCAL_UPDATE_CANDIDATE_FILE" 2>/dev/null || echo home_assistant)"
      lsummary="$(jq -r '.summary // empty' "$LOCAL_UPDATE_CANDIDATE_FILE" 2>/dev/null || true)"
      ldate="$(jq -r '.release_date // empty' "$LOCAL_UPDATE_CANDIDATE_FILE" 2>/dev/null || true)"
      if [ -n "$lv" ] && { version_gt "$lv" "$best_version" || [ "$best_source" = "" ]; }; then
        best_version="$lv"
        best_source="local_zip"
        best_repository="$lzip"
        best_restart_required="$lrestart"
        best_release_date="$ldate"
        best_summary="$lsummary"
      fi
    fi
  fi

  if [ "$check_mode" != "local_only" ]; then
  # 1. Dane Supervisor Store odczytywane pasywnie, bez wymuszania odświeżenia Store.
  #    Dla lokalnych aktualizacji ZIP nie ma powodu blokować Core/Supervisora
  #    kosztownym odświeżaniem Store. Supervisor aktualizuje katalog niezależnie.
  if supervisor_get "/addons" "/tmp/sbc5_addons.json" true; then
    local candidates line v repo slug url installed name
    candidates="$(jq -r '
      (.data.addons // .addons // [])[]? |
      select((.name // "") == "SBC5 Control Center" or (.slug // "") == "sbc5_control_center" or ((.slug // "") | endswith("_sbc5_control_center")) or (.slug // "") == "sbc5_fan_manager" or ((.slug // "") | endswith("_rpi5_fan_manager"))) |
      [(.version_latest // .version // ""),(.repository // ""),(.slug // ""),(.url // ""),(.installed // false),(.name // "")] | @tsv
    ' /tmp/sbc5_addons.json 2>/dev/null || true)"

    while IFS=$'\t' read -r v repo slug url installed name; do
      [ -n "$v" ] || continue
      # local repository is only the installed local app and cannot announce a future version
      if [ -n "$repo" ] && [ "$repo" != "local" ] && [ "$repo" != "null" ]; then
        source_configured=true
        if version_gt "$v" "$best_version"; then
          best_version="$v"
          best_source="supervisor_store"
          best_repository="$repo"
          best_release_url="$url"
          best_summary="Nowa wersja została wykryta przez natywny katalog aplikacji Home Assistant."
        fi
      fi
    done <<< "$candidates"
  fi

  # 2. Opcjonalny zdalny manifest dla instalacji lokalnych/manualnych.
  if [ -n "$APP_UPDATE_MANIFEST_URL" ]; then
    source_configured=true
    if curl -fsSL --connect-timeout 8 --max-time 20 "$APP_UPDATE_MANIFEST_URL" -o /tmp/sbc5_app_update_manifest.json 2>/dev/null; then
      local mv mname mslug mreleased mrelease mdownload mchangelog mrestart msummary
      mv="$(jq -r '.version // empty' /tmp/sbc5_app_update_manifest.json 2>/dev/null || true)"
      mname="$(jq -r '.name // "SBC5 Control Center"' /tmp/sbc5_app_update_manifest.json 2>/dev/null || true)"
      mslug="$(jq -r '.slug // "sbc5_fan_manager"' /tmp/sbc5_app_update_manifest.json 2>/dev/null || true)"
      if [ -n "$mv" ] && { [ "$mname" = "SBC5 Control Center" ] || [ "$mslug" = "sbc5_fan_manager" ]; }; then
        mreleased="$(jq -r '.release_date // empty' /tmp/sbc5_app_update_manifest.json 2>/dev/null || true)"
        mrelease="$(jq -r '.release_url // empty' /tmp/sbc5_app_update_manifest.json 2>/dev/null || true)"
        mdownload="$(jq -r '.download_url // empty' /tmp/sbc5_app_update_manifest.json 2>/dev/null || true)"
        mchangelog="$(jq -r '.changelog_url // empty' /tmp/sbc5_app_update_manifest.json 2>/dev/null || true)"
        mrestart="$(jq -r '.restart_required // empty' /tmp/sbc5_app_update_manifest.json 2>/dev/null || true)"
        msummary="$(jq -r '.summary // empty' /tmp/sbc5_app_update_manifest.json 2>/dev/null || true)"
        if version_gt "$mv" "$best_version"; then
          best_version="$mv"
          best_source="manifest"
          best_repository="$APP_UPDATE_MANIFEST_URL"
          best_release_url="$mrelease"
          best_download_url="$mdownload"
          best_changelog_url="$mchangelog"
          best_restart_required="$mrestart"
          best_release_date="$mreleased"
          best_summary="$msummary"
        elif [ "$best_source" = "" ]; then
          best_source="manifest"
          best_repository="$APP_UPDATE_MANIFEST_URL"
          best_release_url="$mrelease"
          best_download_url="$mdownload"
          best_changelog_url="$mchangelog"
          best_restart_required="$mrestart"
          best_release_date="$mreleased"
          best_summary="$msummary"
        fi
      else
        source_message="Manifest aktualizacji nie zawiera poprawnej wersji lub identyfikatora aplikacji."
        log "$source_message"
      fi
    else
      source_message="Nie udało się pobrać manifestu aktualizacji: ${APP_UPDATE_MANIFEST_URL}"
      log "$source_message"
    fi
  fi

  fi  # full-source checks

  local state signature
  if [ "$best_source" = "local_zip" ] && [ -r "$LOCAL_UPDATE_CANDIDATE_FILE" ]; then
    state="available"
  elif version_gt "$best_version" "$APP_VERSION"; then
    state="available"
  elif [ "$source_configured" = "true" ]; then
    state="current"
    if [ -z "$best_source" ]; then
      if [ "$LOCAL_PACKAGE_UPDATES_ENABLED" = "true" ]; then best_source="local_zip_scan"; else best_source="configured_source"; fi
    fi
  else
    state="not_configured"
    source_message="Brak zdalnego źródła wersji. Dla aktualizacji lokalnej umieść ZIP w /config/sbc5_control_center_updates/ (2.6.19 i starsze: /config/rpi5_control_center_updates/) albo skonfiguruj repozytorium/manifest zdalny."
  fi

  signature="${state}|${best_version}|${best_source}|${best_release_url}|${best_restart_required}"
  publish_app_update_state "$state" "$best_version" "$best_source" "$best_repository" "$best_release_url" "$best_download_url" "$best_changelog_url" "$best_restart_required" "$best_release_date" "$best_summary" "$source_message"

  if [ "$state" = "available" ]; then
    if [ "$UPDATE_NOTIFY" = "true" ] && [ "$signature" != "$LAST_UPDATE_SIGNATURE" ]; then
      notify_app_update_available "$best_version" "$best_source" "$best_release_url" "$best_changelog_url" "$best_restart_required" "$best_summary"
    fi
  else
    dismiss_app_update_notification
  fi

  LAST_UPDATE_SIGNATURE="$signature"
  jq -n --arg signature "$signature" --arg checked "$(date '+%Y-%m-%d %H:%M:%S')" \
    '{signature:$signature,last_check:$checked}' > "$UPDATE_STATE_FILE" 2>/dev/null || true

  case "$state" in
    available) log "Sprawdzanie aktualizacji zakończone: dostępna wersja ${best_version} (źródło=${best_source})." ;;
    current) log "Sprawdzanie aktualizacji zakończone: ${APP_VERSION} jest aktualna (źródło=${best_source})." ;;
    not_configured) log "Sprawdzanie aktualizacji zakończone: brak skonfigurowanego źródła wersji." ;;
    *) log "Sprawdzanie aktualizacji zakończone: stan=${state}." ;;
  esac
}

update_check_loop() {
  sleep 20
  while true; do
    check_app_update || true
    load_options
    sleep "$((UPDATE_CHECK_INTERVAL_HOURS * 3600))"
  done
}

ha_publish_restart_state() {
  local state="$1" reason="$2" package_version="$3"
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0

  local post_update="false" updated_from="" updated_to="" semantic signature
  if [ -r "$POST_UPDATE_STATE_FILE" ]; then
    post_update="true"
    updated_from="$(jq -r '.from_version // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)"
    updated_to="$(jq -r '.to_version // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)"
  fi

  # 2.8.22: the watchdog may call this repeatedly, but an unchanged restart state
  # must not generate a new HA state/event merely because a timestamp changed.
  semantic="${state}|${reason}|${APP_VERSION}|${REQUIRED_PACKAGE_VERSION}|${package_version}|${RESTART_POLICY}|${RESOLVED_MOBILE_NOTIFY_SERVICE}|${post_update}|${updated_from}|${updated_to}"
  signature="$(printf '%s' "$semantic" | sha256sum | awk '{print $1}')"
  if [ -n "${RESTART_LAST_PUBLISHED_SIGNATURE:-}" ] && [ "$signature" = "$RESTART_LAST_PUBLISHED_SIGNATURE" ]; then
    return 0
  fi

  local payload
  payload="$(jq -n \
    --arg state "$state" \
    --arg reason "$reason" \
    --arg app_version "$APP_VERSION" \
    --arg required_package "$REQUIRED_PACKAGE_VERSION" \
    --arg package_version "$package_version" \
    --arg policy "$RESTART_POLICY" \
    --arg mobile_service "$RESOLVED_MOBILE_NOTIFY_SERVICE" \
    --arg post_update "$post_update" \
    --arg updated_from "$updated_from" \
    --arg updated_to "$updated_to" \
    --arg updated "$(date '+%Y-%m-%d %H:%M:%S')" \
    '{
      state: $state,
      attributes: {
        friendly_name: "SBC5 wymagany restart",
        icon: (if $state == "host" then "mdi:restart-alert" elif $state == "home_assistant" then "mdi:home-assistant" else "mdi:check-circle" end),
        reason: $reason,
        app_version: $app_version,
        required_package_version: $required_package,
        loaded_package_version: $package_version,
        restart_policy: $policy,
        user_confirmation_required: true,
        native_home_assistant_restart: true,
        post_update: ($post_update == "true"),
        updated_from: $updated_from,
        updated_to: $updated_to,
        mobile_action_available: ($mobile_service != ""),
        mobile_notify_service: (if $mobile_service == "" then "brak" else ("notify." + $mobile_service) end),
        last_update: $updated
      }
    }')"

  if curl -fsS -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "http://supervisor/core/api/states/sensor.sbc5_restart_required" \
    >/dev/null 2>&1; then
    RESTART_LAST_PUBLISHED_SIGNATURE="$signature"
  fi
}

ha_restart_notification() {
  local state="$1" reason="$2"
  [ "$RESTART_NOTICE_ON_START" = "true" ] || return 0
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0

  resolve_mobile_notify_service

  local title message post_from="" post_to=""
  if [ -r "$POST_UPDATE_STATE_FILE" ]; then
    post_from="$(jq -r '.from_version // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)"
    post_to="$(jq -r '.to_version // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)"
  fi
  case "$state" in
    home_assistant)
      if [ -n "$post_to" ]; then
        title="SBC5 Control Center ${post_to} — aktualizacja zakończona"
      else
        title="SBC5 Control Center — wymagany restart Home Assistant"
      fi
      message="${reason}"$'\n\n'"Restart zostanie wykonany natywną akcją Home Assistant, która przed restartem automatycznie sprawdza konfigurację."
      ;;
    host)
      title="SBC5 Control Center — wymagany restart hosta"
      message="${reason}"$'\n\n'"Zmiana dotyczy konfiguracji boot/Device Tree. Wymagany jest pełny restart Raspberry Pi 5."
      ;;
    *) return 0 ;;
  esac

  if [ -n "$RESOLVED_MOBILE_NOTIFY_SERVICE" ]; then
    message="${message}"$'\n\n'"Na telefon wysłano również powiadomienie z przyciskiem restartu."
  else
    message="${message}"$'\n\n'"Wewnętrzne powiadomienia Home Assistant nie obsługują własnych przycisków akcji. Użyj karty Restart Manager lub skonfiguruj usługę powiadomień mobilnych w aplikacji."
  fi

  curl -fsS -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$(jq -cn --arg title "$title" --arg message "$message" --arg id "$RESTART_NOTIFICATION_ID" '{title:$title,message:$message,notification_id:$id}')" \
    http://supervisor/core/api/services/persistent_notification/create \
    >/dev/null 2>&1 || true

  ha_mobile_restart_notification "$state" "$reason" || true
}

ha_dismiss_restart_notification() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  curl -fsS -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$(jq -cn --arg id "$RESTART_NOTIFICATION_ID" '{notification_id:$id}')" \
    http://supervisor/core/api/services/persistent_notification/dismiss \
    >/dev/null 2>&1 || true
}

mark_cpu_host_restart_required() {
  local profile="$1" expected_arm="$2" reason="$3"
  jq -n \
    --arg type "host" --arg scope "cpu_profile" --arg profile "$profile" --arg expected_arm "$expected_arm" \
    --arg reason "$reason" --arg boot_id "$CURRENT_BOOT_ID" --arg version "$APP_VERSION" \
    --arg created "$(date '+%Y-%m-%d %H:%M:%S')" \
    '{type:$type,scope:$scope,expected_profile:$profile,expected_arm_freq:($expected_arm|if .=="" then null else (tonumber? // .) end),reason:$reason,boot_id:$boot_id,version:$version,created:$created}' \
    > "$RESTART_STATE_FILE"
  log "Restart Manager: wymagany restart hosta — $reason"
  publish_restart_requirement true
}

cpu_profile_verify_after_boot() {
  local profile="$1" expected_arm="$2" max_khz="" max_mhz="" cpu_file saved_arm="" include_present=false ok=false
  local attempt=1 max_attempts=5 max_source="unknown" fallback=""
  find_boot_config || return 1
  cpu_file="$(dirname "$BOOT_CFG")/$CPU_PROFILE_FILENAME"
  [ -r "$cpu_file" ] && saved_arm="$(cpu_profile_read_file_arm_freq "$cpu_file")"
  grep -Eq '^[[:space:]]*include[[:space:]]+sbc5cc-cpu-profile\.txt[[:space:]]*$' "$BOOT_CFG" 2>/dev/null && include_present=true
  cleanup_mount

  # v2.7.2: use the same host-aware cpufreq reader as telemetry. v2.7.1
  # accidentally called a non-existent read_cpu_freq(), so valid 2500/2600/etc.
  # clocks were reported as active_max=unknown and Repairs stayed open.
  while [ "$attempt" -le "$max_attempts" ]; do
    max_khz="$(read_cpu_frequency_bound_khz max 2>/dev/null || true)"
    if [[ "$max_khz" =~ ^[0-9]+$ ]]; then
      max_source="scaling_max_freq"
      break
    fi
    fallback="$(host_read_one_line /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq 2>/dev/null || true)"
    if [[ "$fallback" =~ ^[0-9]+$ ]]; then
      max_khz="$fallback"; max_source="cpuinfo_max_freq"
      break
    fi
    fallback="$(host_read_one_line /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq 2>/dev/null || true)"
    if [[ "$fallback" =~ ^[0-9]+$ ]]; then
      max_khz="$fallback"; max_source="policy0_scaling_max_freq"
      break
    fi
    [ "$attempt" -lt "$max_attempts" ] && sleep 3
    attempt=$((attempt + 1))
  done
  if [[ "$max_khz" =~ ^[0-9]+$ ]]; then max_mhz=$(( (max_khz + 500) / 1000 )); else max_mhz=""; fi

  if [ "$profile" = "factory" ]; then
    if [ -z "$saved_arm" ] && [ "$include_present" = "false" ] && { [ -z "$max_mhz" ] || [ "$max_mhz" -le 2400 ]; }; then ok=true; fi
  elif [ -n "$expected_arm" ]; then
    if [ "$saved_arm" = "$expected_arm" ] && [ -n "$max_mhz" ] && [ "$max_mhz" -eq "$expected_arm" ]; then ok=true; fi
  else
    # Advanced profile without a manual arm_freq cannot be verified by max clock;
    # successful boot plus intact profile file/include is the strongest signal.
    if [ "$include_present" = "true" ] && [ -r "$CPU_PROFILE_STATE_FILE" ]; then ok=true; fi
  fi

  if [ "$ok" = "true" ]; then
    log "CPU Profile Manager: Boot Verification PASS — profil=${profile}, saved_arm=${saved_arm:-factory}, active_max=${max_mhz:-unknown} MHz, source=${max_source}, attempt=${attempt}/${max_attempts}."
    return 0
  fi
  log "CPU Profile Manager: Boot Verification FAIL — profil=${profile}, expected_arm=${expected_arm:-factory}, saved_arm=${saved_arm:-null}, active_max=${max_mhz:-unknown} MHz, source=${max_source}, attempt=${attempt}/${max_attempts}. Restart pozostaje wymagany."
  return 1
}

mark_host_restart_required() {
  local reason="$1"
  jq -n \
    --arg type "host" \
    --arg reason "$reason" \
    --arg boot_id "$CURRENT_BOOT_ID" \
    --arg version "$APP_VERSION" \
    --arg created "$(date '+%Y-%m-%d %H:%M:%S')" \
    '{type:$type,reason:$reason,boot_id:$boot_id,version:$version,created:$created}' \
    > "$RESTART_STATE_FILE"
  log "Restart Manager: wymagany restart hosta — $reason"
  publish_restart_requirement true
}

clear_completed_host_restart() {
  [ -r "$RESTART_STATE_FILE" ] || return 0
  local type saved_boot scope profile expected_arm verification_failed=false
  type="$(jq -r '.type // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
  saved_boot="$(jq -r '.boot_id // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
  verification_failed="$(jq -r '.verification_failed // false' "$RESTART_STATE_FILE" 2>/dev/null || echo false)"
  [ "$type" = "host" ] && [ -n "$saved_boot" ] || return 0
  # Normal pending changes must wait for a new host boot. A marker that already
  # failed verification may be revalidated on the same boot; this lets 2.7.2
  # close the false 2.7.1 Repair without forcing an unnecessary second reboot.
  if [ "$saved_boot" = "$CURRENT_BOOT_ID" ] && [ "$verification_failed" != "true" ]; then return 0; fi
  scope="$(jq -r '.scope // "generic"' "$RESTART_STATE_FILE" 2>/dev/null || echo generic)"
  if [ "$scope" = "cpu_profile" ]; then
    profile="$(jq -r '.expected_profile // "factory"' "$RESTART_STATE_FILE" 2>/dev/null || echo factory)"
    expected_arm="$(jq -r 'if .expected_arm_freq == null then "" else (.expected_arm_freq|tostring) end' "$RESTART_STATE_FILE" 2>/dev/null || true)"
    if cpu_profile_verify_after_boot "$profile" "$expected_arm"; then
      log "Restart Manager: nowy boot hosta potwierdził profil CPU/OC — zamykam żądanie restartu."
      rm -f "$RESTART_STATE_FILE"
    else
      # Move boot_id forward so the current boot still exposes restart=host rather
      # than silently classifying the old marker as completed.
      local tmp="${RESTART_STATE_FILE}.tmp.$$"
      jq --arg boot "$CURRENT_BOOT_ID" --arg reason "Restart wykonano, ale profil CPU/OC nie został potwierdzony. Wymagany ponowny restart po naprawie konfiguracji." \
        '.boot_id=$boot | .reason=$reason | .verification_failed=true' "$RESTART_STATE_FILE" > "$tmp" 2>/dev/null && mv -f "$tmp" "$RESTART_STATE_FILE" || rm -f "$tmp"
      native_restart_repair_set host "Restart wykonano, ale profil CPU/OC nie został zastosowany. Sprawdź SBC5 CPU Profile Manager." "" "$APP_VERSION" || true
    fi
  else
    log "Restart Manager: wykryto nowy boot hosta — kasuję zakończone żądanie restartu."
    rm -f "$RESTART_STATE_FILE"
  fi
}

RESTART_REQUIRED_TYPE="none"
RESTART_REQUIRED_REASON="Brak oczekujących restartów."
LOADED_PACKAGE_VERSION="unknown"

detect_restart_requirement() {
  RESTART_REQUIRED_TYPE="none"
  RESTART_REQUIRED_REASON="Brak oczekujących restartów."
  LOADED_PACKAGE_VERSION="unknown"

  clear_completed_host_restart
  clear_completed_post_update_host_restart

  if [ -r "$RESTART_STATE_FILE" ]; then
    local pending_type pending_reason pending_boot
    pending_type="$(jq -r '.type // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
    pending_reason="$(jq -r '.reason // "Zmiany w konfiguracji boot wymagają ponownego uruchomienia hosta."' "$RESTART_STATE_FILE" 2>/dev/null || true)"
    pending_boot="$(jq -r '.boot_id // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
    if [ "$pending_type" = "host" ] && [ "$pending_boot" = "$CURRENT_BOOT_ID" ]; then
      RESTART_REQUIRED_TYPE="host"
      RESTART_REQUIRED_REASON="$pending_reason"
      LOADED_PACKAGE_VERSION="$(ha_get_state sensor.sbc5_package_version 2>/dev/null || true)"
      [ -n "$LOADED_PACKAGE_VERSION" ] || LOADED_PACKAGE_VERSION="unknown"
      return 0
    fi
  fi

  LOADED_PACKAGE_VERSION="$(ha_get_state sensor.sbc5_package_version 2>/dev/null || true)"
  [ -n "$LOADED_PACKAGE_VERSION" ] || LOADED_PACKAGE_VERSION="missing"

  if [ -r "$POST_UPDATE_STATE_FILE" ]; then
    local post_type post_reason post_from post_to
    post_type="$(jq -r '.restart_required // "none"' "$POST_UPDATE_STATE_FILE" 2>/dev/null || echo none)"
    post_reason="$(jq -r '.reason // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)"
    post_from="$(jq -r '.from_version // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)"
    post_to="$(jq -r '.to_version // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)"
    if [ "$post_type" = "host" ]; then
      RESTART_REQUIRED_TYPE="host"
      RESTART_REQUIRED_REASON="${post_reason} Wydanie wymaga pełnego restartu Raspberry Pi 5."
      return 0
    elif [ "$post_type" = "home_assistant" ]; then
      # 1.9.14: szybki restart Core może zakończyć się pomiędzy próbkami monitora.
      # Za twardy dowód zakończenia restartu uznajemy jednocześnie: nową wersję
      # natywnego bridge (sensor wersji) oraz aktywną usługę canonical bridge.
      if [ "$LOADED_PACKAGE_VERSION" = "$REQUIRED_PACKAGE_VERSION" ] && ha_service_exists sbc5_control_center set_restart_required; then
        log "Post-update: wykryto załadowany package/bridge ${REQUIRED_PACKAGE_VERSION} — restart HA zakończony, czyszczę stan oczekujący."
        rm -f "$POST_UPDATE_STATE_FILE" 2>/dev/null || true
        RESTART_REQUIRED_TYPE="none"
        RESTART_REQUIRED_REASON=""
        return 0
      fi
      RESTART_REQUIRED_TYPE="home_assistant"
      RESTART_REQUIRED_REASON="${post_reason} Aby zakończyć aktualizację, uruchom ponownie Home Assistant."
      if [ "$LOADED_PACKAGE_VERSION" != "$REQUIRED_PACKAGE_VERSION" ]; then
        RESTART_REQUIRED_REASON="${RESTART_REQUIRED_REASON} Bridge HA jest nadal w wersji ${LOADED_PACKAGE_VERSION}; po restarcie powinien wczytać ${REQUIRED_PACKAGE_VERSION}."
      fi
      return 0
    fi
  fi

  if [ "$LOADED_PACKAGE_VERSION" != "$REQUIRED_PACKAGE_VERSION" ]; then
    RESTART_REQUIRED_TYPE="home_assistant"
    RESTART_REQUIRED_REASON="Pakiet Home Assistant nie jest jeszcze wczytany w wersji ${REQUIRED_PACKAGE_VERSION} (aktualnie: ${LOADED_PACKAGE_VERSION}). Podmień packages/sbc5_control_center.yaml z tej wersji aplikacji, a następnie uruchom ponownie Home Assistant."
  fi
}

publish_restart_requirement() {
  local force_notify="${1:-false}"
  detect_restart_requirement
  ha_publish_restart_state "$RESTART_REQUIRED_TYPE" "$RESTART_REQUIRED_REASON" "$LOADED_PACKAGE_VERSION"

  if [ "$RESTART_REQUIRED_TYPE" = "none" ]; then
    # Czyść również po restarcie aplikacji i ponawiaj cleanup, jeżeli poprzednia
    # próba nie mogła usunąć Repair z bieżącego Core. To zapobiega sytuacji,
    # w której karta pokazuje „Bez restartu”, a Ustawienia nadal zgłaszają problem.
    if [ "$LAST_RESTART_STATE" != "none" ] || [ "$force_notify" = "true" ] || \
       [ -r "$NATIVE_RESTART_MARKER" ] || [ -r "$NATIVE_REPAIR_POSTED_FILE" ]; then
      native_restart_repair_clear || true
      ha_dismiss_restart_notification
    fi
  else
    local post_from="" post_to="$APP_VERSION"
    if [ -r "$POST_UPDATE_STATE_FILE" ]; then
      post_from="$(jq -r '.from_version // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)"
      post_to="$(jq -r '.to_version // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || echo "$APP_VERSION")"
    fi
    native_restart_repair_set "$RESTART_REQUIRED_TYPE" "$RESTART_REQUIRED_REASON" "$post_from" "$post_to"
    if [ "$force_notify" = "true" ] || [ "$RESTART_REQUIRED_TYPE" != "$LAST_RESTART_STATE" ]; then
      ha_restart_notification "$RESTART_REQUIRED_TYPE" "$RESTART_REQUIRED_REASON"
    fi
  fi

  LAST_RESTART_STATE="$RESTART_REQUIRED_TYPE"
}

supervisor_post() {
  local endpoint="$1" body="${2:-}" output="${3:-/tmp/sbc5_supervisor_response.json}"
  [ -n "$body" ] || body='{}'
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 1
  local code
  code="$(curl -sS -o "$output" -w '%{http_code}' -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$body" \
    "http://supervisor${endpoint}" 2>/dev/null || echo 000)"
  case "$code" in 2??) return 0 ;; *) log "Supervisor API ${endpoint}: HTTP ${code}"; return 1 ;; esac
}

restart_home_assistant_confirmed() {
  load_options
  publish_restart_requirement false

  if [ "$RESTART_POLICY" != "ask" ]; then
    log "Restart Manager: restart z aplikacji zablokowany przez restart_policy=notify_only."
    ha_restart_notification "home_assistant" "Restart jest ustawiony w trybie tylko powiadomienie. Uruchom Home Assistant ponownie ręcznie albo zmień restart_policy na ask."
    return 1
  fi

  if [ "$RESTART_REQUIRED_TYPE" = "host" ]; then
    log "Restart Manager: wymagany jest restart hosta; restart samego Home Assistant nie wystarczy."
    ha_restart_notification "host" "$RESTART_REQUIRED_REASON"
    return 1
  fi

  if [ "$RESTART_REQUIRED_TYPE" = "none" ]; then
    log "Restart Manager: brak wymaganych restartów."
    return 0
  fi

  if [ "$PRE_RESTART_CONFIG_CHECK" = "true" ]; then
    # Walidacja jest wykonywana zanim do packages trafi bridge bootstrap. Dzięki temu
    # działający proces HA nie zgłasza "Integration sbc5_fan_manager_bridge not found".
    log "Restart Manager: wykonuję sprawdzenie konfiguracji przez Supervisor /core/check."
    if ! supervisor_post "/core/check" '{}' "/tmp/sbc5_core_check.json"; then
      local detail
      detail="$(tr '\n' ' ' </tmp/sbc5_core_check.json 2>/dev/null | cut -c1-700)"
      [ -n "$detail" ] || detail="Supervisor odrzucił sprawdzenie konfiguracji."
      log "BŁĄD: konfiguracja Home Assistant nie przeszła walidacji. Restart anulowany. $detail"
      return 1
    fi
  fi

  # Dopiero teraz, tuż przed restartem, aktywujemy bridge package. Przy następnym
  # uruchomieniu Core pliki custom component są już na dysku od początku procesu.
  if ! ha_service_exists sbc5_control_center set_restart_required; then
    if ! stage_bridge_package_for_restart; then
      log "UWAGA: nie udało się przygotować bridge Repairs. Restart HA będzie kontynuowany bez natywnego Repairs."
    fi
  fi

  # Najpierw używamy endpointu Supervisor /core/restart. Supervisor pozostaje
  # dostępny w czasie restartu Core i może potwierdzić przyjęcie polecenia bez
  # fałszywego timeoutu powodowanego przez homeassistant.restart.
  log "Restart Manager: zlecam restart Home Assistant przez Supervisor /core/restart."
  if supervisor_post "/core/restart" '{}' "/tmp/sbc5_core_restart.json"; then
    log "Restart Manager: Supervisor przyjął polecenie restartu. Oczekuję na ponowne załadowanie canonical bridge."
    return 0
  fi

  # Fallback dla wersji Supervisor, które nie udostępniają /core/restart.
  # Zerwanie połączenia może oznaczać, że usługa homeassistant.restart właśnie
  # zatrzymała Core, dlatego nigdy nie wycofujemy przygotowanego package.
  log "Restart Manager: /core/restart niedostępne — próbuję homeassistant.restart jako fallback."
  local code=""
  code="$(curl -sS --connect-timeout 3 --max-time 6 -o /tmp/sbc5_ha_restart.json -w '%{http_code}' -X POST \
    -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{}' \
    http://supervisor/core/api/services/homeassistant/restart 2>/dev/null || true)"
  case "$code" in
    2??)
      log "Restart Manager: Home Assistant przyjął polecenie restartu (HTTP ${code})."
      return 0
      ;;
  esac

  # Sprawdź, czy Core faktycznie zaczął znikać mimo braku odpowiedzi HTTP.
  local i
  for i in 1 2 3 4 5 6 7 8; do
    sleep 1
    if ! core_api_available; then
      log "Restart Manager: połączenie z Core zostało przerwane — traktuję restart jako rozpoczęty."
      return 0
    fi
  done

  log "BŁĄD: Supervisor nie potwierdził restartu Home Assistant. Package bootstrap pozostaje aktywny; wykonaj restart HA ręcznie z Ustawienia → System."
  return 1
}

restart_manager_loop() {
  sleep 17
  while true; do
    publish_restart_requirement false
    sleep "$RESTART_MANAGER_INTERVAL_SECONDS"
  done
}

fan_profile_reconcile_write_state() {
  local status="$1" requested="$2" runtime="$3" max_state="${4:-0}" config_ok="${5:-false}" overlay_ok="${6:-false}" message="${7:-}"
  local tmp="${FAN_PROFILE_RECONCILE_FILE}.tmp.$$" now
  now="$(date -Iseconds)"
  jq -cn \
    --arg status "$status" --arg requested "$requested" --arg runtime "$runtime" \
    --argjson max_state "${max_state:-0}" --argjson config_ok "$config_ok" --argjson overlay_ok "$overlay_ok" \
    --arg boot_id "$CURRENT_BOOT_ID" --arg updated_at "$now" --arg message "$message" \
    '{status:$status,requested_profile:$requested,runtime_profile:$runtime,runtime_max_state:$max_state,config_has_custom1:$config_ok,overlay_present:$overlay_ok,boot_id:$boot_id,updated_at:$updated_at,message:$message}' \
    > "$tmp" 2>/dev/null && mv -f "$tmp" "$FAN_PROFILE_RECONCILE_FILE" || rm -f "$tmp" 2>/dev/null || true
}

fan_profile_custom1_boot_artifacts_state() {
  local config_ok=false overlay_ok=false d
  if ! find_boot_config; then
    printf 'false\tfalse\n'
    return 1
  fi

  if grep -Eq '^[[:space:]]*dtoverlay=rpi5-custom1([[:space:]]|$)' "$BOOT_CFG" 2>/dev/null \
     && grep -Eq '^[[:space:]]*dtparam=cooling_fan=on([[:space:]]|$)' "$BOOT_CFG" 2>/dev/null; then
    config_ok=true
  fi

  for d in "$BOOT_MP/overlays" "$BOOT_MP/slot-A/overlays" "$BOOT_MP/slot-B/overlays"; do
    if [ -s "$d/rpi5-custom1.dtbo" ]; then overlay_ok=true; break; fi
  done
  printf '%s\t%s\n' "$config_ok" "$overlay_ok"
  cleanup_mount
  [ "$config_ok" = "true" ] && [ "$overlay_ok" = "true" ]
}

fan_profile_reconcile_startup() {
  local requested runtime="unknown" dev="" max_state=0 artifacts config_ok=false overlay_ok=false
  local prev_status="" prev_boot="" message=""
  requested="$(ha_requested_profile_code 2>/dev/null || echo factory)"

  if [ "$requested" != "custom1" ]; then
    rm -f "$FAN_PROFILE_RECONCILE_FILE" 2>/dev/null || true
    return 0
  fi

  dev="$(adaptive_pwm_find_device 2>/dev/null || true)"
  if [ -n "$dev" ]; then
    max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"
    case "$max_state" in ''|*[!0-9]*) max_state=0 ;; esac
  fi

  if [ "$max_state" -ge 100 ] 2>/dev/null; then
    fan_profile_reconcile_write_state active custom1 custom1 "$max_state" true true "Siatka 1% jest aktywna; Adaptive PWM może przejąć sterowanie."
    return 0
  fi

  artifacts="$(fan_profile_custom1_boot_artifacts_state 2>/dev/null || true)"
  IFS=$'\t' read -r config_ok overlay_ok <<< "${artifacts:-false\tfalse}"
  [ "$config_ok" = "true" ] || config_ok=false
  [ "$overlay_ok" = "true" ] || overlay_ok=false
  prev_status="$(jq -r '.status // empty' "$FAN_PROFILE_RECONCILE_FILE" 2>/dev/null || true)"
  prev_boot="$(jq -r '.boot_id // empty' "$FAN_PROFILE_RECONCILE_FILE" 2>/dev/null || true)"

  if [ "$config_ok" = "true" ] && [ "$overlay_ok" = "true" ]; then
    if [ -n "$prev_boot" ] && [ "$prev_boot" != "$CURRENT_BOOT_ID" ] && [ "$prev_status" = "repaired_waiting_host_reboot" ]; then
      message="custom1 jest zapisany w config.txt i DTBO istnieje, ale po nowym boot_id kernel nadal zgłasza max_state=${max_state}. Overlay nie został załadowany; nie nadpisuję config.txt ponownie."
      fan_profile_reconcile_write_state overlay_not_loaded_after_reboot custom1 factory "$max_state" true true "$message"
      log "Fan Profile Reconciliation: ${message}"
    else
      message="custom1 jest zapisany w config.txt i DTBO istnieje, ale bieżący kernel nadal pracuje na max_state=${max_state}. Wymagany pełny restart hosta."
      fan_profile_reconcile_write_state overlay_written_not_loaded custom1 factory "$max_state" true true "$message"
      log "Fan Profile Reconciliation: overlay obecny, runtime jeszcze fabryczny (max_state=${max_state}); oczekuję na pełny restart hosta."
    fi
    mark_host_restart_required "$message"
    return 1
  fi

  if [ "$prev_boot" = "$CURRENT_BOOT_ID" ] && [ "$prev_status" = "repaired_waiting_host_reboot" ]; then
    message="Naprawa custom1 została już wykonana w tym boot_id; nie zapisuję config.txt ponownie. Wymagany pełny restart hosta."
    fan_profile_reconcile_write_state repaired_waiting_host_reboot custom1 factory "$max_state" "$config_ok" "$overlay_ok" "$message"
    mark_host_restart_required "$message"
    return 1
  fi

  log "Fan Profile Reconciliation: desired=custom1, runtime max_state=${max_state}, config_ok=${config_ok}, overlay_ok=${overlay_ok} — wykonuję jednorazową naprawę boot overlay."
  load_options
  if write_overlay_profile custom1; then
    commit_custom_curve_config_signature || true
    message="Odbudowano rpi5-custom1 i wpis config.txt. Wymagany pełny restart hosta; po restarcie oczekiwane max_state>=100."
    fan_profile_reconcile_write_state repaired_waiting_host_reboot custom1 factory "$max_state" true true "$message"
    log "Fan Profile Reconciliation: naprawa zakończona; zapis nie będzie powtarzany w bieżącym boot_id."
    return 1
  fi

  message="Nie udało się odbudować custom1/config.txt. Sterowanie pozostaje bezpiecznie po stronie kernela."
  fan_profile_reconcile_write_state repair_failed custom1 factory "$max_state" "$config_ok" "$overlay_ok" "$message"
  log "BŁĄD Fan Profile Reconciliation: ${message}"
  return 1
}

fan_profile_runtime_health_check() {
  local requested dev max_state=0
  requested="$(ha_requested_profile_code 2>/dev/null || echo factory)"
  dev="$(adaptive_pwm_find_device 2>/dev/null || true)"
  [ -n "$dev" ] || return 1
  max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"
  case "$max_state" in ''|*[!0-9]*) max_state=0 ;; esac
  case "$requested" in
    custom1) [ "$max_state" -ge 100 ] 2>/dev/null ;;
    factory) [ "$max_state" -lt 100 ] 2>/dev/null ;;
    *) return 1 ;;
  esac
}

fan_profile_runtime_health_summary() {
  local requested dev max_state=0 rec=""
  requested="$(ha_requested_profile_code 2>/dev/null || echo factory)"
  dev="$(adaptive_pwm_find_device 2>/dev/null || true)"
  if [ -n "$dev" ]; then max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"; fi
  case "$max_state" in ''|*[!0-9]*) max_state=0 ;; esac
  rec="$(jq -r '.status // empty' "$FAN_PROFILE_RECONCILE_FILE" 2>/dev/null || true)"
  printf 'desired=%s; max_state=%s; reconciliation=%s' "$requested" "$max_state" "${rec:-none}"
}

compile_overlay() {
  local profile="$1"
  select_overlay "$profile" || return 1
  case "$profile" in custom15|custom[1-5]) generate_custom_overlay || return 1 ;; esac
  rm -f "$ACTIVE_OVERLAY_DTBO"

  if ! dtc -W no-unit_address_vs_reg -@ -I dts -O dtb \
      -o "$ACTIVE_OVERLAY_DTBO" "$ACTIVE_OVERLAY_DTS" 2>&1; then
    log "BŁĄD: kompilacja ${ACTIVE_OVERLAY_NAME} nie powiodła się."
    return 1
  fi

  if [ ! -s "$ACTIVE_OVERLAY_DTBO" ]; then
    log "BŁĄD: skompilowany DTBO jest pusty."
    return 1
  fi

  log "Overlay ${ACTIVE_OVERLAY_NAME} skompilowany poprawnie ($(wc -c < "$ACTIVE_OVERLAY_DTBO") B)."
}

read_kernel_trip_points() {
  local f tf type val i j tmp out="" prev="__none"
  local -a vals=()
  for f in /sys/class/thermal/thermal_zone0/trip_point_*_type; do
    [ -r "$f" ] || continue
    IFS= read -r type < "$f" 2>/dev/null || true
    [ "$type" = "active" ] || continue
    tf="${f%_type}_temp"; [ -r "$tf" ] || continue
    IFS= read -r val < "$tf" 2>/dev/null || true
    case "$val" in ''|*[!0-9-]*) continue ;; esac
    vals+=("$val")
  done
  for ((i=1;i<${#vals[@]};i++)); do
    tmp="${vals[i]}"; j=$((i-1))
    while [ "$j" -ge 0 ] && [ "${vals[j]}" -gt "$tmp" ] 2>/dev/null; do vals[j+1]="${vals[j]}"; j=$((j-1)); done
    vals[j+1]="$tmp"
  done
  for val in "${vals[@]}"; do
    [ "$val" = "$prev" ] && continue
    [ -n "$out" ] && out+=","; out+="$val"; prev="$val"
  done
  printf '%s\n' "$out"
}

report_active_profile() {
  local trips label="Niedostępny" code="unknown" pretty="Brak danych" last_written="" i selected=0
  trips="$(read_kernel_trip_points)"
  refresh_all_custom_curve_metadata
  last_written="$(cat "$LAST_FAN_PROFILE_FILE" 2>/dev/null || true)"
  [ "$last_written" = "custom15" ] && last_written="custom1"

  # Gdy ostatnio zapisano własną krzywą, jej numer rozstrzyga przypadki,
  # w których progi temperatury są identyczne z jednym z profili fabrycznych.
  case "$last_written" in
    custom[1-5])
      i="${last_written#custom}"
      if [ -n "$trips" ] && [ "$trips" = "${CUSTOM_CURVE_TRIPS[$i]}" ]; then selected="$i"; fi
      ;;
  esac

  if [ "$selected" != "0" ]; then
    load_custom_curve "$selected"
    label="${CUSTOM_CURVE_LABELS[$selected]}"
    code="custom${selected}"
    pretty="${CUSTOM_CURVE_PRETTIES[$selected]}"
  else
    # Najpierw rozpoznaj profile stałe. Jest to istotne dla domyślnej Własnej 1,
    # której progi temperatury pokrywają się ze Stable50 15 pkt.
    case "$trips" in
      "50000,60000,67500,75000") label="Fabryczny"; code="factory"; pretty="50 / 60 / 67.5 / 75 °C" ;;
      "50000,60000,68000,75000") label="Cichy"; code="quiet"; pretty="50 / 60 / 68 / 75 °C" ;;
      "45000,55000,65000,72000") label="Normalny"; code="normal"; pretty="45 / 55 / 65 / 72 °C" ;;
      "40000,50000,60000,68000") label="Chłodny"; code="cool"; pretty="40 / 50 / 60 / 68 °C" ;;
      "40000,44000,47000,49000") label="Poniżej 50°C"; code="sub50"; pretty="40 / 44 / 47 / 49 °C" ;;
      "46000,48500,50000,52500") label="Stabilne 50°C"; code="stable50"; pretty="46 / 48.5 / 50 / 52.5 °C" ;;
      "44000,45000,46000,47000,48000,49000,50000,51000,52000,53000")
        label="Stabilne 50°C · 10 pkt"; code="stable50_10"; pretty="44 / 45 / 46 / 47 / 48 / 49 / 50 / 51 / 52 / 53 °C" ;;
      "44000,45000,46000,47000,48000,48500,49000,49500,50000,50500,51000,51500,52000,52500,53000")
        label="Stabilne 50°C · 15 pkt"; code="stable50_15"; pretty="44 / 45 / 46 / 47 / 48 / 48.5 / 49 / 49.5 / 50 / 50.5 / 51 / 51.5 / 52 / 52.5 / 53 °C" ;;
      "") ;;
      *)
        # Jeśli zestaw progów nie jest profilem stałym, sprawdź pięć krzywych.
        for i in 1 2 3 4 5; do
          if [ "$trips" = "${CUSTOM_CURVE_TRIPS[$i]}" ]; then selected="$i"; break; fi
        done
        if [ "$selected" != "0" ]; then
          load_custom_curve "$selected"
          label="${CUSTOM_CURVE_LABELS[$selected]}"; code="custom${selected}"; pretty="${CUSTOM_CURVE_PRETTIES[$selected]}"
        else
          label="Niestandardowy"; code="custom"
          pretty="$(echo "$trips" | awk -F, '{for (i=1;i<=NF;i++){if(i>1)printf " / ";printf "%.1f",$i/1000} printf " °C"}')"
        fi
        ;;
    esac
  fi
  if [ "$code" = "factory" ] && [ -e "$FACTORY_RESTORE_PENDING_FILE" ]; then
    rm -f "$FACTORY_RESTORE_PENDING_FILE" 2>/dev/null || true
    log "Fabryczny profil Active Cooler jest aktywny — zakończono awaryjny handoff i usunięto marker oczekującego restartu."
  fi
  ha_set_active_profile "$label" "$code" "$pretty"

  # v2.6.7: profil żądany jest trwałym wyborem użytkownika zapisanym w /data,
  # a sensor.sbc5_active_fan_profile opisuje wyłącznie stan faktycznie załadowany
  # przez kernel. Nigdy nie nadpisujemy żądanego wyboru stanem runtime.
  local requested_code requested_label dev max_state=0 pending=false activation_state="ready" activation_reason="active" message=""
  requested_code="$(ha_requested_profile_code)"
  requested_label="$(ha_requested_profile_label "$requested_code")"
  dev="$(adaptive_pwm_find_device 2>/dev/null || true)"
  if [ -n "$dev" ]; then
    max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"
    case "$max_state" in ''|*[!0-9]*) max_state=0 ;; esac
  fi

  if [ "$requested_code" = "custom1" ] && [ "$max_state" -lt 100 ] 2>/dev/null; then
    local reconcile_status
    reconcile_status="$(jq -r '.status // empty' "$FAN_PROFILE_RECONCILE_FILE" 2>/dev/null || true)"
    pending=true; activation_state="pending_host_reboot"
    case "$reconcile_status" in
      repaired_waiting_host_reboot)
        activation_reason="overlay_repaired_pending_reboot"
        message="Naprawiono rpi5-custom1/config.txt; pełny restart hosta aktywuje siatkę 1%. Aktualnie max_state=${max_state}." ;;
      overlay_written_not_loaded)
        activation_reason="overlay_written_not_loaded"
        message="Overlay custom1 jest zapisany, ale nie został jeszcze wczytany przez kernel. Wymagany pełny restart hosta." ;;
      overlay_not_loaded_after_reboot)
        activation_reason="overlay_not_loaded_after_reboot"
        message="Overlay custom1 istnieje, lecz nie został załadowany także po restarcie. Sprawdź diagnostykę boot/config.txt; sterowanie pozostaje po stronie kernela." ;;
      repair_failed)
        activation_reason="overlay_repair_failed"
        message="Nie udało się odbudować profilu custom1. Sterowanie pozostaje po stronie kernela; sprawdź log i dostęp do partycji boot." ;;
      *)
        activation_reason="one_percent_grid_inactive"
        message="custom1 jest żądany, ale cooling_device ma max_state=${max_state}; siatka 1% wymaga pełnego restartu hosta." ;;
    esac
  elif [ "$requested_code" != "$code" ]; then
    pending=true; activation_state="pending_host_reboot"; activation_reason="profile_mismatch"
    message="Profil żądany ${requested_label} nie jest jeszcze aktywny w kernelu. Wykonaj pełny restart hosta."
  else
    message="Profil żądany i runtime kernela są zgodne."
  fi

  if [ -n "${SUPERVISOR_TOKEN:-}" ]; then
    local req_payload act_payload now
    now="$(date '+%Y-%m-%d %H:%M:%S')"
    req_payload="$(jq -cn \
      --arg state "$requested_label" --arg code "$requested_code" --arg runtime "$label" --arg runtime_code "$code" \
      --argjson pending "$pending" --argjson max "$max_state" --arg updated "$now" \
      '{state:$state,attributes:{friendly_name:"SBC5 żądany profil chłodzenia",icon:"mdi:target",profile_code:$code,runtime_profile:$runtime,runtime_profile_code:$runtime_code,pending_host_reboot:$pending,runtime_max_state:$max,last_update:$updated}}')"
    for profile_entity in sensor.sbc5_requested_fan_profile sensor.rpi5_requested_fan_profile; do
      curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$req_payload" \
        "http://supervisor/core/api/states/${profile_entity}" >/dev/null 2>&1 || true
    done

    act_payload="$(jq -cn \
      --arg state "$activation_state" --arg reason "$activation_reason" --arg desired "$requested_label" --arg desired_code "$requested_code" \
      --arg runtime "$label" --arg runtime_code "$code" --arg message "$message" --argjson max "$max_state" --arg updated "$now" \
      '{state:$state,attributes:{friendly_name:"SBC5 aktywacja profilu chłodzenia",icon:(if $state=="ready" then "mdi:check-circle-outline" else "mdi:restart-alert" end),reason:$reason,desired_profile:$desired,desired_profile_code:$desired_code,runtime_profile:$runtime,runtime_profile_code:$runtime_code,runtime_max_state:$max,message:$message,last_update:$updated}}')"
    for profile_entity in sensor.sbc5_fan_profile_activation sensor.rpi5_fan_profile_activation; do
      curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$act_payload" \
        "http://supervisor/core/api/states/${profile_entity}" >/dev/null 2>&1 || true
    done
  fi

  if [ "$pending" = "true" ]; then
    log "Fan Profile: żądany=${requested_code}; runtime=${code}; max_state=${max_state}; status=pending_host_reboot; reason=${activation_reason}."
  fi
}

host_pid_boot_root() {
  local root rel pid1_comm
  pid1_comm="$(cat /proc/1/comm 2>/dev/null | tr -d '\r\n' || true)"

  # HAOS zwykle montuje hassos-boot jako /mnt/boot, ale zachowujemy kilka
  # alternatyw dla innych układów i wersji Supervisora.
  for root in \
    /proc/1/root/mnt/boot \
    /proc/1/root/boot/firmware \
    /proc/1/root/boot \
    /proc/1/root/flash \
    /proc/1/root/run/host/boot
  do
    [ -d "$root" ] || continue
    rel="$(boot_config_rel_in_root "$root" 2>/dev/null || true)"
    [ -n "$rel" ] || continue
    printf '%s|%s|%s\n' "$root" "$rel" "${pid1_comm:-pid1}"
    return 0
  done
  return 1
}

host_nsenter_boot_info() {
  command -v nsenter >/dev/null 2>&1 || return 1
  nsenter -t 1 -m -r -- sh -c '
    for root in /mnt/boot /boot/firmware /boot /flash /run/host/boot; do
      [ -d "$root" ] || continue
      for rel in config.txt usercfg.txt firmware/config.txt boot/config.txt slot-A/config.txt slot-B/config.txt; do
        [ -r "$root/$rel" ] || continue
        printf "%s|%s\n" "$root" "$rel"
        exit 0
      done
    done
    exit 1
  ' 2>/dev/null
}

nsenter_copy_boot_rel() {
  local host_root="$1" rel="$2" dst="$3"
  command -v nsenter >/dev/null 2>&1 || return 1
  case "$rel" in /*|*'..'*) return 1 ;; esac
  mkdir -p "$(dirname "$dst")" 2>/dev/null || return 1
  if nsenter -t 1 -m -r -- sh -c 'cat -- "$1/$2"' sh "${host_root%/}" "$rel" > "$dst" 2>/dev/null; then
    return 0
  fi
  rm -f "$dst" 2>/dev/null || true
  return 1
}

host_boot_probe_log() {
  local pid1_comm proc_boot_dir="nie" proc_cfg="nie" proc_read="nie" proc_write="nie"
  local ns_boot_dir="nie" ns_cfg="nie" ns_read="nie" ns_mount="N/D" ns_files="N/D"
  pid1_comm="$(cat /proc/1/comm 2>/dev/null | tr -d '\r\n' || true)"

  [ -d /proc/1/root/mnt/boot ] && proc_boot_dir="tak"
  [ -e /proc/1/root/mnt/boot/config.txt ] && proc_cfg="tak"
  [ -r /proc/1/root/mnt/boot/config.txt ] && proc_read="tak"
  [ -w /proc/1/root/mnt/boot/config.txt ] && proc_write="tak"

  if command -v nsenter >/dev/null 2>&1; then
    nsenter -t 1 -m -r -- test -d /mnt/boot >/dev/null 2>&1 && ns_boot_dir="tak"
    nsenter -t 1 -m -r -- test -e /mnt/boot/config.txt >/dev/null 2>&1 && ns_cfg="tak"
    nsenter -t 1 -m -r -- test -r /mnt/boot/config.txt >/dev/null 2>&1 && ns_read="tak"
    ns_mount="$(nsenter -t 1 -m -r -- sh -c 'findmnt -rn -T /mnt/boot -o SOURCE,FSTYPE,OPTIONS 2>/dev/null | head -n1' 2>/dev/null || true)"
    [ -n "$ns_mount" ] || ns_mount="N/D"
    ns_files="$(nsenter -t 1 -m -r -- sh -c 'ls -1 /mnt/boot 2>/dev/null | head -n 12 | tr "\n" "," | sed "s/,$//"' 2>/dev/null || true)"
    [ -n "$ns_files" ] || ns_files="N/D"
  fi

  local ns_info=""
  ns_info="$(host_nsenter_boot_info 2>/dev/null || true)"
  log "Host Probe: PID1=${pid1_comm:-?}; proc_boot=${proc_boot_dir}; proc_config=${proc_cfg}; proc_R=${proc_read}; proc_W=${proc_write}; ns_boot=${ns_boot_dir}; ns_config=${ns_cfg}; ns_R=${ns_read}."
  log "Host Probe: mount=${ns_mount}; pliki_boot=${ns_files}; ns_detect=${ns_info:-N/D}."
}

find_boot_config() {
  local part mp host_info host_root host_rel host_pid1 root rel mounted safe_name
  BOOT_CFG=""; BOOT_MP=""; BOOT_PART=""; BOOT_OWN_MOUNT="false"

  # Najpierw host root przez PID namespace.
  host_info="$(host_pid_boot_root 2>/dev/null || true)"
  if [ -n "$host_info" ]; then
    IFS='|' read -r host_root host_rel host_pid1 <<< "$host_info"
    if [ -r "$host_root/$host_rel" ] && [ -w "$host_root/$host_rel" ]; then
      BOOT_CFG="$host_root/$host_rel"
      BOOT_MP="$host_root"
      BOOT_PART="host:${host_root#/proc/1/root} (${host_pid1})"
      BOOT_OWN_MOUNT="false"
      return 0
    fi
  fi

  # Potem już istniejące mounty widoczne w kontenerze.
  for root in /mnt/boot /boot/firmware /boot /flash /run/host/boot /host/boot; do
    [ -d "$root" ] || continue
    rel="$(boot_config_rel_in_root "$root" 2>/dev/null || true)"
    [ -n "$rel" ] || continue
    if [ -r "$root/$rel" ] && [ -w "$root/$rel" ]; then
      BOOT_CFG="$root/$rel"; BOOT_MP="$root"; BOOT_PART="$root"; BOOT_OWN_MOUNT="false"
      return 0
    fi
  done

  # Na końcu bezpiecznie identyfikujemy partycję boot po LABEL/PARTLABEL i FAT.
  while IFS= read -r part; do
    [ -n "$part" ] || continue
    part="$(readlink -f "$part" 2>/dev/null || printf '%s' "$part")"
    [ -b "$part" ] || continue

    mounted="$(findmnt -rn -S "$part" -o TARGET 2>/dev/null | head -n1 || true)"
    if [ -n "$mounted" ] && [ -d "$mounted" ]; then
      rel="$(boot_config_rel_in_root "$mounted" 2>/dev/null || true)"
      if [ -n "$rel" ] && [ -w "$mounted/$rel" ]; then
        BOOT_CFG="$mounted/$rel"; BOOT_MP="$mounted"; BOOT_PART="$part"; BOOT_OWN_MOUNT="false"
        return 0
      fi
    fi

    safe_name="$(basename "$part" | tr -c 'A-Za-z0-9_.-' '_')"
    mp="/tmp/rpi5fan_${safe_name}"
    mkdir -p "$mp"
    umount "$mp" >/dev/null 2>&1 || true
    if mount "$part" "$mp" >/dev/null 2>&1; then
      rel="$(boot_config_rel_in_root "$mp" 2>/dev/null || true)"
      if [ -n "$rel" ] && [ -w "$mp/$rel" ]; then
        BOOT_CFG="$mp/$rel"; BOOT_MP="$mp"; BOOT_PART="$part"; BOOT_OWN_MOUNT="true"
        return 0
      fi
      umount "$mp" >/dev/null 2>&1 || true
    fi
  done < <(boot_device_candidates | awk 'NF && !seen[$0]++' | head -n 24)

  return 1
}

cleanup_mount() {
  if [ -n "${BOOT_MP:-}" ]; then
    sync
    if [ "${BOOT_OWN_MOUNT:-false}" = "true" ]; then
      umount "$BOOT_MP" >/dev/null 2>&1 || true
    fi
    BOOT_MP=""
    BOOT_OWN_MOUNT="false"
  fi
}

make_backup() {
  if [ ! -f "${BOOT_CFG}.rpi5fan.bak" ]; then
    cp "$BOOT_CFG" "${BOOT_CFG}.rpi5fan.bak"
    log "Utworzono kopię config.txt: ${BOOT_CFG}.rpi5fan.bak"
  fi
}

system_config_backup() {
  local stamp backup latest
  mkdir -p "$SYSTEM_BACKUP_DIR"
  stamp="$(date '+%Y%m%d_%H%M%S')"
  backup="$SYSTEM_BACKUP_DIR/config.txt.before_system_${stamp}_$$.bak"
  latest="${BOOT_CFG}.rpi5cc-system.bak"
  cp "$BOOT_CFG" "$backup" || return 1
  cp "$BOOT_CFG" "$latest" || return 1
  # Zachowaj maksymalnie 10 historycznych kopii w trwałych danych aplikacji.
  ls -1t "$SYSTEM_BACKUP_DIR"/config.txt.before_system_*.bak 2>/dev/null | tail -n +11 | xargs -r rm -f --
  log "System Config: backup przed zmianą: $backup oraz $latest"
}

strip_system_config_block() {
  local src="$1" dst="$2"
  awk -v begin="$SYSTEM_MARK_BEGIN" -v end="$SYSTEM_MARK_END" '
    $0 == begin {skip=1; next}
    $0 == end   {skip=0; next}
    skip {next}
    {print}
  ' "$src" > "$dst"
}

unmanaged_config_key_exists() {
  local file="$1" key="$2"
  grep -Eq "^[[:space:]]*${key}[[:space:]]*=" "$file" 2>/dev/null
}

apply_system_config() {
  local cpu_mode="$1" arm_mhz="$2" ovd_uv="$3" usb_mode="$4" confirmed="$5"
  local base_tmp new_tmp write_cpu="false" write_usb="false" usb_value="" warn=""

  [ "$confirmed" = "true" ] || {
    log "System Config: ODRZUCONO — wymagane jawne confirm=true."
    return 1
  }

  case "$cpu_mode" in factory|manual) ;; *) log "System Config: BŁĄD cpu_mode=$cpu_mode (dozwolone factory/manual)."; return 1 ;; esac
  case "$usb_mode" in auto|high|low) ;; *) log "System Config: BŁĄD usb_mode=$usb_mode (dozwolone auto/high/low)."; return 1 ;; esac

  if [ "$cpu_mode" = "manual" ]; then
    [[ "$arm_mhz" =~ ^[0-9]+$ ]] || { log "System Config: arm_freq musi być liczbą całkowitą."; return 1; }
    [[ "$ovd_uv" =~ ^[0-9]+$ ]] || { log "System Config: over_voltage_delta musi być liczbą całkowitą µV."; return 1; }
    [ "$arm_mhz" -ge 2400 ] && [ "$arm_mhz" -le 2800 ] || { log "System Config: arm_freq poza bezpiecznym zakresem v1.9.x: 2400–2800 MHz."; return 1; }
    [ $((arm_mhz % 50)) -eq 0 ] || { log "System Config: arm_freq musi być wielokrotnością 50 MHz."; return 1; }
    [ "$ovd_uv" -ge 0 ] && [ "$ovd_uv" -le 50000 ] || { log "System Config: over_voltage_delta poza zakresem v1.9.x: 0–50000 µV."; return 1; }
    [ $((ovd_uv % 5000)) -eq 0 ] || { log "System Config: over_voltage_delta musi być wielokrotnością 5000 µV."; return 1; }
    write_cpu="true"
    if [ "$arm_mhz" -gt 2400 ] && [ "$ovd_uv" -eq 0 ]; then
      warn="; UWAGA: OC bez dodatniego over_voltage_delta może być niestabilne"
    fi
  fi

  collect_system_power_info || true
  case "$usb_mode" in
    auto) write_usb="false" ;;
    high)
      if ! [[ "${SYS_POWER_MAX_CURRENT_MA:-}" =~ ^[0-9]+$ ]] || [ "${SYS_POWER_MAX_CURRENT_MA:-0}" -lt 5000 ]; then
        log "System Config: ODRZUCONO usb=high — nie wykryto zasilania 5 A. Użyj Auto albo zapewnij prawidłowe 5 A."
        return 1
      fi
      write_usb="true"; usb_value="1" ;;
    low) write_usb="true"; usb_value="0" ;;
  esac

  if ! find_boot_config; then
    log "System Config: BŁĄD — brak zapisywalnego config.txt."
    return 1
  fi
  [ -w "$BOOT_CFG" ] || { log "System Config: BŁĄD — config.txt nie jest zapisywalny: $BOOT_CFG"; cleanup_mount; return 1; }

  base_tmp="${BOOT_CFG}.rpi5cc.base.$$"
  new_tmp="${BOOT_CFG}.rpi5cc.new.$$"
  strip_system_config_block "$BOOT_CFG" "$base_tmp"

  # Nie nadpisuj cudzych ręcznych ustawień. Zarządzamy wyłącznie własnym blokiem.
  if [ "$write_cpu" = "true" ]; then
    if unmanaged_config_key_exists "$base_tmp" arm_freq || unmanaged_config_key_exists "$base_tmp" over_voltage_delta; then
      log "System Config: ODRZUCONO — arm_freq/over_voltage_delta istnieje poza blokiem Control Center. Usuń konflikt ręcznie albo użyj trybu Fabryczne."
      rm -f "$base_tmp" "$new_tmp"; cleanup_mount; return 1
    fi
  fi
  if [ "$write_usb" = "true" ] && unmanaged_config_key_exists "$base_tmp" usb_max_current_enable; then
    log "System Config: ODRZUCONO — usb_max_current_enable istnieje poza blokiem Control Center. Usuń konflikt ręcznie albo wybierz Auto."
    rm -f "$base_tmp" "$new_tmp"; cleanup_mount; return 1
  fi

  system_config_backup || { log "System Config: BŁĄD tworzenia backupu — zapis anulowany."; rm -f "$base_tmp" "$new_tmp"; cleanup_mount; return 1; }

  cp "$base_tmp" "$new_tmp"
  if [ "$write_cpu" = "true" ] || [ "$write_usb" = "true" ]; then
    cat >> "$new_tmp" <<EOF

$SYSTEM_MARK_BEGIN
# Zarządzane przez SBC5 Control Center ${APP_VERSION}. Zmiany obowiązują po restarcie hosta.
[pi5]
EOF
    if [ "$write_cpu" = "true" ]; then
      printf 'arm_freq=%s\n' "$arm_mhz" >> "$new_tmp"
      printf 'over_voltage_delta=%s\n' "$ovd_uv" >> "$new_tmp"
    fi
    if [ "$write_usb" = "true" ]; then
      printf 'usb_max_current_enable=%s\n' "$usb_value" >> "$new_tmp"
    fi
    cat >> "$new_tmp" <<EOF
[all]
$SYSTEM_MARK_END
EOF
  fi

  # Sprawdź, czy markery są spójne i czy wynik nie jest pusty.
  [ -s "$new_tmp" ] || { log "System Config: BŁĄD walidacji — pusty plik wynikowy."; rm -f "$base_tmp" "$new_tmp"; cleanup_mount; return 1; }
  if [ "$write_cpu" = "true" ] || [ "$write_usb" = "true" ]; then
    [ "$(grep -Fc "$SYSTEM_MARK_BEGIN" "$new_tmp")" -eq 1 ] && [ "$(grep -Fc "$SYSTEM_MARK_END" "$new_tmp")" -eq 1 ] || {
      log "System Config: BŁĄD walidacji markerów — zapis anulowany."; rm -f "$base_tmp" "$new_tmp"; cleanup_mount; return 1;
    }
  fi

  cp "$new_tmp" "$BOOT_CFG" || { log "System Config: BŁĄD zapisu config.txt."; rm -f "$base_tmp" "$new_tmp"; cleanup_mount; return 1; }
  sync
  rm -f "$base_tmp" "$new_tmp" "$BOOT_CONFIG_CACHE_FILE"

  rm -f "$SYSTEM_DEFAULTS_LOCK_FILE" 2>/dev/null || true
  log "System Config: zapis zakończony; cpu=${cpu_mode} arm_freq=${arm_mhz}MHz over_voltage_delta=${ovd_uv}µV; usb=${usb_mode}${warn}."
  mark_host_restart_required "Zmieniono konfigurację CPU/USB w config.txt. Firmware zastosuje nowe wartości dopiero po pełnym restarcie Raspberry Pi 5."
  cleanup_mount
  collect_system_power_info || true
  publish_telemetry_snapshot || true
}

restore_system_config_backup() {
  local src=""
  if ! find_boot_config; then
    log "System Config Restore: brak config.txt."
    return 1
  fi
  if [ -f "${BOOT_CFG}.rpi5cc-system.bak" ]; then
    src="${BOOT_CFG}.rpi5cc-system.bak"
  else
    src="$(ls -1t "$SYSTEM_BACKUP_DIR"/config.txt.before_system_*.bak 2>/dev/null | head -n1 || true)"
  fi
  [ -n "$src" ] && [ -r "$src" ] || { log "System Config Restore: brak kopii systemowej."; cleanup_mount; return 1; }
  # Skopiuj źródło do /tmp zanim utworzymy backup bieżącego stanu; backup na partycji boot
  # jest rotowany i nie może nadpisać pliku, który właśnie przywracamy.
  local restore_tmp="/tmp/rpi5cc_restore_$$.bak"
  cp "$src" "$restore_tmp" || { log "System Config Restore: nie udało się przygotować kopii do odtworzenia."; cleanup_mount; return 1; }
  # Backup aktualnego stanu przed przywróceniem też jest obowiązkowy.
  system_config_backup || { log "System Config Restore: nie udało się zabezpieczyć bieżącego config.txt."; rm -f "$restore_tmp"; cleanup_mount; return 1; }
  cp "$restore_tmp" "$BOOT_CFG" || { log "System Config Restore: BŁĄD zapisu."; rm -f "$restore_tmp"; cleanup_mount; return 1; }
  rm -f "$restore_tmp"
  sync
  rm -f "$BOOT_CONFIG_CACHE_FILE"
  log "System Config Restore: przywrócono $src. Wymagany pełny restart hosta."
  mark_host_restart_required "Przywrócono poprzedni config.txt z kopii System Config. Zmiana zacznie obowiązywać po pełnym restarcie hosta."
  cleanup_mount
  publish_telemetry_snapshot || true
}


strip_config_manager_include_block() {
  local src="$1" dst="$2"
  awk -v begin="$CONFIG_MANAGER_MARK_BEGIN" -v end="$CONFIG_MANAGER_MARK_END" -v managed="$CONFIG_MANAGER_FILENAME" '
    $0 == begin {skip=1; next}
    $0 == end   {skip=0; next}
    skip {next}
    $0 ~ "^[[:space:]]*include[[:space:]]+" managed "[[:space:]]*$" {next}
    {print}
  ' "$src" > "$dst"
}

restore_rpi5_app_defaults() {
  local confirmed="$1" managed cpu_profile_file tmp1 tmp2 tmp3
  [ "$confirmed" = "true" ] || {
    log "SBC5 Factory Recovery: ODRZUCONO — wymagane jawne confirm=true."
    return 1
  }
  [ ! -e "$FAN_CALIBRATION_LOCK_FILE" ] || {
    log "SBC5 Factory Recovery: ODRZUCONO — trwa kalibracja Active Cooler."
    return 1
  }
  find_boot_config || { log "SBC5 Factory Recovery: brak zapisywalnego config.txt."; return 1; }
  [ -w "$BOOT_CFG" ] || { log "SBC5 Factory Recovery: config.txt nie jest zapisywalny: $BOOT_CFG"; cleanup_mount; return 1; }

  managed="$(dirname "$BOOT_CFG")/$CONFIG_MANAGER_FILENAME"
  cpu_profile_file="$(dirname "$BOOT_CFG")/$CPU_PROFILE_FILENAME"
  system_config_backup || { log "SBC5 Factory Recovery: nie udało się wykonać backupu config.txt."; cleanup_mount; return 1; }
  config_manager_backup_managed "$managed" || { log "SBC5 Factory Recovery: nie udało się wykonać backupu $CONFIG_MANAGER_FILENAME."; cleanup_mount; return 1; }

  tmp1="${BOOT_CFG}.rpi5cc-defaults1.$$"
  tmp2="${BOOT_CFG}.rpi5cc-defaults2.$$"
  tmp3="${BOOT_CFG}.rpi5cc-defaults3.$$"
  strip_system_config_block "$BOOT_CFG" "$tmp1" || { rm -f "$tmp1" "$tmp2" "$tmp3"; cleanup_mount; return 1; }
  strip_config_manager_include_block "$tmp1" "$tmp2" || { rm -f "$tmp1" "$tmp2" "$tmp3"; cleanup_mount; return 1; }
  strip_cpu_profile_include_block "$tmp2" "$tmp3" || { rm -f "$tmp1" "$tmp2" "$tmp3"; cleanup_mount; return 1; }
  [ -s "$tmp3" ] || { log "SBC5 Factory Recovery: walidacja dała pusty config.txt — zapis anulowany."; rm -f "$tmp1" "$tmp2" "$tmp3"; cleanup_mount; return 1; }

  cp "$tmp3" "$BOOT_CFG" || { log "SBC5 Factory Recovery: błąd zapisu config.txt."; rm -f "$tmp1" "$tmp2" "$tmp3"; cleanup_mount; return 1; }
  rm -f "$tmp1" "$tmp2" "$tmp3"
  rm -f "$managed" "$cpu_profile_file" 2>/dev/null || true
  : > "$SYSTEM_DEFAULTS_LOCK_FILE"
  rm -f "$BOOT_CONFIG_CACHE_FILE" "$CONFIG_MANAGER_ABSENT_FILE"
  sync

  log "SBC5 Factory Recovery: usunięto wyłącznie bloki CPU/USB, CPU Profile Manager i Config Manager zarządzane przez SBC5 Control Center; ręczne wpisy użytkownika pozostawiono bez zmian."
  log "SBC5 Factory Recovery: automatyczna synchronizacja config.txt z zakładki Konfiguracja jest zablokowana do jawnego wznowienia."
  mark_host_restart_required "Przywrócono domyślne ustawienia SBC5 w zakresie zmian zarządzanych przez SBC5 Control Center. Wymagany pełny restart hosta."
  cleanup_mount
  publish_telemetry_snapshot || true
  return 0
}

resume_managed_rpi5_config() {
  local confirmed="$1"
  [ "$confirmed" = "true" ] || { log "SBC5 Managed Config: wznowienie odrzucone — wymagane confirm=true."; return 1; }
  rm -f "$SYSTEM_DEFAULTS_LOCK_FILE"
  log "SBC5 Managed Config: ponownie zezwolono aplikacji na jawne zmiany CPU/USB/config.txt."
  return 0
}


strip_cpu_profile_include_block() {
  local src="$1" dst="$2"
  awk -v begin="$CPU_PROFILE_MARK_BEGIN" -v end="$CPU_PROFILE_MARK_END" -v managed="$CPU_PROFILE_FILENAME" '
    $0 == begin {skip=1; next}
    $0 == end   {skip=0; next}
    skip {next}
    $0 ~ "^[[:space:]]*include[[:space:]]+" managed "[[:space:]]*$" {next}
    {print}
  ' "$src" > "$dst"
}

cpu_profile_strip_owned_manager_keys() {
  local managed="$1" tmp
  [ -f "$managed" ] || return 0
  grep -q 'SBC5 Control Center' "$managed" 2>/dev/null || return 0
  tmp="${managed}.cpu-strip.$$"
  awk '
    function lhs_name(s, a) { a=s; sub(/=.*/,"",a); gsub(/^[ \t]+|[ \t]+$/,"",a); return a }
    {
      if (index($0,"=")>0) {
        k=lhs_name($0)
        if (k=="arm_freq" || k=="arm_freq_min" || k=="over_voltage" || k=="over_voltage_min" ||
            k=="over_voltage_delta" || k=="force_turbo" || k=="initial_turbo" || k=="temp_limit") next
      }
      print
    }
  ' "$managed" > "$tmp" || { rm -f "$tmp"; return 1; }
  if cmp -s "$tmp" "$managed"; then rm -f "$tmp"; return 0; fi
  mv "$tmp" "$managed"
  return 0
}

cpu_profile_ensure_include() {
  local cfg="$1" base tmp
  grep -Eq '^[[:space:]]*include[[:space:]]+sbc5cc-cpu-profile\.txt[[:space:]]*$' "$cfg" 2>/dev/null && return 0
  base="${cfg}.sbc5cpu-base.$$"
  tmp="${cfg}.sbc5cpu-new.$$"
  strip_cpu_profile_include_block "$cfg" "$base" || return 1
  cp "$base" "$tmp" || { rm -f "$base"; return 1; }
  cat >> "$tmp" <<EOF

$CPU_PROFILE_MARK_BEGIN
# Dedykowany profil CPU/OC. Działa niezależnie od ogólnego Config.txt Managera.
[all]
include $CPU_PROFILE_FILENAME
$CPU_PROFILE_MARK_END
EOF
  [ -s "$tmp" ] || { rm -f "$base" "$tmp"; return 1; }
  cp "$tmp" "$cfg" || { rm -f "$base" "$tmp"; return 1; }
  rm -f "$base" "$tmp"
  return 0
}

cpu_profile_preset_arm_freq() {
  case "$1" in
    mild) printf '2500\n' ;;
    balanced) printf '2600\n' ;;
    performance) printf '2800\n' ;;
    experimental) printf '3000\n' ;;
    *) printf '\n' ;;
  esac
}

cpu_profile_preset_config_json() {
  local p="$1" arm="auto"
  case "$p" in
    mild) arm="2500" ;;
    balanced) arm="2600" ;;
    performance) arm="2800" ;;
    experimental) arm="3000" ;;
    factory) arm="auto" ;;
    *) return 1 ;;
  esac
  jq -cn --arg arm "$arm" '{arm_freq:$arm,arm_freq_min:"auto",over_voltage:"auto",over_voltage_min:"auto",over_voltage_delta:"auto",force_turbo:"auto",initial_turbo:"auto",temp_limit:"auto"}'
}

cpu_profile_from_arm_freq() {
  case "$1" in
    2500) printf 'mild\n' ;;
    2600) printf 'balanced\n' ;;
    2800) printf 'performance\n' ;;
    3000) printf 'experimental\n' ;;
    '') printf 'factory\n' ;;
    *) printf 'advanced\n' ;;
  esac
}

cpu_profile_read_file_arm_freq() {
  local file="$1"
  [ -r "$file" ] || return 0
  awk -F= '/^[[:space:]]*arm_freq[[:space:]]*=/ {v=$2; gsub(/[[:space:]]/,"",v); print v; exit}' "$file" 2>/dev/null || true
}

cpu_profile_normalized_copy() {
  local src="$1" dst="$2"
  [ -r "$src" ] || return 1
  # Numer wersji aplikacji w komentarzu profilu nie zmienia semantyki boot.
  # Starsze wydania wpisywały go do nagłówka; normalizacja zapobiega
  # fałszywemu restartowi hosta po samej aktualizacji SBC5.
  sed -E 's/^# SBC5 Control Center [0-9]+\.[0-9]+\.[0-9]+([^ ]*) — dedykowany profil CPU\/OC$/# SBC5 Control Center — dedykowany profil CPU\/OC/' "$src" > "$dst"
}

cpu_profile_semantically_equal() {
  local a="$1" b="$2" na nb rc=1
  [ -r "$a" ] && [ -r "$b" ] || return 1
  na="/tmp/sbc5cc-cpu-semantic-a-$$-$RANDOM"
  nb="/tmp/sbc5cc-cpu-semantic-b-$$-$RANDOM"
  if cpu_profile_normalized_copy "$a" "$na" && cpu_profile_normalized_copy "$b" "$nb" && cmp -s "$na" "$nb"; then
    rc=0
  fi
  rm -f "$na" "$nb"
  return "$rc"
}

cpu_profile_state_write() {
  local enabled="$1" profile="$2" source="$3" explicit="$4" cfg_json="$5" tmp
  case "$profile" in factory|mild|balanced|performance|experimental|advanced) ;; *) return 1 ;; esac
  tmp="${CPU_PROFILE_STATE_FILE}.tmp.$$"
  jq -n \
    --argjson schema "$CPU_PROFILE_STATE_SCHEMA" \
    --argjson enabled "$enabled" \
    --arg profile "$profile" \
    --arg source "$source" \
    --argjson explicit "$explicit" \
    --argjson config "$cfg_json" \
    --arg updated "$(date '+%Y-%m-%d %H:%M:%S')" \
    '{schema:$schema,enabled:$enabled,requested_profile:$profile,requested_config:$config,source:$source,explicit:$explicit,updated:$updated}' \
    > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$CPU_PROFILE_STATE_FILE"
}

cpu_profile_state_bootstrap() {
  # v2.7.2: once created, this file is the authoritative requested CPU profile.
  # This prevents transient/default options.json values during app startup from
  # destructively reverting a previously requested OC profile to Factory.
  if [ -r "$CPU_PROFILE_STATE_FILE" ] && jq -e \
      --argjson schema "$CPU_PROFILE_STATE_SCHEMA" \
      '(.schema == $schema) and (.requested_profile|IN("factory","mild","balanced","performance","experimental","advanced")) and ((.requested_config // {})|type=="object")' \
      "$CPU_PROFILE_STATE_FILE" >/dev/null 2>&1; then
    return 0
  fi

  local enabled=false option_profile=factory option_cfg='{}' detected_arm='' detected_profile='' cpu_file=''
  if [ -r "$OPTIONS_FILE" ]; then
    enabled="$(jq -r '.section_cpu_enabled // false' "$OPTIONS_FILE" 2>/dev/null || echo false)"
    case "$enabled" in true|false) ;; *) enabled=false ;; esac
    option_profile="$(jq -r '.config_cpu_profile // "factory"' "$OPTIONS_FILE" 2>/dev/null || echo factory)"
    option_cfg="$(jq -c '.config_cpu // {}' "$OPTIONS_FILE" 2>/dev/null || echo '{}')"
  fi
  case "$option_profile" in factory|mild|balanced|performance|experimental|advanced) ;; *) option_profile=factory ;; esac

  # If 2.7.0 already left a dedicated CPU profile on boot, preserve what is
  # actually configured instead of trusting a transient Factory default.
  if find_boot_config >/dev/null 2>&1; then
    cpu_file="$(dirname "$BOOT_CFG")/$CPU_PROFILE_FILENAME"
    detected_arm="$(cpu_profile_read_file_arm_freq "$cpu_file")"
    if [ -n "$detected_arm" ]; then detected_profile="$(cpu_profile_from_arm_freq "$detected_arm")"; fi
    cleanup_mount
  fi

  if [ -n "$detected_profile" ] && [ "$detected_profile" != "factory" ]; then
    if [ "$detected_profile" = "advanced" ]; then
      option_profile=advanced
      option_cfg="$(jq -cn --arg arm "$detected_arm" '{arm_freq:$arm,arm_freq_min:"auto",over_voltage:"auto",over_voltage_min:"auto",over_voltage_delta:"auto",force_turbo:"auto",initial_turbo:"auto",temp_limit:"auto"}')"
    else
      option_profile="$detected_profile"
    fi
    enabled=true
    cpu_profile_state_write "$enabled" "$option_profile" "boot-profile-import" false "$option_cfg" || true
    log "CPU Profile Manager: zaimportowano trwały stan z istniejącego $CPU_PROFILE_FILENAME (profil=${option_profile}, arm_freq=${detected_arm})."
    return 0
  fi

  # No dedicated file. A non-factory selection in options is safe to import.
  # A Factory default is only recorded as non-explicit and cannot remove anything.
  cpu_profile_state_write "$enabled" "$option_profile" "options-bootstrap" false "$option_cfg" || true
  log "CPU Profile Manager: utworzono trwały stan profilu z konfiguracji (profil=${option_profile}, enabled=${enabled}, explicit=false)."
}

cpu_profile_requested_profile() {
  cpu_profile_state_bootstrap || true
  jq -r '.requested_profile // "factory"' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo factory
}

cpu_profile_requested_enabled() {
  cpu_profile_state_bootstrap || true
  jq -r '.enabled // false' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo false
}

cpu_profile_entries() {
  local profile="$1" arm cfg
  case "$profile" in
    factory) return 0 ;;
    mild|balanced|performance|experimental)
      arm="$(cpu_profile_preset_arm_freq "$profile")"
      [ -n "$arm" ] && printf 'arm_freq\t%s\n' "$arm"
      return 0
      ;;
    advanced)
      cfg="$(jq -c '.requested_config // {}' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo '{}')"
      jq -r '
        . | to_entries[]?
        | select(.key|IN("arm_freq","arm_freq_min","over_voltage","over_voltage_min","over_voltage_delta","force_turbo","initial_turbo","temp_limit"))
        | select(.value != null)
        | (.value|tostring) as $v
        | select($v != "" and $v != "auto")
        | [.key,$v] | @tsv
      ' <<<"$cfg" 2>/dev/null || true
      ;;
  esac
}

cpu_profile_expected_arm_freq() {
  local profile="$1" v
  case "$profile" in
    mild|balanced|performance|experimental) cpu_profile_preset_arm_freq "$profile" ;;
    advanced)
      v="$(jq -r '.requested_config.arm_freq // "auto"' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo auto)"
      [ "$v" != "auto" ] && printf '%s\n' "$v" || true
      ;;
    *) true ;;
  esac
}

cpu_profile_import_startup_options_if_safe() {
  # Native Configuration can save a new preset and restart the App before the live
  # reconciler gets a cycle. Import non-Factory changes here. A Factory rollback
  # against an existing non-Factory persistent request remains protected because it
  # is indistinguishable from the transient Supervisor default seen on host reboot;
  # an explicit Factory change is captured immediately by the live reconciler while
  # the App is running.
  [ -r "$OPTIONS_FILE" ] && [ -r "$CPU_PROFILE_STATE_FILE" ] || return 0
  local opt state
  opt="$(jq -r '.config_cpu_profile // "factory"' "$OPTIONS_FILE" 2>/dev/null || echo factory)"
  state="$(jq -r '.requested_profile // "factory"' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo factory)"
  case "$opt" in factory|mild|balanced|performance|experimental|advanced) ;; *) return 0 ;; esac
  if [ "$opt" != "factory" ] || [ "$state" = "factory" ]; then
    cpu_profile_sync_state_from_options_if_changed || true
  fi
}

cpu_profile_restore_options_from_state() {
  cpu_profile_state_bootstrap || return 1
  [ -r "$OPTIONS_FILE" ] || return 0
  local enabled profile cfg explicit tmp current_profile current_enabled current_cfg desired_cfg
  enabled="$(jq -r '.enabled // false' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo false)"
  profile="$(jq -r '.requested_profile // "factory"' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo factory)"
  cfg="$(jq -c '.requested_config // {}' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo '{}')"
  explicit="$(jq -r '.explicit // false' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo false)"
  current_profile="$(jq -r '.config_cpu_profile // "factory"' "$OPTIONS_FILE" 2>/dev/null || echo factory)"
  current_enabled="$(jq -r '.section_cpu_enabled // false' "$OPTIONS_FILE" 2>/dev/null || echo false)"
  current_cfg="$(jq -cS '.config_cpu // {}' "$OPTIONS_FILE" 2>/dev/null || echo '{}')"

  # A non-explicit bootstrap Factory must never erase an existing manual/boot config.
  if [ "$profile" = "factory" ] && [ "$explicit" != "true" ] && [ "$enabled" != "true" ]; then
    return 0
  fi
  case "$profile" in
    factory|mild|balanced|performance|experimental) desired_cfg="$(cpu_profile_preset_config_json "$profile")" ;;
    advanced) desired_cfg="$cfg" ;;
    *) return 1 ;;
  esac
  if [ "$profile" = "$current_profile" ] && [ "$enabled" = "$current_enabled" ] && [ "$current_cfg" = "$(jq -cS . <<<"$desired_cfg" 2>/dev/null || echo '{}')" ]; then
    return 0
  fi
  tmp="${OPTIONS_FILE}.cpu_restore.$$"
  jq --arg p "$profile" --argjson en "$enabled" --argjson cfg "$desired_cfg" '
      .section_cpu_enabled=$en | .config_cpu_profile=$p | .config_cpu=$cfg
    ' "$OPTIONS_FILE" > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$OPTIONS_FILE"
  log "CPU Profile Manager: odtworzono profil=${profile} z trwałego stanu do options.json (enabled=${enabled})."
}

cpu_profile_sync_state_from_options_if_changed() {
  # v2.8.18: startup first restores the persistent state into options.json.
  # Therefore any later difference is a real user/runtime edit and Factory can be
  # imported safely instead of being ignored forever.
  [ -r "$OPTIONS_FILE" ] || return 0
  [ -r "$CPU_PROFILE_STATE_FILE" ] || { cpu_profile_state_bootstrap; return 0; }
  local opt_profile state_profile opt_enabled opt_cfg old_enabled old_cfg canonical_cfg
  opt_profile="$(jq -r '.config_cpu_profile // "factory"' "$OPTIONS_FILE" 2>/dev/null || echo factory)"
  state_profile="$(jq -r '.requested_profile // "factory"' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo factory)"
  opt_enabled="$(jq -r '.section_cpu_enabled // false' "$OPTIONS_FILE" 2>/dev/null || echo false)"
  opt_cfg="$(jq -c '.config_cpu // {}' "$OPTIONS_FILE" 2>/dev/null || echo '{}')"
  old_enabled="$(jq -r '.enabled // false' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo false)"
  old_cfg="$(jq -cS '.requested_config // {}' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo '{}')"
  case "$opt_profile" in factory|mild|balanced|performance|experimental|advanced) ;; *) return 0 ;; esac
  if [ "$opt_profile" != "advanced" ]; then
    canonical_cfg="$(cpu_profile_preset_config_json "$opt_profile")" || return 1
  else
    canonical_cfg="$opt_cfg"
  fi
  if [ "$opt_profile" != "$state_profile" ] || [ "$opt_enabled" != "$old_enabled" ] || [ "$(jq -cS . <<<"$canonical_cfg" 2>/dev/null || echo '{}')" != "$old_cfg" ]; then
    cpu_profile_state_write "$opt_enabled" "$opt_profile" "native-options" true "$canonical_cfg" || return 1
    log "CPU Profile Manager: zsynchronizowano zmianę z natywnej Konfiguracji (profil=${opt_profile}, enabled=${opt_enabled})."
  fi
}

sync_cpu_profile_from_options() {
  local force="${1:-false}" profile section_enabled explicit desired base_tmp main_tmp cpu_file cpu_tmp managed key value line entries=0 changed=false manager_changed=false stamp expected_arm
  cpu_profile_state_bootstrap || return 1
  cpu_profile_sync_state_from_options_if_changed || true
  cpu_profile_restore_options_from_state || return 1
  section_enabled="$(cpu_profile_requested_enabled)"
  [ "$section_enabled" = "true" ] || return 0
  profile="$(cpu_profile_requested_profile)"
  explicit="$(jq -r '.explicit // false' "$CPU_PROFILE_STATE_FILE" 2>/dev/null || echo false)"
  case "$profile" in factory|mild|balanced|performance|experimental|advanced) ;; *) log "CPU Profile Manager: nieznany profil '$profile'."; return 1 ;; esac

  find_boot_config || { boot_access_warn_throttled "Host Boot Access: config.txt niedostępny — wstrzymuję zapis profilu CPU i ustawień boot do czasu odzyskania Host PID/boot access."; return 1; }
  [ -w "$BOOT_CFG" ] || { log "CPU Profile Manager: config.txt nie jest zapisywalny: $BOOT_CFG"; cleanup_mount; return 1; }
  cpu_file="$(dirname "$BOOT_CFG")/$CPU_PROFILE_FILENAME"
  managed="$(dirname "$BOOT_CFG")/$CONFIG_MANAGER_FILENAME"
  desired="/tmp/sbc5cc-cpu-profile-$$.txt"
  cat > "$desired" <<EOF
# SBC5 Control Center — dedykowany profil CPU/OC
# Źródło prawdy: $CPU_PROFILE_STATE_FILE
# Auto = brak wpisu. Zmiany obowiązują po pełnym restarcie hosta.
[pi5]
EOF
  while IFS=$'\t' read -r key value; do
    [ -n "$key" ] || continue
    case "$key" in arm_freq|arm_freq_min|over_voltage|over_voltage_min|over_voltage_delta|force_turbo|initial_turbo|temp_limit) ;; *) continue ;; esac
    config_manager_validate_value "$key" "$value" false || { rm -f "$desired"; cleanup_mount; return 1; }
    line="$(config_manager_line_for "$key" "$value")"
    printf '%s\n' "$line" >> "$desired"
    entries=$((entries + 1))
  done < <(cpu_profile_entries "$profile")

  expected_arm="$(cpu_profile_expected_arm_freq "$profile")"
  if [ "$profile" = "factory" ]; then
    entries=0
    # Factory may delete SBC5 CPU settings only when it came from an explicit
    # persisted state. A bootstrap/default Factory never performs destructive work.
    if [ "$explicit" != "true" ]; then
      rm -f "$desired"; cleanup_mount
      [ "$force" = "true" ] && log "CPU Profile Manager: profil=factory jest tylko wartością startową (explicit=false) — nie usuwam ustawień CPU podczas startupu."
      return 0
    fi
  fi

  base_tmp="${BOOT_CFG}.sbc5cpu-check.$$"
  strip_cpu_profile_include_block "$BOOT_CFG" "$base_tmp" || { rm -f "$desired" "$base_tmp"; cleanup_mount; return 1; }
  if [ "$entries" -gt 0 ]; then
    for key in arm_freq arm_freq_min over_voltage over_voltage_min over_voltage_delta force_turbo initial_turbo temp_limit; do
      if unmanaged_config_key_exists "$base_tmp" "$key"; then
        log "CPU Profile Manager: ODRZUCONO profil ${profile} — $key istnieje bezpośrednio poza blokiem SBC5 CPU. Usuń konflikt ręcznie albo wybierz Fabryczny."
        rm -f "$desired" "$base_tmp"; cleanup_mount; return 1
      fi
    done
  fi
  rm -f "$base_tmp"

  if [ "$entries" -gt 0 ]; then
    if [ ! -f "$cpu_file" ] || ! cpu_profile_semantically_equal "$desired" "$cpu_file" || ! grep -Eq '^[[:space:]]*include[[:space:]]+sbc5cc-cpu-profile\.txt[[:space:]]*$' "$BOOT_CFG" 2>/dev/null; then
      changed=true
    fi
  else
    if [ -f "$cpu_file" ] || grep -Eq '^[[:space:]]*include[[:space:]]+sbc5cc-cpu-profile\.txt[[:space:]]*$' "$BOOT_CFG" 2>/dev/null || grep -Fq "$CPU_PROFILE_MARK_BEGIN" "$BOOT_CFG" 2>/dev/null; then
      changed=true
    fi
  fi
  if [ -f "$managed" ] && grep -Eq '^[[:space:]]*(arm_freq|arm_freq_min|over_voltage|over_voltage_min|over_voltage_delta|force_turbo|initial_turbo|temp_limit)[[:space:]]*=' "$managed" 2>/dev/null; then
    manager_changed=true; changed=true
  fi

  if [ "$changed" != "true" ]; then
    rm -f "$desired"; cleanup_mount
    [ "$force" = "true" ] && log "CPU Profile Manager: profil=${profile} jest spójny z config.txt (expected_arm_freq=${expected_arm:-factory}) — bez zmian i bez nowego restartu."
    return 0
  fi

  system_config_backup || { log "CPU Profile Manager: nie udało się wykonać backupu config.txt."; rm -f "$desired"; cleanup_mount; return 1; }
  if [ -f "$cpu_file" ]; then
    mkdir -p "$SYSTEM_BACKUP_DIR"
    stamp="$(date '+%Y%m%d_%H%M%S')"
    cp "$cpu_file" "$SYSTEM_BACKUP_DIR/sbc5cc-cpu-profile.before_${stamp}_$$.bak" || { log "CPU Profile Manager: nie udało się zabezpieczyć poprzedniego profilu CPU."; rm -f "$desired"; cleanup_mount; return 1; }
    cp "$cpu_file" "${cpu_file}.rpi5cc-cpu.bak" 2>/dev/null || true
    ls -1t "$SYSTEM_BACKUP_DIR"/sbc5cc-cpu-profile.before_*.bak 2>/dev/null | tail -n +11 | xargs -r rm -f --
  fi
  if [ "$manager_changed" = "true" ]; then
    config_manager_backup_managed "$managed" || { log "CPU Profile Manager: nie udało się wykonać backupu $CONFIG_MANAGER_FILENAME."; rm -f "$desired"; cleanup_mount; return 1; }
    cpu_profile_strip_owned_manager_keys "$managed" || true
  fi

  if [ "$entries" -gt 0 ]; then
    cpu_tmp="${cpu_file}.new.$$"
    cp "$desired" "$cpu_tmp" || { log "CPU Profile Manager: nie udało się przygotować $CPU_PROFILE_FILENAME."; rm -f "$desired" "$cpu_tmp"; cleanup_mount; return 1; }
    mv -f "$cpu_tmp" "$cpu_file" || { log "CPU Profile Manager: nie udało się zatwierdzić $CPU_PROFILE_FILENAME."; rm -f "$desired" "$cpu_tmp"; cleanup_mount; return 1; }
    cpu_profile_ensure_include "$BOOT_CFG" || { log "CPU Profile Manager: nie udało się dodać include $CPU_PROFILE_FILENAME."; rm -f "$desired"; cleanup_mount; return 1; }
    if ! cmp -s "$desired" "$cpu_file" || ! grep -Eq '^[[:space:]]*include[[:space:]]+sbc5cc-cpu-profile\.txt[[:space:]]*$' "$BOOT_CFG" 2>/dev/null; then
      log "CPU Profile Manager: BŁĄD weryfikacji po zapisie — profil nie został potwierdzony."
      rm -f "$desired"; cleanup_mount; return 1
    fi
  else
    main_tmp="${BOOT_CFG}.sbc5cpu-factory.$$"
    strip_cpu_profile_include_block "$BOOT_CFG" "$main_tmp" || { rm -f "$desired" "$main_tmp"; cleanup_mount; return 1; }
    [ -s "$main_tmp" ] || { log "CPU Profile Manager: walidacja Factory dała pusty config.txt — anulowano."; rm -f "$desired" "$main_tmp"; cleanup_mount; return 1; }
    cp "$main_tmp" "$BOOT_CFG" || { rm -f "$desired" "$main_tmp"; cleanup_mount; return 1; }
    rm -f "$main_tmp" "$cpu_file"
    if [ -f "$cpu_file" ] || grep -Eq '^[[:space:]]*include[[:space:]]+sbc5cc-cpu-profile\.txt[[:space:]]*$' "$BOOT_CFG" 2>/dev/null || grep -Fq "$CPU_PROFILE_MARK_BEGIN" "$BOOT_CFG" 2>/dev/null; then
      log "CPU Profile Manager: BŁĄD weryfikacji Factory — wpisy SBC5 CPU nadal istnieją."
      rm -f "$desired"; cleanup_mount; return 1
    fi
  fi
  rm -f "$desired" "$BOOT_CONFIG_CACHE_FILE"
  sync
  rm -f "$SYSTEM_DEFAULTS_LOCK_FILE" 2>/dev/null || true

  if [ "$entries" -gt 0 ]; then
    log "CPU Profile Manager: zapisano profil=${profile}; expected_arm_freq=${expected_arm:-manual}; wpisów=${entries}; plik=$CPU_PROFILE_FILENAME. Wymagany pełny restart hosta."
    mark_cpu_host_restart_required "$profile" "$expected_arm" "Zapisano profil CPU/OC ${profile}. Firmware zastosuje nowe taktowanie i parametry CPU dopiero po pełnym restarcie Raspberry Pi 5."
  else
    log "CPU Profile Manager: profil=factory — usunięto wyłącznie SBC5-owned CPU/OC. Wymagany pełny restart hosta."
    mark_cpu_host_restart_required "factory" "" "Przywrócono fabryczny profil CPU/OC. Firmware wróci do domyślnych parametrów po pełnym restarcie Raspberry Pi 5."
  fi
  cleanup_mount
  collect_system_power_info || true
  publish_telemetry_snapshot || true
  return 0
}

gpu_profile_preset_config_json() {
  case "$1" in
    factory) jq -cn '{core_freq:"auto",core_freq_min:"auto",isp_freq:"auto",isp_freq_min:"auto",v3d_freq:"auto",v3d_freq_min:"auto",gpu_freq_min:"auto"}' ;;
    eco) jq -cn '{core_freq:"850",core_freq_min:"500",isp_freq:"850",isp_freq_min:"500",v3d_freq:"900",v3d_freq_min:"500",gpu_freq_min:"auto"}' ;;
    balanced) jq -cn '{core_freq:"950",core_freq_min:"500",isp_freq:"950",isp_freq_min:"500",v3d_freq:"1000",v3d_freq_min:"500",gpu_freq_min:"auto"}' ;;
    performance) jq -cn '{core_freq:"1000",core_freq_min:"500",isp_freq:"1000",isp_freq_min:"500",v3d_freq:"1100",v3d_freq_min:"500",gpu_freq_min:"auto"}' ;;
    experimental) jq -cn '{core_freq:"1100",core_freq_min:"500",isp_freq:"1100",isp_freq_min:"500",v3d_freq:"1200",v3d_freq_min:"500",gpu_freq_min:"auto"}' ;;
    advanced)
      if [ -r "$GPU_PROFILE_STATE_FILE" ]; then
        jq -c '.requested_config // {}' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo '{}'
      elif [ -r "$OPTIONS_FILE" ]; then
        jq -c '.config_gpu // {}' "$OPTIONS_FILE" 2>/dev/null || echo '{}'
      else
        echo '{}'
      fi ;;
    *) echo '{}' ;;
  esac
}

gpu_profile_state_write() {
  local enabled="$1" profile="$2" source="$3" explicit="$4" cfg_json="$5" tmp
  case "$profile" in factory|eco|balanced|performance|experimental|advanced) ;; *) return 1 ;; esac
  case "$enabled" in true|false) ;; *) enabled=false ;; esac
  case "$explicit" in true|false) ;; *) explicit=false ;; esac
  jq -e 'type=="object"' <<<"$cfg_json" >/dev/null 2>&1 || cfg_json='{}'
  tmp="${GPU_PROFILE_STATE_FILE}.tmp.$$"
  jq -n \
    --argjson schema "$GPU_PROFILE_STATE_SCHEMA" \
    --argjson enabled "$enabled" \
    --arg profile "$profile" \
    --arg source "$source" \
    --argjson explicit "$explicit" \
    --argjson config "$cfg_json" \
    --arg updated "$(date '+%Y-%m-%d %H:%M:%S')" \
    '{schema:$schema,enabled:$enabled,requested_profile:$profile,requested_config:$config,source:$source,explicit:$explicit,updated:$updated}' \
    > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$GPU_PROFILE_STATE_FILE"
}

gpu_profile_from_triplet() {
  local core="$1" isp="$2" v3d="$3"
  case "${core}:${isp}:${v3d}" in
    850:850:900) printf 'eco\n' ;;
    950:950:1000) printf 'balanced\n' ;;
    1000:1000:1100) printf 'performance\n' ;;
    1100:1100:1200) printf 'experimental\n' ;;
    ::) printf 'factory\n' ;;
    *) printf 'advanced\n' ;;
  esac
}

gpu_profile_read_managed_triplet() {
  local managed="$1" key val core='' isp='' v3d=''
  [ -r "$managed" ] || { printf '||\n'; return 0; }
  while IFS='=' read -r key val; do
    key="$(printf '%s' "$key" | tr -d '[:space:]')"
    val="$(printf '%s' "$val" | sed 's/[[:space:]]*#.*$//' | tr -d '[:space:]')"
    case "$key" in
      core_freq) core="$val" ;;
      isp_freq) isp="$val" ;;
      v3d_freq) v3d="$val" ;;
    esac
  done < <(grep -E '^[[:space:]]*(core_freq|isp_freq|v3d_freq)[[:space:]]*=' "$managed" 2>/dev/null || true)
  printf '%s|%s|%s\n' "$core" "$isp" "$v3d"
}

gpu_profile_state_bootstrap() {
  # Once valid, the persistent state is authoritative. This mirrors CPU Profile Manager.
  if [ -r "$GPU_PROFILE_STATE_FILE" ] && jq -e \
      --argjson schema "$GPU_PROFILE_STATE_SCHEMA" \
      '(.schema == $schema) and (.requested_profile|IN("factory","eco","balanced","performance","experimental","advanced")) and ((.requested_config // {})|type=="object")' \
      "$GPU_PROFILE_STATE_FILE" >/dev/null 2>&1; then
    return 0
  fi

  local enabled=false option_profile=factory option_cfg='{}' managed='' triplet='||' core='' isp='' v3d='' detected_profile=''
  if [ -r "$OPTIONS_FILE" ]; then
    enabled="$(jq -r '.section_gpu_enabled // false' "$OPTIONS_FILE" 2>/dev/null || echo false)"
    case "$enabled" in true|false) ;; *) enabled=false ;; esac
    option_profile="$(jq -r '.config_gpu_profile // "factory"' "$OPTIONS_FILE" 2>/dev/null || echo factory)"
    option_cfg="$(jq -c '.config_gpu // {}' "$OPTIONS_FILE" 2>/dev/null || echo '{}')"
  fi
  case "$option_profile" in factory|eco|balanced|performance|experimental|advanced) ;; *) option_profile=factory ;; esac

  # Upgrade path from 2.8.12-2.8.15: if options reverted to Factory, recover the
  # profile that is already written in SBC5-owned sbc5cc-managed.txt.
  if find_boot_config >/dev/null 2>&1; then
    managed="$(dirname "$BOOT_CFG")/$CONFIG_MANAGER_FILENAME"
    triplet="$(gpu_profile_read_managed_triplet "$managed")"
    IFS='|' read -r core isp v3d <<<"$triplet"
    if [ -n "$core" ] || [ -n "$isp" ] || [ -n "$v3d" ]; then
      detected_profile="$(gpu_profile_from_triplet "$core" "$isp" "$v3d")"
    fi
    cleanup_mount
  fi

  if [ -n "$detected_profile" ] && [ "$detected_profile" != "factory" ]; then
    option_profile="$detected_profile"
    enabled=true
    if [ "$detected_profile" = "advanced" ]; then
      option_cfg="$(jq -cn --arg core "${core:-auto}" --arg isp "${isp:-auto}" --arg v3d "${v3d:-auto}" '{core_freq:$core,core_freq_min:"auto",isp_freq:$isp,isp_freq_min:"auto",v3d_freq:$v3d,v3d_freq_min:"auto",gpu_freq_min:"auto"}')"
    else
      option_cfg="$(gpu_profile_preset_config_json "$detected_profile")"
    fi
    gpu_profile_state_write true "$option_profile" "boot-managed-import" false "$option_cfg" || true
    log "GPU Profile Manager: zaimportowano trwały stan z $CONFIG_MANAGER_FILENAME (profil=${option_profile}, core=${core:-auto}, isp=${isp:-auto}, v3d=${v3d:-auto})."
    return 0
  fi

  if [ "$option_profile" != "advanced" ]; then
    option_cfg="$(gpu_profile_preset_config_json "$option_profile")"
  fi
  gpu_profile_state_write "$enabled" "$option_profile" "options-bootstrap" false "$option_cfg" || true
  log "GPU Profile Manager: utworzono trwały stan profilu z konfiguracji (profil=${option_profile}, enabled=${enabled}, explicit=false)."
}

gpu_profile_requested_profile() {
  gpu_profile_state_bootstrap || true
  jq -r '.requested_profile // "factory"' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo factory
}

gpu_profile_requested_enabled() {
  gpu_profile_state_bootstrap || true
  jq -r '.enabled // false' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo false
}

gpu_profile_import_startup_options_if_safe() {
  # Same startup rule as CPU: a new non-Factory native preset is trusted even if
  # Supervisor restarted the App immediately; suspicious Factory/default rollback
  # is left to the persistent-state recovery path.
  [ -r "$OPTIONS_FILE" ] && [ -r "$GPU_PROFILE_STATE_FILE" ] || return 0
  local opt state
  opt="$(jq -r '.config_gpu_profile // "factory"' "$OPTIONS_FILE" 2>/dev/null || echo factory)"
  state="$(jq -r '.requested_profile // "factory"' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo factory)"
  case "$opt" in factory|eco|balanced|performance|experimental|advanced) ;; *) return 0 ;; esac
  if [ "$opt" != "factory" ] || [ "$state" = "factory" ]; then
    gpu_profile_sync_state_from_options_if_changed || true
  fi
}

gpu_profile_restore_options_from_state() {
  gpu_profile_state_bootstrap || return 1
  [ -r "$OPTIONS_FILE" ] || return 0
  local enabled profile cfg explicit tmp current_profile current_enabled current_cfg desired_cfg manager_enabled
  enabled="$(jq -r '.enabled // false' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo false)"
  profile="$(jq -r '.requested_profile // "factory"' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo factory)"
  cfg="$(jq -c '.requested_config // {}' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo '{}')"
  explicit="$(jq -r '.explicit // false' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo false)"
  current_profile="$(jq -r '.config_gpu_profile // "factory"' "$OPTIONS_FILE" 2>/dev/null || echo factory)"
  current_enabled="$(jq -r '.section_gpu_enabled // false' "$OPTIONS_FILE" 2>/dev/null || echo false)"
  current_cfg="$(jq -cS '.config_gpu // {}' "$OPTIONS_FILE" 2>/dev/null || echo '{}')"
  manager_enabled="$(jq -r '.config_txt_manager.enabled // false' "$OPTIONS_FILE" 2>/dev/null || echo false)"
  if [ "$profile" = "advanced" ]; then desired_cfg="$cfg"; else desired_cfg="$(gpu_profile_preset_config_json "$profile")"; fi

  # A bootstrap/default Factory is non-destructive. Any persisted non-factory or
  # explicit request wins over transient Supervisor defaults after host reboot.
  if [ "$profile" = "factory" ] && [ "$explicit" != "true" ] && [ "$enabled" != "true" ]; then
    return 0
  fi
  if [ "$profile" = "$current_profile" ] && [ "$enabled" = "$current_enabled" ]      && [ "$current_cfg" = "$(jq -cS . <<<"$desired_cfg" 2>/dev/null || echo '{}')" ]; then
    # Still make sure a managed GPU request keeps Config Manager enabled.
    if [ "$enabled" != "true" ] || [ "$manager_enabled" = "true" ]; then
      return 0
    fi
  fi
  tmp="${OPTIONS_FILE}.gpu_restore.$$"
  jq --arg p "$profile" --argjson en "$enabled" --argjson cfg "$desired_cfg" '
      .section_gpu_enabled=$en |
      .config_gpu_profile=$p |
      .config_gpu=$cfg |
      if $en then .config_txt_manager.enabled=true else . end
    ' "$OPTIONS_FILE" > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$OPTIONS_FILE"
  log "GPU Profile Manager: odtworzono profil=${profile} i wartości profilu z trwałego stanu do options.json (enabled=${enabled})."
}

gpu_profile_sync_state_from_options_if_changed() {
  [ -r "$OPTIONS_FILE" ] || return 0
  gpu_profile_state_bootstrap || return 1
  local opt_profile state_profile opt_enabled opt_cfg old_enabled old_cfg canonical_cfg
  opt_profile="$(jq -r '.config_gpu_profile // "factory"' "$OPTIONS_FILE" 2>/dev/null || echo factory)"
  state_profile="$(jq -r '.requested_profile // "factory"' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo factory)"
  opt_enabled="$(jq -r '.section_gpu_enabled // false' "$OPTIONS_FILE" 2>/dev/null || echo false)"
  opt_cfg="$(jq -c '.config_gpu // {}' "$OPTIONS_FILE" 2>/dev/null || echo '{}')"
  old_enabled="$(jq -r '.enabled // false' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo false)"
  old_cfg="$(jq -cS '.requested_config // {}' "$GPU_PROFILE_STATE_FILE" 2>/dev/null || echo '{}')"
  case "$opt_profile" in factory|eco|balanced|performance|experimental|advanced) ;; *) return 0 ;; esac
  if [ "$opt_profile" = "advanced" ]; then canonical_cfg="$opt_cfg"; else canonical_cfg="$(gpu_profile_preset_config_json "$opt_profile")" || return 1; fi
  if [ "$opt_profile" != "$state_profile" ] || [ "$opt_enabled" != "$old_enabled" ] || [ "$(jq -cS . <<<"$canonical_cfg" 2>/dev/null || echo '{}')" != "$old_cfg" ]; then
    gpu_profile_state_write "$opt_enabled" "$opt_profile" "native-options" true "$canonical_cfg" || return 1
    log "GPU Profile Manager: zsynchronizowano zmianę z natywnej Konfiguracji (profil=${opt_profile}, enabled=${opt_enabled})."
  fi
}

sync_gpu_profile_from_options() {
  local force="${1:-false}" profile enabled
  gpu_profile_state_bootstrap || return 1
  gpu_profile_sync_state_from_options_if_changed || true
  gpu_profile_restore_options_from_state || return 1
  load_options
  profile="$(gpu_profile_requested_profile)"
  enabled="$(gpu_profile_requested_enabled)"
  [ "$force" = "true" ] && log "GPU Profile Manager: source_of_truth=${GPU_PROFILE_STATE_FILE}; profile=${profile}; enabled=${enabled}."
  return 0
}

config_manager_safe_token() {
  local value="$1"
  [ ${#value} -le 90 ] || return 1
  [[ "$value" != *$'\n'* && "$value" != *$'\r'* ]] || return 1
  [[ "$value" != *"#"* ]] || return 1
  return 0
}

config_manager_validate_section() {
  local section="$1"
  [ -n "$section" ] || section="pi5"
  [ ${#section} -le 80 ] || return 1
  [[ "$section" =~ ^[A-Za-z0-9_.:+/=,-]+$ ]]
}

config_manager_validate_value() {
  local key="$1" value="$2" advanced="$3" type known min="" max="" n
  [[ "$key" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || { log "Config Manager: nieprawidłowa nazwa parametru: $key"; return 1; }
  config_manager_safe_token "$value" || { log "Config Manager: wartość jest za długa albo zawiera niedozwolony znak nowej linii/#."; return 1; }

  known="$(jq -r --arg k "$key" 'if .parameters[$k] then "yes" else "no" end' "$CONFIG_CATALOG_FILE" 2>/dev/null || echo no)"
  if [ "$known" != "yes" ]; then
    [ "$advanced" = "true" ] || {
      log "Config Manager: parametr '$key' nie występuje w katalogu. Włącz Tryb zaawansowany, aby zapisać parametr spoza katalogu."
      return 1
    }
    [ ${#key} -le 64 ] && [ $((${#key}+1+${#value})) -le 98 ] || {
      log "Config Manager: wpis przekracza limit 98 znaków config.txt."; return 1;
    }
    return 0
  fi

  type="$(jq -r --arg k "$key" '.parameters[$k].type // "string"' "$CONFIG_CATALOG_FILE" 2>/dev/null || echo string)"
  case "$type" in
    bool)
      case "$value" in 0|1) ;; *) log "Config Manager: $key przyjmuje 0 albo 1."; return 1 ;; esac ;;
    uint32)
      [[ "$value" =~ ^[0-9]+$ ]] || { log "Config Manager: $key wymaga liczby całkowitej 0..4294967295."; return 1; }
      [ "$value" -le 4294967295 ] || { log "Config Manager: $key przekracza 4294967295."; return 1; } ;;
    int)
      [[ "$value" =~ ^-?[0-9]+$ ]] || { log "Config Manager: $key wymaga liczby całkowitej."; return 1; }
      if [ "$advanced" != "true" ]; then
        case "$key" in
          arm_freq) min=600; max=3000 ;;
          arm_freq_min) min=600; max=2400 ;;
          core_freq|isp_freq|v3d_freq) min=500; max=1200 ;;
          core_freq_min|gpu_freq_min|isp_freq_min|v3d_freq_min) min=200; max=960 ;;
          over_voltage|over_voltage_min) min=-16; max=8 ;;
          over_voltage_delta) min=0; max=50000 ;;
          force_turbo) min=0; max=1 ;;
          initial_turbo) min=0; max=60 ;;
          temp_limit) min=0; max=85 ;;
          max_framebuffers) min=0; max=2 ;;
        esac
        if [ -n "$min" ]; then
          n=$((value))
          [ "$n" -ge "$min" ] && [ "$n" -le "$max" ] || {
            log "Config Manager: $key=$value poza zakresem ochronnym aplikacji $min..$max. Tryb zaawansowany może ominąć wyłącznie ten zakres, nie walidację typu."
            return 1
          }
        fi
      fi ;;
    string|directive) : ;;
    *) [ "$advanced" = "true" ] || { log "Config Manager: nieznany typ katalogu dla $key."; return 1; } ;;
  esac

  # Firmware ignoruje znaki po 98. kolumnie — nigdy nie zapisujemy obciętego wpisu.
  if [ "$key" = "include" ]; then
    [ $((8+${#value})) -le 98 ] || { log "Config Manager: include przekracza limit 98 znaków."; return 1; }
  else
    [ $((${#key}+1+${#value})) -le 98 ] || { log "Config Manager: wpis przekracza limit 98 znaków config.txt."; return 1; }
  fi
  return 0
}

config_manager_line_for() {
  local key="$1" value="$2"
  if [ "$key" = "include" ]; then printf 'include %s' "$value"; else printf '%s=%s' "$key" "$value"; fi
}

config_manager_is_repeatable() {
  local key="$1"
  case "$key" in dtparam|dtoverlay|include) return 0 ;; *) return 1 ;; esac
}

config_manager_normalized_copy() {
  local src="$1" dst="$2"
  [ -r "$src" ] || return 1
  # Wersja aplikacji w komentarzu nagłówka nie zmienia semantyki config.txt.
  # Aktualizacja SBC5 nie może przez samą zmianę tego komentarza wymuszać rebootu hosta.
  sed -E 's/^# SBC5 Control Center [0-9]+\.[0-9]+\.[0-9]+([^ ]*) — zarządzany plik config\.txt$/# SBC5 Control Center <version> — zarządzany plik config.txt/' "$src" > "$dst"
}

config_manager_semantically_equal() {
  local a="$1" b="$2" na nb rc=1
  [ -r "$a" ] && [ -r "$b" ] || return 1
  na="/tmp/sbc5cc-semantic-a-$$-$RANDOM"
  nb="/tmp/sbc5cc-semantic-b-$$-$RANDOM"
  if config_manager_normalized_copy "$a" "$na" && config_manager_normalized_copy "$b" "$nb" && cmp -s "$na" "$nb"; then
    rc=0
  fi
  rm -f "$na" "$nb"
  return "$rc"
}

config_manager_backup_managed() {
  local managed="$1" stamp latest
  mkdir -p "$SYSTEM_BACKUP_DIR"
  stamp="$(date '+%Y%m%d_%H%M%S')"
  latest="${managed}.rpi5cc-manager.bak"
  rm -f "$CONFIG_MANAGER_ABSENT_FILE"
  if [ -f "$managed" ]; then
    cp "$managed" "$SYSTEM_BACKUP_DIR/sbc5cc-managed.before_${stamp}_$$.bak" || return 1
    cp "$managed" "$latest" || return 1
  else
    rm -f "$latest"
    : > "$CONFIG_MANAGER_ABSENT_FILE"
  fi
  ls -1t "$SYSTEM_BACKUP_DIR"/sbc5cc-managed.before_*.bak 2>/dev/null | tail -n +11 | xargs -r rm -f --
}

config_manager_ensure_include() {
  local cfg="$1" managed="$2" base tmp
  grep -Eq '^[[:space:]]*include[[:space:]]+sbc5cc-managed\.txt[[:space:]]*$' "$cfg" 2>/dev/null && return 0
  base="${cfg}.rpi5cc-manager-base.$$"
  tmp="${cfg}.rpi5cc-manager-new.$$"
  awk -v begin="$CONFIG_MANAGER_MARK_BEGIN" -v end="$CONFIG_MANAGER_MARK_END" '
    $0 == begin {skip=1; next}
    $0 == end {skip=0; next}
    skip {next}
    {print}
  ' "$cfg" > "$base" || return 1
  cp "$base" "$tmp" || { rm -f "$base"; return 1; }
  cat >> "$tmp" <<EOF

$CONFIG_MANAGER_MARK_BEGIN
# Plik zarządzany: $CONFIG_MANAGER_FILENAME. Nie edytuj tej linii ręcznie, jeśli chcesz używać GUI Control Center.
[all]
include $CONFIG_MANAGER_FILENAME
$CONFIG_MANAGER_MARK_END
EOF
  [ -s "$tmp" ] || { rm -f "$base" "$tmp"; return 1; }
  cp "$tmp" "$cfg" || { rm -f "$base" "$tmp"; return 1; }
  rm -f "$base" "$tmp"
  return 0
}

config_manager_set_in_file() {
  local file="$1" section="$2" key="$3" value="$4" repeat="false" line tmp
  line="$(config_manager_line_for "$key" "$value")"
  config_manager_is_repeatable "$key" && repeat="true"
  tmp="${file}.tmp.$$"
  [ -f "$file" ] || {
    cat > "$file" <<EOF
# SBC5 Control Center $APP_VERSION — zarządzany plik config.txt
# Każda zmiana jest poprzedzona backupem. Wymagany pełny restart hosta.
EOF
  }
  awk -v target="$section" -v key="$key" -v newline="$line" -v repeat="$repeat" '
    function header_name(s, t) { t=s; sub(/^\[/,"",t); sub(/\]$/,"",t); return t }
    function lhs_name(s, a) { a=s; sub(/=.*/,"",a); gsub(/^[ \t]+|[ \t]+$/,"",a); return a }
    BEGIN {cur=""; seen=0; done=0; exact=0}
    /^\[[^]]+\][ \t]*$/ {
      if (cur==target && !done) {
        if (repeat=="true") { if (!exact) print newline }
        else print newline
        done=1
      }
      cur=header_name($0)
      if (cur==target) seen=1
      print; next
    }
    {
      if (cur==target) {
        if (repeat=="true") {
          if ($0==newline) exact=1
        } else if (index($0,"=")>0 && lhs_name($0)==key) {
          if (!done) { print newline; done=1 }
          next
        }
      }
      print
    }
    END {
      if (!seen) {
        print ""
        print "[" target "]"
        print newline
      } else if (!done) {
        if (repeat=="true") { if (!exact) print newline }
        else print newline
      }
    }
  ' "$file" > "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$file"
}

config_manager_remove_from_file() {
  local file="$1" section="$2" key="$3" value="$4" repeat="false" line tmp
  [ -f "$file" ] || return 0
  line="$(config_manager_line_for "$key" "$value")"
  config_manager_is_repeatable "$key" && repeat="true"
  tmp="${file}.tmp.$$"
  awk -v target="$section" -v key="$key" -v oldline="$line" -v repeat="$repeat" '
    function header_name(s, t) { t=s; sub(/^\[/,"",t); sub(/\]$/,"",t); return t }
    function lhs_name(s, a) { a=s; sub(/=.*/,"",a); gsub(/^[ \t]+|[ \t]+$/,"",a); return a }
    BEGIN {cur=""}
    /^\[[^]]+\][ \t]*$/ { cur=header_name($0); print; next }
    {
      if (cur==target) {
        if (repeat=="true" && $0==oldline) next
        if (repeat!="true" && index($0,"=")>0 && lhs_name($0)==key) next
      }
      print
    }
  ' "$file" > "$tmp" || { rm -f "$tmp"; return 1; }
  mv "$tmp" "$file"
}

apply_config_txt_parameter() {
  local section="$1" key="$2" value="$3" advanced="$4" confirmed="$5" managed
  [ "$confirmed" = "true" ] || { log "Config Manager: ODRZUCONO — wymagane confirm=true."; return 1; }
  [ -n "$section" ] || section="pi5"
  config_manager_validate_section "$section" || { log "Config Manager: nieprawidłowa sekcja [$section]."; return 1; }
  config_manager_validate_value "$key" "$value" "$advanced" || return 1

  # Zachowujemy dotychczasowe specjalne zabezpieczenie wysokiego limitu USB.
  if [ "$key" = "usb_max_current_enable" ] && [ "$value" = "1" ]; then
    collect_system_power_info || true
    if ! [[ "${SYS_POWER_MAX_CURRENT_MA:-}" =~ ^[0-9]+$ ]] || [ "${SYS_POWER_MAX_CURRENT_MA:-0}" -lt 5000 ]; then
      log "Config Manager: ODRZUCONO usb_max_current_enable=1 — nie wykryto zasilania 5 A."
      return 1
    fi
  fi

  find_boot_config || { log "Config Manager: brak zapisywalnego config.txt."; return 1; }
  [ -w "$BOOT_CFG" ] || { log "Config Manager: config.txt nie jest zapisywalny: $BOOT_CFG"; cleanup_mount; return 1; }
  managed="$(dirname "$BOOT_CFG")/$CONFIG_MANAGER_FILENAME"

  system_config_backup || { log "Config Manager: nie udało się utworzyć backupu config.txt."; cleanup_mount; return 1; }
  config_manager_backup_managed "$managed" || { log "Config Manager: nie udało się utworzyć backupu $CONFIG_MANAGER_FILENAME."; cleanup_mount; return 1; }
  config_manager_ensure_include "$BOOT_CFG" "$managed" || { log "Config Manager: nie udało się dodać bezpiecznego include."; cleanup_mount; return 1; }
  config_manager_set_in_file "$managed" "$section" "$key" "$value" || { log "Config Manager: nie udało się zapisać $key."; cleanup_mount; return 1; }
  sync
  rm -f "$BOOT_CONFIG_CACHE_FILE"
  rm -f "$SYSTEM_DEFAULTS_LOCK_FILE" 2>/dev/null || true
  log "Config Manager: zapisano [$section] $key=$value (advanced=$advanced) w $CONFIG_MANAGER_FILENAME."
  mark_host_restart_required "Zmieniono $key w zarządzanej konfiguracji config.txt. Firmware zastosuje zmianę po pełnym restarcie Raspberry Pi 5."
  cleanup_mount
  publish_telemetry_snapshot || true
}

remove_config_txt_parameter() {
  local section="$1" key="$2" value="$3" confirmed="$4" managed
  [ "$confirmed" = "true" ] || { log "Config Manager Remove: ODRZUCONO — wymagane confirm=true."; return 1; }
  [ -n "$section" ] || section="pi5"
  config_manager_validate_section "$section" || { log "Config Manager Remove: nieprawidłowa sekcja [$section]."; return 1; }
  [[ "$key" =~ ^[A-Za-z0-9_.-]{1,64}$ ]] || { log "Config Manager Remove: nieprawidłowy parametr."; return 1; }
  config_manager_safe_token "$value" || { log "Config Manager Remove: nieprawidłowa wartość."; return 1; }
  find_boot_config || { log "Config Manager Remove: brak config.txt."; return 1; }
  managed="$(dirname "$BOOT_CFG")/$CONFIG_MANAGER_FILENAME"
  system_config_backup || { cleanup_mount; return 1; }
  config_manager_backup_managed "$managed" || { cleanup_mount; return 1; }
  config_manager_remove_from_file "$managed" "$section" "$key" "$value" || { cleanup_mount; return 1; }
  sync
  rm -f "$BOOT_CONFIG_CACHE_FILE"
  log "Config Manager: usunięto [$section] $key${value:+=$value} z $CONFIG_MANAGER_FILENAME."
  mark_host_restart_required "Usunięto $key z zarządzanej konfiguracji config.txt. Zmiana zacznie obowiązywać po pełnym restarcie hosta."
  cleanup_mount
  publish_telemetry_snapshot || true
}

restore_config_manager_backup() {
  local confirmed="$1" managed bak absent current_tmp=""
  [ "$confirmed" = "true" ] || { log "Config Manager Restore: ODRZUCONO — wymagane confirm=true."; return 1; }
  find_boot_config || { log "Config Manager Restore: brak config.txt."; return 1; }
  managed="$(dirname "$BOOT_CFG")/$CONFIG_MANAGER_FILENAME"
  bak="${managed}.rpi5cc-manager.bak"
  absent="$CONFIG_MANAGER_ABSENT_FILE"
  [ -f "$bak" ] || [ -f "$absent" ] || { log "Config Manager Restore: brak kopii zarządzanego pliku."; cleanup_mount; return 1; }
  system_config_backup || { cleanup_mount; return 1; }
  if [ -f "$managed" ]; then current_tmp="/tmp/sbc5cc-managed-current-$$"; cp "$managed" "$current_tmp" || true; fi
  if [ -f "$bak" ]; then
    cp "$bak" "$managed" || { rm -f "$current_tmp"; cleanup_mount; return 1; }
  else
    local cfg_tmp="${BOOT_CFG}.rpi5cc-restore.$$"
    rm -f "$managed"
    awk -v begin="$CONFIG_MANAGER_MARK_BEGIN" -v end="$CONFIG_MANAGER_MARK_END" '''
      $0 == begin {skip=1; next}
      $0 == end {skip=0; next}
      skip {next}
      {print}
    ''' "$BOOT_CFG" > "$cfg_tmp" || { rm -f "$cfg_tmp" "$current_tmp"; cleanup_mount; return 1; }
    cp "$cfg_tmp" "$BOOT_CFG" || { rm -f "$cfg_tmp" "$current_tmp"; cleanup_mount; return 1; }
    rm -f "$cfg_tmp"
  fi
  sync
  rm -f "$BOOT_CONFIG_CACHE_FILE" "$current_tmp" "$CONFIG_MANAGER_ABSENT_FILE"
  log "Config Manager Restore: przywrócono poprzedni stan $CONFIG_MANAGER_FILENAME."
  mark_host_restart_required "Przywrócono poprzedni stan zarządzanej konfiguracji config.txt. Wymagany pełny restart hosta."
  cleanup_mount
  publish_telemetry_snapshot || true
}

config_txt_options_signature() {
  [ -r "$OPTIONS_FILE" ] || { printf 'no-options'; return 0; }
  jq -cS '
    def flag($new; $old; $default):
      if has($new) then .[$new]
      elif ((.sections // {}) | has($old)) then .sections[$old]
      else $default end;
    {section_flags:{
      cpu:flag("section_cpu_enabled";"cpu";false),gpu:flag("section_gpu_enabled";"gpu";false),
      power_usb:flag("section_power_usb_enabled";"power_usb";false),pcie_rp1:flag("section_pcie_rp1_enabled";"pcie_rp1";false),
      boot_kernel:flag("section_boot_kernel_enabled";"boot_kernel";false),hardware:flag("section_hardware_enabled";"hardware";false),
      uart_debug:flag("section_uart_debug_enabled";"uart_debug";false),video:flag("section_video_enabled";"video";false),
      device_tree:flag("section_device_tree_enabled";"device_tree";false),compatibility:flag("section_compatibility_enabled";"compatibility";false),
      custom_parameters:flag("section_custom_parameters_enabled";"custom_parameters";false)},
     manager:(.config_txt_manager // {}),cpu:(.config_cpu // {}),gpu_profile:(.config_gpu_profile // "advanced"),gpu:(.config_gpu // {}),power_usb:(.config_power_usb // {}),
     pcie_rp1:(.config_pcie_rp1 // {}),boot_kernel:(.config_boot_kernel // {}),hardware:(.config_hardware // {}),
     uart_debug:(.config_uart_debug // {}),video:(.config_video // {}),device_tree:(.config_device_tree // {}),
     compatibility:(.config_compatibility // {}),custom:(.config_custom_parameters // [])}
  ' "$OPTIONS_FILE" 2>/dev/null | sha256sum | awk '{print $1}'
}

config_txt_options_static_entries() {
  [ -r "$OPTIONS_FILE" ] || return 0
  jq -r '
    def flag($new; $old; $default):
      if has($new) then .[$new]
      elif ((.sections // {}) | has($old)) then .sections[$old]
      else $default end;
    def gpu_cfg:
      (.config_gpu_profile // "advanced") as $p |
      if $p == "factory" then {core_freq:"auto",core_freq_min:"auto",isp_freq:"auto",isp_freq_min:"auto",v3d_freq:"auto",v3d_freq_min:"auto",gpu_freq_min:"auto"}
      elif $p == "eco" then {core_freq:"850",core_freq_min:"500",isp_freq:"850",isp_freq_min:"500",v3d_freq:"900",v3d_freq_min:"500",gpu_freq_min:"auto"}
      elif $p == "balanced" then {core_freq:"950",core_freq_min:"500",isp_freq:"950",isp_freq_min:"500",v3d_freq:"1000",v3d_freq_min:"500",gpu_freq_min:"auto"}
      elif $p == "performance" then {core_freq:"1000",core_freq_min:"500",isp_freq:"1000",isp_freq_min:"500",v3d_freq:"1100",v3d_freq_min:"500",gpu_freq_min:"auto"}
      elif $p == "experimental" then {core_freq:"1100",core_freq_min:"500",isp_freq:"1100",isp_freq_min:"500",v3d_freq:"1200",v3d_freq_min:"500",gpu_freq_min:"auto"}
      else (.config_gpu // {}) end;
    [
      # CPU/OC is owned by the dedicated v2.7.0 CPU Profile Manager.
      {},
      (if flag("section_gpu_enabled";"gpu";false) then gpu_cfg else {} end),
      (if flag("section_power_usb_enabled";"power_usb";false) then (.config_power_usb // {}) else {} end),
      (if flag("section_pcie_rp1_enabled";"pcie_rp1";false) then (.config_pcie_rp1 // {}) else {} end),
      (if flag("section_boot_kernel_enabled";"boot_kernel";false) then (.config_boot_kernel // {}) else {} end),
      (if flag("section_hardware_enabled";"hardware";false) then (.config_hardware // {}) else {} end),
      (if flag("section_uart_debug_enabled";"uart_debug";false) then (.config_uart_debug // {}) else {} end),
      (if flag("section_video_enabled";"video";false) then (.config_video // {}) else {} end),
      (if flag("section_device_tree_enabled";"device_tree";false) then (.config_device_tree // {}) else {} end),
      (if flag("section_compatibility_enabled";"compatibility";false) then (.config_compatibility // {}) else {} end)
    ] | add
    | to_entries[]?
    | select(.value != null)
    | (.value|tostring) as $v
    | select($v != "" and $v != "auto")
    | [.key,$v] | @tsv
  ' "$OPTIONS_FILE" 2>/dev/null || true
}

config_txt_options_custom_entries() {
  [ -r "$OPTIONS_FILE" ] || return 0
  jq -r '
    def flag($new; $old; $default):
      if has($new) then .[$new]
      elif ((.sections // {}) | has($old)) then .sections[$old]
      else $default end;
    (if flag("section_custom_parameters_enabled";"custom_parameters";false) then (.config_custom_parameters // []) else [] end)[]?
    | [(.section // "all" | tostring),(.key // "" | tostring),(.value // "" | tostring)]
    | @tsv
  ' "$OPTIONS_FILE" 2>/dev/null || true
}

config_gpu_validate_pairs_tsv() {
  local file="$1" key value core="" core_min="" isp="" isp_min="" v3d="" v3d_min="" gmin=""
  [ -r "$file" ] || return 0
  while IFS=$'\t' read -r key value; do
    case "$key" in
      core_freq) core="$value" ;; core_freq_min) core_min="$value" ;;
      isp_freq) isp="$value" ;; isp_freq_min) isp_min="$value" ;;
      v3d_freq) v3d="$value" ;; v3d_freq_min) v3d_min="$value" ;;
      gpu_freq_min) gmin="$value" ;;
    esac
  done < "$file"
  [ -z "$core" ] || [ -z "$core_min" ] || [ "$core_min" -le "$core" ] || { log "Config Options: core_freq_min=$core_min > core_freq=$core — odrzucono."; return 1; }
  [ -z "$isp" ] || [ -z "$isp_min" ] || [ "$isp_min" -le "$isp" ] || { log "Config Options: isp_freq_min=$isp_min > isp_freq=$isp — odrzucono."; return 1; }
  [ -z "$v3d" ] || [ -z "$v3d_min" ] || [ "$v3d_min" -le "$v3d" ] || { log "Config Options: v3d_freq_min=$v3d_min > v3d_freq=$v3d — odrzucono."; return 1; }
  if [ -n "$gmin" ]; then
    [ -z "$core" ] || [ "$gmin" -le "$core" ] || { log "Config Options: gpu_freq_min=$gmin > core_freq=$core — odrzucono."; return 1; }
    [ -z "$isp" ] || [ "$gmin" -le "$isp" ] || { log "Config Options: gpu_freq_min=$gmin > isp_freq=$isp — odrzucono."; return 1; }
    [ -z "$v3d" ] || [ "$gmin" -le "$v3d" ] || { log "Config Options: gpu_freq_min=$gmin > v3d_freq=$v3d — odrzucono."; return 1; }
  fi
  return 0
}

sync_config_txt_from_options() {
  local force="${1:-false}" sig desired managed key value section line entries_count=0 static_tmp custom_tmp owner_marker
  owner_marker="# Source: Supervisor/App Configuration options"

  load_options
  [ "$CONFIG_TXT_OPTIONS_ENABLED" = "true" ] || return 0
  [ -r "$OPTIONS_FILE" ] || return 0
  if [ -e "$SYSTEM_DEFAULTS_LOCK_FILE" ]; then
    log "Config Options: pomijam synchronizację — aktywny bezpieczny lock po przywróceniu domyślnych ustawień SBC5."
    return 0
  fi

  sig="$(config_txt_options_signature)"
  if [ "$force" != "true" ] && [ -n "$LAST_CONFIG_OPTIONS_SIGNATURE" ] && [ "$sig" = "$LAST_CONFIG_OPTIONS_SIGNATURE" ]; then
    return 0
  fi

  desired="/tmp/sbc5cc-managed-options-$$.txt"
  static_tmp="/tmp/rpi5cc-static-options-$$.tsv"
  custom_tmp="/tmp/rpi5cc-custom-options-$$.tsv"
  config_txt_options_static_entries > "$static_tmp"
  config_txt_options_custom_entries > "$custom_tmp"
  config_gpu_validate_pairs_tsv "$static_tmp" || {
    log "Config Options: synchronizacja przerwana — niespójne wartości min/max GPU/V3D/ISP."
    rm -f "$desired" "$static_tmp" "$custom_tmp"
    return 1
  }

  cat > "$desired" <<EOF
# SBC5 Control Center $APP_VERSION — zarządzany plik config.txt
$owner_marker
# Zmieniaj ustawienia z zakładki Konfiguracja aplikacji. Auto = brak wpisu zarządzanego.
EOF

  if [ -s "$static_tmp" ]; then
    printf '\n[all]\n' >> "$desired"
    while IFS=$'\t' read -r key value; do
      [ -n "$key" ] || continue
      config_manager_validate_value "$key" "$value" "$CONFIG_TXT_OPTIONS_ADVANCED" || {
        log "Config Options: synchronizacja przerwana — nieprawidłowe $key=$value."
        rm -f "$desired" "$static_tmp" "$custom_tmp"
        return 1
      }
      if [ "$key" = "usb_max_current_enable" ] && [ "$value" = "1" ]; then
        collect_system_power_info || true
        if ! [[ "${SYS_POWER_MAX_CURRENT_MA:-}" =~ ^[0-9]+$ ]] || [ "${SYS_POWER_MAX_CURRENT_MA:-0}" -lt 5000 ]; then
          log "Config Options: ODRZUCONO usb_max_current_enable=1 — nie wykryto zasilania 5 A."
          rm -f "$desired" "$static_tmp" "$custom_tmp"
          return 1
        fi
      fi
      line="$(config_manager_line_for "$key" "$value")"
      printf '%s\n' "$line" >> "$desired"
      entries_count=$((entries_count+1))
    done < "$static_tmp"
  fi

  while IFS=$'\t' read -r section key value; do
    [ -n "$key" ] || continue
    [ -n "$section" ] || section="all"
    config_manager_validate_section "$section" || {
      log "Config Options: nieprawidłowa sekcja [$section] dla $key."
      rm -f "$desired" "$static_tmp" "$custom_tmp"
      return 1
    }
    config_manager_validate_value "$key" "$value" "$CONFIG_TXT_OPTIONS_ADVANCED" || {
      log "Config Options: synchronizacja przerwana — nieprawidłowe [$section] $key=$value."
      rm -f "$desired" "$static_tmp" "$custom_tmp"
      return 1
    }
    if [ "$key" = "usb_max_current_enable" ] && [ "$value" = "1" ]; then
      collect_system_power_info || true
      if ! [[ "${SYS_POWER_MAX_CURRENT_MA:-}" =~ ^[0-9]+$ ]] || [ "${SYS_POWER_MAX_CURRENT_MA:-0}" -lt 5000 ]; then
        log "Config Options: ODRZUCONO usb_max_current_enable=1 — nie wykryto zasilania 5 A."
        rm -f "$desired" "$static_tmp" "$custom_tmp"
        return 1
      fi
    fi
    line="$(config_manager_line_for "$key" "$value")"
    printf '\n[%s]\n%s\n' "$section" "$line" >> "$desired"
    entries_count=$((entries_count+1))
  done < "$custom_tmp"
  rm -f "$static_tmp" "$custom_tmp"

  find_boot_config || { boot_access_warn_throttled "Host Boot Access: config.txt niedostępny — wstrzymuję zapis profilu CPU i ustawień boot do czasu odzyskania Host PID/boot access."; rm -f "$desired"; return 1; }
  [ -w "$BOOT_CFG" ] || { log "Config Options: config.txt nie jest zapisywalny: $BOOT_CFG"; rm -f "$desired"; cleanup_mount; return 1; }
  managed="$(dirname "$BOOT_CFG")/$CONFIG_MANAGER_FILENAME"

  # Bez parametrów nie przejmujemy pliku utworzonego innym interfejsem. Jeśli plik
  # już należy do Options UI, wyzerowanie wszystkich pól usuwa wcześniej zarządzane wpisy.
  if [ "$entries_count" -eq 0 ] && { [ ! -f "$managed" ] || ! grep -Fqx "$owner_marker" "$managed" 2>/dev/null; }; then
    LAST_CONFIG_OPTIONS_SIGNATURE="$sig"
    log "Config Options: menedżer włączony, ale wszystkie pola są Auto — brak zmian config.txt."
    rm -f "$desired"
    cleanup_mount
    return 0
  fi

  if [ -f "$managed" ] && config_manager_semantically_equal "$desired" "$managed" && grep -Eq '^[[:space:]]*include[[:space:]]+sbc5cc-managed\.txt[[:space:]]*$' "$BOOT_CFG" 2>/dev/null; then
    LAST_CONFIG_OPTIONS_SIGNATURE="$sig"
    rm -f "$desired"
    cleanup_mount
    return 0
  fi

  system_config_backup || { log "Config Options: nie udało się utworzyć backupu config.txt."; rm -f "$desired"; cleanup_mount; return 1; }
  config_manager_backup_managed "$managed" || { log "Config Options: nie udało się utworzyć backupu $CONFIG_MANAGER_FILENAME."; rm -f "$desired"; cleanup_mount; return 1; }
  config_manager_ensure_include "$BOOT_CFG" "$managed" || { log "Config Options: nie udało się dodać include $CONFIG_MANAGER_FILENAME."; rm -f "$desired"; cleanup_mount; return 1; }
  cp "$desired" "$managed" || { log "Config Options: błąd zapisu $CONFIG_MANAGER_FILENAME."; rm -f "$desired"; cleanup_mount; return 1; }
  rm -f "$desired" "$BOOT_CONFIG_CACHE_FILE"
  sync
  LAST_CONFIG_OPTIONS_SIGNATURE="$sig"
  log "Config Options: zsynchronizowano $entries_count wpisów do $CONFIG_MANAGER_FILENAME. Wymagany pełny restart SBC5."
  mark_host_restart_required "Zmieniono ustawienia config.txt w zakładce Konfiguracja aplikacji. Firmware zastosuje je po pełnym restarcie Raspberry Pi 5."
  cleanup_mount
  publish_telemetry_snapshot || true
}

clear_2_8_22_version_only_config_restart() {
  # 2.8.22 potrafił przepisać sbc5cc-managed.txt wyłącznie dlatego, że w komentarzu
  # nagłówka zmienił się numer wersji aplikacji. Taki zapis nie zmienia boot semantics.
  # Czyścimy wyłącznie marker o dokładnie tym pochodzeniu, z zachowaniem guardów:
  # - marker został utworzony przez 2.8.22 i ma konkretny reason Config Options,
  # - ostatni backup i bieżący plik różnią się semantycznie wyłącznie nagłówkiem wersji,
  # - telemetria boot nie wykrywa realnej różnicy saved vs active.
  [ -r "$RESTART_STATE_FILE" ] || return 0
  local type reason marker_version managed backup pending=false current_header=false backup_header=false
  type="$(jq -r '.type // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
  reason="$(jq -r '.reason // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
  marker_version="$(jq -r '.version // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
  [ "$type" = "host" ] || return 0
  [ "$marker_version" = "2.8.22" ] || return 0
  [ "$reason" = "Zmieniono ustawienia config.txt w zakładce Konfiguracja aplikacji. Firmware zastosuje je po pełnym restarcie Raspberry Pi 5." ] || return 0

  find_boot_config || return 0
  managed="$(dirname "$BOOT_CFG")/$CONFIG_MANAGER_FILENAME"
  backup="${managed}.rpi5cc-manager.bak"
  [ -r "$managed" ] && [ -r "$backup" ] || { cleanup_mount; return 0; }
  grep -Eq '^# SBC5 Control Center 2\.8\.22([^ ]*) — zarządzany plik config\.txt$' "$managed" 2>/dev/null && current_header=true
  grep -Eq '^# SBC5 Control Center 2\.8\.21([^ ]*) — zarządzany plik config\.txt$' "$backup" 2>/dev/null && backup_header=true
  if [ "$current_header" != "true" ] || [ "$backup_header" != "true" ] || ! config_manager_semantically_equal "$managed" "$backup"; then
    cleanup_mount
    return 0
  fi
  cleanup_mount

  if [ -r "$BOOT_CONFIG_CACHE_FILE" ]; then
    pending="$(jq -r '.config_pending_restart // false' "$BOOT_CONFIG_CACHE_FILE" 2>/dev/null || echo false)"
  else
    collect_boot_configuration >/dev/null 2>&1 || true
    pending="${SYS_CONFIG_PENDING_RESTART:-false}"
  fi
  if [ "$pending" = "true" ]; then
    log "Restart Manager: wykryto historyczny marker 2.8.22 po zmianie nagłówka, ale saved != active — zachowuję restart hosta jako bezpieczny."
    return 0
  fi

  rm -f "$RESTART_STATE_FILE"
  if [ -r "$POST_UPDATE_STATE_FILE" ] && [ "$(jq -r '.restart_required // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)" = "host" ] \
     && [ "$(jq -r '.to_version // empty' "$POST_UPDATE_STATE_FILE" 2>/dev/null || true)" = "2.8.22" ]; then
    rm -f "$POST_UPDATE_STATE_FILE"
  fi
  native_restart_repair_clear || true
  log "Restart Manager: usunięto fałszywy restart hosta z 2.8.22 — zmienił się wyłącznie komentarz wersji w sbc5cc-managed.txt."
}

clear_2_8_24_version_only_cpu_restart() {
  # 2.8.24 porównywał dedykowany profil CPU bajt-po-bajcie. Zmiana wyłącznie
  # numeru wersji w komentarzu nagłówka mogła więc przepisać identyczny profil
  # i utworzyć fałszywy restart=host. Czyścimy tylko marker spełniający wszystkie
  # warunki dowodzące, że semantyka profilu oraz include nie uległy zmianie.
  [ -r "$RESTART_STATE_FILE" ] || return 0
  local type scope marker_version reason cpu_file cpu_backup boot_backup current_header=false backup_header=false
  type="$(jq -r '.type // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
  scope="$(jq -r '.scope // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
  marker_version="$(jq -r '.version // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
  reason="$(jq -r '.reason // empty' "$RESTART_STATE_FILE" 2>/dev/null || true)"
  [ "$type" = "host" ] || return 0
  [ "$scope" = "cpu_profile" ] || return 0
  [ "$marker_version" = "2.8.24" ] || return 0
  [[ "$reason" == Zapisano\ profil\ CPU/OC* ]] || return 0

  find_boot_config || return 0
  cpu_file="$(dirname "$BOOT_CFG")/$CPU_PROFILE_FILENAME"
  cpu_backup="${cpu_file}.rpi5cc-cpu.bak"
  boot_backup="${BOOT_CFG}.rpi5cc-system.bak"
  [ -r "$cpu_file" ] && [ -r "$cpu_backup" ] && [ -r "$boot_backup" ] || { cleanup_mount; return 0; }

  grep -Eq '^# SBC5 Control Center 2\.8\.24([^ ]*) — dedykowany profil CPU/OC$' "$cpu_file" 2>/dev/null && current_header=true
  grep -Eq '^# SBC5 Control Center [0-9]+\.[0-9]+\.[0-9]+([^ ]*) — dedykowany profil CPU/OC$' "$cpu_backup" 2>/dev/null && backup_header=true
  if [ "$current_header" != "true" ] || [ "$backup_header" != "true" ] || ! cpu_profile_semantically_equal "$cpu_file" "$cpu_backup"; then
    cleanup_mount
    return 0
  fi

  # Jeżeli include nie istniał przed zapisem, byłaby to realna zmiana boot i marker
  # musi pozostać. Wymagamy obecności include zarówno przed, jak i po operacji.
  if ! grep -Eq '^[[:space:]]*include[[:space:]]+sbc5cc-cpu-profile\.txt[[:space:]]*$' "$BOOT_CFG" 2>/dev/null \
     || ! grep -Eq '^[[:space:]]*include[[:space:]]+sbc5cc-cpu-profile\.txt[[:space:]]*$' "$boot_backup" 2>/dev/null; then
    cleanup_mount
    return 0
  fi
  cleanup_mount

  rm -f "$RESTART_STATE_FILE"
  native_restart_repair_clear || true
  log "Restart Manager: usunięto fałszywy restart CPU z 2.8.24 — profil i include były semantycznie identyczne; zmienił się wyłącznie komentarz wersji."
}

config_txt_options_sync_loop() {
  local sig interval enabled settings
  while true; do
    settings="$(jq -r '[(.config_txt_manager.enabled // false), (.config_txt_manager.sync_interval_seconds // 5)] | @tsv' "$OPTIONS_FILE" 2>/dev/null || printf 'false\t5')"
    IFS=$'\t' read -r enabled interval <<< "$settings"
    num_in_range "${interval:-5}" 2 60 || interval=5

    if [ "$enabled" != "true" ]; then
      sleep "$CONFIG_DISABLED_POLL_SECONDS"
      continue
    fi

    sleep "$interval"
    sig="$(config_txt_options_signature)"
    if [ -z "$LAST_CONFIG_OPTIONS_SIGNATURE" ] || [ "$sig" != "$LAST_CONFIG_OPTIONS_SIGNATURE" ]; then
      sync_config_txt_from_options false || true
    fi
  done
}


clean_fan_config() {
  awk -v begin="$MARK_BEGIN" -v end="$MARK_END" \
      -v overlay10="$OVERLAY_10_NAME" -v overlay15="$OVERLAY_15_NAME" '
    $0 == begin {skip=1; next}
    $0 == end   {skip=0; next}
    skip {next}

    /^dtparam=fan_temp[0-9]+=/ {next}
    /^dtparam=fan_temp[0-9]+_hyst=/ {next}
    /^dtparam=fan_temp[0-9]+_speed=/ {next}

    index($0, "dtoverlay=" overlay10) == 1 {next}
    index($0, "dtoverlay=" overlay15) == 1 {next}
    index($0, "dtoverlay=rpi5-custom") == 1 {next}

    {print}
  ' "$BOOT_CFG" > "${BOOT_CFG}.tmp"
}

copy_active_overlay_to_possible_locations() {
  local copied=0 d
  for d in \
    "$BOOT_MP/overlays" \
    "$BOOT_MP/slot-A/overlays" \
    "$BOOT_MP/slot-B/overlays"
  do
    if [ -d "$d" ]; then
      if cp "$ACTIVE_OVERLAY_DTBO" "$d/${ACTIVE_OVERLAY_NAME}.dtbo"; then
        log "DTBO zapisany: ${d#$BOOT_MP/}/${ACTIVE_OVERLAY_NAME}.dtbo"
        copied=$((copied+1))
      fi
    fi
  done

  for d in "$BOOT_MP/slot-A/overlays" "$BOOT_MP/slot-B/overlays"; do
    if [ -d "$d" ] && [ ! -e "$d/README" ]; then
      : > "$d/README"
      log "Dodano znacznik README w ${d#$BOOT_MP/}/"
    fi
  done

  [ "$copied" -gt 0 ] || {
    log "BŁĄD: nie znaleziono żadnego katalogu overlays na partycji boot."
    return 1
  }
}

write_overlay_profile() {
  local profile="$1"
  rm -f "$FACTORY_RESTORE_PENDING_FILE" 2>/dev/null || true
  compile_overlay "$profile" || return 1

  if ! find_boot_config; then
    log "Nie znaleziono partycji rozruchowej z config.txt."
    return 1
  fi

  log "Znaleziono config.txt na $BOOT_PART"
  make_backup

  if ! copy_active_overlay_to_possible_locations; then
    cleanup_mount
    return 1
  fi

  clean_fan_config

  cat >> "${BOOT_CFG}.tmp" <<PROFILE

$MARK_BEGIN
# Profil: $profile
dtparam=cooling_fan=on
dtoverlay=${ACTIVE_OVERLAY_NAME}
$MARK_END
PROFILE

  cp "${BOOT_CFG}.tmp" "$BOOT_CFG"
  rm -f "${BOOT_CFG}.tmp"
  sync

  case "$profile" in custom15) printf 'custom1\n' > "$LAST_FAN_PROFILE_FILE" ;; *) printf '%s\n' "$profile" > "$LAST_FAN_PROFILE_FILE" ;; esac
  log "Profil '$profile' zapisany."
  log "Wymagany pełny restart hosta."
  log "Przed restartem możesz uruchomić DIAGNOSE."
  mark_host_restart_required "Zapisano profil ${profile} i zmieniono Device Tree/config.txt. Kernel musi ponownie wczytać konfigurację chłodzenia."

  cleanup_mount
}

write_4point_profile() {
  local profile="$1"
  local t0 t1 t2 t3 h0 h1 h2 h3 s0 s1 s2 s3

  case "$profile" in
    factory)
      t0=50000; t1=60000; t2=67500; t3=75000
      h0=5000; h1=5000; h2=5000; h3=5000
      s0=75; s1=125; s2=175; s3=250 ;;
    quiet)
      t0=50000; t1=60000; t2=68000; t3=75000
      h0=5000; h1=5000; h2=5000; h3=5000
      s0=75; s1=125; s2=175; s3=250 ;;
    normal)
      t0=45000; t1=55000; t2=65000; t3=72000
      h0=4000; h1=4000; h2=4000; h3=4000
      s0=75; s1=125; s2=175; s3=250 ;;
    cool)
      t0=40000; t1=50000; t2=60000; t3=68000
      h0=3000; h1=3000; h2=3000; h3=3000
      s0=75; s1=125; s2=175; s3=250 ;;
    sub50)
      t0=40000; t1=44000; t2=47000; t3=49000
      h0=2000; h1=2000; h2=2000; h3=2000
      s0=90; s1=140; s2=200; s3=255 ;;
    stable50)
      t0=46000; t1=48500; t2=50000; t3=52500
      h0=1000; h1=1000; h2=1000; h3=1000
      s0=75; s1=115; s2=155; s3=255 ;;
    *)
      log "Nieznany profil: $profile"
      return 1 ;;
  esac

  if ! find_boot_config; then
    log "Nie znaleziono partycji rozruchowej z config.txt."
    return 1
  fi

  log "Znaleziono config.txt na $BOOT_PART"
  make_backup
  clean_fan_config

  cat >> "${BOOT_CFG}.tmp" <<PROFILE

$MARK_BEGIN
# Profil: $profile
dtparam=cooling_fan=on
dtparam=fan_temp0=$t0
dtparam=fan_temp0_hyst=$h0
dtparam=fan_temp0_speed=$s0
dtparam=fan_temp1=$t1
dtparam=fan_temp1_hyst=$h1
dtparam=fan_temp1_speed=$s1
dtparam=fan_temp2=$t2
dtparam=fan_temp2_hyst=$h2
dtparam=fan_temp2_speed=$s2
dtparam=fan_temp3=$t3
dtparam=fan_temp3_hyst=$h3
dtparam=fan_temp3_speed=$s3
$MARK_END
PROFILE

  cp "${BOOT_CFG}.tmp" "$BOOT_CFG"
  rm -f "${BOOT_CFG}.tmp"
  sync

  printf '%s\n' "$profile" > "$LAST_FAN_PROFILE_FILE"
  if [ "$profile" = "factory" ]; then
    : > "$FACTORY_RESTORE_PENDING_FILE"
    fan_control_release_thermal_ownership adaptive factory_profile_selected >/dev/null 2>&1 || true
    log "Fabryczny Active Cooler: Adaptive PWM zwolniony; do restartu sterowanie pozostaje po stronie kernela."
  else
    rm -f "$FACTORY_RESTORE_PENDING_FILE" 2>/dev/null || true
  fi
  log "Profil '$profile' zapisany. Wymagany pełny restart hosta."
  mark_host_restart_required "Zapisano profil ${profile} w config.txt. Zmiany parametrów wentylatora wymagają pełnego restartu hosta."
  cleanup_mount
}

fdt_symbol() {
  local sym="$1"
  if [ -r /sys/firmware/fdt ] && command -v fdtget >/dev/null 2>&1; then
    fdtget -t s /sys/firmware/fdt /__symbols__ "$sym" 2>/dev/null || true
  fi
}

diagnose_overlay() {
  log "============================================================"
  log "DIAGNOSTYKA DEVICE TREE OVERLAY 10/15 PUNKTÓW"
  log "============================================================"
  log "Kernel: $(uname -r 2>/dev/null || echo '?')"
  log "Model: $(read_rpi_model 2>/dev/null || echo 'N/D')"
  log "Cmdline: $(cat /proc/cmdline 2>/dev/null || echo '?')"

  local level="?" maxlevel="?" pwm="?" rpm="?" d f p
  for d in /sys/class/thermal/cooling_device*; do
    [ -r "$d/type" ] || continue
    grep -qi fan "$d/type" 2>/dev/null || continue
    level="$(cat "$d/cur_state" 2>/dev/null || echo '?')"
    maxlevel="$(cat "$d/max_state" 2>/dev/null || echo '?')"
    log "Cooling device: $d type=$(cat "$d/type" 2>/dev/null) state=$level/$maxlevel"
  done

  for f in /sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input; do
    [ -r "$f" ] || continue
    rpm="$(cat "$f" 2>/dev/null || echo '?')"
    p="${f%fan1_input}pwm1"
    [ -r "$p" ] && pwm="$(cat "$p" 2>/dev/null || echo '?')"
    log "Fan hwmon: $f RPM=$rpm PWM=$pwm"
  done

  log "Aktywne progi: $(read_kernel_trip_points)"

  if ! find_boot_config; then
    log "BŁĄD: nie znaleziono partycji boot z config.txt."
    return 1
  fi

  log "Boot: $BOOT_PART"
  log "config.txt: $BOOT_CFG"

  local os_prefix overlay_prefix last_section
  os_prefix="$(sed -n 's/^[[:space:]]*os_prefix[[:space:]]*=[[:space:]]*//p' "$BOOT_CFG" | tail -n1)"
  overlay_prefix="$(sed -n 's/^[[:space:]]*overlay_prefix[[:space:]]*=[[:space:]]*//p' "$BOOT_CFG" | tail -n1)"
  last_section="$(grep -E '^[[:space:]]*\[[^]]+\]' "$BOOT_CFG" | tail -n1)"
  [ -n "$os_prefix" ] || os_prefix="<brak>"
  [ -n "$overlay_prefix" ] || overlay_prefix="<brak; domyślnie overlays/>"
  [ -n "$last_section" ] || last_section="<brak>"

  log "os_prefix=$os_prefix"
  log "overlay_prefix=$overlay_prefix"
  log "Ostatnia sekcja config.txt: $last_section"

  for ov in "$OVERLAY_10_NAME" "$OVERLAY_15_NAME" "$OVERLAY_CUSTOM_LEGACY_NAME" rpi5-custom1 rpi5-custom2 rpi5-custom3 rpi5-custom4 rpi5-custom5; do
    if grep -q "^dtoverlay=${ov}\([,[:space:]]\|$\)" "$BOOT_CFG"; then
      log "Wpis dtoverlay=${ov}: TAK"
    else
      log "Wpis dtoverlay=${ov}: NIE"
    fi
  done

  log "--- Lokalizacje DTBO ---"
  local exists size readme ov
  for d in "$BOOT_MP/overlays" "$BOOT_MP/slot-A/overlays" "$BOOT_MP/slot-B/overlays"; do
    if [ -d "$d" ]; then
      readme=0; [ -e "$d/README" ] && readme=1
      for ov in "$OVERLAY_10_NAME" "$OVERLAY_15_NAME" "$OVERLAY_CUSTOM_LEGACY_NAME" rpi5-custom1 rpi5-custom2 rpi5-custom3 rpi5-custom4 rpi5-custom5; do
        exists=0; [ -f "$d/${ov}.dtbo" ] && exists=1
        size=0; [ "$exists" -eq 1 ] && size="$(wc -c < "$d/${ov}.dtbo")"
        log "${d#$BOOT_MP/}/ ${ov}: dtbo=$(yesno "$exists") size=$size README=$(yesno "$readme")"
      done
    fi
  done

  log "--- Ostatnie niekomentowane wpisy config.txt ---"
  grep -v '^[[:space:]]*#' "$BOOT_CFG" | grep -v '^[[:space:]]*$' | tail -n 25 | while IFS= read -r line; do
    log "CFG> $line"
  done

  cleanup_mount
  log "============================================================"
  log "KONIEC DIAGNOSTYKI"
  log "Dla profilu 15 pkt oczekiwane max_state=15."
  log "============================================================"
}

read_cpu_temp_millideg() {
  local z type value
  for z in /sys/class/thermal/thermal_zone*; do
    [ -r "$z/type" ] || continue
    IFS= read -r type < "$z/type" 2>/dev/null || true
    type="${type,,}"
    case "$type" in
      *cpu*|cpu-thermal|soc_thermal)
        [ -r "$z/temp" ] || continue
        IFS= read -r value < "$z/temp" 2>/dev/null || true
        case "$value" in ''|*[!0-9-]*) ;; *) printf '%s\n' "$value"; return 0 ;; esac
        ;;
    esac
  done
  if [ -r /sys/class/thermal/thermal_zone0/temp ]; then IFS= read -r value < /sys/class/thermal/thermal_zone0/temp 2>/dev/null || value=0; else value=0; fi
  printf '%s\n' "${value:-0}"
}

read_cpu_frequency_khz() {
  local path v
  for path in \
    /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq \
    /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq; do
    v="$(host_read_one_line "$path" 2>/dev/null || true)"
    case "$v" in ''|*[!0-9]*) ;; *) echo "$v"; return 0 ;; esac
  done
  return 1
}

read_cpu_frequency_bound_khz() {
  local kind="$1" path v
  case "$kind" in
    min) path=/sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq ;;
    max) path=/sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq ;;
    *) return 1 ;;
  esac
  v="$(host_read_one_line "$path" 2>/dev/null || true)"
  case "$v" in ''|*[!0-9]*) return 1 ;; esac
  echo "$v"
}

read_cpu_governor() {
  local v
  v="$(host_read_one_line /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || true)"
  [ -n "$v" ] || return 1
  printf '%s\n' "$v"
}

read_rpi_model() {
  local path value=""
  for path in /proc/device-tree/model /sys/firmware/devicetree/base/model; do
    value="$(host_read_text "$path" 2>/dev/null | head -n1 || true)"
    value="${value//$'\n'/}"
    [ -n "$value" ] && { printf '%s\n' "$value"; return 0; }
  done

  # Ostatni fallback: prywatny sysfs w uprzywilejowanym kontenerze.
  mkdir -p "$HOST_SYSFS_MP" 2>/dev/null || true
  if ! mountpoint -q "$HOST_SYSFS_MP" 2>/dev/null; then
    mount -t sysfs sysfs "$HOST_SYSFS_MP" >/dev/null 2>&1 || true
  fi
  path="$HOST_SYSFS_MP/firmware/devicetree/base/model"
  if [ -r "$path" ]; then
    value="$(cat "$path" 2>/dev/null | tr -d '\000\r\n' || true)"
    [ -n "$value" ] && { printf '%s\n' "$value"; return 0; }
  fi
  return 1
}

dt_power_dir() {
  local d
  for d in \
    /proc/device-tree/chosen/power \
    /sys/firmware/devicetree/base/chosen/power \
    "$HOST_SYSFS_MP/firmware/devicetree/base/chosen/power"; do
    [ -d "$d" ] && { echo "$d"; return 0; }
  done

  # Docker/HAOS może maskować /sys/firmware w istniejącym montowaniu sysfs.
  # Aplikacja ma SYS_ADMIN, więc próbujemy utworzyć własny, niezamaskowany mount sysfs.
  mkdir -p "$HOST_SYSFS_MP" 2>/dev/null || true
  if ! mountpoint -q "$HOST_SYSFS_MP" 2>/dev/null; then
    mount -t sysfs sysfs "$HOST_SYSFS_MP" >/dev/null 2>&1 || true
  fi
  d="$HOST_SYSFS_MP/firmware/devicetree/base/chosen/power"
  [ -d "$d" ] && { echo "$d"; return 0; }
  return 1
}

read_dt_u32_be() {
  local f="$1" hex
  [ -r "$f" ] || return 1
  hex="$(od -An -tx1 -N4 "$f" 2>/dev/null | tr -d ' \n')"
  [ "${#hex}" -eq 8 ] || return 1
  printf '%u\n' "$((16#$hex))"
}

read_dt_hex8() {
  local f="$1" hex
  [ -r "$f" ] || return 1
  hex="$(od -An -tx1 -N8 "$f" 2>/dev/null | tr -d ' \n')"
  [ "${#hex}" -ge 8 ] || return 1
  printf '%s\n' "$hex"
}

read_vcgencmd_usb_high() {
  local bin out val
  for bin in /usr/bin/vcgencmd /opt/vc/bin/vcgencmd /bin/vcgencmd; do
    [ -x "$bin" ] || continue
    out="$("$bin" get_config usb_max_current_enable 2>/dev/null || true)"
    val="${out##*=}"
    case "$val" in
      0) echo 0; return 0 ;;
      1) echo 1; return 0 ;;
    esac
  done
  return 1
}

read_boot_usb_current_override() {
  local cache=/tmp/sbc5_usb_current_config_cache now ts value line boot_cfg
  now="$(date +%s)"
  if [ -r "$cache" ]; then
    IFS='|' read -r ts value < "$cache" || true
    case "$ts" in ''|*[!0-9]*) ts=0 ;; esac
    if [ $((now - ts)) -lt 60 ] 2>/dev/null; then
      [ "$value" != "null" ] && { echo "$value"; return 0; }
      return 1
    fi
  fi

  value="null"
  if discover_boot_config_readonly; then
    boot_cfg="$DISCOVER_BOOT_ROOT/$DISCOVER_BOOT_REL"
    if [ -r "$boot_cfg" ]; then
      line="$(grep -E '^[[:space:]]*usb_max_current_enable[[:space:]]*=' "$boot_cfg" 2>/dev/null | tail -n1 | sed 's/[[:space:]]//g' || true)"
      case "$line" in usb_max_current_enable=0) value=0 ;; usb_max_current_enable=1) value=1 ;; esac
    fi
    cleanup_discovered_boot_mount
  fi

  printf '%s|%s\n' "$now" "$value" > "$cache" 2>/dev/null || true
  [ "$value" != "null" ] && { echo "$value"; return 0; }
  return 1
}

reset_boot_config_globals() {
  SYS_BOOT_CONFIG_AVAILABLE="false"
  SYS_BOOT_CONFIG_DEVICE=""
  SYS_BOOT_CONFIG_PATH=""
  SYS_BOOT_CONFIG_SOURCE=""
  SYS_BOOT_CONFIG_SHA256=""
  SYS_BOOT_CONFIG_ENTRY_COUNT=0
  SYS_BOOT_CONFIG_TRUNCATED="false"
  SYS_BOOT_CONFIG_ENTRIES_JSON='[]'
  SYS_BOOT_CONFIG_INCLUDES_JSON='[]'
  SYS_BOOT_CONFIG_OVERLAYS_JSON='[]'
  SYS_BOOT_CONFIG_DTPARAMS_JSON='[]'
  SYS_ACTIVE_CONFIG_INT_JSON='{}'
  SYS_ACTIVE_CONFIG_STR_JSON='{}'
  SYS_BOOTLOADER_CONFIG_JSON='{}'
  SYS_CONFIG_SAVED_ARM_FREQ_MHZ="null"
  SYS_CONFIG_ACTIVE_ARM_FREQ_MHZ="null"
  SYS_CONFIG_SAVED_CORE_FREQ_MHZ="null"
  SYS_CONFIG_ACTIVE_CORE_FREQ_MHZ="null"
  SYS_CONFIG_SAVED_GPU_FREQ_MHZ="null"
  SYS_CONFIG_ACTIVE_GPU_FREQ_MHZ="null"
  SYS_CONFIG_SAVED_OVER_VOLTAGE=""
  SYS_CONFIG_ACTIVE_OVER_VOLTAGE=""
  SYS_CONFIG_SAVED_OVER_VOLTAGE_DELTA=""
  SYS_CONFIG_ACTIVE_OVER_VOLTAGE_DELTA=""
  SYS_CONFIG_SAVED_USB_MAX_CURRENT_ENABLE="null"
  SYS_CONFIG_ACTIVE_USB_MAX_CURRENT_ENABLE="null"
  SYS_CONFIG_SAVED_ARM_64BIT="null"
  SYS_CONFIG_ACTIVE_ARM_64BIT="null"
  SYS_CONFIG_STATUS="Niedostępna"
  SYS_CONFIG_PENDING_RESTART="false"
  SYS_KERNEL_CMDLINE="$(host_read_text /proc/cmdline 2>/dev/null | head -n1 || true)"
  SYS_KERNEL_VERSION="$(host_uname -r 2>/dev/null || true)"
  SYS_ARCHITECTURE="$(host_uname -m 2>/dev/null || true)"
  SYS_RPI_MODEL="$(read_rpi_model 2>/dev/null || true)"
  [ -n "$SYS_KERNEL_CMDLINE" ] || SYS_KERNEL_CMDLINE="N/D"
  [ -n "$SYS_KERNEL_VERSION" ] || SYS_KERNEL_VERSION="N/D"
  [ -n "$SYS_ARCHITECTURE" ] || SYS_ARCHITECTURE="N/D"
  [ -n "$SYS_RPI_MODEL" ] || SYS_RPI_MODEL="N/D"
}

read_vcgencmd_config_map() {
  local kind="$1" bin out
  for bin in /usr/bin/vcgencmd /opt/vc/bin/vcgencmd /bin/vcgencmd; do
    [ -x "$bin" ] || continue
    out="$("$bin" get_config "$kind" 2>/dev/null || true)"
    [ -n "$out" ] || continue
    printf '%s\n' "$out" | jq -Rn '
      reduce (inputs | select(contains("=")) | split("=")) as $x
      ({}; .[$x[0]] = ($x[1:] | join("=")))'
    return 0
  done
  echo '{}'
}

read_vcgencmd_bootloader_map() {
  local bin out
  for bin in /usr/bin/vcgencmd /opt/vc/bin/vcgencmd /bin/vcgencmd; do
    [ -x "$bin" ] || continue
    out="$("$bin" bootloader_config 2>/dev/null || true)"
    case "$out" in ''|error=*) continue ;; esac
    printf '%s\n' "$out" | jq -Rn '
      reduce (inputs | select(contains("=")) | split("=")) as $x
      ({}; .[$x[0]] = ($x[1:] | join("=")))'
    return 0
  done
  echo '{}'
}

boot_config_rel_in_root() {
  local root="$1" rel
  for rel in \
    config.txt \
    usercfg.txt \
    firmware/config.txt \
    boot/config.txt \
    slot-A/config.txt \
    slot-B/config.txt
  do
    [ -r "$root/$rel" ] || continue
    printf '%s\n' "$rel"
    return 0
  done
  return 1
}

boot_device_candidates() {
  local dev resolved line name type fstype label partlabel

  for label in hassos-boot HAOS-BOOT haos-boot boot; do
    if command -v blkid >/dev/null 2>&1; then
      dev="$(blkid -L "$label" 2>/dev/null || true)"
      [ -n "$dev" ] && printf '%s\n' "$dev"
    fi
    if command -v findfs >/dev/null 2>&1; then
      dev="$(findfs "LABEL=$label" 2>/dev/null || true)"
      [ -n "$dev" ] && printf '%s\n' "$dev"
    fi
  done

  for dev in \
    /dev/disk/by-label/hassos-boot \
    /dev/disk/by-label/HAOS-BOOT \
    /dev/disk/by-label/haos-boot \
    /dev/disk/by-partlabel/hassos-boot \
    /dev/disk/by-partlabel/HAOS-BOOT \
    /dev/disk/by-partlabel/haos-boot \
    /dev/nvme0n1p1 /dev/mmcblk0p1 /dev/sda1 /dev/sdb1
  do
    [ -e "$dev" ] || continue
    resolved="$(readlink -f "$dev" 2>/dev/null || printf '%s' "$dev")"
    [ -n "$resolved" ] && printf '%s\n' "$resolved"
  done

  if command -v lsblk >/dev/null 2>&1; then
    while read -r name type fstype label partlabel; do
      [ "$type" = "part" ] || continue
      case "$fstype" in vfat|fat|fat32|ext4|ext2|ext3|'') ;; *) continue ;; esac
      case "${label,,}:${partlabel,,}" in
        *hassos-boot*|*haos-boot*|*boot*) printf '%s\n' "$name" ;;
      esac
    done < <(lsblk -rpn -o NAME,TYPE,FSTYPE,LABEL,PARTLABEL 2>/dev/null || true)

    while read -r name type fstype label partlabel; do
      [ "$type" = "part" ] || continue
      case "$fstype" in vfat|fat|fat32) printf '%s\n' "$name" ;; esac
    done < <(lsblk -rpn -o NAME,TYPE,FSTYPE,LABEL,PARTLABEL 2>/dev/null || true)
  fi
}

discover_boot_config_readonly() {
  DISCOVER_BOOT_ROOT=""
  DISCOVER_BOOT_REL=""
  DISCOVER_BOOT_DEVICE=""
  DISCOVER_BOOT_SOURCE=""
  DISCOVER_BOOT_OWN_MOUNT="false"
  DISCOVER_BOOT_NS_ROOT=""

  local root rel dev mounted mp safe_name host_info host_root host_rel host_pid1 snapshot ns_info ns_root ns_rel

  # v1.7.7: host_pid=true gives visibility of the HAOS PID namespace.  The
  # host already mounts hassos-boot at /mnt/boot, so /proc/1/root/mnt/boot is
  # the least invasive and most reliable read path.
  host_info="$(host_pid_boot_root 2>/dev/null || true)"
  if [ -n "$host_info" ]; then
    IFS='|' read -r host_root host_rel host_pid1 <<< "$host_info"
    DISCOVER_BOOT_ROOT="$host_root"
    DISCOVER_BOOT_REL="$host_rel"
    DISCOVER_BOOT_DEVICE="/mnt/boot"
    DISCOVER_BOOT_SOURCE="host_pid_root:${host_pid1:-pid1}"
    return 0
  fi

  # Fallback: host PID namespace przez nsenter. Najpierw wykrywamy realny
  # mount i relatywną ścieżkę config.txt, potem pobieramy tylko potrzebne pliki.
  ns_info="$(host_nsenter_boot_info 2>/dev/null || true)"
  if [ -n "$ns_info" ]; then
    IFS='|' read -r ns_root ns_rel <<< "$ns_info"
    snapshot="/tmp/sbc5_host_boot_snapshot"
    rm -rf "$snapshot" 2>/dev/null || true
    mkdir -p "$snapshot" 2>/dev/null || true
    if nsenter_copy_boot_rel "$ns_root" "$ns_rel" "$snapshot/$ns_rel"; then
      # Najczęstsze pliki include kopiujemy od razu, pozostałe dociągnie parser.
      for rel in config.txt usercfg.txt syscfg.txt firmware/config.txt boot/config.txt; do
        [ "$rel" = "$ns_rel" ] && continue
        nsenter_copy_boot_rel "$ns_root" "$rel" "$snapshot/$rel" >/dev/null 2>&1 || true
      done
      DISCOVER_BOOT_ROOT="$snapshot"
      DISCOVER_BOOT_REL="$ns_rel"
      DISCOVER_BOOT_DEVICE="$ns_root"
      DISCOVER_BOOT_SOURCE="host_pid_nsenter_snapshot"
      DISCOVER_BOOT_NS_ROOT="$ns_root"
      return 0
    fi
  fi

  # Następnie sprawdzamy już dostępne punkty montowania w kontenerze.
  for root in \
    /boot/firmware \
    /boot \
    /flash \
    /mnt/boot \
    /run/host/boot \
    /host/boot
  do
    [ -d "$root" ] || continue
    rel="$(boot_config_rel_in_root "$root" 2>/dev/null || true)"
    [ -n "$rel" ] || continue
    DISCOVER_BOOT_ROOT="$root"
    DISCOVER_BOOT_REL="$rel"
    DISCOVER_BOOT_DEVICE="$root"
    DISCOVER_BOOT_SOURCE="mounted_path"
    return 0
  done

  # Potem identyfikujemy partycję boot po LABEL/PARTLABEL, znanych nazwach
  # urządzeń i na końcu po partycjach FAT. Każda próba montowania jest RO.
  while IFS= read -r dev; do
    [ -n "$dev" ] || continue
    dev="$(readlink -f "$dev" 2>/dev/null || printf '%s' "$dev")"
    [ -b "$dev" ] || continue

    mounted="$(findmnt -rn -S "$dev" -o TARGET 2>/dev/null | head -n1 || true)"
    if [ -n "$mounted" ] && [ -d "$mounted" ]; then
      rel="$(boot_config_rel_in_root "$mounted" 2>/dev/null || true)"
      if [ -n "$rel" ]; then
        DISCOVER_BOOT_ROOT="$mounted"
        DISCOVER_BOOT_REL="$rel"
        DISCOVER_BOOT_DEVICE="$dev"
        DISCOVER_BOOT_SOURCE="existing_mount"
        return 0
      fi
    fi

    safe_name="$(basename "$dev" | tr -c 'A-Za-z0-9_.-' '_')"
    mp="/tmp/rpi5cfg_${safe_name}"
    mkdir -p "$mp" 2>/dev/null || continue
    umount "$mp" >/dev/null 2>&1 || true
    if mount -o ro,nosuid,nodev,noexec "$dev" "$mp" >/dev/null 2>&1; then
      rel="$(boot_config_rel_in_root "$mp" 2>/dev/null || true)"
      if [ -n "$rel" ]; then
        DISCOVER_BOOT_ROOT="$mp"
        DISCOVER_BOOT_REL="$rel"
        DISCOVER_BOOT_DEVICE="$dev"
        DISCOVER_BOOT_SOURCE="block_scan_ro"
        DISCOVER_BOOT_OWN_MOUNT="true"
        return 0
      fi
      umount "$mp" >/dev/null 2>&1 || true
    fi
  done < <(boot_device_candidates | awk 'NF && !seen[$0]++' | head -n 24)

  return 1
}

cleanup_discovered_boot_mount() {
  if [ "${DISCOVER_BOOT_OWN_MOUNT:-false}" = "true" ] && [ -n "${DISCOVER_BOOT_ROOT:-}" ]; then
    umount "$DISCOVER_BOOT_ROOT" >/dev/null 2>&1 || true
  fi
  DISCOVER_BOOT_OWN_MOUNT="false"
  DISCOVER_BOOT_NS_ROOT=""
}

load_boot_config_cache() {
  [ -r "$BOOT_CONFIG_CACHE_FILE" ] || return 1
  jq -e . "$BOOT_CONFIG_CACHE_FILE" >/dev/null 2>&1 || return 1

  # v1.9.2: jeden proces jq zamiast kilkudziesięciu osobnych odczytów.
  # @sh bezpiecznie cytuje wartości przed eval, również JSON-y i tekst config.txt.
  local assignments
  assignments="$(jq -r '
    def a($n; $v): $n + "=" + (($v | tostring) | @sh);
    def j($n; $v): $n + "=" + (($v | tojson) | @sh);
    [
      a("SYS_BOOT_CONFIG_AVAILABLE"; (.boot_config_available // false)),
      a("SYS_BOOT_CONFIG_DEVICE"; (.boot_config_device // "")),
      a("SYS_BOOT_CONFIG_PATH"; (.boot_config_path // "")),
      a("SYS_BOOT_CONFIG_SOURCE"; (.boot_config_source // "")),
      a("SYS_BOOT_CONFIG_SHA256"; (.boot_config_sha256 // "")),
      a("SYS_BOOT_CONFIG_ENTRY_COUNT"; (.boot_config_entry_count // 0)),
      a("SYS_BOOT_CONFIG_TRUNCATED"; (.boot_config_truncated // false)),
      j("SYS_BOOT_CONFIG_ENTRIES_JSON"; (.boot_config_entries // [])),
      j("SYS_BOOT_CONFIG_INCLUDES_JSON"; (.boot_config_includes // [])),
      j("SYS_BOOT_CONFIG_OVERLAYS_JSON"; (.boot_config_overlays // [])),
      j("SYS_BOOT_CONFIG_DTPARAMS_JSON"; (.boot_config_dtparams // [])),
      j("SYS_ACTIVE_CONFIG_INT_JSON"; (.active_config_int // {})),
      j("SYS_ACTIVE_CONFIG_STR_JSON"; (.active_config_str // {})),
      j("SYS_BOOTLOADER_CONFIG_JSON"; (.bootloader_config // {})),
      a("SYS_CONFIG_SAVED_ARM_FREQ_MHZ"; (.saved_arm_freq_mhz // "null")),
      a("SYS_CONFIG_ACTIVE_ARM_FREQ_MHZ"; (.active_arm_freq_mhz // "null")),
      a("SYS_CONFIG_SAVED_CORE_FREQ_MHZ"; (.saved_core_freq_mhz // "null")),
      a("SYS_CONFIG_ACTIVE_CORE_FREQ_MHZ"; (.active_core_freq_mhz // "null")),
      a("SYS_CONFIG_SAVED_GPU_FREQ_MHZ"; (.saved_gpu_freq_mhz // "null")),
      a("SYS_CONFIG_ACTIVE_GPU_FREQ_MHZ"; (.active_gpu_freq_mhz // "null")),
      a("SYS_CONFIG_SAVED_OVER_VOLTAGE"; (.saved_over_voltage // "")),
      a("SYS_CONFIG_ACTIVE_OVER_VOLTAGE"; (.active_over_voltage // "")),
      a("SYS_CONFIG_SAVED_OVER_VOLTAGE_DELTA"; (.saved_over_voltage_delta // "")),
      a("SYS_CONFIG_ACTIVE_OVER_VOLTAGE_DELTA"; (.active_over_voltage_delta // "")),
      a("SYS_CONFIG_SAVED_USB_MAX_CURRENT_ENABLE"; (.saved_usb_max_current_enable // "null")),
      a("SYS_CONFIG_ACTIVE_USB_MAX_CURRENT_ENABLE"; (.active_usb_max_current_enable // "null")),
      a("SYS_CONFIG_SAVED_ARM_64BIT"; (.saved_arm_64bit // "null")),
      a("SYS_CONFIG_ACTIVE_ARM_64BIT"; (.active_arm_64bit // "null")),
      a("SYS_CONFIG_STATUS"; (.config_status // "Niedostępna")),
      a("SYS_CONFIG_PENDING_RESTART"; (.config_pending_restart // false)),
      a("SYS_KERNEL_CMDLINE"; (.kernel_cmdline // "")),
      a("SYS_KERNEL_VERSION"; (.kernel_version // "")),
      a("SYS_ARCHITECTURE"; (.architecture // "")),
      a("SYS_RPI_MODEL"; (.rpi_model // ""))
    ] | .[]
  ' "$BOOT_CONFIG_CACHE_FILE" 2>/dev/null)" || return 1
  [ -n "$assignments" ] || return 1
  eval "$assignments"
}


collect_boot_configuration() {
  reset_boot_config_globals

  local now mtime age
  now="$(date +%s)"
  if [ -r "$BOOT_CONFIG_CACHE_FILE" ]; then
    mtime="$(stat -c %Y "$BOOT_CONFIG_CACHE_FILE" 2>/dev/null || echo 0)"
    case "$mtime" in ''|*[!0-9]*) mtime=0 ;; esac
    age=$((now - mtime))
    if [ "$age" -ge 0 ] 2>/dev/null && [ "$age" -lt "$BOOT_CONFIG_CACHE_SECONDS" ] 2>/dev/null; then
      load_boot_config_cache && return 0
    fi
  fi

  local mp="" boot_cfg="" main_rel="" entries_tsv="" includes_tsv="" full_entries_json='[]' display_entries_json='[]'
  local int_json='{}' str_json='{}' bootloader_json='{}'
  local saved_arm="" saved_core="" saved_gpu="" saved_ov="" saved_ovd="" saved_usb="" saved_arm64=""
  local active_arm="" active_core="" active_gpu="" active_ov="" active_ovd="" active_usb="" active_arm64=""
  local status="Niedostępna" has_tuning="false" pending="false"
  local arm_saved_json="null" arm_active_json="null" core_saved_json="null" core_active_json="null" gpu_saved_json="null" gpu_active_json="null"

  if discover_boot_config_readonly; then
    mp="$DISCOVER_BOOT_ROOT"
    main_rel="$DISCOVER_BOOT_REL"
    boot_cfg="$mp/$main_rel"
    SYS_BOOT_CONFIG_DEVICE="$DISCOVER_BOOT_DEVICE"
    SYS_BOOT_CONFIG_PATH="$main_rel"
    SYS_BOOT_CONFIG_SOURCE="$DISCOVER_BOOT_SOURCE"
  fi

  int_json="$(read_vcgencmd_config_map int 2>/dev/null || echo '{}')"
  str_json="$(read_vcgencmd_config_map str 2>/dev/null || echo '{}')"
  bootloader_json="$(read_vcgencmd_bootloader_map 2>/dev/null || echo '{}')"
  SYS_ACTIVE_CONFIG_INT_JSON="$int_json"
  SYS_ACTIVE_CONFIG_STR_JSON="$str_json"
  SYS_BOOTLOADER_CONFIG_JSON="$bootloader_json"

  if [ -n "$boot_cfg" ] && [ -r "$boot_cfg" ]; then
    SYS_BOOT_CONFIG_AVAILABLE="true"
    SYS_BOOT_CONFIG_SHA256="$(sha256sum "$boot_cfg" 2>/dev/null | awk '{print $1}')"
    entries_tsv="$(mktemp /tmp/rpi5cfg_entries.XXXXXX)"
    includes_tsv="$(mktemp /tmp/rpi5cfg_includes.XXXXXX)"
    : > "$entries_tsv"; : > "$includes_tsv"

    declare -A _rpi5_cfg_seen=()
    _rpi5_parse_cfg_file() {
      local rel="$1" inherited_section="${2:-all}" depth="${3:-0}" file raw line section lineno=0 inc key value kind basedir candidate
      [ "$depth" -le 8 ] || return 0
      case "$rel" in /*|*'..'*) return 0 ;; esac
      [ -z "${_rpi5_cfg_seen[$rel]:-}" ] || return 0
      _rpi5_cfg_seen[$rel]=1
      file="$mp/$rel"
      if [ ! -r "$file" ] && [ -n "${DISCOVER_BOOT_NS_ROOT:-}" ]; then
        nsenter_copy_boot_rel "$DISCOVER_BOOT_NS_ROOT" "$rel" "$file" >/dev/null 2>&1 || true
      fi
      [ -r "$file" ] || return 0
      section="$inherited_section"
      while IFS= read -r raw || [ -n "$raw" ]; do
        lineno=$((lineno + 1))
        raw="${raw//$'\r'/}"
        line="${raw%%#*}"
        line="${line#"${line%%[![:space:]]*}"}"
        line="${line%"${line##*[![:space:]]}"}"
        [ -n "$line" ] || continue
        if [[ "$line" =~ ^\[([^]]+)\]$ ]]; then
          section="${BASH_REMATCH[1]}"
          continue
        fi
        if [[ "$line" =~ ^include[[:space:]]+(.+)$ ]]; then
          inc="${BASH_REMATCH[1]}"
          inc="${inc#"${inc%%[![:space:]]*}"}"; inc="${inc%"${inc##*[![:space:]]}"}"
          inc="${inc//$'\t'/ }"
          case "$inc" in /*|*'..'*) continue ;; esac
          basedir="${rel%/*}"
          [ "$basedir" = "$rel" ] && basedir=""
          candidate="$inc"
          if [ -n "$basedir" ] && [ ! -r "$mp/$candidate" ]; then
            if [ ! -r "$mp/$basedir/$inc" ] && [ -n "${DISCOVER_BOOT_NS_ROOT:-}" ]; then
              nsenter_copy_boot_rel "$DISCOVER_BOOT_NS_ROOT" "$basedir/$inc" "$mp/$basedir/$inc" >/dev/null 2>&1 || true
            fi
            [ -r "$mp/$basedir/$inc" ] && candidate="$basedir/$inc"
          fi
          printf '%s\n' "$candidate" >> "$includes_tsv"
          printf '%s\t%s\t%s\tinclude\tinclude\t%s\n' "$rel" "$lineno" "$section" "$candidate" >> "$entries_tsv"
          _rpi5_parse_cfg_file "$candidate" "$section" $((depth + 1))
          continue
        fi
        [[ "$line" == *=* ]] || continue
        key="${line%%=*}"; value="${line#*=}"
        key="${key#"${key%%[![:space:]]*}"}"; key="${key%"${key##*[![:space:]]}"}"
        value="${value#"${value%%[![:space:]]*}"}"; value="${value%"${value##*[![:space:]]}"}"
        key="${key//$'\t'/ }"; value="${value//$'\t'/ }"
        case "$key" in dtoverlay) kind="dtoverlay" ;; dtparam) kind="dtparam" ;; *) kind="setting" ;; esac
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$rel" "$lineno" "$section" "$kind" "$key" "$value" >> "$entries_tsv"
      done < "$file"
    }
    _rpi5_parse_cfg_file "$main_rel" "all" 0
    unset -f _rpi5_parse_cfg_file

    SYS_BOOT_CONFIG_ENTRY_COUNT="$(wc -l < "$entries_tsv" | tr -d ' ')"
    full_entries_json="$(jq -Rn '[inputs | split("\t") | select(length >= 6) | {file:.[0],line:(.[1]|tonumber),section:.[2],kind:.[3],key:.[4],value:.[5]}]' < "$entries_tsv")"
    if [ "$SYS_BOOT_CONFIG_ENTRY_COUNT" -gt 180 ] 2>/dev/null; then
      SYS_BOOT_CONFIG_TRUNCATED="true"
      display_entries_json="$(jq '.[0:180]' <<< "$full_entries_json")"
    else
      display_entries_json="$full_entries_json"
    fi
    SYS_BOOT_CONFIG_ENTRIES_JSON="$(jq -c . <<< "$display_entries_json")"
    SYS_BOOT_CONFIG_INCLUDES_JSON="$(jq -Rn '[inputs | select(length>0)] | unique' < "$includes_tsv" | jq -c .)"
    SYS_BOOT_CONFIG_OVERLAYS_JSON="$(jq -c '[.[] | select(.kind=="dtoverlay")]' <<< "$full_entries_json")"
    SYS_BOOT_CONFIG_DTPARAMS_JSON="$(jq -c '[.[] | select(.kind=="dtparam")]' <<< "$full_entries_json")"

    saved_arm="$(jq -r '[.[]|select(.key=="arm_freq" and (.section=="all" or .section=="pi5" or .section=="cm5"))]|if length then .[-1].value else "" end' <<< "$full_entries_json")"
    saved_core="$(jq -r '[.[]|select(.key=="core_freq" and (.section=="all" or .section=="pi5" or .section=="cm5"))]|if length then .[-1].value else "" end' <<< "$full_entries_json")"
    saved_gpu="$(jq -r '[.[]|select(.key=="gpu_freq" and (.section=="all" or .section=="pi5" or .section=="cm5"))]|if length then .[-1].value else "" end' <<< "$full_entries_json")"
    saved_ov="$(jq -r '[.[]|select(.key=="over_voltage" and (.section=="all" or .section=="pi5" or .section=="cm5"))]|if length then .[-1].value else "" end' <<< "$full_entries_json")"
    saved_ovd="$(jq -r '[.[]|select(.key=="over_voltage_delta" and (.section=="all" or .section=="pi5" or .section=="cm5"))]|if length then .[-1].value else "" end' <<< "$full_entries_json")"
    saved_usb="$(jq -r '[.[]|select(.key=="usb_max_current_enable" and (.section=="all" or .section=="pi5" or .section=="cm5"))]|if length then .[-1].value else "" end' <<< "$full_entries_json")"
    saved_arm64="$(jq -r '[.[]|select(.key=="arm_64bit" and (.section=="all" or .section=="pi5" or .section=="cm5"))]|if length then .[-1].value else "" end' <<< "$full_entries_json")"

    [[ "$saved_arm" =~ ^[0-9]+([.][0-9]+)?$ ]] && arm_saved_json="$saved_arm"
    [[ "$saved_core" =~ ^[0-9]+([.][0-9]+)?$ ]] && core_saved_json="$saved_core"
    [[ "$saved_gpu" =~ ^[0-9]+([.][0-9]+)?$ ]] && gpu_saved_json="$saved_gpu"

    rm -f "$entries_tsv" "$includes_tsv"
    cleanup_discovered_boot_mount
    mp=""
  else
    cleanup_discovered_boot_mount
  fi

  active_arm="$(jq -r '.arm_freq // empty' <<< "$int_json")"
  active_core="$(jq -r '.core_freq // empty' <<< "$int_json")"
  active_gpu="$(jq -r '.gpu_freq // empty' <<< "$int_json")"
  active_ov="$(jq -r '.over_voltage // empty' <<< "$int_json")"
  active_ovd="$(jq -r '.over_voltage_delta // empty' <<< "$int_json")"
  active_usb="$(jq -r '.usb_max_current_enable // empty' <<< "$int_json")"
  active_arm64="$(jq -r '.arm_64bit // empty' <<< "$int_json")"
  [ -n "$active_arm" ] || { [ "${SYS_CPU_MAX_MHZ:-null}" != "null" ] && active_arm="${SYS_CPU_MAX_MHZ%.*}"; }
  if [ -z "$active_usb" ] && [ "${SYS_USB_CONFIG_OVERRIDE:-null}" != "null" ]; then
    active_usb="$SYS_USB_CONFIG_OVERRIDE"
  fi
  if [ -z "$active_arm64" ]; then
    case "$SYS_ARCHITECTURE" in aarch64|arm64) active_arm64=1 ;; armv7*|armhf) active_arm64=0 ;; esac
  fi
  [[ "$active_arm" =~ ^[0-9]+([.][0-9]+)?$ ]] && arm_active_json="$active_arm"
  [[ "$active_core" =~ ^[0-9]+([.][0-9]+)?$ ]] && core_active_json="$active_core"
  [[ "$active_gpu" =~ ^[0-9]+([.][0-9]+)?$ ]] && gpu_active_json="$active_gpu"

  SYS_CONFIG_SAVED_ARM_FREQ_MHZ="$arm_saved_json"
  SYS_CONFIG_ACTIVE_ARM_FREQ_MHZ="$arm_active_json"
  SYS_CONFIG_SAVED_CORE_FREQ_MHZ="$core_saved_json"
  SYS_CONFIG_ACTIVE_CORE_FREQ_MHZ="$core_active_json"
  SYS_CONFIG_SAVED_GPU_FREQ_MHZ="$gpu_saved_json"
  SYS_CONFIG_ACTIVE_GPU_FREQ_MHZ="$gpu_active_json"
  SYS_CONFIG_SAVED_OVER_VOLTAGE="${saved_ov:-}"
  SYS_CONFIG_ACTIVE_OVER_VOLTAGE="${active_ov:-}"
  SYS_CONFIG_SAVED_OVER_VOLTAGE_DELTA="${saved_ovd:-}"
  SYS_CONFIG_ACTIVE_OVER_VOLTAGE_DELTA="${active_ovd:-}"
  case "${saved_usb:-}" in 0) SYS_CONFIG_SAVED_USB_MAX_CURRENT_ENABLE="false" ;; 1) SYS_CONFIG_SAVED_USB_MAX_CURRENT_ENABLE="true" ;; esac
  case "${active_usb:-}" in 0) SYS_CONFIG_ACTIVE_USB_MAX_CURRENT_ENABLE="false" ;; 1) SYS_CONFIG_ACTIVE_USB_MAX_CURRENT_ENABLE="true" ;; esac
  case "${saved_arm64:-}" in 0) SYS_CONFIG_SAVED_ARM_64BIT="false" ;; 1) SYS_CONFIG_SAVED_ARM_64BIT="true" ;; esac
  case "${active_arm64:-}" in 0) SYS_CONFIG_ACTIVE_ARM_64BIT="false" ;; 1) SYS_CONFIG_ACTIVE_ARM_64BIT="true" ;; esac

  [ "$arm_saved_json" != "null" ] && has_tuning="true"
  [ "$core_saved_json" != "null" ] && has_tuning="true"
  [ "$gpu_saved_json" != "null" ] && has_tuning="true"
  [ -n "${saved_ov:-}" ] && has_tuning="true"
  [ -n "${saved_ovd:-}" ] && has_tuning="true"

  if [ "$arm_saved_json" != "null" ] && [ "$arm_active_json" != "null" ] && [ "$arm_saved_json" != "$arm_active_json" ]; then pending="true"; fi
  if [ "$core_saved_json" != "null" ] && [ "$core_active_json" != "null" ] && [ "$core_saved_json" != "$core_active_json" ]; then pending="true"; fi
  if [ "$gpu_saved_json" != "null" ] && [ "$gpu_active_json" != "null" ] && [ "$gpu_saved_json" != "$gpu_active_json" ]; then pending="true"; fi
  if [ -n "${saved_ov:-}" ] && [ -n "${active_ov:-}" ] && [ "$saved_ov" != "$active_ov" ]; then pending="true"; fi
  if [ -n "${saved_ovd:-}" ] && [ -n "${active_ovd:-}" ] && [ "$saved_ovd" != "$active_ovd" ]; then pending="true"; fi
  if [ "$SYS_CONFIG_SAVED_USB_MAX_CURRENT_ENABLE" != "null" ] && [ "$SYS_CONFIG_ACTIVE_USB_MAX_CURRENT_ENABLE" != "null" ] && [ "$SYS_CONFIG_SAVED_USB_MAX_CURRENT_ENABLE" != "$SYS_CONFIG_ACTIVE_USB_MAX_CURRENT_ENABLE" ]; then pending="true"; fi
  if [ "$SYS_CONFIG_SAVED_ARM_64BIT" != "null" ] && [ "$SYS_CONFIG_ACTIVE_ARM_64BIT" != "null" ] && [ "$SYS_CONFIG_SAVED_ARM_64BIT" != "$SYS_CONFIG_ACTIVE_ARM_64BIT" ]; then pending="true"; fi

  if [ "$SYS_BOOT_CONFIG_AVAILABLE" != "true" ]; then
    status="Brak dostępu do konfiguracji boot"
  elif [ "$pending" = "true" ]; then
    status="Zapis ≠ konfiguracja aktywna"
  elif [ "$has_tuning" = "true" ]; then
    status="Zmodyfikowana · aktywna"
  else
    status="Domyślna / bez ręcznego OC"
  fi
  SYS_CONFIG_STATUS="$status"
  SYS_CONFIG_PENDING_RESTART="$pending"

  jq -n \
    --argjson boot_config_available "$SYS_BOOT_CONFIG_AVAILABLE" --arg boot_config_device "$SYS_BOOT_CONFIG_DEVICE" --arg boot_config_path "$SYS_BOOT_CONFIG_PATH" --arg boot_config_source "$SYS_BOOT_CONFIG_SOURCE" --arg boot_config_sha256 "$SYS_BOOT_CONFIG_SHA256" \
    --argjson boot_config_entry_count "$SYS_BOOT_CONFIG_ENTRY_COUNT" --argjson boot_config_truncated "$SYS_BOOT_CONFIG_TRUNCATED" --argjson boot_config_entries "$SYS_BOOT_CONFIG_ENTRIES_JSON" \
    --argjson boot_config_includes "$SYS_BOOT_CONFIG_INCLUDES_JSON" --argjson boot_config_overlays "$SYS_BOOT_CONFIG_OVERLAYS_JSON" --argjson boot_config_dtparams "$SYS_BOOT_CONFIG_DTPARAMS_JSON" \
    --argjson active_config_int "$SYS_ACTIVE_CONFIG_INT_JSON" --argjson active_config_str "$SYS_ACTIVE_CONFIG_STR_JSON" --argjson bootloader_config "$SYS_BOOTLOADER_CONFIG_JSON" \
    --argjson saved_arm_freq_mhz "$SYS_CONFIG_SAVED_ARM_FREQ_MHZ" --argjson active_arm_freq_mhz "$SYS_CONFIG_ACTIVE_ARM_FREQ_MHZ" \
    --argjson saved_core_freq_mhz "$SYS_CONFIG_SAVED_CORE_FREQ_MHZ" --argjson active_core_freq_mhz "$SYS_CONFIG_ACTIVE_CORE_FREQ_MHZ" \
    --argjson saved_gpu_freq_mhz "$SYS_CONFIG_SAVED_GPU_FREQ_MHZ" --argjson active_gpu_freq_mhz "$SYS_CONFIG_ACTIVE_GPU_FREQ_MHZ" \
    --arg saved_over_voltage "$SYS_CONFIG_SAVED_OVER_VOLTAGE" --arg active_over_voltage "$SYS_CONFIG_ACTIVE_OVER_VOLTAGE" \
    --arg saved_over_voltage_delta "$SYS_CONFIG_SAVED_OVER_VOLTAGE_DELTA" --arg active_over_voltage_delta "$SYS_CONFIG_ACTIVE_OVER_VOLTAGE_DELTA" \
    --argjson saved_usb_max_current_enable "$SYS_CONFIG_SAVED_USB_MAX_CURRENT_ENABLE" --argjson active_usb_max_current_enable "$SYS_CONFIG_ACTIVE_USB_MAX_CURRENT_ENABLE" \
    --argjson saved_arm_64bit "$SYS_CONFIG_SAVED_ARM_64BIT" --argjson active_arm_64bit "$SYS_CONFIG_ACTIVE_ARM_64BIT" \
    --arg config_status "$SYS_CONFIG_STATUS" --argjson config_pending_restart "$SYS_CONFIG_PENDING_RESTART" \
    --arg kernel_cmdline "$SYS_KERNEL_CMDLINE" --arg kernel_version "$SYS_KERNEL_VERSION" --arg architecture "$SYS_ARCHITECTURE" --arg rpi_model "$SYS_RPI_MODEL" \
    '{boot_config_available:$boot_config_available,boot_config_device:$boot_config_device,boot_config_path:$boot_config_path,boot_config_source:$boot_config_source,boot_config_sha256:$boot_config_sha256,boot_config_entry_count:$boot_config_entry_count,boot_config_truncated:$boot_config_truncated,boot_config_entries:$boot_config_entries,boot_config_includes:$boot_config_includes,boot_config_overlays:$boot_config_overlays,boot_config_dtparams:$boot_config_dtparams,active_config_int:$active_config_int,active_config_str:$active_config_str,bootloader_config:$bootloader_config,saved_arm_freq_mhz:$saved_arm_freq_mhz,active_arm_freq_mhz:$active_arm_freq_mhz,saved_core_freq_mhz:$saved_core_freq_mhz,active_core_freq_mhz:$active_core_freq_mhz,saved_gpu_freq_mhz:$saved_gpu_freq_mhz,active_gpu_freq_mhz:$active_gpu_freq_mhz,saved_over_voltage:$saved_over_voltage,active_over_voltage:$active_over_voltage,saved_over_voltage_delta:$saved_over_voltage_delta,active_over_voltage_delta:$active_over_voltage_delta,saved_usb_max_current_enable:$saved_usb_max_current_enable,active_usb_max_current_enable:$active_usb_max_current_enable,saved_arm_64bit:$saved_arm_64bit,active_arm_64bit:$active_arm_64bit,config_status:$config_status,config_pending_restart:$config_pending_restart,kernel_cmdline:$kernel_cmdline,kernel_version:$kernel_version,architecture:$architecture,rpi_model:$rpi_model}' \
    > "${BOOT_CONFIG_CACHE_FILE}.tmp" 2>/dev/null && mv -f "${BOOT_CONFIG_CACHE_FILE}.tmp" "$BOOT_CONFIG_CACHE_FILE"
}

collect_pmic_telemetry() {
  SYS_PMIC_AVAILABLE="false"
  SYS_INPUT_VOLTAGE_V="null"
  SYS_PMIC_POWER_W="null"
  SYS_PMIC_EQ_CURRENT_A="null"
  SYS_PMIC_TEMP_C="null"
  SYS_CORE_CURRENT_A="null"
  SYS_CORE_VOLTAGE_V="null"
  SYS_CORE_POWER_W="null"
  SYS_PMIC_RAILS_JSON='[]'
  SYS_PMIC_SOURCE="unavailable"

  local bin="" out="" line key rail value v a power total="0" item tempout
  local -a items=()
  declare -A currents=()
  declare -A volts=()

  for bin in /usr/bin/vcgencmd /opt/vc/bin/vcgencmd /bin/vcgencmd; do
    [ -x "$bin" ] || continue
    out="$("$bin" pmic_read_adc 2>/dev/null || true)"
    case "$out" in ''|error=*) continue ;; esac
    printf '%s\n' "$out" | grep -Eq '(current|volt)\(' || { out=""; continue; }
    break
  done
  [ -n "$out" ] || return 0

  while IFS= read -r line; do
    line="${line#"${line%%[![:space:]]*}"}"
    key="${line%% *}"
    case "$line" in
      *_A\ current\(*\)=*A)
        rail="${key%_A}"
        value="${line#*=}"; value="${value%A}"
        [[ "$value" =~ ^[0-9]+([.][0-9]+)?$ ]] && currents["$rail"]="$value"
        ;;
      *_V\ volt\(*\)=*V)
        rail="${key%_V}"
        value="${line#*=}"; value="${value%V}"
        [[ "$value" =~ ^[0-9]+([.][0-9]+)?$ ]] && volts["$rail"]="$value"
        ;;
    esac
  done <<< "$out"

  if [ -n "${volts[EXT5V]:-}" ]; then
    SYS_INPUT_VOLTAGE_V="$(awk -v v="${volts[EXT5V]}" 'BEGIN{printf "%.4f", v}')"
  fi

  for rail in "${!currents[@]}"; do
    a="${currents[$rail]}"
    v="${volts[$rail]:-}"
    [ -n "$v" ] || continue
    power="$(awk -v a="$a" -v v="$v" 'BEGIN{printf "%.5f", a*v}')"
    total="$(awk -v a="$total" -v b="$power" 'BEGIN{printf "%.5f", a+b}')"
    item="$(jq -cn --arg rail "$rail" --argjson current_a "$a" --argjson voltage_v "$v" --argjson power_w "$power" \
      '{rail:$rail,current_a:$current_a,voltage_v:$voltage_v,power_w:$power_w}')"
    items+=("$item")
  done

  if [ "${#items[@]}" -gt 0 ]; then
    SYS_PMIC_RAILS_JSON="$(printf '%s\n' "${items[@]}" | jq -s 'sort_by(.rail)')"
    SYS_PMIC_POWER_W="$(awk -v v="$total" 'BEGIN{printf "%.3f", v}')"
    SYS_PMIC_AVAILABLE="true"
    SYS_PMIC_SOURCE="vcgencmd:pmic_read_adc"
  fi

  if [ "$SYS_INPUT_VOLTAGE_V" != "null" ] && awk -v v="$SYS_INPUT_VOLTAGE_V" 'BEGIN{exit !(v>0.1)}'; then
    SYS_PMIC_EQ_CURRENT_A="$(awk -v p="$SYS_PMIC_POWER_W" -v v="$SYS_INPUT_VOLTAGE_V" 'BEGIN{if (p>=0 && v>0) printf "%.3f", p/v; else print "null"}')"
  fi

  if [ -n "${currents[VDD_CORE]:-}" ]; then
    SYS_CORE_CURRENT_A="$(awk -v v="${currents[VDD_CORE]}" 'BEGIN{printf "%.4f", v}')"
  fi
  if [ -n "${volts[VDD_CORE]:-}" ]; then
    SYS_CORE_VOLTAGE_V="$(awk -v v="${volts[VDD_CORE]}" 'BEGIN{printf "%.4f", v}')"
  fi
  if [ "$SYS_CORE_CURRENT_A" != "null" ] && [ "$SYS_CORE_VOLTAGE_V" != "null" ]; then
    SYS_CORE_POWER_W="$(awk -v a="$SYS_CORE_CURRENT_A" -v v="$SYS_CORE_VOLTAGE_V" 'BEGIN{printf "%.3f", a*v}')"
  fi

  if [ -x "$bin" ]; then
    tempout="$("$bin" measure_temp pmic 2>/dev/null || true)"
    case "$tempout" in
      temp=*)
        value="${tempout#temp=}"; value="${value%%\'*}"
        [[ "$value" =~ ^[0-9]+([.][0-9]+)?$ ]] && SYS_PMIC_TEMP_C="$value"
        ;;
    esac
  fi
}

read_usb_sysfs_attr() {
  local file="$1" value=""
  [ -r "$file" ] || return 0
  IFS= read -r value < "$file" 2>/dev/null || true
  value="${value//$'\r'/}"
  printf '%s' "$value"
}

collect_usb_device_info() {
  SYS_USB_DEVICE_COUNT=0
  SYS_USB_DECLARED_MA=0
  SYS_USB_DEVICES_JSON='[]'

  local d node vendor product manufacturer product_name bmax ma bus devnum devpath speed authorized item
  local usb_root="${RPI5_USB_SYSFS_ROOT:-/sys/bus/usb/devices}"
  local -a items=()
  for d in "$usb_root"/*; do
    [ -d "$d" ] || continue

    # Read identifiers first.  If the node disappears mid-scan, simply skip it.
    vendor="$(read_usb_sysfs_attr "$d/idVendor")"
    product="$(read_usb_sysfs_attr "$d/idProduct")"
    [ -n "$vendor" ] && [ -n "$product" ] || continue

    # Linux root hubs are host controllers, not downstream USB loads.
    [ "$vendor" = "1d6b" ] && continue

    node="$(basename "$d")"
    manufacturer="$(read_usb_sysfs_attr "$d/manufacturer")"
    [ -n "$manufacturer" ] || manufacturer="Nieznany"
    product_name="$(read_usb_sysfs_attr "$d/product")"
    [ -n "$product_name" ] || product_name="USB ${vendor}:${product}"
    bmax="$(read_usb_sysfs_attr "$d/bMaxPower")"
    if [[ "$bmax" =~ ([0-9]+) ]]; then ma="${BASH_REMATCH[1]}"; else ma=0; fi
    bus="$(read_usb_sysfs_attr "$d/busnum")"
    devnum="$(read_usb_sysfs_attr "$d/devnum")"
    devpath="$(read_usb_sysfs_attr "$d/devpath")"
    speed="$(read_usb_sysfs_attr "$d/speed")"
    authorized="$(read_usb_sysfs_attr "$d/authorized")"
    [ -n "$authorized" ] || authorized="1"

    SYS_USB_DEVICE_COUNT=$((SYS_USB_DEVICE_COUNT + 1))
    SYS_USB_DECLARED_MA=$((SYS_USB_DECLARED_MA + ma))
    item="$(jq -cn \
      --arg node "$node" --arg manufacturer "$manufacturer" --arg product "$product_name" \
      --arg vendor_id "$vendor" --arg product_id "$product" --arg bus "$bus" --arg devnum "$devnum" \
      --arg devpath "$devpath" --arg speed_mbps "$speed" --argjson declared_ma "$ma" \
      --argjson authorized "${authorized:-1}" \
      '{port_path:$node,manufacturer:$manufacturer,product:$product,vendor_id:$vendor_id,product_id:$product_id,bus:$bus,device_number:$devnum,device_path:$devpath,speed_mbps:$speed_mbps,declared_max_current_ma:$declared_ma,authorized:($authorized != 0)}')"
    items+=("$item")
  done

  if [ "${#items[@]}" -gt 0 ]; then
    SYS_USB_DEVICES_JSON="$(printf '%s\n' "${items[@]}" | jq -s 'sort_by(.port_path)')"
  fi
}

collect_power_supply_info() {
  local cur_khz min_khz max_khz pdir val pshex pdo_file pdo_hex cell pdo voltage_mv current_ma type_bits
  local usb_cfg

  SYS_CPU_FREQ_MHZ="null"
  SYS_CPU_MIN_MHZ="null"
  SYS_CPU_MAX_MHZ="null"
  SYS_CPU_GOVERNOR=""
  SYS_POWER_SUPPLY="Nieznany"
  SYS_POWER_TYPE="unknown"
  SYS_POWER_OFFICIAL="false"
  SYS_PD_DETECTED="false"
  SYS_PD_5A="false"
  SYS_POWER_VID=""
  SYS_POWER_PRODUCT_VDO=""
  SYS_POWER_MAX_CURRENT_MA="null"
  SYS_POWER_SOURCE="unavailable"
  SYS_USB_LIMIT_MA="null"
  SYS_USB_HIGH="null"
  SYS_USB_LIMIT_SOURCE="unavailable"
  SYS_USB_OVERCURRENT="null"
  SYS_OVERCURRENT_SOURCE="unavailable"
  SYS_USB_CONFIG_OVERRIDE="null"

  cur_khz="$(read_cpu_frequency_khz 2>/dev/null || true)"
  min_khz="$(read_cpu_frequency_bound_khz min 2>/dev/null || true)"
  max_khz="$(read_cpu_frequency_bound_khz max 2>/dev/null || true)"
  SYS_CPU_GOVERNOR="$(read_cpu_governor 2>/dev/null || true)"
  [ -n "$cur_khz" ] && SYS_CPU_FREQ_MHZ="$(khz_to_mhz_1dp "$cur_khz")"
  [ -n "$min_khz" ] && SYS_CPU_MIN_MHZ="$(khz_to_mhz_1dp "$min_khz")"
  [ -n "$max_khz" ] && SYS_CPU_MAX_MHZ="$(khz_to_mhz_1dp "$max_khz")"

  pdir="$(dt_power_dir 2>/dev/null || true)"
  if [ -n "$pdir" ]; then
    SYS_POWER_SOURCE="device_tree:${pdir}"

    if val="$(read_dt_u32_be "$pdir/max_current" 2>/dev/null)"; then
      if [ "$val" -gt 0 ] 2>/dev/null; then SYS_POWER_MAX_CURRENT_MA="$val"; fi
    fi

    if val="$(read_dt_u32_be "$pdir/usb_max_current_enable" 2>/dev/null)"; then
      if [ "$val" -ne 0 ] 2>/dev/null; then
        SYS_USB_LIMIT_MA="1600"; SYS_USB_HIGH="true"
      else
        SYS_USB_LIMIT_MA="600"; SYS_USB_HIGH="false"
      fi
      SYS_USB_CONFIG_OVERRIDE="$val"
      SYS_USB_LIMIT_SOURCE="device_tree:${pdir}/usb_max_current_enable"
    fi

    if val="$(read_dt_u32_be "$pdir/usb_over_current_detected" 2>/dev/null)"; then
      if [ "$val" -ne 0 ] 2>/dev/null; then SYS_USB_OVERCURRENT="true"; else SYS_USB_OVERCURRENT="false"; fi
      SYS_OVERCURRENT_SOURCE="device_tree:${pdir}/usb_over_current_detected"
    fi

    pshex="$(read_dt_hex8 "$pdir/rpi_power_supply" 2>/dev/null || true)"
    if [ "${#pshex}" -ge 16 ] && [ "${pshex:0:16}" != "0000000000000000" ]; then
      SYS_POWER_OFFICIAL="true"
      SYS_POWER_VID="0x${pshex:0:8}"
      SYS_POWER_PRODUCT_VDO="0x${pshex:8:8}"
    fi

    pdo_file="$pdir/usbpd_power_data_objects"
    if [ -r "$pdo_file" ] && [ -s "$pdo_file" ]; then
      pdo_hex="$(od -An -tx1 "$pdo_file" 2>/dev/null | tr -d ' \n')"
      while [ "${#pdo_hex}" -ge 8 ]; do
        cell="${pdo_hex:0:8}"; pdo_hex="${pdo_hex:8}"
        pdo=$((16#$cell)); type_bits=$(((pdo >> 30) & 3))
        [ "$type_bits" -eq 0 ] || continue
        SYS_PD_DETECTED="true"
        voltage_mv=$((((pdo >> 10) & 1023) * 50))
        current_ma=$(((pdo & 1023) * 10))
        if [ "$voltage_mv" -ge 4750 ] && [ "$voltage_mv" -le 5250 ] && [ "$current_ma" -ge 5000 ]; then
          SYS_PD_5A="true"
        fi
      done
    fi
  fi

  # Fallback 1: vcgencmd, jeżeli jest widoczny w środowisku aplikacji.
  if [ "$SYS_USB_HIGH" = "null" ] && usb_cfg="$(read_vcgencmd_usb_high 2>/dev/null)"; then
    SYS_USB_CONFIG_OVERRIDE="$usb_cfg"
    if [ "$usb_cfg" -eq 1 ]; then SYS_USB_HIGH="true"; SYS_USB_LIMIT_MA="1600"; else SYS_USB_HIGH="false"; SYS_USB_LIMIT_MA="600"; fi
    SYS_USB_LIMIT_SOURCE="vcgencmd:get_config"
  fi

  # Fallback 2: aktywny wpis config.txt. Używany tylko, gdy firmware nie podał właściwości DT.
  if [ "$SYS_USB_HIGH" = "null" ] && usb_cfg="$(read_boot_usb_current_override 2>/dev/null)"; then
    SYS_USB_CONFIG_OVERRIDE="$usb_cfg"
    if [ "$usb_cfg" -eq 1 ]; then SYS_USB_HIGH="true"; SYS_USB_LIMIT_MA="1600"; else SYS_USB_HIGH="false"; SYS_USB_LIMIT_MA="600"; fi
    SYS_USB_LIMIT_SOURCE="config_txt_fallback"
  fi

  # Fallback 3: limit wynika z raportowanej przez firmware wydajności zasilacza.
  if [ "$SYS_USB_HIGH" = "null" ] && [ "$SYS_POWER_MAX_CURRENT_MA" != "null" ]; then
    if [ "$SYS_POWER_MAX_CURRENT_MA" -ge 5000 ] 2>/dev/null; then
      SYS_USB_HIGH="true"; SYS_USB_LIMIT_MA="1600"
    else
      SYS_USB_HIGH="false"; SYS_USB_LIMIT_MA="600"
    fi
    SYS_USB_LIMIT_SOURCE="max_current_inference"
  fi

  if [ "$SYS_POWER_OFFICIAL" = "true" ]; then
    SYS_POWER_SUPPLY="Oficjalny Raspberry Pi 27W"
    SYS_POWER_TYPE="official_27w"
  elif [ "$SYS_PD_5A" = "true" ]; then
    SYS_POWER_SUPPLY="USB-PD 5 V / 5 A"
    SYS_POWER_TYPE="usb_pd_5a"
  elif [ "$SYS_PD_DETECTED" = "true" ]; then
    if [ "$SYS_POWER_MAX_CURRENT_MA" != "null" ]; then
      SYS_POWER_SUPPLY="USB-PD — maks. ${SYS_POWER_MAX_CURRENT_MA} mA"
    else
      SYS_POWER_SUPPLY="USB-PD (bez profilu 5 A)"
    fi
    SYS_POWER_TYPE="usb_pd_limited"
  elif [ "$SYS_POWER_MAX_CURRENT_MA" != "null" ]; then
    SYS_POWER_SUPPLY="Zasilanie — maks. ${SYS_POWER_MAX_CURRENT_MA} mA"
    if [ "$SYS_POWER_MAX_CURRENT_MA" -ge 5000 ] 2>/dev/null; then SYS_POWER_TYPE="high_current_supply"; else SYS_POWER_TYPE="reported_supply"; fi
  elif [ "$SYS_USB_HIGH" = "true" ]; then
    SYS_POWER_SUPPLY="Nierozpoznany — wysoki limit USB"
    SYS_POWER_TYPE="unknown_high_current"
  elif [ "$SYS_USB_HIGH" = "false" ]; then
    SYS_POWER_SUPPLY="Brak identyfikacji PD / niski limit USB"
    SYS_POWER_TYPE="non_pd_or_default_3a"
  fi

}

collect_system_power_info() {
  collect_power_supply_info
  collect_pmic_telemetry
  collect_usb_device_info
  collect_boot_configuration
}

# v1.9.6: częstotliwość i użycie każdego z czterech rdzeni Cortex-A76.
# Brak awk/jq/cat w pętli: sysfs i /proc/stat są czytane builtinami Bash.
collect_per_core_cpu_info() {
  local idx path v mhz cpu user nice system idle iowait irq softirq steal guest guest_nice
  local total idle_all prev_total prev_idle delta_total delta_idle busy usage_tenths
  local -a freqs=(null null null null)
  local -a usage=(null null null null)

  for idx in 0 1 2 3; do
    v=""
    for path in \
      "/sys/devices/system/cpu/cpu${idx}/cpufreq/scaling_cur_freq" \
      "/sys/devices/system/cpu/cpu${idx}/cpufreq/cpuinfo_cur_freq"; do
      [ -r "$path" ] || continue
      IFS= read -r v < "$path" 2>/dev/null || v=""
      case "$v" in ''|*[!0-9]*) v="" ;; *) break ;; esac
    done
    if [ -n "$v" ]; then
      mhz="$(khz_to_mhz_1dp "$v")"
      case "$mhz" in ''|*[!0-9.]*) freqs[$idx]=null ;; *) freqs[$idx]="$mhz" ;; esac
    fi
  done

  while IFS=' ' read -r cpu user nice system idle iowait irq softirq steal guest guest_nice _rest; do
    case "$cpu" in cpu0|cpu1|cpu2|cpu3) idx="${cpu#cpu}" ;; *) continue ;; esac
    user="${user:-0}"; nice="${nice:-0}"; system="${system:-0}"; idle="${idle:-0}"
    iowait="${iowait:-0}"; irq="${irq:-0}"; softirq="${softirq:-0}"; steal="${steal:-0}"
    case "$user$nice$system$idle$iowait$irq$softirq$steal" in *[!0-9]*) continue ;; esac
    total=$((user + nice + system + idle + iowait + irq + softirq + steal))
    idle_all=$((idle + iowait))
    prev_total="${CPU_CORE_PREV_TOTAL[$idx]:-0}"
    prev_idle="${CPU_CORE_PREV_IDLE[$idx]:-0}"
    if [ "$prev_total" -gt 0 ] && [ "$total" -gt "$prev_total" ]; then
      delta_total=$((total - prev_total))
      delta_idle=$((idle_all - prev_idle))
      [ "$delta_idle" -lt 0 ] && delta_idle=0
      busy=$((delta_total - delta_idle))
      [ "$busy" -lt 0 ] && busy=0
      [ "$busy" -gt "$delta_total" ] && busy="$delta_total"
      usage_tenths=$(((busy * 1000 + delta_total / 2) / delta_total))
      usage[$idx]="$((usage_tenths / 10)).$((usage_tenths % 10))"
    fi
    CPU_CORE_PREV_TOTAL[$idx]="$total"
    CPU_CORE_PREV_IDLE[$idx]="$idle_all"
  done < /proc/stat

  SYS_CPU_CORE_FREQS_JSON="[${freqs[0]},${freqs[1]},${freqs[2]},${freqs[3]}]"
  SYS_CPU_CORE_USAGE_JSON="[${usage[0]},${usage[1]},${usage[2]},${usage[3]}]"
}

# Lekki odczyt CPU wykonywany przy każdym cyklu publikacji telemetrii.
# Nie skanuje USB, config.txt, Device Tree ani bootloadera.
collect_cpu_runtime_info() {
  local cur_khz min_khz max_khz
  cur_khz="$(read_cpu_frequency_khz 2>/dev/null || true)"
  min_khz="$(read_cpu_frequency_bound_khz min 2>/dev/null || true)"
  max_khz="$(read_cpu_frequency_bound_khz max 2>/dev/null || true)"
  SYS_CPU_GOVERNOR="$(read_cpu_governor 2>/dev/null || true)"
  [ -n "$cur_khz" ] && SYS_CPU_FREQ_MHZ="$(khz_to_mhz_1dp "$cur_khz")"
  [ -n "$min_khz" ] && SYS_CPU_MIN_MHZ="$(khz_to_mhz_1dp "$min_khz")"
  [ -n "$max_khz" ] && SYS_CPU_MAX_MHZ="$(khz_to_mhz_1dp "$max_khz")"
  collect_per_core_cpu_info
}

# FAST/NORMAL/SLOW scheduler: pełna diagnostyka zasilania/USB/config.txt nie jest
# już wykonywana co 5 s. Usunięcie cache config.txt wymusza natychmiastowy refresh.
collect_runtime_power_info() {
  local now last_power last_pmic last_ext ext_due="false"
  local -a jobs=()
  now="${EPOCHREALTIME%%.*}"
  last_power="${TELEMETRY_LAST_POWER_REFRESH:-0}"
  last_pmic="${TELEMETRY_LAST_PMIC_REFRESH:-0}"
  last_ext="${TELEMETRY_LAST_EXTENDED_REFRESH:-0}"
  case "$last_power" in ''|*[!0-9]*) last_power=0 ;; esac
  case "$last_pmic" in ''|*[!0-9]*) last_pmic=0 ;; esac
  case "$last_ext" in ''|*[!0-9]*) last_ext=0 ;; esac

  PERF_EXTENDED_DONE_THIS_CYCLE="false"
  PERF_LAST_PARALLEL_JOBS=0
  PERF_LAST_PARALLEL_MS=0
  PERF_LAST_PARALLEL_MODE="sequential"

  if [ "$last_ext" -eq 0 ] 2>/dev/null || [ $((now - last_ext)) -ge "$TELEMETRY_EXTENDED_INTERVAL_SECONDS" ] 2>/dev/null; then
    ext_due="true"
  fi

  if [ "$last_power" -eq 0 ] 2>/dev/null || [ ! -r "$BOOT_CONFIG_CACHE_FILE" ] || [ $((now - last_power)) -ge "$TELEMETRY_POWER_INTERVAL_SECONDS" ] 2>/dev/null; then
    # Lightweight CPU values stay in the parent shell. Expensive independent
    # collectors are forked so Linux may schedule them on separate Pi 5 cores.
    collect_cpu_runtime_info
    collect_power_supply_info
    jobs=(collect_pmic_telemetry collect_usb_device_info collect_boot_configuration)
    if [ "$ext_due" = "true" ]; then jobs+=(collect_extended_system_info); fi
    run_parallel_collectors "${jobs[@]}"
    TELEMETRY_LAST_POWER_REFRESH="$now"
    TELEMETRY_LAST_PMIC_REFRESH="$now"
    if [ "$ext_due" = "true" ]; then
      TELEMETRY_LAST_EXTENDED_REFRESH="$now"
      PERF_EXTENDED_DONE_THIS_CYCLE="true"
      PERF_LAST_EXTENDED_REFRESHED="true"
    fi
    PERF_LAST_POWER_MODE="slow"
    return 0
  fi

  collect_cpu_runtime_info
  PERF_LAST_POWER_MODE="fast"
  jobs=()
  if [ $((now - last_pmic)) -ge "$TELEMETRY_PMIC_INTERVAL_SECONDS" ] 2>/dev/null; then
    jobs+=(collect_pmic_telemetry)
    TELEMETRY_LAST_PMIC_REFRESH="$now"
    PERF_LAST_POWER_MODE="normal"
  fi
  if [ "$ext_due" = "true" ] && [ "${#jobs[@]}" -gt 0 ]; then
    jobs+=(collect_extended_system_info)
    TELEMETRY_LAST_EXTENDED_REFRESH="$now"
    PERF_EXTENDED_DONE_THIS_CYCLE="true"
    PERF_LAST_EXTENDED_REFRESHED="true"
  fi
  if [ "${#jobs[@]}" -gt 0 ]; then run_parallel_collectors "${jobs[@]}"; fi
}



collect_device_identity_cached() {
  local now cpuinfo os_release fw boot model_hw
  now="${EPOCHREALTIME%%.*}"
  case "${DEVICE_IDENTITY_LAST_REFRESH:-0}" in ''|*[!0-9]*) DEVICE_IDENTITY_LAST_REFRESH=0 ;; esac
  if [ "$DEVICE_IDENTITY_LAST_REFRESH" -gt 0 ] 2>/dev/null && [ $((now - DEVICE_IDENTITY_LAST_REFRESH)) -lt "$DEVICE_IDENTITY_REFRESH_SECONDS" ] 2>/dev/null; then
    return 0
  fi
  DEVICE_IDENTITY_LAST_REFRESH="$now"

  cpuinfo="$(host_read_text /proc/cpuinfo 2>/dev/null || true)"
  SYS_SERIAL_NUMBER="$(host_read_one_line /proc/device-tree/serial-number 2>/dev/null || true)"
  [ -n "$SYS_SERIAL_NUMBER" ] || SYS_SERIAL_NUMBER="$(host_read_one_line /sys/firmware/devicetree/base/serial-number 2>/dev/null || true)"
  if [ -z "$SYS_SERIAL_NUMBER" ] && [ -n "$cpuinfo" ]; then
    SYS_SERIAL_NUMBER="$(awk -F: '/^Serial[[:space:]]*:/ {gsub(/^[ \t]+|[ \t]+$/,"",$2); print $2; exit}' <<< "$cpuinfo" 2>/dev/null || true)"
  fi
  SYS_BOARD_REVISION="$(awk -F: '/^Revision[[:space:]]*:/ {gsub(/^[ \t]+|[ \t]+$/,"",$2); print $2; exit}' <<< "$cpuinfo" 2>/dev/null || true)"

  model_hw="$(sed -n 's/.* \(Rev [0-9][0-9.]*\)$/\1/p' <<< "${SYS_RPI_MODEL:-}" | head -n1)"
  SYS_HARDWARE_REVISION="${model_hw:-$SYS_BOARD_REVISION}"

  os_release=""
  if [ -r /proc/1/root/etc/os-release ]; then
    os_release="$(tr -d '\r' < /proc/1/root/etc/os-release 2>/dev/null || true)"
  elif command -v nsenter >/dev/null 2>&1; then
    os_release="$(nsenter -t 1 -m -r -- sh -c 'cat /etc/os-release' 2>/dev/null | tr -d '\r' || true)"
  fi
  SYS_OS_NAME="$(sed -n 's/^NAME=//p' <<< "$os_release" | head -n1 | sed 's/^"//;s/"$//')"
  SYS_OS_VERSION="$(sed -n 's/^VERSION_ID=//p' <<< "$os_release" | head -n1 | sed 's/^"//;s/"$//')"
  SYS_OS_PRETTY_NAME="$(sed -n 's/^PRETTY_NAME=//p' <<< "$os_release" | head -n1 | sed 's/^"//;s/"$//')"

  SYS_NETWORK_MAC=""
  if [ -n "${SYS_NET_IFACE:-}" ] && [ -r "/sys/class/net/$SYS_NET_IFACE/address" ]; then
    SYS_NETWORK_MAC="$(tr '[:upper:]' '[:lower:]' < "/sys/class/net/$SYS_NET_IFACE/address" 2>/dev/null | tr -d '\r\n' || true)"
  fi

  fw="$(vcgencmd version 2>/dev/null || true)"
  SYS_FIRMWARE_BUILD="$(sed -n '1p' <<< "$fw")"
  SYS_FIRMWARE_VERSION="$(sed -n '/^version[[:space:]]/ {p; q;}' <<< "$fw")"
  [ -n "$SYS_FIRMWARE_VERSION" ] || SYS_FIRMWARE_VERSION="$SYS_FIRMWARE_BUILD"
  boot="$(vcgencmd bootloader_version 2>/dev/null || true)"
  SYS_BOOTLOADER_VERSION="$(sed -n '/^version[[:space:]]/ {p; q;}' <<< "$boot")"
  if [ -z "$SYS_BOOTLOADER_VERSION" ]; then
    SYS_BOOTLOADER_VERSION="$(sed -n '1p' <<< "$boot")"
  else
    local boot_build
    boot_build="$(sed -n '1p' <<< "$boot")"
    [ -n "$boot_build" ] && SYS_BOOTLOADER_VERSION="${SYS_BOOTLOADER_VERSION} · ${boot_build}"
  fi
}

collect_extended_system_info() {
  SYS_MEM_TOTAL_MB="null"
  SYS_MEM_AVAILABLE_MB="null"
  SYS_MEM_USED_MB="null"
  SYS_MEM_USED_PERCENT="null"
  SYS_SWAP_TOTAL_MB="null"
  SYS_SWAP_USED_MB="null"
  SYS_SWAP_FREE_MB="null"
  SYS_SWAP_USED_PERCENT="null"
  SYS_ROOTFS_DEVICE=""
  SYS_ROOTFS_MOUNTPOINT="/"
  SYS_ROOTFS_TOTAL_GB="null"
  SYS_ROOTFS_USED_GB="null"
  SYS_ROOTFS_FREE_GB="null"
  SYS_ROOTFS_USED_PERCENT="null"
  SYS_LOAD_1M="null"
  SYS_LOAD_5M="null"
  SYS_LOAD_15M="null"
  SYS_UPTIME_SECONDS="null"
  SYS_CPU_CORE_COUNT="null"
  SYS_CPU_MODEL=""
  SYS_HOSTNAME=""
  if [ -r /proc/1/root/etc/hostname ]; then
    IFS= read -r SYS_HOSTNAME < /proc/1/root/etc/hostname 2>/dev/null || true
  fi
  [ -n "$SYS_HOSTNAME" ] || SYS_HOSTNAME="$(hostname 2>/dev/null || true)"
  SYS_NET_IFACE=""
  SYS_IPV4=""
  SYS_NET_RX_BYTES="null"
  SYS_NET_TX_BYTES="null"
  SYS_THROTTLED_RAW=""
  SYS_UNDERVOLTAGE="null"
  SYS_FREQ_CAPPED="null"
  SYS_THROTTLED="null"
  SYS_SOFT_TEMP_LIMIT="null"
  SYS_UNDERVOLTAGE_OCCURRED="null"
  SYS_FREQ_CAPPED_OCCURRED="null"
  SYS_THROTTLED_OCCURRED="null"
  SYS_SOFT_TEMP_LIMIT_OCCURRED="null"
  SYS_THERMAL_ZONES_JSON='[]'

  if [ -r /proc/meminfo ]; then
    local mem_total_kb mem_avail_kb swap_total_kb swap_free_kb
    mem_total_kb="$(awk '/^MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || true)"
    mem_avail_kb="$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo 2>/dev/null || true)"
    swap_total_kb="$(awk '/^SwapTotal:/ {print $2}' /proc/meminfo 2>/dev/null || true)"
    swap_free_kb="$(awk '/^SwapFree:/ {print $2}' /proc/meminfo 2>/dev/null || true)"
    if [ -n "$mem_total_kb" ] && [ "$mem_total_kb" -gt 0 ] 2>/dev/null; then
      SYS_MEM_TOTAL_MB="$(awk -v v="$mem_total_kb" 'BEGIN{printf "%.1f", v/1024}')"
      if [ -n "$mem_avail_kb" ] && [ "$mem_avail_kb" -ge 0 ] 2>/dev/null; then
        SYS_MEM_AVAILABLE_MB="$(awk -v v="$mem_avail_kb" 'BEGIN{printf "%.1f", v/1024}')"
        SYS_MEM_USED_MB="$(awk -v t="$mem_total_kb" -v a="$mem_avail_kb" 'BEGIN{printf "%.1f", (t-a)/1024}')"
        SYS_MEM_USED_PERCENT="$(awk -v t="$mem_total_kb" -v a="$mem_avail_kb" 'BEGIN{printf "%.1f", ((t-a)*100)/t}')"
      fi
    fi
    if [ -n "$swap_total_kb" ] && [ "$swap_total_kb" -gt 0 ] 2>/dev/null; then
      SYS_SWAP_TOTAL_MB="$(awk -v v="$swap_total_kb" 'BEGIN{printf "%.1f", v/1024}')"
      SYS_SWAP_FREE_MB="$(awk -v v="$swap_free_kb" 'BEGIN{printf "%.1f", v/1024}')"
      SYS_SWAP_USED_MB="$(awk -v t="$swap_total_kb" -v f="$swap_free_kb" 'BEGIN{printf "%.1f", (t-f)/1024}')"
      SYS_SWAP_USED_PERCENT="$(awk -v t="$swap_total_kb" -v f="$swap_free_kb" 'BEGIN{printf "%.1f", ((t-f)*100)/t}')"
    elif [ -n "$swap_total_kb" ] && [ "$swap_total_kb" -eq 0 ] 2>/dev/null; then
      SYS_SWAP_TOTAL_MB="0.0"; SYS_SWAP_USED_MB="0.0"; SYS_SWAP_FREE_MB="0.0"; SYS_SWAP_USED_PERCENT="0.0"
    fi
  fi

  local df_line total_k used_k avail_k used_pct
  df_line="$(df -kP / 2>/dev/null | tail -n1 || true)"
  if [ -n "$df_line" ]; then
    SYS_ROOTFS_DEVICE="$(awk '{print $1}' <<< "$df_line")"
    SYS_ROOTFS_MOUNTPOINT="$(awk '{print $6}' <<< "$df_line")"
    total_k="$(awk '{print $2}' <<< "$df_line")"
    used_k="$(awk '{print $3}' <<< "$df_line")"
    avail_k="$(awk '{print $4}' <<< "$df_line")"
    used_pct="$(awk '{print $5}' <<< "$df_line" | tr -d '%')"
    [ -n "$total_k" ] && SYS_ROOTFS_TOTAL_GB="$(awk -v v="$total_k" 'BEGIN{printf "%.2f", v/1024/1024}')"
    [ -n "$used_k" ] && SYS_ROOTFS_USED_GB="$(awk -v v="$used_k" 'BEGIN{printf "%.2f", v/1024/1024}')"
    [ -n "$avail_k" ] && SYS_ROOTFS_FREE_GB="$(awk -v v="$avail_k" 'BEGIN{printf "%.2f", v/1024/1024}')"
    [ -n "$used_pct" ] && SYS_ROOTFS_USED_PERCENT="$used_pct"
  fi

  if [ -r /proc/loadavg ]; then
    SYS_LOAD_1M="$(awk '{print $1}' /proc/loadavg 2>/dev/null || echo null)"
    SYS_LOAD_5M="$(awk '{print $2}' /proc/loadavg 2>/dev/null || echo null)"
    SYS_LOAD_15M="$(awk '{print $3}' /proc/loadavg 2>/dev/null || echo null)"
  fi
  if [ -r /proc/uptime ]; then
    SYS_UPTIME_SECONDS="$(awk '{printf "%.1f", $1}' /proc/uptime 2>/dev/null || echo null)"
  fi
  if command -v nproc >/dev/null 2>&1; then
    SYS_CPU_CORE_COUNT="$(nproc 2>/dev/null || echo null)"
  fi
  SYS_CPU_MODEL="$(awk -F: '/^Model[[:space:]]*:/ {gsub(/^[ \t]+/,"",$2); print $2; exit} /^model name[[:space:]]*:/ {gsub(/^[ \t]+/,"",$2); print $2; exit}' /proc/cpuinfo 2>/dev/null || true)"
  if [ -z "$SYS_CPU_MODEL" ] && [ -r /proc/device-tree/model ]; then
    SYS_CPU_MODEL="$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || true)"
  fi

  if command -v ip >/dev/null 2>&1; then
    SYS_NET_IFACE="$(ip route 2>/dev/null | awk '/^default/ {print $5; exit}')"
    [ -n "$SYS_NET_IFACE" ] && SYS_IPV4="$(ip -4 -o addr show dev "$SYS_NET_IFACE" scope global 2>/dev/null | awk '{split($4,a,"/"); print a[1]; exit}')"
  fi
  if [ -z "$SYS_NET_IFACE" ]; then
    local ni
    for ni in /sys/class/net/*; do
      [ -e "$ni" ] || continue
      [ "${ni##*/}" = "lo" ] && continue
      SYS_NET_IFACE="${ni##*/}"; break
    done
  fi
  if [ -n "$SYS_NET_IFACE" ]; then
    [ -r "/sys/class/net/$SYS_NET_IFACE/statistics/rx_bytes" ] && SYS_NET_RX_BYTES="$(cat "/sys/class/net/$SYS_NET_IFACE/statistics/rx_bytes" 2>/dev/null || echo null)"
    [ -r "/sys/class/net/$SYS_NET_IFACE/statistics/tx_bytes" ] && SYS_NET_TX_BYTES="$(cat "/sys/class/net/$SYS_NET_IFACE/statistics/tx_bytes" 2>/dev/null || echo null)"
  fi
  if [ -z "$SYS_IPV4" ] && command -v hostname >/dev/null 2>&1; then
    SYS_IPV4="$(hostname -I 2>/dev/null | awk '{print $1}')"
  fi

  collect_device_identity_cached

  local throttled value
  throttled="$(vcgencmd get_throttled 2>/dev/null || true)"
  if [[ "$throttled" =~ throttled=(0x[0-9a-fA-F]+) ]]; then
    SYS_THROTTLED_RAW="${BASH_REMATCH[1]}"
    value=$((SYS_THROTTLED_RAW))
    [ $((value & 1)) -ne 0 ] && SYS_UNDERVOLTAGE="true" || SYS_UNDERVOLTAGE="false"
    [ $((value & 2)) -ne 0 ] && SYS_FREQ_CAPPED="true" || SYS_FREQ_CAPPED="false"
    [ $((value & 4)) -ne 0 ] && SYS_THROTTLED="true" || SYS_THROTTLED="false"
    [ $((value & 8)) -ne 0 ] && SYS_SOFT_TEMP_LIMIT="true" || SYS_SOFT_TEMP_LIMIT="false"
    [ $((value & 65536)) -ne 0 ] && SYS_UNDERVOLTAGE_OCCURRED="true" || SYS_UNDERVOLTAGE_OCCURRED="false"
    [ $((value & 131072)) -ne 0 ] && SYS_FREQ_CAPPED_OCCURRED="true" || SYS_FREQ_CAPPED_OCCURRED="false"
    [ $((value & 262144)) -ne 0 ] && SYS_THROTTLED_OCCURRED="true" || SYS_THROTTLED_OCCURRED="false"
    [ $((value & 524288)) -ne 0 ] && SYS_SOFT_TEMP_LIMIT_OCCURRED="true" || SYS_SOFT_TEMP_LIMIT_OCCURRED="false"
  fi

  local zone ztype ztemp zc zobj
  for zone in /sys/class/thermal/thermal_zone*; do
    [ -r "$zone/temp" ] || continue
    ztype="$(cat "$zone/type" 2>/dev/null || echo "${zone##*/}")"
    ztemp="$(cat "$zone/temp" 2>/dev/null || echo '')"
    case "$ztemp" in ''|*[!0-9-]*) continue ;; esac
    zc="$(awk -v v="$ztemp" 'BEGIN{if (v>1000 || v<-1000) printf "%.1f", v/1000; else printf "%.1f", v}')"
    zobj="$(jq -cn --arg type "$ztype" --argjson temp_c "$zc" '{type:$type,temp_c:$temp_c}' 2>/dev/null || echo '')"
    [ -n "$zobj" ] && SYS_THERMAL_ZONES_JSON="$(jq -c --argjson o "$zobj" '. + [$o]' <<< "$SYS_THERMAL_ZONES_JSON" 2>/dev/null || echo "$SYS_THERMAL_ZONES_JSON")"
  done
}

collect_extended_system_info_cached() {
  local now last
  if [ "${PERF_EXTENDED_DONE_THIS_CYCLE:-false}" = "true" ]; then
    PERF_LAST_EXTENDED_REFRESHED="true"
    return 0
  fi
  PERF_LAST_EXTENDED_REFRESHED="false"
  now="${EPOCHREALTIME%%.*}"
  last="${TELEMETRY_LAST_EXTENDED_REFRESH:-0}"
  case "$last" in ''|*[!0-9]*) last=0 ;; esac
  if [ "$last" -eq 0 ] 2>/dev/null || [ $((now - last)) -ge "$TELEMETRY_EXTENDED_INTERVAL_SECONDS" ] 2>/dev/null; then
    # Po starcie musimy zainicjalizować pola. Później, jeśli w tym samym cyklu
    # pracował PMIC/SLOW, odkładamy SYSTEM o 5 s, aby nie kumulować skoku CPU.
    if [ "$last" -ne 0 ] 2>/dev/null && [ "$PERF_LAST_POWER_MODE" != "fast" ]; then
      return 0
    fi
    collect_extended_system_info
    TELEMETRY_LAST_EXTENDED_REFRESH="$now"
    PERF_LAST_EXTENDED_REFRESHED="true"
  fi
}

publish_telemetry_snapshot() {
  local rpm="0" pwm="0" level="0" max_level="0" temp_milli="0" temp_c="0.0" pct="0"
  local temp_sign="" temp_abs="0" temp_tenths="0" fan_type="" f="" p="" d="" tmp="" now=""
  local cycle_start_us="0" power_end_us="0" extended_end_us="0" cycle_end_us="0"
  local fan_calibration_json='{"state":"not_calibrated","grid_resolution_percent":1,"map_points":0}'
  local ai_cooling_json='{"schema":5,"state":"disabled","mode":"disabled","confidence_percent":0,"observations_total":0,"qualified_samples_total":0}'
  local platform_compatibility_json='{"state":"unknown","installed_core":"","installed_haos":"","minimum_core":"2026.10.1","minimum_haos":"18.3"}'
  cycle_start_us="$(epoch_us)"

  temp_milli="$(read_cpu_temp_millideg 2>/dev/null || echo 0)"
  case "$temp_milli" in ''|*[!0-9-]*) temp_milli=0 ;; esac
  if [ "$temp_milli" -lt 0 ] 2>/dev/null; then temp_sign="-"; temp_abs=$((-temp_milli)); else temp_abs=$temp_milli; fi
  temp_tenths=$(( (temp_abs + 50) / 100 ))
  temp_c="${temp_sign:-}$((temp_tenths / 10)).$((temp_tenths % 10))"

  for f in /sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input; do
    [ -r "$f" ] || continue
    IFS= read -r rpm < "$f" 2>/dev/null || rpm=0
    p="${f%fan1_input}pwm1"
    [ -r "$p" ] && { IFS= read -r pwm < "$p" 2>/dev/null || pwm=0; }
    break
  done

  for d in /sys/class/thermal/cooling_device*; do
    [ -r "$d/type" ] || continue
    IFS= read -r fan_type < "$d/type" 2>/dev/null || continue
    [[ "${fan_type,,}" == *fan* ]] || continue
    IFS= read -r level < "$d/cur_state" 2>/dev/null || level=0
    IFS= read -r max_level < "$d/max_state" 2>/dev/null || max_level=0
    break
  done

  case "$rpm" in ''|*[!0-9]*) rpm=0 ;; esac
  case "$pwm" in ''|*[!0-9]*) pwm=0 ;; esac
  case "$level" in ''|*[!0-9]*) level=0 ;; esac
  case "$max_level" in ''|*[!0-9]*) max_level=0 ;; esac
  [ "$pwm" -lt 0 ] 2>/dev/null && pwm=0
  [ "$pwm" -gt 255 ] 2>/dev/null && pwm=255
  pct=$(( (pwm * 100 + 127) / 255 ))
  [ "$pct" -lt 0 ] 2>/dev/null && pct=0
  [ "$pct" -gt 100 ] 2>/dev/null && pct=100

  collect_runtime_power_info
  power_end_us="$(epoch_us)"
  collect_extended_system_info_cached
  extended_end_us="$(epoch_us)"

  if [ -s "$FAN_CALIBRATION_STATE_FILE" ]; then
    fan_calibration_json="$(jq -c '{state:(.state // "unknown"),grid_resolution_percent:(.grid_resolution_percent // 1),detected_start_pwm_percent:(.detected_start_pwm_percent // null),safe_start_pwm_percent:(.safe_start_pwm_percent // null),detected_min_run_pwm_percent:(.detected_min_run_pwm_percent // null),min_safe_pwm_percent:(.min_safe_pwm_percent // null),current_pwm_percent:(.current_pwm_percent // null),current_rpm:(.current_rpm // null),progress_percent:(.progress_percent // null),stage:(.stage // ""),map_points:((.rpm_map // [])|length),calibrated_at:(.calibrated_at // ""),updated_at:(.updated_at // ""),last_error:(.last_error // "")}' "$FAN_CALIBRATION_STATE_FILE" 2>/dev/null || echo '{"state":"unknown","grid_resolution_percent":1,"map_points":0}')"
  fi
  if [ -s "$AI_COOLING_STATUS_FILE" ]; then
    ai_cooling_json="$(jq -c '.' "$AI_COOLING_STATUS_FILE" 2>/dev/null || echo '{"schema":5,"state":"unknown"}')"
  fi
  if [ -s "$PLATFORM_COMPATIBILITY_FILE" ]; then
    platform_compatibility_json="$(jq -c '{state:(.state // "unknown"),installed_core:(.installed_core // ""),installed_haos:(.installed_haos // ""),minimum_core:(.minimum_core // "2026.10.1"),minimum_haos:(.minimum_haos // "18.3"),message:(.message // ""),checked:(.checked // "")}' "$PLATFORM_COMPATIBILITY_FILE" 2>/dev/null || echo '{"state":"unknown","installed_core":"","installed_haos":"","minimum_core":"2026.10.1","minimum_haos":"18.3"}')"
  fi

  mkdir -p "$(dirname "$TELEMETRY_STATE_FILE")" 2>/dev/null || return 1
  tmp="${TELEMETRY_STATE_FILE}.tmp.$$"
  now="${EPOCHREALTIME%%.*}"
  jq -n \
    --argjson fan_calibration "$fan_calibration_json" --argjson ai_cooling "$ai_cooling_json" --argjson platform_compatibility "$platform_compatibility_json" \
    --argjson sample_epoch "$now" \
    --arg config_cpu_profile "$(cpu_profile_requested_profile 2>/dev/null || echo factory)" \
    --arg config_gpu_profile "$(gpu_profile_requested_profile 2>/dev/null || echo "$CONFIG_GPU_PROFILE")" \
    --argjson cpu_temperature "$temp_c" \
    --argjson fan_rpm "$rpm" --argjson fan_pwm "$pwm" --argjson fan_level "$level" --argjson fan_max_level "$max_level" --argjson fan_percent "$pct" \
    --argjson cpu_frequency_mhz "$SYS_CPU_FREQ_MHZ" --argjson cpu_frequency_min_mhz "$SYS_CPU_MIN_MHZ" --argjson cpu_frequency_max_mhz "$SYS_CPU_MAX_MHZ" --arg cpu_governor "$SYS_CPU_GOVERNOR" \
    --argjson cpu_core_frequencies_mhz "$SYS_CPU_CORE_FREQS_JSON" --argjson cpu_core_usage_percent "$SYS_CPU_CORE_USAGE_JSON" \
    --arg power_supply "$SYS_POWER_SUPPLY" --arg power_supply_type "$SYS_POWER_TYPE" --argjson power_supply_official "$SYS_POWER_OFFICIAL" \
    --argjson power_supply_pd_detected "$SYS_PD_DETECTED" --argjson power_supply_pd_5a_capable "$SYS_PD_5A" --arg power_supply_vid "$SYS_POWER_VID" --arg power_supply_product_vdo "$SYS_POWER_PRODUCT_VDO" \
    --argjson power_max_current_ma "$SYS_POWER_MAX_CURRENT_MA" --arg power_detection_source "$SYS_POWER_SOURCE" \
    --argjson usb_current_limit_ma "$SYS_USB_LIMIT_MA" --arg usb_limit_source "$SYS_USB_LIMIT_SOURCE" --argjson usb_config_override "$SYS_USB_CONFIG_OVERRIDE" --argjson usb_high_current "$SYS_USB_HIGH" \
    --argjson usb_over_current_detected "$SYS_USB_OVERCURRENT" --arg over_current_source "$SYS_OVERCURRENT_SOURCE" \
    --argjson pmic_available "$SYS_PMIC_AVAILABLE" --arg pmic_source "$SYS_PMIC_SOURCE" --argjson input_voltage_v "$SYS_INPUT_VOLTAGE_V" \
    --argjson pmic_power_w "$SYS_PMIC_POWER_W" --argjson pmic_equivalent_current_a "$SYS_PMIC_EQ_CURRENT_A" --argjson pmic_temperature_c "$SYS_PMIC_TEMP_C" \
    --argjson core_current_a "$SYS_CORE_CURRENT_A" --argjson core_voltage_v "$SYS_CORE_VOLTAGE_V" --argjson core_power_w "$SYS_CORE_POWER_W" --argjson pmic_rails "$SYS_PMIC_RAILS_JSON" \
    --argjson usb_device_count "$SYS_USB_DEVICE_COUNT" --argjson usb_declared_current_ma "$SYS_USB_DECLARED_MA" --argjson usb_devices "$SYS_USB_DEVICES_JSON" \
    --argjson boot_config_available "$SYS_BOOT_CONFIG_AVAILABLE" --arg boot_config_device "$SYS_BOOT_CONFIG_DEVICE" --arg boot_config_path "$SYS_BOOT_CONFIG_PATH" --arg boot_config_source "$SYS_BOOT_CONFIG_SOURCE" --arg boot_config_sha256 "$SYS_BOOT_CONFIG_SHA256" \
    --argjson boot_config_entry_count "$SYS_BOOT_CONFIG_ENTRY_COUNT" --argjson boot_config_truncated "$SYS_BOOT_CONFIG_TRUNCATED" --argjson boot_config_entries "$SYS_BOOT_CONFIG_ENTRIES_JSON" --argjson boot_config_includes "$SYS_BOOT_CONFIG_INCLUDES_JSON" \
    --argjson boot_config_overlays "$SYS_BOOT_CONFIG_OVERLAYS_JSON" --argjson boot_config_dtparams "$SYS_BOOT_CONFIG_DTPARAMS_JSON" --argjson active_config_int "$SYS_ACTIVE_CONFIG_INT_JSON" --argjson active_config_str "$SYS_ACTIVE_CONFIG_STR_JSON" --argjson bootloader_config "$SYS_BOOTLOADER_CONFIG_JSON" \
    --argjson saved_arm_freq_mhz "$SYS_CONFIG_SAVED_ARM_FREQ_MHZ" --argjson active_arm_freq_mhz "$SYS_CONFIG_ACTIVE_ARM_FREQ_MHZ" --argjson saved_core_freq_mhz "$SYS_CONFIG_SAVED_CORE_FREQ_MHZ" --argjson active_core_freq_mhz "$SYS_CONFIG_ACTIVE_CORE_FREQ_MHZ" --argjson saved_gpu_freq_mhz "$SYS_CONFIG_SAVED_GPU_FREQ_MHZ" --argjson active_gpu_freq_mhz "$SYS_CONFIG_ACTIVE_GPU_FREQ_MHZ" \
    --arg saved_over_voltage "$SYS_CONFIG_SAVED_OVER_VOLTAGE" --arg active_over_voltage "$SYS_CONFIG_ACTIVE_OVER_VOLTAGE" --arg saved_over_voltage_delta "$SYS_CONFIG_SAVED_OVER_VOLTAGE_DELTA" --arg active_over_voltage_delta "$SYS_CONFIG_ACTIVE_OVER_VOLTAGE_DELTA" --argjson saved_usb_max_current_enable "$SYS_CONFIG_SAVED_USB_MAX_CURRENT_ENABLE" --argjson active_usb_max_current_enable "$SYS_CONFIG_ACTIVE_USB_MAX_CURRENT_ENABLE" --argjson saved_arm_64bit "$SYS_CONFIG_SAVED_ARM_64BIT" --argjson active_arm_64bit "$SYS_CONFIG_ACTIVE_ARM_64BIT" --arg config_status "$SYS_CONFIG_STATUS" --argjson config_pending_restart "$SYS_CONFIG_PENDING_RESTART" \
    --arg kernel_cmdline "$SYS_KERNEL_CMDLINE" --arg kernel_version "$SYS_KERNEL_VERSION" --arg architecture "$SYS_ARCHITECTURE" --arg rpi_model "$SYS_RPI_MODEL" \
    --arg board_revision "$SYS_BOARD_REVISION" --arg hardware_revision "$SYS_HARDWARE_REVISION" --arg serial_number "$SYS_SERIAL_NUMBER" --arg network_mac "$SYS_NETWORK_MAC" \
    --arg os_name "$SYS_OS_NAME" --arg os_version "$SYS_OS_VERSION" --arg os_pretty_name "$SYS_OS_PRETTY_NAME" --arg firmware_version "$SYS_FIRMWARE_VERSION" --arg firmware_build "$SYS_FIRMWARE_BUILD" --arg bootloader_version "$SYS_BOOTLOADER_VERSION" \
    --argjson memory_total_mb "$SYS_MEM_TOTAL_MB" --argjson memory_available_mb "$SYS_MEM_AVAILABLE_MB" --argjson memory_used_mb "$SYS_MEM_USED_MB" --argjson memory_used_percent "$SYS_MEM_USED_PERCENT" \
    --argjson swap_total_mb "$SYS_SWAP_TOTAL_MB" --argjson swap_used_mb "$SYS_SWAP_USED_MB" --argjson swap_free_mb "$SYS_SWAP_FREE_MB" --argjson swap_used_percent "$SYS_SWAP_USED_PERCENT" \
    --arg rootfs_device "$SYS_ROOTFS_DEVICE" --arg rootfs_mountpoint "$SYS_ROOTFS_MOUNTPOINT" --argjson rootfs_total_gb "$SYS_ROOTFS_TOTAL_GB" --argjson rootfs_used_gb "$SYS_ROOTFS_USED_GB" --argjson rootfs_free_gb "$SYS_ROOTFS_FREE_GB" --argjson rootfs_used_percent "$SYS_ROOTFS_USED_PERCENT" \
    --argjson load_1m "$SYS_LOAD_1M" --argjson load_5m "$SYS_LOAD_5M" --argjson load_15m "$SYS_LOAD_15M" --argjson uptime_seconds "$SYS_UPTIME_SECONDS" --argjson cpu_core_count "$SYS_CPU_CORE_COUNT" --arg cpu_model "$SYS_CPU_MODEL" \
    --arg hostname "$SYS_HOSTNAME" --arg network_interface "$SYS_NET_IFACE" --arg ipv4 "$SYS_IPV4" --argjson network_rx_bytes "$SYS_NET_RX_BYTES" --argjson network_tx_bytes "$SYS_NET_TX_BYTES" \
    --arg throttled_raw "$SYS_THROTTLED_RAW" --argjson undervoltage "$SYS_UNDERVOLTAGE" --argjson frequency_capped "$SYS_FREQ_CAPPED" --argjson throttled "$SYS_THROTTLED" --argjson soft_temp_limit "$SYS_SOFT_TEMP_LIMIT" \
    --argjson undervoltage_occurred "$SYS_UNDERVOLTAGE_OCCURRED" --argjson frequency_capped_occurred "$SYS_FREQ_CAPPED_OCCURRED" --argjson throttled_occurred "$SYS_THROTTLED_OCCURRED" --argjson soft_temp_limit_occurred "$SYS_SOFT_TEMP_LIMIT_OCCURRED" --argjson thermal_zones "$SYS_THERMAL_ZONES_JSON" \
    '{schema:11,sample_epoch:$sample_epoch,config_cpu_profile:$config_cpu_profile,config_gpu_profile:$config_gpu_profile,cpu_temperature:$cpu_temperature,fan_rpm:$fan_rpm,fan_pwm:$fan_pwm,fan_level:$fan_level,fan_max_level:$fan_max_level,fan_percent:$fan_percent,fan_calibration:$fan_calibration,ai_cooling:$ai_cooling,platform_compatibility:$platform_compatibility,
      cpu_frequency_mhz:$cpu_frequency_mhz,cpu_frequency_min_mhz:$cpu_frequency_min_mhz,cpu_frequency_max_mhz:$cpu_frequency_max_mhz,cpu_governor:$cpu_governor,cpu_core_frequencies_mhz:$cpu_core_frequencies_mhz,cpu_core_usage_percent:$cpu_core_usage_percent,
      power_supply:$power_supply,power_supply_type:$power_supply_type,power_supply_official:$power_supply_official,power_supply_pd_detected:$power_supply_pd_detected,power_supply_pd_5a_capable:$power_supply_pd_5a_capable,power_supply_vid:$power_supply_vid,power_supply_product_vdo:$power_supply_product_vdo,power_max_current_ma:$power_max_current_ma,power_detection_source:$power_detection_source,
      usb_current_limit_ma:$usb_current_limit_ma,usb_high_current:$usb_high_current,usb_limit_source:$usb_limit_source,usb_config_override:$usb_config_override,usb_over_current_detected:$usb_over_current_detected,over_current_source:$over_current_source,
      pmic_available:$pmic_available,pmic_source:$pmic_source,input_voltage_v:$input_voltage_v,pmic_power_w:$pmic_power_w,pmic_equivalent_current_a:$pmic_equivalent_current_a,pmic_temperature_c:$pmic_temperature_c,core_current_a:$core_current_a,core_voltage_v:$core_voltage_v,core_power_w:$core_power_w,pmic_rails:$pmic_rails,
      usb_device_count:$usb_device_count,usb_declared_current_ma:$usb_declared_current_ma,usb_devices:$usb_devices,
      boot_config_available:$boot_config_available,boot_config_device:$boot_config_device,boot_config_path:$boot_config_path,boot_config_source:$boot_config_source,boot_config_sha256:$boot_config_sha256,boot_config_entry_count:$boot_config_entry_count,boot_config_truncated:$boot_config_truncated,boot_config_entries:$boot_config_entries,boot_config_includes:$boot_config_includes,boot_config_overlays:$boot_config_overlays,boot_config_dtparams:$boot_config_dtparams,active_config_int:$active_config_int,active_config_str:$active_config_str,bootloader_config:$bootloader_config,saved_arm_freq_mhz:$saved_arm_freq_mhz,active_arm_freq_mhz:$active_arm_freq_mhz,saved_core_freq_mhz:$saved_core_freq_mhz,active_core_freq_mhz:$active_core_freq_mhz,saved_gpu_freq_mhz:$saved_gpu_freq_mhz,active_gpu_freq_mhz:$active_gpu_freq_mhz,saved_over_voltage:$saved_over_voltage,active_over_voltage:$active_over_voltage,saved_over_voltage_delta:$saved_over_voltage_delta,active_over_voltage_delta:$active_over_voltage_delta,saved_usb_max_current_enable:$saved_usb_max_current_enable,active_usb_max_current_enable:$active_usb_max_current_enable,saved_arm_64bit:$saved_arm_64bit,active_arm_64bit:$active_arm_64bit,config_status:$config_status,config_pending_restart:$config_pending_restart,kernel_cmdline:$kernel_cmdline,kernel_version:$kernel_version,architecture:$architecture,rpi_model:$rpi_model,board_revision:$board_revision,hardware_revision:$hardware_revision,serial_number:$serial_number,network_mac:$network_mac,os_name:$os_name,os_version:$os_version,os_pretty_name:$os_pretty_name,firmware_version:$firmware_version,firmware_build:$firmware_build,bootloader_version:$bootloader_version,memory_total_mb:$memory_total_mb,memory_available_mb:$memory_available_mb,memory_used_mb:$memory_used_mb,memory_used_percent:$memory_used_percent,swap_total_mb:$swap_total_mb,swap_used_mb:$swap_used_mb,swap_free_mb:$swap_free_mb,swap_used_percent:$swap_used_percent,rootfs_device:$rootfs_device,rootfs_mountpoint:$rootfs_mountpoint,rootfs_total_gb:$rootfs_total_gb,rootfs_used_gb:$rootfs_used_gb,rootfs_free_gb:$rootfs_free_gb,rootfs_used_percent:$rootfs_used_percent,load_1m:$load_1m,load_5m:$load_5m,load_15m:$load_15m,uptime_seconds:$uptime_seconds,cpu_core_count:$cpu_core_count,cpu_model:$cpu_model,hostname:$hostname,network_interface:$network_interface,ipv4:$ipv4,network_rx_bytes:$network_rx_bytes,network_tx_bytes:$network_tx_bytes,throttled_raw:$throttled_raw,undervoltage:$undervoltage,frequency_capped:$frequency_capped,throttled:$throttled,soft_temp_limit:$soft_temp_limit,undervoltage_occurred:$undervoltage_occurred,frequency_capped_occurred:$frequency_capped_occurred,throttled_occurred:$throttled_occurred,soft_temp_limit_occurred:$soft_temp_limit_occurred,thermal_zones:$thermal_zones}' \
    > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$TELEMETRY_STATE_FILE"

  if [ -n "${SUPERVISOR_TOKEN:-}" ]; then
    local relay_payload relay_now telemetry_json
    relay_now="${EPOCHREALTIME%%.*}"
    if [ "${TELEMETRY_LAST_RELAY_PUBLISH:-0}" -eq 0 ] 2>/dev/null || [ $((relay_now - TELEMETRY_LAST_RELAY_PUBLISH)) -ge "$HOST_RELAY_INTERVAL_SECONDS" ] 2>/dev/null; then
      TELEMETRY_LAST_RELAY_PUBLISH="$relay_now"
      telemetry_json="$(<"$TELEMETRY_STATE_FILE")"
      relay_payload="{\"state\":\"${temp_c}\",\"attributes\":${telemetry_json}}"
      # After namespace migration only the canonical relay is required. Legacy aliases
      # are kept temporarily during migration, then stopped to cut two REST POSTs / 10 s.
      local -a relay_entities=(sensor.sbc5_control_center_host_telemetry)
      if ! namespace_migration_complete; then
        relay_entities+=(sensor.rpi5_control_center_host_telemetry sensor.rpi5_fan_manager_host_telemetry)
      fi
      for relay_entity in "${relay_entities[@]}"; do
        curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$relay_payload" \
          "http://supervisor/core/api/states/${relay_entity}" >/dev/null 2>&1 || true
      done
    fi

    # 2.8.22: AI gets a compact relay independent from the heavy host-telemetry relay.
    # Publish only when its semantic payload changes; retain a 5-minute keepalive for
    # REST-created state recovery/visibility without waking HA templates unnecessarily.
    if [ "${TELEMETRY_LAST_AI_RELAY_CHECK:-0}" -eq 0 ] 2>/dev/null || [ $((relay_now - TELEMETRY_LAST_AI_RELAY_CHECK)) -ge "$AI_RUNTIME_RELAY_INTERVAL_SECONDS" ] 2>/dev/null; then
      TELEMETRY_LAST_AI_RELAY_CHECK="$relay_now"
      local ai_runtime_state ai_runtime_payload ai_runtime_signature ai_runtime_due=false
      ai_runtime_state="$(jq -r '.state // "unknown"' <<< "$ai_cooling_json" 2>/dev/null || echo unknown)"
      ai_runtime_payload="$(jq -cn --arg state "$ai_runtime_state" --argjson ai "$ai_cooling_json" \
        '{state:$state,attributes:{friendly_name:"SBC5 Control Center AI Runtime",icon:"mdi:brain",ai_cooling:$ai}}')"
      ai_runtime_signature="$(printf '%s' "$ai_runtime_payload" | sha256sum | awk '{print $1}')"
      if [ -z "${AI_RUNTIME_LAST_SIGNATURE:-}" ] || [ "$ai_runtime_signature" != "$AI_RUNTIME_LAST_SIGNATURE" ]; then
        ai_runtime_due=true
      elif [ "${TELEMETRY_LAST_AI_RELAY_PUBLISH:-0}" -eq 0 ] 2>/dev/null || [ $((relay_now - TELEMETRY_LAST_AI_RELAY_PUBLISH)) -ge "$AI_RUNTIME_RELAY_KEEPALIVE_SECONDS" ] 2>/dev/null; then
        ai_runtime_due=true
      fi
      if [ "$ai_runtime_due" = "true" ]; then
        if curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$ai_runtime_payload" \
          http://supervisor/core/api/states/sensor.sbc5_control_center_ai_runtime >/dev/null 2>&1; then
          AI_RUNTIME_LAST_SIGNATURE="$ai_runtime_signature"
          TELEMETRY_LAST_AI_RELAY_PUBLISH="$relay_now"
        fi
      fi
    fi
  fi

  cycle_end_us="$(epoch_us)"
  PERF_LAST_POWER_MS=$(( (power_end_us - cycle_start_us) / 1000 ))
  PERF_LAST_EXTENDED_MS=$(( (extended_end_us - power_end_us) / 1000 ))
  PERF_LAST_CYCLE_MS=$(( (cycle_end_us - cycle_start_us) / 1000 ))
  if [ "$PERF_LAST_POWER_MODE" = "slow" ]; then PERF_LAST_CYCLE_TIER="slow"
  elif [ "$PERF_LAST_POWER_MODE" = "normal" ] || [ "$PERF_LAST_EXTENDED_REFRESHED" = "true" ]; then PERF_LAST_CYCLE_TIER="normal"
  else PERF_LAST_CYCLE_TIER="fast"; fi
  PERF_CYCLE_COUNT=$((PERF_CYCLE_COUNT + 1))
  case "$PERF_LAST_CYCLE_TIER" in
    slow)
      PERF_SLOW_COUNT=$((PERF_SLOW_COUNT + 1))
      PERF_LAST_SLOW_CYCLE_MS="$PERF_LAST_CYCLE_MS"
      PERF_LAST_SLOW_PARALLEL_JOBS="$PERF_LAST_PARALLEL_JOBS"
      PERF_LAST_SLOW_PARALLEL_MS="$PERF_LAST_PARALLEL_MS"
      ;;
    normal) PERF_NORMAL_COUNT=$((PERF_NORMAL_COUNT + 1)) ;;
    *) PERF_FAST_COUNT=$((PERF_FAST_COUNT + 1)) ;;
  esac
}

publish_performance_state() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  local now wall_us usage_usec mem_bytes delta_cpu delta_wall pct_tenths=0 cpu_percent mem_tenths mem_mb payload
  local cores cpu_total_tenths cpu_total_percent allowed_list
  now="${EPOCHREALTIME%%.*}"
  if [ "${PERF_LAST_STATE_PUBLISH:-0}" -gt 0 ] 2>/dev/null && [ $((now - PERF_LAST_STATE_PUBLISH)) -lt 60 ] 2>/dev/null; then
    return 0
  fi
  PERF_LAST_STATE_PUBLISH="$now"
  wall_us="$(epoch_us)"
  usage_usec="$(read_cgroup_cpu_usage_usec 2>/dev/null || echo 0)"
  mem_bytes="$(read_cgroup_memory_bytes 2>/dev/null || echo 0)"
  cpu_percent="0.0"
  if [ "${PERF_PREV_CGROUP_USAGE_USEC:-0}" -gt 0 ] 2>/dev/null && [ "${PERF_PREV_WALL_USEC:-0}" -gt 0 ] 2>/dev/null; then
    delta_cpu=$((usage_usec - PERF_PREV_CGROUP_USAGE_USEC))
    delta_wall=$((wall_us - PERF_PREV_WALL_USEC))
    if [ "$delta_cpu" -ge 0 ] 2>/dev/null && [ "$delta_wall" -gt 0 ] 2>/dev/null; then
      pct_tenths=$((delta_cpu * 1000 / delta_wall))
      cpu_percent="$((pct_tenths / 10)).$((pct_tenths % 10))"
    fi
  fi
  PERF_PREV_CGROUP_USAGE_USEC="$usage_usec"
  PERF_PREV_WALL_USEC="$wall_us"
  mem_mb="0.0"
  if [ "$mem_bytes" -gt 0 ] 2>/dev/null; then
    mem_tenths=$((mem_bytes * 10 / 1048576))
    mem_mb="$((mem_tenths / 10)).$((mem_tenths % 10))"
  fi
  cores="$(nproc 2>/dev/null || echo 1)"
  case "$cores" in ''|*[!0-9]*) cores=1 ;; esac
  [ "$cores" -lt 1 ] 2>/dev/null && cores=1
  cpu_total_tenths=$(( (pct_tenths + cores / 2) / cores ))
  cpu_total_percent="$((cpu_total_tenths / 10)).$((cpu_total_tenths % 10))"
  allowed_list="$(read_cpu_allowed_list 2>/dev/null || echo unknown)"
  resolve_multicore_workers

  payload="$(jq -cn \
    --arg state "$cpu_percent" --argjson cpu_percent "$cpu_percent" --argjson cpu_total_percent "$cpu_total_percent" --argjson cpu_available_cores "$cores" --arg cpu_allowed_list "$allowed_list" --argjson memory_mb "$mem_mb" \
    --argjson cycle_ms "$PERF_LAST_CYCLE_MS" --argjson power_ms "$PERF_LAST_POWER_MS" --argjson extended_ms "$PERF_LAST_EXTENDED_MS" \
    --arg mode "$PERF_LAST_CYCLE_TIER" --argjson cycles "$PERF_CYCLE_COUNT" --argjson fast "$PERF_FAST_COUNT" --argjson normal "$PERF_NORMAL_COUNT" --argjson slow "$PERF_SLOW_COUNT" \
    --argjson publish_s "$TELEMETRY_PUBLISH_INTERVAL_SECONDS" --argjson realtime_s "$REALTIME_PUBLISH_INTERVAL_SECONDS" --argjson relay_s "$HOST_RELAY_INTERVAL_SECONDS" --argjson pmic_s "$TELEMETRY_PMIC_INTERVAL_SECONDS" --argjson system_s "$TELEMETRY_EXTENDED_INTERVAL_SECONDS" --argjson slow_s "$TELEMETRY_POWER_INTERVAL_SECONDS" --argjson boot_cache_s "$BOOT_CONFIG_CACHE_SECONDS" \
    --argjson multicore_enabled "$MULTICORE_TELEMETRY_ENABLED" --arg multicore_workers_config "$MULTICORE_WORKERS_CONFIG" --argjson multicore_workers_effective "$MULTICORE_WORKERS_EFFECTIVE" --argjson parallel_jobs "$PERF_LAST_PARALLEL_JOBS" --argjson parallel_stage_ms "$PERF_LAST_PARALLEL_MS" --arg parallel_mode "$PERF_LAST_PARALLEL_MODE" --argjson parallel_cycles "$PERF_PARALLEL_CYCLES" --argjson max_parallel_jobs "$PERF_MAX_PARALLEL_JOBS" \
    --argjson last_slow_cycle_ms "$PERF_LAST_SLOW_CYCLE_MS" --argjson last_slow_parallel_jobs "$PERF_LAST_SLOW_PARALLEL_JOBS" --argjson last_slow_parallel_ms "$PERF_LAST_SLOW_PARALLEL_MS" --argjson parallel_samples "$PERF_PARALLEL_SAMPLES" --argjson parallel_ms_total "$PERF_PARALLEL_MS_TOTAL" --argjson parallel_jobs_total "$PERF_PARALLEL_JOBS_TOTAL" --argjson max_parallel_ms "$PERF_MAX_PARALLEL_MS" --argjson estimated_sequential_ms "$PERF_LAST_PARALLEL_EST_SEQ_MS" --argjson multicore_gain_ms "$PERF_LAST_MULTICORE_GAIN_MS" --argjson multicore_gain_percent "$PERF_LAST_MULTICORE_GAIN_PERCENT" --argjson parallel_efficiency_percent "$PERF_LAST_PARALLEL_EFFICIENCY_PERCENT" \
    '{state:$state,attributes:{friendly_name:"SBC5 Control Center CPU Usage",icon:"mdi:speedometer-slow",unit_of_measurement:"%",state_class:"measurement",cpu_percent:$cpu_percent,cpu_total_percent:$cpu_total_percent,cpu_available_cores:$cpu_available_cores,cpu_allowed_list:$cpu_allowed_list,memory_mb:$memory_mb,last_cycle_ms:$cycle_ms,power_stage_ms:$power_ms,extended_stage_ms:$extended_ms,last_cycle_tier:$mode,cycles_since_start:$cycles,fast_cycles:$fast,normal_cycles:$normal,slow_cycles:$slow,multicore_telemetry_enabled:$multicore_enabled,multicore_workers_config:$multicore_workers_config,multicore_workers_effective:$multicore_workers_effective,last_parallel_jobs:$parallel_jobs,last_parallel_stage_ms:$parallel_stage_ms,last_parallel_mode:$parallel_mode,parallel_cycles_since_start:$parallel_cycles,max_parallel_jobs_since_start:$max_parallel_jobs,last_slow_cycle_ms:$last_slow_cycle_ms,last_slow_parallel_jobs:$last_slow_parallel_jobs,last_slow_parallel_stage_ms:$last_slow_parallel_ms,avg_parallel_stage_ms:(if $parallel_samples>0 then ($parallel_ms_total/$parallel_samples|floor) else 0 end),max_parallel_stage_ms:$max_parallel_ms,parallel_jobs_total:$parallel_jobs_total,estimated_sequential_ms:$estimated_sequential_ms,multicore_gain_ms:$multicore_gain_ms,multicore_gain_percent:$multicore_gain_percent,parallel_efficiency_percent:$parallel_efficiency_percent,telemetry_publish_s:$publish_s,realtime_refresh_s:$realtime_s,pmic_refresh_s:$pmic_s,system_refresh_s:$system_s,slow_refresh_s:$slow_s,host_relay_s:$relay_s,boot_cache_s:$boot_cache_s,measurement:"cgroup usage; 100% ≈ one fully used CPU core; cpu_total_percent is normalized across available cores"}}')"
  curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$payload" \
    http://supervisor/core/api/states/sensor.sbc5_control_center_cpu_usage >/dev/null 2>&1 || true
}

# v1.9.6: lekka ścieżka chłodzenia. Nie uruchamia jq/curl/vcgencmd ani ciężkiej diagnostyki.
# Standardowy interwał 5 s zapewnia płynny odczyt bez zbędnego obciążenia.
publish_realtime_cooling_snapshot() {
  local temp_milli="0" temp_c="0.0" temp_abs="0" temp_tenths="0" temp_sign="" rpm="0" pwm="0" level="0" max_level="0" pct="0"
  local z="" type="" value="" f="" p="" d="" fan_type="" now=""

  for z in /sys/class/thermal/thermal_zone*; do
    [ -r "$z/type" ] || continue
    IFS= read -r type < "$z/type" 2>/dev/null || true
    type="${type,,}"
    case "$type" in
      *cpu*|cpu-thermal|soc_thermal)
        [ -r "$z/temp" ] || continue
        IFS= read -r value < "$z/temp" 2>/dev/null || true
        case "$value" in ''|*[!0-9-]*) ;; *) temp_milli="$value"; break ;; esac
        ;;
    esac
  done
  if [ "$temp_milli" = "0" ] && [ -r /sys/class/thermal/thermal_zone0/temp ]; then
    IFS= read -r temp_milli < /sys/class/thermal/thermal_zone0/temp 2>/dev/null || temp_milli=0
  fi
  case "$temp_milli" in ''|*[!0-9-]*) temp_milli=0 ;; esac
  temp_c="$(millideg_to_c_1dp "$temp_milli")"

  for f in /sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input; do
    [ -r "$f" ] || continue
    IFS= read -r rpm < "$f" 2>/dev/null || rpm=0
    p="${f%fan1_input}pwm1"
    [ -r "$p" ] && { IFS= read -r pwm < "$p" 2>/dev/null || pwm=0; }
    break
  done
  for d in /sys/class/thermal/cooling_device*; do
    [ -r "$d/type" ] || continue
    IFS= read -r fan_type < "$d/type" 2>/dev/null || continue
    [[ "${fan_type,,}" == *fan* ]] || continue
    IFS= read -r level < "$d/cur_state" 2>/dev/null || level=0
    IFS= read -r max_level < "$d/max_state" 2>/dev/null || max_level=0
    break
  done

  case "$rpm" in ''|*[!0-9]*) rpm=0 ;; esac
  case "$pwm" in ''|*[!0-9]*) pwm=0 ;; esac
  case "$level" in ''|*[!0-9]*) level=0 ;; esac
  case "$max_level" in ''|*[!0-9]*) max_level=0 ;; esac
  [ "$pwm" -lt 0 ] 2>/dev/null && pwm=0
  [ "$pwm" -gt 255 ] 2>/dev/null && pwm=255
  pct=$(( (pwm * 100 + 127) / 255 ))
  now="${EPOCHREALTIME:-0}"

  # Jeden mały zapis do współdzielonego /config; brak zewnętrznych procesów w ścieżce 1 s.
  printf '{"sample_epoch":%s,"cpu_temperature":%s,"fan_rpm":%s,"fan_pwm":%s,"fan_percent":%s,"fan_level":%s,"fan_max_level":%s}\n' \
    "$now" "$temp_c" "$rpm" "$pwm" "$pct" "$level" "$max_level" > "$REALTIME_STATE_FILE" 2>/dev/null || true
}

realtime_cooling_loop() {
  sleep 1
  while true; do
    publish_realtime_cooling_snapshot || true
    sleep "$REALTIME_PUBLISH_INTERVAL_SECONDS"
  done
}

# v2.1.8 Balanced Adaptive PWM --------------------------------------------------
# The kernel thermal curve establishes the initial base state. While this controller
# is active it exclusively owns the bound fan control path using the safest takeover
# mechanism exported by the running kernel (user_space governor when available,
# otherwise thermal-zone mode=disabled), keeps a persistent controller_state, and
# restores the original kernel thermal state on every exit/fallback path.
adaptive_pwm_find_device() {
  local root d type
  # v2.1.3: the add-on/container view of /sys can be mounted read-only even
  # with full_access. host_pid gives us the real host sysfs through PID1.
  # Prefer that path so cur_state remains RW exactly as exported by Linux.
  for root in /proc/1/root/sys/class/thermal /sys/class/thermal; do
    [ -d "$root" ] || continue
    for d in "$root"/cooling_device*; do
      [ -e "$d" ] || continue
      [ -r "$d/type" ] || continue
      IFS= read -r type < "$d/type" 2>/dev/null || continue
      [[ "${type,,}" == *fan* ]] || continue
      [ -r "$d/cur_state" ] && [ -r "$d/max_state" ] || continue
      printf '%s\n' "$d"
      return 0
    done
  done
  return 1
}

adaptive_pwm_kernel_profile_matches_custom1() {
  local trips expected
  trips="$(read_kernel_trip_points)"
  load_custom_curve 1
  expected="$CUSTOM_TRIPS_CSV"
  [ -n "$trips" ] && [ "$trips" = "$expected" ]
}

adaptive_pwm_profile_active() {
  # v2.6.7: user-space Adaptive PWM must not be blocked only because the kernel
  # still exposes the factory trip temperatures after an app/HA restart. If the
  # calibrated 1% cooling device is present and writable, Auto/Hybrid can safely
  # take exclusive ownership of cur_state and regulate around custom1 immediately.
  local dev max_state
  [ -e "$FACTORY_RESTORE_PENDING_FILE" ] && return 1
  dev="$(adaptive_pwm_find_device 2>/dev/null || true)"
  [ -n "$dev" ] || return 1
  max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"
  case "$max_state" in ''|*[!0-9]*) max_state=0 ;; esac
  [ "$max_state" -ge 100 ] 2>/dev/null || return 1
  [ -w "$dev/cur_state" ] || return 1
  return 0
}

adaptive_pwm_write_status() {
  local state="$1" action="$2" temp_milli="${3:-0}" current="${4:-0}" desired="${5:-0}" max_state="${6:-0}" writable="${7:-false}"
  local owner="${8:-kernel}" zone="${9:-}" controller="${10:-$desired}" base="${11:-$current}" original_policy="${12:-}" adaptive_trim_pp="${13:-0}"
  local temp_c target_c now
  temp_c="$(millideg_to_c_1dp "$temp_milli" 2>/dev/null || echo 0.0)"
  target_c="$CURVE1_TARGET_C"
  now="${EPOCHREALTIME:-0}"
  mkdir -p "$(dirname "$ADAPTIVE_PWM_STATE_FILE")" 2>/dev/null || true
  printf '{"sample_epoch":%s,"state":"%s","action":"%s","temperature_c":%s,"target_c":%s,"deadband_c":%s,"current_level":%s,"requested_level":%s,"controller_level":%s,"base_level":%s,"adaptive_trim_pp":%s,"max_level":%s,"writable":%s,"control_owner":"%s","thermal_zone":"%s","original_policy":"%s"}\n' \
    "$now" "$state" "$action" "$temp_c" "$target_c" "$ADAPTIVE_PWM_DEADBAND_C" "$current" "$desired" "$controller" "$base" "$adaptive_trim_pp" "$max_state" "$writable" "$owner" "$zone" "$original_policy" \
    > "$ADAPTIVE_PWM_STATE_FILE" 2>/dev/null || true
}
apply_ai_grid_suggestion() {
  local confirmed="${1:-false}" backup="${AI_GRID_PROFILE_FILE}.bak.$$" result=""
  [ "$confirmed" = "true" ] || { log "AI Grid: odrzucono zastosowanie bez confirm=true."; return 2; }
  [ -s "$AI_COOLING_STATUS_FILE" ] || { log "AI Grid: brak statusu AI."; return 3; }
  load_custom_curve 1
  if [ -s "$AI_GRID_PROFILE_FILE" ]; then cp -f "$AI_GRID_PROFILE_FILE" "$backup" 2>/dev/null || true; else rm -f "$backup"; fi
  result="$(python3 "$AI_COOLING_SCRIPT" apply-grid --status "$AI_COOLING_STATUS_FILE" --profile "$AI_GRID_PROFILE_FILE" --target "$CURVE1_TARGET_C" --min-confidence 75 2>/dev/null)" || {
    rc=$?; rm -f "$backup" 2>/dev/null || true
    log "AI Grid: sugestia nie została zastosowana (rc=${rc}, ${result:-brak danych})."
    return "$rc"
  }
  load_custom_curve 1
  if write_overlay_profile custom1; then
    rm -f "$backup" 2>/dev/null || true
    ha_publish_curve_editor_state || true
    printf '%s\n' "${EPOCHREALTIME:-$(date +%s)}" > "$CONFIG_UI_RELOAD_FILE" 2>/dev/null || true
    log "AI Grid: zastosowano zatwierdzoną sugestię; geometria=${CUSTOM_PRETTY}."
    return 0
  fi
  if [ -s "$backup" ]; then mv -f "$backup" "$AI_GRID_PROFILE_FILE"; else rm -f "$AI_GRID_PROFILE_FILE"; fi
  load_custom_curve 1
  log "AI Grid: nie udało się zapisać overlay; przywrócono poprzednią siatkę."
  return 5
}

clear_ai_grid_override() {
  local backup="${AI_GRID_PROFILE_FILE}.bak.$$"
  [ -s "$AI_GRID_PROFILE_FILE" ] && cp -f "$AI_GRID_PROFILE_FILE" "$backup" 2>/dev/null || true
  python3 "$AI_COOLING_SCRIPT" clear-grid --profile "$AI_GRID_PROFILE_FILE" >/dev/null 2>&1 || return 1
  load_custom_curve 1
  if write_overlay_profile custom1; then
    rm -f "$backup" 2>/dev/null || true
    ha_publish_curve_editor_state || true
    printf '%s\n' "${EPOCHREALTIME:-$(date +%s)}" > "$CONFIG_UI_RELOAD_FILE" 2>/dev/null || true
    log "AI Grid: przywrócono automatyczną geometrię krzywej z konfiguracji aplikacji."
    return 0
  fi
  [ -s "$backup" ] && mv -f "$backup" "$AI_GRID_PROFILE_FILE"
  load_custom_curve 1
  return 1
}

fan_calibration_file_valid() {
  local file="$1"
  [ -s "$file" ] || return 1
  jq -e 'type == "object"' "$file" >/dev/null 2>&1
}

fan_calibration_ready_file_valid() {
  local file="$1"
  fan_calibration_file_valid "$file" || return 1
  jq -e '.state == "ready" and (.min_safe_pwm_percent|type)=="number" and (.min_safe_pwm_percent >= 1 and .min_safe_pwm_percent <= 100) and (.rpm_map|type)=="array" and ((.rpm_map|length) > 0)' "$file" >/dev/null 2>&1
}

fan_calibration_sync_mirror() {
  local tmp
  fan_calibration_file_valid "$FAN_CALIBRATION_STATE_FILE" || return 1
  mkdir -p "$(dirname "$FAN_CALIBRATION_MIRROR_FILE")" 2>/dev/null || return 1
  tmp="${FAN_CALIBRATION_MIRROR_FILE}.tmp.$$"
  cp -f "$FAN_CALIBRATION_STATE_FILE" "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$FAN_CALIBRATION_MIRROR_FILE" 2>/dev/null || { rm -f "$tmp"; return 1; }
}

fan_calibration_init_storage() {
  local source="" state=""
  mkdir -p "$(dirname "$FAN_CALIBRATION_STATE_FILE")" "$(dirname "$FAN_CALIBRATION_MIRROR_FILE")" 2>/dev/null || true

  # First 2.2.0 start: migrate the full 2.1.x calibration map from the HA-config mirror.
  if ! fan_calibration_file_valid "$FAN_CALIBRATION_STATE_FILE"; then
    if fan_calibration_file_valid "$FAN_CALIBRATION_MIRROR_FILE"; then
      cp -f "$FAN_CALIBRATION_MIRROR_FILE" "$FAN_CALIBRATION_STATE_FILE" 2>/dev/null || true
      source="legacy_mirror"
    fi
  elif ! fan_calibration_ready_file_valid "$FAN_CALIBRATION_STATE_FILE" && fan_calibration_ready_file_valid "$FAN_CALIBRATION_MIRROR_FILE"; then
    # Prefer a complete historical map over an interrupted/non-ready primary state.
    cp -f "$FAN_CALIBRATION_MIRROR_FILE" "$FAN_CALIBRATION_STATE_FILE" 2>/dev/null || true
    source="ready_mirror_recovery"
  fi

  if fan_calibration_file_valid "$FAN_CALIBRATION_STATE_FILE"; then
    fan_calibration_sync_mirror >/dev/null 2>&1 || true
    state="$(jq -r '.state // "unknown"' "$FAN_CALIBRATION_STATE_FILE" 2>/dev/null || echo unknown)"
    if [ -n "$source" ]; then
      log "Fan Calibration: zmigrowano trwały stan kalibracji do /data (source=${source}; state=${state})."
    fi
    return 0
  fi
  return 1
}

fan_calibration_min_safe_pct() {
  local v=""
  if fan_calibration_ready_file_valid "$FAN_CALIBRATION_STATE_FILE"; then
    v="$(jq -r '.min_safe_pwm_percent // empty' "$FAN_CALIBRATION_STATE_FILE" 2>/dev/null || true)"
  fi
  case "$v" in ''|*[!0-9]*) v="$CURVE1_MIN_PWM_PCT" ;; esac
  [ "$v" -ge 1 ] 2>/dev/null || v="$CURVE1_MIN_PWM_PCT"
  [ "$v" -le 100 ] 2>/dev/null || v="$CURVE1_MIN_PWM_PCT"
  printf '%s\n' "$v"
}

fan_hwmon_tach_path() {
  local f
  # Prefer host sysfs; fall back to the container mirror for read-only telemetry.
  for f in /proc/1/root/sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input \
           /proc/1/root/sys/class/hwmon/hwmon*/fan1_input \
           /sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input \
           /sys/class/hwmon/hwmon*/fan1_input; do
    [ -r "$f" ] || continue
    printf '%s\n' "$f"
    return 0
  done
  return 1
}

fan_calibration_sample_rpm() {
  local tach="$1" count="${2:-$FAN_CALIBRATION_SAMPLE_COUNT}" i rpm sum=0 valid=0
  for i in $(seq 1 "$count"); do
    rpm="$(cat "$tach" 2>/dev/null || echo 0)"
    case "$rpm" in ''|*[!0-9]*) rpm=0 ;; esac
    sum=$((sum + rpm)); valid=$((valid + 1))
    [ "$i" -lt "$count" ] && sleep 1
  done
  [ "$valid" -gt 0 ] || { printf '0\n'; return 1; }
  printf '%s\n' "$((sum / valid))"
}

fan_calibration_publish_state() {
  [ -n "${SUPERVISOR_TOKEN:-}" ] || return 0
  local payload
  if fan_calibration_file_valid "$FAN_CALIBRATION_STATE_FILE"; then
    payload="$(jq -c '{state:(.state // "unknown"),attributes:{friendly_name:"SBC5 Fan Calibration",icon:"mdi:fan",grid_resolution_percent:(.grid_resolution_percent // 1),detected_start_pwm_percent:(.detected_start_pwm_percent // null),safe_start_pwm_percent:(.safe_start_pwm_percent // null),detected_min_run_pwm_percent:(.detected_min_run_pwm_percent // null),min_safe_pwm_percent:(.min_safe_pwm_percent // null),current_pwm_percent:(.current_pwm_percent // null),current_rpm:(.current_rpm // null),progress_percent:(.progress_percent // null),stage:(.stage // ""),map_points:((.rpm_map // [])|length),thermal_zone:(.thermal_zone // ""),original_policy:(.original_policy // ""),calibration_policy:(.calibration_policy // ""),thermal_ownership:(.thermal_ownership // ""),last_error:(.last_error // ""),updated_at:(.updated_at // ""),note:(.note // "")}}' "$FAN_CALIBRATION_STATE_FILE" 2>/dev/null || true)"
  else
    payload='{"state":"not_calibrated","attributes":{"friendly_name":"SBC5 Fan Calibration","icon":"mdi:fan","grid_resolution_percent":1,"map_points":0,"note":"Uruchom kalibrację po zastosowaniu profilu custom1 i restarcie hosta."}}'
  fi
  [ -n "$payload" ] || return 0
  curl -fsS -X POST -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" -d "$payload" \
    http://supervisor/core/api/states/sensor.sbc5_fan_calibration >/dev/null 2>&1 || true
}

fan_calibration_write_status() {
  local state="$1" error="${2:-}" note="${3:-}" extra="${4:-}" now tmp base='{}'
  [ -n "$extra" ] || extra='{}'
  now="$(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')"
  mkdir -p "$(dirname "$FAN_CALIBRATION_STATE_FILE")" 2>/dev/null || return 1
  if fan_calibration_file_valid "$FAN_CALIBRATION_STATE_FILE"; then
    base="$(jq -c '.' "$FAN_CALIBRATION_STATE_FILE" 2>/dev/null || echo '{}')"
  fi
  tmp="${FAN_CALIBRATION_STATE_FILE}.tmp.$$"
  jq -cn --arg state "$state" --arg err "$error" --arg note "$note" --arg now "$now" --argjson base "$base" --argjson extra "$extra" \
    '$base + $extra + {state:$state,last_error:$err,note:$note,grid_resolution_percent:1,updated_at:$now}' > "$tmp" 2>/dev/null || { rm -f "$tmp"; return 1; }
  jq -e 'type == "object"' "$tmp" >/dev/null 2>&1 || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$FAN_CALIBRATION_STATE_FILE" 2>/dev/null || { rm -f "$tmp"; return 1; }
  [ "$state" = "ready" ] && sync >/dev/null 2>&1 || true
  fan_calibration_sync_mirror >/dev/null 2>&1 || log "Fan Calibration: ostrzeżenie — nie udało się odświeżyć kopii diagnostycznej w /homeassistant."
  fan_calibration_publish_state || true
}

fan_calibration_verify_ready() {
  local expected_min_safe="$1" expected_points="$2"
  fan_calibration_ready_file_valid "$FAN_CALIBRATION_STATE_FILE" || return 1
  jq -e --argjson m "$expected_min_safe" --argjson n "$expected_points" \
    '.state == "ready" and .min_safe_pwm_percent == $m and ((.rpm_map // [])|length) == $n' \
    "$FAN_CALIBRATION_STATE_FILE" >/dev/null 2>&1
}

fan_calibration_force_runtime_sync() {
  fan_calibration_publish_state || true
  TELEMETRY_LAST_RELAY_PUBLISH=0
  publish_telemetry_snapshot >/dev/null 2>&1 || true
}

fan_calibration_find_bound_zone() {
  local dev="$1" dev_real zone link link_real
  dev_real="$(readlink -f "$dev" 2>/dev/null || true)"
  [ -n "$dev_real" ] || return 1
  for zone in /proc/1/root/sys/class/thermal/thermal_zone* /sys/class/thermal/thermal_zone*; do
    [ -d "$zone" ] || continue
    for link in "$zone"/cdev[0-9]*; do
      [ -L "$link" ] || continue
      link_real="$(readlink -f "$link" 2>/dev/null || true)"
      [ -n "$link_real" ] || continue
      if [ "$link_real" = "$dev_real" ]; then
        printf '%s\n' "$zone"
        return 0
      fi
    done
  done
  return 1
}

# v2.1.6 central arbitration for Active Cooler writes. Adaptive PWM and
# calibration share one owner marker. Prefer policy=user_space when the kernel
# exposes it; otherwise use thermal_zone mode=disabled, which is the standard
# sysfs mechanism for handing thermal control to a userspace controller.
# Every takeover stores the original policy/mode and restores it on release.
FAN_CONTROL_ZONE=""
FAN_CONTROL_ORIGINAL_POLICY=""
FAN_CONTROL_ORIGINAL_MODE=""
FAN_CONTROL_OWNERSHIP_METHOD=""
FAN_CONTROL_OWNER="kernel"

fan_control_owner_write() {
  local owner="$1" zone="$2" original_policy="$3" original_mode="$4" method="$5" dev="$6" now tmp
  now="$(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')"
  tmp="${FAN_CONTROL_OWNER_FILE}.tmp"
  jq -cn --arg owner "$owner" --arg zone "$zone" --arg original_policy "$original_policy" \
    --arg original_mode "$original_mode" --arg method "$method" --arg dev "$dev" --arg now "$now" --arg boot_id "$CURRENT_BOOT_ID" \
    '{owner:$owner,thermal_zone:$zone,original_policy:$original_policy,original_mode:$original_mode,ownership_method:$method,control_path:$dev,acquired_at:$now,boot_id:$boot_id}' \
    > "$tmp" 2>/dev/null || return 1
  mv -f "$tmp" "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || return 1
}

fan_control_take_thermal_ownership() {
  local owner="$1" dev="$2" zone old_policy old_mode available current_policy current_mode
  local existing_owner existing_zone existing_method method="" requested max_state
  FAN_CONTROL_ZONE=""; FAN_CONTROL_ORIGINAL_POLICY=""; FAN_CONTROL_ORIGINAL_MODE=""; FAN_CONTROL_OWNERSHIP_METHOD=""; FAN_CONTROL_OWNER="kernel"
  zone="$(fan_calibration_find_bound_zone "$dev" 2>/dev/null || true)"
  [ -n "$zone" ] || return 1

  old_policy="$(cat "$zone/policy" 2>/dev/null || true)"
  old_mode="$(cat "$zone/mode" 2>/dev/null || true)"

  if [ -s "$FAN_CONTROL_OWNER_FILE" ]; then
    existing_owner="$(jq -r '.owner // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
    existing_zone="$(jq -r '.thermal_zone // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
    existing_method="$(jq -r '.ownership_method // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
    if [ "$existing_owner" != "$owner" ] || [ "$existing_zone" != "$zone" ]; then
      return 3
    fi
    case "$existing_method" in
      user_space)
        current_policy="$(cat "$zone/policy" 2>/dev/null || true)"
        [ "$current_policy" = "user_space" ] || return 3
        ;;
      mode_disabled)
        current_mode="$(cat "$zone/mode" 2>/dev/null || true)"
        [ "$current_mode" = "disabled" ] || return 3
        ;;
      *) return 3 ;;
    esac
    FAN_CONTROL_ZONE="$zone"
    FAN_CONTROL_ORIGINAL_POLICY="$(jq -r '.original_policy // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
    FAN_CONTROL_ORIGINAL_MODE="$(jq -r '.original_mode // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
    FAN_CONTROL_OWNERSHIP_METHOD="$existing_method"
    FAN_CONTROL_OWNER="$owner"
    return 0
  fi

  # Rust canary recovery: after an app rebuild/rollback the host thermal zone may
  # remain in mode=disabled while the transient /data owner marker is missing.
  # When the canonical SBC5 namespace is COMPLETE and custom1 is already active,
  # adopt that orphaned userspace state instead of reporting ownership_failed_2.
  if [ "$old_mode" = "disabled" ] && [ -w "$zone/mode" ] && namespace_control_allowed; then
    requested="$(ha_requested_profile_code 2>/dev/null || echo factory)"
    max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"
    case "$max_state" in ''|*[!0-9]*) max_state=0 ;; esac
    if [ "$requested" = "custom1" ] && [ "$max_state" -ge 100 ] 2>/dev/null && [ -w "$dev/cur_state" ]; then
      method="mode_disabled"
      fan_control_owner_write "$owner" "$zone" "$old_policy" "enabled" "$method" "$dev" || return 1
      FAN_CONTROL_ZONE="$zone"; FAN_CONTROL_ORIGINAL_POLICY="$old_policy"; FAN_CONTROL_ORIGINAL_MODE="enabled"
      FAN_CONTROL_OWNERSHIP_METHOD="$method"; FAN_CONTROL_OWNER="$owner"
      log "Fan Control: odzyskano osierocone przejęcie; owner=${owner}; thermal_zone=${zone}; takeover=mode_disabled; mode already disabled; marker odtworzony."
      return 0
    fi
  fi

  # Preferred path: a true userspace thermal governor, when compiled in.
  available="$(cat "$zone/available_policies" 2>/dev/null || true)"
  if [ -r "$zone/policy" ] && [ -w "$zone/policy" ]; then
    case " $available " in
      *" user_space "*)
        if [ -n "$old_policy" ] && [ "$old_policy" != "user_space" ]; then
          method="user_space"
          fan_control_owner_write "$owner" "$zone" "$old_policy" "$old_mode" "$method" "$dev" || return 1
          if printf 'user_space\n' > "$zone/policy" 2>/dev/null; then
            sleep 0.25
            current_policy="$(cat "$zone/policy" 2>/dev/null || true)"
            if [ "$current_policy" = "user_space" ]; then
              FAN_CONTROL_ZONE="$zone"; FAN_CONTROL_ORIGINAL_POLICY="$old_policy"; FAN_CONTROL_ORIGINAL_MODE="$old_mode"
              FAN_CONTROL_OWNERSHIP_METHOD="$method"; FAN_CONTROL_OWNER="$owner"
              log "Fan Control: owner=${owner}; thermal_zone=${zone}; takeover=user_space; policy ${old_policy}->user_space."
              return 0
            fi
          fi
          rm -f "$FAN_CONTROL_OWNER_FILE"
        fi
        ;;
    esac
  fi

  # HA OS may compile no user_space governor. In that case the thermal sysfs
  # API exposes mode=disabled specifically so a userspace controller can take
  # charge. Only use it when mode is writable and was enabled.
  if [ -r "$zone/mode" ] && [ -w "$zone/mode" ] && [ "$old_mode" = "enabled" ]; then
    method="mode_disabled"
    fan_control_owner_write "$owner" "$zone" "$old_policy" "$old_mode" "$method" "$dev" || return 1
    if printf 'disabled\n' > "$zone/mode" 2>/dev/null; then
      sleep 0.25
      current_mode="$(cat "$zone/mode" 2>/dev/null || true)"
      if [ "$current_mode" = "disabled" ]; then
        FAN_CONTROL_ZONE="$zone"; FAN_CONTROL_ORIGINAL_POLICY="$old_policy"; FAN_CONTROL_ORIGINAL_MODE="$old_mode"
        FAN_CONTROL_OWNERSHIP_METHOD="$method"; FAN_CONTROL_OWNER="$owner"
        log "Fan Control: owner=${owner}; thermal_zone=${zone}; takeover=mode_disabled; mode ${old_mode}->disabled; policy=${old_policy:-unknown}."
        return 0
      fi
    fi
    rm -f "$FAN_CONTROL_OWNER_FILE"
  fi

  # 2 = no supported exclusive-control mechanism on this kernel/zone.
  return 2
}

# v2.6.9 seamless update handoff -------------------------------------------------
# A local-app rebuild used to terminate the Adaptive PWM process, restore the
# kernel thermal governor and immediately drop the fan to the factory step.  When
# the rebuild is intentional and stays on the same host boot, keep the thermal
# ownership and last safe cur_state until the new container validates and adopts
# the existing owner marker.  Arbitrary stops/failures still release to kernel.
fan_control_owner_state_adoptable() {
  local expected_owner="${1:-adaptive}" owner zone method current_policy current_mode dev max_state requested
  [ -s "$FAN_CONTROL_OWNER_FILE" ] || return 1
  owner="$(jq -r '.owner // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
  [ "$owner" = "$expected_owner" ] || return 1
  requested="$(ha_requested_profile_code 2>/dev/null || echo factory)"
  [ "$requested" = "custom1" ] || return 1
  dev="$(adaptive_pwm_find_device 2>/dev/null || true)"
  [ -n "$dev" ] || return 1
  max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"
  case "$max_state" in ''|*[!0-9]*) max_state=0 ;; esac
  [ "$max_state" -ge 100 ] 2>/dev/null || return 1
  [ -w "$dev/cur_state" ] || return 1
  zone="$(jq -r '.thermal_zone // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
  method="$(jq -r '.ownership_method // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
  [ -n "$zone" ] && [ -d "$zone" ] || return 1
  case "$method" in
    user_space)
      current_policy="$(cat "$zone/policy" 2>/dev/null || true)"
      [ "$current_policy" = "user_space" ] || return 1
      ;;
    mode_disabled)
      current_mode="$(cat "$zone/mode" 2>/dev/null || true)"
      [ "$current_mode" = "disabled" ] || return 1
      ;;
    *) return 1 ;;
  esac
  return 0
}

fan_control_handoff_marker_valid() {
  local boot created now age reason
  [ -s "$FAN_CONTROL_HANDOFF_FILE" ] || return 1
  boot="$(jq -r '.boot_id // empty' "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true)"
  reason="$(jq -r '.reason // empty' "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true)"
  created="$(jq -r '.created_epoch // 0' "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || echo 0)"
  case "$created" in ''|*[!0-9]*) created=0 ;; esac
  now="$(date +%s)"; age=$((now-created))
  [ "$boot" = "$CURRENT_BOOT_ID" ] || return 1
  [ "$reason" = "local_update_rebuild" ] || return 1
  [ "$created" -gt 0 ] 2>/dev/null || return 1
  [ "$age" -ge 0 ] 2>/dev/null || return 1
  [ "$age" -le "$FAN_CONTROL_HANDOFF_MAX_AGE_SECONDS" ] 2>/dev/null || return 1
  fan_control_owner_state_adoptable adaptive
}

fan_control_prepare_update_handoff() {
  local target_version="${1:-unknown}" dev state now tmp method zone
  rm -f "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true
  fan_control_owner_state_adoptable adaptive || {
    log "Fan Control: update handoff pominięty — Adaptive PWM nie ma aktywnego, bezpiecznego ownera 1%."
    return 1
  }
  dev="$(adaptive_pwm_find_device 2>/dev/null || true)"
  state="$(cat "$dev/cur_state" 2>/dev/null || echo 0)"; case "$state" in ''|*[!0-9]*) state=0 ;; esac
  method="$(jq -r '.ownership_method // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
  zone="$(jq -r '.thermal_zone // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
  now="$(date +%s)"; tmp="${FAN_CONTROL_HANDOFF_FILE}.tmp.$$"
  jq -cn --arg reason "local_update_rebuild" --arg boot_id "$CURRENT_BOOT_ID" --arg from "$APP_VERSION" --arg to "$target_version" \
    --arg method "$method" --arg zone "$zone" --argjson created "$now" --argjson state "$state" \
    '{schema:1,reason:$reason,boot_id:$boot_id,from_version:$from,to_version:$to,ownership_method:$method,thermal_zone:$zone,created_epoch:$created,preserved_state:$state}' \
    > "$tmp" 2>/dev/null || return 1
  mv -f "$tmp" "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || return 1
  log "Fan Control: przygotowano seamless handoff ${APP_VERSION}->${target_version}; zachowuję Adaptive PWM i cur_state=${state}/100 podczas rebuild."
  return 0
}

fan_control_shutdown_or_handoff() {
  local reason="${1:-controller_exit}"
  if fan_control_handoff_marker_valid; then
    log "Fan Control: ${reason} podczas planowanego rebuild — ownership Adaptive PWM pozostaje aktywny do przejęcia przez nową wersję."
    return 0
  fi
  rm -f "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true
  fan_control_release_thermal_ownership adaptive "$reason" >/dev/null 2>&1 || true
}

fan_control_release_thermal_ownership() {
  local expected_owner="${1:-}" reason="${2:-release}" owner zone original_policy original_mode method current
  [ -s "$FAN_CONTROL_OWNER_FILE" ] || {
    FAN_CONTROL_ZONE=""; FAN_CONTROL_ORIGINAL_POLICY=""; FAN_CONTROL_ORIGINAL_MODE=""; FAN_CONTROL_OWNERSHIP_METHOD=""; FAN_CONTROL_OWNER="kernel"
    return 0
  }
  owner="$(jq -r '.owner // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
  zone="$(jq -r '.thermal_zone // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
  original_policy="$(jq -r '.original_policy // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
  original_mode="$(jq -r '.original_mode // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
  method="$(jq -r '.ownership_method // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
  if [ -n "$expected_owner" ] && [ "$owner" != "$expected_owner" ]; then
    return 3
  fi

  case "$method" in
    user_space)
      if [ -n "$zone" ] && [ -r "$zone/policy" ]; then
        current="$(cat "$zone/policy" 2>/dev/null || true)"
        if [ "$current" = "user_space" ] && [ -n "$original_policy" ] && [ "$original_policy" != "user_space" ]; then
          [ -w "$zone/policy" ] || return 1
          printf '%s\n' "$original_policy" > "$zone/policy" 2>/dev/null || return 1
          sleep 0.2
          current="$(cat "$zone/policy" 2>/dev/null || true)"
          [ "$current" = "$original_policy" ] || return 1
        elif [ -n "$original_policy" ] && [ "$current" != "$original_policy" ]; then
          log "Fan Control: owner=${owner}; polityka zmieniona zewnętrznie (${current}); nie nadpisuję jej."
        fi
      fi
      ;;
    mode_disabled)
      if [ -n "$zone" ] && [ -r "$zone/mode" ]; then
        current="$(cat "$zone/mode" 2>/dev/null || true)"
        if [ "$current" = "disabled" ] && [ -n "$original_mode" ]; then
          [ -w "$zone/mode" ] || return 1
          printf '%s\n' "$original_mode" > "$zone/mode" 2>/dev/null || return 1
          sleep 0.2
          current="$(cat "$zone/mode" 2>/dev/null || true)"
          [ "$current" = "$original_mode" ] || return 1
        elif [ -n "$original_mode" ] && [ "$current" != "$original_mode" ]; then
          log "Fan Control: owner=${owner}; mode strefy zmieniony zewnętrznie (${current}); nie nadpisuję go."
        fi
      fi
      ;;
    "") ;;
    *) log "Fan Control: nieznana metoda ownera '${method}', marker zostanie zwolniony bez zmian sysfs." ;;
  esac

  rm -f "$FAN_CONTROL_OWNER_FILE"
  FAN_CONTROL_ZONE=""; FAN_CONTROL_ORIGINAL_POLICY=""; FAN_CONTROL_ORIGINAL_MODE=""; FAN_CONTROL_OWNERSHIP_METHOD=""; FAN_CONTROL_OWNER="kernel"
  log "Fan Control: owner=${owner:-unknown} zwolniony; reason=${reason}; method=${method:-none}; sterowanie wróciło do kernela."
  return 0
}

fan_control_recover_stale_ownership() {
  local owner zone method dev max_state state
  [ -s "$FAN_CONTROL_OWNER_FILE" ] || { rm -f "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true; return 0; }
  owner="$(jq -r '.owner // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"

  if fan_control_handoff_marker_valid; then
    zone="$(jq -r '.thermal_zone // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
    method="$(jq -r '.ownership_method // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
    FAN_CONTROL_ZONE="$zone"
    FAN_CONTROL_ORIGINAL_POLICY="$(jq -r '.original_policy // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
    FAN_CONTROL_ORIGINAL_MODE="$(jq -r '.original_mode // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
    FAN_CONTROL_OWNERSHIP_METHOD="$method"
    FAN_CONTROL_OWNER="adaptive"
    dev="$(adaptive_pwm_find_device 2>/dev/null || true)"
    max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"
    state="$(cat "$dev/cur_state" 2>/dev/null || echo 0)"
    log "Fan Control: seamless handoff wykryty po rebuild; zachowano owner=adaptive, method=${method}, cur_state=${state}/${max_state}. Nowy kontroler przejmie stan bez powrotu do kernela."
    return 0
  fi

  if [ -s "$FAN_CONTROL_HANDOFF_FILE" ]; then
    log "Fan Control: odrzucono nieaktualny/niebezpieczny marker handoff; przywracam kontrolę kernela."
    rm -f "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true
  fi
  if fan_control_release_thermal_ownership "$owner" startup_recovery; then
    log "Fan Control: odzyskano pozostawione sterowanie po poprzednim uruchomieniu (owner=${owner:-unknown})."
    return 0
  fi
  log "Fan Control: OSTRZEŻENIE — nie udało się odzyskać pozostawionego thermal owner; Adaptive PWM nie przejmie sterowania."
  return 1
}

fan_calibration_set_and_verify() {
  local dev="$1" requested="$2" settle="${3:-$FAN_CALIBRATION_SETTLE_SECONDS}" attempt actual
  for attempt in 1 2 3; do
    printf '%s\n' "$requested" > "$dev/cur_state" 2>/dev/null || return 1
    sleep "$settle"
    actual="$(cat "$dev/cur_state" 2>/dev/null || echo -1)"
    case "$actual" in ''|*[!0-9]*) actual=-1 ;; esac
    [ "$actual" -eq "$requested" ] 2>/dev/null && return 0
    # The thermal governor may update cur_state between writes. Re-apply the
    # requested level so the tachometer sample reflects the requested PWM.
    sleep 0.2
  done
  return 2
}

fan_calibration_progress() {
  local stage="$1" p="$2" rpm="${3:-0}" progress="${4:-0}" note="$5" extra
  extra="$(jq -cn --arg stage "$stage" --argjson p "$p" --argjson rpm "$rpm" --argjson progress "$progress" \
    '{stage:$stage,current_pwm_percent:$p,current_rpm:$rpm,progress_percent:$progress}')"
  fan_calibration_write_status running "" "$note" "$extra"
}

run_fan_calibration() {
  load_options
  local dev tach zone="" original_policy="" original_mode="" ownership_method="" takeover=false max_state current original temp p rpm progress=0 detected_start=0 safe_start=0 probe=0 lowest=0 min_safe=0 raw map='[]' aborted=false abort_reason="" now extra takeover_rc=0
  dev="$(adaptive_pwm_find_device 2>/dev/null || true)"
  tach="$(fan_hwmon_tach_path 2>/dev/null || true)"
  if [ -z "$dev" ] || [ -z "$tach" ]; then
    log "Fan Calibration: brak backendu (cooling_device=${dev:-brak}, tach=${tach:-brak})."
    fan_calibration_write_status unsupported no_fan_or_tach "Nie znaleziono cooling_device lub tachometru Active Cooler." '{}'
    return 1
  fi
  log "Fan Calibration: backend thermal=${dev}; tach=${tach}."
  max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"
  case "$max_state" in ''|*[!0-9]*) max_state=0 ;; esac
  if [ "$max_state" -lt 100 ] 2>/dev/null; then
    log "Fan Calibration: max_state=${max_state} — siatka 1% nieaktywna; zastosuj custom1 i wykonaj pełny restart hosta."
    extra="$(jq -cn --argjson max "$max_state" '{kernel_max_state:$max}')"
    fan_calibration_write_status restart_required one_percent_overlay_not_active "Siatka PWM 1% nie jest aktywna (max_state=${max_state}). Zastosuj custom1 i wykonaj pełny restart hosta." "$extra"
    return 2
  fi
  if [ ! -w "$dev/cur_state" ]; then
    extra="$(jq -cn --arg path "$dev/cur_state" '{control_path:$path}')"
    log "Fan Calibration: host cur_state nadal nie jest zapisywalny: $dev/cur_state"
    fan_calibration_write_status unsupported cur_state_not_writable "Hostowy interfejs thermal cur_state nie jest zapisywalny." "$extra"
    return 1
  fi
  log "Fan Calibration: sterowanie RW potwierdzone; max_state=${max_state}."
  temp="$(read_cpu_temp_millideg 2>/dev/null || echo 0)"
  case "$temp" in ''|*[!0-9-]*) temp=0 ;; esac
  if [ "$temp" -ge "$FAN_CALIBRATION_MAX_START_TEMP_MILLI" ] 2>/dev/null; then
    extra="$(jq -cn --argjson t "$temp" '{temperature_millideg:$t}')"
    fan_calibration_write_status error cpu_too_hot_to_start "Kalibracja nie wystartowała — CPU musi mieć mniej niż 60°C." "$extra"
    return 1
  fi
  original="$(cat "$dev/cur_state" 2>/dev/null || echo 0)"
  case "$original" in ''|*[!0-9]*) original=0 ;; esac

  # v2.1.6: calibration and Adaptive PWM share one explicit owner. Lock first,
  # then hand Adaptive PWM back before calibration takes exclusive control via
  # user_space when available or thermal-zone mode=disabled on HA OS kernels.
  : > "$FAN_CALIBRATION_LOCK_FILE"
  fan_control_release_thermal_ownership adaptive calibration_handoff >/dev/null 2>&1 || true
  takeover_rc=0
  fan_control_take_thermal_ownership calibration "$dev" || takeover_rc=$?
  if [ "$takeover_rc" -ne 0 ] 2>/dev/null; then
    zone="$(fan_calibration_find_bound_zone "$dev" 2>/dev/null || true)"
    if [ "$takeover_rc" -eq 2 ] 2>/dev/null; then abort_reason=exclusive_control_unavailable
    elif [ "$takeover_rc" -eq 3 ] 2>/dev/null; then abort_reason=fan_control_busy
    else abort_reason=thermal_takeover_failed; fi
    extra="$(jq -cn --arg zone "$zone" --arg available "$(cat "$zone/available_policies" 2>/dev/null || true)" --arg mode "$(cat "$zone/mode" 2>/dev/null || true)" '{thermal_zone:$zone,available_policies:$available,thermal_mode:$mode}')"
    log "Fan Calibration: nie mogę przejąć wyłącznego sterowania dla ${zone:-unknown} (${abort_reason})."
    fan_calibration_write_status unsupported "$abort_reason" "Kalibracja wymaga wyłącznego sterowania strefą, aby kernel nie nadpisywał poziomów 1%." "$extra"
    rm -f "$FAN_CALIBRATION_LOCK_FILE"
    return 1
  fi
  zone="$FAN_CONTROL_ZONE"
  original_policy="$FAN_CONTROL_ORIGINAL_POLICY"
  original_mode="$FAN_CONTROL_ORIGINAL_MODE"
  ownership_method="$FAN_CONTROL_OWNERSHIP_METHOD"
  takeover=true
  log "Fan Calibration: owner=calibration; zone=${zone}; method=${ownership_method}; original_policy=${original_policy:-unknown}; original_mode=${original_mode:-unknown}."

  fan_calibration_write_status running start_detection "Kalibracja Active Cooler: wykrywanie progu startu co 1% PWM." \
    "$(jq -cn --argjson original "$original" --arg zone "$zone" --arg old "$original_policy" --arg mode "$original_mode" --arg method "$ownership_method" '{original_state:$original,rpm_map:[],detected_start_pwm_percent:null,safe_start_pwm_percent:null,detected_min_run_pwm_percent:null,min_safe_pwm_percent:null,thermal_zone:$zone,original_policy:$old,original_mode:$mode,calibration_policy:$method,thermal_ownership:"calibration"}')"

  printf '0\n' > "$dev/cur_state" 2>/dev/null || true
  sleep 1
  for p in $(seq "$FAN_CALIBRATION_MIN_TEST_PCT" "$FAN_CALIBRATION_MAX_START_PCT"); do
    temp="$(read_cpu_temp_millideg 2>/dev/null || echo 0)"; case "$temp" in ''|*[!0-9-]*) temp=0 ;; esac
    if [ "$temp" -ge "$FAN_CALIBRATION_MAX_TEMP_MILLI" ] 2>/dev/null; then aborted=true; abort_reason=temperature_limit; break; fi
    if ! fan_calibration_set_and_verify "$dev" "$p" "$FAN_CALIBRATION_SETTLE_SECONDS"; then
      aborted=true; abort_reason=state_not_held; break
    fi
    rpm="$(fan_calibration_sample_rpm "$tach" 2 2>/dev/null || echo 0)"
    if [ $((p % 5)) -eq 0 ] 2>/dev/null || [ "$p" -eq "$FAN_CALIBRATION_MIN_TEST_PCT" ] 2>/dev/null; then
      log "Fan Calibration: start scan ${p}% -> ${rpm} RPM."
      fan_calibration_progress start_detection "$p" "$rpm" "$(( (p - FAN_CALIBRATION_MIN_TEST_PCT) * 25 / (FAN_CALIBRATION_MAX_START_PCT - FAN_CALIBRATION_MIN_TEST_PCT + 1) ))" "Wykrywanie progu startu wentylatora."
    fi
    if [ "$rpm" -ge "$FAN_CALIBRATION_SPIN_RPM" ] 2>/dev/null; then detected_start="$p"; break; fi
  done

  if [ "$aborted" = "false" ] && [ "$detected_start" -le 0 ] 2>/dev/null; then aborted=true; abort_reason=no_start_detected; fi
  if [ "$aborted" = "false" ]; then
    safe_start=$((detected_start + FAN_CALIBRATION_START_MARGIN_PCT)); [ "$safe_start" -gt 100 ] && safe_start=100
    probe=$((safe_start + 5)); [ "$probe" -gt 70 ] && probe=70
    fan_calibration_set_and_verify "$dev" "$probe" 2 || { aborted=true; abort_reason=state_not_held; }
  fi

  if [ "$aborted" = "false" ]; then
    lowest="$probe"
    for p in $(seq "$probe" -1 "$FAN_CALIBRATION_MIN_TEST_PCT"); do
      temp="$(read_cpu_temp_millideg 2>/dev/null || echo 0)"; case "$temp" in ''|*[!0-9-]*) temp=0 ;; esac
      if [ "$temp" -ge "$FAN_CALIBRATION_MAX_TEMP_MILLI" ] 2>/dev/null; then aborted=true; abort_reason=temperature_limit; break; fi
      if ! fan_calibration_set_and_verify "$dev" "$p" "$FAN_CALIBRATION_SETTLE_SECONDS"; then
        aborted=true; abort_reason=state_not_held; break
      fi
      rpm="$(fan_calibration_sample_rpm "$tach" 2 2>/dev/null || echo 0)"
      if [ $((p % 5)) -eq 0 ] 2>/dev/null || [ "$p" -eq "$probe" ] 2>/dev/null; then
        log "Fan Calibration: run floor scan ${p}% -> ${rpm} RPM."
        fan_calibration_progress run_floor "$p" "$rpm" 35 "Wykrywanie minimalnej stabilnej pracy wentylatora."
      fi
      if [ "$rpm" -ge "$FAN_CALIBRATION_SPIN_RPM" ] 2>/dev/null; then lowest="$p"; else break; fi
    done
    min_safe=$((lowest + FAN_CALIBRATION_RUN_MARGIN_PCT)); [ "$min_safe" -gt 100 ] && min_safe=100
  fi

  if [ "$aborted" = "false" ]; then
    fan_calibration_write_status running map_generation "Budowanie mapy RPM dla każdego 1% PWM od minimalnego bezpiecznego poziomu do 100%." \
      "$(jq -cn --argjson start "$detected_start" --argjson safe_start "$safe_start" --argjson run "$lowest" --argjson min_safe "$min_safe" --arg zone "$zone" --arg old "$original_policy" --arg mode "$original_mode" --arg method "$ownership_method" '{detected_start_pwm_percent:$start,safe_start_pwm_percent:$safe_start,detected_min_run_pwm_percent:$run,min_safe_pwm_percent:$min_safe,thermal_zone:$zone,original_policy:$old,original_mode:$mode,calibration_policy:$method,thermal_ownership:"calibration"}')"
    for p in $(seq "$min_safe" 100); do
      temp="$(read_cpu_temp_millideg 2>/dev/null || echo 0)"; case "$temp" in ''|*[!0-9-]*) temp=0 ;; esac
      if [ "$temp" -ge "$FAN_CALIBRATION_MAX_TEMP_MILLI" ] 2>/dev/null; then aborted=true; abort_reason=temperature_limit; break; fi
      if ! fan_calibration_set_and_verify "$dev" "$p" "$FAN_CALIBRATION_SETTLE_SECONDS"; then
        aborted=true; abort_reason=state_not_held; break
      fi
      rpm="$(fan_calibration_sample_rpm "$tach" "$FAN_CALIBRATION_SAMPLE_COUNT" 2>/dev/null || echo 0)"
      temp="$(read_cpu_temp_millideg 2>/dev/null || echo 0)"; case "$temp" in ''|*[!0-9-]*) temp=0 ;; esac
      raw=$(( (p * 255 + 50) / 100 ))
      map="$(jq -c --argjson p "$p" --argjson raw "$raw" --argjson rpm "$rpm" --argjson temp "$temp" '. + [{pwm_percent:$p,pwm_raw:$raw,rpm:$rpm,temperature_millideg:$temp}]' <<<"$map")"
      if [ $((p % 5)) -eq 0 ] 2>/dev/null || [ "$p" -eq "$min_safe" ] 2>/dev/null || [ "$p" -eq 100 ] 2>/dev/null; then
        progress=$((40 + (p - min_safe) * 60 / (100 - min_safe + 1)))
        [ "$progress" -gt 99 ] && progress=99
        log "Fan Calibration: mapa ${p}% -> ${rpm} RPM; postęp=${progress}%."
        fan_calibration_progress map_generation "$p" "$rpm" "$progress" "Budowanie mapy RPM 1% PWM."
      fi
    done
  fi

  if [ "$aborted" = "true" ]; then
    printf '100\n' > "$dev/cur_state" 2>/dev/null || true
    if [ "$takeover" = "true" ]; then
      if fan_control_release_thermal_ownership calibration calibration_abort; then
        log "Fan Calibration: thermal owner zwolniony; method=${ownership_method}; stan kernela przywrócony."
      else
        log "Fan Calibration: OSTRZEŻENIE — nie udało się zwolnić thermal owner calibration."
      fi
    fi
    extra="$(jq -cn --arg reason "$abort_reason" --argjson start "$detected_start" --argjson safe_start "$safe_start" --argjson run "$lowest" --argjson min_safe "$min_safe" --argjson map "$map" --arg zone "$zone" --arg old "$original_policy" --arg mode "$original_mode" --arg method "$ownership_method" '{abort_reason:$reason,detected_start_pwm_percent:$start,safe_start_pwm_percent:$safe_start,detected_min_run_pwm_percent:$run,min_safe_pwm_percent:$min_safe,rpm_map:$map,thermal_zone:$zone,original_policy:$old,original_mode:$mode,calibration_policy:$method,thermal_ownership:"restored"}')"
    fan_calibration_write_status error "$abort_reason" "Kalibracja przerwana; przywrócono sterowanie kernela." "$extra"
    rm -f "$FAN_CALIBRATION_LOCK_FILE"
    log "Fan Calibration: przerwano (${abort_reason}); thermal owner przywrócony."
    return 1
  fi

  # Restore the original fan state while the application still owns the cdev,
  # then hand the thermal zone back to its original kernel policy/mode.
  printf '%s\n' "$original" > "$dev/cur_state" 2>/dev/null || true
  if [ "$takeover" = "true" ]; then
    if fan_control_release_thermal_ownership calibration calibration_complete; then
      log "Fan Calibration: thermal owner zwolniony; method=${ownership_method}; stan kernela przywrócony."
    else
      printf '100\n' > "$dev/cur_state" 2>/dev/null || true
      extra="$(jq -cn --arg zone "$zone" --arg old "$original_policy" --arg mode "$original_mode" --arg method "$ownership_method" '{thermal_zone:$zone,original_policy:$old,original_mode:$mode,calibration_policy:$method,thermal_ownership:"restore_failed"}')"
      fan_calibration_write_status error thermal_control_restore_failed "Mapa została zmierzona, ale nie udało się przywrócić oryginalnego sterowania thermal kernela; zażądano 100% chłodzenia." "$extra"
      rm -f "$FAN_CALIBRATION_LOCK_FILE"
      log "Fan Calibration: BŁĄD przywracania thermal owner; ustawiono 100%."
      return 1
    fi
  fi
  now="$(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S')"
  extra="$(jq -cn --argjson start "$detected_start" --argjson safe_start "$safe_start" --argjson run "$lowest" --argjson min_safe "$min_safe" --argjson original "$original" --argjson map "$map" --arg now "$now" --arg zone "$zone" --arg old "$original_policy" --arg mode "$original_mode" --arg method "$ownership_method" '{detected_start_pwm_percent:$start,safe_start_pwm_percent:$safe_start,detected_min_run_pwm_percent:$run,min_safe_pwm_percent:$min_safe,original_state:$original,rpm_map:$map,calibrated_at:$now,stage:"complete",progress_percent:100,current_pwm_percent:$original,thermal_zone:$zone,original_policy:$old,original_mode:$mode,calibration_policy:$method,thermal_ownership:"restored"}')"
  local map_points
  map_points="$(jq 'length' <<<"$map" 2>/dev/null || echo 0)"
  if ! fan_calibration_write_status ready "" "Kalibracja zakończona. Mapa 1% PWM jest gotowa; sterowanie thermal oddano z powrotem kernelowi." "$extra"; then
    rm -f "$FAN_CALIBRATION_LOCK_FILE"
    log "Fan Calibration: BŁĄD zapisu trwałego stanu kalibracji; regulator pozostanie przy bezpiecznym fallbacku."
    return 1
  fi
  if ! fan_calibration_verify_ready "$min_safe" "$map_points"; then
    rm -f "$FAN_CALIBRATION_LOCK_FILE"
    log "Fan Calibration: BŁĄD weryfikacji trwałego zapisu (oczekiwano min_safe=${min_safe}%, map=${map_points} pkt)."
    return 1
  fi
  # Keep the lock until /data, HA-config mirror and both HA runtime views are synchronized.
  fan_calibration_force_runtime_sync
  rm -f "$FAN_CALIBRATION_LOCK_FILE"
  log "Fan Calibration: zweryfikowano trwały zapis /data; min_safe=${min_safe}%, map=${map_points} pkt; mirror i HA runtime zsynchronizowane."
  log "Fan Calibration: gotowe; start=${detected_start}%, safe_start=${safe_start}%, min_run=${lowest}%, min_safe=${min_safe}%, map=${map_points} pkt; method=${ownership_method}; kernel thermal przywrócony."
  return 0
}

# v2.1.7: derive a temperature-appropriate re-entry state from the active custom1
# curve. This is used after calibration so the controller does not inherit the
# pre-calibration PWM after the fan has just spent time at high test levels.
adaptive_pwm_curve_state_for_temp() {
  local temp_milli="$1" max_state="${2:-100}" i t1 t2 s1 s2 state num den
  # CUSTOM_T/CUSTOM_PWM are cached by the controller and refreshed on config token changes.
  s1=$(( (CUSTOM_PWM[1] * 100 + 127) / 255 ))
  if [ "$temp_milli" -le "${CUSTOM_T[1]}" ] 2>/dev/null; then
    state="$s1"
  else
    state=-1
    for i in $(seq 1 14); do
      t1="${CUSTOM_T[$i]}"; t2="${CUSTOM_T[$((i+1))]}"
      if [ "$temp_milli" -le "$t2" ] 2>/dev/null; then
        s1=$(( (CUSTOM_PWM[$i] * 100 + 127) / 255 ))
        s2=$(( (CUSTOM_PWM[$((i+1))] * 100 + 127) / 255 ))
        den=$((t2 - t1))
        if [ "$den" -le 0 ] 2>/dev/null; then
          state="$s1"
        else
          num=$(( (temp_milli - t1) * (s2 - s1) ))
          state=$(( s1 + (num + den / 2) / den ))
        fi
        break
      fi
    done
    if [ "$state" -lt 0 ] 2>/dev/null; then
      state=$(( (CUSTOM_PWM[15] * 100 + 127) / 255 ))
    fi
  fi
  [ "$state" -lt 0 ] 2>/dev/null && state=0
  [ "$state" -gt "$max_state" ] 2>/dev/null && state="$max_state"
  printf '%s\n' "$state"
}

ai_cooling_mark_disabled() {
  mkdir -p "$(dirname "$AI_COOLING_STATUS_FILE")" "$(dirname "$AI_COOLING_MIRROR_FILE")" 2>/dev/null || true
  local now tmp payload
  now="${EPOCHREALTIME%%.*}"
  payload="$(jq -cn --arg mode "${AI_COOLING_EFFECTIVE_MODE:-disabled}" --argjson epoch "${now:-0}" '{schema:5,state:"disabled",mode:$mode,reason:"disabled_or_incompatible_mode",confidence_percent:0,observations_total:0,qualified_samples_total:0,bin_observations:0,bin_qualified_samples:0,prediction_pwm_percent:null,correction_pwm_percent:0,updated_epoch:$epoch}' 2>/dev/null || echo '{"schema":5,"state":"disabled"}')"
  tmp="${AI_COOLING_STATUS_FILE}.tmp.$$"; printf '%s\n' "$payload" > "$tmp" 2>/dev/null && mv -f "$tmp" "$AI_COOLING_STATUS_FILE" 2>/dev/null || true
  tmp="${AI_COOLING_MIRROR_FILE}.tmp.$$"; printf '%s\n' "$payload" > "$tmp" 2>/dev/null && mv -f "$tmp" "$AI_COOLING_MIRROR_FILE" 2>/dev/null || true
}

ai_cooling_mark_paused() {
  local reason="${1:-adaptive_not_active}" now tmp payload base='{}'
  [ "${AI_COOLING_EFFECTIVE_MODE:-disabled}" = "disabled" ] && { ai_cooling_mark_disabled; return 0; }
  mkdir -p "$(dirname "$AI_COOLING_STATUS_FILE")" "$(dirname "$AI_COOLING_MIRROR_FILE")" 2>/dev/null || true
  now="${EPOCHREALTIME%%.*}"
  if [ -s "$AI_COOLING_STATUS_FILE" ] && jq -e 'type=="object"' "$AI_COOLING_STATUS_FILE" >/dev/null 2>&1; then
    base="$(cat "$AI_COOLING_STATUS_FILE" 2>/dev/null || echo '{}')"
  fi
  payload="$(jq -c --arg reason "$reason" --arg mode "${AI_COOLING_EFFECTIVE_MODE:-learning}" --argjson epoch "${now:-0}" '
    . + {schema:5,state:"paused",mode:$mode,reason:$reason,correction_pwm_percent:0,updated_epoch:$epoch}
  ' <<<"$base" 2>/dev/null || echo '{"schema":5,"state":"paused","reason":"adaptive_not_active","correction_pwm_percent":0}')"
  tmp="${AI_COOLING_STATUS_FILE}.tmp.$$"; printf '%s\n' "$payload" > "$tmp" 2>/dev/null && mv -f "$tmp" "$AI_COOLING_STATUS_FILE" 2>/dev/null || true
  tmp="${AI_COOLING_MIRROR_FILE}.tmp.$$"; printf '%s\n' "$payload" > "$tmp" 2>/dev/null && mv -f "$tmp" "$AI_COOLING_MIRROR_FILE" 2>/dev/null || true
}

adaptive_pwm_controller_loop() {
  sleep 8
  trap 'fan_control_shutdown_or_handoff controller_exit' EXIT
  trap 'fan_control_shutdown_or_handoff controller_signal; trap - EXIT; exit 0' TERM INT
  local dev="" temp_milli=0 target_milli=0 deadband_milli=200 error=0 current=0 max_state=0 desired=0 actual_after=0
  local low_count=0 up_count=0 up_hold=0 deadband_count=0 controller_state=-1 base_state=-1 action="hold" writable=false last_logged="" adaptive_write_log_tick=0 adaptive_log_important=false safety_delta=10000 fast_delta=6000
  local min_run_floor=1 ownership_rc=0 owner_zone="" owner_original="" owner_method="" owner_now="" emergency_handoff_milli=70000
  # v2.6.9 Curve-Anchored Adaptive PWM. The custom1 curve is the absolute center
  # line; Adaptive keeps only a bounded trim around it. This prevents historical
  # controller_state wind-up (e.g. 80-87% near the setpoint) and makes recovery
  # after calibration/rebuild gradual instead of a one-cycle jump to curve PWM.
  local resume_after_calibration=false reentry_cycle=false reentry_state=-1 curve_state=0 target_state=0 adaptive_trim=0
  local adaptive_trim_limit=12 slew_up_step=3 slew_down_step=4 slew_fast_up_step=5 slew_fast_down_step=5 trim_decay_interval_cycles=1
  local trim_sign_decay_step=2 trim_sign_threshold=250 sign_guard=""
  local down_direct_delta=1000 down_fast_delta=2000 up_direct_delta=2000
  local up_confirm_cycles=2 up_hold_cycles=3
  local ai_cycle="$AI_COOLING_EVAL_CYCLES" ai_result="" ai_output="" ai_state="" ai_reason="" ai_conf=0 ai_prediction=-1 ai_qualified_samples=0 ai_correction=0 ai_bucket="" ai_observations_total=0 ai_bin_observations=0 ai_qualified_total=0 ai_qualified_flag=0 ai_qualification_reason="" ai_stable_streak=0 ai_last_log="" ai_log_tick=0
  local reload_token="" reload_now=""

  load_custom_curve 1
  reload_token="$(cat "$CONFIG_UI_RELOAD_FILE" 2>/dev/null || true)"
  target_milli="$(awk -v t="$CURVE1_TARGET_C" 'BEGIN{printf "%d",t*1000+0.5}')"
  deadband_milli="$(awk -v t="$ADAPTIVE_PWM_DEADBAND_C" 'BEGIN{printf "%d",t*1000+0.5}')"

  while true; do
    reload_now="$(cat "$CONFIG_UI_RELOAD_FILE" 2>/dev/null || true)"
    if [ -n "$reload_now" ] && [ "$reload_now" != "$reload_token" ]; then
      reload_token="$reload_now"
      load_options
      load_custom_curve 1
      target_milli="$(awk -v t="$CURVE1_TARGET_C" 'BEGIN{printf "%d",t*1000+0.5}')"
      deadband_milli="$(awk -v t="$ADAPTIVE_PWM_DEADBAND_C" 'BEGIN{printf "%d",t*1000+0.5}')"
      controller_state=-1; base_state=-1; adaptive_trim=0; low_count=0; up_count=0; up_hold=0; deadband_count=0; last_logged=""; adaptive_write_log_tick=0
      log "Adaptive PWM: hot reload konfiguracji; cache custom1 odświeżony, target=${CURVE1_TARGET_C}°C, deadband=±${ADAPTIVE_PWM_DEADBAND_C}°C."
    fi
    if ! namespace_control_allowed; then
      controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
      adaptive_pwm_write_status standby namespace_migration_standby "$(read_cpu_temp_millideg 2>/dev/null || echo 0)" 0 0 100 false migration "" 0 0 ""
      sleep 2
      continue
    fi

    if [ "$ADAPTIVE_PWM_ENABLED" != "true" ]; then
      fan_control_release_thermal_ownership adaptive adaptive_disabled >/dev/null 2>&1 || true
      controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
      adaptive_pwm_write_status disabled disabled 0 0 0 0 false kernel "" 0 0 ""
      [ "${AI_COOLING_EFFECTIVE_MODE:-disabled}" = "disabled" ] && ai_cooling_mark_disabled
      sleep 30
      continue
    fi

    if [ -e "$FAN_CALIBRATION_LOCK_FILE" ]; then
      resume_after_calibration=true
      fan_control_release_thermal_ownership adaptive calibration_handoff >/dev/null 2>&1 || true
      controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
      adaptive_pwm_write_status paused fan_calibration "$(read_cpu_temp_millideg 2>/dev/null || echo 0)" 0 0 100 false calibration "" 0 0 ""
      ai_cooling_mark_paused fan_calibration
      sleep 2
      continue
    fi

    if ! adaptive_pwm_profile_active; then
      fan_control_release_thermal_ownership adaptive profile_not_active >/dev/null 2>&1 || true
      low_count=0; up_count=0; up_hold=0; deadband_count=0; controller_state=-1; base_state=-1
      adaptive_pwm_write_status standby profile_not_active "$(read_cpu_temp_millideg 2>/dev/null || echo 0)" 0 0 0 false kernel "" 0 0 ""
      ai_cooling_mark_paused adaptive_profile_not_active
      sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
      continue
    fi

    dev="$(adaptive_pwm_find_device 2>/dev/null || true)"
    if [ -z "$dev" ]; then
      fan_control_release_thermal_ownership adaptive no_fan_cooling_device >/dev/null 2>&1 || true
      low_count=0; up_count=0; up_hold=0; deadband_count=0; controller_state=-1; base_state=-1
      adaptive_pwm_write_status fallback no_fan_cooling_device "$(read_cpu_temp_millideg 2>/dev/null || echo 0)" 0 0 0 false kernel "" 0 0 ""
      sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
      continue
    fi

    temp_milli="$(read_cpu_temp_millideg 2>/dev/null || echo 0)"
    current="$(cat "$dev/cur_state" 2>/dev/null || echo 0)"
    max_state="$(cat "$dev/max_state" 2>/dev/null || echo 0)"
    case "$temp_milli" in ''|*[!0-9-]*) temp_milli=0 ;; esac
    case "$current" in ''|*[!0-9]*) current=0 ;; esac
    case "$max_state" in ''|*[!0-9]*) max_state=0 ;; esac

    if [ "$temp_milli" -le 0 ] 2>/dev/null; then
      fan_control_release_thermal_ownership adaptive invalid_temperature >/dev/null 2>&1 || true
      controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
      adaptive_pwm_write_status fallback invalid_temperature "$temp_milli" "$current" "$current" "$max_state" false kernel "" "$current" "$current" ""
      sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
      continue
    fi

    if [ "$max_state" -lt 100 ] 2>/dev/null; then
      fan_control_release_thermal_ownership adaptive one_percent_grid_required >/dev/null 2>&1 || true
      controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
      if [ "$last_logged" != "one_percent_grid_required:${max_state}" ]; then
        log "Adaptive PWM: wstrzymany — runtime cooling_device max_state=${max_state}; wymagana aktywna siatka 1% (max_state>=100) i pełny restart hosta po zastosowaniu custom1."
        last_logged="one_percent_grid_required:${max_state}"
      fi
      adaptive_pwm_write_status fallback one_percent_grid_required "$temp_milli" "$current" "$current" "$max_state" false kernel "" "$current" "$current" ""
      ai_cooling_mark_paused one_percent_grid_required
      sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
      continue
    fi

    [ -w "$dev/cur_state" ] && writable=true || writable=false
    if [ "$writable" != "true" ]; then
      fan_control_release_thermal_ownership adaptive cur_state_not_writable >/dev/null 2>&1 || true
      controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
      adaptive_pwm_write_status fallback cur_state_not_writable "$temp_milli" "$current" "$current" "$max_state" false kernel "" "$current" "$current" ""
      ai_cooling_mark_paused cur_state_not_writable
      sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
      continue
    fi

    # While Adaptive PWM is active it is the only owner of cur_state. The kernel
    # The kernel curve supplies the base state before takeover. Exclusive zone
    # ownership then prevents step_wise from resetting 29/33/38/46/55/60... between cycles.
    # Never keep a thermal zone in userspace ownership at high temperature.
    # At 70°C or above, demand 100% fan and immediately leave the kernel in charge.
    if [ "$temp_milli" -ge "$emergency_handoff_milli" ] 2>/dev/null; then
      printf '%s\n' "$max_state" > "$dev/cur_state" 2>/dev/null || true
      fan_control_release_thermal_ownership adaptive emergency_temperature_handoff >/dev/null 2>&1 || true
      log "Adaptive PWM: SAFETY handoff przy $(millideg_to_c_1dp "$temp_milli")°C — fan=100%, thermal control pozostaje po stronie kernela."
      controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
      adaptive_pwm_write_status fallback emergency_kernel_handoff "$temp_milli" "$current" "$max_state" "$max_state" true kernel "" "$max_state" "$current" ""
      sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
      continue
    fi

    ownership_rc=0
    fan_control_take_thermal_ownership adaptive "$dev" || ownership_rc=$?
    if [ "$ownership_rc" -ne 0 ] 2>/dev/null; then
      fan_control_release_thermal_ownership adaptive ownership_lost >/dev/null 2>&1 || true
      controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
      adaptive_pwm_write_status fallback "ownership_failed_${ownership_rc}" "$temp_milli" "$current" "$current" "$max_state" false kernel "" "$current" "$current" ""
      ai_cooling_mark_paused "ownership_failed_${ownership_rc}"
      sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
      continue
    fi

    owner_zone="$FAN_CONTROL_ZONE"
    owner_original="$FAN_CONTROL_ORIGINAL_POLICY"
    owner_method="$FAN_CONTROL_OWNERSHIP_METHOD"
    current="$(cat "$dev/cur_state" 2>/dev/null || echo 0)"; case "$current" in ''|*[!0-9]*) current=0 ;; esac
    if [ -s "$FAN_CONTROL_HANDOFF_FILE" ] && fan_control_handoff_marker_valid; then
      log "Fan Control: seamless handoff przejęty przez nowy kontroler; cur_state=${current}/${max_state}; owner=adaptive."
      rm -f "$FAN_CONTROL_HANDOFF_FILE" 2>/dev/null || true
    fi
    min_run_floor="$(fan_calibration_min_safe_pct)"
    reentry_cycle=false
    if [ "$controller_state" -lt 0 ] 2>/dev/null; then
      local kernel_profile_match=true
      base_state="$current"
      curve_state="$(adaptive_pwm_curve_state_for_temp "$temp_milli" "$max_state" 2>/dev/null || echo "$current")"
      case "$curve_state" in ''|*[!0-9]*) curve_state="$current" ;; esac
      [ "$curve_state" -lt "$min_run_floor" ] 2>/dev/null && curve_state="$min_run_floor"
      [ "$curve_state" -gt "$max_state" ] 2>/dev/null && curve_state="$max_state"
      # Never inherit the old controller's accumulated offset. Physical PWM is
      # preserved by the slew limiter, while the adaptive term starts neutral
      # and is rebuilt from fresh temperature error.
      adaptive_trim=0
      controller_state="$current"
      adaptive_pwm_kernel_profile_matches_custom1 || kernel_profile_match=false
      if [ "$resume_after_calibration" = "true" ] || [ "$kernel_profile_match" != "true" ]; then
        reentry_cycle=true
        if [ "$resume_after_calibration" = "true" ]; then
          resume_after_calibration=false
          log "Adaptive PWM: wznowienie po kalibracji; T=$(millideg_to_c_1dp "$temp_milli")°C; previous_state=${current}/${max_state}; curve_base=${curve_state}/${max_state}; trim_reset=${adaptive_trim}pp; slew=enabled."
        else
          log "Adaptive PWM: runtime reconciliation; kernel trips != custom1, ale siatka 1% jest aktywna. T=$(millideg_to_c_1dp "$temp_milli")°C; kernel_state=${current}/${max_state}; curve_base=${curve_state}/${max_state}; trim_reset=${adaptive_trim}pp; przejmuję sterowanie user-space z ograniczonym slew."
        fi
      fi
      last_logged=""
      log "Adaptive PWM: przejęto wyłączne sterowanie; current=${controller_state}/${max_state}; curve_base=${curve_state}/${max_state}; trim=${adaptive_trim}pp (limit ±${adaptive_trim_limit}); thermal_zone=${owner_zone}; method=${owner_method}."
    fi

    error=$((temp_milli - target_milli))
    curve_state="$(adaptive_pwm_curve_state_for_temp "$temp_milli" "$max_state" 2>/dev/null || echo "$controller_state")"
    case "$curve_state" in ''|*[!0-9]*) curve_state="$controller_state" ;; esac
    [ "$curve_state" -lt "$min_run_floor" ] 2>/dev/null && curve_state="$min_run_floor"
    [ "$curve_state" -gt "$max_state" ] 2>/dev/null && curve_state="$max_state"
    action="curve_hold"

    # v2.7.2 Adaptive Trim Sign Guard + faster deadband decay. custom1(T) remains the absolute base.
    # The trim may only reinforce the current temperature error: positive above
    # target, negative below target. In the deadband it decays toward zero and is
    # never reconstructed from controller_state-curve_state (which could flip
    # +12 -> -12 when the curve point moved faster than the slewed actuator).
    sign_guard=""
    if [ "$temp_milli" -ge 80000 ] 2>/dev/null || [ "$error" -ge "$safety_delta" ] 2>/dev/null; then
      adaptive_trim="$adaptive_trim_limit"; action="safety_max"; low_count=0; up_count=0; up_hold=0; deadband_count=0
    elif [ "$error" -ge "$fast_delta" ] 2>/dev/null; then
      if [ "$adaptive_trim" -lt 0 ] 2>/dev/null; then adaptive_trim=0; sign_guard="_sign_guard"; fi
      deadband_count=0; adaptive_trim=$((adaptive_trim + 3)); action="trim_up_fast${sign_guard}"; low_count=0; up_count=0; up_hold=0
    elif [ "$error" -ge "$up_direct_delta" ] 2>/dev/null; then
      if [ "$adaptive_trim" -lt 0 ] 2>/dev/null; then adaptive_trim=0; sign_guard="_sign_guard"; fi
      deadband_count=0; adaptive_trim=$((adaptive_trim + 2)); action="trim_up_direct${sign_guard}"; low_count=0; up_count=0; up_hold=0
    elif [ "$error" -gt "$deadband_milli" ] 2>/dev/null; then
      if [ "$adaptive_trim" -lt 0 ] 2>/dev/null; then adaptive_trim=0; sign_guard="_sign_guard"; fi
      deadband_count=0; low_count=0
      if [ "$up_hold" -gt 0 ] 2>/dev/null; then
        up_hold=$((up_hold - 1)); up_count=0; action="trim_up_hold_${up_hold}${sign_guard}"
      else
        up_count=$((up_count + 1)); action="trim_up_confirm_${up_count}${sign_guard}"
        if [ "$up_count" -ge "$up_confirm_cycles" ] 2>/dev/null; then
          adaptive_trim=$((adaptive_trim + 1)); action="trim_up_confirmed${sign_guard}"; up_count=0; up_hold="$up_hold_cycles"
        fi
      fi
    elif [ "$error" -le $((-down_fast_delta)) ] 2>/dev/null; then
      if [ "$adaptive_trim" -gt 0 ] 2>/dev/null; then adaptive_trim=0; sign_guard="_sign_guard"; fi
      deadband_count=0; adaptive_trim=$((adaptive_trim - 3)); action="trim_down_fast${sign_guard}"; low_count=0; up_count=0; up_hold=0
    elif [ "$error" -le $((-down_direct_delta)) ] 2>/dev/null; then
      if [ "$adaptive_trim" -gt 0 ] 2>/dev/null; then adaptive_trim=0; sign_guard="_sign_guard"; fi
      deadband_count=0; adaptive_trim=$((adaptive_trim - 2)); action="trim_down_direct${sign_guard}"; low_count=0; up_count=0; up_hold=0
    elif [ "$error" -lt $((-deadband_milli)) ] 2>/dev/null; then
      if [ "$adaptive_trim" -gt 0 ] 2>/dev/null; then adaptive_trim=0; sign_guard="_sign_guard"; fi
      deadband_count=0; up_count=0; up_hold=0; low_count=$((low_count + 1)); action="trim_down_confirm_${low_count}${sign_guard}"
      if [ "$low_count" -ge "$ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES" ] 2>/dev/null; then
        adaptive_trim=$((adaptive_trim - 1)); action="trim_down_confirmed${sign_guard}"; low_count=0
      fi
    else
      low_count=0; up_count=0; [ "$up_hold" -gt 0 ] 2>/dev/null && up_hold=$((up_hold - 1))
      deadband_count=$((deadband_count + 1))
      if [ "$error" -le $((-trim_sign_threshold)) ] 2>/dev/null && [ "$adaptive_trim" -gt 0 ] 2>/dev/null; then
        adaptive_trim=$((adaptive_trim - trim_sign_decay_step)); [ "$adaptive_trim" -lt 0 ] 2>/dev/null && adaptive_trim=0
        action="deadband_sign_decay_down"; deadband_count=0
      elif [ "$error" -ge "$trim_sign_threshold" ] 2>/dev/null && [ "$adaptive_trim" -lt 0 ] 2>/dev/null; then
        adaptive_trim=$((adaptive_trim + trim_sign_decay_step)); [ "$adaptive_trim" -gt 0 ] 2>/dev/null && adaptive_trim=0
        action="deadband_sign_decay_up"; deadband_count=0
      elif [ "$deadband_count" -ge "$trim_decay_interval_cycles" ] 2>/dev/null; then
        deadband_count=0
        if [ "$adaptive_trim" -gt 0 ] 2>/dev/null; then adaptive_trim=$((adaptive_trim - 1)); action="deadband_trim_leak_down"
        elif [ "$adaptive_trim" -lt 0 ] 2>/dev/null; then adaptive_trim=$((adaptive_trim + 1)); action="deadband_trim_leak_up"
        else action="deadband_actuator_hold"; fi
      else
        action="deadband_actuator_hold"
      fi
    fi

    # Final invariant: trim never has the opposite sign outside the configured deadband.
    if [ "$error" -gt "$deadband_milli" ] 2>/dev/null && [ "$adaptive_trim" -lt 0 ] 2>/dev/null; then
      adaptive_trim=0; action="${action}_sign_guard"
    elif [ "$error" -lt $((-deadband_milli)) ] 2>/dev/null && [ "$adaptive_trim" -gt 0 ] 2>/dev/null; then
      adaptive_trim=0; action="${action}_sign_guard"
    fi

    [ "$adaptive_trim" -gt "$adaptive_trim_limit" ] 2>/dev/null && adaptive_trim="$adaptive_trim_limit"
    [ "$adaptive_trim" -lt $((-adaptive_trim_limit)) ] 2>/dev/null && adaptive_trim=$((-adaptive_trim_limit))

    if [ "$action" = "safety_max" ]; then
      target_state="$max_state"
    else
      target_state=$((curve_state + adaptive_trim))
      [ "$target_state" -lt "$min_run_floor" ] 2>/dev/null && target_state="$min_run_floor"
      [ "$target_state" -gt "$max_state" ] 2>/dev/null && target_state="$max_state"
    fi
    desired="$target_state"

    # Hybrid keeps the same curve anchor but uses the user-configured, usually
    # tighter correction corridor instead of the automatic ±12 pp limit.
    if [ "$COOLING_CONTROL_MODE" = "hybrid" ]; then
      local hybrid_low hybrid_high unclamped
      hybrid_low=$((curve_state - HYBRID_CORRECTION_LIMIT_PCT)); hybrid_high=$((curve_state + HYBRID_CORRECTION_LIMIT_PCT))
      [ "$hybrid_low" -lt "$min_run_floor" ] && hybrid_low="$min_run_floor"
      [ "$hybrid_high" -gt "$max_state" ] && hybrid_high="$max_state"
      unclamped="$desired"
      [ "$desired" -lt "$hybrid_low" ] && desired="$hybrid_low"
      [ "$desired" -gt "$hybrid_high" ] && desired="$hybrid_high"
      if [ "$desired" -ne "$unclamped" ] 2>/dev/null; then action="${action}_hybrid_limit"; fi
    fi

    # v2.8.4 AI Quality Window Recovery. The classic controller remains authoritative.
    # The learner is evaluated every Adaptive PWM controller cycle (~10 s), so the
    # 60 s temperature window and 30 s PWM window contain enough real points to become
    # ready. Training observations remain independently rate-limited in ai_cooling.py
    # to ~30 s, therefore this does not increase the learned-sample write rate.
    # In AI Assist it may nudge the already-safe Adaptive decision by max +/-2%.
    if [ "${AI_COOLING_EFFECTIVE_MODE:-disabled}" != "disabled" ] && [ -x "$AI_COOLING_SCRIPT" ] && [ "$reentry_cycle" != "true" ] && [ "$action" != "safety_max" ]; then
      ai_cycle=$((ai_cycle + 1))
      if [ "$ai_cycle" -ge "$AI_COOLING_EVAL_CYCLES" ] 2>/dev/null; then
        ai_cycle=0
        ai_result="$(python3 "$AI_COOLING_SCRIPT" step \
          --model "$AI_COOLING_MODEL_FILE" --status "$AI_COOLING_STATUS_FILE" --mirror "$AI_COOLING_MIRROR_FILE" \
          --telemetry "$TELEMETRY_STATE_FILE" --mode "$AI_COOLING_EFFECTIVE_MODE" --control-mode "$COOLING_CONTROL_MODE" \
          --controller-action "$action" --temp-milli "$temp_milli" --target "$CURVE1_TARGET_C" --pwm "$controller_state" --baseline "$desired" \
          --min-safe "$min_run_floor" --maximum "$max_state" --assist-limit "$AI_COOLING_ASSIST_LIMIT_PCT" --deadband "$ADAPTIVE_PWM_DEADBAND_C" \
          --min-samples "$AI_COOLING_MIN_SAMPLES" --grid-profile "$AI_GRID_PROFILE_FILE" --curve-points-csv "$CUSTOM_TRIPS_CSV" 2>/dev/null || true)"
        if [ -n "$ai_result" ]; then
          ai_log_tick=$((ai_log_tick + 1))
          IFS=$'\t' read -r ai_output ai_state ai_reason ai_conf ai_prediction ai_qualified_samples ai_correction ai_bucket ai_observations_total ai_bin_observations ai_qualified_total ai_qualified_flag ai_qualification_reason ai_stable_streak <<< "$ai_result"
          case "$ai_output" in ''|*[!0-9]*) ai_output="$desired" ;; esac
          case "$ai_conf" in ''|*[!0-9]*) ai_conf=0 ;; esac
          case "$ai_prediction" in ''|*[!0-9]*) ai_prediction=-1 ;; esac
          case "$ai_correction" in ''|-|*[!0-9-]*) ai_correction=0 ;; esac
          case "$ai_qualified_samples" in ''|*[!0-9]*) ai_qualified_samples=0 ;; esac
          case "$ai_bin_observations" in ''|*[!0-9]*) ai_bin_observations=0 ;; esac
          case "$ai_qualified_total" in ''|*[!0-9]*) ai_qualified_total=0 ;; esac
          if [ "$AI_COOLING_EFFECTIVE_MODE" = "assist" ] && [ "$COOLING_CONTROL_MODE" = "automatic" ] && [ "$ai_output" -ne "$desired" ] 2>/dev/null; then
            desired="$ai_output"
            action="${action}_ai_assist"
          fi
          if [ "$ai_qualified_flag" = "1" ] && { [ "$ai_qualified_samples" = "1" ] || [ "$ai_qualified_samples" = "$AI_COOLING_MIN_SAMPLES" ] || [ $((ai_qualified_samples % 5)) -eq 0 ]; }; then
            log "AI Cooling: qualified sample; bucket=${ai_bucket}; quality=${ai_qualified_samples}/${AI_COOLING_MIN_SAMPLES}; observations=${ai_bin_observations}; confidence=${ai_conf}%; prediction=${ai_prediction}%."
          elif { [ "$ai_last_log" != "${ai_state}:${ai_bucket}:${ai_conf}:${ai_prediction}:${ai_qualified_samples}" ] || [ $((ai_log_tick % AI_COOLING_LOG_KEEPALIVE_CYCLES)) -eq 0 ]; } && { [ "$ai_state" = "assist" ] || [ "$ai_reason" = "insufficient_qualified_samples" ] || [ "$ai_bin_observations" = "1" ]; }; then
            log "AI Cooling: state=${ai_state}; reason=${ai_reason}; bucket=${ai_bucket}; observations=${ai_bin_observations}; qualified=${ai_qualified_samples}/${AI_COOLING_MIN_SAMPLES}; confidence=${ai_conf}%; prediction=${ai_prediction}%; qualification=${ai_qualification_reason}."
            ai_last_log="${ai_state}:${ai_bucket}:${ai_conf}:${ai_prediction}:${ai_qualified_samples}"
          fi
        fi
      fi
    elif [ "${AI_COOLING_EFFECTIVE_MODE:-disabled}" = "disabled" ]; then
      if [ ! -s "$AI_COOLING_STATUS_FILE" ] || [ "$(jq -r '.state // empty' "$AI_COOLING_STATUS_FILE" 2>/dev/null || true)" != "disabled" ]; then ai_cooling_mark_disabled; fi
    fi

    # v2.6.9 final actuator guard. AI Assist may nudge the classic target, but
    # the physical write still obeys a bounded curve corridor and a slew-rate limit.
    # Safety maximum remains immediate.
    if [ "$action" != "safety_max" ]; then
      local final_low final_high before_slew step_up step_down
      final_low=$((curve_state - adaptive_trim_limit - AI_COOLING_ASSIST_LIMIT_PCT))
      final_high=$((curve_state + adaptive_trim_limit + AI_COOLING_ASSIST_LIMIT_PCT))
      [ "$final_low" -lt "$min_run_floor" ] && final_low="$min_run_floor"
      [ "$final_high" -gt "$max_state" ] && final_high="$max_state"
      [ "$desired" -lt "$final_low" ] && desired="$final_low"
      [ "$desired" -gt "$final_high" ] && desired="$final_high"
      before_slew="$desired"
      step_up="$slew_up_step"; step_down="$slew_down_step"
      [ "$error" -ge "$fast_delta" ] 2>/dev/null && step_up="$slew_fast_up_step"
      [ "$error" -le $((-down_fast_delta)) ] 2>/dev/null && step_down="$slew_fast_down_step"
      if [ "$desired" -gt $((controller_state + step_up)) ] 2>/dev/null; then
        desired=$((controller_state + step_up)); action="${action}_slew_up"
      elif [ "$desired" -lt $((controller_state - step_down)) ] 2>/dev/null; then
        desired=$((controller_state - step_down)); action="${action}_slew_down"
      fi
      [ "$desired" -lt "$min_run_floor" ] 2>/dev/null && desired="$min_run_floor"
      [ "$desired" -gt "$max_state" ] 2>/dev/null && desired="$max_state"
    fi

    # A mismatch while exclusive ownership is active means another writer touched cur_state. Do not
    # adopt it as the new base; reassert the remembered controller state.
    if [ "$reentry_cycle" != "true" ] && [ "$current" -ne "$controller_state" ] 2>/dev/null && [ "$desired" -eq "$controller_state" ] 2>/dev/null; then
      action="reassert_owner_state"
      if [ "$last_logged" != "external:${current}:${controller_state}" ]; then
        log "Fan Write: source=external observed=${current}; owner=adaptive; reassert=${controller_state}."
        last_logged="external:${current}:${controller_state}"
      fi
    fi

    # Re-check ownership immediately before touching cur_state. This closes the
    # handoff window when calibration starts while an Adaptive cycle is running.
    owner_now="$(jq -r '.owner // empty' "$FAN_CONTROL_OWNER_FILE" 2>/dev/null || true)"
    if [ -e "$FAN_CALIBRATION_LOCK_FILE" ] || [ "$owner_now" != "adaptive" ]; then
      [ "$owner_now" = "adaptive" ] && fan_control_release_thermal_ownership adaptive prewrite_handoff >/dev/null 2>&1 || true
      adaptive_pwm_write_status paused ownership_handoff "$temp_milli" "$current" "$controller_state" "$max_state" false "${owner_now:-kernel}" "$owner_zone" "$controller_state" "$base_state" "$owner_original"
      controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
      sleep 1
      continue
    fi

    if [ "$desired" -ne "$current" ] 2>/dev/null; then
      if printf '%s\n' "$desired" > "$dev/cur_state" 2>/dev/null; then
        sleep 0.05
        actual_after="$(cat "$dev/cur_state" 2>/dev/null || echo -1)"; case "$actual_after" in ''|*[!0-9]*) actual_after=-1 ;; esac
        if [ "$actual_after" -eq "$desired" ] 2>/dev/null; then
          controller_state="$desired"
          adaptive_write_log_tick=$((adaptive_write_log_tick + 1))
          adaptive_log_important=false
          case "$action" in
            *fast*|*sign_guard*|reassert_owner_state) adaptive_log_important=true ;;
          esac
          if [ "$last_logged" != "$action:$current:$desired" ]; then
            if [ "$adaptive_log_important" = "true" ] || [ "$adaptive_write_log_tick" -eq 1 ] || [ $((adaptive_write_log_tick % ADAPTIVE_PWM_LOG_KEEPALIVE_WRITES)) -eq 0 ]; then
              log "Adaptive PWM: T=$(millideg_to_c_1dp "$temp_milli")°C target=${CURVE1_TARGET_C}°C curve=${curve_state}% trim=${adaptive_trim}pp controller ${current}->${desired}/${max_state} (${action}); owner=adaptive."
            fi
            last_logged="$action:$current:$desired"
          fi
        else
          log "Adaptive PWM: zapis ${desired} nie został utrzymany (actual=${actual_after}); oddaję sterowanie kernelowi."
          fan_control_release_thermal_ownership adaptive write_not_held >/dev/null 2>&1 || true
          adaptive_pwm_write_status fallback write_not_held "$temp_milli" "$actual_after" "$desired" "$max_state" false kernel "$owner_zone" "$controller_state" "$base_state" "$owner_original"
          controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
          sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
          continue
        fi
      else
        log "Adaptive PWM: nie udało się zapisać cur_state; oddaję sterowanie kernelowi."
        fan_control_release_thermal_ownership adaptive write_failed >/dev/null 2>&1 || true
        adaptive_pwm_write_status fallback write_failed "$temp_milli" "$current" "$current" "$max_state" false kernel "$owner_zone" "$controller_state" "$base_state" "$owner_original"
        controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
        sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
        continue
      fi
    fi

    current="$(cat "$dev/cur_state" 2>/dev/null || echo "$controller_state")"; case "$current" in ''|*[!0-9]*) current="$controller_state" ;; esac
    adaptive_pwm_write_status active "$action" "$temp_milli" "$current" "$controller_state" "$max_state" true adaptive "$owner_zone" "$controller_state" "$curve_state" "$owner_original" "$adaptive_trim"
    sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
  done
}
telemetry_publisher_loop() {
  # Offset telemetry from Adaptive/AI cycles to avoid synchronized CPU spikes.
  sleep 7
  while true; do
    publish_telemetry_snapshot || true
    publish_performance_state || true
    sleep "$TELEMETRY_PUBLISH_INTERVAL_SECONDS"
  done
}

show_status() {
  local rpm="0" pwm="0" level="?" max_level="?" f p d

  for f in /sys/devices/platform/cooling_fan/hwmon/hwmon*/fan1_input; do
    [ -r "$f" ] || continue
    rpm="$(cat "$f" 2>/dev/null || echo 0)"
    p="${f%fan1_input}pwm1"
    [ -r "$p" ] && pwm="$(cat "$p" 2>/dev/null || echo 0)"
    break
  done

  for d in /sys/class/thermal/cooling_device*; do
    [ -r "$d/type" ] || continue
    grep -qi fan "$d/type" 2>/dev/null || continue
    level="$(cat "$d/cur_state" 2>/dev/null || echo '?')"
    max_level="$(cat "$d/max_state" 2>/dev/null || echo '?')"
    break
  done

  log "Stan wentylatora: poziom=$level/$max_level RPM=$rpm PWM=$pwm"
  collect_system_power_info
  log "CPU: ${SYS_CPU_FREQ_MHZ} MHz (min=${SYS_CPU_MIN_MHZ}, max=${SYS_CPU_MAX_MHZ}, governor=${SYS_CPU_GOVERNOR:-?})"
  log "Zasilanie: ${SYS_POWER_SUPPLY}; max_current=${SYS_POWER_MAX_CURRENT_MA} mA; źródło=${SYS_POWER_SOURCE}; limit USB=${SYS_USB_LIMIT_MA} mA (${SYS_USB_LIMIT_SOURCE}); over-current=${SYS_USB_OVERCURRENT} (${SYS_OVERCURRENT_SOURCE})"
  log "Energia: PMIC=${SYS_PMIC_POWER_W} W; prąd równoważny@EXT5V=${SYS_PMIC_EQ_CURRENT_A} A; EXT5V=${SYS_INPUT_VOLTAGE_V} V; VDD_CORE=${SYS_CORE_CURRENT_A} A/${SYS_CORE_VOLTAGE_V} V/${SYS_CORE_POWER_W} W; PMIC temp=${SYS_PMIC_TEMP_C}°C; źródło=${SYS_PMIC_SOURCE}"
  log "USB: urządzeń=${SYS_USB_DEVICE_COUNT}; suma deklarowanego bMaxPower=${SYS_USB_DECLARED_MA} mA / limit=${SYS_USB_LIMIT_MA} mA (to nie jest rzeczywisty chwilowy pobór)."
  log "Konfiguracja: ${SYS_CONFIG_STATUS}; boot=${SYS_BOOT_CONFIG_DEVICE:-brak}/${SYS_BOOT_CONFIG_PATH:-} źródło=${SYS_BOOT_CONFIG_SOURCE:-brak}; arm_freq zapis=${SYS_CONFIG_SAVED_ARM_FREQ_MHZ} MHz aktywne=${SYS_CONFIG_ACTIVE_ARM_FREQ_MHZ} MHz; over_voltage_delta zapis=${SYS_CONFIG_SAVED_OVER_VOLTAGE_DELTA:-N/D} aktywne=${SYS_CONFIG_ACTIVE_OVER_VOLTAGE_DELTA:-N/D}; usb_max_current_enable zapis=${SYS_CONFIG_SAVED_USB_MAX_CURRENT_ENABLE} aktywne=${SYS_CONFIG_ACTIVE_USB_MAX_CURRENT_ENABLE}; rozbieżność=${SYS_CONFIG_PENDING_RESTART}."
  log "Aktywne progi: $(read_kernel_trip_points)"
  report_active_profile
}

restore_backup() {
  if ! find_boot_config; then
    log "Nie znaleziono config.txt."
    return 1
  fi

  if [ -f "${BOOT_CFG}.rpi5fan.bak" ]; then
    cp "${BOOT_CFG}.rpi5fan.bak" "$BOOT_CFG"
    sync
    log "Przywrócono kopię config.txt. Wymagany restart hosta."
    mark_host_restart_required "Przywrócono kopię config.txt. Aby firmware i kernel wczytały przywróconą konfigurację, wymagany jest restart hosta."
  else
    log "Brak kopii config.txt.rpi5fan.bak"
  fi
  cleanup_mount
}

profile_reporter() {
  sleep 41
  while true; do
    report_active_profile
    sleep "$PROFILE_REPORT_INTERVAL_SECONDS"
  done
}

migration_handoff_startup() {
  [ -x "$STORE_MIGRATION_SCRIPT" ] || return 0
  local out rc
  while true; do
    out="$(SBC5CC_APP_VERSION="$APP_VERSION" python3 "$STORE_MIGRATION_SCRIPT" auto --version "$APP_VERSION" 2>&1)"
    rc=$?
    [ -n "$out" ] && log "Store Migration: $out"
    case "$rc" in
      0) return 0 ;;
      20)
        log "Store Migration: sklepowa instancja czeka na zatrzymanie lokalnej instancji źródłowej; regulator nie zostanie uruchomiony przed importem."
        sleep 15
        ;;
      21)
        log "Store Migration: ta lokalna instancja została już zastąpiona przez wersję sklepową. Pozostaję w bezpiecznym standby; można ją odinstalować po weryfikacji wersji sklepowej."
        while true; do sleep 3600; done
        ;;
      22)
        log "Store Migration: wykryto równolegle uruchomioną instancję sklepową. Lokalna instancja pozostaje źródłem; zatrzymaj wersję sklepową przed eksportem handoffu."
        return 0
        ;;
      *)
        log "Store Migration: nie udało się zakończyć automatycznego handoffu (rc=${rc}); zachowuję bieżące dane i nie wykonuję destrukcyjnych zmian."
        return 0
        ;;
    esac
  done
}

# v2.8.32: local -> Store migration is completed before profile bootstrap/load_options,
# so imported AI/calibration/profile state becomes the source of truth from the first
# controller cycle. The store identity waits until the local source is stopped.
migration_handoff_startup

# v2.8.18: restore both persistent profile requests before the first options snapshot.
# This makes native Supervisor Configuration, Ingress and YAML start from the same source of truth.
cpu_profile_state_bootstrap || true
cpu_profile_import_startup_options_if_safe || true
cpu_profile_restore_options_from_state || true
gpu_profile_state_bootstrap || true
gpu_profile_import_startup_options_if_safe || true
gpu_profile_restore_options_from_state || true
# v2.8.18: native Supervisor Configuration reads its own persistent option store,
# not /data/options.json. Reconcile that store before rendering runtime state.
supervisor_profile_reconcile_startup || true
load_options
detect_custom_curve_config_change
LAST_UPDATE_SIGNATURE="$(jq -r '.signature // empty' "$UPDATE_STATE_FILE" 2>/dev/null || true)"

if ! platform_preflight; then
  log "FATAL: wymagania platformy dla SBC5 Control Center ${APP_VERSION} nie są spełnione. Aplikacja nie zostanie uruchomiona."
  exit 64
fi

install_project_logo
log "SBC5 Control Center v${APP_VERSION} uruchomiony."
log "Profile: factory, custom1 (profile legacy ukryte i zachowane tylko dla migracji/diagnostyki)"
load_custom_curve 1
log "Active Cooler: profil=custom1; control_mode=${COOLING_CONTROL_MODE}; auto_style=${COOLING_AUTO_STYLE}; target=${CUSTOM_TARGET_C}°C; hyst=${CUSTOM_HYST_DENSE_C}/${CUSTOM_HYST_OUTER_C}°C; PWM=${CUSTOM_MIN_PWM_PCT}/${CUSTOM_TARGET_PWM_PCT}/${CUSTOM_MAX_PWM_PCT}%; hybrid_limit=±${HYBRID_CORRECTION_LIMIT_PCT}%."
log "Adaptive PWM: control_mode=${COOLING_CONTROL_MODE}; enabled=${ADAPTIVE_PWM_ENABLED}; deadband=±${ADAPTIVE_PWM_DEADBAND_C}°C; interval=${ADAPTIVE_PWM_INTERVAL_SECONDS}s; up_confirm=2; anti_windup_hold=3 cykle; down_confirm=${ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES}; grid=1%; baza=custom1(T)+bounded trim ±12pp; deadband=actuator-hold + sign-aware decay + trim leak 1pp/~10s; sign_guard=enabled; curve_cache=hot-reload; owner=exclusive auto(user_space|mode_disabled); reentry=slew-limited; actuator slew=+3/-4pp na cykl (fast +5/-5); telemetry runtime=canonical relay schema 10."
log "Update Handoff: seamless Adaptive PWM ownership transfer=enabled; timeout=${FAN_CONTROL_HANDOFF_MAX_AGE_SECONDS}s; arbitrary stop nadal zwalnia sterowanie do kernela."
log "AI Cooling Preview: section=${AI_COOLING_SECTION_ENABLED}; configured=${AI_COOLING_MODE}; effective=${AI_COOLING_EFFECTIVE_MODE}; assist_limit=±${AI_COOLING_ASSIST_LIMIT_PCT}%; min_samples=${AI_COOLING_MIN_SAMPLES}; local_model=/data/ai_cooling_model.json."
log "Restart Manager: policy=${RESTART_POLICY}, pre_check=${PRE_RESTART_CONFIG_CHECK}, notices=${RESTART_NOTICE_ON_START}"
log "Config.txt Options UI: enabled=${CONFIG_TXT_OPTIONS_ENABLED}, sync=${CONFIG_TXT_OPTIONS_SYNC_INTERVAL}s, advanced=${CONFIG_TXT_OPTIONS_ADVANCED}"
log "Performance: realtime=${REALTIME_PUBLISH_INTERVAL_SECONDS}s; telemetry=${TELEMETRY_PUBLISH_INTERVAL_SECONDS}s; relay=${HOST_RELAY_INTERVAL_SECONDS}s; AI-relay=${AI_RUNTIME_RELAY_INTERVAL_SECONDS}s; PMIC=${TELEMETRY_PMIC_INTERVAL_SECONDS}s; system=${TELEMETRY_EXTENDED_INTERVAL_SECONDS}s; power/USB/config=${TELEMETRY_POWER_INTERVAL_SECONDS}s; profile=${PROFILE_REPORT_INTERVAL_SECONDS}s; profile-options=${PROFILE_OPTIONS_SYNC_INTERVAL_SECONDS}s; UX-poll=${UX_RUNTIME_POLL_SECONDS}s; boot-cache=${BOOT_CONFIG_CACHE_SECONDS}s; AI evaluator=$((AI_COOLING_EVAL_CYCLES * ADAPTIVE_PWM_INTERVAL_SECONDS))s; control-log=sample/${ADAPTIVE_PWM_LOG_KEEPALIVE_WRITES} writes; AI-log-keepalive=$((AI_COOLING_LOG_KEEPALIVE_CYCLES * ADAPTIVE_PWM_INTERVAL_SECONDS))s."
resolve_multicore_workers
log "Multicore Telemetry: enabled=${MULTICORE_TELEMETRY_ENABLED}; workers=${MULTICORE_WORKERS_CONFIG} -> ${MULTICORE_WORKERS_EFFECTIVE}; cpus_allowed=$(read_cpu_allowed_list 2>/dev/null || echo unknown)."
log "Polecenia: status, reload_config, diagnose, restore_backup, curve_editor_refresh, calibrate_fan, fan_calibration_refresh, restore_active_cooler_factory, restore_rpi5_app_defaults, resume_managed_rpi5_config, set_custom_curve_template, set_custom_curve_point, reset_custom_curve_parameter, reset_custom_curve_factory, reset_all_custom_curves_factory, reset_custom_curve, apply_ai_grid_suggestion, clear_ai_grid_override, ux_self_test, set_cpu_profile, set_gpu_profile, apply_system_config, restore_system_config_backup, apply_config_txt_parameter, remove_config_txt_parameter, restore_config_manager_backup, restart_status, restart_ha_confirmed, check_app_update, install_local_update, cleanup_update_packages, migration_status, migration_export, migration_import, migration_rollback"
PID1_COMM="$(cat /proc/1/comm 2>/dev/null | tr -d '\r\n' || true)"
HOST_BOOT_INFO="$(host_pid_boot_root 2>/dev/null || true)"
if [ -n "$HOST_BOOT_INFO" ]; then
  IFS='|' read -r HOST_BOOT_ROOT HOST_BOOT_REL HOST_BOOT_PID1 <<< "$HOST_BOOT_INFO"
  log "Host Access: SUKCES; PID1=${PID1_COMM:-?}; config=${HOST_BOOT_ROOT}/${HOST_BOOT_REL}; R=$( [ -r "${HOST_BOOT_ROOT}/${HOST_BOOT_REL}" ] && echo tak || echo nie ); W=$( [ -w "${HOST_BOOT_ROOT}/${HOST_BOOT_REL}" ] && echo tak || echo nie )."
else
  HOST_NS_INFO="$(host_nsenter_boot_info 2>/dev/null || true)"
  if [ -n "$HOST_NS_INFO" ]; then
    log "Host Access: bezpośredni /proc/1/root niedostępny, ale nsenter widzi boot=${HOST_NS_INFO}."
  else
    log "Host Access: brak bezpośredniego /proc/1/root i nsenter — uruchamiam skanowanie mountów/partycji boot jako fallback."
  fi
fi
host_boot_probe_log

# 2.6.34: expensive host diagnostics back off when full host access is unavailable.
# Protection Mode changes require an app restart, so this is intentionally fixed per runtime.
if [ -z "${HOST_BOOT_INFO:-}" ] && [ -z "${HOST_NS_INFO:-}" ]; then
  TELEMETRY_PMIC_INTERVAL_SECONDS=120
  TELEMETRY_EXTENDED_INTERVAL_SECONDS=120
  SECURITY_INFO="$(supervisor_self_security_json 2>/dev/null || true)"
  if [ -n "$SECURITY_INFO" ]; then
    SECURITY_PROTECTED="$(jq -r '.protected // "unknown"' <<<"$SECURITY_INFO" 2>/dev/null || echo unknown)"
    SECURITY_HOST_PID="$(jq -r '.host_pid // "unknown"' <<<"$SECURITY_INFO" 2>/dev/null || echo unknown)"
    SECURITY_FULL_ACCESS="$(jq -r '.full_access // "unknown"' <<<"$SECURITY_INFO" 2>/dev/null || echo unknown)"
    log "Host Access Guard: Supervisor protected=${SECURITY_PROTECTED}; host_pid=${SECURITY_HOST_PID}; full_access=${SECURITY_FULL_ACCESS}; PID1=${PID1_COMM:-?}."
    if [ "$SECURITY_PROTECTED" = "true" ]; then
      log "Host Access Guard: Protection Mode jest włączony — wyłącz go w Info aplikacji i uruchom aplikację ponownie, aby Host PID/config.txt/PMIC były dostępne."
    elif [ "$SECURITY_HOST_PID" = "true" ] && [ "${PID1_COMM:-}" != "systemd" ]; then
      log "Host Access Guard: Supervisor deklaruje host_pid=true, ale namespace hosta nie jest aktywny; bezpiecznie wstrzymuję zapisy boot. Uruchom aplikację ponownie po zmianie uprawnień."
    fi
  fi
  log "Host Access Health: DEGRADED — ciężkie odczyty PMIC/system ograniczone do 120 s; zapisy boot są wstrzymane do odzyskania Host Access."
else
  log "Host Access Health: OK — pełna diagnostyka hosta aktywna."
fi

# v2.8.15: reconcile requested custom1 with the cooling device actually loaded by
# the kernel. A stale user-space owner is still released first by startup recovery;
# this step repairs missing boot artifacts once and never forces Adaptive PWM while
# max_state<100.
fan_profile_reconcile_startup || true

# v2.7.2: trwały CPU Profile State jest źródłem prawdy; preset nie zależy od config_cpu ani ogólnego managera.
sync_cpu_profile_from_options true || true
log "CPU Profile Manager: source_of_truth=${CPU_PROFILE_STATE_FILE}; profile=$(cpu_profile_requested_profile); enabled=$(cpu_profile_requested_enabled)."
# v2.8.15: GPU profile also has a persistent source of truth. It is restored
# before Config Manager renders sbc5cc-managed.txt, so Supervisor defaults cannot
# silently replace a dashboard-selected preset after the host reboot.
sync_gpu_profile_from_options true || true
# Persist the canonicalized startup state back to Supervisor as well (for example
# preset values inferred from a native selector change).
supervisor_sync_profile_state_to_store || true
# Pozostałe pola CONFIG.TXT nadal respektują przełącznik ogólnego managera.
if [ "$CONFIG_TXT_OPTIONS_ENABLED" = "true" ]; then
  sync_config_txt_from_options true || true
fi

if [ "$CUSTOM_CURVE_CONFIG_CHANGED" = "true" ]; then
  log "Wykryto zmianę konfiguracji własnej krzywej -> przygotowuję custom1 i oznaczam wymagany restart hosta."
  if write_overlay_profile custom1; then
    commit_custom_curve_config_signature
  else
    log "Nie udało się przygotować custom1; podpis konfiguracji nie został zatwierdzony i próba zostanie ponowiona."
  fi
elif [ "$APPLY_CUSTOM_CURVE_ON_START" != "off" ]; then
  log "Legacy apply_custom_curve_on_start=${APPLY_CUSTOM_CURVE_ON_START} -> zapisuję custom${APPLY_CUSTOM_CURVE_ON_START} do partycji boot."
  write_overlay_profile "custom${APPLY_CUSTOM_CURVE_ON_START}" || true
elif [ "$APPLY_CUSTOM_ON_START" = "true" ]; then
  log "apply_custom_on_start=true -> zapisuję krzywą własną 1."
  write_overlay_profile custom1 || true
fi

migrate_project_layout
ensure_runtime_directories
ensure_card_ui_override_state
fan_calibration_init_storage || true
publish_realtime_cooling_snapshot || true
publish_telemetry_snapshot || true
fan_control_recover_stale_ownership || true
fan_calibration_publish_state || true
ensure_legacy_bridge_shim_installed || true
start_dynamic_config_ui() {
  if [ -x /config_ui.py ]; then
    SBC5CC_APP_VERSION="$APP_VERSION" RPI5CC_CONFIG_UI_PORT="$CONFIG_UI_PORT" /config_ui.py >/tmp/rpi5cc-config-ui.log 2>&1 &
    log "Dynamic Config UI: Ingress uruchomiony na porcie $CONFIG_UI_PORT."
  else
    log "Dynamic Config UI: brak /config_ui.py — interfejs Ingress niedostępny."
  fi
}

config_ui_reload_loop() {
  local last="" cur=""
  while true; do
    if [ -r "$CONFIG_UI_RELOAD_FILE" ]; then
      cur="$(cat "$CONFIG_UI_RELOAD_FILE" 2>/dev/null || true)"
      if [ -n "$cur" ] && [ "$cur" != "$last" ]; then
        last="$cur"
        load_options
        detect_custom_curve_config_change
        if [ "$CUSTOM_CURVE_CONFIG_CHANGED" = "true" ]; then
          if write_overlay_profile custom1; then commit_custom_curve_config_signature; fi
        fi
        ha_sync_profile_options || true
        ha_publish_curve_editor_state || true
        sync_cpu_profile_from_options true || true
        sync_gpu_profile_from_options true || true
        if [ "$CONFIG_TXT_OPTIONS_ENABLED" = "true" ]; then sync_config_txt_from_options true || true; fi
        publish_telemetry_snapshot || true
        ha_sync_cpu_gpu_profile_selectors || true
        LAST_PROFILE_STATE_OPTIONS_SIGNATURE="$(profile_state_options_signature)"
        log "Dynamic Config UI: zastosowano zapisane ustawienia; profile CPU/GPU zsynchronizowano z kartą YAML, natywną Konfiguracją i config.txt."
      fi
    fi
    sleep 10
  done
}

migrate_dynamic_config_sections
start_dynamic_config_ui

ensure_native_bridge_installed || true
cleanup_legacy_bridge_if_migrated || true
schedule_unified_dashboard_sync
ensure_bridge_package_installed || true
load_options
finalize_local_update_after_startup || true
cleanup_local_update_archives "startup"
ha_sync_profile_options
ha_publish_curve_editor_state || true
resolve_mobile_notify_service
clear_2_8_22_version_only_config_restart || true
clear_2_8_24_version_only_cpu_restart || true
detect_app_upgrade
show_status
ha_sync_selected_profile_to_requested || true
publish_restart_requirement true
if [ -x /namespace_native_guard.sh ]; then
  if namespace_migration_complete; then
    log "Namespace Guard: migracja COMPLETE — guard migracyjny nie jest uruchamiany."
  else
    /namespace_native_guard.sh &
  fi
fi
profile_reporter &
realtime_cooling_loop &
adaptive_pwm_controller_loop &
telemetry_publisher_loop &
profile_options_sync_loop &
ux_runtime_state_loop &
profile_boot_sync_loop &
restart_manager_loop &
post_update_restart_monitor_loop &
update_check_loop &
local_update_watch_loop &
local_update_native_health_loop &
config_txt_options_sync_loop &
config_ui_reload_loop &
profile_state_reconcile_loop &

while IFS= read -r line; do
  [ -n "$line" ] || continue
  profile="$(printf '%s' "$line" | jq -r '.profile // empty' 2>/dev/null || true)"
  command="$(printf '%s' "$line" | jq -r '.command // empty' 2>/dev/null || true)"
  if [ "$command" != "install_local_update" ]; then
    log "Odebrano polecenie: $line"
  fi

  if [ -n "$profile" ]; then
    _profile_ok=true
    case "$profile" in
      stable50_10|stable50_15)
        write_overlay_profile "$profile" || _profile_ok=false ;;
      custom15|custom[1-5])
        load_options
        write_overlay_profile "$profile" || _profile_ok=false ;;
      *)
        write_4point_profile "$profile" || _profile_ok=false ;;
    esac
    if [ "$_profile_ok" = "true" ]; then
      ha_publish_action_result ok apply_fan_profile "Zapisano profil $profile. Wymagany restart hosta, jeśli wskazuje go Restart Manager."
    else
      ha_publish_action_result error apply_fan_profile "Nie udało się zapisać profilu $profile. Sprawdź log aplikacji."
    fi
    continue
  fi

  case "$command" in
    status) show_status ;;
    migration_status)
      SBC5CC_APP_VERSION="$APP_VERSION" python3 "$STORE_MIGRATION_SCRIPT" status 2>&1 | while IFS= read -r migration_line; do log "Store Migration: ${migration_line}"; done ;;
    migration_export)
      if SBC5CC_APP_VERSION="$APP_VERSION" python3 "$STORE_MIGRATION_SCRIPT" export --version "$APP_VERSION" >/tmp/sbc5_migration_export.log 2>&1; then
        log "Store Migration: ręczny eksport zakończony; $(tr '\n' ' ' </tmp/sbc5_migration_export.log 2>/dev/null || true)"
        ha_publish_action_result ok migration_export "Przygotowano zweryfikowany handoff danych dla wersji sklepowej."
      else
        rc=$?; log "Store Migration: eksport nie został wykonany (rc=${rc}); $(tr '\n' ' ' </tmp/sbc5_migration_export.log 2>/dev/null || true)"
        ha_publish_action_result error migration_export "Eksport migracyjny nie został wykonany; sprawdź log aplikacji."
      fi ;;
    migration_import)
      if SBC5CC_APP_VERSION="$APP_VERSION" python3 "$STORE_MIGRATION_SCRIPT" import --version "$APP_VERSION" >/tmp/sbc5_migration_import.log 2>&1; then
        log "Store Migration: ręczny import zakończony; $(tr '\n' ' ' </tmp/sbc5_migration_import.log 2>/dev/null || true)"
        ha_publish_action_result ok migration_import "Zaimportowano trwały stan lokalnej instancji. Uruchom ponownie aplikację, aby wszystkie profile zostały odczytane od początku."
      else
        rc=$?; log "Store Migration: import nie został wykonany (rc=${rc}); $(tr '\n' ' ' </tmp/sbc5_migration_import.log 2>/dev/null || true)"
        ha_publish_action_result error migration_import "Import migracyjny nie został wykonany; sprawdź, czy lokalna instancja jest zatrzymana."
      fi ;;
    migration_rollback)
      if SBC5CC_APP_VERSION="$APP_VERSION" python3 "$STORE_MIGRATION_SCRIPT" rollback >/tmp/sbc5_migration_rollback.log 2>&1; then
        log "Store Migration: rollback zakończony."
        ha_publish_action_result ok migration_rollback "Przywrócono stan wersji sklepowej sprzed importu. Uruchom ponownie aplikację."
      else
        log "Store Migration: rollback niedostępny lub nieudany; $(tr '\n' ' ' </tmp/sbc5_migration_rollback.log 2>/dev/null || true)"
        ha_publish_action_result error migration_rollback "Brak poprawnego backupu migracji do przywrócenia."
      fi ;;
    cleanup_update_packages) load_options; cleanup_local_update_archives "manual_command" ;;
    reload_config)
      load_options
      detect_custom_curve_config_change
      if [ "$CUSTOM_CURVE_CONFIG_CHANGED" = "true" ]; then
        if write_overlay_profile custom1; then commit_custom_curve_config_signature; fi
      fi
      ha_sync_profile_options
      ha_publish_curve_editor_state || true
      sync_cpu_profile_from_options true || true
      sync_gpu_profile_from_options true || true
      if [ "$CONFIG_TXT_OPTIONS_ENABLED" = "true" ]; then sync_config_txt_from_options true || true; fi
      supervisor_sync_profile_state_to_store || true
      publish_telemetry_snapshot || true
      ha_sync_cpu_gpu_profile_selectors || true
      LAST_PROFILE_STATE_OPTIONS_SIGNATURE="$(profile_state_options_signature)"
      log "Wczytano konfigurację i zsynchronizowano profile CPU/GPU pomiędzy YAML, Ingress i natywną Konfiguracją." ;;
    calibrate_fan)
      if run_fan_calibration; then
        ha_publish_action_result ok calibrate_fan "Kalibracja Active Cooler zakończona; mapa PWM 1% jest gotowa."
      else
        rc=$?
        if [ "$rc" -eq 2 ]; then
          ha_publish_action_result error calibrate_fan "Siatka PWM 1% wymaga zastosowania custom1 i pełnego restartu hosta przed kalibracją."
        else
          ha_publish_action_result error calibrate_fan "Kalibracja Active Cooler nie została zakończona; sprawdź sensor.sbc5_fan_calibration i log aplikacji."
        fi
      fi ;;
    fan_calibration_refresh)
      fan_calibration_init_storage || true
      fan_calibration_force_runtime_sync
      ha_publish_action_result ok fan_calibration_refresh "Odświeżono trwały stan kalibracji Active Cooler i relay Home Assistant." ;;
    curve_editor_refresh)
      load_options
      ha_sync_profile_options || true
      ha_publish_curve_editor_state || true
      log "Curve Editor: odświeżono dane edytora."
      ha_publish_action_result ok curve_editor_refresh "Dane 5 krzywych zostały zsynchronizowane." ;;
    set_cpu_profile)
      cpu_profile_code="$(printf '%s' "$line" | jq -r '.cpu_profile // empty' 2>/dev/null || true)"
      case "$cpu_profile_code" in factory|mild|balanced|performance|experimental|advanced) ;;
        *)
          log "CPU Profile Manager: odrzucono nieprawidłowy profil z Lovelace: ${cpu_profile_code:-brak}."
          ha_publish_action_result error set_cpu_profile "Nieprawidłowy profil CPU/OC."
          continue ;;
      esac
      if [ ! -r "$OPTIONS_FILE" ]; then
        log "CPU Profile Manager: brak $OPTIONS_FILE — nie można zapisać profilu ${cpu_profile_code}."
        ha_publish_action_result error set_cpu_profile "Brak options.json — profil CPU/OC nie został zapisany."
        continue
      fi
      cpu_profile_tmp="${OPTIONS_FILE}.cpu_profile.$$"
      if jq --arg p "$cpu_profile_code" '.section_cpu_enabled=true | .config_cpu_profile=$p' "$OPTIONS_FILE" > "$cpu_profile_tmp" 2>/dev/null; then
        mv -f "$cpu_profile_tmp" "$OPTIONS_FILE"
      else
        rm -f "$cpu_profile_tmp"
        ha_publish_action_result error set_cpu_profile "Nie udało się zapisać wyboru profilu CPU/OC."
        continue
      fi
      if [ "$cpu_profile_code" = "advanced" ]; then
        cpu_profile_cfg="$(jq -c '.config_cpu // {}' "$OPTIONS_FILE" 2>/dev/null || echo '{}')"
      else
        cpu_profile_cfg="$(cpu_profile_preset_config_json "$cpu_profile_code")"
      fi
      if cpu_profile_state_write true "$cpu_profile_code" "lovelace_yaml" true "$cpu_profile_cfg"; then
        cpu_profile_restore_options_from_state || true
        load_options
        if sync_cpu_profile_from_options true; then
          supervisor_sync_profile_state_to_store || true
          cpu_profile_expected="$(cpu_profile_expected_arm_freq "$cpu_profile_code")"
          log "CPU Profile Manager: profil ${cpu_profile_code} wybrany z karty YAML; expected_arm_freq=${cpu_profile_expected:-factory}."
          publish_telemetry_snapshot || true
          ha_sync_cpu_gpu_profile_selectors || true
          LAST_PROFILE_STATE_OPTIONS_SIGNATURE="$(profile_state_options_signature)"
          ha_publish_action_result ok set_cpu_profile "Wybrano profil CPU/OC ${cpu_profile_code}. YAML, Ingress i natywna Konfiguracja zostały zsynchronizowane; jeśli zmienił config.txt, Restart Manager zgłosi pełny restart hosta."
        else
          ha_publish_action_result error set_cpu_profile "Profil zapisano jako żądany, ale nie udało się zsynchronizować config.txt."
        fi
      else
        ha_publish_action_result error set_cpu_profile "Nie udało się utrwalić stanu CPU Profile Manager."
      fi ;;
    set_gpu_profile)
      gpu_profile_code="$(printf '%s' "$line" | jq -r '.gpu_profile // empty' 2>/dev/null || true)"
      case "$gpu_profile_code" in factory|eco|balanced|performance|experimental|advanced) ;;
        *)
          log "GPU Profile Manager: odrzucono nieprawidłowy profil z Lovelace: ${gpu_profile_code:-brak}."
          ha_publish_action_result error set_gpu_profile "Nieprawidłowy profil GPU/V3D/ISP."
          continue ;;
      esac
      if [ ! -r "$OPTIONS_FILE" ]; then
        log "GPU Profile Manager: brak $OPTIONS_FILE — nie można zapisać profilu ${gpu_profile_code}."
        ha_publish_action_result error set_gpu_profile "Brak options.json — profil GPU/V3D/ISP nie został zapisany."
        continue
      fi
      gpu_profile_tmp="${OPTIONS_FILE}.gpu_profile.$$"
      # Akcja z karty jest świadomym żądaniem zastosowania profilu: włącz sekcję GPU i Config Manager.
      if jq --arg p "$gpu_profile_code" '.section_gpu_enabled=true | .config_txt_manager.enabled=true | .config_gpu_profile=$p' "$OPTIONS_FILE" > "$gpu_profile_tmp" 2>/dev/null; then
        mv -f "$gpu_profile_tmp" "$OPTIONS_FILE"
      else
        rm -f "$gpu_profile_tmp"
        ha_publish_action_result error set_gpu_profile "Nie udało się zapisać wyboru profilu GPU/V3D/ISP."
        continue
      fi
      if [ "$gpu_profile_code" = "advanced" ]; then
        gpu_profile_cfg="$(jq -c '.config_gpu // {}' "$OPTIONS_FILE" 2>/dev/null || echo '{}')"
      else
        gpu_profile_cfg="$(gpu_profile_preset_config_json "$gpu_profile_code")"
      fi
      if ! gpu_profile_state_write true "$gpu_profile_code" "lovelace_yaml" true "$gpu_profile_cfg"; then
        ha_publish_action_result error set_gpu_profile "Nie udało się utrwalić stanu GPU Profile Manager."
        continue
      fi
      gpu_profile_restore_options_from_state || true
      load_options
      if sync_config_txt_from_options true; then
        supervisor_sync_profile_state_to_store || true
        publish_telemetry_snapshot || true
        log "GPU Profile Manager: profil ${gpu_profile_code} wybrany z karty YAML; zapisano trwały stan ${GPU_PROFILE_STATE_FILE} i zsynchronizowano Config Manager."
        ha_sync_cpu_gpu_profile_selectors || true
        LAST_PROFILE_STATE_OPTIONS_SIGNATURE="$(profile_state_options_signature)"
        ha_publish_action_result ok set_gpu_profile "Wybrano profil GPU/V3D/ISP ${gpu_profile_code}. YAML, Ingress i natywna Konfiguracja zostały zsynchronizowane; jeśli config.txt uległ zmianie, Restart Manager zgłosi pełny restart Raspberry Pi 5."
      else
        ha_publish_action_result error set_gpu_profile "Profil zapisano jako żądany, ale nie udało się zsynchronizować config.txt."
      fi ;;
    ux_self_test)
      ux_self_test || true ;;
    set_custom_curve_template)
      curve_idx="$(printf '%s' "$line" | jq -r '.curve_index // 1' 2>/dev/null || echo 1)"
      curve_name="$(printf '%s' "$line" | jq -r '.name // ("Profil " + ((.curve_index // 1)|tostring))' 2>/dev/null || echo "Profil $curve_idx")"
      curve_target="$(printf '%s' "$line" | jq -r '.target_temp_c // 50' 2>/dev/null || echo 50)"
      curve_hd="$(printf '%s' "$line" | jq -r '.hysteresis_dense_c // 0.75' 2>/dev/null || echo 0.75)"
      curve_ho="$(printf '%s' "$line" | jq -r '.hysteresis_outer_c // 1.0' 2>/dev/null || echo 1.0)"
      curve_min="$(printf '%s' "$line" | jq -r '.min_pwm_percent // 29' 2>/dev/null || echo 29)"
      curve_tgt="$(printf '%s' "$line" | jq -r '.target_pwm_percent // 55' 2>/dev/null || echo 55)"
      curve_max="$(printf '%s' "$line" | jq -r '.max_pwm_percent // 100' 2>/dev/null || echo 100)"
      curve_response="$(printf '%s' "$line" | jq -r '.response_mode // "precise"' 2>/dev/null || echo precise)"
      if set_custom_curve_template "$curve_idx" "$curve_name" "$curve_target" "$curve_hd" "$curve_ho" "$curve_min" "$curve_tgt" "$curve_max" "$curve_response"; then
        ha_publish_action_result ok set_custom_curve_template "Zapisano generator krzywej $curve_idx."
      else
        ha_publish_action_result error set_custom_curve_template "Nie zapisano krzywej $curve_idx — sprawdź zakresy i kolejność PWM."
      fi ;;
    set_custom_curve_point)
      curve_idx="$(printf '%s' "$line" | jq -r '.curve_index // 1' 2>/dev/null || echo 1)"
      curve_point="$(printf '%s' "$line" | jq -r '.point_index // 1' 2>/dev/null || echo 1)"
      curve_temp="$(printf '%s' "$line" | jq -r '.temp_c // 44' 2>/dev/null || echo 44)"
      curve_hyst="$(printf '%s' "$line" | jq -r '.hysteresis_c // 1.0' 2>/dev/null || echo 1.0)"
      curve_pwm="$(printf '%s' "$line" | jq -r '.pwm_percent // 29' 2>/dev/null || echo 29)"
      if set_custom_curve_point "$curve_idx" "$curve_point" "$curve_temp" "$curve_hyst" "$curve_pwm"; then
        ha_publish_action_result ok set_custom_curve_point "Zapisano punkt $curve_point krzywej $curve_idx."
      else
        ha_publish_action_result error set_custom_curve_point "Punkt odrzucony — temperatura musi rosnąć, a PWM nie może maleć."
      fi ;;
    reset_custom_curve_parameter)
      curve_idx="$(printf '%s' "$line" | jq -r '.curve_index // 1' 2>/dev/null || echo 1)"
      curve_parameter="$(printf '%s' "$line" | jq -r '.parameter // empty' 2>/dev/null || true)"
      if reset_custom_curve_parameter "$curve_idx" "$curve_parameter"; then
        ha_publish_action_result ok reset_custom_curve_parameter "Przywrócono domyślny parametr '$curve_parameter' krzywej $curve_idx."
      else
        ha_publish_action_result error reset_custom_curve_parameter "Nie udało się przywrócić parametru '$curve_parameter'."
      fi ;;
    reset_custom_curve_factory)
      curve_idx="$(printf '%s' "$line" | jq -r '.curve_index // 1' 2>/dev/null || echo 1)"
      if reset_custom_curve_factory "$curve_idx"; then
        ha_publish_action_result ok reset_custom_curve_factory "Krzywa $curve_idx została przywrócona do wartości domyślnych."
      else
        ha_publish_action_result error reset_custom_curve_factory "Nie udało się przywrócić krzywej $curve_idx."
      fi ;;
    reset_all_custom_curves_factory)
      if reset_all_custom_curves_factory; then
        ha_publish_action_result ok reset_all_custom_curves_factory "Przywrócono wszystkie 5 krzywych."
      else
        ha_publish_action_result error reset_all_custom_curves_factory "Nie udało się przywrócić wszystkich krzywych."
      fi ;;
    apply_ai_grid_suggestion)
      confirmed="$(printf '%s' "$line" | jq -r '.confirm // false' 2>/dev/null || echo false)"
      if apply_ai_grid_suggestion "$confirmed"; then
        ha_publish_action_result ok apply_ai_grid_suggestion "Zastosowano sugestię AI Grid. Zapisano nową geometrię custom1; wymagany restart hosta."
      else
        ha_publish_action_result error apply_ai_grid_suggestion "Nie zastosowano sugestii AI Grid — sugestia może być niedostępna, nieaktualna lub zapis overlay nie powiódł się."
      fi ;;
    clear_ai_grid_override)
      if clear_ai_grid_override; then
        ha_publish_action_result ok clear_ai_grid_override "Przywrócono automatyczną siatkę temperatur z konfiguracji aplikacji; wymagany restart hosta."
      else
        ha_publish_action_result error clear_ai_grid_override "Nie udało się przywrócić automatycznej siatki."
      fi ;;
    reset_custom_curve)
      curve_idx="$(printf '%s' "$line" | jq -r '.curve_index // 1' 2>/dev/null || echo 1)"
      reset_custom_curve_editor_override "$curve_idx" || true ;;
    restore_active_cooler_factory)
      confirmed="$(printf '%s' "$line" | jq -r '.confirm // false' 2>/dev/null || echo false)"
      if [ "$confirmed" != "true" ]; then
        log "Fabryczne chłodzenie: ODRZUCONO — wymagane jawne confirm=true."
        ha_publish_action_result error restore_active_cooler_factory "Przywrócenie fabrycznego Active Coolera wymaga potwierdzenia użytkownika."
      elif [ -e "$FAN_CALIBRATION_LOCK_FILE" ]; then
        log "Fabryczne chłodzenie: odmowa podczas trwającej kalibracji."
        ha_publish_action_result error restore_active_cooler_factory "Najpierw poczekaj na zakończenie kalibracji Active Cooler."
      elif write_4point_profile factory; then
        ha_publish_action_result ok restore_active_cooler_factory "Przywrócono fabryczną charakterystykę Active Cooler SBC5. Wykonaj pełny restart hosta, aby kernel wczytał ustawienia."
      else
        ha_publish_action_result error restore_active_cooler_factory "Nie udało się przywrócić fabrycznej charakterystyki Active Cooler. Sprawdź log aplikacji."
      fi ;;
    restore_rpi5_app_defaults)
      confirmed="$(printf '%s' "$line" | jq -r '.confirm // false' 2>/dev/null || echo false)"
      if restore_rpi5_app_defaults "$confirmed"; then
        ha_publish_action_result ok restore_rpi5_app_defaults "Cofnięto zmiany SBC5 zarządzane przez Control Center. Ręczne wpisy użytkownika zachowano. Wymagany pełny restart hosta."
      else
        ha_publish_action_result error restore_rpi5_app_defaults "Nie przywrócono ustawień SBC5 — sprawdź potwierdzenie, kalibrację i log aplikacji."
      fi ;;
    resume_managed_rpi5_config)
      confirmed="$(printf '%s' "$line" | jq -r '.confirm // false' 2>/dev/null || echo false)"
      if resume_managed_rpi5_config "$confirmed"; then
        ha_publish_action_result ok resume_managed_rpi5_config "Ponownie zezwolono Control Center na zarządzanie ustawieniami SBC5/config.txt."
      else
        ha_publish_action_result error resume_managed_rpi5_config "Wznowienie zarządzania wymaga potwierdzenia użytkownika."
      fi ;;
    diagnose) diagnose_overlay || true ;;
    restore_backup) restore_backup || true ;;
    apply_system_config)
      cpu_mode="$(printf '%s' "$line" | jq -r '.cpu_mode // "factory"' 2>/dev/null || echo factory)"
      arm_mhz="$(printf '%s' "$line" | jq -r '.arm_freq_mhz // 2400' 2>/dev/null || echo 2400)"
      ovd_uv="$(printf '%s' "$line" | jq -r '.over_voltage_delta_uv // 0' 2>/dev/null || echo 0)"
      usb_mode="$(printf '%s' "$line" | jq -r '.usb_current_mode // "auto"' 2>/dev/null || echo auto)"
      confirmed="$(printf '%s' "$line" | jq -r '.confirm // false' 2>/dev/null || echo false)"
      if apply_system_config "$cpu_mode" "$arm_mhz" "$ovd_uv" "$usb_mode" "$confirmed"; then
        ha_publish_action_result ok apply_system_config "Konfiguracja CPU/USB została zapisana."
      else
        ha_publish_action_result error apply_system_config "Zapis CPU/USB został odrzucony. Sprawdź log i konflikty config.txt."
      fi ;;
    restore_system_config_backup)
      confirmed="$(printf '%s' "$line" | jq -r '.confirm // false' 2>/dev/null || echo false)"
      if [ "$confirmed" = "true" ]; then restore_system_config_backup || true; else log "System Config Restore: ODRZUCONO — wymagane confirm=true."; fi ;;
    apply_config_txt_parameter)
      section="$(printf '%s' "$line" | jq -r '.section // "pi5"' 2>/dev/null || echo pi5)"
      key="$(printf '%s' "$line" | jq -r '.key // empty' 2>/dev/null || true)"
      value="$(printf '%s' "$line" | jq -r '.value // empty' 2>/dev/null || true)"
      advanced="$(printf '%s' "$line" | jq -r '.advanced // false' 2>/dev/null || echo false)"
      confirmed="$(printf '%s' "$line" | jq -r '.confirm // false' 2>/dev/null || echo false)"
      apply_config_txt_parameter "$section" "$key" "$value" "$advanced" "$confirmed" || true ;;
    remove_config_txt_parameter)
      section="$(printf '%s' "$line" | jq -r '.section // "pi5"' 2>/dev/null || echo pi5)"
      key="$(printf '%s' "$line" | jq -r '.key // empty' 2>/dev/null || true)"
      value="$(printf '%s' "$line" | jq -r '.value // empty' 2>/dev/null || true)"
      confirmed="$(printf '%s' "$line" | jq -r '.confirm // false' 2>/dev/null || echo false)"
      remove_config_txt_parameter "$section" "$key" "$value" "$confirmed" || true ;;
    restore_config_manager_backup)
      confirmed="$(printf '%s' "$line" | jq -r '.confirm // false' 2>/dev/null || echo false)"
      restore_config_manager_backup "$confirmed" || true ;;
    restart_status) publish_restart_requirement true ;;
    restart_ha_confirmed) restart_home_assistant_confirmed || true ;;
    check_updates|check_app_update) check_app_update || true ;;
    install_local_update) install_local_update || true ;;
    *) log "Nieobsługiwane polecenie." ;;
  esac
done
