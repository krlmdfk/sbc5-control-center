#!/usr/bin/env python3
"""Build-time Adaptive Trim Recovery patch for SBC5 Control Center 3.1.31.

Applied after the 3.1.29 thermal-control patch. It adds fused-trend-aware
anti-windup without changing AI Cooling or Thermal Predictor authority limits.
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
        '  local thermal_signal="" thermal_trend_30="0.0" thermal_trend_120="0.0" thermal_direction="neutral" thermal_spike_rejected=0 thermal_candidate_streak=0 thermal_reverse_hold=0 thermal_signal_quality="warming_up" thermal_median_milli=0\n',
        '  local thermal_signal="" thermal_trend_30="0.0" thermal_trend_120="0.0" thermal_trend_fused="0.0" thermal_trend_fused_milli=0 thermal_direction="neutral" thermal_spike_rejected=0 thermal_candidate_streak=0 thermal_reverse_hold=0 thermal_signal_quality="warming_up" thermal_median_milli=0\n',
        "fused trend controller variables",
    )

    text = replace_once(
        text,
        '    thermal_trend_30="0.0"; thermal_trend_120="0.0"; thermal_direction="neutral"\n',
        '    thermal_trend_30="0.0"; thermal_trend_120="0.0"; thermal_trend_fused="0.0"; thermal_trend_fused_milli=0; thermal_direction="neutral"\n',
        "fused trend reset",
    )

    text = replace_once(
        text,
        "        IFS=$'\\t' read -r temp_control_milli thermal_trend_30 thermal_trend_120 thermal_direction thermal_spike_rejected thermal_candidate_streak thermal_reverse_hold thermal_signal_quality thermal_median_milli <<< \"$thermal_signal\"\n",
        "        IFS=$'\\t' read -r temp_control_milli thermal_trend_30 thermal_trend_120 thermal_trend_fused thermal_trend_fused_milli thermal_direction thermal_spike_rejected thermal_candidate_streak thermal_reverse_hold thermal_signal_quality thermal_median_milli <<< \"$thermal_signal\"\n",
        "fused trend filter output",
    )

    text = replace_once(
        text,
        '        case "$thermal_spike_rejected" in 0|1) ;; *) thermal_spike_rejected=0 ;; esac\n',
        '        case "$thermal_trend_fused_milli" in -[0-9]*|[0-9]*) ;; *) thermal_trend_fused_milli=0 ;; esac\n'
        '        case "$thermal_spike_rejected" in 0|1) ;; *) thermal_spike_rejected=0 ;; esac\n',
        "fused trend validation",
    )

    hot_branch = '''    elif [ "$error" -gt "$deadband_milli" ] 2>/dev/null; then
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
'''
    hot_branch_new = '''    elif [ "$error" -gt "$deadband_milli" ] 2>/dev/null; then
      if [ "$adaptive_trim" -lt 0 ] 2>/dev/null; then adaptive_trim=0; sign_guard="_sign_guard"; fi
      deadband_count=0; low_count=0
      # 3.1.31 Adaptive Trim Anti-Windup: do not accumulate positive trim while
      # the fused thermal trend already shows meaningful cooling. A strong hot
      # condition still uses the direct/fast branches above, so safety response
      # and large-load recovery remain unchanged.
      if [ "$thermal_trend_fused_milli" -le -300 ] 2>/dev/null; then
        up_count=0; up_hold=0
        if [ "$adaptive_trim" -gt 0 ] 2>/dev/null && [ "$error" -le 800 ] 2>/dev/null; then
          adaptive_trim=$((adaptive_trim - 1)); [ "$adaptive_trim" -lt 0 ] 2>/dev/null && adaptive_trim=0
          action="trim_recovery_cooling"
        else
          action="trim_up_blocked_cooling"
        fi
      elif [ "$thermal_trend_fused_milli" -le -200 ] 2>/dev/null; then
        up_count=0; [ "$up_hold" -gt 0 ] 2>/dev/null && up_hold=$((up_hold - 1))
        action="trim_up_blocked_fused_trend"
      elif [ "$up_hold" -gt 0 ] 2>/dev/null; then
        up_hold=$((up_hold - 1)); up_count=0; action="trim_up_hold_${up_hold}${sign_guard}"
      else
        up_count=$((up_count + 1)); action="trim_up_confirm_${up_count}${sign_guard}"
        if [ "$up_count" -ge "$up_confirm_cycles" ] 2>/dev/null; then
          adaptive_trim=$((adaptive_trim + 1)); action="trim_up_confirmed${sign_guard}"; up_count=0; up_hold="$up_hold_cycles"
        fi
      fi
'''
    text = replace_once(text, hot_branch, hot_branch_new, "positive trim anti-windup")

    deadband = '''    else
      low_count=0; up_count=0; [ "$up_hold" -gt 0 ] 2>/dev/null && up_hold=$((up_hold - 1))
      deadband_count=$((deadband_count + 1))
      if [ "$error" -le $((-trim_sign_threshold)) ] 2>/dev/null && [ "$adaptive_trim" -gt 0 ] 2>/dev/null; then
'''
    deadband_new = '''    else
      low_count=0; up_count=0; [ "$up_hold" -gt 0 ] 2>/dev/null && up_hold=$((up_hold - 1))
      deadband_count=$((deadband_count + 1))
      # Near target, release stale positive trim faster when the controller is
      # neutral/cooling. This is bounded to 2 pp per control cycle and never
      # changes the ±12 pp trim envelope or actuator slew limits.
      if [ "$adaptive_trim" -gt 0 ] 2>/dev/null && [ "$error" -le 800 ] 2>/dev/null && [ "$error" -ge -800 ] 2>/dev/null && { [ "$thermal_direction" = "neutral" ] || [ "$thermal_trend_fused_milli" -le -300 ] 2>/dev/null; }; then
        adaptive_trim=$((adaptive_trim - 2)); [ "$adaptive_trim" -lt 0 ] 2>/dev/null && adaptive_trim=0
        action="deadband_trim_recovery_fast"; deadband_count=0
      elif [ "$error" -le $((-trim_sign_threshold)) ] 2>/dev/null && [ "$adaptive_trim" -gt 0 ] 2>/dev/null; then
'''
    text = replace_once(text, deadband, deadband_new, "near-target trim recovery")

    text = replace_once(
        text,
        '              log "Adaptive PWM: T_raw=$(millideg_to_c_1dp "$temp_milli")°C T_control=$(millideg_to_c_1dp "$temp_control_milli")°C target=${CURVE1_TARGET_C}°C trend30=${thermal_trend_30}C/min trend120=${thermal_trend_120}C/min direction=${thermal_direction}; curve=${curve_state}% trim=${adaptive_trim}pp controller ${current}->${desired}/${max_state} (${action}); owner=adaptive."\n',
        '              log "Adaptive PWM: T_raw=$(millideg_to_c_1dp "$temp_milli")°C T_control=$(millideg_to_c_1dp "$temp_control_milli")°C target=${CURVE1_TARGET_C}°C trend30=${thermal_trend_30}C/min trend120=${thermal_trend_120}C/min trendF=${thermal_trend_fused}C/min direction=${thermal_direction}; curve=${curve_state}% trim=${adaptive_trim}pp controller ${current}->${desired}/${max_state} (${action}); owner=adaptive."\n',
        "adaptive fused-trend log",
    )

    text = replace_once(
        text,
        'log "Adaptive PWM: control_mode=${COOLING_CONTROL_MODE}; enabled=${ADAPTIVE_PWM_ENABLED}; deadband=±${ADAPTIVE_PWM_DEADBAND_C}°C; interval=${ADAPTIVE_PWM_INTERVAL_SECONDS}s; T_raw=safety; T_control=median3+asymmetric-EWMA; trends=30/120s; direction_hysteresis=2-cycle confirm + 2-cycle reversal hold; up_confirm=2; anti_windup_hold=3 cykle; down_confirm=${ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES}; grid=1%; baza=custom1(T_control)+bounded trim ±12pp; deadband=actuator-hold + sign-aware decay + trim leak 1pp/~10s; sign_guard=enabled; curve_cache=hot-reload; owner=exclusive auto(user_space|mode_disabled); reentry=slew-limited; actuator slew=+3/-4pp na cykl (fast-up +8pp @ +5°C; critical-up +12pp @ +7°C; fast-down -5pp); telemetry runtime=canonical relay schema 10."\n',
        'log "Adaptive PWM: control_mode=${COOLING_CONTROL_MODE}; enabled=${ADAPTIVE_PWM_ENABLED}; deadband=±${ADAPTIVE_PWM_DEADBAND_C}°C; interval=${ADAPTIVE_PWM_INTERVAL_SECONDS}s; T_raw=safety; T_control=median3+asymmetric-EWMA; trends=30/120s + fused(65/35); direction_hysteresis=2-cycle confirm + 2-cycle reversal hold; up_confirm=2; anti_windup=trend-aware + near-target fast recovery; down_confirm=${ADAPTIVE_PWM_DOWN_CONFIRM_CYCLES}; grid=1%; baza=custom1(T_control)+bounded trim ±12pp; deadband=actuator-hold + sign-aware decay + trim recovery; sign_guard=enabled; curve_cache=hot-reload; owner=exclusive auto(user_space|mode_disabled); reentry=slew-limited; actuator slew=+3/-4pp na cykl (fast-up +8pp @ +5°C; critical-up +12pp @ +7°C; fast-down -5pp); telemetry runtime=canonical relay schema 10."\n',
        "startup anti-windup diagnostics",
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
