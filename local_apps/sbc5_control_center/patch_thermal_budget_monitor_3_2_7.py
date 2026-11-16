#!/usr/bin/env python3
"""3.2.7 build-time thermal budget observability.

Runs after 3.1.32 and 3.2.6 patches; adds diagnostic context to existing
throttled Adaptive PWM log records without adding a new polling loop.
"""
from pathlib import Path
import argparse


def patch(text: str) -> str:
    old = 'reversal=${last_actuator_direction}/${reversal_hold} (${action}); owner=adaptive.'
    new = ('reversal=${last_actuator_direction}/${reversal_hold} '
           'budget=${acoustic_ceiling:-100}% '
           'quality=${thermal_signal_quality:-unknown} '
           '(${action}); owner=adaptive.')
    if text.count(old) != 1:
        raise SystemExit(f"3.2.7 thermal diagnostics: expected one log field, got {text.count(old)}")
    return text.replace(old, new, 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    path.write_text(patch(path.read_text(encoding="utf-8")), encoding="utf-8")
