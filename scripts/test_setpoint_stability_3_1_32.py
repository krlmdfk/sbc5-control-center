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

# 3.3.3: execute the actual patched deadband decision in isolation.
start = patched.index('      # 3.1.32 Setpoint Stability:')
end = patched.index('    # Final invariant:', start)
block = patched[start:end]
def deadband_case(error, raw_error, trend, quality, trim=6):
    setup = f"""
target_milli=49000
temp_milli={49000 + raw_error}
error={error}
thermal_trend_fused_milli={trend}
thermal_direction=neutral
thermal_signal_quality={quality}
adaptive_trim={trim}
trim_sign_threshold=300
trim_sign_decay_step=1
trim_decay_interval_cycles=1
deadband_count=1
"""
    script = setup + "\nif true; then\n" + block + '\nprintf "%s:%s" "$action" "$adaptive_trim"'
    return subprocess.check_output(["bash", "-c", script], text=True)

assert deadband_case(600, 600, 0, "good") == "deadband_trim_hold_warm:6"
assert deadband_case(600, 600, -350, "good") == "deadband_trim_recovery_soft:5"
assert deadband_case(200, 200, 0, "good") == "deadband_trim_recovery_fast:4"
assert deadband_case(600, 100, 0, "good") == "deadband_trim_leak_down:5"
assert deadband_case(600, 600, 0, "transient") == "deadband_trim_leak_down:5"

# 3.3.4: exercise the actual built bias block with a deterministic clock.
bias_start = patched.index("    # 3.3.4 Steady-State Bias Compensation")
bias_end = patched.index('    if [ "$action" = "safety_max" ]; then', bias_start)
bias_block = patched[bias_start:bias_end].replace('steady_now="$SECONDS"', 'steady_now="$test_now"')
setup = """
steady_bias=0; steady_since=-1; steady_last_step=-1; steady_last_tick=-1
steady_log_tick=-1
log() { printf '%s\n' "$*" >&2; }
ADAPTIVE_PWM_INTERVAL_SECONDS=10
target_milli=49000
adaptive_trim_limit=12
"""
cases = []
def bias_tick(now, error=900, raw_error=900, trend=0, quality="good",
              trim=0, mode="automatic", reentry="false", action="curve_hold"):
    cases.append(
        f'test_now={now}; error={error}; temp_milli={49000+raw_error}; '
        f'thermal_trend_fused_milli={trend}; thermal_signal_quality={quality}; '
        f'adaptive_trim={trim}; COOLING_CONTROL_MODE={mode}; '
        f'reentry_cycle={reentry}; action={action}\n'
        + bias_block + '\nprintf "%s:%s\\n" "$steady_bias" "$effective_trim"\n'
    )

for now in range(0, 301, 10):
    bias_tick(now)
bias_tick(310, trim=12)  # floor cannot add to saturated normal trim
bias_tick(320, trim=2)   # floor may preserve useful warm-side correction
bias_tick(330, error=500, raw_error=500, trend=-400)
bias_tick(340, error=500, raw_error=500, trend=-400)
bias_tick(350, error=500, raw_error=500, trend=-400)
bias_tick(360, error=0, raw_error=0)
bias_tick(400)  # clock gap must invalidate prior evidence
bias_tick(410, mode="hybrid")
bias_tick(420, quality="transient")
bias_tick(430, action="safety_max", trim=12)
bias_tick(440, reentry="true")
bias_run = subprocess.run(
    ["bash", "-u", "-s"], input=setup + "\n".join(cases), text=True,
    capture_output=True, check=True, timeout=10
)
bias_results = bias_run.stdout.splitlines()
diagnostics = bias_run.stderr.splitlines()
assert len(diagnostics) == 8, diagnostics
assert "floor=0pp base=0pp effective=0pp qualified=0s reason=qualifying" in diagnostics[0]
assert "floor=1pp base=0pp effective=1pp qualified=120s reason=qualified" in diagnostics[2]
assert "floor=4pp base=0pp effective=4pp qualified=300s reason=ceiling" in diagnostics[5]
assert "reason=at_or_below_target" in diagnostics[6]
assert "reason=quality" in diagnostics[7]
assert bias_results[:12] == ["0:0"] * 12
assert bias_results[12] == "1:1"
assert bias_results[18] == "2:2"
assert bias_results[24] == "3:3"
assert bias_results[30] == "4:4"
assert bias_results[31:] == [
    "4:12", "4:4", "3:0", "3:0", "3:0", "0:0",
    "0:0", "0:0", "0:0", "0:12", "0:0",
], bias_results[31:]
assert 'target_state=$((curve_state + effective_trim))' in patched
assert 'steady_bias=0; steady_since=-1; steady_last_step=-1; steady_last_tick=-1' in patched

with tempfile.NamedTemporaryFile("w", suffix=".sh", encoding="utf-8", delete=False) as fh:
    fh.write(patched)
    tmp = Path(fh.name)
try:
    subprocess.run(["bash", "-n", str(tmp)], check=True)
finally:
    tmp.unlink(missing_ok=True)

print("SBC5 3.1.32 Setpoint Stability regression PASS")
