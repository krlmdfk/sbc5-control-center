#!/usr/bin/env python3
"""Regression tests: evaluator output cannot bypass the Adaptive PWM boundary."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
run = (ROOT / "local_apps/sbc5_control_center/run_legacy.sh").read_text(encoding="utf-8")
begin = run.index("ai_cooling_suggestion_allowed() {")
end = run.index("\nadaptive_pwm_controller_loop() {", begin)
fn = run[begin:end]
assert fn.strip().startswith("ai_cooling_suggestion_allowed() {")
assert fn.rstrip().endswith("}")

def accepted(baseline, proposed, correction, state="assist", minimum="9", maximum="100"):
    command = f"{fn}\nai_cooling_suggestion_allowed \"$1\" \"$2\" \"$3\" \"$4\" \"$5\" \"$6\""
    r = subprocess.run(
        ["bash", "-c", command, "--", *map(str, [baseline, proposed, correction, state, minimum, maximum])],
        text=True, capture_output=True, timeout=3,
    )
    assert r.returncode in (0, 1), r.stderr
    return r.returncode == 0

for baseline in (9, 43, 50, 96):
    for delta in (-4, -2, -1, 0, 1, 2, 4):
        proposed = baseline + delta
        if proposed >= 9 and proposed <= 100:
            assert accepted(baseline, proposed, delta), (baseline, delta)
for bad in [
    (50, 55, 5), (50, 45, -5), (50, 54, 2),
    (50, 49, 1), (50, 52, 2, "learning"),
    (50, 52, 2, "disabled"), (50, 52, 2, "ready"),
    (50, "nan", 0), (50, "99999", 0), (50, "50;touch /tmp/bad", 0),
    (50, 50, 0, "assist", 51, 100),
    (50, 51, 1, "assist", 9, 50),
    (50, 51, 1, "assist", 9, 999),
    ("050", 51, 1), (-1, 0, 1),
    (50, 51, "01"),
]:
    assert not accepted(*bad), f"unsafe evaluator suggestion was allowed: {bad}"

controller = run[run.index("adaptive_pwm_controller_loop() {"):run.index("\ntelemetry_publisher_loop() {")]
assert 'if ai_cooling_suggestion_allowed "$desired" "$ai_output" "$ai_correction" "$ai_state" "$min_run_floor" "$max_state"; then' in controller
assert 'desired="$ai_output"' in controller
assert 'odrzucono nieprawidłową korektę modelu' in controller
assert 'if [ "$action" != "safety_max" ]; then' in controller
assert '"$owner_now" != "adaptive"' in controller
print("SBC5 AI output gate and Adaptive PWM authority: PASS")
