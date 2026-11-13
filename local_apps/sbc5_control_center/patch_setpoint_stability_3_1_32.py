#!/usr/bin/env python3
"""Build-time Setpoint Stability patch for SBC5 Control Center 3.1.32.

Applied after the 3.1.29 thermal-control and 3.1.31 Adaptive Trim patches.
It softens near-target trim release, adds a bounded 2-cycle actuator reversal
guard, and improves runtime diagnostics without changing AI Cooling or Thermal
Predictor authority limits.
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
        '  local low_count=0 up_count=0 up_hold=0 deadband_count=0 controller_state=-1 base_state=-1 action="hold" writable=false last_logged="" adaptive_write_log_tick=0 adaptive_log_important=false safety_delta=10000 fast_delta=6000\n',
        '  local low_count=0 up_count=0 up_hold=0 deadband_count=0 controller_state=-1 base_state=-1 action="hold" writable=false last_logged="" adaptive_write_log_tick=0 adaptive_log_important=false safety_delta=10000 fast_delta=6000\n'
        '  local last_actuator_direction="none" reversal_hold=0 reversal_guard_cycles=2 reversal_guard_step=1 requested_before_actuator=0 reversal_limit=0\n',
        "actuator reversal guard variables",
    )

    text = replace_once(
        text,
        '    if [ "$controller_state" -lt 0 ] 2>/dev/null; then\n      local kernel_profile_match=true\n',
        '    if [ "$controller_state" -lt 0 ] 2>/dev/null; then\n      local kernel_profile_match=true\n      last_actuator_direction="none"; reversal_hold=0\n',
        "reversal guard reset on ownership entry",
    )

    old_recovery = '''      if [ "$adaptive_trim" -gt 0 ] 2>/dev/null && [ "$error" -le 800 ] 2>/dev/null && [ "$error" -ge -800 ] 2>/dev/null && { [ "$thermal_direction" = "neutral" ] || [ "$thermal_trend_fused_milli" -le -300 ] 2>/dev/null; }; then
        adaptive_trim=$((adaptive_trim - 2)); [ "$adaptive_trim" -lt 0 ] 2>/dev/null && adaptive_trim=0
        action="deadband_trim_recovery_fast"; deadband_count=0
      elif [ "$error" -le $((-trim_sign_threshold)) ] 2>/dev/null && [ "$adaptive_trim" -gt 0 ] 2>/dev/null; then
'''
    new_recovery = '''      # 3.1.32 Setpoint Stability: the 2 pp fast trim release is reserved for
      # the true near-target zone. While still 0.3..0.8 C above target, release
      # at most 1 pp and only when the fused trend already confirms cooling.
      if [ "$adaptive_trim" -gt 0 ] 2>/dev/null && [ "$error" -le 300 ] 2>/dev/null && [ "$error" -ge -800 ] 2>/dev/null && { [ "$thermal_direction" = "neutral" ] || [ "$thermal_trend_fused_milli" -le -300 ] 2>/dev/null; }; then
        adaptive_trim=$((adaptive_trim - 2)); [ "$adaptive_trim" -lt 0 ] 2>/dev/null && adaptive_trim=0
        action="deadband_trim_recovery_fast"; deadband_count=0
      elif [ "$adaptive_trim" -gt 0 ] 2>/dev/null && [ "$error" -gt 300 ] 2>/dev/null && [ "$error" -le 800 ] 2>/dev/null && [ "$thermal_trend_fused_milli" -le -300 ] 2>/dev/null; then
        adaptive_trim=$((adaptive_trim - 1)); [ "$adaptive_trim" -lt 0 ] 2>/dev/null && adaptive_trim=0
        action="deadband_trim_recovery_soft"; deadband_count=0
      elif [ "$error" -le $((-trim_sign_threshold)) ] 2>/dev/null && [ "$adaptive_trim" -gt 0 ] 2>/dev/null; then
'''
    text = replace_once(text, old_recovery, new_recovery, "setpoint trim recovery")

    marker = '''    # v2.6.9 final actuator guard. AI Assist may nudge the classic target, but
'''
    text = replace_once(
        text,
        marker,
        '    requested_before_actuator="$desired"\n\n' + marker,
        "pre-actuator request capture",
    )

    old_guard_tail = '''      if [ "$desired" -gt $((controller_state + step_up)) ] 2>/dev/null; then
        desired=$((controller_state + step_up)); action="${action}_slew_up"
      elif [ "$desired" -lt $((controller_state - step_down)) ] 2>/dev/null; then
        desired=$((controller_state - step_down)); action="${action}_slew_down"
      fi
      [ "$desired" -lt "$min_run_floor" ] 2>/dev/null && desired="$min_run_floor"
      [ "$desired" -gt "$max_state" ] 2>/dev/null && desired="$max_state"
'''
    new_guard_tail = '''      if [ "$desired" -gt $((controller_state + step_up)) ] 2>/dev/null; then
        desired=$((controller_state + step_up)); action="${action}_slew_up"
      elif [ "$desired" -lt $((controller_state - step_down)) ] 2>/dev/null; then
        desired=$((controller_state - step_down)); action="${action}_slew_down"
      fi

      # 3.1.32 Actuator Reversal Guard: for two controller cycles after a
      # physical PWM movement, an opposite-direction request near the target is
      # limited to 1 pp. A genuine >=2 C error bypasses the guard, and safety_max
      # never enters this block at all.
      if [ "$reversal_hold" -gt 0 ] 2>/dev/null; then
        if [ "$last_actuator_direction" = "up" ] && [ "$desired" -lt "$controller_state" ] 2>/dev/null && [ "$error" -gt -2000 ] 2>/dev/null; then
          reversal_limit=$((controller_state - reversal_guard_step))
          if [ "$desired" -lt "$reversal_limit" ] 2>/dev/null; then desired="$reversal_limit"; action="${action}_reversal_guard"; fi
        elif [ "$last_actuator_direction" = "down" ] && [ "$desired" -gt "$controller_state" ] 2>/dev/null && [ "$error" -lt 2000 ] 2>/dev/null; then
          reversal_limit=$((controller_state + reversal_guard_step))
          if [ "$desired" -gt "$reversal_limit" ] 2>/dev/null; then desired="$reversal_limit"; action="${action}_reversal_guard"; fi
        fi
        reversal_hold=$((reversal_hold - 1))
      fi
      [ "$desired" -lt "$min_run_floor" ] 2>/dev/null && desired="$min_run_floor"
      [ "$desired" -gt "$max_state" ] 2>/dev/null && desired="$max_state"
'''
    text = replace_once(text, old_guard_tail, new_guard_tail, "bounded actuator reversal guard")

    old_success = '''        if [ "$actual_after" -eq "$desired" ] 2>/dev/null; then
          controller_state="$desired"
          adaptive_write_log_tick=$((adaptive_write_log_tick + 1))
'''
    new_success = '''        if [ "$actual_after" -eq "$desired" ] 2>/dev/null; then
          if [ "$desired" -gt "$current" ] 2>/dev/null; then
            last_actuator_direction="up"; reversal_hold="$reversal_guard_cycles"
          elif [ "$desired" -lt "$current" ] 2>/dev/null; then
            last_actuator_direction="down"; reversal_hold="$reversal_guard_cycles"
          fi
          controller_state="$desired"
          adaptive_write_log_tick=$((adaptive_write_log_tick + 1))
'''
    text = replace_once(text, old_success, new_success, "reversal history update")

    old_log = '              log "Adaptive PWM: T_raw=$(millideg_to_c_1dp "$temp_milli")°C T_control=$(millideg_to_c_1dp "$temp_control_milli")°C target=${CURVE1_TARGET_C}°C trend30=${thermal_trend_30}C/min trend120=${thermal_trend_120}C/min trendF=${thermal_trend_fused}C/min direction=${thermal_direction}; curve=${curve_state}% trim=${adaptive_trim}pp controller ${current}->${desired}/${max_state} (${action}); owner=adaptive."\n'
    new_log = '              log "Adaptive PWM: T_raw=$(millideg_to_c_1dp "$temp_milli")°C T_control=$(millideg_to_c_1dp "$temp_control_milli")°C target=${CURVE1_TARGET_C}°C trend30=${thermal_trend_30}C/min trend120=${thermal_trend_120}C/min trendF=${thermal_trend_fused}C/min direction=${thermal_direction}; curve=${curve_state}% trim=${adaptive_trim}pp physical=${current}->${actual_after}/${max_state} request=${requested_before_actuator}% applied=${desired}% reversal=${last_actuator_direction}/${reversal_hold} (${action}); owner=adaptive."\n'
    text = replace_once(text, old_log, new_log, "physical PWM diagnostics")

    old_tp_log = '            log "Thermal Predictor: mode=${tp_mode}; F30=${tp_f30}C F60=${tp_f60}C F120=${tp_f120}C; confidence=${tp_conf}%; MAE_avg=${tp_mae}C; weighted=${tp_weighted}C error=${tp_error}C; weights=${tp_weights}; gain=${tp_gain}; accepted/rejected=${tp_accepted}/${tp_rejected}; AI_corr=${ai_correction}pp; TP_req=${tp_req}pp; TP_applied=${tp_applied}pp; gate=${tp_gate_mode:-observe}/${tp_gate_reason:-unknown}; decision=${tp_decision_reason:-near_target}; guard=${ai_reason}."\n'
    new_tp_log = '''            local tp_log_reason="${tp_decision_reason:-near_target}"
            case "$tp_log_reason" in
              hot_forecast_unconfirmed) tp_log_reason="hot_forecast_confirmation_rejected" ;;
              cool_forecast_unconfirmed) tp_log_reason="cool_forecast_confirmation_rejected" ;;
            esac
            log "Thermal Predictor: mode=${tp_mode}; F30=${tp_f30}C F60=${tp_f60}C F120=${tp_f120}C; confidence=${tp_conf}%; MAE_avg=${tp_mae}C; weighted=${tp_weighted}C raw_weighted=${tp_weighted_raw}C filter_lag=${tp_filter_lag}C error=${tp_error}C; weights=${tp_weights}; gain=${tp_gain}; accepted/rejected=${tp_accepted}/${tp_rejected}; AI_corr=${ai_correction}pp; TP_req=${tp_req}pp; TP_applied=${tp_applied}pp; gate=${tp_gate_mode:-observe}/${tp_gate_reason:-unknown}; decision=${tp_log_reason}; guard=${ai_reason}."
'''
    text = replace_once(text, old_tp_log, new_tp_log, "thermal predictor diagnostic reason")

    text = replace_once(
        text,
        'anti_windup=trend-aware + near-target fast recovery; down_confirm=',
        'anti_windup=trend-aware + graded near-target recovery; reversal_guard=2 cycles/1pp near target; down_confirm=',
        "startup setpoint stability diagnostics",
    )
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    original = path.read_text(encoding="utf-8")
    path.write_text(patch(original), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
