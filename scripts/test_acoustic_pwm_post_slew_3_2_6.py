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

def apply(current, desired, ceiling, *, mode="automatic", reentry="false", max_state=100, recovering="false"):
    variables = ("desired", "controller_state", "acoustic_ceiling", "max_state",
                 "min_run_floor", "COOLING_CONTROL_MODE", "reentry_cycle", "action",
                 "critical_acoustic_recover")
    values = (desired, current, ceiling, max_state, 20, mode, reentry, "normal", recovering)
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

# 3.3.3: replay the full actuator guard, including BOTH acoustic stages.
# Real requests from logs-13 and logs-16. The ceiling helper is stubbed
# to the recorded budget to isolate actuator priority from sensor policy.
guard_start = raw.index('    if [ "$action" != "safety_max" ]; then', raw.index("# v2.6.9 final actuator guard"))
guard_end = raw.index("    # A mismatch while exclusive ownership", guard_start)
guard = raw[guard_start:guard_end]

def replay(current, request, curve, error, ceiling, *, action="normal",
           mode="automatic", reentry="false", last_direction="up", hold=2,
           critical_hold="false", return_hold=False, recovering="false", return_recovery=False):
    values = {
        "controller_state": current, "desired": request, "curve_state": curve,
        "error": error, "recorded_ceiling": ceiling, "action": action,
        "COOLING_CONTROL_MODE": mode, "reentry_cycle": reentry,
        "max_state": 100, "min_run_floor": 20, "adaptive_trim_limit": 12,
        "AI_COOLING_ASSIST_LIMIT_PCT": 5, "acoustic_ceiling": 100,
        "temp_milli": 49000 + error, "temp_control_milli": 49000 + error,
        "thermal_trend_fused_milli": 500, "thermal_signal_quality": "good",
        "slew_up_step": 3, "slew_down_step": 4, "slew_fast_down_step": 5,
        "thermal_fast_delta": 5000, "thermal_critical_delta": 7000,
        "thermal_fast_up_step": 8, "thermal_critical_up_step": 12,
        "down_fast_delta": 2000, "reversal_hold": hold,
        "last_actuator_direction": last_direction, "reversal_guard_step": 1,
        "critical_acoustic_hold": critical_hold, "critical_acoustic_recover": recovering,
    }
    script = ("test_case() {\n" +
              "\n".join(f"local {k}={v!r}" for k, v in values.items()) +
              '\nadaptive_pwm_acoustic_ceiling() { echo "$recorded_ceiling"; }\n' +
              guard + '\nprintf "%s,%s,%s,%s,%s\\n" "$desired" "$action" "$acoustic_ceiling" "$critical_acoustic_hold" "$critical_acoustic_recover"\n}\ntest_case\n')
    result = subprocess.run(["bash", "-c", script], capture_output=True,
                            text=True, check=True, timeout=4)
    pwm, action, budget, latch, recovery = result.stdout.strip().split(",", 4)
    output = (int(pwm), action, int(budget))
    if return_recovery:
        return (*output, latch, recovery)
    return (*output, latch) if return_hold else output

# logs-13: 05:37:50; logs-16: 05:14:51, 05:15:17, 05:15:27.
for case, expected in [
    ((86, 96, 84, 7300, 82), 96),
    ((94, 100, 90, 8300, 97), 100),
    ((97, 100, 92, 8600, 94), 100),
    ((94, 97, 85, 7500, 82), 97),
    ((94, 97, 85, 7000, 82), 97),
]:
    pwm, action, budget = replay(*case)
    assert pwm == expected and budget == 100, (case, pwm, action, budget)
    assert "thermal_critical" in action and "acoustic_" not in action, action

# Immediately below threshold the existing fast-path acoustic policy returns;
# preserve its bounded recovery rather than silently disabling all quiet modes.
pwm, action, budget = replay(94, 93, 81, 6900, 86)
assert pwm == 86 and budget == 86 and "thermal_fast" in action, (pwm, action, budget)
assert replay(94, 100, 90, 8300, 82, action="safety_max")[0] == 100
assert replay(94, 97, 85, 7500, 82, mode="manual")[2] == 100
assert replay(94, 97, 85, 7500, 82, reentry="true")[2] == 100

# 3.3.3 hysteresis: enter at +7 C, hold through +6.9/+6.6 C,
# release at +6.5 C, and do not re-enter until +7 C.
latch = "false"
for error, expected, budget in [
    (6900, "false", 86), (7000, "true", 100),
    (6900, "true", 100), (6600, "true", 100),
    (6500, "false", 86), (6900, "false", 86),
    (7000, "true", 100),
]:
    pwm, action, actual_budget, latch = replay(
        90, 95, 83, error, 86, critical_hold=latch, return_hold=True)
    assert (latch, actual_budget) == (expected, budget), (error, pwm, action, latch, actual_budget)
    if expected == "true" and error < 7000:
        assert "critical_acoustic_hold" in action and "thermal_fast" in action, action

for mode, reentry in [("manual", "false"), ("automatic", "true")]:
    assert replay(90, 95, 83, 6900, 86, critical_hold="true",
                  mode=mode, reentry=reentry, return_hold=True)[3] == "false"
assert 'last_actuator_direction="none"; reversal_hold=0\n      critical_acoustic_hold=false' in raw

# 3.3.5: observed recovery from 95% with an 86% acoustic ceiling.
# Isolate acoustic enforcement from ordinary thermal decisions.
for current, expected in ((95, 91), (91, 87), (87, 86)):
    pwm, reason = apply(current, current, 86, recovering="true")
    assert pwm == expected, (current, pwm, reason)
    assert reason.endswith("critical_acoustic_slow_release"), reason
assert apply(95, 95, 86)[0] == 87
assert apply(95, 90, 100, recovering="true")[0] == 90
assert apply(95, 80, 86, recovering="true")[0] == 80
assert apply(95, 95, 86, mode="manual", recovering="true")[0] == 95

# Full guard: release latch, continue recovery, clear after reaching the cap,
# and re-enter critical without acoustic restrictions.
pwm, action, budget, latch, recovery = replay(
    95, 94, 82, 5700, 86, critical_hold="true", return_recovery=True)
assert (pwm, budget, latch, recovery) == (91, 86, "false", "true"), (pwm, action, budget, latch, recovery)
assert replay(91, 94, 82, 5700, 86, recovering="true", return_recovery=True)[0] == 87
assert replay(87, 94, 82, 5700, 86, recovering="true", return_recovery=True)[0] == 86
assert replay(86, 94, 82, 5700, 86, recovering="true", return_recovery=True)[4] == "false"
assert replay(95, 100, 88, 8000, 86, recovering="true", return_recovery=True)[2:] == (100, "true", "false")
assert replay(95, 100, 88, 8000, 86, action="safety_max", recovering="true")[0] == 100
for mode, reentry in (("manual", "false"), ("automatic", "true")):
    assert replay(95, 94, 82, 5700, 86, mode=mode, reentry=reentry,
                  recovering="true", return_recovery=True)[4] == "false"

# Confirm build uses this patch after reversal/slew patch.
docker = (root / "Dockerfile").read_text(encoding="utf-8")
assert docker.index("python3 /patch_setpoint_stability_3_1_32.py /run_legacy.sh") < docker.index(
    "python3 /patch_acoustic_post_slew_3_2_6.py /run_legacy.sh")
syntax = subprocess.run(["bash", "-n"], input=raw, text=True, capture_output=True, timeout=10)
assert syntax.returncode == 0, syntax.stderr
print("SBC5 3.2.6 post-slew backup acoustic regression: PASS")
