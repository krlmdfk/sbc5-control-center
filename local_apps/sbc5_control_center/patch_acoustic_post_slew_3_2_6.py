#!/usr/bin/env python3
"""Build-time acoustic ceiling actuator fix for SBC5 3.2.6 field test.

Runs AFTER existing thermal, Adaptive Trim and Setpoint Stability patches.
Does not change safety_max or kernel emergency handoff.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def patch(text: str) -> str:
    anchor = '''        reversal_hold=$((reversal_hold - 1))
      fi
      [ "$desired" -lt "$min_run_floor" ] 2>/dev/null && desired="$min_run_floor"
'''
    if text.count(anchor) != 1:
        raise SystemExit(f"Expected exactly one post-reversal actuator anchor, got {text.count(anchor)}")
    replacement = '''        reversal_hold=$((reversal_hold - 1))
      fi

      # 3.2.6: post-slew acoustic enforcement. The earlier 3.2.5 cap
      # only changed the *request*, leaving the actuator >95% for many cycles
      # after the requested ceiling fell. Cap after reversal/slew as well.
      # Never enter for safety_max: the enclosing guard bypasses this entire
      # block. The helper itself fails open at >=60C, >=6C/min, invalid data,
      # unknown filter quality, or excessive raw-vs-control lag.
      if [ "$COOLING_CONTROL_MODE" = "automatic" ] &&
         [ "$reentry_cycle" != "true" ] &&
         [[ "${acoustic_ceiling:-}" =~ ^[0-9]+$ ]] &&
         [ "$acoustic_ceiling" -lt "$max_state" ] &&
         [ "$desired" -gt "$acoustic_ceiling" ]; then
        local acoustic_down_target
        if [ "$controller_state" -gt "$acoustic_ceiling" ] 2>/dev/null; then
          # At most 8 percentage points down per cycle; avoid abrupt fan
          # deceleration and respect minimum calibrated running floor.
          acoustic_down_target=$((controller_state - 8))
          # 3.3.5: during recovery from critical override, the acoustic
          # layer may not force a faster drop than 4 pp per cycle.
          if [ "${critical_acoustic_recover:-false}" = "true" ]; then
            acoustic_down_target=$((controller_state - 4))
          fi
          [ "$acoustic_down_target" -lt "$acoustic_ceiling" ] &&
            acoustic_down_target="$acoustic_ceiling"
        else
          acoustic_down_target="$acoustic_ceiling"
        fi
        if [ "$desired" -gt "$acoustic_down_target" ] 2>/dev/null; then
          desired="$acoustic_down_target"
          action="${action}_acoustic_post_slew"
          if [ "${critical_acoustic_recover:-false}" = "true" ]; then
            action="${action}_critical_acoustic_slow_release"
          fi
        fi
      fi
      # Once the physical actuator has returned to the ordinary ceiling,
      # future acoustic-only adjustments use the original 8 pp policy.
      if [ "${critical_acoustic_recover:-false}" = "true" ] &&
         [ "$acoustic_ceiling" -lt "$max_state" ] &&
         [ "$controller_state" -le "$acoustic_ceiling" ]; then
        critical_acoustic_recover=false
      fi
      [ "$desired" -lt "$min_run_floor" ] 2>/dev/null && desired="$min_run_floor"
'''
    text = text.replace(anchor, replacement, 1)
    # 3.3.3: the critical path outranks the optional acoustic cap.
    # The loop resets acoustic_ceiling to max_state each cycle; skipping
    # the pre-slew cap consequently disables the post-slew cap as well.
    pre_anchor = '''      if [ "$COOLING_CONTROL_MODE" = "automatic" ] && [ "$reentry_cycle" != "true" ]; then
        acoustic_ceiling="$max_state"
        acoustic_quality="${thermal_signal_quality:-unknown}"
'''
    pre_replacement = '''      # 3.3.3: hysteresis applies only to the optional acoustic ceiling.
      # Enter at the existing +7 C threshold; release at +6.5 C.
      # The critical/fast slew thresholds and absolute safety remain unchanged.
      if [ "$COOLING_CONTROL_MODE" != "automatic" ] || [ "$reentry_cycle" = "true" ]; then
        critical_acoustic_hold=false; critical_acoustic_recover=false
      elif [ "$error" -ge "$thermal_critical_delta" ] 2>/dev/null; then
        critical_acoustic_hold=true; critical_acoustic_recover=false
      elif [ "$error" -le $((thermal_critical_delta - 500)) ] 2>/dev/null; then
        if [ "${critical_acoustic_hold:-false}" = "true" ]; then
          critical_acoustic_recover=true
        fi
        critical_acoustic_hold=false
      fi
      if [ "${critical_acoustic_hold:-false}" = "true" ] &&
         [ "$error" -lt "$thermal_critical_delta" ] 2>/dev/null; then
        action="${action}_critical_acoustic_hold"
      fi
      if [ "$COOLING_CONTROL_MODE" = "automatic" ] && [ "$reentry_cycle" != "true" ] &&
         [ "$error" -lt "$thermal_critical_delta" ] 2>/dev/null &&
         [ "${critical_acoustic_hold:-false}" != "true" ]; then
        acoustic_ceiling="$max_state"
        acoustic_quality="${thermal_signal_quality:-unknown}"
'''
    if text.count(pre_anchor) != 1:
        raise SystemExit("Expected exactly one pre-slew acoustic gate")
    text = text.replace(pre_anchor, pre_replacement, 1)
    init = '  local acoustic_ceiling=100 acoustic_quality="unknown"\n'
    reset = '      last_actuator_direction="none"; reversal_hold=0\n'
    if text.count(init) != 1 or text.count(reset) != 1:
        raise SystemExit("Expected unique acoustic hysteresis lifecycle anchors")
    text = text.replace(init, init + '  local critical_acoustic_hold=false critical_acoustic_recover=false\n', 1)
    return text.replace(reset, reset + '      critical_acoustic_hold=false\n      critical_acoustic_recover=false\n', 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    source = path.read_text(encoding="utf-8")
    path.write_text(patch(source), encoding="utf-8")


if __name__ == "__main__":
    main()
