#!/usr/bin/env python3
"""Build-time patch for SBC5 3.1.29 thermal control stability.

The compatibility control plane is intentionally kept as one audited source file.
This patch is applied during the container build and is regression-tested in CI.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch(text: str) -> str:
    text = replace_once(
        text,
        'ADAPTIVE_PWM_STATE_FILE="/homeassistant/sbc5_control_center/adaptive_pwm.json"\n',
        'ADAPTIVE_PWM_STATE_FILE="/homeassistant/sbc5_control_center/adaptive_pwm.json"\n'
        'THERMAL_CONTROL_FILTER_SCRIPT="/thermal_control_filter.py"\n'
        'THERMAL_CONTROL_FILTER_STATE_FILE="/data/thermal_control_filter.json"\n'
        'THERMAL_CONTROL_FILTER_MIRROR_FILE="/homeassistant/sbc5_control_center/thermal_control_filter.json"\n',
        "thermal filter constants",
    )

    old_status = '''adaptive_pwm_write_status() {
  local state="$1" action="$2" temp_milli="${3:-0}" current="${4:-0}" desired="${5:-0}" max_state="${6:-0}" writable="${7:-false}"
  local owner="${8:-kernel}" zone="${9:-}" controller="${10:-$desired}" base="${11:-$current}" original_policy="${12:-}" adaptive_trim_pp="${13:-0}"
  local temp_c target_c now
  temp_c="$(millideg_to_c_1dp "$temp_milli" 2>/dev/null || echo 0.0)"
  target_c="$CURVE1_TARGET_C"
  now="${EPOCHREALTIME:-0}"
  mkdir -p "$(dirname "$ADAPTIVE_PWM_STATE_FILE")" 2>/dev/null || true
  printf '{"sample_epoch":%s,"state":"%s","action":"%s","temperature_c":%s,"target_c":%s,"deadband_c":%s,"current_level":%s,"requested_level":%s,"controller_level":%s,"base_level":%s,"adaptive_trim_pp":%s,"max_level":%s,"writable":%s,"control_owner":"%s","thermal_zone":"%s","original_policy":"%s"}\\n' \\
    "$now" "$state" "$action" "$temp_c" "$target_c" "$ADAPTIVE_PWM_DEADBAND_C" "$current" "$desired" "$controller" "$base" "$adaptive_trim_pp" "$max_state" "$writable" "$owner" "$zone" "$original_policy" \\
    > "$ADAPTIVE_PWM_STATE_FILE" 2>/dev/null || true
}
'''
    new_status = '''adaptive_pwm_write_status() {
  local state="$1" action="$2" temp_milli="${3:-0}" current="${4:-0}" desired="${5:-0}" max_state="${6:-0}" writable="${7:-false}"
  local owner="${8:-kernel}" zone="${9:-}" controller="${10:-$desired}" base="${11:-$current}" original_policy="${12:-}" adaptive_trim_pp="${13:-0}"
  local temp_c control_temp_c target_c now trend30 trend120 direction signal_quality spike_rejected
  temp_c="$(millideg_to_c_1dp "$temp_milli" 2>/dev/null || echo 0.0)"
  control_temp_c="$(millideg_to_c_1dp "${temp_control_milli:-$temp_milli}" 2>/dev/null || echo "$temp_c")"
  trend30="${thermal_trend_30:-0.0}"; trend120="${thermal_trend_120:-0.0}"
  direction="${thermal_direction:-neutral}"; signal_quality="${thermal_signal_quality:-unknown}"
  spike_rejected="${thermal_spike_rejected:-0}"; [ "$spike_rejected" = "1" ] && spike_rejected=true || spike_rejected=false
  target_c="$CURVE1_TARGET_C"
  now="${EPOCHREALTIME:-0}"
  mkdir -p "$(dirname "$ADAPTIVE_PWM_STATE_FILE")" 2>/dev/null || true
  printf '{"sample_epoch":%s,"state":"%s","action":"%s","temperature_c":%s,"temperature_raw_c":%s,"temperature_control_c":%s,"temperature_trend_30s_c_per_min":%s,"temperature_trend_120s_c_per_min":%s,"thermal_direction":"%s","thermal_signal_quality":"%s","spike_rejected":%s,"target_c":%s,"deadband_c":%s,"current_level":%s,"requested_level":%s,"controller_level":%s,"base_level":%s,"adaptive_trim_pp":%s,"max_level":%s,"writable":%s,"control_owner":"%s","thermal_zone":"%s","original_policy":"%s"}\\n' \\
    "$now" "$state" "$action" "$temp_c" "$temp_c" "$control_temp_c" "$trend30" "$trend120" "$direction" "$signal_quality" "$spike_rejected" "$target_c" "$ADAPTIVE_PWM_DEADBAND_C" "$current" "$desired" "$controller" "$base" "$adaptive_trim_pp" "$max_state" "$writable" "$owner" "$zone" "$original_policy" \\
    > "$ADAPTIVE_PWM_STATE_FILE" 2>/dev/null || true
}
'''
    text = replace_once(text, old_status, new_status, "adaptive status diagnostics")

    text = replace_once(
        text,
        '  local dev="" temp_milli=0 target_milli=0 deadband_milli=200 error=0 current=0 max_state=0 desired=0 actual_after=0\n',
        '  local dev="" temp_milli=0 temp_control_milli=0 target_milli=0 deadband_milli=200 error=0 current=0 max_state=0 desired=0 actual_after=0\n',
        "controller temperature variables",
    )
    text = replace_once(
        text,
        '  local reload_token="" reload_now=""\n',
        '  local thermal_signal="" thermal_trend_30="0.0" thermal_trend_120="0.0" thermal_direction="neutral" thermal_spike_rejected=0 thermal_candidate_streak=0 thermal_reverse_hold=0 thermal_signal_quality="warming_up" thermal_median_milli=0\n'
        '  local reload_token="" reload_now=""\n',
        "controller filter variables",
    )

    invalid_block = '''    if [ "$temp_milli" -le 0 ] 2>/dev/null; then
      fan_control_release_thermal_ownership adaptive invalid_temperature >/dev/null 2>&1 || true
      controller_state=-1; base_state=-1; low_count=0; up_count=0; up_hold=0; deadband_count=0
      adaptive_pwm_write_status fallback invalid_temperature "$temp_milli" "$current" "$current" "$max_state" false kernel "" "$current" "$current" ""
      sleep "$ADAPTIVE_PWM_INTERVAL_SECONDS"
      continue
    fi

'''
    filter_block = invalid_block + '''    # 3.1.29 Thermal Control Stability: keep raw CPU temperature authoritative for
    # emergency/safety paths, but condition the normal control signal with a
    # median-of-3 spike guard plus asymmetric EWMA and robust 30/120 s trends.
    temp_control_milli="$temp_milli"
    thermal_trend_30="0.0"; thermal_trend_120="0.0"; thermal_direction="neutral"
    thermal_spike_rejected=0; thermal_candidate_streak=0; thermal_reverse_hold=0; thermal_signal_quality="fallback_raw"; thermal_median_milli="$temp_milli"
    if [ -x "$THERMAL_CONTROL_FILTER_SCRIPT" ]; then
      thermal_signal="$(python3 "$THERMAL_CONTROL_FILTER_SCRIPT" --temp-milli "$temp_milli" --target-milli "$target_milli" --state "$THERMAL_CONTROL_FILTER_STATE_FILE" --mirror "$THERMAL_CONTROL_FILTER_MIRROR_FILE" 2>/dev/null || true)"
      if [ -n "$thermal_signal" ]; then
        IFS=$'\\t' read -r temp_control_milli thermal_trend_30 thermal_trend_120 thermal_direction thermal_spike_rejected thermal_candidate_streak thermal_reverse_hold thermal_signal_quality thermal_median_milli <<< "$thermal_signal"
        case "$temp_control_milli" in ''|*[!0-9-]*) temp_control_milli="$temp_milli" ;; esac
        case "$thermal_spike_rejected" in 0|1) ;; *) thermal_spike_rejected=0 ;; esac
        case "$thermal_candidate_streak" in ''|*[!0-9]*) thermal_candidate_streak=0 ;; esac
        case "$thermal_reverse_hold" in ''|*[!0-9]*) thermal_reverse_hold=0 ;; esac
        case "$thermal_direction" in hot|cool|neutral) ;; *) thermal_direction="neutral" ;; esac
      fi
    fi

'''
    text = replace_once(text, invalid_block, filter_block, "thermal filter evaluation")

    count = text.count('adaptive_pwm_curve_state_for_temp "$temp_milli"')
    if count != 2:
        raise SystemExit(f"curve control temperature: expected 2 matches, found {count}")
    text = text.replace('adaptive_pwm_curve_state_for_temp "$temp_milli"', 'adaptive_pwm_curve_state_for_temp "$temp_control_milli"')
    text = replace_once(
        text,
        '    error=$((temp_milli - target_milli))\n',
        '    error=$((temp_control_milli - target_milli))\n',
        "control error temperature",
    )

    text = replace_once(
        text,
        '    elif [ "$error" -le $((-down_direct_delta)) ] 2>/dev/null; then\n',
        '    elif [ "$error" -le $((-down_direct_delta)) ] 2>/dev/null && { [ "$thermal_direction" = "cool" ] || [ "$error" -le $((-down_fast_delta)) ] 2>/dev/null; }; then\n',
        "downward direct trend guard",
    )
    text = replace_once(
        text,
        '    elif [ "$error" -lt $((-deadband_milli)) ] 2>/dev/null; then\n',
        '    elif [ "$error" -lt $((-deadband_milli)) ] 2>/dev/null && [ "$thermal_direction" = "cool" ]; then\n',
        "downward confirm trend guard",
    )

    text = replace_once(
        text,
        '              log "Adaptive PWM: T=$(millideg_to_c_1dp "$temp_milli")°C target=${CURVE1_TARGET_C}°C curve=${curve_state}% trim=${adaptive_trim}pp controller ${current}->${desired}/${max_state} (${action}); owner=adaptive."\n',
        '              log "Adaptive PWM: T_raw=$(millideg_to_c_1dp "$temp_milli")°C T_control=$(millideg_to_c_1dp "$temp_control_milli")°C target=${CURVE1_TARGET_C}°C trend30=${thermal_trend_30}C/min trend120=${thermal_trend_120}C/min direction=${thermal_direction}; curve=${curve_state}% trim=${adaptive_trim}pp controller ${current}->${desired}/${max_state} (${action}); owner=adaptive."\n',
        "adaptive log diagnostics",
    )

    text = replace_once(
        text,
        'log "Adaptive PWM: control_mode=${COOLING_CONTROL_MODE}; enabled=${ADAPTIVE_PWM_ENABLED}; deadband=±${ADAPTIVE_PWM_DEADBAND_C}°C; interval=${ADAPTIVE_PWM_INTERVAL_SECONDS}s; up_confirm=2; anti_windup_hold=3 cykle; down_confirm=${ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES}; grid=1%; baza=custom1(T)+bounded trim ±12pp; deadband=actuator-hold + sign-aware decay + trim leak 1pp/~10s; sign_guard=enabled; curve_cache=hot-reload; owner=exclusive auto(user_space|mode_disabled); reentry=slew-limited; actuator slew=+3/-4pp na cykl (fast-up +8pp @ +5°C; critical-up +12pp @ +7°C; fast-down -5pp); telemetry runtime=canonical relay schema 10."\n',
        'log "Adaptive PWM: control_mode=${COOLING_CONTROL_MODE}; enabled=${ADAPTIVE_PWM_ENABLED}; deadband=±${ADAPTIVE_PWM_DEADBAND_C}°C; interval=${ADAPTIVE_PWM_INTERVAL_SECONDS}s; T_raw=safety; T_control=median3+asymmetric-EWMA; trends=30/120s; direction_hysteresis=2-cycle confirm + 2-cycle reversal hold; up_confirm=2; anti_windup_hold=3 cykle; down_confirm=${ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES}; grid=1%; baza=custom1(T_control)+bounded trim ±12pp; deadband=actuator-hold + sign-aware decay + trim leak 1pp/~10s; sign_guard=enabled; curve_cache=hot-reload; owner=exclusive auto(user_space|mode_disabled); reentry=slew-limited; actuator slew=+3/-4pp na cykl (fast-up +8pp @ +5°C; critical-up +12pp @ +7°C; fast-down -5pp); telemetry runtime=canonical relay schema 10."\n',
        "startup diagnostics",
    )
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    original = path.read_text(encoding="utf-8")
    patched = patch(original)
    path.write_text(patched, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
