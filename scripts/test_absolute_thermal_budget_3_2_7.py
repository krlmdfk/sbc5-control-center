#!/usr/bin/env python3
"""3.2.7 absolute thermal policy regression: uses only offline Bash fragments.

CPU setpoint (49C) is a comfort/control target, not a safety limit.
Manufacturer throttling is much higher; user-space retains earlier 66C
protection and independent 70C kernel handoff.
"""
from pathlib import Path
import importlib.util
import subprocess

app = Path(__file__).resolve().parents[1] / "local_apps/sbc5_control_center"
source = (app / "run_legacy.sh").read_text(encoding="utf-8")
assert '[ "$temp_milli" -ge 66000 ]' in source
assert '[ "${temp_control_milli:-0}" -ge 66000 ]' in source
assert '[ "$error" -ge "$safety_delta" ]' not in source
assert 'emergency_handoff_milli=70000' in source
assert 'fan_control_release_thermal_ownership adaptive emergency_temperature_handoff' in source
assert 'if [ "$action" = "safety_max" ]; then' in source
assert 'if [ "$action" != "safety_max" ]; then' in source

start = source.index("adaptive_pwm_acoustic_ceiling() {")
end = source.index("\nadaptive_pwm_controller_loop() {", start)
func = source[start:end]


def ceiling(raw, conditioned, trend, quality="good", max_pwm=100):
    cmd = func + '\nadaptive_pwm_acoustic_ceiling "$1" "$2" "$3" "$4" "$5"'
    args = [str(v) for v in (raw, conditioned, trend, quality, max_pwm)]
    cp = subprocess.run(["bash", "-c", cmd, "_", *args], text=True,
                        capture_output=True, check=True, timeout=4)
    return int(cp.stdout.strip())


checks = [
    # Real SBC5 3.2.6 backup log 21:35:25 and 21:35:58,
    # both previously allowed 100% at <60C.
    ((56800, 58300, 1780, "transient"), 92),
    ((57900, 58400, 1064, "transient"), 92),
    ((59000, 58700, 1820, "transient"), 92),
    ((60000, 60000, 0), 94),
    ((62000, 62000, 0), 97),
    ((65000, 65000, 0), 97),
    ((66000, 66000, 0), 100),
    # Safety: robust 60 second extrapolation predicts >=66C.
    ((64000, 64000, 2500), 100),
    # Conservatively fail open if sensor quality is invalid.
    ((56800, 58300, 1780, "spike_filtered"), 100),
    ((56800, 58300, 1780, "warming_up"), 100),
    ((56800, 58300, 1780, "unknown"), 100),
    ((56000, 53000, 0, "good"), 100),  # raw > filtered by 3C
    ((53000, 53000, 6000), 100),  # extreme trend
]
for args, expected in checks:
    actual = ceiling(*args)
    assert actual == expected, (args, actual, expected)

# Check final built image with every patch, including diagnostic observability.
rendered = source
patches = (
    "patch_thermal_stability_3_1_29.py",
    "patch_adaptive_trim_3_1_31.py",
    "patch_setpoint_stability_3_1_32.py",
    "patch_acoustic_post_slew_3_2_6.py",
    "patch_thermal_budget_monitor_3_2_7.py",
)
for filename in patches:
    path = app / filename
    spec = importlib.util.spec_from_file_location(filename.replace(".", "_"), path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rendered = mod.patch(rendered)
assert 'budget=${acoustic_ceiling:-100}% quality=${thermal_signal_quality:-unknown}' in rendered
assert "acoustic_post_slew" in rendered
syntax = subprocess.run(["bash", "-n"], input=rendered, text=True,
                        capture_output=True, timeout=10)
assert syntax.returncode == 0, syntax.stderr
print("SBC5 3.2.7 absolute thermal budget and image composition: PASS")
