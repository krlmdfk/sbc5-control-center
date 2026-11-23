#!/usr/bin/env python3
"""Build-time 3.3.3 thermal priority over acoustic PWM ceilings.

Keep the existing independent 66 C safety_max and 70 C kernel handoff.
Only automatic Adaptive PWM acoustic limits are bypassed while the controller
is in a thermal-critical band. The previous acoustic envelope returns after
a 2 C hysteresis; AI limits, manual mode and fan ownership are unchanged.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(source: str, old: str, new: str) -> str:
    matches = source.count(old)
    if matches != 1:
        raise ValueError(f"3.3.3 thermal patch anchor expected once, got {matches}: {old[:90]!r}")
    return source.replace(old, new, 1)


def patch(source: str) -> str:
    helper = r'''# 3.3.3: thermal criticality outranks acoustic comfort in automatic mode.
# 1 means bypass the acoustic budget. This is NOT a hardware safety threshold:
# safety_max (66 C) and kernel handoff (70 C) remain separate.
adaptive_pwm_thermal_priority_active() {
  local raw="$1" conditioned="$2" target="$3" trip_delta="$4" release_delta="$5" previous="$6"
  local trip release
  if ! [[ "$raw" =~ ^[0-9]+$ && "$conditioned" =~ ^[0-9]+$ &&
          "$target" =~ ^[0-9]+$ && "$trip_delta" =~ ^[0-9]+$ &&
          "$release_delta" =~ ^[0-9]+$ && "$previous" =~ ^[01]$ ]]; then
    printf '1\n'
    return 0
  fi
  if [ "$raw" -le 0 ] || [ "$conditioned" -le 0 ]; then
    printf '1\n'
    return 0
  fi
  trip=$((target + trip_delta))
  release=$((target + release_delta))
  if [ "$raw" -ge 60000 ] || [ "$conditioned" -ge 60000 ] ||
     [ "$raw" -ge "$trip" ] || [ "$conditioned" -ge "$trip" ]; then
    printf '1\n'
    return 0
  fi
  # If active, retain full cooling until BOTH signals fall into the
  # lower band. A one-cycle downward reading cannot re-enable the cap.
  if [ "$previous" = "1" ] &&
     { [ "$raw" -gt "$release" ] || [ "$conditioned" -gt "$release" ]; }; then
    printf '1\n'
    return 0
  fi
  printf '0\n'
}

'''
    source = replace_once(source, "adaptive_pwm_controller_loop() {\n", helper + "adaptive_pwm_controller_loop() {\n")
    source = replace_once(
        source,
        '  local acoustic_ceiling=100 acoustic_quality="unknown"',
        '  local acoustic_ceiling=100 acoustic_quality="unknown" thermal_priority_latched=0',
    )
    source = replace_once(
        source,
        '    error=$((temp_milli - target_milli))\n',
        '    error=$((temp_milli - target_milli))\n'
        '    thermal_priority_latched="$(adaptive_pwm_thermal_priority_active '
        '"$temp_milli" "${temp_control_milli:-$temp_milli}" '
        '"$target_milli" "$thermal_critical_delta" "$thermal_fast_delta" '
        '"$thermal_priority_latched")"\n',
    )
    source = replace_once(
        source,
        '        acoustic_ceiling="$(adaptive_pwm_acoustic_ceiling "$temp_milli" "${temp_control_milli:-$temp_milli}" "${thermal_trend_fused_milli:-}" "$acoustic_quality" "$max_state")"',
        '        if [ "$thermal_priority_latched" = "1" ]; then\n'
        '          acoustic_ceiling="$max_state"\n'
        '          action="${action}_thermal_priority"\n'
        '        else\n'
        '          acoustic_ceiling="$(adaptive_pwm_acoustic_ceiling "$temp_milli" "${temp_control_milli:-$temp_milli}" "${thermal_trend_fused_milli:-}" "$acoustic_quality" "$max_state")"\n'
        '        fi',
    )
    return source


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")


if __name__ == "__main__":
    main()
