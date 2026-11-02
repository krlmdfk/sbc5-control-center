#!/usr/bin/env python3
"""Regression tests for SBC5 3.1.32 Setpoint Stability."""
from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"


def load_patch(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


p29 = load_patch(APP / "patch_thermal_stability_3_1_29.py", "p29")
p31 = load_patch(APP / "patch_adaptive_trim_3_1_31.py", "p31")
p32 = load_patch(APP / "patch_setpoint_stability_3_1_32.py", "p32")

raw = (APP / "run_legacy.sh").read_text(encoding="utf-8")
patched = p32.patch(p31.patch(p29.patch(raw)))

assert '[ "$error" -le 300 ]' in patched
assert 'action="deadband_trim_recovery_soft"' in patched
assert 'adaptive_trim=$((adaptive_trim - 1))' in patched
assert 'reversal_guard_cycles=2' in patched
assert 'reversal_guard_step=1' in patched
assert 'action="${action}_reversal_guard"' in patched
assert '[ "$error" -gt -2000 ]' in patched
assert '[ "$error" -lt 2000 ]' in patched
assert 'requested_before_actuator="$desired"' in patched
assert 'physical=${current}->${actual_after}/${max_state}' in patched
assert 'request=${requested_before_actuator}% applied=${desired}%' in patched
assert 'hot_forecast_confirmation_rejected' in patched
assert 'cool_forecast_confirmation_rejected' in patched
assert 'controller ${current}->${desired}/${max_state}' not in patched
assert 'ACTIVE_MAX_DELTA_PP = 2' in (APP / "thermal_active_policy.py").read_text(encoding="utf-8")
assert 'PROBATION_MAX_DELTA_PP = 1' in (APP / "thermal_active_policy.py").read_text(encoding="utf-8")

with tempfile.NamedTemporaryFile("w", suffix=".sh", encoding="utf-8", delete=False) as fh:
    fh.write(patched)
    tmp = Path(fh.name)
try:
    subprocess.run(["bash", "-n", str(tmp)], check=True)
finally:
    tmp.unlink(missing_ok=True)

print("SBC5 3.1.32 Setpoint Stability regression PASS")
