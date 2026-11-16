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
          [ "$acoustic_down_target" -lt "$acoustic_ceiling" ] &&
            acoustic_down_target="$acoustic_ceiling"
        else
          acoustic_down_target="$acoustic_ceiling"
        fi
        if [ "$desired" -gt "$acoustic_down_target" ] 2>/dev/null; then
          desired="$acoustic_down_target"
          action="${action}_acoustic_post_slew"
        fi
      fi
      [ "$desired" -lt "$min_run_floor" ] 2>/dev/null && desired="$min_run_floor"
'''
    return text.replace(anchor, replacement, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    source = path.read_text(encoding="utf-8")
    path.write_text(patch(source), encoding="utf-8")


if __name__ == "__main__":
    main()
