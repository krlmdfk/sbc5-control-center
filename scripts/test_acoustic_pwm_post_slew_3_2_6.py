#!/usr/bin/env python3
"""Offline regression of the *built* 3.2.6 physical PWM acoustic limiter.

Run only extracted Bash fragments; no network, fan writes, or HA hardware.
"""
import importlib.util
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1] / "local_apps/sbc5_control_center"
raw = (root / "run_legacy.sh").read_text(encoding="utf-8")
for name in ("patch_thermal_stability_3_1_29.py", "patch_adaptive_trim_3_1_31.py",
             "patch_setpoint_stability_3_1_32.py", "patch_acoustic_post_slew_3_2_6.py"):
    spec = importlib.util.spec_from_file_location("p" + name.replace(".", "_"), root / name)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    raw = mod.patch(raw)

start = raw.index("      # 3.2.6: post-slew acoustic enforcement.")
end = raw.index('      [ "$desired" -lt "$min_run_floor" ]', start)
fragment = raw[start:end]
assert "acoustic_post_slew" in fragment
assert "controller_state - 8" in fragment
assert '[ "$COOLING_CONTROL_MODE" = "automatic" ]' in fragment
assert '[ "$acoustic_ceiling" -lt "$max_state" ]' in fragment

def apply(current, desired, ceiling, *, mode="automatic", reentry="false", max_state=100):
    variables = ("desired", "controller_state", "acoustic_ceiling", "max_state",
                 "min_run_floor", "COOLING_CONTROL_MODE", "reentry_cycle", "action")
    values = (desired, current, ceiling, max_state, 20, mode, reentry, "normal")
    script = ("test_case() {\n" +
              "\n".join(f"local {k}={v!r}" for k,v in zip(variables, values)) +
              "\n" + fragment +
              '\nprintf "%s,%s\\n" "$desired" "$action"\n}\ntest_case\n')
    result = subprocess.run(["bash", "-c", script], capture_output=True,
                            text=True, check=True, timeout=4)
    pwm, action = result.stdout.strip().split(",", 1)
    return int(pwm), action

# Reproduce observed backup 99% with 92% ceiling: quickly but smoothly recover.
assert apply(99, 99, 92)[0] == 92
assert apply(99, 99, 82)[0] == 91
assert apply(91, 91, 82)[0] == 83
assert apply(83, 83, 82)[0] == 82
# Normal targets below limit are untouched; no artificial fan acceleration.
assert apply(62, 60, 75)[0] == 60
assert apply(60, 95, 82)[0] == 82
# Fully bypass for dangerous temperature/trend or uncertain signal (helper
# returns max_state), for manual mode and reentry.
assert apply(99, 99, 100)[0] == 99
assert apply(99, 99, 82, mode="manual")[0] == 99
assert apply(99, 99, 82, reentry="true")[0] == 99
assert apply(99, 99, 82)[1].endswith("acoustic_post_slew")

# Confirm build uses this patch after reversal/slew patch.
docker = (root / "Dockerfile").read_text(encoding="utf-8")
assert docker.index("python3 /patch_setpoint_stability_3_1_32.py /run_legacy.sh") < docker.index(
    "python3 /patch_acoustic_post_slew_3_2_6.py /run_legacy.sh")
syntax = subprocess.run(["bash", "-n"], input=raw, text=True, capture_output=True, timeout=10)
assert syntax.returncode == 0, syntax.stderr
print("SBC5 3.2.6 post-slew backup acoustic regression: PASS")
