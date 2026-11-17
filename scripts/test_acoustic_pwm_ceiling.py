#!/usr/bin/env python3
"""Offline safety regression for the optional acoustic PWM ceiling.

No fan writes, hardware access, HA instance, or live controller execution.
"""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "local_apps" / "sbc5_control_center"
runtime = (APP / "run_legacy.sh").read_text(encoding="utf-8")
begin = runtime.index("adaptive_pwm_acoustic_ceiling() {")
end = runtime.index("\nadaptive_pwm_controller_loop() {", begin)
function_text = runtime[begin:end]

# Load ONLY this pure bash helper in a subprocess; never source run_legacy.sh
# and never access physical fan sysfs.
def ceiling(raw, filtered, trend, quality="good", maximum=100):
    args = [str(x) for x in (raw, filtered, trend, quality, maximum)]
    command = function_text + "\nadaptive_pwm_acoustic_ceiling \"$1\" \"$2\" \"$3\" \"$4\" \"$5\""
    result = subprocess.run(
        ["bash", "-c", command, "_", *args],
        capture_output=True, text=True, check=True, timeout=3,
    )
    return int(result.stdout.strip())

cases = [
    ((50000, 50000, 0), 75),
    ((53999, 53999, 0), 75),
    ((54000, 54000, 0), 82),
    ((56999, 56999, 0), 82),
    ((57000, 57000, 0), 88),
    ((59999, 59999, 0), 88),
    ((60000, 60000, 0), 94),
    # Raw safety sensor may override filtered temperature.
    ((60200, 54500, 0), 100),
    ((54000, 60100, 0), 94),
    # Extreme heating (>=6C/min) bypasses acoustic ceiling; moderate heating gets headroom.
    ((53000, 53000, 2500), 81),
    ((53000, 53000, 2499), 75),
    ((56800, 58300, 1780, "transient"), 92), # 21:35:25 case, <60C
    ((57900, 58400, 1064, "transient"), 92), # 21:35:58 case, <60C
    ((59000, 58700, 1820, "transient"), 92),
    ((66000, 66000, 0), 100),
    ((65900, 65900, 100), 100),  # projected 66.0C
    ((63000, 63000, 3100), 100),  # projected 66.1C in 60s
    ((63000, 63000, 2500), 97),  # projected 65.5C; 97% max
    ((54000, 54000, 0, "transient"), 86),
    ((55000, 55000, 6400), 100),
    ((55300, 54800, 4295), 88),  # Real backup heat ramp in logs
    ((57300, 56800, 3340), 94),  # Peak before 3.2.6
    ((53000, 53000, 6000), 100),  # Severe trend safety bypass
    ((59999, 59999, 5999), 94),
    # If sensor/thermal filter state is unknown, fail open.
    ((53000, 53000, 0, "warming_up"), 100),
    ((53000, 53000, 0, "spike_filtered"), 100),
    # 3.2.8: falling raw CPU samples filtered by median3, both safely below 60C
    ((53500, 56400, -109, "spike_filtered"), 86),   # 05:16:05, former 94% PWM
    ((54000, 55600, 1823, "spike_filtered"), 88),   # 05:14:41, former 91% PWM
    ((51300, 54100, -1485, "spike_filtered"), 86),  # 05:16:47
    # A rising CPU spike must retain unrestricted emergency headroom.
    ((58400, 55600, 1460, "spike_filtered"), 100),  # 05:14:51
    ((60000, 57000, 0, "spike_filtered"), 100),
    ((53000, 56501, 0, "spike_filtered"), 100),     # >3.5C disagreement
    ((53000, 60000, 0, "spike_filtered"), 100),     # filtered >=60C
    ((55000, 57000, 6000, "spike_filtered"), 100),  # fast heating
    ((55000, 57000, 2500, "spike_filtered"), 94),   # 88 + 6 headroom
    ((54000, 56000, 2499, "spike_filtered"), 88),
    ((53000, 53000, 0, "fallback_raw"), 100),
    ((53000, 53000, 0, "unknown"), 100),
    ((53000, 53000, 0, "transient"), 79),
    ((0, 0, 0), 100),
    (("invalid", 53000, 0), 100),
    ((53000, "invalid", 0), 100),
    ((53000, 53000, "invalid"), 100),
    ((53000, 53000, 0, "good", 65), 65),
    ((55001, 53000, 0), 100),  # Raw vs filtered lag > 2C,
]
for args, expected in cases:
    actual = ceiling(*args)
    assert actual == expected, (args, expected, actual)

# Safety gates must remain ordered, uninterrupted, and unaffected.
assert runtime.index("emergency_temperature_handoff") < runtime.index("adaptive_pwm_acoustic_ceiling \"")
assert runtime.index('if [ "$action" = "safety_max" ]; then') < runtime.index('acoustic_ceiling="$(adaptive_pwm_acoustic_ceiling')
assert 'if [ "$action" != "safety_max" ]; then' in runtime
assert 'if [ "$COOLING_CONTROL_MODE" = "automatic" ]' in runtime
assert "reentry_cycle" in runtime
assert "fan_control_release_thermal_ownership adaptive emergency_temperature_handoff" in runtime
assert 'adaptive_pwm_acoustic_ceiling "$temp_milli"' in runtime

# Verify actual image build-time patch sequence composes without collision.
def load_patch(name):
    path = APP / name
    spec = importlib.util.spec_from_file_location("sbc5_" + name.replace(".", "_"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.patch

rendered = runtime
for name in (
    "patch_thermal_stability_3_1_29.py",
    "patch_adaptive_trim_3_1_31.py",
    "patch_setpoint_stability_3_1_32.py",
    "patch_acoustic_post_slew_3_2_6.py",
    "patch_thermal_budget_monitor_3_2_7.py",
):
    rendered = load_patch(name)(rendered)
assert "adaptive_pwm_acoustic_ceiling() {" in rendered
assert "thermal_trend_fused_milli" in rendered
assert "acoustic_quality=" in rendered
assert "safety_max" in rendered
assert "last_actuator_direction" in rendered
assert "budget=${acoustic_ceiling:-100}% quality=${thermal_signal_quality:-unknown}" in rendered
assert "3.2.6: post-slew acoustic enforcement" in rendered
assert "acoustic_post_slew" in rendered
syntax = subprocess.run(["bash", "-n"], input=rendered, capture_output=True, text=True, timeout=8)
assert syntax.returncode == 0, syntax.stderr
print("SBC5 acoustic ceiling safety and build-time composition: PASS")
